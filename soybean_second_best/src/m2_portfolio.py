"""M2: 进口来源组合优化与蒙特卡洛风险分析（定理 6.1、推论 6.2、命题 6.4）。

1. 解析解: s* = w_mv + (U/(ℓ·M))·Ω⁻¹(p̄_mv·1 − p),
   w_mv = Ω⁻¹1/(1'Ω⁻¹1), p̄_mv = (1'Ω⁻¹p)/(1'Ω⁻¹1)
   （目标: min M·s'p·U + 0.5·ℓ·M²·s'Ωs, U=1e-4 换算亿元; 负份额时活跃集迭代）
2. QP 数值解比对（内点一致 <1e-6）
3. 蒙特卡洛: 月度 Markov 中断（进入概率 prob/12·联动 copula, 平均持续 4 个月,
   中断月供应×(1−sev)), 逐月短缺核算与储备释放, 年度损失 0.5·(ℓ/12)·Σ short²
4. 有效前沿: 期望采购成本 vs CVaR 5%
5. 情景 C1–C3 与 (Y, X) 工具网格（命题 6.4 边际替代率）
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src import model_core as mc

ROOT = mc.ROOT
U = mc.WT_CNY_TO_YI


def analytic_shares(p, Om, ell, M):
    """定理 6.1 封闭解 + 推论 6.2 活跃集迭代（负份额置零后在子空间重解）。"""
    idx = list(range(len(p)))
    for _ in range(len(p)):
        Oi = np.linalg.inv(Om[np.ix_(idx, idx)])
        one = np.ones(len(idx))
        pv = p[idx]
        w_mv = Oi @ one / (one @ Oi @ one)
        p_mv = (one @ Oi @ pv) / (one @ Oi @ one)
        s_sub = w_mv + (U / (ell * M)) * Oi @ (p_mv * one - pv)
        if (s_sub >= -1e-12).all():
            s = np.zeros(len(p))
            for k, i in enumerate(idx):
                s[i] = max(s_sub[k], 0.0)
            return s
        idx = [i for k, i in enumerate(idx) if s_sub[k] > 0]
    raise RuntimeError("活跃集迭代未收敛")


def qp_shares(p, Om, ell, M, cap=None):
    """QP 数值解; cap: 各来源份额上限（可获得量约束, None=无约束与定理6.1同口径）。"""
    def obj(s):
        return M * float(s @ p) * U + 0.5 * ell * M ** 2 * float(s @ Om @ s)
    ub = [1.0] * len(p) if cap is None else list(np.minimum(cap, 1.0))
    cons = [{"type": "eq", "fun": lambda s: s.sum() - 1}]
    res = minimize(obj, np.full(len(p), 0.25), method="SLSQP",
                   bounds=[(0, u) for u in ub], constraints=cons,
                   options=dict(maxiter=300, ftol=1e-14))
    return res.x


def simulate_year(s, M, prob, sev, ell_m, X=0.0, Y_mobil=0.0, n=20000,
                  rho_common=0.15, dur_mean=4, seed=20260705,
                  scenario=None, D_month=None):
    """月度蒙特卡洛。返回 dict(cost_draws 亿元, shortage 万吨/月均)。
    scenario: None|'C1'|'C2'|'C3' — C1 美豆6个月近停摆; C2 巴西-20%4个月; C3 联合。
    ell_m = ℓ/12（月度化损失曲率）。X 储备总量(万吨, 年内可用)。"""
    rng = np.random.default_rng(seed)
    k = len(s)
    m_month = M * s / 12.0                      # 各来源月度到港
    if D_month is None:
        D_month = M / 12.0                      # 月度进口需求基线
    lam_month = np.asarray(prob) / 12.0 * dur_mean  # 稳态中断占比近似的进入率
    C = np.full((k, k), rho_common); np.fill_diagonal(C, 1.0)
    Lc = np.linalg.cholesky(C)
    from scipy.stats import norm
    thr = norm.ppf(np.clip(np.asarray(prob) / 12.0 * dur_mean, 1e-9, 1 - 1e-9))

    losses = np.zeros(n); shorts = np.zeros(n)
    sev = np.asarray(sev, float)
    for it in range(n):
        state = np.zeros(k, bool)
        X_left = X
        loss = 0.0; sh_sum = 0.0
        # 情景触发月
        c1 = scenario in ("C1", "C3"); c2 = scenario in ("C2", "C3")
        for t in range(12):
            z = Lc @ rng.standard_normal(k)
            entering = norm.cdf(z) < norm.cdf(thr)
            state = np.where(state, rng.random(k) > 1.0 / dur_mean, entering)
            eff_sev = np.where(state, sev, 0.0)
            if c1 and t < 6:
                eff_sev[1] = max(eff_sev[1], 0.9)      # S2 美国
            if c2 and t < 4:
                eff_sev[0] = max(eff_sev[0], 0.2)      # S1 巴西
            arrive = float(((1 - eff_sev) * m_month).sum())
            gap = D_month - arrive - Y_mobil / 12.0
            rel = min(max(gap, 0.0), X_left)
            X_left -= rel
            short = max(gap - rel, 0.0)
            sh_sum += short
            loss += 0.5 * ell_m * short ** 2
        losses[it] = loss; shorts[it] = sh_sum
    return dict(loss=losses, shortage=shorts)


def cvar(x, a=0.05):
    q = np.quantile(x, 1 - a)
    tail = x[x >= q]
    return float(tail.mean()) if len(tail) else float(q)


def run(cfg=None, save=True, fast=False):
    cfg = cfg or mc.load_cfg()
    src = mc.load_sources()
    p = src.landed_cost_cny_t.to_numpy(float)
    prob = src.disrupt_prob_annual.to_numpy(float)
    sev = src.disrupt_severity.to_numpy(float)
    names = src.name.tolist()
    Om = mc.build_omega(prob, sev)
    ell = cfg["derived"]["ell_qty"] * cfg["structural_params"].get("ell0_scale", 1.0)
    M = cfg["imports_2024"]["M_forecast_2526"]
    X = cfg["structural_params"]["reserve_X"]
    n_mc = 2000 if fast else 20000

    # 1-2. 解析 vs QP（无约束, 定理6.1 一致性检验）+ 带可获得量约束的现实解
    s_an = analytic_shares(p, Om, ell, M)
    s_qp = qp_shares(p, Om, ell, M)
    err = float(np.abs(s_an - s_qp).max())
    interior = (s_an > 1e-6).all()
    print(f"[M2] 解析 vs QP 最大偏差 {err:.2e} ({'内点' if interior else '角点'})")
    m_cap = np.array([7200.0, 4427.0, 820.0, 830.0])   # 与 M1 同口径
    s_cap = qp_shares(p, Om, ell, M, cap=m_cap / M)
    s_2024 = src.share_2024.to_numpy(float)
    shares = pd.DataFrame({"source": names, "analytic": s_an.round(4),
                           "qp": s_qp.round(4), "qp_capped": s_cap.round(4),
                           "actual_2024": s_2024})

    # 3-4. 有效前沿（份额网格 + 关键点）
    # 月度化曲率 ℓ_m = 12·ℓ: 均匀年短缺 s 时 0.5·12ℓ·12·(s/12)² = 0.5·ℓ·s²（尺度等价,
    # 集中于少数月份的短缺被更重惩罚——刚性需求下的正确性质）
    ell_m = 12.0 * ell
    rng = np.random.default_rng(7)
    grid = [s_an, s_cap, s_2024, np.array([1, 0, 0, 0.0]), np.array([0.25] * 4),
            np.array([0.5, 0.3, 0.1, 0.1]), np.array([0.6, 0.2, 0.1, 0.1]),
            np.array([0.8, 0.1, 0.05, 0.05])]
    for _ in range(6 if fast else 20):
        w = rng.dirichlet([2, 1.2, 0.5, 0.5])
        grid.append(w)
    rows = []
    for s in grid:
        sim = simulate_year(s, M, prob, sev, ell_m, X=X, n=n_mc)
        cost = M * float(s @ p) * U
        rows.append(dict(cost=cost, cvar=cvar(sim["loss"]),
                         eloss=float(sim["loss"].mean()),
                         s=np.round(s, 3).tolist()))
    frontier = pd.DataFrame(rows)
    frontier["tag"] = [""] * len(frontier)
    frontier.loc[0, "tag"] = "解析最优"; frontier.loc[1, "tag"] = "约束最优"
    frontier.loc[2, "tag"] = "2024实际"

    # 5. 情景 C1–C3（基于 2024 实际组合）
    scen_rows = []
    for scn in [None, "C1", "C2", "C3"]:
        sim = simulate_year(s_2024, M, prob, sev, ell_m, X=X, n=n_mc, scenario=scn)
        scen_rows.append(dict(scenario=scn or "基线", mean_short_wt=float(sim["shortage"].mean()),
                              p95_short_wt=float(np.quantile(sim["shortage"], 0.95)),
                              mean_loss_yi=float(sim["loss"].mean()),
                              cvar5_yi=cvar(sim["loss"])))
    scen = pd.DataFrame(scen_rows)

    # 6. (Y, X) 工具网格 — 命题 6.4 边际替代率
    tool_rows = []
    for Yv in [1800.0, 2090.0, 2400.0]:
        for Xv in [500.0, 1000.0, 2000.0]:
            chi = cfg["structural_params"]["mobilization_chi"]
            sim = simulate_year(s_an, M, prob, sev, ell_m, X=Xv,
                                Y_mobil=chi * Yv, n=n_mc)
            tool_rows.append(dict(Y=Yv, X=Xv, cvar5=cvar(sim["loss"]),
                                  eloss=float(sim["loss"].mean())))
    tools = pd.DataFrame(tool_rows)
    # 边际替代率 ΔCVaR/ΔY vs ΔCVaR/ΔX（在中心点）
    c = tools.set_index(["Y", "X"]).cvar5
    mrs_Y = (c[(2400, 1000)] - c[(1800, 1000)]) / 600.0
    mrs_X = (c[(2090, 2000)] - c[(2090, 500)]) / 1500.0
    print(f"[M2] ΔCVaR/ΔY={mrs_Y:.5f}, ΔCVaR/ΔX={mrs_X:.5f} 亿元/万吨")

    res = dict(shares=shares, frontier=frontier, scenarios=scen, tools=tools,
               analytic_qp_err=err, interior=interior,
               mrs=dict(dCVaR_dY=float(mrs_Y), dCVaR_dX=float(mrs_X)))
    if save:
        shares.to_csv(ROOT / "results/tables/T3_optimal_shares.csv", index=False)
        scen.round(3).to_csv(ROOT / "results/tables/T_M2_scenarios.csv", index=False)
        tools.round(3).to_csv(ROOT / "results/tables/T_M2_tool_grid.csv", index=False)
        _figures(frontier, scen)
    return res


def _figures(frontier, scen):
    plt = mc.setup_cjk()
    fig, ax = plt.subplots(figsize=(7.5, 5))
    m = frontier.tag == ""
    ax.scatter(frontier.cost[m], frontier.cvar[m], s=25, alpha=0.6, label="份额组合")
    for _, r in frontier[~m].iterrows():
        ax.scatter(r.cost, r.cvar, s=90, marker="*",
                   label=f"{r.tag} {r.s}")
    ax.set_xlabel("期望采购成本 (亿元)"); ax.set_ylabel("CVaR 5% 短缺损失 (亿元)")
    ax.set_title("进口来源组合: 成本–风险有效前沿 (M2)")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(ROOT / "results/figures/F3_frontier.png", dpi=300)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(scen.scenario, scen.cvar5_yi, color="#8c1f28", alpha=0.85)
    ax.set_ylabel("CVaR 5% 损失 (亿元)"); ax.set_title("中断情景的年度损失 (2024实际组合)")
    fig.tight_layout(); fig.savefig(ROOT / "results/figures/F4_scenario_shortage.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    r = run(fast=True)
    print(r["shares"].to_string(index=False))
    print(r["scenarios"].to_string(index=False))
