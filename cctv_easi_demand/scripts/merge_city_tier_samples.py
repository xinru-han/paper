#!/usr/bin/env python3
"""
Merge city-tier sample metadata into the enriched CCTV consumption dataset.

Input supplement:
  补充样本城市级别--20260610.xlsx

Outputs:
  processed/Data_merged_enriched_citytier.csv
  processed/Data_merged_enriched_citytier_municipality_capital.csv
  processed/city_tier_sample_mapping.csv
  processed/city_tier_matching_report.md
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "processed" / "Data_merged_enriched.csv"
DEFAULT_SUPPLEMENT = ROOT / "补充样本城市级别--20260610.xlsx"
OUT_DIR = ROOT / "processed"


def load_city_tier_mapping(path: Path) -> tuple[dict[str, str], dict[str, str], pd.DataFrame]:
    city = pd.read_excel(path, sheet_name="样本城市级别", dtype={"ID": "string", "CityTier": "string"})
    city = city[["ID", "CityTier"]].copy()
    city["ID"] = city["ID"].astype("string").str.strip()
    city["CityTier"] = city["CityTier"].astype("string").str.strip()
    city = city.dropna(subset=["ID"])
    if city["ID"].duplicated().any():
        dupes = city.loc[city["ID"].duplicated(), "ID"].head(10).tolist()
        raise ValueError(f"补充表存在重复 ID，示例：{dupes}")

    labels = pd.read_excel(path, sheet_name="城市级别说明", dtype="string")
    labels = labels[["CityTier", "城市级别"]].copy()
    labels["CityTier"] = labels["CityTier"].astype("string").str.strip()
    labels["城市级别"] = labels["城市级别"].astype("string").str.strip()
    label_map = dict(zip(labels["CityTier"], labels["城市级别"]))
    tier_map = dict(zip(city["ID"], city["CityTier"]))

    city["city_tier_label"] = city["CityTier"].map(label_map)
    city["city_tier_a_flag"] = (city["CityTier"] == "A").astype(int)
    return tier_map, label_map, city


def write_mapping(mapping_df: pd.DataFrame, path: Path) -> None:
    mapping_df.to_csv(path, index=False, encoding="utf-8-sig")


def merge_stream(
    input_csv: Path,
    output_csv: Path,
    output_a_csv: Path,
    tier_map: dict[str, str],
    label_map: dict[str, str],
    progress_every: int = 1_000_000,
) -> dict[str, object]:
    row_count = 0
    matched_rows = 0
    unmatched_rows = 0
    a_rows = 0
    ids_seen: set[str] = set()
    matched_ids: set[str] = set()
    a_ids: set[str] = set()
    tier_row_counts: Counter[str] = Counter()

    added_cols = ["CityTier", "city_tier_label", "city_tier_a_flag"]

    with input_csv.open("r", encoding="utf-8-sig", newline="") as src, output_csv.open(
        "w", encoding="utf-8-sig", newline=""
    ) as dst, output_a_csv.open("w", encoding="utf-8-sig", newline="") as dst_a:
        reader = csv.DictReader(src)
        if not reader.fieldnames:
            raise ValueError(f"{input_csv} 没有表头")
        fieldnames = list(reader.fieldnames)
        for col in added_cols:
            if col not in fieldnames:
                fieldnames.append(col)

        writer = csv.DictWriter(dst, fieldnames=fieldnames, extrasaction="ignore")
        writer_a = csv.DictWriter(dst_a, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer_a.writeheader()

        for row in reader:
            row_count += 1
            sample_id = str(row.get("ID", "")).strip()
            if sample_id:
                ids_seen.add(sample_id)
            tier = tier_map.get(sample_id, "")
            label = label_map.get(tier, "")
            row["CityTier"] = tier
            row["city_tier_label"] = label
            row["city_tier_a_flag"] = "1" if tier == "A" else "0"

            if tier:
                matched_rows += 1
                matched_ids.add(sample_id)
                tier_row_counts[tier] += 1
            else:
                unmatched_rows += 1
                tier_row_counts["UNMATCHED"] += 1

            writer.writerow(row)
            if tier == "A":
                a_rows += 1
                a_ids.add(sample_id)
                writer_a.writerow(row)

            if progress_every and row_count % progress_every == 0:
                print(
                    f"Processed {row_count:,} rows; matched {matched_rows:,}; "
                    f"A rows {a_rows:,}",
                    flush=True,
                )

    return {
        "row_count": row_count,
        "matched_rows": matched_rows,
        "unmatched_rows": unmatched_rows,
        "a_rows": a_rows,
        "ids_seen": ids_seen,
        "matched_ids": matched_ids,
        "a_ids": a_ids,
        "tier_row_counts": tier_row_counts,
    }


def write_report(
    path: Path,
    input_csv: Path,
    supplement: Path,
    output_csv: Path,
    output_a_csv: Path,
    mapping_csv: Path,
    stats: dict[str, object],
    mapping_df: pd.DataFrame,
    label_map: dict[str, str],
) -> None:
    ids_seen = stats["ids_seen"]
    matched_ids = stats["matched_ids"]
    a_ids = stats["a_ids"]
    tier_row_counts = stats["tier_row_counts"]
    assert isinstance(ids_seen, set)
    assert isinstance(matched_ids, set)
    assert isinstance(a_ids, set)
    assert isinstance(tier_row_counts, Counter)

    mapping_ids = set(mapping_df["ID"].astype(str))
    data_ids_missing_mapping = sorted(ids_seen - mapping_ids)
    mapping_ids_not_in_data = sorted(mapping_ids - ids_seen)

    tier_id_counts = mapping_df["CityTier"].value_counts().sort_index()
    tier_id_lines = "\n".join(
        f"- {tier}（{label_map.get(tier, '')}）：{int(count):,} 个 ID"
        for tier, count in tier_id_counts.items()
    )
    tier_row_lines = "\n".join(
        f"- {tier}（{label_map.get(tier, '未匹配')}）：{count:,} 行"
        for tier, count in sorted(tier_row_counts.items())
    )

    row_count = int(stats["row_count"])
    matched_rows = int(stats["matched_rows"])
    a_rows = int(stats["a_rows"])
    report = f"""# 城市级别补充样本匹配报告

生成时间：{dt.datetime.now().isoformat(sep=" ", timespec="seconds")}

## 输入

- 主数据：`{input_csv.relative_to(ROOT)}`
- 补充表：`{supplement.relative_to(ROOT)}`
- 匹配键：`ID`

## 输出

- 全量匹配后数据：`{output_csv.relative_to(ROOT)}`
- 直辖市/省会城市样本数据：`{output_a_csv.relative_to(ROOT)}`
- ID-城市级别映射表：`{mapping_csv.relative_to(ROOT)}`

## 匹配结果

- 主数据行数：{row_count:,}
- 主数据唯一 ID 数：{len(ids_seen):,}
- 成功匹配行数：{matched_rows:,}（{matched_rows / row_count:.2%}）
- 未匹配行数：{int(stats["unmatched_rows"]):,}
- 成功匹配唯一 ID 数：{len(matched_ids):,}
- 补充表唯一 ID 数：{mapping_df["ID"].nunique():,}
- 补充表中未出现在主数据的 ID 数：{len(mapping_ids_not_in_data):,}
- 主数据中缺少城市级别映射的 ID 数：{len(data_ids_missing_mapping):,}

## 补充表 ID 分布

{tier_id_lines}

## 主数据行级分布

{tier_row_lines}

## 直辖市/省会城市样本

定义：`CityTier == "A"`，补充表说明为 `{label_map.get("A", "")}`。

- A 类样本唯一 ID 数：{len(a_ids):,}
- A 类样本行数：{a_rows:,}
- A 类样本占主数据行数比例：{a_rows / row_count:.2%}

## 新增字段

- `CityTier`：城市级别编码，A/B/C/D/E。
- `city_tier_label`：城市级别中文说明。
- `city_tier_a_flag`：是否为直辖市/省会城市样本，1=是，0=否。

## 备注

本次没有覆盖原始 `processed/Data_merged_enriched.csv`，而是另存为带城市级别字段的新文件。后续可在 `CityTier == "A"` 的子集上继续匹配直辖市和省会城市的城市级气温、降水等变量。
"""
    if data_ids_missing_mapping:
        report += "\n## 主数据缺少映射的 ID 示例\n\n"
        report += ", ".join(data_ids_missing_mapping[:50]) + "\n"
    if mapping_ids_not_in_data:
        report += "\n## 补充表未出现在主数据的 ID 示例\n\n"
        report += ", ".join(mapping_ids_not_in_data[:50]) + "\n"
    path.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--supplement", type=Path, default=DEFAULT_SUPPLEMENT)
    parser.add_argument("--output", type=Path, default=OUT_DIR / "Data_merged_enriched_citytier.csv")
    parser.add_argument(
        "--output-a",
        type=Path,
        default=OUT_DIR / "Data_merged_enriched_citytier_municipality_capital.csv",
    )
    parser.add_argument("--mapping-output", type=Path, default=OUT_DIR / "city_tier_sample_mapping.csv")
    parser.add_argument("--report", type=Path, default=OUT_DIR / "city_tier_matching_report.md")
    args = parser.parse_args()

    tier_map, label_map, mapping_df = load_city_tier_mapping(args.supplement)
    write_mapping(mapping_df, args.mapping_output)
    stats = merge_stream(args.input, args.output, args.output_a, tier_map, label_map)
    write_report(
        args.report,
        args.input,
        args.supplement,
        args.output,
        args.output_a,
        args.mapping_output,
        stats,
        mapping_df,
        label_map,
    )

    print(f"Wrote {args.output}")
    print(f"Wrote {args.output_a}")
    print(f"Wrote {args.mapping_output}")
    print(f"Wrote {args.report}")
    print(
        f"Rows: {stats['row_count']:,}; matched: {stats['matched_rows']:,}; "
        f"A rows: {stats['a_rows']:,}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
