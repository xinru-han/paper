# -*- coding: utf-8 -*-
"""多效应量Meta分析（v3：全文提取扩充样本）。

方法（对标 IFPRI DP02361 与 Tan et al. 2026 JAE）：
  - 一篇多效应量，效应量嵌套于文献；合并效应用相关效应RVE
    （Hedges-Tipton-Johnson 2010, rho=0.8, robumeta同款权重），
    SE在文献层面聚类稳健，t分布(m-1)推断；
  - Meta回归：RVE加权WLS，含路径虚拟变量、微观/内生性控制与
    1/sqrt(N) 精度项（IFPRI式发表偏倚控制）；
  - 发表偏倚：Egger + Begg（Tan式）与 FAT-PET-PEESE；
  - 异常值：主分析剔除 [Q1-3IQR, Q3+3IQR] 之外的PCC（IFPRI规则），
    全样本结果同表报告；
  - 弹性轨：Target×Path 弹性中位数（reported/full优先，
    converted次之，semi近似最后），|e|<1。
输出 results/meta_v3/。
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta_stats import rve_pool, rve_wls, egger_begg, star

OUT = os.path.join(BASE, "results", "meta_v3")
os.makedirs(OUT, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(BASE, ".matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for f in ["Noto Sans CJK SC", "Noto Serif CJK SC"]:
    if f in {x.name for x in font_manager.fontManager.ttflist}:
        plt.rcParams["font.sans-serif"] = [f, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False

log_lines = []


def log(m=""):
    print(m)
    log_lines.append(str(m))


df = pd.read_csv(os.path.join(BASE, "data", "meta_effects_expanded.csv"),
                 encoding="utf-8-sig")
df = df.dropna(subset=["PCC", "SE_PCC"])
TARGETS = ["Yield", "Area", "Efficiency"]
PATHS = ["MCI", "AMS", "AML"]
TNAME = {"Yield": "粮食单产", "Area": "播种面积", "Efficiency": "生产效率"}

log(f"效应量 {len(df)} 条 / 文献 {df['study_id'].nunique()} 篇")

# ---------------------------------------------- IFPRI式异常值规则
def trim_iqr3(d):
    q1, q3 = d["PCC"].quantile([0.25, 0.75])
    iqr = q3 - q1
    return d[(d["PCC"] >= q1 - 3 * iqr) & (d["PCC"] <= q3 + 3 * iqr)]


def fmt(r):
    return (f"k={r['k']:>3d} m={r['m']:>2d}  PCC={r['mu']:+.3f}{star(r['pval']):<3s} "
            f"[{r['ci'][0]:+.3f},{r['ci'][1]:+.3f}]  p={r['pval']:.4f}  "
            f"tau2={r['tau2']:.4f}  I2={r['I2']:.1f}%")


# ================================================ 表1 合并效应
log("\n" + "=" * 76)
log("表1 合并效应（相关效应RVE，rho=0.8；主分析=剔除[Q1-3IQR,Q3+3IQR]外异常值）")
log("=" * 76)
rows1 = []
for tg in TARGETS:
    d_all = df[df["Target"] == tg]
    d = trim_iqr3(d_all)
    r = rve_pool(d["PCC"].values, d["SE_PCC"].values ** 2, d["study_id"].values)
    ra = rve_pool(d_all["PCC"].values, d_all["SE_PCC"].values ** 2,
                  d_all["study_id"].values)
    log(f"{TNAME[tg]:6s} 主  {fmt(r)}   (全样本 PCC={ra['mu']:+.3f}{star(ra['pval'])}, "
        f"k={ra['k']}, 剔除{len(d_all)-len(d)}条)")
    rows1.append(dict(维度=TNAME[tg], k=r["k"], 文献数=r["m"],
                      合并PCC=round(r["mu"], 3), 显著性=star(r["pval"]),
                      CI下=round(r["ci"][0], 3), CI上=round(r["ci"][1], 3),
                      p值=round(r["pval"], 4), tau2=round(r["tau2"], 4),
                      I2=round(r["I2"], 1),
                      全样本PCC=round(ra["mu"], 3), 全样本p=round(ra["pval"], 4),
                      剔除异常值条数=len(d_all) - len(d)))
pd.DataFrame(rows1).to_csv(os.path.join(OUT, "table1_overall_rve.csv"),
                           index=False, encoding="utf-8-sig")

# ================================================ 表2 分路径
log("\n" + "=" * 76)
log("表2 分路径合并效应（RVE）")
log("=" * 76)
rows2 = []
for tg in TARGETS:
    d_t = trim_iqr3(df[df["Target"] == tg])
    for p in ["ALL"] + PATHS:
        d = d_t if p == "ALL" else d_t[d_t["Path"] == p]
        if len(d) == 0:
            continue
        if d["study_id"].nunique() < 2:
            log(f"{TNAME[tg]} {p:4s} 文献数<2，跳过合并")
            continue
        r = rve_pool(d["PCC"].values, d["SE_PCC"].values ** 2,
                     d["study_id"].values)
        log(f"{TNAME[tg]} {p:4s} {fmt(r)}")
        rows2.append(dict(维度=TNAME[tg], 路径=p, k=r["k"], 文献数=r["m"],
                          合并PCC=round(r["mu"], 3), 显著性=star(r["pval"]),
                          CI下=round(r["ci"][0], 3), CI上=round(r["ci"][1], 3),
                          p值=round(r["pval"], 4), I2=round(r["I2"], 1)))
pd.DataFrame(rows2).to_csv(os.path.join(OUT, "table2_subgroup_rve.csv"),
                           index=False, encoding="utf-8-sig")

# ================================================ 表3 Meta回归
log("\n" + "=" * 76)
log("表3 RVE Meta回归（基准组MCI；含微观/内生性/1/sqrt(N)精度项）")
log("=" * 76)
rows3 = []
for tg in TARGETS:
    d = trim_iqr3(df[df["Target"] == tg]).copy()
    d["AMS"] = (d["Path"] == "AMS").astype(float)
    d["AML"] = (d["Path"] == "AML").astype(float)
    d["inv_sqrtN"] = 1.0 / np.sqrt(d["N"].astype(float))
    d["micro"] = d["micro"].fillna(0).astype(float)
    d["endog"] = d["endog"].fillna(0).astype(float)
    Xc = [c for c in ["AMS", "AML", "micro", "endog", "inv_sqrtN"]
          if d[c].std() > 0]
    m_st = d["study_id"].nunique()
    if m_st < len(Xc) + 4:
        log(f"\n[{TNAME[tg]}] 文献数{m_st}不足，仅报告精简模型")
        Xc = [c for c in ["AMS", "AML"] if c in Xc and d[c].std() > 0]
        if m_st < len(Xc) + 3 or not Xc:
            log("  样本仍不足，跳过")
            continue
    X = pd.DataFrame({"const": 1.0}, index=d.index).join(d[Xc])
    res, tau2, m = rve_wls(d["PCC"].values, X, d["SE_PCC"].values ** 2,
                           d["study_id"].values)
    log(f"\n[{TNAME[tg]}] k={len(d)}, m={m}, tau2={tau2:.4f}")
    for nm, rr in res.iterrows():
        log(f"  {nm:10s} {rr['coef']:+.4f}{star(rr['p']):<3s} "
            f"(SE={rr['se']:.4f}, p={rr['p']:.4f})")
        rows3.append(dict(维度=TNAME[tg], 变量=nm, 系数=round(rr["coef"], 4),
                          SE=round(rr["se"], 4), p值=round(rr["p"], 4),
                          显著性=star(rr["p"]), k=len(d), 文献数=m))
pd.DataFrame(rows3).to_csv(os.path.join(OUT, "table3_meta_regression_rve.csv"),
                           index=False, encoding="utf-8-sig")

# ================================================ 表4 发表偏倚
log("\n" + "=" * 76)
log("表4 发表偏倚：Egger / Begg / FAT-PET-PEESE（聚类稳健）")
log("=" * 76)
rows4 = []
for tg in TARGETS:
    d = trim_iqr3(df[df["Target"] == tg]).copy()
    eb = egger_begg(d["PCC"].values, d["SE_PCC"].values)
    log(f"\n[{TNAME[tg]}] k={len(d)}")
    log(f"  Egger截距={eb['egger_intercept']:+.3f} p={eb['egger_p']:.4f}   "
        f"Begg tau={eb['begg_tau']:+.3f} p={eb['begg_p']:.4f}")
    X = pd.DataFrame({"const": 1.0, "SE": d["SE_PCC"].values}, index=d.index)
    pet, _, m = rve_wls(d["PCC"].values, X, d["SE_PCC"].values ** 2,
                        d["study_id"].values)
    fat_b, fat_p = pet.loc["SE", "coef"], pet.loc["SE", "p"]
    pet_b, pet_p = pet.loc["const", "coef"], pet.loc["const", "p"]
    log(f"  FAT斜率={fat_b:+.3f}{star(fat_p)} p={fat_p:.4f}   "
        f"PET截距={pet_b:+.4f}{star(pet_p)} p={pet_p:.4f}")
    rows4.append(dict(维度=TNAME[tg], Egger_p=round(eb["egger_p"], 4),
                      Begg_p=round(eb["begg_p"], 4), FAT=round(fat_b, 3),
                      FAT_p=round(fat_p, 4), PET=round(pet_b, 4),
                      PET_p=round(pet_p, 4), k=len(d)))
    if pet_p < 0.05:
        Xp = pd.DataFrame({"const": 1.0, "Var": d["SE_PCC"].values ** 2},
                          index=d.index)
        pe, _, _ = rve_wls(d["PCC"].values, Xp, d["SE_PCC"].values ** 2,
                           d["study_id"].values)
        log(f"  PEESE={pe.loc['const','coef']:+.4f}{star(pe.loc['const','p'])} "
            f"p={pe.loc['const','p']:.4f}")
        rows4[-1]["PEESE"] = round(pe.loc["const", "coef"], 4)
        rows4[-1]["PEESE_p"] = round(pe.loc["const", "p"], 4)
pd.DataFrame(rows4).to_csv(os.path.join(OUT, "table4_pub_bias.csv"),
                           index=False, encoding="utf-8-sig")

# ================================================ 弹性轨
log("\n" + "=" * 76)
log("弹性轨（|e|<1；优先 reported/full，再 converted，最后 semi 近似）")
log("=" * 76)
el = df[df["elasticity"].abs() < 1].copy()
PRIO = {"reported": 0, "full": 0, "converted": 1, "semi": 2}
rows_e = []
for tg in TARGETS:
    for p in PATHS:
        cell = el[(el["Target"] == tg) & (el["Path"] == p)].copy()
        med, k, etype, ids = np.nan, 0, "none", ""
        for tier in [0, 1, 2]:
            sub = cell[cell["elast_type"].map(PRIO).eq(tier)]
            if len(sub):
                med = sub["elasticity"].median()
                k = len(sub)
                etype = {0: "full/reported", 1: "converted", 2: "semi"}[tier]
                ids = ";".join(sub["study_id"].str[:18].unique()[:8])
                break
        rows_e.append(dict(Target=tg, Path=p, k_elast=k, elast_type=etype,
                           elast_median=round(med, 4) if k else np.nan,
                           n_studies=cell["study_id"].nunique(), ids=ids))
        if k:
            log(f"{TNAME[tg]:6s} {p}: {med:+.4f} [{etype}] k={k}")
pd.DataFrame(rows_e).to_csv(os.path.join(OUT, "elasticity_track_v3.csv"),
                            index=False, encoding="utf-8-sig")

# ================================================ 森林图（文献层均值）
for tg in TARGETS:
    d = trim_iqr3(df[df["Target"] == tg])
    if len(d) < 3:
        continue
    aggd = d.groupby("study_id").agg(
        PCC=("PCC", "mean"), SE=("SE_PCC", "mean"),
        Path=("Path", lambda s: s.mode()[0]),
        author=("author_year", "first")).sort_values(["Path", "author"])
    r = rve_pool(d["PCC"].values, d["SE_PCC"].values ** 2, d["study_id"].values)
    kk = len(aggd)
    colors = {"MCI": "#1f77b4", "AMS": "#d62728", "AML": "#2ca02c"}
    plt.figure(figsize=(9, max(4, 0.35 * kk)))
    ypos = np.arange(kk, 0, -1)
    for p in PATHS:
        msk = (aggd["Path"] == p).values
        if msk.sum():
            plt.errorbar(aggd["PCC"][msk], ypos[msk],
                         xerr=1.96 * aggd["SE"][msk], fmt="o", ms=4,
                         color=colors[p], ecolor="gray", capsize=2, label=p)
    plt.axvline(0, color="black", lw=1)
    plt.axvline(r["mu"], color="red", ls="--",
                label=f"RVE合并={r['mu']:.3f}{star(r['pval'])}")
    plt.axvspan(r["ci"][0], r["ci"][1], color="red", alpha=0.12)
    plt.yticks(ypos, aggd["author"], fontsize=7)
    plt.xlabel("PCC（文献内多效应量均值展示）")
    plt.title(f"森林图（v3多效应量）：{TNAME[tg]}  k={r['k']}条/{r['m']}篇")
    plt.legend(loc="lower right", fontsize=8)
    plt.grid(axis="x", ls=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, f"forest_{tg}_v3.png"), dpi=300)
    plt.close()

with open(os.path.join(OUT, "7-multilevel-meta-results.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")
log("\n完成，输出至 results/meta_v3/")
