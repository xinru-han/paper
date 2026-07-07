# -*- coding: utf-8 -*-
"""公共评估框架: 特征白名单 + 扩窗滚动时序验证 (杜绝泄漏)"""
import numpy as np
import pandas as pd
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             brier_score_loss, mean_absolute_error,
                             mean_squared_error, r2_score)

PANEL = "/root/grain_profit_warning/data/processed/master_panel.csv"
OUTDIR = "/root/grain_profit_warning/output"
TEST_YEARS = list(range(2015, 2025))  # 扩窗: 训练2004..t-1, 预测t

# 特征白名单 —— 只含 t 年预测时可观测的变量
CAT_FEATURES = ["crop", "province", "region"]


def feature_cols(df, ex_post=False):
    """ex_post=False: 预警版(不含收获后信息 gp_year_mean/gp_cv)"""
    cols = [c for c in df.columns if c.startswith(("L1_", "L2_", "trend3_", "in_", "rp_"))]
    cols += [c for c in df.columns if c.startswith(("temp_", "prec_"))]
    cols += ["gp_pre_mean", "gp_grow_mean", "gp_pre_yoy",
             "trend", "policy_corn_reform", "policy_min_price"]
    if ex_post:
        cols += ["gp_year_mean", "gp_cv", "gp_yoy"]
    return [c for c in cols if c in df.columns]


def load_panel():
    df = pd.read_csv(PANEL)
    # 至少要有滞后净利润才可预测
    df = df.dropna(subset=["net_profit", "L1_net_profit"]).reset_index(drop=True)
    return df


def rolling_splits(df):
    for t in TEST_YEARS:
        tr = df[df["year"] < t]
        te = df[df["year"] == t]
        if len(te) == 0:
            continue
        yield t, tr.index.values, te.index.values


def encode_categories(df, cats=CAT_FEATURES):
    """整数编码(全集编码不泄漏: 类别集合是先验已知的)"""
    out = df.copy()
    for c in cats:
        out[c + "_code"] = pd.Categorical(out[c]).codes
    return out, [c + "_code" for c in cats]


def eval_regression(y, p):
    return {"rmse": float(np.sqrt(mean_squared_error(y, p))),
            "mae": float(mean_absolute_error(y, p)),
            "r2": float(r2_score(y, p)) if len(np.unique(y)) > 1 else np.nan,
            "sign_acc": float(np.mean((p < 0) == (y < 0)))}


def eval_classification(y, p):
    out = {"auc": np.nan, "pr_auc": np.nan,
           "brier": float(brier_score_loss(y, p)),
           "acc": float(np.mean((p > 0.5) == y))}
    if len(np.unique(y)) > 1:
        out["auc"] = float(roc_auc_score(y, p))
        out["pr_auc"] = float(average_precision_score(y, p))
    # 预警场景: 亏损召回率(阈值0.5)
    if y.sum() > 0:
        out["loss_recall"] = float(((p > 0.5) & (y == 1)).sum() / y.sum())
    return out


def summarize(rows, task):
    """rows: list of dict(year, n, **metrics) → 加权平均 + 分年"""
    d = pd.DataFrame(rows)
    metrics = [c for c in d.columns if c not in ("year", "n", "model")]
    avg = {m: float(np.average(d[m].dropna(),
                               weights=d.loc[d[m].notna(), "n"])) for m in metrics}
    return d, avg


def save_preds(preds, name):
    """preds: DataFrame(crop,province,year,y_true,y_pred[,p_loss])"""
    import os
    os.makedirs(f"{OUTDIR}/preds", exist_ok=True)
    preds.to_csv(f"{OUTDIR}/preds/{name}.csv", index=False, encoding="utf-8-sig")
