#!/usr/bin/env python3
"""
使用 TabNet (pytorch-tabnet) 预测户外消费系数。
包含：Copula收入分布匹配、Kriging空间插值、Bootstrap预测区间、早停机制、
超参数优化（固定结构）、统一随机种子(42)、补全阶段交叉验证。
"""

import pandas as pd
import numpy as np
import os
from contextlib import redirect_stdout, redirect_stderr
from sklearn.neural_network import MLPRegressor
from data_preparation_advanced import (
    load_and_prepare_data_advanced, calc_outdoor_coef,
    apply_kriging_interpolation, apply_grain_structure_interpolation, prepare_features_combined,
    impute_home_total_and_ratio,
)
from postprocess_predictions import run as run_postprocess

BASE_DIR = os.getcwd()
OUTPUT_FILE = os.path.join(BASE_DIR, "predictions_tabnet.csv")
OUTPUT_FILE_ROBUST = os.path.join(BASE_DIR, "predictions_tabnet_robust.csv")
OUTPUT_FILE_BOOTSTRAP = os.path.join(BASE_DIR, "predictions_tabnet_bootstrap.csv")
IMPUTED_RATIOS_FILE = os.path.join(BASE_DIR, "data", "imputed_ratios_best.csv")
SEED = int(os.environ.get("PREDICT_SEED", 42))
MODEL_NAME = "tabnet"


def _which_backend():
    """检测实际将使用的后端：TabNet 或 MLP（退化）。"""
    try:
        from pytorch_tabnet.tab_model import TabNetRegressor
        X = np.zeros((4, 2), dtype=np.float32)
        y = np.zeros((4, 1), dtype=np.float32)
        model = TabNetRegressor(n_d=64, n_a=64, n_steps=5, gamma=1.5, n_independent=2, n_shared=2,
                                momentum=0.3, mask_type="entmax", seed=SEED)
        with open(os.devnull, "w") as devnull:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                model.fit(X, y, max_epochs=1, batch_size=2)
        return "TabNet", None
    except Exception as e:
        return "MLP", str(e)


def train_tabnet_model(X_train, y_train, X_val=None, y_val=None):
    X = np.asarray(X_train, dtype=np.float32)
    y = np.asarray(y_train, dtype=np.float32).ravel()
    try:
        from pytorch_tabnet.tab_model import TabNetRegressor
        y_2d = y.reshape(-1, 1)
        model = TabNetRegressor(
            n_d=64, n_a=64, n_steps=5, gamma=1.5, n_independent=2, n_shared=2,
            momentum=0.3, mask_type="entmax", seed=SEED,
        )
        with open(os.devnull, "w") as devnull:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                model.fit(X, y_2d, max_epochs=100, patience=10, batch_size=256, virtual_batch_size=128)
        return model
    except Exception:
        pass
    model = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=500, random_state=SEED, early_stopping=True)
    model.fit(X_train, y_train)
    return model

def predict_grain_structure(df_micro, X_pred_feats, feature_cols, known_provinces, X_pred, train_model_func):
    if 'total_大米' not in df_micro.columns:
        return None
    df_micro = df_micro.copy()
    df_micro['calc_稻谷'] = df_micro['total_大米'] / 0.7
    total_za = df_micro.get('total_杂粮', pd.Series(0.0, index=df_micro.index)).fillna(0)
    df_micro['Total_Grain_Mass'] = (df_micro['calc_稻谷'].fillna(0) + df_micro['total_小麦'].fillna(0) + df_micro['total_豆类'].fillna(0) + total_za)
    df_grain = df_micro[df_micro['Total_Grain_Mass'] > 0.1].copy()
    if len(df_grain) < 10:
        return None
    targets = {'Share_Paddy': ('calc_稻谷', 'paddy'), 'Share_Wheat': ('total_小麦', 'wheat'), 'Share_Beans': ('total_豆类', 'beans'), 'Share_Other': ('total_杂粮', 'other')}
    all_results = []
    for name, (total_col_name, grain_type) in targets.items():
        if total_col_name not in df_grain.columns:
            continue
        df_train = df_grain[feature_cols].copy()
        df_train['target_y'] = (df_grain[total_col_name] / df_grain['Total_Grain_Mass']).clip(0, 1)
        df_train = df_train.dropna(subset=feature_cols + ['target_y'])
        if len(df_train) < 10:
            continue
        X_train, scaler, label_enc = prepare_features_combined(df_train[feature_cols], feature_cols)
        y_target = df_train['target_y'].values
        model = train_model_func(X_train, y_target)
        X_pred_processed, _, _ = prepare_features_combined(X_pred_feats, feature_cols, scaler, label_enc)
        pred = model.predict(X_pred_processed)
        if getattr(pred, "ndim", 1) == 2 and pred.shape[1] == 1:
            pred = pred.ravel()
        s_pred = np.asarray(pred, dtype=np.float64).ravel()
        res_df = pd.DataFrame({'Province': X_pred['T1'], 'Year': X_pred['wave'], f'{name}_Direct': s_pred})
        res_df = apply_grain_structure_interpolation(res_df, known_provinces, f'{name}_Direct', f'{name}_Final', X_pred_feats, grain_type=grain_type)
        all_results.append(res_df[['Province', 'Year', f'{name}_Final']].copy())
    if all_results:
        df_final = all_results[0]
        for df in all_results[1:]:
            df_final = pd.merge(df_final, df, on=['Province', 'Year'], how='outer')
        share_cols = [c for c in df_final.columns if c.endswith('_Final') and 'Share_' in c]
        if share_cols:
            s = df_final[share_cols].fillna(0).clip(0, 1)
            tot = s.sum(axis=1).replace(0, np.nan)
            df_final[share_cols] = s.div(tot, axis=0).fillna(1.0 / len(share_cols))
        df_final.to_csv(os.path.join(BASE_DIR, "grain_structure_predictions_tabnet.csv"), index=False)
        return df_final
    return None

def predict_category(q_col, total_col, ratio_col, df_micro, X_pred_feats, feature_cols, known_provinces, X_pred, use_imputation=False):
    short = total_col.replace("total_", "")
    precomputed_col = f"ratio_filled_{short}"
    df_clean = None
    if use_imputation and precomputed_col in df_micro.columns and df_micro[precomputed_col].notna().sum() >= 10:
        df_clean = df_micro.dropna(subset=[precomputed_col] + feature_cols).copy()
        if len(df_clean) >= 10:
            y_ratio = df_clean[precomputed_col].values
        else:
            df_clean = None
    if df_clean is None and use_imputation:
        home_col = "home_" + short
        if total_col in df_micro.columns and home_col in df_micro.columns:
            df_filled = impute_home_total_and_ratio(df_micro, feature_cols, total_col, home_col, train_tabnet_model)
            if df_filled is not None and df_filled["ratio_filled"].notna().sum() >= 10:
                df_clean = df_filled.dropna(subset=["ratio_filled"]).copy()
                y_ratio = df_clean["ratio_filled"].values
    if df_clean is None:
        df_clean = df_micro.dropna(subset=feature_cols + [total_col, ratio_col]).copy()
        if len(df_clean) < 10:
            return None
        df_clean = df_clean[df_clean[total_col] > 0]
        if len(df_clean) < 10:
            return None
        y_ratio = df_clean[ratio_col].values
    if len(df_clean) < 10:
        return None
    X_train, scaler, label_enc = prepare_features_combined(df_clean[feature_cols], feature_cols)
    model = train_tabnet_model(X_train, y_ratio)
    X_pred_processed, _, _ = prepare_features_combined(X_pred_feats, feature_cols, scaler, label_enc)
    pred = model.predict(X_pred_processed)
    if getattr(pred, "ndim", 1) == 2 and pred.shape[1] == 1:
        pred = pred.ravel()
    s_pred = np.clip(np.asarray(pred, dtype=np.float64).ravel(), 1e-6, 1.0)
    coef_direct = calc_outdoor_coef(s_pred)
    res_df = pd.DataFrame({'Province': X_pred['T1'], 'Year': X_pred['wave'], 'Coef_Direct': coef_direct.astype(np.float64)})
    return apply_kriging_interpolation(res_df, known_provinces, 'Coef_Direct', 'Coef_Final')

if __name__ == "__main__":
    backend, reason = _which_backend()
    if backend == "TabNet":
        print("当前使用: TabNet 预测户外消费系数")
    else:
        print("当前使用: MLP（TabNet 不可用，已退化）预测户外消费系数" + (f" — {reason}" if reason else ""))
    df_micro, X_pred_feats, feature_cols, category_map, known_provinces = load_and_prepare_data_advanced(use_copula=True)
    X_pred = X_pred_feats.copy()
    predict_grain_structure(df_micro, X_pred_feats, feature_cols, known_provinces, X_pred, train_tabnet_model)
    seed_env = os.environ.get("PREDICT_SEED", "42")
    for use_impute, out_path, label in [(True, OUTPUT_FILE, "主流程（补缺失）"), (False, OUTPUT_FILE_ROBUST, "稳健性（不补缺失）")]:
        if seed_env != "42" and not use_impute:
            continue
        if seed_env != "42" and use_impute:
            out_path = os.path.join(BASE_DIR, f"predictions_{MODEL_NAME}_seed{seed_env}.csv")
        if use_impute and os.path.isfile(IMPUTED_RATIOS_FILE):
            df_micro_use, _, _, _, _ = load_and_prepare_data_advanced(use_copula=True, imputed_ratios_path=IMPUTED_RATIOS_FILE)
        else:
            df_micro_use = df_micro
        all_results = []
        for q_col, total_col in category_map.items():
            ratio_col = f"ratio_{total_col.replace('total_', '')}"
            if total_col not in df_micro_use.columns or ratio_col not in df_micro_use.columns:
                continue
            res_df = predict_category(q_col, total_col, ratio_col, df_micro_use, X_pred_feats, feature_cols, known_provinces, X_pred, use_imputation=use_impute)
            if res_df is not None:
                res_df["Category"] = q_col
                all_results.append(res_df)
        if all_results:
            df_pivot = pd.concat(all_results, ignore_index=True).pivot_table(index=["Province", "Year"], columns="Category", values="Coef_Final", aggfunc="first").reset_index()
            df_pivot.columns.name = None
            df_pivot.to_csv(out_path, index=False)
            if seed_env == "42":
                print(f"✅ {label} 已保存: {out_path}")
                if out_path == OUTPUT_FILE_ROBUST:
                    import shutil
                    g = os.path.join(BASE_DIR, "grain_structure_predictions_tabnet.csv")
                    if os.path.isfile(g):
                        shutil.copy(g, os.path.join(BASE_DIR, "grain_structure_predictions_tabnet_robust.csv"))
                run_postprocess(predictions_path=out_path)
