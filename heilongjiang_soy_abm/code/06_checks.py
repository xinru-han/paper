"""
06_checks.py — 审阅收尾项（P9/P10/P15）
(1) P15 县代码核实：原始问卷 县代码×县名 对照表
(2) P9  补贴交叉验证完整表（含离群与n，大豆费率系统性偏低如实呈现）
(3) P10 预期口径敏感性：dpi 用 sub_{t-1} 重构主规格
(4) 轮作补贴哨兵值(9999)清理后的核查表
输出：output/tables/county_code_check.csv, subsidy_crosscheck_full.csv,
      reg_sublag_sens.csv, rotation_subsidy_check.csv(更新)
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os, warnings
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
RAW = "/root/data/数据/黑龙江农户调查"

# ---------- (1) P15 县代码核实 ----------
rows = []
for yr in [2019, 2020, 2021, 2022, 2023, 2024]:
    df = pd.read_excel(f"{RAW}/户问卷{yr}.xlsx", usecols=lambda c: c in ("县代码", "县名"))
    g = df.groupby(["县代码", "县名"]).size().rename("n").reset_index()
    g["year"] = yr
    rows.append(g)
CC = pd.concat(rows, ignore_index=True)
CC.to_csv(f"{OUT}/tables/county_code_check.csv", index=False)
print("== 县代码核实 ==")
print(CC.pivot_table(index=["县代码", "县名"], columns="year", values="n", aggfunc="sum")
      .fillna(0).astype(int).to_string())

# ---------- (2) P9 补贴交叉验证完整表 ----------
p = pd.read_csv(f"{OUT}/panel_analysis.csv")
SUB_OFFICIAL = {2021: (68, 248), 2022: (28, 248), 2023: (15, 350), 2024: (20, 350)}
rows = []
for (cty, yr), g in p.groupby(["county_name", "year"]):
    rec = {"county": cty, "year": yr,
           "official_corn": SUB_OFFICIAL[yr][0], "official_soy": SUB_OFFICIAL[yr][1]}
    if yr == 2024:
        gc = g[(g["area_corn"] > 0) & (g["sub_corn_rep"] > 0) & (g["sub_corn_rep"] != 9999)]
        gs = g[(g["area_soy"] > 0) & (g["sub_soy_rep"] > 0) & (g["sub_soy_rep"] != 9999)]
        rec["derived_corn"] = (gc["sub_corn_rep"] / gc["area_corn"]).median() if len(gc) else np.nan
        rec["derived_soy"] = (gs["sub_soy_rep"] / gs["area_soy"]).median() if len(gs) else np.nan
        rec["n_corn"], rec["n_soy"] = len(gc), len(gs)
    else:
        gg = g[(g["sub_prod_rep"] > 0) & (g["sub_prod_rep"] != 9999) & (g["B"] > 0)]
        pure_c = gg[(gg["area_soy"] == 0) & (gg["area_corn"] > 0)]
        pure_s = gg[(gg["area_corn"] == 0) & (gg["area_soy"] > 0)]
        rec["derived_corn"] = (pure_c["sub_prod_rep"] / pure_c["area_corn"]).median() if len(pure_c) else np.nan
        rec["derived_soy"] = (pure_s["sub_prod_rep"] / pure_s["area_soy"]).median() if len(pure_s) else np.nan
        rec["n_corn"], rec["n_soy"] = len(pure_c), len(pure_s)
    rows.append(rec)
SCX = pd.DataFrame(rows)
SCX["gap_corn"] = SCX["derived_corn"] - SCX["official_corn"]
SCX["gap_soy"] = SCX["derived_soy"] - SCX["official_soy"]
SCX.round(1).to_csv(f"{OUT}/tables/subsidy_crosscheck_full.csv", index=False)
print("\n== 补贴交叉验证（完整，含离群） ==")
print(SCX.round(1).to_string(index=False))

# ---------- (3) P10 预期口径敏感性：sub_{t-1} ----------
est = p[p["plant_soy_lag"].notna() & p["dpi_mkt100_base"].notna()
        & p["dpi_sub_lag"].notna() & (p["county_name"] != "双城区")].copy()
est = est[est["village"].notna()]
est["village"] = est["village"].astype(np.int64)
est["dpi100_sublag"] = est["dpi_mkt100_base"] + est["dpi_sub_lag"] / 100.0
CTRL = ["head_age10", "head_edu", "labor_n", "logB"]
for c in CTRL:
    est[c + "_miss"] = est[c].isna().astype(int)
    est[c] = est[c].fillna(est[c].median())
MISS = [c + "_miss" for c in CTRL if est[c + "_miss"].sum() > 0]
X = " + ".join(CTRL + MISS)
est["peer_lag0"] = est["peer_lag"].fillna(0)
est["peer_miss"] = est["peer_lag"].isna().astype(int)
out = []
for lab, v in [("sub_t(基准)", "dpi100_base"), ("sub_t-1(滞后口径)", "dpi100_sublag")]:
    f = f"plant_soy ~ {v} + plant_soy_lag + peer_lag0 + peer_miss + {X} + C(county_name) + C(year)"
    m = smf.glm(f, data=est, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": est["village"]})
    out.append({"spec": lab, "n": int(m.nobs), "beta": m.params[v], "se": m.bse[v],
                "p": m.pvalues[v], "gamma": m.params["plant_soy_lag"]})
SL = pd.DataFrame(out).round(4)
SL.to_csv(f"{OUT}/tables/reg_sublag_sens.csv", index=False)
print("\n== 补贴预期口径敏感性 ==")
print(SL.to_string(index=False))

# ---------- (4) 轮作补贴核查（剔除9999哨兵） ----------
rot = p[(p["sub_rot_rep"] > 0) & (p["sub_rot_rep"] != 9999)]
RT = rot.groupby(["county_name", "year"]).agg(
    n=("hh_id", "size"), med_amt=("sub_rot_rep", "median"),
    soy_part=("plant_soy", "mean"),
    new_soy=("plant_soy_lag", lambda s: float((s == 0).mean()))).round(2)
RT.to_csv(f"{OUT}/tables/rotation_subsidy_check.csv")
print("\n== 轮作补贴核查（剔除哨兵9999） ==")
print(RT.to_string())

with open(f"{OUT}/logs/phase6_checks.md", "w") as f:
    f.write("# Phase 6 收尾核查\n\n## 县代码\n"
            + CC.pivot_table(index=["县代码", "县名"], columns="year", values="n",
                             aggfunc="sum").fillna(0).astype(int).to_string()
            + "\n\n## 补贴交叉验证\n" + SCX.round(1).to_string(index=False)
            + "\n\n## 预期口径敏感性\n" + SL.to_string(index=False)
            + "\n\n## 轮作补贴\n" + RT.to_string())
print("\ndone 06")
