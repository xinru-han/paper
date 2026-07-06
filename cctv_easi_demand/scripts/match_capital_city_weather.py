#!/usr/bin/env python3
"""
Match prefecture/city-level weather to the municipality/provincial-capital sample.

Because the consumption data only has Province plus CityTier=A, the matching
assumption is:
  CityTier=A -> municipality itself, or the province/autonomous-region capital.

The script extracts 2020-2022 daily city-level temperature and precipitation
from /Volumes/ORICO/地级市天气数据/城市 and streams the A-tier transaction sample.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WEATHER_DIR = Path("/Volumes/ORICO/地级市天气数据/城市")
INPUT_A = ROOT / "processed" / "Data_merged_enriched_citytier_municipality_capital.csv"
OUT_DIR = ROOT / "processed"


PROVINCE_CAPITAL_CITY = {
    "北京市": "北京市",
    "天津市": "天津市",
    "上海市": "上海市",
    "重庆市": "重庆市",
    "河北省": "石家庄市",
    "山西省": "太原市",
    "内蒙古自治区": "呼和浩特市",
    "辽宁省": "沈阳市",
    "吉林省": "长春市",
    "黑龙江省": "哈尔滨市",
    "江苏省": "南京市",
    "浙江省": "杭州市",
    "安徽省": "合肥市",
    "福建省": "福州市",
    "江西省": "南昌市",
    "山东省": "济南市",
    "河南省": "郑州市",
    "湖北省": "武汉市",
    "湖南省": "长沙市",
    "广东省": "广州市",
    "广西壮族自治区": "南宁市",
    "海南省": "海口市",
    "四川省": "成都市",
    "贵州省": "贵阳市",
    "云南省": "昆明市",
    "西藏自治区": "拉萨市",
    "陕西省": "西安市",
    "甘肃省": "兰州市",
    "青海省": "西宁市",
    "宁夏回族自治区": "银川市",
    "新疆维吾尔自治区": "乌鲁木齐市",
}


def read_target_provinces(input_csv: Path) -> list[str]:
    provinces: set[str] = set()
    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            province = row.get("Province", "").strip()
            if province:
                provinces.add(province)
    return sorted(provinces)


def load_weather_daily(years: list[int], target_map: dict[str, str]) -> pd.DataFrame:
    weather_parts = []
    missing_files = []
    for year in years:
        temp_file = WEATHER_DIR / f"{year}年各城市气温日度数据.xlsx"
        precip_file = WEATHER_DIR / f"{year}年各城市平均降水量日度数据.xlsx"
        if not temp_file.exists():
            missing_files.append(str(temp_file))
            continue
        if not precip_file.exists():
            missing_files.append(str(precip_file))
            continue

        temp = pd.read_excel(
            temp_file,
            usecols=["平均气温", "日期", "最高气温", "最低气温", "省", "省代码", "市", "市代码", "年份"],
        )
        precip = pd.read_excel(
            precip_file,
            usecols=["降水量", "日期", "省", "省代码", "市", "市代码", "年份"],
        )
        for df in (temp, precip):
            df["日期"] = pd.to_datetime(df["日期"], errors="coerce").dt.strftime("%Y-%m-%d")
            df["省"] = df["省"].astype(str).str.strip()
            df["市"] = df["市"].astype(str).str.strip()

        target_pairs = set(target_map.items())
        temp = temp[temp[["省", "市"]].apply(tuple, axis=1).isin(target_pairs)].copy()
        precip = precip[precip[["省", "市"]].apply(tuple, axis=1).isin(target_pairs)].copy()

        merged = temp.merge(
            precip[["省", "市", "日期", "降水量"]],
            on=["省", "市", "日期"],
            how="outer",
            validate="one_to_one",
        )
        merged = merged.rename(
            columns={
                "省": "weather_province",
                "市": "matched_city",
                "省代码": "weather_province_code",
                "市代码": "weather_city_code",
                "日期": "date_clean",
                "年份": "weather_year",
                "平均气温": "city_temp_avg_c",
                "最高气温": "city_temp_max_c",
                "最低气温": "city_temp_min_c",
                "降水量": "city_precipitation_mm",
            }
        )
        weather_parts.append(merged)
        print(f"Loaded city weather {year}: {len(merged):,} province-capital daily rows", flush=True)

    if missing_files:
        raise FileNotFoundError("Missing weather files: " + "; ".join(missing_files))
    if not weather_parts:
        raise ValueError("No weather data loaded.")

    weather = pd.concat(weather_parts, ignore_index=True)
    weather = weather.drop_duplicates(["weather_province", "matched_city", "date_clean"])
    return weather


def write_mapping_csv(target_map: dict[str, str], weather: pd.DataFrame, path: Path) -> None:
    availability = (
        weather.groupby(["weather_province", "matched_city"], dropna=False)
        .agg(
            weather_days=("date_clean", "nunique"),
            first_date=("date_clean", "min"),
            last_date=("date_clean", "max"),
            city_temp_avg_nonmissing=("city_temp_avg_c", lambda s: s.notna().sum()),
            city_precip_nonmissing=("city_precipitation_mm", lambda s: s.notna().sum()),
        )
        .reset_index()
    )
    rows = []
    for province, city in sorted(target_map.items()):
        hit = availability[(availability["weather_province"] == province) & (availability["matched_city"] == city)]
        if len(hit):
            rec = hit.iloc[0].to_dict()
        else:
            rec = {
                "weather_days": 0,
                "first_date": "",
                "last_date": "",
                "city_temp_avg_nonmissing": 0,
                "city_precip_nonmissing": 0,
            }
        rows.append(
            {
                "Province": province,
                "matched_city": city,
                "weather_days": rec["weather_days"],
                "first_date": rec["first_date"],
                "last_date": rec["last_date"],
                "city_temp_avg_nonmissing": rec["city_temp_avg_nonmissing"],
                "city_precip_nonmissing": rec["city_precip_nonmissing"],
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def stream_match(
    input_csv: Path,
    output_csv: Path,
    weather_lookup: dict[tuple[str, str], dict[str, str]],
    province_city_map: dict[str, str],
    progress_every: int = 1_000_000,
) -> dict[str, object]:
    added_cols = [
        "matched_city",
        "weather_city_code_citylevel",
        "city_temp_avg_c",
        "city_temp_max_c",
        "city_temp_min_c",
        "city_precipitation_mm",
        "city_weather_match_flag",
    ]
    total_rows = matched_rows = missing_rows = 0
    missing_by_date = Counter()
    missing_by_province = Counter()
    city_rows = Counter()
    city_ids: dict[str, set[str]] = {}

    with input_csv.open("r", encoding="utf-8-sig", newline="") as src, output_csv.open(
        "w", encoding="utf-8-sig", newline=""
    ) as dst:
        reader = csv.DictReader(src)
        if not reader.fieldnames:
            raise ValueError(f"{input_csv} has no header")
        fieldnames = list(reader.fieldnames)
        for col in added_cols:
            if col not in fieldnames:
                fieldnames.append(col)
        writer = csv.DictWriter(dst, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for row in reader:
            total_rows += 1
            province = row.get("Province", "").strip()
            date_clean = row.get("date_clean", "").strip()
            city = province_city_map.get(province, "")
            key = (province, date_clean)
            weather = weather_lookup.get(key)
            row["matched_city"] = city
            if weather:
                row["weather_city_code_citylevel"] = weather.get("weather_city_code", "")
                row["city_temp_avg_c"] = weather.get("city_temp_avg_c", "")
                row["city_temp_max_c"] = weather.get("city_temp_max_c", "")
                row["city_temp_min_c"] = weather.get("city_temp_min_c", "")
                row["city_precipitation_mm"] = weather.get("city_precipitation_mm", "")
                row["city_weather_match_flag"] = "1"
                matched_rows += 1
            else:
                row["weather_city_code_citylevel"] = ""
                row["city_temp_avg_c"] = ""
                row["city_temp_max_c"] = ""
                row["city_temp_min_c"] = ""
                row["city_precipitation_mm"] = ""
                row["city_weather_match_flag"] = "0"
                missing_rows += 1
                missing_by_date[date_clean] += 1
                missing_by_province[province] += 1

            city_rows[(province, city)] += 1
            city_ids.setdefault((province, city), set()).add(row.get("ID", ""))
            writer.writerow(row)

            if progress_every and total_rows % progress_every == 0:
                print(
                    f"Processed {total_rows:,} rows; city-weather matched {matched_rows:,}; missing {missing_rows:,}",
                    flush=True,
                )

    return {
        "total_rows": total_rows,
        "matched_rows": matched_rows,
        "missing_rows": missing_rows,
        "missing_by_date": missing_by_date,
        "missing_by_province": missing_by_province,
        "city_rows": city_rows,
        "city_ids": city_ids,
    }


def make_lookup(weather: pd.DataFrame) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    keep_cols = [
        "weather_city_code",
        "city_temp_avg_c",
        "city_temp_max_c",
        "city_temp_min_c",
        "city_precipitation_mm",
    ]
    for _, row in weather.iterrows():
        key = (str(row["weather_province"]), str(row["date_clean"]))
        lookup[key] = {
            col: "" if pd.isna(row.get(col)) else str(row.get(col))
            for col in keep_cols
        }
    return lookup


def write_report(
    path: Path,
    input_csv: Path,
    output_csv: Path,
    weather_csv: Path,
    mapping_csv: Path,
    target_map: dict[str, str],
    weather: pd.DataFrame,
    stats: dict[str, object],
) -> None:
    total_rows = int(stats["total_rows"])
    matched_rows = int(stats["matched_rows"])
    missing_rows = int(stats["missing_rows"])
    missing_by_date: Counter = stats["missing_by_date"]  # type: ignore[assignment]
    missing_by_province: Counter = stats["missing_by_province"]  # type: ignore[assignment]
    city_rows: Counter = stats["city_rows"]  # type: ignore[assignment]
    city_ids: dict = stats["city_ids"]  # type: ignore[assignment]

    city_lines = []
    for (province, city), count in city_rows.most_common():
        city_lines.append(f"- {province} -> {city}：{count:,} 行，{len(city_ids[(province, city)]):,} 个 ID")
    missing_date_lines = "\n".join(f"- {d}: {n:,} 行" for d, n in missing_by_date.most_common(20)) or "- 无"
    missing_prov_lines = "\n".join(f"- {p}: {n:,} 行" for p, n in missing_by_province.most_common()) or "- 无"
    target_lines = "\n".join(f"- {p} -> {c}" for p, c in sorted(target_map.items()))

    weather_days = weather["date_clean"].nunique()
    weather_city_count = weather[["weather_province", "matched_city"]].drop_duplicates().shape[0]
    date_min = weather["date_clean"].min()
    date_max = weather["date_clean"].max()

    report = f"""# 直辖市/省会城市样本城市级天气匹配报告

生成时间：{dt.datetime.now().isoformat(sep=" ", timespec="seconds")}

## 匹配口径

消费数据只有 `Province` 和 `CityTier=A`，没有具体城市名。因此本次采用：

`CityTier=A` -> 直辖市自身 / 省会城市。

即按 `Province -> matched_city` 后，再用 `Province + date_clean` 对应城市日度天气。

## 输入

- A 类消费样本：`{input_csv.relative_to(ROOT)}`
- 城市天气文件夹：`{WEATHER_DIR}`
- 年份：2020-2022

## 输出

- 匹配后 A 类样本：`{output_csv.relative_to(ROOT)}`
- 提取出的省会/直辖市日度天气：`{weather_csv.relative_to(ROOT)}`
- 省份-城市映射与天气覆盖：`{mapping_csv.relative_to(ROOT)}`

## 城市天气覆盖

- 提取城市数：{weather_city_count}
- 日期范围：{date_min} 至 {date_max}
- 不同日期数：{weather_days}
- 天气日度记录数：{len(weather):,}

## 匹配结果

- A 类消费样本行数：{total_rows:,}
- 成功匹配城市天气行数：{matched_rows:,}
- 未匹配行数：{missing_rows:,}
- 匹配率：{matched_rows / total_rows:.2%}

## 新增字段

- `matched_city`：按省份映射的直辖市/省会城市。
- `weather_city_code_citylevel`：城市级天气表中的市代码。
- `city_temp_avg_c`：城市日平均气温。
- `city_temp_max_c`：城市日最高气温。
- `city_temp_min_c`：城市日最低气温。
- `city_precipitation_mm`：城市日平均降水量。
- `city_weather_match_flag`：是否成功匹配城市天气。

## 省份到城市映射

{target_lines}

## A 类样本行数分布

{chr(10).join(city_lines)}

## 未匹配日期分布

{missing_date_lines}

## 未匹配省份分布

{missing_prov_lines}

## 注意

如果 `CityTier=A` 在原始编码中包含“非省会但省会级/副省级城市”的样本，仅凭当前补充表无法进一步区分具体城市；本次只能按省会/直辖市映射。若后续能获得 `ID -> 具体城市`，应以具体城市重做匹配。
"""
    path.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-a", type=Path, default=INPUT_A)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUT_DIR / "Data_merged_enriched_citytier_municipality_capital_cityweather.csv",
    )
    parser.add_argument(
        "--weather-output",
        type=Path,
        default=OUT_DIR / "capital_city_weather_daily_2020_2022.csv",
    )
    parser.add_argument(
        "--mapping-output",
        type=Path,
        default=OUT_DIR / "capital_city_weather_mapping.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=OUT_DIR / "capital_city_weather_matching_report.md",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    target_provinces = read_target_provinces(args.input_a)
    missing_map = [p for p in target_provinces if p not in PROVINCE_CAPITAL_CITY]
    if missing_map:
        raise KeyError(f"缺少省会映射：{missing_map}")
    target_map = {p: PROVINCE_CAPITAL_CITY[p] for p in target_provinces}

    weather = load_weather_daily([2020, 2021, 2022], target_map)
    weather.to_csv(args.weather_output, index=False, encoding="utf-8-sig")
    write_mapping_csv(target_map, weather, args.mapping_output)

    # Confirm every target province-city pair has at least one weather row.
    available_pairs = set(map(tuple, weather[["weather_province", "matched_city"]].drop_duplicates().values.tolist()))
    missing_pairs = sorted(set(target_map.items()) - available_pairs)
    if missing_pairs:
        print(f"WARNING: missing weather pairs: {missing_pairs}", flush=True)

    lookup = make_lookup(weather)
    stats = stream_match(args.input_a, args.output, lookup, target_map)
    write_report(args.report, args.input_a, args.output, args.weather_output, args.mapping_output, target_map, weather, stats)

    print(f"Wrote {args.output}")
    print(f"Wrote {args.weather_output}")
    print(f"Wrote {args.mapping_output}")
    print(f"Wrote {args.report}")
    print(
        f"Rows: {stats['total_rows']:,}; matched: {stats['matched_rows']:,}; missing: {stats['missing_rows']:,}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
