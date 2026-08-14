# -*- coding: utf-8 -*-
"""Build the unified manually verified MCI/AMS/AML analysis dataset.

The manually checked PCC, SE(PCC), elasticity, sample size and target are kept
unchanged. Verified path assignments are merged by record ID. Records assigned
to OTH and the documented final-sample exclusions are not analysed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = DATA / "manual_verified_parameters.csv"
PATH_FILE = DATA / "verified_path_assignments.csv"
EXCLUSION_FILE = DATA / "sample_exclusions.csv"

VALID_PATHS = {"MCI", "AMS", "AML"}


def first_number(value):
    if pd.isna(value):
        return float("nan")
    direct = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.notna(direct):
        return float(direct)
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(value))
    return float(match.group(0)) if match else float("nan")


def determine_target(row):
    casm = str(row.get("CASM 软链接目标", "")).lower()
    y_def = str(row.get("因变量定义 (Y) 及形式", "")).lower()
    if "area" in casm or "面积" in y_def or "趋粮" in y_def:
        return "Area"
    if ("efficiency" in casm or "效率" in y_def or "tfp" in y_def
            or "错配" in y_def or "集约" in y_def):
        return "Efficiency"
    return "Yield"


def locate_column(columns, required, forbidden=()):
    matches = [c for c in columns
               if all(term in c for term in required)
               and not any(term in c for term in forbidden)]
    if len(matches) != 1:
        raise ValueError(f"Expected one column for {required}, found {matches}")
    return matches[0]


def main():
    source = pd.read_csv(SOURCE, encoding="utf-8-sig")
    paths = pd.read_csv(PATH_FILE, encoding="utf-8-sig")
    exclusions = pd.read_csv(EXCLUSION_FILE, encoding="utf-8-sig")

    if not source["编号"].is_unique or not paths["编号"].is_unique:
        raise ValueError("Record IDs must be unique in source and path files")
    if set(source["编号"]) != set(paths["编号"]):
        raise ValueError("Verified path assignments do not cover the source records")

    pcc_col = locate_column(source.columns, ("PCC",), ("SE",))
    se_col = locate_column(source.columns, ("SE", "PCC"))
    elasticity_col = locate_column(source.columns, ("CASM 对接弹性",))

    classified = source.merge(paths, on="编号", how="left", validate="one_to_one")
    classified["Target"] = classified.apply(determine_target, axis=1)
    classified["N"] = pd.to_numeric(classified["样本量 (N)"], errors="coerce")
    classified["PCC"] = classified[pcc_col].map(first_number)
    classified["SE_PCC"] = classified[se_col].map(first_number)
    classified["elasticity"] = classified[elasticity_col].map(first_number)

    exclusion_reason = exclusions.set_index("编号")["reason"]
    classified["sample_exclusion_reason"] = classified["编号"].map(exclusion_reason)
    classified["path_exclusion_reason"] = classified["Path"].map(
        lambda p: "Core explanatory variable is non-mechanisation (OTH)" if p == "OTH" else ""
    )
    classified["included_in_analysis"] = (
        classified["sample_exclusion_reason"].isna()
        & classified["Path"].isin(VALID_PATHS)
    )

    preferred = [
        "编号", "来源", "标题", "作者_年份", "期刊级别", "数据层级/区域",
        "调研/数据年份", "作物分类", "N", "因变量定义 (Y) 及形式",
        "自变量定义 (X) 及形式", "PCC", "SE_PCC", "elasticity", "Target", "Path",
        "included_in_analysis", "sample_exclusion_reason", "path_exclusion_reason",
    ]
    classified = classified[[c for c in preferred if c in classified.columns]].copy()
    strict = classified[classified["included_in_analysis"]].copy()
    excluded = classified[~classified["included_in_analysis"]].copy()

    if strict[["PCC", "SE_PCC", "N"]].isna().any().any():
        raise ValueError("Included records contain missing PCC, SE_PCC or N")
    if (strict["SE_PCC"] <= 0).any():
        raise ValueError("Included records contain non-positive SE_PCC")
    expected_paths = {"MCI": 11, "AMS": 25, "AML": 4}
    expected_targets = {"Yield": 17, "Area": 5, "Efficiency": 18}
    if strict["Path"].value_counts().to_dict() != expected_paths:
        raise ValueError(f"Unexpected strict path counts: {strict['Path'].value_counts().to_dict()}")
    if strict["Target"].value_counts().to_dict() != expected_targets:
        raise ValueError(f"Unexpected strict target counts: {strict['Target'].value_counts().to_dict()}")

    classified.to_csv(DATA / "analysis_dataset_all_classified.csv",
                      index=False, encoding="utf-8-sig")
    strict.to_csv(DATA / "analysis_dataset_strict.csv",
                  index=False, encoding="utf-8-sig")
    excluded.to_csv(DATA / "excluded_records.csv",
                    index=False, encoding="utf-8-sig")
    strict.to_csv(DATA / "literature_list_strict.csv",
                  index=False, encoding="utf-8-sig")

    counts = pd.concat([
        pd.crosstab(strict["Target"], strict["Path"], margins=True)
        .rename_axis("Target").reset_index(),
    ], ignore_index=True)
    counts.to_csv(DATA / "analysis_sample_counts.csv",
                  index=False, encoding="utf-8-sig")
    print(f"Strict analysis dataset: k={len(strict)}")
    print(pd.crosstab(strict["Target"], strict["Path"], margins=True).to_string())
    print(f"Excluded records: k={len(excluded)}")


if __name__ == "__main__":
    main()
