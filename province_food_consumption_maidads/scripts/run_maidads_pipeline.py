from __future__ import annotations

import json
import math
import re
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ProvinceMAIDADS" / "Results"
DATA_OUT = ROOT / "ProvinceMAIDADS" / "Data" / "output"

FOOD_ITEMS = {
    "grain": {"q": "q_grain", "p": "p_grain", "code": "GRAIN"},
    "oil": {"q": "q_oil", "p": "p_oil", "code": "OIL"},
    "vegetable": {"q": "q_vegetable", "p": "p_vegetable", "code": "VEGT"},
    "fruit": {"q": "q_fruit", "p": "p_fruit", "code": "FRTO"},
    "pork": {"q": "q_pork", "p": "p_pork", "code": "PIGM"},
    "beef": {"q": "q_beef", "p": "p_beef", "code": "CATM"},
    "mutton": {"q": "q_mutton", "p": "p_mutton", "code": "SHGM"},
    "poultry": {"q": "q_poultry", "p": "p_poultry", "code": "CHKM"},
    "aquatic": {"q": "q_aquaticprod", "p": "p_aquaticprod", "code": "FISH"},
    "egg": {"q": "q_egg", "p": "p_egg", "code": "EGGS"},
    "milk": {"q": "q_milk", "p": "p_milk", "code": "MILK"},
}

GROUPS = {
    "grain": ["grain"],
    "oil": ["oil"],
    "vegfruit": ["vegetable", "fruit"],
    "pork": ["pork"],
    "meatother": ["beef", "mutton", "poultry", "aquatic"],
    "dairyegg": ["milk", "egg"],
    "nonfood": [],
}

GROUP_LABELS = {
    "grain": "Staples",
    "oil": "Oils and fats",
    "vegfruit": "Vegetables and fruits",
    "pork": "Pork",
    "meatother": "Non-pork meat/aquatic",
    "dairyegg": "Dairy and eggs",
    "nonfood": "Other/non-covered residual",
}

FEED_COEFF = {
    "pork": 3.88,
    "poultry": 3.10,
    "egg": 2.46,
    "milk": 0.62,
    "aquatic": 1.35,
    "beef": 9.80,
    "mutton": 9.80,
}

# The user supplied these coefficients as feed-grain conversion factors.  Keep a
# separate share column so the output can be replaced by total-feed coefficients
# plus cereal shares when a sourced feed-conversion table is added.
FEED_CEREAL_SHARE = {
    "pork": 1.0,
    "poultry": 1.0,
    "egg": 1.0,
    "milk": 1.0,
    "aquatic": 1.0,
    "beef": 1.0,
    "mutton": 1.0,
}

PROVINCE_CODE = {
    "北京": 11,
    "天津": 12,
    "河北": 13,
    "山西": 14,
    "内蒙古": 15,
    "辽宁": 21,
    "吉林": 22,
    "黑龙江": 23,
    "上海": 31,
    "江苏": 32,
    "浙江": 33,
    "安徽": 34,
    "福建": 35,
    "江西": 36,
    "山东": 37,
    "河南": 41,
    "湖北": 42,
    "湖南": 43,
    "广东": 44,
    "广西": 45,
    "海南": 46,
    "重庆": 50,
    "四川": 51,
    "贵州": 52,
    "云南": 53,
    "西藏": 54,
    "陕西": 61,
    "甘肃": 62,
    "青海": 63,
    "宁夏": 64,
    "新疆": 65,
}

PROJECTION_PROVINCE_MAP = {
    "Beijing": "北京",
    "Tianjin": "天津",
    "Hebei": "河北",
    "Shanxi": "山西",
    "Inner Mongolia": "内蒙古",
    "Liaoning": "辽宁",
    "Jilin": "吉林",
    "Heilongjiang": "黑龙江",
    "Shanghai": "上海",
    "jiangsu": "江苏",
    "Jiangsu": "江苏",
    "Zhejiang": "浙江",
    "Anhui": "安徽",
    "Fujian": "福建",
    "Jiangxi": "江西",
    "Shandong": "山东",
    "Henan": "河南",
    "Hubei": "湖北",
    "Hunan": "湖南",
    "Guangdong": "广东",
    "Guangxi": "广西",
    "Hainan": "海南",
    "Chongqing": "重庆",
    "Sichuan": "四川",
    "Guizhou": "贵州",
    "Yunnan": "云南",
    "Tibet": "西藏",
    "Shaanxi": "陕西",
    "Gansu": "甘肃",
    "Qinghai": "青海",
    "Ningxia": "宁夏",
    "Xinjiang": "新疆",
}

POPULATION_PROJECTION_SOURCE = (
    "Chen, Y., Guo, F., Wang, J. et al. (2020) Sci Data 7, 83; "
    "doi:10.1038/s41597-020-0421-y"
)


def ensure_dirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)


def clean_province(name: str) -> str:
    s = str(name).strip()
    replacements = {
        "北京市": "北京",
        "天津市": "天津",
        "河北省": "河北",
        "山西省": "山西",
        "内蒙古自治区": "内蒙古",
        "辽宁省": "辽宁",
        "吉林省": "吉林",
        "黑龙江省": "黑龙江",
        "上海市": "上海",
        "江苏省": "江苏",
        "浙江省": "浙江",
        "安徽省": "安徽",
        "福建省": "福建",
        "江西省": "江西",
        "山东省": "山东",
        "河南省": "河南",
        "湖北省": "湖北",
        "湖南省": "湖南",
        "广东省": "广东",
        "广西壮族自治区": "广西",
        "海南省": "海南",
        "重庆市": "重庆",
        "四川省": "四川",
        "贵州省": "贵州",
        "云南省": "云南",
        "西藏自治区": "西藏",
        "陕西省": "陕西",
        "甘肃省": "甘肃",
        "青海省": "青海",
        "宁夏回族自治区": "宁夏",
        "新疆维吾尔自治区": "新疆",
    }
    return replacements.get(s, s)


def numeric(x) -> pd.Series:
    return pd.to_numeric(x, errors="coerce")


def read_nutrition() -> pd.DataFrame:
    path = ROOT / "营养成分表.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df.rename(
        columns={
            "Unnamed: 0": "item_name",
            "Unnamed: 1": "code",
            "能量": "energy",
            "蛋白质": "protein",
            "脂肪": "fat",
            "碳水化合物": "carb",
            "毛-纯": "edible_share",
        }
    )
    df = df[df["code"].notna()].copy()
    df = df[df["code"].astype(str).str.upper() != "CODE"].copy()
    for col in ["energy", "protein", "fat", "carb", "edible_share"]:
        df[col] = numeric(df[col])
    df["kcal_per_100g_edible"] = df["energy"]
    missing_energy = df["kcal_per_100g_edible"].fillna(0) <= 0
    df.loc[missing_energy, "kcal_per_100g_edible"] = (
        4 * df.loc[missing_energy, "protein"]
        + 9 * df.loc[missing_energy, "fat"]
        + 4 * df.loc[missing_energy, "carb"]
    )
    df["kcal_per_kg_as_purchased"] = (
        df["kcal_per_100g_edible"] * 10 * df["edible_share"] / 100
    )
    return df


def read_grain_weights(nutrition: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    path = ROOT / "粮食细类消费.csv"
    raw = pd.read_csv(path, encoding="utf-8-sig").rename(
        columns={"Unnamed: 0": "code", "2024": "qty", "Unnamed: 2": "label"}
    )
    raw["qty"] = numeric(raw["qty"])
    grain_codes = ["RICE", "WHEA", "MAIZ", "POTA", "SORG", "BARL", "SOYS", "OTGR"]
    grain = raw[raw["code"].isin(grain_codes)].copy()
    grain["grain_equiv_qty"] = grain["qty"]
    grain.loc[grain["code"] == "POTA", "grain_equiv_qty"] = (
        grain.loc[grain["code"] == "POTA", "qty"] / 5
    )
    merged = grain.merge(
        nutrition[["code", "kcal_per_kg_as_purchased"]], on="code", how="left"
    )
    if merged["kcal_per_kg_as_purchased"].isna().any():
        missing = merged.loc[merged["kcal_per_kg_as_purchased"].isna(), "code"].tolist()
        raise ValueError(f"Missing nutrition rows for grain components: {missing}")
    merged["grain_equiv_weight"] = merged["grain_equiv_qty"] / merged["grain_equiv_qty"].sum()
    # For calories, use each component's actual as-purchased kcal/kg.  The
    # potato /5 conversion is a grain-equivalent accounting convention, not a
    # calorie conversion.
    merged["kcal_weight"] = merged["qty"] / merged["qty"].sum()
    grain_kcal = float((merged["kcal_weight"] * merged["kcal_per_kg_as_purchased"]).sum())
    return merged, grain_kcal


def read_population() -> pd.DataFrame:
    raw = pd.read_csv(ROOT / "分省年度人口.csv", encoding="utf-8-sig", header=None)
    header_row = raw.index[raw.iloc[:, 0].astype(str).str.strip().eq("时间")][0]
    cols = raw.iloc[header_row].tolist()
    data = raw.iloc[header_row + 1 :].copy()
    data.columns = cols
    data = data[data["时间"].astype(str).str.contains(r"\d{4}", na=False)].copy()
    data["year"] = data["时间"].astype(str).str.extract(r"(\d{4})").astype(int)
    rows = []
    for col in data.columns:
        if col in ["时间", "year"] or pd.isna(col):
            continue
        prov = clean_province(col)
        if prov not in PROVINCE_CODE:
            continue
        tmp = data[["year", col]].copy()
        tmp["provincechn"] = prov
        tmp["province"] = PROVINCE_CODE[prov]
        tmp["population_10k"] = numeric(tmp[col])
        tmp = tmp.drop(columns=[col])
        rows.append(tmp)
    out = pd.concat(rows, ignore_index=True)
    return out.dropna(subset=["population_10k"])


def read_forecast() -> pd.DataFrame:
    raw = pd.read_csv(ROOT / "副本2026-2050预测数据.csv", encoding="utf-8-sig")
    raw = raw.rename(
        columns={
            "Unnamed: 0": "year",
            "基准情景": "gdp_growth_pct",
            "基准方案": "population_10k",
            "基准情景.1": "urban_rate",
            "基准方案.1": "exchange_rate",
        }
    )
    raw["year"] = numeric(raw["year"])
    raw = raw.dropna(subset=["year"]).copy()
    raw["year"] = raw["year"].astype(int)
    for col in ["gdp_growth_pct", "population_10k", "urban_rate", "exchange_rate"]:
        raw[col] = numeric(raw[col])
    return raw


def read_provincial_population_projection(ssp: str = "SSP2") -> pd.DataFrame:
    path = ROOT / "DATA_Provincial_Population_Projection" / "Pop_TOTAL.csv"
    raw = pd.read_csv(path, encoding="utf-8-sig")
    raw = raw[(raw["X"].ne("TOTAL")) & (raw["X.1"].eq(ssp))].copy()
    raw["provincechn"] = raw["X"].map(PROJECTION_PROVINCE_MAP)
    if raw["provincechn"].isna().any():
        missing = sorted(raw.loc[raw["provincechn"].isna(), "X"].astype(str).unique())
        raise ValueError(f"Unmapped population projection provinces: {missing}")
    raw["province"] = raw["provincechn"].map(PROVINCE_CODE)
    year_cols = [c for c in raw.columns if re.fullmatch(r"X\d{4}", str(c))]
    out = raw.melt(
        id_vars=["X", "X.1", "provincechn", "province"],
        value_vars=year_cols,
        var_name="year",
        value_name="population_person",
    )
    out["year"] = out["year"].str.replace("X", "", regex=False).astype(int)
    out["population_person"] = numeric(out["population_person"])
    out["population_10k"] = out["population_person"] / 10000.0
    out["population_projection_source"] = POPULATION_PROJECTION_SOURCE
    out["population_scenario"] = ssp
    out = out[
        [
            "province",
            "provincechn",
            "year",
            "population_10k",
            "population_person",
            "population_scenario",
            "population_projection_source",
        ]
    ].sort_values(["province", "year"])
    expected = set(PROVINCE_CODE.values())
    found = set(out.loc[out["year"].eq(2030), "province"].astype(int))
    if found != expected:
        raise ValueError(f"Population projection province coverage mismatch: {sorted(expected - found)}")
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(DATA_OUT / f"provincial_population_projection_{ssp.lower()}.csv", index=False)
    return out


def read_nonfood_cpi() -> pd.DataFrame:
    path = ROOT / "中国_CPI_非食品.csv"
    raw = pd.read_csv(path, encoding="gb18030", header=None, names=["date", "value"])
    raw = raw[raw["date"].astype(str).str.match(r"\d{4}-")].copy()
    raw["year"] = raw["date"].astype(str).str.slice(0, 4).astype(int)
    raw["nonfood_cpi_yoy"] = numeric(raw["value"])
    raw = raw[["year", "nonfood_cpi_yoy"]].groupby("year", as_index=False).mean()
    raw = raw.sort_values("year")
    raw["national_nonfood_price_index_2023"] = np.nan
    raw.loc[raw["year"] == 2023, "national_nonfood_price_index_2023"] = 100.0
    for idx in raw.index[raw["year"] > 2023]:
        prev_idx = raw.index[raw.index.get_loc(idx) - 1]
        raw.loc[idx, "national_nonfood_price_index_2023"] = (
            raw.loc[prev_idx, "national_nonfood_price_index_2023"] * raw.loc[idx, "nonfood_cpi_yoy"] / 100
        )
    for idx in list(raw.index[raw["year"] < 2023])[::-1]:
        next_idx = raw.index[raw.index.get_loc(idx) + 1]
        raw.loc[idx, "national_nonfood_price_index_2023"] = (
            raw.loc[next_idx, "national_nonfood_price_index_2023"] / (raw.loc[next_idx, "nonfood_cpi_yoy"] / 100)
        )
    if raw["year"].min() > 2015 and 2016 in set(raw["year"]):
        row_2016 = raw.loc[raw["year"].eq(2016)].iloc[0]
        raw = pd.concat(
            [
                pd.DataFrame(
                    [
                        {
                            "year": 2015,
                            "nonfood_cpi_yoy": np.nan,
                            "national_nonfood_price_index_2023": row_2016["national_nonfood_price_index_2023"]
                            / (row_2016["nonfood_cpi_yoy"] / 100),
                            "national_nonfood_bridge": "backcast_from_2016_yoy",
                        }
                    ]
                ),
                raw.assign(national_nonfood_bridge="observed_yoy_chain"),
            ],
            ignore_index=True,
        )
    else:
        raw["national_nonfood_bridge"] = "observed_yoy_chain"
    return raw


def read_province_cpi_table(filename: str, value_name: str) -> pd.DataFrame:
    path = ROOT / filename
    rows = []
    header = None
    with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            cells = [c.replace("\t", "").strip() for c in line.strip().split(",")]
            cells = [c for c in cells if c != ""]
            if not cells:
                continue
            if cells[0] == "数据时间":
                header = cells
                continue
            if header is None or not re.match(r"^\d{4}年$", cells[0]):
                continue
            year = int(cells[0].replace("年", ""))
            for prov_name, value in zip(header[1:], cells[1:]):
                prov = clean_province(prov_name)
                if prov not in PROVINCE_CODE:
                    continue
                rows.append(
                    {
                        "year": year,
                        "province": PROVINCE_CODE[prov],
                        "provincechn": prov,
                        value_name: pd.to_numeric(value, errors="coerce"),
                    }
                )
    return pd.DataFrame(rows).dropna(subset=[value_name])


def index_from_yoy(df: pd.DataFrame, yoy_col: str, index_col: str, base_year: int = 2023) -> pd.DataFrame:
    out = df.copy()
    out[index_col] = np.nan
    pieces = []
    for province, tmp in out.groupby("province", sort=False):
        tmp = tmp.sort_values("year").copy()
        if base_year not in set(tmp["year"]):
            pieces.append(tmp)
            continue
        tmp.loc[tmp["year"] == base_year, index_col] = 100.0
        for idx in tmp.index[tmp["year"] > base_year]:
            pos = tmp.index.get_loc(idx)
            prev_idx = tmp.index[pos - 1]
            if pd.isna(tmp.loc[prev_idx, index_col]) or pd.isna(tmp.loc[idx, yoy_col]):
                continue
            tmp.loc[idx, index_col] = tmp.loc[prev_idx, index_col] * tmp.loc[idx, yoy_col] / 100
        for idx in list(tmp.index[tmp["year"] < base_year])[::-1]:
            pos = tmp.index.get_loc(idx)
            next_idx = tmp.index[pos + 1]
            if pd.isna(tmp.loc[next_idx, index_col]) or pd.isna(tmp.loc[next_idx, yoy_col]):
                continue
            tmp.loc[idx, index_col] = tmp.loc[next_idx, index_col] / (tmp.loc[next_idx, yoy_col] / 100)
        pieces.append(tmp)
    return pd.concat(pieces, ignore_index=True)


def build_province_cpi_indices(data: pd.DataFrame | None = None) -> pd.DataFrame:
    total = read_province_cpi_table("消费价格指数上年=100.csv", "total_cpi_yoy")
    food = pd.concat(
        [
            read_province_cpi_table("食品类消费价格指数1上年=100.csv", "food_cpi_yoy"),
            read_province_cpi_table("食品类消费价格指数2上年=100.csv", "food_cpi_yoy"),
            read_province_cpi_table("食品类消费价格指数3上年=100.csv", "food_cpi_yoy"),
        ],
        ignore_index=True,
    )
    food = food.sort_values(["province", "year"]).drop_duplicates(["province", "year"], keep="last")
    out = total.merge(food[["year", "province", "food_cpi_yoy"]], on=["year", "province"], how="left")
    if data is not None:
        share = data[["year", "province"]].copy()
        if {"exp_food_nominal", "expenditure_nominal"}.issubset(data.columns):
            share["food_budget_share_all"] = (
                numeric(data["exp_food_nominal"]) / numeric(data["expenditure_nominal"])
            )
        else:
            share["food_budget_share_all"] = numeric(data["exp_food"]) / numeric(data["m"])
        out = out.merge(share[["year", "province", "food_budget_share_all"]], on=["year", "province"], how="left")
    else:
        out["food_budget_share_all"] = np.nan
    s = out["food_budget_share_all"].clip(lower=0.01, upper=0.80)
    out["nonfood_cpi_yoy_approx"] = (out["total_cpi_yoy"] - s * out["food_cpi_yoy"]) / (1 - s)
    invalid = (out["nonfood_cpi_yoy_approx"] < 70) | (out["nonfood_cpi_yoy_approx"] > 140)
    out.loc[invalid, "nonfood_cpi_yoy_approx"] = np.nan
    for yoy_col, index_col in [
        ("total_cpi_yoy", "total_price_index_2023"),
        ("food_cpi_yoy", "food_price_index_2023"),
        ("nonfood_cpi_yoy_approx", "nonfood_price_index_2023"),
    ]:
        out = index_from_yoy(out, yoy_col, index_col)
    national_nonfood = read_nonfood_cpi()
    out = out.merge(national_nonfood, on="year", how="left")
    out["nonfood_price_source"] = "derived_from_total_food_cpi"
    missing_nonfood = out["nonfood_price_index_2023"].isna()
    out.loc[missing_nonfood, "nonfood_price_index_2023"] = out.loc[
        missing_nonfood, "national_nonfood_price_index_2023"
    ]
    out.loc[missing_nonfood, "nonfood_price_source"] = "national_nonfood_cpi_fallback"
    out["nonfood_relative_price_index_2023"] = (
        out["nonfood_price_index_2023"] / out["total_price_index_2023"] * 100
    )
    return out.sort_values(["province", "year"])


def build_model_data(
    nonfood_price_mode: str = "national_nonfood_cpi",
    output_suffix: str = "",
    monetary_mode: str = "real_2023_cpi",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nutrition = read_nutrition()
    grain_weights, grain_kcal = read_grain_weights(nutrition)
    pop = read_population()

    data = pd.read_stata(ROOT / "ProvinceData" / "workdata" / "data.dta")
    data = data.merge(pop[["year", "province", "population_10k"]], on=["year", "province"], how="left")
    data["obs_id"] = data["province"].astype(int).astype(str) + "_" + data["year"].astype(int).astype(str)
    data["expenditure_nominal"] = numeric(data["expenditure"])
    data["exp_food_nominal"] = numeric(data["exp_food"])

    cpi_panel = build_province_cpi_indices(data)
    cpi_panel.to_csv(DATA_OUT / "province_cpi_indices.csv", index=False)
    cpi_cols = [
        "total_cpi_yoy",
        "food_cpi_yoy",
        "nonfood_cpi_yoy_approx",
        "total_price_index_2023",
        "food_price_index_2023",
        "nonfood_price_index_2023",
        "nonfood_relative_price_index_2023",
        "national_nonfood_price_index_2023",
        "food_budget_share_all",
    ]
    data = data.merge(cpi_panel[["year", "province", *cpi_cols]], on=["year", "province"], how="left")

    if monetary_mode == "real_2023_cpi":
        data["deflator_total_2015"] = numeric(data["fixed_cpi"])
        data["monetary_deflator"] = data["total_price_index_2023"] / 100.0
        data["food_price_deflator"] = data["food_price_index_2023"] / 100.0
    elif monetary_mode == "real_fixed_cpi_2015":
        data["deflator_total_2015"] = numeric(data["fixed_cpi"])
        data["monetary_deflator"] = data["deflator_total_2015"] / 100.0
        data["food_price_deflator"] = data["monetary_deflator"]
    elif monetary_mode == "nominal":
        data["deflator_total_2015"] = 100.0
        data["monetary_deflator"] = 1.0
        data["food_price_deflator"] = 1.0
    else:
        raise ValueError(f"Unknown monetary_mode: {monetary_mode}")
    data["m"] = data["expenditure_nominal"] / data["monetary_deflator"]

    kcal_lookup = dict(zip(nutrition["code"], nutrition["kcal_per_kg_as_purchased"]))
    kcal_lookup["GRAIN"] = grain_kcal
    kcal_lookup["OIL"] = float(
        nutrition.loc[nutrition["code"].isin(["SOYO", "RAPO", "GRDO"]), "kcal_per_kg_as_purchased"].mean()
    )

    for item, spec in FOOD_ITEMS.items():
        q = numeric(data[spec["q"]])
        p = numeric(data[spec["p"]]) / data["food_price_deflator"]
        kcal_kg = kcal_lookup[spec["code"]]
        data[f"{item}_kcal_year"] = q * kcal_kg
        data[f"{item}_x"] = data[f"{item}_kcal_year"] / 365 / 2000
        data[f"{item}_exp"] = q * p
        data[f"{item}_kg"] = q
        data[f"{item}_kcal_per_kg"] = kcal_kg

    for group, items in GROUPS.items():
        if group == "nonfood":
            continue
        data[f"x_{group}"] = data[[f"{i}_x" for i in items]].sum(axis=1)
        data[f"e_{group}"] = data[[f"{i}_exp" for i in items]].sum(axis=1)
        data[f"p_{group}_model"] = data[f"e_{group}"] / data[f"x_{group}"]

    food_exp_cols = [f"e_{g}" for g in GROUPS if g != "nonfood"]
    data["covered_food_exp"] = data[food_exp_cols].sum(axis=1)
    data["nonfood_exp"] = data["m"] - data["covered_food_exp"]
    data["other_noncovered_exp"] = data["nonfood_exp"]
    if nonfood_price_mode == "national_nonfood_cpi":
        data["p_nonfood_model"] = data["national_nonfood_price_index_2023"]
    elif nonfood_price_mode == "flat":
        data["p_nonfood_model"] = 100.0
    elif nonfood_price_mode == "cpi_nonfood":
        data["p_nonfood_model"] = data["nonfood_price_index_2023"]
    elif nonfood_price_mode == "relative_cpi_nonfood":
        data["p_nonfood_model"] = data["nonfood_relative_price_index_2023"]
    else:
        raise ValueError(f"Unknown nonfood_price_mode: {nonfood_price_mode}")
    data["x_nonfood"] = data["nonfood_exp"] / data["p_nonfood_model"]
    data["covered_daily_kcal"] = data[[f"x_{g}" for g in GROUPS if g != "nonfood"]].sum(axis=1) * 2000
    data["covered_food_budget_share"] = data["covered_food_exp"] / data["m"]

    keep_groups = list(GROUPS.keys())
    rows = []
    for _, row in data.iterrows():
        for group in keep_groups:
            rows.append(
                {
                    "obs_id": row["obs_id"],
                    "province": int(row["province"]),
                    "provincechn": row["provincechn"],
                    "year": int(row["year"]),
                    "population_10k": row["population_10k"],
                    "group": group,
                    "group_label": GROUP_LABELS[group],
                    "x": row[f"x_{group}"],
                    "p": row[f"p_{group}_model"],
                    "m": row["m"],
                }
            )
    long_df = pd.DataFrame(rows)

    panel_cols = [
        "obs_id",
        "province",
        "provincechn",
        "year",
        "population_10k",
        "expenditure_nominal",
        "exp_food_nominal",
        "deflator_total_2015",
        "monetary_deflator",
        "m",
        "covered_food_exp",
        "nonfood_exp",
        "covered_daily_kcal",
        "covered_food_budget_share",
    ]
    panel_cols += cpi_cols
    for group in keep_groups:
        panel_cols += [f"x_{group}", f"p_{group}_model"]
    panel = data[panel_cols].copy()
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna()
    long_df = long_df[long_df["obs_id"].isin(panel["obs_id"])].copy()

    if (panel["nonfood_exp"] <= 0).any():
        bad = panel.loc[panel["nonfood_exp"] <= 0, ["obs_id", "nonfood_exp"]]
        raise ValueError(f"Non-positive nonfood residuals:\n{bad.head()}")
    if (long_df["x"] <= 0).any() or (long_df["p"] <= 0).any():
        raise ValueError("Non-positive model quantity or price found.")

    nutrition_out = nutrition.copy()
    nutrition_out.to_csv(DATA_OUT / "nutrition_processed.csv", index=False)
    grain_weights.to_csv(DATA_OUT / "grain_weights_processed.csv", index=False)
    panel.to_csv(DATA_OUT / f"maidads6_panel{output_suffix}.csv", index=False)
    long_df.to_csv(DATA_OUT / f"maidads6_long{output_suffix}.csv", index=False)
    return panel, long_df, nutrition_out


@dataclass
class ModelArrays:
    obs_ids: np.ndarray
    provinces: np.ndarray
    years: np.ndarray
    group_names: list[str]
    x: np.ndarray
    p: np.ndarray
    m: np.ndarray


def panel_to_arrays(panel: pd.DataFrame) -> ModelArrays:
    group_names = list(GROUPS.keys())
    x = panel[[f"x_{g}" for g in group_names]].to_numpy(float)
    p = panel[[f"p_{g}_model" for g in group_names]].to_numpy(float)
    m = panel["m"].to_numpy(float)
    return ModelArrays(
        obs_ids=panel["obs_id"].to_numpy(),
        provinces=panel["province"].to_numpy(int),
        years=panel["year"].to_numpy(int),
        group_names=group_names,
        x=x,
        p=p,
        m=m,
    )


def softmax(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    z = z - np.max(z)
    e = np.exp(z)
    return e / e.sum()


def sigmoid_safe(x: float | np.ndarray) -> float | np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60, 60)))


def phi_gamma(
    u: float, alpha: np.ndarray, beta: np.ndarray, delta: np.ndarray, tau: np.ndarray, omega: float
) -> tuple[np.ndarray, np.ndarray]:
    s1 = sigmoid_safe(u)
    phi = alpha * (1 - s1) + beta * s1
    if omega <= 1e-12:
        s2 = 0.5
    else:
        s2 = sigmoid_safe(omega * u)
    gamma = delta * (1 - s2) + tau * s2
    return phi, gamma


def phi_gamma_matrix(
    u: np.ndarray, alpha: np.ndarray, beta: np.ndarray, delta: np.ndarray, tau: np.ndarray, omega: float
) -> tuple[np.ndarray, np.ndarray]:
    u = np.asarray(u, dtype=float)
    s1 = sigmoid_safe(u)[:, None]
    phi = alpha[None, :] * (1 - s1) + beta[None, :] * s1
    if omega <= 1e-12:
        s2 = np.full((u.size, 1), 0.5)
    else:
        s2 = sigmoid_safe(omega * u)[:, None]
    gamma = delta[None, :] * (1 - s2) + tau[None, :] * s2
    return phi, gamma


def unpack_aidads(raw: np.ndarray, n: int) -> dict[str, np.ndarray | float]:
    alpha = softmax(raw[:n])
    beta = np.zeros(n)
    beta[-1] = 1.0
    gamma = np.exp(np.clip(raw[n : 2 * n], -30, 12))
    kappa = float(raw[2 * n])
    return {"alpha": alpha, "beta": beta, "delta": gamma, "tau": gamma, "omega": 0.0, "kappa": kappa}


def unpack_maidads(raw: np.ndarray, n: int) -> dict[str, np.ndarray | float]:
    alpha = softmax(raw[:n])
    beta = np.zeros(n)
    beta[-1] = 1.0
    delta = np.exp(np.clip(raw[n : 2 * n], -30, 12))
    tau = np.exp(np.clip(raw[2 * n : 3 * n], -30, 12))
    omega = float(np.exp(np.clip(raw[3 * n], -9, 4)))
    kappa = float(raw[3 * n + 1])
    return {"alpha": alpha, "beta": beta, "delta": delta, "tau": tau, "omega": omega, "kappa": kappa}


def utility_gap_vector(
    u: np.ndarray,
    p: np.ndarray,
    m: np.ndarray,
    alpha: np.ndarray,
    beta: np.ndarray,
    delta: np.ndarray,
    tau: np.ndarray,
    omega: float,
    kappa: float,
) -> np.ndarray:
    phi, gamma = phi_gamma_matrix(u, alpha, beta, delta, tau, omega)
    disc = m - np.sum(p * gamma, axis=1)
    qdisc = phi * disc[:, None] / p
    out = np.sum(phi * np.log(np.maximum(qdisc, 1e-300)), axis=1) - u - kappa
    out[(disc <= 0) | ~np.isfinite(out)] = np.nan
    return out


def solve_u_vectorized(
    p: np.ndarray,
    m: np.ndarray,
    alpha: np.ndarray,
    beta: np.ndarray,
    delta: np.ndarray,
    tau: np.ndarray,
    omega: float,
    kappa: float,
) -> np.ndarray | None:
    p = np.asarray(p, dtype=float)
    m = np.asarray(m, dtype=float)
    c = m.size
    grid = np.linspace(-35, 35, 71)
    vals = np.vstack(
        [
            utility_gap_vector(np.full(c, u), p, m, alpha, beta, delta, tau, omega, kappa)
            for u in grid
        ]
    )
    ok = np.isfinite(vals)
    crosses = ok[:-1] & ok[1:] & (vals[:-1] * vals[1:] <= 0)
    has = crosses.any(axis=0)
    if not np.all(has):
        return None

    first = np.argmax(crosses, axis=0)
    rows = np.arange(c)
    lo = grid[first].astype(float)
    hi = grid[first + 1].astype(float)
    glo = vals[first, rows].astype(float)

    for _ in range(64):
        mid = (lo + hi) / 2
        gmid = utility_gap_vector(mid, p, m, alpha, beta, delta, tau, omega, kappa)
        if np.any(~np.isfinite(gmid)):
            return None
        same_side = glo * gmid > 0
        lo[same_side] = mid[same_side]
        glo[same_side] = gmid[same_side]
        hi[~same_side] = mid[~same_side]
    return (lo + hi) / 2


def solve_u_for_obs(
    p: np.ndarray,
    m: float,
    alpha: np.ndarray,
    beta: np.ndarray,
    delta: np.ndarray,
    tau: np.ndarray,
    omega: float,
    kappa: float,
) -> float | None:
    u = solve_u_vectorized(
        np.asarray(p, dtype=float)[None, :],
        np.asarray([m], dtype=float),
        alpha,
        beta,
        delta,
        tau,
        omega,
        kappa,
    )
    if u is None:
        return None
    return float(u[0])


def predict_x(params: dict[str, np.ndarray | float], arr: ModelArrays) -> tuple[np.ndarray | None, np.ndarray | None]:
    alpha = np.asarray(params["alpha"], float)
    beta = np.asarray(params["beta"], float)
    delta = np.asarray(params["delta"], float)
    tau = np.asarray(params["tau"], float)
    omega = float(params["omega"])
    kappa = float(params["kappa"])
    uvec = solve_u_vectorized(arr.p, arr.m, alpha, beta, delta, tau, omega, kappa)
    if uvec is None:
        return None, None
    phi, gamma = phi_gamma_matrix(uvec, alpha, beta, delta, tau, omega)
    disc = arr.m - np.sum(arr.p * gamma, axis=1)
    if np.any(disc <= 0):
        return None, None
    xhat = gamma + phi * disc[:, None] / arr.p
    if np.any(~np.isfinite(xhat)) or np.any(xhat <= 0):
        return None, None
    return xhat, uvec


def neg_loglike(raw: np.ndarray, arr: ModelArrays, model: str) -> float:
    n = arr.x.shape[1]
    try:
        params = unpack_aidads(raw, n) if model == "aidads" else unpack_maidads(raw, n)
        xhat, _ = predict_x(params, arr)
        if xhat is None:
            return 1e12
        eps = arr.x - xhat
        w = eps.T @ eps / eps.shape[0]
        w = w + np.eye(w.shape[0]) * 1e-10
        sign, logdet = np.linalg.slogdet(w)
        if sign <= 0 or not np.isfinite(logdet):
            return 1e12
        c, n2 = arr.x.shape
        nll = 0.5 * c * (n2 * (1 + math.log(2 * math.pi)) + logdet)
        if not np.isfinite(nll):
            return 1e12
        return float(nll)
    except Exception:
        return 1e12


def initial_aidads(arr: ModelArrays) -> np.ndarray:
    n = arr.x.shape[1]
    shares = (arr.p * arr.x) / arr.m[:, None]
    alpha0 = shares.mean(axis=0)
    alpha0 = np.maximum(alpha0, 1e-4)
    alpha0 = alpha0 / alpha0.sum()
    gamma0 = np.maximum(arr.x.min(axis=0) / 4, 1e-4)
    raw = np.r_[np.log(alpha0), np.log(gamma0), 1.0]
    return raw


def raw_param_names(model: str, group_names: list[str]) -> list[str]:
    if model == "aidads":
        return (
            [f"raw_alpha[{g}]" for g in group_names]
            + [f"log_gamma[{g}]" for g in group_names]
            + ["kappa"]
        )
    return (
        [f"raw_alpha[{g}]" for g in group_names]
        + [f"log_delta[{g}]" for g in group_names]
        + [f"log_tau[{g}]" for g in group_names]
        + ["log_omega", "kappa"]
    )


def optimizer_diagnostics(
    res,
    bounds: list[tuple[float, float]],
    names: list[str],
    model: str,
    start_id: str,
    selected: bool,
) -> dict:
    jac = getattr(res, "jac", None)
    if jac is None:
        grad_norm = np.nan
        max_abs_gradient = np.nan
    else:
        jac = np.asarray(jac, dtype=float)
        grad_norm = float(np.linalg.norm(jac))
        max_abs_gradient = float(np.nanmax(np.abs(jac)))
    boundary_params = []
    x = np.asarray(getattr(res, "x", np.full(len(bounds), np.nan)), dtype=float)
    for name, value, (lo, hi) in zip(names, x, bounds):
        if np.isfinite(value) and (abs(value - lo) < 1e-5 or abs(value - hi) < 1e-5):
            boundary_params.append(name)
    return {
        "model": "AIDADS_sat" if model == "aidads" else "MAIDADS_sat",
        "start_id": start_id,
        "selected": selected,
        "success": bool(getattr(res, "success", False)),
        "nll": float(getattr(res, "fun", np.nan)),
        "n_iter": int(getattr(res, "nit", -1)) if getattr(res, "nit", None) is not None else -1,
        "grad_norm": grad_norm,
        "max_abs_gradient": max_abs_gradient,
        "hessian_status": "not_available_lbfgsb",
        "n_boundary_raw_params": len(boundary_params),
        "boundary_raw_params": ";".join(boundary_params),
        "message": str(getattr(res, "message", "")),
    }


def parameter_boundary_rows(fits: tuple[dict, dict], group_names: list[str]) -> list[dict]:
    rows = []
    for fit in fits:
        params = fit["params"]
        for j, group in enumerate(group_names):
            for name in ["alpha", "beta", "delta", "tau"]:
                value = float(params[name][j])
                if name == "beta":
                    imposed = (group != "nonfood" and abs(value) < 1e-12) or (
                        group == "nonfood" and abs(value - 1.0) < 1e-12
                    )
                else:
                    imposed = False
                rows.append(
                    {
                        "model": fit["model"],
                        "group": group,
                        "parameter": name,
                        "value": value,
                        "near_lower_boundary": bool(value < 1e-4),
                        "near_upper_boundary": bool(name in ["alpha", "beta"] and value > 1 - 1e-4),
                        "imposed_by_saturation": imposed,
                    }
                )
        for name in ["omega", "kappa"]:
            value = float(params[name])
            rows.append(
                {
                    "model": fit["model"],
                    "group": "all",
                    "parameter": name,
                    "value": value,
                    "near_lower_boundary": bool(name == "omega" and value < 1e-4),
                    "near_upper_boundary": False,
                    "imposed_by_saturation": False,
                }
            )
    return rows


def fit_model(
    arr: ModelArrays,
    maidads_random_scales: tuple[float, ...] = (0.05, 0.15),
    maxiter_a: int = 450,
    maxiter_m: int = 650,
    progress: bool = True,
    seed: int = 20260607,
    wide_multistart: bool = True,
) -> tuple[dict, dict]:
    n = arr.x.shape[1]
    group_names = arr.group_names
    raw0 = initial_aidads(arr)
    bounds_a = [(-8, 8)] * n + [(-12, 8)] * n + [(-20, 20)]
    diagnostics: list[dict] = []

    def callback(label: str):
        state = {"i": 0}

        def _cb(xk: np.ndarray) -> None:
            if not progress:
                return
            state["i"] += 1
            if state["i"] == 1 or state["i"] % 25 == 0:
                val = neg_loglike(xk, arr, "aidads" if label.startswith("AIDADS") else "maidads")
                print(f"{label}: iter={state['i']}, nll={val:.3f}", flush=True)

        return _cb

    if progress:
        print("Fitting AIDADS_sat baseline...", flush=True)
    res_a = minimize(
        neg_loglike,
        raw0,
        args=(arr, "aidads"),
        method="L-BFGS-B",
        bounds=bounds_a,
        callback=callback("AIDADS_sat"),
        options={"maxiter": maxiter_a, "maxfun": maxiter_a * 200, "ftol": 1e-8, "maxls": 30},
    )
    if progress:
        print(
            f"AIDADS_sat finished: nll={res_a.fun:.3f}, success={res_a.success}, message={res_a.message}",
            flush=True,
        )
    diagnostics.append(
        optimizer_diagnostics(
            res_a,
            bounds_a,
            raw_param_names("aidads", group_names),
            "aidads",
            "warm_start",
            True,
        )
    )

    aparams = unpack_aidads(res_a.x, n)
    gamma = np.asarray(aparams["delta"], float)
    raw_nested_m0 = np.r_[
        res_a.x[:n],
        np.log(np.maximum(gamma, 1e-12)),
        np.log(np.maximum(gamma, 1e-12)),
        -9.0,
        res_a.x[-1],
    ]
    raw_m0 = np.r_[
        res_a.x[:n],
        np.log(gamma),
        np.log(gamma * 1.02 + 1e-8),
        math.log(0.2),
        res_a.x[-1],
    ]
    bounds_m = [(-8, 8)] * n + [(-12, 8)] * n + [(-12, 8)] * n + [(-9, 3)] + [(-20, 20)]
    best = None

    def is_usable_result(res) -> bool:
        return bool(res.success) and np.isfinite(res.fun) and float(res.fun) < 1e11

    def is_better_result(candidate, incumbent) -> bool:
        if incumbent is None:
            return True
        candidate_ok = is_usable_result(candidate)
        incumbent_ok = is_usable_result(incumbent)
        if candidate_ok != incumbent_ok:
            return candidate_ok
        return float(candidate.fun) < float(incumbent.fun)

    starts = [raw_nested_m0, raw_m0]
    # Warm-start from an externally verified global optimum (7-group split-pork
    # MAIDADS has a deep basin the AIDADS-anchored starts miss).  The saved
    # vector is a strong seed even for bootstrap resamples; L-BFGS-B refines it.
    _ws_path = Path(__file__).with_name("maidads_warmstart_7g.npy")
    if _ws_path.exists():
        try:
            _ws = np.load(_ws_path)
            if _ws.shape == raw_m0.shape:
                _lo = np.array([b[0] for b in bounds_m])
                _hi = np.array([b[1] for b in bounds_m])
                starts.insert(0, np.clip(_ws.astype(float), _lo, _hi))
        except Exception:
            pass
    rng = np.random.default_rng(seed)
    _scales = tuple(maidads_random_scales)
    if wide_multistart:
        _scales = _scales + (0.3, 0.6, 0.6, 1.0)
    for scale in _scales:
        starts.append(raw_m0 + rng.normal(0, scale, size=raw_m0.size))
    for i, start in enumerate(starts, start=1):
        if progress:
            print(f"Fitting MAIDADS_sat start {i}/{len(starts)}...", flush=True)
        res = minimize(
            neg_loglike,
            start,
            args=(arr, "maidads"),
            method="L-BFGS-B",
            bounds=bounds_m,
            callback=callback(f"MAIDADS_sat start {i}"),
            options={"maxiter": maxiter_m, "maxfun": maxiter_m * 200, "ftol": 1e-8, "maxls": 30},
        )
        if progress:
            print(
                f"MAIDADS_sat start {i} finished: nll={res.fun:.3f}, success={res.success}, message={res.message}",
                flush=True,
            )
        diagnostics.append(
            optimizer_diagnostics(
                res,
                bounds_m,
                raw_param_names("maidads", group_names),
                "maidads",
                f"start_{i}",
                False,
            )
        )
        if is_better_result(res, best):
            best = res

    mparams = unpack_maidads(best.x, n)
    for row in diagnostics:
        if row["model"] == "MAIDADS_sat" and np.isclose(row["nll"], float(best.fun), rtol=0, atol=1e-8):
            row["selected"] = True
            break
    return (
        {
            "model": "AIDADS_sat",
            "result": res_a,
            "params": aparams,
            "nll": float(res_a.fun),
            "diagnostics": diagnostics,
        },
        {
            "model": "MAIDADS_sat",
            "result": best,
            "params": mparams,
            "nll": float(best.fun),
            "diagnostics": diagnostics,
        },
    )


def elasticity_for_point(
    p: np.ndarray,
    m: float,
    params: dict[str, np.ndarray | float],
) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    alpha = np.asarray(params["alpha"], float)
    beta = np.asarray(params["beta"], float)
    delta = np.asarray(params["delta"], float)
    tau = np.asarray(params["tau"], float)
    omega = float(params["omega"])
    kappa = float(params["kappa"])

    def pred_at_income(income: float) -> tuple[np.ndarray, float]:
        tmp_arr = ModelArrays(
            obs_ids=np.array(["elasticity_point"]),
            provinces=np.array([0]),
            years=np.array([0]),
            group_names=list(GROUPS.keys()),
            x=np.zeros((1, len(GROUPS))),
            p=np.asarray(p, dtype=float)[None, :],
            m=np.asarray([income], dtype=float),
        )
        xhat_tmp, u_tmp = predict_x(
            {"alpha": alpha, "beta": beta, "delta": delta, "tau": tau, "omega": omega, "kappa": kappa},
            tmp_arr,
        )
        if xhat_tmp is None or u_tmp is None:
            raise ValueError("Could not solve utility for elasticity point.")
        return xhat_tmp[0], float(u_tmp[0])

    xhat, u = pred_at_income(m)
    step = max(1e-4, 1e-4 * m)
    m_minus = max(m - step, 1e-6)
    m_plus = m + step
    try:
        x_minus, _ = pred_at_income(m_minus)
        x_plus, _ = pred_at_income(m_plus)
    except Exception as exc:
        raise ValueError("Could not solve utility for elasticity point.")
    eta = (np.log(x_plus) - np.log(x_minus)) / (np.log(m_plus) - np.log(m_minus))
    phi, _ = phi_gamma(u, alpha, beta, delta, tau, omega)
    return eta, xhat, u, phi


def price_elasticities_for_point(
    p: np.ndarray,
    m: float,
    params: dict[str, np.ndarray | float],
    step_pct: float = 1e-4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    eta, xhat, u, _ = elasticity_for_point(p, m, params)
    p = np.asarray(p, dtype=float)
    marshallian = np.full((p.size, p.size), np.nan)
    for j in range(p.size):
        h = max(step_pct, 1e-8)
        p_minus = p.copy()
        p_plus = p.copy()
        p_minus[j] *= 1 - h
        p_plus[j] *= 1 + h
        try:
            _, x_minus, _, _ = elasticity_for_point(p_minus, m, params)
            _, x_plus, _, _ = elasticity_for_point(p_plus, m, params)
        except Exception:
            continue
        marshallian[:, j] = (np.log(x_plus) - np.log(x_minus)) / (
            np.log(p_plus[j]) - np.log(p_minus[j])
        )
    budget_shares = p * xhat / m
    hicksian = marshallian + eta[:, None] * budget_shares[None, :]
    return marshallian, hicksian, eta, budget_shares, u


def elasticity_consistency_row(
    location: str,
    income: float,
    group_names: list[str],
    marshallian: np.ndarray,
    hicksian: np.ndarray,
    eta: np.ndarray,
    budget_shares: np.ndarray,
) -> dict:
    adding_up_income = float(np.nansum(budget_shares * eta) - 1.0)
    price_adding = np.nansum(budget_shares[:, None] * marshallian, axis=0) + budget_shares
    marshallian_homogeneity = np.nansum(marshallian, axis=1) + eta
    hicksian_homogeneity = np.nansum(hicksian, axis=1)
    slutsky_errors = []
    for i in range(len(group_names)):
        for j in range(len(group_names)):
            slutsky_errors.append(budget_shares[i] * hicksian[i, j] - budget_shares[j] * hicksian[j, i])
    own_price_positive = [
        group_names[i]
        for i in range(len(group_names))
        if np.isfinite(marshallian[i, i]) and marshallian[i, i] > 0
    ]
    return {
        "location": location,
        "income": income,
        "adding_up_income_error": adding_up_income,
        "max_abs_price_adding_up_error": float(np.nanmax(np.abs(price_adding))),
        "max_abs_marshallian_homogeneity_error": float(np.nanmax(np.abs(marshallian_homogeneity))),
        "max_abs_hicksian_homogeneity_error": float(np.nanmax(np.abs(hicksian_homogeneity))),
        "max_abs_slutsky_symmetry_error": float(np.nanmax(np.abs(slutsky_errors))),
        "n_positive_own_price_marshallian": len(own_price_positive),
        "positive_own_price_groups": ";".join(own_price_positive),
    }


def support_flag(value: float, lower: float, upper: float) -> str:
    return "in_support" if lower <= value <= upper else "extrapolation"


def build_results(panel: pd.DataFrame, arr: ModelArrays, fits: tuple[dict, dict], nutrition: pd.DataFrame) -> dict:
    group_names = arr.group_names
    diagnostics = pd.DataFrame(fits[1].get("diagnostics", []))
    if not diagnostics.empty:
        diagnostics.to_csv(OUT / "multistart_diagnostics.csv", index=False)
        diagnostics[diagnostics["selected"].astype(bool)].to_csv(
            OUT / "best_solution_gradient_report.csv", index=False
        )
    pd.DataFrame(parameter_boundary_rows(fits, group_names)).to_csv(
        OUT / "parameter_boundary_report.csv", index=False
    )

    fit_rows = []
    for fit in fits:
        params = fit["params"]
        xhat, u = predict_x(params, arr)
        eps = arr.x - xhat
        rmse = np.sqrt((eps**2).mean(axis=0))
        mae = np.abs(eps).mean(axis=0)
        for j, group in enumerate(group_names):
            fit_rows.append(
                {
                    "model": fit["model"],
                    "group": group,
                    "rmse_x": rmse[j],
                    "mae_x": mae[j],
                    "mean_x": arr.x[:, j].mean(),
                }
            )
        fit["xhat"] = xhat
        fit["u"] = u
    pd.DataFrame(fit_rows).to_csv(OUT / "model_fit_by_group.csv", index=False)

    param_rows = []
    for fit in fits:
        p = fit["params"]
        for j, group in enumerate(group_names):
            param_rows.append(
                {
                    "model": fit["model"],
                    "group": group,
                    "alpha": p["alpha"][j],
                    "beta": p["beta"][j],
                    "delta": p["delta"][j],
                    "tau": p["tau"][j],
                    "omega": p["omega"],
                    "kappa": p["kappa"],
                    "nll": fit["nll"],
                    "success": bool(fit["result"].success),
                    "message": str(fit["result"].message),
                }
            )
    pd.DataFrame(param_rows).to_csv(OUT / "parameter_estimates.csv", index=False)

    main = fits[1]
    p_mean = panel[panel["year"] == 2023][[f"p_{g}_model" for g in group_names]].mean().to_numpy(float)
    m_support_min = float(panel["m"].min())
    m_support_max = float(panel["m"].max())
    income_grid = np.array(
        sorted(
            set(
                list(np.quantile(panel["m"], [0.05, 0.25, 0.5, 0.75, 0.95]))
                + [10000, 20000, 30000, 50000, 80000, 120000, 160000, 200000]
            )
        )
    )
    el_rows = []
    exp_el_rows = []
    price_m_rows = []
    price_h_rows = []
    consistency_rows = []
    for m in income_grid:
        try:
            eta, xhat, u, phi = elasticity_for_point(p_mean, float(m), main["params"])
            mar, hic, eta_p, budget_shares, _ = price_elasticities_for_point(p_mean, float(m), main["params"])
        except Exception:
            continue
        for j, group in enumerate(group_names):
            budget_share = p_mean[j] * xhat[j] / m
            el_rows.append(
                {
                    "income": m,
                    "group": group,
                    "eta": eta[j],
                    "quantity_2000kcal_elasticity": eta[j],
                    "expenditure_elasticity": eta[j],
                    "budget_share_elasticity": eta[j] - 1,
                    "xhat": xhat[j],
                    "budget_share": budget_share,
                    "u": u,
                    "phi": phi[j],
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
            )
            exp_el_rows.append(
                {
                    "income": m,
                    "group": group,
                    "quantity_2000kcal_elasticity": eta[j],
                    "expenditure_elasticity": eta[j],
                    "budget_share_elasticity": eta[j] - 1,
                    "budget_share": budget_share,
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
            )
        for i, group_i in enumerate(group_names):
            for j, group_j in enumerate(group_names):
                base = {
                    "income": m,
                    "demand_group": group_i,
                    "price_group": group_j,
                    "is_own_price": group_i == group_j,
                    "budget_share_demand_group": budget_shares[i],
                    "budget_share_price_group": budget_shares[j],
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
                price_m_rows.append({**base, "elasticity": mar[i, j]})
                price_h_rows.append({**base, "elasticity": hic[i, j]})
        consistency_rows.append(
            elasticity_consistency_row(
                "income_grid",
                float(m),
                group_names,
                mar,
                hic,
                eta_p,
                budget_shares,
            )
        )
        food_eta = float(np.average(eta[:-1], weights=xhat[:-1]))
        food_exp_eta = float(np.average(eta[:-1], weights=p_mean[:-1] * xhat[:-1]))
        animal_idx = [group_names.index("pork"), group_names.index("meatother"), group_names.index("dairyegg")]
        plant_idx = [group_names.index("grain"), group_names.index("oil"), group_names.index("vegfruit")]
        aggregates = [
            ("all_food", list(range(len(group_names) - 1))),
            ("plant_food", plant_idx),
            ("animal_food", animal_idx),
        ]
        for agg_name, idx in aggregates:
            q_eta = float(np.average(eta[idx], weights=xhat[idx]))
            e_eta = float(np.average(eta[idx], weights=p_mean[idx] * xhat[idx]))
            bshare = float(np.dot(p_mean[idx], xhat[idx]) / m)
            el_rows.append(
                {
                    "income": m,
                    "group": agg_name,
                    "eta": q_eta if agg_name != "all_food" else food_eta,
                    "quantity_2000kcal_elasticity": q_eta if agg_name != "all_food" else food_eta,
                    "expenditure_elasticity": e_eta if agg_name != "all_food" else food_exp_eta,
                    "budget_share_elasticity": (e_eta if agg_name != "all_food" else food_exp_eta) - 1,
                    "xhat": xhat[idx].sum(),
                    "budget_share": bshare,
                    "u": u,
                    "phi": np.nan,
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
            )
            exp_el_rows.append(
                {
                    "income": m,
                    "group": agg_name,
                    "quantity_2000kcal_elasticity": q_eta if agg_name != "all_food" else food_eta,
                    "expenditure_elasticity": e_eta if agg_name != "all_food" else food_exp_eta,
                    "budget_share_elasticity": (e_eta if agg_name != "all_food" else food_exp_eta) - 1,
                    "budget_share": bshare,
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
            )
    pd.DataFrame(el_rows).to_csv(OUT / "elasticity_income_grid.csv", index=False)
    pd.DataFrame(exp_el_rows).to_csv(OUT / "elasticity_expenditure_grid.csv", index=False)
    pd.DataFrame(price_m_rows).to_csv(OUT / "elasticity_price_marshallian_grid.csv", index=False)
    pd.DataFrame(price_h_rows).to_csv(OUT / "elasticity_price_hicksian_grid.csv", index=False)
    pd.DataFrame(consistency_rows).to_csv(OUT / "elasticity_consistency_tests.csv", index=False)

    obs_el_rows = []
    for r in range(arr.x.shape[0]):
        eta, xhat, u, phi = elasticity_for_point(arr.p[r], arr.m[r], main["params"])
        for j, group in enumerate(group_names):
            obs_el_rows.append(
                {
                    "obs_id": arr.obs_ids[r],
                    "province": arr.provinces[r],
                    "year": arr.years[r],
                    "group": group,
                    "eta": eta[j],
                    "quantity_2000kcal_elasticity": eta[j],
                    "expenditure_elasticity": eta[j],
                    "budget_share_elasticity": eta[j] - 1,
                    "xhat": xhat[j],
                    "observed_x": arr.x[r, j],
                    "u": u,
                    "support_flag": "in_support",
                }
            )
    pd.DataFrame(obs_el_rows).to_csv(OUT / "elasticity_observed_points.csv", index=False)

    prediction = build_projection(panel, main["params"], nutrition)
    prediction["projection_group"].to_csv(OUT / "projection_group_2030_2035_2050.csv", index=False)
    prediction["projection_items"].to_csv(OUT / "projection_item_feed_2030_2035_2050.csv", index=False)
    prediction["projection_path"].to_csv(OUT / "projection_province_path.csv", index=False)
    prediction["projection_growth_path"].to_csv(OUT / "projection_growth_path.csv", index=False)
    write_method_reports(panel, prediction)

    manifest = {
        "models": [
            {
                "model": fit["model"],
                "nll": fit["nll"],
                "success": bool(fit["result"].success),
                "message": str(fit["result"].message),
            }
            for fit in fits
        ],
        "n_obs": int(arr.x.shape[0]),
        "n_goods": int(arr.x.shape[1]),
        "groups": group_names,
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def group_item_shares(panel_base: pd.DataFrame, nutrition: pd.DataFrame) -> pd.DataFrame:
    # Rebuild item-level 2023 shares from the original data for projection allocation.
    data = pd.read_stata(ROOT / "ProvinceData" / "workdata" / "data.dta")
    data = data[data["year"] == 2023].copy()
    _, grain_kcal = read_grain_weights(nutrition)
    kcal_lookup = dict(zip(nutrition["code"], nutrition["kcal_per_kg_as_purchased"]))
    kcal_lookup["GRAIN"] = grain_kcal
    kcal_lookup["OIL"] = float(
        nutrition.loc[nutrition["code"].isin(["SOYO", "RAPO", "GRDO"]), "kcal_per_kg_as_purchased"].mean()
    )
    rows = []
    for item, spec in FOOD_ITEMS.items():
        group = next(g for g, items in GROUPS.items() if item in items)
        kcal_kg = kcal_lookup[spec["code"]]
        tmp = data[["province", "provincechn"]].copy()
        tmp["item"] = item
        tmp["group"] = group
        tmp["kg"] = numeric(data[spec["q"]])
        tmp["kcal"] = tmp["kg"] * kcal_kg
        tmp["kcal_per_kg"] = kcal_kg
        rows.append(tmp)
    out = pd.concat(rows, ignore_index=True)
    totals = out.groupby(["province", "group"], as_index=False)["kcal"].sum().rename(columns={"kcal": "group_kcal"})
    out = out.merge(totals, on=["province", "group"], how="left")
    out["kcal_share"] = out["kcal"] / out["group_kcal"]
    return out


def build_projection(panel: pd.DataFrame, params: dict[str, np.ndarray | float], nutrition: pd.DataFrame) -> dict[str, pd.DataFrame]:
    group_names = list(GROUPS.keys())
    base = panel[panel["year"] == 2023].copy()
    forecast = read_forecast()
    population_projection = read_provincial_population_projection("SSP2")
    targets = [2030, 2035, 2050]
    forecast = forecast[forecast["year"].between(2025, 2050)].copy()
    population_targets = population_projection[population_projection["year"].isin(targets)].copy()
    pop_lookup = {
        (int(r.province), int(r.year)): float(r.population_10k)
        for r in population_targets.itertuples()
    }
    pop_total_lookup = population_targets.groupby("year")["population_10k"].sum().to_dict()

    # The forecast file starts in 2025. Use the first available growth rate as a
    # 2024 bridge and record that assumption explicitly.
    first_growth = float(forecast.loc[forecast["year"] == forecast["year"].min(), "gdp_growth_pct"].iloc[0]) / 100
    growth = {2024: first_growth}
    growth.update({int(r.year): float(r.gdp_growth_pct) / 100 for r in forecast.itertuples()})

    national_m = float(np.average(base["m"], weights=base["population_10k"]))
    national_m_path = {}
    m_nat = national_m
    for year in range(2024, 2051):
        m_nat *= 1 + growth.get(year, 0.0)
        national_m_path[year] = m_nat

    future_rows = []
    growth_rows = []
    for _, row in base.iterrows():
        m = float(row["m"])
        for year in range(2024, 2051):
            gap = math.log(max(national_m_path[year], 1e-9)) - math.log(max(m, 1e-9))
            convergence_adjustment = float(np.clip(0.02 * gap, -0.015, 0.015))
            income_growth = growth.get(year, 0.0) + convergence_adjustment
            m *= 1 + income_growth
            growth_rows.append(
                {
                    "province": int(row["province"]),
                    "provincechn": row["provincechn"],
                    "year": year,
                    "national_growth_rate_used": growth.get(year, 0.0),
                    "province_income_growth_rate_used": income_growth,
                    "convergence_adjustment": convergence_adjustment,
                    "income_growth_source": "bridge_first_available_forecast_plus_convergence"
                    if year == 2024
                    else "national_forecast_plus_convergence",
                    "population_share_source": "chen_guo_wang_2020_ssp2_provincial_projection",
                    "population_scenario": "SSP2",
                    "population_projection_source": POPULATION_PROJECTION_SOURCE,
                }
            )
            if year in targets:
                pop = pop_lookup.get((int(row["province"]), year), np.nan)
                total_pop = pop_total_lookup.get(year, np.nan)
                pop_share = pop / total_pop if total_pop and not pd.isna(pop) else np.nan
                future_rows.append(
                    {
                        "province": int(row["province"]),
                        "provincechn": row["provincechn"],
                        "year": year,
                        "m": m,
                        "population_10k": pop,
                        "income_support_flag": support_flag(m, float(panel["m"].min()), float(panel["m"].max())),
                        "population_share_projected": pop_share,
                        "population_share_source": "chen_guo_wang_2020_ssp2_provincial_projection",
                        "population_scenario": "SSP2",
                        "population_projection_source": POPULATION_PROJECTION_SOURCE,
                        **{f"p_{g}_model": row[f"p_{g}_model"] for g in group_names},
                    }
                )
    growth_path = pd.DataFrame(growth_rows)
    future = pd.DataFrame(future_rows)
    arr = ModelArrays(
        obs_ids=(future["province"].astype(str) + "_" + future["year"].astype(str)).to_numpy(),
        provinces=future["province"].to_numpy(int),
        years=future["year"].to_numpy(int),
        group_names=group_names,
        x=np.zeros((future.shape[0], len(group_names))),
        p=future[[f"p_{g}_model" for g in group_names]].to_numpy(float),
        m=future["m"].to_numpy(float),
    )
    xhat, u = predict_x(params, arr)
    if xhat is None:
        raise ValueError("Projection failed to solve.")
    for j, group in enumerate(group_names):
        future[f"xhat_{group}"] = xhat[:, j]
        if group == "nonfood":
            future[f"daily_kcal_{group}"] = np.nan
            future[f"annual_kcal_total_{group}"] = np.nan
        else:
            future[f"daily_kcal_{group}"] = xhat[:, j] * 2000
            future[f"annual_kcal_total_{group}"] = xhat[:, j] * 2000 * 365 * future["population_10k"] * 10000
    future["u"] = u

    rows = []
    for _, row in future.iterrows():
        for group in group_names:
            rows.append(
                {
                    "province": row["province"],
                    "provincechn": row["provincechn"],
                    "year": row["year"],
                    "group": group,
                    "xhat_per_cap": row[f"xhat_{group}"],
                    "daily_kcal_per_cap": row[f"daily_kcal_{group}"],
                    "annual_kcal_total": row[f"annual_kcal_total_{group}"],
                    "population_10k": row["population_10k"],
                    "m": row["m"],
                    "income_support_flag": row["income_support_flag"],
                    "population_share_projected": row["population_share_projected"],
                    "population_share_source": row["population_share_source"],
                    "population_scenario": row["population_scenario"],
                    "population_projection_source": row["population_projection_source"],
                }
            )
    group_proj = pd.DataFrame(rows)
    national = group_proj.groupby(["year", "group"], as_index=False).agg(
        daily_kcal_per_cap_weighted=("daily_kcal_per_cap", lambda s: np.nan),
        annual_kcal_total=("annual_kcal_total", lambda s: s.sum(min_count=1)),
        xhat_per_cap_weighted=("xhat_per_cap", lambda s: np.nan),
        population_10k=("population_10k", "sum"),
        m_mean=("m", "mean"),
        population_scenario=("population_scenario", "first"),
        population_projection_source=("population_projection_source", "first"),
    )
    # Recompute weighted daily kcal and model quantity explicitly.
    national_weighted = []
    for (year, group), tmp in group_proj.groupby(["year", "group"]):
        w = tmp["population_10k"].to_numpy(float)
        kcal = tmp["daily_kcal_per_cap"].to_numpy(float)
        xidx = tmp["xhat_per_cap"].to_numpy(float)
        national_weighted.append(
            {
                "year": year,
                "group": group,
                "daily_kcal_per_cap_weighted": np.nan if np.all(pd.isna(kcal)) else float(np.average(kcal[~pd.isna(kcal)], weights=w[~pd.isna(kcal)])),
                "xhat_per_cap_weighted": float(np.average(xidx, weights=w)),
            }
        )
    nw = pd.DataFrame(national_weighted)
    national = national.drop(columns=["daily_kcal_per_cap_weighted", "xhat_per_cap_weighted"]).merge(nw, on=["year", "group"])

    shares = group_item_shares(panel, nutrition)
    item_rows = []
    for _, row in future.iterrows():
        pshares = shares[shares["province"] == row["province"]]
        for _, sh in pshares.iterrows():
            if sh["item"] not in FEED_COEFF:
                continue
            group_kcal_day = row[f"daily_kcal_{sh['group']}"]
            item_kcal_day = group_kcal_day * sh["kcal_share"]
            kg_per_cap_year = item_kcal_day * 365 / sh["kcal_per_kg"]
            total_kg = kg_per_cap_year * row["population_10k"] * 10000
            feed_coeff = FEED_COEFF.get(sh["item"], 0.0)
            cereal_share = FEED_CEREAL_SHARE.get(sh["item"], 1.0)
            feed = total_kg * feed_coeff * cereal_share
            item_rows.append(
                {
                    "province": row["province"],
                    "provincechn": row["provincechn"],
                    "year": row["year"],
                    "group": sh["group"],
                    "item": sh["item"],
                    "kg_per_cap_year": kg_per_cap_year,
                    "total_kg": total_kg,
                    "feed_kg_per_kg_product": feed_coeff,
                    "feed_cereal_share": cereal_share,
                    "feed_grain_kg": feed,
                    "feed_coefficient_source": "user_supplied_feed_grain_equivalent_coefficients",
                }
            )
    items = pd.DataFrame(item_rows)
    feed_nat = items.groupby(["year", "item"], as_index=False).agg(
        total_kg=("total_kg", "sum"),
        feed_kg_per_kg_product=("feed_kg_per_kg_product", "first"),
        feed_cereal_share=("feed_cereal_share", "first"),
        feed_grain_kg=("feed_grain_kg", "sum"),
        feed_coefficient_source=("feed_coefficient_source", "first"),
    )
    return {
        "projection_group": national,
        "projection_items": feed_nat,
        "projection_path": future,
        "projection_growth_path": growth_path,
    }


def markdown_table(df: pd.DataFrame, digits: int = 6) -> str:
    if df.empty:
        return "_No rows._"
    tmp = df.copy()
    for col in tmp.select_dtypes(include=[np.number]).columns:
        tmp[col] = tmp[col].map(lambda x: "" if pd.isna(x) else f"{x:.{digits}g}")
    tmp = tmp.fillna("").astype(str)
    headers = [str(col) for col in tmp.columns]
    rows = tmp.values.tolist()
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def write_method_reports(panel: pd.DataFrame, prediction: dict[str, pd.DataFrame]) -> None:
    budget_error = panel["m"] - panel["covered_food_exp"] - panel["nonfood_exp"]
    quality_lines = [
        "# 数据质量与口径核查",
        "",
        "## 预算恒等式",
        "",
        f"- 最大绝对预算残差：{float(np.nanmax(np.abs(budget_error))):.6g}",
        f"- 覆盖食品支出份额均值：{float(panel['covered_food_budget_share'].mean()):.6g}",
        f"- 覆盖食品每日 kcal 均值：{float(panel['covered_daily_kcal'].mean()):.6g}",
        f"- 覆盖食品每日 kcal 最小/最大：{float(panel['covered_daily_kcal'].min()):.6g} / {float(panel['covered_daily_kcal'].max()):.6g}",
        "",
        "## 价格与金额口径",
        "",
        "- 主估计使用 2023 年实际价口径：总支出用省级总 CPI 平减，食品价格用省级食品 CPI 平减。",
        "- 主估计非覆盖支出价格使用全国非食品 CPI，2023=100；省级反推非食品 CPI 仅作稳健性。",
        "- `nonfood` 在模型内部保留为兼容变量名，经济含义为“其他/未覆盖支出”，包含未覆盖食品、烟酒、在外就餐和真正非食品。",
        "",
        "## 样本支撑",
        "",
        f"- 实际消费支出 m 的样本范围：{float(panel['m'].min()):.6g} 到 {float(panel['m'].max()):.6g}。",
        "- 弹性和预测表中的 `support_flag` / `income_support_flag` 标明样本支撑内估计或外推。",
    ]
    (OUT / "data_quality_report.md").write_text("\n".join(quality_lines), encoding="utf-8")

    if (DATA_OUT / "province_cpi_indices.csv").exists():
        cpi = pd.read_csv(DATA_OUT / "province_cpi_indices.csv")
        if "nonfood_price_source" in cpi.columns:
            source_counts = cpi["nonfood_price_source"].value_counts(dropna=False).reset_index()
            source_counts.columns = ["source", "n_rows"]
        else:
            source_counts = pd.DataFrame()
        cpi_lines = [
            "# 非食品 CPI 质量报告",
            "",
            "- 主估计使用全国非食品 CPI，避免用被解释变量相关的食品支出份额反推主价格。",
            "- 稳健性口径使用省级总 CPI、食品 CPI 与食品支出份额反推省级非食品 CPI，标记为 approximate。",
            "- 全国非食品 CPI 的 2015 年指数由 2016 年同比向前反推。",
            "",
            "## 省级反推来源计数",
            "",
            markdown_table(source_counts) if not source_counts.empty else "_未生成来源计数。_",
        ]
        (OUT / "nonfood_cpi_quality_report.md").write_text("\n".join(cpi_lines), encoding="utf-8")

    feed_lines = [
        "# 饲料粮需求方法说明",
        "",
        "- 本轮 `projection_item_feed_2030_2035_2050.csv` 只输出动物产品 item。",
        "- 用户提供的系数被解释为“饲料粮等价 kg / kg 产品”：猪肉 3.88，禽肉 3.10，蛋 2.46，奶 0.62，水产品 1.35，牛肉和羊肉 9.80。",
        "- 代码保留 `feed_cereal_share` 字段；当前因输入已经是饲料粮系数，设为 1.0。若后续换成总饲料系数，应补充各产品谷物占比。",
        "- 产品拆分使用 2023 年各省组内动物产品 kcal 份额，并固定到预测期。",
    ]
    (OUT / "feed_demand_method.md").write_text("\n".join(feed_lines), encoding="utf-8")

    audit_lines = [
        "# CODE_AUDIT_FIX_REPORT",
        "",
        "| 审查项 | 本轮处理 | 输出文件 | 剩余限制 |",
        "| --- | --- | --- | --- |",
        "| A1/OOS 指标广播 | 已改为按 variant/model/split/group 输出；追加脚本会重跑 AIDADS 与 MAIDADS | `oos_fit_by_group.csv`, `oos_predictions.csv` | 朴素基线、留一省/留一区域仍待增强 |",
        "| A2/bootstrap 过少 | 追加正式规模 `run_formal_bootstrap.py`，记录省份簇 bootstrap 成功率与区间 | `bootstrap_*`, `FormalBootstrap/*` | 若模型或数据变更，需重新跑正式规模 bootstrap |",
        "| A3/LR χ² 不合法 | 删除把 χ² p 作为最终证据的表述，追加 cluster bootstrap LR；普通 χ² p 不报告 | `lr_test_chi2_and_bootstrap.csv` | 严格 parametric-null bootstrap 仍可增强 |",
        "| A4/价格口径 | 主估计改为 2023 实际价；食品价格和总支出分别用食品/总 CPI 平减 | `maidads6_panel.csv` | 缺分项食品 CPI |",
        "| A5/省级预测路径 | 人口路径改用 Chen et al. (2020) Sci Data 的 SSP2 省级人口预测；收入仍用全国增长率加省份收敛情景 | `projection_growth_path.csv`, `Data/output/provincial_population_projection_ssp2.csv` | 需补正式分省收入、城镇化和年龄结构预测 |",
        "| A6/价格弹性与一致性 | 新增 Marshallian/Hicksian 价格弹性和理论一致性误差表 | `elasticity_price_*`, `elasticity_consistency_tests.csv` | 解析式(7)(8)单元测试仍可进一步补强 |",
        "| B3/饲料粮 | 只输出动物产品，并保留 feed_cereal_share 字段 | `feed_demand_method.md` | 若系数为总饲料而非饲料粮，需补谷物占比 |",
        "| B4/未覆盖食品 | 把展示标签改为其他/未覆盖支出，并写入口径说明 | `data_quality_report.md` | 需外部总热量/FAOSTAT 对账 |",
        "| B5/grain kcal | 马铃薯 /5 只保留为粮食当量权重，热量按实际 kcal/kg 加权 | `grain_weights_processed.csv` | 仍缺分省主粮细类结构 |",
    ]
    (OUT / "CODE_AUDIT_FIX_REPORT.md").write_text("\n".join(audit_lines), encoding="utf-8")


def write_summary(manifest: dict) -> None:
    params = pd.read_csv(OUT / "parameter_estimates.csv")
    fit = pd.read_csv(OUT / "model_fit_by_group.csv")
    elast = pd.read_csv(OUT / "elasticity_income_grid.csv")
    price_m = pd.read_csv(OUT / "elasticity_price_marshallian_grid.csv")
    consistency = pd.read_csv(OUT / "elasticity_consistency_tests.csv")
    proj = pd.read_csv(OUT / "projection_group_2030_2035_2050.csv")
    feed = pd.read_csv(OUT / "projection_item_feed_2030_2035_2050.csv")
    lines = []
    lines.append("# 中国省级 MAIDADS 估计结果总览")
    lines.append("")
    lines.append("## 一、运行状态")
    lines.append("")
    lines.append(f"- 样本：{manifest['n_obs']} 个省-年观测，{manifest['n_goods']} 个消费组。")
    lines.append(f"- 消费组：{', '.join(manifest['groups'])}。")
    for m in manifest["models"]:
        lines.append(f"- {m['model']}: nll={m['nll']:.3f}, success={m['success']}, message={m['message']}")
    lines.append("")
    lines.append("## 二、核心数据口径")
    lines.append("")
    lines.append("- 食物数量统一换算为每日每人 2000 kcal 的数量单位；非食品为支出余额除以价格指数后的数量指数。")
    lines.append("- 主估计采用 2023 年实际价口径：总支出用省级总 CPI 平减，食品价格用省级食品 CPI 平减，保证 `price * quantity = real expenditure`。")
    lines.append("- 营养换算使用 `营养成分表.csv`，先乘以可食用部分；能量缺失或为 0 时用 `4*蛋白质 + 9*脂肪 + 4*碳水化合物` 补算。")
    lines.append("- 主粮聚合权重来自 `粮食细类消费.csv`；大豆和马铃薯计入粮食。马铃薯 `/5` 只保留为粮食当量权重，热量换算使用实际 kcal/kg。")
    lines.append("- 预测使用全国收入增长路径作为外生基准，并加入省份收入收敛情景；省级人口路径使用 Chen et al. (2020) Sci Data 的 SSP2 省级人口预测。")
    lines.append("- 主估计非覆盖支出价格使用全国非食品 CPI；省级反推非食品 CPI 只作为稳健性。")
    lines.append("")
    lines.append("## 三、MAIDADS 参数估计")
    lines.append(markdown_table(params[params["model"] == "MAIDADS_sat"]))
    lines.append("")
    lines.append("## 四、分组拟合误差")
    lines.append(markdown_table(fit))
    lines.append("")
    lines.append("## 五、收入弹性")
    lines.append("")
    lines.append("收入弹性使用同一 MAIDADS 预测函数做中心差分计算，避免解析导数在当前尺度下不稳定。")
    selected = elast[elast["income"].isin(sorted(elast["income"].unique())[:: max(1, len(elast["income"].unique()) // 8)])]
    lines.append(markdown_table(selected.pivot_table(index="group", columns="income", values="eta").reset_index()))
    lines.append("")
    lines.append("## 六、价格弹性与理论一致性")
    lines.append("")
    own_price = price_m[price_m["is_own_price"].astype(bool)].copy()
    lines.append("Marshallian 自价格弹性如下；MAIDADS 的价格弹性由 LES 型预算结构机械决定，不作为本文方法贡献。")
    lines.append(markdown_table(own_price.pivot_table(index="demand_group", columns="income", values="elasticity").reset_index()))
    lines.append("")
    lines.append("理论一致性误差摘要：")
    lines.append(markdown_table(consistency.describe(include="all").reset_index()))
    lines.append("")
    lines.append("## 七、全国加权预测：每日每人 kcal")
    lines.append(markdown_table(proj.pivot_table(index="group", columns="year", values="daily_kcal_per_cap_weighted").reset_index()))
    lines.append("")
    lines.append("非食品是模型数量指数，不是 kcal；因此非食品的每日 kcal 项留空。")
    lines.append("")
    lines.append("## 八、动物产品对应饲料粮需求：百万吨")
    feed2 = feed.copy()
    feed2["feed_grain_million_ton"] = feed2["feed_grain_kg"] / 1e9
    lines.append(markdown_table(feed2.pivot_table(index="item", columns="year", values="feed_grain_million_ton").reset_index()))
    lines.append("")
    lines.append("## 九、主要结果文件")
    lines.append("")
    lines.append("- `parameter_estimates.csv`：AIDADS 与 MAIDADS 的参数估计。")
    lines.append("- `model_fit_by_group.csv`：分消费组 RMSE/MAE 拟合误差。")
    lines.append("- `elasticity_income_grid.csv`：不同收入水平的收入弹性。")
    lines.append("- `elasticity_expenditure_grid.csv`：数量/支出/预算份额三种支出弹性口径。")
    lines.append("- `elasticity_price_marshallian_grid.csv`、`elasticity_price_hicksian_grid.csv`：价格弹性矩阵。")
    lines.append("- `elasticity_consistency_tests.csv`：加总、齐次性与 Slutsky 对称性误差。")
    lines.append("- `elasticity_observed_points.csv`：每个省-年观测点的收入弹性。")
    lines.append("- `projection_group_2030_2035_2050.csv`：2030/2035/2050 分组全国加权预测。")
    lines.append("- `projection_item_feed_2030_2035_2050.csv`：动物产品总量和饲料粮需求预测。")
    lines.append("- `projection_province_path.csv`：省级 2030/2035/2050 预测路径。")
    lines.append("- `projection_growth_path.csv`：预测收入增长路径和 2024 桥接假设。")
    lines.append("- `multistart_diagnostics.csv`、`parameter_boundary_report.csv`、`best_solution_gradient_report.csv`：估计收敛与边界诊断。")
    lines.append("- `data_quality_report.md`、`nonfood_cpi_quality_report.md`、`feed_demand_method.md`、`CODE_AUDIT_FIX_REPORT.md`：审计和方法说明。")
    lines.append("")
    lines.append("## 十、重要限制")
    lines.append("")
    lines.append("- 本机 PATH 中没有 `gams`，因此使用 Python Track-P 复现 MAIDADS，而不是原 GAMS 程序。")
    lines.append("- 本轮预测已接入 Chen et al. (2020) SSP2 省级人口预测；收入、城镇化和年龄结构路径仍需进一步补充。")
    lines.append("- 2024 收入增长因预测文件从 2025 年开始，使用首个可得预测增速桥接；该假设已写入 `projection_growth_path.csv`。")
    lines.append("- 省级非食品 CPI 仍为由总 CPI、食品 CPI 与食品支出份额反推的近似值；本轮已把它降为稳健性口径，若后续取得直接省级非食品 CPI，应替换该口径。")
    (OUT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ensure_dirs()
    panel, _, nutrition = build_model_data()
    arr = panel_to_arrays(panel)
    fits = fit_model(arr)
    manifest = build_results(panel, arr, fits, nutrition)
    write_summary(manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
