"""
03_estimate.py — 计量估计
(1) 动态 pooled logit：plant_soy ~ dpi100 + plant_soy_lag + peer_lag + X + 县FE + 年FE，村聚类SE
(2) LPM 稳健性
(3) Mundlak-CRE logit（加入 dpi100 的户内均值）
(4) 规模异质性：dpi100 × 经营规模三分位
(5) fractional logit：s | plant_soy=1 ~ dpi100 + s_lag + 县FE
(6) AME（补贴差+100元/亩 → 参与概率变化）
输出：output/params/behavior_params.json, output/tables/reg_*.csv, output/logs/phase3_report.md
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
os.makedirs(f"{OUT}/tables", exist_ok=True)

p = pd.read_csv(f"{OUT}/panel_analysis.csv")
est = p[p["plant_soy_lag"].notna() & p["dpi100"].notna()].copy()

# 控制变量缺失处理：中位数填补 + 缺失指示（保样本）
CTRLS = ["head_age10", "head_edu", "labor_n", "logB"]
for c in CTRLS:
    est[c + "_miss"] = est[c].isna().astype(int)
    est[c] = est[c].fillna(est[c].median())
est["peer_lag0"] = est["peer_lag"].fillna(0)
est["peer_miss"] = est["peer_lag"].isna().astype(int)
est["county"] = est["county_name"]
est["yr"] = est["year"].astype(int)

# 规模三分位（按估计样本 B）
est["size_ter"] = pd.qcut(est["B"], 3, labels=["small", "mid", "large"])

FE = "C(county) + C(yr)"
MISS = [c + "_miss" for c in CTRLS if est[c + "_miss"].sum() > 0]
X = " + ".join(CTRLS + MISS)

def cluster_fit(formula, data, family=None):
    if family is None:
        m = smf.ols(formula, data=data)
    else:
        m = smf.glm(formula, data=data, family=family)
    return m.fit(cov_type="cluster", cov_kwds={"groups": data["village"]})

results = {}

# 双城区参与率恒为0（完全分离，玉米带结构性专业化）：logit 样本剔除，
# LPM 保留全样本；ABM 中双城作结构性零参与处理
estL = est[est["county"] != "双城区"].copy()

# ---- (1) 主模型：动态 logit ----
f1 = f"plant_soy ~ dpi100 + plant_soy_lag + peer_lag0 + peer_miss + {X} + {FE}"
m1 = cluster_fit(f1, estL, sm.families.Binomial())
results["logit_main"] = m1

# ---- (2) LPM（全样本，含双城） ----
m2 = cluster_fit(f1, est)
results["lpm"] = m2

# ---- (3) Mundlak-CRE ----
estL["dpi100_bar"] = estL.groupby("hh_id")["dpi100"].transform("mean")
f3 = f"plant_soy ~ dpi100 + dpi100_bar + plant_soy_lag + peer_lag0 + peer_miss + {X} + {FE}"
m3 = cluster_fit(f3, estL, sm.families.Binomial())
results["logit_cre"] = m3

# ---- (4) 规模异质性 ----
f4 = f"plant_soy ~ dpi100:C(size_ter) + dpi100 + plant_soy_lag + peer_lag0 + peer_miss + {X} + {FE}"
# 用显式交互（以 small 为基准）
MISS_STR = " + ".join(MISS)
f4 = f"plant_soy ~ dpi100*C(size_ter) + plant_soy_lag + peer_lag0 + peer_miss + head_age10 + head_edu + labor_n + " \
     f"{MISS_STR} + {FE}"
m4 = cluster_fit(f4, estL, sm.families.Binomial())
results["logit_size"] = m4

# ---- (5) 分解：市场差与补贴差分别进入 ----
f5 = f"plant_soy ~ dpi_mkt100 + dpi_sub100 + plant_soy_lag + peer_lag0 + peer_miss + {X} + C(county)"
m5 = cluster_fit(f5, estL, sm.families.Binomial())
results["logit_decomp"] = m5

# ---- (6) fractional logit（份额，种植户内） ----
sh = estL[estL["plant_soy"] == 1].copy()
sh["s_lag0"] = sh["s_lag"].fillna(0)
f6 = f"s ~ dpi100 + s_lag0 + logB + C(county) + C(yr)"
m6 = smf.glm(f6, data=sh, family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": sh["village"]})
results["fraclogit_share"] = m6

# ---- AME：dpi100 的平均边际效应（logit 主模型）----
def ame_dpi(m, data, var="dpi100"):
    mu = m.predict(data)
    beta = m.params[var]
    return float((beta * mu * (1 - mu)).mean())

ame_main = ame_dpi(m1, estL)
# 规模分组 AME
ame_size = {}
for g in ["small", "mid", "large"]:
    sub = estL[estL["size_ter"] == g]
    mu = m4.predict(sub)
    b = m4.params["dpi100"] + (m4.params.get(f"dpi100:C(size_ter)[T.{g}]", 0.0) if g != "small" else 0.0)
    ame_size[g] = float((b * mu * (1 - mu)).mean())

# ---- 状态依赖 AME：plant_soy_lag 0→1 ----
d0 = estL.copy(); d0["plant_soy_lag"] = 0.0
d1 = estL.copy(); d1["plant_soy_lag"] = 1.0
ame_state = float((m1.predict(d1) - m1.predict(d0)).mean())

# ---- 导出回归表 ----
def tab(m, name):
    t = pd.DataFrame({"coef": m.params, "se": m.bse, "z": m.tvalues, "p": m.pvalues})
    t.round(4).to_csv(f"{OUT}/tables/reg_{name}.csv")
    return t

for name, m in results.items():
    tab(m, name)

# ---- behavior_params.json（供 ABM）----
def fe_dict(m, prefix):
    return {k.split("[T.")[1].rstrip("]"): float(v) for k, v in m.params.items() if k.startswith(prefix)}

params = {
    "participation": {
        "model": "dynamic_pooled_logit",
        "n": int(m1.nobs),
        "coef": {k: float(v) for k, v in m1.params.items()},
        "vcov_vars": list(m1.params.index),
        "vcov": m1.cov_params().values.tolist(),
        "ame_dpi100": ame_main,
        "ame_state_dep": ame_state,
        "ame_by_size": ame_size,
    },
    "share": {
        "model": "fractional_logit",
        "n": int(m6.nobs),
        "coef": {k: float(v) for k, v in m6.params.items()},
        "vcov": m6.cov_params().values.tolist(),
        "vcov_vars": list(m6.params.index),
        "resid_sd": float((sh["s"] - m6.predict(sh)).std()),
    },
    "controls_medians": {c: float(est[c].median()) for c in CTRLS},
}
with open(f"{OUT}/params/behavior_params.json", "w") as f:
    json.dump(params, f, ensure_ascii=False, indent=1)

# ---- 报告 ----
rep = ["# Phase 3 估计报告\n"]
key_rows = ["dpi100", "dpi_mkt100", "dpi_sub100", "plant_soy_lag", "peer_lag0", "s_lag0"]
summ = []
for name, m in results.items():
    for k in key_rows:
        if k in m.params.index:
            summ.append({"model": name, "var": k, "coef": m.params[k], "se": m.bse[k], "p": m.pvalues[k], "n": int(m.nobs)})
S = pd.DataFrame(summ).round(4)
rep.append(S.to_string(index=False))
rep.append(f"\n\nAME(dpi100, 即Δπ+100元/亩): {ame_main:.4f}  → 补贴差+100元/亩 ≈ +{ame_main*100:.1f} 个百分点")
rep.append(f"状态依赖 AME(lag 0→1): {ame_state:.4f}")
rep.append(f"规模分组 AME: { {k: round(v,4) for k,v in ame_size.items()} }")
rep.append(f"\n份额方程残差SD: {params['share']['resid_sd']:.4f}")
with open(f"{OUT}/logs/phase3_report.md", "w") as f:
    f.write("\n".join(rep))
print(S.to_string(index=False))
print(f"AME dpi100={ame_main:.4f}, state={ame_state:.4f}, size={ame_size}")
