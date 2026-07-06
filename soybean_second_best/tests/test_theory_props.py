"""理论性质单元测试（§3 挂钩 + M6 快速档）。pytest -q < 5 分钟。"""
import numpy as np
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import model_core as mc


@pytest.fixture(scope="module")
def cfg():
    return mc.load_cfg()


@pytest.fixture(scope="module")
def regions():
    return mc.validate_regions(mc.load_regions())


def test_merit_order_monotone(regions):
    sc = mc.merit_order_supply(regions)
    assert np.all(np.diff(sc.c_grid) >= -1e-9), "MC 必须单调不减"
    assert sc.total_capacity > 2000


def test_r_risk_mc_vs_analytic(cfg):
    """蒙特卡洛 vs copula 口径解析二阶矩, X=0 时误差 <1%。"""
    src = mc.load_sources()
    prob = src.disrupt_prob_annual.to_numpy(float)
    sev = src.disrupt_severity.to_numpy(float)
    m = src.volume_2024_wt.to_numpy(float)
    ell = 1e-4
    Om_cop = mc.omega_from_copula(prob, sev)
    analytic = 0.5 * ell * float(m @ Om_cop @ m)
    rng = np.random.default_rng(1)
    # 直接一期抽样（与 omega_from_copula 同过程）
    from scipy.stats import norm
    n = 400000
    k = len(m)
    C = np.full((k, k), 0.15); np.fill_diagonal(C, 1.0)
    z = rng.multivariate_normal(np.zeros(k), C, size=n)
    hit = norm.cdf(z) < prob[None, :]
    loss = (hit * sev[None, :]) @ m
    mc_val = 0.5 * ell * float(np.mean(loss ** 2))
    assert abs(mc_val - analytic) / analytic < 0.01


def test_ces_min_limit():
    x = (2000.0, 9000.0, 11000.0)
    g = mc.ces_G(*x, eta=1e-4)
    assert abs(g - min(x)) / min(x) < 0.02


def test_b_security_shape(cfg):
    sp = cfg["structural_params"]
    lam = 0.01
    args = dict(pi=0.05, lam=lam, chi=0.15, kappa=0.3, M=9500.0, X=1000.0)
    b1 = mc.B_security(1500.0, **args)
    b2 = mc.B_security(2500.0, **args)
    assert 0 <= b1 < b2, "B 随 Y 单调增"


def test_feed_elasticity():
    Pf, sS = mc.feed_unit_cost(3400.0, 2800.0, alpha=0.13, eps=0.9)
    sig = mc.derived_demand_elasticity(sS, 0.9, 0.5)
    assert 0 < sS < 0.3 and 0.3 < sig < 1.0


def test_m2_analytic_vs_qp(cfg):
    from src import m2_portfolio as m2
    src = mc.load_sources()
    p = src.landed_cost_cny_t.to_numpy(float)
    Om = mc.build_omega(src.disrupt_prob_annual, src.disrupt_severity)
    ell = cfg["derived"]["ell_qty"]
    s_an = m2.analytic_shares(p, Om, ell, 9580.0)
    s_qp = m2.qp_shares(p, Om, ell, 9580.0)
    assert np.abs(s_an - s_qp).max() < 1e-5


def test_m4_convergence(cfg):
    from src.m4_abm import aggregate_supply_curve
    prices, ya, ym, cap = aggregate_supply_curve(cfg, tau=5.0)
    l1 = float(np.trapezoid(np.abs(ya - ym), prices)
               / max(np.trapezoid(ym, prices), 1e-9))
    assert l1 < 0.05


def test_m3_ell_positive(cfg):
    d = cfg.get("derived", {})
    assert d.get("ell_qty", 0) > 0
    assert 0 < d.get("Lambda_food", 0) < 0.2
