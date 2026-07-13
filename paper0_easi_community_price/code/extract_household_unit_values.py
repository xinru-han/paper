#!/usr/bin/env python3
"""Rebuild six food-source quantities and validation unit values.

The item questionnaire distinguishes purchased food that was directly eaten
(question 04), home-produced food that was directly eaten (question 07), and
food received as a gift (question 09).  Question 02 is an acquisition quantity,
not a consumption quantity, and is retained only for purchase-unit-value
validation together with question 03 expenditure.
"""

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
        buyvar = qvar.replace("_laiyuan-02-", "_laiyuan-04-", 1)
        processvar = qvar.replace("_laiyuan-02-", "_laiyuan-21-", 1)
        if processvar not in names:
            processvar = None
        givevar = qvar.replace("_laiyuan-02-", "_laiyuan-05-", 1)
        spoilvar = qvar.replace("_laiyuan-02-", "_laiyuan-17-", 1)
        stockvar = qvar.replace("_laiyuan-02-", "_laiyuan-06-", 1)
        freqvar = qvar.replace("_laiyuan-02-", "_laiyuan-10-", 1)
        amountvar = qvar.replace("_laiyuan-02-", "_laiyuan-11-", 1)
        selfvar = qvar.replace("_laiyuan-02-", "_laiyuan-07-", 1)
        selfpricevar = qvar.replace("_laiyuan-02-", "_laiyuan-08-", 1)
        giftvar = qvar.replace("_laiyuan-02-", "_laiyuan-09-", 1)
        required = (
            xvar,
            fvar,
            buyvar,
            givevar,
            spoilvar,
            stockvar,
            freqvar,
            amountvar,
            selfvar,
            selfpricevar,
            giftvar,
        )
        if all(value in names for value in required):
            pairs.append(
                (
                    qvar,
                    xvar,
                    fvar,
                    buyvar,
                    processvar,
                    givevar,
                    spoilvar,
                    stockvar,
                    freqvar,
                    amountvar,
                    selfvar,
                    selfpricevar,
                    giftvar,
                )
            )
    if not pairs:
        raise RuntimeError(f"No matched 00/02/03 item fields in {path}")

    columns = ["nhCode", "freq_period_days"]
    columns.extend(value for pair in pairs for value in pair if value is not None)
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
    acquisition_quantity = np.zeros(len(frame), dtype=float)
    acquisition_value = np.zeros(len(frame), dtype=float)
    purchased_consumption = np.zeros(len(frame), dtype=float)
    purchase_direct_reported = np.zeros(len(frame), dtype=float)
    purchase_residual_fallback = np.zeros(len(frame), dtype=float)
    purchase_typical_fallback = np.zeros(len(frame), dtype=float)
    self_consumption = np.zeros(len(frame), dtype=float)
    gift_consumption = np.zeros(len(frame), dtype=float)
    self_reported_value = np.zeros(len(frame), dtype=float)
    self_price_covered_quantity = np.zeros(len(frame), dtype=float)
    valid_pairs = np.zeros(len(frame), dtype=np.int16)
    invalid_negative = 0
    invalid_self_price = 0

    for (
        qvar,
        xvar,
        fvar,
        buyvar,
        processvar,
        givevar,
        spoilvar,
        stockvar,
        freqvar,
        amountvar,
        selfvar,
        selfpricevar,
        giftvar,
    ) in pairs:
        q = numeric(frame[qvar])
        x = numeric(frame[xvar])
        q_buy = numeric(frame[buyvar])
        q_process = (
            numeric(frame[processvar])
            if processvar is not None
            else pd.Series(np.nan, index=frame.index, dtype=float)
        )
        q_given = numeric(frame[givevar])
        q_spoiled = numeric(frame[spoilvar])
        q_stocked = numeric(frame[stockvar])
        buy_frequency = numeric(frame[freqvar])
        buy_amount = numeric(frame[amountvar])
        q_self = numeric(frame[selfvar])
        p_self = numeric(frame[selfpricevar])
        q_gift = numeric(frame[giftvar])
        frequency = numeric(frame[fvar])
        invalid_negative += int(
            (
                (q < 0)
                | (x < 0)
                | (q_buy < 0)
                | (q_process < 0)
                | (q_given < 0)
                | (q_spoiled < 0)
                | (q_stocked < 0)
                | (buy_frequency < 0)
                | (buy_amount < 0)
                | (q_self < 0)
                | (q_gift < 0)
            )
            .fillna(False)
            .sum()
        )
        invalid_self_price += int(((p_self <= 0) | (p_self > 200)).fillna(False).sum())
        factor = np.where(
            frequency.eq(2),
            30.0 / 7.0,
            np.where(frequency.eq(1) & days.gt(0), 30.0 / days, np.nan),
        )
        factor_valid = np.isfinite(factor)
        acquisition_quantity += np.where(q.ge(0) & factor_valid, q * factor, 0.0)
        acquisition_value += np.where(x.ge(0) & factor_valid, x * factor, 0.0)
        direct_observed = q_buy.ge(0) & factor_valid
        residual = (
            q
            - q_process.fillna(0)
            - q_given.fillna(0)
            - q_spoiled.fillna(0)
            - q_stocked.fillna(0)
        ).clip(lower=0)
        residual_observed = (~direct_observed) & q.gt(0) & factor_valid
        typical = buy_frequency * buy_amount
        typical_observed = (
            (~direct_observed)
            & (~residual_observed)
            & buy_frequency.gt(0)
            & buy_amount.gt(0)
        )
        direct_month = np.where(direct_observed, q_buy * factor, 0.0)
        residual_month = np.where(residual_observed, residual * factor, 0.0)
        typical_month = np.where(typical_observed, typical, 0.0)
        purchase_direct_reported += direct_month
        purchase_residual_fallback += residual_month
        purchase_typical_fallback += typical_month
        purchased_consumption += direct_month + residual_month + typical_month
        self_consumption += np.where(
            q_self.gt(0) & factor_valid, q_self * factor, 0.0
        )
        gift_consumption += np.where(
            q_gift.gt(0) & factor_valid, q_gift * factor, 0.0
        )
        valid_self_price = q_self.gt(0) & p_self.gt(0) & p_self.le(200) & factor_valid
        self_reported_value += np.where(
            valid_self_price, q_self * p_self * factor, 0.0
        )
        self_price_covered_quantity += np.where(
            valid_self_price, q_self * factor, 0.0
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
            "purchase_acquisition_quantity": acquisition_quantity,
            "purchase_acquisition_value": acquisition_value,
            "purchase_consumed_quantity": purchased_consumption,
            "purchase_direct_quantity": purchase_direct_reported,
            "purchase_residual_quantity": purchase_residual_fallback,
            "purchase_typical_quantity": purchase_typical_fallback,
            "self_consumed_quantity": self_consumption,
            "gift_consumed_quantity": gift_consumption,
            "source_total_quantity": (
                purchased_consumption + self_consumption + gift_consumption
            ),
            "self_reported_value": self_reported_value,
            "self_price_covered_quantity": self_price_covered_quantity,
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
        "invalid_self_prices": invalid_self_price,
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
            purchase_acquisition_quantity=("purchase_acquisition_quantity", "sum"),
            purchase_acquisition_value=("purchase_acquisition_value", "sum"),
            purchase_consumed_quantity=("purchase_consumed_quantity", "sum"),
            purchase_direct_quantity=("purchase_direct_quantity", "sum"),
            purchase_residual_quantity=("purchase_residual_quantity", "sum"),
            purchase_typical_quantity=("purchase_typical_quantity", "sum"),
            self_consumed_quantity=("self_consumed_quantity", "sum"),
            gift_consumed_quantity=("gift_consumed_quantity", "sum"),
            source_total_quantity=("source_total_quantity", "sum"),
            self_reported_value=("self_reported_value", "sum"),
            self_price_covered_quantity=("self_price_covered_quantity", "sum"),
            valid_item_pairs=("valid_item_pairs", "sum"),
        )
    )
    collapsed["unit_value"] = collapsed["purchase_value"] / collapsed["purchased_quantity"]
    collapsed["self_unit_value"] = (
        collapsed["self_reported_value"] / collapsed["self_price_covered_quantity"]
    )
    invalid_uv = (
        collapsed["unit_value"].le(0)
        | collapsed["unit_value"].gt(200)
        | collapsed["valid_item_pairs"].eq(0)
    )
    collapsed.loc[invalid_uv, "unit_value"] = np.nan
    invalid_self_uv = (
        collapsed["self_unit_value"].le(0)
        | collapsed["self_unit_value"].gt(200)
        | collapsed["self_price_covered_quantity"].le(0)
    )
    collapsed.loc[invalid_self_uv, "self_unit_value"] = np.nan

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
        *{f"purchase_acquisition_quantity{g}" for g in range(1, 7)},
        *{f"purchase_acquisition_value{g}" for g in range(1, 7)},
        *{f"purchase_consumed_quantity{g}" for g in range(1, 7)},
        *{f"purchase_direct_quantity{g}" for g in range(1, 7)},
        *{f"purchase_residual_quantity{g}" for g in range(1, 7)},
        *{f"purchase_typical_quantity{g}" for g in range(1, 7)},
        *{f"self_consumed_quantity{g}" for g in range(1, 7)},
        *{f"gift_consumed_quantity{g}" for g in range(1, 7)},
        *{f"source_total_quantity{g}" for g in range(1, 7)},
        *{f"self_reported_value{g}" for g in range(1, 7)},
        *{f"self_price_covered_quantity{g}" for g in range(1, 7)},
        *{f"self_unit_value{g}" for g in range(1, 7)},
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
        self_values = wide[f"self_unit_value{group}"].dropna()
        final_rows.append(
            {
                "group": group,
                "households": len(wide),
                "positive_unit_values": len(values),
                "mean": values.mean(),
                "p50": values.quantile(0.5),
                "p99": values.quantile(0.99),
                "positive_self_unit_values": len(self_values),
                "self_price_mean": self_values.mean(),
                "self_price_p50": self_values.quantile(0.5),
                "self_price_p99": self_values.quantile(0.99),
                "purchase_consumed_mean": wide[
                    f"purchase_consumed_quantity{group}"
                ].mean(),
                "self_consumed_mean": wide[f"self_consumed_quantity{group}"].mean(),
                "gift_consumed_mean": wide[f"gift_consumed_quantity{group}"].mean(),
            }
        )
    pd.DataFrame(final_rows).to_csv(args.final_audit, index=False)


if __name__ == "__main__":
    main()
