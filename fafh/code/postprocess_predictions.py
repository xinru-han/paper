#!/usr/bin/env python3
"""
基于预测结果与 data_q.csv、粮食结构、人口，做后处理：
1. 合并粮食结构（稻谷、小麦、豆类、杂粮占比）
2. 用 data_q.csv 中各省户内食用消费量与预测的户外消费系数、粮食品种占比，计算各省各类食物户内外消费量
3. 按 procince_pop.csv 人口加权得到全国户内外消费量
"""

import pandas as pd
import numpy as np
import os
import argparse
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
POPULATION_FILE = os.path.join(DATA_DIR, "procince_pop.csv")
DATA_Q_FILE = os.path.join(DATA_DIR, "data_q.csv")

# data_q 中户内消费量列（人均）：与预测的户外消费系数列对应；含食用油、糖；牛肉与羊肉分开
DATA_Q_INDOOR_COLS = [
    "q_liangshi", "q_shucai", "q_zhurou", "q_niurou", "q_yangrou", "q_qinlei", "q_shuichanpin",
    "q_danlei", "q_nailei", "q_guaguo", "q_youliao", "q_tang",
]
# 预测表中户外消费系数列（非粮食类，与 DATA_Q_INDOOR_COLS 除 q_liangshi 外一一对应）
COEF_COLS_NON_GRAIN = [
    "q_shucai", "q_zhurou", "q_niurou", "q_yangrou", "q_qinlei", "q_shuichanpin",
    "q_danlei", "q_nailei", "q_guaguo", "q_youliao", "q_tang",
]
# 粮食四类：预测系数列与占比列
GRAIN_COEF_COLS = ["q_daogu", "q_xiaomai", "q_doulei", "q_zaliang"]
GRAIN_SHARE_COLS = ["稻谷占比", "小麦占比", "豆类占比", "杂粮占比"]


def _grain_structure_path(model_name: str) -> str:
    """各模型粮食结构文件与模型名区分。"""
    return os.path.join(BASE_DIR, f"grain_structure_predictions_{model_name}.csv")


def _model_name_from_predictions_path(path: str) -> str:
    basename = os.path.basename(path)
    if basename.startswith("predictions_") and basename.endswith(".csv"):
        return basename.replace("predictions_", "").replace(".csv", "")
    return ""


def load_population():
    df = pd.read_csv(POPULATION_FILE)
    df = df.rename(columns={"T1": "Province", "wave": "Year"})
    return df[["Province", "Year", "pop"]]


def load_data_q():
    """各省户内食用消费量（人均）：data_q.csv，列 q_liangshi, q_shiyongyou, q_shucai 等。"""
    if not os.path.isfile(DATA_Q_FILE):
        return None
    df = pd.read_csv(DATA_Q_FILE)
    df = df.rename(columns={"T1": "Province", "wave": "Year"})
    return df


def load_grain_structure(grain_path: str):
    """稻谷、小麦、豆类、杂粮占比（四类之和为 1）。"""
    if not os.path.isfile(grain_path):
        return None
    df = pd.read_csv(grain_path)
    if "Year" not in df.columns and "wave" in df.columns:
        df = df.rename(columns={"wave": "Year"})
    # 优先用 _Final，否则 _Direct
    renames = {}
    for name, final_name, direct_name in [
        ("稻谷占比", "Share_Paddy_Final", "Share_Paddy_Direct"),
        ("小麦占比", "Share_Wheat_Final", "Share_Wheat_Direct"),
        ("豆类占比", "Share_Beans_Final", "Share_Beans_Direct"),
        ("杂粮占比", "Share_Other_Final", "Share_Other_Direct"),
    ]:
        if final_name in df.columns:
            renames[final_name] = name
        elif direct_name in df.columns:
            renames[direct_name] = name
    if not renames:
        return None
    use_cols = ["Province", "Year"] + list(renames.keys())
    df = df[[c for c in use_cols if c in df.columns]].copy()
    df = df.rename(columns=renames)
    # 若缺某类占比，用 1 减去已有占比并归一化
    for c in GRAIN_SHARE_COLS:
        if c not in df.columns:
            df[c] = np.nan
    share_cols = [c for c in GRAIN_SHARE_COLS if c in df.columns]
    if share_cols:
        s = df[share_cols].fillna(0).clip(0, 1)
        tot = s.sum(axis=1).replace(0, np.nan)
        df[share_cols] = s.div(tot, axis=0).fillna(1.0 / len(share_cols))
    return df


def add_province_consumption(df_merged: pd.DataFrame, df_q: pd.DataFrame, df_pop: pd.DataFrame):
    """
    根据 data_q 各省户内消费量、预测的户外消费系数和粮食品种占比，计算各省户内与户内外消费量。
    df_merged 需含 Province, Year，户外消费系数列 q_daogu, q_xiaomai, ...，以及稻谷/小麦/豆类/杂粮占比。
    """
    df_merged = df_merged.copy()
    df_merged = df_merged.merge(df_pop, on=["Province", "Year"], how="left")
    df_merged["pop"] = df_merged["pop"].fillna(0)
    df_merged = df_merged.merge(
        df_q[["Province", "Year"] + [c for c in DATA_Q_INDOOR_COLS if c in df_q.columns]],
        on=["Province", "Year"],
        how="left",
    )

    # 粮食：q_liangshi 按占比拆成四类，再分别乘户外系数
    if "q_liangshi" in df_merged.columns:
        q_liang = df_merged["q_liangshi"].fillna(0)
        pop = df_merged["pop"]
        for coef_col, share_col in zip(GRAIN_COEF_COLS, GRAIN_SHARE_COLS):
            if coef_col not in df_merged.columns or share_col not in df_merged.columns:
                continue
            share = df_merged[share_col].fillna(0.25)
            coef = df_merged[coef_col].fillna(1.0)
            # 省户内人均 * 占比 → 该类户内人均；省户内外 = 户内人均 * 系数 * 人口
            indoor_pc = q_liang * share
            df_merged[f"户内消费量_{coef_col.replace('q_', '')}"] = indoor_pc * pop
            df_merged[f"户内外消费量_{coef_col.replace('q_', '')}"] = indoor_pc * coef * pop

    # 非粮食：户内外 = 户内人均 * 户外消费系数 * 人口
    for q_col in COEF_COLS_NON_GRAIN:
        if q_col not in df_merged.columns or q_col not in df_q.columns:
            continue
        indoor_pc = df_merged[q_col].fillna(0)  # 这里 q_col 在 merge 后是 data_q 的户内人均
        coef_col = q_col  # 预测表里系数列名也是 q_*
        if coef_col in df_merged.columns:
            # 避免重复列：data_q 的列会带后缀 _x，预测的为 _y 或原名
            for c in [coef_col, f"{coef_col}_x", f"{coef_col}_y"]:
                if c in df_merged.columns and c != q_col:
                    coef_vals = df_merged[c]
                    break
            else:
                coef_vals = df_merged[coef_col].fillna(1.0)
        else:
            coef_vals = df_merged.get(coef_col, pd.Series(1.0, index=df_merged.index)).fillna(1.0)
        pop = df_merged["pop"]
        cat = q_col.replace("q_", "")
        df_merged[f"户内消费量_{cat}"] = indoor_pc * pop
        df_merged[f"户内外消费量_{cat}"] = indoor_pc * coef_vals * pop

    return df_merged


def _ensure_coef_and_indoor_columns(df_merged: pd.DataFrame, df_pred: pd.DataFrame):
    """合并后预测的系数列可能为 coef_col 或 coef_col_y；户内来自 data_q 为 q_col 或 q_col_x。统一到标准列名便于计算。"""
    df_merged = df_merged.copy()
    # 预测表提供的系数列
    for c in list(df_pred.columns):
        if c in ["Province", "Year"] or not c.startswith("q_"):
            continue
        if c in df_merged.columns:
            continue
        if f"{c}_y" in df_merged.columns:
            df_merged[c + "_coef"] = df_merged[f"{c}_y"]
        elif c in df_pred.columns:
            df_merged[c + "_coef"] = df_merged.get(c, np.nan)
    return df_merged


def add_province_consumption_v2(df_pred: pd.DataFrame, df_q: pd.DataFrame, df_pop: pd.DataFrame, df_grain: pd.DataFrame | None):
    """
    使用 data_q 各省户内消费量、预测的户外消费系数、粮食结构，计算各省户内与户内外消费量。
    """
    df = df_pred.merge(df_pop, on=["Province", "Year"], how="left")
    df["pop"] = df["pop"].fillna(0)
    df = df.merge(df_q[["Province", "Year"] + [c for c in DATA_Q_INDOOR_COLS if c in df_q.columns]], on=["Province", "Year"], how="left")
    if df_grain is not None:
        df = df.merge(df_grain[["Province", "Year"] + GRAIN_SHARE_COLS], on=["Province", "Year"], how="left")
    for c in GRAIN_SHARE_COLS:
        if c not in df.columns:
            df[c] = 0.25

    pop = df["pop"]
    # 粮食四类：户内人均 = q_liangshi * 占比，户内外 = 户内人均 * 系数 * pop
    if "q_liangshi" in df.columns:
        q_liang = df["q_liangshi"].fillna(0)
        for coef_col, share_col in zip(GRAIN_COEF_COLS, GRAIN_SHARE_COLS):
            if coef_col not in df_pred.columns or share_col not in df.columns:
                continue
            share = df[share_col].fillna(0.25)
            coef = df[coef_col].fillna(1.0)
            cat = coef_col.replace("q_", "")
            df[f"户内消费量_{cat}"] = (q_liang * share) * pop
            df[f"户内外消费量_{cat}"] = (q_liang * share * coef) * pop

    # 非粮食：户内人均来自 data_q 的 q_*，户内外 = 户内人均 * 系数 * pop
    for q_col in COEF_COLS_NON_GRAIN:
        if q_col not in df_pred.columns or q_col not in df.columns:
            continue
        indoor_pc = df[q_col].fillna(0)
        coef = df[q_col].fillna(1.0)  # 预测表 merge 后系数列与 data_q 的 q_col 会冲突，这里用预测表的
        # 合并后来自预测表的系数：列名仍是 q_*（来自 df_pred）
        coef = df_pred[["Province", "Year", q_col]].merge(df[["Province", "Year"]], on=["Province", "Year"], how="right")[q_col].fillna(1.0).values
        if len(coef) != len(df):
            coef = df[q_col].fillna(1.0).values  # 若长度不对则用 merge 后的列（可能来自 data_q，错误则用 1）
        cat = q_col.replace("q_", "")
        df[f"户内消费量_{cat}"] = indoor_pc * pop.values
        df[f"户内外消费量_{cat}"] = (indoor_pc * coef) * pop.values

    return df


def add_province_consumption_clear(df_pred: pd.DataFrame, df_q: pd.DataFrame, df_pop: pd.DataFrame, df_grain: pd.DataFrame | None):
    """
    清晰逻辑：预测表只有 (Province, Year, q_daogu, q_xiaomai, ...) 为户外消费系数；
    data_q 只有 (Province, Year, q_liangshi, q_shiyongyou, ...) 为户内人均消费量。
    先 merge 再按列名区分计算。
    """
    # 预测表列名保持为系数
    coef_cols = [c for c in GRAIN_COEF_COLS + COEF_COLS_NON_GRAIN if c in df_pred.columns]
    df = df_pred[["Province", "Year"] + coef_cols].copy()
    df = df.rename(columns={c: c + "_coef" for c in coef_cols})
    df = df.merge(df_pop, on=["Province", "Year"], how="left")
    df["pop"] = df["pop"].fillna(0)
    q_cols_use = [c for c in DATA_Q_INDOOR_COLS if c in df_q.columns]
    if "q_niuyangrou" not in q_cols_use and "q_niurou" in df_q.columns and "q_yangrou" in df_q.columns:
        q_cols_use = q_cols_use + ["q_niurou", "q_yangrou"]
    df = df.merge(df_q[["Province", "Year"] + [c for c in q_cols_use if c in df_q.columns]], on=["Province", "Year"], how="left")
    if "q_niuyangrou" not in df.columns and "q_niurou" in df.columns and "q_yangrou" in df.columns:
        niu = df["q_niurou"]
        yang = df["q_yangrou"]
        if isinstance(niu, pd.DataFrame):
            niu = niu.iloc[:, 0]
        if isinstance(yang, pd.DataFrame):
            yang = yang.iloc[:, 0]
        df["q_niuyangrou"] = niu.fillna(0) + yang.fillna(0)
    if df_grain is not None:
        df = df.merge(df_grain[["Province", "Year"] + GRAIN_SHARE_COLS], on=["Province", "Year"], how="left")
    for c in GRAIN_SHARE_COLS:
        if c not in df.columns:
            df[c] = 0.25

    # 输出省人均消费量（不乘 pop）：户内人均 = data_q 对应值×占比，户内外人均 = 户内人均 × 户外消费系数
    # 粮食（保证 1D，避免重名列导致 shape (n,2)）
    if "q_liangshi" in df.columns:
        q_liang_raw = df["q_liangshi"]
        if isinstance(q_liang_raw, pd.DataFrame):
            q_liang_raw = q_liang_raw.iloc[:, 0]
        q_liang = np.asarray(q_liang_raw.fillna(0)).ravel()
        for coef_col, share_col in zip(GRAIN_COEF_COLS, GRAIN_SHARE_COLS):
            ckey = coef_col + "_coef"
            if ckey not in df.columns or share_col not in df.columns:
                continue
            share_raw = df[share_col]
            if isinstance(share_raw, pd.DataFrame):
                share_raw = share_raw.iloc[:, 0]
            share = np.asarray(share_raw.fillna(0.25)).ravel()
            coef_raw = df[ckey]
            if isinstance(coef_raw, pd.DataFrame):
                coef_raw = coef_raw.iloc[:, 0]
            coef = np.asarray(coef_raw.fillna(1.0)).ravel()
            cat = coef_col.replace("q_", "")
            indoor_pc = q_liang * share  # 省户内人均消费量
            df[f"户内消费量_{cat}"] = indoor_pc
            df[f"户内外消费量_{cat}"] = indoor_pc * coef  # 户内外人均 = 户内人均 × 户外消费系数

    # 非粮食（原始数据为 total_牛肉/home_牛肉、total_羊肉/home_羊肉，合并后预测为 q_niurou、q_yangrou；若 merge 产生重名列则取单列并保证 1D）
    for q_col in COEF_COLS_NON_GRAIN:
        ckey = q_col + "_coef"
        if ckey not in df.columns or q_col not in df.columns:
            continue
        col_q = df[q_col]
        if isinstance(col_q, pd.DataFrame):
            col_q = col_q.iloc[:, 0]
        indoor_pc = np.asarray(col_q.fillna(0)).ravel()
        coef_raw = df[ckey]
        if isinstance(coef_raw, pd.DataFrame):
            coef_raw = coef_raw.iloc[:, 0]
        coef = np.asarray(coef_raw.fillna(1.0)).ravel()
        cat = q_col.replace("q_", "")
        df[f"户内消费量_{cat}"] = indoor_pc  # 省户内人均消费量
        df[f"户内外消费量_{cat}"] = indoor_pc * coef  # 户内外人均 = 户内人均 × 户外消费系数

    return df


def build_national(df_province: pd.DataFrame, df_pop: pd.DataFrame):
    """按人口加权全国户外消费系数；省表为人均消费量，全国为人均的人口加权平均。"""
    df = df_province.merge(df_pop, on=["Province", "Year"], how="inner", suffixes=("_x", "_y"))
    for c in ["pop", "pop_x", "pop_y"]:
        if c in df.columns:
            df["pop"] = df[c]
            break
    if "pop" not in df.columns:
        return None
    df = df[(df["pop"] > 0) & df["pop"].notna()]
    if df.empty:
        return None

    years = sorted(df["Year"].unique())
    rows = []
    for year in years:
        sub = df[df["Year"] == year]
        total_pop = sub["pop"].sum()
        if total_pop <= 0:
            continue
        row = {"Year": year, "total_population": total_pop}
        for c in list(df_province.columns):
            if c.endswith("_coef"):
                q_col = c.replace("_coef", "")
                if c not in sub.columns:
                    continue
                valid = sub[sub[c].notna() & (sub[c] > 0)]
                if len(valid) > 0 and valid["pop"].sum() > 0:
                    row[f"全国户外消费系数_{q_col.replace('q_', '')}"] = (valid[c] * valid["pop"]).sum() / valid["pop"].sum()
        for col in list(df_province.columns):
            if col.startswith("户内外消费量_") or col.startswith("户内消费量_"):
                if col in sub.columns:
                    row[col] = (sub[col] * sub["pop"]).sum() / total_pop  # 全国人均 = 各省人均按人口加权
                else:
                    row[col] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def run(
    predictions_path: str,
    grain_structure_path: str | None = None,
    output_province_path: str | None = None,
    output_national_path: str | None = None,
):
    model_name = _model_name_from_predictions_path(predictions_path)
    if not model_name:
        model_name = "fttransformer_advanced"
    grain_path = grain_structure_path or _grain_structure_path(model_name)
    # 各模型输出到独立文件：results_province_<model>.csv、results_national_<model>.csv
    out_prov = output_province_path or os.path.join(BASE_DIR, f"results_province_{model_name}.csv")
    out_nat = output_national_path or os.path.join(BASE_DIR, f"results_national_{model_name}.csv")

    df_pred = pd.read_csv(predictions_path)
    if "Year" not in df_pred.columns and "wave" in df_pred.columns:
        df_pred = df_pred.rename(columns={"wave": "Year"})

    df_pop = load_population()
    df_q = load_data_q()
    if df_q is None:
        print("未找到 data_q.csv，无法使用各省户内消费量")
        return None, None

    df_grain = load_grain_structure(grain_path)
    if df_grain is None:
        for c in GRAIN_SHARE_COLS:
            df_pred[c] = 0.25

    df_province = add_province_consumption_clear(df_pred, df_q, df_pop, df_grain)
    df_province.to_csv(out_prov, index=False)
    print(f"省级结果已写入: {out_prov}")

    df_national = build_national(df_province, df_pop)
    if df_national is not None and not df_national.empty:
        df_national.to_csv(out_nat, index=False)
        print(f"全国结果已写入: {out_nat}")
    else:
        print("未生成全国结果")

    return df_province, df_national


def main():
    parser = argparse.ArgumentParser(description="对预测结果做后处理：用 data_q 各省户内消费量+预测系数+粮食结构，计算省/全国户内外消费量")
    parser.add_argument("--predictions", "-p", default=None, help="预测结果 CSV 路径")
    parser.add_argument("--grain", "-g", default=None, help="粮食结构 CSV 路径")
    parser.add_argument("--output-province", "-o", default=None, help="省级结果输出路径")
    parser.add_argument("--output-national", default=None, help="全国结果输出路径")
    parser.add_argument("--all-models", action="store_true", help="对当前目录下所有 predictions_*.csv 执行后处理")
    args = parser.parse_args()

    if args.all_models:
        for path in sorted(glob.glob(os.path.join(BASE_DIR, "predictions_*.csv"))):
            print(f"\n处理: {path}")
            run(
                path,
                output_province_path=args.output_province,
                output_national_path=args.output_national,
            )
        return

    predictions_path = args.predictions or os.path.join(BASE_DIR, "predictions_fttransformer_advanced.csv")
    if not os.path.isfile(predictions_path):
        first = next(iter(glob.glob(os.path.join(BASE_DIR, "predictions_*.csv"))), None)
        predictions_path = first or predictions_path
    if not os.path.isfile(predictions_path):
        print(f"未找到文件: {predictions_path}")
        return
    run(
        predictions_path,
        grain_structure_path=args.grain,
        output_province_path=args.output_province,
        output_national_path=args.output_national,
    )


if __name__ == "__main__":
    main()
