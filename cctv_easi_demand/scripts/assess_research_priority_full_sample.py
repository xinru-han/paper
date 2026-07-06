#!/usr/bin/env python3
"""
Assess which empirical study should be prioritized using the full enriched sample.

The script scans the full transaction-level CSV in chunks and writes compact
diagnostic tables plus a Markdown recommendation report.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "processed" / "Data_merged_enriched_citytier.csv"
OUT_DIR = ROOT / "processed"


USECOLS = [
    "ID",
    "Province",
    "Family_Type",
    "Family_Size",
    "Family_Income",
    "Category",
    "Spend",
    "Volume",
    "Price",
    "date_clean",
    "year",
    "year_month",
    "holiday_flag",
    "category_group",
    "is_fresh",
    "is_storable",
    "is_processed",
    "is_animal_protein",
    "is_staple",
    "is_dairy",
    "is_premium_proxy",
    "income_band_clean",
    "region",
    "coastal_dummy",
    "north_south",
    "cpi_yoy_prev_year_100",
    "covid_cum_confirmed",
    "covid_daily_new",
    "temp_avg_c",
    "precipitation_mm",
    "wholesale_agri_200",
    "wholesale_basket_200",
    "wholesale_grain_oil_200",
    "category_wholesale_index",
    "carbon_kgco2e_per_kg_or_l",
    "water_l_per_kg_or_l",
    "estimated_carbon_kgco2e",
    "estimated_water_l",
    "CityTier",
    "city_tier_label",
    "city_tier_a_flag",
]


def safe_numeric(df: pd.DataFrame, cols: list[str]) -> None:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")


def add_sum(counter: defaultdict[tuple, dict[str, float]], key: tuple, **values: float) -> None:
    target = counter[key]
    for k, v in values.items():
        if pd.notna(v):
            target[k] += float(v)


def group_sum(df: pd.DataFrame, keys: list[str], metrics: list[str]) -> pd.DataFrame:
    return df.groupby(keys, dropna=False)[metrics].sum(min_count=1).reset_index()


def temp_bin(s: pd.Series) -> pd.Series:
    return pd.cut(
        s,
        bins=[-100, 0, 10, 20, 30, 100],
        labels=["<=0C", "0-10C", "10-20C", "20-30C", ">30C"],
        include_lowest=True,
    ).astype("string").fillna("missing")


def precip_bin(s: pd.Series) -> pd.Series:
    return pd.cut(
        s,
        bins=[-0.00001, 0, 1, 10, 50, 10_000],
        labels=["0", "0-1", "1-10", "10-50", ">50"],
        include_lowest=True,
    ).astype("string").fillna("missing")


def concat_group(parts: list[pd.DataFrame], keys: list[str], metrics: list[str]) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame(columns=keys + metrics)
    df = pd.concat(parts, ignore_index=True)
    return df.groupby(keys, dropna=False)[metrics].sum(min_count=1).reset_index()


def add_share(df: pd.DataFrame, group_keys: list[str], value_col: str = "Spend") -> pd.DataFrame:
    total = df.groupby(group_keys, dropna=False)[value_col].transform("sum")
    df[f"{value_col}_share"] = df[value_col] / total
    return df


def fmt_pct(x: float) -> str:
    return f"{x:.2%}"


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    chunksize = 500_000
    numeric_cols = [
        "Spend",
        "Volume",
        "Price",
        "holiday_flag",
        "is_fresh",
        "is_storable",
        "is_processed",
        "is_animal_protein",
        "is_staple",
        "is_dairy",
        "is_premium_proxy",
        "cpi_yoy_prev_year_100",
        "covid_cum_confirmed",
        "covid_daily_new",
        "temp_avg_c",
        "precipitation_mm",
        "wholesale_agri_200",
        "wholesale_basket_200",
        "wholesale_grain_oil_200",
        "category_wholesale_index",
        "carbon_kgco2e_per_kg_or_l",
        "water_l_per_kg_or_l",
        "estimated_carbon_kgco2e",
        "estimated_water_l",
    ]
    base_metrics = ["rows", "Spend", "Volume", "estimated_carbon_kgco2e", "estimated_water_l"]

    row_count = 0
    unique_ids: set[str] = set()
    coverage_counts = Counter()
    price_valid_rows = 0
    volume_positive_rows = 0
    volume_zero_rows = 0
    spend_positive_rows = 0

    citytier_parts = []
    category_parts = []
    citytier_category_parts = []
    income_category_parts = []
    family_category_parts = []
    year_month_parts = []
    weather_category_parts = []
    weather_group_parts = []
    citytier_year_parts = []

    for i, chunk in enumerate(
        pd.read_csv(INPUT, usecols=USECOLS, chunksize=chunksize, encoding="utf-8-sig", low_memory=False),
        start=1,
    ):
        safe_numeric(chunk, numeric_cols)
        chunk["rows"] = 1
        chunk["ID"] = chunk["ID"].astype("string")
        unique_ids.update(chunk["ID"].dropna().astype(str).unique())
        row_count += len(chunk)

        chunk["spend_fresh"] = chunk["Spend"].fillna(0) * chunk["is_fresh"].fillna(0)
        chunk["spend_storable"] = chunk["Spend"].fillna(0) * chunk["is_storable"].fillna(0)
        chunk["spend_processed"] = chunk["Spend"].fillna(0) * chunk["is_processed"].fillna(0)
        chunk["spend_animal_protein"] = chunk["Spend"].fillna(0) * chunk["is_animal_protein"].fillna(0)
        chunk["spend_staple"] = chunk["Spend"].fillna(0) * chunk["is_staple"].fillna(0)
        chunk["spend_dairy"] = chunk["Spend"].fillna(0) * chunk["is_dairy"].fillna(0)
        chunk["spend_premium"] = chunk["Spend"].fillna(0) * chunk["is_premium_proxy"].fillna(0)

        price_valid_rows += int(chunk["Price"].notna().sum())
        volume_positive_rows += int((chunk["Volume"].fillna(0) > 0).sum())
        volume_zero_rows += int((chunk["Volume"].fillna(0) == 0).sum())
        spend_positive_rows += int((chunk["Spend"].fillna(0) > 0).sum())

        for col in [
            "CityTier",
            "temp_avg_c",
            "precipitation_mm",
            "category_wholesale_index",
            "estimated_carbon_kgco2e",
            "estimated_water_l",
            "cpi_yoy_prev_year_100",
            "covid_cum_confirmed",
        ]:
            coverage_counts[col] += int(chunk[col].notna().sum())

        metrics = base_metrics + [
            "spend_fresh",
            "spend_storable",
            "spend_processed",
            "spend_animal_protein",
            "spend_staple",
            "spend_dairy",
            "spend_premium",
        ]
        citytier_parts.append(group_sum(chunk, ["CityTier", "city_tier_label"], metrics))
        category_parts.append(group_sum(chunk, ["Category", "category_group"], metrics + ["Price"]))
        citytier_category_parts.append(group_sum(chunk, ["CityTier", "city_tier_label", "Category"], metrics))
        income_category_parts.append(group_sum(chunk, ["income_band_clean", "Category"], metrics))
        family_category_parts.append(group_sum(chunk, ["Family_Type", "Category"], metrics))
        year_month_parts.append(group_sum(chunk, ["year_month"], metrics))
        citytier_year_parts.append(group_sum(chunk, ["CityTier", "year"], metrics))

        chunk["temp_bin"] = temp_bin(chunk["temp_avg_c"])
        chunk["precip_bin"] = precip_bin(chunk["precipitation_mm"])
        weather_category_parts.append(group_sum(chunk, ["temp_bin", "Category"], metrics))
        weather_group_parts.append(group_sum(chunk, ["temp_bin", "precip_bin", "category_group"], metrics))

        print(f"Scanned chunk {i}; rows {row_count:,}", flush=True)

    metrics = base_metrics + [
        "spend_fresh",
        "spend_storable",
        "spend_processed",
        "spend_animal_protein",
        "spend_staple",
        "spend_dairy",
        "spend_premium",
    ]
    citytier = concat_group(citytier_parts, ["CityTier", "city_tier_label"], metrics)
    category = concat_group(category_parts, ["Category", "category_group"], metrics + ["Price"])
    citytier_category = concat_group(citytier_category_parts, ["CityTier", "city_tier_label", "Category"], metrics)
    income_category = concat_group(income_category_parts, ["income_band_clean", "Category"], metrics)
    family_category = concat_group(family_category_parts, ["Family_Type", "Category"], metrics)
    year_month = concat_group(year_month_parts, ["year_month"], metrics)
    citytier_year = concat_group(citytier_year_parts, ["CityTier", "year"], metrics)
    weather_category = concat_group(weather_category_parts, ["temp_bin", "Category"], metrics)
    weather_group = concat_group(weather_group_parts, ["temp_bin", "precip_bin", "category_group"], metrics)

    for df, keys in [
        (category, []),
        (citytier_category, ["CityTier"]),
        (income_category, ["income_band_clean"]),
        (family_category, ["Family_Type"]),
        (weather_category, ["temp_bin"]),
        (weather_group, ["temp_bin", "precip_bin"]),
    ]:
        add_share(df, keys, "Spend")

    for df in [citytier, category, citytier_category, income_category, family_category, year_month, citytier_year]:
        for col in [
            "spend_fresh",
            "spend_storable",
            "spend_processed",
            "spend_animal_protein",
            "spend_staple",
            "spend_dairy",
            "spend_premium",
        ]:
            df[f"{col}_share"] = df[col] / df["Spend"]
        df["carbon_per_yuan"] = df["estimated_carbon_kgco2e"] / df["Spend"]
        df["water_per_yuan"] = df["estimated_water_l"] / df["Spend"]

    category["price_row_mean_proxy"] = category["Price"] / category["rows"]

    paths = {
        "citytier": OUT_DIR / "full_sample_priority_citytier_summary.csv",
        "category": OUT_DIR / "full_sample_priority_category_summary.csv",
        "citytier_category": OUT_DIR / "full_sample_priority_citytier_category_share.csv",
        "income_category": OUT_DIR / "full_sample_priority_income_category_share.csv",
        "family_category": OUT_DIR / "full_sample_priority_family_category_share.csv",
        "year_month": OUT_DIR / "full_sample_priority_year_month_summary.csv",
        "citytier_year": OUT_DIR / "full_sample_priority_citytier_year_summary.csv",
        "weather_category": OUT_DIR / "full_sample_priority_weather_temp_category_share.csv",
        "weather_group": OUT_DIR / "full_sample_priority_weather_group_share.csv",
    }
    citytier.to_csv(paths["citytier"], index=False, encoding="utf-8-sig")
    category.to_csv(paths["category"], index=False, encoding="utf-8-sig")
    citytier_category.to_csv(paths["citytier_category"], index=False, encoding="utf-8-sig")
    income_category.to_csv(paths["income_category"], index=False, encoding="utf-8-sig")
    family_category.to_csv(paths["family_category"], index=False, encoding="utf-8-sig")
    year_month.to_csv(paths["year_month"], index=False, encoding="utf-8-sig")
    citytier_year.to_csv(paths["citytier_year"], index=False, encoding="utf-8-sig")
    weather_category.to_csv(paths["weather_category"], index=False, encoding="utf-8-sig")
    weather_group.to_csv(paths["weather_group"], index=False, encoding="utf-8-sig")

    # Pull a few high-signal diagnostics for the Markdown report.
    citytier_display = citytier.sort_values("CityTier")[[
        "CityTier",
        "city_tier_label",
        "rows",
        "Spend",
        "spend_fresh_share",
        "spend_animal_protein_share",
        "spend_dairy_share",
        "spend_processed_share",
        "spend_storable_share",
        "carbon_per_yuan",
        "water_per_yuan",
    ]]
    top_categories = category.sort_values("Spend", ascending=False).head(10)[
        ["Category", "category_group", "Spend", "Spend_share", "rows", "Volume"]
    ]
    temp_spend = weather_category.groupby("temp_bin", dropna=False)["Spend"].sum().reset_index()
    temp_spend["Spend_share"] = temp_spend["Spend"] / temp_spend["Spend"].sum()
    temp_spend = temp_spend.sort_values("temp_bin")

    coverage_lines = []
    for col in [
        "CityTier",
        "temp_avg_c",
        "precipitation_mm",
        "estimated_carbon_kgco2e",
        "estimated_water_l",
        "cpi_yoy_prev_year_100",
        "covid_cum_confirmed",
        "category_wholesale_index",
    ]:
        coverage_lines.append(f"- `{col}`：{coverage_counts[col]:,} 行，覆盖率 {fmt_pct(coverage_counts[col] / row_count)}")

    report_path = OUT_DIR / "full_sample_research_priority_report.md"
    report = f"""# 全样本实证研究优先级诊断

生成时间：{dt.datetime.now().isoformat(sep=" ", timespec="seconds")}

## 数据基础

- 使用数据：`processed/Data_merged_enriched_citytier.csv`
- 行数：{row_count:,}
- 唯一家庭 ID：{len(unique_ids):,}
- 时间：2020-2022
- 城市级别：全样本已匹配，`CityTier` 覆盖率 {fmt_pct(coverage_counts["CityTier"] / row_count)}

## 关键变量覆盖

{chr(10).join(coverage_lines)}

交易量/价格口径：

- `Spend > 0` 行：{spend_positive_rows:,}，占 {fmt_pct(spend_positive_rows / row_count)}
- `Volume > 0` 行：{volume_positive_rows:,}，占 {fmt_pct(volume_positive_rows / row_count)}
- `Volume == 0/缺失按0计` 行：{volume_zero_rows:,}，占 {fmt_pct(volume_zero_rows / row_count)}
- 原始 `Price` 非空行：{price_valid_rows:,}，占 {fmt_pct(price_valid_rows / row_count)}

## 城市级别消费结构差异

{citytier_display.to_markdown(index=False)}

## 全样本支出最高的品类

{top_categories.to_markdown(index=False)}

## 天气温度分组下的样本支出覆盖

{temp_spend.to_markdown(index=False)}

## 结论：建议先做的实证研究

**第一优先：城市层级、收入分层与家庭食品消费升级/健康低碳结构。**

理由：

1. `CityTier` 在全样本中 100% 覆盖，且 A/B/C/D/E 均有样本；这使得全样本不再只能停留在省级异质性，可以直接讨论城市层级梯度。
2. 品类、城市层级、收入、家庭类型、时间变量都来自主数据或确定性匹配，数据风险最低；不依赖外部政策强度或难以验证的历史预警数据。
3. 碳足迹和水足迹系数已覆盖 100%，可作为“购买结构对应的环境足迹代理”；但由于 `Volume == 0` 行较多，建议主结果先用**金额份额/结构**，碳水足迹作为扩展结果。
4. 省级气温和降水覆盖率高，适合放到第二篇或稳健性/机制扩展；但如果一开始就做天气冲击，识别粒度仍是省级天气，不如城市层级主线稳。
5. 内部价格弹性不建议作为第一篇：`Price` 非空和 `Volume > 0` 受量纲/零值影响，且单位价值混合了品质、规格和促销，解释风险更高。

## 建议第一篇的题目雏形

**城市层级与家庭食品消费升级：来自 2020-2022 年中国家庭食品购买面板的证据**

可扩展副标题：**消费结构、健康化与低碳代理指标**

## 推荐基准模型

以家庭-月-品类或家庭-月为主：

- 结果变量：品类支出份额、升级食品份额、基础食品份额、动物蛋白份额、乳制品份额、新鲜食品份额、加工食品份额、碳/水足迹代理。
- 核心解释变量：`CityTier`、收入档、家庭类型、家庭规模，以及 `CityTier × income_band_clean`。
- 控制：家庭固定效应无法识别不随时间变的 `CityTier` 主效应，因此建议两套模型并行：
  - 截面/ pooled：`y_ihmt = CityTier_i + income_i + family_i + province + year_month + category + controls`
  - 家庭固定效应：重点估时间变化变量、节假日/天气冲击及其与 `CityTier` 的异质性：`y_ihmt = shock_t/p/t × CityTier_i + household FE + year_month/category FE`
- 标准误：按家庭 ID 或省份聚类，视聚合层级而定。

## 第二顺位

**天气冲击与家庭食品消费结构调整**。理由是气温/降水覆盖率高，且可以利用 2020-2022 日度波动；但当前是省级天气，建议等你把直辖市/省会城市的城市级气象数据匹配到 A 类子集后，再做更细粒度版本。

## 暂不建议第一篇做

- 价格弹性：单位价值偏误和 `Volume` 零值问题较强。
- 真实营养摄入：尚未检测到营养系数文件，且购买不等于摄入。
- 疫情强因果：COVID 已匹配，但政策强度/封控强度仍不完整，先做容易被识别质疑。

## 输出诊断表

- `processed/full_sample_priority_citytier_summary.csv`
- `processed/full_sample_priority_category_summary.csv`
- `processed/full_sample_priority_citytier_category_share.csv`
- `processed/full_sample_priority_income_category_share.csv`
- `processed/full_sample_priority_family_category_share.csv`
- `processed/full_sample_priority_year_month_summary.csv`
- `processed/full_sample_priority_citytier_year_summary.csv`
- `processed/full_sample_priority_weather_temp_category_share.csv`
- `processed/full_sample_priority_weather_group_share.csv`
"""
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote {report_path}")
    for p in paths.values():
        print(f"Wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
