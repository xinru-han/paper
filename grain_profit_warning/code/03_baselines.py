# -*- coding: utf-8 -*-
"""基准模型: FE-OLS/FE-Logit(计量基准) + 随机森林(对齐0429版) + XGBoost + LightGBM
扩窗滚动验证 2015-2024, 回归(net_profit)与分类(loss)双任务
输出: output/tables/model_comparison_{reg,clf}.csv, output/preds/*.csv
"""
import os, sys, warnings
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings("ignore")
from common import (load_panel, feature_cols, rolling_splits, encode_categories,
                    eval_regression, eval_classification, save_preds, OUTDIR)

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.impute import SimpleImputer
import xgboost as xgb
import lightgbm as lgb

os.makedirs(f"{OUTDIR}/tables", exist_ok=True)

df = load_panel()
df, cat_codes = encode_categories(df)
feats = feature_cols(df) + cat_codes
print(f"panel={df.shape}, features={len(feats)}")

reg_rows, clf_rows = [], []
all_preds = []

def run_year(t, tri, tei):
    tr, te = df.loc[tri], df.loc[tei]
    Xtr, Xte = tr[feats], te[feats]
    ytr_r, yte_r = tr["net_profit"].values, te["net_profit"].values
    ytr_c, yte_c = tr["loss"].values, te["loss"].values
    res = {}

    # ---- 线性基准 (省+作物哑变量≈FE, 中位数插补) ----
    imp = SimpleImputer(strategy="median", keep_empty_features=True)
    num = [c for c in feats if c not in cat_codes]
    Xtr_l = pd.DataFrame(imp.fit_transform(Xtr[num]), columns=num, index=tr.index)
    Xte_l = pd.DataFrame(imp.transform(Xte[num]), columns=num, index=te.index)
    for c in ["crop", "province"]:
        dtr = pd.get_dummies(tr[c], prefix=c)
        dte = pd.get_dummies(te[c], prefix=c).reindex(columns=dtr.columns, fill_value=0)
        Xtr_l, Xte_l = pd.concat([Xtr_l, dtr], axis=1), pd.concat([Xte_l, dte], axis=1)
    ols = LinearRegression().fit(Xtr_l, ytr_r)
    res["FE-OLS"] = ("reg", ols.predict(Xte_l))
    lg = LogisticRegression(max_iter=2000, C=1.0).fit(Xtr_l, ytr_c)
    res["FE-Logit"] = ("clf", lg.predict_proba(Xte_l)[:, 1])

    # ---- RF (对齐0429: n=100) ----
    Xtr_i = pd.DataFrame(imp.fit_transform(Xtr), columns=feats, index=tr.index)
    Xte_i = pd.DataFrame(imp.transform(Xte), columns=feats, index=te.index)
    rf_r = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=4).fit(Xtr_i, ytr_r)
    res["RF"] = ("reg", rf_r.predict(Xte_i))
    rf_c = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=4).fit(Xtr_i, ytr_c)
    res["RF"] = ("both", rf_r.predict(Xte_i), rf_c.predict_proba(Xte_i)[:, 1])

    # ---- XGBoost (原生缺失处理) ----
    xr = xgb.XGBRegressor(n_estimators=600, learning_rate=0.03, max_depth=4,
                          subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                          random_state=42, n_jobs=4).fit(Xtr, ytr_r)
    xc = xgb.XGBClassifier(n_estimators=600, learning_rate=0.03, max_depth=4,
                           subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                           random_state=42, n_jobs=4, eval_metric="logloss").fit(Xtr, ytr_c)
    res["XGB"] = ("both", xr.predict(Xte), xc.predict_proba(Xte)[:, 1])

    # ---- LightGBM ----
    lr = lgb.LGBMRegressor(n_estimators=800, learning_rate=0.03, num_leaves=15,
                           subsample=0.8, colsample_bytree=0.8, random_state=42,
                           n_jobs=4, verbose=-1).fit(Xtr, ytr_r)
    lc = lgb.LGBMClassifier(n_estimators=800, learning_rate=0.03, num_leaves=15,
                            subsample=0.8, colsample_bytree=0.8, random_state=42,
                            n_jobs=4, verbose=-1).fit(Xtr, ytr_c)
    res["LGBM"] = ("both", lr.predict(Xte), lc.predict_proba(Xte)[:, 1])

    for name, v in res.items():
        kind = v[0]
        if kind in ("reg", "both"):
            pr = v[1]
            reg_rows.append({"model": name, "year": t, "n": len(te), **eval_regression(yte_r, pr)})
        if kind in ("clf", "both"):
            pc = v[1] if kind == "clf" else v[2]
            clf_rows.append({"model": name, "year": t, "n": len(te), **eval_classification(yte_c, pc)})
        pred = te[["crop", "province", "year"]].copy()
        pred["model"] = name
        pred["y_true"] = yte_r
        pred["loss_true"] = yte_c
        if kind in ("reg", "both"):
            pred["y_pred"] = v[1]
        if kind in ("clf", "both"):
            pred["p_loss"] = v[1] if kind == "clf" else v[2]
        all_preds.append(pred)

for t, tri, tei in rolling_splits(df):
    run_year(t, tri, tei)
    print("done", t)

reg = pd.DataFrame(reg_rows)
clf = pd.DataFrame(clf_rows)
reg.to_csv(f"{OUTDIR}/tables/yearly_reg_baselines.csv", index=False)
clf.to_csv(f"{OUTDIR}/tables/yearly_clf_baselines.csv", index=False)
save_preds(pd.concat(all_preds), "baselines")

def agg(d):
    metrics = [c for c in d.columns if c not in ("model", "year", "n")]
    return d.groupby("model").apply(
        lambda g: pd.Series({m: np.average(g[m].dropna(), weights=g.loc[g[m].notna(), "n"])
                             for m in metrics}), include_groups=False)

print("\n== 回归(net_profit, 元/亩) 加权平均 2015-2024 ==")
print(agg(reg).round(3).to_string())
print("\n== 分类(loss) 加权平均 2015-2024 ==")
print(agg(clf).round(3).to_string())
agg(reg).round(4).to_csv(f"{OUTDIR}/tables/model_comparison_reg.csv")
agg(clf).round(4).to_csv(f"{OUTDIR}/tables/model_comparison_clf.csv")
