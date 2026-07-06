"""大豆全产业链第二优均衡 — 交互式政策仿真网站。

HTTP Basic 认证; 端口 7070; 供 175.27.226.92:7070 对外访问。
交互模块: M1 规划求解 / M2 进口组合 / M3 网络冲击 / M5 政策 ABM。
"""
import base64
import functools
import io
import json
import sys
import threading
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, Response, jsonify, render_template, request, send_from_directory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import model_core as mc          # noqa: E402
from src import m1_planner as m1          # noqa: E402
from src import m2_portfolio as m2        # noqa: E402
from src import m3_network                # noqa: E402
from src.m4_abm import ABM                # noqa: E402
from src import m5_policy as m5           # noqa: E402

app = Flask(__name__)
USER, PASSWORD = "hanxinru", "Hxr!1989"
_lock = threading.Lock()
_state = {}


def check_auth(f):
    @functools.wraps(f)
    def w(*a, **kw):
        auth = request.authorization
        if not auth or auth.username != USER or auth.password != PASSWORD:
            return Response("认证失败", 401,
                            {"WWW-Authenticate": 'Basic realm="soybean-sim"'})
        return f(*a, **kw)
    return w


def get_state():
    """惰性初始化: 校准供给曲线与 β（首次请求 ~10s, 之后缓存）。"""
    with _lock:
        if "cfg" not in _state:
            cfg = mc.load_cfg()
            sc, cost_scale, target = m1.calibrate_supply(cfg)
            beta = cfg.get("derived", {}).get("beta_security")
            if beta is None:
                beta, _, _ = m1.calibrate_beta(cfg, sc)
            _state.update(cfg=cfg, sc=sc, beta=float(beta))
        return _state


@app.route("/")
@check_auth
def index():
    cfg = get_state()["cfg"]
    d = cfg.get("derived", {})
    figs = sorted(p.name for p in (ROOT / "results/figures").glob("*.png"))
    return render_template("index.html", derived=d, figs=figs)


@app.route("/figure/<name>")
@check_auth
def figure(name):
    return send_from_directory(ROOT / "results/figures", name)


@app.route("/static/<path:name>")
def static_file(name):
    return send_from_directory(Path(__file__).parent / "static", name)


@app.route("/report")
@check_auth
def report():
    f = ROOT / "results/REPORT.md"
    txt = f.read_text(encoding="utf-8") if f.exists() else "尚未生成，请先运行 run_all.py"
    return render_template("report.html", content=txt)


@app.route("/api/m1", methods=["POST"])
@check_auth
def api_m1():
    """M1 规划求解: 输入结构参数 → Y*, m*, 福利分项, 供给曲线。"""
    st = get_state()
    cfg, sc = st["cfg"], st["sc"]
    q = request.json or {}
    P = m1.build_problem(
        cfg, sc,
        rho_scale=float(q.get("rho_scale", 1.0)),
        pbar_shift=float(q.get("pbar_shift", 0.0)),
        D_shift=float(q.get("D_shift", 0.0)),
        vy_override=float(q["vy"]) if q.get("vy") else None,
        X_override=float(q["reserve_X"]) if q.get("reserve_X") else None,
        ell_override=cfg["derived"]["ell_qty"] * float(q.get("ell_scale", 1.0)))
    P["pi"] = float(q.get("pi", cfg["structural_params"]["crisis_prob_pi"]))
    P["kappa"] = float(q.get("kappa", cfg["structural_params"]["crisis_import_loss_kappa"]))
    P["chi"] = float(q.get("chi", cfg["structural_params"]["mobilization_chi"]))
    P = m1.calibrate_chain(cfg, P)
    P["beta_sec"] = float(q.get("beta", st["beta"]))
    with _lock:
        parts = m1.solve(P)
    yy = np.linspace(0, min(sc.total_capacity, 4200), 120)
    return jsonify(dict(
        Y_star=round(parts["Y"], 1), M_star=round(parts["M"], 1),
        Z_star=round(parts["Z"], 1), welfare=round(parts["welfare"], 1),
        MC_at_Y=round(float(sc.MC(parts["Y"])), 0),
        parts={k: round(parts[k], 1) for k in
               ["supply_cost", "import_cost", "risk_R", "B_security",
                "quality_V", "Phi_G", "F_invest", "C_Z"]},
        m_vec=[round(v, 1) for v in parts["x"][1:5]],
        curve=dict(y=yy.round(1).tolist(), mc=sc.MC(yy).round(0).tolist())))


@app.route("/api/m2", methods=["POST"])
@check_auth
def api_m2():
    """M2 组合: 输入风险参数 → 最优份额 + 情景 CVaR。"""
    st = get_state()
    cfg = st["cfg"]
    q = request.json or {}
    src = mc.load_sources()
    p = src.landed_cost_cny_t.to_numpy(float) + float(q.get("pbar_shift", 0.0))
    prob = src.disrupt_prob_annual.to_numpy(float) * float(q.get("prob_scale", 1.0))
    sev = src.disrupt_severity.to_numpy(float)
    prob = np.clip(prob, 0.001, 0.99)
    M = float(q.get("M", cfg["imports_2024"]["M_forecast_2526"]))
    X = float(q.get("reserve_X", cfg["structural_params"]["reserve_X"]))
    ell = cfg["derived"]["ell_qty"] * float(q.get("ell_scale", 1.0))
    Om = mc.build_omega(prob, sev)
    m_cap = np.array([7200.0, 4427.0, 820.0, 830.0])
    s_cap = m2.qp_shares(p, Om, ell, M, cap=m_cap / M)
    s_an = m2.analytic_shares(p, Om, ell, M)
    out_scen = []
    for scn in [None, "C1", "C2", "C3"]:
        sim = m2.simulate_year(s_cap, M, prob, sev, 12 * ell, X=X, n=2000,
                               scenario=scn)
        out_scen.append(dict(scenario=scn or "基线",
                             cvar5=round(m2.cvar(sim["loss"]), 1),
                             mean_short=round(float(sim["shortage"].mean()), 1)))
    return jsonify(dict(sources=src.name.tolist(),
                        shares_capped=[round(float(v), 4) for v in s_cap],
                        shares_analytic=[round(float(v), 4) for v in s_an],
                        cost_yi=round(M * float(s_cap @ p) * 1e-4, 1),
                        scenarios=out_scen))


@app.route("/api/m3", methods=["POST"])
@check_auth
def api_m3():
    """M3 网络冲击: 大豆供给冲击 x% → 部门价格与消费指数。"""
    q = request.json or {}
    shock = float(q.get("shock_pct", 20.0)) / 100.0
    A = pd.read_csv(ROOT / "data/io_table_9sector.csv", index_col=0)
    meta = pd.read_csv(ROOT / "data/io_meta_9sector.csv")
    Am = A.to_numpy(); n = len(A)
    v = np.zeros(n); v[0] = shock
    dlnp = np.linalg.solve(np.eye(n) - Am.T, v)
    b = meta.b_weight.to_numpy()
    return jsonify(dict(labels=meta.label.tolist(),
                        dlnp_pct=(dlnp * 100).round(3).tolist(),
                        food_index_pct=round(float(b @ dlnp) * 100, 3)))


@app.route("/api/m5", methods=["POST"])
@check_auth
def api_m5():
    """M5 政策 ABM: 单个政策 3 种子 × 800 农户 × 2026–2032（约数秒）。"""
    st = get_state()
    cfg = st["cfg"]
    q = request.json or {}
    pol = dict(sub_area=float(q.get("sub_area", 350.0)),
               price_floor_tau=float(q.get("price_floor", 0.0)),
               theta_transmission=float(q.get("theta", 0.35)),
               reserve_X=float(q.get("reserve_X", 1000)))
    if q.get("targeted"):
        pol["sub_area"] = 0.0
        pol["sub_targeted"] = m5.targeted_subsidy(
            cfg, budget_yi=float(q.get("budget", 540.0)))
    series, aggs = [], []
    with _lock:
        for s in range(3):
            df = ABM(cfg, n_agents=800, seed=2000 + s, policy=pol).run(range(2026, 2033))
            series.append(df)
    dfm = pd.concat(series).groupby("year").mean(numeric_only=True).reset_index()
    return jsonify(dict(
        years=dfm.year.astype(int).tolist(),
        Y=dfm.Y.round(0).tolist(), M=dfm.M_planned.round(0).tolist(),
        income=dfm.income_soy.round(0).tolist(),
        q_bar=dfm.q_bar.round(3).tolist(),
        fiscal=round(float(dfm.fiscal.mean()), 1),
        selfsuff=round(float((dfm.Y / (dfm.Y + dfm.M_planned)).mean()), 3),
        gini=round(float(dfm.gini.mean()), 3),
        short=dfm.short.round(1).tolist()))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7070, threaded=True)
