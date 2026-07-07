"""
05_identification.py — 识别策略主修复（审阅 P1/P5/P6）
(1) 暴露度DiD/事件研究：D_ivt = α_v + λ_t + Σβ_τ·1[t=τ]×Suit_i + X'θ + ε
    全样本884户次、Suit三口径、赛马列(Suit×豆粮价格比)、wild bootstrap + 置换推断
(2) 磨损分析：留存回归 + IPW权重（并回写 panel_analysis.csv 供03使用）
(3) 轮作补贴21户次核查（P1-2）
(4) 村级补贴差辅助回归（村报玉米标准）
输出：output/tables/event_study*.csv, attrition*.csv, output/figures/fig_event_study.png
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
rng = np.random.default_rng(20260707)

for f in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
plt.rcParams["axes.unicode_minus"] = False

p = pd.read_csv(f"{OUT}/panel_analysis.csv")
p = p[p["village"].notna()].copy()
p["village"] = p["village"].astype(np.int64)

# ---------------- 事件研究 ----------------
es = p.copy()
CTRL = ["head_age10", "head_edu", "labor_n", "logB"]
for c in CTRL:
    es[c + "_miss"] = es[c].isna().astype(int)
    es[c] = es[c].fillna(es[c].median())
MISS = [c + "_miss" for c in CTRL if es[c + "_miss"].sum() > 0]
XSTR = " + ".join(CTRL + MISS)

def cluster_ols(formula, data):
    return smf.ols(formula, data=data).fit(cov_type="cluster",
                                           cov_kwds={"groups": data["village"]})

def _crv1_t(yv, Xv, cl_codes, n_cl, j):
    """快速 OLS + CRV1 聚类 t 值（numpy级）。"""
    XtX_inv = np.linalg.pinv(Xv.T @ Xv)
    beta = XtX_inv @ (Xv.T @ yv)
    u = yv - Xv @ beta
    Xu = Xv * u[:, None]
    S = np.zeros((Xv.shape[1], Xv.shape[1]))
    for g in range(n_cl):
        m = cl_codes == g
        sg = Xu[m].sum(axis=0)
        S += np.outer(sg, sg)
    n, k = Xv.shape
    adj = (n_cl / (n_cl - 1)) * ((n - 1) / (n - k))
    V = adj * XtX_inv @ S @ XtX_inv
    return beta[j], beta[j] / np.sqrt(V[j, j])

def wild_p(formula, data, param, B=999):
    """Rademacher wild cluster bootstrap-t（施加原假设 β=0，矩阵级）。"""
    import patsy
    y, X = patsy.dmatrices(formula, data, return_type="dataframe")
    yv, Xv = y.values.ravel(), X.values
    j = list(X.columns).index(param)
    cl = pd.factorize(data["village"])[0]
    n_cl = cl.max() + 1
    _, t_obs = _crv1_t(yv, Xv, cl, n_cl, j)
    Xr = np.delete(Xv, j, axis=1)
    br = np.linalg.pinv(Xr.T @ Xr) @ (Xr.T @ yv)
    yhat0 = Xr @ br
    u0 = yv - yhat0
    ts = np.empty(B)
    for b in range(B):
        w = rng.choice([-1.0, 1.0], size=n_cl)[cl]
        _, ts[b] = _crv1_t(yhat0 + u0 * w, Xv, cl, n_cl, j)
    return float((np.abs(ts) >= abs(t_obs)).mean())

def perm_p(formula, data, param, suit_col, B=499):
    """置换推断（矩阵级）：重排 Suit 后仅重算含 S 的交互列。"""
    import patsy
    y, X = patsy.dmatrices(formula, data, return_type="dataframe")
    yv, Xv = y.values.ravel(), X.values.copy()
    cols = list(X.columns)
    j = cols.index(param)
    cl = pd.factorize(data["village"])[0]
    n_cl = cl.max() + 1
    b_obs, _ = _crv1_t(yv, Xv, cl, n_cl, j)
    # 含 S 的列及其年份指示
    s_cols = [i for i, c in enumerate(cols) if c.startswith("S:") or c == "S"]
    yr_ind = {}
    yrs = data["year"].values
    for i in s_cols:
        c = cols[i]
        if "[" in c:
            tau = int(c.split("[")[-1].rstrip("]").replace("T.", ""))
            yr_ind[i] = (yrs == tau).astype(float)
        else:
            yr_ind[i] = np.ones(len(yrs))
    S0 = data["S"].values
    vill = data["village"].values
    vs = data.groupby("village")["S"].first()
    v_level = data.groupby("village")["S"].nunique().max() == 1
    v_cty = data.groupby("village")["county_name"].first()
    stats = np.empty(B)
    for b in range(B):
        if v_level:
            perm = vs.copy()
            for cty in v_cty.unique():
                idx = v_cty[v_cty == cty].index
                perm.loc[idx] = rng.permutation(vs.loc[idx].values)
            Sp = perm.reindex(vill).values
        else:
            Sp = S0.copy()
            for v in np.unique(vill):
                m = vill == v
                Sp[m] = rng.permutation(Sp[m])
        Xb = Xv.copy()
        for i in s_cols:
            Xb[:, i] = Sp * yr_ind[i]
        stats[b], _ = _crv1_t(yv, Xb, cl, n_cl, j)
    return float((np.abs(stats) >= abs(b_obs)).mean())

results, fig_rows = [], []
for suit, lab in [("suit_vill_z", "村2021大豆份额"), ("suit_hhy_z", "户基期相对单产"),
                  ("suit_cty_z", "县适宜度序数")]:
    d = es[es[suit].notna()].copy()
    d["S"] = d[suit]
    f = (f"plant_soy ~ S:C(year, Treatment(2022)) + {XSTR} + C(village) + C(year)")
    m = cluster_ols(f, d)
    row = {"suit": lab, "n": int(m.nobs), "villages": d["village"].nunique()}
    for tau in [2021, 2023, 2024]:
        k = f"S:C(year, Treatment(2022))[{tau}]"
        if k in m.params:
            row[f"b{tau}"] = m.params[k]
            row[f"se{tau}"] = m.bse[k]
            row[f"p{tau}"] = m.pvalues[k]
            fig_rows.append({"suit": lab, "tau": tau, "b": m.params[k],
                             "lo": m.params[k] - 1.96 * m.bse[k],
                             "hi": m.params[k] + 1.96 * m.bse[k]})
    fig_rows.append({"suit": lab, "tau": 2022, "b": 0.0, "lo": 0.0, "hi": 0.0})
    # 推断增强：2023/2024系数的 wild bootstrap 与置换 p
    k23 = f"S:C(year, Treatment(2022))[2023]"
    k24 = f"S:C(year, Treatment(2022))[2024]"
    row["wild_p23"] = wild_p(f, d, k23, B=1999)
    row["wild_p24"] = wild_p(f, d, k24, B=1999)
    row["perm_p24"] = perm_p(f, d, k24, suit, B=499)
    # 赛马：Suit × 豆粮价格比（滞后）
    d2 = d[d["pr_ratio_lag"].notna()].copy()
    f2 = f + " + S:pr_ratio_lag"
    m2 = cluster_ols(f2, d2)
    row["b24_horse"] = m2.params.get(k24, np.nan)
    row["p24_horse"] = m2.pvalues.get(k24, np.nan)
    row["b_ratio"] = m2.params.get("S:pr_ratio_lag", np.nan)
    row["p_ratio"] = m2.pvalues.get("S:pr_ratio_lag", np.nan)
    results.append(row)

ES = pd.DataFrame(results)
ES.round(4).to_csv(f"{OUT}/tables/event_study.csv", index=False)
print("== 事件研究 ==")
print(ES.round(3).to_string(index=False))

# 事件研究图
fig, ax = plt.subplots(figsize=(7, 4.2))
off = {"村2021大豆份额": -0.15, "户基期相对单产": 0.0, "县适宜度序数": 0.15}
for lab, g in pd.DataFrame(fig_rows).groupby("suit"):
    g = g.sort_values("tau")
    ax.errorbar(g["tau"] + off[lab], g["b"], yerr=[g["b"] - g["lo"], g["hi"] - g["b"]],
                fmt="o", capsize=3, label=lab, ms=4)
ax.axhline(0, c="gray", lw=0.8)
ax.axvline(2022.5, c="red", ls=":", lw=0.8)
ax.set_xticks([2021, 2022, 2023, 2024])
ax.set_ylabel("Suit×年份系数（对2022年）")
ax.set_title("事件研究：补贴差跳升前后适宜度暴露的参与响应")
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(f"{OUT}/figures/fig_event_study.png", dpi=200)
plt.close()

# ---------------- 磨损分析与 IPW ----------------
att = p[p["year"] < 2024].copy()
for c in CTRL:
    att[c + "_miss"] = att[c].isna().astype(int)
    att[c] = att[c].fillna(att[c].median())
att["dpi_b"] = att["dpi100_base"].fillna(att["dpi100_base"].median())
fa = ("retained_next ~ plant_soy + s + dpi_b + logB + head_age10 + head_edu + labor_n"
      " + C(county_name) + C(year)")
ma = cluster_ols(fa, att)
AT = pd.DataFrame({"coef": ma.params, "se": ma.bse, "p": ma.pvalues}).round(4)
AT.to_csv(f"{OUT}/tables/attrition_lpm.csv")
print("\n== 磨损选择性（留存LPM，关键系数） ==")
print(AT.loc[[i for i in AT.index if not i.startswith("C(")]].to_string())

# 逐年留存率与2023队列细分
ret_tab = att.groupby("year").agg(N=("retained_next", "size"), retain=("retained_next", "mean"))
ret23 = att[att["year"] == 2023].groupby("plant_soy")["retained_next"].agg(["mean", "size"])
ret_tab.round(3).to_csv(f"{OUT}/tables/attrition_rates.csv")
print(ret_tab.round(3).to_string())
print("2023队列按是否种豆的留存率:\n", ret23.round(3).to_string())

# IPW：logit 留存概率 → 下一年观测的权重 1/p̂
ml = smf.glm(fa, data=att, family=sm.families.Binomial()).fit()
att["p_ret"] = ml.predict(att).clip(0.1, 0.99)
w = att[["hh_id", "year", "p_ret"]].copy()
w["year"] += 1  # 权重作用于 t+1 年的观测
p = p.merge(w, on=["hh_id", "year"], how="left")
p["ipw"] = 1.0 / p["p_ret"]
p.loc[p["year"] == 2021, "ipw"] = 1.0  # 首年无磨损模型
p["ipw"] = p["ipw"].fillna(1.0).clip(upper=p["ipw"].quantile(0.99))
p.to_csv(f"{OUT}/panel_analysis.csv", index=False)
print(f"\nIPW 权重: mean={p['ipw'].mean():.3f}, p95={p['ipw'].quantile(.95):.3f}")

# ---------------- 轮作补贴核查（P1-2） ----------------
rot = p[p["sub_rot_rep"] > 0]
print("\n== 户报轮作补贴 ==")
print(rot.groupby(["county_name", "year"]).agg(n=("hh_id", "size"),
      med_amt=("sub_rot_rep", "median"), soy_part=("plant_soy", "mean"),
      new_soy=("plant_soy_lag", lambda s: (s == 0).mean())).round(2).to_string())
rot_chk = rot[["county_name", "year", "hh_id", "sub_rot_rep", "area_soy", "plant_soy",
               "plant_soy_lag", "s", "s_lag"]]
rot_chk.to_csv(f"{OUT}/tables/rotation_subsidy_check.csv", index=False)

# ---------------- 村级补贴差辅助回归（P1辅助） ----------------
dv = p[p["dpi_sub_vill"].notna() & p["plant_soy_lag"].notna()].copy()
if len(dv) > 50:
    for c in CTRL:
        dv[c + "_miss"] = dv[c].isna().astype(int)
        dv[c] = dv[c].fillna(dv[c].median())
    dv["dsv100"] = dv["dpi_sub_vill"] / 100
    dv["dm100"] = dv["dpi_mkt100_base"]
    fv = f"plant_soy ~ dsv100 + dm100 + plant_soy_lag + {XSTR} + C(county_name) + C(year)"
    mv = cluster_ols(fv, dv[dv["dm100"].notna()])
    VS = pd.DataFrame({"coef": mv.params, "se": mv.bse, "p": mv.pvalues}).round(4)
    VS.to_csv(f"{OUT}/tables/village_subsidy_reg.csv")
    print(f"\n== 村报补贴差 LPM（n={int(mv.nobs)}） ==")
    print(VS.loc[["dsv100", "dm100", "plant_soy_lag"]].to_string())

# 报告
with open(f"{OUT}/logs/phase5_report.md", "w") as f:
    f.write("# Phase 5 识别修复报告\n\n## 事件研究\n" + ES.round(4).to_string(index=False)
            + "\n\n## 磨损\n" + ret_tab.round(3).to_string()
            + "\n\n留存LPM关键系数:\n"
            + AT.loc[[i for i in AT.index if not i.startswith("C(")]].to_string())
print("\ndone 05")
