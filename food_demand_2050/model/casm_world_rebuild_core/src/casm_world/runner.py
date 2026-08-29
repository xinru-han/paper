"""Diagnostic model runner.

The current command is a 2023 plumbing smoke test only.  It deliberately does
not expose an SSP command until drivers, estimated parameters, linked
processing, and validation gates are complete.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from casm_world.equilibrium import solve_equilibrium


def equilibrium_matrices(
    base: pd.DataFrame, commodity_order: list[str]
) -> tuple[list[str], np.ndarray, np.ndarray]:
    required = {"economy_id", "commodity", "supply_2023", "demand_2023"}
    if not required <= set(base.columns):
        raise ValueError(f"Missing calibrated-base columns: {sorted(required-set(base.columns))}")
    economies = sorted(base["economy_id"].astype(str).unique())
    index = pd.MultiIndex.from_product(
        [economies, commodity_order], names=["economy_id", "commodity"]
    )
    keyed = base.set_index(["economy_id", "commodity"])
    if not keyed.index.is_unique:
        raise ValueError("Calibrated base contains duplicate economy-product rows")
    keyed = keyed.reindex(index)
    if keyed[["supply_2023", "demand_2023"]].isna().any().any():
        raise ValueError("Calibrated base does not cover the full model matrix")
    supply = keyed["supply_2023"].to_numpy(float).reshape(len(economies), len(commodity_order))
    demand = keyed["demand_2023"].to_numpy(float).reshape(len(economies), len(commodity_order))
    return economies, supply, demand


def run_2023_smoke(base: pd.DataFrame, commodity_order: list[str]):
    """Verify that the balanced base reaches the generic solver unchanged."""

    economies, supply, demand = equilibrium_matrices(base, commodity_order)
    result = solve_equilibrium(
        supply,
        demand,
        supply_elasticity=0.30,
        demand_elasticity=-0.30,
        base_prices=1.0,
        region_names=economies,
        product_names=commodity_order,
        clearance_tolerance=1.0e-10,
    )
    return economies, result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.project_root.resolve()
    model_config = yaml.safe_load((root / "config/model.yaml").read_text(encoding="utf-8"))
    base = pd.read_csv(root / "data/processed/benchmark_equilibrium_interim_2023.csv")
    economies, result = run_2023_smoke(base, list(model_config["commodities"]))
    prices = pd.DataFrame(
        {
            "year": 2023,
            "commodity": result.product_names,
            "world_price_index": result.prices,
            "relative_market_residual": result.residuals,
        }
    )
    output = root / "outputs/smoke_2023_world_prices.csv"
    prices.to_csv(output, index=False)
    report = {
        "status": "diagnostic_smoke_test_not_a_scenario_projection",
        "economy_count": len(economies),
        "commodity_count": len(result.product_names),
        "max_relative_market_residual": result.max_abs_residual,
        "max_price_deviation_from_base": float(np.max(np.abs(result.prices - 1.0))),
        "output": str(output),
        "publishable": False,
    }
    (root / "outputs/smoke_2023_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

