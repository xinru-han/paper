# -*- coding: utf-8 -*-
"""预警体系: 集成最优模型 → 亏损概率分级(蓝黄橙红) → 成本敏感阈值校准
→ 2023/2024样本外预警演示表 + 命中率评估
"""
import os, sys, glob, warnings
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings("ignore")
from common import OUTDIR, eval_classification

CROP_CN = {"corn": "玉米", "wheat": "小麦", "soybean": "大豆",
           "rice_early_indica": "早籼稻", "rice_mid_indica": "中籼稻",
           "rice_late_indica": "晚籼稻", "rice_japonica": "粳稻"}

# ---- 1. 汇总所有模型预测 ----
preds = []
for f in glob.glob(f"{OUTDIR}/preds/*.csv"):
    preds.append(pd.read_csv(f))
P = pd.concat(preds, ignore_index=True)
P = P.dropna(subset=["p_loss"])
models = P["model"].unique()
print("models:", models)

# ---- 2. 选择集成成员: 按2015-2022(校准期)AUC排序取前3 ----
calib = P[P.year <= 2022]
auc = {}
from sklearn.metrics import roc_auc_score
for m in models:
    s = calib[calib.model == m]
    if s["loss_true"].nunique() > 1:
        auc[m] = roc_auc_score(s["loss_true"], s["p_loss"])
rank = sorted(auc.items(), key=lambda kv: -kv[1])
print("校准期AUC排名:", [(m, round(a, 3)) for m, a in rank])
top3 = [m for m, _ in rank[:3]]

ens = (P[P.model.isin(top3)]
       .groupby(["crop", "province", "year"])
       .agg(p_loss=("p_loss", "mean"), y_pred=("y_pred", "mean"),
            y_true=("y_true", "first"), loss_true=("loss_true", "first"))
       .reset_index())
ens["model"] = "Ensemble"

# ---- 3. 成本敏感阈值: 漏报代价3×误报, 在校准期上找最优主阈值 ----
ec = ens[ens.year <= 2022]
best_t, best_cost = 0.5, np.inf
for t in np.arange(0.05, 0.95, 0.01):
    fn = ((ec.p_loss <= t) & (ec.loss_true == 1)).sum()
    fp = ((ec.p_loss > t) & (ec.loss_true == 0)).sum()
    cost = 3 * fn + fp
    if cost < best_cost:
        best_cost, best_t = cost, t
print(f"成本敏感主阈值(漏报:误报=3:1): {best_t:.2f}")

def grade(p, t):
    """以主阈值t为橙界, 分四级"""
    if p >= min(t + 0.2, 0.95):
        return "红色"
    if p >= t:
        return "橙色"
    if p >= max(t - 0.2, 0.05):
        return "黄色"
    return "蓝色"

ens["预警等级"] = ens["p_loss"].apply(lambda p: grade(p, best_t))

# ---- 4. 集成模型全期表现 ----
rows = []
for t in sorted(ens.year.unique()):
    s = ens[ens.year == t]
    rows.append({"year": t, "n": len(s),
                 **eval_classification(s["loss_true"].values, s["p_loss"].values)})
yr = pd.DataFrame(rows)
yr.to_csv(f"{OUTDIR}/tables/warning_ensemble_yearly.csv", index=False)
print(yr.round(3).to_string(index=False))

# 分级命中率(全测试期)
tab = (ens.groupby("预警等级")
       .agg(n=("loss_true", "size"), 实际亏损率=("loss_true", "mean"),
            平均预测亏损概率=("p_loss", "mean"),
            平均实际净利润=("y_true", "mean"))
       .reindex(["红色", "橙色", "黄色", "蓝色"]))
tab.to_csv(f"{OUTDIR}/tables/warning_grade_validation.csv", encoding="utf-8-sig")
print("\n== 预警分级验证(2015-2024) ==\n", tab.round(3).to_string())

# ---- 5. 2023/2024 演示表 ----
for yy in (2023, 2024):
    demo = ens[ens.year == yy].copy()
    demo["作物"] = demo["crop"].map(CROP_CN)
    demo = demo.sort_values("p_loss", ascending=False)
    out = demo[["作物", "province", "p_loss", "y_pred", "预警等级", "y_true", "loss_true"]]
    out.columns = ["作物", "省份", "亏损概率", "预测净利润(元/亩)", "预警等级",
                   "实际净利润(元/亩)", "实际亏损"]
    out.to_csv(f"{OUTDIR}/tables/warning_demo_{yy}.csv", index=False, encoding="utf-8-sig")
    hit = ((demo["预警等级"].isin(["红色", "橙色"])) == (demo["loss_true"] == 1)).mean()
    rec = demo.loc[demo.loss_true == 1, "预警等级"].isin(["红色", "橙色"]).mean() if demo.loss_true.sum() else np.nan
    print(f"\n{yy}: n={len(demo)}, 橙红==亏损 一致率={hit:.3f}, 亏损召回率={rec:.3f}")
    print(demo.head(10)[["作物", "province", "p_loss", "预警等级", "y_true"]].to_string(index=False))

ens.to_csv(f"{OUTDIR}/preds/ensemble.csv", index=False, encoding="utf-8-sig")
