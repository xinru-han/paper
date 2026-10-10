#!/usr/bin/env python3
"""Build consistent 8/10-good micro demand data, preserving zeros and price provenance."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = Path("/root/data/数据/食物消费调查数据/处理后的data")
ITEM_ROOT = Path("/root/data/Paper/食物消费数据/paper0-EASI/item_level_food_descriptives/outputs")
DATA, OUT = ROOT / "data", ROOT / "outputs"
KEY = ["household_id", "data_year"]
VKEY = ["village_id", "data_year"]
IDENTITY = [*VKEY, "town_id", "county_id", "province_id", "vilLat", "vilLon"]
FLOW = ["purchase_consumed_month", "own_consumed_month", "gift_consumed_month", "total_consumed_month", "purchase_acquired_month", "purchase_expenditure_month"]
GROUPS = {
    1: ("主食及加工品", ["zhushi_1", "zhushi_2_1", "zhushi_3", "zhushi_3_1", "zhushi_5", "zhushi_6", "zhushi_7", "zhushi_1_1", "zhushi_2", "zhushi_2_2", "zhushi_8"], ["常吃的面粉单价", "常吃的大米单价"]),
    2: ("猪肉及排骨", ["roulei_1", "roulei_2"], ["肥瘦猪肉单价"]),
    3: ("其他畜禽肉及肉制品", ["roulei_3", "roulei_4", "roulei_9", "roulei_5", "roulei_6", "roulei_7", "roulei_8", "xiancai_3", "roulei_11", "roulei_12"], []),
    4: ("蛋类及制品", ["danlei_1", "danlei_2", "danlei_3"], ["普通鸡蛋的单价"]),
    5: ("奶类", ["nailei_1", "nailei_2", "nailei_3"], ["普通盒装纯牛奶的单价"]),
    6: ("水产品及制品", ["shuichan_1", "roulei_13"], ["鲤鱼的单价", "带鱼的单价"]),
    7: ("油脂", ["youzhi_1", "youzhi_2", "youzhi_3", "youzhi_4", "youzhi_5", "youzhi_6"], ["常吃菜籽油的单价"]),
    8: ("蔬菜及制品", ["shucai_1", "shucai_2", "shucai_3", "shucai_4", "shucai_5", "shucai_6", "shucai_7", "shucai_8", "shucai_9", "xiancai_1", "xiancai_2"], ["青菜的单价", "白菜的单价"]),
    9: ("水果及水果制品", ["shuiguo_1", "shuiguo_2", "shuiguo_3", "shuiguo_7", "shuiguo_4", "shuiguo_5"], ["普通苹果的单价", "常吃桔子的单价"]),
    10: ("干果坚果", ["shuiguo_6"], ["常吃瓜子（葵花子）的单价"]),
}
MERGE8 = {1: [1], 2: [2, 3], 3: [4], 4: [5], 5: [6], 6: [7], 7: [8], 8: [9, 10]}
NAME8 = ["主食及加工品", "畜禽肉及肉制品", "蛋类及制品", "奶类", "水产品及制品", "油脂", "蔬菜及制品", "水果干果及制品"]
CAP8 = [120.0, 60.0, 30.0, 120.0, 60.0, 21.0, 180.0, 180.0]
FAMILY_NAMES = {0: "关系不完整或有冲突", 1: "单人家庭", 2: "夫妻家庭", 3: "核心家庭", 4: "扩展及其他家庭"}
AGE_NAMES = {0: "年龄信息不完整", 1: "无儿童无老人", 2: "有儿童无老人", 3: "无儿童有老人", 4: "有儿童有老人"}
ITEM_GROUP = {item: g for g, (_, items, _) in GROUPS.items() for item in items}


def numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype(float)


def core_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    roster = [f"family1_{m:02d}_HA{k}" for m in range(1, 9) for k in [1, 2, 3, 4]]
    edus = [f"family2_{m:02d}_HA10" for m in range(1, 9)]
    income_fields = [f"zhuanyishouru_{k}" for k in [1, 3, 4, 5, 6, 7, 8]] + [f"caichanshouru_{k}" for k in range(1, 6)] + ["shengchanshouru_3", "shengchanshouru_4", "jingyingshouru_1", "gongzishouru_1", "gongzishouru_2"]
    cols = ["nhCode", "data_year", "prov", "provn", "vilLat", "vilLon", "HA0", "hh_income_sum", "agri_business_income", "total_income", "total_income_w", "annual_expense_total", "monthly_expense_total", *roster, *edus, *income_fields]
    f = pd.read_stata(RAW / "户表数据_已清洗.dta", columns=cols, convert_categoricals=False)
    f["household_id"] = f["nhCode"].astype(str).str.strip()
    f["village_id"] = f["household_id"].str[:12]
    f["town_id"], f["county_id"], f["province_id"] = f["village_id"].str[:9], f["village_id"].str[:6], f["village_id"].str[:2]
    if f.duplicated(KEY).any():
        raise ValueError("Nonunique household-year key")
    if not f.household_id.str.fullmatch(r"\d{14,20}").all():
        raise ValueError("Household IDs do not have the expected text format")
    provmap = f.loc[f.provn.ne("")].groupby("province_id").provn.first()
    f["province_name"] = f.provn.replace("", np.nan).fillna(f.province_id.map(provmap))
    rel = np.column_stack([numeric(f[f"family1_{m:02d}_HA1"]).to_numpy() for m in range(1, 9)])
    birth = []
    for m in range(1, 9):
        solar = pd.to_numeric(f[f"family1_{m:02d}_HA3"].astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")
        lunar = pd.to_numeric(f[f"family1_{m:02d}_HA4"].astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")
        birth.append(solar.fillna(lunar).to_numpy())
    age = f.data_year.to_numpy()[:, None] - np.column_stack(birth)
    age[(age < 0) | (age > 110)] = np.nan
    present = np.isfinite(rel) | np.isfinite(age)
    roster_n = present.sum(axis=1)
    reported = numeric(f.HA0)
    f["hhsize_reported_valid"] = reported.between(1, 20) & reported.eq(reported.round())
    f["hhsize"] = reported.where(f.hhsize_reported_valid, pd.Series(roster_n, index=f.index).where(roster_n > 0))
    f["roster_n"] = roster_n
    f["roster_complete"] = (roster_n == f.hhsize) & (np.isin(rel, np.arange(1, 11)).sum(axis=1) == roster_n) & ((rel == 1).sum(axis=1) == 1)
    f["age_complete"] = (np.isfinite(age).sum(axis=1) == f.hhsize)
    f["children_n"], f["elderly_n"] = (age < 15).sum(axis=1), (age >= 65).sum(axis=1)
    f["child_ratio"], f["elderly_ratio"] = f.children_n / f.hhsize, f.elderly_n / f.hhsize
    f["family_type"] = 0
    complete = f.roster_complete
    f.loc[complete & f.hhsize.eq(1), "family_type"] = 1
    couple = complete & f.hhsize.eq(2) & (np.isin(rel, [1, 2]).sum(axis=1) == 2)
    f.loc[couple, "family_type"] = 2
    nuclear = complete & f.hhsize.ge(2) & (np.isin(rel, [1, 2, 4]).sum(axis=1) == roster_n) & ((rel == 4).sum(axis=1) > 0)
    f.loc[nuclear, "family_type"] = 3
    f.loc[complete & f.family_type.eq(0), "family_type"] = 4
    f["family_type_name"] = f.family_type.map(FAMILY_NAMES)
    f["age_family_type"] = np.where(f.age_complete, 1 + f.children_n.gt(0).astype(int) + 2 * f.elderly_n.gt(0).astype(int), 0)
    f["age_family_name"] = f.age_family_type.map(AGE_NAMES)
    female, edu = np.full(len(f), np.nan), np.full(len(f), np.nan)
    for m in range(1, 9):
        head = rel[:, m - 1] == 1
        sex = numeric(f[f"family1_{m:02d}_HA2"])
        school = numeric(f[f"family2_{m:02d}_HA10"])
        fill = head & np.isnan(female) & sex.isin([0, 1])
        female[fill] = sex[fill].eq(0).astype(float)
        fill = head & np.isnan(edu) & school.between(1, 5)
        edu[fill] = school[fill]
    f["female_head_missing"], f["education_missing"] = np.isnan(female).astype(int), np.isnan(edu).astype(int)
    f["female_head"] = np.nan_to_num(female)
    f["head_education"] = edu
    f = f.copy()
    f["income_household_raw_annual"] = numeric(f.total_income)
    f["income_household_annual"] = numeric(f.total_income_w)
    f["income_reference_year"] = f.data_year - 1
    income_components = f[income_fields].apply(numeric)
    f["income_component_reported_n"] = income_components.notna().sum(axis=1)
    f["income_components_sum"] = income_components.sum(axis=1)
    f["income_hh_sum_upstream"] = numeric(f.hh_income_sum)
    f["agri_income_upstream"] = numeric(f.agri_business_income)
    f["income_hh_sum_check"] = np.isclose(f.income_components_sum, f.income_hh_sum_upstream).astype(int)
    f["income_total_sum_check"] = np.isclose(f.income_hh_sum_upstream + f.agri_income_upstream, f.income_household_raw_annual).astype(int)
    f["income_source_changed"] = (~f.total_income.eq(f.total_income_w)).astype(int)
    f["income_pc_annual"] = f.income_household_annual.where(f.income_household_annual > 0) / f.hhsize
    f["income_pc_monthly"] = f.income_pc_annual / 12
    f["ln_income_pc"] = np.log(f.income_pc_annual)
    f["total_exp_monthly"] = numeric(f.monthly_expense_total).where(numeric(f.monthly_expense_total) > 0)
    f["total_exp_pc_monthly"] = f.total_exp_monthly / f.hhsize
    f["village_cluster"] = pd.factorize(f.village_id + "_" + f.data_year.astype(str), sort=True)[0] + 1
    keep = [*IDENTITY, "household_id", "province_name", "hhsize", "hhsize_reported_valid", "roster_n", "roster_complete", "age_complete", "children_n", "elderly_n", "child_ratio", "elderly_ratio", "family_type", "family_type_name", "age_family_type", "age_family_name", "female_head", "female_head_missing", "head_education", "education_missing", "income_household_raw_annual", "income_household_annual", "income_reference_year", "income_source_changed", "income_pc_annual", "income_pc_monthly", "ln_income_pc", "income_component_reported_n", "income_components_sum", "income_hh_sum_upstream", "agri_income_upstream", "income_hh_sum_check", "income_total_sum_check", "total_exp_monthly", "total_exp_pc_monthly", "village_cluster"]
    audit = pd.DataFrame([{"check": "household_rows", "value": len(f)}, {"check": "reported_size_invalid", "value": int((~f.hhsize_reported_valid).sum())}, {"check": "incomplete_relationship_roster", "value": int((~f.roster_complete).sum())}, {"check": "incomplete_age_roster", "value": int((~f.age_complete).sum())}, {"check": "income_upstream_changed", "value": int(f.income_source_changed.sum())}, {"check": "income_nonpositive", "value": int(f.income_household_annual.le(0).sum())}, {"check": "income_17_component_sum_mismatch", "value": int(f.income_hh_sum_check.eq(0).sum())}, {"check": "income_total_sum_mismatch", "value": int(f.income_total_sum_check.eq(0).sum())}, {"check": "income_all_components_unreported", "value": int(f.income_component_reported_n.eq(0).sum())}])
    return f[keep].copy(), audit


def robust_clean(price: pd.DataFrame, value: str, by: str) -> pd.DataFrame:
    p = price.copy()
    p["lnp"] = np.log(p[value].where(p[value] > 0))
    keys = [p[by], p.province_id, p.data_year]
    median = p.lnp.groupby(keys).transform("median")
    mad = (p.lnp - median).abs().groupby(keys).transform("median")
    ym = p.lnp.groupby([p[by], p.data_year]).transform("median")
    ymad = (p.lnp - ym).abs().groupby([p[by], p.data_year]).transform("median")
    center, scale = median.where(mad > 0, ym), mad.where(mad > 0, ymad)
    p["robust_z"] = (p.lnp - center) / (1.4826 * scale)
    tm = p.lnp.groupby([p[by], p.town_id, p.data_year]).transform("median")
    tn = p.lnp.groupby([p[by], p.town_id, p.data_year]).transform("count")
    p["corroborated"] = tn.ge(2) & (p.lnp - tm).abs().le(math.log(1.25))
    p["outlier"] = p.robust_z.abs().gt(5) & ~(p.robust_z.lt(0) & p.corroborated)
    p["price"] = p[value].mask(p.outlier)
    return p.drop(columns="lnp")


def village_price_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    labels = pd.read_csv(RAW / "村表数据_已清洗_变量标签.csv")
    mapping = pd.read_csv(ITEM_ROOT / "household_community_price_mapping.csv")
    cat_to_item = mapping.loc[mapping.item_code.isin(ITEM_GROUP)].set_index("community_category").item_code.to_dict()
    rep, endpoints = [], []
    for row in labels.itertuples(index=False):
        parts = str(row.label).split("｜")
        if len(parts) != 3 or "价格" not in parts[0]:
            continue
        if parts[2] in {"最高单价", "最低单价"} and parts[1] in cat_to_item:
            endpoints.append({"var": row.var, "item_code": cat_to_item[parts[1]], "outlet": parts[0], "endpoint": "high" if parts[2] == "最高单价" else "low"})
        for g, (_, _, patterns) in GROUPS.items():
            product = next((s for s in patterns if s in parts[2]), None)
            if product:
                rep.append({"var": row.var, "group": g, "outlet": parts[0].split("价格")[0], "product": product})
    rep, endpoints = pd.DataFrame(rep), pd.DataFrame(endpoints)
    cols = list(dict.fromkeys([*rep["var"], *endpoints["var"]]))
    village = pd.read_stata(RAW / "村表数据_已清洗.dta", columns=["xzcCode_clean", "data_year", "vilLat", "vilLon", *cols], convert_categoricals=False)
    village = village.copy()
    village["village_id"] = village.xzcCode_clean.astype(str).str.strip()
    village["town_id"], village["county_id"], village["province_id"] = village.village_id.str[:9], village.village_id.str[:6], village.village_id.str[:2]
    if village.duplicated(VKEY).any():
        raise ValueError("Nonunique village-year key")
    rl = village.melt(id_vars=IDENTITY, value_vars=rep["var"], var_name="var", value_name="raw_price").merge(rep, on="var", validate="many_to_one")
    rl["raw_price"] = numeric(rl.raw_price)
    rl["sentinel99"] = rl.raw_price.eq(99)
    rl["valid_price"] = rl.raw_price.where(rl.raw_price.gt(0) & ~rl.sentinel99)
    # Repeated mp fields carry the same named product even when a row names a
    # different category. Collapse them before treating an outlet as a quote.
    rd = rl.groupby(IDENTITY + ["group", "outlet", "product"], as_index=False, dropna=False).valid_price.median()
    rd = rd.groupby(IDENTITY + ["group"], as_index=False, dropna=False).valid_price.median()
    rd = robust_clean(rd, "valid_price", "group")
    el = village.melt(id_vars=IDENTITY, value_vars=endpoints["var"], var_name="var", value_name="raw_price").merge(endpoints, on="var", validate="many_to_one")
    el["raw_price"] = numeric(el.raw_price)
    el["value"] = el.raw_price.where(el.raw_price.gt(0))
    ep = el.groupby(IDENTITY + ["item_code", "outlet", "endpoint"], dropna=False).value.median().unstack("endpoint").reset_index()
    ep["reversed"] = ep.high.lt(ep.low)
    ep["both_valid"] = ep.high.notna() & ep.low.notna() & ~ep.reversed
    ep["range_proxy"] = np.sqrt(ep.high * ep.low).where(ep.both_valid)
    ed = ep.groupby(IDENTITY + ["item_code"], as_index=False, dropna=False).range_proxy.median()
    ed = robust_clean(ed, "range_proxy", "item_code")
    return rd, ed, rl, ep


def impute_price(targets: pd.DataFrame, donors: pd.DataFrame, allow_unresolved: bool = False) -> pd.DataFrame:
    part = targets.merge(donors[VKEY + ["price"]], on=VKEY, how="left", validate="one_to_one")
    part["source"] = np.where(part.price.notna(), 1, np.nan)
    for keys, code in [(["town_id", "data_year"], 2), (["county_id", "data_year"], 4), (["province_id", "data_year"], 5), (["data_year"], 6)]:
        if code == 4:
            for idx in part.index[part.price.isna() & part.vilLat.notna() & part.vilLon.notna()]:
                row = part.loc[idx]
                candidates = donors.loc[donors.data_year.eq(row.data_year) & donors.county_id.eq(row.county_id) & donors.vilLat.notna() & donors.vilLon.notna()]
                if len(candidates):
                    lat1, lat2 = math.radians(row.vilLat), np.radians(candidates.vilLat.to_numpy(float))
                    dl = np.radians(candidates.vilLon.to_numpy(float) - row.vilLon)
                    a = np.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * np.cos(lat2) * np.sin(dl / 2) ** 2
                    distance = 6371.0088 * 2 * np.arcsin(np.sqrt(a))
                    chosen = candidates.iloc[int(np.nanargmin(distance))]
                    part.at[idx, "price"], part.at[idx, "source"] = chosen.price, 3
        tab = donors.groupby(keys, as_index=False).price.median().rename(columns={"price": "fallback"})
        part = part.merge(tab, on=keys, how="left", validate="many_to_one")
        fill = part.price.isna() & part.fallback.notna()
        part.loc[fill, "price"], part.loc[fill, "source"] = part.loc[fill, "fallback"], code
        part = part.drop(columns="fallback")
    if not allow_unresolved and (part.price.isna().any() or part.price.le(0).any()):
        raise ValueError("Unresolved positive community price")
    return part[VKEY + ["price", "source"]]


def component_prices(core: pd.DataFrame) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    rd, ed, rl, ep = village_price_inputs()
    targets = core[IDENTITY].drop_duplicates(VKEY)
    rep_filled = {}
    for g in GROUPS:
        if g == 3:
            continue
        donors = rd.loc[rd.group.eq(g) & rd.price.notna()]
        rep_filled[g] = impute_price(targets, donors)
    range_filled = {}
    for item in ITEM_GROUP:
        donors = ed.loc[ed.item_code.eq(item) & ed.price.notna()]
        if not len(donors):
            raise ValueError(f"No valid range prices for {item}")
        range_filled[item] = impute_price(targets, donors, allow_unresolved=True)
    for item in GROUPS[3][1]:
        missing = range_filled[item].price.isna()
        if not missing.any():
            continue
        proxy = {"roulei_8": "roulei_6"}.get(item)
        if proxy is None:
            raise ValueError(f"No documented cross-commodity fallback for {item}")
        paired = range_filled[item].merge(range_filled[proxy], on=VKEY, suffixes=("_own", "_proxy"))
        relative_scale = float((paired.price_own / paired.price_proxy).median())
        range_filled[item].loc[missing, "price"] = range_filled[proxy].loc[missing, "price"] * relative_scale
        range_filled[item].loc[missing, "source"] = 7
    # A single global scale adjustment aligns range proxies to the pork
    # representative-price convention without copying pork spatial variation.
    pork_pair = rep_filled[2].merge(range_filled["roulei_1"], on=VKEY, suffixes=("_rep", "_range"))
    calibration = float((pork_pair.price_rep / pork_pair.price_range).median())
    rows, scale_rows, source_rows = [], [], []
    for item, g in ITEM_GROUP.items():
        endpoint = range_filled[item]
        if g == 3:
            p = endpoint.copy()
            p["price"] *= calibration
            method, factor = "calibrated_quality_range_proxy", calibration
        else:
            anchor = rep_filled[g]
            joined = endpoint.merge(anchor, on=VKEY, suffixes=("_range", "_rep"))
            factor = float((joined.price_range / joined.price_rep).median())
            p = anchor.copy()
            p["price"] *= factor
            method = "representative_anchor_fixed_item_scale"
        p["item_code"], p["group10"], p["price_method"] = item, g, method
        rows.append(p)
        count = p.source.value_counts()
        source_rows.append({"item_code": item, "group10": g, "method": method, "village_years": len(p), "direct": int(count.get(1, 0)), "town_median": int(count.get(2, 0)), "nearest_county": int(count.get(3, 0)), "county_median": int(count.get(4, 0)), "province_median": int(count.get(5, 0)), "year_median": int(count.get(6, 0)), "cross_commodity_proxy": int(count.get(7, 0)), "unique_prices": p.price.nunique()})
        scale_rows.append({"item_code": item, "group10": g, "method": method, "fixed_scale": factor})
    result = pd.concat(rows, ignore_index=True)
    result.rename(columns={"price": "item_price", "source": "item_price_source"}, inplace=True)
    quote_audit = []
    for item, group in ed.groupby("item_code"):
        pair = ep.loc[ep.item_code.eq(item)]
        quote_audit.append({"item_code": item, "valid_range_pairs": int(pair.both_valid.sum()), "reversed_pairs": int(pair.reversed.sum()), "positive_low_under_0_1": int(pair.low.between(0, 0.1, inclusive="neither").sum()), "positive_low_under_0_5": int(pair.low.between(0, 0.5, inclusive="neither").sum()), "range_direct_raw": int(group.range_proxy.notna().sum()), "range_five_mad_flagged": int(group.outlier.sum()), "range_direct_clean": int(group.price.notna().sum())})
    rep_audit = rd.groupby("group").agg(direct_raw=("valid_price", "count"), outlier=("outlier", "sum"), direct_clean=("price", "count")).reset_index()
    rep_audit["positive99_sentinels"] = rep_audit.group.map(rl.groupby("group").sentinel99.sum())
    return result, [pd.DataFrame(scale_rows), pd.DataFrame(source_rows), pd.DataFrame(quote_audit), rep_audit]


def upper_flag(core: pd.DataFrame, value: pd.Series, floor: float) -> pd.Series:
    logq = np.log1p(value.where(value > 0))
    keys = [core.province_id, core.data_year]
    med = logq.groupby(keys).transform("median")
    mad = (logq - med).abs().groupby(keys).transform("median")
    ym = logq.groupby(core.data_year).transform("median")
    ymad = (logq - ym).abs().groupby(core.data_year).transform("median")
    z = (logq - med.where(mad > 0, ym)) / (1.4826 * mad.where(mad > 0, ymad))
    return (z.gt(5) & value.gt(floor)).fillna(False)


def build_system(core: pd.DataFrame, long: pd.DataFrame, prices: pd.DataFrame, membership: dict[int, list[int]], names: list[str], sample: pd.Series, reference_sample: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    f = core.copy()
    weights, desc = [], []
    membermap = {c: g for g, children in membership.items() for c in children}
    q = long.copy()
    q["group"] = q.group10.map(membermap)
    ref = q.merge(core.loc[reference_sample, KEY], on=KEY, how="inner", validate="many_to_one")
    ref["quantity_pc"] = ref.total_consumed_month / ref.hhsize
    base = ref.groupby("item_code").quantity_pc.mean()
    p = prices.copy()
    p["group"] = p.group10.map(membermap)
    p["base_quantity"] = p.item_code.map(base)
    denom = p.groupby(VKEY + ["group"]).base_quantity.transform("sum")
    p["basket_weight"] = p.base_quantity / denom
    p["weighted_price"] = p.item_price * p.basket_weight
    price_group = p.groupby(VKEY + ["group"], as_index=False).agg(price=("weighted_price", "sum"), worst_price_source=("item_price_source", "max"))
    q["value"] = q.total_consumed_month * q.item_price
    q["value_purchase"] = q.purchase_consumed_month * q.item_price
    q["value_own"] = q.own_consumed_month * q.item_price
    q["value_gift"] = q.gift_consumed_month * q.item_price
    collapsed = q.groupby(KEY + ["group"], as_index=False).agg(value=("value", "sum"), quantity_jin=("total_consumed_month", "sum"), value_purchase=("value_purchase", "sum"), value_own=("value_own", "sum"), value_gift=("value_gift", "sum"), purchase_exp=("purchase_expenditure_month", "sum"))
    for g in membership:
        cp = collapsed.loc[collapsed.group.eq(g)].drop(columns="group")
        vp = price_group.loc[price_group.group.eq(g)].drop(columns="group")
        f = f.merge(cp, on=KEY, validate="one_to_one").merge(vp, on=VKEY, validate="many_to_one")
        new_columns = {
            f"v{g}": f["value"] / f.hhsize,
            f"p{g}": f["price"],
            f"q{g}": f["value"] / f.hhsize / f["price"],
            f"qraw{g}": f["quantity_jin"] / f.hhsize,
            f"p_source{g}": f["worst_price_source"],
        }
        for label in ["value_purchase", "value_own", "value_gift", "purchase_exp"]:
            new_columns[f"{label}{g}"] = f[label] / f.hhsize
        f = pd.concat([f.drop(columns=["value", "price", "quantity_jin", "worst_price_source", "value_purchase", "value_own", "value_gift", "purchase_exp"]), pd.DataFrame(new_columns, index=f.index)], axis=1).copy()
        part = p.loc[p.group.eq(g), ["item_code", "base_quantity", "basket_weight"]].drop_duplicates("item_code")
        part["group"], part["group_name"] = g, names[g - 1]
        weights.append(part)
    f["food_exp_pc_monthly"] = f[[f"v{g}" for g in membership]].sum(axis=1)
    f["food_exp_pc_annual"] = 12 * f.food_exp_pc_monthly
    f["food_exp_household_monthly"] = f.food_exp_pc_monthly * f.hhsize
    f["sample_main"] = sample.astype(int)
    f["sample_model"] = (sample & f.food_exp_pc_monthly.gt(0) & f.income_pc_monthly.gt(0) & f.hhsize.gt(0)).astype(int)
    p01, p99 = f.loc[f.sample_model.eq(1), "income_pc_annual"].quantile([.01, .99])
    f["income_percentile_tail"] = (~f.income_pc_annual.between(p01, p99)).astype(int)
    f["sample_income_supported"] = (f.sample_model.eq(1) & f.income_pc_annual.between(p01, p99)).astype(int)
    f["family_model_sample"] = (f.sample_model.eq(1) & f.family_type.gt(0)).astype(int)
    f["income_expenditure_ratio"] = f.food_exp_pc_monthly / f.income_pc_monthly
    f["income_accounting_mismatch"] = f.income_expenditure_ratio.gt(20).astype(int)
    f["food_total_exp_ratio"] = f.food_exp_pc_monthly / f.total_exp_pc_monthly
    f["ln_foodexp_pc"] = np.log(f.food_exp_pc_monthly.where(f.food_exp_pc_monthly > 0))
    for g in membership:
        f[f"s{g}"] = f[f"v{g}"] / f.food_exp_pc_monthly
        f[f"d{g}"] = f[f"q{g}"].gt(0).astype(int)
        f[f"lnp{g}"] = np.log(f[f"p{g}"])
        for sample_name, mask in [("all", pd.Series(True, index=f.index)), ("model", f.sample_model.eq(1))]:
            x = f.loc[mask]
            desc.append({"system_goods": len(membership), "sample": sample_name, "group": g, "group_name": names[g - 1], "N": len(x), "participation": x[f"d{g}"].mean(), "raw_jin_pc_mean": x[f"qraw{g}"].mean(), "equivalent_basket_pc_mean": x[f"q{g}"].mean(), "price_mean": x[f"p{g}"].mean(), "price_p01": x[f"p{g}"].quantile(.01), "price_p50": x[f"p{g}"].median(), "price_p99": x[f"p{g}"].quantile(.99), "share_mean": x[f"s{g}"].mean(), "value_pc_monthly_mean": x[f"v{g}"].mean(), "unique_prices": x[f"p{g}"].nunique()})
    shares = f.loc[f.food_exp_pc_monthly.gt(0), [f"s{g}" for g in membership]].sum(axis=1)
    if not np.allclose(shares, 1, atol=1e-12):
        raise ValueError("Budget shares do not sum to one")
    baseline = f.loc[f.sample_model.eq(1)]
    log_index = np.zeros(len(f))
    for g in membership:
        weight = float(baseline[f"s{g}"].mean())
        base_price = float(np.exp(np.log(baseline[f"p{g}"]).mean()))
        f[f"pn{g}"] = f[f"p{g}"] / base_price
        log_index += weight * np.log(f[f"pn{g}"])
    f["food_price_index"] = np.exp(log_index)
    f["food_budget_pc_month"] = f.food_exp_pc_monthly
    f["income_pc_month"] = f.income_pc_monthly
    return f, pd.concat(weights, ignore_index=True), pd.DataFrame(desc)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    core, core_audit = core_data()
    long = pd.read_stata(ITEM_ROOT / "household_item_long.dta", convert_categoricals=False)
    long = long.loc[long.item_code.isin(ITEM_GROUP)].copy()
    long["group10"] = long.item_code.map(ITEM_GROUP)
    if long.duplicated(KEY + ["item_code"]).any():
        raise ValueError("Duplicate household-year-item")
    long = long.merge(core[KEY + ["hhsize", "province_id"]], on=KEY, validate="many_to_one")
    if len(long) != len(core) * len(ITEM_GROUP):
        raise ValueError("Missing included household item records")
    if not long.module_observed.eq(1).all():
        raise ValueError("Missing modules cannot be encoded as zero consumption")
    if not np.allclose(long.total_consumed_month, long.purchase_consumed_month + long.own_consumed_month + long.gift_consumed_month, rtol=1e-8, atol=1e-8):
        raise ValueError("Purchase/own/gift identity fails")
    flag = pd.Series(False, index=core.index)
    anomaly = []
    for g8, children in MERGE8.items():
        part = long.loc[long.group10.isin(children)].groupby(KEY)[["total_consumed_month", "own_consumed_month"]].sum().reset_index()
        a = core.merge(part, on=KEY, validate="one_to_one")
        total, own = a.total_consumed_month / a.hhsize, a.own_consumed_month / a.hhsize
        physical = total > CAP8[g8 - 1]
        tail_total, tail_own = upper_flag(core, total, CAP8[g8 - 1] / 2), upper_flag(core, own, CAP8[g8 - 1] / 2)
        flag |= physical | tail_total | tail_own
        anomaly.append({"group8": g8, "group_name": NAME8[g8 - 1], "cap_jin_pc_month": CAP8[g8 - 1], "physical_flag": int(physical.sum()), "tail_total_flag": int(tail_total.sum()), "tail_own_flag": int(tail_own.sum())})
    core["quantity_anomaly"] = flag.astype(int)
    log_income = core.ln_income_pc
    keys = [core.province_id, core.data_year]
    income_center = log_income.groupby(keys).transform("median")
    income_mad = (log_income - income_center).abs().groupby(keys).transform("median")
    core["income_log_mad_z"] = (log_income - income_center) / (1.4826 * income_mad)
    core["income_log_mad_outlier"] = core.income_log_mad_z.abs().gt(5).astype(int)
    sample = ~flag
    reference_sample = sample & core.income_pc_monthly.gt(0)
    prices, audits = component_prices(core)
    long["village_id"] = long.household_id.str[:12]
    long = long.merge(prices, on=VKEY + ["item_code", "group10"], validate="many_to_one")
    ten, weights10, desc10 = build_system(core, long, prices, {g: [g] for g in GROUPS}, [s[0] for s in GROUPS.values()], sample, reference_sample)
    eight, weights8, desc8 = build_system(core, long, prices, MERGE8, NAME8, sample, reference_sample)
    if not np.allclose(ten.food_exp_pc_monthly, eight.food_exp_pc_monthly, rtol=1e-12, atol=1e-10):
        raise ValueError("8/10 food valuations differ")
    if not ten.sample_model.equals(eight.sample_model):
        raise ValueError("8/10 model samples differ")
    for name, frame in [("analysis_10", ten), ("analysis_8", eight)]:
        frame.to_stata(DATA / f"{name}.dta", write_index=False, version=118, value_labels={"family_type": FAMILY_NAMES, "age_family_type": AGE_NAMES})
        frame.to_csv(DATA / f"{name}.csv", index=False, encoding="utf-8-sig")
    prices.to_csv(DATA / "village_item_prices.csv", index=False, encoding="utf-8-sig")
    itemmap = pd.read_csv(ITEM_ROOT / "item_catalog.csv")
    itemmap = itemmap.loc[itemmap.item_code.isin(ITEM_GROUP)].copy()
    itemmap["group10"] = itemmap.item_code.map(ITEM_GROUP)
    itemmap["group10_name"] = itemmap.group10.map({g: spec[0] for g, spec in GROUPS.items()})
    itemmap["group8"] = itemmap.group10.map({child: g for g, children in MERGE8.items() for child in children})
    itemmap.to_csv(OUT / "item_group_definition.csv", index=False, encoding="utf-8-sig")
    core_audit.to_csv(OUT / "core_audit.csv", index=False)
    for name, frame in zip(["fixed_item_price_scales", "item_price_source_audit", "item_quality_range_audit", "representative_price_audit"], audits):
        frame.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(anomaly).to_csv(OUT / "quantity_anomaly_audit.csv", index=False, encoding="utf-8-sig")
    weights10.to_csv(OUT / "fixed_basket_weights_10.csv", index=False, encoding="utf-8-sig")
    weights8.to_csv(OUT / "fixed_basket_weights_8.csv", index=False, encoding="utf-8-sig")
    pd.concat([desc8, desc10]).to_csv(OUT / "food_group_descriptives.csv", index=False, encoding="utf-8-sig")
    family = ten.groupby(["family_type", "family_type_name"], as_index=False).agg(N_all=("household_id", "size"), N_model=("sample_model", "sum"), income_pc_annual_mean=("income_pc_annual", "mean"))
    family.to_csv(OUT / "family_morphology_counts.csv", index=False, encoding="utf-8-sig")
    ten.groupby(["age_family_type", "age_family_name"], as_index=False).agg(N_all=("household_id", "size"), N_model=("sample_model", "sum")).to_csv(OUT / "age_family_counts.csv", index=False, encoding="utf-8-sig")
    stages = [{"stage": "all_household_years", "N": len(core)}, {"stage": "quantity_screen_pass", "N": int(sample.sum())}, {"stage": "positive_income", "N": int(core.income_pc_monthly.gt(0).sum())}, {"stage": "common_8_10_model_sample", "N": int(ten.sample_model.sum())}, {"stage": "complete_relationship_model_sample", "N": int(ten.family_model_sample.sum())}]
    pd.DataFrame(stages).to_csv(OUT / "sample_flow.csv", index=False)
    model = ten.loc[ten.sample_model.eq(1)]
    prov = model.groupby(["province_id", "province_name"], as_index=False).agg(N=("household_id", "size"), income_pc_annual=("income_pc_annual", "mean"), food_exp_pc_monthly=("food_exp_pc_monthly", "mean"))
    prov.to_csv(OUT / "province_baselines.csv", index=False, encoding="utf-8-sig")
    income_desc = ten[["income_household_raw_annual", "income_household_annual", "income_pc_annual", "income_pc_monthly", "food_exp_pc_monthly", "income_expenditure_ratio"]].describe(percentiles=[.01, .05, .5, .95, .99]).transpose()
    income_desc.to_csv(OUT / "income_and_expenditure_descriptives.csv", encoding="utf-8-sig")
    income_outliers = []
    for sample_name, mask in [("all", pd.Series(True, index=ten.index)), ("model", ten.sample_model.eq(1)), ("income_supported", ten.sample_income_supported.eq(1))]:
        x = ten.loc[mask]
        income_outliers.append({"sample": sample_name, "N": len(x), "income_5MAD_both_tails": int(x.income_log_mad_outlier.sum()), "income_p01_p99_tail": int(x.income_percentile_tail.sum()), "food_income_ratio_gt20": int(x.income_accounting_mismatch.sum()), "income_pc_annual_min": x.income_pc_annual.min(), "income_pc_annual_median": x.income_pc_annual.median(), "income_pc_annual_max": x.income_pc_annual.max(), "food_income_ratio_p99": x.income_expenditure_ratio.quantile(.99)})
    pd.DataFrame(income_outliers).to_csv(OUT / "income_outlier_audit.csv", index=False)
    ten.loc[ten.income_log_mad_outlier.eq(1) | ten.income_percentile_tail.eq(1) | ten.income_accounting_mismatch.eq(1), KEY + ["province_id", "hhsize", "income_household_raw_annual", "income_household_annual", "income_pc_annual", "food_exp_pc_monthly", "income_expenditure_ratio", "income_log_mad_z", "income_log_mad_outlier", "income_percentile_tail", "income_accounting_mismatch", "sample_model", "sample_income_supported"]].to_csv(DATA / "income_outlier_household_diagnostics.csv", index=False)
    validation = [{"check": "household_unique", "value": int(not ten.duplicated(KEY).any())}, {"check": "shared_8_10_samples", "value": int(ten.sample_model.equals(eight.sample_model))}, {"check": "shared_8_10_food_value", "value": int(np.allclose(ten.food_exp_pc_monthly, eight.food_exp_pc_monthly, rtol=1e-12, atol=1e-10))}]
    for k, frame in [(8, eight), (10, ten)]:
        x = frame.loc[frame.sample_model.eq(1)]
        matrix = np.column_stack([np.ones(len(x)), np.log(x[[f"p{g}" for g in range(1, k + 1)]].to_numpy(float))])
        validation.append({"check": f"system{k}_logprice_rank", "value": int(np.linalg.matrix_rank(matrix)), "expected": k + 1})
        validation.append({"check": f"system{k}_max_share_sum_error", "value": float((x[[f"s{g}" for g in range(1, k + 1)]].sum(axis=1) - 1).abs().max()), "expected": 0})
    pd.DataFrame(validation).to_csv(OUT / "data_validation.csv", index=False)
    manifest = {"N_all": len(core), "N_model": int(ten.sample_model.sum()), "N_family_model": int(ten.family_model_sample.sum()), "income_unit": "nominal yuan per person per year; monthly divides by 12", "quantity_model_unit": "fixed-reference-basket equivalent jin per person per month", "quantity_raw_unit": "jin per person per month", "price_model_unit": "yuan per fixed-reference-basket equivalent jin", "food_valuation": "sum of commodity community prices times total consumption quantities; purchase+own+gift", "price_caveat": "other-meat prices use calibrated category-quality-range proxy; all fixed item scales derive from category ranges and are exploratory", "family_type": FAMILY_NAMES, "age_family_type": AGE_NAMES, "pork_definition": "roulei_1 pork plus roulei_2 pork ribs; unknown-species processed meat remains other meat", "nut_definition": "shuiguo_6 only; dried fruits/fruit preserves remain fruit products", "eight_ten_value_max_difference": float((ten.food_exp_pc_monthly-eight.food_exp_pc_monthly).abs().max())}
    (OUT / "data_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"N_all": len(core), "N_model": int(ten.sample_model.sum()), "N_family_model": int(ten.family_model_sample.sum())}))


if __name__ == "__main__":
    main()
