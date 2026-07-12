#!/usr/bin/env python3
"""Rebuild six household unit values from item purchase quantity and cost."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MODULES = {
    1: ["主食部分.csv", "主食加工品的获取与消费.csv"],
    2: ["豆类过去7天的消费.csv", "豆制品的获取与消费.csv"],
    3: ["肉类.csv", "肉制品.csv"],
    4: ["油脂类.csv"],
    5: ["_蔬菜.csv", "蔬菜制品.csv"],
    6: ["水果干果.csv", "水果制品.csv"],
}


def numeric(series: pd.Series) -> pd.Series:
    """Parse numeric entries, including simple fractions and annotated values."""
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


def extract_module(path: Path, year: int, group: int) -> tuple[pd.DataFrame, dict]:
    names = list(pd.read_csv(path, nrows=0, encoding="utf-8-sig").columns)
    qvars = [name for name in names if "_laiyuan-02-" in name]
    pairs = []
    for qvar in qvars:
        xvar = qvar.replace("_laiyuan-02-", "_laiyuan-03-", 1)
        fvar = qvar.replace("_laiyuan-02-", "_laiyuan-00-", 1)
        if xvar in names and fvar in names:
            pairs.append((qvar, xvar, fvar))
    if not pairs:
        raise RuntimeError(f"No matched 00/02/03 item fields in {path}")

    columns = ["nhCode", "freq_period_days"]
    columns.extend(value for pair in pairs for value in pair)
    columns = list(dict.fromkeys(columns))
    frame = pd.read_csv(
        path,
        usecols=columns,
        dtype={"nhCode": "string"},
        encoding="utf-8-sig",
        low_memory=False,
    )
    days = numeric(frame["freq_period_days"])
    quantity = np.zeros(len(frame), dtype=float)
    expenditure = np.zeros(len(frame), dtype=float)
    valid_pairs = np.zeros(len(frame), dtype=np.int16)
    invalid_negative = 0

    for qvar, xvar, fvar in pairs:
        q = numeric(frame[qvar])
        x = numeric(frame[xvar])
        frequency = numeric(frame[fvar])
        invalid_negative += int(((q < 0) | (x < 0)).fillna(False).sum())
        factor = np.where(
            frequency.eq(2),
            30.0 / 7.0,
            np.where(frequency.eq(1) & days.gt(0), 30.0 / days, np.nan),
        )
        valid = q.gt(0) & x.gt(0) & np.isfinite(factor)
        quantity += np.where(valid, q * factor, 0.0)
        expenditure += np.where(valid, x * factor, 0.0)
        valid_pairs += valid.to_numpy(dtype=np.int16)

    ids = frame["nhCode"].astype("string").str.strip()
    part = pd.DataFrame(
        {
            "household_id": ids,
            "data_year": year,
            "group": group,
            "purchased_quantity": quantity,
            "purchase_value": expenditure,
            "valid_item_pairs": valid_pairs,
        }
    )
    if part["household_id"].duplicated().any():
        raise RuntimeError(f"Duplicate household IDs in {path}")
    audit = {
        "year": year,
        "group": group,
        "module": path.name,
        "observations": len(part),
        "matched_item_fields": len(pairs),
        "invalid_negative_pairs": invalid_negative,
    }
    return part, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--final-audit", type=Path, required=True)
    args = parser.parse_args()

    parts: list[pd.DataFrame] = []
    audits: list[dict] = []
    for year in (2023, 2024):
        for group, modules in MODULES.items():
            for module in modules:
                part, audit = extract_module(args.source / str(year) / module, year, group)
                parts.append(part)
                audits.append(audit)

    long = pd.concat(parts, ignore_index=True)
    collapsed = (
        long.groupby(["household_id", "data_year", "group"], as_index=False)
        .agg(
            purchased_quantity=("purchased_quantity", "sum"),
            purchase_value=("purchase_value", "sum"),
            valid_item_pairs=("valid_item_pairs", "sum"),
        )
    )
    collapsed["unit_value"] = collapsed["purchase_value"] / collapsed["purchased_quantity"]
    invalid_uv = (
        collapsed["unit_value"].le(0)
        | collapsed["unit_value"].gt(200)
        | collapsed["valid_item_pairs"].eq(0)
    )
    collapsed.loc[invalid_uv, "unit_value"] = np.nan

    wide = collapsed.pivot(index=["household_id", "data_year"], columns="group")
    wide.columns = [
        (f"uv{group}" if measure == "unit_value" else f"{measure}{group}")
        for measure, group in wide.columns
    ]
    wide = wide.reset_index().sort_values(["household_id", "data_year"])
    expected = {
        "household_id",
        "data_year",
        *{f"uv{g}" for g in range(1, 7)},
        *{f"purchase_value{g}" for g in range(1, 7)},
        *{f"purchased_quantity{g}" for g in range(1, 7)},
        *{f"valid_item_pairs{g}" for g in range(1, 7)},
    }
    missing = expected.difference(wide.columns)
    if missing:
        raise RuntimeError(f"Missing output columns: {sorted(missing)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(args.output, index=False)
    pd.DataFrame(audits).to_csv(args.audit, index=False)

    final_rows = []
    for group in range(1, 7):
        values = wide[f"uv{group}"].dropna()
        final_rows.append(
            {
                "group": group,
                "households": len(wide),
                "positive_unit_values": len(values),
                "mean": values.mean(),
                "p50": values.quantile(0.5),
                "p99": values.quantile(0.99),
            }
        )
    pd.DataFrame(final_rows).to_csv(args.final_audit, index=False)


if __name__ == "__main__":
    main()
