#!/usr/bin/env python3
"""
各品种训练样本中户内消费系数（ratio）的详细统计描述，用于检查异常值。
与 predict_* 中训练时使用的样本一致：dropna(feature_cols + total_col + ratio_col)。
覆盖 category_map 中全部品种：稻谷、小麦、豆类、杂粮、蔬菜、猪肉、牛羊肉、禽肉、水产品、蛋类、奶类、水果。
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = BASE_DIR

def main():
    from data_preparation_advanced import load_and_prepare_data_advanced

    print("加载数据（与训练流程一致）...")
    df_micro, X_pred_feats, feature_cols, category_map, _ = load_and_prepare_data_advanced(use_copula=True)

    # 从 category_map 生成所有品种：(显示名, total_col, ratio_col, q_col)
    targets = []
    for q_col, total_col in category_map.items():
        name = total_col.replace("total_", "")
        ratio_col = "ratio_" + name
        targets.append((name, total_col, ratio_col, q_col))

    all_stats = []
    for name, total_col, ratio_col, q_col in targets:
        if total_col not in df_micro.columns or ratio_col not in df_micro.columns:
            print(f"\n[{name}] 缺少列 {total_col} 或 {ratio_col}，跳过")
            continue

        # 与训练时相同的样本：dropna(feature_cols + total_col + ratio_col)
        need_cols = list(dict.fromkeys(feature_cols + [total_col, ratio_col]))
        df_clean = df_micro.dropna(subset=need_cols).copy()
        df_clean = df_clean[df_clean[total_col] > 0].copy()
        r = df_clean[ratio_col].astype(float)

        n = len(r)
        print(f"\n{'='*60}")
        print(f"  {name}（{ratio_col}）— 训练样本户内消费系数")
        print(f"{'='*60}")
        print(f"  有效样本量: {n}")

        if n == 0:
            print(f"  无有效样本，跳过。")
            continue

        # 基本统计
        stats = {
            "品类": name,
            "q_col": q_col,
            "样本量": n,
            "均值": r.mean(),
            "标准差": r.std(),
            "最小值": r.min(),
            "最大值": r.max(),
            "中位数": r.median(),
        }
        for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
            stats[f"P{p}"] = r.quantile(p / 100.0)
        all_stats.append(stats)

        print(f"  均值:   {stats['均值']:.4f}")
        print(f"  标准差: {stats['标准差']:.4f}")
        print(f"  中位数: {stats['中位数']:.4f}")
        print(f"  最小值: {stats['最小值']:.4f}  最大值: {stats['最大值']:.4f}")
        print(f"  分位数: P1={stats['P1']:.4f}  P5={stats['P5']:.4f}  P25={stats['P25']:.4f}  P50={stats['P50']:.4f}  P75={stats['P75']:.4f}  P95={stats['P95']:.4f}  P99={stats['P99']:.4f}")

        # 异常值：常用阈值
        low_05 = (r < 0.05).sum()
        low_10 = (r < 0.10).sum()
        high_95 = (r > 0.95).sum()
        high_99 = (r > 0.99).sum()
        print(f"  异常值个数: ratio<0.05: {low_05}, ratio<0.10: {low_10}, ratio>0.95: {high_95}, ratio>0.99: {high_99}")

        # IQR 异常值
        q1, q3 = r.quantile(0.25), r.quantile(0.75)
        iqr = q3 - q1
        lb = q1 - 1.5 * iqr
        ub = q3 + 1.5 * iqr
        out_iqr = ((r < lb) | (r > ub)).sum()
        print(f"  IQR 异常值 (1.5*IQR): 下界={lb:.4f}, 上界={ub:.4f}, 异常个数={out_iqr}")

        # 分布：按区间计数
        bins = [0, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0]
        labels = ["(0,0.05]", "(0.05,0.1]", "(0.1,0.25]", "(0.25,0.5]", "(0.5,0.75]", "(0.75,0.9]", "(0.9,0.95]", "(0.95,1]"]
        r_bin = pd.cut(r, bins=bins, labels=labels, include_lowest=True)
        print(f"  区间分布:")
        for lbl in labels:
            c = (r_bin == lbl).sum()
            pct = 100.0 * c / n
            print(f"    {lbl}: {c} ({pct:.1f}%)")

        # 极端样本：最小/最大各若干条
        home_col = ratio_col.replace("ratio_", "home_")
        show_cols = ["T1", "wave", total_col, ratio_col]
        if home_col in df_clean.columns:
            show_cols = ["T1", "wave", total_col, home_col, ratio_col]
        df_clean = df_clean.sort_values(ratio_col)
        print(f"\n  户内消费系数最低的 10 条:")
        print(df_clean[show_cols].head(10).to_string(index=False))
        print(f"\n  户内消费系数最高的 10 条:")
        print(df_clean[show_cols].tail(10).to_string(index=False))
        print()

    # 汇总表写出
    if all_stats:
        df_stats = pd.DataFrame(all_stats)
        out_path = os.path.join(OUT_DIR, "describe_ratio_all.csv")
        df_stats.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"统计汇总已写入: {out_path}")

    # 写出各品种训练样本的 ratio 原始值
    for name, total_col, ratio_col, q_col in targets:
        if total_col not in df_micro.columns or ratio_col not in df_micro.columns:
            continue
        need_cols = list(dict.fromkeys(feature_cols + [total_col, ratio_col]))
        df_clean = df_micro.dropna(subset=need_cols).copy()
        df_clean = df_clean[df_clean[total_col] > 0]
        if df_clean.empty:
            continue
        fname = f"ratio_samples_{q_col.replace('q_', '')}.csv"
        df_clean[["T1", "wave", total_col, ratio_col]].to_csv(os.path.join(OUT_DIR, fname), index=False, encoding="utf-8-sig")
        print(f"训练样本 ratio 明细已写入: {fname}")

if __name__ == "__main__":
    main()
