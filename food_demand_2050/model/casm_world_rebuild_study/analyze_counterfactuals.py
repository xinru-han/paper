"""Build audited economy, region, nutrition and GHG diet contrasts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from casm_world.analysis import aggregate_solved_results, load_analysis_config  # noqa: E402
from casm_world.ghg import postsolve as ghg_postsolve  # noqa: E402
from casm_world.reporting import (  # noqa: E402
    aggregate_model_account_values,
    aggregate_source_geography_values,
)


DEFAULT_CONFIG = Path(__file__).with_name("config.yaml")
PRIMARY_BASKET = [
    "RIC",
    "WHE",
    "CRN",
    "OCG",
    "SBS",
    "NBS",
    "RBS",
    "SCA",
    "SBE",
    "BFV",
    "PRK",
    "PLM",
    "MLK",
]
QUANTITY_COLUMNS = [
    "primary_supply_mt",
    "processing_supply_mt",
    "production_mt",
    "food_demand_mt",
    "final_demand_mt",
    "processing_demand_mt",
    "demand_mt",
    "net_import_mt",
]


def _project_path(value: str) -> Path:
    path = (PROJECT_ROOT / value).resolve()
    path.relative_to(PROJECT_ROOT)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _add_scenario_parts(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    split = result["scenario"].astype(str).str.split("__", n=1, expand=True)
    if split.shape[1] != 2 or split.isna().any().any():
        raise ValueError("Counterfactual scenario must be BASE_SSP__DIET_PATHWAY")
    if "base_ssp" in result:
        if not result["base_ssp"].astype(str).eq(split[0]).all():
            raise ValueError("base_ssp disagrees with compound scenario")
    else:
        result.insert(1, "base_ssp", split[0].to_numpy())
    if "diet_pathway" in result:
        if not result["diet_pathway"].astype(str).eq(split[1]).all():
            raise ValueError("diet_pathway disagrees with compound scenario")
    else:
        result.insert(2, "diet_pathway", split[1].to_numpy())
    return result


def _paired_contrast(
    frame: pd.DataFrame,
    *,
    id_columns: Sequence[str],
    value_columns: Sequence[str],
    baseline_pathway: str = "BASELINE",
    denominator_floor: float = 1.0e-9,
) -> pd.DataFrame:
    keys = [column for column in id_columns if column != "diet_pathway"]
    base = frame[frame["diet_pathway"].eq(baseline_pathway)][
        [*keys, *value_columns]
    ].copy()
    base = base.rename(columns={column: f"{column}_baseline" for column in value_columns})
    alternatives = frame[~frame["diet_pathway"].eq(baseline_pathway)][
        [*id_columns, *value_columns]
    ].copy()
    merged = alternatives.merge(base, on=keys, how="left", validate="many_to_one")
    if merged[[f"{column}_baseline" for column in value_columns]].isna().any().any():
        raise ValueError("A counterfactual row lacks its same-SSP baseline")
    for column in value_columns:
        baseline = merged[f"{column}_baseline"]
        merged[f"{column}_change"] = merged[column] - baseline
        merged[f"{column}_change_percent"] = np.where(
            baseline.abs().gt(denominator_floor),
            100.0 * (merged[column] / baseline - 1.0),
            np.nan,
        )
    return merged.sort_values(list(id_columns)).reset_index(drop=True)


def build_group_results(
    country: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    analysis_config = load_analysis_config(
        _project_path(config["inputs"]["analysis_config"])
    )
    model_membership = pd.read_csv(
        _project_path(config["inputs"]["model_membership"])
    )
    source_membership = pd.read_csv(
        _project_path(config["inputs"]["source_membership"])
    )
    weights = pd.read_csv(
        _project_path(config["inputs"]["source_allocation_weights"])
    )
    outputs: list[pd.DataFrame] = []
    for scenario in sorted(country["scenario"].unique()):
        selected = country[country["scenario"].eq(scenario)].copy()
        outputs.append(
            aggregate_solved_results(
                selected,
                model_membership,
                source_membership,
                weights,
                analysis_config,
            )
        )
        print(f"aggregated reporting groups for {scenario}")
    return _add_scenario_parts(pd.concat(outputs, ignore_index=True))


def build_ghg_tables(
    country: pd.DataFrame,
    config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    factors = pd.read_csv(_project_path(config["inputs"]["ghg_factors"]))
    detail = ghg_postsolve(
        country[["scenario", "year", "economy_id", "commodity", "production_mt"]],
        factors,
    )
    detail["covered_production_mt"] = detail["production_mt"].where(
        detail["coverage_status"].ne("noncovered"), 0.0
    )
    country_summary = (
        detail.groupby(["scenario", "year", "economy_id"], as_index=False)
        .agg(
            covered_production_mt=("covered_production_mt", "sum"),
            emissions_mtco2e=("emissions_mtco2e", "sum"),
        )
    )
    country_summary = _add_scenario_parts(country_summary)

    model_membership = pd.read_csv(
        _project_path(config["inputs"]["model_membership"])
    )
    source_membership = pd.read_csv(
        _project_path(config["inputs"]["source_membership"])
    )
    weights = pd.read_csv(
        _project_path(config["inputs"]["source_allocation_weights"]),
        usecols=["accounting_target", "source_economy_id", "commodity", "supply_weight"],
    )
    values = ["covered_production_mt", "emissions_mtco2e"]
    account_groups = aggregate_model_account_values(
        detail,
        model_membership,
        value_columns=values,
        dimension_columns=("scenario", "year", "commodity"),
        entity_column="economy_id",
    )
    source = detail.merge(
        weights,
        left_on=["economy_id", "commodity"],
        right_on=["accounting_target", "commodity"],
        how="left",
        validate="many_to_many",
    )
    if source["source_economy_id"].isna().any():
        raise ValueError("GHG rows lack source-geography allocation weights")
    for column in values:
        source[column] = source[column] * source["supply_weight"]
    source_groups = aggregate_source_geography_values(
        source,
        source_membership,
        value_columns=values,
        dimension_columns=("scenario", "year", "commodity"),
        entity_column="source_economy_id",
    )
    group_by_product = pd.concat([account_groups, source_groups], ignore_index=True)
    group = _add_scenario_parts(
        group_by_product.groupby(
            ["scenario", "year", "group_system", "group_code", "group_name"],
            as_index=False,
        )[values].sum()
    )
    world_country = country_summary.groupby(["scenario", "year"], as_index=False)[
        "emissions_mtco2e"
    ].sum()
    world_group = group[
        group["group_system"].eq("GLOBAL") & group["group_code"].eq("WORLD")
    ][["scenario", "year", "emissions_mtco2e"]]
    check = world_country.merge(
        world_group,
        on=["scenario", "year"],
        suffixes=("_country", "_group"),
        validate="one_to_one",
    )
    maximum_error = float(
        (check["emissions_mtco2e_country"] - check["emissions_mtco2e_group"]).abs().max()
    )
    if maximum_error > 1.0e-9:
        raise AssertionError(f"World GHG group conservation failed: {maximum_error}")
    return country_summary, group, {
        "status": "passed",
        "world_conservation_maximum_absolute_error_mtco2e": maximum_error,
        "coefficient_base_year": 2023,
        "boundary": "attributed biological farm-gate production emissions",
    }


def build_nutrition_tables(
    country: pd.DataFrame,
    config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    coefficients = pd.read_csv(
        _project_path(config["inputs"]["nutrition_coefficients"])
    )[
        [
            "commodity",
            "food_use",
            "source_class",
            "energy_kcal_per_kg",
            "protein_g_per_kg",
            "fat_g_per_kg",
        ]
    ]
    contributions = country[
        ["scenario", "base_ssp", "diet_pathway", "year", "economy_id", "commodity", "food_demand_mt"]
    ].merge(coefficients, on="commodity", how="left", validate="many_to_one")
    if contributions.isna().any().any():
        raise ValueError("Nutrition coefficient join contains missing values")
    nonfood = contributions["source_class"].eq("nonfood")
    maximum_nonfood = float(contributions.loc[nonfood, "food_demand_mt"].max())
    if maximum_nonfood > 1.0e-10:
        raise ValueError("A nonfood product has positive food demand")
    for output, coefficient in (
        ("energy_kcal", "energy_kcal_per_kg"),
        ("protein_g", "protein_g_per_kg"),
        ("fat_g", "fat_g_per_kg"),
    ):
        contributions[output] = (
            contributions["food_demand_mt"] * 1.0e9 * contributions[coefficient]
        )
    economy = contributions.groupby(
        ["scenario", "base_ssp", "diet_pathway", "year", "economy_id"],
        as_index=False,
    ).agg(
        food_demand_mt=("food_demand_mt", "sum"),
        energy_kcal=("energy_kcal", "sum"),
        protein_g=("protein_g", "sum"),
        fat_g=("fat_g", "sum"),
    )
    drivers = pd.read_csv(PROJECT_ROOT / "data/processed/ssp_drivers_2023_2050.csv")[
        ["scenario", "year", "economy_id", "population_million"]
    ].rename(columns={"scenario": "base_ssp"})
    economy = economy.merge(
        drivers,
        on=["base_ssp", "year", "economy_id"],
        how="left",
        validate="many_to_one",
    )
    if economy["population_million"].isna().any():
        raise ValueError("Nutrition rows lack SSP population")
    denominator = economy["population_million"] * 1.0e6 * 365.0
    economy["kcal_per_capita_day"] = economy["energy_kcal"] / denominator
    economy["protein_g_per_capita_day"] = economy["protein_g"] / denominator
    economy["fat_g_per_capita_day"] = economy["fat_g"] / denominator
    world = economy.groupby(
        ["scenario", "base_ssp", "diet_pathway", "year"], as_index=False
    ).agg(
        population_million=("population_million", "sum"),
        food_demand_mt=("food_demand_mt", "sum"),
        energy_kcal=("energy_kcal", "sum"),
        protein_g=("protein_g", "sum"),
        fat_g=("fat_g", "sum"),
    )
    world_denominator = world["population_million"] * 1.0e6 * 365.0
    world["kcal_per_capita_day"] = world["energy_kcal"] / world_denominator
    world["protein_g_per_capita_day"] = world["protein_g"] / world_denominator
    world["fat_g_per_capita_day"] = world["fat_g"] / world_denominator
    return economy, world, {
        "status": "passed",
        "maximum_nonfood_food_demand_mt": maximum_nonfood,
        "interpretation_scope": "model-covered edible commodity basket, not a complete diet",
    }


def _primary_basket_summary(group: pd.DataFrame) -> pd.DataFrame:
    selected = group[group["commodity"].isin(PRIMARY_BASKET)]
    keys = [
        "scenario",
        "base_ssp",
        "diet_pathway",
        "year",
        "group_system",
        "group_code",
        "group_name",
    ]
    return selected.groupby(keys, as_index=False).agg(
        primary_production_mt=("primary_supply_mt", "sum"),
        primary_food_demand_mt=("food_demand_mt", "sum"),
        primary_net_import_mt=("net_import_mt", "sum"),
    )


def _write_tables(
    tables_dir: Path,
    country_contrasts: pd.DataFrame,
    group_contrasts: pd.DataFrame,
    group: pd.DataFrame,
    ghg_group: pd.DataFrame,
    nutrition_economy: pd.DataFrame,
    nutrition_world: pd.DataFrame,
    prices: pd.DataFrame,
    sensitivity_prices: pd.DataFrame,
    config: dict,
) -> dict[str, Path]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    price_frame = prices[prices["year"].eq(2050)].copy()
    price_contrast = _paired_contrast(
        price_frame,
        id_columns=["base_ssp", "diet_pathway", "commodity"],
        value_columns=["world_price_index_2023"],
    )
    price_contrast = price_contrast.rename(
        columns={
            "world_price_index_2023": "world_price_index_2050_2023eq1",
            "world_price_index_2023_baseline": "world_price_index_2050_2023eq1_baseline",
            "world_price_index_2023_change": "world_price_index_2050_2023eq1_change",
            "world_price_index_2023_change_percent": "world_price_index_2050_change_percent",
        }
    )
    paths["world_price_impacts"] = tables_dir / "table1_world_price_impacts_2050.csv"
    price_contrast.to_csv(paths["world_price_impacts"], index=False, lineterminator="\n")

    china = country_contrasts[
        country_contrasts["base_ssp"].eq(config["central_ssp"])
        & country_contrasts["economy_id"].eq("CHN")
    ].copy()
    paths["china_impacts"] = tables_dir / "table2_china_impacts_ssp2_2050.csv"
    china.to_csv(paths["china_impacts"], index=False, lineterminator="\n")

    focus_systems = {
        "GLOBAL",
        "FOCUS",
        "ECONOMIC",
        "WB_INCOME_FY25",
        "WB_DEVELOPMENT_STATUS",
        "UN_REGION",
        "UN_SPECIAL_GROUP",
    }
    regions = group_contrasts[
        group_contrasts["base_ssp"].eq(config["central_ssp"])
        & group_contrasts["group_system"].isin(focus_systems)
    ].copy()
    paths["regional_impacts"] = tables_dir / "table3_region_economic_group_impacts_ssp2_2050.csv"
    regions.to_csv(paths["regional_impacts"], index=False, lineterminator="\n")

    central = country_contrasts[
        country_contrasts["base_ssp"].eq(config["central_ssp"])
        & ~country_contrasts["economy_id"].eq("CHN")
        & country_contrasts["production_mt_baseline"].gt(0.1)
    ].copy()
    central["absolute_production_change_mt"] = central["production_mt_change"].abs()
    top = (
        central.sort_values("absolute_production_change_mt", ascending=False)
        .groupby("diet_pathway", as_index=False, group_keys=False)
        .head(40)
    )
    paths["economy_impacts"] = tables_dir / "table4_largest_economy_product_impacts_ssp2_2050.csv"
    top.to_csv(paths["economy_impacts"], index=False, lineterminator="\n")

    ghg_contrast = _paired_contrast(
        ghg_group[ghg_group["year"].eq(2050)],
        id_columns=[
            "base_ssp",
            "diet_pathway",
            "group_system",
            "group_code",
            "group_name",
        ],
        value_columns=["covered_production_mt", "emissions_mtco2e"],
    )
    paths["ghg_impacts"] = tables_dir / "table5_ghg_impacts_2050.csv"
    ghg_contrast.to_csv(paths["ghg_impacts"], index=False, lineterminator="\n")

    nutrition_values = [
        "food_demand_mt",
        "kcal_per_capita_day",
        "protein_g_per_capita_day",
        "fat_g_per_capita_day",
    ]
    china_nutrition = _paired_contrast(
        nutrition_economy[
            nutrition_economy["year"].eq(2050)
            & nutrition_economy["economy_id"].eq("CHN")
        ],
        id_columns=["base_ssp", "diet_pathway", "economy_id"],
        value_columns=nutrition_values,
    )
    world_nutrition = _paired_contrast(
        nutrition_world[nutrition_world["year"].eq(2050)],
        id_columns=["base_ssp", "diet_pathway"],
        value_columns=nutrition_values,
    )
    nutrition = pd.concat(
        [
            china_nutrition.assign(aggregation="China"),
            world_nutrition.assign(economy_id="WORLD", aggregation="World"),
        ],
        ignore_index=True,
        sort=False,
    )
    paths["nutrition_impacts"] = tables_dir / "table6_model_covered_nutrition_impacts_2050.csv"
    nutrition.to_csv(paths["nutrition_impacts"], index=False, lineterminator="\n")

    sp = sensitivity_prices.copy()
    sensitivity_contrast = _paired_contrast(
        sp,
        id_columns=[
            "response_variant",
            "demand_model_form",
            "base_ssp",
            "diet_pathway",
            "commodity",
        ],
        value_columns=["world_price_index_2023"],
    )
    sensitivity_contrast = sensitivity_contrast.rename(
        columns={
            "world_price_index_2023": "world_price_index_2050_2023eq1",
            "world_price_index_2023_baseline": "world_price_index_2050_2023eq1_baseline",
            "world_price_index_2023_change": "world_price_index_2050_2023eq1_change",
            "world_price_index_2023_change_percent": "world_price_index_2050_change_percent",
        }
    )
    paths["sensitivity"] = tables_dir / "table7_price_sensitivity_ssp2_2050.csv"
    sensitivity_contrast.to_csv(paths["sensitivity"], index=False, lineterminator="\n")

    primary = _primary_basket_summary(group)
    primary_contrast = _paired_contrast(
        primary[primary["year"].eq(2050)],
        id_columns=[
            "base_ssp",
            "diet_pathway",
            "group_system",
            "group_code",
            "group_name",
        ],
        value_columns=[
            "primary_production_mt",
            "primary_food_demand_mt",
            "primary_net_import_mt",
        ],
    )
    paths["primary_basket"] = tables_dir / "table8_primary_basket_group_impacts_2050.csv"
    primary_contrast.to_csv(paths["primary_basket"], index=False, lineterminator="\n")
    return paths


def _metric(
    table: pd.DataFrame,
    filters: dict,
    column: str,
) -> float:
    selected = table
    for key, value in filters.items():
        selected = selected[selected[key].eq(value)]
    if len(selected) != 1:
        raise ValueError(f"Expected one metric row for {filters}, found {len(selected)}")
    return float(selected.iloc[0][column])


def build_key_findings(
    tables: dict[str, Path],
    config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    prices = pd.read_csv(tables["world_price_impacts"])
    china = pd.read_csv(tables["china_impacts"])
    ghg = pd.read_csv(tables["ghg_impacts"])
    sensitivity = pd.read_csv(tables["sensitivity"])
    primary = pd.read_csv(tables["primary_basket"])
    ssp = str(config["central_ssp"])
    findings: list[dict] = []

    def add(metric_id: str, domain: str, label: str, value: float, unit: str, scope: str):
        findings.append(
            {
                "metric_id": metric_id,
                "domain": domain,
                "label": label,
                "value": value,
                "unit": unit,
                "scope": scope,
            }
        )

    for product, label in (
        ("PRK", "Pigmeat world price"),
        ("RIC", "Rice world price"),
        ("BFV", "Bovine-meat world price"),
        ("PLM", "Poultry-meat world price"),
        ("FMK", "Fluid-milk world price"),
        ("WDM", "Whole-milk-powder world price"),
    ):
        add(
            f"cgs_price_{product.lower()}",
            "world_market",
            label,
            _metric(
                prices,
                {"base_ssp": ssp, "diet_pathway": "CGS", "commodity": product},
                "world_price_index_2050_change_percent",
            ),
            "% vs same-SSP baseline",
            "SSP2, 2050",
        )
    for product, label in (("PRK", "Pigmeat"), ("RIC", "Rice"), ("FMK", "Fluid milk")):
        add(
            f"china_cgs_net_import_{product.lower()}",
            "china",
            f"China {label} net-import change",
            _metric(
                china,
                {"diet_pathway": "CGS", "commodity": product},
                "net_import_mt_change",
            ),
            "Mt",
            "SSP2, 2050",
        )

    world_ghg = _metric(
        ghg,
        {
            "base_ssp": ssp,
            "diet_pathway": "CGS",
            "group_system": "GLOBAL",
            "group_code": "WORLD",
        },
        "emissions_mtco2e_change",
    )
    china_ghg = _metric(
        ghg,
        {
            "base_ssp": ssp,
            "diet_pathway": "CGS",
            "group_system": "FOCUS",
            "group_code": "CHINA_MAINLAND",
        },
        "emissions_mtco2e_change",
    )
    add("world_cgs_ghg", "environment", "World farm-gate GHG change", world_ghg, "Mt CO2e", "SSP2, 2050")
    add("china_cgs_ghg", "environment", "China farm-gate GHG change", china_ghg, "Mt CO2e", "SSP2, 2050")
    add(
        "ex_china_cgs_ghg",
        "environment",
        "Outside-China farm-gate GHG change",
        world_ghg - china_ghg,
        "Mt CO2e",
        "SSP2, 2050",
    )

    world_primary = _metric(
        primary,
        {
            "base_ssp": ssp,
            "diet_pathway": "CGS",
            "group_system": "GLOBAL",
            "group_code": "WORLD",
        },
        "primary_production_mt_change",
    )
    add(
        "world_cgs_primary_production",
        "production",
        "World non-overlapping primary-basket production change",
        world_primary,
        "Mt",
        "SSP2, 2050",
    )

    cgs_sensitivity = sensitivity[
        sensitivity["base_ssp"].eq(ssp) & sensitivity["diet_pathway"].eq("CGS")
    ]
    sensitivity_ranges = {}
    for product in ("PRK", "RIC", "PLM", "FMK", "WDM"):
        values = cgs_sensitivity[cgs_sensitivity["commodity"].eq(product)][
            "world_price_index_2050_change_percent"
        ]
        sensitivity_ranges[product] = [float(values.min()), float(values.max())]
        add(
            f"cgs_price_sensitivity_range_{product.lower()}",
            "sensitivity",
            f"{product} CGS price-effect sensitivity range",
            float(values.max() - values.min()),
            "percentage-point range",
            "SSP2, 2050; low/central/high/CES",
        )

    findings_frame = pd.DataFrame.from_records(findings)
    claims = findings_frame.copy()
    claims.insert(0, "status", "pass")
    claims["source_table"] = "generated from audited counterfactual tables"
    claims["manuscript_use"] = "eligible with stated scope and conditional language"
    report = {
        "status": "passed",
        "central_ssp": ssp,
        "headline_pathway": "CGS",
        "world_ghg_change_mtco2e": world_ghg,
        "china_ghg_change_mtco2e": china_ghg,
        "outside_china_ghg_change_mtco2e": world_ghg - china_ghg,
        "world_primary_basket_production_change_mt": world_primary,
        "price_effect_sensitivity_ranges_percent": sensitivity_ranges,
        "interpretation_warning": (
            "CES model-form sensitivity changes the sign or magnitude of some product "
            "effects; no single price result is presented as model-form invariant."
        ),
    }
    return findings_frame, claims, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    outputs = {key: _project_path(value) for key, value in config["outputs"].items()}
    for path in outputs.values():
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)

    country = _add_scenario_parts(pd.read_csv(outputs["country_product"]))
    prices = _add_scenario_parts(pd.read_csv(outputs["world_prices"]))
    sensitivity_prices = _add_scenario_parts(
        pd.read_csv(outputs["sensitivity_world_prices"])
    )
    group = build_group_results(country, config)
    group.to_csv(outputs["group_results"], index=False, compression="gzip")

    country_2050 = country[country["year"].eq(2050)].copy()
    country_contrasts = _paired_contrast(
        country_2050,
        id_columns=["base_ssp", "diet_pathway", "economy_id", "commodity"],
        value_columns=QUANTITY_COLUMNS,
    )
    country_contrasts.to_csv(
        outputs["country_contrasts_2050"], index=False, compression="gzip"
    )
    group_2050 = group[group["year"].eq(2050)].copy()
    group_contrasts = _paired_contrast(
        group_2050,
        id_columns=[
            "base_ssp",
            "diet_pathway",
            "group_system",
            "group_code",
            "group_name",
            "commodity",
        ],
        value_columns=[*QUANTITY_COLUMNS, "other_final_demand_mt"],
    )
    group_contrasts.to_csv(
        outputs["group_contrasts_2050"], index=False, compression="gzip"
    )

    ghg_country, ghg_group, ghg_audit = build_ghg_tables(country, config)
    ghg_country.to_csv(outputs["ghg_country"], index=False, compression="gzip")
    ghg_group.to_csv(outputs["ghg_group"], index=False, compression="gzip")
    nutrition_economy, nutrition_world, nutrition_audit = build_nutrition_tables(
        country, config
    )
    nutrition_economy.to_csv(
        outputs["nutrition_economy"], index=False, compression="gzip"
    )
    nutrition_world.to_csv(outputs["nutrition_world"], index=False, lineterminator="\n")

    table_paths = _write_tables(
        outputs["tables_directory"],
        country_contrasts,
        group_contrasts,
        group,
        ghg_group,
        nutrition_economy,
        nutrition_world,
        prices,
        sensitivity_prices,
        config,
    )
    findings, claims, headline_report = build_key_findings(table_paths, config)
    findings.to_csv(outputs["key_findings"], index=False, lineterminator="\n")
    claims.to_csv(outputs["claims_registry"], index=False, lineterminator="\n")

    report = {
        "status": "passed",
        "study_id": config["study_id"],
        "scenario_type": config["interpretation"]["scenario_type"],
        "row_counts": {
            "country_product": int(len(country)),
            "group_results": int(len(group)),
            "country_contrasts_2050": int(len(country_contrasts)),
            "group_contrasts_2050": int(len(group_contrasts)),
            "ghg_country": int(len(ghg_country)),
            "ghg_group": int(len(ghg_group)),
            "nutrition_economy": int(len(nutrition_economy)),
            "nutrition_world": int(len(nutrition_world)),
        },
        "audits": {"ghg": ghg_audit, "nutrition": nutrition_audit},
        "headline": headline_report,
        "tables": {
            key: {"path": str(path), "sha256": _sha256(path)}
            for key, path in table_paths.items()
        },
        "limitations": {
            "excluded_food_groups": config["excluded_prior_casm_foods"],
            "bilateral_trade": "not modelled",
            "shared_crop_resource": "not implemented in source CASM-World rebuild",
            "world_model_publication_status": (
                "computationally valid diagnostic conditional model; source model "
                "publication validator passes 18 of 20 gates"
            ),
            "ghg": "frozen 2023 attributed farm-gate coefficients; not lifecycle emissions",
            "nutrition": "model-covered edible basket only; not diet adequacy or health outcomes",
        },
    }
    outputs["analysis_report"].write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {outputs['group_results']} ({len(group)} rows)")
    print(f"wrote {outputs['analysis_report']}")


if __name__ == "__main__":
    main()
