#!/usr/bin/env python3
"""
对指定模型运行 Bootstrap 预测区间：多次用不同随机种子运行预测，汇总得到均值与 2.5%/97.5% 分位数。
用法: python run_bootstrap.py <model_name> [n_bootstrap]
例如: python run_bootstrap.py lightgbm 50
模型名: lightgbm, lasso, linear, xgboost, catboost, randomforest, mlp, tabnet, tabm, tabpfn, resnet_tabular, fttransformer
"""

import os
import sys
import subprocess
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS = [
    "lightgbm", "lasso", "linear", "xgboost", "catboost", "randomforest",
    "mlp", "tabnet", "tabm", "tabpfn", "resnet_tabular", "fttransformer",
]
SCRIPT_MAP = {m: f"predict_{m}.py" for m in MODELS}

# 为避免由极小 home/total 预测导致的发散（coef = 1/home_share），
# 在汇总 bootstrap 区间前对系数进行温和 winsorization。
# 这不会影响系数“>=1”的经济含义，但能显著提升区间的可解释性与可复现性。
COEF_MIN = 1.0
COEF_MAX = 10.0


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in SCRIPT_MAP:
        print("用法: python run_bootstrap.py <model_name> [n_bootstrap=30]")
        print("模型名:", ", ".join(MODELS))
        sys.exit(1)
    model_name = sys.argv[1]
    n_bootstrap = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    script = os.path.join(BASE_DIR, SCRIPT_MAP[model_name])
    if not os.path.isfile(script):
        print(f"未找到脚本: {script}")
        sys.exit(1)

    out_bootstrap = os.path.join(BASE_DIR, f"predictions_{model_name}_bootstrap.csv")
    env = os.environ.copy()
    collected = []
    for b in range(n_bootstrap):
        seed = 42 + b
        env["PREDICT_SEED"] = str(seed)
        ret = subprocess.run(
            [sys.executable, script],
            cwd=BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        if ret.returncode != 0:
            print(f"  seed {seed} 失败: {ret.stderr[:200] if ret.stderr else ret.stdout[:200]}")
            continue
        path = os.path.join(BASE_DIR, f"predictions_{model_name}_seed{seed}.csv")
        if os.path.isfile(path):
            df = pd.read_csv(path)
            collected.append(df)
            try:
                os.remove(path)
            except Exception:
                pass
        else:
            print(f"  seed {seed} 未生成 {path}，请确认该脚本在 PREDICT_SEED!=42 时写入该文件")
    if not collected:
        print("无有效 Bootstrap 运行结果")
        sys.exit(1)
    # 对齐列：以 Province, Year 为索引，各 Category 列取均值与分位数
    id_cols = ["Province", "Year"]
    # 仅保留系数列；部分脚本在 seed 运行时可能写出额外列，需显式筛选
    coef_cols = [c for c in collected[0].columns if (c not in id_cols and str(c).startswith("q_"))]
    all_dfs = []
    for df in collected:
        df = df.set_index(id_cols)
        # 只保留共同存在的系数列
        keep = [c for c in coef_cols if c in df.columns]
        df = df[keep]
        # winsorize 以避免极端值支配均值与分位数
        df = df.clip(lower=COEF_MIN, upper=COEF_MAX)
        all_dfs.append(df)
    stack = np.stack([d.values.astype(np.float64) for d in all_dfs], axis=0)
    mean_val = np.nanmean(stack, axis=0)
    low_val = np.nanpercentile(stack, 2.5, axis=0)
    high_val = np.nanpercentile(stack, 97.5, axis=0)
    index_df = collected[0].reset_index()[id_cols]
    result = index_df.copy()
    for i, c in enumerate(all_dfs[0].columns):
        result[c + "_Mean"] = mean_val[:, i]
        result[c + "_Lower"] = low_val[:, i]
        result[c + "_Upper"] = high_val[:, i]
    result.to_csv(out_bootstrap, index=False)
    print(f"Bootstrap 完成: {len(collected)}/{n_bootstrap} 次，已保存 {out_bootstrap}")


if __name__ == "__main__":
    main()
