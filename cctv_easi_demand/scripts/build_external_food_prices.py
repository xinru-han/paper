#!/usr/bin/env python3
"""Build exogenous retail food prices matched to CCTV consumption categories.

The script reads the two local NDRC warning-system price folders, standardizes
TXT / HTML-XLS / XLSX / binary-XLS files, aggregates prices by province-month,
and outputs category-level and 10-group price tables for 2020-2022.
"""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup


BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "processed"
OUT.mkdir(exist_ok=True)

GRAIN_DIR = BASE / "成品粮零售---2005年1月----2024年5月30日(2005年1月预警系统)"
FOOD_DIR = BASE / "城市居民食品-1995年1月----2024年5月30日(2011年1月后预警系统全-1989-2010TXT文件有月份丢失)"

DATE_MIN = pd.Timestamp("2020-01-01")
DATE_MAX = pd.Timestamp("2022-12-31")

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

PROVINCE_ALIAS = {
    **{v: v for v in PROVINCE_FULL.values()},
    **PROVINCE_FULL,
    "广西自治区": "广西壮族自治区",
    "宁夏自治区": "宁夏回族自治区",
    "新疆自治区": "新疆维吾尔自治区",
    "内蒙古自治区": "内蒙古自治区",
    "西藏自治区": "西藏自治区",
}

CITY_TO_PROVINCE = {
    "石家庄市": "河北省",
    "唐山市": "河北省",
    "邢台市": "河北省",
    "太原市": "山西省",
    "大同市": "山西省",
    "晋城市": "山西省",
    "运城市": "山西省",
    "呼和浩特市": "内蒙古自治区",
    "包头市": "内蒙古自治区",
    "乌海市": "内蒙古自治区",
    "沈阳市": "辽宁省",
    "大连市": "辽宁省",
    "鞍山市": "辽宁省",
    "锦州市": "辽宁省",
    "铁岭市": "辽宁省",
    "长春市": "吉林省",
    "吉林市": "吉林省",
    "通化市": "吉林省",
    "哈尔滨市": "黑龙江省",
    "双鸭山市": "黑龙江省",
    "牡丹江市": "黑龙江省",
    "大庆市": "黑龙江省",
    "南京市": "江苏省",
    "徐州市": "江苏省",
    "苏州市": "江苏省",
    "南通市": "江苏省",
    "扬州市": "江苏省",
    "杭州市": "浙江省",
    "宁波市": "浙江省",
    "绍兴市": "浙江省",
    "衢州市": "浙江省",
    "合肥市": "安徽省",
    "淮南市": "安徽省",
    "铜陵市": "安徽省",
    "安庆市": "安徽省",
    "滁州市": "安徽省",
    "福州市": "福建省",
    "厦门市": "福建省",
    "三明市": "福建省",
    "泉州市": "福建省",
    "南昌市": "江西省",
    "九江市": "江西省",
    "赣州市": "江西省",
    "济南市": "山东省",
    "青岛市": "山东省",
    "枣庄市": "山东省",
    "烟台市": "山东省",
    "泰安市": "山东省",
    "菏泽市": "山东省",
    "郑州市": "河南省",
    "洛阳市": "河南省",
    "周口市": "河南省",
    "武汉市": "湖北省",
    "黄石市": "湖北省",
    "宜昌市": "湖北省",
    "襄阳市": "湖北省",
    "荆门市": "湖北省",
    "长沙市": "湖南省",
    "衡阳市": "湖南省",
    "常德市": "湖南省",
    "广州市": "广东省",
    "深圳市": "广东省",
    "汕头市": "广东省",
    "惠州市": "广东省",
    "南宁市": "广西壮族自治区",
    "柳州市": "广西壮族自治区",
    "北海市": "广西壮族自治区",
    "海口市": "海南省",
    "三亚市": "海南省",
    "成都市": "四川省",
    "乐山市": "四川省",
    "绵阳市": "四川省",
    "贵阳市": "贵州省",
    "遵义市": "贵州省",
    "安顺市": "贵州省",
    "昆明市": "云南省",
    "昭通市": "云南省",
    "曲靖市": "云南省",
    "楚雄州": "云南省",
    "拉萨市": "西藏自治区",
    "西安市": "陕西省",
    "延安市": "陕西省",
    "汉中市": "陕西省",
    "渭南市": "陕西省",
    "兰州市": "甘肃省",
    "平凉市": "甘肃省",
    "酒泉市": "甘肃省",
    "西宁市": "青海省",
    "格尔木市": "青海省",
    "银川市": "宁夏回族自治区",
    "吴忠市": "宁夏回族自治区",
    "石嘴山市": "宁夏回族自治区",
    "乌鲁木齐市": "新疆维吾尔自治区",
    "伊犁州": "新疆维吾尔自治区",
    "哈密地区": "新疆维吾尔自治区",
    "巴音郭楞自治州": "新疆维吾尔自治区",
}

GROUP10 = {
    "大米": "G01_主食",
    "面粉": "G01_主食",
    "挂面": "G01_主食",
    "方便面": "G01_主食",
    "食用油": "G02_食用油",
    "蔬菜": "G03_蔬菜",
    "水果": "G04_水果",
    "猪肉": "G05_猪肉",
    "禽类": "G06_禽类及其他肉类",
    "其他肉类": "G06_禽类及其他肉类",
    "牛肉": "G07_牛羊肉",
    "羊肉": "G07_牛羊肉",
    "海鲜类": "G08_海鲜",
    "常温牛奶": "G09_乳制品",
    "新鲜牛奶": "G09_乳制品",
    "常温酸奶": "G09_乳制品",
    "新鲜酸奶": "G09_乳制品",
    "奶酪": "G09_乳制品",
    "黄油": "G09_乳制品",
    "成人奶粉": "G09_乳制品",
    "坚果": "G10_坚果",
}


def norm_province(x: Any) -> str:
    s = str(x).strip().replace("\ufeff", "")
    if not s or s.lower() == "nan" or s == "(null)":
        return ""
    parts = [p.strip() for p in s.replace("全国-", "").replace("全国", "").split("-") if p.strip()]
    for part in parts:
        if part in PROVINCE_ALIAS:
            return PROVINCE_ALIAS[part]
        part2 = (
            part.replace("省", "")
            .replace("市", "")
            .replace("自治区", "")
            .replace("壮族", "")
            .replace("回族", "")
            .replace("维吾尔", "")
        )
        if part2 in PROVINCE_FULL:
            return PROVINCE_FULL[part2]
    s = parts[-1] if parts else s
    if "-" in s:
        s = s.split("-")[-1]
    s = s.strip()
    if s in PROVINCE_ALIAS:
        return PROVINCE_ALIAS[s]
    if s in CITY_TO_PROVINCE:
        return CITY_TO_PROVINCE[s]
    s2 = (
        s.replace("省", "")
        .replace("市", "")
        .replace("自治区", "")
        .replace("壮族", "")
        .replace("回族", "")
        .replace("维吾尔", "")
    )
    return PROVINCE_FULL.get(s, PROVINCE_FULL.get(s2, CITY_TO_PROVINCE.get(s, s)))


def clean_col(x: Any) -> str:
    return re.sub(r"\s+", "", str(x).replace("\ufeff", "").strip())


def clean_text(x: Any) -> str:
    if x is None:
        return ""
    s = str(x).replace("\ufeff", "").strip()
    if s.lower() in {"nan", "none", "(null)", "null"}:
        return ""
    return re.sub(r"\s+", "", s)


def safe_numeric(s: pd.Series) -> pd.Series:
    out = (
        s.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("，", "", regex=False)
        .str.replace("(null)", "", regex=False)
        .str.replace("null", "", case=False, regex=False)
        .str.replace("--", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(out, errors="coerce")


def collect_consumption_scope() -> tuple[list[str], list[str], list[str]]:
    provinces: set[str] = set()
    categories: set[str] = set()
    months: set[str] = set()
    path = BASE / "Data_merged.csv"
    for chunk in pd.read_csv(
        path,
        usecols=["Province", "Category", "Date"],
        dtype=str,
        chunksize=500_000,
        encoding="utf-8-sig",
    ):
        provinces.update(norm_province(x) for x in chunk["Province"].dropna().unique())
        categories.update(clean_text(x) for x in chunk["Category"].dropna().unique())
        dt = pd.to_datetime(chunk["Date"], errors="coerce", format="mixed")
        m = (dt >= DATE_MIN) & (dt <= DATE_MAX)
        months.update(dt[m].dt.strftime("%Y-%m").dropna().unique())
    provinces = sorted(x for x in provinces if x)
    categories = sorted(x for x in categories if x)
    months = sorted(x for x in months if x)
    return provinces, categories, months


def relevant_file(path: Path) -> bool:
    if path.name.startswith("._") or path.name == ".DS_Store":
        return False
    if path.suffix.lower() not in {".txt", ".xls", ".xlsx"}:
        return False
    text = str(path)
    return bool(re.search(r"2020|2021|2022", text))


def read_html_xls(path: Path) -> pd.DataFrame:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        return pd.DataFrame()
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
        if cells:
            rows.append(cells)
    if len(rows) <= 1:
        return pd.DataFrame()
    max_len = max(len(r) for r in rows)
    rows = [r + [""] * (max_len - len(r)) for r in rows]
    header = [clean_col(x) for x in rows[0]]
    return pd.DataFrame(rows[1:], columns=header)


def read_txt_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=r"\s+", engine="python", skiprows=[1], dtype=str, encoding="utf-8")


def read_excel_tables(path: Path) -> list[tuple[str, pd.DataFrame]]:
    tables = []
    xl = pd.ExcelFile(path)
    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(path, sheet_name=sheet, dtype=str)
        except Exception as exc:
            print(f"read_excel failed: {path} [{sheet}] {exc}", flush=True)
            continue
        tables.append((sheet, df))
    return tables


def standardize_table(df: pd.DataFrame, path: Path, dataset: str, sheet: str, source_format: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    df.columns = [clean_col(c) for c in df.columns]
    rename = {}
    for c in df.columns:
        if c in {"期号", "日期"}:
            rename[c] = "period_code"
        elif c in {"机构"}:
            rename[c] = "province_raw"
        elif c in {"监测点"}:
            rename[c] = "monitor_point"
        elif c in {"品种"}:
            rename[c] = "variety_raw"
        elif c in {"规格"}:
            rename[c] = "spec"
        elif c in {"单位", "品种单位"}:
            rename[c] = "unit"
        elif c in {"采价点", "采报价单位名称"}:
            rename[c] = "price_point"
        elif c in {"零售价格", "价格"}:
            rename[c] = "retail_price"
    df = df.rename(columns=rename)
    needed = {"period_code", "variety_raw", "retail_price"}
    if not needed.issubset(df.columns):
        return pd.DataFrame()
    if "province_raw" not in df.columns:
        df["province_raw"] = df.get("monitor_point", "")
    if "monitor_point" not in df.columns:
        df["monitor_point"] = df["province_raw"]
    for col in ["spec", "unit", "price_point"]:
        if col not in df.columns:
            df[col] = ""

    out = pd.DataFrame(
        {
            "source_dataset": dataset,
            "source_file": str(path.relative_to(BASE)),
            "source_sheet": sheet,
            "source_format": source_format,
            "period_code": df["period_code"].map(clean_text),
            "province": df["province_raw"].map(norm_province),
            "source_place": df["monitor_point"].map(clean_text),
            "variety_raw": df["variety_raw"].map(clean_text),
            "spec": df["spec"].map(clean_text),
            "unit": df["unit"].map(clean_text),
            "price_point": df["price_point"].map(clean_text),
            "retail_price": safe_numeric(df["retail_price"]),
        }
    )
    out["date"] = pd.to_datetime(out["period_code"], format="%Y%m%d", errors="coerce")
    out["year_month"] = out["date"].dt.strftime("%Y-%m")
    return out


def read_price_file(path: Path, dataset: str) -> pd.DataFrame:
    suffix = path.suffix.lower()
    try:
        head = path.read_bytes()[:32].lower()
    except Exception:
        head = b""
    frames: list[pd.DataFrame] = []
    if suffix == ".txt":
        try:
            frames.append(standardize_table(read_txt_table(path), path, dataset, "txt", "txt"))
        except Exception as exc:
            print(f"read_txt failed: {path} {exc}", flush=True)
    elif suffix == ".xls" and head.startswith(b"<html"):
        try:
            frames.append(standardize_table(read_html_xls(path), path, dataset, "html", "html_xls"))
        except Exception as exc:
            print(f"read_html_xls failed: {path} {exc}", flush=True)
    else:
        for sheet, df in read_excel_tables(path):
            frames.append(standardize_table(df, path, dataset, sheet, suffix.lstrip(".")))
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def is_avg_point(x: Any) -> bool:
    s = clean_text(x)
    if not s:
        return False
    if any(k in s for k in ["平均", "总平均"]):
        return True
    return s in {"集市", "超市", "农贸市场"}


def map_categories(variety: str, spec: str, dataset: str) -> list[tuple[str, str, str]]:
    v = clean_text(variety)
    sp = clean_text(spec)
    text = v + "|" + sp
    hits: list[tuple[str, str, str]] = []

    def add(cat: str, level: str, rule: str) -> None:
        hits.append((cat, level, rule))

    if re.search(r"粳米|籼米|大米", text):
        add("大米", "direct", "rice")
    if re.search(r"面粉|特一粉|标准粉", text):
        add("面粉", "direct", "flour")
    if re.search(r"挂面", text):
        add("挂面", "direct", "noodle")
    if re.search(r"方便面", text):
        add("方便面", "direct", "instant_noodle")
    if re.search(r"菜籽油|大豆油|花生油|调和油|食用油", text):
        add("食用油", "direct", "edible_oil")
    if re.search(r"猪肉|肋条肉|五花肉|精瘦肉|后腿肉", text):
        add("猪肉", "direct", "pork")
    if re.search(r"牛肉", text):
        add("牛肉", "direct", "beef")
        add("其他肉类", "proxy", "other_meat_from_beef")
    if re.search(r"羊肉", text):
        add("羊肉", "direct", "mutton")
        add("其他肉类", "proxy", "other_meat_from_mutton")
    if re.search(r"鸡肉|白条鸡|活鸡|鸭肉|白条鸭|活鸭|禽", text):
        add("禽类", "direct", "poultry")
        add("其他肉类", "proxy", "other_meat_from_poultry")
    if re.search(r"带鱼|草鱼|鲤鱼|鲫鱼|鲢鱼|鱼|虾|水产|海鲜", text):
        add("海鲜类", "direct", "aquatic")
    if re.search(r"牛奶|鲜奶|纯牛奶", v) and "奶粉" not in v:
        add("新鲜牛奶", "direct_or_common_milk", "milk")
        add("常温牛奶", "common_milk_proxy", "milk")
    if re.search(r"酸奶", text):
        add("新鲜酸奶", "direct_or_common_yogurt", "yogurt")
        add("常温酸奶", "common_yogurt_proxy", "yogurt")
    if re.search(r"奶粉", text):
        add("成人奶粉", "direct", "milk_powder")
    if re.search(r"奶酪|芝士", text):
        add("奶酪", "direct", "cheese")
    if re.search(r"黄油|奶油", text):
        add("黄油", "direct", "butter")
    if "花生油" not in text and re.search(r"坚果|核桃|花生仁|花生|瓜子|杏仁|腰果|开心果", text):
        add("坚果", "direct_or_nut_proxy", "nuts")

    veg_terms = (
        "土豆|马铃薯|萝卜|胡萝卜|大白菜|小白菜|油菜|芹菜|黄瓜|茄子|西红柿|番茄|"
        "豆角|青椒|尖椒|圆白菜|卷心菜|蒜薹|蒜苔|韭菜|菜花|花菜|菠菜|生菜|西兰花|莲藕|"
        "冬瓜|南瓜|西葫芦|蘑菇|香菇|大葱|大蒜|生姜|蔬菜"
    )
    if re.search(veg_terms, text):
        add("蔬菜", "direct", "vegetable")

    fruit_terms = "苹果|香蕉|梨|鸭梨|西瓜|橙|柑|橘|桔|葡萄|桃|水果"
    if re.search(fruit_terms, text):
        add("水果", "direct", "fruit")

    seen = set()
    uniq = []
    for item in hits:
        if item[0] not in seen:
            uniq.append(item)
            seen.add(item[0])
    return uniq


def build_raw_prices(main_provinces: list[str]) -> tuple[pd.DataFrame, Counter, Counter]:
    files = []
    files += [(p, "grain_retail") for p in sorted(GRAIN_DIR.rglob("*")) if relevant_file(p)]
    files += [(p, "urban_food") for p in sorted(FOOD_DIR.rglob("*")) if relevant_file(p)]
    frames = []
    read_counter: Counter = Counter()
    row_counter: Counter = Counter()
    for idx, (path, dataset) in enumerate(files, 1):
        df = read_price_file(path, dataset)
        read_counter[dataset] += 1
        row_counter["rows_read"] += len(df)
        if df.empty:
            continue
        df = df[
            (df["date"] >= DATE_MIN)
            & (df["date"] <= DATE_MAX)
            & (df["province"].isin(main_provinces))
            & (df["retail_price"] > 0)
            & (df["variety_raw"] != "")
        ].copy()
        if not df.empty:
            frames.append(df)
        print(f"[{idx:03d}/{len(files):03d}] {dataset}: {path.name} -> {len(df):,} usable rows", flush=True)
    if not frames:
        return pd.DataFrame(), read_counter, row_counter
    raw = pd.concat(frames, ignore_index=True)
    raw["is_average_point"] = raw["price_point"].map(is_avg_point)
    raw = raw.drop_duplicates(
        subset=[
            "source_dataset",
            "date",
            "province",
            "variety_raw",
            "spec",
            "unit",
            "price_point",
            "retail_price",
        ]
    )
    raw["date"] = raw["date"].dt.strftime("%Y-%m-%d")
    return raw, read_counter, row_counter


def prefer_point_observations(raw: pd.DataFrame) -> pd.DataFrame:
    key = ["source_dataset", "date", "province", "variety_raw", "spec", "unit"]
    has_point = raw.assign(non_avg=(~raw["is_average_point"]).astype(int)).groupby(key)["non_avg"].transform("max")
    keep = (~raw["is_average_point"]) | (has_point == 0)
    retained = raw[keep].copy()
    retained["retained_for_mean"] = 1
    return retained


def expand_to_categories(retained: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = []
    unmapped = Counter()
    for r in retained.itertuples(index=False):
        mapped = map_categories(r.variety_raw, r.spec, r.source_dataset)
        if not mapped:
            unmapped[(r.source_dataset, r.variety_raw, r.spec, r.unit)] += 1
            continue
        for cat, level, rule in mapped:
            records.append(
                {
                    "province": r.province,
                    "date": r.date,
                    "year_month": r.year_month,
                    "Category": cat,
                    "retail_price": r.retail_price,
                    "source_dataset": r.source_dataset,
                    "variety_raw": r.variety_raw,
                    "spec": r.spec,
                    "unit": r.unit,
                    "match_level_observed": level,
                    "match_rule": rule,
                    "source_file": r.source_file,
                }
            )
    mapped_df = pd.DataFrame(records)
    unmapped_rows = [
        {
            "source_dataset": k[0],
            "variety_raw": k[1],
            "spec": k[2],
            "unit": k[3],
            "unmapped_obs": v,
        }
        for k, v in unmapped.items()
    ]
    return mapped_df, pd.DataFrame(unmapped_rows).sort_values("unmapped_obs", ascending=False)


def observed_category_month(mapped: pd.DataFrame) -> pd.DataFrame:
    if mapped.empty:
        return pd.DataFrame()
    obs = (
        mapped.groupby(["province", "year_month", "Category"], as_index=False)
        .agg(
            external_price_mean_observed=("retail_price", "mean"),
            external_price_median_observed=("retail_price", "median"),
            n_price_obs=("retail_price", "count"),
            n_source_varieties=("variety_raw", "nunique"),
            source_varieties=("variety_raw", lambda x: ";".join(sorted(set(map(str, x)))[:30])),
            units=("unit", lambda x: ";".join(sorted(set(map(str, x)))[:10])),
            observed_match_levels=("match_level_observed", lambda x: ";".join(sorted(set(map(str, x))))),
        )
        .sort_values(["province", "year_month", "Category"])
    )
    return obs


def fill_full_category_grid(
    observed: pd.DataFrame,
    main_provinces: list[str],
    main_months: list[str],
    main_categories: list[str],
) -> pd.DataFrame:
    grid = pd.MultiIndex.from_product(
        [main_provinces, main_months, main_categories],
        names=["province", "year_month", "Category"],
    ).to_frame(index=False)
    full = grid.merge(observed, on=["province", "year_month", "Category"], how="left")
    full["external_price_mean"] = full["external_price_mean_observed"]
    full["external_price_median"] = full["external_price_median_observed"]
    full["price_fill_level"] = np.where(full["external_price_mean"].notna(), "observed_province_month", "")
    full["proxy_source_category"] = ""

    national = (
        observed.groupby(["year_month", "Category"], as_index=False)
        .agg(
            national_price_mean=("external_price_mean_observed", "mean"),
            national_price_median=("external_price_median_observed", "mean"),
            national_n_provinces=("province", "nunique"),
        )
    )
    full = full.merge(national, on=["year_month", "Category"], how="left")
    missing = full["external_price_mean"].isna() & full["national_price_mean"].notna()
    full.loc[missing, "external_price_mean"] = full.loc[missing, "national_price_mean"]
    full.loc[missing, "external_price_median"] = full.loc[missing, "national_price_median"]
    full.loc[missing, "price_fill_level"] = "national_month_category"

    proxy_map = {
        "常温酸奶": ["新鲜酸奶", "新鲜牛奶", "常温牛奶"],
        "新鲜酸奶": ["常温酸奶", "新鲜牛奶", "常温牛奶"],
        "奶酪": ["新鲜牛奶", "常温牛奶"],
        "黄油": ["新鲜牛奶", "常温牛奶", "食用油"],
        "成人奶粉": ["新鲜牛奶", "常温牛奶"],
        "常温牛奶": ["新鲜牛奶"],
        "新鲜牛奶": ["常温牛奶"],
        "方便面": ["挂面", "面粉"],
        "挂面": ["面粉"],
        "其他肉类": ["禽类", "牛肉", "羊肉"],
        "坚果": ["食用油"],
    }
    lookup = full.set_index(["province", "year_month", "Category"])["external_price_mean"].to_dict()
    lookup_fill = full.set_index(["province", "year_month", "Category"])["price_fill_level"].to_dict()
    nat_lookup = full.groupby(["year_month", "Category"])["external_price_mean"].mean().to_dict()

    for idx, row in full[full["external_price_mean"].isna()].iterrows():
        candidates = proxy_map.get(row["Category"], [])
        vals = []
        src = []
        for cat in candidates:
            val = lookup.get((row["province"], row["year_month"], cat))
            if val is not None and not (isinstance(val, float) and math.isnan(val)):
                vals.append(float(val))
                src.append(cat)
        if vals:
            full.at[idx, "external_price_mean"] = float(np.mean(vals))
            full.at[idx, "external_price_median"] = float(np.median(vals))
            full.at[idx, "price_fill_level"] = "province_month_proxy_category"
            full.at[idx, "proxy_source_category"] = ";".join(src)
            continue
        vals = []
        src = []
        for cat in candidates:
            val = nat_lookup.get((row["year_month"], cat))
            if val is not None and not (isinstance(val, float) and math.isnan(val)):
                vals.append(float(val))
                src.append(cat)
        if vals:
            full.at[idx, "external_price_mean"] = float(np.mean(vals))
            full.at[idx, "external_price_median"] = float(np.median(vals))
            full.at[idx, "price_fill_level"] = "national_month_proxy_category"
            full.at[idx, "proxy_source_category"] = ";".join(src)

    full["external_log_price"] = np.log(full["external_price_mean"].where(full["external_price_mean"] > 0))
    full["Category_group10"] = full["Category"].map(GROUP10)
    cat_mean_log = full.groupby("Category")["external_log_price"].transform("mean")
    full["external_log_price_centered_category"] = full["external_log_price"] - cat_mean_log
    full["external_price_index_category_mean100"] = np.exp(full["external_log_price_centered_category"]) * 100
    return full


def build_group10(category_full: pd.DataFrame) -> pd.DataFrame:
    df = category_full.dropna(subset=["Category_group10", "external_log_price_centered_category"]).copy()
    group = (
        df.groupby(["province", "year_month", "Category_group10"], as_index=False)
        .agg(
            external_log_price_group10=("external_log_price_centered_category", "mean"),
            external_price_index_group10_mean100=("external_price_index_category_mean100", "mean"),
            n_categories_in_group=("Category", "nunique"),
            categories=("Category", lambda x: ";".join(sorted(set(map(str, x))))),
            fill_levels=("price_fill_level", lambda x: ";".join(sorted(set(map(str, x))))),
        )
        .rename(columns={"Category_group10": "food_group10"})
        .sort_values(["province", "year_month", "food_group10"])
    )
    group["external_price_index_group10_mean100"] = np.exp(group["external_log_price_group10"]) * 100
    return group


def write_report(
    raw: pd.DataFrame,
    retained: pd.DataFrame,
    mapped: pd.DataFrame,
    category_full: pd.DataFrame,
    group10: pd.DataFrame,
    unmapped: pd.DataFrame,
    main_provinces: list[str],
    main_months: list[str],
    main_categories: list[str],
    read_counter: Counter,
    row_counter: Counter,
) -> None:
    coverage = (
        category_full.groupby("Category", as_index=False)
        .agg(
            rows=("external_price_mean", "size"),
            non_missing=("external_price_mean", lambda x: int(x.notna().sum())),
            observed_rows=("price_fill_level", lambda x: int((x == "observed_province_month").sum())),
            national_fill=("price_fill_level", lambda x: int((x == "national_month_category").sum())),
            proxy_fill=("price_fill_level", lambda x: int(x.astype(str).str.contains("proxy").sum())),
            missing=("external_price_mean", lambda x: int(x.isna().sum())),
        )
        .sort_values("Category")
    )
    group_cov = (
        group10.groupby("food_group10", as_index=False)
        .agg(rows=("external_price_index_group10_mean100", "size"), non_missing=("external_price_index_group10_mean100", lambda x: int(x.notna().sum())))
        .sort_values("food_group10")
    )
    lines = []
    lines.append("# 外生食品价格匹配报告")
    lines.append("")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 输入范围")
    lines.append("")
    lines.append(f"- 价格文件夹 1：`{GRAIN_DIR.name}`")
    lines.append(f"- 价格文件夹 2：`{FOOD_DIR.name}`")
    lines.append(f"- 消费样本省份数：{len(main_provinces)}")
    lines.append(f"- 消费样本月份数：{len(main_months)}，范围 {min(main_months)} 至 {max(main_months)}")
    lines.append(f"- 消费样本品类数：{len(main_categories)}")
    lines.append("")
    lines.append("## 输出文件")
    lines.append("")
    for name in [
        "external_food_prices_raw_long_2020_2022.csv",
        "external_food_prices_retained_points_2020_2022.csv",
        "external_food_prices_mapped_observations_2020_2022.csv",
        "external_food_prices_category_province_month_2020_2022.csv",
        "external_food_prices_category_province_month_wide_2020_2022.csv",
        "external_food_prices_group10_province_month_2020_2022.csv",
        "external_food_prices_unmapped_varieties_2020_2022.csv",
    ]:
        p = OUT / name
        if p.exists():
            lines.append(f"- `{name}`：{p.stat().st_size / (1024 * 1024):.1f} MB")
    lines.append("")
    lines.append("## 处理统计")
    lines.append("")
    lines.append(f"- 读取价格文件数：{sum(read_counter.values())}；其中 `{dict(read_counter)}`")
    lines.append(f"- 初步读入行数：{row_counter.get('rows_read', 0):,}")
    lines.append(f"- 2020-2022 相关省份有效价格观测：{len(raw):,}")
    lines.append(f"- 剔除平均点位后保留观测：{len(retained):,}")
    lines.append(f"- 映射到消费品类后的观测：{len(mapped):,}")
    lines.append(f"- 21 品类省份-月份完整网格：{len(category_full):,}")
    lines.append(f"- 10 组省份-月份价格表：{len(group10):,}")
    lines.append("")
    lines.append("## 21 品类覆盖")
    lines.append("")
    lines.append("| 品类 | 网格行 | 非缺失 | 省月直接观测 | 全国月补值 | 代理补值 | 仍缺失 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in coverage.itertuples(index=False):
        lines.append(f"| {r.Category} | {r.rows} | {r.non_missing} | {r.observed_rows} | {r.national_fill} | {r.proxy_fill} | {r.missing} |")
    lines.append("")
    lines.append("## 10 组覆盖")
    lines.append("")
    lines.append("| 10组 | 行数 | 非缺失 |")
    lines.append("|---|---:|---:|")
    for r in group_cov.itertuples(index=False):
        lines.append(f"| {r.food_group10} | {r.rows} | {r.non_missing} |")
    lines.append("")
    lines.append("## 口径说明")
    lines.append("")
    lines.append("- 对同一省份、日期、品种、规格、单位，优先使用非平均点位；如果只有 `超市平均`、`集市平均`、`总平均价` 等平均行，则使用平均行。")
    lines.append("- 月度价格采用可用旬度/点位零售价格的算术均值。")
    lines.append("- 21 品类表保留 `price_fill_level`：`observed_province_month` 为省份-月份直接观测；`national_month_category` 为全国同月同品类均值补齐；`province_month_proxy_category` 和 `national_month_proxy_category` 为相近品类代理。")
    lines.append("- 10 组表使用 21 品类的组内平均对数价格指数，适合 EASI 主模型作为外生价格变量。")
    lines.append("")
    if not unmapped.empty:
        lines.append("## 未映射价格品种 Top 30")
        lines.append("")
        lines.append("| 来源 | 品种 | 规格 | 单位 | 未映射观测 |")
        lines.append("|---|---|---|---|---:|")
        for r in unmapped.head(30).itertuples(index=False):
            lines.append(f"| {r.source_dataset} | {r.variety_raw} | {r.spec} | {r.unit} | {r.unmapped_obs} |")
        lines.append("")
    (OUT / "external_food_price_matching_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    main_provinces, main_categories, main_months = collect_consumption_scope()
    print(f"Consumption scope: {len(main_provinces)} provinces, {len(main_months)} months, {len(main_categories)} categories", flush=True)
    raw, read_counter, row_counter = build_raw_prices(main_provinces)
    if raw.empty:
        raise RuntimeError("No price rows were parsed.")

    raw_out = OUT / "external_food_prices_raw_long_2020_2022.csv"
    raw.to_csv(raw_out, index=False, encoding="utf-8-sig")

    retained = prefer_point_observations(raw)
    retained.to_csv(OUT / "external_food_prices_retained_points_2020_2022.csv", index=False, encoding="utf-8-sig")

    mapped, unmapped = expand_to_categories(retained)
    mapped.to_csv(OUT / "external_food_prices_mapped_observations_2020_2022.csv", index=False, encoding="utf-8-sig")
    unmapped.to_csv(OUT / "external_food_prices_unmapped_varieties_2020_2022.csv", index=False, encoding="utf-8-sig")

    observed = observed_category_month(mapped)
    category_full = fill_full_category_grid(observed, main_provinces, main_months, main_categories)
    category_full.to_csv(OUT / "external_food_prices_category_province_month_2020_2022.csv", index=False, encoding="utf-8-sig")

    wide = category_full.pivot_table(
        index=["province", "year_month"],
        columns="Category",
        values="external_price_index_category_mean100",
        aggfunc="first",
    ).reset_index()
    wide.columns = [f"priceidx_{c}" if c not in {"province", "year_month"} else c for c in wide.columns]
    wide.to_csv(OUT / "external_food_prices_category_province_month_wide_2020_2022.csv", index=False, encoding="utf-8-sig")

    group10 = build_group10(category_full)
    group10.to_csv(OUT / "external_food_prices_group10_province_month_2020_2022.csv", index=False, encoding="utf-8-sig")

    try:
        raw.to_parquet(OUT / "external_food_prices_raw_long_2020_2022.parquet", index=False)
        category_full.to_parquet(OUT / "external_food_prices_category_province_month_2020_2022.parquet", index=False)
        group10.to_parquet(OUT / "external_food_prices_group10_province_month_2020_2022.parquet", index=False)
    except Exception as exc:
        print(f"Parquet export skipped: {exc}", flush=True)

    write_report(
        raw=raw,
        retained=retained,
        mapped=mapped,
        category_full=category_full,
        group10=group10,
        unmapped=unmapped,
        main_provinces=main_provinces,
        main_months=main_months,
        main_categories=main_categories,
        read_counter=read_counter,
        row_counter=row_counter,
    )
    print("Done. Report:", OUT / "external_food_price_matching_report.md", flush=True)


if __name__ == "__main__":
    main()
