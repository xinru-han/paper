"""Interim 2023 equilibrium calibration from the unbalanced audit table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


USE_ACCOUNTS = ["food", "feed", "processing", "other_use", "seed", "loss", "residual"]


def _pivot(observations: pd.DataFrame) -> pd.DataFrame:
    required = {"economy_id", "commodity", "role", "account", "unit", "value"}
    if not required <= set(observations.columns):
        raise ValueError(f"Missing benchmark columns: {sorted(required-set(observations.columns))}")
    balance = observations[
        observations["role"].eq("balance") & observations["unit"].eq("Mt")
    ].copy()
    if balance.empty:
        raise ValueError("No Mt balance observations")
    if not np.isfinite(pd.to_numeric(balance["value"], errors="coerce")).all():
        raise ValueError("Balance observations contain null or non-finite values")
    return balance.pivot_table(
        index=["economy_id", "commodity"],
        columns="account",
        values="value",
        aggfunc="sum",
    )


def _column(frame: pd.DataFrame, name: str) -> pd.Series:
    if name not in frame:
        return pd.Series(0.0, index=frame.index, dtype=float)
    return frame[name].fillna(0.0).astype(float)


def build_interim_equilibrium(
    observations: pd.DataFrame,
    *,
    commodity_codes: list[str],
    ddg_ratio: float,
) -> tuple[pd.DataFrame, dict]:
    """Create a globally clearing base for solver development.

    The result is explicitly interim: it does not claim that independent
    product scaling satisfies linked processing identities.
    """

    if not (0 < ddg_ratio < 2):
        raise ValueError("DDG/ethanol mass ratio is outside a plausible range")
    pivot = _pivot(observations)
    production = _column(pivot, "production")
    imports = _column(pivot, "imports")
    exports = _column(pivot, "exports")
    stock_change = _column(pivot, "stock_change")
    domestic = _column(pivot, "domestic_supply")
    uses = sum((_column(pivot, account) for account in USE_ACCOUNTS), start=production * 0)
    energy_production = _column(pivot, "energy_production")
    energy_consumption = _column(pivot, "energy_consumption")

    supply = production.copy()
    demand = domestic.where(domestic.gt(0), uses)
    availability = production + imports - exports - stock_change
    demand = demand.where(demand.gt(0), availability)

    index_commodity = pivot.index.get_level_values("commodity")
    bio = index_commodity.isin(["ETH", "BDI"])
    supply.loc[bio] = energy_production.loc[bio]
    demand.loc[bio] = energy_consumption.loc[bio]
    milk = index_commodity == "MLK"
    demand.loc[milk] = supply.loc[milk]
    fluid = index_commodity == "FMK"
    supply.loc[fluid] = demand.loc[fluid]

    base = pd.DataFrame(
        {
            "raw_supply": supply.clip(lower=0),
            "raw_demand": demand.clip(lower=0),
        }
    ).reset_index()

    # DDG is absent as a direct FAOSTAT tonne series.  It remains a transparent
    # derived row tied to ethanol until an external 2023 dataset is frozen.
    ethanol = base[base["commodity"].eq("ETH")].copy()
    ddg = ethanol[["economy_id"]].copy()
    ddg["commodity"] = "DDG"
    ddg["raw_supply"] = ethanol["raw_supply"].to_numpy() * ddg_ratio
    ddg["raw_demand"] = ddg["raw_supply"]
    base = pd.concat([base, ddg], ignore_index=True)

    economies = sorted(base["economy_id"].unique())
    full_index = pd.MultiIndex.from_product(
        [economies, commodity_codes], names=["economy_id", "commodity"]
    )
    base = (
        base.groupby(["economy_id", "commodity"], as_index=True)[
            ["raw_supply", "raw_demand"]
        ]
        .sum()
        .reindex(full_index, fill_value=0.0)
        .reset_index()
    )

    global_totals = base.groupby("commodity")[["raw_supply", "raw_demand"]].sum()
    invalid = global_totals[(global_totals["raw_supply"] <= 0) | (global_totals["raw_demand"] <= 0)]
    if not invalid.empty:
        raise ValueError(f"Products lack positive global supply or demand: {invalid.index.tolist()}")
    scales = global_totals["raw_supply"] / global_totals["raw_demand"]
    base["demand_scale"] = base["commodity"].map(scales)
    base["supply_2023"] = base["raw_supply"]
    base["demand_2023"] = base["raw_demand"] * base["demand_scale"]
    base["net_import_2023"] = base["demand_2023"] - base["supply_2023"]
    base["price_index_2023"] = 1.0
    base["structural_supply_zero"] = base["raw_supply"].eq(0)
    base["structural_demand_zero"] = base["raw_demand"].eq(0)

    check = base.groupby("commodity")["net_import_2023"].sum()
    if check.abs().max() > 1e-10:
        raise AssertionError("Interim benchmark does not clear globally")
    scale_deviation = (scales - 1.0).abs()
    report = {
        "status": "interim_solver_development_only",
        "economy_count": len(economies),
        "commodity_count": len(commodity_codes),
        "row_count": int(len(base)),
        "maximum_global_market_residual_mt": float(check.abs().max()),
        "maximum_demand_scale_deviation": float(scale_deviation.max()),
        "commodities_above_5pct_scaling": sorted(scale_deviation[scale_deviation > 0.05].index.tolist()),
        "ddg_ratio": ddg_ratio,
        "publishable": False,
        "next_gate": "joint_processing_and_weighted_constrained_balancing",
    }
    return base.sort_values(["economy_id", "commodity"]).reset_index(drop=True), report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.project_root.resolve()
    observations = pd.read_csv(root / "data/processed/benchmark_unbalanced_2023.csv")
    model_config = yaml.safe_load((root / "config/model.yaml").read_text(encoding="utf-8"))
    calibration = yaml.safe_load((root / "config/calibration.yaml").read_text(encoding="utf-8"))
    ddg_ratio = float(calibration["derived_products"]["DDG"]["output_mass_per_mass_ethanol"])
    base, report = build_interim_equilibrium(
        observations,
        commodity_codes=list(model_config["commodities"]),
        ddg_ratio=ddg_ratio,
    )
    output = root / "data/processed/benchmark_equilibrium_interim_2023.csv"
    base.to_csv(output, index=False)
    report["output"] = str(output)
    (root / "data/processed/benchmark_equilibrium_interim_report_2023.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
