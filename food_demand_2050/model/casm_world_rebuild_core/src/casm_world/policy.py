"""Coarse non-bilateral tariff paths with an explicit post-2035 hold rule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from casm_world.benchmark import country_codebook
from casm_world.paths import load_source_catalog, verify_source


def latest_country_tariffs(payload: list, codebook: pd.DataFrame) -> pd.DataFrame:
    """Select each country's latest non-null WDI primary-product tariff."""

    if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[1], list):
        raise ValueError("Unexpected World Bank tariff API payload")
    rows = pd.DataFrame.from_records(payload[1])
    required = {"countryiso3code", "date", "value"}
    if not required <= set(rows):
        raise ValueError(f"Missing WDI tariff fields: {sorted(required-set(rows))}")
    rows = rows[rows["value"].notna()].copy()
    rows["economy_id"] = rows["countryiso3code"].astype(str).str.upper()
    rows["observation_year"] = pd.to_numeric(rows["date"], errors="coerce")
    rows["tariff_rate_percent"] = pd.to_numeric(rows["value"], errors="coerce")
    rows = rows[
        rows["observation_year"].between(2018, 2023)
        & rows["tariff_rate_percent"].between(0, 100)
    ]
    valid_codes = set(codebook["economy_id"])
    rows = rows[rows["economy_id"].isin(valid_codes)]
    rows = rows.sort_values(["economy_id", "observation_year"], ascending=[True, False])
    latest = rows.drop_duplicates("economy_id")[[
        "economy_id", "observation_year", "tariff_rate_percent"
    ]]
    metadata = codebook[["economy_id", "region_code"]].copy()
    return latest.merge(metadata, on="economy_id", how="left", validate="one_to_one")


def complete_tariff_reference(
    observed: pd.DataFrame,
    *,
    model_accounts: list[str],
    codebook: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """Complete missing model accounts using UN-region, then global medians."""

    required = {"economy_id", "observation_year", "tariff_rate_percent", "region_code"}
    if not required <= set(observed):
        raise ValueError(f"Missing tariff reference columns: {sorted(required-set(observed))}")
    global_median = float(observed["tariff_rate_percent"].median())
    region_medians = observed.groupby("region_code")["tariff_rate_percent"].median()
    geography = codebook.set_index("economy_id")
    tariff = observed.set_index("economy_id")
    records: list[dict] = []
    for account in sorted(set(model_accounts)):
        lookup = "TWN" if account == "OTHER_EASTERN_ASIA" else account
        if lookup in tariff.index:
            row = tariff.loc[lookup]
            value = float(row["tariff_rate_percent"])
            year = int(row["observation_year"])
            status = "observed_latest_wdi"
        else:
            region = geography.at[lookup, "region_code"] if lookup in geography.index else np.nan
            if pd.notna(region) and region in region_medians.index:
                value = float(region_medians.loc[region])
                status = "un_region_median_fallback"
            else:
                value = global_median
                status = "global_median_fallback"
            year = 0
        records.append(
            {
                "economy_id": account,
                "tariff_rate_percent_2023": value,
                "source_observation_year": year,
                "value_status": status,
            }
        )
    reference = pd.DataFrame.from_records(records)
    if reference["tariff_rate_percent_2023"].isna().any():
        raise ValueError("Tariff reference contains missing values")
    counts = reference["value_status"].value_counts().sort_index().to_dict()
    return reference, {"reference_status_counts": {key: int(value) for key, value in counts.items()}}


def build_tariff_paths(
    reference: pd.DataFrame,
    *,
    commodity_codes: list[str],
    scenario_multipliers: dict[str, float],
    years: range,
    target_year: int,
) -> tuple[pd.DataFrame, dict]:
    """Interpolate scenario rates to 2035 and hold the 2035 rate thereafter."""

    if 2023 not in years or target_year <= 2023 or max(years) < target_year:
        raise ValueError("Tariff path horizon is invalid")
    if len(commodity_codes) != len(set(commodity_codes)) or not commodity_codes:
        raise ValueError("Commodity codes must be non-empty and unique")
    records: list[dict] = []
    for row in reference.itertuples(index=False):
        base = float(row.tariff_rate_percent_2023)
        if not np.isfinite(base) or base < 0:
            raise ValueError("Tariff reference rates must be finite and non-negative")
        for scenario, multiplier in scenario_multipliers.items():
            if multiplier < 0:
                raise ValueError(f"Tariff multiplier cannot be negative: {scenario}")
            target = base * float(multiplier)
            for year in years:
                progress = min(max((year - 2023) / (target_year - 2023), 0.0), 1.0)
                rate = base + progress * (target - base)
                for commodity in commodity_codes:
                    records.append(
                        {
                            "scenario": scenario,
                            "economy_id": row.economy_id,
                            "commodity": commodity,
                            "year": year,
                            "tariff_rate_percent": rate,
                            "tariff_wedge": 1.0 + rate / 100.0,
                            "reference_status": row.value_status,
                        }
                    )
    paths = pd.DataFrame.from_records(records)
    if paths[["tariff_rate_percent", "tariff_wedge"]].isna().any().any():
        raise ValueError("Tariff paths contain missing values")
    held = paths[paths["year"].ge(target_year)].groupby(
        ["scenario", "economy_id", "commodity"]
    )["tariff_rate_percent"].nunique()
    if held.max() != 1:
        raise AssertionError("Every post-2035 tariff must equal its 2035 value")
    report = {
        "status": "complete_coarse_policy_wedge",
        "economy_count": int(reference["economy_id"].nunique()),
        "commodity_count": len(commodity_codes),
        "scenario_count": len(scenario_multipliers),
        "year_start": min(years),
        "year_end": max(years),
        "target_year": target_year,
        "post_target_rule": "hold_target_value_constant",
        "silent_zero_fill": False,
        "product_resolution": "uniform_country_primary_product_reference",
    }
    return paths, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.project_root.resolve()
    config = yaml.safe_load((root / "config/policy.yaml").read_text(encoding="utf-8"))
    model = yaml.safe_load((root / "config/model.yaml").read_text(encoding="utf-8"))
    catalog = load_source_catalog(root / "config/data_sources.yaml")
    for key in ("world_bank_primary_tariff", "un_m49"):
        verify_source(catalog.source(key))
    payload = json.loads(catalog.source("world_bank_primary_tariff").path.read_text(encoding="utf-8"))
    codebook = country_codebook(catalog.source("un_m49").path)
    observed = latest_country_tariffs(payload, codebook)
    base = pd.read_csv(root / "data/processed/benchmark_equilibrium_interim_2023.csv")
    reference, coverage = complete_tariff_reference(
        observed,
        model_accounts=base["economy_id"].unique().tolist(),
        codebook=codebook,
    )
    paths, report = build_tariff_paths(
        reference,
        commodity_codes=list(model["commodities"]),
        scenario_multipliers={
            key: float(value) for key, value in config["ssp_2035_multipliers"].items()
        },
        years=range(2023, int(config["projection_end"]) + 1),
        target_year=int(config["target_year"]),
    )
    report.update(coverage)
    observed.to_csv(root / "data/processed/tariff_observed_latest.csv", index=False)
    reference.to_csv(root / "data/processed/tariff_reference_2023.csv", index=False)
    paths.to_csv(root / "data/processed/tariff_paths_2023_2050.csv", index=False)
    (root / "data/processed/tariff_paths_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
