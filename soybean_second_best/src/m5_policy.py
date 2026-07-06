"""M5: 政策实验矩阵 P0–P6（统一预算约束 ≈540 亿元/年, §8）。

P0 无干预 | P1 统一面积补贴350元/亩 | P2 定向补贴(按区域社会净收益梯度1.5×/0.5×)
P3 价格保护(τ=627元/吨, 无补贴) | P4 质量链条包(40%检测分储→ϑ↑, 30%K/H, 30%定向)
P5 韧性包(30%储备X→2000, 30%多元化S3/S4降价降险, 40%定向) | P6 组合最优(网格搜索)

评价: 福利分项、财政成本、CVaR₅%短缺损失、农户收入与基尼、自给率/HHI、质量、
P3 无谓损失 vs 命题12.4 解析值 τ²|D′|/2。

预登记假设（先写后跑）: P2≻P1(财政效率), P4质量维度最优, P5 CVaR最优,
P3被P2支配且DWL≈τ²|D′|/2, P6≻单项包。
"""
import numpy as np
import pandas as pd

from src import model_core as mc
from src.m4_abm import ABM

ROOT = mc.ROOT
U = mc.WT_CNY_TO_YI
BUDGET = 540.0   # 亿元/年


def targeted_subsidy(cfg, budget_yi=BUDGET, hi=1.5, lo=0.5):
    """P2: 按区域社会净收益 S_r 排序的定向补贴(元/亩), 预算=budget。
    S_r 代理: 单产高/半径短/θ高 → R2,R4 高档; R5,R6 低档。"""
    R = mc.load_regions()
    score = (R.yield_kg_mu / R.yield_kg_mu.max() * 0.5
             + R.quality_theta / R.quality_theta.max() * 0.3
             + (1 - R.proc_radius_km / R.proc_radius_km.max()) * 0.2)
    mult = np.where(score >= score.median(), hi, lo)
    # 归一: Σ area_r·mult_r·s0 = budget → s0
    s0 = budget_yi / float((R.area_wan_mu * mult).sum() * 1e-4)
    return (mult * s0).astype(float)   # 元/亩 各区


POLICIES = {
    "P0": dict(sub_area=0.0),
    "P1": dict(sub_area=350.0),
    "P2": dict(sub_area=0.0, use_targeted=True),
    "P3": dict(sub_area=0.0, price_floor_tau=627.0),
    "P4": dict(sub_area=0.0, use_targeted=True, targeted_budget=0.3 * BUDGET,
               theta_transmission=0.68, quality_budget=0.4 * BUDGET + 0.3 * BUDGET),
    "P5": dict(sub_area=0.0, use_targeted=True, targeted_budget=0.4 * BUDGET,
               reserve_X=2000, import_cost_shift_s34=-80.0, import_prob_scale=None,
               quality_budget=0.6 * BUDGET),
    "P6": None,   # 组合搜索
}
PREREG = ["P2≻P1 财政效率", "P4 质量维度最优", "P5 CVaR 维度最优",
          "P3 被 P2 支配且 DWL≈τ²|D'|/2", "P6≻单项包"]


def build_policy(cfg, name, spec=None):
    spec = dict(spec if spec is not None else POLICIES[name])
    if spec.pop("use_targeted", False):
        bud = spec.pop("targeted_budget", BUDGET)
        spec["sub_targeted"] = targeted_subsidy(cfg, budget_yi=bud)
    if spec.get("import_prob_scale") is None and name == "P5":
        spec["import_prob_scale"] = np.array([1, 1, 0.7, 0.7])
    spec.pop("targeted_budget", None)
    return spec


_SC_CACHE = {}


def _get_sc(cfg):
    if "sc" not in _SC_CACHE:
        sc = mc.merit_order_supply(mc.validate_regions(mc.load_regions()),
                                   cost_scale=cfg["derived"].get("cost_scale", 1.0))
        _SC_CACHE["sc"] = sc
    return _SC_CACHE["sc"]


def eval_policy(cfg, name, spec=None, n_seeds=20, n_agents=2000, horizon=(2026, 2035),
                budget_control=True):
    pol = build_policy(cfg, name, spec)
    # P2/P4/P5 的定向补贴: 先用 2 个种子试算实际支出, 按预算回缩(吸纳内生面积响应)
    if budget_control and pol.get("sub_targeted") is not None:
        probe = ABM(cfg, n_agents=800, seed=999, policy=pol).run(range(2026, 2029))
        fiscal_probe = float(probe.fiscal.mean()) - pol.get("quality_budget", 0.0)
        target = (POLICIES.get(name) or {}).get("targeted_budget",
                                                BUDGET - pol.get("quality_budget", 0.0))
        target = max(target, 1.0)
        if fiscal_probe > 1.05 * target:
            pol["sub_targeted"] = pol["sub_targeted"] * (target / fiscal_probe)
    sp = cfg["structural_params"]
    ell = cfg["derived"]["ell_qty"] * sp.get("ell0_scale", 1.0)
    beta = cfg["derived"].get("beta_security", 1000.0)
    sc = _get_sc(cfg)
    vy = float(cfg["prices"]["spread_dom_import_2024"])
    X_pol = pol.get("reserve_X") or sp["reserve_X"]
    # 基线质量尺度 q̄0 = ϑ0^{1/(δ−m)}·E[φ]·(θ_r 面积加权): 观测溢价 vy 对应
    # 基线质量水平, 质量项按 q̄/q̄0 归一（q̄ 直接乘 vy 会把水平当乘子, 低估 60%）
    R_ = mc.load_regions()
    q0 = (sp["theta_transmission"] ** (1.0 / sp["delta_minus_m"]) * 1.011
          * float(np.average(R_.quality_theta, weights=R_.area_wan_mu)))
    rows = []
    for s in range(n_seeds):
        df = ABM(cfg, n_agents=n_agents, seed=1000 + s, policy=pol).run(
            range(horizon[0], horizon[1] + 1))
        # 事后短缺损失用经济曲率 ℓ; 事前安全价值 B 用规划者权重 λ_B=β·ℓ（式3.4,
        # 二者并存: B 是危机期权价值, losses 是实现损失——第二优福利的两个组成）
        losses = 0.5 * ell * df.short.to_numpy() ** 2               # 亿元/年
        B_t = np.array([mc.B_security(y, sp["crisis_prob_pi"], beta * ell,
                                      sp["mobilization_chi"],
                                      sp["crisis_import_loss_kappa"], m, X_pol)
                        for y, m in zip(df.Y, df.M_planned)])
        supply_cost = np.array([sc.cost_integral(y) for y in df.Y])  # 资源成本
        imp_cost = df.M_planned * df.p_imp * U
        quality_v = (df.q_bar / q0) * df.Y * vy * U                  # 食用溢价价值(归一)
        # 福利不再扣 MCF: β 为含财政摩擦的揭示权重(政府在承担财政成本下选择了
        # 现行规模), M5 再扣 20% 即双重计费; 财政作为独立列与效率指标报告
        welfare = -supply_cost - imp_cost - losses + B_t + quality_v
        rows.append(dict(
            seed=s, Y=df.Y.mean(), M=df.M_planned.mean(),
            welfare=float(welfare.mean()), fiscal=float(df.fiscal.mean()),
            loss_mean=float(losses.mean()), loss_max=float(losses.max()),
            income=float(df.income_soy.mean()), gini=float(df.gini.mean()),
            selfsuff=float((df.Y / (df.Y + df.M_planned)).mean()),
            hhi=float(df.hhi.mean()), q_bar=float(df.q_bar.mean()),
            hi_q=float(df.hi_q_share.mean()), short=float(df.short.mean()),
            p_dom=float(df.p_dom.mean())))
    d = pd.DataFrame(rows)
    agg = d.mean(numeric_only=True).to_dict()
    agg["cvar_loss"] = float(np.quantile(d.loss_max, 0.95))
    agg["policy"] = name
    return agg, d


def p3_dwl(cfg, res_p3, res_p0):
    """命题12.4: DWL ≈ τ²·|D′|/2。|D′| 用 ABM 供给响应近似(dY/dp)。"""
    tau = 627.0
    dY = res_p3["Y"] - res_p0["Y"]
    dp = res_p3["p_dom"] - res_p0["p_dom"]
    slope = abs(dY / dp) if abs(dp) > 1 else 0.5   # 万吨/(元/吨)
    dwl_analytic = 0.5 * tau ** 2 * slope * U      # 亿元
    dwl_sim = max((res_p3["p_dom"] - res_p0["p_dom"]) * res_p3["M"] * U * 0
                  + 0.5 * (res_p3["p_dom"] - res_p0["p_dom"]) * dY * U, 0.0)
    return dwl_analytic, dwl_sim, slope


def run(cfg=None, save=True, fast=False):
    cfg = cfg or mc.load_cfg()
    n_seeds = 8 if fast else 200
    n_agents = 1500 if fast else 10000
    results, raw = {}, {}
    for name in ["P0", "P1", "P2", "P3", "P4", "P5"]:
        agg, d = eval_policy(cfg, name, n_seeds=n_seeds, n_agents=n_agents)
        results[name], raw[name] = agg, d
        print(f"[M5] {name}: Y={agg['Y']:.0f} W={agg['welfare']:.0f} "
              f"财政={agg['fiscal']:.0f} CVaR={agg['cvar_loss']:.1f}")
    # P6: {P2,P4,P5} 权重单纯形粗网格
    best, best_w = None, None
    grid = [(a / 4, b / 4, 1 - a / 4 - b / 4) for a in range(5) for b in range(5 - a)]
    grid = grid[::3] if fast else grid
    for (w2, w4, w5) in grid:
        spec = dict(sub_area=0.0, use_targeted=True, targeted_budget=w2 * BUDGET
                    + w4 * 0.3 * BUDGET + w5 * 0.4 * BUDGET,
                    theta_transmission=0.35 + w4 * (0.68 - 0.35),
                    reserve_X=1000 + w5 * 1000,
                    import_cost_shift_s34=-80.0 * w5,
                    quality_budget=w4 * 0.7 * BUDGET + w5 * 0.6 * BUDGET)
        agg, d = eval_policy(cfg, "P6", spec=spec,
                             n_seeds=max(4, n_seeds // 2), n_agents=n_agents)
        if best is None or agg["welfare"] > best["welfare"]:
            best, best_w, best_raw = agg, (w2, w4, w5), d
    best["policy"] = f"P6({best_w[0]:.2f},{best_w[1]:.2f},{best_w[2]:.2f})"
    results["P6"], raw["P6"] = best, best_raw
    print(f"[M5] P6 最优权重 (P2,P4,P5)={best_w}, W={best['welfare']:.0f}")

    dwl_an, dwl_sim, slope = p3_dwl(cfg, results["P3"], results["P0"])
    tbl = pd.DataFrame(results.values())
    cols = ["policy", "welfare", "fiscal", "cvar_loss", "Y", "M", "selfsuff",
            "hhi", "income", "gini", "q_bar", "hi_q", "short", "p_dom"]
    tbl = tbl[cols].round(3)
    # 预登记假设兑现
    checks = {
        "P2≻P1(福利/财政效率)": bool(results["P2"]["welfare"] >= results["P1"]["welfare"]),
        "P4 质量最优": bool(results["P4"]["q_bar"] == max(r["q_bar"] for r in results.values())),
        "P5 CVaR最优": bool(results["P5"]["cvar_loss"] <= min(
            results[k]["cvar_loss"] for k in ["P0", "P1", "P2", "P3", "P4", "P5"])),
        "P3 被 P2 支配": bool(results["P2"]["welfare"] >= results["P3"]["welfare"]),
        "P6≻单项包": bool(results["P6"]["welfare"] >= max(results[k]["welfare"]
                                                       for k in ["P2", "P4", "P5"])),
    }
    res = dict(table=tbl, checks=checks, dwl_analytic=dwl_an, dwl_sim=dwl_sim,
               dwl_slope=slope, prereg=PREREG, results=results)
    if save:
        tbl.to_csv(ROOT / "results/tables/T4_policy_matrix.csv", index=False)
        with open(ROOT / "results/tables/T4_policy_matrix.md", "w") as f:
            f.write(tbl.to_markdown(index=False))
        _figures(tbl)
    return res


def _figures(tbl):
    plt = mc.setup_cjk()
    # F7 雷达图
    dims = ["welfare", "fiscal", "cvar_loss", "income", "selfsuff", "q_bar"]
    lab = ["福利", "财政(低优)", "CVaR(低优)", "农户收入", "自给率", "质量"]
    T = tbl.copy()
    for c, invert in zip(dims, [False, True, True, False, False, False]):
        v = T[c].to_numpy(float)
        rng_ = v.max() - v.min() or 1.0
        T[c] = 1 - (v - v.min()) / rng_ if invert else (v - v.min()) / rng_
    ang = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist() + [0]
    fig, ax = plt.subplots(figsize=(7.5, 7), subplot_kw=dict(polar=True))
    for _, r in T.iterrows():
        vals = [r[c] for c in dims] + [r[dims[0]]]
        ax.plot(ang, vals, label=r.policy, lw=1.5)
    ax.set_xticks(ang[:-1]); ax.set_xticklabels(lab)
    ax.set_title("政策矩阵六维比较 (M5)"); ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(ROOT / "results/figures/F7_policy_radar.png", dpi=300)
    plt.close(fig)
    # F8 福利瀑布（相对 P0）
    fig, ax = plt.subplots(figsize=(8, 4.5))
    base = tbl[tbl.policy == "P0"].welfare.iloc[0]
    ax.bar(tbl.policy, tbl.welfare - base, color="#2b6a99")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("相对 P0 的福利变化 (亿元/年)")
    ax.set_title("政策的福利效果 (M5)")
    plt.setp(ax.get_xticklabels(), rotation=20, fontsize=8)
    fig.tight_layout(); fig.savefig(ROOT / "results/figures/F8_welfare_decomp.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    r = run(fast=True)
    print(r["table"].to_string(index=False))
    print(r["checks"], f"DWL 解析={r['dwl_analytic']:.1f} 模拟={r['dwl_sim']:.1f} 亿元")
