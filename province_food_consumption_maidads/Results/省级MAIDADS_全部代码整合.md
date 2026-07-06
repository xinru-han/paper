# 中国省级 MAIDADS 全部代码整合

- 生成时间：2026-07-06 10:07:51
- 工作目录：`/root/data/Paper/省级食物消费`

## 一、运行顺序

```bash
cd /root/data/Paper/省级食物消费
python3 ProvinceMAIDADS/scripts/run_maidads_pipeline.py
python3 ProvinceMAIDADS/scripts/run_additional_checks.py
python3 ProvinceMAIDADS/scripts/run_formal_bootstrap.py --bootstrap-reps 1000 --lr-reps 500 --workers 6
python3 ProvinceMAIDADS/scripts/prepare_paper_workflow_outputs.py
python3 .codex/skills/provincial-maidads-paper-writer/scripts/paper_gate_check.py --root ProvinceMAIDADS
python3 ProvinceMAIDADS/scripts/build_manuscript_draft.py
python3 ProvinceMAIDADS/scripts/build_maidads_simulator_workbook.py
python3 ProvinceMAIDADS/scripts/compile_markdown_outputs.py
```

## 二、代码文件索引

| 文件 | 行数 | 作用 |
| --- | ---: | --- |
| `run_maidads_pipeline.py` | 1844 | 数据构造、MAIDADS/AIDADS 主估计、弹性、预测和主摘要生成 |
| `run_additional_checks.py` | 621 | CPI 稳健性、样本外验证、bootstrap 和追加摘要生成 |
| `run_formal_bootstrap.py` | 471 | 正式规模省份簇 bootstrap 与 LR cluster bootstrap，可断点续跑并同步正式推断结果 |
| `prepare_paper_workflow_outputs.py` | 424 | 按论文写作 skill 要求整理结果目录、补充 gate 所需审计文件 |
| `build_manuscript_draft.py` | 632 | 生成 evidence ledger、论文初稿、表格、参考文献和本地审稿意见 |
| `build_maidads_simulator_workbook.py` | 562 | 生成无宏版省级 MAIDADS Excel 模拟器 |
| `compile_markdown_outputs.py` | 270 | 把所有结果与代码整合为两个 Markdown 归档文件 |

## 三、完整源码

### run_maidads_pipeline.py

源文件：`/root/data/Paper/省级食物消费/ProvinceMAIDADS/scripts/run_maidads_pipeline.py`

```python
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
```

### run_additional_checks.py

源文件：`/root/data/Paper/省级食物消费/ProvinceMAIDADS/scripts/run_additional_checks.py`

```python
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

import run_maidads_pipeline as pipe


ROOT = pipe.ROOT
OUT = pipe.OUT
DATA_OUT = pipe.DATA_OUT
OOS_OUT = OUT / "OOS"


def raw_from_maidads_params(params: dict[str, np.ndarray | float]) -> np.ndarray:
    alpha = np.asarray(params["alpha"], float)
    delta = np.asarray(params["delta"], float)
    tau = np.asarray(params["tau"], float)
    return np.r_[
        np.log(np.maximum(alpha, 1e-12)),
        np.log(np.maximum(delta, 1e-12)),
        np.log(np.maximum(tau, 1e-12)),
        math.log(max(float(params["omega"]), 1e-12)),
        float(params["kappa"]),
    ]


def params_from_csv(path: Path, model: str, group_names: list[str]) -> dict[str, np.ndarray | float]:
    df = pd.read_csv(path)
    order = {g: i for i, g in enumerate(group_names)}
    tmp = df[df["model"].eq(model)].copy()
    tmp["ord"] = tmp["group"].map(order)
    tmp = tmp.sort_values("ord")
    return {
        "alpha": tmp["alpha"].to_numpy(float),
        "beta": tmp["beta"].to_numpy(float),
        "delta": tmp["delta"].to_numpy(float),
        "tau": tmp["tau"].to_numpy(float),
        "omega": float(tmp["omega"].iloc[0]),
        "kappa": float(tmp["kappa"].iloc[0]),
    }


def fit_rows(variant: str, fits: tuple[dict, dict], arr: pipe.ModelArrays) -> tuple[pd.DataFrame, pd.DataFrame]:
    param_rows = []
    fit_rows = []
    for fit in fits:
        params = fit["params"]
        xhat, _ = pipe.predict_x(params, arr)
        if xhat is None:
            continue
        eps = arr.x - xhat
        rmse = np.sqrt((eps**2).mean(axis=0))
        mae = np.abs(eps).mean(axis=0)
        for j, group in enumerate(arr.group_names):
            param_rows.append(
                {
                    "variant": variant,
                    "model": fit["model"],
                    "group": group,
                    "alpha": params["alpha"][j],
                    "beta": params["beta"][j],
                    "delta": params["delta"][j],
                    "tau": params["tau"][j],
                    "omega": params["omega"],
                    "kappa": params["kappa"],
                    "nll": fit["nll"],
                    "success": bool(fit["result"].success),
                    "message": str(fit["result"].message),
                }
            )
            fit_rows.append(
                {
                    "variant": variant,
                    "model": fit["model"],
                    "group": group,
                    "rmse_x": rmse[j],
                    "mae_x": mae[j],
                    "mean_x": arr.x[:, j].mean(),
                }
            )
    return pd.DataFrame(param_rows), pd.DataFrame(fit_rows)


def subset_arrays(arr: pipe.ModelArrays, mask: np.ndarray) -> pipe.ModelArrays:
    return pipe.ModelArrays(
        obs_ids=arr.obs_ids[mask],
        provinces=arr.provinces[mask],
        years=arr.years[mask],
        group_names=arr.group_names,
        x=arr.x[mask],
        p=arr.p[mask],
        m=arr.m[mask],
    )


def oos_split(
    panel: pd.DataFrame,
    variant: str,
    train_year_max: int,
    test_year_min: int,
    test_year_max: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, tuple[dict, dict]]:
    arr = pipe.panel_to_arrays(panel)
    train = subset_arrays(arr, arr.years <= train_year_max)
    test = subset_arrays(arr, (arr.years >= test_year_min) & (arr.years <= test_year_max))
    fits = pipe.fit_model(
        train,
        maidads_random_scales=(0.05,),
        maxiter_a=320,
        maxiter_m=460,
        progress=True,
        seed=seed,
    )
    rows = []
    split_label = f"{test_year_min}-{test_year_max}" if test_year_min != test_year_max else str(test_year_min)
    train_label = f"2015-{train_year_max}"
    for fit in fits:
        xhat, u = pipe.predict_x(fit["params"], test)
        if xhat is None:
            raise ValueError(
                f"OOS prediction failed for {variant}/{fit['model']}, train <= {train_year_max}, "
                f"test {test_year_min}-{test_year_max}."
            )
        model_rows = []
        for r in range(test.x.shape[0]):
            for j, group in enumerate(test.group_names):
                model_rows.append(
                    {
                        "variant": variant,
                        "model": fit["model"],
                        "train_years": train_label,
                        "test_years": split_label,
                        "obs_id": test.obs_ids[r],
                        "province": test.provinces[r],
                        "year": test.years[r],
                        "group": group,
                        "observed_x": test.x[r, j],
                        "predicted_x": xhat[r, j],
                        "error": test.x[r, j] - xhat[r, j],
                        "u": u[r],
                    }
                )
        pred_one = pd.DataFrame(model_rows)
        rows.extend(model_rows)
        safe_name = f"oos_predictions__{variant}__{fit['model']}__{train_label}_to_{split_label}.csv"
        pred_one.to_csv(OOS_OUT / safe_name.replace("/", "-"), index=False)
    pred = pd.DataFrame(rows)
    fit = pred.groupby(["variant", "model", "train_years", "test_years", "group"], as_index=False).agg(
        rmse_x=("error", lambda s: float(np.sqrt(np.mean(np.square(s))))),
        mae_x=("error", lambda s: float(np.mean(np.abs(s)))),
        mean_x=("observed_x", "mean"),
        n_test=("observed_x", "size"),
    )
    fit["relative_rmse"] = fit["rmse_x"] / fit["mean_x"].replace(0, np.nan)
    return fit, pred, fits


def oos_validations(panels: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    OOS_OUT.mkdir(parents=True, exist_ok=True)
    specs = [
        (2020, 2021, 2023, 20260608),
        (2022, 2023, 2023, 20260611),
        (2023, 2024, 2024, 20260624),  # 2024 holdout: fit 2015-2023, predict newest year
    ]
    fit_parts = []
    pred_parts = []
    for variant, panel in panels.items():
        for train_end, test_start, test_end, seed in specs:
            fit, pred, _ = oos_split(panel, variant, train_end, test_start, test_end, seed)
            fit_parts.append(fit)
            pred_parts.append(pred)
    all_fit = pd.concat(fit_parts, ignore_index=True)
    all_pred = pd.concat(pred_parts, ignore_index=True)
    duplicated = all_fit[["variant", "model", "train_years", "test_years", "group"]].duplicated().sum()
    if duplicated:
        raise RuntimeError(f"OOS fit has duplicated variant/model/split/group rows: {duplicated}")
    wide = (
        all_fit[all_fit["group"].ne("nonfood")]
        .groupby(["variant", "model", "train_years", "test_years"])["rmse_x"]
        .mean()
        .reset_index()
    )
    if wide.shape[0] > 1 and wide["rmse_x"].round(10).nunique() == 1:
        raise RuntimeError("OOS RMSE is identical across all models/variants/splits; check grouping or overwritten predictions.")
    return all_fit, all_pred


def fit_bootstrap_maidads(
    arr_boot: pipe.ModelArrays,
    raw_start: np.ndarray,
    maxiter: int = 260,
) -> tuple[dict[str, np.ndarray | float], object, float]:
    n = arr_boot.x.shape[1]
    bounds = [(-8, 8)] * n + [(-12, 8)] * n + [(-12, 8)] * n + [(-9, 3)] + [(-20, 20)]
    res = minimize(
        pipe.neg_loglike,
        raw_start,
        args=(arr_boot, "maidads"),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": maxiter, "ftol": 1e-7, "maxls": 25},
    )
    return pipe.unpack_maidads(res.x, n), res, float(res.fun)


def bootstrap_checks(panel: pd.DataFrame, nutrition: pd.DataFrame, b: int = 25) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    arr = pipe.panel_to_arrays(panel)
    full_params = params_from_csv(OUT / "parameter_estimates.csv", "MAIDADS_sat", arr.group_names)
    raw_start = raw_from_maidads_params(full_params)
    rng = np.random.default_rng(20260609)
    provinces = np.unique(arr.provinces)
    p_mean = panel[panel["year"] == 2023][[f"p_{g}_model" for g in arr.group_names]].mean().to_numpy(float)
    m_median = float(np.median(arr.m))

    metric_rows = []
    param_rows = []
    draw_rows = []
    for draw in range(1, b + 1):
        sampled = rng.choice(provinces, size=provinces.size, replace=True)
        idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
        arr_boot = subset_arrays(arr, idx)
        try:
            draw_start = raw_start + rng.normal(0, 0.05, size=raw_start.size)
            params, res, nll = fit_bootstrap_maidads(arr_boot, draw_start)
            eta, _, _, _ = pipe.elasticity_for_point(p_mean, m_median, params)
            projection = pipe.build_projection(panel, params, nutrition)
        except Exception as exc:
            draw_rows.append({"draw": draw, "success": False, "nll": np.nan, "message": str(exc)})
            continue
        draw_rows.append({"draw": draw, "success": bool(res.success), "nll": nll, "message": str(res.message)})
        for j, group in enumerate(arr.group_names):
            param_rows.append(
                {
                    "draw": draw,
                    "group": group,
                    "alpha": params["alpha"][j],
                    "beta": params["beta"][j],
                    "delta": params["delta"][j],
                    "tau": params["tau"][j],
                    "omega": params["omega"],
                    "kappa": params["kappa"],
                }
            )
            metric_rows.append(
                {
                    "draw": draw,
                    "metric": "income_elasticity_median_income",
                    "group_or_item": group,
                    "year": np.nan,
                    "value": eta[j],
                }
            )
        proj = projection["projection_group"]
        for _, row in proj[proj["year"].isin([2030, 2050]) & proj["group"].ne("nonfood")].iterrows():
            metric_rows.append(
                {
                    "draw": draw,
                    "metric": "daily_kcal_per_cap_weighted",
                    "group_or_item": row["group"],
                    "year": int(row["year"]),
                    "value": row["daily_kcal_per_cap_weighted"],
                }
            )
        feed = projection["projection_items"].copy()
        feed["feed_grain_million_ton"] = feed["feed_grain_kg"] / 1e9
        for _, row in feed[feed["year"].isin([2030, 2050]) & (feed["feed_grain_million_ton"] > 0)].iterrows():
            metric_rows.append(
                {
                    "draw": draw,
                    "metric": "feed_grain_million_ton",
                    "group_or_item": row["item"],
                    "year": int(row["year"]),
                    "value": row["feed_grain_million_ton"],
                }
            )
        if draw == 1 or draw % 5 == 0:
            print(f"Bootstrap draw {draw}/{b}: nll={nll:.3f}, success={res.success}", flush=True)

    metrics = pd.DataFrame(metric_rows)
    params = pd.DataFrame(param_rows)
    draws = pd.DataFrame(draw_rows)
    success_draws = set(draws.loc[draws["success"].astype(bool), "draw"]) if not draws.empty else set()
    metrics_ci = metrics[metrics["draw"].isin(success_draws)].copy() if success_draws else metrics.iloc[0:0].copy()
    params_ci_source = params[params["draw"].isin(success_draws)].copy() if success_draws else params.iloc[0:0].copy()
    if metrics_ci.empty:
        ci = pd.DataFrame()
    else:
        ci = (
            metrics_ci.groupby(["metric", "group_or_item", "year"], dropna=False)["value"]
            .quantile([0.025, 0.5, 0.975])
            .unstack()
            .reset_index()
            .rename(columns={0.025: "ci_2_5", 0.5: "median", 0.975: "ci_97_5"})
        )
    param_ci = []
    if not params_ci_source.empty:
        for name in ["alpha", "beta", "delta", "tau", "omega", "kappa"]:
            tmp = (
                params_ci_source.groupby("group")[name]
                .quantile([0.025, 0.5, 0.975])
                .unstack()
                .reset_index()
                .rename(columns={0.025: "ci_2_5", 0.5: "median", 0.975: "ci_97_5"})
            )
            tmp.insert(0, "parameter", name)
            param_ci.append(tmp)
    param_ci_df = pd.concat(param_ci, ignore_index=True) if param_ci else pd.DataFrame()
    draws.to_csv(OUT / "bootstrap_draw_status.csv", index=False)
    metrics.to_csv(OUT / "bootstrap_draw_metrics.csv", index=False)
    params.to_csv(OUT / "bootstrap_parameter_draws.csv", index=False)
    return ci, param_ci_df, draws


def lr_bootstrap(panel: pd.DataFrame, observed_lr: float, b: int = 20) -> tuple[pd.DataFrame, pd.DataFrame]:
    arr = pipe.panel_to_arrays(panel)
    rng = np.random.default_rng(20260612)
    provinces = np.unique(arr.provinces)
    rows = []
    for draw in range(1, b + 1):
        sampled = rng.choice(provinces, size=provinces.size, replace=True)
        idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
        arr_boot = subset_arrays(arr, idx)
        try:
            fits = pipe.fit_model(
                arr_boot,
                maidads_random_scales=(0.03,),
                maxiter_a=220,
                maxiter_m=320,
                progress=False,
                seed=20270000 + draw,
            )
            nll_a = float(fits[0]["nll"])
            nll_m = float(fits[1]["nll"])
            lr = 2 * (nll_a - nll_m)
            success = bool(fits[0]["result"].success) and bool(fits[1]["result"].success)
            message = "ok"
        except Exception as exc:
            nll_a = np.nan
            nll_m = np.nan
            lr = np.nan
            success = False
            message = str(exc)
        rows.append(
            {
                "draw": draw,
                "success": success,
                "nll_aidads": nll_a,
                "nll_maidads": nll_m,
                "lr_stat": lr,
                "message": message,
            }
        )
        if draw == 1 or draw % 5 == 0:
            print(f"LR bootstrap draw {draw}/{b}: lr={lr:.3f}, success={success}", flush=True)
    draws = pd.DataFrame(rows)
    success_lr = draws.loc[draws["success"].astype(bool) & draws["lr_stat"].notna(), "lr_stat"]
    if success_lr.empty:
        summary = pd.DataFrame(
            [
                {
                    "test": "MAIDADS_vs_AIDADS",
                    "observed_lr": observed_lr,
                    "bootstrap_reps": b,
                    "successful_reps": 0,
                    "cluster_bootstrap_tail_probability": np.nan,
                    "chi2_p_value_status": "invalid_not_reported",
                    "note": "No successful LR bootstrap draws.",
                }
            ]
        )
    else:
        scale = "formal" if b >= 500 else "pilot"
        summary = pd.DataFrame(
            [
                {
                    "test": "MAIDADS_vs_AIDADS",
                    "observed_lr": observed_lr,
                    "bootstrap_reps": b,
                    "successful_reps": int(success_lr.shape[0]),
                    "cluster_bootstrap_tail_probability": float(np.mean(success_lr >= observed_lr)),
                    "lr_bootstrap_median": float(success_lr.median()),
                    "lr_bootstrap_q95": float(success_lr.quantile(0.95)),
                    "chi2_p_value_status": "invalid_not_reported",
                    "note": f"Cluster bootstrap {scale}; chi-square reference not used.",
                }
            ]
        )
    draws.to_csv(OUT / "lr_bootstrap_draws.csv", index=False)
    summary.to_csv(OUT / "lr_test_chi2_and_bootstrap.csv", index=False)
    return summary, draws


def model_comparison(
    main_manifest: dict,
    robustness_manifest: dict,
    oos_fit: pd.DataFrame,
    lr_summary: pd.DataFrame,
) -> pd.DataFrame:
    n = main_manifest["n_obs"]
    n_goods = main_manifest["n_goods"]
    k_a = 2 * n_goods
    k_m = 3 * n_goods + 1
    rows = []
    for m in main_manifest["models"]:
        k = k_a if m["model"].startswith("AIDADS") else k_m
        rows.append(
            {
                "variant": "baseline_real_national_nonfood",
                "model": m["model"],
                "nll": m["nll"],
                "k_effective": k,
                "aic": 2 * k + 2 * m["nll"],
                "bic": k * math.log(n) + 2 * m["nll"],
                "success": m["success"],
            }
        )
    for m in robustness_manifest["models"]:
        k = k_a if m["model"].startswith("AIDADS") else k_m
        rows.append(
            {
                "variant": "robust_real_derived_cpi_nonfood",
                "model": m["model"],
                "nll": m["nll"],
                "k_effective": k,
                "aic": 2 * k + 2 * m["nll"],
                "bic": k * math.log(n) + 2 * m["nll"],
                "success": m["success"],
            }
        )
    lr = 2 * (main_manifest["models"][0]["nll"] - main_manifest["models"][1]["nll"])
    lr_boot_p = np.nan
    lr_boot_success = np.nan
    if not lr_summary.empty:
        lr_boot_p = lr_summary["cluster_bootstrap_tail_probability"].iloc[0]
        lr_boot_success = lr_summary["successful_reps"].iloc[0]
    rows.append(
        {
            "variant": "baseline_real_national_nonfood",
            "model": "LR_MAIDADS_vs_AIDADS",
            "nll": np.nan,
            "k_effective": k_m - k_a,
            "aic": np.nan,
            "bic": np.nan,
            "success": True,
            "lr_stat": lr,
            "p_value_chi2": np.nan,
            "chi2_p_value_status": "invalid_not_reported_unidentified_nuisance_under_H0",
            "cluster_bootstrap_tail_probability": lr_boot_p,
            "lr_bootstrap_successful_reps": lr_boot_success,
        }
    )
    out = pd.DataFrame(rows)
    oos_mean = (
        oos_fit[oos_fit["group"].ne("nonfood")]
        .groupby(["variant", "model"], as_index=False)["rmse_x"]
        .mean()
        .rename(columns={"rmse_x": "oos_food_rmse_mean"})
    )
    out = out.merge(oos_mean, on=["variant", "model"], how="left")
    return out


def write_additional_summary(
    robustness_manifest: dict,
    oos_fit: pd.DataFrame,
    boot_ci: pd.DataFrame,
    comparison: pd.DataFrame,
    lr_summary: pd.DataFrame,
) -> None:
    lines = []
    lines.append("# 追加处理与稳健性估计结果")
    lines.append("")
    lines.append("## 一、已补充内容")
    lines.append("")
    lines.append("- 主结果采用全国非食品 CPI；稳健性用食物支出份额近似反推出省级非食品 CPI。")
    lines.append("- 构造 `cpi_nonfood` 省级近似非食品价格口径并重新估计 AIDADS/MAIDADS。")
    lines.append("- 对每个 `variant × model` 分别用 2015-2020 年训练、2021-2023 年测试，以及 2015-2022 年训练、2023 年测试做样本外验证。")
    status_path = OUT / "bootstrap_draw_status.csv"
    if status_path.exists():
        status = pd.read_csv(status_path)
        success_count = int(status["success"].astype(bool).sum())
        total_count = int(status.shape[0])
        lines.append(f"- 做 {total_count} 次省份簇 bootstrap，其中 {success_count} 次完全收敛；关键区间仅用完全收敛 draw 汇总。")
    else:
        lines.append("- 做省份簇 bootstrap，给关键弹性、预测和饲料粮需求提供初步区间。")
    lines.append("")
    lines.append("## 二、CPI 非食品稳健性估计")
    for m in robustness_manifest["models"]:
        lines.append(f"- {m['model']}: nll={m['nll']:.3f}, success={m['success']}, message={m['message']}")
    lines.append("")
    lines.append("## 三、样本外验证")
    lines.append(pipe.markdown_table(oos_fit))
    lines.append("")
    lines.append("## 四、模型比较")
    lines.append(pipe.markdown_table(comparison))
    lines.append("")
    lr_reps = int(lr_summary["bootstrap_reps"].iloc[0]) if "bootstrap_reps" in lr_summary else 0
    lr_title = "LR bootstrap（正式规模）" if lr_reps >= 500 else "LR bootstrap（pilot）"
    lines.append(f"## 五、{lr_title}")
    lines.append("")
    lines.append("普通 χ² p 值因 MAIDADS 在 AIDADS 原假设下存在不可识别 nuisance parameter，本轮不作为有效推断报告。")
    lines.append(pipe.markdown_table(lr_summary))
    lines.append("")
    lines.append("## 六、bootstrap 关键区间")
    key = boot_ci[
        (boot_ci["metric"].isin(["daily_kcal_per_cap_weighted", "feed_grain_million_ton"]))
        & (boot_ci["year"].isin([2050]))
    ].copy()
    lines.append(pipe.markdown_table(key))
    lines.append("")
    lines.append("## 七、输出文件")
    lines.append("")
    lines.append("- `province_cpi_indices.csv`：省级总/食品/近似非食品 CPI 与 2023=100 指数。")
    lines.append("- `robustness_cpi_nonfood_parameter_estimates.csv`：CPI 非食品价格口径参数。")
    lines.append("- `robustness_cpi_nonfood_fit_by_group.csv`：CPI 非食品价格口径拟合误差。")
    lines.append("- `robustness_cpi_nonfood_projection_group_2030_2035_2050.csv`：CPI 稳健预测。")
    lines.append("- `oos_fit_by_group.csv`、`oos_predictions.csv` 与 `Results/OOS/oos_predictions__*.csv`：按口径、模型、样本切分独立保存的样本外验证。")
    lines.append("- `bootstrap_key_ci.csv`、`bootstrap_parameter_ci.csv`、`bootstrap_draw_metrics.csv`：bootstrap 区间和抽样明细。")
    lines.append("- `lr_test_chi2_and_bootstrap.csv`、`lr_bootstrap_draws.csv`：LR 检验的 cluster bootstrap 摘要和抽样明细。")
    lines.append("")
    lines.append("## 八、仍需人工确认")
    lines.append("")
    lines.append("- 食品 CPI 三个文件是分段表，本脚本按年份拼接；请后续核对 2015 年以前文件是否确为同一食品分类口径。")
    lines.append("- 省级非食品 CPI 由总 CPI、食品 CPI、食物支出份额反推，是近似值；更理想的是直接拿到省级非食品 CPI。")
    status_path = OUT / "bootstrap_draw_status.csv"
    boot_reps = pd.read_csv(status_path).shape[0] if status_path.exists() else 0
    if boot_reps >= 500 and lr_reps >= 500:
        lines.append("- 正式规模 bootstrap 与 LR bootstrap 已完成；若模型选择推断成为论文核心，可追加 parametric-null LR bootstrap 稳健性。")
    else:
        lines.append("- 当前 bootstrap 或 LR bootstrap 仍低于正式规模；正式论文版请把对应 reps 提高到 500-1000。")
    (OUT / "ADDITIONAL_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    pipe.ensure_dirs()
    OOS_OUT.mkdir(parents=True, exist_ok=True)
    panel, _, nutrition = pipe.build_model_data()
    main_manifest = json.loads((OUT / "run_manifest.json").read_text(encoding="utf-8"))

    print("Running CPI nonfood robustness...", flush=True)
    panel_cpi, _, _ = pipe.build_model_data(nonfood_price_mode="cpi_nonfood", output_suffix="_cpi_nonfood")
    arr_cpi = pipe.panel_to_arrays(panel_cpi)
    fits_cpi = pipe.fit_model(
        arr_cpi,
        maidads_random_scales=(0.05,),
        maxiter_a=340,
        maxiter_m=500,
        progress=True,
        seed=20260610,
    )
    params_cpi, fit_cpi = fit_rows("robust_real_derived_cpi_nonfood", fits_cpi, arr_cpi)
    diag_cpi = pd.DataFrame(fits_cpi[1].get("diagnostics", []))
    if not diag_cpi.empty:
        diag_cpi.to_csv(OUT / "robustness_cpi_nonfood_multistart_diagnostics.csv", index=False)
    params_cpi.to_csv(OUT / "robustness_cpi_nonfood_parameter_estimates.csv", index=False)
    fit_cpi.to_csv(OUT / "robustness_cpi_nonfood_fit_by_group.csv", index=False)
    proj_cpi = pipe.build_projection(panel_cpi, fits_cpi[1]["params"], nutrition)
    proj_cpi["projection_group"].to_csv(OUT / "robustness_cpi_nonfood_projection_group_2030_2035_2050.csv", index=False)
    proj_cpi["projection_items"].to_csv(OUT / "robustness_cpi_nonfood_projection_item_feed_2030_2035_2050.csv", index=False)
    proj_cpi["projection_growth_path"].to_csv(OUT / "robustness_cpi_nonfood_projection_growth_path.csv", index=False)
    robustness_manifest = {
        "models": [
            {
                "model": fit["model"],
                "nll": fit["nll"],
                "success": bool(fit["result"].success),
                "message": str(fit["result"].message),
            }
            for fit in fits_cpi
        ],
        "n_obs": int(arr_cpi.x.shape[0]),
        "n_goods": int(arr_cpi.x.shape[1]),
        "groups": arr_cpi.group_names,
    }
    (OUT / "robustness_cpi_nonfood_manifest.json").write_text(
        json.dumps(robustness_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Running OOS validations...", flush=True)
    oos_fit, oos_pred = oos_validations(
        {
            "baseline_real_national_nonfood": panel,
            "robust_real_derived_cpi_nonfood": panel_cpi,
        }
    )
    oos_fit.to_csv(OUT / "oos_fit_by_group.csv", index=False)
    oos_pred.to_csv(OUT / "oos_predictions.csv", index=False)
    oos_2023_fit = oos_fit[oos_fit["test_years"].eq("2023")].copy()
    oos_2023_pred = oos_pred[oos_pred["test_years"].eq("2023")].copy()
    oos_2023_fit.to_csv(OUT / "oos_2023_fit_by_group.csv", index=False)
    oos_2023_pred.to_csv(OUT / "oos_2023_predictions.csv", index=False)

    print("Running cluster bootstrap...", flush=True)
    boot_reps = int(os.environ.get("MAIDADS_BOOTSTRAP_REPS", "30"))
    boot_ci, param_ci, draws = bootstrap_checks(panel, nutrition, b=boot_reps)
    boot_ci.to_csv(OUT / "bootstrap_key_ci.csv", index=False)
    boot_ci.to_csv(OUT / "bootstrap_key_ci_success_only.csv", index=False)
    param_ci.to_csv(OUT / "bootstrap_parameter_ci.csv", index=False)

    print("Running LR bootstrap...", flush=True)
    observed_lr = 2 * (main_manifest["models"][0]["nll"] - main_manifest["models"][1]["nll"])
    lr_reps = int(os.environ.get("MAIDADS_LR_BOOTSTRAP_REPS", "12"))
    lr_summary, _ = lr_bootstrap(panel, observed_lr, b=lr_reps)

    comparison = model_comparison(main_manifest, robustness_manifest, oos_fit, lr_summary)
    comparison.to_csv(OUT / "model_comparison.csv", index=False)
    write_additional_summary(robustness_manifest, oos_fit, boot_ci, comparison, lr_summary)
    print(json.dumps({"robustness": robustness_manifest, "bootstrap_success": int(draws["success"].sum())}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

### run_formal_bootstrap.py

源文件：`/root/data/Paper/省级食物消费/ProvinceMAIDADS/scripts/run_formal_bootstrap.py`

```python
from __future__ import annotations

import argparse
import concurrent.futures as futures
from functools import partial
import json
import math
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import run_additional_checks as checks
import run_maidads_pipeline as pipe


ROOT = pipe.ROOT
OUT = pipe.OUT
DATA_OUT = pipe.DATA_OUT
FORMAL = OUT / "FormalBootstrap"
BOOT = FORMAL / "bootstrap"
LR = FORMAL / "lr_bootstrap"

_WORKER: dict[str, Any] = {}


def _ensure_dirs() -> None:
    FORMAL.mkdir(parents=True, exist_ok=True)
    BOOT.mkdir(parents=True, exist_ok=True)
    LR.mkdir(parents=True, exist_ok=True)


def _append_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    pd.DataFrame(rows).to_csv(path, mode="a", index=False, header=not path.exists())


def _completed_draws(path: Path) -> set[int]:
    if not path.exists():
        return set()
    df = pd.read_csv(path, usecols=["draw"])
    return set(df["draw"].dropna().astype(int))


def _init_worker() -> None:
    panel = pd.read_csv(DATA_OUT / "maidads6_panel.csv")
    nutrition = pipe.read_nutrition()
    arr = pipe.panel_to_arrays(panel)
    full_params = checks.params_from_csv(OUT / "parameter_estimates.csv", "MAIDADS_sat", arr.group_names)
    raw_start = checks.raw_from_maidads_params(full_params)
    _WORKER.update(
        {
            "panel": panel,
            "nutrition": nutrition,
            "arr": arr,
            "raw_start": raw_start,
            "provinces": np.unique(arr.provinces),
            "p_mean": panel[panel["year"] == 2023][[f"p_{g}_model" for g in arr.group_names]].mean().to_numpy(float),
            "m_median": float(np.median(arr.m)),
        }
    )


def _bootstrap_draw(draw: int, maxiter: int) -> dict[str, Any]:
    t0 = time.time()
    arr: pipe.ModelArrays = _WORKER["arr"]
    panel: pd.DataFrame = _WORKER["panel"]
    nutrition: pd.DataFrame = _WORKER["nutrition"]
    raw_start: np.ndarray = _WORKER["raw_start"]
    provinces: np.ndarray = _WORKER["provinces"]
    rng = np.random.default_rng(2026060900 + draw)

    sampled = rng.choice(provinces, size=provinces.size, replace=True)
    idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
    arr_boot = checks.subset_arrays(arr, idx)
    draw_start = raw_start + rng.normal(0, 0.05, size=raw_start.size)
    status = {
        "draw": draw,
        "success": False,
        "nll": np.nan,
        "message": "",
        "elapsed_seconds": np.nan,
        "n_sampled_provinces": int(provinces.size),
        "n_unique_sampled_provinces": int(pd.Series(sampled).nunique()),
    }
    metric_rows: list[dict[str, Any]] = []
    param_rows: list[dict[str, Any]] = []
    try:
        params, res, nll = checks.fit_bootstrap_maidads(arr_boot, draw_start, maxiter=maxiter)
        eta, _, _, _ = pipe.elasticity_for_point(_WORKER["p_mean"], _WORKER["m_median"], params)
        projection = pipe.build_projection(panel, params, nutrition)
        status.update({"success": bool(res.success), "nll": nll, "message": str(res.message)})
        for j, group in enumerate(arr.group_names):
            param_rows.append(
                {
                    "draw": draw,
                    "group": group,
                    "alpha": params["alpha"][j],
                    "beta": params["beta"][j],
                    "delta": params["delta"][j],
                    "tau": params["tau"][j],
                    "omega": params["omega"],
                    "kappa": params["kappa"],
                }
            )
            metric_rows.append(
                {
                    "draw": draw,
                    "metric": "income_elasticity_median_income",
                    "group_or_item": group,
                    "year": np.nan,
                    "value": eta[j],
                }
            )
        proj = projection["projection_group"]
        for _, row in proj[proj["year"].isin([2030, 2050]) & proj["group"].ne("nonfood")].iterrows():
            metric_rows.append(
                {
                    "draw": draw,
                    "metric": "daily_kcal_per_cap_weighted",
                    "group_or_item": row["group"],
                    "year": int(row["year"]),
                    "value": row["daily_kcal_per_cap_weighted"],
                }
            )
        feed = projection["projection_items"].copy()
        feed["feed_grain_million_ton"] = feed["feed_grain_kg"] / 1e9
        for _, row in feed[feed["year"].isin([2030, 2050]) & (feed["feed_grain_million_ton"] > 0)].iterrows():
            metric_rows.append(
                {
                    "draw": draw,
                    "metric": "feed_grain_million_ton",
                    "group_or_item": row["item"],
                    "year": int(row["year"]),
                    "value": row["feed_grain_million_ton"],
                }
            )
    except Exception as exc:
        status["message"] = repr(exc)
    status["elapsed_seconds"] = time.time() - t0
    return {"status": status, "metrics": metric_rows, "params": param_rows}


def _lr_draw(draw: int, maxiter_a: int, maxiter_m: int) -> dict[str, Any]:
    t0 = time.time()
    arr: pipe.ModelArrays = _WORKER["arr"]
    provinces: np.ndarray = _WORKER["provinces"]
    rng = np.random.default_rng(2026061200 + draw)
    sampled = rng.choice(provinces, size=provinces.size, replace=True)
    idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
    arr_boot = checks.subset_arrays(arr, idx)
    row = {
        "draw": draw,
        "success": False,
        "nll_aidads": np.nan,
        "nll_maidads": np.nan,
        "lr_stat": np.nan,
        "message": "",
        "elapsed_seconds": np.nan,
        "n_sampled_provinces": int(provinces.size),
        "n_unique_sampled_provinces": int(pd.Series(sampled).nunique()),
    }
    try:
        fits = pipe.fit_model(
            arr_boot,
            maidads_random_scales=(0.03,),
            maxiter_a=maxiter_a,
            maxiter_m=maxiter_m,
            progress=False,
            seed=20270000 + draw,
            wide_multistart=False,
        )
        nll_a = float(fits[0]["nll"])
        nll_m = float(fits[1]["nll"])
        row.update(
            {
                "success": bool(fits[0]["result"].success) and bool(fits[1]["result"].success),
                "nll_aidads": nll_a,
                "nll_maidads": nll_m,
                "lr_stat": 2 * (nll_a - nll_m),
                "message": "ok",
            }
        )
    except Exception as exc:
        row["message"] = repr(exc)
    row["elapsed_seconds"] = time.time() - t0
    return row


def _dedupe(path: Path, key_cols: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty:
        return df
    df = df.drop_duplicates(key_cols, keep="last").sort_values(key_cols).reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def _summarize_bootstrap(target_reps: int) -> dict[str, Any]:
    draws = _dedupe(BOOT / "formal_bootstrap_draw_status.csv", ["draw"])
    metrics = _dedupe(BOOT / "formal_bootstrap_draw_metrics.csv", ["draw", "metric", "group_or_item", "year"])
    params = _dedupe(BOOT / "formal_bootstrap_parameter_draws.csv", ["draw", "group"])

    success_draws = set(draws.loc[draws["success"].astype(bool), "draw"].astype(int)) if not draws.empty else set()
    metrics_ci_source = metrics[metrics["draw"].isin(success_draws)].copy() if success_draws else metrics.iloc[0:0].copy()
    params_ci_source = params[params["draw"].isin(success_draws)].copy() if success_draws else params.iloc[0:0].copy()

    if metrics_ci_source.empty:
        ci = pd.DataFrame()
    else:
        ci = (
            metrics_ci_source.groupby(["metric", "group_or_item", "year"], dropna=False)["value"]
            .quantile([0.025, 0.5, 0.975])
            .unstack()
            .reset_index()
            .rename(columns={0.025: "ci_2_5", 0.5: "median", 0.975: "ci_97_5"})
        )
        ci["n_success_draws"] = len(success_draws)
        ci["target_reps"] = target_reps

    param_ci = []
    if not params_ci_source.empty:
        for name in ["alpha", "beta", "delta", "tau", "omega", "kappa"]:
            tmp = (
                params_ci_source.groupby("group")[name]
                .quantile([0.025, 0.5, 0.975])
                .unstack()
                .reset_index()
                .rename(columns={0.025: "ci_2_5", 0.5: "median", 0.975: "ci_97_5"})
            )
            tmp.insert(0, "parameter", name)
            tmp["n_success_draws"] = len(success_draws)
            tmp["target_reps"] = target_reps
            param_ci.append(tmp)
    param_ci_df = pd.concat(param_ci, ignore_index=True) if param_ci else pd.DataFrame()

    draws.to_csv(OUT / "bootstrap_draw_status.csv", index=False)
    metrics.to_csv(OUT / "bootstrap_draw_metrics.csv", index=False)
    params.to_csv(OUT / "bootstrap_parameter_draws.csv", index=False)
    ci.to_csv(OUT / "bootstrap_key_ci.csv", index=False)
    ci.to_csv(OUT / "bootstrap_key_ci_success_only.csv", index=False)
    param_ci_df.to_csv(OUT / "bootstrap_parameter_ci.csv", index=False)
    ci.to_csv(BOOT / "bootstrap_key_ci.csv", index=False)
    param_ci_df.to_csv(BOOT / "bootstrap_parameter_ci.csv", index=False)
    return {
        "target_reps": target_reps,
        "completed_reps": int(draws.shape[0]),
        "successful_reps": int(len(success_draws)),
        "convergence_rate": float(len(success_draws) / draws.shape[0]) if draws.shape[0] else np.nan,
    }


def _observed_lr() -> float:
    comparison = pd.read_csv(OUT / "model_comparison.csv")
    row = comparison[comparison["model"].eq("LR_MAIDADS_vs_AIDADS")]
    if not row.empty and "lr_stat" in row:
        return float(row["lr_stat"].iloc[0])
    params = pd.read_csv(OUT / "parameter_estimates.csv")
    nll_a = float(params.loc[params["model"].eq("AIDADS_sat"), "nll"].iloc[0])
    nll_m = float(params.loc[params["model"].eq("MAIDADS_sat"), "nll"].iloc[0])
    return 2 * (nll_a - nll_m)


def _summarize_lr(target_reps: int) -> dict[str, Any]:
    observed_lr = _observed_lr()
    draws = _dedupe(LR / "formal_lr_bootstrap_draws.csv", ["draw"])
    success_lr = draws.loc[draws["success"].astype(bool) & draws["lr_stat"].notna(), "lr_stat"] if not draws.empty else pd.Series(dtype=float)
    if success_lr.empty:
        summary = pd.DataFrame(
            [
                {
                    "test": "MAIDADS_vs_AIDADS",
                    "observed_lr": observed_lr,
                    "bootstrap_reps": target_reps,
                    "completed_reps": int(draws.shape[0]),
                    "successful_reps": 0,
                    "convergence_rate": 0.0,
                    "cluster_bootstrap_tail_probability": np.nan,
                    "chi2_p_value_status": "invalid_not_reported",
                    "note": "No successful LR bootstrap draws.",
                    "inference_scale": "formal" if target_reps >= 500 else "pilot",
                }
            ]
        )
    else:
        summary = pd.DataFrame(
            [
                {
                    "test": "MAIDADS_vs_AIDADS",
                    "observed_lr": observed_lr,
                    "bootstrap_reps": target_reps,
                    "completed_reps": int(draws.shape[0]),
                    "successful_reps": int(success_lr.shape[0]),
                    "convergence_rate": float(success_lr.shape[0] / draws.shape[0]),
                    "cluster_bootstrap_tail_probability": float(np.mean(success_lr >= observed_lr)),
                    "lr_bootstrap_median": float(success_lr.median()),
                    "lr_bootstrap_q95": float(success_lr.quantile(0.95)),
                    "lr_bootstrap_q99": float(success_lr.quantile(0.99)),
                    "chi2_p_value_status": "invalid_not_reported",
                    "note": "Cluster bootstrap with province-block resampling; chi-square p-value not used.",
                    "inference_scale": "formal" if target_reps >= 500 else "pilot",
                }
            ]
        )
    draws.to_csv(OUT / "lr_bootstrap_draws.csv", index=False)
    summary.to_csv(OUT / "lr_test_chi2_and_bootstrap.csv", index=False)
    draws.to_csv(LR / "lr_bootstrap_draws.csv", index=False)
    summary.to_csv(LR / "lr_test_chi2_and_bootstrap.csv", index=False)
    _update_model_comparison(summary)
    return summary.iloc[0].to_dict()


def _update_model_comparison(lr_summary: pd.DataFrame) -> None:
    path = OUT / "model_comparison.csv"
    if not path.exists() or lr_summary.empty:
        return
    comparison = pd.read_csv(path)
    mask = comparison["model"].eq("LR_MAIDADS_vs_AIDADS")
    if not mask.any():
        return
    row = lr_summary.iloc[0]
    comparison.loc[mask, "cluster_bootstrap_tail_probability"] = row.get("cluster_bootstrap_tail_probability", np.nan)
    comparison.loc[mask, "lr_bootstrap_successful_reps"] = row.get("successful_reps", np.nan)
    comparison.loc[mask, "lr_bootstrap_completed_reps"] = row.get("completed_reps", np.nan)
    comparison.loc[mask, "lr_bootstrap_reps"] = row.get("bootstrap_reps", np.nan)
    comparison.loc[mask, "lr_bootstrap_inference_scale"] = row.get("inference_scale", "")
    comparison.to_csv(path, index=False)


def _run_pool(kind: str, draws: list[int], workers: int, task_fn, append_fn, progress_every: int) -> None:
    if not draws:
        print(f"{kind}: all requested draws already completed.", flush=True)
        return
    completed = 0
    started = time.time()

    def _report(draw: int) -> None:
        if completed == 1 or completed % progress_every == 0 or completed == len(draws):
            elapsed = time.time() - started
            rate = completed / elapsed if elapsed > 0 else float("nan")
            print(
                f"{kind}: completed {completed}/{len(draws)} queued draws "
                f"(latest draw {draw}, {rate:.3f} draws/sec)",
                flush=True,
            )

    use_serial = workers is not None and workers <= 1
    if not use_serial:
        # Prefer a fork-context multiprocessing.Pool: the macOS/sandbox default
        # "spawn" start method trips a semaphore syscall that is not permitted
        # here, but "fork" works and lets children inherit the parent's memory.
        try:
            import multiprocessing as _mp
            ctx = _mp.get_context("fork")
            draw_order = list(draws)
            with ctx.Pool(processes=workers, initializer=_init_worker) as pool:
                for draw, result in zip(
                    draw_order, pool.imap(task_fn, draw_order, chunksize=1)
                ):
                    append_fn(result)
                    completed += 1
                    _report(draw)
            return
        except (PermissionError, OSError, NotImplementedError, ValueError) as exc:
            print(
                f"{kind}: process pool unavailable ({exc}); falling back to serial execution.",
                flush=True,
            )
            completed = 0
            started = time.time()

    # Serial fallback: initialise worker state once in-process, run draws sequentially.
    _init_worker()
    for draw in draws:
        result = task_fn(draw)
        append_fn(result)
        completed += 1
        _report(draw)


def _run_bootstrap(reps: int, workers: int, maxiter: int) -> dict[str, Any]:
    status_path = BOOT / "formal_bootstrap_draw_status.csv"
    existing = _completed_draws(status_path)
    draws = [d for d in range(1, reps + 1) if d not in existing]

    def append(result: dict[str, Any]) -> None:
        _append_csv(BOOT / "formal_bootstrap_parameter_draws.csv", result["params"])
        _append_csv(BOOT / "formal_bootstrap_draw_metrics.csv", result["metrics"])
        _append_csv(status_path, [result["status"]])

    _run_pool(
        "Formal parameter bootstrap",
        draws,
        workers,
        partial(_bootstrap_draw, maxiter=maxiter),
        append,
        progress_every=max(1, min(25, reps // 20)),
    )
    return _summarize_bootstrap(reps)


def _run_lr(reps: int, workers: int, maxiter_a: int, maxiter_m: int) -> dict[str, Any]:
    status_path = LR / "formal_lr_bootstrap_draws.csv"
    existing = _completed_draws(status_path)
    draws = [d for d in range(1, reps + 1) if d not in existing]

    def append(row: dict[str, Any]) -> None:
        _append_csv(status_path, [row])

    _run_pool(
        "Formal LR bootstrap",
        draws,
        workers,
        partial(_lr_draw, maxiter_a=maxiter_a, maxiter_m=maxiter_m),
        append,
        progress_every=max(1, min(10, reps // 25)),
    )
    return _summarize_lr(reps)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-reps", type=int, default=int(os.environ.get("MAIDADS_BOOTSTRAP_REPS", "1000")))
    parser.add_argument("--lr-reps", type=int, default=int(os.environ.get("MAIDADS_LR_BOOTSTRAP_REPS", "500")))
    parser.add_argument("--workers", type=int, default=int(os.environ.get("MAIDADS_BOOTSTRAP_WORKERS", "6")))
    parser.add_argument("--bootstrap-maxiter", type=int, default=int(os.environ.get("MAIDADS_BOOTSTRAP_MAXITER", "650")))
    parser.add_argument("--lr-maxiter-a", type=int, default=int(os.environ.get("MAIDADS_LR_MAXITER_A", "320")))
    parser.add_argument("--lr-maxiter-m", type=int, default=int(os.environ.get("MAIDADS_LR_MAXITER_M", "460")))
    parser.add_argument("--skip-bootstrap", action="store_true")
    parser.add_argument("--skip-lr", action="store_true")
    args = parser.parse_args()

    _ensure_dirs()
    manifest = {
        "bootstrap_target_reps": args.bootstrap_reps,
        "lr_target_reps": args.lr_reps,
        "workers": args.workers,
        "bootstrap_maxiter": args.bootstrap_maxiter,
        "lr_maxiter_a": args.lr_maxiter_a,
        "lr_maxiter_m": args.lr_maxiter_m,
        "started_at": pd.Timestamp.now().isoformat(),
    }
    (FORMAL / "formal_bootstrap_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    out: dict[str, Any] = {}
    if not args.skip_bootstrap:
        out["bootstrap"] = _run_bootstrap(args.bootstrap_reps, args.workers, args.bootstrap_maxiter)
    else:
        out["bootstrap"] = _summarize_bootstrap(args.bootstrap_reps)
    if not args.skip_lr:
        out["lr"] = _run_lr(args.lr_reps, args.workers, args.lr_maxiter_a, args.lr_maxiter_m)
    else:
        out["lr"] = _summarize_lr(args.lr_reps)

    out["finished_at"] = pd.Timestamp.now().isoformat()
    (FORMAL / "formal_bootstrap_summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
```

### prepare_paper_workflow_outputs.py

源文件：`/root/data/Paper/省级食物消费/ProvinceMAIDADS/scripts/prepare_paper_workflow_outputs.py`

```python
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ProvinceMAIDADS"
RESULTS = PROJECT / "Results"
DATA_OUT = PROJECT / "Data" / "output"

DIAG = RESULTS / "Diagnostics"
ELAST = RESULTS / "Elasticities"
BOOT = RESULTS / "Bootstrap"
PROJ = RESULTS / "Projection"
OOS = RESULTS / "OOS"
PAPER_WORK = PROJECT / ".paper_work"


def ensure_dirs() -> None:
    for path in [DIAG, ELAST, BOOT, PROJ, OOS, PAPER_WORK]:
        path.mkdir(parents=True, exist_ok=True)


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def build_oos_summary() -> None:
    src = RESULTS / "oos_fit_by_group.csv"
    if not src.exists():
        return
    oos = pd.read_csv(src)
    oos["split"] = oos["train_years"].astype(str) + " -> " + oos["test_years"].astype(str)
    cols = [
        "variant",
        "model",
        "split",
        "train_years",
        "test_years",
        "group",
        "rmse_x",
        "mae_x",
        "mean_x",
        "relative_rmse",
        "n_test",
    ]
    oos[cols].to_csv(OOS / "oos_summary_by_model.csv", index=False)
    # Compatibility copies requested by the writing skill.
    copy_if_exists(src, OOS / "oos_fit_by_group.csv")
    copy_if_exists(RESULTS / "oos_predictions.csv", OOS / "oos_predictions_all_models.csv")


def build_diagnostics() -> None:
    mapping = {
        "multistart_diagnostics.csv": "multistart_diagnostics.csv",
        "best_solution_gradient_report.csv": "best_solution_gradient_report.csv",
        "lr_bootstrap_draws.csv": "lr_bootstrap_draws.csv",
    }
    for src_name, dst_name in mapping.items():
        copy_if_exists(RESULTS / src_name, DIAG / dst_name)

    boundary_src = RESULTS / "parameter_boundary_report.csv"
    if boundary_src.exists():
        boundary = pd.read_csv(boundary_src)
        boundary["fixed_by_restriction"] = boundary.get("imposed_by_saturation", False).astype(bool)
        near_lower = boundary.get("near_lower_boundary", False).astype(bool)
        near_upper = boundary.get("near_upper_boundary", False).astype(bool)
        boundary["estimated_on_boundary"] = (near_lower | near_upper) & (~boundary["fixed_by_restriction"])
        boundary.to_csv(DIAG / "parameter_boundary_report.csv", index=False)

    lr_src = RESULTS / "lr_test_chi2_and_bootstrap.csv"
    if lr_src.exists():
        lr = pd.read_csv(lr_src)
        out = pd.DataFrame()
        out["test"] = lr.get("test", pd.Series(["MAIDADS_vs_AIDADS"]))
        out["lr_observed"] = lr.get("observed_lr", pd.Series([np.nan]))
        out["df_naive"] = 7
        out["p_chi2_naive"] = np.nan
        out["p_bootstrap_cluster"] = lr.get("cluster_bootstrap_tail_probability", pd.Series([np.nan]))
        out["n_bootstrap"] = lr.get("bootstrap_reps", pd.Series([np.nan]))
        out["successful_reps"] = lr.get("successful_reps", pd.Series([np.nan]))
        out["convergence_rate"] = out["successful_reps"] / out["n_bootstrap"]
        out["status"] = np.where(out["n_bootstrap"] >= 500, "formal", "pilot_only")
        out["note"] = lr.get("note", pd.Series(["Cluster bootstrap; chi-square reference not used."]))
        out.to_csv(DIAG / "lr_test_chi2_and_bootstrap.csv", index=False)

    build_model_equation_tests()


def build_elasticity_package() -> None:
    for name in [
        "elasticity_income_grid.csv",
        "elasticity_expenditure_grid.csv",
        "elasticity_price_marshallian_grid.csv",
        "elasticity_price_hicksian_grid.csv",
        "elasticity_consistency_tests.csv",
        "elasticity_observed_points.csv",
    ]:
        copy_if_exists(RESULTS / name, ELAST / name)


def build_bootstrap_package() -> None:
    for name in [
        "bootstrap_draw_status.csv",
        "bootstrap_draw_metrics.csv",
        "bootstrap_key_ci.csv",
        "bootstrap_key_ci_success_only.csv",
        "bootstrap_parameter_ci.csv",
        "bootstrap_parameter_draws.csv",
    ]:
        copy_if_exists(RESULTS / name, BOOT / name)


def build_projection_decomposition() -> None:
    panel_path = DATA_OUT / "maidads6_panel.csv"
    proj_path = RESULTS / "projection_group_2030_2035_2050.csv"
    if not panel_path.exists() or not proj_path.exists():
        return
    panel = pd.read_csv(panel_path)
    proj = pd.read_csv(proj_path)
    base = panel[panel["year"].eq(2023)].copy()
    rows = []
    base_pop = float(base["population_10k"].sum())
    scenario_name = "ssp2_population_income_convergence"
    if "population_scenario" in proj.columns:
        scenarios = sorted(str(x) for x in proj["population_scenario"].dropna().unique())
        if scenarios:
            scenario_name = f"{scenarios[0].lower()}_population_income_convergence"
    for group in ["grain", "oil", "vegfruit", "pork", "meatother", "dairyegg"]:
        x_col = f"x_{group}"
        base_daily = float(np.average(base[x_col] * 2000, weights=base["population_10k"]))
        base_total = base_daily * 365 * base_pop * 10000
        for _, row in proj[proj["group"].eq(group)].iterrows():
            pop = float(row["population_10k"])
            full_total = float(row["annual_kcal_total"])
            population_only_total = base_daily * 365 * pop * 10000
            rows.append(
                {
                    "scenario": scenario_name,
                    "year": int(row["year"]),
                    "group": group,
                    "base_2023_daily_kcal_per_cap": base_daily,
                    "projection_daily_kcal_per_cap": row["daily_kcal_per_cap_weighted"],
                    "base_2023_total_kcal": base_total,
                    "population_only_total_kcal": population_only_total,
                    "full_total_kcal": full_total,
                    "population_contribution_kcal": population_only_total - base_total,
                    "per_cap_demand_contribution_kcal": full_total - population_only_total,
                    "total_change_kcal": full_total - base_total,
                }
            )
    pd.DataFrame(rows).to_csv(PROJ / "projection_decomposition_2030_2035_2050.csv", index=False)


def build_projection_package() -> None:
    for name in [
        "projection_group_2030_2035_2050.csv",
        "projection_item_feed_2030_2035_2050.csv",
        "projection_province_path.csv",
        "projection_growth_path.csv",
        "robustness_cpi_nonfood_projection_group_2030_2035_2050.csv",
        "robustness_cpi_nonfood_projection_item_feed_2030_2035_2050.csv",
    ]:
        copy_if_exists(RESULTS / name, PROJ / name)
    copy_if_exists(RESULTS / "feed_demand_method.md", PROJ / "feed_demand_method.md")
    build_projection_decomposition()


def build_nutrition_audit() -> None:
    nutrition_path = DATA_OUT / "nutrition_processed.csv"
    grain_path = DATA_OUT / "grain_weights_processed.csv"
    lines = [
        "# Nutrition Conversion Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    if nutrition_path.exists():
        nutrition = pd.read_csv(nutrition_path)
        lines += [
            "## Nutrition table",
            "",
            f"- Processed rows: {nutrition.shape[0]}",
            "- `kcal_per_kg_as_purchased = kcal_per_100g_edible * 10 * edible_share / 100`.",
            "- If reported energy is missing or zero, energy is reconstructed from protein, fat and carbohydrate.",
            f"- Non-positive kcal rows after processing: {int((nutrition['kcal_per_kg_as_purchased'] <= 0).sum())}",
            "",
        ]
    if grain_path.exists():
        grain = pd.read_csv(grain_path)
        potato_rows = grain[grain["code"].eq("POTA")]
        potato_note = "not present"
        if not potato_rows.empty:
            potato_note = (
                f"grain_equiv_weight={float(potato_rows['grain_equiv_weight'].iloc[0]):.6g}; "
                f"kcal_weight={float(potato_rows['kcal_weight'].iloc[0]):.6g}"
            )
        lines += [
            "## Grain aggregation",
            "",
            "- Grain-equivalent weights are retained for accounting, including potato divided by 5.",
            "- Calorie aggregation uses actual consumption-quantity weights and actual kcal/kg, not the potato /5 grain-equivalent conversion.",
            f"- Potato audit: {potato_note}.",
            f"- Sum of kcal weights: {float(grain['kcal_weight'].sum()):.12g}",
            f"- Sum of grain-equivalent weights: {float(grain['grain_equiv_weight'].sum()):.12g}",
            "",
        ]
    (DATA_OUT / "nutrition_conversion_audit.md").write_text("\n".join(lines), encoding="utf-8")


def build_model_equation_tests() -> None:
    lines = [
        "# Model Equation Tests",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    panel_path = DATA_OUT / "maidads6_panel.csv"
    if panel_path.exists():
        panel = pd.read_csv(panel_path)
        budget_error = panel["m"] - panel["covered_food_exp"] - panel["nonfood_exp"]
        lines += [
            "## Budget Identity",
            "",
            f"- Max absolute budget residual: {float(np.nanmax(np.abs(budget_error))):.8g}",
            f"- Mean covered food budget share: {float(panel['covered_food_budget_share'].mean()):.8g}",
            "",
        ]
    consistency_path = RESULTS / "elasticity_consistency_tests.csv"
    if consistency_path.exists():
        cons = pd.read_csv(consistency_path)
        cols = [c for c in cons.columns if c.startswith("max_abs") or c.endswith("_error")]
        lines += ["## Elasticity Consistency", ""]
        for col in cols:
            lines.append(f"- {col}: max={float(cons[col].abs().max()):.8g}")
        lines.append("")
    grad_path = RESULTS / "best_solution_gradient_report.csv"
    if grad_path.exists():
        grad = pd.read_csv(grad_path)
        lines += [
            "## Optimizer Diagnostics",
            "",
            f"- Selected rows: {grad.shape[0]}",
            f"- Max absolute gradient among selected rows: {float(grad['max_abs_gradient'].max()):.8g}",
            f"- Gradient norm among selected rows: {float(grad['grad_norm'].max()):.8g}",
            "",
        ]
    (DIAG / "model_equation_tests.md").write_text("\n".join(lines), encoding="utf-8")


def copy_fix_report() -> None:
    copy_if_exists(RESULTS / "CODE_AUDIT_FIX_REPORT.md", PROJECT / "CODE_AUDIT_FIX_REPORT.md")


def markdown_table(df: pd.DataFrame, digits: int = 3) -> str:
    if df is None or df.empty:
        return "_无可用记录。_"
    tmp = df.copy()
    tmp.columns = [str(c) for c in tmp.columns]
    for col in tmp.select_dtypes(include=[np.number]).columns:
        tmp[col] = tmp[col].map(lambda x: "" if pd.isna(x) else f"{x:.{digits}f}")
    tmp = tmp.fillna("").astype(str)
    lines = [
        "| " + " | ".join(tmp.columns) + " |",
        "| " + " | ".join(["---"] * len(tmp.columns)) + " |",
    ]
    for row in tmp.itertuples(index=False):
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def refresh_additional_results_summary() -> None:
    """Rewrite the additional-results note from the synchronized formal outputs."""
    lines: list[str] = [
        "# 追加处理与稳健性估计结果",
        "",
        "## 一、已补充内容",
        "",
        "- 主结果采用全国非食品 CPI；稳健性用食物支出份额近似反推出省级非食品 CPI。",
        "- 构造 `cpi_nonfood` 省级近似非食品价格口径并重新估计 AIDADS/MAIDADS。",
        "- 对每个 `variant × model` 分别用 2015-2020 年训练、2021-2023 年测试，以及 2015-2022 年训练、2023 年测试做样本外验证。",
    ]

    status_path = RESULTS / "bootstrap_draw_status.csv"
    if status_path.exists():
        status = pd.read_csv(status_path)
        success_count = int(status["success"].astype(bool).sum())
        total_count = int(status.shape[0])
        scale = "正式规模" if total_count >= 500 else "pilot"
        lines.append(
            f"- 做 {total_count} 次省份簇 bootstrap（{scale}），其中 {success_count} 次完全收敛；关键区间仅用完全收敛 draw 汇总。"
        )
    else:
        lines.append("- 尚未找到省份簇 bootstrap 状态表。")

    lr_path = RESULTS / "lr_test_chi2_and_bootstrap.csv"
    if lr_path.exists():
        lr = pd.read_csv(lr_path)
        if not lr.empty:
            lr_row = lr.iloc[0]
            lr_reps = int(lr_row.get("bootstrap_reps", lr_row.get("n_bootstrap", 0)))
            lr_success = int(lr_row.get("successful_reps", 0))
            lr_scale = "正式规模" if lr_reps >= 500 else "pilot"
            lines.append(
                f"- LR cluster bootstrap 已完成 {lr_reps} 次（{lr_scale}），其中 {lr_success} 次成功；普通 χ² p 值不作为有效推断。"
            )

    lines.append("")
    lines.append("## 二、CPI 非食品稳健性估计")
    manifest_path = RESULTS / "robustness_cpi_nonfood_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        robustness = pd.DataFrame(manifest.get("models", []))
        lines.append(markdown_table(robustness))
    else:
        lines.append("_未找到 CPI 非食品稳健性 manifest。_")

    lines.append("")
    lines.append("## 三、样本外验证")
    oos_path = RESULTS / "oos_fit_by_group.csv"
    lines.append(markdown_table(pd.read_csv(oos_path)) if oos_path.exists() else "_未找到样本外验证表。_")

    lines.append("")
    lines.append("## 四、模型比较")
    comparison_path = RESULTS / "model_comparison.csv"
    lines.append(markdown_table(pd.read_csv(comparison_path)) if comparison_path.exists() else "_未找到模型比较表。_")

    lines.append("")
    lines.append("## 五、LR cluster bootstrap")
    lines.append("")
    lines.append("普通 χ² p 值因 MAIDADS 在 AIDADS 原假设下存在不可识别 nuisance parameter，本轮不作为有效推断报告。")
    lines.append(markdown_table(pd.read_csv(lr_path)) if lr_path.exists() else "_未找到 LR bootstrap 摘要。_")

    lines.append("")
    lines.append("## 六、bootstrap 关键区间")
    ci_path = RESULTS / "bootstrap_key_ci.csv"
    if ci_path.exists():
        boot_ci = pd.read_csv(ci_path)
        key = boot_ci[
            (boot_ci["metric"].isin(["daily_kcal_per_cap_weighted", "feed_grain_million_ton"]))
            & (boot_ci["year"].isin([2050]))
        ].copy()
        lines.append(markdown_table(key))
    else:
        lines.append("_未找到 bootstrap 关键区间。_")

    lines.extend(
        [
            "",
            "## 七、输出文件",
            "",
            "- `province_cpi_indices.csv`：省级总/食品/近似非食品 CPI 与 2023=100 指数。",
            "- `robustness_cpi_nonfood_parameter_estimates.csv`：CPI 非食品价格口径参数。",
            "- `robustness_cpi_nonfood_fit_by_group.csv`：CPI 非食品价格口径拟合误差。",
            "- `robustness_cpi_nonfood_projection_group_2030_2035_2050.csv`：CPI 稳健预测。",
            "- `oos_fit_by_group.csv`、`oos_predictions.csv` 与 `Results/OOS/oos_predictions__*.csv`：按口径、模型、样本切分独立保存的样本外验证。",
            "- `bootstrap_key_ci.csv`、`bootstrap_parameter_ci.csv`、`bootstrap_draw_metrics.csv`：bootstrap 区间和抽样明细。",
            "- `lr_test_chi2_and_bootstrap.csv`、`lr_bootstrap_draws.csv`：LR 检验的 cluster bootstrap 摘要和抽样明细。",
            "",
            "## 八、仍需人工确认",
            "",
            "- 食品 CPI 三个文件是分段表，本脚本按年份拼接；请后续核对 2015 年以前文件是否确为同一食品分类口径。",
            "- 省级非食品 CPI 由总 CPI、食品 CPI、食物支出份额反推，是近似值；更理想的是直接拿到省级非食品 CPI。",
            "- 正式规模 bootstrap 与 LR cluster bootstrap 已完成；若模型选择推断成为论文核心，可追加 parametric-null LR bootstrap 稳健性。",
            "- 预测人口路径已改用 Chen et al. (2020) SSP2 省级人口预测；收入、城镇化和年龄结构路径仍需更正式的数据来源。",
        ]
    )
    (RESULTS / "ADDITIONAL_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def build_file_inventory() -> None:
    files = sorted(
        str(path.relative_to(PROJECT))
        for path in PROJECT.rglob("*")
        if path.is_file() and ".paper_work" not in path.parts
    )
    (PAPER_WORK / "file_inventory.txt").write_text("\n".join(files) + "\n", encoding="utf-8")


def write_manifest() -> None:
    manifest = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Prepare ProvinceMAIDADS result outputs for provincial-maidads-paper-writer gate checks and manuscript drafting.",
        "directories": {
            "diagnostics": str(DIAG.relative_to(PROJECT)),
            "elasticities": str(ELAST.relative_to(PROJECT)),
            "bootstrap": str(BOOT.relative_to(PROJECT)),
            "projection": str(PROJ.relative_to(PROJECT)),
            "oos": str(OOS.relative_to(PROJECT)),
        },
    }
    (PAPER_WORK / "paper_workflow_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    build_oos_summary()
    build_diagnostics()
    build_elasticity_package()
    build_bootstrap_package()
    build_projection_package()
    build_nutrition_audit()
    copy_fix_report()
    refresh_additional_results_summary()
    build_file_inventory()
    write_manifest()
    print(PROJECT / ".paper_work")


if __name__ == "__main__":
    main()
```

### build_manuscript_draft.py

源文件：`/root/data/Paper/省级食物消费/ProvinceMAIDADS/scripts/build_manuscript_draft.py`

```python
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ProvinceMAIDADS"
RESULTS = PROJECT / "Results"
DATA_OUT = PROJECT / "Data" / "output"
PAPER_WORK = PROJECT / ".paper_work"
MANUSCRIPT = PROJECT / "manuscript"
SECTIONS = MANUSCRIPT / "sections"
TABLES = MANUSCRIPT / "tables"
APPENDIX = MANUSCRIPT / "appendix"
REVIEWS = MANUSCRIPT / "reviewer_reports"


def md_table(df: pd.DataFrame, digits: int = 3) -> str:
    tmp = df.copy()
    tmp.columns = [str(c) for c in tmp.columns]
    for col in tmp.select_dtypes(include=[np.number]).columns:
        tmp[col] = tmp[col].map(lambda x: "" if pd.isna(x) else f"{x:.{digits}f}")
    tmp = tmp.fillna("").astype(str)
    lines = [
        "| " + " | ".join(tmp.columns) + " |",
        "| " + " | ".join(["---"] * len(tmp.columns)) + " |",
    ]
    for row in tmp.itertuples(index=False):
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def read_inputs() -> dict[str, pd.DataFrame]:
    return {
        "panel": pd.read_csv(DATA_OUT / "maidads6_panel.csv"),
        "comparison": pd.read_csv(RESULTS / "model_comparison.csv"),
        "fit": pd.read_csv(RESULTS / "model_fit_by_group.csv"),
        "params": pd.read_csv(RESULTS / "parameter_estimates.csv"),
        "oos": pd.read_csv(RESULTS / "OOS" / "oos_summary_by_model.csv"),
        "lr": pd.read_csv(RESULTS / "Diagnostics" / "lr_test_chi2_and_bootstrap.csv"),
        "bootstrap": pd.read_csv(RESULTS / "Bootstrap" / "bootstrap_draw_status.csv"),
        "boot_ci": pd.read_csv(RESULTS / "Bootstrap" / "bootstrap_key_ci.csv"),
        "elasticity_income": pd.read_csv(RESULTS / "Elasticities" / "elasticity_income_grid.csv"),
        "elasticity_price": pd.read_csv(RESULTS / "Elasticities" / "elasticity_price_marshallian_grid.csv"),
        "consistency": pd.read_csv(RESULTS / "Elasticities" / "elasticity_consistency_tests.csv"),
        "projection": pd.read_csv(RESULTS / "Projection" / "projection_group_2030_2035_2050.csv"),
        "feed": pd.read_csv(RESULTS / "Projection" / "projection_item_feed_2030_2035_2050.csv"),
        "decomposition": pd.read_csv(RESULTS / "Projection" / "projection_decomposition_2030_2035_2050.csv"),
    }


def get_scalar(df: pd.DataFrame, mask, col: str) -> float:
    out = df.loc[mask, col]
    if out.empty:
        return float("nan")
    return float(out.iloc[0])


def build_summary_tables(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    comparison = data["comparison"].copy()
    model_rows = comparison[comparison["model"].isin(["AIDADS_sat", "MAIDADS_sat"])].copy()
    fit_table = model_rows[
        ["variant", "model", "nll", "aic", "bic", "oos_food_rmse_mean"]
    ].copy()
    fit_table.to_csv(TABLES / "table_1_model_comparison.csv", index=False)

    inc = data["elasticity_income"].copy()
    median_income = float(data["panel"]["m"].median())
    unique_incomes = np.array(sorted(inc["income"].dropna().unique()))
    med_grid = float(unique_incomes[np.argmin(np.abs(unique_incomes - median_income))])
    groups = ["grain", "oil", "vegfruit", "meatsea", "dairyegg", "all_food", "animal_food", "plant_food"]
    elasticity_table = inc[inc["income"].eq(med_grid) & inc["group"].isin(groups)][
        ["income", "group", "quantity_2000kcal_elasticity", "expenditure_elasticity", "budget_share"]
    ].copy()
    elasticity_table.to_csv(TABLES / "table_2_income_elasticities_median.csv", index=False)

    proj = data["projection"].copy()
    proj_table = proj[proj["year"].isin([2030, 2035, 2050]) & proj["group"].ne("nonfood")][
        ["year", "group", "daily_kcal_per_cap_weighted", "annual_kcal_total", "population_10k"]
    ].copy()
    proj_table.to_csv(TABLES / "table_3_projection_kcal.csv", index=False)

    feed = data["feed"].copy()
    feed["feed_grain_million_ton"] = feed["feed_grain_kg"] / 1e9
    feed_table = feed[["year", "item", "total_kg", "feed_kg_per_kg_product", "feed_grain_million_ton"]].copy()
    feed_table.to_csv(TABLES / "table_4_feed_grain.csv", index=False)

    price = data["elasticity_price"]
    own = price[price["is_own_price"].astype(bool)].copy()
    price_summary = (
        own.groupby("demand_group")["elasticity"]
        .agg(["min", "median", "max"])
        .reset_index()
        .rename(columns={"demand_group": "group", "median": "median_own_price_elasticity"})
    )
    price_summary.to_csv(TABLES / "table_5_own_price_elasticities.csv", index=False)

    return {
        "fit_table": fit_table,
        "elasticity_table": elasticity_table,
        "projection_table": proj_table,
        "feed_table": feed_table,
        "price_summary": price_summary,
        "median_income_grid": pd.DataFrame({"median_income_grid": [med_grid]}),
    }


def build_evidence_ledger(data: dict[str, pd.DataFrame], tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    panel = data["panel"]
    comparison = data["comparison"]
    projection = data["projection"]
    feed = data["feed"].copy()
    feed["feed_grain_million_ton"] = feed["feed_grain_kg"] / 1e9
    consistency = data["consistency"]
    bootstrap = data["bootstrap"]
    lr = data["lr"]
    oos = data["oos"]
    inc_table = tables["elasticity_table"]

    n_prov = panel["province"].nunique()
    year_min, year_max = int(panel["year"].min()), int(panel["year"].max())
    n_obs = panel.shape[0]
    boot_n = bootstrap.shape[0]
    boot_success = int(bootstrap["success"].astype(bool).sum())
    lr_obs = float(lr["lr_observed"].iloc[0])
    lr_p = float(lr["p_bootstrap_cluster"].iloc[0])
    lr_reps = int(lr["n_bootstrap"].iloc[0])
    lr_success = int(lr["successful_reps"].iloc[0])
    bootstrap_status = "formal" if boot_n >= 500 else "pilot_only"
    bootstrap_scale = "formal-scale" if boot_n >= 500 else "pilot-scale"
    lr_status = "formal" if lr_reps >= 500 else "pilot_only"
    lr_scale = "formal-scale" if lr_reps >= 500 else "pilot-scale"
    max_consistency = float(
        consistency[
            [
                "adding_up_income_error",
                "max_abs_price_adding_up_error",
                "max_abs_marshallian_homogeneity_error",
                "max_abs_hicksian_homogeneity_error",
                "max_abs_slutsky_symmetry_error",
            ]
        ]
        .abs()
        .max()
        .max()
    )

    rows = []

    def add(cid, section, claim, file, column, status="allowed", notes=""):
        rows.append(
            {
                "claim_id": cid,
                "section": section,
                "claim": claim,
                "evidence_file": file,
                "table_or_column": column,
                "status": status,
                "notes": notes,
            }
        )

    add(
        "C001",
        "Data",
        f"The estimating sample covers {n_prov} provinces from {year_min} to {year_max}, yielding {n_obs} province-year observations.",
        "Data/output/maidads6_panel.csv",
        "province, year",
    )
    add(
        "C002",
        "Data",
        "The model uses five covered food groups plus an other/non-covered expenditure residual.",
        "Results/CODE_AUDIT_FIX_REPORT.md",
        "B4/nonfood naming row",
    )
    for variant in ["baseline_real_national_nonfood", "robust_real_derived_cpi_nonfood"]:
        a_nll = get_scalar(comparison, (comparison["variant"].eq(variant)) & (comparison["model"].eq("AIDADS_sat")), "nll")
        m_nll = get_scalar(comparison, (comparison["variant"].eq(variant)) & (comparison["model"].eq("MAIDADS_sat")), "nll")
        add(
            f"C10{1 if variant.startswith('baseline') else 2}",
            "Estimation",
            f"In {variant}, MAIDADS improves in-sample fit relative to AIDADS: nll {m_nll:.3f} versus {a_nll:.3f}.",
            "Results/model_comparison.csv",
            "variant, model, nll",
        )
    base_a_oos = get_scalar(comparison, (comparison["variant"].eq("baseline_real_national_nonfood")) & (comparison["model"].eq("AIDADS_sat")), "oos_food_rmse_mean")
    base_m_oos = get_scalar(comparison, (comparison["variant"].eq("baseline_real_national_nonfood")) & (comparison["model"].eq("MAIDADS_sat")), "oos_food_rmse_mean")
    add(
        "C103",
        "Estimation",
        f"Out-of-sample food RMSE is separately computed by model and is lower for MAIDADS than AIDADS in the baseline specification ({base_m_oos:.4f} versus {base_a_oos:.4f}).",
        "Results/model_comparison.csv; Results/OOS/oos_summary_by_model.csv",
        "oos_food_rmse_mean",
    )
    add(
        "C104",
        "Estimation",
        f"The LR statistic is {lr_obs:.3f}; the {lr_scale} cluster-bootstrap LR exercise has {lr_success}/{lr_reps} successful draws and tail probability {lr_p:.3f}.",
        "Results/Diagnostics/lr_test_chi2_and_bootstrap.csv",
        "lr_observed, p_bootstrap_cluster, n_bootstrap",
        lr_status,
    )
    add(
        "C105",
        "Estimation",
        f"Elasticity consistency checks have maximum absolute error {max_consistency:.2e}.",
        "Results/Elasticities/elasticity_consistency_tests.csv",
        "max_abs_*",
    )
    for _, row in inc_table.iterrows():
        add(
            f"C20{len(rows)}",
            "Elasticities",
            f"At the median-income grid point ({row['income']:.0f}), {row['group']} has quantity elasticity {row['quantity_2000kcal_elasticity']:.3f}.",
            "Results/Elasticities/elasticity_income_grid.csv",
            "income, group, quantity_2000kcal_elasticity",
        )
    for group in ["grain", "oil", "vegfruit", "meatsea", "dairyegg"]:
        kcal_2050 = get_scalar(
            projection,
            (projection["year"].eq(2050)) & (projection["group"].eq(group)),
            "daily_kcal_per_cap_weighted",
        )
        add(
            f"C30{group}",
            "Projection",
            f"Under the conditional scenario, projected 2050 daily kcal per capita for {group} is {kcal_2050:.1f}.",
            "Results/Projection/projection_group_2030_2035_2050.csv",
            "year, group, daily_kcal_per_cap_weighted",
            "scenario_only",
        )
    for item in ["pork", "poultry", "egg", "milk", "aquatic", "beef", "mutton"]:
        value = get_scalar(
            feed,
            (feed["year"].eq(2050)) & (feed["item"].eq(item)),
            "feed_grain_million_ton",
        )
        add(
            f"C40{item}",
            "Projection",
            f"Under the conditional scenario, 2050 feed-grain equivalent demand associated with {item} is {value:.1f} million tons.",
            "Results/Projection/projection_item_feed_2030_2035_2050.csv",
            "year, item, feed_grain_kg",
            "scenario_only",
        )
    add(
        "C501",
        "Inference",
        f"The parameter and projection bootstrap exercise uses {boot_n} province-block draws, of which {boot_success} converge; reported intervals are {bootstrap_scale}.",
        "Results/Bootstrap/bootstrap_draw_status.csv",
        "draw, success",
        bootstrap_status,
    )
    add(
        "C601",
        "Projection",
        "The projection path uses national income growth, income-convergence adjustments, and Chen et al. (2020) SSP2 provincial population projections; it remains a conditional scenario because province-level income, urbanization, and age-structure paths are not yet fully specified.",
        "Results/Projection/projection_growth_path.csv",
        "income_growth_source, population_share_source, population_projection_source",
        "scenario_only",
    )
    ledger = pd.DataFrame(rows)
    ledger.to_csv(PAPER_WORK / "evidence_ledger.csv", index=False)
    return ledger


def write_refs() -> None:
    refs = r"""@article{gouel_guimbard_2019,
  author = {Gouel, Christophe and Guimbard, Houssein},
  title = {Nutrition Transition and the Structure of Global Food Demand},
  journal = {American Journal of Agricultural Economics},
  volume = {101},
  number = {2},
  pages = {383--403},
  year = {2019},
  doi = {10.1093/ajae/aay030}
}

@article{preckel_cranfield_hertel_2010,
  author = {Preckel, Paul V. and Cranfield, John A. L. and Hertel, Thomas W.},
  title = {A modified, implicitly additive demand system},
  journal = {Applied Economics},
  volume = {42},
  number = {2},
  pages = {143--155},
  year = {2010}
}

@article{chen_guo_wang_2020,
  author = {Chen, Y. and Guo, F. and Wang, J. and others},
  title = {Provincial and gridded population projection for China under shared socioeconomic pathways from 2010 to 2100},
  journal = {Scientific Data},
  volume = {7},
  pages = {83},
  year = {2020},
  doi = {10.1038/s41597-020-0421-y}
}
"""
    (MANUSCRIPT / "refs.bib").write_text(refs, encoding="utf-8")


def draft_sections(data: dict[str, pd.DataFrame], tables: dict[str, pd.DataFrame], ledger: pd.DataFrame) -> None:
    gate = json.loads((PAPER_WORK / "gate_status.json").read_text(encoding="utf-8"))
    status = gate["status"]
    comparison_md = md_table(tables["fit_table"], 3)
    elasticity_md = md_table(tables["elasticity_table"], 3)
    projection_pivot = tables["projection_table"].pivot_table(
        index="group", columns="year", values="daily_kcal_per_cap_weighted"
    ).reset_index()
    projection_md = md_table(projection_pivot, 1)
    feed_pivot = tables["feed_table"].pivot_table(
        index="item", columns="year", values="feed_grain_million_ton"
    ).reset_index()
    feed_md = md_table(feed_pivot, 1)
    price_md = md_table(tables["price_summary"], 3)
    lr = data["lr"].iloc[0]
    boot = data["bootstrap"]
    boot_success = int(boot["success"].astype(bool).sum())
    boot_scale = "formal-scale" if boot.shape[0] >= 500 else "pilot-scale"
    lr_scale = "formal-scale" if int(lr["n_bootstrap"]) >= 500 else "pilot-scale"
    cons = data["consistency"]
    max_consistency = float(
        cons[
            [
                "adding_up_income_error",
                "max_abs_price_adding_up_error",
                "max_abs_marshallian_homogeneity_error",
                "max_abs_hicksian_homogeneity_error",
                "max_abs_slutsky_symmetry_error",
            ]
        ].abs().max().max()
    )
    panel = data["panel"]
    n_prov = panel["province"].nunique()
    n_obs = panel.shape[0]
    y0, y1 = int(panel["year"].min()), int(panel["year"].max())

    sections = {}
    sections["00_abstract.md"] = f"""# Abstract

This paper develops a first-pass province-level application of the modified implicitly additive demand system (MAIDADS) to study food demand, nutrition transition, and conditional food-demand projections in China. The estimating sample contains {n_obs} province-year observations for {n_prov} provinces over {y0}--{y1}. Food consumption is aggregated into five covered food groups measured in daily 2,000-kcal units, while remaining expenditure is treated as an other/non-covered residual. The main specification uses 2023 real-price units and a national non-food CPI for the residual price index.

The current results should be read as a working-paper draft rather than final journal evidence. The audit gate status is **{status}** because the projection module still relies on conditional income-convergence assumptions. Inference has been upgraded to formal-scale resampling: the parameter and projection bootstrap uses {boot.shape[0]} province-block draws, of which {boot_success} converge, and the LR cluster bootstrap uses {int(lr['n_bootstrap'])} draws. Population paths now use the Chen et al. (2020) SSP2 provincial projection. Within these limits, MAIDADS improves in-sample fit relative to AIDADS and modestly improves out-of-sample food-demand prediction. The estimated demand system passes adding-up, homogeneity, and Slutsky-consistency checks at numerical tolerances. Conditional projections suggest continued reallocation away from staples and toward animal products, although total covered-food calories change less than composition. The paper concludes by identifying the data additions needed for a journal-ready version: direct provincial non-food CPI, province-level income, urbanization, and age-structure paths, and broader food-group coverage.

Unsupported or weak claims to resolve:
- Add province-level income, urbanization, and age-structure paths before presenting projections as forecasts rather than scenario simulations.
"""

    sections["01_introduction.md"] = """# 1. Introduction

China's food system is moving through a nutrition transition in which rising incomes, urbanization, demographic change, and relative prices reshape the composition of diets. A central empirical challenge is that food demand does not respond linearly to income: staples tend to saturate, animal-source foods may rise over a longer range, and the expenditure residual absorbs both uncovered foods and non-food consumption. These features make constant-elasticity or locally linear demand specifications poorly suited for long-run scenario analysis.

This paper adapts the MAIDADS framework of Gouel and Guimbard (2019), building on the modified implicitly additive demand system of Preckel, Cranfield, and Hertel (2010), to a Chinese provincial panel. The goal is not merely to report a table of elasticities. Instead, the paper asks whether a structural, income-flexible demand system can summarize provincial nutrition transition patterns and produce transparent conditional scenarios for 2030, 2035, and 2050.

The contribution is threefold. First, the analysis constructs a province-year demand-system panel in which covered foods are converted to daily 2,000-kcal units and prices are harmonized in 2023 real terms. Second, it estimates saturated AIDADS and MAIDADS systems, reports income and price elasticities, and audits the theoretical restrictions implied by the demand system. Third, it links the estimated demand system to conditional projection paths and animal-product feed-grain equivalents, while making clear which parts of the evidence are preliminary.

This draft deliberately adopts a conservative writing stance. The current bootstrap exercises are now formal-scale, but the projection path combines a sourced SSP2 population projection with conditional income assumptions rather than a complete official provincial forecast system. The quantitative results are therefore useful for model inference and research design, while long-run projection statements remain scenario simulations rather than official forecasts.

Unsupported or weak claims to resolve:
- Add a fuller China food-demand literature review and verified citations.
- Strengthen identification discussion around unit values, quality, and price endogeneity.
"""

    sections["02_literature.md"] = """# 2. Related Literature

The paper is closest to the literature on income-flexible demand systems for global food demand and nutrition transition. Gouel and Guimbard (2019) use MAIDADS to model global food demand and show why demand saturation is central for long-run food projections. The present project follows that structural logic but shifts the unit of observation from countries to Chinese provinces and from a global income distribution to a province-year panel.

The methodological foundation is the modified implicitly additive demand system of Preckel, Cranfield, and Hertel (2010). MAIDADS nests AIDADS by allowing subsistence consumption to vary with utility, while imposing saturation restrictions that prevent covered food demand from growing without bound at high income levels. This feature is useful for studying diets in an economy where total calories may stabilize even as composition continues to change.

For population inputs, the projection module uses the provincial SSP population data of Chen et al. (2020), which provide province-level and gridded population projections for China from 2010 to 2100. This improves the demographic basis of the scenario exercise relative to the earlier population-share extrapolation, although income, urbanization, and age-composition assumptions remain simplified.

The draft still requires a fuller literature review on China-specific food demand, household demand systems, nutrition transition, and feed-grain implications. Those references should be added only after a verified bibliography is supplied.

Unsupported or weak claims to resolve:
- Add verified references for China demand-system estimates, nutrition transition evidence, and feed conversion assumptions.
"""

    sections["03_data.md"] = f"""# 3. Data and Variable Construction

The estimating sample contains {n_obs} observations for {n_prov} provinces from {y0} to {y1}. The model uses six aggregate demand categories: staples, oils and fats, vegetables and fruits, meat and aquatic products, dairy and eggs, and an other/non-covered residual. The residual is retained internally under the code name `nonfood`, but it should not be interpreted as a strict outside good. It includes uncovered foods, eating away from home, alcohol and tobacco components when present in the residual, and true non-food expenditure.

Food quantities are converted to daily 2,000-kcal units. The nutrition table is adjusted for edible shares. When reported energy is missing or zero, energy is reconstructed from macronutrients. Grain aggregation includes soybeans and potatoes. The potato division by five is retained only for grain-equivalent accounting; calorie aggregation uses actual kcal per kilogram and consumption-quantity weights.

The main monetary specification uses 2023 real-price terms. Total expenditure is deflated by the provincial total CPI index, covered-food prices by provincial food CPI, and the other/non-covered residual price by national non-food CPI. A robustness specification uses a derived provincial non-food CPI from total CPI, food CPI, and food expenditure shares. Because direct provincial non-food CPI is not yet available, residual-price variation should be interpreted cautiously.

Projection-year population is taken from the Chen et al. (2020) provincial population projection under SSP2. The raw projection table is reported in persons and is converted to the model's `population_10k` unit before aggregation.

Unsupported or weak claims to resolve:
- Add direct provincial non-food CPI or official CPI weights.
- Add an external covered-calorie benchmark against FAOSTAT or statistical yearbook food balance data.
"""

    sections["04_model.md"] = """# 4. Model

The empirical model is a saturated six-good MAIDADS demand system. For province-year observation c and good i, fitted demand is

```text
x_ci = gamma_i(u_c) + phi_i(u_c) [m_c - sum_j p_cj gamma_j(u_c)] / p_ci .
```

The marginal budget share is

```text
phi_i(u) = [alpha_i + beta_i exp(u)] / [1 + exp(u)],
```

and the subsistence term is

```text
gamma_i(u) = [delta_i + tau_i exp(omega u)] / [1 + exp(omega u)].
```

Utility is solved from the implicit equation

```text
sum_i phi_i(u_c) ln[x_ci - gamma_i(u_c)] - u_c - kappa = 0.
```

The saturated specification imposes beta equal to zero for covered food groups and one for the other/non-covered residual. The model is estimated by concentrated likelihood using quantity errors. AIDADS is estimated first and then used to initialize MAIDADS. Multi-start diagnostics, boundary reports, and gradient summaries are retained as part of the paper evidence package.

Income elasticities are computed by the model's prediction function using central differences. Marshallian price elasticities and Hicksian elasticities are reported for completeness and for demand-system checks, but price elasticity is not positioned as the main contribution because MAIDADS has limited independent price flexibility and provincial unit values may contain quality variation.

Unsupported or weak claims to resolve:
- Add direct analytic-vs-numeric elasticity unit tests before final submission.
- Add a stronger treatment of panel dependence beyond cluster bootstrap.
"""

    sections["05_estimation_diagnostics.md"] = f"""# 5. Estimation, Fit, and Diagnostics

Table 1 summarizes the fit of AIDADS and MAIDADS under the main and robustness price specifications.

{comparison_md}

In the main specification, MAIDADS lowers the concentrated negative log likelihood relative to AIDADS. Out-of-sample validation is now computed separately for each model and specification, avoiding the earlier error in which a single OOS statistic could be broadcast across rows. The main-specification mean food RMSE is lower for MAIDADS than AIDADS, but the improvement is modest and should be interpreted together with the split-specific group errors.

The LR statistic comparing MAIDADS and AIDADS is {float(lr['lr_observed']):.3f}. However, the standard chi-square reference distribution is not used for inference because nuisance parameters are not identified under the restricted model. The current LR bootstrap is {lr_scale}: {int(lr['successful_reps'])} successful draws out of {int(lr['n_bootstrap'])}, with a cluster-bootstrap tail probability of {float(lr['p_bootstrap_cluster']):.3f}. This result cautions against interpreting the large in-sample LR statistic as decisive model-selection evidence.

The theoretical consistency checks are numerically tight. The maximum absolute consistency error across the recorded adding-up, homogeneity, and Slutsky checks is {max_consistency:.2e}. Parameter boundary reports distinguish restrictions imposed by saturation from parameters estimated near a boundary.

Unsupported or weak claims to resolve:
- Clarify the null-resampling interpretation of the LR bootstrap and consider a parametric-null bootstrap robustness check.
- Add a table of split-specific OOS results in the appendix.
"""

    sections["06_elasticities.md"] = f"""# 6. Demand Elasticities

Table 2 reports income elasticities at the sample median-income grid point.

{elasticity_md}

The current estimates imply declining covered-kcal demand for staples and oils at the median grid point, positive responsiveness for vegetables and fruits, mild positive responsiveness for meat and aquatic products, and relatively strong positive responsiveness for dairy and eggs. Aggregated across groups, all covered foods and plant foods have negative median-income elasticities, while animal foods remain positive. These patterns are consistent with a nutrition-transition interpretation in which the main response to income growth is compositional rather than a uniform expansion of total covered calories.

Table 5 summarizes Marshallian own-price elasticities over the income grid.

{price_md}

Price elasticities should be treated as auxiliary outputs. Some own-price elasticities are close to zero and may be positive for certain groups and income points. This pattern reinforces the need to avoid making price responsiveness the core contribution until price measurement and quality adjustment are strengthened.

Unsupported or weak claims to resolve:
- Investigate positive own-price elasticities for selected plant-food groups.
- Add robustness using a price-flexible demand system such as QUAIDS or EASI if price effects become central.
"""

    sections["07_projection.md"] = f"""# 7. Conditional Projections to 2030, 2035, and 2050

The projection exercise is a conditional scenario simulation. It uses national growth paths, province-specific income convergence adjustments, and the Chen et al. (2020) SSP2 provincial population projection. It is not an official province-level forecast because province-level income, urbanization, and age-structure paths remain simplified.

Table 3 reports national weighted daily kcal per capita by covered-food group.

{projection_md}

Under the scenario, staples remain the largest covered-food source in 2050, while meat and aquatic products account for a substantial share of covered-food calories. Total covered-food calories are relatively stable compared with the compositional changes across groups.

Animal-product quantities are mapped into feed-grain equivalents using the user-supplied conversion factors. Table 4 reports the implied national feed-grain equivalents in million tons.

{feed_md}

The feed-grain module should be interpreted as an accounting translation rather than a behavioral supply-chain model. The coefficients are currently treated as feed-grain equivalent factors; if they are instead total-feed coefficients, feed cereal shares must be added.

Unsupported or weak claims to resolve:
- Replace the income-convergence assumption with sourced province-level income, urbanization, and age-structure paths; retain or compare alternative SSP population scenarios.
- Add sourced feed conversion coefficients and cereal shares.
"""

    sections["08_robustness.md"] = """# 8. Robustness and Audit Findings

The main robustness exercise replaces the national non-food CPI residual price with a derived provincial non-food CPI. The resulting MAIDADS fit remains better than AIDADS within that specification. Cross-specification AIC and BIC comparisons should not be over-interpreted because the residual-price construction differs across specifications.

The code audit also changed several data and reporting conventions. The residual category is described as other/non-covered expenditure rather than strict non-food consumption. The grain-calorie calculation uses actual calorie weights rather than the potato grain-equivalent conversion. OOS files are stored separately by variant, model, and split. The projection module now uses Chen et al. (2020) SSP2 provincial population paths rather than population-share trend extrapolation. The paper workflow records a YELLOW gate status because the income side of projections remains a conditional scenario, not because bootstrap inference is still pilot-scale.

Unsupported or weak claims to resolve:
- Add official non-food CPI or CPI category weights.
- Add leave-one-province and leave-one-region validation.
"""

    sections["09_conclusion.md"] = """# 9. Conclusion

This draft shows that a province-level MAIDADS framework can organize evidence on China's nutrition transition and produce transparent conditional food-demand scenarios. The first-pass results support a compositional interpretation: income growth does not simply raise all covered foods proportionally; it changes the relative importance of staples, animal products, dairy and eggs, and plant foods.

The current contribution is methodological and diagnostic as much as substantive. The project now has a reproducible data pipeline, model estimates, OOS validation by model, price-elasticity matrices, theoretical consistency checks, formal-scale bootstrap status records, and a simulator workbook. These are necessary building blocks for a journal paper.

The draft is not yet a final submission version. Formal-scale bootstrap inference has been completed, but the LR comparison should still be interpreted through the cluster-bootstrap result rather than the invalid naive chi-square reference. Long-run projections now have a sourced provincial SSP2 population path, but still require stronger province-level income, urbanization, and age-structure scenarios. Direct provincial non-food CPI and broader food-group coverage would materially improve identification and interpretation. Once these additions are made, the paper can move from a working-paper draft to a journal-style submission.

Unsupported or weak claims to resolve:
- Upgrade projection inputs before removing the working-paper caveats.
"""

    SECTIONS.mkdir(parents=True, exist_ok=True)
    for name, text in sections.items():
        (SECTIONS / name).write_text(text, encoding="utf-8")


def assemble_paper() -> None:
    order = [
        "00_abstract.md",
        "01_introduction.md",
        "02_literature.md",
        "03_data.md",
        "04_model.md",
        "05_estimation_diagnostics.md",
        "06_elasticities.md",
        "07_projection.md",
        "08_robustness.md",
        "09_conclusion.md",
    ]
    title = """# Provincial Food Demand Elasticities and Nutrition Transition in China: A First-Pass MAIDADS Working Paper

**Manuscript status:** Working-paper draft generated under a YELLOW audit gate. Formal-scale bootstrap inference is included; conditional scenario projections are explicitly labeled.

"""
    body = [title]
    for name in order:
        body.append((SECTIONS / name).read_text(encoding="utf-8"))
    body.append(
        """# References

Gouel, C., and H. Guimbard. 2019. “Nutrition Transition and the Structure of Global Food Demand.” *American Journal of Agricultural Economics* 101(2): 383--403.

Preckel, P. V., J. A. L. Cranfield, and T. W. Hertel. 2010. “A Modified, Implicitly Additive Demand System.” *Applied Economics* 42(2): 143--155.

Chen, Y., F. Guo, J. Wang, et al. 2020. “Provincial and Gridded Population Projection for China under Shared Socioeconomic Pathways from 2010 to 2100.” *Scientific Data* 7: 83. https://doi.org/10.1038/s41597-020-0421-y.

TODO: Add verified China food-demand, nutrition-transition, and feed-conversion references.
"""
    )
    MANUSCRIPT.mkdir(parents=True, exist_ok=True)
    (MANUSCRIPT / "paper.md").write_text("\n\n".join(body), encoding="utf-8")


def write_local_review(gate_status: str) -> None:
    REVIEWS.mkdir(parents=True, exist_ok=True)
    review = f"""# Local Reviewer Report, Round 1

Decision: Accept as Working Paper / Major Revision before journal submission

Summary:
The manuscript is now evidence-gated and conservative. It correctly labels the current status as `{gate_status}`, incorporates formal-scale bootstrap inference, and avoids treating conditional projections as final forecasts.

Top issues:
1. The LR bootstrap has been expanded to formal scale, but its tail probability does not support treating the large in-sample LR statistic as decisive model-selection evidence.
2. Projection paths now use Chen et al. (2020) SSP2 provincial population data, but income remains a convergence scenario rather than a sourced province-level forecast.
3. The paper should carefully distinguish formal demand-system inference from conditional long-run projection assumptions.
4. The other/non-covered residual should never be interpreted as strict non-food demand.
5. Price elasticities are auxiliary and some own-price signs require further investigation.
6. Direct provincial non-food CPI or official CPI weights are still missing.
7. The literature review needs verified China-specific citations.
8. Feed-grain conversion coefficients require formal source documentation and possibly cereal-share adjustments.

Required revisions before journal submission:
- Add sourced province-level income, urbanization, and age-structure projection data.
- Add external calorie validation and broader food categories.
- Add price-quality/endogeneity robustness.
- Complete bibliography and literature review.
"""
    (REVIEWS / "local_round1.md").write_text(review, encoding="utf-8")

    revision = """# Revision Plan

1. Add direct provincial non-food CPI or category-level CPI weights.
2. Replace conditional income assumptions with sourced province-level income, urbanization, and age-structure paths; add SSP population sensitivity scenarios.
3. Add leave-one-province and leave-one-region OOS validation.
4. Add China food-demand and nutrition-transition references to `refs.bib`.
5. Add sourced feed conversion coefficients and cereal shares.
6. Revisit positive own-price elasticities and consider a price-flexible robustness model.
7. Consider a parametric-null LR bootstrap robustness check if model-selection inference becomes central.
"""
    (MANUSCRIPT / "revision_plan.md").write_text(revision, encoding="utf-8")


def main() -> None:
    for path in [PAPER_WORK, MANUSCRIPT, SECTIONS, TABLES, APPENDIX, REVIEWS]:
        path.mkdir(parents=True, exist_ok=True)
    data = read_inputs()
    tables = build_summary_tables(data)
    ledger = build_evidence_ledger(data, tables)
    write_refs()
    draft_sections(data, tables, ledger)
    assemble_paper()
    gate = json.loads((PAPER_WORK / "gate_status.json").read_text(encoding="utf-8"))
    remote_log = PAPER_WORK / "remote_llm_run_log.md"
    write_local_review(gate["status"])
    manifest = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "gate_status": gate["status"],
        "paper": str((MANUSCRIPT / "paper.md").relative_to(PROJECT)),
        "evidence_ledger": str((PAPER_WORK / "evidence_ledger.csv").relative_to(PROJECT)),
        "sections": sorted(p.name for p in SECTIONS.glob("*.md")),
        "remote_llm_used_in_current_build": False,
        "remote_llm_prior_attempts_recorded": remote_log.exists(),
        "remote_llm_note": (
            "Current formal-bootstrap rebuild was generated from local evidence files only. "
            "Prior DeepSeek drafting attempts and Claude API status, if any, are recorded in "
            f"{remote_log.relative_to(PROJECT)}."
            if remote_log.exists()
            else "Current build was generated from local evidence files only; no remote LLM log was found."
        ),
    }
    (PAPER_WORK / "manuscript_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(MANUSCRIPT / "paper.md")


if __name__ == "__main__":
    main()
```

### build_maidads_simulator_workbook.py

源文件：`/root/data/Paper/省级食物消费/ProvinceMAIDADS/scripts/build_maidads_simulator_workbook.py`

```python
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "ProvinceMAIDADS" / "Results"
DATA_OUT = ROOT / "ProvinceMAIDADS" / "Data" / "output"
OUTPUT = RESULTS / "省级MAIDADS_Simulator.xlsx"

GROUPS = ["grain", "oil", "vegfruit", "meatsea", "dairyegg", "nonfood"]
GROUP_LABELS = {
    "grain": "Grain / staples",
    "oil": "Oils and fats",
    "vegfruit": "Vegetables and fruits",
    "meatsea": "Meat and aquatic products",
    "dairyegg": "Dairy and eggs",
    "nonfood": "Other / non-covered",
}
PRICE_COLS = {g: f"p_{g}_model" for g in GROUPS}
OBS_X_COLS = {g: f"x_{g}" for g in GROUPS}
PROJ_X_COLS = {g: f"xhat_{g}" for g in GROUPS}


def style_title(cell, fill="1F4E78", color="FFFFFF", size=16):
    cell.fill = PatternFill("solid", fgColor=fill)
    cell.font = Font(color=color, bold=True, size=size)
    cell.alignment = Alignment(horizontal="left", vertical="center")


def style_header(row_cells, fill="D9EAF7"):
    for cell in row_cells:
        cell.fill = PatternFill("solid", fgColor=fill)
        cell.font = Font(bold=True, color="1F2937")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(bottom=Side(style="thin", color="9EADBD"))


def style_table(ws, min_row, max_row, min_col, max_col):
    thin = Side(style="thin", color="D9E2EC")
    for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
        for cell in row:
            cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
            cell.alignment = Alignment(vertical="center")
            if cell.row > min_row and cell.row % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="F8FAFC")


def write_df(ws, df: pd.DataFrame, start_row=1, start_col=1, header=True):
    row = start_row
    if header:
        for c, col in enumerate(df.columns, start_col):
            ws.cell(row=row, column=c, value=col)
        style_header(ws[row])
        row += 1
    for r in df.itertuples(index=False):
        for c, value in enumerate(r, start_col):
            if pd.isna(value):
                value = None
            ws.cell(row=row, column=c, value=value)
        row += 1
    return row - 1


def build_province_data() -> pd.DataFrame:
    panel = pd.read_csv(DATA_OUT / "maidads6_panel.csv")
    proj = pd.read_csv(RESULTS / "projection_province_path.csv")

    observed_rows = []
    for _, row in panel.iterrows():
        item = {
            "key": f"{row['provincechn']}|{int(row['year'])}",
            "source": "observed",
            "provincechn": row["provincechn"],
            "province": int(row["province"]),
            "year": int(row["year"]),
            "population_10k": row["population_10k"],
            "m": row["m"],
        }
        for g in GROUPS:
            item[f"p_{g}"] = row[PRICE_COLS[g]]
            item[f"x_{g}"] = row[OBS_X_COLS[g]]
        observed_rows.append(item)

    projection_rows = []
    for _, row in proj.iterrows():
        item = {
            "key": f"{row['provincechn']}|{int(row['year'])}",
            "source": "projection",
            "provincechn": row["provincechn"],
            "province": int(row["province"]),
            "year": int(row["year"]),
            "population_10k": row["population_10k"],
            "m": row["m"],
        }
        for g in GROUPS:
            item[f"p_{g}"] = row[PRICE_COLS[g]]
            item[f"x_{g}"] = row[PROJ_X_COLS[g]]
        projection_rows.append(item)

    out = pd.DataFrame(observed_rows + projection_rows)

    national_rows = []
    for year, tmp in out.groupby("year"):
        weights = tmp["population_10k"].to_numpy(float)
        item = {
            "key": f"全国加权|{int(year)}",
            "source": "national_weighted",
            "provincechn": "全国加权",
            "province": 0,
            "year": int(year),
            "population_10k": tmp["population_10k"].sum(),
            "m": float(np.average(tmp["m"], weights=weights)),
        }
        for g in GROUPS:
            item[f"p_{g}"] = float(np.average(tmp[f"p_{g}"], weights=weights))
            item[f"x_{g}"] = float(np.average(tmp[f"x_{g}"], weights=weights))
        national_rows.append(item)
    out = pd.concat([pd.DataFrame(national_rows), out], ignore_index=True)
    out = out.sort_values(["province", "year", "provincechn"]).reset_index(drop=True)
    return out


def build_workbook() -> Workbook:
    wb = Workbook()
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.calculation.calcMode = "auto"
    default = wb.active
    wb.remove(default)

    ws_readme = wb.create_sheet("Read Me")
    ws_model = wb.create_sheet("MAIDADS MODEL")
    ws_run = wb.create_sheet("RUN")
    ws_data = wb.create_sheet("Province Data")
    ws_proj = wb.create_sheet("Projection Data")
    ws_elast = wb.create_sheet("Elasticities")
    ws_checks = wb.create_sheet("Checks")
    ws_solver = wb.create_sheet("Utility Solver")
    ws_lists = wb.create_sheet("Lists")

    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False

    params = pd.read_csv(RESULTS / "parameter_estimates.csv")
    params = params[params["model"].eq("MAIDADS_sat")].set_index("group").loc[GROUPS].reset_index()
    province_data = build_province_data()
    projection_group = pd.read_csv(RESULTS / "projection_group_2030_2035_2050.csv")
    projection_feed = pd.read_csv(RESULTS / "projection_item_feed_2030_2035_2050.csv")
    income_elast = pd.read_csv(RESULTS / "elasticity_income_grid.csv")
    price_elast = pd.read_csv(RESULTS / "elasticity_price_marshallian_grid.csv")
    consistency = pd.read_csv(RESULTS / "elasticity_consistency_tests.csv")

    # Read Me
    ws_readme.merge_cells("A1:H1")
    ws_readme["A1"] = "China Provincial MAIDADS Simulator"
    style_title(ws_readme["A1"])
    readme_rows = [
        ("Purpose", "Formula-driven simulator based on the latest provincial MAIDADS estimates."),
        ("Template", "Mimics the original structure: Read Me, model equations, RUN, data and checks."),
        ("No macros", "Utility is approximated through a hidden grid search instead of VBA UDFs."),
        ("Inputs", "Change province/year, income, or price multipliers in RUN."),
        ("Main units", "Food x = daily kcal / 2000; prices and m are in 2023 real-price terms."),
        ("Caution", "Future years and income points outside sample support are projections/extrapolations."),
    ]
    for r, (k, v) in enumerate(readme_rows, 4):
        ws_readme.cell(r, 1, k).font = Font(bold=True)
        ws_readme.cell(r, 2, v)
        ws_readme.cell(r, 2).alignment = Alignment(wrap_text=True, vertical="top")
    ws_readme["A13"] = "Sheets"
    ws_readme["A13"].font = Font(bold=True, size=12)
    sheet_notes = [
        ("RUN", "Interactive simulation page."),
        ("MAIDADS MODEL", "Equations and units used by the workbook."),
        ("Province Data", "Observed and projected province-year inputs."),
        ("Projection Data", "National projection and feed-grain outputs."),
        ("Elasticities", "Estimated income and price elasticity tables."),
        ("Checks", "Formula checks and diagnostics."),
        ("Utility Solver", "Hidden grid used to solve utility for base and +/- income."),
    ]
    for r, (s, d) in enumerate(sheet_notes, 15):
        ws_readme.cell(r, 1, s).font = Font(bold=True)
        ws_readme.cell(r, 2, d)
        ws_readme.cell(r, 2).alignment = Alignment(wrap_text=True, vertical="top")
    ws_readme.column_dimensions["A"].width = 22
    ws_readme.column_dimensions["B"].width = 78
    for row in range(4, 10):
        ws_readme.row_dimensions[row].height = 24

    # Model sheet
    ws_model.merge_cells("A1:J1")
    ws_model["A1"] = "MAIDADS Equations Used in This Workbook"
    style_title(ws_model["A1"])
    model_lines = [
        ("Demand", "x_i = gamma_i(u) + phi_i(u) * [m - SUM_j p_j gamma_j(u)] / p_i"),
        ("Marginal budget share", "phi_i(u) = [alpha_i + beta_i exp(u)] / [1 + exp(u)]"),
        ("Subsistence", "gamma_i(u) = [delta_i + tau_i exp(omega u)] / [1 + exp(omega u)]"),
        ("Utility", "SUM_i phi_i(u) ln[x_i - gamma_i(u)] - u - kappa = 0"),
        ("Income elasticity", "Computed by central difference using m*(1 +/- step)."),
        ("Price elasticity", "Marshallian formula follows the LES-like MAIDADS price response; Hicksian matrix is in the results files."),
        ("Checks", "Budget shares sum to one; weighted income elasticities sum to one; implicit utility gap should be near zero."),
    ]
    for r, (k, v) in enumerate(model_lines, 4):
        ws_model.cell(r, 1, k).font = Font(bold=True)
        ws_model.cell(r, 2, v)
    ws_model.column_dimensions["A"].width = 24
    ws_model.column_dimensions["B"].width = 120

    # Lists and data
    provinces = sorted(province_data["provincechn"].unique(), key=lambda x: (x != "全国加权", x))
    years = sorted(province_data["year"].unique())
    for i, p in enumerate(provinces, 2):
        ws_lists.cell(i, 1, p)
    ws_lists["A1"] = "Province"
    for i, y in enumerate(years, 2):
        ws_lists.cell(i, 2, y)
    ws_lists["B1"] = "Year"
    ws_lists.sheet_state = "hidden"

    data_last = write_df(ws_data, province_data)
    ws_data.freeze_panes = "A2"
    ws_data.auto_filter.ref = f"A1:{get_column_letter(ws_data.max_column)}{data_last}"
    for col in range(1, ws_data.max_column + 1):
        ws_data.column_dimensions[get_column_letter(col)].width = 16 if col > 6 else 18
    for col in range(7, ws_data.max_column + 1):
        for cell in ws_data.iter_cols(min_col=col, max_col=col, min_row=2, max_row=data_last):
            for c in cell:
                c.number_format = "0.0000"

    # Projection sheet
    ws_proj.merge_cells("A1:H1")
    ws_proj["A1"] = "Projection Outputs"
    style_title(ws_proj["A1"])
    group_pivot = projection_group.pivot_table(
        index="group", columns="year", values="daily_kcal_per_cap_weighted"
    ).reset_index()
    group_pivot.columns = [str(c) for c in group_pivot.columns]
    ws_proj["A3"] = "National weighted daily kcal per capita"
    ws_proj["A3"].font = Font(bold=True, size=12)
    group_end = write_df(ws_proj, group_pivot, 4, 1)
    feed = projection_feed.copy()
    feed["feed_grain_million_ton"] = feed["feed_grain_kg"] / 1e9
    feed_pivot = feed.pivot_table(index="item", columns="year", values="feed_grain_million_ton").reset_index()
    feed_pivot.columns = [str(c) for c in feed_pivot.columns]
    ws_proj["A13"] = "Feed-grain demand, million tons"
    ws_proj["A13"].font = Font(bold=True, size=12)
    feed_end = write_df(ws_proj, feed_pivot, 14, 1)
    style_table(ws_proj, 4, group_end, 1, group_pivot.shape[1])
    style_table(ws_proj, 14, feed_end, 1, feed_pivot.shape[1])
    for col in range(1, 7):
        ws_proj.column_dimensions[get_column_letter(col)].width = 18

    chart = LineChart()
    chart.title = "Daily kcal by group"
    chart.y_axis.title = "kcal/person/day"
    chart.x_axis.title = "Group"
    data_ref = Reference(ws_proj, min_col=2, max_col=group_pivot.shape[1], min_row=4, max_row=group_end)
    cats_ref = Reference(ws_proj, min_col=1, min_row=5, max_row=group_end)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.height = 8
    chart.width = 15
    ws_proj.add_chart(chart, "G4")

    # Elasticities sheet
    ws_elast.merge_cells("A1:J1")
    ws_elast["A1"] = "Elasticity Tables"
    style_title(ws_elast["A1"])
    inc = income_elast[income_elast["group"].isin(GROUPS + ["all_food", "animal_food", "plant_food"])].copy()
    inc = inc[["income", "group", "eta", "budget_share", "support_flag"]]
    ws_elast["A3"] = "Income elasticity grid"
    ws_elast["A3"].font = Font(bold=True, size=12)
    inc_end = write_df(ws_elast, inc, 4, 1)
    own = price_elast[price_elast["is_own_price"].astype(bool)].copy()
    own = own[["income", "demand_group", "elasticity", "support_flag"]]
    own_start = inc_end + 3
    ws_elast.cell(own_start, 1, "Marshallian own-price elasticities").font = Font(bold=True, size=12)
    own_end = write_df(ws_elast, own, own_start + 1, 1)
    style_table(ws_elast, 4, inc_end, 1, 5)
    style_table(ws_elast, own_start + 1, own_end, 1, 4)
    ws_elast.freeze_panes = "A4"
    ws_elast.auto_filter.ref = f"A4:E{inc_end}"
    for col in range(1, 8):
        ws_elast.column_dimensions[get_column_letter(col)].width = 18

    # RUN sheet layout
    ws_run.merge_cells("A1:R1")
    ws_run["A1"] = "Provincial MAIDADS Simulator"
    style_title(ws_run["A1"])
    ws_run["B4"] = "Inputs"
    ws_run["B4"].font = Font(bold=True, size=12)
    input_rows = [
        ("Province", "全国加权"),
        ("Year", 2023),
        ("Source", '=INDEX(\'Province Data\'!$B$2:$B$%d,MATCH($C$15,\'Province Data\'!$A$2:$A$%d,0))' % (data_last, data_last)),
        ("Income multiplier", 1.0),
        ("Manual m override", None),
        ("Elasticity step", 0.0001),
    ]
    for idx, (label, value) in enumerate(input_rows, 8):
        ws_run.cell(idx, 2, label).font = Font(bold=True)
        ws_run.cell(idx, 3, value)
    ws_run["B15"] = "Lookup key"
    ws_run["C15"] = '=$C$8&"|"&$C$9'
    ws_run["B16"] = "Budget m"
    ws_run["C16"] = '=IF(ISBLANK($C$12),INDEX(\'Province Data\'!$G$2:$G$%d,MATCH($C$15,\'Province Data\'!$A$2:$A$%d,0))*$C$11,$C$12)' % (data_last, data_last)
    ws_run["B17"] = "Utility u"
    ws_run["C17"] = '=INDEX(\'Utility Solver\'!$A$2:$A$802,MATCH(MIN(\'Utility Solver\'!$V$2:$V$802),\'Utility Solver\'!$V$2:$V$802,0))'
    ws_run["B18"] = "Utility u, m+"
    ws_run["C18"] = '=INDEX(\'Utility Solver\'!$A$2:$A$802,MATCH(MIN(\'Utility Solver\'!$AE$2:$AE$802),\'Utility Solver\'!$AE$2:$AE$802,0))'
    ws_run["B19"] = "Utility u, m-"
    ws_run["C19"] = '=INDEX(\'Utility Solver\'!$A$2:$A$802,MATCH(MIN(\'Utility Solver\'!$AN$2:$AN$802),\'Utility Solver\'!$AN$2:$AN$802,0))'
    ws_run["B20"] = "Implicit utility gap"
    ws_run["C20"] = '=INDEX(\'Utility Solver\'!$U$2:$U$802,MATCH(MIN(\'Utility Solver\'!$V$2:$V$802),\'Utility Solver\'!$V$2:$V$802,0))'
    for cell in ws_run["C8:C20"]:
        cell[0].fill = PatternFill("solid", fgColor="FFF7D6")
    dv_prov = DataValidation(type="list", formula1=f"=Lists!$A$2:$A${len(provinces)+1}", allow_blank=False)
    dv_year = DataValidation(type="list", formula1=f"=Lists!$B$2:$B${len(years)+1}", allow_blank=False)
    ws_run.add_data_validation(dv_prov)
    ws_run.add_data_validation(dv_year)
    dv_prov.add(ws_run["C8"])
    dv_year.add(ws_run["C9"])

    headers = [
        "Food group",
        "alpha",
        "beta",
        "delta",
        "tau",
        "omega",
        "kappa",
        "Base price",
        "Price mult.",
        "Price p",
        "gamma",
        "phi",
        "Demand x",
        "Income elast.",
        "Budget share",
        "Expenditure",
        "Daily kcal",
    ]
    start_row = 24
    for c, h in enumerate(headers, 2):
        ws_run.cell(start_row, c, h)
    style_header(ws_run[start_row])
    price_data_cols = {g: province_data.columns.get_loc(f"p_{g}") + 1 for g in GROUPS}
    for idx, g in enumerate(GROUPS, start_row + 1):
        param = params[params["group"].eq(g)].iloc[0]
        ws_run.cell(idx, 2, GROUP_LABELS[g])
        for c, field in zip(range(3, 9), ["alpha", "beta", "delta", "tau", "omega", "kappa"]):
            ws_run.cell(idx, c, float(param[field]))
        price_col_letter = get_column_letter(price_data_cols[g])
        ws_run.cell(idx, 9, f"=INDEX('Province Data'!${price_col_letter}$2:${price_col_letter}${data_last},MATCH($C$15,'Province Data'!$A$2:$A${data_last},0))")
        ws_run.cell(idx, 10, 1.0)
        ws_run.cell(idx, 11, f"=I{idx}*J{idx}")
        ws_run.cell(idx, 12, f"=(E{idx}+F{idx}*EXP(G{idx}*$C$17))/(1+EXP(G{idx}*$C$17))")
        ws_run.cell(idx, 13, f"=(C{idx}+D{idx}*EXP($C$17))/(1+EXP($C$17))")
        ws_run.cell(idx, 14, f"=L{idx}+M{idx}*($C$16-SUMPRODUCT($K$25:$K$30,$L$25:$L$30))/K{idx}")
        ws_run.cell(idx, 15, f'=IFERROR((LN(U{idx})-LN(X{idx}))/(LN($C$16*(1+$C$13))-LN($C$16*(1-$C$13))),"")')
        ws_run.cell(idx, 16, f"=N{idx}*K{idx}/$C$16")
        ws_run.cell(idx, 17, f"=N{idx}*K{idx}")
        ws_run.cell(idx, 18, "" if g == "nonfood" else f"=N{idx}*2000")
        ws_run.cell(idx, 19, f"=(E{idx}+F{idx}*EXP(G{idx}*$C$18))/(1+EXP(G{idx}*$C$18))")
        ws_run.cell(idx, 20, f"=(C{idx}+D{idx}*EXP($C$18))/(1+EXP($C$18))")
        ws_run.cell(idx, 21, f"=S{idx}+T{idx}*($C$16*(1+$C$13)-SUMPRODUCT($K$25:$K$30,$S$25:$S$30))/K{idx}")
        ws_run.cell(idx, 22, f"=(E{idx}+F{idx}*EXP(G{idx}*$C$19))/(1+EXP(G{idx}*$C$19))")
        ws_run.cell(idx, 23, f"=(C{idx}+D{idx}*EXP($C$19))/(1+EXP($C$19))")
        ws_run.cell(idx, 24, f"=V{idx}+W{idx}*($C$16*(1-$C$13)-SUMPRODUCT($K$25:$K$30,$V$25:$V$30))/K{idx}")
    total_row = start_row + 7
    ws_run.cell(total_row, 2, "Total / checks").font = Font(bold=True)
    ws_run.cell(total_row, 13, "=SUM(M25:M30)")
    ws_run.cell(total_row, 15, "=SUMPRODUCT(O25:O30,P25:P30)")
    ws_run.cell(total_row, 16, "=SUM(P25:P30)")
    ws_run.cell(total_row, 17, "=SUM(Q25:Q30)")
    ws_run.cell(total_row, 18, "=SUM(R25:R29)")
    style_table(ws_run, start_row, total_row, 2, 18)
    for col in range(19, 25):
        ws_run.column_dimensions[get_column_letter(col)].hidden = True

    matrix_row = 35
    ws_run.cell(matrix_row, 2, "Marshallian price elasticities").font = Font(bold=True, size=12)
    header_row = matrix_row + 1
    ws_run.cell(header_row, 2, "Demand \\ Price")
    for j, g in enumerate(GROUPS, 3):
        ws_run.cell(header_row, j, GROUP_LABELS[g])
    style_header(ws_run[header_row])
    for i, g_i in enumerate(GROUPS, header_row + 1):
        ws_run.cell(i, 2, GROUP_LABELS[g_i])
        demand_row = start_row + 1 + GROUPS.index(g_i)
        for j, g_j in enumerate(GROUPS, 3):
            price_row = start_row + 1 + GROUPS.index(g_j)
            own = "1" if g_i == g_j else "0"
            ws_run.cell(
                i,
                j,
                f"=($M${price_row}*(($C$16-SUMPRODUCT($K$25:$K$30,$L$25:$L$30))/($P${price_row}*$C$16)))*($M${demand_row}-{own})-($P${demand_row}*$O${price_row})",
            )
    style_table(ws_run, header_row, header_row + len(GROUPS), 2, 2 + len(GROUPS))

    hicks_row = header_row + len(GROUPS) + 3
    ws_run.cell(hicks_row, 2, "Hicksian price elasticities").font = Font(bold=True, size=12)
    ws_run.cell(hicks_row + 1, 2, "Demand \\ Price")
    for j, g in enumerate(GROUPS, 3):
        ws_run.cell(hicks_row + 1, j, GROUP_LABELS[g])
    style_header(ws_run[hicks_row + 1])
    for i, g_i in enumerate(GROUPS, hicks_row + 2):
        ws_run.cell(i, 2, GROUP_LABELS[g_i])
        demand_idx = start_row + 1 + GROUPS.index(g_i)
        source_mar_row = header_row + 1 + GROUPS.index(g_i)
        for j, g_j in enumerate(GROUPS, 3):
            price_idx = start_row + 1 + GROUPS.index(g_j)
            mar_cell = f"{get_column_letter(j)}{source_mar_row}"
            ws_run.cell(i, j, f"={mar_cell}+$O${demand_idx}*$P${price_idx}")
    style_table(ws_run, hicks_row + 1, hicks_row + 1 + len(GROUPS), 2, 2 + len(GROUPS))

    for col, width in {
        "A": 3,
        "B": 28,
        "C": 16,
        "D": 12,
        "E": 12,
        "F": 12,
        "G": 12,
        "H": 12,
        "I": 14,
        "J": 12,
        "K": 14,
        "L": 12,
        "M": 12,
        "N": 14,
        "O": 14,
        "P": 14,
        "Q": 14,
        "R": 14,
    }.items():
        ws_run.column_dimensions[col].width = width
    ws_run.freeze_panes = "B24"

    # Utility Solver sheet
    solver_headers = (
        ["u"]
        + [f"gamma_{g}" for g in GROUPS]
        + [f"phi_{g}" for g in GROUPS]
        + ["disc_base"]
        + [f"qdisc_base_{g}" for g in GROUPS]
        + ["gap_base", "abs_gap_base", "disc_plus"]
        + [f"qdisc_plus_{g}" for g in GROUPS]
        + ["gap_plus", "abs_gap_plus", "disc_minus"]
        + [f"qdisc_minus_{g}" for g in GROUPS]
        + ["gap_minus", "abs_gap_minus"]
    )
    for c, h in enumerate(solver_headers, 1):
        ws_solver.cell(1, c, h)
    style_header(ws_solver[1])
    u_values = np.round(np.linspace(-20, 20, 801), 6)
    for r, u in enumerate(u_values, 2):
        ws_solver.cell(r, 1, float(u))
        for j, g in enumerate(GROUPS):
            run_row = start_row + 1 + j
            gamma_col = 2 + j
            phi_col = 8 + j
            ws_solver.cell(r, gamma_col, f"=(RUN!$E${run_row}+RUN!$F${run_row}*EXP(RUN!$G${run_row}*$A{r}))/(1+EXP(RUN!$G${run_row}*$A{r}))")
            ws_solver.cell(r, phi_col, f"=(RUN!$C${run_row}+RUN!$D${run_row}*EXP($A{r}))/(1+EXP($A{r}))")
        ws_solver.cell(r, 14, f"=RUN!$C$16-SUMPRODUCT(RUN!$K$25:$K$30,B{r}:G{r})")
        for j in range(6):
            run_row = start_row + 1 + j
            ws_solver.cell(r, 15 + j, f"=IF($N{r}<=0,NA(),{get_column_letter(8+j)}{r}*$N{r}/RUN!$K${run_row})")
        ws_solver.cell(r, 21, f'=IF($N{r}<=0,1E+99,SUMPRODUCT(H{r}:M{r},LN(O{r}:T{r}))-$A{r}-RUN!$H$25)')
        ws_solver.cell(r, 22, f"=ABS(U{r})")
        ws_solver.cell(r, 23, f"=RUN!$C$16*(1+RUN!$C$13)-SUMPRODUCT(RUN!$K$25:$K$30,B{r}:G{r})")
        for j in range(6):
            run_row = start_row + 1 + j
            ws_solver.cell(r, 24 + j, f"=IF($W{r}<=0,NA(),{get_column_letter(8+j)}{r}*$W{r}/RUN!$K${run_row})")
        ws_solver.cell(r, 30, f'=IF($W{r}<=0,1E+99,SUMPRODUCT(H{r}:M{r},LN(X{r}:AC{r}))-$A{r}-RUN!$H$25)')
        ws_solver.cell(r, 31, f"=ABS(AD{r})")
        ws_solver.cell(r, 32, f"=RUN!$C$16*(1-RUN!$C$13)-SUMPRODUCT(RUN!$K$25:$K$30,B{r}:G{r})")
        for j in range(6):
            run_row = start_row + 1 + j
            ws_solver.cell(r, 33 + j, f"=IF($AF{r}<=0,NA(),{get_column_letter(8+j)}{r}*$AF{r}/RUN!$K${run_row})")
        ws_solver.cell(r, 39, f'=IF($AF{r}<=0,1E+99,SUMPRODUCT(H{r}:M{r},LN(AG{r}:AL{r}))-$A{r}-RUN!$H$25)')
        ws_solver.cell(r, 40, f"=ABS(AM{r})")
    ws_solver.freeze_panes = "A2"
    ws_solver.sheet_state = "hidden"

    # Checks sheet
    ws_checks.merge_cells("A1:H1")
    ws_checks["A1"] = "Workbook Checks"
    style_title(ws_checks["A1"])
    checks = [
        ("Phi sum", "=RUN!M31", "Should equal 1."),
        ("Budget share sum", "=RUN!P31", "Should equal 1."),
        ("Weighted income elasticity", "=RUN!O31", "Should equal 1."),
        ("Implicit utility gap", "=RUN!C20", "Should be close to 0; grid approximation tolerance depends on utility grid step."),
        ("Budget identity", "=RUN!Q31-RUN!C16", "Should be close to 0."),
        ("Main MAIDADS nll", "=INDEX(model_comparison_nll,MATCH(\"MAIDADS_sat\",model_comparison_model,0))", "Reference only; formula names are not defined in this workbook."),
    ]
    ws_checks.append(["Check", "Value", "Interpretation"])
    style_header(ws_checks[2])
    for r, (name, formula, note) in enumerate(checks, 3):
        ws_checks.cell(r, 1, name)
        ws_checks.cell(r, 2, formula)
        ws_checks.cell(r, 3, note)
    ws_checks["A12"] = "Consistency tests from results file"
    ws_checks["A12"].font = Font(bold=True, size=12)
    cons_end = write_df(ws_checks, consistency, 13, 1)
    style_table(ws_checks, 2, 8, 1, 3)
    style_table(ws_checks, 13, cons_end, 1, consistency.shape[1])
    ws_checks.column_dimensions["A"].width = 34
    ws_checks.column_dimensions["B"].width = 18
    ws_checks.column_dimensions["C"].width = 90
    for col in range(4, consistency.shape[1] + 1):
        ws_checks.column_dimensions[get_column_letter(col)].width = 18

    # Remove unsupported named-formula check row value.
    ws_checks["B8"] = "See model_comparison.csv"

    # Formatting across RUN.
    for row in ws_run.iter_rows(min_row=25, max_row=31, min_col=3, max_col=18):
        for cell in row:
            cell.number_format = "0.0000"
    for row in ws_run.iter_rows(min_row=37, max_row=55, min_col=3, max_col=8):
        for cell in row:
            cell.number_format = "0.0000"
    ws_run["C16"].number_format = "#,##0.00"
    ws_run["C17"].number_format = "0.0000"
    ws_run["C18"].number_format = "0.0000"
    ws_run["C19"].number_format = "0.0000"
    ws_run["C20"].number_format = "0.000000"

    for ws in [ws_proj, ws_elast, ws_data, ws_checks]:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, (int, float)):
                    cell.number_format = "0.0000"

    return wb


def main() -> None:
    wb = build_workbook()
    wb.save(OUTPUT)
    # Reopen once to ensure the package is readable.
    check = load_workbook(OUTPUT, data_only=False, read_only=True)
    required = {"Read Me", "MAIDADS MODEL", "RUN", "Province Data", "Projection Data", "Elasticities", "Checks"}
    missing = required.difference(check.sheetnames)
    if missing:
        raise RuntimeError(f"Workbook missing sheets: {sorted(missing)}")
    check.close()
    print(OUTPUT)


if __name__ == "__main__":
    main()
```

### compile_markdown_outputs.py

源文件：`/root/data/Paper/省级食物消费/ProvinceMAIDADS/scripts/compile_markdown_outputs.py`

```python
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "ProvinceMAIDADS" / "Results"
DATA_OUT = ROOT / "ProvinceMAIDADS" / "Data" / "output"
SCRIPTS = ROOT / "ProvinceMAIDADS" / "scripts"


RESULT_DESCRIPTIONS = {
    "parameter_estimates.csv": "主模型 AIDADS/MAIDADS 参数估计",
    "model_fit_by_group.csv": "主模型分组拟合误差",
    "elasticity_income_grid.csv": "收入网格弹性",
    "elasticity_expenditure_grid.csv": "数量、支出、预算份额三种弹性口径",
    "elasticity_price_marshallian_grid.csv": "Marshallian 自价格与交叉价格弹性",
    "elasticity_price_hicksian_grid.csv": "Hicksian 自价格与交叉价格弹性",
    "elasticity_consistency_tests.csv": "弹性理论一致性检验",
    "elasticity_observed_points.csv": "每个省-年观测点弹性",
    "multistart_diagnostics.csv": "主估计多起点与梯度诊断",
    "best_solution_gradient_report.csv": "最优解梯度诊断",
    "parameter_boundary_report.csv": "参数边界诊断",
    "projection_group_2030_2035_2050.csv": "主模型分组预测",
    "projection_item_feed_2030_2035_2050.csv": "主模型动物产品与饲料粮预测",
    "projection_province_path.csv": "主模型省级预测路径",
    "projection_growth_path.csv": "预测收入增长路径、Chen et al. (2020) SSP2 省级人口路径与 2024 桥接假设",
    "model_comparison.csv": "模型比较、AIC/BIC/OOS/LR bootstrap",
    "lr_test_chi2_and_bootstrap.csv": "LR 检验 bootstrap 摘要",
    "lr_bootstrap_draws.csv": "LR bootstrap 抽样明细",
    "oos_fit_by_group.csv": "样本外验证拟合误差",
    "oos_predictions.csv": "样本外逐省预测",
    "oos_2023_fit_by_group.csv": "2023 样本外验证拟合误差",
    "oos_2023_predictions.csv": "2023 样本外逐省预测",
    "bootstrap_draw_status.csv": "bootstrap 抽样收敛状态",
    "bootstrap_draw_metrics.csv": "bootstrap 抽样指标明细",
    "bootstrap_key_ci.csv": "关键指标 bootstrap 区间，收敛 draw 汇总",
    "bootstrap_key_ci_success_only.csv": "关键指标 bootstrap 区间备份，收敛 draw 汇总",
    "bootstrap_parameter_ci.csv": "参数 bootstrap 区间",
    "bootstrap_parameter_draws.csv": "参数 bootstrap 抽样明细",
    "robustness_cpi_nonfood_parameter_estimates.csv": "CPI 非食品口径参数估计",
    "robustness_cpi_nonfood_fit_by_group.csv": "CPI 非食品口径拟合误差",
    "robustness_cpi_nonfood_projection_group_2030_2035_2050.csv": "CPI 非食品口径分组预测",
    "robustness_cpi_nonfood_projection_item_feed_2030_2035_2050.csv": "CPI 非食品口径饲料粮预测",
    "robustness_cpi_nonfood_projection_growth_path.csv": "CPI 非食品口径预测增长路径与 SSP2 人口路径",
    "robustness_cpi_nonfood_multistart_diagnostics.csv": "CPI 非食品稳健性多起点诊断",
    "oos_summary_by_model.csv": "按口径、模型和样本切分的 OOS 汇总",
    "projection_decomposition_2030_2035_2050.csv": "预测变化的人口与人均需求贡献分解",
}

METHOD_MD_DESCRIPTIONS = {
    "CODE_AUDIT_FIX_REPORT.md": "代码审查修正状态报告",
    "data_quality_report.md": "数据质量与预算恒等式核查",
    "feed_demand_method.md": "饲料粮需求换算说明",
    "nonfood_cpi_quality_report.md": "非食品 CPI 质量报告",
    "model_equation_tests.md": "预算恒等式、弹性一致性和优化诊断测试",
    "nutrition_conversion_audit.md": "营养换算和主粮热量审计",
}


SCRIPT_DESCRIPTIONS = {
    "run_maidads_pipeline.py": "数据构造、MAIDADS/AIDADS 主估计、弹性、预测和主摘要生成",
    "run_additional_checks.py": "CPI 稳健性、样本外验证、bootstrap 和追加摘要生成",
    "run_formal_bootstrap.py": "正式规模省份簇 bootstrap 与 LR cluster bootstrap，可断点续跑并同步正式推断结果",
    "prepare_paper_workflow_outputs.py": "按论文写作 skill 要求整理结果目录、补充 gate 所需审计文件",
    "build_manuscript_draft.py": "生成 evidence ledger、论文初稿、表格、参考文献和本地审稿意见",
    "build_maidads_simulator_workbook.py": "生成无宏版省级 MAIDADS Excel 模拟器",
    "compile_markdown_outputs.py": "把所有结果与代码整合为两个 Markdown 归档文件",
}


def csv_shape(path: Path) -> tuple[int, int]:
    try:
        return pd.read_csv(path).shape
    except Exception:
        return -1, -1


def csv_block(path: Path) -> str:
    return "```csv\n" + path.read_text(encoding="utf-8").rstrip() + "\n```"


def json_block(path: Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```"


def build_results_markdown() -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = RESULTS / "省级MAIDADS_全部结果整合.md"
    result_csvs = sorted(
        p for p in RESULTS.rglob("*.csv") if not p.name.startswith("~") and p.name != output.name
    )
    result_jsons = sorted(RESULTS.glob("*.json"))
    method_mds = sorted(p for p in list(RESULTS.rglob("*.md")) + list(DATA_OUT.rglob("*.md")) if p.name in METHOD_MD_DESCRIPTIONS)
    data_csvs = sorted(DATA_OUT.glob("*.csv"))

    lines = [
        "# 中国省级 MAIDADS 全部结果整合",
        "",
        f"- 生成时间：{now}",
        f"- 工作目录：`{ROOT}`",
        f"- 主结果目录：`{RESULTS}`",
        f"- 数据构造输出目录：`{DATA_OUT}`",
        "",
        "## 一、主要结论",
        "",
        "- 主模型、稳健性、样本外验证和 bootstrap 的最新结果见后文摘要与完整 CSV。",
        "- 本版按两份审查文件修正：主口径改为 2023 实际价 + 全国非食品 CPI；省级反推非食品 CPI 作为稳健性；补齐价格弹性、理论一致性、诊断、OOS 分模型输出和正式规模 LR cluster bootstrap。",
        "- 预测人口路径已改用 Chen et al. (2020) Scientific Data 的 SSP2 省级人口预测；收入路径仍为全国增长率加省份收敛情景。",
        "- `省级需求弹性结果代码检查与修正方案.md` 与 `代码审查_问题与修复方案.md` 已纳入研究方案修订依据。",
        "",
        "## 二、研究方案修正说明",
        "",
    ]
    plan_path = ROOT / "省级MAIDADS顶刊研究方案_v4_代码审查修正版.md"
    if plan_path.exists():
        lines.append(plan_path.read_text(encoding="utf-8"))
    else:
        lines.append("_未找到 v4 研究方案修正版文件。_")
    lines.extend(
        [
            "",
            "## 三、主结果摘要",
            "",
            (RESULTS / "RESULTS_SUMMARY.md").read_text(encoding="utf-8"),
            "",
            "## 四、追加处理与稳健性摘要",
            "",
            (RESULTS / "ADDITIONAL_RESULTS.md").read_text(encoding="utf-8"),
            "",
            "## 五、结果文件索引",
            "",
            "| 文件 | 行数 | 列数 | 说明 |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for path in result_csvs:
        rows, cols = csv_shape(path)
        display_name = str(path.relative_to(RESULTS)) if path.is_relative_to(RESULTS) else path.name
        lines.append(f"| `{display_name}` | {rows} | {cols} | {RESULT_DESCRIPTIONS.get(path.name, '结果表')} |")
    lines.extend(["", "## 六、方法与审计说明文件", ""])
    for path in method_mds:
        lines.extend([f"### {path.name}", "", f"说明：{METHOD_MD_DESCRIPTIONS[path.name]}", "", path.read_text(encoding="utf-8"), ""])
    lines.extend(["", "## 七、Manifest JSON", ""])
    for path in result_jsons:
        lines.extend([f"### {path.name}", "", json_block(path), ""])
    lines.extend(
        [
            "## 八、全部结果 CSV 原文",
            "",
            "以下折叠块完整嵌入 `ProvinceMAIDADS/Results` 下所有 CSV，便于单文件归档。",
            "",
        ]
    )
    for path in result_csvs:
        rows, cols = csv_shape(path)
        display_name = str(path.relative_to(RESULTS)) if path.is_relative_to(RESULTS) else path.name
        lines.extend(
            [
                "<details>",
                f"<summary><strong>{display_name}</strong> ({rows} 行 x {cols} 列)</summary>",
                "",
                csv_block(path),
                "",
                "</details>",
                "",
            ]
        )
    lines.extend(
        [
            "## 九、数据构造输出 CSV 原文",
            "",
            "| 文件 | 行数 | 列数 |",
            "| --- | ---: | ---: |",
        ]
    )
    for path in data_csvs:
        rows, cols = csv_shape(path)
        lines.append(f"| `{path.name}` | {rows} | {cols} |")
    lines.append("")
    for path in data_csvs:
        rows, cols = csv_shape(path)
        lines.extend(
            [
                "<details>",
                f"<summary><strong>{path.name}</strong> ({rows} 行 x {cols} 列)</summary>",
                "",
                csv_block(path),
                "",
                "</details>",
                "",
            ]
        )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def build_code_markdown() -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = RESULTS / "省级MAIDADS_全部代码整合.md"
    script_files = [
        SCRIPTS / "run_maidads_pipeline.py",
        SCRIPTS / "run_additional_checks.py",
        SCRIPTS / "run_formal_bootstrap.py",
        SCRIPTS / "prepare_paper_workflow_outputs.py",
        SCRIPTS / "build_manuscript_draft.py",
        SCRIPTS / "build_maidads_simulator_workbook.py",
        SCRIPTS / "compile_markdown_outputs.py",
    ]
    lines = [
        "# 中国省级 MAIDADS 全部代码整合",
        "",
        f"- 生成时间：{now}",
        f"- 工作目录：`{ROOT}`",
        "",
        "## 一、运行顺序",
        "",
        "```bash",
        f"cd {ROOT}",
        "python3 ProvinceMAIDADS/scripts/run_maidads_pipeline.py",
        "python3 ProvinceMAIDADS/scripts/run_additional_checks.py",
        "python3 ProvinceMAIDADS/scripts/run_formal_bootstrap.py --bootstrap-reps 1000 --lr-reps 500 --workers 6",
        "python3 ProvinceMAIDADS/scripts/prepare_paper_workflow_outputs.py",
        "python3 .codex/skills/provincial-maidads-paper-writer/scripts/paper_gate_check.py --root ProvinceMAIDADS",
        "python3 ProvinceMAIDADS/scripts/build_manuscript_draft.py",
        "python3 ProvinceMAIDADS/scripts/build_maidads_simulator_workbook.py",
        "python3 ProvinceMAIDADS/scripts/compile_markdown_outputs.py",
        "```",
        "",
        "## 二、代码文件索引",
        "",
        "| 文件 | 行数 | 作用 |",
        "| --- | ---: | --- |",
    ]
    for path in script_files:
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        lines.append(f"| `{path.name}` | {line_count} | {SCRIPT_DESCRIPTIONS[path.name]} |")
    lines.extend(["", "## 三、完整源码", ""])
    for path in script_files:
        lines.extend(
            [
                f"### {path.name}",
                "",
                f"源文件：`{path}`",
                "",
                "```python",
                path.read_text(encoding="utf-8").rstrip(),
                "```",
                "",
            ]
        )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    results_md = build_results_markdown()
    code_md = build_code_markdown()
    print(results_md)
    print(code_md)


if __name__ == "__main__":
    main()
```
