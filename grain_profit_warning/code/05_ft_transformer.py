# -*- coding: utf-8 -*-
"""FT-Transformer (rtdl_revisiting_models), 回归+分类, 扩窗滚动验证
数值特征: 训练窗内标准化+中位数插补+缺失指示; 类别特征: embedding
"""
import os, sys, warnings
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings("ignore")
from common import (load_panel, feature_cols, rolling_splits, encode_categories,
                    eval_regression, eval_classification, save_preds, OUTDIR)
from rtdl_revisiting_models import FTTransformer

torch.manual_seed(42)
np.random.seed(42)
device = "cpu"

df = load_panel()
df, cat_codes = encode_categories(df)
num_feats = feature_cols(df)
CAT_CARD = [df[c].max() + 1 for c in cat_codes]

def prep(tr, te):
    med = tr[num_feats].median()
    def tx(d):
        x = d[num_feats]
        miss = x.isna().astype(np.float32)
        x = x.fillna(med)
        mu, sd = tr[num_feats].fillna(med).mean(), tr[num_feats].fillna(med).std().replace(0, 1)
        x = (x - mu) / sd
        return np.hstack([x.values.astype(np.float32), miss.values]), \
               d[cat_codes].values.astype(np.int64)
    return tx(tr), tx(te)

def make_model(d_out):
    return FTTransformer(
        n_cont_features=len(num_feats) * 2, cat_cardinalities=CAT_CARD,
        d_out=d_out, n_blocks=2, d_block=96, attention_n_heads=8,
        attention_dropout=0.2, ffn_d_hidden_multiplier=2.0,
        ffn_dropout=0.1, residual_dropout=0.0).to(device)

def fit_predict(Xtr, Ctr, ytr, Xte, Cte, task):
    y = torch.tensor(ytr, dtype=torch.float32)
    if task == "reg":
        mu, sd = y.mean(), y.std()
        y = (y - mu) / sd
        lossfn = nn.MSELoss()
    else:
        lossfn = nn.BCEWithLogitsLoss()
    model = make_model(1)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    Xtr_t = torch.tensor(Xtr); Ctr_t = torch.tensor(Ctr)
    n = len(Xtr_t); bs = 128
    # 训练窗内部再留出最后一年做早停
    model.train()
    best, best_state, patience = np.inf, None, 0
    idx = np.arange(n); val = idx[-max(64, n // 8):]; trn = idx[:-len(val)]
    for epoch in range(200):
        perm = np.random.permutation(trn)
        for i in range(0, len(perm), bs):
            b = perm[i:i + bs]
            opt.zero_grad()
            out = model(Xtr_t[b], Ctr_t[b]).squeeze(-1)
            l = lossfn(out, y[b])
            l.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            vl = lossfn(model(Xtr_t[val], Ctr_t[val]).squeeze(-1), y[val]).item()
        model.train()
        if vl < best - 1e-5:
            best, best_state, patience = vl, {k: v.clone() for k, v in model.state_dict().items()}, 0
        else:
            patience += 1
            if patience >= 15:
                break
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        out = model(torch.tensor(Xte), torch.tensor(Cte)).squeeze(-1)
    if task == "reg":
        return (out * sd + mu).numpy()
    return torch.sigmoid(out).numpy()

reg_rows, clf_rows, all_preds = [], [], []
for t, tri, tei in rolling_splits(df):
    tr, te = df.loc[tri], df.loc[tei]
    (Xtr, Ctr), (Xte, Cte) = prep(tr, te)
    pr = fit_predict(Xtr, Ctr, tr["net_profit"].values, Xte, Cte, "reg")
    pc = fit_predict(Xtr, Ctr, tr["loss"].values.astype(np.float32), Xte, Cte, "clf")
    reg_rows.append({"model": "FT-Transformer", "year": t, "n": len(te),
                     **eval_regression(te["net_profit"].values, pr)})
    clf_rows.append({"model": "FT-Transformer", "year": t, "n": len(te),
                     **eval_classification(te["loss"].values, pc)})
    pred = te[["crop", "province", "year"]].copy()
    pred["model"] = "FT-Transformer"
    pred["y_true"] = te["net_profit"].values; pred["loss_true"] = te["loss"].values
    pred["y_pred"] = pr; pred["p_loss"] = pc
    all_preds.append(pred)
    print("done", t, reg_rows[-1]["rmse"], clf_rows[-1]["auc"])

pd.DataFrame(reg_rows).to_csv(f"{OUTDIR}/tables/yearly_reg_ft.csv", index=False)
pd.DataFrame(clf_rows).to_csv(f"{OUTDIR}/tables/yearly_clf_ft.csv", index=False)
save_preds(pd.concat(all_preds), "ft_transformer")
r = pd.DataFrame(reg_rows); c = pd.DataFrame(clf_rows)
print("REG avg:", {m: round(np.average(r[m], weights=r.n), 3) for m in ["rmse", "mae", "r2", "sign_acc"]})
print("CLF avg:", {m: round(np.average(c[m].dropna(), weights=c.loc[c[m].notna(), 'n']), 3) for m in ["auc", "pr_auc", "brier", "acc"]})
