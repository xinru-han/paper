"""Historical real-exchange-rate trends and transparent SSP extensions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import yaml

from casm_world.benchmark import country_codebook
from casm_world.paths import load_source_catalog, verify_source


def _normalized_member(archive: zipfile.ZipFile) -> str:
    members = [name for name in archive.namelist() if name.endswith("All_Data_(Normalized).csv")]
    if len(members) != 1:
        raise ValueError("Expected one normalized all-data CSV in archive")
    return members[0]


def read_real_exchange_rate_panel(
    exchange_archive: Path,
    deflator_archive: Path,
    codebook: pd.DataFrame,
    *,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Return annual real LCU/USD indices from two FAOSTAT domains."""

    with zipfile.ZipFile(exchange_archive) as archive:
        with archive.open(_normalized_member(archive)) as stream:
            exchange = pd.read_csv(
                stream,
                usecols=[
                    "Area Code (M49)",
                    "Element Code",
                    "Year",
                    "Months Code",
                    "Value",
                ],
                low_memory=False,
            )
    # FAOSTAT's SLC series is redenomination-consistent and unique by country-
    # year. The LCU series can contain two currencies during a transition.
    exchange = exchange[
        exchange["Element Code"].astype(str).eq("SLC")
        & pd.to_numeric(exchange["Months Code"], errors="coerce").eq(7021)
        & pd.to_numeric(exchange["Year"], errors="coerce").between(start_year, end_year)
    ].copy()
    exchange["m49"] = (
        exchange["Area Code (M49)"].astype(str).str.strip().str.lstrip("'").str.zfill(3)
    )
    exchange["year"] = pd.to_numeric(exchange["Year"], errors="raise").astype(int)
    exchange["nominal_lcu_per_usd"] = pd.to_numeric(exchange["Value"], errors="coerce")
    exchange = exchange[["m49", "year", "nominal_lcu_per_usd"]]

    with zipfile.ZipFile(deflator_archive) as archive:
        with archive.open(_normalized_member(archive)) as stream:
            deflator = pd.read_csv(
                stream,
                usecols=[
                    "Area Code (M49)",
                    "Item Code",
                    "Element Code",
                    "Year",
                    "Value",
                ],
                low_memory=False,
            )
    deflator = deflator[
        pd.to_numeric(deflator["Item Code"], errors="coerce").eq(22024)
        & pd.to_numeric(deflator["Element Code"], errors="coerce").eq(62250)
        & pd.to_numeric(deflator["Year"], errors="coerce").between(start_year, end_year)
    ].copy()
    deflator["m49"] = (
        deflator["Area Code (M49)"].astype(str).str.strip().str.lstrip("'").str.zfill(3)
    )
    deflator["year"] = pd.to_numeric(deflator["Year"], errors="raise").astype(int)
    deflator["gdp_deflator"] = pd.to_numeric(deflator["Value"], errors="coerce")
    deflator = deflator[["m49", "year", "gdp_deflator"]]

    panel = exchange.merge(deflator, on=["m49", "year"], how="inner", validate="one_to_one")
    us = deflator[deflator["m49"].eq("840")][["year", "gdp_deflator"]].rename(
        columns={"gdp_deflator": "us_gdp_deflator"}
    )
    panel = panel.merge(us, on="year", how="inner", validate="many_to_one")
    panel = panel.merge(
        codebook[["m49", "economy_id"]], on="m49", how="inner", validate="many_to_one"
    )
    panel["real_lcu_per_usd"] = (
        panel["nominal_lcu_per_usd"]
        * panel["us_gdp_deflator"]
        / panel["gdp_deflator"]
    )
    valid = np.isfinite(panel["real_lcu_per_usd"]) & panel["real_lcu_per_usd"].gt(0)
    return panel.loc[valid, ["economy_id", "year", "real_lcu_per_usd"]].sort_values(
        ["economy_id", "year"]
    ).reset_index(drop=True)


def estimate_real_exchange_rates(
    panel: pd.DataFrame,
    *,
    minimum_observations: int,
    country_weight: float,
    lower_bound: float,
    upper_bound: float,
) -> pd.DataFrame:
    """Estimate bounded annual log trends with global-median shrinkage."""

    required = {"economy_id", "year", "real_lcu_per_usd"}
    if not required <= set(panel):
        raise ValueError(f"Missing exchange-rate columns: {sorted(required-set(panel))}")
    if minimum_observations < 2 or not 0 <= country_weight <= 1:
        raise ValueError("Invalid exchange-rate estimation settings")
    records: list[dict] = []
    for economy, group in panel.groupby("economy_id"):
        group = group.drop_duplicates("year").sort_values("year")
        if len(group) < minimum_observations:
            continue
        rate = float(
            np.polyfit(
                group["year"].to_numpy(float),
                np.log(group["real_lcu_per_usd"].to_numpy(float)),
                1,
            )[0]
        )
        records.append(
            {
                "economy_id": economy,
                "raw_annual_log_rate": rate,
                "observations": int(len(group)),
            }
        )
    rates = pd.DataFrame.from_records(records)
    if rates.empty:
        raise ValueError("No real-exchange-rate trends could be estimated")
    global_median = float(rates["raw_annual_log_rate"].median())
    rates["global_median_rate"] = global_median
    rates["annual_log_rate"] = (
        country_weight * rates["raw_annual_log_rate"]
        + (1.0 - country_weight) * global_median
    ).clip(lower_bound, upper_bound)
    rates["rate_status"] = "country_global_shrinkage"
    return rates.sort_values("economy_id").reset_index(drop=True)


def build_exchange_rate_paths(
    rates: pd.DataFrame,
    *,
    model_accounts: list[str],
    scenario_multipliers: dict[str, float],
    years: range,
    taper_end_year: int,
) -> tuple[pd.DataFrame, dict]:
    """Build 2023-normalized paths whose annual changes reach zero by a fixed year."""

    if 2023 not in years or taper_end_year <= 2023 or max(years) < taper_end_year:
        raise ValueError("Exchange-rate path or taper horizon is invalid")
    keyed = rates.set_index("economy_id")
    fallback_rate = float(rates["annual_log_rate"].median())
    records: list[dict] = []
    fallbacks: list[str] = []
    for account in sorted(set(model_accounts)):
        lookup = "TWN" if account == "OTHER_EASTERN_ASIA" else account
        if lookup in keyed.index:
            base_rate = float(keyed.at[lookup, "annual_log_rate"])
            status = "estimated_faostat"
        else:
            base_rate = fallback_rate
            status = "global_median_fallback"
            fallbacks.append(account)
        for scenario, multiplier in scenario_multipliers.items():
            if multiplier < 0:
                raise ValueError(f"Scenario persistence cannot be negative: {scenario}")
            log_index = 0.0
            for year in years:
                if year == 2023:
                    annual_rate = 0.0
                elif year <= taper_end_year:
                    remaining = (taper_end_year - year + 1) / (taper_end_year - 2023)
                    annual_rate = base_rate * float(multiplier) * remaining
                    log_index += annual_rate
                else:
                    annual_rate = 0.0
                records.append(
                    {
                        "scenario": scenario,
                        "economy_id": account,
                        "year": year,
                        "real_exchange_rate_index_2023": float(np.exp(log_index)),
                        "annual_log_change": annual_rate,
                        "value_status": status,
                    }
                )
    paths = pd.DataFrame.from_records(records)
    if not np.isfinite(paths["real_exchange_rate_index_2023"]).all():
        raise ValueError("Exchange-rate paths contain non-finite values")
    if not np.allclose(
        paths.loc[paths["year"].eq(2023), "real_exchange_rate_index_2023"], 1.0
    ):
        raise AssertionError("Every real exchange-rate path must equal one in 2023")
    held = paths[paths["year"].ge(taper_end_year)].groupby(
        ["scenario", "economy_id"]
    )["real_exchange_rate_index_2023"].nunique()
    if held.max() != 1:
        raise AssertionError("Post-taper exchange-rate levels must be held constant")
    report = {
        "status": "complete_with_explicit_author_assumptions",
        "model_account_count": len(set(model_accounts)),
        "scenario_count": len(scenario_multipliers),
        "year_start": min(years),
        "year_end": max(years),
        "taper_end_year": taper_end_year,
        "fallback_account_count": len(set(fallbacks)),
        "fallback_accounts": sorted(set(fallbacks)),
        "post_taper_rule": "hold_level_constant",
    }
    return paths, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.project_root.resolve()
    config = yaml.safe_load((root / "config/exchange_rates.yaml").read_text(encoding="utf-8"))
    catalog = load_source_catalog(root / "config/data_sources.yaml")
    for key in ("fao_exchange_rates", "fao_deflators", "un_m49"):
        verify_source(catalog.source(key))
    start, end = map(int, config["estimation_window"])
    panel = read_real_exchange_rate_panel(
        catalog.source("fao_exchange_rates").path,
        catalog.source("fao_deflators").path,
        country_codebook(catalog.source("un_m49").path),
        start_year=start,
        end_year=end,
    )
    low, high = map(float, config["annual_log_rate_bounds"])
    rates = estimate_real_exchange_rates(
        panel,
        minimum_observations=int(config["minimum_observations"]),
        country_weight=float(config["country_weight"]),
        lower_bound=low,
        upper_bound=high,
    )
    base = pd.read_csv(root / "data/processed/benchmark_equilibrium_interim_2023.csv")
    paths, report = build_exchange_rate_paths(
        rates,
        model_accounts=base["economy_id"].unique().tolist(),
        scenario_multipliers={
            key: float(value)
            for key, value in config["ssp_persistence_multipliers"].items()
        },
        years=range(2023, 2051),
        taper_end_year=int(config["taper_end_year"]),
    )
    rates.to_csv(root / "data/processed/real_exchange_rate_estimated_rates_2023.csv", index=False)
    paths.to_csv(root / "data/processed/real_exchange_rate_paths_2023_2050.csv", index=False)
    (root / "data/processed/real_exchange_rate_paths_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
