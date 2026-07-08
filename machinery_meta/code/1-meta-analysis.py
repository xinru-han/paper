# -*- coding: utf-8 -*-
"""随机效应Meta分析（check后数据，41条机械化主分析样本）。

相对v1的方法升级（对标当前meta分析规范）：
  - tau^2 由 DerSimonian-Laird 升级为 REML（保留DL作对照）；
  - 合并效应置信区间采用 Knapp-Hartung 校正（t分布）；
  - 报告 95% 预测区间（真实效应分布，Riley et al. 2011）；
  - 敏感性：留一法(leave-one-out)、IQR提纯、简单平均/样本量加权对照；
  - 弹性轨：按 路径×维度 取全弹性中位数（|e|<1），供CASM参数映射。
输出：results/meta/ 下的 txt、csv 表与 png 图。
"""
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "results", "meta")
os.makedirs(OUT, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(BASE, ".matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for f in ["Noto Sans CJK SC", "Noto Serif CJK SC", "AR PL SungtiL GB",
          "AR PL KaitiM GB", "WenQuanYi Zen Hei", "SimHei"]:
    if f in {x.name for x in font_manager.fontManager.ttflist}:
        plt.rcParams["font.sans-serif"] = [f, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False

log_lines = []


def log(msg=""):
    print(msg)
    log_lines.append(str(msg))


# ------------------------------------------------------------------ 数据
df = pd.read_csv(os.path.join(BASE, "data", "meta_base_dataset.csv"),
                 encoding="utf-8-sig")
df = df.dropna(subset=["PCC", "SE_PCC"])
mech = df[df["Mech"] == 1].copy()
log(f"机械化主分析样本 k={len(mech)}（全样本56条中剔除非机械化核心变量15条）")

TARGETS = ["Yield", "Area", "Efficiency"]
PATHS = ["MCI", "AMS", "AML"]
TNAME = {"Yield": "粮食单产", "Area": "播种面积", "Efficiency": "生产效率"}
PNAME = {"MCI": "农机资本投入(MCI)", "AMS": "农机社会化服务(AMS)",
         "AML": "综合机械化水平(AML)"}


# ------------------------------------------------------------- 估计函数
def tau2_reml(y, v, tol=1e-10, maxit=200):
    """REML估计tau^2（仅截距模型）。"""
    tau2 = max(np.var(y, ddof=1) - np.mean(v), 0.0) if len(y) > 1 else 0.0
    for _ in range(maxit):
        w = 1.0 / (v + tau2)
        mu = np.sum(w * y) / np.sum(w)
        num = np.sum(w**2 * ((y - mu) ** 2 - v)) + np.sum(w**2) / np.sum(w) * tau2
        new = max(num / np.sum(w**2), 0.0)
        if abs(new - tau2) < tol:
            tau2 = new
            break
        tau2 = new
    return tau2


def tau2_dl(y, v):
    w = 1.0 / v
    mu = np.sum(w * y) / np.sum(w)
    Q = np.sum(w * (y - mu) ** 2)
    C = np.sum(w) - np.sum(w**2) / np.sum(w)
    return max((Q - (len(y) - 1)) / C, 0.0) if C > 0 else 0.0, Q


def pool(y, v, method="REML", knha=True):
    """随机效应合并；返回 dict。"""
    k = len(y)
    tau2_d, Q = tau2_dl(y, v)
    tau2 = tau2_reml(y, v) if method == "REML" and k > 1 else tau2_d
    w = 1.0 / (v + tau2)
    mu = np.sum(w * y) / np.sum(w)
    se = np.sqrt(1.0 / np.sum(w))
    if knha and k > 1:  # Knapp-Hartung 方差校正 + t 分布
        s2 = np.sum(w * (y - mu) ** 2) / ((k - 1) * np.sum(w))
        se = np.sqrt(max(s2, 0.0)) if s2 > 0 else se
        crit = stats.t.ppf(0.975, k - 1)
        pval = 2 * stats.t.sf(abs(mu / se), k - 1) if se > 0 else np.nan
    else:
        crit = 1.96
        pval = 2 * stats.norm.sf(abs(mu / se)) if se > 0 else np.nan
    dfq = k - 1
    I2 = max(0.0, (Q - dfq) / Q) * 100 if Q > 0 and k > 1 else 0.0
    # 95%预测区间（Riley et al. 2011, t_{k-2}）
    if k > 2:
        pi_se = np.sqrt(tau2 + se**2)
        tcrit = stats.t.ppf(0.975, k - 2)
        pi = (mu - tcrit * pi_se, mu + tcrit * pi_se)
    else:
        pi = (np.nan, np.nan)
    return dict(k=k, mu=mu, se=se, ci=(mu - crit * se, mu + crit * se),
                pval=pval, tau2=tau2, tau2_dl=tau2_d, Q=Q, I2=I2, pi=pi)


def star(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def fmt(r):
    return (f"k={r['k']:>2d}  PCC={r['mu']:+.3f}{star(r['pval']):<3s} "
            f"[{r['ci'][0]:+.3f},{r['ci'][1]:+.3f}] (KH)  p={r['pval']:.4f}  "
            f"tau2={r['tau2']:.4f}  I2={r['I2']:.1f}%  "
            f"PI=[{r['pi'][0]:+.3f},{r['pi'][1]:+.3f}]")


# ------------------------------------------------- 表1：基准综合效应
log("\n" + "=" * 72)
log("表1 基准综合效应（REML + Knapp-Hartung；全体机械化样本）")
log("=" * 72)
rows1 = []
for tg in TARGETS:
    d = mech[mech["Target"] == tg]
    r = pool(d["PCC"].values, d["SE_PCC"].values ** 2)
    log(f"{TNAME[tg]:6s} {fmt(r)}")
    rows1.append(dict(维度=TNAME[tg], k=r["k"], 合并PCC=round(r["mu"], 3),
                      显著性=star(r["pval"]), CI下=round(r["ci"][0], 3),
                      CI上=round(r["ci"][1], 3), p值=round(r["pval"], 4),
                      tau2=round(r["tau2"], 4), I2=round(r["I2"], 1),
                      Q=round(r["Q"], 2),
                      预测区间下=round(r["pi"][0], 3), 预测区间上=round(r["pi"][1], 3)))
pd.DataFrame(rows1).to_csv(os.path.join(OUT, "table1_overall_effects.csv"),
                           index=False, encoding="utf-8-sig")

# ------------------------------------------------- 表2：分路径子组
log("\n" + "=" * 72)
log("表2 分路径子组Meta分析（REML + Knapp-Hartung）")
log("=" * 72)
rows2 = []
for tg in TARGETS:
    d_all = mech[mech["Target"] == tg]
    r = pool(d_all["PCC"].values, d_all["SE_PCC"].values ** 2)
    rows2.append(dict(维度=TNAME[tg], 路径="全样本", k=r["k"],
                      合并PCC=round(r["mu"], 3), 显著性=star(r["pval"]),
                      CI下=round(r["ci"][0], 3), CI上=round(r["ci"][1], 3),
                      I2=round(r["I2"], 1)))
    log(f"{TNAME[tg]} 全样本      {fmt(r)}")
    for p in PATHS:
        d = d_all[d_all["Path"] == p]
        if len(d) == 0:
            continue
        if len(d) == 1:
            y, se = d["PCC"].iloc[0], d["SE_PCC"].iloc[0]
            pv = 2 * stats.norm.sf(abs(y / se))
            rows2.append(dict(维度=TNAME[tg], 路径=PNAME[p], k=1,
                              合并PCC=round(y, 3), 显著性=star(pv),
                              CI下=round(y - 1.96 * se, 3),
                              CI上=round(y + 1.96 * se, 3), I2=np.nan))
            log(f"{TNAME[tg]} {p:4s} k= 1  PCC={y:+.3f}{star(pv)} (单篇，谨慎解释)")
            continue
        r = pool(d["PCC"].values, d["SE_PCC"].values ** 2)
        rows2.append(dict(维度=TNAME[tg], 路径=PNAME[p], k=r["k"],
                          合并PCC=round(r["mu"], 3), 显著性=star(r["pval"]),
                          CI下=round(r["ci"][0], 3), CI上=round(r["ci"][1], 3),
                          I2=round(r["I2"], 1)))
        log(f"{TNAME[tg]} {p:4s} {fmt(r)}")
pd.DataFrame(rows2).to_csv(os.path.join(OUT, "table2_subgroup_by_path.csv"),
                           index=False, encoding="utf-8-sig")

# ------------------------------------------------- 表5：稳健性检验
log("\n" + "=" * 72)
log("表5 稳健性：IQR提纯 / 简单平均 / 样本量加权 / 留一法极值")
log("=" * 72)
rows5 = []
for tg in TARGETS:
    d = mech[mech["Target"] == tg]
    y, v = d["PCC"].values, d["SE_PCC"].values ** 2
    base = pool(y, v)
    # IQR 提纯
    q1, q3 = np.percentile(y, [25, 75])
    iqr = q3 - q1
    keep = (y >= q1 - 1.5 * iqr) & (y <= q3 + 1.5 * iqr)
    trim = pool(y[keep], v[keep]) if keep.sum() > 1 else base
    dropped = d.loc[~keep, "编号"].tolist()
    # 简单平均 / 样本量加权
    simple = y.mean()
    nw = np.nansum(d["N"].values * y) / np.nansum(d["N"].values)
    # 留一法
    loo = [pool(np.delete(y, i), np.delete(v, i))["mu"] for i in range(len(y))] \
        if len(y) > 2 else [base["mu"]]
    rows5.append(dict(维度=TNAME[tg], 基准REML=round(base["mu"], 3),
                      IQR提纯=round(trim["mu"], 3), IQR剔除数=int((~keep).sum()),
                      IQR剔除编号=";".join(dropped),
                      简单平均=round(simple, 3), 样本量加权=round(nw, 3),
                      留一法最小=round(min(loo), 3), 留一法最大=round(max(loo), 3)))
    log(f"{TNAME[tg]:6s} 基准={base['mu']:+.3f}  IQR提纯={trim['mu']:+.3f}"
        f"(剔{int((~keep).sum())}: {','.join(dropped) if dropped else '-'})  "
        f"简单平均={simple:+.3f}  N加权={nw:+.3f}  "
        f"留一法区间[{min(loo):+.3f},{max(loo):+.3f}]")
pd.DataFrame(rows5).to_csv(os.path.join(OUT, "table5_robustness.csv"),
                           index=False, encoding="utf-8-sig")

# ------------------------------------------------- 弹性轨（CASM参数）
log("\n" + "=" * 72)
log("弹性轨：路径×维度 弹性中位数（|e|<1；优先全弹性，缺失时以半弹性近似）")
log("=" * 72)
el = mech[mech["elasticity"].abs() < 1]
rows_e = []
for tg in TARGETS:
    for p in PATHS:
        cell = el[(el["Target"] == tg) & (el["Path"] == p)]
        full = cell[cell["elast_type"] == "full"]
        semi = cell[cell["elast_type"] == "semi"]
        if len(full):
            d, etype = full, "full"
        elif len(semi):
            d, etype = semi, "semi(近似)"
        else:
            d, etype = full, "none"
        med, k = (d["elasticity"].median(), len(d)) if len(d) else (np.nan, 0)
        rows_e.append(dict(Target=tg, Path=p, k_elast=k, elast_type=etype,
                           elast_median=round(med, 4) if k else np.nan,
                           ids=";".join(d["编号"]) if k else ""))
        if k:
            log(f"{TNAME[tg]:6s} {p}: 中位数={med:+.4f} [{etype}] "
                f"(k={k}: {','.join(d['编号'])})")
pd.DataFrame(rows_e).to_csv(os.path.join(OUT, "elasticity_track.csv"),
                            index=False, encoding="utf-8-sig")

# ------------------------------------------------- 森林图 / 累积图
def forest(tg):
    d = mech[mech["Target"] == tg].sort_values(["Path", "PubYear"]).reset_index(drop=True)
    r = pool(d["PCC"].values, d["SE_PCC"].values ** 2)
    k = len(d)
    colors = {"MCI": "#1f77b4", "AMS": "#d62728", "AML": "#2ca02c"}
    plt.figure(figsize=(9, max(4, 0.38 * k)))
    ypos = np.arange(k, 0, -1)
    for p in PATHS:
        m = d["Path"] == p
        if m.sum():
            plt.errorbar(d.loc[m, "PCC"], ypos[m.values],
                         xerr=1.96 * d.loc[m, "SE_PCC"], fmt="o",
                         color=colors[p], ecolor="gray", capsize=2,
                         markersize=4, label=PNAME[p])
    plt.axvline(0, color="black", lw=1)
    plt.axvline(r["mu"], color="red", ls="--",
                label=f"合并PCC={r['mu']:.3f} (REML+KH)")
    plt.axvspan(r["ci"][0], r["ci"][1], color="red", alpha=0.12)
    plt.axvspan(r["pi"][0], r["pi"][1], color="orange", alpha=0.07,
                label="95%预测区间")
    plt.yticks(ypos, d["作者_年份"], fontsize=8)
    plt.xlabel("Partial Correlation Coefficient (PCC)")
    plt.title(f"森林图：机械化对{TNAME[tg]}的影响 (k={k})")
    plt.legend(loc="lower right", fontsize=8)
    plt.grid(axis="x", ls=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, f"forest_{tg}.png"), dpi=300)
    plt.close()
    exp = d[["编号", "作者_年份", "Path", "PCC", "SE_PCC", "N"]].copy()
    exp["CI_L"] = exp["PCC"] - 1.96 * exp["SE_PCC"]
    exp["CI_U"] = exp["PCC"] + 1.96 * exp["SE_PCC"]
    exp["pooled"], exp["pooled_L"], exp["pooled_U"] = r["mu"], r["ci"][0], r["ci"][1]
    exp.to_csv(os.path.join(OUT, f"forest_{tg}_data.csv"),
               index=False, encoding="utf-8-sig")


def cumulative(tg):
    d = mech[mech["Target"] == tg].dropna(subset=["PubYear"]).sort_values("PubYear")
    if len(d) < 3:
        return
    mus, los, his, yrs = [], [], [], []
    for i in range(2, len(d) + 1):
        sub = d.iloc[:i]
        r = pool(sub["PCC"].values, sub["SE_PCC"].values ** 2)
        mus.append(r["mu"]); los.append(r["ci"][0]); his.append(r["ci"][1])
        yrs.append(int(sub["PubYear"].iloc[-1]))
    plt.figure(figsize=(8, 5))
    x = range(2, len(d) + 1)
    plt.plot(x, mus, "b-o", ms=4, label="累积合并PCC")
    plt.fill_between(x, los, his, color="blue", alpha=0.15, label="95% CI (KH)")
    plt.axhline(0, color="black", ls="--", lw=1)
    step = max(1, len(yrs) // 8)
    plt.xticks(list(x)[::step], [yrs[i] for i in range(0, len(yrs), step)])
    plt.xlabel("发表年份（累积）"); plt.ylabel("累积合并PCC")
    plt.title(f"累积Meta分析：{TNAME[tg]}")
    plt.legend(); plt.grid(alpha=0.4); plt.tight_layout()
    plt.savefig(os.path.join(OUT, f"cumulative_{tg}.png"), dpi=300)
    plt.close()
    pd.DataFrame(dict(order=list(x), year=yrs, pooled=mus, lo=los, hi=his)) \
        .to_csv(os.path.join(OUT, f"cumulative_{tg}_data.csv"),
                index=False, encoding="utf-8-sig")


for tg in TARGETS:
    forest(tg)
    cumulative(tg)
log("\n森林图与累积图已输出至 results/meta/")

with open(os.path.join(OUT, "1-meta-analysis-results.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")
