#!/usr/bin/env python3
"""Build analysis data for the literal nine-group food demand system."""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/root/data/Paper/食物消费数据/paper0-EASI/easi_nine_groups")
RAW = Path("/root/data/数据/食物消费调查数据/处理后的data")
ITEM_LONG = Path("/root/data/Paper/食物消费数据/paper0-EASI/item_level_food_descriptives/outputs/household_item_long.dta")
DATA = ROOT / "data"
OUT = ROOT / "outputs"


GROUPS = {
    1: {
        "name": "主食及加工品",
        "items": ["zhushi_1", "zhushi_2_1", "zhushi_3", "zhushi_3_1", "zhushi_5", "zhushi_6", "zhushi_7", "zhushi_1_1", "zhushi_2", "zhushi_2_2", "zhushi_8"],
        "price_patterns": ["常吃的面粉单价", "常吃的大米单价"],
        "cap_pc_month": 120.0,
    },
    2: {
        "name": "豆类及加工品",
        "items": ["doulei_1", "doulei_4", "doulei_2", "doulei_3", "xiancai_4"],
        "price_patterns": ["常吃的豆腐单价", "常吃的黄豆单价"],
        "cap_pc_month": 30.0,
    },
    3: {
        "name": "畜禽肉",
        "items": ["roulei_1", "roulei_2", "roulei_3", "roulei_4", "roulei_9", "roulei_5", "roulei_6", "roulei_7", "roulei_8"],
        "price_patterns": ["肥瘦猪肉单价"],
        "cap_pc_month": 60.0,
    },
    4: {
        "name": "蛋类及制品",
        "items": ["danlei_1", "danlei_2", "danlei_3"],
        "price_patterns": ["普通鸡蛋的单价"],
        "cap_pc_month": 30.0,
    },
    5: {
        "name": "奶类",
        "items": ["nailei_1", "nailei_2", "nailei_3"],
        "price_patterns": ["普通盒装纯牛奶的单价"],
        "cap_pc_month": 120.0,
    },
    6: {
        "name": "水产品及制品",
        "items": ["shuichan_1", "roulei_13"],
        "price_patterns": ["鲤鱼的单价", "带鱼的单价"],
        "cap_pc_month": 60.0,
    },
    7: {
        "name": "油脂",
        "items": ["youzhi_1", "youzhi_2", "youzhi_3", "youzhi_4", "youzhi_5", "youzhi_6"],
        "price_patterns": ["常吃菜籽油的单价"],
        "cap_pc_month": 21.0,
    },
    8: {
        "name": "蔬菜及制品",
        "items": ["shucai_1", "shucai_2", "shucai_3", "shucai_4", "shucai_5", "shucai_6", "shucai_7", "shucai_8", "shucai_9", "xiancai_1", "xiancai_2"],
        "price_patterns": ["青菜的单价", "白菜的单价"],
        "cap_pc_month": 180.0,
    },
    9: {
        "name": "干果及制品",
        "items": ["shuiguo_6", "shuiguo_4", "shuiguo_5"],
        "price_patterns": ["常吃瓜子（葵花子）的单价"],
        "cap_pc_month": 60.0,
    },
}


OUTLETS = ["大超市", "食品杂货店", "自由市场/农贸市场", "肉店/水产店"]
FLOW_COLUMNS = [
    "purchase_consumed_month",
    "own_consumed_month",
    "gift_consumed_month",
    "total_consumed_month",
    "purchase_acquired_month",
    "purchase_expenditure_month",
]


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype(float)


def median_abs_deviation(values: pd.Series) -> float:
    clean = values.dropna()
    if not len(clean):
        return np.nan
    med = clean.median()
    return float((clean - med).abs().median())


def household_core() -> pd.DataFrame:
    roster_rel = [f"family1_{m:02d}_HA1" for m in range(1, 9)]
    roster_sex = [f"family1_{m:02d}_HA2" for m in range(1, 9)]
    roster_birth = [f"family1_{m:02d}_HA3" for m in range(1, 9)]
    roster_edu = [f"family2_{m:02d}_HA10" for m in range(1, 9)]
    columns = [
        "nhCode", "data_year", "prov", "vilLat", "vilLon", "HA0",
        "total_income_w", "monthly_expense_total", *roster_rel, *roster_sex,
        *roster_birth, *roster_edu,
    ]
    frame = pd.read_stata(RAW / "户表数据_已清洗.dta", columns=columns, convert_categoricals=False)
    frame["household_id"] = frame["nhCode"].astype("string").str.strip()
    frame["village_id"] = frame["household_id"].str.slice(0, 12)
    frame["town_id"] = frame["village_id"].str.slice(0, 9)
    frame["county_id"] = frame["village_id"].str.slice(0, 6)
    frame["province_id"] = frame["village_id"].str.slice(0, 2)
    reported = numeric(frame["HA0"])
    roster_size = frame[roster_rel].notna().sum(axis=1).astype(float)
    frame["hhsize"] = reported.where(reported.between(1, 20), roster_size.where(roster_size.gt(0)))

    child, elderly, age_n = np.zeros(len(frame)), np.zeros(len(frame)), np.zeros(len(frame))
    female_head = np.full(len(frame), np.nan)
    head_education = np.full(len(frame), np.nan)
    for m in range(1, 9):
        rel = numeric(frame[f"family1_{m:02d}_HA1"])
        sex = numeric(frame[f"family1_{m:02d}_HA2"])
        birth_text = frame[f"family1_{m:02d}_HA3"].astype("string")
        birth_year = pd.to_numeric(birth_text.str.extract(r"(\d{4})", expand=False), errors="coerce")
        age = frame["data_year"] - birth_year
        age = age.where(age.between(0, 110))
        child += (age < 15).fillna(False).to_numpy(float)
        elderly += (age >= 65).fillna(False).to_numpy(float)
        age_n += age.notna().to_numpy(float)
        is_head = rel.eq(1).to_numpy()
        fill_sex = is_head & np.isnan(female_head) & sex.isin([0, 1]).to_numpy()
        female_head[fill_sex] = sex.loc[fill_sex].eq(0).astype(float)
        edu = numeric(frame[f"family2_{m:02d}_HA10"])
        fill_edu = is_head & np.isnan(head_education) & edu.notna().to_numpy()
        head_education[fill_edu] = edu.loc[fill_edu]
    frame["child_ratio"] = np.divide(child, age_n, out=np.zeros(len(frame)), where=age_n > 0)
    frame["elderly_ratio"] = np.divide(elderly, age_n, out=np.zeros(len(frame)), where=age_n > 0)
    frame["age_missing"] = (age_n == 0).astype(int)
    frame["female_head_missing"] = np.isnan(female_head).astype(int)
    frame["female_head"] = np.nan_to_num(female_head, nan=0.0)
    frame["education_missing"] = np.isnan(head_education).astype(int)
    frame["head_no_education"] = np.where(np.isnan(head_education), 0, head_education == 1).astype(int)
    frame["head_primary_education"] = np.where(np.isnan(head_education), 0, head_education == 2).astype(int)
    frame["income_annual"] = numeric(frame["total_income_w"]).where(numeric(frame["total_income_w"]) > 0)
    frame["ln_income"] = np.log(frame["income_annual"])
    frame["inv_income"] = 1 / frame["income_annual"]
    frame["total_exp_monthly"] = numeric(frame["monthly_expense_total"]).where(numeric(frame["monthly_expense_total"]) > 0)
    frame["year_2024"] = frame["data_year"].eq(2024).astype(int)
    province_dummies = pd.get_dummies(frame["province_id"], prefix="province", dtype=int)
    if len(province_dummies.columns):
        province_dummies = province_dummies.drop(columns=sorted(province_dummies.columns)[0])
    frame = pd.concat([frame, province_dummies], axis=1)
    frame["village_cluster"] = pd.factorize(frame["village_id"].astype(str) + "_" + frame["data_year"].astype(str), sort=True)[0] + 1
    if frame.duplicated(["household_id", "data_year"]).any():
        raise RuntimeError("Household-year IDs are not unique")
    keep = [
        "household_id", "data_year", "village_id", "town_id", "county_id",
        "province_id", "vilLat", "vilLon", "hhsize", "child_ratio",
        "elderly_ratio", "female_head", "head_no_education",
        "head_primary_education", "age_missing", "female_head_missing",
        "education_missing", "income_annual", "ln_income", "inv_income",
        "total_exp_monthly", "year_2024", "village_cluster",
        *province_dummies.columns.tolist(),
    ]
    return frame[keep]


def aggregate_quantities(core: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    long = pd.read_stata(ITEM_LONG, convert_categoricals=False)
    item_to_group = {item: group for group, spec in GROUPS.items() for item in spec["items"]}
    long["group"] = long["item_code"].map(item_to_group)
    excluded = long.loc[long["group"].isna()].copy()
    included = long.loc[long["group"].notna()].copy()
    included["group"] = included["group"].astype(int)
    collapsed = included.groupby(["household_id", "data_year", "group"], as_index=False)[FLOW_COLUMNS].sum()
    base = core[["household_id", "data_year"]].copy()
    wide = base.copy()
    for g in GROUPS:
        part = collapsed.loc[collapsed["group"].eq(g)].drop(columns="group")
        part = part.rename(
            columns={
                "total_consumed_month": f"qt{g}",
                "purchase_consumed_month": f"qb{g}",
                "own_consumed_month": f"qs{g}",
                "gift_consumed_month": f"qg{g}",
                "purchase_acquired_month": f"qa{g}",
                "purchase_expenditure_month": f"xe{g}",
            }
        )
        wide = wide.merge(part, on=["household_id", "data_year"], how="left", validate="one_to_one")
        fields = [f"qt{g}", f"qb{g}", f"qs{g}", f"qg{g}", f"qa{g}", f"xe{g}"]
        wide[fields] = wide[fields].fillna(0.0)
        if not np.allclose(wide[f"qt{g}"], wide[f"qb{g}"] + wide[f"qs{g}"] + wide[f"qg{g}"], rtol=1e-8, atol=1e-8):
            raise RuntimeError(f"Source quantities do not add up for group {g}")
        wide[f"uv{g}"] = wide[f"xe{g}"] / wide[f"qa{g}"]
        wide.loc[~(wide[f"xe{g}"].gt(0) & wide[f"qa{g}"].gt(0)), f"uv{g}"] = np.nan

    excluded_summary = (
        excluded.groupby(["item_code", "item_name"], as_index=False)
        .agg(
            household_years=("household_id", "size"),
            consumer_households=("total_consumed_month", lambda x: int((x > 0).sum())),
            total_quantity=("total_consumed_month", "sum"),
            mean_quantity=("total_consumed_month", "mean"),
        )
    )
    excluded_summary["participation"] = excluded_summary["consumer_households"] / excluded_summary["household_years"]
    group_def = pd.DataFrame(
        [
            {
                "group": g,
                "group_name": spec["name"],
                "item_count": len(spec["items"]),
                "item_codes": "; ".join(spec["items"]),
                "representative_price": "; ".join(spec["price_patterns"]),
                "physical_cap_jin_pc_month": spec["cap_pc_month"],
            }
            for g, spec in GROUPS.items()
        ]
    )
    return wide, excluded_summary, group_def


def parse_price_dictionary() -> pd.DataFrame:
    labels = pd.read_csv(RAW / "村表数据_已清洗_变量标签.csv", encoding="utf-8-sig")
    rows = []
    for row in labels.itertuples(index=False):
        parts = str(row.label).split("｜")
        if len(parts) != 3 or "价格" not in parts[0]:
            continue
        outlet = next((outlet for outlet in OUTLETS if parts[0].startswith(outlet)), None)
        if outlet is None:
            continue
        for g, spec in GROUPS.items():
            product = next((pattern for pattern in spec["price_patterns"] if pattern in parts[2]), None)
            if product is not None:
                rows.append({"var": row.var, "group": g, "outlet": outlet, "product": product, "label": row.label})
    result = pd.DataFrame(rows).drop_duplicates("var")
    missing = sorted(set(GROUPS) - set(result["group"]))
    if missing:
        raise RuntimeError(f"No representative price fields for groups {missing}")
    return result


def robust_direct_prices(village: pd.DataFrame, dictionary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    identity = ["village_id", "data_year", "town_id", "county_id", "province_id", "vilLat", "vilLon"]
    long = village.melt(id_vars=identity, value_vars=dictionary["var"], var_name="var", value_name="price")
    long = long.merge(dictionary, on="var", how="left", validate="many_to_one")
    long["price"] = numeric(long["price"])
    # Every representative-product field says "没有就填-99". A small set of
    # exports lost the minus sign; exact +99 is therefore a documented sentinel,
    # not a market-price upper-tail rule.
    long["positive_99_sentinel"] = long["price"].eq(99)
    sentinel_counts = long.groupby("group")["positive_99_sentinel"].sum().to_dict()
    long.loc[long["positive_99_sentinel"], "price"] = np.nan
    long.loc[long["price"].le(0), "price"] = np.nan
    independent = (
        long.groupby(identity + ["group", "outlet", "product"], as_index=False, dropna=False)
        .agg(price=("price", "median"))
    )
    direct = (
        independent.groupby(identity + ["group"], as_index=False, dropna=False)
        .agg(price_direct_raw=("price", "median"), independent_quote_count=("price", "count"))
    )
    audits = []
    cleaned_parts = []
    for g, group in direct.groupby("group"):
        part = group.copy()
        part["lnp"] = np.log(part["price_direct_raw"])
        py = part.groupby(["province_id", "data_year"])["lnp"].transform("median")
        ad = (part["lnp"] - py).abs()
        pmad = ad.groupby([part["province_id"], part["data_year"]]).transform("median")
        ym = part.groupby("data_year")["lnp"].transform("median")
        yad = (part["lnp"] - ym).abs()
        ymad = yad.groupby(part["data_year"]).transform("median")
        use_province = pmad.gt(0) & part["lnp"].notna()
        center = py.where(use_province, ym)
        mad = pmad.where(use_province, ymad)
        part["robust_z"] = (part["lnp"] - center) / (1.4826 * mad)
        town_median = part.groupby(["town_id", "data_year"])["lnp"].transform("median")
        town_n = part.groupby(["town_id", "data_year"])["lnp"].transform("count")
        part["local_corroborated"] = (town_n >= 2) & ((part["lnp"] - town_median).abs() <= math.log(1.25))
        part["five_mad_outlier"] = part["robust_z"].abs().gt(5) & ~((part["robust_z"] < 0) & part["local_corroborated"])
        part["price_direct"] = part["price_direct_raw"].mask(part["five_mad_outlier"])
        audits.append(
            {
                "group": int(g),
                "group_name": GROUPS[int(g)]["name"],
                "representative_variables": int(dictionary.loc[dictionary["group"].eq(g), "var"].nunique()),
                "positive_99_sentinels": int(sentinel_counts.get(g, 0)),
                "raw_direct_village_years": int(part["price_direct_raw"].notna().sum()),
                "five_mad_outliers": int(part["five_mad_outlier"].sum()),
                "clean_direct_village_years": int(part["price_direct"].notna().sum()),
                "direct_p01": part["price_direct"].quantile(0.01),
                "direct_p50": part["price_direct"].median(),
                "direct_p99": part["price_direct"].quantile(0.99),
            }
        )
        cleaned_parts.append(part[identity + ["group", "price_direct", "independent_quote_count", "five_mad_outlier", "local_corroborated"]])
    return pd.concat(cleaned_parts, ignore_index=True), pd.DataFrame(audits)


def haversine(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    radius = 6371.0088
    a1, a2 = np.radians(lat1), np.radians(lat2)
    dlat = a2 - a1
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(a1) * np.cos(a2) * np.sin(dlon / 2) ** 2
    return 2 * radius * np.arcsin(np.sqrt(a))


def household_prices(core: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dictionary = parse_price_dictionary()
    village_columns = ["xzcCode_clean", "data_year", "vilLat", "vilLon", *dictionary["var"].tolist()]
    village = pd.read_stata(RAW / "村表数据_已清洗.dta", columns=village_columns, convert_categoricals=False)
    village["village_id"] = village["xzcCode_clean"].astype("string").str.strip()
    village["town_id"] = village["village_id"].str.slice(0, 9)
    village["county_id"] = village["village_id"].str.slice(0, 6)
    village["province_id"] = village["village_id"].str.slice(0, 2)
    direct, quote_audit = robust_direct_prices(village, dictionary)
    targets = core[["village_id", "data_year", "town_id", "county_id", "province_id", "vilLat", "vilLon"]].drop_duplicates(["village_id", "data_year"])
    result = targets.copy()
    source_audits = []
    for g in GROUPS:
        donors = direct.loc[direct["group"].eq(g) & direct["price_direct"].notna()].copy()
        dprice = donors[["village_id", "data_year", "price_direct"]].rename(columns={"price_direct": f"p{g}"})
        part = targets.merge(dprice, on=["village_id", "data_year"], how="left", validate="one_to_one")
        part[f"p{g}_source"] = np.where(part[f"p{g}"].notna(), 1, np.nan)

        town = donors.groupby(["town_id", "data_year"], as_index=False)["price_direct"].median().rename(columns={"price_direct": "town_price"})
        part = part.merge(town, on=["town_id", "data_year"], how="left", validate="many_to_one")
        fill = part[f"p{g}"].isna() & part["town_price"].notna()
        part.loc[fill, f"p{g}"] = part.loc[fill, "town_price"]
        part.loc[fill, f"p{g}_source"] = 2

        for idx in part.index[part[f"p{g}"].isna() & part["vilLat"].notna() & part["vilLon"].notna()]:
            row = part.loc[idx]
            candidates = donors.loc[
                donors["data_year"].eq(row["data_year"])
                & donors["county_id"].eq(row["county_id"])
                & donors["vilLat"].notna()
                & donors["vilLon"].notna()
            ]
            if len(candidates):
                distance = haversine(float(row["vilLat"]), float(row["vilLon"]), candidates["vilLat"].to_numpy(float), candidates["vilLon"].to_numpy(float))
                chosen = candidates.iloc[int(np.nanargmin(distance))]
                part.at[idx, f"p{g}"] = chosen["price_direct"]
                part.at[idx, f"p{g}_source"] = 3

        for keys, code in [(["county_id", "data_year"], 4), (["province_id", "data_year"], 5), (["data_year"], 6)]:
            fallback = donors.groupby(keys, as_index=False)["price_direct"].median().rename(columns={"price_direct": "fallback_price"})
            part = part.merge(fallback, on=keys, how="left", validate="many_to_one")
            fill = part[f"p{g}"].isna() & part["fallback_price"].notna()
            part.loc[fill, f"p{g}"] = part.loc[fill, "fallback_price"]
            part.loc[fill, f"p{g}_source"] = code
            part = part.drop(columns="fallback_price")
        if part[f"p{g}"].isna().any() or part[f"p{g}"].le(0).any():
            raise RuntimeError(f"Unresolved price for group {g}")
        result = result.merge(part[["village_id", "data_year", f"p{g}", f"p{g}_source"]], on=["village_id", "data_year"], validate="one_to_one")
        counts = part[f"p{g}_source"].value_counts().to_dict()
        source_audits.append(
            {
                "group": g,
                "group_name": GROUPS[g]["name"],
                "target_village_years": len(part),
                "direct": int(counts.get(1, 0)),
                "town_median": int(counts.get(2, 0)),
                "nearest_county_village": int(counts.get(3, 0)),
                "county_median": int(counts.get(4, 0)),
                "province_median": int(counts.get(5, 0)),
                "year_median": int(counts.get(6, 0)),
            }
        )
    keep = ["village_id", "data_year"] + [field for g in GROUPS for field in [f"p{g}", f"p{g}_source"]]
    return result[keep], quote_audit, pd.DataFrame(source_audits)


def robust_upper_flag(frame: pd.DataFrame, value: pd.Series, floor: float) -> tuple[pd.Series, pd.Series]:
    positive = value.gt(0)
    logq = np.log1p(value.where(positive))
    province_median = logq.groupby([frame["province_id"], frame["data_year"]]).transform("median")
    ad = (logq - province_median).abs()
    province_mad = ad.groupby([frame["province_id"], frame["data_year"]]).transform("median")
    province_n = positive.groupby([frame["province_id"], frame["data_year"]]).transform("sum")
    year_median = logq.groupby(frame["data_year"]).transform("median")
    year_ad = (logq - year_median).abs()
    year_mad = year_ad.groupby(frame["data_year"]).transform("median")
    use_province = (province_n >= 10) & province_mad.gt(0)
    center = province_median.where(use_province, year_median)
    mad = province_mad.where(use_province, year_mad)
    z = (logq - center) / (1.4826 * mad)
    flag = (z > 5) & (value > floor)
    return flag.fillna(False), z


def finalize_analysis(core: pd.DataFrame, quantities: pd.DataFrame, prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame = core.merge(quantities, on=["household_id", "data_year"], validate="one_to_one")
    frame = frame.merge(prices, on=["village_id", "data_year"], validate="many_to_one")
    anomaly_rows = []
    physical_any = pd.Series(False, index=frame.index)
    tail_any = pd.Series(False, index=frame.index)
    for g, spec in GROUPS.items():
        total_pc = frame[f"qt{g}"] / frame["hhsize"]
        own_pc = frame[f"qs{g}"] / frame["hhsize"]
        physical = total_pc > spec["cap_pc_month"]
        total_tail, total_z = robust_upper_flag(frame, total_pc, spec["cap_pc_month"] / 2)
        own_tail, own_z = robust_upper_flag(frame, own_pc, spec["cap_pc_month"] / 2)
        frame[f"physical{g}"] = physical.astype(int)
        frame[f"tail_total{g}"] = total_tail.astype(int)
        frame[f"tail_own{g}"] = own_tail.astype(int)
        physical_any |= physical
        tail_any |= total_tail | own_tail
        anomaly_rows.append(
            {
                "group": g,
                "group_name": spec["name"],
                "physical_cap_jin_pc_month": spec["cap_pc_month"],
                "physical_flagged": int(physical.sum()),
                "total_five_mad_flagged": int(total_tail.sum()),
                "own_five_mad_flagged": int(own_tail.sum()),
                "max_total_jin_pc_month": float(total_pc.max()),
                "max_total_z": float(total_z.max()),
                "max_own_z": float(own_z.max()),
            }
        )
        frame[f"lnp{g}"] = np.log(frame[f"p{g}"])
        frame[f"v{g}"] = frame[f"p{g}"] * frame[f"qt{g}"]
    frame["physical_any"] = physical_any.astype(int)
    frame["tail_any"] = tail_any.astype(int)
    frame["sample_main"] = (~physical_any & ~tail_any).astype(int)
    value_cols = [f"v{g}" for g in GROUPS]
    frame["food_exp"] = frame[value_cols].sum(axis=1)
    frame["ln_foodexp"] = np.log(frame["food_exp"].where(frame["food_exp"] > 0))
    for g in GROUPS:
        frame[f"s{g}"] = frame[f"v{g}"] / frame["food_exp"]
    frame["share_sum"] = frame[[f"s{g}" for g in GROUPS]].sum(axis=1)
    frame["food_exp_pc"] = frame["food_exp"] / frame["hhsize"]
    frame["food_to_total_exp"] = frame["food_exp"] / frame["total_exp_monthly"]
    required = [
        "hhsize", "ln_income", "inv_income", "ln_foodexp", "child_ratio",
        "elderly_ratio", "female_head", "head_no_education",
        "head_primary_education", "age_missing", "female_head_missing",
        "education_missing", *[f"lnp{g}" for g in GROUPS],
    ]
    complete = frame[required].notna().all(axis=1) & frame["food_exp"].gt(0)
    frame["sample_model"] = (frame["sample_main"].eq(1) & complete).astype(int)
    if not np.allclose(frame.loc[frame["food_exp"].gt(0), "share_sum"], 1, atol=1e-8):
        raise RuntimeError("Budget shares do not add to one")

    sample_audit = pd.DataFrame(
        [
            {"stage": "all household-years", "observations": len(frame)},
            {"stage": "positive nine-group expenditure", "observations": int(frame["food_exp"].gt(0).sum())},
            {"stage": "within physical caps", "observations": int((~physical_any).sum())},
            {"stage": "physical caps plus five-MAD total/own tails", "observations": int(frame["sample_main"].sum())},
            {"stage": "complete IV model sample", "observations": int(frame["sample_model"].sum())},
        ]
    )
    descriptives = []
    for sample_name, mask in [("all", pd.Series(True, index=frame.index)), ("model", frame["sample_model"].eq(1))]:
        subset = frame.loc[mask]
        for g, spec in GROUPS.items():
            quantity = subset[f"qt{g}"]
            positive = quantity[quantity > 0]
            descriptives.append(
                {
                    "sample": sample_name,
                    "group": g,
                    "group_name": spec["name"],
                    "N": len(subset),
                    "participation": float(quantity.gt(0).mean()),
                    "quantity_mean_all": float(quantity.mean()),
                    "quantity_p50_consumers": float(positive.median()) if len(positive) else np.nan,
                    "quantity_p90_consumers": float(positive.quantile(0.9)) if len(positive) else np.nan,
                    "quantity_p99_consumers": float(positive.quantile(0.99)) if len(positive) else np.nan,
                    "price_mean": float(subset[f"p{g}"].mean()),
                    "price_p50": float(subset[f"p{g}"].median()),
                    "budget_share_mean": float(subset[f"s{g}"].mean()),
                    "budget_share_p50": float(subset[f"s{g}"].median()),
                }
            )
    return frame, pd.DataFrame(anomaly_rows), pd.DataFrame(descriptives), sample_audit


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    core = household_core()
    quantities, excluded, group_def = aggregate_quantities(core)
    prices, quote_audit, source_audit = household_prices(core)
    analysis, anomaly_audit, descriptives, sample_audit = finalize_analysis(core, quantities, prices)

    model_controls = [
        "hhsize", "child_ratio", "elderly_ratio", "female_head",
        "head_no_education", "head_primary_education", "age_missing",
        "female_head_missing", "education_missing",
        *[column for column in analysis.columns if column.startswith("province_") and column != "province_id"],
    ]
    model_rows = analysis.loc[analysis["sample_model"].eq(1)]
    design_audit = []
    for specification, controls in [
        ("province_FE_plus_year", [*model_controls, "year_2024"]),
        ("final_province_FE", model_controls),
    ]:
        matrix = np.column_stack([np.ones(len(model_rows)), model_rows[controls].to_numpy(float)])
        design_audit.append(
            {
                "specification": specification,
                "columns_including_constant": matrix.shape[1],
                "matrix_rank": int(np.linalg.matrix_rank(matrix)),
                "full_column_rank": int(np.linalg.matrix_rank(matrix) == matrix.shape[1]),
                "controls": "; ".join(controls),
            }
        )

    analysis.to_stata(DATA / "nine_group_analysis.dta", write_index=False, version=118)
    group_def.to_csv(OUT / "group_definition.csv", index=False, encoding="utf-8-sig")
    excluded.to_csv(OUT / "excluded_item_summary.csv", index=False, encoding="utf-8-sig")
    quote_audit.to_csv(OUT / "price_quote_audit.csv", index=False, encoding="utf-8-sig")
    source_audit.to_csv(OUT / "price_source_audit.csv", index=False, encoding="utf-8-sig")
    anomaly_audit.to_csv(OUT / "quantity_anomaly_audit.csv", index=False, encoding="utf-8-sig")
    descriptives.to_csv(OUT / "nine_group_descriptives.csv", index=False, encoding="utf-8-sig")
    sample_audit.to_csv(OUT / "sample_flow.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(design_audit).to_csv(OUT / "design_matrix_audit.csv", index=False, encoding="utf-8-sig")
    print(f"Built nine-group analysis data: {len(analysis):,} rows; model sample {analysis['sample_model'].sum():,}")


if __name__ == "__main__":
    main()
