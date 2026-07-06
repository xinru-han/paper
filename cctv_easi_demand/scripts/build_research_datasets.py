#!/usr/bin/env python3
"""
Build research-ready matched datasets for the CCTV household food consumption data.

Outputs are written to ../processed by default:
- standardized CPI, COVID, wholesale-price, weather, holiday, category mapping tables
- full transaction-level enriched CSV
- processing report

The script is intentionally conservative: category nutrition files and GDP files are
auto-detected, but if absent they are reported as missing rather than inferred.
"""

from __future__ import annotations

import csv
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "processed"
OUT.mkdir(exist_ok=True)

DATE_MIN = pd.Timestamp("2020-01-01")
DATE_MAX = pd.Timestamp("2022-12-31")

MAIN_FILES = [
    ("Data_2020-2022.csv", "Data_2020-2022"),
    ("Data_补充.csv", "Data_补充"),
]

PROVINCE_FULL = {
    "北京": "北京市",
    "天津": "天津市",
    "河北": "河北省",
    "山西": "山西省",
    "内蒙古": "内蒙古自治区",
    "辽宁": "辽宁省",
    "吉林": "吉林省",
    "黑龙江": "黑龙江省",
    "上海": "上海市",
    "江苏": "江苏省",
    "浙江": "浙江省",
    "安徽": "安徽省",
    "福建": "福建省",
    "江西": "江西省",
    "山东": "山东省",
    "河南": "河南省",
    "湖北": "湖北省",
    "湖南": "湖南省",
    "广东": "广东省",
    "广西": "广西壮族自治区",
    "海南": "海南省",
    "重庆": "重庆市",
    "四川": "四川省",
    "贵州": "贵州省",
    "云南": "云南省",
    "西藏": "西藏自治区",
    "陕西": "陕西省",
    "甘肃": "甘肃省",
    "青海": "青海省",
    "宁夏": "宁夏回族自治区",
    "新疆": "新疆维吾尔自治区",
}

REGION_MAP = {
    "北京市": "东部",
    "天津市": "东部",
    "河北省": "东部",
    "上海市": "东部",
    "江苏省": "东部",
    "浙江省": "东部",
    "福建省": "东部",
    "山东省": "东部",
    "广东省": "东部",
    "海南省": "东部",
    "山西省": "中部",
    "安徽省": "中部",
    "江西省": "中部",
    "河南省": "中部",
    "湖北省": "中部",
    "湖南省": "中部",
    "内蒙古自治区": "西部",
    "广西壮族自治区": "西部",
    "重庆市": "西部",
    "四川省": "西部",
    "贵州省": "西部",
    "云南省": "西部",
    "西藏自治区": "西部",
    "陕西省": "西部",
    "甘肃省": "西部",
    "青海省": "西部",
    "宁夏回族自治区": "西部",
    "新疆维吾尔自治区": "西部",
    "辽宁省": "东北",
    "吉林省": "东北",
    "黑龙江省": "东北",
}

COASTAL = {
    "北京市",
    "天津市",
    "河北省",
    "辽宁省",
    "上海市",
    "江苏省",
    "浙江省",
    "福建省",
    "山东省",
    "广东省",
    "广西壮族自治区",
    "海南省",
}

NORTH = {
    "北京市",
    "天津市",
    "河北省",
    "山西省",
    "内蒙古自治区",
    "辽宁省",
    "吉林省",
    "黑龙江省",
    "山东省",
    "河南省",
    "陕西省",
    "甘肃省",
    "青海省",
    "宁夏回族自治区",
    "新疆维吾尔自治区",
}

INCOME_ORDER = {
    "<5000 RMB": 1,
    "5001-7000 RMB": 2,
    "7001-9000 RMB": 3,
    "9001-12000 RMB": 4,
    ">12000 RMB": 5,
}

FAMILY_SIZE_MIDPOINT = {
    "家庭人口数1-2": 1.5,
    "家庭人口数3": 3.0,
    "家庭人口数4": 4.0,
    "家庭人口数5+": 5.5,
}


def norm_province(x: str) -> str:
    s = str(x).strip().replace("\ufeff", "")
    if not s or s == "nan":
        return ""
    if s in PROVINCE_FULL.values():
        return s
    s2 = s.replace("省", "").replace("市", "").replace("自治区", "").replace("壮族", "").replace("回族", "").replace("维吾尔", "")
    return PROVINCE_FULL.get(s, PROVINCE_FULL.get(s2, s))


def clean_income(x: str) -> str:
    s = str(x).strip()
    if s == ">12000RMB":
        return ">12000 RMB"
    return s


def parse_main_date(raw: str) -> pd.Timestamp | pd.NaT:
    s = str(raw).strip()
    if not s:
        return pd.NaT
    return pd.to_datetime(s, errors="coerce")


def safe_float(x: Any) -> float | None:
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return None
    try:
        return float(s)
    except Exception:
        return None


def daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def decode_wind_csv(path: Path) -> list[list[str]]:
    with path.open("r", encoding="gb18030", newline="") as f:
        return list(csv.reader(f))


def read_cpi() -> tuple[pd.DataFrame, dict[tuple[str, int], float]]:
    path = BASE / "消费价格指数上年=100.csv"
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    fixed = [line.replace("\t,", ",").replace("\t", ",") for line in lines]
    rows = list(csv.reader(fixed))
    header = [h.strip() for h in rows[2] if h.strip()]
    records = []
    for row in rows[3:]:
        vals = [v.strip() for v in row]
        if not vals or not vals[0]:
            continue
        m = re.search(r"(\d{4})", vals[0])
        if not m:
            continue
        year = int(m.group(1))
        for prov, val in zip(header[1:], vals[1:]):
            prov = norm_province(prov)
            fv = safe_float(val)
            if prov and fv is not None:
                records.append({"province": prov, "year": year, "cpi_yoy_prev_year_100": fv})
    df = pd.DataFrame(records)
    df = df[(df["year"] >= 2020) & (df["year"] <= 2022)].copy()
    out = OUT / "cpi_province_year_2020_2022.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    mp = {(r.province, int(r.year)): float(r.cpi_yoy_prev_year_100) for r in df.itertuples(index=False)}
    return df, mp


def read_covid(main_provinces: list[str]) -> tuple[pd.DataFrame, dict[tuple[str, str], tuple[float, float]]]:
    rows = decode_wind_csv(BASE / "covid19累计值.csv")
    indicator = rows[1]
    provinces = []
    for text in indicator[1:]:
        parts = str(text).split(":")
        prov = ""
        if len(parts) >= 3:
            prov = parts[1].replace("(停止)中国", "").strip()
        provinces.append(norm_province(prov))

    data = rows[8:]
    raw_records = []
    for row in data:
        if not row:
            continue
        dt = pd.to_datetime(row[0], errors="coerce")
        if pd.isna(dt) or dt < DATE_MIN or dt > DATE_MAX:
            continue
        ds = dt.strftime("%Y-%m-%d")
        for prov, val in zip(provinces, row[1:]):
            if not prov:
                continue
            fv = safe_float(val)
            if fv is not None:
                raw_records.append({"province": prov, "date": ds, "covid_cum_confirmed": fv})

    raw = pd.DataFrame(raw_records)
    grid = pd.MultiIndex.from_product(
        [main_provinces, pd.date_range(DATE_MIN, DATE_MAX, freq="D").strftime("%Y-%m-%d")],
        names=["province", "date"],
    ).to_frame(index=False)
    df = grid.merge(raw, on=["province", "date"], how="left").sort_values(["province", "date"])
    df["covid_cum_confirmed"] = df.groupby("province")["covid_cum_confirmed"].ffill().fillna(0)
    df["covid_daily_new"] = df.groupby("province")["covid_cum_confirmed"].diff().fillna(df["covid_cum_confirmed"])
    df.loc[df["covid_daily_new"] < 0, "covid_daily_new"] = 0
    out = OUT / "covid_province_daily_2020_2022.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    mp = {
        (r.province, r.date): (float(r.covid_cum_confirmed), float(r.covid_daily_new))
        for r in df.itertuples(index=False)
    }
    return df, mp


def slug_wholesale_indicator(indicator_name: str) -> str:
    tail = str(indicator_name).replace("中国:", "")
    mapping = {
        "农产品批发价格200指数": "wholesale_agri_200",
        "菜篮子产品批发价格200指数": "wholesale_basket_200",
        "粮油产品批发价格200指数": "wholesale_grain_oil_200",
        "农产品批发价格指数:粮食": "wholesale_grain",
        "农产品批发价格指数:粮食:大米": "wholesale_rice",
        "农产品批发价格指数:粮食:面粉": "wholesale_flour",
        "农产品批发价格指数:粮食:玉米": "wholesale_corn",
        "农产品批发价格指数:粮食:大豆": "wholesale_soybean",
        "农产品批发价格指数:粮食:蔬菜": "wholesale_veg_grain_section",
        "农产品批发价格指数:粮食:马铃薯": "wholesale_potato",
        "农产品批发价格指数:油料:食用油": "wholesale_edible_oil",
        "农产品批发价格指数:油料:花生油": "wholesale_peanut_oil",
        "农产品批发价格指数:蔬菜:大白菜": "wholesale_cabbage",
        "农产品批发价格指数:蔬菜:黄瓜": "wholesale_cucumber",
        "农产品批发价格指数:蔬菜:大蒜": "wholesale_garlic",
        "农产品批发价格指数:水果": "wholesale_fruit",
        "农产品批发价格指数:水果:鸭梨": "wholesale_pear",
        "农产品批发价格指数:水果:香蕉": "wholesale_banana",
        "农产品批发价格指数:水果:柑桔": "wholesale_citrus",
        "农产品批发价格指数:水果:葡萄": "wholesale_grape",
        "农产品批发价格指数:畜禽产品": "wholesale_livestock_poultry",
        "农产品批发价格指数:畜禽产品:猪肉": "wholesale_pork",
        "农产品批发价格指数:畜禽产品:牛肉": "wholesale_beef",
        "农产品批发价格指数:畜禽产品:羊肉": "wholesale_mutton",
        "农产品批发价格指数:畜禽产品:禽肉": "wholesale_poultry",
        "农产品批发价格指数:畜禽产品:蛋类": "wholesale_eggs",
        "农产品批发价格指数:水产品": "wholesale_aquatic",
        "农产品批发价格指数:水产品:淡水产品": "wholesale_freshwater",
        "农产品批发价格指数:水产品:草鱼": "wholesale_grass_carp",
        "农产品批发价格指数:水产品:海水产品": "wholesale_marine",
        "农产品批发价格指数:水产品:带鱼": "wholesale_hairtail",
    }
    return mapping.get(tail, re.sub(r"\W+", "_", tail))


def read_wholesale() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, float]]]:
    path = BASE / "中国_农产品批发价格200指数.csv"
    if not path.exists():
        return pd.DataFrame(), pd.DataFrame(), {}
    rows = decode_wind_csv(path)
    names = rows[1][1:]
    slugs = [slug_wholesale_indicator(x) for x in names]
    long_records = []
    for row in rows[8:]:
        if not row:
            continue
        dt = pd.to_datetime(row[0], errors="coerce")
        if pd.isna(dt) or dt < DATE_MIN or dt > DATE_MAX:
            continue
        ds = dt.strftime("%Y-%m-%d")
        for slug, name, val in zip(slugs, names, row[1:]):
            fv = safe_float(val)
            if fv is not None:
                long_records.append(
                    {
                        "date": ds,
                        "indicator_slug": slug,
                        "indicator_name": name,
                        "wholesale_index_2015_100": fv,
                    }
                )
    long_df = pd.DataFrame(long_records)
    long_df.to_csv(OUT / "agri_wholesale_price_index_daily_long_2020_2022.csv", index=False, encoding="utf-8-sig")
    if long_df.empty:
        return long_df, pd.DataFrame(), {}
    wide = long_df.pivot_table(index="date", columns="indicator_slug", values="wholesale_index_2015_100", aggfunc="first").reset_index()
    wide = wide.sort_values("date")
    wide.to_csv(OUT / "agri_wholesale_price_index_daily_wide_2020_2022.csv", index=False, encoding="utf-8-sig")
    mp = {str(r["date"]): {k: float(v) for k, v in r.items() if k != "date" and pd.notna(v)} for r in wide.to_dict("records")}
    return long_df, wide, mp


def holiday_table() -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    holiday_ranges = [
        ("元旦", "2020-01-01", "2020-01-01"),
        ("春节", "2020-01-24", "2020-01-30"),
        ("清明节", "2020-04-04", "2020-04-06"),
        ("劳动节", "2020-05-01", "2020-05-05"),
        ("端午节", "2020-06-25", "2020-06-27"),
        ("国庆节/中秋节", "2020-10-01", "2020-10-08"),
        ("元旦", "2021-01-01", "2021-01-03"),
        ("春节", "2021-02-11", "2021-02-17"),
        ("清明节", "2021-04-03", "2021-04-05"),
        ("劳动节", "2021-05-01", "2021-05-05"),
        ("端午节", "2021-06-12", "2021-06-14"),
        ("中秋节", "2021-09-19", "2021-09-21"),
        ("国庆节", "2021-10-01", "2021-10-07"),
        ("元旦", "2022-01-01", "2022-01-03"),
        ("春节", "2022-01-31", "2022-02-06"),
        ("清明节", "2022-04-03", "2022-04-05"),
        ("劳动节", "2022-04-30", "2022-05-04"),
        ("端午节", "2022-06-03", "2022-06-05"),
        ("中秋节", "2022-09-10", "2022-09-12"),
        ("国庆节", "2022-10-01", "2022-10-07"),
    ]
    adjusted = {
        "2020-01-19",
        "2020-02-01",
        "2020-04-26",
        "2020-05-09",
        "2020-06-28",
        "2020-09-27",
        "2020-10-10",
        "2021-02-07",
        "2021-02-20",
        "2021-04-25",
        "2021-05-08",
        "2021-09-18",
        "2021-09-26",
        "2021-10-09",
        "2022-01-29",
        "2022-01-30",
        "2022-04-02",
        "2022-04-24",
        "2022-05-07",
        "2022-10-08",
        "2022-10-09",
    }
    by_day: dict[str, list[str]] = defaultdict(list)
    start_by_name: dict[tuple[int, str], date] = {}
    for name, start, end in holiday_ranges:
        sdt = pd.Timestamp(start).date()
        edt = pd.Timestamp(end).date()
        start_by_name[(sdt.year, name.split("/")[0])] = sdt
        if name == "国庆节/中秋节":
            start_by_name[(2020, "国庆节")] = sdt
            start_by_name[(2020, "中秋节")] = sdt
        for d in daterange(sdt, edt):
            by_day[d.isoformat()].append(name)

    rows = []
    for d in daterange(DATE_MIN.date(), DATE_MAX.date()):
        ds = d.isoformat()
        names = by_day.get(ds, [])
        weekday = d.weekday()
        is_weekend = weekday >= 5

        def rel_to(name: str) -> int | None:
            s = start_by_name.get((d.year, name))
            if s is None:
                return None
            return (d - s).days

        spring_rel = rel_to("春节")
        mid_rel = rel_to("中秋节")
        national_rel = rel_to("国庆节")
        rows.append(
            {
                "date": ds,
                "year": d.year,
                "holiday_name": ";".join(names),
                "holiday_flag": int(bool(names)),
                "adjusted_workday_flag": int(ds in adjusted),
                "calendar_weekday": weekday + 1,
                "calendar_is_weekend": int(is_weekend),
                "spring_festival_rel_day": spring_rel if spring_rel is not None else "",
                "spring_festival_window_7": int(spring_rel is not None and -7 <= spring_rel <= 7),
                "spring_festival_window_14": int(spring_rel is not None and -14 <= spring_rel <= 14),
                "mid_autumn_rel_day": mid_rel if mid_rel is not None else "",
                "mid_autumn_window_7": int(mid_rel is not None and -7 <= mid_rel <= 7),
                "national_day_rel_day": national_rel if national_rel is not None else "",
                "national_day_window_7": int(national_rel is not None and -7 <= national_rel <= 7),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "calendar_holiday_2020_2022.csv", index=False, encoding="utf-8-sig")
    return df, {r["date"]: r for r in rows}


def read_weather(main_provinces: list[str]) -> tuple[pd.DataFrame, dict[tuple[str, str], dict[str, float]]]:
    temp_path = BASE / "气象数据/1973～2024 年气温面板数据/1973年1月1日~2024年12月31日各省份气温日度数据.xlsx"
    precip_path = BASE / "气象数据/1973～2024 年降水量面板数据/1973年1月1日~2024年12月31日各省份平均降水量日度数据.xlsx"
    if not temp_path.exists() or not precip_path.exists():
        return pd.DataFrame(), {}
    temp = pd.read_excel(temp_path, sheet_name=0, usecols=["省", "省代码", "日期", "平均气温", "最高气温", "最低气温"])
    temp["province"] = temp["省"].map(norm_province)
    temp["date"] = pd.to_datetime(temp["日期"], errors="coerce")
    temp = temp[(temp["date"] >= DATE_MIN) & (temp["date"] <= DATE_MAX) & temp["province"].isin(main_provinces)].copy()
    temp["date"] = temp["date"].dt.strftime("%Y-%m-%d")
    temp = temp.rename(columns={"省代码": "province_code", "平均气温": "temp_avg_c", "最高气温": "temp_max_c", "最低气温": "temp_min_c"})
    temp = temp[["province", "province_code", "date", "temp_avg_c", "temp_max_c", "temp_min_c"]]

    precip = pd.read_excel(precip_path, sheet_name=0, usecols=["省", "省代码", "日期", "降水量"])
    precip["province"] = precip["省"].map(norm_province)
    precip["date"] = pd.to_datetime(precip["日期"], errors="coerce")
    precip = precip[(precip["date"] >= DATE_MIN) & (precip["date"] <= DATE_MAX) & precip["province"].isin(main_provinces)].copy()
    precip["date"] = precip["date"].dt.strftime("%Y-%m-%d")
    precip = precip.rename(columns={"降水量": "precipitation_mm"})
    precip = precip[["province", "date", "precipitation_mm"]]

    df = temp.merge(precip, on=["province", "date"], how="outer").sort_values(["province", "date"])
    df.to_csv(OUT / "weather_province_daily_2020_2022.csv", index=False, encoding="utf-8-sig")
    df["year_month"] = df["date"].str.slice(0, 7)
    monthly = (
        df.groupby(["province", "year_month"], as_index=False)
        .agg(
            temp_avg_c_mean=("temp_avg_c", "mean"),
            temp_max_c_mean=("temp_max_c", "mean"),
            temp_min_c_mean=("temp_min_c", "mean"),
            precipitation_mm_sum=("precipitation_mm", "sum"),
            precipitation_mm_mean=("precipitation_mm", "mean"),
            weather_days=("date", "count"),
        )
        .sort_values(["province", "year_month"])
    )
    monthly.to_csv(OUT / "weather_province_month_2020_2022.csv", index=False, encoding="utf-8-sig")
    mp = {}
    for r in df.itertuples(index=False):
        mp[(r.province, r.date)] = {
            "temp_avg_c": safe_float(r.temp_avg_c),
            "temp_max_c": safe_float(r.temp_max_c),
            "temp_min_c": safe_float(r.temp_min_c),
            "precipitation_mm": safe_float(r.precipitation_mm),
        }
    return df, mp


def lookup_user_value(df: pd.DataFrame, footprint: str, kind: str, value: str) -> float | None:
    if footprint == "CF":
        cols = {
            "item": ("Food commodity ITEM", "Carbon Footprint kg CO2eq/kg or l of food ITEM"),
            "typology": ("Food commodity TYPOLOGY", "Carbon Footprint g CO2eq/g o cc of food TYPOLOGY"),
            "subtypology": ("Food commodity sub-TYPOLOGY", "Carbon Footprint g CO2eq/g o cc of food sub-TYPOLOGY"),
        }
    else:
        cols = {
            "item": ("Food commodity ITEM", "Water Footprint liters water/kg o liter of food ITEM"),
            "typology": ("Food commodity TYPOLOGY", "Water Footprint cc water/g o cc of food TYPOLOGY"),
            "subtypology": ("Food commodity sub-TYPOLOGY", "Water Footprint cc water/g o cc of food sub-TYPOLOGY"),
        }
    key_col, val_col = cols[kind]
    sub = df[df[key_col].astype(str).str.upper().eq(value.upper())]
    vals = pd.to_numeric(sub[val_col], errors="coerce").dropna().unique()
    if len(vals):
        return float(vals[0])
    return None


@dataclass
class CategoryMap:
    category: str
    category_group: str
    cf_kind: str
    cf_key: str
    wf_kind: str
    wf_key: str
    match_confidence: str
    notes: str
    is_fresh: int
    is_storable: int
    is_processed: int
    is_animal_protein: int
    is_staple: int
    is_dairy: int
    is_premium_proxy: int
    wholesale_slug: str


def build_category_mapping() -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    xlsx = BASE / "SuEatableLife_Food_Fooprint_database.xlsx"
    cf_df = pd.read_excel(xlsx, sheet_name="SEL CF for users") if xlsx.exists() else pd.DataFrame()
    wf_df = pd.read_excel(xlsx, sheet_name="SEL WF for users") if xlsx.exists() else pd.DataFrame()

    maps = [
        CategoryMap("蔬菜", "蔬果", "typology", "VEGETABLES OPENFIELD", "typology", "VEGETABLES", "medium", "以露地蔬菜/蔬菜大类代理混合蔬菜。", 1, 0, 0, 0, 0, 0, 0, "wholesale_veg_grain_section"),
        CategoryMap("水果", "蔬果", "typology", "FRUIT OPENFIELD", "typology", "FRUIT", "medium", "以露地水果/水果大类代理混合水果。", 1, 0, 0, 0, 0, 0, 1, "wholesale_fruit"),
        CategoryMap("猪肉", "肉禽水产", "item", "PORK BONE FREE MEAT*", "item", "PORK BONE FREE MEAT*", "medium", "用去骨猪肉代理。", 1, 0, 0, 1, 0, 0, 0, "wholesale_pork"),
        CategoryMap("海鲜类", "肉禽水产", "typology", "FISH", "typology", "FISH", "low", "海鲜类混合鱼类和贝壳类；暂用鱼类大类代理。", 1, 0, 0, 1, 0, 0, 1, "wholesale_aquatic"),
        CategoryMap("禽类", "肉禽水产", "typology", "POULTRY MEAT WITH BONE", "item", "CHICKEN MEAT WITH BONE*", "medium", "用带骨禽肉/鸡肉代理。", 1, 0, 0, 1, 0, 0, 0, "wholesale_poultry"),
        CategoryMap("常温牛奶", "乳制品", "item", "COW MILK", "item", "COW MILK", "high", "用牛奶代理。", 0, 1, 1, 1, 0, 1, 0, "wholesale_basket_200"),
        CategoryMap("新鲜牛奶", "乳制品", "item", "COW MILK", "item", "COW MILK", "high", "用牛奶代理。", 1, 0, 1, 1, 0, 1, 0, "wholesale_basket_200"),
        CategoryMap("新鲜酸奶", "乳制品", "typology", "YOGURT", "typology", "YOGURT", "medium", "用酸奶大类代理。", 1, 0, 1, 1, 0, 1, 1, "wholesale_basket_200"),
        CategoryMap("常温酸奶", "乳制品", "typology", "YOGURT", "typology", "YOGURT", "medium", "用酸奶大类代理。", 0, 1, 1, 1, 0, 1, 1, "wholesale_basket_200"),
        CategoryMap("坚果", "油脂坚果", "typology", "NUTS", "typology", "NUTS SHELLED", "medium", "用坚果/去壳坚果代理。", 0, 1, 1, 0, 0, 0, 1, "wholesale_basket_200"),
        CategoryMap("食用油", "油脂坚果", "typology", "OIL", "typology", "OIL", "medium", "用食用油大类代理。", 0, 1, 1, 0, 0, 0, 0, "wholesale_edible_oil"),
        CategoryMap("牛肉", "肉禽水产", "typology", "BEEF BONE FREE MEAT*", "typology", "BEEF BONE FREE MEAT*", "medium", "用去骨牛肉代理。", 1, 0, 0, 1, 0, 0, 1, "wholesale_beef"),
        CategoryMap("方便面", "加工食品", "item", "PASTA*", "item", "PASTA*", "low", "SuEatableLife 未见方便面；暂用意面/面制品代理，需谨慎。", 0, 1, 1, 0, 1, 0, 0, "wholesale_grain_oil_200"),
        CategoryMap("大米", "主粮", "item", "RICE*", "item", "RICE", "high", "用大米代理。", 0, 1, 0, 0, 1, 0, 0, "wholesale_rice"),
        CategoryMap("挂面", "主粮", "item", "PASTA*", "item", "PASTA*", "medium", "用面条/意面类代理。", 0, 1, 1, 0, 1, 0, 0, "wholesale_flour"),
        CategoryMap("面粉", "主粮", "item", "WHEAT PLAIN FLOUR", "item", "WHEAT FLOUR", "high", "用小麦粉代理。", 0, 1, 0, 0, 1, 0, 0, "wholesale_flour"),
        CategoryMap("羊肉", "肉禽水产", "item", "LAMB BONE FREE MEAT*", "item", "LAMB BONE FREE MEAT*", "medium", "用去骨羔羊肉代理。", 1, 0, 0, 1, 0, 0, 1, "wholesale_mutton"),
        CategoryMap("黄油", "乳制品", "item", "BUTTER*", "item", "BUTTER*", "high", "用黄油代理。", 0, 1, 1, 1, 0, 1, 1, "wholesale_basket_200"),
        CategoryMap("成人奶粉", "乳制品", "typology", "MILK", "item", "MILK POWDER", "low", "水足迹用奶粉；碳足迹库中未见奶粉，暂用牛奶大类低置信代理。", 0, 1, 1, 1, 0, 1, 1, "wholesale_basket_200"),
        CategoryMap("奶酪", "乳制品", "item", "CHEESE", "typology", "CHEESE", "high", "用奶酪代理。", 0, 1, 1, 1, 0, 1, 1, "wholesale_basket_200"),
        CategoryMap("其他肉类", "肉禽水产", "typology", "POULTRY BONE FREE MEAT", "typology", "POULTRY BONE FREE MEAT", "low", "品类含义不明；暂用禽肉大类代理，需敏感性检验。", 1, 0, 0, 1, 0, 0, 0, "wholesale_livestock_poultry"),
    ]

    rows = []
    for m in maps:
        cf = lookup_user_value(cf_df, "CF", m.cf_kind, m.cf_key) if not cf_df.empty else None
        wf = lookup_user_value(wf_df, "WF", m.wf_kind, m.wf_key) if not wf_df.empty else None
        rows.append(
            {
                **m.__dict__,
                "carbon_kgco2e_per_kg_or_l": cf,
                "water_l_per_kg_or_l": wf,
                "footprint_source": "SuEatableLife_Food_Fooprint_database.xlsx; Petersson et al. Scientific Data 2021",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "category_mapping_footprint_flags.csv", index=False, encoding="utf-8-sig")
    return df, {r["category"]: r for r in df.to_dict("records")}


def detect_optional_files() -> dict[str, list[str]]:
    nutrient_files = []
    gdp_files = []
    for p in BASE.rglob("*"):
        if p.name.startswith("._") or not p.is_file():
            continue
        name = p.name.lower()
        path = str(p)
        if "nutr" in name or "营养" in p.name:
            nutrient_files.append(path)
        if "gdp" in name or "生产总值" in p.name or "人均gdp" in name:
            gdp_files.append(path)
    return {"nutrient_files": nutrient_files, "gdp_files": gdp_files}


def collect_main_provinces_categories() -> tuple[list[str], list[str]]:
    provinces = set()
    categories = set()
    for filename, _source in MAIN_FILES:
        with (BASE / filename).open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            # handle Family_size typo but only need Province/Category here
            for row in reader:
                provinces.add(norm_province(row.get("Province", "")))
                categories.add(str(row.get("Category", "")).strip())
    return sorted(provinces), sorted(categories)


def write_province_covariates(
    main_provinces: list[str],
    cpi_map: dict[tuple[str, int], float],
    covid_map: dict[tuple[str, str], tuple[float, float]],
    wholesale_map: dict[str, dict[str, float]],
    holiday_map: dict[str, dict[str, Any]],
    weather_map: dict[tuple[str, str], dict[str, float]],
) -> None:
    rows = []
    for prov in main_provinces:
        for d in pd.date_range(DATE_MIN, DATE_MAX, freq="D"):
            ds = d.strftime("%Y-%m-%d")
            covid = covid_map.get((prov, ds), (None, None))
            wh = wholesale_map.get(ds, {})
            hol = holiday_map.get(ds, {})
            weather = weather_map.get((prov, ds), {})
            rows.append(
                {
                    "province": prov,
                    "date": ds,
                    "year": d.year,
                    "year_month": d.strftime("%Y-%m"),
                    "cpi_yoy_prev_year_100": cpi_map.get((prov, d.year)),
                    "covid_cum_confirmed": covid[0],
                    "covid_daily_new": covid[1],
                    "holiday_flag": hol.get("holiday_flag", 0),
                    "holiday_name": hol.get("holiday_name", ""),
                    "adjusted_workday_flag": hol.get("adjusted_workday_flag", 0),
                    "spring_festival_window_14": hol.get("spring_festival_window_14", 0),
                    "national_day_window_7": hol.get("national_day_window_7", 0),
                    "mid_autumn_window_7": hol.get("mid_autumn_window_7", 0),
                    "temp_avg_c": weather.get("temp_avg_c"),
                    "temp_max_c": weather.get("temp_max_c"),
                    "temp_min_c": weather.get("temp_min_c"),
                    "precipitation_mm": weather.get("precipitation_mm"),
                    "wholesale_agri_200": wh.get("wholesale_agri_200"),
                    "wholesale_basket_200": wh.get("wholesale_basket_200"),
                    "wholesale_grain_oil_200": wh.get("wholesale_grain_oil_200"),
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "province_date_covariates_2020_2022.csv", index=False, encoding="utf-8-sig")
    monthly = (
        df.groupby(["province", "year_month"], as_index=False)
        .agg(
            cpi_yoy_prev_year_100=("cpi_yoy_prev_year_100", "mean"),
            covid_cum_confirmed_end=("covid_cum_confirmed", "max"),
            covid_daily_new_sum=("covid_daily_new", "sum"),
            holiday_days=("holiday_flag", "sum"),
            adjusted_workdays=("adjusted_workday_flag", "sum"),
            temp_avg_c_mean=("temp_avg_c", "mean"),
            temp_max_c_mean=("temp_max_c", "mean"),
            temp_min_c_mean=("temp_min_c", "mean"),
            precipitation_mm_sum=("precipitation_mm", "sum"),
            wholesale_agri_200_mean=("wholesale_agri_200", "mean"),
            wholesale_basket_200_mean=("wholesale_basket_200", "mean"),
            wholesale_grain_oil_200_mean=("wholesale_grain_oil_200", "mean"),
        )
        .sort_values(["province", "year_month"])
    )
    monthly.to_csv(OUT / "province_month_covariates_2020_2022.csv", index=False, encoding="utf-8-sig")


def fmt_or_blank(x: Any) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    if isinstance(x, float):
        if math.isfinite(x):
            return f"{x:.10g}"
        return ""
    return str(x)


def enrich_transactions(
    cpi_map: dict[tuple[str, int], float],
    covid_map: dict[tuple[str, str], tuple[float, float]],
    wholesale_map: dict[str, dict[str, float]],
    holiday_map: dict[str, dict[str, Any]],
    weather_map: dict[tuple[str, str], dict[str, float]],
    category_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    out_path = OUT / "Data_merged_enriched.csv"
    base_cols = ["ID", "Province", "Family_Type", "Family_Size", "Family_Income", "Date", "Category", "Spend", "Volume", "Price"]
    extra_cols = [
        "source_file",
        "date_clean",
        "year",
        "month",
        "year_month",
        "week",
        "weekday",
        "is_weekend",
        "holiday_name",
        "holiday_flag",
        "adjusted_workday_flag",
        "spring_festival_window_14",
        "mid_autumn_window_7",
        "national_day_window_7",
        "income_band_clean",
        "income_rank",
        "family_size_midpoint",
        "per_capita_spend_proxy",
        "price_calc",
        "price_missing_flag",
        "volume_zero_flag",
        "spend_zero_flag",
        "category_group",
        "is_fresh",
        "is_storable",
        "is_processed",
        "is_animal_protein",
        "is_staple",
        "is_dairy",
        "is_premium_proxy",
        "region",
        "coastal_dummy",
        "north_south",
        "cpi_yoy_prev_year_100",
        "covid_cum_confirmed",
        "covid_daily_new",
        "temp_avg_c",
        "temp_max_c",
        "temp_min_c",
        "precipitation_mm",
        "wholesale_agri_200",
        "wholesale_basket_200",
        "wholesale_grain_oil_200",
        "category_wholesale_index",
        "category_wholesale_slug",
        "carbon_kgco2e_per_kg_or_l",
        "water_l_per_kg_or_l",
        "estimated_carbon_kgco2e",
        "estimated_water_l",
        "footprint_match_confidence",
        "footprint_match_notes",
    ]
    total = 0
    unmatched_categories = Counter()
    date_parse_fail = 0
    with out_path.open("w", encoding="utf-8-sig", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=base_cols + extra_cols)
        writer.writeheader()
        for filename, source in MAIN_FILES:
            with (BASE / filename).open("r", encoding="utf-8-sig", newline="") as fin:
                reader = csv.DictReader(fin)
                for raw in reader:
                    row = {}
                    for c in base_cols:
                        if c == "Family_Size":
                            row[c] = raw.get("Family_Size", raw.get("Family_size", ""))
                        else:
                            row[c] = raw.get(c, "")

                    prov = norm_province(row["Province"])
                    cat = str(row["Category"]).strip()
                    dt = parse_main_date(row["Date"])
                    if pd.isna(dt):
                        date_parse_fail += 1
                        ds = ""
                        year = month = week = weekday = ""
                        ym = ""
                    else:
                        ds = dt.strftime("%Y-%m-%d")
                        year = int(dt.year)
                        month = int(dt.month)
                        week = int(dt.isocalendar().week)
                        weekday = int(dt.weekday() + 1)
                        ym = dt.strftime("%Y-%m")

                    spend = safe_float(row["Spend"])
                    vol = safe_float(row["Volume"])
                    price = safe_float(row["Price"])
                    price_calc = (spend / vol) if spend is not None and vol not in (None, 0) else None
                    income_clean = clean_income(row["Family_Income"])
                    fs_mid = FAMILY_SIZE_MIDPOINT.get(row["Family_Size"])
                    per_capita = (spend / fs_mid) if spend is not None and fs_mid else None
                    hol = holiday_map.get(ds, {})
                    covid = covid_map.get((prov, ds), (None, None))
                    wh = wholesale_map.get(ds, {})
                    weather = weather_map.get((prov, ds), {})
                    catinfo = category_map.get(cat)
                    if not catinfo:
                        unmatched_categories[cat] += 1
                        catinfo = {}

                    carbon_factor = safe_float(catinfo.get("carbon_kgco2e_per_kg_or_l"))
                    water_factor = safe_float(catinfo.get("water_l_per_kg_or_l"))
                    est_carbon = vol * carbon_factor if vol is not None and carbon_factor is not None else None
                    est_water = vol * water_factor if vol is not None and water_factor is not None else None
                    wholesale_slug = catinfo.get("wholesale_slug", "")
                    extra = {
                        "source_file": source,
                        "date_clean": ds,
                        "year": year,
                        "month": month,
                        "year_month": ym,
                        "week": week,
                        "weekday": weekday,
                        "is_weekend": int(weekday in (6, 7)) if weekday != "" else "",
                        "holiday_name": hol.get("holiday_name", ""),
                        "holiday_flag": hol.get("holiday_flag", ""),
                        "adjusted_workday_flag": hol.get("adjusted_workday_flag", ""),
                        "spring_festival_window_14": hol.get("spring_festival_window_14", ""),
                        "mid_autumn_window_7": hol.get("mid_autumn_window_7", ""),
                        "national_day_window_7": hol.get("national_day_window_7", ""),
                        "income_band_clean": income_clean,
                        "income_rank": INCOME_ORDER.get(income_clean, ""),
                        "family_size_midpoint": fs_mid,
                        "per_capita_spend_proxy": per_capita,
                        "price_calc": price_calc,
                        "price_missing_flag": int(price is None),
                        "volume_zero_flag": int(vol == 0) if vol is not None else "",
                        "spend_zero_flag": int(spend == 0) if spend is not None else "",
                        "category_group": catinfo.get("category_group", ""),
                        "is_fresh": catinfo.get("is_fresh", ""),
                        "is_storable": catinfo.get("is_storable", ""),
                        "is_processed": catinfo.get("is_processed", ""),
                        "is_animal_protein": catinfo.get("is_animal_protein", ""),
                        "is_staple": catinfo.get("is_staple", ""),
                        "is_dairy": catinfo.get("is_dairy", ""),
                        "is_premium_proxy": catinfo.get("is_premium_proxy", ""),
                        "region": REGION_MAP.get(prov, ""),
                        "coastal_dummy": int(prov in COASTAL) if prov else "",
                        "north_south": "北方" if prov in NORTH else ("南方" if prov else ""),
                        "cpi_yoy_prev_year_100": cpi_map.get((prov, year)) if year != "" else "",
                        "covid_cum_confirmed": covid[0],
                        "covid_daily_new": covid[1],
                        "temp_avg_c": weather.get("temp_avg_c"),
                        "temp_max_c": weather.get("temp_max_c"),
                        "temp_min_c": weather.get("temp_min_c"),
                        "precipitation_mm": weather.get("precipitation_mm"),
                        "wholesale_agri_200": wh.get("wholesale_agri_200"),
                        "wholesale_basket_200": wh.get("wholesale_basket_200"),
                        "wholesale_grain_oil_200": wh.get("wholesale_grain_oil_200"),
                        "category_wholesale_index": wh.get(wholesale_slug) if wholesale_slug else "",
                        "category_wholesale_slug": wholesale_slug,
                        "carbon_kgco2e_per_kg_or_l": carbon_factor,
                        "water_l_per_kg_or_l": water_factor,
                        "estimated_carbon_kgco2e": est_carbon,
                        "estimated_water_l": est_water,
                        "footprint_match_confidence": catinfo.get("match_confidence", ""),
                        "footprint_match_notes": catinfo.get("notes", ""),
                    }
                    out = {**row, **{k: fmt_or_blank(v) for k, v in extra.items()}}
                    writer.writerow(out)
                    total += 1
                    if total % 1_000_000 == 0:
                        print(f"enriched {total:,} rows", flush=True)
    return {
        "enriched_rows": total,
        "date_parse_fail": date_parse_fail,
        "unmatched_categories": dict(unmatched_categories),
        "enriched_file": str(out_path),
        "enriched_size_bytes": out_path.stat().st_size,
    }


def enrich_transactions_fast() -> dict[str, Any]:
    """Vectorized chunk implementation for the full transaction-level table."""
    out_path = OUT / "Data_merged_enriched.csv"
    if out_path.exists():
        out_path.unlink()

    cov = pd.read_csv(OUT / "province_date_covariates_2020_2022.csv", encoding="utf-8-sig")
    cov = cov.rename(columns={"province": "Province", "date": "date_clean"})
    cov = cov.drop(columns=[c for c in ["year", "year_month"] if c in cov.columns])

    cat = pd.read_csv(OUT / "category_mapping_footprint_flags.csv", encoding="utf-8-sig")
    cat = cat.rename(columns={"category": "Category"})
    cat_keep = [
        "Category",
        "category_group",
        "is_fresh",
        "is_storable",
        "is_processed",
        "is_animal_protein",
        "is_staple",
        "is_dairy",
        "is_premium_proxy",
        "wholesale_slug",
        "carbon_kgco2e_per_kg_or_l",
        "water_l_per_kg_or_l",
        "match_confidence",
        "notes",
    ]
    cat = cat[cat_keep].copy()

    wholesale_long_path = OUT / "agri_wholesale_price_index_daily_long_2020_2022.csv"
    if wholesale_long_path.exists():
        wh = pd.read_csv(wholesale_long_path, encoding="utf-8-sig")
        cat_slug = cat[["Category", "wholesale_slug"]].dropna()
        cat_wh = cat_slug.merge(wh, left_on="wholesale_slug", right_on="indicator_slug", how="left")
        cat_wh = cat_wh.rename(
            columns={
                "date": "date_clean",
                "wholesale_index_2015_100": "category_wholesale_index",
            }
        )
        cat_wh = cat_wh[["Category", "date_clean", "category_wholesale_index"]]
    else:
        cat_wh = pd.DataFrame(columns=["Category", "date_clean", "category_wholesale_index"])

    base_cols = ["ID", "Province", "Family_Type", "Family_Size", "Family_Income", "Date", "Category", "Spend", "Volume", "Price"]
    out_cols = base_cols + [
        "source_file",
        "date_clean",
        "year",
        "month",
        "year_month",
        "week",
        "weekday",
        "is_weekend",
        "holiday_name",
        "holiday_flag",
        "adjusted_workday_flag",
        "spring_festival_window_14",
        "mid_autumn_window_7",
        "national_day_window_7",
        "income_band_clean",
        "income_rank",
        "family_size_midpoint",
        "per_capita_spend_proxy",
        "price_calc",
        "price_missing_flag",
        "volume_zero_flag",
        "spend_zero_flag",
        "category_group",
        "is_fresh",
        "is_storable",
        "is_processed",
        "is_animal_protein",
        "is_staple",
        "is_dairy",
        "is_premium_proxy",
        "region",
        "coastal_dummy",
        "north_south",
        "cpi_yoy_prev_year_100",
        "covid_cum_confirmed",
        "covid_daily_new",
        "temp_avg_c",
        "temp_max_c",
        "temp_min_c",
        "precipitation_mm",
        "wholesale_agri_200",
        "wholesale_basket_200",
        "wholesale_grain_oil_200",
        "category_wholesale_index",
        "category_wholesale_slug",
        "carbon_kgco2e_per_kg_or_l",
        "water_l_per_kg_or_l",
        "estimated_carbon_kgco2e",
        "estimated_water_l",
        "footprint_match_confidence",
        "footprint_match_notes",
    ]

    total = 0
    date_parse_fail = 0
    unmatched_categories = Counter()
    first = True
    chunksize = 500_000

    for filename, source in MAIN_FILES:
        path = BASE / filename
        for chunk in pd.read_csv(path, encoding="utf-8-sig", dtype=str, chunksize=chunksize):
            if "Family_size" in chunk.columns and "Family_Size" not in chunk.columns:
                chunk = chunk.rename(columns={"Family_size": "Family_Size"})
            for col in base_cols:
                if col not in chunk.columns:
                    chunk[col] = ""
            chunk = chunk[base_cols].copy()
            chunk["source_file"] = source
            chunk["Province"] = chunk["Province"].map(norm_province)

            dt = pd.to_datetime(chunk["Date"], errors="coerce")
            date_parse_fail += int(dt.isna().sum())
            chunk["date_clean"] = dt.dt.strftime("%Y-%m-%d")
            chunk["year"] = dt.dt.year
            chunk["month"] = dt.dt.month
            chunk["year_month"] = dt.dt.strftime("%Y-%m")
            chunk["week"] = dt.dt.isocalendar().week.astype("float")
            chunk["weekday"] = dt.dt.weekday + 1
            chunk["is_weekend"] = chunk["weekday"].isin([6, 7]).astype("Int64")

            chunk["income_band_clean"] = chunk["Family_Income"].map(clean_income)
            chunk["income_rank"] = chunk["income_band_clean"].map(INCOME_ORDER)
            chunk["family_size_midpoint"] = chunk["Family_Size"].map(FAMILY_SIZE_MIDPOINT)

            spend = pd.to_numeric(chunk["Spend"], errors="coerce")
            volume = pd.to_numeric(chunk["Volume"], errors="coerce")
            price = pd.to_numeric(chunk["Price"], errors="coerce")
            chunk["per_capita_spend_proxy"] = spend / chunk["family_size_midpoint"]
            chunk["price_calc"] = spend.where(volume > 0) / volume.where(volume > 0)
            chunk["price_missing_flag"] = price.isna().astype("Int64")
            chunk["volume_zero_flag"] = (volume == 0).astype("Int64")
            chunk["spend_zero_flag"] = (spend == 0).astype("Int64")

            chunk["region"] = chunk["Province"].map(REGION_MAP)
            chunk["coastal_dummy"] = chunk["Province"].isin(COASTAL).astype("Int64")
            chunk["north_south"] = chunk["Province"].map(lambda x: "北方" if x in NORTH else ("南方" if isinstance(x, str) and x else ""))

            before_cat = len(chunk)
            chunk = chunk.merge(cov, on=["Province", "date_clean"], how="left")
            chunk = chunk.merge(cat, on="Category", how="left")
            no_cat = chunk["category_group"].isna()
            if no_cat.any():
                unmatched_categories.update(chunk.loc[no_cat, "Category"].fillna("").tolist())
            chunk = chunk.merge(cat_wh, on=["Category", "date_clean"], how="left")

            chunk["category_wholesale_slug"] = chunk["wholesale_slug"]
            volume_after_merge = pd.to_numeric(chunk["Volume"], errors="coerce")
            chunk["estimated_carbon_kgco2e"] = volume_after_merge * pd.to_numeric(
                chunk["carbon_kgco2e_per_kg_or_l"], errors="coerce"
            )
            chunk["estimated_water_l"] = volume_after_merge * pd.to_numeric(
                chunk["water_l_per_kg_or_l"], errors="coerce"
            )
            chunk["footprint_match_confidence"] = chunk["match_confidence"]
            chunk["footprint_match_notes"] = chunk["notes"]

            # Avoid row multiplication if a future source accidentally duplicates merge keys.
            if len(chunk) != before_cat:
                raise RuntimeError(f"Unexpected row multiplication while enriching {filename}: {before_cat} -> {len(chunk)}")

            final = chunk.reindex(columns=out_cols)
            final.to_csv(
                out_path,
                index=False,
                mode="w" if first else "a",
                header=first,
                encoding="utf-8-sig" if first else "utf-8",
            )
            first = False
            total += len(final)
            print(f"enriched {total:,} rows", flush=True)

    return {
        "enriched_rows": total,
        "date_parse_fail": date_parse_fail,
        "unmatched_categories": dict(unmatched_categories),
        "enriched_file": str(out_path),
        "enriched_size_bytes": out_path.stat().st_size,
    }


def write_report(stats: dict[str, Any], optional: dict[str, list[str]], categories: list[str]) -> None:
    lines = []
    lines.append("# 数据匹配处理报告")
    lines.append("")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 已生成文件")
    lines.append("")
    outputs = [
        "category_mapping_footprint_flags.csv",
        "calendar_holiday_2020_2022.csv",
        "cpi_province_year_2020_2022.csv",
        "covid_province_daily_2020_2022.csv",
        "agri_wholesale_price_index_daily_long_2020_2022.csv",
        "agri_wholesale_price_index_daily_wide_2020_2022.csv",
        "weather_province_daily_2020_2022.csv",
        "weather_province_month_2020_2022.csv",
        "province_date_covariates_2020_2022.csv",
        "province_month_covariates_2020_2022.csv",
        "Data_merged_enriched.csv",
    ]
    for name in outputs:
        p = OUT / name
        if p.exists():
            size = p.stat().st_size / (1024 * 1024)
            lines.append(f"- `{name}`：{size:.1f} MB")
    lines.append("")
    lines.append("## 全量交易增强表")
    lines.append("")
    lines.append(f"- 行数：{stats.get('enriched_rows', 0):,}")
    lines.append(f"- 日期解析失败：{stats.get('date_parse_fail', 0):,}")
    lines.append(f"- 文件大小：{stats.get('enriched_size_bytes', 0) / (1024**3):.2f} GB")
    lines.append("")
    lines.append("## 已匹配变量")
    lines.append("")
    lines.append("- 时间派生：日期、年、月、年月、ISO 周、星期、周末。")
    lines.append("- 节假日：2020-2022 年国务院节假日、调休工作日、春节/中秋/国庆窗口。")
    lines.append("- 省级 CPI：`消费价格指数上年=100.csv`，按省份-年份匹配。")
    lines.append("- COVID：`covid19累计值.csv`，按省份-日期匹配累计确诊和当日新增。")
    lines.append("- 农产品批发价格：`中国_农产品批发价格200指数.csv`，按日期匹配总指数、菜篮子指数、粮油指数，并按食品品类匹配可用的对应子指数。")
    lines.append("- 气象：省份日度平均/最高/最低气温、平均降水量，按省份-日期匹配。")
    lines.append("- 碳/水足迹：按 21 个食品品类映射 SuEatableLife 数据库中的 item/typology/sub-typology 值。")
    lines.append("- 地区重编码：东中西东北、沿海、南北。")
    lines.append("- 家庭与交易派生：收入清洗、收入等级、家庭规模中点、人均消费代理、`Spend / Volume` 单位价值、零值/缺失标记。")
    lines.append("")
    lines.append("## 当前未实际匹配的变量")
    lines.append("")
    if optional["nutrient_files"]:
        lines.append(f"- 已检测到营养文件：{optional['nutrient_files']}。本脚本本次尚未解析，建议确认列名后加入营养模块。")
    else:
        lines.append("- 未检测到 `nutrients` 文件夹或营养系数文件，因此本次未生成营养成分匹配列。")
    if optional["gdp_files"]:
        lines.append(f"- 已检测到 GDP 文件：{optional['gdp_files']}。本脚本本次尚未解析，建议确认列名后加入 GDP 模块。")
    else:
        lines.append("- 未检测到 GDP/人均 GDP CSV 文件，因此本次未匹配省级 GDP 与人均 GDP。")
    lines.append("")
    lines.append("## 重要口径说明")
    lines.append("")
    lines.append("- 碳足迹单位为 kg CO2e / kg 或 L 食物，水足迹单位为 L water / kg 或 L 食物；估算列用 `Volume × 系数` 得到，前提是 `Volume` 可解释为 kg 或 L。")
    lines.append("- `Volume` 的量纲若不统一，营养、碳足迹和水足迹只能作为代理指标，不能解释为真实摄入或真实环境足迹。")
    lines.append("- 农产品批发价格细分子指数大多从 2022-09-26 起才有值，因此 2020-2022 全期中很多品类子指数会缺失；全期可用性较好的是总 200 指数、菜篮子指数和粮油指数。")
    lines.append("- NMC 预警页面 `/rest/findAlarm` 未暴露历史日期参数，且网站声明未经授权禁止下载使用；本次未批量抓取 2020-2022 历史预警。")
    lines.append("")
    lines.append("## 食品品类覆盖")
    lines.append("")
    lines.append(f"- 主数据食品品类数：{len(categories)}")
    lines.append("- 品类：`" + "`, `".join(categories) + "`")
    (OUT / "matching_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print("Collecting main provinces/categories...", flush=True)
    main_provinces, categories = collect_main_provinces_categories()
    print(f"Main provinces: {len(main_provinces)}; categories: {len(categories)}", flush=True)

    print("Building CPI...", flush=True)
    _cpi_df, cpi_map = read_cpi()
    print("Building holidays...", flush=True)
    _holiday_df, holiday_map = holiday_table()
    print("Building category footprint mapping...", flush=True)
    _cat_df, category_map = build_category_mapping()
    print("Building COVID...", flush=True)
    _covid_df, covid_map = read_covid(main_provinces)
    print("Building wholesale price indexes...", flush=True)
    _wh_long, _wh_wide, wholesale_map = read_wholesale()
    print("Building weather...", flush=True)
    _weather_df, weather_map = read_weather(main_provinces)
    print("Writing province covariates...", flush=True)
    write_province_covariates(main_provinces, cpi_map, covid_map, wholesale_map, holiday_map, weather_map)
    print("Detecting optional files...", flush=True)
    optional = detect_optional_files()
    print("Enriching full transactions...", flush=True)
    stats = enrich_transactions_fast()
    print("Writing report...", flush=True)
    write_report(stats, optional, categories)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
