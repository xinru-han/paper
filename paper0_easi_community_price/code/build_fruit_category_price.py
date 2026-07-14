#!/usr/bin/env python3
"""Build a fixed-weight seven-category community fruit price index."""

from __future__ import annotations

import argparse
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)


OUTLETS = ("chaoshi08", "zhd08", "zysc08")
CATEGORY_LABELS = {
    1: "melons",
    2: "citrus",
    3: "berries_and_other_fresh",
    4: "pome_and_stone_fruit",
    5: "nuts_and_seeds",
    6: "canned_preserved_fruit",
    7: "other_dried_fruit",
}
ITEM_CATEGORY = {
    "shuiguo_1": 1,
    "shuiguo_2": 2,
    "shuiguo_3": 3,
    "shuiguo_7": 4,
    "shuiguo_6": 5,
    "shuiguo_4": 6,
    "shuiguo_5": 7,
}
MODULES = ("水果干果.csv", "水果制品.csv")
SOURCE_LABELS = {
    1: "own_village_direct",
    3: "same_town_direct_median",
    4: "nearest_direct_village_in_county",
    5: "county_year_direct_median",
    6: "province_year_direct_median",
    7: "province_pooled_direct_median",
    8: "national_year_direct_median",
    9: "overall_direct_median",
}


def numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").astype(float)
    text = series.astype("string").str.strip()
    text = text.str.replace("，", ".", regex=False).str.replace("。", ".", regex=False)
    direct = pd.to_numeric(text, errors="coerce")
    fraction = text.str.extract(r"^\s*(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)\s*$")
    numerator = pd.to_numeric(fraction[0], errors="coerce")
    denominator = pd.to_numeric(fraction[1], errors="coerce")
    frac_value = numerator / denominator.where(denominator.ne(0))
    first_number = pd.to_numeric(
        text.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False), errors="coerce"
    )
    return direct.fillna(frac_value).fillna(first_number).astype(float)


def fruit_weights(source: Path) -> pd.DataFrame:
    values = {category: 0.0 for category in CATEGORY_LABELS}
    fields = {category: 0 for category in CATEGORY_LABELS}
    unclassified_value = 0.0
    unclassified_fields = 0

    for year in (2023, 2024):
        for module in MODULES:
            path = source / str(year) / module
            names = list(pd.read_csv(path, nrows=0, encoding="utf-8-sig").columns)
            qvars = [name for name in names if "_laiyuan-02-" in name]
            columns = ["freq_period_days"]
            for qvar in qvars:
                columns.extend(
                    [qvar, qvar.replace("_laiyuan-02-", "_laiyuan-03-", 1),
                     qvar.replace("_laiyuan-02-", "_laiyuan-00-", 1)]
                )
            frame = pd.read_csv(
                path,
                usecols=list(dict.fromkeys(columns)),
                encoding="utf-8-sig",
                low_memory=False,
            )
            days = numeric(frame["freq_period_days"])
            for qvar in qvars:
                xvar = qvar.replace("_laiyuan-02-", "_laiyuan-03-", 1)
                fvar = qvar.replace("_laiyuan-02-", "_laiyuan-00-", 1)
                quantity = numeric(frame[qvar])
                expenditure = numeric(frame[xvar])
                frequency = numeric(frame[fvar])
                factor = np.where(
                    frequency.eq(2),
                    30.0 / 7.0,
                    np.where(frequency.eq(1) & days.gt(0), 30.0 / days, np.nan),
                )
                valid = quantity.gt(0) & expenditure.gt(0) & np.isfinite(factor)
                monthly_value = float(
                    np.where(valid, expenditure * factor, 0.0).sum()
                )
                item = qvar.rsplit("-", 1)[-1]
                category = ITEM_CATEGORY.get(item)
                if category is None:
                    unclassified_value += monthly_value
                    unclassified_fields += 1
                else:
                    values[category] += monthly_value
                    fields[category] += 1

    total = sum(values.values())
    if not np.isfinite(total) or total <= 0:
        raise RuntimeError("No positive mapped fruit expenditure for fixed weights")
    rows = [
        {
            "category": category,
            "category_label": CATEGORY_LABELS[category],
            "monthly_purchase_value": values[category],
            "expenditure_weight": values[category] / total,
            "matched_item_fields": fields[category],
            "included_in_index": 1,
        }
        for category in CATEGORY_LABELS
    ]
    rows.append(
        {
            "category": 0,
            "category_label": "unclassified_placeholder",
            "monthly_purchase_value": unclassified_value,
            "expenditure_weight": unclassified_value / (total + unclassified_value),
            "matched_item_fields": unclassified_fields,
            "included_in_index": 0,
        }
    )
    return pd.DataFrame(rows)


def midpoint(high: pd.Series, low: pd.Series) -> pd.Series:
    result = (high + low) / 2.0
    result = result.where(~low.isna(), high)
    return result.where(~high.isna(), low)


def screen_log_mad(values: pd.Series, years: pd.Series) -> tuple[pd.Series, pd.Series]:
    result = values.copy()
    outlier = pd.Series(False, index=values.index)
    for year in years.dropna().unique():
        mask = years.eq(year) & result.gt(0)
        logged = np.log(result.loc[mask])
        median = logged.median()
        mad = (logged - median).abs().median()
        if np.isfinite(mad) and mad > 0:
            flagged = (logged - median).abs() > 5.0 * 1.4826 * mad
            outlier.loc[flagged.index] = flagged
    result.loc[outlier] = np.nan
    return result, outlier


def haversine(lat1: float, lon1: float, lat2: pd.Series, lon2: pd.Series) -> pd.Series:
    lat1r = np.radians(lat1)
    lon1r = np.radians(lon1)
    lat2r = np.radians(lat2.astype(float))
    lon2r = np.radians(lon2.astype(float))
    cosine = (
        np.sin(lat1r) * np.sin(lat2r)
        + np.cos(lat1r) * np.cos(lat2r) * np.cos(lon2r - lon1r)
    )
    return pd.Series(6371.0 * np.arccos(np.clip(cosine, -1.0, 1.0)), index=lat2.index)


def fill_category(
    target: pd.DataFrame, donors: pd.DataFrame, category: int
) -> tuple[pd.Series, pd.Series]:
    direct_name = f"p6cat{category}_direct"
    values = target[direct_name].copy()
    source = pd.Series(np.where(values.notna(), 1, np.nan), index=target.index)

    town = donors.groupby(["town_id", "data_year"])[direct_name].median()
    town_keys = pd.MultiIndex.from_frame(target[["town_id", "data_year"]])
    town_values = pd.Series(town.reindex(town_keys).to_numpy(), index=target.index)
    fill = values.isna() & town_values.notna()
    values.loc[fill] = town_values.loc[fill]
    source.loc[fill] = 3

    direct = donors.loc[donors[direct_name].notna()].copy()
    for index in target.index[values.isna()]:
        row = target.loc[index]
        candidates = direct.loc[
            direct["county_id"].eq(row["county_id"])
            & direct["data_year"].eq(row["data_year"])
            & ~direct["village_id"].eq(row["village_id"])
        ]
        if (
            candidates.empty
            or pd.isna(row["vilLat"])
            or pd.isna(row["vilLon"])
        ):
            continue
        distance = haversine(row["vilLat"], row["vilLon"], candidates["vilLat"], candidates["vilLon"])
        if distance.notna().any():
            nearest = candidates.loc[distance.idxmin(), direct_name]
            if pd.notna(nearest):
                values.loc[index] = nearest
                source.loc[index] = 4

    county = donors.groupby(["county_id", "data_year"])[direct_name].median()
    county_keys = pd.MultiIndex.from_frame(target[["county_id", "data_year"]])
    county_values = pd.Series(county.reindex(county_keys).to_numpy(), index=target.index)
    fill = values.isna() & county_values.notna()
    values.loc[fill] = county_values.loc[fill]
    source.loc[fill] = 5

    province = donors.groupby(["province_id", "data_year"])[direct_name].median()
    province_keys = pd.MultiIndex.from_frame(target[["province_id", "data_year"]])
    province_values = pd.Series(province.reindex(province_keys).to_numpy(), index=target.index)
    fill = values.isna() & province_values.notna()
    values.loc[fill] = province_values.loc[fill]
    source.loc[fill] = 6

    province_pooled = donors.groupby("province_id")[direct_name].median()
    province_pooled_values = target["province_id"].map(province_pooled)
    fill = values.isna() & province_pooled_values.notna()
    values.loc[fill] = province_pooled_values.loc[fill]
    source.loc[fill] = 7

    year_median = donors.groupby("data_year")[direct_name].median()
    year_values = target["data_year"].map(year_median)
    fill = values.isna() & year_values.notna()
    values.loc[fill] = year_values.loc[fill]
    source.loc[fill] = 8

    overall = donors[direct_name].median()
    fill = values.isna() & np.isfinite(overall)
    values.loc[fill] = overall
    source.loc[fill] = 9
    if values.isna().any() or ~(values > 0).all():
        raise RuntimeError(f"Category {category} price remains missing or nonpositive")
    return values.astype(float), source.astype(int)


def build_prices(
    village_path: Path, target_path: Path, weights: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    village = pd.read_stata(village_path, convert_categoricals=False)
    village["village_id"] = village["xzcCode_clean"].astype("string").str.strip()
    village["town_id"] = village["village_id"].str[:9]
    village["county_id"] = village["village_id"].str[:6]
    village["province_id"] = village["village_id"].str[:2]
    audit_rows: list[dict] = []

    for category in CATEGORY_LABELS:
        outlet_prices = []
        invalid = 0
        for outlet in OUTLETS:
            high_pattern = re.compile(rf"^{outlet}_0{category}_.*_hp$")
            low_pattern = re.compile(rf"^{outlet}_0{category}_.*_lp$")
            high_columns = [column for column in village.columns if high_pattern.match(column)]
            low_columns = [column for column in village.columns if low_pattern.match(column)]
            if not high_columns or not low_columns:
                raise RuntimeError(f"Missing category {category} quote fields for {outlet}")
            high_frame = village[high_columns].apply(pd.to_numeric, errors="coerce")
            low_frame = village[low_columns].apply(pd.to_numeric, errors="coerce")
            invalid += int(((high_frame <= 0) | (high_frame > 200)).sum().sum())
            invalid += int(((low_frame <= 0) | (low_frame > 200)).sum().sum())
            high_frame = high_frame.where((high_frame > 0) & (high_frame <= 200))
            low_frame = low_frame.where((low_frame > 0) & (low_frame <= 200))
            outlet_prices.append(midpoint(high_frame.median(axis=1), low_frame.median(axis=1)))
        direct = pd.concat(outlet_prices, axis=1).median(axis=1)
        direct, outlier = screen_log_mad(direct, village["data_year"])
        village[f"p6cat{category}_direct"] = direct
        audit_rows.extend(
            [
                {"category": category, "statistic": "invalid_quote_cells", "value": invalid},
                {"category": category, "statistic": "five_mad_direct_outliers", "value": int(outlier.sum())},
                {"category": category, "statistic": "direct_villages", "value": int(direct.notna().sum())},
            ]
        )

    keep = [
        "village_id", "data_year", "town_id", "county_id", "province_id",
        "vilLat", "vilLon",
    ] + [f"p6cat{category}_direct" for category in CATEGORY_LABELS]
    donors = village[keep].copy()
    target = pd.read_stata(target_path, convert_categoricals=False)
    target["village_id"] = target["village_id"].astype("string").str.strip()
    target = target[
        ["village_id", "data_year", "town_id", "county_id", "province_id", "vilLat", "vilLon"]
    ].copy()
    target = target.merge(
        donors[["village_id", "data_year"] + [f"p6cat{category}_direct" for category in CATEGORY_LABELS]],
        on=["village_id", "data_year"],
        how="left",
        validate="one_to_one",
    )

    weight_lookup = weights.loc[weights["included_in_index"].eq(1)].set_index("category")["expenditure_weight"]
    log_index = pd.Series(0.0, index=target.index)
    source_columns = []
    for category in CATEGORY_LABELS:
        values, source = fill_category(target, donors, category)
        target[f"p6cat{category}"] = values
        target[f"p6cat{category}_source"] = source
        source_columns.append(f"p6cat{category}_source")
        log_index += float(weight_lookup.loc[category]) * np.log(values)
        for source_code, count in source.value_counts().sort_index().items():
            audit_rows.append(
                {
                    "category": category,
                    "statistic": f"completed_source_{int(source_code)}_villages",
                    "source_label": SOURCE_LABELS[int(source_code)],
                    "value": int(count),
                }
            )

    target["p6_basket"] = np.exp(log_index)
    target["p6_basket_source"] = target[source_columns].max(axis=1).astype(int)
    target["direct_category_count"] = target[
        [f"p6cat{category}_direct" for category in CATEGORY_LABELS]
    ].notna().sum(axis=1)
    target["all_categories_direct"] = target["direct_category_count"].eq(7).astype(int)
    output_columns = [
        "data_year", "village_id", "p6_basket", "p6_basket_source",
        "direct_category_count", "all_categories_direct",
    ]
    for category in CATEGORY_LABELS:
        output_columns.extend(
            [f"p6cat{category}_direct", f"p6cat{category}", f"p6cat{category}_source"]
        )
    return target[output_columns], pd.DataFrame(audit_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--village", type=Path, required=True)
    parser.add_argument("--household-source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--price-output", type=Path, required=True)
    parser.add_argument("--weight-output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()

    weights = fruit_weights(args.household_source)
    prices, audit = build_prices(args.village, args.target, weights)
    args.price_output.parent.mkdir(parents=True, exist_ok=True)
    weights.to_csv(args.weight_output, index=False)
    prices.to_csv(args.price_output, index=False)
    audit.to_csv(args.audit_output, index=False)


if __name__ == "__main__":
    main()
