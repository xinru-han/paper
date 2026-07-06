"""共享经济学函数（理论文档公式实现）。

单位约定: 产量/贸易量=万吨; 面积=万亩; 单价=元/吨; 每亩量=元/亩或公斤/亩; 福利=亿元。
换算: 1 万吨 × 1 元/吨 = 1e4 元 = 1e-4 亿元 → WT_CNY_TO_YI = 1e-4。
"""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
WT_CNY_TO_YI = 1e-4          # 万吨×元/吨 -> 亿元
MU_PER_HA = 15.0


def load_cfg():
    with open(ROOT / "config/calibration.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_regions():
    return pd.read_csv(ROOT / "data/regions.csv")


def load_sources():
    return pd.read_csv(ROOT / "data/import_sources.csv")


def setup_cjk():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "Noto Sans CJK JP",
                                       "Noto Serif CJK SC", "Noto Serif CJK JP", "SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


# ---------------------------------------------------------------- 优序供给
@dataclass
class SupplyCurve:
    """引理4.2 优序供给曲线。c_grid/y_grid: 累计产量(万吨)对应边际成本(元/吨)。"""
    y_grid: np.ndarray
    c_grid: np.ndarray
    total_capacity: float
    region_table: pd.DataFrame

    def MC(self, Y):
        return np.interp(np.asarray(Y, float), self.y_grid, self.c_grid)

    def inverse(self, p):
        return float(np.interp(p, self.c_grid, self.y_grid))

    def cost_integral(self, Y):
        """总供给成本 ∫0^Y MC dy, 亿元。"""
        Y = float(Y)
        yg = np.append(self.y_grid[self.y_grid < Y], Y)
        cg = self.MC(yg)
        return float(np.trapezoid(cg, yg)) * WT_CNY_TO_YI


def merit_order_supply(regions_df, cost_scale=1.0, ext_grid=2.0, n_ext=60) -> SupplyCurve:
    """引理4.2: 由区域数据构造优序供给曲线（全成本口径, 元/吨）。

    每区: f_r(e) = yield_base*(1+0.8*(1-exp(-e)))  (f'>0, f''<0)
          c_e(e) = 0.5*ce2*e^2, ce2 校准使 e=1 的技术投入成本 ≈ other_cost 的 60%
          u_r(e) = (land_opp + other + c_e(e)) / f_r(e)   → 求 e† 最小化
    产能内: 该区在 c†_r 处供给 area*f(e†); 按 c† 升序累积成阶梯。
    超产能: 沿集约边际 c_e'(e)/f'(e) 上升（式4.5), 用 e ∈ [e†, e†+ext_grid] 细分。
    cost_scale: 校准旋钮, 整体缩放成本梯度（M1 一致性检验用）。
    """
    from scipy.optimize import minimize_scalar
    segs = []  # (mc, dY) 段
    rows = []
    for _, r in regions_df.iterrows():
        base = r.yield_kg_mu
        land, other = r.land_opp_cost_cny_mu * cost_scale, r.other_cost_cny_mu * cost_scale
        # ce2 校准使 e†=1（观测技术水平满足 FOC c'(1)=u(1)·f'(1)）:
        #   r_g = g'(1)/g(1), ce2 = (land+other)·r_g/(1−r_g/2)
        r_g = 0.8 * np.exp(-1.0) / (1 + 0.8 * (1 - np.exp(-1.0)))
        ce2 = (land + other) * r_g / (1 - r_g / 2)

        norm = 1 + 0.8 * (1 - np.exp(-1.0))   # f(1)=观测单产（e=1 为现状技术水平）

        def f(e):
            return base * (1 + 0.8 * (1 - np.exp(-e))) / norm

        def unit_cost(e):  # 元/吨 = 元/亩 / (吨/亩)
            return (land + other + 0.5 * ce2 * e ** 2) / (f(e) / 1000.0)

        res = minimize_scalar(unit_cost, bounds=(0.5, 3.0), method="bounded")
        e_d, c_d = res.x, res.fun
        cap = r.area_wan_mu * f(e_d) / 1000.0  # 万亩 × kg/亩 ÷ 1000 = 万吨 (15487.5×133.35→2065)
        segs.append((c_d, cap, r.region_id))
        rows.append(dict(region_id=r.region_id, name=r["name"], e_opt=e_d,
                         unit_cost=c_d, capacity_wt=cap))
        # 扩展段 = 粗放边际(轮作地池扩面, 土地机会成本沿 c†→1.6c† 线性上升,
        # 额外产能 = 现有产能×1.0, 与 ABM pool_scale=2 同口径) + 少量集约边际
        n_seg = 24
        for k in range(1, n_seg + 1):
            mc_k = c_d * (1 + 0.6 * k / n_seg)
            segs.append((mc_k, cap / n_seg, r.region_id))
    segs.sort(key=lambda s: s[0])
    y = np.cumsum([s[1] for s in segs])
    c = np.array([s[0] for s in segs])
    y = np.insert(y, 0, 0.0); c = np.insert(c, 0, c[0])
    return SupplyCurve(y, c, float(y[-1]), pd.DataFrame(rows))


def validate_regions(regions_df, target_low=2065.0, target_high=2090.5, tol=0.03):
    """校验 sum(area*yield) 落在观测产量带内, 偏差>3% 按比例调 yield 并报告。"""
    prod = (regions_df.area_wan_mu * regions_df.yield_kg_mu).sum() / 1000.0
    target = 0.5 * (target_low + target_high)
    if abs(prod - target) / target > tol:
        k = target / prod
        regions_df = regions_df.copy()
        regions_df["yield_kg_mu"] *= k
        print(f"[validate_regions] 基础单产合计 {prod:.1f} 万吨偏离目标 {target:.1f}, yield×{k:.4f}")
    return regions_df


# ---------------------------------------------------------------- 安全与风险
def B_security(Y, pi, lam, chi, kappa, M, X):
    """式3.4: B(Y) = 0.5·π·λ·[((κM−X)_+)² − ((κM−X−χY)_+)²]，亿元。
    λ=ell（定义3.5 核算约定, 单位 亿元/万吨²）。Y,M,X 万吨。"""
    g1 = max(kappa * M - X, 0.0)
    g2 = max(kappa * M - X - chi * Y, 0.0)
    return 0.5 * pi * lam * (g1 ** 2 - g2 ** 2)


def R_risk(m_vec, Omega, ell, X=0.0, prob=None, sev=None, mc_draws=20000,
           rho_common=0.15, rng=None):
    """式2.2 进口中断风险成本(亿元)。X=0: 解析 0.5·ell·m'Ωm。
    X>0: 蒙特卡洛（需给 prob/sev 原始参数）计算 0.5·ell·E[((ξ'm−X)_+)²]。"""
    m = np.asarray(m_vec, float)
    if X <= 0:
        return 0.5 * ell * float(m @ Omega @ m)
    assert prob is not None and sev is not None, "X>0 需提供 prob/sev"
    return mc_shortfall(m, prob, sev, ell, X=X, n=mc_draws,
                        rho_common=rho_common, rng=rng)


def build_omega(prob, sev, rho_common=0.15):
    """§2.4: Ω[i,i]=p_i·sev_i²; Ω[i,j]=p_i·sev_i·p_j·sev_j·ρ (i≠j)。"""
    prob, sev = np.asarray(prob, float), np.asarray(sev, float)
    d = prob * sev
    Om = np.outer(d, d) * rho_common
    np.fill_diagonal(Om, prob * sev ** 2)
    return Om


def omega_from_copula(prob, sev, rho_common=0.15):
    """与 mc_shortfall 抽样过程严格一致的二阶矩矩阵 E[ξξ']:
    对角 p_i·sev_i²; 非对角 sev_i·sev_j·P(两源同时中断)（高斯 copula 双变量CDF）。
    用于单元测试对照; 解析规划(M1/M2)仍用计划书 §2.4 的 build_omega 情景设定。"""
    from scipy.stats import multivariate_normal, norm
    prob, sev = np.asarray(prob, float), np.asarray(sev, float)
    k = len(prob)
    Om = np.zeros((k, k))
    th = norm.ppf(prob)
    for i in range(k):
        Om[i, i] = prob[i] * sev[i] ** 2
        for j in range(i + 1, k):
            pj = multivariate_normal(mean=[0, 0], cov=[[1, rho_common], [rho_common, 1]]
                                     ).cdf([th[i], th[j]])
            Om[i, j] = Om[j, i] = sev[i] * sev[j] * pj
    return Om


def mc_shortfall(m_vec, prob, sev, ell, X=0.0, n=20000, rho_common=0.15, rng=None):
    """蒙特卡洛风险成本(亿元): 0.5·ell·E[((Σ ξ_j m_j − X)_+)²]，
    ξ_j = 中断指示·severity, 高斯 copula 相关 ρ_common。"""
    if rng is None:
        rng = np.random.default_rng(20260705)
    m = np.asarray(m_vec, float)
    k = len(m)
    C = np.full((k, k), rho_common); np.fill_diagonal(C, 1.0)
    z = rng.multivariate_normal(np.zeros(k), C, size=n)
    from scipy.stats import norm
    hit = norm.cdf(z) < np.asarray(prob)[None, :]
    loss = (hit * np.asarray(sev)[None, :]) @ m
    short = np.maximum(loss - X, 0.0)
    return 0.5 * ell * float(np.mean(short ** 2))


# ---------------------------------------------------------------- 链条与饲料
def ces_G(Y, K, H, alpha=(1 / 3, 1 / 3, 1 / 3), eta=0.5):
    """式2.3 链条 CES 聚合, rho=(eta-1)/eta; eta→0 退化为 min()。"""
    x = np.array([Y, K, H], float)
    a = np.asarray(alpha, float)
    if eta < 1e-3:
        return float(np.min(x))
    if abs(eta - 1.0) < 1e-9:
        return float(np.prod(x ** a))
    rho = (eta - 1.0) / eta
    return float((a @ np.maximum(x, 1e-12) ** rho) ** (1.0 / rho))


def feed_unit_cost(pS, pA, alpha=0.13, eps=0.9):
    """引理11.1: CES 饲料成本 P_f 与豆粕成本份额 s_S。
    P_f = [α·pS^(1−ε) + (1−α)·pA^(1−ε)]^(1/(1−ε))。"""
    if abs(eps - 1.0) < 1e-9:
        Pf = pS ** alpha * pA ** (1 - alpha)
    else:
        Pf = (alpha * pS ** (1 - eps) + (1 - alpha) * pA ** (1 - eps)) ** (1 / (1 - eps))
    sS = alpha * (pS / Pf) ** (1 - eps)
    return float(Pf), float(sS)


def derived_demand_elasticity(s_S, eps, eta_L):
    """命题11.2 (Hicks–Marshall): σ_D = (1−s_S)·ε + s_S·η_L。"""
    return (1 - s_S) * eps + s_S * eta_L


# ---------------------------------------------------------------- 福利核算
def welfare(components: dict):
    """式4.9 目标函数分项核算(亿元)。
    W = −供给成本 −进口支出 −风险 R + B + 质量 V + Φ(G) − F − C_Z − DWL
    返回 (W, 明细dict)。components 缺省项按 0 计。"""
    c = {k: components.get(k, 0.0) for k in
         ["supply_cost", "import_cost", "risk_R", "B_security", "quality_V",
          "Phi_G", "F_invest", "C_Z", "deadweight"]}
    W = (-c["supply_cost"] - c["import_cost"] - c["risk_R"] + c["B_security"]
         + c["quality_V"] + c["Phi_G"] - c["F_invest"] - c["C_Z"] - c["deadweight"])
    c["welfare"] = W
    return W, c
