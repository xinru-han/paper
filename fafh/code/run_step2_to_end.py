#!/usr/bin/env python3
"""
步骤 2～5：12 个模型主流程预测 → 后处理与模型比较 → 稳健性检验 → Bootstrap（可选）。
执行进度同步输出到 step2_to_end_log.txt，便于随时检查。
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = BASE_DIR
LOG_FILE = os.path.join(BASE_DIR, "step2_to_end_log.txt")

MODELS = [
    "lightgbm", "lasso", "linear", "xgboost", "catboost", "randomforest",
    "mlp", "tabnet", "tabm", "resnet_tabular", "fttransformer", "tabpfn",
]
SCRIPT_MAP = {m: f"predict_{m}.py" for m in MODELS}
IMPUTED_RATIOS_FILE = os.path.join(DATA_DIR, "imputed_ratios_best.csv")
MODEL_COMPARISON_CSV = os.path.join(OUTPUT_DIR, "model_comparison_national.csv")
PIPELINE_SUMMARY_MD = os.path.join(OUTPUT_DIR, "pipeline_summary.md")
ACCURACY_DETAIL_CSV = os.path.join(OUTPUT_DIR, "model_accuracy_detail.csv")
ACCURACY_SUMMARY_CSV = os.path.join(OUTPUT_DIR, "model_accuracy_summary.csv")
COMPARE_ACCURACY_SCRIPT = os.path.join(BASE_DIR, "compare_model_accuracy.py")


def log_print(msg, log_handle):
    """同时写入日志文件并打印到控制台。"""
    line = msg if msg.endswith("\n") else msg + "\n"
    log_handle.write(line)
    log_handle.flush()
    print(msg, end="" if msg.endswith("\n") else "\n", flush=True)


def run_cmd(cmd, log_handle, timeout=3600, cwd=BASE_DIR, env=None):
    """运行命令，实时将 stdout/stderr 写入日志并打印。"""
    env = env or os.environ.copy()
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    for line in proc.stdout:
        log_print(line.rstrip(), log_handle)
    ret = proc.wait(timeout=timeout)
    return ret


def run_step_2(log_handle):
    log_print("\n" + "=" * 60, log_handle)
    log_print("步骤 2：12 个模型主流程预测（使用补缺失样本）", log_handle)
    log_print("=" * 60, log_handle)
    env = os.environ.copy()
    env["PREDICT_SEED"] = "42"
    for i, name in enumerate(MODELS, 1):
        script = os.path.join(BASE_DIR, SCRIPT_MAP.get(name, f"predict_{name}.py"))
        if not os.path.isfile(script):
            log_print(f"  [{i}/{len(MODELS)}] 跳过 {name}（无脚本）", log_handle)
            continue
        if name == "tabpfn":
            log_print(f"  [{i}/{len(MODELS)}] 运行 {name}（最后一个模型，运行较慢，请耐心等待）...", log_handle)
            log_print(f"    开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", log_handle)
        else:
            log_print(f"  [{i}/{len(MODELS)}] 运行 {name} ...", log_handle)
        ret = run_cmd([sys.executable, script], log_handle, timeout=7200 if name == "tabpfn" else 3600, env=env)
        if ret != 0:
            log_print(f"    {name} 退出码: {ret}", log_handle)
        elif name == "tabpfn":
            log_print(f"    {name} 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", log_handle)
    log_print("步骤 2 完成。", log_handle)


def run_step_3(log_handle):
    log_print("\n" + "=" * 60, log_handle)
    log_print("步骤 3：后处理与模型比较", log_handle)
    log_print("=" * 60, log_handle)
    sys.path.insert(0, BASE_DIR)
    try:
        from postprocess_predictions import run as run_postprocess
    except ImportError as e:
        log_print(f"无法导入 postprocess_predictions: {e}", log_handle)
        return
    national_dfs = []
    for name in MODELS:
        pred_path = os.path.join(BASE_DIR, f"predictions_{name}.csv")
        if not os.path.isfile(pred_path):
            continue
        try:
            df_prov, df_nat = run_postprocess(pred_path)
            if df_nat is not None and not df_nat.empty:
                df_nat["model"] = name
                national_dfs.append(df_nat)
        except Exception as e:
            log_print(f"  后处理 {name} 失败: {e}", log_handle)
    if national_dfs:
        import pandas as pd
        df_all = pd.concat(national_dfs, ignore_index=True)
        coef_cols = [c for c in df_all.columns if c.startswith("全国户外消费系数_")]
        id_cols = ["Year", "model"]
        keep = [c for c in id_cols + coef_cols if c in df_all.columns]
        df_wide = df_all[keep].copy()
        df_wide.to_csv(MODEL_COMPARISON_CSV, index=False, encoding="utf-8-sig")
        log_print(f"  已保存模型比较表: {MODEL_COMPARISON_CSV}", log_handle)
    log_print("步骤 3 完成。", log_handle)


def run_step_3_5_accuracy(log_handle, timeout=7200):
    """步骤 3.5：对比各模型预测精度（交叉验证 MAE、RMSE、R²、MAPE）。"""
    log_print("\n" + "=" * 60, log_handle)
    log_print("步骤 3.5：预测精度对比（交叉验证 RMSE / MAE / R² / MAPE）", log_handle)
    log_print("=" * 60, log_handle)
    if not os.path.isfile(COMPARE_ACCURACY_SCRIPT):
        log_print(f"  未找到 {COMPARE_ACCURACY_SCRIPT}，跳过精度对比。", log_handle)
        return
    log_print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", log_handle)
    ret = run_cmd([sys.executable, COMPARE_ACCURACY_SCRIPT], log_handle, timeout=timeout)
    if ret == 0:
        log_print(f"  完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", log_handle)
        if os.path.isfile(ACCURACY_SUMMARY_CSV):
            log_print(f"  已保存精度汇总: {ACCURACY_SUMMARY_CSV}", log_handle)
        if os.path.isfile(ACCURACY_DETAIL_CSV):
            log_print(f"  已保存精度明细: {ACCURACY_DETAIL_CSV}", log_handle)
    else:
        log_print(f"  预测精度对比退出码: {ret}", log_handle)
    log_print("步骤 3.5 完成。", log_handle)


def run_step_4(log_handle):
    log_print("\n" + "=" * 60, log_handle)
    log_print("步骤 4：稳健性检验（不补缺失样本）", log_handle)
    log_print("=" * 60, log_handle)
    env = os.environ.copy()
    env["PREDICT_SEED"] = "42"
    sys.path.insert(0, BASE_DIR)
    try:
        from postprocess_predictions import run as run_postprocess
    except ImportError:
        run_postprocess = None
    for i, name in enumerate(MODELS, 1):
        script = os.path.join(BASE_DIR, SCRIPT_MAP.get(name, f"predict_{name}.py"))
        if not os.path.isfile(script):
            continue
        robust_path = os.path.join(BASE_DIR, f"predictions_{name}_robust.csv")
        if os.path.isfile(robust_path):
            log_print(f"  [{i}/{len(MODELS)}] {name} 已存在 robust，跳过运行", log_handle)
            if run_postprocess:
                try:
                    run_postprocess(robust_path)
                except Exception:
                    pass
            continue
        if name == "tabpfn":
            log_print(f"  [{i}/{len(MODELS)}] 运行 {name}（主流程含 robust，运行较慢，请耐心等待）", log_handle)
            log_print(f"    开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", log_handle)
        else:
            log_print(f"  [{i}/{len(MODELS)}] 运行 {name}（主流程含 robust）", log_handle)
        ret = run_cmd([sys.executable, script], log_handle, timeout=7200 if name == "tabpfn" else 3600, env=env)
        if name == "tabpfn" and ret == 0:
            log_print(f"    {name} 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", log_handle)
        if ret == 0 and run_postprocess and os.path.isfile(robust_path):
            try:
                run_postprocess(robust_path)
            except Exception:
                pass
    log_print("步骤 4 完成。", log_handle)


def run_step_5(log_handle, n_bootstrap=30, models_subset=None):
    models = models_subset if models_subset is not None else MODELS
    log_print("\n" + "=" * 60, log_handle)
    log_print("步骤 5：Bootstrap 预测区间", log_handle)
    log_print("=" * 60, log_handle)
    for i, name in enumerate(models, 1):
        script = os.path.join(BASE_DIR, SCRIPT_MAP.get(name, f"predict_{name}.py"))
        if not os.path.isfile(script):
            log_print(f"  [{i}/{len(models)}] 跳过 {name}（无脚本）", log_handle)
            continue
        log_print(f"  [{i}/{len(models)}] Bootstrap {name} (n={n_bootstrap}) ...", log_handle)
        ret = run_cmd(
            [sys.executable, os.path.join(BASE_DIR, "run_bootstrap.py"), name, str(n_bootstrap)],
            log_handle,
            timeout=3600 * 2,
        )
        if ret != 0:
            log_print(f"    {name} bootstrap 失败: {ret}", log_handle)
    log_print("步骤 5 完成。", log_handle)


def write_pipeline_summary(log_handle, bootstrap_done=False):
    lines = [
        "# 户外消费系数研究流程摘要（步骤 2～5）",
        "",
        "## 已执行步骤",
        "2. 12 个模型主流程预测",
        "3. 后处理与模型比较",
        "3.5. 预测精度对比（交叉验证 RMSE/MAE/R²/MAPE）",
        "4. 稳健性检验",
        "5. Bootstrap 预测区间" + ("（已执行）" if bootstrap_done else "（未执行）"),
        "",
        "## 主要输出文件",
        "- 各模型预测: `predictions_<model>.csv`",
        "- 各模型稳健结果: `predictions_<model>_robust.csv`",
        "- 各模型 Bootstrap: `predictions_<model>_bootstrap.csv`",
        "- 模型比较（全国）: `model_comparison_national.csv`",
        "- 预测精度明细: `model_accuracy_detail.csv`（各模型×品类 MAE/RMSE/R²/MAPE）",
        "- 预测精度汇总: `model_accuracy_summary.csv`（按模型平均及排名）",
        "- 省级/全国户内外消费量: `results_province_<model>.csv`, `results_national_<model>.csv`",
        "",
    ]
    with open(PIPELINE_SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log_print(f"已写入流程摘要: {PIPELINE_SUMMARY_MD}", log_handle)


def main():
    parser = argparse.ArgumentParser(description="步骤 2～5：模型预测、后处理、稳健性、Bootstrap")
    parser.add_argument("--bootstrap", nargs="?", const="all", default=None,
                        help="执行步骤 5；可选 all 或整数（仅前 N 个模型）")
    parser.add_argument("--n-bootstrap", type=int, default=30, help="Bootstrap 次数")
    args = parser.parse_args()

    if not os.path.isfile(IMPUTED_RATIOS_FILE):
        print("未找到 data/imputed_ratios_best.csv，请先运行 run_step1_imputation.py")
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)
    log = open(LOG_FILE, "w", encoding="utf-8")
    try:
        log.write(f"[{datetime.now().isoformat()}] 步骤 2～5 开始\n")
        log.write(f"日志同步写入: {LOG_FILE}\n")
        log.flush()
        log_print(f"\n日志同步写入: {LOG_FILE}\n", log)

        run_step_2(log)
        run_step_3(log)
        run_step_3_5_accuracy(log)
        run_step_4(log)

        bootstrap_done = False
        if args.bootstrap is not None:
            if args.bootstrap == "all":
                run_step_5(log, n_bootstrap=args.n_bootstrap)
                bootstrap_done = True
            else:
                try:
                    n_models = int(args.bootstrap)
                    run_step_5(log, n_bootstrap=args.n_bootstrap, models_subset=MODELS[:n_models])
                    bootstrap_done = True
                except ValueError:
                    run_step_5(log, n_bootstrap=args.n_bootstrap)
                    bootstrap_done = True

        write_pipeline_summary(log, bootstrap_done=bootstrap_done)
        log_print("\n" + "=" * 60, log)
        log_print("步骤 2～5 全部结束。", log)
        log_print("=" * 60, log)
    except Exception as e:
        log_print(f"执行异常: {e}", log)
        log.write(f"\n[{datetime.now().isoformat()}] 异常: {e}\n")
        sys.exit(1)
    finally:
        log.write(f"\n[{datetime.now().isoformat()}] 步骤 2～5 结束\n")
        log.close()


if __name__ == "__main__":
    main()
