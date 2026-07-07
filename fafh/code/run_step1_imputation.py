#!/usr/bin/env python3
"""
步骤 1：缺失值补全与模型选择（MAE/RMSE/R²）。
执行进度同步输出到 step1_imputation_log.txt，便于随时检查。
"""

import os
import sys
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_FILE = os.path.join(BASE_DIR, "step1_imputation_log.txt")
IMPUTED_RATIOS_FILE = os.path.join(DATA_DIR, "imputed_ratios_best.csv")


def log_print(msg, log_handle):
    """同时写入日志文件并打印到控制台。"""
    line = msg if msg.endswith("\n") else msg + "\n"
    log_handle.write(line)
    log_handle.flush()
    print(msg, end="" if msg.endswith("\n") else "\n", flush=True)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    log = open(LOG_FILE, "w", encoding="utf-8")
    try:
        log.write(f"[{datetime.now().isoformat()}] 步骤 1 开始：缺失值补全与模型选择\n")
        log.write("=" * 60 + "\n")
        log.flush()
        log_print("\n" + "=" * 60, log)
        log_print("步骤 1：缺失值补全与模型选择（MAE/RMSE/R²）", log)
        log_print("=" * 60, log)
        log_print(f"日志同步写入: {LOG_FILE}\n", log)

        cmd = [sys.executable, os.path.join(BASE_DIR, "run_imputation_selection.py")]
        proc = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )
        for line in proc.stdout:
            log_print(line.rstrip(), log)
        ret = proc.wait(timeout=7200)
        if ret != 0:
            log_print(f"步骤 1 退出码: {ret}", log)
            sys.exit(1)
        log_print("\n步骤 1 完成。", log)
        if os.path.isfile(IMPUTED_RATIOS_FILE):
            log_print(f"已生成: {IMPUTED_RATIOS_FILE}", log)
    except subprocess.TimeoutExpired:
        log_print("步骤 1 超时（7200s）", log)
        try:
            proc.kill()
        except NameError:
            pass
        sys.exit(1)
    except Exception as e:
        log_print(f"步骤 1 执行异常: {e}", log)
        log.write(f"\n[{datetime.now().isoformat()}] 异常: {e}\n")
        sys.exit(1)
    finally:
        log.write(f"\n[{datetime.now().isoformat()}] 步骤 1 结束\n")
        log.close()

    if not os.path.isfile(IMPUTED_RATIOS_FILE):
        print("未生成 imputed_ratios_best.csv，请检查日志:", LOG_FILE)
        sys.exit(1)


if __name__ == "__main__":
    main()
