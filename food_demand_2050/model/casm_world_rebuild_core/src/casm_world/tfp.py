"""Agricultural TFP trend estimation and transparent SSP extensions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from casm_world.paths import load_source_catalog, verify_source


def estimate_tfp_rates(
    data: pd.DataFrame,
    *,
    start_year: int,
    end_year: int,
    country_weight: float,
    lower_bound: float,
    upper_bound: float,
) -> pd.DataFrame:
    required = {"ISO3", "Region", "Year", "Variable", "Value"}
    if not required <= set(data.columns):
        raise ValueError(f"Missing USDA TFP columns: {sorted(required-set(data.columns))}")
    if not 0 <= country_weight <= 1:
        raise ValueError("country_weight must lie in [0,1]")
    panel = data[
        data["Variable"].eq("TFP_Index")
        & data["Year"].between(start_year, end_year)
    ].copy()
    panel["Value"] = pd.to_numeric(panel["Value"], errors="coerce")
    panel = panel[panel["Value"].gt(0) & panel["ISO3"].notna()]
    records = []
    for iso3, group in panel.groupby("ISO3"):
        group = group.sort_values("Year").drop_duplicates("Year")
        if len(group) < 5:
            continue
        slope = float(np.polyfit(group["Year"].to_numpy(float), np.log(group["Value"]), 1)[0])
        records.append(
            {
                "economy_id": str(iso3).upper(),
                "usda_region": str(group["Region"].iloc[-1]),
                "raw_annual_log_rate": slope,
                "observations": int(len(group)),
            }
        )
    rates = pd.DataFrame.from_records(records)
    if rates.empty:
        raise ValueError("No country TFP trends could be estimated")
    region_median = rates.groupby("usda_region")["raw_annual_log_rate"].median()
    rates["regional_rate"] = rates["usda_region"].map(region_median)
    rates["annual_log_rate"] = (
        country_weight * rates["raw_annual_log_rate"]
        + (1.0 - country_weight) * rates["regional_rate"]
    ).clip(lower_bound, upper_bound)
    rates["rate_status"] = "country_regional_shrinkage"
    return rates.sort_values("economy_id").reset_index(drop=True)


def build_tfp_paths(
    rates: pd.DataFrame,
    *,
    model_accounts: list[str],
    scenario_multipliers: dict[str, float],
    years: range,
) -> tuple[pd.DataFrame, dict]:
    if 2023 not in years:
        raise ValueError("TFP path must contain the 2023 anchor")
    keyed = rates.set_index("economy_id")
    global_rate = float(rates["annual_log_rate"].median())
    records = []
    fallback_accounts = []
    for account in sorted(set(model_accounts)):
        lookup = "TWN" if account == "OTHER_EASTERN_ASIA" else account
        if lookup in keyed.index:
            rate = float(keyed.at[lookup, "annual_log_rate"])
            status = "estimated_usda"
        else:
            rate = global_rate
            status = "global_median_fallback"
            fallback_accounts.append(account)
        for scenario, multiplier in scenario_multipliers.items():
            if multiplier <= 0:
                raise ValueError(f"TFP multiplier must be positive for {scenario}")
            scenario_rate = rate * float(multiplier)
            for year in years:
                records.append(
                    {
                        "scenario": scenario,
                        "economy_id": account,
                        "year": year,
                        "tfp_index_2023": float(np.exp(scenario_rate * (year - 2023))),
                        "annual_log_rate": scenario_rate,
                        "value_status": status,
                    }
                )
    result = pd.DataFrame.from_records(records)
    if result["tfp_index_2023"].isna().any() or not np.isfinite(result["tfp_index_2023"]).all():
        raise ValueError("TFP paths contain missing or non-finite values")
    anchor = result[result["year"].eq(2023)]["tfp_index_2023"]
    if not np.allclose(anchor, 1.0):
        raise AssertionError("Every TFP path must equal one in 2023")
    report = {
        "model_account_count": len(set(model_accounts)),
        "scenario_count": len(scenario_multipliers),
        "year_start": min(years),
        "year_end": max(years),
        "estimated_account_count": len(set(model_accounts)) - len(set(fallback_accounts)),
        "fallback_account_count": len(set(fallback_accounts)),
        "fallback_accounts": sorted(set(fallback_accounts)),
        "status": "complete_with_explicit_fallbacks",
    }
    return result, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.project_root.resolve()
    config = yaml.safe_load((root / "config/tfp.yaml").read_text(encoding="utf-8"))
    catalog = load_source_catalog(root / "config/data_sources.yaml")
    source = catalog.source("usda_agricultural_tfp")
    verify_source(source)
    raw = pd.read_csv(source.path, low_memory=False)
    start, end = config["estimation_window"]
    low, high = config["annual_log_rate_bounds"]
    rates = estimate_tfp_rates(
        raw,
        start_year=int(start),
        end_year=int(end),
        country_weight=float(config["country_weight"]),
        lower_bound=float(low),
        upper_bound=float(high),
    )
    base = pd.read_csv(root / "data/processed/benchmark_equilibrium_interim_2023.csv")
    paths, report = build_tfp_paths(
        rates,
        model_accounts=base["economy_id"].unique().tolist(),
        scenario_multipliers={key: float(value) for key, value in config["ssp_rate_multipliers"].items()},
        years=range(2023, 2051),
    )
    rates.to_csv(root / "data/processed/tfp_estimated_rates_2023.csv", index=False)
    paths.to_csv(root / "data/processed/tfp_paths_2023_2050.csv", index=False)
    (root / "data/processed/tfp_paths_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

