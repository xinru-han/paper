#!/usr/bin/env python3
"""Extract the narrow household fields used by the Stata demand pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    columns = [
        "nhCode",
        "data_year",
        "prov",
        "vilLat",
        "vilLon",
        "HA0",
        "total_income_w",
        "monthly_expense_total",
    ]
    for member in range(1, 9):
        mm = f"{member:02d}"
        columns.extend(
            [
                f"family1_{mm}_HA1",
                f"family1_{mm}_HA2",
                f"family1_{mm}_HA3",
                f"family2_{mm}_HA10",
            ]
        )

    frame = pd.read_stata(
        args.input,
        columns=columns,
        convert_categoricals=False,
    )
    frame["nhCode"] = frame["nhCode"].astype("string").str.strip()
    for member in range(1, 9):
        date_name = f"family1_{member:02d}_HA3"
        frame[date_name] = frame[date_name].astype("string").fillna("")

    if frame.duplicated(["nhCode", "data_year"]).any():
        raise RuntimeError("Household ID and survey year are not unique")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_stata(args.output, write_index=False, version=118)


if __name__ == "__main__":
    main()
