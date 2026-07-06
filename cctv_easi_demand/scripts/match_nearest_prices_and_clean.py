#!/usr/bin/env python3
"""Match nearest monitoring-date external food prices and clean outliers.

Inputs:
- processed/external_food_prices_mapped_observations_2020_2022.csv
- Data_merged.csv

Outputs:
- cleaned province-monitor-date category/group price tables
- transaction-level consumption parquet with nearest external price and
  outlier flags / winsorized variables
- cleaning reports and threshold tables
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from build_external_food_prices import GROUP10, norm_province


BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "processed"
OUT.mkdir(exist_ok=True)

DATE_MIN = pd.Timestamp("2020-01-01")
DATE_MAX = pd.Timestamp("2022-12-31")

PRICE_MAPPED = OUT / "external_food_prices_mapped_observations_2020_2022.csv"
CONSUMPTION = BASE / "Data_merged.csv"

Q_LOW = 0.005
Q_HIGH = 0.995
VOLUME_OUTLIER_Q_HIGH = 0.999
VOLUME_OUTLIER_Q_HIGH_LABEL = "p999"

FAMILY_SIZE_MIDPOINT = {
    "家庭人口数1-2": 1.5,
    "家庭人口数3": 3.0,
    "家庭人口数4": 4.0,
    "家庭人口数5+": 5.5,
}


PROXY_MAP = {
    "坚果": ["食用油"],
    "挂面": ["面粉"],
    "常温酸奶": ["新鲜牛奶", "常温牛奶"],
    "新鲜酸奶": ["新鲜牛奶", "常温牛奶"],
    "奶酪": ["新鲜牛奶", "常温牛奶"],
    "黄油": ["新鲜牛奶", "常温牛奶", "食用油"],
}


def finite_quantile(values: pd.Series, q: float) -> float:
    vals = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if vals.empty:
        return np.nan
    return float(vals.quantile(q))


def load_consumption_scope() -> tuple[list[str], list[str], list[str]]:
    provinces: set[str] = set()
    categories: set[str] = set()
    months: set[str] = set()
    for chunk in pd.read_csv(
        CONSUMPTION,
        usecols=["Province", "Category", "Date"],
        dtype=str,
        chunksize=500_000,
        encoding="utf-8-sig",
    ):
        provinces.update(norm_province(x) for x in chunk["Province"].dropna().unique())
        categories.update(str(x).strip() for x in chunk["Category"].dropna().unique())
        dt = pd.to_datetime(chunk["Date"], errors="coerce", format="mixed")
        m = (dt >= DATE_MIN) & (dt <= DATE_MAX)
        months.update(dt[m].dt.strftime("%Y-%m").dropna().unique())
    return sorted(x for x in provinces if x), sorted(x for x in categories if x), sorted(months)


def clean_price_observations() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cols = ["province", "date", "year_month", "Category", "retail_price", "unit", "variety_raw", "spec", "match_level_observed"]
    df = pd.read_csv(PRICE_MAPPED, usecols=cols, encoding="utf-8-sig")
    df["_row_id"] = np.arange(len(df))
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["retail_price"] = pd.to_numeric(df["retail_price"], errors="coerce")
    df["unit"] = df["unit"].fillna("")
    df["price_invalid_flag"] = (
        df["date"].isna() | df["province"].isna() | df["Category"].isna() | df["retail_price"].isna() | (df["retail_price"] <= 0)
    ).astype("int8")
    valid = df[df["price_invalid_flag"].eq(0)].copy()
    valid["log_price"] = np.log(valid["retail_price"])

    thresholds = (
        valid.groupby(["Category", "unit"], as_index=False)
        .agg(
            n_obs=("log_price", "size"),
            log_price_p005=("log_price", lambda x: finite_quantile(x, Q_LOW)),
            log_price_p995=("log_price", lambda x: finite_quantile(x, Q_HIGH)),
            price_p005=("retail_price", lambda x: finite_quantile(x, Q_LOW)),
            price_p995=("retail_price", lambda x: finite_quantile(x, Q_HIGH)),
            price_median=("retail_price", "median"),
        )
        .sort_values(["Category", "unit"])
    )
    valid = valid.merge(thresholds[["Category", "unit", "log_price_p005", "log_price_p995"]], on=["Category", "unit"], how="left")
    valid["price_outlier_flag"] = (
        (valid["log_price"] < valid["log_price_p005"]) | (valid["log_price"] > valid["log_price_p995"])
    ).astype("int8")
    df["price_outlier_flag"] = np.int8(0)
    df.loc[valid["_row_id"].to_numpy(), "price_outlier_flag"] = valid["price_outlier_flag"].to_numpy(dtype=np.int8)
    df["price_clean_keep_flag"] = ((df["price_invalid_flag"] == 0) & (df["price_outlier_flag"] == 0)).astype("int8")

    report = (
        df.groupby(["Category", "unit"], as_index=False)
        .agg(
            n_raw=("retail_price", "size"),
            n_invalid=("price_invalid_flag", "sum"),
            n_outlier=("price_outlier_flag", "sum"),
            n_clean=("price_clean_keep_flag", "sum"),
            price_min=("retail_price", "min"),
            price_median=("retail_price", "median"),
            price_max=("retail_price", "max"),
        )
        .merge(thresholds, on=["Category", "unit"], how="left", suffixes=("", "_threshold"))
        .sort_values(["Category", "unit"])
    )
    return df, df[df["price_clean_keep_flag"].eq(1)].copy(), report


def build_monitor_date_prices(
    clean_price_obs: pd.DataFrame,
    main_provinces: list[str],
    main_categories: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    observed = (
        clean_price_obs.groupby(["province", "date", "Category"], as_index=False)
        .agg(
            external_price_mean_monitor=("retail_price", "mean"),
            external_price_median_monitor=("retail_price", "median"),
            n_price_obs_clean=("retail_price", "count"),
            n_varieties=("variety_raw", "nunique"),
            source_varieties=("variety_raw", lambda x: ";".join(sorted(set(map(str, x)))[:30])),
            units=("unit", lambda x: ";".join(sorted(set(map(str, x)))[:10])),
            observed_match_levels=("match_level_observed", lambda x: ";".join(sorted(set(map(str, x))))),
        )
        .sort_values(["province", "date", "Category"])
    )
    price_dates = sorted(observed["date"].dropna().unique())
    grid = pd.MultiIndex.from_product(
        [main_provinces, price_dates, main_categories],
        names=["province", "date", "Category"],
    ).to_frame(index=False)
    full = grid.merge(observed, on=["province", "date", "Category"], how="left")
    full["price_fill_level"] = np.where(full["external_price_mean_monitor"].notna(), "observed_province_monitor_date", "")
    full["proxy_source_category"] = ""

    lookup = full.set_index(["province", "date", "Category"])["external_price_mean_monitor"].to_dict()
    for idx, row in full[full["external_price_mean_monitor"].isna()].iterrows():
        candidates = PROXY_MAP.get(row["Category"], [])
        vals = []
        src = []
        for cat in candidates:
            val = lookup.get((row["province"], row["date"], cat))
            if val is not None and not (isinstance(val, float) and math.isnan(val)):
                vals.append(float(val))
                src.append(cat)
        if vals:
            full.at[idx, "external_price_mean_monitor"] = float(np.mean(vals))
            full.at[idx, "external_price_median_monitor"] = float(np.median(vals))
            full.at[idx, "n_price_obs_clean"] = 0
            full.at[idx, "price_fill_level"] = "province_monitor_date_proxy_category"
            full.at[idx, "proxy_source_category"] = ";".join(src)

    full["date"] = pd.to_datetime(full["date"])
    full["year_month"] = full["date"].dt.strftime("%Y-%m")
    full["external_log_price_monitor"] = np.log(full["external_price_mean_monitor"].where(full["external_price_mean_monitor"] > 0))
    full["food_group10"] = full["Category"].map(GROUP10)
    cat_mean_log = full.groupby("Category")["external_log_price_monitor"].transform("mean")
    full["external_log_price_centered_category_monitor"] = full["external_log_price_monitor"] - cat_mean_log
    full["external_price_index_category_monitor_mean100"] = np.exp(full["external_log_price_centered_category_monitor"]) * 100

    group = (
        full.dropna(subset=["food_group10", "external_log_price_centered_category_monitor"])
        .groupby(["province", "date", "food_group10"], as_index=False)
        .agg(
            external_log_price_group10_monitor=("external_log_price_centered_category_monitor", "mean"),
            n_categories_in_group=("Category", "nunique"),
            categories=("Category", lambda x: ";".join(sorted(set(map(str, x))))),
            fill_levels=("price_fill_level", lambda x: ";".join(sorted(set(map(str, x))))),
        )
        .sort_values(["province", "date", "food_group10"])
    )
    group["year_month"] = pd.to_datetime(group["date"]).dt.strftime("%Y-%m")
    group["external_price_index_group10_monitor_mean100"] = np.exp(group["external_log_price_group10_monitor"]) * 100
    return full, group


def build_price_lookup(price_by_date: pd.DataFrame) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    cols = [
        "external_price_mean_monitor",
        "external_price_median_monitor",
        "external_log_price_monitor",
        "external_price_index_category_monitor_mean100",
        "price_fill_level",
        "proxy_source_category",
        "n_price_obs_clean",
    ]
    for (prov, cat), sub in price_by_date.sort_values("date").groupby(["province", "Category"]):
        dates = pd.to_datetime(sub["date"]).to_numpy(dtype="datetime64[D]")
        lookup[(prov, cat)] = {"dates": dates, **{c: sub[c].to_numpy() for c in cols}}
    return lookup


def collect_household_year_category_outliers() -> tuple[pd.DataFrame, pd.DataFrame]:
    partials: list[pd.DataFrame] = []
    family_partials: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        CONSUMPTION,
        usecols=["ID", "Family_Size", "Date", "Category", "Spend", "Volume"],
        dtype={"ID": "string", "Family_Size": "string", "Category": "string"},
        chunksize=500_000,
        encoding="utf-8-sig",
    ):
        dt = pd.to_datetime(chunk["Date"], errors="coerce", format="mixed")
        spend = pd.to_numeric(chunk["Spend"], errors="coerce")
        volume = pd.to_numeric(chunk["Volume"], errors="coerce")
        family_size = chunk["Family_Size"].astype("string").str.strip().map(FAMILY_SIZE_MIDPOINT)
        tmp = pd.DataFrame(
            {
                "_ID_key": chunk["ID"].astype("string").str.strip(),
                "year": dt.dt.year,
                "Category": chunk["Category"].astype("string").str.strip(),
                "annual_spend": spend.where(spend >= 0, 0).fillna(0),
                "annual_volume": volume.where(volume >= 0, 0).fillna(0),
                "transaction_count": 1,
                "family_size_midpoint": family_size,
            }
        )
        tmp = tmp[
            tmp["_ID_key"].notna()
            & tmp["_ID_key"].ne("")
            & tmp["year"].between(DATE_MIN.year, DATE_MAX.year)
            & tmp["Category"].notna()
            & tmp["Category"].ne("")
        ]
        if tmp.empty:
            continue
        tmp["year"] = tmp["year"].astype("int16")
        family_partials.append(
            tmp.dropna(subset=["family_size_midpoint"])
            .groupby(["_ID_key", "year", "family_size_midpoint"], as_index=False)
            .size()
            .rename(columns={"size": "family_size_obs"})
        )
        partials.append(
            tmp.groupby(["_ID_key", "year", "Category"], as_index=False).agg(
                household_year_category_spend=("annual_spend", "sum"),
                household_year_category_volume=("annual_volume", "sum"),
                household_year_category_transaction_count=("transaction_count", "sum"),
            )
        )

    if not partials:
        empty_thresholds = pd.DataFrame(columns=["Category"])
        empty_annual = pd.DataFrame(columns=["_ID_key", "year", "Category"])
        return empty_thresholds, empty_annual

    annual = (
        pd.concat(partials, ignore_index=True)
        .groupby(["_ID_key", "year", "Category"], as_index=False)
        .agg(
            household_year_category_spend=("household_year_category_spend", "sum"),
            household_year_category_volume=("household_year_category_volume", "sum"),
            household_year_category_transaction_count=("household_year_category_transaction_count", "sum"),
        )
    )
    annual["year"] = annual["year"].astype("int16")
    if family_partials:
        family_counts = (
            pd.concat(family_partials, ignore_index=True)
            .groupby(["_ID_key", "year", "family_size_midpoint"], as_index=False)["family_size_obs"]
            .sum()
            .sort_values(["_ID_key", "year", "family_size_obs", "family_size_midpoint"], ascending=[True, True, False, False])
        )
        family_mode = family_counts.drop_duplicates(["_ID_key", "year"], keep="first").rename(
            columns={"family_size_midpoint": "household_year_category_family_size_midpoint"}
        )
        annual = annual.merge(
            family_mode[["_ID_key", "year", "household_year_category_family_size_midpoint"]],
            on=["_ID_key", "year"],
            how="left",
        )
    else:
        annual["household_year_category_family_size_midpoint"] = np.nan
    denom = annual["household_year_category_family_size_midpoint"].where(
        annual["household_year_category_family_size_midpoint"] > 0
    )
    annual["household_year_category_spend_pc"] = annual["household_year_category_spend"] / denom
    annual["household_year_category_volume_pc"] = annual["household_year_category_volume"] / denom

    threshold_rows: list[dict[str, Any]] = []
    for cat, sub in annual.groupby("Category"):
        row: dict[str, Any] = {
            "Category": cat,
            "n_household_year_category": int(len(sub)),
            "n_positive_annual_spend_pc": int((sub["household_year_category_spend_pc"] > 0).sum()),
            "n_positive_annual_volume_pc": int((sub["household_year_category_volume_pc"] > 0).sum()),
        }
        vals = sub.loc[sub["household_year_category_volume_pc"] > 0, "household_year_category_volume_pc"]
        logs = np.log(vals.to_numpy(dtype=float)) if len(vals) else np.array([], dtype=float)
        if logs.size:
            hi = float(np.quantile(logs, VOLUME_OUTLIER_Q_HIGH))
            row[f"log_annual_volume_pc_{VOLUME_OUTLIER_Q_HIGH_LABEL}"] = hi
            row[f"annual_volume_pc_{VOLUME_OUTLIER_Q_HIGH_LABEL}"] = float(np.exp(hi))
        else:
            row[f"log_annual_volume_pc_{VOLUME_OUTLIER_Q_HIGH_LABEL}"] = np.nan
            row[f"annual_volume_pc_{VOLUME_OUTLIER_Q_HIGH_LABEL}"] = np.nan
        threshold_rows.append(row)

    thresholds = pd.DataFrame(threshold_rows).sort_values("Category")
    annual = annual.merge(thresholds, on="Category", how="left")
    annual["household_year_category_spend_outlier_flag"] = np.int8(0)
    annual["household_year_category_volume_outlier_flag"] = np.int8(0)

    volume_mask = annual["household_year_category_volume_pc"] > 0
    valid_volume_threshold = annual[f"log_annual_volume_pc_{VOLUME_OUTLIER_Q_HIGH_LABEL}"].notna()
    volume_log = pd.Series(np.nan, index=annual.index, dtype="float64")
    volume_log.loc[volume_mask] = np.log(annual.loc[volume_mask, "household_year_category_volume_pc"].to_numpy(dtype=float))
    annual.loc[
        volume_mask
        & valid_volume_threshold
        & (volume_log > annual[f"log_annual_volume_pc_{VOLUME_OUTLIER_Q_HIGH_LABEL}"]),
        "household_year_category_volume_outlier_flag",
    ] = 1
    annual["household_year_category_outlier_any_flag"] = annual["household_year_category_volume_outlier_flag"].astype("int8")

    keep_cols = [
        "_ID_key",
        "year",
        "Category",
        "household_year_category_spend",
        "household_year_category_volume",
        "household_year_category_transaction_count",
        "household_year_category_family_size_midpoint",
        "household_year_category_spend_pc",
        "household_year_category_volume_pc",
        "household_year_category_spend_outlier_flag",
        "household_year_category_volume_outlier_flag",
        "household_year_category_outlier_any_flag",
    ]
    return thresholds, annual[keep_cols]


def match_nearest_price(chunk: pd.DataFrame, lookup: dict[tuple[str, str], dict[str, Any]]) -> pd.DataFrame:
    n = len(chunk)
    out = pd.DataFrame(index=chunk.index)
    out["external_price_date"] = pd.NaT
    out["external_price_days_diff"] = np.nan
    out["external_price_abs_days_diff"] = np.nan
    out["external_price_mean_nearest"] = np.nan
    out["external_price_median_nearest"] = np.nan
    out["external_log_price_nearest"] = np.nan
    out["external_price_index_category_nearest_mean100"] = np.nan
    out["external_price_fill_level_nearest"] = ""
    out["external_price_proxy_source_category"] = ""
    out["external_price_n_obs_clean"] = np.nan

    dates = chunk["date_clean"].to_numpy(dtype="datetime64[D]")
    for (prov, cat), idx in chunk.groupby(["province_clean", "Category"], dropna=False).groups.items():
        rec = lookup.get((prov, cat))
        if rec is None:
            continue
        idx_arr = np.asarray(list(idx))
        d = dates[chunk.index.get_indexer(idx_arr)]
        price_dates = rec["dates"]
        pos = np.searchsorted(price_dates, d)
        right = np.clip(pos, 0, len(price_dates) - 1)
        left = np.clip(pos - 1, 0, len(price_dates) - 1)
        right_diff = np.abs((price_dates[right] - d).astype("timedelta64[D]").astype(int))
        left_diff = np.abs((d - price_dates[left]).astype("timedelta64[D]").astype(int))
        choose_left = left_diff <= right_diff
        chosen = np.where(choose_left, left, right)
        signed_diff = (d - price_dates[chosen]).astype("timedelta64[D]").astype(int)
        out.loc[idx_arr, "external_price_date"] = pd.to_datetime(price_dates[chosen])
        out.loc[idx_arr, "external_price_days_diff"] = signed_diff
        out.loc[idx_arr, "external_price_abs_days_diff"] = np.abs(signed_diff)
        out.loc[idx_arr, "external_price_mean_nearest"] = rec["external_price_mean_monitor"][chosen]
        out.loc[idx_arr, "external_price_median_nearest"] = rec["external_price_median_monitor"][chosen]
        out.loc[idx_arr, "external_log_price_nearest"] = rec["external_log_price_monitor"][chosen]
        out.loc[idx_arr, "external_price_index_category_nearest_mean100"] = rec["external_price_index_category_monitor_mean100"][chosen]
        out.loc[idx_arr, "external_price_fill_level_nearest"] = rec["price_fill_level"][chosen]
        out.loc[idx_arr, "external_price_proxy_source_category"] = rec["proxy_source_category"][chosen]
        out.loc[idx_arr, "external_price_n_obs_clean"] = rec["n_price_obs_clean"][chosen]
    return pd.concat([chunk, out], axis=1)


def clean_consumption_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk = chunk.copy()
    chunk["_ID_key"] = chunk["ID"].astype("string").str.strip()
    chunk["province_clean"] = chunk["Province"].map(norm_province)
    dt = pd.to_datetime(chunk["Date"], errors="coerce", format="mixed")
    chunk["date_clean"] = dt.dt.floor("D")
    chunk["year"] = chunk["date_clean"].dt.year.astype("Int16")
    chunk["year_month"] = chunk["date_clean"].dt.strftime("%Y-%m")
    chunk["family_size_midpoint"] = chunk["Family_Size"].astype("string").str.strip().map(FAMILY_SIZE_MIDPOINT)
    chunk["Spend_num"] = pd.to_numeric(chunk["Spend"], errors="coerce")
    chunk["Volume_num"] = pd.to_numeric(chunk["Volume"], errors="coerce")
    chunk["Price_num"] = pd.to_numeric(chunk["Price"], errors="coerce")
    chunk["unit_value_calc"] = chunk["Spend_num"] / chunk["Volume_num"].where(chunk["Volume_num"] > 0)

    chunk["date_invalid_flag"] = chunk["date_clean"].isna().astype("int8")
    chunk["spend_negative_flag"] = (chunk["Spend_num"] < 0).fillna(False).astype("int8")
    chunk["volume_negative_flag"] = (chunk["Volume_num"] < 0).fillna(False).astype("int8")
    chunk["price_original_negative_flag"] = (chunk["Price_num"] < 0).fillna(False).astype("int8")
    chunk["spend_zero_flag"] = (chunk["Spend_num"] == 0).fillna(False).astype("int8")
    chunk["volume_zero_flag"] = (chunk["Volume_num"] == 0).fillna(False).astype("int8")

    for col in ["spend_outlier_flag", "volume_outlier_flag", "unit_value_outlier_flag"]:
        chunk[col] = np.int8(0)
    chunk["Spend_winsor"] = chunk["Spend_num"].where(chunk["Spend_num"] >= 0)
    chunk["Volume_winsor"] = chunk["Volume_num"].where(chunk["Volume_num"] >= 0)
    chunk["unit_value_calc_winsor"] = chunk["unit_value_calc"].where(chunk["unit_value_calc"] > 0)

    chunk["consumption_outlier_any_flag"] = (
        chunk[
            [
                "date_invalid_flag",
                "spend_negative_flag",
                "volume_negative_flag",
                "price_original_negative_flag",
                "spend_outlier_flag",
                "volume_outlier_flag",
                "unit_value_outlier_flag",
            ]
        ].sum(axis=1)
        > 0
    ).astype("int8")
    chunk["analysis_keep_flag"] = (chunk["consumption_outlier_any_flag"] == 0).astype("int8")
    chunk["food_group10"] = chunk["Category"].map(GROUP10)
    return chunk


def write_consumption_with_prices(
    price_lookup: dict[tuple[str, str], dict[str, Any]],
    household_year_outliers: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    out_path = OUT / "Data_merged_nearest_external_price_cleaned_2020_2022.parquet"
    if out_path.exists():
        out_path.unlink()
    writer: pq.ParquetWriter | None = None
    stats = Counter()
    category_stats = Counter()
    match_days = Counter()
    cols_for_stats = [
        "date_invalid_flag",
        "spend_negative_flag",
        "volume_negative_flag",
        "price_original_negative_flag",
        "spend_zero_flag",
        "volume_zero_flag",
        "spend_outlier_flag",
        "volume_outlier_flag",
        "unit_value_outlier_flag",
        "household_year_category_spend_outlier_flag",
        "household_year_category_volume_outlier_flag",
        "consumption_outlier_any_flag",
        "analysis_keep_flag",
    ]
    annual_cols = [
        "_ID_key",
        "year",
        "Category",
        "household_year_category_spend",
        "household_year_category_volume",
        "household_year_category_transaction_count",
        "household_year_category_family_size_midpoint",
        "household_year_category_spend_pc",
        "household_year_category_volume_pc",
        "household_year_category_spend_outlier_flag",
        "household_year_category_volume_outlier_flag",
        "household_year_category_outlier_any_flag",
    ]
    annual_flags = household_year_outliers[annual_cols].copy()
    try:
        for i, chunk in enumerate(pd.read_csv(CONSUMPTION, chunksize=300_000, encoding="utf-8-sig"), 1):
            cleaned = clean_consumption_chunk(chunk)
            matched = match_nearest_price(cleaned, price_lookup)
            matched = matched.merge(annual_flags, on=["_ID_key", "year", "Category"], how="left")
            for col in [
                "household_year_category_spend_outlier_flag",
                "household_year_category_volume_outlier_flag",
                "household_year_category_outlier_any_flag",
            ]:
                matched[col] = matched[col].fillna(0).astype("int8")
            matched["spend_outlier_flag"] = matched["household_year_category_spend_outlier_flag"]
            matched["volume_outlier_flag"] = matched["household_year_category_volume_outlier_flag"]
            matched["unit_value_outlier_flag"] = np.int8(0)
            matched["consumption_outlier_any_flag"] = (
                matched[
                    [
                        "date_invalid_flag",
                        "spend_negative_flag",
                        "volume_negative_flag",
                        "price_original_negative_flag",
                        "spend_outlier_flag",
                        "volume_outlier_flag",
                        "unit_value_outlier_flag",
                    ]
                ].sum(axis=1)
                > 0
            ).astype("int8")
            matched["analysis_keep_flag"] = (matched["consumption_outlier_any_flag"] == 0).astype("int8")
            matched["external_price_match_missing_flag"] = matched["external_price_mean_nearest"].isna().astype("int8")
            matched["external_price_match_over_10days_flag"] = (matched["external_price_abs_days_diff"] > 10).fillna(True).astype("int8")
            for col in cols_for_stats + ["external_price_match_missing_flag", "external_price_match_over_10days_flag"]:
                stats[col] += int(matched[col].sum())
            stats["rows"] += len(matched)
            for cat, sub in matched.groupby("Category"):
                category_stats[(cat, "rows")] += len(sub)
                category_stats[(cat, "outlier_any")] += int(sub["consumption_outlier_any_flag"].sum())
                category_stats[(cat, "annual_spend_outlier")] += int(sub["household_year_category_spend_outlier_flag"].sum())
                category_stats[(cat, "annual_volume_outlier")] += int(sub["household_year_category_volume_outlier_flag"].sum())
                category_stats[(cat, "price_missing")] += int(sub["external_price_match_missing_flag"].sum())
                category_stats[(cat, "price_over_10days")] += int(sub["external_price_match_over_10days_flag"].sum())
            for k, v in matched["external_price_abs_days_diff"].value_counts(dropna=False).items():
                match_days[str(k)] += int(v)

            # Keep string/date columns stable for pyarrow.
            matched = matched.drop(columns=["_ID_key"])
            for c in matched.select_dtypes(include=["object"]).columns:
                matched[c] = matched[c].astype("string")
            table = pa.Table.from_pandas(matched, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out_path, table.schema, compression="zstd")
            writer.write_table(table)
            print(f"matched and cleaned {stats['rows']:,} rows", flush=True)
    finally:
        if writer is not None:
            writer.close()

    cat_rows = []
    for cat in sorted({k[0] for k in category_stats}):
        rows = category_stats[(cat, "rows")]
        cat_rows.append(
            {
                "Category": cat,
                "rows": rows,
                "consumption_outlier_any": category_stats[(cat, "outlier_any")],
                "consumption_outlier_rate": category_stats[(cat, "outlier_any")] / rows if rows else np.nan,
                "annual_spend_outlier": category_stats[(cat, "annual_spend_outlier")],
                "annual_volume_outlier": category_stats[(cat, "annual_volume_outlier")],
                "price_match_missing": category_stats[(cat, "price_missing")],
                "price_match_over_10days": category_stats[(cat, "price_over_10days")],
            }
        )
    stats_dict = dict(stats)
    stats_dict["output_path"] = str(out_path)
    stats_dict["output_size_bytes"] = out_path.stat().st_size if out_path.exists() else 0
    match_days_df = pd.DataFrame([{"abs_days_diff": k, "rows": v} for k, v in match_days.items()]).sort_values("abs_days_diff")
    match_days_df.to_csv(OUT / "nearest_external_price_match_days_distribution.csv", index=False, encoding="utf-8-sig")
    return stats_dict, pd.DataFrame(cat_rows)


def write_report(
    price_report: pd.DataFrame,
    price_by_date: pd.DataFrame,
    group_by_date: pd.DataFrame,
    consumption_thresholds_df: pd.DataFrame,
    consumption_stats: dict[str, Any],
    consumption_category_report: pd.DataFrame,
) -> None:
    price_cov = (
        price_by_date.groupby("Category", as_index=False)
        .agg(
            rows=("external_price_mean_monitor", "size"),
            non_missing=("external_price_mean_monitor", lambda x: int(x.notna().sum())),
            observed=("price_fill_level", lambda x: int((x == "observed_province_monitor_date").sum())),
            proxy=("price_fill_level", lambda x: int(x.astype(str).str.contains("proxy").sum())),
        )
        .sort_values("Category")
    )
    lines = []
    lines.append("# 最近监测价格匹配与异常值清洗报告")
    lines.append("")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 输出文件")
    lines.append("")
    for name in [
        "external_food_prices_category_province_monitor_date_cleaned_2020_2022.csv",
        "external_food_prices_group10_province_monitor_date_cleaned_2020_2022.csv",
        "Data_merged_nearest_external_price_cleaned_2020_2022.parquet",
        "external_food_price_observation_outlier_report.csv",
        "consumption_outlier_thresholds_by_category.csv",
        "consumption_household_year_category_outlier_report.csv",
        "consumption_outlier_report_by_category.csv",
        "nearest_external_price_match_days_distribution.csv",
    ]:
        p = OUT / name
        if p.exists():
            lines.append(f"- `{name}`：{p.stat().st_size / (1024 * 1024):.1f} MB")
    lines.append("")
    lines.append("## 价格清洗与覆盖")
    lines.append("")
    lines.append(f"- 原始映射价格观测分组数：{len(price_report):,}")
    lines.append(f"- 监测日价格表行数：{len(price_by_date):,}")
    lines.append(f"- 10 组监测日价格表行数：{len(group_by_date):,}")
    lines.append(f"- 价格观测异常值数：{int(price_report['n_outlier'].sum()):,}")
    lines.append("")
    lines.append("| 品类 | 省份-监测日网格 | 非缺失 | 直接观测 | 代理 |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in price_cov.itertuples(index=False):
        lines.append(f"| {r.Category} | {r.rows} | {r.non_missing} | {r.observed} | {r.proxy} |")
    lines.append("")
    lines.append("## 消费数据清洗")
    lines.append("")
    rows = int(consumption_stats.get("rows", 0))
    lines.append(f"- 消费记录数：{rows:,}")
    for key in [
        "date_invalid_flag",
        "spend_negative_flag",
        "volume_negative_flag",
        "price_original_negative_flag",
        "spend_zero_flag",
        "volume_zero_flag",
        "spend_outlier_flag",
        "volume_outlier_flag",
        "unit_value_outlier_flag",
        "household_year_category_spend_outlier_flag",
        "household_year_category_volume_outlier_flag",
        "consumption_outlier_any_flag",
        "external_price_match_missing_flag",
        "external_price_match_over_10days_flag",
    ]:
        val = int(consumption_stats.get(key, 0))
        rate = val / rows if rows else 0
        lines.append(f"- `{key}`：{val:,}（{rate:.4%}）")
    lines.append("")
    lines.append("## 消费品类异常概览")
    lines.append("")
    lines.append("| 品类 | 行数 | 消费异常数 | 消费异常率 | 年度人均支出异常 | 年度人均购买量高值异常 | 价格缺失 | 价格间隔超过10天 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in consumption_category_report.sort_values("Category").itertuples(index=False):
        lines.append(
            f"| {r.Category} | {int(r.rows)} | {int(r.consumption_outlier_any)} | {r.consumption_outlier_rate:.4%} | {int(r.annual_spend_outlier)} | {int(r.annual_volume_outlier)} | {int(r.price_match_missing)} | {int(r.price_match_over_10days)} |"
        )
    lines.append("")
    lines.append("## 口径说明")
    lines.append("")
    lines.append("- 价格先在原始监测点层面按 `Category × unit` 的 log 价格 0.5%/99.5% 分位识别异常，异常观测不进入省份-监测日均值。")
    lines.append("- 省份-监测日价格按清洗后的点位价格算术均值聚合。")
    lines.append("- 每条消费记录按 `province_clean × Category` 匹配最近监测日价格，并保留 `external_price_days_diff`。正数表示消费日晚于监测日，负数表示消费日早于监测日。")
    lines.append("- 消费异常不再使用单笔交易支出、单笔购买量或单位价值切尾部，也不再将支出或单位价值作为异常筛选条件。")
    lines.append("- 购买量异常按 `ID × year × Category` 汇总全年购买量，使用 `Family_Size` 中点换算人均年度购买量，再在品类内对正值样本按 log 99.9% 上尾识别高值异常；低购买量不判为异常。")
    lines.append("- `Family_Size` 换算为 `家庭人口数1-2=1.5`、`家庭人口数3=3.0`、`家庭人口数4=4.0`、`家庭人口数5+=5.5`。")
    lines.append("- `volume_outlier_flag` 对应上述户年品类人均年度购买量高值口径；`spend_outlier_flag` 和 `unit_value_outlier_flag` 当前固定为 0。`Spend_winsor`、`Volume_winsor`、`unit_value_calc_winsor` 保留为非负原值/正单位值，不做交易级缩尾。")
    lines.append("- 建模时建议使用 `analysis_keep_flag == 1` 的样本，并用 `external_log_price_nearest` 或 10 组监测日价格作为外生价格。")
    (OUT / "nearest_price_matching_and_cleaning_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    main_provinces, main_categories, _months = load_consumption_scope()
    print(f"Scope: {len(main_provinces)} provinces, {len(main_categories)} categories", flush=True)

    print("Cleaning price observations...", flush=True)
    price_obs_all, price_obs_clean, price_report = clean_price_observations()
    price_report.to_csv(OUT / "external_food_price_observation_outlier_report.csv", index=False, encoding="utf-8-sig")
    try:
        price_obs_all.to_parquet(OUT / "external_food_prices_mapped_observations_with_outlier_flags_2020_2022.parquet", index=False)
    except Exception as exc:
        print(f"Price observation parquet skipped: {exc}", flush=True)

    print("Building province-monitor-date price tables...", flush=True)
    price_by_date, group_by_date = build_monitor_date_prices(price_obs_clean, main_provinces, main_categories)
    price_by_date.to_csv(OUT / "external_food_prices_category_province_monitor_date_cleaned_2020_2022.csv", index=False, encoding="utf-8-sig")
    group_by_date.to_csv(OUT / "external_food_prices_group10_province_monitor_date_cleaned_2020_2022.csv", index=False, encoding="utf-8-sig")
    price_by_date.to_parquet(OUT / "external_food_prices_category_province_monitor_date_cleaned_2020_2022.parquet", index=False)
    group_by_date.to_parquet(OUT / "external_food_prices_group10_province_monitor_date_cleaned_2020_2022.parquet", index=False)

    print("Collecting household-year-category consumption outliers...", flush=True)
    consumption_thresholds_df, household_year_outliers = collect_household_year_category_outliers()
    consumption_thresholds_df.to_csv(OUT / "consumption_outlier_thresholds_by_category.csv", index=False, encoding="utf-8-sig")
    household_year_outlier_report = household_year_outliers[household_year_outliers["household_year_category_outlier_any_flag"].eq(1)].copy()
    household_year_outlier_report.to_csv(
        OUT / "consumption_household_year_category_outlier_report.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("Matching nearest prices and cleaning consumption...", flush=True)
    lookup = build_price_lookup(price_by_date)
    consumption_stats, consumption_category_report = write_consumption_with_prices(lookup, household_year_outliers)
    consumption_category_report.to_csv(OUT / "consumption_outlier_report_by_category.csv", index=False, encoding="utf-8-sig")

    print("Writing report...", flush=True)
    write_report(
        price_report=price_report,
        price_by_date=price_by_date,
        group_by_date=group_by_date,
        consumption_thresholds_df=consumption_thresholds_df,
        consumption_stats=consumption_stats,
        consumption_category_report=consumption_category_report,
    )
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
