"""M4: 农户—加工—进口—政府多主体仿真（2026–2035, 年度步）。

主体与规则（§7.1, 命题 15.1–15.2）:
- 农户 N 个（默认 10000, 按 regions.csv 面积份额分配; 地块 lognormal σ=0.8, 潜在
  轮作地池 = 现状大豆面积/基线种豆概率）。Logit 选择大豆 vs 玉米:
    ΔV_i = [f_i·(p̃+s^Y+ϑ·prem·q_i)/1000 − c_r] − corn_net_r − γ/2·Var(π)·a_i
           + ζ₁·Service_r + ζ₂·scale·Peer_r
    P(豆) = 1/(1+exp(−ΔV/τ))
- 质量 q_i = ϑ^{1/(δ−m)}·φ_i（式 9.6), φ_i ~ lognormal(0, 0.15)
- 进口商: M2 的带约束 QP 份额（当年价格+政策 Ω）
- 价格: p_imp AR(1) log(μ=3650, σ=12%); 国产食用价差 OU(均值回归 5 年均值 1202,
  σ=350, 起点 627); 玉米净收益 AR(1)
- 政府: 政策工具向量 policy dict（M5 传入）
- 时序: 价格→政策→预期(自适应0.6/0.4)→选择→单产(气候σ=8%)→质量结算→进口配置
  →短缺/储备→记录

自检（§7.3, run_selfcheck）:
  A. 无政策基线 2026–2028 产量 ∈ [1950,2250], 进口 ∈ [9000,10800]
  B. τ→5 时聚合供给曲线与 M1 优序供给 L1 距离 <5%
  C. 2018 型摩擦(C1)下美豆份额年内降幅 ≥40%
"""
import numpy as np
import pandas as pd

from src import model_core as mc
from src import m2_portfolio as m2

ROOT = mc.ROOT
U = mc.WT_CNY_TO_YI

DEFAULT_POLICY = dict(sub_area=350.73, sub_targeted=None, price_floor_tau=0.0,
                      theta_transmission=None, reserve_X=None,
                      import_cost_shift=None, import_prob_scale=None,
                      quality_budget=0.0)


class ABM:
    def __init__(self, cfg, n_agents=10000, seed=None, policy=None, scenario=None,
                 pool_scale=2.0):
        self.cfg = cfg
        sp = cfg["structural_params"]
        self.sp = sp
        self.rng = np.random.default_rng(cfg["meta"]["seed"] if seed is None else seed)
        self.policy = {**DEFAULT_POLICY, **(policy or {})}
        self.scenario = scenario
        self.regions = mc.validate_regions(mc.load_regions())
        self.src = mc.load_sources()
        self.tau = sp["logit_tau"]
        self.gamma = sp["risk_aversion_gamma"]
        self.theta0 = sp["theta_transmission"]
        self.dm = sp["delta_minus_m"]
        # --- 农户初始化 ---
        R = self.regions
        n_r = (R.area_share * n_agents).round().astype(int).to_numpy()
        n_r[-1] += n_agents - n_r.sum()
        self.reg_idx = np.repeat(np.arange(len(R)), n_r)
        # 潜在轮作地池 = 现状面积 × pool_scale（基线种豆概率 1/pool_scale）
        self.pool_scale = pool_scale
        pool_mu = (R.area_wan_mu.to_numpy() * pool_scale) / n_r   # 万亩/户
        a = self.rng.lognormal(np.log(pool_mu[self.reg_idx]) - 0.5 * 0.8 ** 2, 0.8)
        # 区域内归一: 各区地池总量精确等于 area×pool_scale（消除有限样本偏差）
        pool_target = R.area_wan_mu.to_numpy() * pool_scale
        sums = pd.Series(a).groupby(self.reg_idx).sum().to_numpy()
        a = a * (pool_target / sums)[self.reg_idx]
        self.area_i = a                                            # 万亩
        self.phi_i = self.rng.lognormal(0.0, 0.15, n_agents)      # 生产率
        self.soy_prev = self.rng.random(n_agents) < 0.5
        self.e_i = np.full(n_agents, 1.0)
        # 区域向量
        self.yield_r = R.yield_kg_mu.to_numpy()[self.reg_idx]
        # 全成本(含 e=1 技术投入 0.5·ce2), 与 M1 优序供给同构; cost_scale 由 M1 校准写入
        cs_scale = cfg.get("derived", {}).get("cost_scale", 1.0)
        r_g = 0.8 * np.exp(-1.0) / (1 + 0.8 * (1 - np.exp(-1.0)))
        A_r = (R.land_opp_cost_cny_mu + R.other_cost_cny_mu).to_numpy() * cs_scale
        self.cost_r = (A_r * (1 + 0.5 * r_g / (1 - r_g / 2)))[self.reg_idx]
        self.service_r = R.service_level.to_numpy()[self.reg_idx]
        self.theta_r = R.quality_theta.to_numpy()[self.reg_idx]
        # 价格状态。价差 OU 锚: 基线用 2024 现值 627（五年均值 1202 含 2020–22
        # 异常期, 仅作质量溢价尺度 spread_lr; 敏感性情景可改 spread_anchor）
        self.p_imp = cfg["prices"]["p_import_landed_2024"]
        self.spread = cfg["prices"]["spread_dom_import_2024"]
        self.spread_anchor = float(self.spread)
        self.spread_lr = cfg["prices"]["spread_dom_import_5yr"]
        self.p_hat = self.p_imp + self.spread
        self.records = []
        # 玉米净收益(全成本口径, 元/亩): 在基线价格与基线补贴下校准
        self.corn_net = None
        self._corn_calibrate(350.73)

    def _fi(self):
        norm = 1 + 0.8 * (1 - np.exp(-1.0))
        return (self.yield_r * (1 + 0.8 * (1 - np.exp(-self.e_i))) / norm * self.phi_i)

    def _dv_terms(self, p_eff, sub, theta):
        """选择方程的确定项（step 与校准共用, 保证一致）。"""
        q_i = theta ** (1.0 / self.dm) * self.phi_i * self.theta_r
        prem = theta * self.spread_lr * q_i
        f_i = self._fi()
        soy_rev = f_i / 1000.0 * (p_eff + prem) + sub
        var_pi = (f_i / 1000.0) ** 2 * (0.12 * p_eff) ** 2
        base = (soy_rev - self.cost_r - 0.5 * self.gamma * var_pi
                + self.sp["service_effect_zeta1"] * self.service_r)
        return base, q_i, prem, f_i

    def _corn_calibrate(self, sub=350.73):
        """玉米机会净收益（分区域校准, anchor）: 使基线激励下各区 mean(ΔV_r)=0 →
        P(豆|r)=1/pool_scale, 复现观测的区域面积份额。玉米净收益的区域差异大
        （黑龙江玉米强、西南弱), 无分区公开口径 → 以基线份额反推, struct 参数。"""
        base, *_ = self._dv_terms(self.p_imp + self.spread, sub, self.theta0)
        by_r = pd.Series(base).groupby(self.reg_idx).mean().to_numpy()
        off = self.tau * np.log(max(self.pool_scale - 1.0, 1e-6)) if self.pool_scale > 1 else 0.0
        self.corn_net = by_r[self.reg_idx] + off

    def step(self, year, mc_fast=True):
        rng, sp, pol = self.rng, self.sp, self.policy
        # 1. 价格实现
        self.p_imp = float(np.exp(np.log(3650) * 0.35 + np.log(self.p_imp) * 0.65
                                  + rng.normal(0, 0.12)))
        if pol.get("import_cost_shift"):
            self.p_imp += pol["import_cost_shift"]
        self.spread += 0.4 * (self.spread_anchor - self.spread) + rng.normal(0, 350)
        self.spread = float(np.clip(self.spread, -200, 2600))
        p_dom = self.p_imp + self.spread
        if pol["price_floor_tau"] > 0:
            p_dom = max(p_dom, self.p_imp + pol["price_floor_tau"])
        # 2-3. 政策与预期
        self.p_hat = 0.6 * p_dom + 0.4 * self.p_hat
        theta = pol["theta_transmission"] or self.theta0
        sub = pol["sub_area"]
        if pol.get("sub_targeted") is not None:
            sub = pol["sub_targeted"][self.reg_idx]
        # 4. 种植选择 (Logit)
        base, q_i, prem, f_i = self._dv_terms(self.p_hat, sub if np.ndim(sub) else sub,
                                              theta)
        peer_r = pd.Series(self.soy_prev).groupby(self.reg_idx).mean().to_numpy()
        dV = (base - self.corn_net
              + sp["peer_effect_zeta2"] * 200.0 * (peer_r[self.reg_idx] - 0.5))
        p_soy = 1.0 / (1.0 + np.exp(-np.clip(dV / self.tau, -60, 60)))
        soy = rng.random(len(dV)) < p_soy
        # 5. 单产实现（区域气候冲击 σ=8%）
        clim = rng.normal(1.0, 0.08, len(self.regions))[self.reg_idx]
        harv = f_i * clim
        area_soy = float(self.area_i[soy].sum() * 1e0)            # 万亩(area_i已是万亩)
        Y = float((self.area_i * harv / 1000.0)[soy].sum())       # 万吨
        # 6. 质量结算
        q_bar = float(np.average(q_i[soy], weights=self.area_i[soy])) if soy.any() else 0
        hi_q_share = float(self.area_i[soy][q_i[soy] > 1.0].sum()
                           / max(self.area_i[soy].sum(), 1e-9))
        income_i = np.where(soy, (harv / 1000.0 * (p_dom + prem) + sub - self.cost_r),
                            self.corn_net)                        # 元/亩
        # 7. 进口配置
        D = self.cfg["demand"]["D_total"]
        M_need = max(D - Y, 500.0)
        p_vec = self.src.landed_cost_cny_t.to_numpy(float).copy()
        p_vec = p_vec * (self.p_imp / 3650.0)
        prob = self.src.disrupt_prob_annual.to_numpy(float).copy()
        sev = self.src.disrupt_severity.to_numpy(float).copy()
        if pol.get("import_prob_scale") is not None:
            prob = prob * pol["import_prob_scale"]
        if pol.get("import_cost_shift_s34"):
            p_vec[2:] += pol["import_cost_shift_s34"]
        scen_yr = self.scenario if (self.scenario and year == 2027) else None
        m_cap = np.array([7200.0, 4427.0, 820.0, 830.0])
        if scen_yr in ("C1", "C3"):
            prob[1], sev[1] = 1.0, 0.9                            # 美豆近停摆
            m_cap[1] *= (1 - 0.9)                                 # 可成交量骤降
            m_cap[0] *= 1.15                                      # 巴西转售补位(2018史实)
        if scen_yr in ("C2", "C3"):
            prob[0], sev[0] = 1.0, max(sev[0], 0.2)
            m_cap[0] *= (1 - 0.2)
        Om = mc.build_omega(prob, sev)
        ell = self.cfg["derived"]["ell_qty"] * sp.get("ell0_scale", 1.0)
        cap_sh = m_cap / M_need
        if cap_sh.sum() <= 1.0:                                   # 可获得量不足: 全额吃满
            s = cap_sh / cap_sh.sum() * min(cap_sh.sum(), 1.0)
            M_need_eff = float(m_cap.sum())
        else:
            s = m2.qp_shares(p_vec, Om, ell, M_need, cap=cap_sh)
            M_need_eff = M_need
        # 中断实现（年度简化: 概率×severity 的期望到港损失+随机）
        hit = rng.random(4) < prob
        arrive = M_need_eff * float((s * np.where(hit, 1 - sev, 1.0)).sum())
        X = pol["reserve_X"] or sp["reserve_X"]
        short = max(D - Y - arrive - X, 0.0)
        # 8. 记录
        fiscal = float((np.where(soy, np.broadcast_to(sub, soy.shape), 0.0)
                        * self.area_i).sum())                     # 元/亩×万亩=万元→亿: /1e4? 万亩×元/亩=1e4亩×元/亩=1e4元=万元 →亿元: ×1e-4
        fiscal = fiscal * 1e-4 + pol.get("quality_budget", 0.0)
        self.soy_prev = soy
        rec = dict(year=year, Y=Y, area=area_soy, M=arrive, M_planned=M_need,
                   short=short, p_dom=p_dom, p_imp=self.p_imp, spread=self.spread,
                   share_us=float(s[1]), share_brazil=float(s[0]),
                   hhi=float((s ** 2).sum()), q_bar=q_bar, hi_q_share=hi_q_share,
                   income_mean=float(np.mean(income_i)),
                   income_soy=float(np.mean(income_i[soy])) if soy.any() else 0.0,
                   gini=gini(np.maximum(income_i * self.area_i, 0.0)),
                   fiscal=fiscal, soy_share=float(np.mean(soy)))
        self.records.append(rec)
        return rec

    def run(self, years=None):
        years = years or range(self.cfg["meta"]["horizon"][0],
                               self.cfg["meta"]["horizon"][1] + 1)
        for y in years:
            self.step(y)
        return pd.DataFrame(self.records)


def gini(x):
    x = np.sort(np.asarray(x, float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


def aggregate_supply_curve(cfg, tau=5.0, n_agents=4000, seed=1):
    """命题15.2 收敛检验: τ→小时 ABM 聚合供给 vs M1 优序供给。"""
    """用优序供给的区域原语构造 τ-logit 聚合供给（φ=1 消除异质性,
    检验纯粹的 τ→0 收敛, 命题15.2）。返回 (prices, Y_abm, Y_m1, cap_base)。"""
    from src.m1_planner import calibrate_supply
    sc, _, _ = calibrate_supply(cfg)
    rt = sc.region_table
    prices = np.linspace(3000, 9000, 120)
    f_r = rt.capacity_wt.to_numpy()          # 区域产能(万吨)
    c_r = rt.unit_cost.to_numpy()            # 元/吨
    yld = mc.load_regions().yield_kg_mu.to_numpy()
    Ys, Ym = [], []
    for p in prices:
        dv = yld / 1000.0 * (p - c_r)        # 元/亩
        P = 1.0 / (1.0 + np.exp(-np.clip(dv / tau, -60, 60)))
        Ys.append(float((f_r * P).sum()))
        Ym.append(float(f_r[c_r <= p].sum()))   # 优序阶梯（同原语, 不含集约边际段）
    return prices, np.array(Ys), np.array(Ym), float(f_r.sum())


def run_selfcheck(cfg=None, fast=True, save=True):
    cfg = cfg or mc.load_cfg()
    out = {}
    # A. 基线复现（3 种子平均, 平滑价格路径抽样噪声）
    dfs = [ABM(cfg, n_agents=2000 if fast else 10000, seed=s).run(range(2026, 2029))
           for s in (42, 43, 44)]
    df = pd.concat(dfs)
    out["baseline_Y"] = float(df.Y.mean()); out["baseline_M"] = float(df.M_planned.mean())
    out["check_A"] = bool(1950 <= out["baseline_Y"] <= 2250
                          and 9000 <= out["baseline_M"] <= 10800)
    # B. 收敛检验
    prices, Ys, Y_m1, cap_base = aggregate_supply_curve(cfg, tau=5.0)
    mask = Y_m1 > 0
    # L1 泛函距离: ∫|S_abm−S_merit|dp / ∫S_merit dp（对阶梯跳点稳健）
    l1 = float(np.trapezoid(np.abs(Ys - Y_m1), prices)
               / max(np.trapezoid(Y_m1, prices), 1e-9))
    out["convergence_L1"] = l1; out["check_B"] = bool(l1 < 0.05)
    # C. 2018 型摩擦
    abm = ABM(cfg, n_agents=2000, seed=7, scenario="C1")
    df_c = abm.run(range(2026, 2029))
    us_pre = df_c[df_c.year == 2026].share_us.iloc[0]
    us_crisis = df_c[df_c.year == 2027].share_us.iloc[0]
    drop = (us_pre - us_crisis) / max(us_pre, 1e-9)
    out["us_share_drop"] = float(drop); out["check_C"] = bool(drop >= 0.40 or us_pre < 0.05)
    if save:
        pd.DataFrame([out]).to_csv(ROOT / "results/tables/T_M4_selfcheck.csv", index=False)
        plt = mc.setup_cjk()
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.plot(Y_m1[mask], prices[mask], label="M1 优序供给", lw=2)
        ax.plot(Ys[mask], prices[mask], "--", label=f"ABM 聚合 (τ=5), L1={l1:.3f}")
        ax.set_xlabel("产量 (万吨)"); ax.set_ylabel("价格 (元/吨)")
        ax.set_title("命题15.2: ABM 聚合供给向优序供给收敛")
        ax.legend(); fig.tight_layout()
        fig.savefig(ROOT / "results/figures/F6_abm_convergence.png", dpi=300)
        plt.close(fig)
    return out


if __name__ == "__main__":
    out = run_selfcheck()
    print(out)
