# -*- coding: utf-8 -*-
"""PySR 符号回归: 在2004-2014训练窗提炼简约预警公式, 2015-2024滚动评估
为可解释性只用少量核心特征(SHAP前列+经济直觉), 输出公式卡片
"""
import os, sys, warnings
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings("ignore")
from common import (load_panel, rolling_splits, eval_regression,
                    eval_classification, save_preds, OUTDIR)

# 精选可解释特征(元/亩、比率), 缺失少
CORE = ["L1_net_profit", "L1_profit_margin", "L1_sale_price", "L1_total_cost",
        "L1_cost_yoy", "L1_price_yoy", "rp_pre_yoy", "in_urea_yoy",
        "L1_s_land", "L1_s_labor", "temp_ano_grow", "prec_ano_grow"]

df = load_panel()
sub = df.dropna(subset=[c for c in CORE if not c.startswith(("rp_", "in_"))]).copy()
for c in CORE:
    sub[c] = sub[c].fillna(sub[c].median())

from pysr import PySRRegressor

def make_model(fname):
    return PySRRegressor(
        niterations=200, populations=24,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["neg"],
        maxsize=22, parsimony=0.003,
        elementwise_loss="loss(y, yhat) = (y - yhat)^2",
        model_selection="best",
        random_state=42, deterministic=True, parallelism="serial",
        temp_equation_file=False,
        output_directory=f"{OUTDIR}/models/pysr_{fname}",
        progress=False, verbosity=0)

# 只在 2004-2014 拟合一次(公式的意义在于稳定, 不逐年重拟), 2015-2024 全程外推
tr = sub[sub.year <= 2014]
te = sub[sub.year >= 2015]
Xtr, Xte = tr[CORE], te[CORE]

m = make_model("net_profit")
m.fit(Xtr.values, tr["net_profit"].values, variable_names=CORE)
pr = m.predict(Xte.values)
print("== 最优公式(净利润) ==")
print(m.get_best().equation if hasattr(m.get_best(), "equation") else m.get_best())
print(eval_regression(te["net_profit"].values, pr))

# 亏损概率: 用符号回归拟合净利润, 再用训练期残差分布把预测值转成P(净利润<0)
resid = tr["net_profit"].values - m.predict(Xtr.values)
sd = resid.std()
from scipy.stats import norm
pc = norm.cdf(0, loc=pr, scale=sd)
print("== 亏损概率(经由公式+残差正态) ==")
print(eval_classification(te["loss"].values, pc))

pred = te[["crop", "province", "year"]].copy()
pred["model"] = "PySR"
pred["y_true"] = te["net_profit"].values; pred["loss_true"] = te["loss"].values
pred["y_pred"] = pr; pred["p_loss"] = pc
save_preds(pred, "pysr")

# 分年指标
rows_r, rows_c = [], []
for t in sorted(te.year.unique()):
    s = pred[pred.year == t]
    rows_r.append({"model": "PySR", "year": t, "n": len(s),
                   **eval_regression(s["y_true"].values, s["y_pred"].values)})
    rows_c.append({"model": "PySR", "year": t, "n": len(s),
                   **eval_classification(s["loss_true"].values, s["p_loss"].values)})
pd.DataFrame(rows_r).to_csv(f"{OUTDIR}/tables/yearly_reg_pysr.csv", index=False)
pd.DataFrame(rows_c).to_csv(f"{OUTDIR}/tables/yearly_clf_pysr.csv", index=False)

# 公式表(帕累托前沿)输出
eqs = m.equations_[["complexity", "loss", "equation"]]
eqs.to_csv(f"{OUTDIR}/tables/pysr_equations.csv", index=False)
print(eqs.tail(8).to_string())
