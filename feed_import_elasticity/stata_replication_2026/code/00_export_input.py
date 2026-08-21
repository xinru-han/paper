#!/usr/bin/env python3
"""Convert audited revision checkpoints to a compact Stata input file.

No estimation is performed here. All demand-system estimation and testing is
performed by the Stata do-files in this directory.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINTS = ROOT / "revision_2026" / "checkpoints"
OUT = Path(__file__).resolve().parents[1] / "input"
PRODUCTS = ["corn", "sorghum", "cassava", "oats", "barley"]
CONTROLS = ["pork", "beef", "mutton", "poultry_meat", "eggs", "milk"]


def wide_prices() -> pd.DataFrame:
    prices = pd.read_parquet(CHECKPOINTS / "price_variants.parquet")
    prices = prices.loc[prices["price_measure"].eq("completed")]
    wide = prices.pivot(
        index=["province", "year_quarter"],
        columns="product",
        values="log_price_final",
    ).reset_index()
    return wide.rename(columns={p: f"lnp_{p}" for p in PRODUCTS})


def main() -> None:
    panel = pd.read_parquet(CHECKPOINTS / "panel_wide.parquet")
    keep = [
        "province",
        "year_quarter",
        "year",
        "total_import_expenditure_usd",
        "positive_budget_flag",
        "bartik_instrument",
        *CONTROLS,
    ]
    rename = {
        "province": "province_name",
        "total_import_expenditure_usd": "total_expenditure",
        "positive_budget_flag": "positive_budget",
        "bartik_instrument": "bartik",
    }
    for product in PRODUCTS:
        keep.extend(
            [
                f"budget_share__{product}",
                f"import_qty_kg__{product}",
                f"import_value_usd__{product}",
            ]
        )
        rename.update(
            {
                f"budget_share__{product}": f"w_{product}",
                f"import_qty_kg__{product}": f"q_{product}",
                f"import_value_usd__{product}": f"v_{product}",
            }
        )

    data = panel[keep].rename(columns=rename).merge(
        wide_prices(),
        left_on=["province_name", "year_quarter"],
        right_on=["province", "year_quarter"],
        validate="one_to_one",
    )
    data = data.drop(columns="province")
    data = data.sort_values(["province_name", "year_quarter"]).reset_index(drop=True)

    assert len(data) == 868
    assert int(data["positive_budget"].sum()) == 634
    assert not data[[f"lnp_{p}" for p in PRODUCTS]].isna().any().any()

    OUT.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUT / "feed_import_panel.csv", index=False, encoding="utf-8")
    print(f"Wrote {len(data)} rows to {OUT / 'feed_import_panel.csv'}")


if __name__ == "__main__":
    main()
