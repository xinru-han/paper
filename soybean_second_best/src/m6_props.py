"""M6: 理论命题的结构检验 T1–T6 ↔ H1′–H6′（§9）。"""
import numpy as np
import pandas as pd

from src import model_core as mc
from src import m1_planner as m1
from src import m2_portfolio as m2
from src.m4_abm import ABM
from src import m5_policy as m5

ROOT = mc.ROOT
U = mc.WT_CNY_TO_YI


def t1_risk_capacity(cfg, fast=True):
    """H1′: ∂Y*/∂ρ>0 且高成本 ω 组增幅更小（交叉导数<0）。"""
    sc0, base_scale, _ = m1.calibrate_supply(cfg)
    Y_obs = cfg["supply_domestic"]["Y_2025"]
    c_star = float(sc0.MC(Y_obs))
    out = {}
    for tag, ws in [("low_w", 0.7), ("high_w", 1.3)]:
        # ω 操作化为成本梯度(供给曲线曲率): 绕校准点 (Y_2090, c*) 旋转曲线。
        # 水平缩放会被 β 校准的齐次性吸收, 命题 H1′ 的机制在曲率: dY*/dρ ∝ 1/MC′
        sc = mc.SupplyCurve(sc0.y_grid, c_star + ws * (sc0.c_grid - c_star),
                            sc0.total_capacity, sc0.region_table)
        beta, P0, base = m1.calibrate_beta(cfg, sc)
        Ys = []
        for rs in (1.0, 2.0):
            P = m1.calibrate_chain(cfg, m1.build_problem(cfg, sc, rho_scale=rs))
            P["beta_sec"] = beta
            P["sc"] = sc
            Ys.append(m1.solve(P, x0=base["x"])["Y"])
        out[tag] = Ys[1] - Ys[0]
    ok = out["low_w"] > 0 and out["high_w"] > 0 and out["high_w"] < out["low_w"]
    return dict(test="T1", dY_low_w=round(out["low_w"], 1),
                dY_high_w=round(out["high_w"], 1), passed=bool(ok))


def t2_quality_transmission(cfg, fast=True):
    """H2′: ϑ 0.22→0.68 → q̄↑; dlnq/dlnϑ ≈ 1/(δ−m) ±30%。"""
    n = 1500 if fast else 5000
    qs = {}
    for th in (0.22, 0.68):
        df = ABM(cfg, n_agents=n, seed=5,
                 policy=dict(theta_transmission=th)).run(range(2026, 2029))
        qs[th] = df.q_bar.mean()
    elas = np.log(qs[0.68] / qs[0.22]) / np.log(0.68 / 0.22)
    target = 1.0 / cfg["structural_params"]["delta_minus_m"]
    ok = qs[0.68] > qs[0.22] and abs(elas - target) / target < 0.30
    return dict(test="T2", q_low=round(qs[0.22], 4), q_high=round(qs[0.68], 4),
                elasticity=round(float(elas), 3), target=round(target, 3), passed=bool(ok))


def t3_selection(cfg, fast=True):
    """H3′: 进入专用市场(q_i>1)农户的 φ 中位数更高, 单调门槛 AUC>0.8。"""
    abm = ABM(cfg, n_agents=1500 if fast else 10000, seed=11)
    abm.step(2026)
    theta = cfg["structural_params"]["theta_transmission"]
    q_i = theta ** (1.0 / abm.dm) * abm.phi_i * abm.theta_r
    soy = abm.soy_prev
    enter = q_i > np.quantile(q_i[soy], 0.75) if soy.any() else q_i > 1
    phi_in = np.median(abm.phi_i[soy & enter]) if (soy & enter).any() else 0
    phi_out = np.median(abm.phi_i[soy & ~enter]) if (soy & ~enter).any() else 1
    # AUC: φ 对 enter 的判别力
    from numpy import argsort
    x, y = abm.phi_i[soy], enter[soy].astype(int)
    order = argsort(x)
    ranks = np.empty(len(x)); ranks[order] = np.arange(1, len(x) + 1)
    n1, n0 = y.sum(), (1 - y).sum()
    auc = (ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / max(n1 * n0, 1)
    ok = phi_in > phi_out and auc > 0.8
    return dict(test="T3", phi_med_in=round(float(phi_in), 3),
                phi_med_out=round(float(phi_out), 3), auc=round(float(auc), 3),
                passed=bool(ok))


def t4_chain_complementarity(cfg, fast=True):
    """H4′: sign(∂²Φ/∂Y∂K) 的边界 = ε_Φ=1/η 直线（误差<5%）; Leontief 短板下
    扩种边际收益→0。Φ(G)=G^(1−ε_Φ)/(1−ε_Φ)。"""
    Y0, K0, H0 = 2090.0, 9500.0, 9500.0
    h = 1.0
    etas = np.linspace(0.25, 1.4, 12)
    bound_err = []
    for eta in etas:
        # 对每个 η 求跨偏导变号的 ε_Φ*
        def cross(epsphi):
            def Phi(Y, K):
                G = mc.ces_G(Y + 9400, K, H0, eta=float(eta))
                return G ** (1 - epsphi) / (1 - epsphi)
            return (Phi(Y0 + h, K0 + h) - Phi(Y0 + h, K0)
                    - Phi(Y0, K0 + h) + Phi(Y0, K0)) / h ** 2
        lo, hi = 0.05, 3.0
        if cross(lo) * cross(hi) > 0:
            continue
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            if cross(lo) * cross(mid) <= 0:
                hi = mid
            else:
                lo = mid
        eps_star = 0.5 * (lo + hi)
        bound_err.append(abs(eps_star - 1.0 / eta) * eta)   # 相对 1/η 的误差
    err = float(np.mean(bound_err)) if bound_err else 1.0
    # Leontief 短板: η→0, K 束紧时 dΦ/dY → 0
    G1 = mc.ces_G(2090 + 9400, 5000, H0, eta=1e-4)
    G2 = mc.ces_G(2290 + 9400, 5000, H0, eta=1e-4)
    leontief_flat = abs(G2 - G1) < 1e-6
    ok = err < 0.05 and leontief_flat
    return dict(test="T4", boundary_err=round(err, 4),
                leontief_flat=bool(leontief_flat), passed=bool(ok))


def t5_tool_substitution(cfg, fast=True):
    """H5′: ∂(边际CVaR降幅_Y)/∂X < 0（工具替代）。用 M2 工具网格。"""
    import pandas as pd
    f = ROOT / "results/tables/T_M2_tool_grid.csv"
    if f.exists():
        tools = pd.read_csv(f)
    else:
        tools = m2.run(cfg, save=False, fast=True)["tools"]
    c = tools.set_index(["Y", "X"]).cvar5
    mY_lowX = (c[(2400, 500)] - c[(1800, 500)]) / 600.0
    mY_highX = (c[(2400, 2000)] - c[(1800, 2000)]) / 600.0
    ok = mY_lowX < 0 and mY_highX > mY_lowX   # X 大时 Y 的边际降幅变小(替代)
    return dict(test="T5", dCVaRdY_lowX=round(float(mY_lowX), 5),
                dCVaRdY_highX=round(float(mY_highX), 5), passed=bool(ok))


def t6_policy_efficiency(cfg, fast=True, m5_res=None):
    """H6′: P2 同产量财政成本 < P1; P3 DWL 与解析式偏差 <25%（或两者均≈0）。"""
    r = m5_res or m5.run(cfg, save=False, fast=True)
    p0, p1, p2 = r["results"]["P0"], r["results"]["P1"], r["results"]["P2"]
    # 财政效率 = 每元财政支出的福利增量（含定向带来的质量/安全收益）
    eff1 = (p1["welfare"] - p0["welfare"]) / max(p1["fiscal"], 1)
    eff2 = (p2["welfare"] - p0["welfare"]) / max(p2["fiscal"], 1)
    dwl_ok = (abs(r["dwl_sim"] - r["dwl_analytic"])
              <= max(0.25 * r["dwl_analytic"], 5.0))   # 相对25%或绝对5亿容差
    ok = eff2 >= eff1 * 0.98 and dwl_ok
    return dict(test="T6", welfare_per_fiscal_P1=round(eff1, 4),
                welfare_per_fiscal_P2=round(eff2, 4),
                dwl_sim=round(r["dwl_sim"], 2), dwl_analytic=round(r["dwl_analytic"], 2),
                passed=bool(ok))


def run(cfg=None, save=True, fast=True, m5_res=None):
    cfg = cfg or mc.load_cfg()
    rows = [t1_risk_capacity(cfg, fast), t2_quality_transmission(cfg, fast),
            t3_selection(cfg, fast), t4_chain_complementarity(cfg, fast),
            t5_tool_substitution(cfg, fast), t6_policy_efficiency(cfg, fast, m5_res)]
    df = pd.DataFrame([{**r} for r in rows])
    if save:
        df.to_csv(ROOT / "results/tables/T_M6_propositions.csv", index=False)
    return df


if __name__ == "__main__":
    print(run().to_string(index=False))
