#!/usr/bin/env python3
"""
对比各模型在「户内消费系数」预测上的精度（交叉验证）。
指标：MAE、RMSE、R²、MAPE。
输出：各模型×品类明细 CSV、按模型汇总 CSV，并在控制台打印对比表。
运行过程同步写入 compare_accuracy_log.txt，便于随时查看进度。
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import KFold

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DETAIL_CSV = os.path.join(BASE_DIR, "model_accuracy_detail.csv")
OUTPUT_SUMMARY_CSV = os.path.join(BASE_DIR, "model_accuracy_summary.csv")
LOG_FILE = os.path.join(BASE_DIR, "compare_accuracy_log.txt")


class Tee:
    """将 write 同时写入多个文件（如日志文件与标准输出），便于进程输出同步到 txt。"""
    def __init__(self, *files):
        self.files = files
    def write(self, data):
        for f in self.files:
            f.write(data)
            try:
                f.flush()
            except Exception:
                pass
    def flush(self):
        for f in self.files:
            if hasattr(f, "flush"):
                try:
                    f.flush()
                except Exception:
                    pass

SEED = int(os.environ.get("PREDICT_SEED", 42))
N_SPLITS = 5
MIN_SAMPLES = 30


def _get_models():
    """返回 (model_name, train_func, use_dataframe) 列表。use_dataframe=True 表示该模型需要 DataFrame 训练/预测。"""
    models = []
    try:
        from predict_lightgbm import train_lightgbm_model
        models.append(("lightgbm", train_lightgbm_model, False))
    except Exception as e:
        print(f"  skip lightgbm: {e}")
    try:
        from predict_lasso import train_lasso_model
        models.append(("lasso", train_lasso_model, False))
    except Exception as e:
        print(f"  skip lasso: {e}")
    try:
        from predict_linear import train_linear_model
        models.append(("linear", train_linear_model, False))
    except Exception as e:
        print(f"  skip linear: {e}")
    try:
        from predict_xgboost import train_xgboost_model
        models.append(("xgboost", train_xgboost_model, False))
    except Exception as e:
        print(f"  skip xgboost: {e}")
    try:
        from predict_catboost import train_catboost_model
        models.append(("catboost", train_catboost_model, False))
    except Exception as e:
        print(f"  skip catboost: {e}")
    try:
        from predict_randomforest import train_randomforest_model
        models.append(("randomforest", train_randomforest_model, False))
    except Exception as e:
        print(f"  skip randomforest: {e}")
    try:
        from predict_mlp import train_mlp_model
        models.append(("mlp", train_mlp_model, False))
    except Exception as e:
        print(f"  skip mlp: {e}")
    try:
        from predict_tabnet import train_tabnet_model
        models.append(("tabnet", train_tabnet_model, False))
    except Exception as e:
        print(f"  skip tabnet: {e}")
    try:
        from predict_tabm import train_tabm_model
        models.append(("tabm", train_tabm_model, False))
    except Exception as e:
        print(f"  skip tabm: {e}")
    try:
        from predict_tabpfn import train_tabpfn_model
        models.append(("tabpfn", train_tabpfn_model, False))
    except Exception as e:
        print(f"  skip tabpfn: {e}")
    try:
        from predict_resnet_tabular import train_resnet_model
        models.append(("resnet_tabular", train_resnet_model, False))
    except Exception as e:
        print(f"  skip resnet_tabular: {e}")
    try:
        from predict_fttransformer import DirectRatioOptimizer
        models.append(("fttransformer", ("fttransformer", DirectRatioOptimizer), True))
    except Exception as e:
        print(f"  skip fttransformer: {e}")
    return models


def _compute_metrics(y_true, y_pred):
    """y_true, y_pred 为一维数组，预测目标为户内消费系数 (0,1]。返回 MAE, RMSE, R2, MAPE。"""
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    y_pred = np.asarray(y_pred, dtype=np.float64).ravel()
    y_pred = np.clip(y_pred, 1e-6, 1.0)
    err = y_pred - y_true
    mae = np.abs(err).mean()
    rmse = np.sqrt((err ** 2).mean())
    ss_res = (err ** 2).sum()
    ss_tot = ((y_true - y_true.mean()) ** 2).sum()
    r2 = 1.0 - ss_res / (ss_tot + 1e-12)
    # MAPE: 避免除零，对真实值加小量
    mape = (np.abs(err) / (np.abs(y_true) + 1e-6)).mean() * 100.0
    return {"MAE": float(mae), "RMSE": float(rmse), "R2": float(r2), "MAPE": float(mape)}


def evaluate_category_cv_numpy(df_clean, feature_cols, ratio_col, train_func, n_splits=N_SPLITS):
    """使用 numpy 接口的模型：K 折交叉验证，返回各折平均 MAE, RMSE, R2, MAPE。"""
    from data_preparation_advanced import prepare_features_combined
    df_clean = df_clean.dropna(subset=feature_cols + [ratio_col]).copy()
    df_clean = df_clean[df_clean[ratio_col].notna() & (df_clean[ratio_col] > 0) & (df_clean[ratio_col] <= 1)]
    if len(df_clean) < MIN_SAMPLES:
        return None
    X_all, scaler, label_enc = prepare_features_combined(df_clean[feature_cols], feature_cols)
    y_all = df_clean[ratio_col].values.astype(np.float64)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    mae_list, rmse_list, r2_list, mape_list = [], [], [], []
    for train_idx, val_idx in kf.split(X_all):
        X_train, X_val = X_all[train_idx], X_all[val_idx]
        y_train, y_val = y_all[train_idx], y_all[val_idx]
        try:
            model = train_func(X_train, y_train)
            pred = model.predict(X_val)
            if pred.ndim > 1:
                pred = pred.ravel()
            pred = np.clip(pred, 1e-6, 1.0)
            m = _compute_metrics(y_val, pred)
            mae_list.append(m["MAE"])
            rmse_list.append(m["RMSE"])
            r2_list.append(m["R2"])
            mape_list.append(m["MAPE"])
        except Exception:
            continue
    if not mae_list:
        return None
    return {
        "MAE": np.mean(mae_list),
        "RMSE": np.mean(rmse_list),
        "R2": np.mean(r2_list),
        "MAPE": np.mean(mape_list),
    }


def evaluate_category_cv_fttransformer(df_clean, feature_cols, total_col, ratio_col, n_splits=N_SPLITS):
    """FT-Transformer：需要 DataFrame 与 DirectRatioOptimizer，K 折交叉验证。"""
    from predict_fttransformer import DirectRatioOptimizer
    df_clean = df_clean.dropna(subset=feature_cols + [ratio_col, total_col]).copy()
    df_clean = df_clean[(df_clean[total_col] > 0) & (df_clean[ratio_col] > 0) & (df_clean[ratio_col] <= 1)]
    if len(df_clean) < MIN_SAMPLES:
        return None
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    mae_list, rmse_list, r2_list, mape_list = [], [], [], []
    for train_idx, val_idx in kf.split(df_clean):
        df_train = df_clean.iloc[train_idx].copy()
        df_val = df_clean.iloc[val_idx].copy()
        try:
            opt = DirectRatioOptimizer("cv")
            opt.fit_and_optimize(df_train, feature_cols, total_col, ratio_col, n_trials=20)
            y_val_true = df_val[ratio_col].values.astype(np.float64)
            pred = opt.predict(df_val[feature_cols])
            pred = np.asarray(pred, dtype=np.float64).ravel()
            pred = np.clip(pred, 1e-6, 1.0)
            m = _compute_metrics(y_val_true, pred)
            mae_list.append(m["MAE"])
            rmse_list.append(m["RMSE"])
            r2_list.append(m["R2"])
            mape_list.append(m["MAPE"])
        except Exception:
            continue
    if not mae_list:
        return None
    return {
        "MAE": np.mean(mae_list),
        "RMSE": np.mean(rmse_list),
        "R2": np.mean(r2_list),
        "MAPE": np.mean(mape_list),
    }


def main():
    from data_preparation_advanced import load_and_prepare_data_advanced, prepare_features_combined

    log = open(LOG_FILE, "w", encoding="utf-8")
    log.write(f"[{datetime.now().isoformat()}] 各模型预测精度对比开始\n")
    log.write(f"日志同步写入: {LOG_FILE}\n")
    log.flush()
    orig_stdout = sys.stdout
    sys.stdout = Tee(log, orig_stdout)
    try:
        print("=" * 60)
        print("各模型预测精度对比（户内消费系数，交叉验证）")
        print("=" * 60)
        print("\n1. 加载数据...")
        df_micro, X_pred_feats, feature_cols, category_map, known_provinces = load_and_prepare_data_advanced(use_copula=True)
        models = _get_models()
        if len(models) < 2:
            print("可用模型不足 2 个，请检查依赖。")
            sys.exit(1)
        print(f"   可用模型数: {len(models)}")
        print(f"   交叉验证: {N_SPLITS} 折，最小样本数: {MIN_SAMPLES}")

        print("\n2. 按品类 × 模型做交叉验证，计算 MAE / RMSE / R² / MAPE...")
        results = []
        for q_col, total_col in category_map.items():
            ratio_col = f"ratio_{total_col.replace('total_', '')}"
            if total_col not in df_micro.columns or ratio_col not in df_micro.columns:
                continue
            df_clean = df_micro.dropna(subset=feature_cols).copy()
            df_clean = df_clean[df_clean[total_col] > 1e-6]
            if len(df_clean) < MIN_SAMPLES:
                continue
            for model_name, train_spec, use_df in models:
                try:
                    print(f"   {model_name} / {q_col} ...", end=" ", flush=True)
                    if use_df and model_name == "fttransformer":
                        metrics = evaluate_category_cv_fttransformer(
                            df_clean, feature_cols, total_col, ratio_col, n_splits=N_SPLITS
                        )
                    else:
                        train_func = train_spec
                        metrics = evaluate_category_cv_numpy(
                            df_clean, feature_cols, ratio_col, train_func, n_splits=N_SPLITS
                        )
                    if metrics is not None:
                        results.append({
                            "model": model_name,
                            "category": q_col,
                            "MAE": metrics["MAE"],
                            "RMSE": metrics["RMSE"],
                            "R2": metrics["R2"],
                            "MAPE": metrics["MAPE"],
                        })
                        print(f"MAE={metrics['MAE']:.4f} RMSE={metrics['RMSE']:.4f} R2={metrics['R2']:.4f} MAPE={metrics['MAPE']:.2f}%")
                    else:
                        print("跳过(数据不足)")
                except Exception as e:
                    print(f" 异常: {e}")
                    continue

        if not results:
            print("   无有效评估结果。")
            sys.exit(1)

        df_detail = pd.DataFrame(results)

        print("\n3. 按模型汇总（各品类指标平均）...")
        agg = df_detail.groupby("model").agg(
            MAE=("MAE", "mean"),
            RMSE=("RMSE", "mean"),
            R2=("R2", "mean"),
            MAPE=("MAPE", "mean"),
        ).reset_index()
        agg = agg.sort_values("MAE").reset_index(drop=True)
        agg["rank_MAE"] = np.arange(1, len(agg) + 1)
        agg["rank_RMSE"] = agg["RMSE"].rank().astype(int)
        agg["rank_R2"] = agg["R2"].rank(ascending=False).astype(int)

        print("\n" + agg.to_string(index=False))
        print("\n   说明: rank_MAE/rank_RMSE 越小越好，rank_R2 越大越好。")

        df_detail.to_csv(OUTPUT_DETAIL_CSV, index=False, encoding="utf-8-sig")
        agg.to_csv(OUTPUT_SUMMARY_CSV, index=False, encoding="utf-8-sig")
        print(f"\n   已保存明细: {OUTPUT_DETAIL_CSV}")
        print(f"   已保存汇总: {OUTPUT_SUMMARY_CSV}")
    finally:
        sys.stdout = orig_stdout
        log.write(f"\n[{datetime.now().isoformat()}] 各模型预测精度对比结束\n")
        log.close()


if __name__ == "__main__":
    main()
