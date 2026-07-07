# -*- coding: utf-8 -*-
"""论文图表: 描述性事实 + 模型对比 + 预警演示
fig1 净利润趋势(分作物) fig2 亏损率热图 fig3 分年AUC曲线
fig4 集成预测散点 fig5 预警分级校准(实际亏损率单调性)
"""
import os, sys, glob, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings("ignore")
from common import OUTDIR, PANEL

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
FIG = f"{OUTDIR}/figures"
os.makedirs(FIG, exist_ok=True)

CROP_CN = {"corn": "玉米", "wheat": "小麦", "soybean": "大豆",
           "rice_early_indica": "早籼稻", "rice_mid_indica": "中籼稻",
           "rice_late_indica": "晚籼稻", "rice_japonica": "粳稻"}

df = pd.read_csv(PANEL)
df["作物"] = df["crop"].map(CROP_CN)

# fig1 净利润趋势
fig, ax = plt.subplots(figsize=(9, 5))
for c, g in df.groupby("作物"):
    m = g.groupby("year")["net_profit"].mean()
    ax.plot(m.index, m.values, marker="o", ms=3, label=c)
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("年份"); ax.set_ylabel("平均净利润（元/亩）")
ax.legend(ncol=4, fontsize=9); ax.set_title("主要粮食作物省均净利润（2004–2024）")
plt.tight_layout(); plt.savefig(f"{FIG}/fig1_net_profit_trend.png", dpi=200); plt.close()

# fig2 亏损率热图 (作物×年)
piv = df.pivot_table(index="作物", columns="year", values="loss", aggfunc="mean")
fig, ax = plt.subplots(figsize=(11, 3.5))
im = ax.imshow(piv.values, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1)
ax.set_yticks(range(len(piv.index)), piv.index)
ax.set_xticks(range(0, len(piv.columns), 2), piv.columns[::2])
plt.colorbar(im, label="亏损省份占比")
ax.set_title("分作物亏损面（亏损省份占比，2004–2024）")
plt.tight_layout(); plt.savefig(f"{FIG}/fig2_loss_heatmap.png", dpi=200); plt.close()

# fig3 分年AUC曲线 (所有模型)
files = {"baselines": None, "ft": "FT-Transformer", "tabpfn": "TabPFN", "pysr": "PySR"}
frames = []
for stem in ["baselines", "ft", "tabpfn", "pysr"]:
    f = f"{OUTDIR}/tables/yearly_clf_{stem}.csv"
    if os.path.exists(f):
        frames.append(pd.read_csv(f))
if frames:
    ycl = pd.concat(frames)
    fig, ax = plt.subplots(figsize=(9, 5))
    for m, g in ycl.groupby("model"):
        ax.plot(g["year"], g["auc"], marker="o", ms=4, label=m)
    ax.set_xlabel("测试年份"); ax.set_ylabel("AUC"); ax.axhline(0.5, color="grey", ls="--", lw=0.7)
    ax.legend(fontsize=9); ax.set_title("亏损预测分年AUC（扩窗滚动验证）")
    plt.tight_layout(); plt.savefig(f"{FIG}/fig3_auc_by_year.png", dpi=200); plt.close()

# fig4/5 依赖 ensemble
ep = f"{OUTDIR}/preds/ensemble.csv"
if os.path.exists(ep):
    ens = pd.read_csv(ep)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(ens["y_true"], ens["y_pred"], s=10, alpha=0.5,
               c=(ens["loss_true"] == 1), cmap="coolwarm")
    lim = [ens[["y_true", "y_pred"]].min().min(), ens[["y_true", "y_pred"]].max().max()]
    ax.plot(lim, lim, "k--", lw=0.8); ax.axhline(0, color="grey", lw=0.5); ax.axvline(0, color="grey", lw=0.5)
    ax.set_xlabel("实际净利润（元/亩）"); ax.set_ylabel("集成预测（元/亩）")
    ax.set_title("集成模型样本外预测（2015–2024）")
    plt.tight_layout(); plt.savefig(f"{FIG}/fig4_ensemble_scatter.png", dpi=200); plt.close()

    order = ["蓝色", "黄色", "橙色", "红色"]
    g = ens.groupby("预警等级").agg(实际亏损率=("loss_true", "mean"), n=("loss_true", "size")).reindex(order)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    colors = ["#3b6fb6", "#e8c832", "#e88a2e", "#c8322e"]
    ax.bar(g.index, g["实际亏损率"], color=colors)
    for i, (v, n) in enumerate(zip(g["实际亏损率"], g["n"])):
        ax.text(i, v + 0.02, f"{v:.0%}\n(n={n})", ha="center", fontsize=9)
    ax.set_ylabel("实际亏损率"); ax.set_title("预警等级与实际亏损率（2015–2024 样本外）")
    plt.tight_layout(); plt.savefig(f"{FIG}/fig5_grade_calibration.png", dpi=200); plt.close()

print("figures saved:", os.listdir(FIG))
