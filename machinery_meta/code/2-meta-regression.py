# -*- coding: utf-8 -*-
"""WLS Meta回归（路径异质性）与 FAT-PET-PEESE 发表偏倚检验。

相对v1的更新：
  - 使用check后重算的PCC；主分析仅机械化样本(41条)；
  - Meta回归按维度分Panel：PCC ~ AMS + AML + LogN（MCI为基准组），
    随机效应方差(tau^2, REML)进入权重 w=1/(v+tau^2)，文献层面聚类稳健SE；
  - FAT-PET采用加权(1/v)回归+聚类稳健SE；PET显著时报告PEESE；
  - 输出漏斗图；剔除了v1中基于虚构数据的GPR模块与过拟合的SHAP模块。
"""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "results", "meta")
os.makedirs(OUT, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(BASE, ".matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for f in ["Noto Sans CJK SC", "Noto Serif CJK SC", "AR PL SungtiL GB"]:
    if f in {x.name for x in font_manager.fontManager.ttflist}:
        plt.rcParams["font.sans-serif"] = [f, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False

log_lines = []


def log(msg=""):
    print(msg)
    log_lines.append(str(msg))


def tau2_reml(y, v, tol=1e-10, maxit=200):
    tau2 = max(np.var(y, ddof=1) - np.mean(v), 0.0) if len(y) > 1 else 0.0
    for _ in range(maxit):
        w = 1.0 / (v + tau2)
        mu = np.sum(w * y) / np.sum(w)
        num = np.sum(w**2 * ((y - mu) ** 2 - v)) + np.sum(w**2) / np.sum(w) * tau2
        new = max(num / np.sum(w**2), 0.0)
        if abs(new - tau2) < tol:
            return new
        tau2 = new
    return tau2


def star(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


df = pd.read_csv(os.path.join(BASE, "data", "meta_base_dataset.csv"),
                 encoding="utf-8-sig")
df = df.dropna(subset=["PCC", "SE_PCC"])
mech = df[df["Mech"] == 1].copy()
TARGETS = ["Yield", "Area", "Efficiency"]
TNAME = {"Yield": "粮食单产", "Area": "播种面积", "Efficiency": "生产效率"}

# ================================================= 表3 WLS Meta回归
log("=" * 72)
log("表3 WLS Meta回归（基准组=农机资本投入MCI；文献层面聚类稳健SE）")
log("=" * 72)
rows3 = []
for tg in TARGETS:
    d = mech[mech["Target"] == tg].copy()
    d["AMS"] = (d["Path"] == "AMS").astype(float)
    d["AML"] = (d["Path"] == "AML").astype(float)
    v = d["SE_PCC"].values ** 2
    tau2 = tau2_reml(d["PCC"].values, v)
    w = 1.0 / (v + tau2)
    Xcols = ["AMS", "AML", "LogN"]
    # 子组过小时自动降维（虚拟变量全0/全1无法识别）
    Xcols = [c for c in Xcols if d[c].std() > 0]
    X = sm.add_constant(d[Xcols].astype(float))
    if len(d) < max(10, 3 * (len(Xcols) + 1)):
        gm = d.groupby("Path")["PCC"].agg(["count", "mean"]).round(3)
        log(f"\n[{TNAME[tg]}] k={len(d)} 不足以支持Meta回归（避免过拟合），"
            f"仅报告分路径描述统计：\n{gm.to_string()}")
        continue
    groups = d["作者_年份"].astype("category").cat.codes
    res = sm.WLS(d["PCC"].astype(float), X, weights=w).fit(
        cov_type="cluster", cov_kwds={"groups": groups})
    log(f"\n[{TNAME[tg]}] k={len(d)}, tau2(REML)={tau2:.4f}")
    for name in res.params.index:
        b, s, p = res.params[name], res.bse[name], res.pvalues[name]
        log(f"  {name:8s} {b:+.4f}{star(p):<3s} (SE={s:.4f}, p={p:.4f})")
        rows3.append(dict(维度=TNAME[tg], 变量=name, 系数=round(b, 4),
                          SE=round(s, 4), p值=round(p, 4), 显著性=star(p),
                          k=len(d)))
pd.DataFrame(rows3).to_csv(os.path.join(OUT, "table3_meta_regression.csv"),
                           index=False, encoding="utf-8-sig")

# ================================================= 表4 FAT-PET-PEESE
log("\n" + "=" * 72)
log("表4 FAT-PET-PEESE 发表偏倚检验（加权WLS，文献层面聚类稳健SE）")
log("=" * 72)
rows4 = []
for tg in TARGETS:
    d = mech[mech["Target"] == tg].copy()
    if len(d) < 5:
        log(f"\n[{TNAME[tg]}] k={len(d)} 过小，检验功效不足，仅供参考")
    y = d["PCC"].astype(float)
    se = d["SE_PCC"].astype(float)
    wgt = 1.0 / se**2
    groups = d["作者_年份"].astype("category").cat.codes
    # FAT-PET: PCC = b0 + b1*SE
    X = sm.add_constant(se.rename("SE"))
    pet = sm.WLS(y, X, weights=wgt).fit(cov_type="cluster",
                                        cov_kwds={"groups": groups})
    fat_b, fat_p = pet.params["SE"], pet.pvalues["SE"]
    pet_b, pet_p = pet.params["const"], pet.pvalues["const"]
    log(f"\n[{TNAME[tg]}] k={len(d)}")
    log(f"  FAT（漏斗不对称）: 斜率={fat_b:+.3f}{star(fat_p)} p={fat_p:.4f}"
        + ("  → 存在发表偏倚" if fat_p < 0.05 else "  → 未见显著偏倚"))
    log(f"  PET（校正后效应）: 截距={pet_b:+.4f}{star(pet_p)} p={pet_p:.4f}")
    rows4.append(dict(维度=TNAME[tg], 检验="FAT", 系数=round(fat_b, 3),
                      p值=round(fat_p, 4), 显著性=star(fat_p), k=len(d)))
    rows4.append(dict(维度=TNAME[tg], 检验="PET", 系数=round(pet_b, 4),
                      p值=round(pet_p, 4), 显著性=star(pet_p), k=len(d)))
    if pet_p < 0.05:
        Xp = sm.add_constant((se**2).rename("Var"))
        peese = sm.WLS(y, Xp, weights=wgt).fit(cov_type="cluster",
                                               cov_kwds={"groups": groups})
        pb, pp = peese.params["const"], peese.pvalues["const"]
        log(f"  PEESE（推荐真实效应）: {pb:+.4f}{star(pp)} p={pp:.4f}")
        rows4.append(dict(维度=TNAME[tg], 检验="PEESE", 系数=round(pb, 4),
                          p值=round(pp, 4), 显著性=star(pp), k=len(d)))
    # 漏斗图
    plt.figure(figsize=(6, 5))
    plt.scatter(y, se, s=28, alpha=0.75, edgecolors="k", linewidths=0.4)
    mu = np.average(y, weights=wgt)
    ymax = se.max() * 1.1
    xs = np.linspace(0, ymax, 50)
    plt.plot([mu, mu], [0, ymax], "r--", lw=1, label=f"加权均值={mu:.3f}")
    plt.plot(mu - 1.96 * xs, xs, "k:", lw=1)
    plt.plot(mu + 1.96 * xs, xs, "k:", lw=1, label="伪95%界")
    plt.gca().invert_yaxis()
    plt.xlabel("PCC"); plt.ylabel("SE(PCC)")
    plt.title(f"漏斗图：{TNAME[tg]} (k={len(d)})")
    plt.legend(fontsize=8); plt.grid(alpha=0.4); plt.tight_layout()
    plt.savefig(os.path.join(OUT, f"funnel_{tg}.png"), dpi=300)
    plt.close()
pd.DataFrame(rows4).to_csv(os.path.join(OUT, "table4_fat_pet_peese.csv"),
                           index=False, encoding="utf-8-sig")

log("\n漏斗图已输出至 results/meta/")
with open(os.path.join(OUT, "2-meta-regression-results.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")
