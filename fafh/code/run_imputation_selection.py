#!/usr/bin/env python3
"""
先用 12 种模型（LightGBM、Lasso、Linear、XGBoost、CatBoost、RandomForest、MLP、TabNet、TabM、TabPFN、ResNet、FT-Transformer）对缺失值做预测并评估，
选出精度最高的一个，将其补缺失结果保存为统一样本；后续各模型主流程可使用该样本。
运行一次即可生成 data/imputed_ratios_best.csv 与 data/best_imputation_model.txt。
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
IMPUTED_RATIOS_FILE = os.path.join(DATA_DIR, "imputed_ratios_best.csv")
BEST_MODEL_FILE = os.path.join(DATA_DIR, "best_imputation_model.txt")
SELECTION_RESULTS_CSV = os.path.join(DATA_DIR, "imputation_selection_results.csv")  # 各模型汇总指标 + 选中模型
EVALUATION_DETAIL_CSV = os.path.join(DATA_DIR, "imputation_evaluation_detail.csv")   # 各模型×品类明细

# 12 种模型的 (名称, 训练函数或 None)：与各 predict_*.py 中系数预测使用相同方法；FT-Transformer 为 None，评估与补缺失用自身实现
def _get_imputation_models():
    models = []
    try:
        from predict_lightgbm import train_lightgbm_model
        models.append(("lightgbm", train_lightgbm_model))
    except Exception as e:
        print(f"  skip lightgbm: {e}")
    try:
        from predict_lasso import train_lasso_model
        models.append(("lasso", train_lasso_model))
    except Exception as e:
        print(f"  skip lasso: {e}")
    try:
        from predict_linear import train_linear_model
        models.append(("linear", train_linear_model))
    except Exception as e:
        print(f"  skip linear: {e}")
    try:
        from predict_xgboost import train_xgboost_model
        models.append(("xgboost", train_xgboost_model))
    except Exception as e:
        print(f"  skip xgboost: {e}")
    try:
        from predict_catboost import train_catboost_model
        models.append(("catboost", train_catboost_model))
    except Exception as e:
        print(f"  skip catboost: {e}")
    try:
        from predict_randomforest import train_randomforest_model
        models.append(("randomforest", train_randomforest_model))
    except Exception as e:
        print(f"  skip randomforest: {e}")
    try:
        from predict_mlp import train_mlp_model
        models.append(("mlp", train_mlp_model))
    except Exception as e:
        print(f"  skip mlp: {e}")
    try:
        from predict_tabnet import train_tabnet_model
        models.append(("tabnet", train_tabnet_model))
    except Exception as e:
        print(f"  skip tabnet: {e}")
    try:
        from predict_tabm import train_tabm_model
        models.append(("tabm", train_tabm_model))
    except Exception as e:
        print(f"  skip tabm: {e}")
    try:
        from predict_tabpfn import train_tabpfn_model
        models.append(("tabpfn", train_tabpfn_model))
    except Exception as e:
        print(f"  skip tabpfn: {e}")
    try:
        from predict_resnet_tabular import train_resnet_model
        models.append(("resnet_tabular", train_resnet_model))
    except Exception as e:
        print(f"  skip resnet_tabular: {e}")
    try:
        from predict_fttransformer_advanced import evaluate_imputation_cv_fttransformer, impute_home_total_and_ratio_fttransformer
        models.append(("fttransformer", None))  # 评估与补缺失在 main 中走专用分支
    except Exception as e:
        print(f"  skip fttransformer: {e}")
    return models


def main():
    from data_preparation_advanced import (
        load_and_prepare_data_advanced,
        impute_home_total_and_ratio,
        evaluate_imputation_cv,
    )
    print("=" * 60)
    print("缺失值补全模型选择：12 种模型评估 → 选最优 → 保存统一补缺失样本")
    print("=" * 60)
    print("\n1. 加载数据...")
    df_micro, X_pred_feats, feature_cols, category_map, known_provinces = load_and_prepare_data_advanced(use_copula=True)
    models = _get_imputation_models()
    if len(models) < 2:
        print("可用模型不足 2 个，请检查依赖。")
        sys.exit(1)
    print(f"   可用模型数: {len(models)}")

    # 步骤2：对每个品类（如大米、牛肉等），在「有观测到户内/户内外消费量」的样本上做 5 折交叉验证，
    # 用各模型预测「户内/户内外」再算 ratio，与真实 ratio 比较，得到 MAE/RMSE/R2，用于后面选最优模型。
    print("\n2. 按品类在观测数据上做交叉验证，评估各模型补缺失精度（每个 model×品类 会训练多折，库内 epoch 输出已静默）...")
    results = []
    devnull = open(os.devnull, "w")
    for q_col, total_col in category_map.items():
        home_col = "home_" + total_col.replace("total_", "")
        if total_col not in df_micro.columns or home_col not in df_micro.columns:
            continue
        short = total_col.replace("total_", "")
        for model_name, train_func in models:
            try:
                print(f"   评估 {model_name} / {q_col} ...", end=" ", flush=True)
                old_stdout, old_stderr = sys.stdout, sys.stderr
                sys.stdout, sys.stderr = devnull, devnull
                try:
                    if model_name == "fttransformer":
                        from predict_fttransformer_advanced import evaluate_imputation_cv_fttransformer
                        metrics = evaluate_imputation_cv_fttransformer(
                            df_micro, feature_cols, total_col, home_col, n_splits=5
                        )
                    else:
                        metrics = evaluate_imputation_cv(
                            df_micro, feature_cols, total_col, home_col, train_func, n_splits=5
                        )
                finally:
                    sys.stdout, sys.stderr = old_stdout, old_stderr
                if metrics is not None:
                    results.append({
                        "model": model_name,
                        "category": q_col,
                        "short": short,
                        "MAE": metrics["MAE"],
                        "RMSE": metrics["RMSE"],
                        "R2": metrics["R2"],
                    })
                    print(f"MAE={metrics['MAE']:.4f} RMSE={metrics['RMSE']:.4f} R2={metrics['R2']:.4f}")
                else:
                    print("跳过(数据不足)")
            except Exception as e:
                print(f"\n   {model_name} / {q_col}: {e}")
    devnull.close()
    if not results:
        print("   无有效评估结果。")
        sys.exit(1)
    df_res = pd.DataFrame(results)

    print("\n3. 按模型汇总（各品类 MAE 平均），选 MAE 最小的模型...")
    agg = df_res.groupby("model").agg(MAE=("MAE", "mean"), RMSE=("RMSE", "mean"), R2=("R2", "mean")).reset_index()
    agg = agg.sort_values("MAE").reset_index(drop=True)
    agg["rank"] = np.arange(1, len(agg) + 1)
    agg["is_best"] = (agg["rank"] == 1)
    print(agg.to_string(index=False))
    best_model_name = agg.iloc[0]["model"]
    best_train_func = dict(models)[best_model_name]
    print(f"\n   选中模型: {best_model_name}")

    os.makedirs(DATA_DIR, exist_ok=True)
    df_res.to_csv(EVALUATION_DETAIL_CSV, index=False, encoding="utf-8-sig")
    agg.to_csv(SELECTION_RESULTS_CSV, index=False, encoding="utf-8-sig")
    print(f"   已保存评估明细: {EVALUATION_DETAIL_CSV}")
    print(f"   已保存汇总与选中结果: {SELECTION_RESULTS_CSV}")

    print("\n4. 用选中模型对所有品类做补缺失，生成统一样本...")
    out_cols = []
    for q_col, total_col in category_map.items():
        home_col = "home_" + total_col.replace("total_", "")
        if total_col not in df_micro.columns or home_col not in df_micro.columns:
            continue
        short = total_col.replace("total_", "")
        col_name = f"ratio_filled_{short}"
        try:
            if best_model_name == "fttransformer":
                from predict_fttransformer_advanced import impute_home_total_and_ratio_fttransformer
                df_filled = impute_home_total_and_ratio_fttransformer(
                    df_micro, feature_cols, total_col, home_col
                )
            else:
                df_filled = impute_home_total_and_ratio(
                    df_micro, feature_cols, total_col, home_col, best_train_func
                )
            if df_filled is not None:
                df_micro = df_micro.copy()
                df_micro[col_name] = np.nan
                df_micro.loc[df_filled.index, col_name] = df_filled["ratio_filled"].values
                out_cols.append(col_name)
        except Exception as e:
            print(f"   {q_col} 补缺失失败: {e}")
    if not out_cols:
        print("   未生成任何补缺失列。")
        sys.exit(1)
    df_save = df_micro[out_cols].copy()
    df_save.to_csv(IMPUTED_RATIOS_FILE, index=True)
    with open(BEST_MODEL_FILE, "w", encoding="utf-8") as f:
        f.write(best_model_name)
    print(f"   已保存: {IMPUTED_RATIOS_FILE}")
    print(f"   已保存: {BEST_MODEL_FILE}")
    print("\n后续各模型预测户内消费系数时，主流程将自动使用该补缺失样本（稳健性仍为不补缺失）。")


if __name__ == "__main__":
    main()
