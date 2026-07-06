"""M1: 校准规划模型与比较静态（理论文档式 4.9, 定理 4.3–4.4, 命题 5.3）。

规划问题: max W(Y, m, Z, K, H)
  W = −∫MC −进口支出 −R(m) + B(Y) + V_Y·Y + Φ(G(Y+M,K,H)) − F(K,H) − C_Z(Z)
  s.t. Y + Σm + Z = D, 非负。
校准锚（§4.1）:
  - 全成本口径 MC: cost_scale 校准使 MC(Y_2025=2090) 落在 [6400,7600] 元/吨带
    （观测激励 = 拍卖价 4298 + 补贴当量 2581 ≈ 6879 元/吨）
  - V_Y = 国产-进口价差 × 食用/专用份额 ≈ 627×0.75 ≈ 470 元/吨（∈[300,800]带）
  - C_Z: cz1=100 元/吨, cz2 使 C_Z'(900)=800 元/吨
  - Φ(G)=phi0·G^0.9, F=0.5(fk·K²+fh·H²), phi0/fk/fh 校准到基线 K≈9500 万吨
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src import model_core as mc

ROOT = mc.ROOT
U = mc.WT_CNY_TO_YI   # 万吨×元/吨 -> 亿元


def calibrate_supply(cfg, regions=None):
    """构造优序供给并校准 cost_scale 使 MC(Y_obs) ≈ 观测边际激励。

    供给成本口径已含玉米机会成本（land_opp = 玉米剩余, build_regions.py）→
    农户边际条件: p_dom + (s_soy − s_corn)/yield = MC。观测激励 = 拍卖价 +
    补贴差当量（不再是大豆补贴全额——玉米同补部分不改变相对激励）。"""
    regions = regions if regions is not None else mc.validate_regions(mc.load_regions())
    Y_obs = cfg["supply_domestic"]["Y_2025"]
    p_auc = cfg["prices"]["p_domestic_food_2026Q1"]                  # 4298
    sub_diff = cfg["subsidies_2025"].get("corn_soy_diff_hlj", 248.0)
    sub_t = sub_diff / (cfg["supply_domestic"]["yield_2025"] / 1000)  # ≈1825 元/吨
    target = p_auc + sub_t                                            # ≈ 6123 元/吨
    lo, hi = 0.5, 3.0
    for _ in range(60):                                               # 二分校准
        mid = 0.5 * (lo + hi)
        sc = mc.merit_order_supply(regions, cost_scale=mid)
        v = sc.MC(Y_obs)
        if v < target:
            lo = mid
        else:
            hi = mid
    sc = mc.merit_order_supply(regions, cost_scale=0.5 * (lo + hi))
    ok = 5500 <= sc.MC(Y_obs) <= 6900 and abs(sc.MC(Y_obs) - target) / target < 0.10
    print(f"[M1校准] cost_scale={0.5*(lo+hi):.3f} MC({Y_obs:.0f})={sc.MC(Y_obs):.0f} "
          f"目标={target:.0f} 一致性检验: {'通过' if ok else '失败'}")
    return sc, float(0.5 * (lo + hi)), target


def build_problem(cfg, sc, rho_scale=1.0, pbar_shift=0.0, beta_scale=1.0,
                  omega_scale=1.0, D_shift=0.0, vy_override=None, ell_override=None,
                  X_override=None, sub_include=True):
    """组装参数字典。rho_scale 缩放 Ω 与 λ（风险强度 ρ）; beta_scale 缩放安全参数 π。"""
    sp = cfg["structural_params"]
    src = mc.load_sources()
    p_vec = src.landed_cost_cny_t.to_numpy(float) + pbar_shift
    Om = mc.build_omega(src.disrupt_prob_annual, src.disrupt_severity) * rho_scale
    ell = (ell_override if ell_override is not None
           else cfg["derived"]["ell_qty"] * sp.get("ell0_scale", 1.0)) * rho_scale
    D = cfg["demand"]["D_total"] + D_shift
    vy = vy_override if vy_override is not None else \
        float(cfg["prices"]["spread_dom_import_2024"])
    # C_Z(Z) = cz0·Z + cz1·Z + 0.5·cz2·Z²: cz0=替代蛋白自身资源成本（≈进口平价,
    # 替代只有在进口含风险溢价时才净增益）; cz1/cz2 为计划书 §4.1 的增量成本锚
    cz0, cz1, cz2 = 3650.0, 100.0, (800.0 - 100.0) / 900.0
    X = X_override if X_override is not None else sp["reserve_X"]
    # 来源年度可获得量上限(万吨): 巴西≈2024对华出口的96%(南美物流约束);
    # 美国≈2024×2(政策相依); 阿根廷/其他≈2024×2(出口能力约束, USDA口径)
    m_cap = np.array([7200.0, 4427.0, 820.0, 830.0])
    return dict(p_vec=p_vec, Om=Om, ell=ell, D=D, vy=vy, cz0=cz0, cz1=cz1, cz2=cz2,
                pi=sp["crisis_prob_pi"] * beta_scale, kappa=sp["crisis_import_loss_kappa"],
                chi=sp["mobilization_chi"], X=X, m_cap=m_cap, beta_sec=1.0,
                eta=sp["eta_chain"], eps_phi=sp["eps_phi_curvature"], sc=sc,
                omega_scale=omega_scale,
                Y_min=cfg["demand"].get("Y_min_food", 1100.0))


def welfare_parts(x, P):
    """x = [Y, m1..m4, Z, K, H] -> (W, 明细)。"""
    Y, m, Z, K, H = x[0], x[1:5], x[5], x[6], x[7]
    M = float(np.sum(m))
    sc = P["sc"]
    supply_cost = sc.cost_integral(Y) * P.get("omega_scale", 1.0)
    import_cost = float(m @ P["p_vec"]) * U
    risk = mc.R_risk(m, P["Om"], P["ell"])
    # λ_B = β·ℓ: β 为安全政治权重（定理4.4 的安全参数），由 calibrate_beta 揭示
    B = mc.B_security(Y, P["pi"], P["beta_sec"] * P["ell"], P["chi"], P["kappa"], M, P["X"])
    quality = P["vy"] * Y * U
    G = mc.ces_G(Y + M, K, H, eta=P["eta"])
    # Φ(G)=phi0·G^0.9, phi0 校准: 基线 G0 处 Φ'·G_Y ≈ 300 元/吨 → phi0 = 300*U/ (0.9*G0^-0.1*G_Y)
    phi0 = P.get("phi0", 0.02)
    Phi = phi0 * G ** 0.9
    F = 0.5 * (P.get("fk", 2e-6) * K ** 2 + P.get("fh", 2e-6) * H ** 2)
    CZ = (0.5 * P["cz2"] * Z ** 2 + (P["cz0"] + P["cz1"]) * Z) * U
    W, parts = mc.welfare(dict(supply_cost=supply_cost, import_cost=import_cost,
                               risk_R=risk, B_security=B, quality_V=quality,
                               Phi_G=Phi, F_invest=F, C_Z=CZ))
    parts.update(Y=Y, M=M, Z=Z, K=K, H=H, G=G)
    return W, parts


def calibrate_chain(cfg, P, Y0=2090.5, M0=9410.0, K0=9500.0, H0=9500.0):
    """校准 phi0/fk/fh: 基线处 Φ'·G_Y ≈ 300 元/吨, 且 K,H 的 FOC 在 K0,H0 处成立。"""
    eta = P["eta"]
    G0 = mc.ces_G(Y0 + M0, K0, H0, eta=eta)
    h = 1.0
    G_Y = (mc.ces_G(Y0 + M0 + h, K0, H0, eta=eta) - G0) / h
    G_K = (mc.ces_G(Y0 + M0, K0 + h, H0, eta=eta) - G0) / h
    G_H = (mc.ces_G(Y0 + M0, K0, H0 + h, eta=eta) - G0) / h
    phi0 = 300.0 * U / (0.9 * G0 ** (-0.1) * G_Y)
    fk = phi0 * 0.9 * G0 ** (-0.1) * G_K / K0
    fh = phi0 * 0.9 * G0 ** (-0.1) * G_H / H0
    P.update(phi0=phi0, fk=fk, fh=fh)
    return P


def solve(P, x0=None):
    D = P["D"]
    if x0 is None:
        x0 = np.array([2000.0, D * 0.55, D * 0.16, D * 0.03, D * 0.03, 900.0, 9500.0, 9500.0])
    cons = [{"type": "eq", "fun": lambda x: x[0] + x[1:5].sum() + x[5] - D}]
    cap = P["m_cap"]
    # Y 下界 = 食用需求底部(进口不可替代的非转基因食用豆, 2015 实测底部 1179)
    y_lo = float(P.get("Y_min", 1100.0))
    bounds = [(y_lo, P["sc"].total_capacity)] + \
             [(0.0, float(cap[j])) for j in range(4)] + \
             [(0.0, 2500.0), (1000.0, 25000.0), (1000.0, 25000.0)]
    res = minimize(lambda x: -welfare_parts(x, P)[0], x0, method="SLSQP",
                   bounds=bounds, constraints=cons,
                   options=dict(maxiter=500, ftol=1e-10))
    W, parts = welfare_parts(res.x, P)
    parts["kkt_ok"] = bool(res.success)
    parts["x"] = res.x
    return parts


def comparative_statics(cfg, sc, base_parts, beta_sec=1.0, rel=0.10):
    """∂Y*/∂{ρ, p̄, β, ω, D} 数值符号与弹性（命题5.3）。"""
    rows = []
    shifts = dict(rho=dict(rho_scale=1 + rel), pbar=dict(pbar_shift=365.0),
                  beta=dict(beta_scale=1 + rel), omega=dict(omega_scale=1 + rel),
                  D=dict(D_shift=cfg["demand"]["D_total"] * rel))
    expected = dict(rho=+1, pbar=+1, beta=+1, omega=-1, D=+1)
    Y0 = base_parts["Y"]
    for k, kw in shifts.items():
        P = calibrate_chain(cfg, build_problem(cfg, sc, **kw))
        P["beta_sec"] = beta_sec
        parts = solve(P, x0=base_parts["x"])
        dY = parts["Y"] - Y0
        elas = (dY / Y0) / rel
        sign = int(np.sign(round(dY, 2))) if abs(dY) > 0.5 else 0
        ok = sign == expected[k] or sign == 0  # 平坦区容忍0
        rows.append(dict(param=k, dY=round(dY, 1), elasticity=round(elas, 4),
                         sign=sign, expected=expected[k], match=ok))
    return pd.DataFrame(rows)


def calibrate_beta(cfg, sc, Y_target=None, tol=0.01):
    """校准安全政治权重 β（定理4.4 安全参数）: 使规划解 Y* = 观测 Y_2025。
    这是计划书 §4.1 揭示性楔子的结构化利用——现行"价格+补贴"体制隐含的
    安全边际估值 = 使观测规模成为最优所需的 β·ℓ。返回 (β, P, base_parts)。"""
    Y_target = Y_target or cfg["supply_domestic"]["Y_2025"]
    lo, hi = 1.0, 3000.0
    P = base = None
    for _ in range(40):
        beta = np.sqrt(lo * hi)
        P = calibrate_chain(cfg, build_problem(cfg, sc))
        P["beta_sec"] = beta
        base = solve(P)
        if abs(base["Y"] - Y_target) / Y_target < tol:
            break
        if base["Y"] < Y_target:
            lo = beta
        else:
            hi = beta
    return P["beta_sec"], P, base


def run(cfg=None, save=True, fast=False):
    cfg = cfg or mc.load_cfg()
    sc, cost_scale, target_incentive = calibrate_supply(cfg)
    beta_sec, P, base = calibrate_beta(cfg, sc)
    print(f"[M1校准] 揭示安全权重 β = {beta_sec:.1f} (λ_B = β·ℓ = {beta_sec*P['ell']:.5f} 亿元/万吨²)")
    Y_star, M_star = base["Y"], base["M"]

    # 揭示性楔子诊断
    p_bar = float(mc.load_sources().landed_cost_cny_t.to_numpy().mean())
    wedge_revealed = sc.MC(cfg["supply_domestic"]["Y_2025"]) - p_bar
    h = 5.0
    Wp = welfare_parts(np.r_[base["x"][0] + h, base["x"][1:]], P)[1]
    dBdY = (Wp["B_security"] - base["B_security"]) / h / U          # 元/吨
    dVdY = P["vy"]
    dPhidY = (Wp["Phi_G"] - base["Phi_G"]) / h / U
    wedge_model = dBdY + dVdY + dPhidY
    ratio = wedge_model / wedge_revealed

    obs = dict(Y=cfg["supply_domestic"]["Y_2025"], M=cfg["imports_2024"]["M_total"],
               spread=cfg["prices"]["spread_dom_import_2024"])
    fit = pd.DataFrame([
        dict(indicator="Y 国产产量(万吨)", model=round(Y_star, 1), observed=obs["Y"],
             dev_pct=round(100 * (Y_star / obs["Y"] - 1), 2)),
        dict(indicator="M 进口量(万吨)", model=round(M_star, 1), observed=obs["M"],
             dev_pct=round(100 * (M_star / obs["M"] - 1), 2)),
        dict(indicator="Z 替代蛋白(万吨)", model=round(base["Z"], 1), observed=900, dev_pct=None),
        dict(indicator="MC(Y*) 边际成本(元/吨)", model=round(float(sc.MC(Y_star)), 0),
             observed=round(target_incentive, 0), dev_pct=None),
        dict(indicator="揭示楔子(元/吨)", model=round(wedge_model, 0),
             observed=round(wedge_revealed, 0), dev_pct=round(100 * (ratio - 1), 1)),
    ])

    cs = comparative_statics(cfg, sc, base, beta_sec=beta_sec,
                             rel=0.10 if not fast else 0.15)
    if not cs.match.all():
        print("[M1警告] 比较静态符号不符:\n", cs[~cs.match])

    res = dict(Y_star=Y_star, M_star=M_star, Z_star=base["Z"], welfare=base["welfare"],
               parts={k: base[k] for k in ["supply_cost", "import_cost", "risk_R",
                                            "B_security", "quality_V", "Phi_G",
                                            "F_invest", "C_Z"]},
               wedge_model=wedge_model, wedge_revealed=wedge_revealed,
               wedge_ratio=ratio, cost_scale=cost_scale, beta_sec=beta_sec,
               fit=fit, cs=cs, sc=sc, P=P, x=base["x"])
    if save:
        fit.to_csv(ROOT / "results/tables/T1_baseline_fit.csv", index=False)
        cs.to_csv(ROOT / "results/tables/T2_comparative_statics.csv", index=False)
        _write_derived(dict(cost_scale=float(round(cost_scale, 4)),
                            beta_security=float(round(beta_sec, 2)),
                            Y_star=float(round(Y_star, 1))))
        _figures(cfg, res)
    return res


def _write_derived(kv):
    import yaml
    cfg_path = ROOT / "config/calibration.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        full = yaml.safe_load(f)
    full.setdefault("derived", {}).update(kv)
    text = yaml.safe_dump(full, allow_unicode=True, sort_keys=False)
    tmp = cfg_path.with_suffix(".yaml.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(cfg_path)


def _figures(cfg, res):
    plt = mc.setup_cjk()
    sc = res["sc"]
    p_bar = float(mc.load_sources().landed_cost_cny_t.to_numpy().mean())
    Y_obs = cfg["supply_domestic"]["Y_2025"]
    # F1 优序供给曲线
    fig, ax = plt.subplots(figsize=(8, 5))
    yy = np.linspace(0, min(sc.total_capacity, 4000), 400)
    ax.plot(yy, sc.MC(yy), lw=2, color="#8c1f28", label="优序供给 MC(Y) 全成本口径")
    ax.axhline(p_bar, ls="--", color="#2b6a99", label=f"进口平价 {p_bar:.0f} 元/吨")
    ax.axvline(res["Y_star"], ls=":", color="k", label=f"Y* = {res['Y_star']:.0f} 万吨")
    ax.axvline(Y_obs, ls="-.", color="gray", label=f"2025 实测 {Y_obs:.0f} 万吨")
    shadow = sc.MC(res["Y_star"])
    ax.axhline(shadow, ls=":", color="#c07a26", label=f"影子价格 {shadow:.0f} 元/吨")
    ax.set_xlabel("国产大豆产量 Y (万吨)"); ax.set_ylabel("边际成本 (元/吨)")
    ax.set_title("优序供给曲线与社会最优规模 (M1)"); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(ROOT / "results/figures/F1_merit_supply.png", dpi=300)
    plt.close(fig)
    # F2 Y* vs 风险强度 ρ
    rhos = np.linspace(0.2, 3.0, 8)
    Ys = []
    for r in rhos:
        P = calibrate_chain(cfg, build_problem(cfg, sc, rho_scale=float(r)))
        P["beta_sec"] = res["beta_sec"]
        Ys.append(solve(P, x0=res["x"])["Y"])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(rhos, Ys, "o-", color="#8c1f28")
    ax.set_xlabel("风险强度 ρ (基线=1)"); ax.set_ylabel("Y* (万吨)")
    ax.set_title("最优国产规模对进口风险强度的响应")
    fig.tight_layout(); fig.savefig(ROOT / "results/figures/F2_Ystar_vs_rho.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    r = run()
    print(r["fit"].to_string(index=False))
    print(r["cs"].to_string(index=False))
    print(f"W={r['welfare']:.1f} 亿元, 楔子比={r['wedge_ratio']:.3f}")
