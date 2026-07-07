# -*- coding: utf-8 -*-
"""TabPFN (表格基础模型, 上下文学习) 回归+分类, 扩窗滚动验证
样本<10000, 特征~70 → 适用范围内; CPU推理
"""
import os, sys, warnings
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings("ignore")
from common import (load_panel, feature_cols, rolling_splits, encode_categories,
                    eval_regression, eval_classification, save_preds, OUTDIR)

from tabpfn import TabPFNRegressor, TabPFNClassifier

df = load_panel()
df, cat_codes = encode_categories(df)
feats = feature_cols(df) + cat_codes

reg_rows, clf_rows, all_preds = [], [], []
for t, tri, tei in rolling_splits(df):
    tr, te = df.loc[tri], df.loc[tei]
    Xtr, Xte = tr[feats].values, te[feats].values
    reg = TabPFNRegressor(device="cpu", random_state=42, ignore_pretraining_limits=True)
    reg.fit(Xtr, tr["net_profit"].values)
    pr = reg.predict(Xte)
    clf = TabPFNClassifier(device="cpu", random_state=42, ignore_pretraining_limits=True)
    clf.fit(Xtr, tr["loss"].values)
    pc = clf.predict_proba(Xte)[:, 1]
    reg_rows.append({"model": "TabPFN", "year": t, "n": len(te),
                     **eval_regression(te["net_profit"].values, pr)})
    clf_rows.append({"model": "TabPFN", "year": t, "n": len(te),
                     **eval_classification(te["loss"].values, pc)})
    pred = te[["crop", "province", "year"]].copy()
    pred["model"] = "TabPFN"
    pred["y_true"] = te["net_profit"].values; pred["loss_true"] = te["loss"].values
    pred["y_pred"] = pr; pred["p_loss"] = pc
    all_preds.append(pred)
    print("done", t, round(reg_rows[-1]["rmse"], 1), round(clf_rows[-1]["auc"], 3), flush=True)

pd.DataFrame(reg_rows).to_csv(f"{OUTDIR}/tables/yearly_reg_tabpfn.csv", index=False)
pd.DataFrame(clf_rows).to_csv(f"{OUTDIR}/tables/yearly_clf_tabpfn.csv", index=False)
save_preds(pd.concat(all_preds), "tabpfn")
r = pd.DataFrame(reg_rows); c = pd.DataFrame(clf_rows)
print("REG avg:", {m: round(np.average(r[m], weights=r.n), 3) for m in ["rmse", "mae", "r2", "sign_acc"]})
print("CLF avg:", {m: round(np.average(c[m].dropna(), weights=c.loc[c[m].notna(), 'n']), 3) for m in ["auc", "pr_auc", "brier", "acc"]})
