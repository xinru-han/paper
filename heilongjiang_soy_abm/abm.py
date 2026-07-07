"""
黑龙江玉米—大豆种植决策 Agent-Based Model（修正版）
行为参数来自 output/params/behavior_params.json（03_estimate.py 动态logit + fractional logit）。
向量化 NumPy 实现：仅年份循环显式，agent×MC 副本全向量化。

相对旧版的修正：
  1) 份额方程使用含县固定效应的 agent 截距（旧版只用全局 Intercept）
  2) 参数不确定性：每个 MC 副本从 N(β̂, V̂) 抽一套系数（村聚类稳健 VCV）
  3) 宏观年冲击 σ_macro：年×副本共同冲击进参与方程截距
  4) 份额残差抽样 σ_s（观测残差SD），不再是确定性均值
  5) 校准截距偏移 calib_offset：使基年模拟参与率匹配观测值
  6) 双城区结构性零参与（估计样本外，玉米带完全分离）
"""
import numpy as np
import pandas as pd
import json


def load_params(path):
    with open(path) as f:
        return json.load(f)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def _coef_key(vcov_vars, county, yr_fe):
    """行为方程设计向量的列顺序与 behavior_params 的 vcov_vars 对齐。"""
    return {v: i for i, v in enumerate(vcov_vars)}


def _draw_betas(P, n_mc, rng):
    """每个 MC 副本抽一套系数（多元正态，聚类稳健VCV）。返回 (K, n_mc)。"""
    mu = np.array([P["coef"][v] for v in P["vcov_vars"]])
    V = np.array(P["vcov"])
    try:
        L = np.linalg.cholesky(V + 1e-12 * np.eye(len(mu)))
        return mu[:, None] + L @ rng.standard_normal((len(mu), n_mc))
    except np.linalg.LinAlgError:
        return np.repeat(mu[:, None], n_mc, axis=1)


def abm_init(agent_df, params, n_mc=500, seed=20260705,
             sigma_a=0.5, sigma_macro=0.3, calib_offset=0.0, param_uncertainty=True):
    """agent_df 每行一个农户：county_name, village, B, logB, head_age10, head_edu,
    labor_n, ey_corn, ey_soy, s_init, plant_soy_init, structural_zero(双城=1)。"""
    rng = np.random.default_rng(seed)
    N = len(agent_df)
    P, S = params["participation"], params["share"]

    bP = _draw_betas(P, n_mc, rng) if param_uncertainty else \
        np.repeat(np.array([P["coef"][v] for v in P["vcov_vars"]])[:, None], n_mc, axis=1)
    bS = _draw_betas(S, n_mc, rng) if param_uncertainty else \
        np.repeat(np.array([S["coef"][v] for v in S["vcov_vars"]])[:, None], n_mc, axis=1)
    iP = {v: i for i, v in enumerate(P["vcov_vars"])}
    iS = {v: i for i, v in enumerate(S["vcov_vars"])}

    county = agent_df["county_name"].to_numpy()

    state = {
        "N": N, "n_mc": n_mc, "rng": rng,
        "county": county, "village": agent_df["village"].to_numpy(),
        "B": agent_df["B"].to_numpy(float),
        "ey_corn": agent_df["ey_corn"].to_numpy(float),
        "ey_soy": agent_df["ey_soy"].to_numpy(float),
        "structural_zero": agent_df["structural_zero"].to_numpy(bool),
        "D_init": agent_df.get("D_init", agent_df["plant_soy_init"]).to_numpy(float),
        "bP": bP, "bS": bS, "iP": iP, "iS": iS,
        "sigma_macro": sigma_macro, "calib_offset": calib_offset,
        "sigma_s": S.get("resid_sd", 0.2),
    }
    # 全部静态数值特征入 state（_linpred 按系数名自动取用）
    skip = {"county_name", "village", "hh_id", "ey_corn", "ey_soy", "structural_zero",
            "s_init", "plant_soy_init", "D_init"}
    for col in agent_df.columns:
        if col not in skip and col not in state:
            v = pd.to_numeric(agent_df[col], errors="coerce")
            state[col] = v.fillna(v.median()).to_numpy(float)
    # 户内均值项（Wooldridge装置）：bar_<var> 列 → bars 字典
    state["bars"] = {}
    for col in agent_df.columns:
        if col.startswith("bar_"):
            v = pd.to_numeric(agent_df[col], errors="coerce")
            state["bars"][col[4:]] = v.fillna(v.median()).to_numpy(float)
    ones = np.ones((1, n_mc))
    state["s_prev"] = agent_df["s_init"].to_numpy(float)[:, None] * ones
    state["plant_soy_prev"] = agent_df["plant_soy_init"].to_numpy(float)[:, None] * ones
    state["a_i"] = rng.normal(0, sigma_a, size=(N, n_mc))
    return state


def abm_expectations(state, scenario, t, params):
    """朴素预期 + 轮作农学反馈：重迎茬减产（大豆连作惩罚）与轮作增产。"""
    econ = params["econ"]
    d_rot, d_rep = econ.get("delta_rot", 0.05), econ.get("delta_rep", 0.05)
    s_prev = state["s_prev"]
    ey_corn = state["ey_corn"][:, None] * (1 + d_rot * s_prev)
    ey_soy = state["ey_soy"][:, None] * (1 - d_rep * s_prev)
    return dict(p_corn=scenario["p_corn"][t], p_soy=scenario["p_soy"][t],
                ey_corn=ey_corn, ey_soy=ey_soy)


def _dpi(exp, scenario, t, params, s_prev):
    """轮作补贴只覆盖新增大豆面积：边际决策中按 (1−s_prev) 折算计入大豆预期收益。"""
    econ = params["econ"]; cost = econ["cost_per_mu"]
    sub_rot_eff = scenario["sub_rot"][t] * (1.0 - s_prev)
    pi_corn = exp["p_corn"] * exp["ey_corn"] - cost["corn"] + scenario["sub_corn"][t]
    pi_soy = exp["p_soy"] * exp["ey_soy"] - cost["soy"] + scenario["sub_soy"][t] + sub_rot_eff
    return pi_soy - pi_corn


def _linpred(state, eq, dpi100, peer):
    """通用线性预测：按 vcov_vars 逐项解析变量名 → agent 数据。

    支持：Intercept / dpi100_* / plant_soy_lag / s_lag0 / peer_lag0 / D_init /
    *_bar（agent常量）/ 静态户特征 / *_miss(=0) / 县FE、年FE(取最新年)。
    返回 (N, n_mc)。
    """
    idx = state["i" + eq]
    betas = state["b" + eq]
    N, M = state["N"], state["n_mc"]
    county = state["county"]
    yr_terms = sorted([v for v in idx if v.startswith("C(yr)[T.") or v.startswith("C(year)[T.")])
    latest_yr = yr_terms[-1] if yr_terms else None
    xb = np.zeros((N, M))
    for name, j in idx.items():
        b = betas[j][None, :]  # (1, n_mc)
        if name == "Intercept":
            xb += b
        # 后缀判断必须先于前缀判断：否则 dpi100_base_bar / peer_lag0_bar 会被
        # startswith("dpi100")/"peer_lag0" 误路由到时变项通道（Wooldridge装置失效）。
        elif name.endswith("_miss") or name == "peer_miss":
            continue  # 仿真中无缺失
        elif name.endswith("_bar"):
            base = name[:-4]
            arr = state["bars"].get(base)
            if arr is not None:
                xb += b * arr[:, None]
        elif name == "D_init":
            xb += b * state["D_init"][:, None]
        elif name == "plant_soy_lag":
            xb += b * state["plant_soy_prev"]
        elif name == "s_lag0":
            xb += b * state["s_prev"]
        elif name == "peer_lag0":
            xb += b * peer
        elif name.startswith("dpi100") or name == "dpi_mkt100_base":
            xb += b * dpi100
        elif name.startswith("C(county)[T."):
            lev = name.split("[T.")[1].rstrip("]")
            xb += b * (county == lev)[:, None]
        elif name.startswith(("C(yr)[T.", "C(year)[T.")):
            if name == latest_yr:
                xb += b  # 前瞻环境取最新年FE
        elif name in state:
            xb += b * np.asarray(state[name], float)[:, None]
    return xb


def abm_decide(state, exp, scenario, t, params, peer):
    rng = state["rng"]
    dpi = _dpi(exp, scenario, t, params, state["s_prev"])
    dpi100 = dpi / 100.0
    macro = rng.normal(0, state["sigma_macro"], size=(1, state["n_mc"]))

    xb = _linpred(state, "P", dpi100, peer) + state["a_i"] + macro + state["calib_offset"]
    prob = _sigmoid(xb)
    prob[state["structural_zero"]] = 0.0  # 双城区结构性零参与
    plant_soy = (rng.random(prob.shape) < prob).astype(float)

    # 非条件份额 E[s|x]（含零）→ 条件份额 ≈ E[s]/P(D=1)。分母用 max(prob, mu_u)
    # 而非 max(prob,1e-3)：后者在低参与户使比值爆大再被截到0.98（低参与户被赋予
    # 近纯大豆份额，系统性上偏）；前者从构造上保证 s_cond∈(0,1] 且 ≥ mu_u。
    mu_u = _sigmoid(_linpred(state, "S", dpi100, peer))
    s_cond = np.clip(mu_u / np.maximum(prob, mu_u), 0.02, 0.98)
    eps = rng.normal(0, state["sigma_s"], size=mu_u.shape)
    s = np.where(plant_soy > 0, np.clip(s_cond + eps, 0.02, 0.98), 0.0)
    return plant_soy, s, prob, dpi


def abm_realize(state, exp, scenario, t, plant_soy, s, params):
    econ = params["econ"]; cost = econ["cost_per_mu"]; rng = state["rng"]
    N, M = state["N"], state["n_mc"]
    sig_p = params.get("sigma_p", 0.08); sig_y = params.get("sigma_y", 0.15)
    p_corn = exp["p_corn"] * np.exp(rng.normal(0, sig_p, size=(N, M)))
    p_soy = exp["p_soy"] * np.exp(rng.normal(0, sig_p, size=(N, M)))
    y_corn = exp["ey_corn"] * np.exp(rng.normal(0, sig_y, size=(N, M)))
    y_soy = exp["ey_soy"] * np.exp(rng.normal(0, sig_y, size=(N, M)))
    B = state["B"][:, None]
    area_soy = s * B; area_corn = (1 - s) * B
    # 轮作补贴：本期新增大豆面积（相对上期份额的增量）
    rot_area = np.maximum(0.0, s - state["s_prev"]) * B
    sc, ss, sr = scenario["sub_corn"][t], scenario["sub_soy"][t], scenario["sub_rot"][t]
    income = (area_corn * (p_corn * y_corn - cost["corn"] + sc)
              + area_soy * (p_soy * y_soy - cost["soy"] + ss)
              + rot_area * sr)
    fiscal = area_corn * sc + area_soy * ss + rot_area * sr
    return dict(income=income, fiscal=fiscal, area_soy=area_soy, area_corn=area_corn)


def _village_peer(state):
    """上一期村内同伴大豆份额（leave-one-out）。"""
    villages = state["village"]; s_prev = state["s_prev"]
    peer = np.zeros_like(s_prev)
    for v in np.unique(villages):
        idx = np.where(villages == v)[0]
        if len(idx) <= 1:
            continue
        block = s_prev[idx]
        tot = block.sum(axis=0, keepdims=True)
        peer[idx] = (tot - block) / (len(idx) - 1)
    return peer


def abm_step(state, scenario, t, params, peer_on=True):
    exp = abm_expectations(state, scenario, t, params)
    peer = _village_peer(state) if peer_on else np.zeros((state["N"], state["n_mc"]))
    plant_soy, s, prob, dpi = abm_decide(state, exp, scenario, t, params, peer)
    out = abm_realize(state, exp, scenario, t, plant_soy, s, params)
    state["s_prev"] = s
    state["plant_soy_prev"] = plant_soy
    out.update(plant_soy=plant_soy, s=s, prob=prob, dpi=dpi)
    return out


def make_scenario(years, p_corn, p_soy, sub_corn, sub_soy, sub_rot):
    n = len(years)
    def arr(x):
        return np.asarray(x, float) if np.ndim(x) else np.full(n, float(x))
    return dict(years=list(years), p_corn=arr(p_corn), p_soy=arr(p_soy),
                sub_corn=arr(sub_corn), sub_soy=arr(sub_soy), sub_rot=arr(sub_rot))


def run_scenario(agent_df, params, scenario, n_mc=500, seed=20260705, peer_on=True,
                 sigma_a=0.5, sigma_macro=0.3, calib_offset=0.0, param_uncertainty=True):
    state = abm_init(agent_df, params, n_mc=n_mc, seed=seed, sigma_a=sigma_a,
                     sigma_macro=sigma_macro, calib_offset=calib_offset,
                     param_uncertainty=param_uncertainty)
    years = scenario["years"]
    rec = {k: [] for k in ["year", "soy_particip", "soy_particip_lo", "soy_particip_hi",
                           "soy_share", "soy_share_lo", "soy_share_hi",
                           "fiscal", "fiscal_lo", "fiscal_hi", "soy_area", "total_area"]}
    per_county = {c: {"year": [], "soy_share": [], "particip": []}
                  for c in np.unique(state["county"])}
    nz = ~state["structural_zero"]
    agent_prob_last = None      # 末年户级预测参与概率（MC均值），供回测算命中率/Brier
    for t, yr in enumerate(years):
        out = abm_step(state, scenario, t, params, peer_on=peer_on)
        agent_prob_last = out["prob"].mean(axis=1)
        B = state["B"][:, None]
        share_rep = out["area_soy"].sum(0) / B.sum()
        part_rep = out["plant_soy"][nz].mean(0)  # 参与率口径：非结构零县
        fiscal_rep = out["fiscal"].sum(0)
        q = lambda a, p: float(np.quantile(a, p))
        rec["year"].append(yr)
        rec["soy_particip"].append(float(part_rep.mean()))
        rec["soy_particip_lo"].append(q(part_rep, 0.05)); rec["soy_particip_hi"].append(q(part_rep, 0.95))
        rec["soy_share"].append(float(share_rep.mean()))
        rec["soy_share_lo"].append(q(share_rep, 0.05)); rec["soy_share_hi"].append(q(share_rep, 0.95))
        rec["fiscal"].append(float(fiscal_rep.mean()))
        rec["fiscal_lo"].append(q(fiscal_rep, 0.05)); rec["fiscal_hi"].append(q(fiscal_rep, 0.95))
        rec["soy_area"].append(float(out["area_soy"].sum(0).mean()))
        rec["total_area"].append(float(B.sum()))
        for c in per_county:
            m = state["county"] == c
            per_county[c]["year"].append(yr)
            per_county[c]["soy_share"].append(float((out["area_soy"][m].sum(0) / B[m].sum()).mean()))
            per_county[c]["particip"].append(float(out["plant_soy"][m].mean()))
    return dict(agg=rec, per_county=per_county, final_state=state,
                agent_prob_last=agent_prob_last)
