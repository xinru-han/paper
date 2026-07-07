# -*- coding: utf-8 -*-
"""SHAP 关键因素识别: 用全训练期(2004-2023)拟合LightGBM, 解释2015-2024预测
输出: 全局重要性表/图, 依赖图(前6因素), 分作物重要性
"""
import os, sys, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings("ignore")
from common import load_panel, feature_cols, encode_categories, OUTDIR

import lightgbm as lgb
import shap

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
os.makedirs(f"{OUTDIR}/figures", exist_ok=True)

CN = {  # 图表用中文名
    "L1_net_profit": "上年净利润", "L1_profit_margin": "上年成本利润率",
    "L1_sale_price": "上年出售价格", "L1_total_cost": "上年总成本",
    "L1_yield_main": "上年亩产", "L1_revenue": "上年产值",
    "L1_cost_yoy": "上年成本同比", "L1_price_yoy": "上年售价同比",
    "L1_cost_land": "上年土地成本", "L1_cost_labor": "上年人工成本",
    "L1_cost_fert": "上年化肥费", "L1_wage_day": "上年劳动日工价",
    "L1_land_rent": "上年流转地租金", "L1_s_land": "上年土地成本份额",
    "L1_s_labor": "上年人工成本份额", "L1_s_fert": "上年化肥成本份额",
    "L1_loss": "上年是否亏损", "L1_cash_income": "上年现金收益",
    "L2_net_profit": "前年净利润", "trend3_net_profit": "净利润3年趋势",
    "trend3_sale_price": "售价3年趋势", "trend3_total_cost": "成本3年趋势",
    "trend3_yield_main": "亩产3年趋势",
    "in_urea": "尿素价格", "in_urea_yoy": "尿素价格同比",
    "in_npk_cl": "复合肥价格", "in_npk_cl_yoy": "复合肥价格同比",
    "in_dap": "磷酸二铵价格", "in_abc": "碳铵价格", "in_ssp": "过磷酸钙价格",
    "in_mulch_film": "地膜价格", "in_chlorpyrifos": "农药(毒死蜱)价格",
    "in_machine_tillage": "机耕费", "in_machine_harvest": "机收费",
    "gp_pre_mean": "播前收购价", "gp_grow_mean": "生长季收购价",
    "gp_pre_yoy": "播前收购价同比",
    "rp_pre_mean": "成品粮零售价(1-9月)", "rp_pre_yoy": "成品粮零售价同比",
    "rp_q1_mean": "成品粮零售价(一季度)", "rp_q1_yoy": "零售价一季度同比",
    "temp_grow": "生长季气温", "temp_ano_grow": "生长季气温距平",
    "temp_ano_absmax": "气温距平极值", "prec_grow": "生长季降水",
    "prec_ano_grow": "生长季降水距平", "prec_ano_absmax": "降水距平极值",
    "trend": "时间趋势", "policy_corn_reform": "玉米临储改革",
    "policy_min_price": "最低收购价作物", "crop_code": "作物",
    "province_code": "省份", "region_code": "区域",
    "L1_sale_price": "上年出售价格", "L1_fert_kg": "上年化肥折纯用量",
    "L1_labor_days": "上年用工天数",
}

df = load_panel()
df, cat_codes = encode_categories(df)
feats = feature_cols(df) + cat_codes
test = df[df.year >= 2015]

params = dict(n_estimators=800, learning_rate=0.03, num_leaves=15, subsample=0.8,
              colsample_bytree=0.8, random_state=42, n_jobs=8, verbose=-1)
# 解释模型: 训练到2023(解释2015-2024整体驱动因素; 预测性能已由滚动验证保证)
tr = df[df.year <= 2023]
mr = lgb.LGBMRegressor(**params).fit(tr[feats], tr["net_profit"])
mc = lgb.LGBMClassifier(**params).fit(tr[feats], tr["loss"])

def shap_table(model, X, name):
    ex = shap.TreeExplainer(model)
    sv = ex.shap_values(X)
    if isinstance(sv, list):
        sv = sv[1]
    imp = pd.DataFrame({"feature": feats,
                        "mean_abs_shap": np.abs(sv).mean(0)}).sort_values(
        "mean_abs_shap", ascending=False)
    imp["feature_cn"] = imp["feature"].map(CN).fillna(imp["feature"])
    imp.to_csv(f"{OUTDIR}/tables/shap_importance_{name}.csv", index=False, encoding="utf-8-sig")
    # summary 图
    Xp = X.copy(); Xp.columns = [CN.get(c, c) for c in X.columns]
    plt.figure()
    shap.summary_plot(sv, Xp, max_display=20, show=False)
    plt.tight_layout()
    plt.savefig(f"{OUTDIR}/figures/shap_summary_{name}.png", dpi=200)
    plt.close("all")
    return sv, imp

Xte = test[feats]
sv_r, imp_r = shap_table(mr, Xte, "reg")
sv_c, imp_c = shap_table(mc, Xte, "clf")
print("== 净利润 SHAP top15 ==\n", imp_r.head(15)[["feature_cn", "mean_abs_shap"]].to_string(index=False))
print("== 亏损 SHAP top15 ==\n", imp_c.head(15)[["feature_cn", "mean_abs_shap"]].to_string(index=False))

# 依赖图: 前6个非类别特征
top6 = [f for f in imp_c["feature"] if f not in cat_codes][:6]
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for ax, f in zip(axes.ravel(), top6):
    j = feats.index(f)
    ax.scatter(Xte[f], sv_c[:, j], s=8, alpha=0.5)
    ax.set_xlabel(CN.get(f, f)); ax.set_ylabel("SHAP值(亏损)")
    ax.axhline(0, color="grey", lw=0.5)
plt.tight_layout()
plt.savefig(f"{OUTDIR}/figures/shap_dependence_top6.png", dpi=200)
plt.close("all")

# 分作物重要性(亏损模型)
rows = []
for crop in test["crop"].unique():
    mask = (test["crop"] == crop).values
    if mask.sum() < 20:
        continue
    a = np.abs(sv_c[mask]).mean(0)
    top = pd.Series(a, index=feats).nlargest(8)
    for f, v in top.items():
        rows.append({"crop": crop, "feature": f, "feature_cn": CN.get(f, f), "mean_abs_shap": v})
pd.DataFrame(rows).to_csv(f"{OUTDIR}/tables/shap_by_crop.csv", index=False, encoding="utf-8-sig")
print("saved shap tables & figures")
