"""
03_estimate.py — 计量估计（审阅修订版：规格矩阵 + 推断协议）

规格矩阵（§4.2）：
 (1) 动态pooled logit, dpi_base（基期锁定, 主规格）
 (2) 同(1), dpi_roll（行为口径对照）
 (3) Wooldridge(2005)正确实现：D_i首期 + 全部时变X户内均值；pooled logit给APE，
     BinomialBayesMixedGLM给随机效应σ_a（非平衡按Rabe-Hesketh修正：自身首期/自身均值）
 (4) LPM（含双城全样本）+ wild cluster bootstrap p
 (5) dpi_loo（LOO单产, 下界）
 (6) 事件研究浓缩列：dpi_sub100 × Suit_vill
稳健性：Firth罚似然、完整个案、IPW加权、平衡面板(≥3年)、规格曲线(控制变量2^5组合)
份额：非条件分数logit（非双城全样本）为主，条件版入附录
推断：村聚类CRV1 + LPM wild bootstrap；AME带delta法区间
动态面板：FD-2SLS（Anderson-Hsiao型，D_{t-2}作工具）
输出：output/tables/reg_*.csv, spec_curve.csv/png, behavior_params.json
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import patsy
import json, os, itertools
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
os.makedirs(f"{OUT}/tables", exist_ok=True)
rng = np.random.default_rng(20260707)
for f in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
plt.rcParams["axes.unicode_minus"] = False

p = pd.read_csv(f"{OUT}/panel_analysis.csv")
p = p[p["village"].notna()].copy()
p["village"] = p["village"].astype(np.int64)

est = p[p["plant_soy_lag"].notna() & p["dpi100_base"].notna()].copy()

# ---- 控制变量分块（P3）----
BLK = {
    "A人力": ["head_age10", "head_edu", "head_male", "head_health", "labor_n"],
    "B劳动": ["offfarm_n", "wage_share"],
    "C土地资本": ["rentin_d", "ln_asset"],
    "D风险信息": ["insurance", "internet", "head_train_agr"],
    "E村级": ["v_coop_n"],
}
ALLC = [v for vs in BLK.values() for v in vs]
complete_mask = est[ALLC + ["peer_lag"]].notna().all(axis=1)
for c in ALLC:
    est[c + "_miss"] = est[c].isna().astype(int)
    est[c] = est[c].fillna(est[c].median())
est["peer_lag0"] = est["peer_lag"].fillna(0)
est["peer_miss"] = est["peer_lag"].isna().astype(int)
est["county"] = est["county_name"]
est["yr"] = est["year"].astype(int)

def xstr(blocks):
    vs = [v for b in blocks for v in BLK[b]]
    miss = [v + "_miss" for v in vs if est[v + "_miss"].sum() > 0]
    return " + ".join(vs + miss)

FE = "C(county) + C(yr)"
XA = xstr(["A人力"])
XFULL = xstr(list(BLK))
estL = est[est["county"] != "双城区"].copy()

def cfit(formula, data, family=None, weights=None):
    if family is None:
        m = smf.ols(formula, data=data)
        if weights is not None:
            m = smf.wls(formula, data=data, weights=weights)
    else:
        # IPW 概率权重走 var_weights（而非 freq_weights）：后者把权重当频数、
        # 使 nobs=权重和，污染 CRV1 的 (N-1)/(N-k) 有限样本因子。
        m = smf.glm(formula, data=data, family=family,
                    var_weights=weights if weights is not None else None)
    return m.fit(cov_type="cluster", cov_kwds={"groups": data["village"]})

def ame_ci(m, data, var):
    """AME 与 delta 法区间（logit）。"""
    mu = np.asarray(m.predict(data))
    beta = m.params[var]
    ame = float((beta * mu * (1 - mu)).mean())
    names = list(m.params.index)
    X = patsy.dmatrix(m.model.data.design_info, data, return_type="dataframe")[names].values
    lam = mu * (1 - mu)
    j = names.index(var)
    G = (lam[:, None] * beta * (1 - 2 * mu)[:, None] * X).mean(axis=0)
    G[j] += lam.mean()
    V = m.cov_params().values
    se = float(np.sqrt(G @ V @ G))
    return ame, ame - 1.96 * se, ame + 1.96 * se

def wild_p_ols(formula, data, param, weights=None, B=4999):
    y, X = patsy.dmatrices(formula, data, return_type="dataframe")
    yv, Xv = y.values.ravel(), X.values
    cols = list(X.columns)
    j = cols.index(param)
    cl = data["village"].values
    w = np.ones(len(yv)) if weights is None else np.asarray(weights)
    t_obs = sm.WLS(yv, Xv, weights=w).fit(cov_type="cluster", cov_kwds={"groups": cl}).tvalues[j]
    Xr = np.delete(Xv, j, axis=1)
    r0 = sm.WLS(yv, Xr, weights=w).fit()
    clus = np.unique(cl)
    ts = np.empty(B)
    for b in range(B):
        ww = dict(zip(clus, rng.choice([-1.0, 1.0], len(clus))))
        ystar = r0.fittedvalues + r0.resid * np.vectorize(ww.get)(cl)
        ts[b] = sm.WLS(ystar, Xv, weights=w).fit(
            cov_type="cluster", cov_kwds={"groups": cl}).tvalues[j]
    return float((np.abs(ts) >= abs(t_obs)).mean())

R = {}   # name -> fitted model
meta = {}  # name -> dict

# ---------- (1) 主规格：基期锁定 ----------
f1 = f"plant_soy ~ dpi100_base + plant_soy_lag + peer_lag0 + peer_miss + {XA} + {FE}"
R["m1_base"] = cfit(f1, estL, sm.families.Binomial())
# 控制变量分块递进（主表2-3列）
f1b = f"plant_soy ~ dpi100_base + plant_soy_lag + peer_lag0 + peer_miss + {xstr(['A人力','B劳动','C土地资本'])} + {FE}"
R["m1b_ctrlBC"] = cfit(f1b, estL, sm.families.Binomial())
f1c = f"plant_soy ~ dpi100_base + plant_soy_lag + peer_lag0 + peer_miss + {XFULL} + {FE}"
R["m1c_ctrlFull"] = cfit(f1c, estL, sm.families.Binomial())

# ---------- (2) 滚动版对照 ----------
R["m2_roll"] = cfit(f1.replace("dpi100_base", "dpi100_roll"), estL, sm.families.Binomial())

# ---------- (3) Wooldridge(2005) 正确实现 ----------
first = p.sort_values("year").groupby("hh_id").first()
estL["D_init"] = estL["hh_id"].map(first["plant_soy"]).astype(float)
# Wooldridge(2005) 正确装置：D_i0 + 全部时变协变量的户内均值 X̄_i。
# 除 dpi/peer/logB 外，A人力块中确有户内变异的控制（年龄/教育/健康/劳动力）
# 也须进 Mundlak 均值，否则 CRE 未真正控制其与个体效应的相关（一致性前提）。
bar_core = ["dpi100_base", "peer_lag0", "logB"]
bar_tv = [v for v in ["head_age10", "head_edu", "head_health", "labor_n"]
          if v in estL and estL.groupby("hh_id")[v].transform("std").fillna(0).gt(1e-9).any()]
for v in bar_core + bar_tv:
    estL[v + "_bar"] = estL.groupby("hh_id")[v].transform("mean")
bar_str = " + ".join([v + "_bar" for v in bar_core + bar_tv])
f3 = (f"plant_soy ~ dpi100_base + plant_soy_lag + peer_lag0 + peer_miss + D_init"
      f" + {bar_str} + logB + {XA} + {FE}")
R["m3_wooldridge"] = cfit(f3, estL, sm.families.Binomial())
# 随机效应 σ_a：BayesMixedGLM（同一设计 + 户随机截距）
try:
    yv, Xv = patsy.dmatrices(f3, estL, return_type="dataframe")
    exog_vc = pd.get_dummies(estL["hh_id"]).values.astype(float)
    ident = np.zeros(exog_vc.shape[1], dtype=int)
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    bm = BinomialBayesMixedGLM(yv.values.ravel(), Xv.values, exog_vc, ident,
                               vcp_p=2.0, fe_p=2.0)
    bres = bm.fit_vb()
    SIGMA_A = float(np.exp(bres.vcp_mean[0]))
except Exception as e:
    print("BayesMixedGLM失败:", e)
    SIGMA_A = np.nan

# ---------- (4) LPM 全样本 + wild bootstrap ----------
f4 = f"plant_soy ~ dpi100_base + plant_soy_lag + peer_lag0 + peer_miss + {XA} + {FE}"
R["m4_lpm_all"] = cfit(f4, est)
R["m4_lpm_nodc"] = cfit(f4, estL)
WILD_P = {"lpm_all": wild_p_ols(f4, est, "dpi100_base"),
          "lpm_nodc": wild_p_ols(f4, estL, "dpi100_base"),
          "lpm_lag_all": wild_p_ols(f4, est, "plant_soy_lag")}

# ---------- (5) LOO 版 ----------
dloo = estL[estL["dpi100_loo"].notna()]
R["m5_loo"] = cfit(f1.replace("dpi100_base", "dpi100_loo"), dloo, sm.families.Binomial())

# ---------- (6) 事件研究浓缩列：补贴差×Suit ----------
f6 = (f"plant_soy ~ dpi_sub100:suit_vill_z + dpi_mkt100_base + plant_soy_lag"
      f" + peer_lag0 + peer_miss + {XA} + C(village) + C(yr)")
R["m6_subXsuit"] = cfit(f6, estL)

# ---------- (7) 前导安慰剂：未来收益差 Δπ_{i,t+1} 预测当期 D_it（§3.5(3)③） ----------
# 若在控制当期 Δπ 后，未来收益差仍显著预测当期选择，说明存在共同趋势/遗漏变量，
# 需下调 Δπ 系数的因果解读。构造户内向前一期的 dpi100_base 作为前导项。
lead_series = p.set_index(["hh_id", "year"])["dpi100_base"]
for d_ in (est, estL):
    d_["dpi100_base_lead"] = [lead_series.get((h, y + 1), np.nan)
                              for h, y in zip(d_["hh_id"], d_["yr"])]
elead = estL[estL["dpi100_base_lead"].notna()].copy()
f_lead = (f"plant_soy ~ dpi100_base + dpi100_base_lead + plant_soy_lag"
          f" + peer_lag0 + peer_miss + {XA} + {FE}")
LEAD = {}
try:
    # 前导可用样本仅 2 个年份（有后一年者），logit MLE 因近共线/分离奇异 →
    # 用 LPM（与全文少聚类推断锚一致，wild bootstrap 给 p），只关心前导项方向与显著性。
    R["m7_lead_placebo"] = cfit(f_lead, elead)
    f_leadonly = f_lead.replace("dpi100_base + dpi100_base_lead", "dpi100_base_lead")
    R["m7_lead_only"] = cfit(f_leadonly, elead)
    LEAD = {"n": int(R["m7_lead_placebo"].nobs),
            "b_contemp": float(R["m7_lead_placebo"].params.get("dpi100_base", np.nan)),
            "p_contemp": float(R["m7_lead_placebo"].pvalues.get("dpi100_base", np.nan)),
            "b_lead": float(R["m7_lead_placebo"].params.get("dpi100_base_lead", np.nan)),
            "p_lead": float(R["m7_lead_placebo"].pvalues.get("dpi100_base_lead", np.nan)),
            "b_lead_only": float(R["m7_lead_only"].params.get("dpi100_base_lead", np.nan)),
            "p_lead_only": float(R["m7_lead_only"].pvalues.get("dpi100_base_lead", np.nan))}
    # 前导项 LPM wild bootstrap p（少聚类稳健，与全文推断协议一致）
    LEAD["wild_p_lead"] = wild_p_ols(f_lead, elead, "dpi100_base_lead")
except Exception as e:
    print("前导安慰剂失败:", e)

# ---------- (8) leave-one-village 价格/成本口径稳健性（§3.5(2) 反向因果） ----------
dlov = estL[estL["dpi100_base_lov"].notna()].copy()
LOV = {}
try:
    R["r_lov"] = cfit(f1.replace("dpi100_base", "dpi100_base_lov"), dlov, sm.families.Binomial())
    amelov = ame_ci(R["r_lov"], dlov, "dpi100_base_lov")
    LOV = {"n": int(R["r_lov"].nobs),
           "b_lov": float(R["r_lov"].params.get("dpi100_base_lov", np.nan)),
           "p_lov": float(R["r_lov"].pvalues.get("dpi100_base_lov", np.nan)),
           "ame_lov": amelov[0], "ame_lov_ci": [amelov[1], amelov[2]]}
except Exception as e:
    print("LOV稳健性失败:", e)

# ---------- 稳健性 ----------
def drop_novar(formula, data):
    """剔除子样本中零方差的项，避免奇异。"""
    lhs, rhs = formula.split("~")
    keep = []
    for t in [x.strip() for x in rhs.split("+")]:
        if t.startswith("C(") or ":" in t or "*" in t:
            keep.append(t)
        elif t in data.columns and data[t].std(skipna=True) > 1e-12:
            keep.append(t)
    return lhs + "~ " + " + ".join(keep)

R["r_ipw"] = cfit(f1, estL, sm.families.Binomial(), weights=estL["ipw"])
bald = estL[estL["balanced3"] == 1]
R["r_balanced"] = cfit(drop_novar(f1, bald), bald, sm.families.Binomial())
cc = estL[complete_mask.reindex(estL.index, fill_value=False)]
if len(cc) > 80 and cc["plant_soy"].nunique() > 1:
    try:
        R["r_complete"] = cfit(drop_novar(f1c, cc), cc, sm.families.Binomial())
    except Exception as e:
        print("complete-case失败:", e)
# Firth 罚似然（手写IRLS，Jeffreys先验）
def firth_logit(X, y, maxit=200, tol=1e-9):
    b = np.zeros(X.shape[1])
    Iinv = None
    for _ in range(maxit):
        eta = np.clip(X @ b, -30, 30)
        mu = 1 / (1 + np.exp(-eta))
        W = mu * (1 - mu)
        XW = X * W[:, None]
        Iinv = np.linalg.pinv(X.T @ XW)
        h = np.einsum("ij,jk,ik->i", XW, Iinv, X)
        U = X.T @ (y - mu + h * (0.5 - mu))
        db = Iinv @ U
        b = b + db
        if np.max(np.abs(db)) < tol:
            break
    return b, np.sqrt(np.diag(Iinv))

try:
    yF, XF = patsy.dmatrices(f1, estL, return_type="dataframe")
    bF, seF = firth_logit(XF.values, yF.values.ravel())
    firth = pd.DataFrame({"var": list(XF.columns), "coef": bF, "se": seF})
    firth.to_csv(f"{OUT}/tables/reg_firth.csv", index=False)
    FIRTH_B = float(firth.loc[firth["var"] == "dpi100_base", "coef"].iloc[0])
except Exception as e:
    print("Firth失败:", e)
    FIRTH_B = np.nan

# ---------- FD-2SLS（Anderson–Hsiao） ----------
try:
    bal = p[p["balanced3"] == 1].sort_values(["hh_id", "year"])
    bal = bal[bal["county_name"] != "双城区"]
    w = bal.pivot_table(index="hh_id", columns="year",
                        values=["plant_soy", "dpi100_base"], aggfunc="first")
    rows = []
    for t in [2023, 2024]:
        need = [("plant_soy", t), ("plant_soy", t - 1), ("plant_soy", t - 2), ("dpi100_base", t), ("dpi100_base", t - 1)]
        sub = w.dropna(subset=need)
        if not len(sub):
            continue
        rows.append(pd.DataFrame({
            "hh": sub.index,
            "dD": (sub[("plant_soy", t)] - sub[("plant_soy", t - 1)]).values,
            "dD_lag": (sub[("plant_soy", t - 1)] - sub[("plant_soy", t - 2)]).values,
            "D_l2": sub[("plant_soy", t - 2)].values,
            "ddpi": (sub[("dpi100_base", t)] - sub[("dpi100_base", t - 1)]).values,
            "yr": t}))
    ah = pd.concat(rows, ignore_index=True)
    from linearmodels.iv import IV2SLS
    ah["const"] = 1.0
    # 同一户在2023/2024两行相关 → 按户聚类（与全文聚类协议一致）
    iv = IV2SLS(ah["dD"], ah[["const", "ddpi"]], ah[["dD_lag"]], ah[["D_l2"]])\
        .fit(cov_type="clustered", clusters=ah["hh"])
    try:  # 弱工具第一阶段 F（D_{t-2} 对内生 dD_lag 的偏 F）
        fsF = float(iv.first_stage.diagnostics.loc["dD_lag", "f.stat"])
    except Exception:
        fsF = np.nan
    AH = {"gamma_fd2sls": float(iv.params["dD_lag"]), "se": float(iv.std_errors["dD_lag"]),
          "beta_dpi": float(iv.params["ddpi"]), "n": int(iv.nobs),
          "first_stage_F": fsF, "n_clusters": int(ah["hh"].nunique())}
except Exception as e:
    print("AH-IV失败:", e)
    AH = {}

# ---------- 规格曲线 ----------
spec_rows = []
for r_ in range(len(BLK) + 1):
    for combo in itertools.combinations(BLK.keys(), r_):
        xs = xstr(list(combo)) if combo else ""
        f_ = f"plant_soy ~ dpi100_base + plant_soy_lag + peer_lag0 + peer_miss + {FE}" + (f" + {xs}" if xs else "")
        try:
            m_ = cfit(f_, estL, sm.families.Binomial())
            spec_rows.append({"blocks": "+".join(combo) if combo else "无",
                              "b": m_.params["dpi100_base"], "se": m_.bse["dpi100_base"],
                              "p": m_.pvalues["dpi100_base"], "gamma": m_.params["plant_soy_lag"]})
        except Exception:
            continue
SC = pd.DataFrame(spec_rows).sort_values("b").reset_index(drop=True)
SC.to_csv(f"{OUT}/tables/spec_curve.csv", index=False)
fig, ax = plt.subplots(figsize=(7, 4))
ax.errorbar(range(len(SC)), SC["b"], yerr=1.96 * SC["se"], fmt="o", ms=3, capsize=2, alpha=0.7)
ax.axhline(0, c="gray", lw=0.8)
ax.set_xlabel(f"控制变量组合（{len(SC)}种规格，按系数排序）")
ax.set_ylabel("β(Δπ_base/100) 及95%CI")
ax.set_title("规格曲线：收益差系数对控制变量选择的稳健性")
plt.tight_layout()
plt.savefig(f"{OUT}/figures/fig_spec_curve.png", dpi=200)
plt.close()

# ---------- 份额：非条件分数logit（主）+ 条件版（附录） ----------
sh_all = estL.copy()
sh_all["s_lag0"] = sh_all["s_lag"].fillna(0)
f_su = f"s ~ dpi100_base + s_lag0 + logB + {XA} + C(county) + C(yr)"
R["s_uncond"] = cfit(f_su, sh_all, sm.families.Binomial())
sh_c = estL[estL["plant_soy"] == 1].copy()
sh_c["s_lag0"] = sh_c["s_lag"].fillna(0)
R["s_cond"] = cfit("s ~ dpi100_base + s_lag0 + logB + C(county) + C(yr)", sh_c,
                   sm.families.Binomial())

# ---------- 规模异质性（连续交互，P11） ----------
estL["logB_c"] = estL["logB"] - estL["logB"].mean()
f_sz = f"plant_soy ~ dpi100_base*logB_c + plant_soy_lag + peer_lag0 + peer_miss + {XA.replace('labor_n','labor_n')} + {FE}"
R["m_sizeX"] = cfit(f_sz, estL, sm.families.Binomial())

# ---------- 导出 ----------
for name, m in R.items():
    pd.DataFrame({"coef": m.params, "se": m.bse, "z": m.tvalues, "p": m.pvalues})\
        .round(4).to_csv(f"{OUT}/tables/reg_{name}.csv")

ame1 = ame_ci(R["m1_base"], estL, "dpi100_base")
d0, d1 = estL.copy(), estL.copy()
d0["plant_soy_lag"], d1["plant_soy_lag"] = 0.0, 1.0
ame_state = float((R["m1_base"].predict(d1) - R["m1_base"].predict(d0)).mean())
mw = R["m3_wooldridge"]
ame_w = ame_ci(mw, estL, "dpi100_base")
d0w, d1w = estL.copy(), estL.copy()
d0w["plant_soy_lag"], d1w["plant_soy_lag"] = 0.0, 1.0
ame_state_w = float((mw.predict(d1w) - mw.predict(d0w)).mean())

params = {
    "participation": {
        "model": "dynamic_pooled_logit_dpi_base",
        "n": int(R["m1_base"].nobs),
        "coef": {k: float(v) for k, v in R["m1_base"].params.items()},
        "vcov_vars": list(R["m1_base"].params.index),
        "vcov": R["m1_base"].cov_params().values.tolist(),
        "ame_dpi100": ame1[0], "ame_dpi100_ci": [ame1[1], ame1[2]],
        "ame_state_dep": ame_state,
    },
    "participation_wooldridge": {
        "coef": {k: float(v) for k, v in mw.params.items()},
        "vcov_vars": list(mw.params.index),
        "vcov": mw.cov_params().values.tolist(),
        "ame_dpi100": ame_w[0], "ame_dpi100_ci": [ame_w[1], ame_w[2]],
        "ame_state_dep": ame_state_w,
        "sigma_a_RE": SIGMA_A,
    },
    "share_unconditional": {
        "n": int(R["s_uncond"].nobs),
        "coef": {k: float(v) for k, v in R["s_uncond"].params.items()},
        "vcov_vars": list(R["s_uncond"].params.index),
        "vcov": R["s_uncond"].cov_params().values.tolist(),
        # ABM 把 eps 加在"条件份额 s_cond"上（仅对种植户），故噪声须取种植子样本
        # 上条件份额模型的残差SD；用非条件全样本（含大量零份额户）的残差SD会系统性夸大。
        "resid_sd": float((sh_c["s"] - R["s_cond"].predict(sh_c)).std()),
        "resid_sd_uncond": float((sh_all["s"] - R["s_uncond"].predict(sh_all)).std()),
    },
    "inference": {"wild_bootstrap_p": WILD_P, "firth_beta": FIRTH_B, "anderson_hsiao": AH,
                  "lead_placebo": LEAD, "lov_robustness": LOV,
                  "n_villages": int(estL["village"].nunique()),
                  "n_events": int(estL["plant_soy"].sum())},
    "controls_medians": {c: float(est[c].median()) for c in ALLC + ["logB"]},
}
with open(f"{OUT}/params/behavior_params.json", "w") as f:
    json.dump(params, f, ensure_ascii=False, indent=1)

# ---------- 报告 ----------
rep = ["# Phase 3 估计报告（规格矩阵版）\n"]
key = ["dpi100_base", "dpi100_roll", "dpi100_loo", "dpi100_base_lov", "dpi100_base_lead",
       "plant_soy_lag", "peer_lag0", "D_init", "dpi100_base_bar",
       "dpi_sub100:suit_vill_z", "dpi100_base:logB_c", "s_lag0", "logB"]
summ = []
for name, m in R.items():
    for k in key:
        if k in m.params.index:
            summ.append({"model": name, "var": k, "coef": m.params[k],
                         "se": m.bse[k], "p": m.pvalues[k], "n": int(m.nobs)})
S = pd.DataFrame(summ).round(4)
rep += [S.to_string(index=False),
        f"\nAME(基期锁定Δπ+100元): {ame1[0]*100:.2f}pp [{ame1[1]*100:.2f}, {ame1[2]*100:.2f}]",
        f"AME(Wooldridge): {ame_w[0]*100:.2f}pp [{ame_w[1]*100:.2f}, {ame_w[2]*100:.2f}]",
        f"状态依赖AME: pooled={ame_state*100:.1f}pp, Wooldridge={ame_state_w*100:.1f}pp",
        f"σ_a(RE估计)={SIGMA_A:.3f}" if not np.isnan(SIGMA_A) else "σ_a估计失败",
        f"wild bootstrap p: {WILD_P}",
        f"Firth β={FIRTH_B:.3f}" if not np.isnan(FIRTH_B) else "Firth失败",
        f"前导安慰剂(Δπ_t+1): {LEAD}",
        f"LOV(剔本村价格/成本): {LOV}",
        f"Anderson-Hsiao: {AH}",
        f"规格曲线: β范围[{SC['b'].min():.3f},{SC['b'].max():.3f}], 全部>0: {bool((SC['b']>0).all())}",
        f"村数={estL['village'].nunique()}, 阳性事件={int(estL['plant_soy'].sum())}"]
with open(f"{OUT}/logs/phase3_report.md", "w") as f:
    f.write("\n".join(rep))
print(S.to_string(index=False))
print(f"AME base: {ame1[0]*100:.2f}pp [{ame1[1]*100:.2f},{ame1[2]*100:.2f}], "
      f"Wooldridge: {ame_w[0]*100:.2f}pp; state {ame_state*100:.1f}/{ame_state_w*100:.1f}pp; "
      f"sigma_a={SIGMA_A}; wild={WILD_P}; AH={AH}")
