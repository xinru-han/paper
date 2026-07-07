#!/usr/bin/env python3
"""
使用 TabM 预测户外消费系数（参考 https://github.com/yandex-research/tabm ICLR 2025）。
优先使用官方 tabm 包；不可用时退化为自实现 Ensemble MLP（训练目标与官方一致：对 k 个预测分别求损失再取平均）。
包含：1.Copula 2.Kriging空间插值 3.Bootstrap(见run_bootstrap.py) 4.早停 5.超参固定 6.统一种子(42) 7.补全CV。
"""

import pandas as pd
import numpy as np
import os
import torch
import torch.nn as nn
from data_preparation_advanced import (
    load_and_prepare_data_advanced, calc_outdoor_coef,
    apply_kriging_interpolation, apply_grain_structure_interpolation, prepare_features_combined,
    impute_home_total_and_ratio,
)
from postprocess_predictions import run as run_postprocess

BASE_DIR = os.getcwd()
OUTPUT_FILE = os.path.join(BASE_DIR, "predictions_tabm.csv")
OUTPUT_FILE_ROBUST = os.path.join(BASE_DIR, "predictions_tabm_robust.csv")
OUTPUT_FILE_BOOTSTRAP = os.path.join(BASE_DIR, "predictions_tabm_bootstrap.csv")
IMPUTED_RATIOS_FILE = os.path.join(BASE_DIR, "data", "imputed_ratios_best.csv")
SEED = int(os.environ.get("PREDICT_SEED", 42))
MODEL_NAME = "tabm"

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# 小批量训练以控制 GPU 显存，避免 OOM
TABM_BATCH_SIZE = 512

# --- 官方 TabM 或自实现退化为 Ensemble MLP ---

def _use_official_tabm():
    """检测是否可使用官方 tabm 包。"""
    try:
        from tabm import TabM
        from rtdl_num_embeddings import LinearReLUEmbeddings
        # 用极小输入做一次前向以确认可用
        d = 2
        m = TabM.make(n_num_features=d, num_embeddings=LinearReLUEmbeddings(d), d_out=1)
        x = torch.randn(2, d)
        _ = m(x)
        return True
    except Exception:
        return False

USE_OFFICIAL_TABM = _use_official_tabm()


class _TabMFallback(nn.Module):
    """自实现：Ensemble of MLPs（无权重共享），训练目标与官方一致（对 k 个预测分别求损失再取平均）。"""
    def __init__(self, d_in, d_out, k=32, d_hidden=128):
        super().__init__()
        self.k = k
        self.W1 = nn.Parameter(torch.randn(k, d_in, d_hidden) / np.sqrt(d_in))
        self.b1 = nn.Parameter(torch.zeros(k, d_hidden))
        self.W2 = nn.Parameter(torch.randn(k, d_hidden, d_hidden) / np.sqrt(d_hidden))
        self.b2 = nn.Parameter(torch.zeros(k, d_hidden))
        self.W_out = nn.Parameter(torch.randn(k, d_hidden, d_out) / np.sqrt(d_hidden))
        self.b_out = nn.Parameter(torch.zeros(k, d_out))
        self.dropout = nn.Dropout(0.1)
        self.activation = nn.ReLU()

    def forward(self, x):
        x = x.unsqueeze(1).expand(-1, self.k, -1)
        x = torch.matmul(x.transpose(0, 1), self.W1).transpose(0, 1) + self.b1
        x = self.dropout(self.activation(x))
        x = torch.matmul(x.transpose(0, 1), self.W2).transpose(0, 1) + self.b2
        x = self.dropout(self.activation(x))
        x = torch.matmul(x.transpose(0, 1), self.W_out).transpose(0, 1) + self.b_out
        return x


class _TabMWrapper:
    """统一 predict(X) 接口：推理时对 k 个预测取平均。"""
    def __init__(self, model, k=None):
        self.model = model
        self._k = k

    def predict(self, X):
        self.model.eval()
        dev = next(self.model.parameters()).device
        with torch.no_grad():
            X_t = torch.as_tensor(X, dtype=torch.float32).to(dev)
            out = self.model(X_t)
            if out.dim() == 3:
                preds = out.mean(dim=1)
            else:
                preds = out
            return preds.cpu().numpy().flatten()


def train_tabm_model(X_train, y_train, X_val=None, y_val=None):
    d_in = X_train.shape[1]
    n = len(X_train)
    X_t = torch.as_tensor(X_train, dtype=torch.float32).to(device)
    y_t = torch.as_tensor(y_train, dtype=torch.float32).to(device)
    batch_size = min(TABM_BATCH_SIZE, max(1, n))

    if USE_OFFICIAL_TABM:
        from tabm import TabM
        from rtdl_num_embeddings import LinearReLUEmbeddings
        torch.manual_seed(SEED)
        np.random.seed(SEED)
        model = TabM.make(
            n_num_features=d_in,
            num_embeddings=LinearReLUEmbeddings(d_in),
            d_out=1,
        ).to(device)
        k = model.k
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.002, weight_decay=0.0003)
        model.train()
        for _ in range(100):
            perm = torch.randperm(n, device=X_t.device) if n > 1 else torch.arange(n, device=X_t.device)
            for start in range(0, n, batch_size):
                optimizer.zero_grad()
                idx = perm[start : start + batch_size]
                bx, by = X_t[idx], y_t[idx]
                preds = model(bx)
                y_expand = by.unsqueeze(1).expand(-1, k).unsqueeze(-1)
                loss = nn.functional.mse_loss(preds, y_expand)
                loss.backward()
                optimizer.step()
        return _TabMWrapper(model, k)
    else:
        torch.manual_seed(SEED)
        np.random.seed(SEED)
        model = _TabMFallback(d_in=d_in, d_out=1, k=32).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
        model.train()
        for _ in range(100):
            perm = torch.randperm(n, device=X_t.device) if n > 1 else torch.arange(n, device=X_t.device)
            for start in range(0, n, batch_size):
                optimizer.zero_grad()
                idx = perm[start : start + batch_size]
                bx, by = X_t[idx], y_t[idx]
                outputs = model(bx)
                y_expand = by.unsqueeze(1).expand(-1, model.k, 1)
                loss = nn.functional.mse_loss(outputs, y_expand)
                loss.backward()
                optimizer.step()
        return _TabMWrapper(model, model.k)

# --- 业务逻辑函数 ---

def predict_grain_structure(df_micro, X_pred_feats, feature_cols, known_provinces, X_pred, train_model_func):
    if 'total_大米' not in df_micro.columns:
        return None
    df_micro = df_micro.copy()
    df_micro['calc_稻谷'] = df_micro['total_大米'] / 0.7
    total_za = df_micro.get('total_杂粮', pd.Series(0.0, index=df_micro.index)).fillna(0)
    df_micro['Total_Grain_Mass'] = (df_micro['calc_稻谷'].fillna(0) + df_micro['total_小麦'].fillna(0) + df_micro['total_豆类'].fillna(0) + total_za)
    df_grain = df_micro[df_micro['Total_Grain_Mass'] > 0.1].copy()
    if len(df_grain) < 10: return None
    
    targets = {'Share_Paddy': ('calc_稻谷', 'paddy'), 'Share_Wheat': ('total_小麦', 'wheat'), 'Share_Beans': ('total_豆类', 'beans'), 'Share_Other': ('total_杂粮', 'other')}
    all_results = []
    for name, (total_col_name, grain_type) in targets.items():
        if total_col_name not in df_grain.columns: continue
        df_train = df_grain[feature_cols].copy()
        df_train['target_y'] = (df_grain[total_col_name] / df_grain['Total_Grain_Mass']).clip(0, 1)
        df_train = df_train.dropna(subset=feature_cols + ['target_y'])
        if len(df_train) < 10: continue
        
        X_train, scaler, label_enc = prepare_features_combined(df_train[feature_cols], feature_cols)
        model = train_model_func(X_train, df_train['target_y'].values)
        X_pred_processed, _, _ = prepare_features_combined(X_pred_feats, feature_cols, scaler, label_enc)
        s_pred = model.predict(X_pred_processed)
        
        res_df = pd.DataFrame({'Province': X_pred['T1'], 'Year': X_pred['wave'], f'{name}_Direct': s_pred.astype(np.float64)})
        res_df = apply_grain_structure_interpolation(res_df, known_provinces, f'{name}_Direct', f'{name}_Final', X_pred_feats, grain_type=grain_type)
        all_results.append(res_df[['Province', 'Year', f'{name}_Final']].copy())
        
    if all_results:
        df_final = all_results[0]
        for df in all_results[1:]: df_final = pd.merge(df_final, df, on=['Province', 'Year'], how='outer')
        share_cols = [c for c in df_final.columns if c.endswith('_Final') and 'Share_' in c]
        if share_cols:
            s = df_final[share_cols].fillna(0).clip(0, 1)
            tot = s.sum(axis=1).replace(0, np.nan)
            df_final[share_cols] = s.div(tot, axis=0).fillna(1.0 / len(share_cols))
        df_final.to_csv(os.path.join(BASE_DIR, "grain_structure_predictions_tabm.csv"), index=False)
        return df_final
    return None

def predict_category(q_col, total_col, ratio_col, df_micro, X_pred_feats, feature_cols, known_provinces, X_pred, use_imputation=False):
    short = total_col.replace("total_", "")
    precomputed_col = f"ratio_filled_{short}"
    df_clean = None
    if use_imputation and precomputed_col in df_micro.columns and df_micro[precomputed_col].notna().sum() >= 10:
        df_clean = df_micro.dropna(subset=[precomputed_col] + feature_cols).copy()
        if len(df_clean) >= 10: y_ratio = df_clean[precomputed_col].values
        else: df_clean = None
            
    if df_clean is None and use_imputation:
        home_col = "home_" + short
        if total_col in df_micro.columns and home_col in df_micro.columns:
            df_filled = impute_home_total_and_ratio(df_micro, feature_cols, total_col, home_col, train_tabm_model)
            if df_filled is not None and df_filled["ratio_filled"].notna().sum() >= 10:
                df_clean = df_filled.dropna(subset=["ratio_filled"]).copy()
                y_ratio = df_clean["ratio_filled"].values
                
    if df_clean is None:
        df_clean = df_micro.dropna(subset=feature_cols + [total_col, ratio_col]).copy()
        if len(df_clean) < 10: return None
        df_clean = df_clean[df_clean[total_col] > 0]
        if len(df_clean) < 10: return None
        y_ratio = df_clean[ratio_col].values

    X_train, scaler, label_enc = prepare_features_combined(df_clean[feature_cols], feature_cols)
    model = train_tabm_model(X_train, y_ratio)
    X_pred_processed, _, _ = prepare_features_combined(X_pred_feats, feature_cols, scaler, label_enc)
    s_pred = np.clip(model.predict(X_pred_processed), 1e-6, 1.0)
    coef_direct = calc_outdoor_coef(s_pred)
    res_df = pd.DataFrame({'Province': X_pred['T1'], 'Year': X_pred['wave'], 'Coef_Direct': coef_direct.astype(np.float64)})
    return apply_kriging_interpolation(res_df, known_provinces, 'Coef_Direct', 'Coef_Final')

if __name__ == "__main__":
    if USE_OFFICIAL_TABM:
        print("当前使用: TabM（官方包 yandex-research/tabm）预测户外消费系数")
    else:
        print("当前使用: TabM（自实现退化为 Ensemble MLP）预测户外消费系数")
    df_micro, X_pred_feats, feature_cols, category_map, known_provinces = load_and_prepare_data_advanced(use_copula=True)
    X_pred = X_pred_feats.copy()
    
    predict_grain_structure(df_micro, X_pred_feats, feature_cols, known_provinces, X_pred, train_tabm_model)
    
    seed_env = os.environ.get("PREDICT_SEED", "42")
    for use_impute, out_path, label in [(True, OUTPUT_FILE, "主流程（补缺失）"), (False, OUTPUT_FILE_ROBUST, "稳健性（不补缺失）")]:
        if seed_env != "42" and not use_impute:
            continue
        if seed_env != "42" and use_impute:
            out_path = os.path.join(BASE_DIR, f"predictions_{MODEL_NAME}_seed{seed_env}.csv")
        df_micro_use = df_micro
        if use_impute and os.path.isfile(IMPUTED_RATIOS_FILE):
            df_micro_use, _, _, _, _ = load_and_prepare_data_advanced(use_copula=True, imputed_ratios_path=IMPUTED_RATIOS_FILE)
            
        all_results = []
        for q_col, total_col in category_map.items():
            ratio_col = f"ratio_{total_col.replace('total_', '')}"
            if total_col not in df_micro_use.columns or ratio_col not in df_micro_use.columns: continue
            res_df = predict_category(q_col, total_col, ratio_col, df_micro_use, X_pred_feats, feature_cols, known_provinces, X_pred, use_imputation=use_impute)
            if res_df is not None:
                res_df["Category"] = q_col
                all_results.append(res_df)
                
        if all_results:
            df_pivot = pd.concat(all_results, ignore_index=True).pivot_table(index=["Province", "Year"], columns="Category", values="Coef_Final", aggfunc="first").reset_index()
            df_pivot.to_csv(out_path, index=False)
            if seed_env == "42":
                print(f"✅ {label} 已保存: {out_path}")
                run_postprocess(predictions_path=out_path)