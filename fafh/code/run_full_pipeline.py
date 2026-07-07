#!/usr/bin/env python3
"""
户外消费系数研究完整流程（符合学术规范）。

流程顺序：
1. 缺失值补全与模型选择：12 种模型评估补缺失精度（MAE/RMSE/R²），选出最优，生成统一样本。
2. 12 个模型主流程预测：各模型在补缺失样本上预测户外消费系数，生成 predictions_<model>.csv。
3. 后处理与模型比较：生成省级/全国户内外消费量；汇总各模型全国结果，用于比较。
4. 稳健性检验：各模型在不补缺失样本上预测，生成 predictions_<model>_robust.csv 及对应全国结果。
5. Bootstrap 预测区间：对指定模型多次不同种子预测，汇总均值与 2.5%/97.5% 分位数。

用法:
  python run_full_pipeline.py                    # 执行步骤 1–4（不跑 Bootstrap）
  python run_full_pipeline.py --bootstrap        # 执行步骤 1–5（对全部 12 个模型跑 Bootstrap）
  python run_full_pipeline.py --bootstrap 5      # 仅对前 5 个模型跑 Bootstrap（示例）
  python run_full_pipeline.py --skip-imputation   # 跳过步骤 1（已存在 imputed_ratios_best.csv 时）
"""

import os
import sys
import subprocess
import argparse
import pandas as pd
import numpy as np
from glob import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = BASE_DIR

# 12 个模型名称（与 predict_<name>.py 及后处理输出一致）
MODELS = [
    "lightgbm", "lasso", "linear", "xgboost", "catboost", "randomforest",
    "mlp", "tabnet", "tabm", "tabpfn", "resnet_tabular", "fttransformer",
]
SCRIPT_MAP = {m: f"predict_{m}.py" for m in MODELS}
# Bootstrap 脚本中 fttransformer 对应 predict_fttransformer.py
BOOTSTRAP_SCRIPT_MAP = {m: f"predict_{m}.py" for m in MODELS}

IMPUTED_RATIOS_FILE = os.path.join(DATA_DIR, "imputed_ratios_best.csv")
BEST_IMPUTATION_FILE = os.path.join(DATA_DIR, "best_imputation_model.txt")
IMPUTATION_RESULTS_CSV = os.path.join(DATA_DIR, "imputation_selection_results.csv")
MODEL_COMPARISON_CSV = os.path.join(OUTPUT_DIR, "model_comparison_national.csv")
PIPELINE_SUMMARY_MD = os.path.join(OUTPUT_DIR, "pipeline_summary.md")


def run_step_1_imputation():
    """步骤 1：缺失值补全模型选择，生成统一样本。"""
    print("\n" + "=" * 60)
    print("步骤 1：缺失值补全与模型选择（MAE/RMSE/R²）")
    print("=" * 60)
    ret = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "run_imputation_selection.py")],
        cwd=BASE_DIR,
        timeout=7200,
    )
    if ret.returncode != 0:
        print("步骤 1 失败，退出码:", ret.returncode)
        sys.exit(1)
    if not os.path.isfile(IMPUTED_RATIOS_FILE):
        print("未生成 imputed_ratios_best.csv")
        sys.exit(1)
    print("步骤 1 完成。")
    return True


def run_step_2_predictions(models=None):
    """步骤 2：12 个模型主流程预测（使用补缺失样本）。"""
    models = models or MODELS
    print("\n" + "=" * 60)
    print("步骤 2：12 个模型主流程预测")
    print("=" * 60)
    env = os.environ.copy()
    env["PREDICT_SEED"] = "42"
    for i, name in enumerate(models, 1):
        script = os.path.join(BASE_DIR, SCRIPT_MAP.get(name, f"predict_{name}.py"))
        if not os.path.isfile(script):
            print(f"  [{i}/{len(models)}] 跳过 {name}（无脚本 {script}）")
            continue
        print(f"  [{i}/{len(models)}] 运行 {name} ...")
        ret = subprocess.run(
            [sys.executable, script],
            cwd=BASE_DIR,
            env=env,
            timeout=3600,
        )
        if ret.returncode != 0:
            print(f"    {name} 失败，退出码: {ret.returncode}")
    print("步骤 2 完成。")
    return True


def run_step_3_postprocess_and_compare(models=None):
    """步骤 3：后处理（省级/全国户内外消费量）并汇总各模型全国结果，用于模型比较。"""
    models = models or MODELS
    print("\n" + "=" * 60)
    print("步骤 3：后处理与模型比较")
    print("=" * 60)
    sys.path.insert(0, BASE_DIR)
    try:
        from postprocess_predictions import run as run_postprocess
    except ImportError as e:
        print("无法导入 postprocess_predictions:", e)
        return False

    national_dfs = []
    for name in models:
        pred_path = os.path.join(BASE_DIR, f"predictions_{name}.csv")
        if not os.path.isfile(pred_path):
            continue
        try:
            df_prov, df_nat = run_postprocess(pred_path)
            if df_nat is not None and not df_nat.empty:
                df_nat["model"] = name
                national_dfs.append(df_nat)
        except Exception as e:
            print(f"  后处理 {name} 失败: {e}")

    if national_dfs:
        # 汇总全国结果：各模型一行，列為各品类全国户外消费系数等
        df_all = pd.concat(national_dfs, ignore_index=True)
        # 保存宽表：Year, model, 以及各 全国户外消费系数_* 列
        coef_cols = [c for c in df_all.columns if c.startswith("全国户外消费系数_")]
        id_cols = ["Year", "model"]
        keep = [c for c in id_cols + coef_cols if c in df_all.columns]
        df_wide = df_all[keep].copy()
        df_wide.to_csv(MODEL_COMPARISON_CSV, index=False, encoding="utf-8-sig")
        print(f"  已保存模型比较表: {MODEL_COMPARISON_CSV}")
    print("步骤 3 完成。")
    return True


def run_step_4_robust(models=None):
    """步骤 4：稳健性检验（不补缺失）。"""
    models = models or MODELS
    print("\n" + "=" * 60)
    print("步骤 4：稳健性检验（不补缺失样本）")
    print("=" * 60)
    env = os.environ.copy()
    env["PREDICT_SEED"] = "42"
    for i, name in enumerate(models, 1):
        script = os.path.join(BASE_DIR, SCRIPT_MAP.get(name, f"predict_{name}.py"))
        if not os.path.isfile(script):
            continue
        robust_path = os.path.join(BASE_DIR, f"predictions_{name}_robust.csv")
        if os.path.isfile(robust_path):
            print(f"  [{i}/{len(models)}] {name} 已存在 robust 结果，跳过运行")
            # 仍做后处理
            try:
                from postprocess_predictions import run as run_postprocess
                run_postprocess(robust_path)
            except Exception:
                pass
            continue
        # 各 predict_*.py 在主流程会生成主结果与 robust；robust 为 use_impute=False
        # 通常一次运行会同时写 predictions_<name>.csv 和 predictions_<name>_robust.csv
        print(f"  [{i}/{len(models)}] 运行 {name}（主流程已含 robust 分支）")
        ret = subprocess.run([sys.executable, script], cwd=BASE_DIR, env=env, timeout=3600)
        if ret.returncode != 0:
            print(f"    {name} 失败: {ret.returncode}")
        else:
            try:
                from postprocess_predictions import run as run_postprocess
                run_postprocess(robust_path)
            except Exception:
                pass
    print("步骤 4 完成。")
    return True


def run_step_5_bootstrap(models=None, n_bootstrap=30):
    """步骤 5：Bootstrap 预测区间。"""
    models = models or MODELS
    print("\n" + "=" * 60)
    print("步骤 5：Bootstrap 预测区间")
    print("=" * 60)
    for i, name in enumerate(models, 1):
        script = os.path.join(BASE_DIR, BOOTSTRAP_SCRIPT_MAP.get(name, f"predict_{name}.py"))
        if not os.path.isfile(script):
            print(f"  [{i}/{len(models)}] 跳过 {name}（无脚本）")
            continue
        print(f"  [{i}/{len(models)}] Bootstrap {name} (n={n_bootstrap}) ...")
        ret = subprocess.run(
            [sys.executable, os.path.join(BASE_DIR, "run_bootstrap.py"), name, str(n_bootstrap)],
            cwd=BASE_DIR,
            timeout=3600 * 2,
        )
        if ret.returncode != 0:
            print(f"    {name} bootstrap 失败: {ret.returncode}")
    print("步骤 5 完成。")
    return True


def write_pipeline_summary(skip_imputation=False, bootstrap_done=False):
    """写入流程摘要到 pipeline_summary.md（简要记录步骤与输出文件）。"""
    lines = [
        "# 户外消费系数研究流程摘要",
        "",
        "## 已执行步骤",
        "1. 缺失值补全与模型选择" + ("（已跳过）" if skip_imputation else ""),
        "2. 12 个模型主流程预测",
        "3. 后处理与模型比较",
        "4. 稳健性检验",
        "5. Bootstrap 预测区间" + ("（已执行）" if bootstrap_done else "（未执行）"),
        "",
        "## 主要输出文件",
        "- 补缺失统一样本: `data/imputed_ratios_best.csv`",
        "- 补缺失选用模型: `data/best_imputation_model.txt`",
        "- 补缺失评估结果: `data/imputation_selection_results.csv`",
        "- 各模型预测: `predictions_<model>.csv`",
        "- 各模型稳健结果: `predictions_<model>_robust.csv`",
        "- 各模型 Bootstrap: `predictions_<model>_bootstrap.csv`",
        "- 模型比较（全国）: `model_comparison_national.csv`",
        "- 省级/全国户内外消费量: `results_province_<model>.csv`, `results_national_<model>.csv`",
        "",
    ]
    with open(PIPELINE_SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"已写入流程摘要: {PIPELINE_SUMMARY_MD}")


def main():
    parser = argparse.ArgumentParser(description="户外消费系数研究完整流程")
    parser.add_argument("--skip-imputation", action="store_true", help="跳过步骤 1（已存在统一样本时）")
    parser.add_argument("--bootstrap", nargs="?", const="all", default=None,
                        help="执行步骤 5 Bootstrap；可选值 all 或整数（仅前 N 个模型）")
    parser.add_argument("--n-bootstrap", type=int, default=30, help="Bootstrap 次数，默认 30")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    if not args.skip_imputation:
        run_step_1_imputation()
    else:
        if not os.path.isfile(IMPUTED_RATIOS_FILE):
            print("跳过补缺失但未找到 imputed_ratios_best.csv，请先运行步骤 1 或去掉 --skip-imputation")
            sys.exit(1)
        print("\n跳过步骤 1（使用已有 imputed_ratios_best.csv）")

    run_step_2_predictions()
    run_step_3_postprocess_and_compare()
    run_step_4_robust()

    bootstrap_done = False
    if args.bootstrap is not None:
        if args.bootstrap == "all":
            run_step_5_bootstrap(n_bootstrap=args.n_bootstrap)
            bootstrap_done = True
        else:
            try:
                n_models = int(args.bootstrap)
                run_step_5_bootstrap(models=MODELS[:n_models], n_bootstrap=args.n_bootstrap)
                bootstrap_done = True
            except ValueError:
                run_step_5_bootstrap(n_bootstrap=args.n_bootstrap)
                bootstrap_done = True

    write_pipeline_summary(skip_imputation=args.skip_imputation, bootstrap_done=bootstrap_done)
    print("\n" + "=" * 60)
    print("完整流程结束。详见 研究逻辑与方法.md 与 pipeline_summary.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
