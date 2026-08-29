"""Agricultural greenhouse-gas accounting after the market solution.

The market model solves physical production.  This module does not feed back
into prices or quantities: it attaches a frozen 2023 FAOSTAT production-side
coefficient to each solved economy/product row and converts Mt of product to
Mt CO2e.  The boundary is deliberately narrower than FAOSTAT's complete farm-
gate inventory, and the inventory total is used only as an external validation
control, never as a balancing target.
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import zipfile

import numpy as np
import pandas as pd
import yaml

from casm_world.benchmark import country_codebook
from casm_world.concordance import load_concordance
from casm_world.geography import load_territory_config, territory_crosswalk
from casm_world.paths import load_source_catalog, sha256_file, verify_source


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "ghg.yaml"
ALLOWED_COVERAGE = frozenset({"direct", "inherited", "noncovered"})
FAOSTAT_INTENSITY_ELEMENTS = {
    723113: "emissions_ktco2e",
    71761: "reported_intensity",
    5510: "production_t",
}
OUTPUT_FACTOR_COLUMN = "coefficient_kgco2e_per_kg"


def load_ghg_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Load and validate the post-solution accounting contract."""

    config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schema_version") != "1.0":
        raise ValueError("ghg.yaml must be a schema_version 1.0 mapping")
    if int(config.get("benchmark_year", -1)) != 2023:
        raise ValueError("GHG coefficient benchmark year must be 2023")
    module = config.get("module", {})
    if module.get("execution_stage") != "post_solution":
        raise ValueError("GHG accounting must remain post_solution")
    if module.get("nitrogen_module_enabled") is not False:
        raise ValueError("The nitrogen module must remain disabled")
    expected_units = {
        "production_unit": "Mt",
        "intensity_unit": "kg CO2e/kg product",
        "emissions_unit": "Mt CO2e",
    }
    for key, expected in expected_units.items():
        if module.get(key) != expected:
            raise ValueError(f"Unexpected GHG unit {key}: {module.get(key)!r}")

    products = config.get("products")
    if not isinstance(products, dict) or len(products) != 31:
        raise ValueError("GHG boundary must define exactly 31 products")
    proxies = set(config.get("direct_intensity_proxies", {})) | set(
        config.get("crop_component_proxies", {})
    )
    for commodity, definition in products.items():
        if not isinstance(definition, dict):
            raise ValueError(f"Invalid GHG definition for {commodity}")
        status = definition.get("coverage_status")
        proxy = definition.get("proxy")
        if status not in ALLOWED_COVERAGE:
            raise ValueError(f"Invalid coverage status for {commodity}: {status}")
        if status == "noncovered" and proxy != "NONE":
            raise ValueError(f"Noncovered {commodity} must use proxy NONE")
        if status != "noncovered" and proxy not in proxies:
            raise ValueError(f"Unknown GHG proxy for {commodity}: {proxy}")

    crop_elements = config.get("crop_component_elements", {})
    expected_crop_elements = {72257, 72302, 72307}
    if {int(code) for code in crop_elements} != expected_crop_elements:
        raise ValueError("Crop component elements must be the four non-overlapping totals")
    # The residue total must replace, not accompany, its direct/indirect parts.
    forbidden_component_mix = {72342, 72362} & {int(code) for code in crop_elements}
    if forbidden_component_mix:
        raise ValueError("Crop-residue total cannot be added to its components")

    controls = config.get("validation_controls", {})
    if controls.get("farm_gate_total", {}).get("use") != "comparison_only":
        raise ValueError("FAOSTAT Farm gate total must be comparison_only")
    if config.get("boundary", {}).get("validation_rule") is None:
        raise ValueError("GHG validation boundary must be documented")

    scenario = config.get("scenario_postsolve", {})
    consumed = scenario.get("consumed_columns")
    if consumed != ["scenario", "year", "economy_id", "commodity", "production_mt"]:
        raise ValueError("Formal SSP GHG may consume only the five declared columns")
    if set(consumed) & set(scenario.get("forbidden_quantity_columns", [])):
        raise ValueError("A forbidden demand/trade quantity entered the SSP GHG input")
    if scenario.get("scenarios") != ["SSP1", "SSP2", "SSP3", "SSP4", "SSP5"]:
        raise ValueError("Formal GHG scenarios must be SSP1--SSP5")
    if (int(scenario.get("first_year", -1)), int(scenario.get("last_year", -1))) != (
        2023,
        2050,
    ):
        raise ValueError("Formal GHG years must be 2023--2050")
    if scenario.get("coefficient_rule") != "frozen_2023_production_side_coefficient":
        raise ValueError("Formal SSP GHG must use the frozen production-side coefficient")
    scenario_outputs = config.get("scenario_outputs", {})
    if set(scenario_outputs) != {"detail", "country", "product", "world", "audit"}:
        raise ValueError("Formal SSP GHG outputs are incomplete")
    return config


def _normalized_member(zipped: zipfile.ZipFile) -> str:
    names = [
        name
        for name in zipped.namelist()
        if "All_Data_" in name and name.endswith("(Normalized).csv")
    ]
    if len(names) != 1:
        raise ValueError("Expected exactly one normalized FAOSTAT data member")
    return names[0]


def _m49(value: object) -> str | None:
    text = str(value).strip().lstrip("'")
    if not text.isdigit():
        return None
    return text.zfill(3)


def _read_faostat_rows(
    archive: Path,
    *,
    year: int,
    item_codes: Iterable[int],
    element_codes: Iterable[int],
    allowed_m49: set[str],
    chunksize: int = 250_000,
) -> pd.DataFrame:
    """Stream one small item/element/year slice from a normalized archive."""

    wanted_items = {int(value) for value in item_codes}
    wanted_elements = {int(value) for value in element_codes}
    wanted_columns = {
        "Area Code (M49)",
        "Area",
        "Item Code",
        "Item",
        "Element Code",
        "Element",
        "Year",
        "Unit",
        "Value",
        "Flag",
    }
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(archive) as zipped:
        member = _normalized_member(zipped)
        with zipped.open(member) as stream:
            for chunk in pd.read_csv(
                stream,
                usecols=lambda column: column in wanted_columns,
                chunksize=chunksize,
                low_memory=False,
            ):
                item = pd.to_numeric(chunk["Item Code"], errors="coerce")
                element = pd.to_numeric(chunk["Element Code"], errors="coerce")
                years = pd.to_numeric(chunk["Year"], errors="coerce")
                keep = item.isin(wanted_items) & element.isin(wanted_elements) & years.eq(year)
                if not keep.any():
                    continue
                selected = chunk.loc[keep].copy()
                selected["m49"] = selected["Area Code (M49)"].map(_m49)
                selected = selected[selected["m49"].isin(allowed_m49)]
                if not selected.empty:
                    frames.append(selected)
    if not frames:
        return pd.DataFrame(
            columns=[*sorted(wanted_columns), "m49"]
        )
    result = pd.concat(frames, ignore_index=True)
    result["item_code"] = pd.to_numeric(result["Item Code"], errors="raise").astype(int)
    result["element_code"] = pd.to_numeric(
        result["Element Code"], errors="raise"
    ).astype(int)
    result["value"] = pd.to_numeric(result["Value"], errors="coerce").astype(float)
    # FAOSTAT retains explicit missing observations (normally Flag=M) as
    # rows with a blank Value. They are missing evidence, not physical zeros,
    # and therefore must fall through to the named regional/global hierarchy.
    result = result[result["value"].notna()].copy()
    if not np.isfinite(result["value"]).all() or (result["value"] < 0).any():
        raise ValueError(f"Non-finite or negative FAOSTAT values in {archive.name}")
    return result


def _account_geography(
    project_root: Path,
    catalog: Any,
    model_accounts: Sequence[str],
) -> tuple[pd.DataFrame, dict[str, str], set[str]]:
    codebook = country_codebook(catalog.source("un_m49").path).copy()
    allowed_m49 = set(codebook["m49"])
    territory_config = load_territory_config(
        project_root / "config" / "territory_aggregation.yaml"
    )
    target_map = territory_crosswalk(territory_config).set_index(
        "source_economy_id"
    )["accounting_target"].to_dict()
    codebook["accounting_target"] = codebook["economy_id"].map(target_map).fillna(
        codebook["economy_id"]
    )
    region_numeric = pd.to_numeric(codebook["region_code"], errors="coerce")
    codebook["un_region_code"] = region_numeric.map(
        lambda value: "000" if pd.isna(value) else f"{int(value):03d}"
    )
    codebook["un_region_name"] = codebook["region_name"].fillna("Unassigned")
    # The synthetic account is explicitly the accounting target for TWN.
    tw = codebook.loc[codebook["economy_id"].eq("TWN")].iloc[0].copy()
    synthetic = pd.DataFrame(
        [
            {
                "economy_id": "OTHER_EASTERN_ASIA",
                "un_region_code": tw["un_region_code"],
                "un_region_name": tw["un_region_name"],
            }
        ]
    )
    account_geo = codebook[
        ["economy_id", "un_region_code", "un_region_name"]
    ].copy()
    account_geo = pd.concat([account_geo, synthetic], ignore_index=True)
    account_geo = account_geo.drop_duplicates("economy_id", keep="first")
    requested = set(model_accounts)
    missing = requested - set(account_geo["economy_id"])
    if missing:
        raise ValueError(f"Missing UN region for model accounts: {sorted(missing)}")
    account_geo = account_geo[account_geo["economy_id"].isin(requested)].copy()
    if len(account_geo) != len(requested):
        raise AssertionError("Model account geography is not one-to-one")
    return account_geo, target_map, allowed_m49


def _attach_source_accounts(
    rows: pd.DataFrame,
    codebook: pd.DataFrame,
    target_map: Mapping[str, str],
) -> pd.DataFrame:
    result = rows.merge(
        codebook[["m49", "economy_id"]],
        on="m49",
        how="left",
        validate="many_to_one",
    )
    if result["economy_id"].isna().any():
        raise ValueError("FAOSTAT row could not be mapped to an ISO3 source economy")
    result["economy_id"] = result["economy_id"].map(target_map).fillna(
        result["economy_id"]
    )
    return result


def _direct_proxy_observations(
    archive: Path,
    config: Mapping[str, Any],
    codebook: pd.DataFrame,
    target_map: Mapping[str, str],
    allowed_m49: set[str],
    model_accounts: set[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    proxy_config = config["direct_intensity_proxies"]
    item_to_proxy: dict[int, str] = {}
    for proxy, definition in proxy_config.items():
        for item in definition["faostat_item_codes"]:
            code = int(item)
            if code in item_to_proxy:
                raise ValueError(f"Direct intensity item {code} belongs to two proxies")
            item_to_proxy[code] = proxy
    rows = _read_faostat_rows(
        archive,
        year=int(config["benchmark_year"]),
        item_codes=item_to_proxy,
        element_codes=FAOSTAT_INTENSITY_ELEMENTS,
        allowed_m49=allowed_m49,
    )
    rows = _attach_source_accounts(rows, codebook, target_map)
    rows["proxy_key"] = rows["item_code"].map(item_to_proxy)

    invalid_units = rows.loc[
        rows["element_code"].eq(723113) & rows["Unit"].ne("kt"), "Unit"
    ].unique()
    invalid_units = list(invalid_units) + list(
        rows.loc[
            rows["element_code"].eq(5510) & rows["Unit"].ne("t"), "Unit"
        ].unique()
    )
    invalid_units += list(
        rows.loc[
            rows["element_code"].eq(71761)
            & rows["Unit"].ne("kg CO2eq/kg"),
            "Unit",
        ].unique()
    )
    if invalid_units:
        raise ValueError(f"Unexpected FAOSTAT intensity units: {invalid_units}")

    source_keys = ["m49", "economy_id", "proxy_key", "item_code"]
    values = rows.pivot_table(
        index=source_keys,
        columns="element_code",
        values="value",
        aggfunc="sum",
    ).reset_index()
    values = values.rename(columns=FAOSTAT_INTENSITY_ELEMENTS)
    for column in FAOSTAT_INTENSITY_ELEMENTS.values():
        if column not in values:
            values[column] = np.nan
    usable = values[values["production_t"].gt(0)].copy()
    usable["effective_emissions_ktco2e"] = usable["emissions_ktco2e"]
    impute = usable["effective_emissions_ktco2e"].isna() & usable[
        "reported_intensity"
    ].notna()
    usable.loc[impute, "effective_emissions_ktco2e"] = (
        usable.loc[impute, "reported_intensity"]
        * usable.loc[impute, "production_t"]
        / 1000.0
    )
    usable = usable[usable["effective_emissions_ktco2e"].notna()].copy()

    consistency = usable[
        usable["emissions_ktco2e"].notna() & usable["reported_intensity"].notna()
    ].copy()
    consistency["recomputed"] = (
        consistency["emissions_ktco2e"] * 1000.0 / consistency["production_t"]
    )
    consistency["absolute_difference"] = (
        consistency["recomputed"] - consistency["reported_intensity"]
    ).abs()

    aggregated = (
        usable.groupby(["economy_id", "proxy_key"], as_index=False)
        .agg(
            source_emissions_ktco2e=("effective_emissions_ktco2e", "sum"),
            source_production_t=("production_t", "sum"),
            source_item_count=("item_code", "nunique"),
        )
    )
    aggregated = aggregated[aggregated["economy_id"].isin(model_accounts)].copy()
    aggregated[OUTPUT_FACTOR_COLUMN] = (
        aggregated["source_emissions_ktco2e"]
        * 1000.0
        / aggregated["source_production_t"]
    )
    diagnostics = {
        "source_rows": int(len(rows)),
        "usable_source_item_rows": int(len(usable)),
        "emissions_reconstructed_from_reported_intensity_rows": int(impute.sum()),
        "reported_intensity_consistency_rows": int(len(consistency)),
        "max_reported_vs_recomputed_absolute_difference": float(
            consistency["absolute_difference"].max() if len(consistency) else 0.0
        ),
    }
    return aggregated, diagnostics


def _crop_proxy_observations(
    crop_archive: Path,
    qcl_archive: Path,
    config: Mapping[str, Any],
    codebook: pd.DataFrame,
    target_map: Mapping[str, str],
    allowed_m49: set[str],
    model_accounts: set[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    proxies = config["crop_component_proxies"]
    item_to_proxy: dict[int, str] = {}
    production_elements: set[int] = set()
    for proxy, definition in proxies.items():
        production_elements.update(
            int(value) for value in definition["qcl_production_element_codes"]
        )
        for item in definition["faostat_item_codes"]:
            code = int(item)
            if code in item_to_proxy:
                raise ValueError(f"Crop item {code} belongs to two proxies")
            item_to_proxy[code] = proxy
    element_config = {
        int(code): definition
        for code, definition in config["crop_component_elements"].items()
    }
    gases = _read_faostat_rows(
        crop_archive,
        year=int(config["benchmark_year"]),
        item_codes=item_to_proxy,
        element_codes=element_config,
        allowed_m49=allowed_m49,
    )
    if not gases.empty and set(gases["Unit"]) != {"kt"}:
        raise ValueError("Selected crop emission process totals must be in kt of gas")
    gases = _attach_source_accounts(gases, codebook, target_map)
    gases["proxy_key"] = gases["item_code"].map(item_to_proxy)
    gases["gas"] = gases["element_code"].map(
        lambda code: element_config[int(code)]["gas"]
    )
    gwp = {str(key): float(value) for key, value in config["gwp100_ar5"].items()}
    gases["emissions_ktco2e"] = gases["value"] * gases["gas"].map(gwp)

    production = _read_faostat_rows(
        qcl_archive,
        year=int(config["benchmark_year"]),
        item_codes=item_to_proxy,
        element_codes=production_elements,
        allowed_m49=allowed_m49,
    )
    if not production.empty and set(production["Unit"]) != {"t"}:
        raise ValueError("Selected QCL crop production must be in t")
    production = _attach_source_accounts(production, codebook, target_map)
    production["proxy_key"] = production["item_code"].map(item_to_proxy)

    source_keys = ["m49", "economy_id", "proxy_key", "item_code"]
    emissions = gases.groupby(source_keys, as_index=False).agg(
        emissions_ktco2e=("emissions_ktco2e", "sum"),
        selected_process_count=("element_code", "nunique"),
    )
    quantities = production.groupby(source_keys, as_index=False).agg(
        production_t=("value", "sum")
    )
    usable = emissions.merge(
        quantities,
        on=source_keys,
        how="inner",
        validate="one_to_one",
    )
    usable = usable[usable["production_t"].gt(0)].copy()
    aggregated = (
        usable.groupby(["economy_id", "proxy_key"], as_index=False)
        .agg(
            source_emissions_ktco2e=("emissions_ktco2e", "sum"),
            source_production_t=("production_t", "sum"),
            source_item_count=("item_code", "nunique"),
        )
    )
    aggregated = aggregated[aggregated["economy_id"].isin(model_accounts)].copy()
    aggregated[OUTPUT_FACTOR_COLUMN] = (
        aggregated["source_emissions_ktco2e"]
        * 1000.0
        / aggregated["source_production_t"]
    )
    diagnostics = {
        "selected_gas_rows": int(len(gases)),
        "selected_qcl_production_rows": int(len(production)),
        "matched_source_item_rows": int(len(usable)),
        "selected_element_codes": sorted(element_config),
        "forbidden_residue_component_codes_used": sorted(
            {72342, 72362} & set(element_config)
        ),
    }
    return aggregated, diagnostics


def build_emission_factors(
    *,
    model_accounts: Sequence[str],
    commodity_codes: Sequence[str],
    account_geography: pd.DataFrame,
    proxy_observations: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    """Build a complete account/product coefficient table with named fallback."""

    accounts = sorted(set(str(value).strip().upper() for value in model_accounts))
    commodities = list(commodity_codes)
    if set(commodities) != set(config["products"]):
        raise ValueError("GHG products and model commodity concordance disagree")
    if account_geography["economy_id"].duplicated().any():
        raise ValueError("Account geography must be unique")
    geography = account_geography.set_index("economy_id")
    if set(accounts) != set(geography.index):
        raise ValueError("Account geography does not cover the factor universe")

    required_proxy = {"economy_id", "proxy_key", OUTPUT_FACTOR_COLUMN}
    if not required_proxy <= set(proxy_observations.columns):
        raise ValueError(f"Proxy observations are missing {sorted(required_proxy)}")
    proxy = proxy_observations[list(required_proxy)].copy()
    proxy["economy_id"] = proxy["economy_id"].astype(str).str.upper()
    proxy[OUTPUT_FACTOR_COLUMN] = pd.to_numeric(
        proxy[OUTPUT_FACTOR_COLUMN], errors="coerce"
    )
    valid = proxy[OUTPUT_FACTOR_COLUMN].map(
        lambda value: pd.notna(value) and isfinite(float(value)) and float(value) >= 0
    )
    if not valid.all():
        raise ValueError("Proxy coefficients must be finite and non-negative")
    if proxy.duplicated(["economy_id", "proxy_key"]).any():
        raise ValueError("Duplicate country/proxy coefficient")
    proxy = proxy.merge(
        account_geography,
        on="economy_id",
        how="left",
        validate="many_to_one",
    )

    country_values = proxy.set_index(["economy_id", "proxy_key"])[
        OUTPUT_FACTOR_COLUMN
    ].to_dict()
    region_stats = (
        proxy.groupby(["un_region_code", "proxy_key"], as_index=False)
        .agg(
            region_median=(OUTPUT_FACTOR_COLUMN, "median"),
            region_observation_count=(OUTPUT_FACTOR_COLUMN, "size"),
        )
        .set_index(["un_region_code", "proxy_key"])
    )
    global_stats = proxy.groupby("proxy_key", as_index=False).agg(
        global_median=(OUTPUT_FACTOR_COLUMN, "median"),
        global_observation_count=(OUTPUT_FACTOR_COLUMN, "size"),
    ).set_index("proxy_key")

    all_proxy_definitions = {
        **config["direct_intensity_proxies"],
        **config["crop_component_proxies"],
    }
    rows: list[dict[str, Any]] = []
    for account in accounts:
        region_code = str(geography.at[account, "un_region_code"])
        region_name = str(geography.at[account, "un_region_name"])
        for commodity in commodities:
            definition = config["products"][commodity]
            status = str(definition["coverage_status"])
            proxy_key = str(definition["proxy"])
            if status == "noncovered":
                country_available = False
                region_available = False
                country_value = region_value = global_value = selected = 0.0
                region_count = global_count = 0
                fallback_level = "not_applicable_noncovered"
                source_method = "not_attributed_at_product_boundary"
                source_items = "none"
            else:
                proxy_definition = all_proxy_definitions[proxy_key]
                source_method = str(proxy_definition["method"])
                source_items = ",".join(
                    str(int(value))
                    for value in proxy_definition["faostat_item_codes"]
                )
                country_key = (account, proxy_key)
                region_key = (region_code, proxy_key)
                country_available = country_key in country_values
                region_available = region_key in region_stats.index
                country_value = float(country_values.get(country_key, 0.0))
                if region_available:
                    region_value = float(region_stats.at[region_key, "region_median"])
                    region_count = int(
                        region_stats.at[region_key, "region_observation_count"]
                    )
                else:
                    region_value = 0.0
                    region_count = 0
                if proxy_key not in global_stats.index:
                    raise ValueError(f"No global fallback observations for {proxy_key}")
                global_value = float(global_stats.at[proxy_key, "global_median"])
                global_count = int(
                    global_stats.at[proxy_key, "global_observation_count"]
                )
                if country_available:
                    selected = country_value
                    fallback_level = "country"
                elif region_available:
                    selected = region_value
                    fallback_level = "un_region_median"
                else:
                    selected = global_value
                    fallback_level = "global_median"

            rows.append(
                {
                    "economy_id": account,
                    "commodity": commodity,
                    "coefficient_base_year": int(config["benchmark_year"]),
                    "coverage_status": status,
                    "boundary_role": str(definition["boundary_role"]),
                    "proxy_key": proxy_key,
                    "source_method": source_method,
                    "source_item_codes": source_items,
                    "inheritance": str(definition.get("inheritance", "none")),
                    "upstream_booked_to": str(
                        definition.get("upstream_booked_to", "none")
                    ),
                    "un_region_code": region_code,
                    "un_region_name": region_name,
                    "country_coefficient_available": bool(country_available),
                    "country_coefficient_kgco2e_per_kg": country_value,
                    "un_region_median_available": bool(region_available),
                    "un_region_median_kgco2e_per_kg": region_value,
                    "un_region_observation_count": region_count,
                    "global_median_kgco2e_per_kg": global_value,
                    "global_observation_count": global_count,
                    OUTPUT_FACTOR_COLUMN: selected,
                    "fallback_level": fallback_level,
                    "coefficient_unit": "kg CO2e/kg product",
                    "emission_boundary": str(config["boundary"]["name"]),
                }
            )
    factors = pd.DataFrame.from_records(rows)
    expected_rows = len(accounts) * len(commodities)
    numeric_columns = [
        "country_coefficient_kgco2e_per_kg",
        "un_region_median_kgco2e_per_kg",
        "global_median_kgco2e_per_kg",
        OUTPUT_FACTOR_COLUMN,
    ]
    if len(factors) != expected_rows or factors.duplicated(
        ["economy_id", "commodity"]
    ).any():
        raise AssertionError("Factor table is not a complete account/product rectangle")
    if factors.isna().any().any():
        raise AssertionError("Factor table contains NA after explicit fallback")
    if not np.isfinite(factors[numeric_columns].to_numpy(dtype=float)).all():
        raise AssertionError("Factor table contains non-finite values")
    if (factors[numeric_columns] < 0).any().any():
        raise AssertionError("Factor table contains a negative coefficient")
    return factors.sort_values(["economy_id", "commodity"]).reset_index(drop=True)


def postsolve(
    solved_production: pd.DataFrame,
    factors: pd.DataFrame,
    *,
    production_column: str = "production_mt",
) -> pd.DataFrame:
    """Apply frozen coefficients to solved production in Mt.

    Extra solution dimensions such as ``scenario`` and ``year`` are retained.
    Factors are joined only by model account and commodity, because their base
    year is metadata rather than a restriction on the projection year.
    """

    required = {"economy_id", "commodity", production_column}
    missing = required - set(solved_production.columns)
    if missing:
        raise ValueError(f"Solved production is missing: {sorted(missing)}")
    if solved_production[["economy_id", "commodity"]].isna().any().any():
        raise ValueError("Solved production identifiers must not be null")
    solution = solved_production.copy()
    solution["economy_id"] = solution["economy_id"].astype(str).str.strip().str.upper()
    solution["commodity"] = solution["commodity"].astype(str).str.strip().str.upper()
    quantity = pd.to_numeric(solution[production_column], errors="coerce")
    if quantity.isna().any() or not np.isfinite(quantity).all() or (quantity < 0).any():
        raise ValueError("Solved production must be finite, non-null and non-negative")
    solution[production_column] = quantity.astype(float)

    factor_columns = [
        "economy_id",
        "commodity",
        "coefficient_base_year",
        "coverage_status",
        "boundary_role",
        "fallback_level",
        OUTPUT_FACTOR_COLUMN,
        "coefficient_unit",
        "emission_boundary",
    ]
    if not set(factor_columns) <= set(factors.columns):
        raise ValueError("Emission-factor table lacks required postsolve columns")
    factor_slice = factors[factor_columns].copy()
    if factor_slice.duplicated(["economy_id", "commodity"]).any():
        raise ValueError("Emission-factor keys must be unique")
    result = solution.merge(
        factor_slice,
        on=["economy_id", "commodity"],
        how="left",
        validate="many_to_one",
    )
    if result[OUTPUT_FACTOR_COLUMN].isna().any():
        missing_keys = result.loc[
            result[OUTPUT_FACTOR_COLUMN].isna(), ["economy_id", "commodity"]
        ].drop_duplicates()
        raise ValueError(
            "Missing GHG coefficient for solved rows: "
            + str(missing_keys.to_dict("records")[:10])
        )
    result = result.rename(columns={production_column: "production_mt"})
    result["emissions_mtco2e"] = (
        result["production_mt"] * result[OUTPUT_FACTOR_COLUMN]
    )
    result["production_unit"] = "Mt"
    result["emissions_unit"] = "Mt CO2e"
    if result.isna().any().any():
        raise AssertionError("GHG postsolve output contains NA")
    if not np.isfinite(result["emissions_mtco2e"]).all() or (
        result["emissions_mtco2e"] < 0
    ).any():
        raise AssertionError("GHG postsolve output is not finite and non-negative")
    return result


def summarize_postsolve(
    postsolve_rows: pd.DataFrame,
    *,
    dimension_columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return additive country, product and world GHG summaries."""

    required = {
        "economy_id",
        "commodity",
        "production_mt",
        "coverage_status",
        "emissions_mtco2e",
    }
    if not required <= set(postsolve_rows.columns):
        raise ValueError(f"Postsolve rows are missing: {sorted(required-set(postsolve_rows))}")
    dimensions = list(dimension_columns) if dimension_columns is not None else [
        column for column in ("scenario", "year") if column in postsolve_rows.columns
    ]
    if len(dimensions) != len(set(dimensions)):
        raise ValueError("Summary dimensions must be unique")
    if not set(dimensions) <= set(postsolve_rows.columns):
        raise ValueError("A requested summary dimension is absent")
    data = postsolve_rows.copy()
    data["covered_production_mt"] = data["production_mt"].where(
        data["coverage_status"].ne("noncovered"), 0.0
    )

    def aggregate(level: str, keys: list[str]) -> pd.DataFrame:
        grouped = (
            data.groupby([*dimensions, *keys], as_index=False, dropna=False)
            .agg(
                covered_production_mt=("covered_production_mt", "sum"),
                emissions_mtco2e=("emissions_mtco2e", "sum"),
            )
        )
        grouped["aggregation_level"] = level
        if "economy_id" not in grouped:
            grouped["economy_id"] = "ALL"
        if "commodity" not in grouped:
            grouped["commodity"] = "ALL"
        denominator = grouped["covered_production_mt"]
        grouped["effective_intensity_kgco2e_per_kg"] = np.where(
            denominator.gt(0), grouped["emissions_mtco2e"] / denominator, 0.0
        )
        return grouped

    summaries = pd.concat(
        [
            aggregate("country", ["economy_id"]),
            aggregate("product", ["commodity"]),
            aggregate("world", []),
        ],
        ignore_index=True,
    )
    summaries["production_unit"] = "Mt"
    summaries["intensity_unit"] = "kg CO2e/kg product"
    summaries["emissions_unit"] = "Mt CO2e"
    ordered = [
        "aggregation_level",
        *dimensions,
        "economy_id",
        "commodity",
        "covered_production_mt",
        "effective_intensity_kgco2e_per_kg",
        "emissions_mtco2e",
        "production_unit",
        "intensity_unit",
        "emissions_unit",
    ]
    summaries = summaries[ordered]
    if summaries.isna().any().any():
        raise AssertionError("GHG summary contains NA")
    return summaries.sort_values(
        ["aggregation_level", *dimensions, "economy_id", "commodity"]
    ).reset_index(drop=True)


def _validation_control(
    archive: Path,
    definition: Mapping[str, Any],
    *,
    year: int,
    codebook: pd.DataFrame,
    target_map: Mapping[str, str],
    allowed_m49: set[str],
    model_accounts: set[str],
    gwp: Mapping[str, float],
    output_column: str,
) -> pd.DataFrame:
    elements = {int(code): str(gas) for code, gas in definition["elements"].items()}
    rows = _read_faostat_rows(
        archive,
        year=year,
        item_codes=[int(value) for value in definition["item_codes"]],
        element_codes=elements,
        allowed_m49=allowed_m49,
    )
    if not rows.empty and set(rows["Unit"]) != {"kt"}:
        raise ValueError(f"Validation control {output_column} must use kt")
    duplicate_keys = ["m49", "item_code", "element_code"]
    if rows.duplicated(duplicate_keys).any():
        raise ValueError(f"Duplicate FAOSTAT validation-control rows: {output_column}")
    rows = _attach_source_accounts(rows, codebook, target_map)
    rows["gas"] = rows["element_code"].map(elements)
    conversion = {**{str(key): float(value) for key, value in gwp.items()}, "CO2e": 1.0}
    rows[output_column] = rows["value"] * rows["gas"].map(conversion) / 1000.0
    result = rows.groupby("economy_id", as_index=False).agg(
        **{output_column: (output_column, "sum")}
    )
    return result[result["economy_id"].isin(model_accounts)].reset_index(drop=True)


def build_validation_table(
    *,
    project_root: Path,
    catalog: Any,
    config: Mapping[str, Any],
    codebook: pd.DataFrame,
    target_map: Mapping[str, str],
    allowed_m49: set[str],
    model_accounts: Sequence[str],
    baseline_postsolve: pd.DataFrame,
) -> pd.DataFrame:
    """Keep FAOSTAT totals as separate controls; never add them to factors."""

    accounts = set(model_accounts)
    gwp = config["gwp100_ar5"]
    controls = config["validation_controls"]
    frames: list[pd.DataFrame] = []
    column_sources = {
        "faostat_farm_gate_mtco2e": "fao_emissions_totals",
        "faostat_crops_control_mtco2e": "fao_emissions_crops",
        "faostat_livestock_control_mtco2e": "fao_emissions_livestock",
        "faostat_energy_unallocated_mtco2e": "fao_emissions_agriculture_energy",
    }
    definition_keys = {
        "faostat_farm_gate_mtco2e": "farm_gate_total",
        "faostat_crops_control_mtco2e": "crops_total",
        "faostat_livestock_control_mtco2e": "livestock_total",
        "faostat_energy_unallocated_mtco2e": "energy_total",
    }
    for column, source_key in column_sources.items():
        frames.append(
            _validation_control(
                catalog.source(source_key).path,
                controls[definition_keys[column]],
                year=int(config["benchmark_year"]),
                codebook=codebook,
                target_map=target_map,
                allowed_m49=allowed_m49,
                model_accounts=accounts,
                gwp=gwp,
                output_column=column,
            )
        )

    validation = pd.DataFrame({"economy_id": sorted(accounts)})
    for frame, column in zip(frames, column_sources):
        available_column = column.replace("_mtco2e", "_available")
        validation = validation.merge(frame, on="economy_id", how="left", validate="one_to_one")
        validation[available_column] = validation[column].notna()
        validation[column] = validation[column].fillna(0.0)
    modeled = baseline_postsolve.groupby("economy_id", as_index=False).agg(
        modeled_attributed_mtco2e=("emissions_mtco2e", "sum")
    )
    validation = validation.merge(modeled, on="economy_id", how="left", validate="one_to_one")
    validation["modeled_attributed_mtco2e"] = validation[
        "modeled_attributed_mtco2e"
    ].fillna(0.0)
    validation["modeled_minus_farm_gate_mtco2e"] = (
        validation["modeled_attributed_mtco2e"]
        - validation["faostat_farm_gate_mtco2e"]
    )
    denominator = validation["faostat_farm_gate_mtco2e"]
    validation["modeled_to_farm_gate_ratio"] = np.where(
        denominator.gt(0), validation["modeled_attributed_mtco2e"] / denominator, 0.0
    )
    validation["unit"] = "Mt CO2e"
    validation["farm_gate_is_validation_only"] = True
    validation["controls_are_not_added_together"] = True
    if validation.isna().any().any():
        raise AssertionError("GHG validation table contains NA")
    return validation


def build_ghg_module(project_root: str | Path = PROJECT_ROOT) -> dict[str, Any]:
    """Build factors, a 2023 postsolve audit and non-binding FAO validation."""

    root = Path(project_root).resolve()
    config = load_ghg_config(root / "config" / "ghg.yaml")
    concordance = load_concordance(root / "config" / "commodities.yaml")
    if set(config["products"]) != set(concordance["commodities"]):
        raise ValueError("GHG and commodity configurations do not cover the same 31 products")

    catalog = load_source_catalog(root / "config" / "data_sources.yaml")
    source_keys = [
        "fao_emissions_intensities",
        "fao_emissions_crops",
        "fao_emissions_livestock",
        "fao_emissions_agriculture_energy",
        "fao_emissions_totals",
        "fao_qcl",
        "un_m49",
    ]
    verified = {key: verify_source(catalog.source(key)) for key in source_keys}

    benchmark_path = root / "data" / "processed" / "benchmark_equilibrium_2023.csv"
    benchmark = pd.read_csv(benchmark_path)
    benchmark_required = {"economy_id", "commodity", "supply_2023"}
    if not benchmark_required <= set(benchmark.columns):
        raise ValueError("Balanced 2023 benchmark lacks production columns")
    accounts = sorted(benchmark["economy_id"].astype(str).str.upper().unique())
    commodities = list(concordance["commodities"])
    account_geo, target_map, allowed_m49 = _account_geography(root, catalog, accounts)
    codebook = country_codebook(catalog.source("un_m49").path)

    direct, direct_diagnostics = _direct_proxy_observations(
        catalog.source("fao_emissions_intensities").path,
        config,
        codebook,
        target_map,
        allowed_m49,
        set(accounts),
    )
    crop, crop_diagnostics = _crop_proxy_observations(
        catalog.source("fao_emissions_crops").path,
        catalog.source("fao_qcl").path,
        config,
        codebook,
        target_map,
        allowed_m49,
        set(accounts),
    )
    proxy_observations = pd.concat([direct, crop], ignore_index=True)
    if proxy_observations.duplicated(["economy_id", "proxy_key"]).any():
        raise AssertionError("Direct and crop proxy sources overlap")
    factors = build_emission_factors(
        model_accounts=accounts,
        commodity_codes=commodities,
        account_geography=account_geo,
        proxy_observations=proxy_observations,
        config=config,
    )

    production = benchmark[["economy_id", "commodity", "supply_2023"]].rename(
        columns={"supply_2023": "production_mt"}
    )
    production["year"] = int(config["benchmark_year"])
    baseline = postsolve(production, factors)
    aggregates = summarize_postsolve(baseline, dimension_columns=["year"])
    validation = build_validation_table(
        project_root=root,
        catalog=catalog,
        config=config,
        codebook=codebook,
        target_map=target_map,
        allowed_m49=allowed_m49,
        model_accounts=accounts,
        baseline_postsolve=baseline,
    )

    output_config = config["outputs"]
    output_paths = {key: root / value for key, value in output_config.items()}
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    factors.to_csv(output_paths["factors"], index=False)
    baseline.to_csv(output_paths["base_postsolve"], index=False)
    aggregates.to_csv(output_paths["base_aggregates"], index=False)
    validation.to_csv(output_paths["validation_table"], index=False)

    world = aggregates[aggregates["aggregation_level"].eq("world")]
    if len(world) != 1:
        raise AssertionError("Expected one 2023 world GHG summary")
    modeled_world = float(world["emissions_mtco2e"].iloc[0])
    fao_world = float(validation["faostat_farm_gate_mtco2e"].sum())
    status_counts = {
        str(key): int(value)
        for key, value in factors.groupby("coverage_status")["commodity"].nunique().items()
    }
    report: dict[str, Any] = {
        "benchmark_year": int(config["benchmark_year"]),
        "status": "passed_postsolution_accounting_not_calibrated_to_fao_total",
        "execution_stage": "post_solution",
        "nitrogen_module_enabled": False,
        "production_unit": "Mt",
        "intensity_unit": "kg CO2e/kg product",
        "emissions_unit": "Mt CO2e",
        "model_account_count": len(accounts),
        "commodity_count": len(commodities),
        "factor_row_count": int(len(factors)),
        "factor_table_has_na": bool(factors.isna().any().any()),
        "all_selected_coefficients_nonnegative": bool(
            factors[OUTPUT_FACTOR_COLUMN].ge(0).all()
        ),
        "coverage_product_counts": status_counts,
        "noncovered_products": sorted(
            factors.loc[factors["coverage_status"].eq("noncovered"), "commodity"].unique()
        ),
        "fallback_row_counts": {
            str(key): int(value)
            for key, value in factors["fallback_level"].value_counts().sort_index().items()
        },
        "direct_intensity_diagnostics": direct_diagnostics,
        "crop_component_diagnostics": crop_diagnostics,
        "selected_crop_elements_are_nonoverlapping_totals": True,
        "faostat_total_plus_components_was_never_computed": True,
        "energy_is_unallocated_validation_control": True,
        "farm_gate_validation_not_forced": True,
        "baseline_modeled_attributed_mtco2e": modeled_world,
        "faostat_farm_gate_validation_mtco2e": fao_world,
        "modeled_to_farm_gate_validation_ratio": (
            modeled_world / fao_world if fao_world > 0 else 0.0
        ),
        "separate_control_totals_mtco2e": {
            "crops": float(validation["faostat_crops_control_mtco2e"].sum()),
            "livestock": float(
                validation["faostat_livestock_control_mtco2e"].sum()
            ),
            "agricultural_energy_unallocated": float(
                validation["faostat_energy_unallocated_mtco2e"].sum()
            ),
        },
        "separate_controls_are_not_summed_or_added_to_postsolve": True,
        "verified_sources": {
            key: {
                "source_id": catalog.source(key).source_id,
                "sha256": digest,
            }
            for key, digest in verified.items()
        },
        "outputs": {key: str(path) for key, path in output_paths.items()},
        "interpretation": (
            "Product-attributed farm-gate post-solution account. Noncovered "
            "processed products carry zero to prevent upstream double counting; "
            "FAOSTAT farm-gate and component controls validate coverage only."
        ),
    }
    output_paths["report"].write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def validate_ssp_production_input(
    production: pd.DataFrame,
    factors: pd.DataFrame,
    scenario_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the formal SSP production rectangle before GHG accounting."""

    consumed = list(scenario_config["consumed_columns"])
    if list(production.columns) != consumed:
        raise ValueError(
            "SSP GHG input frame must contain only the declared consumed columns"
        )
    if production.isna().any().any():
        raise ValueError("Formal SSP production input contains NA")
    if production.duplicated(
        ["scenario", "year", "economy_id", "commodity"]
    ).any():
        raise ValueError("Formal SSP production keys are not unique")

    data = production.copy()
    data["scenario"] = data["scenario"].astype(str)
    data["economy_id"] = data["economy_id"].astype(str).str.strip().str.upper()
    data["commodity"] = data["commodity"].astype(str).str.strip().str.upper()
    years_numeric = pd.to_numeric(data["year"], errors="coerce")
    if years_numeric.isna().any() or not years_numeric.mod(1).eq(0).all():
        raise ValueError("Formal SSP years must be integers")
    data["year"] = years_numeric.astype(int)
    values = pd.to_numeric(data["production_mt"], errors="coerce")
    if values.isna().any() or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Formal SSP production_mt must be finite and non-negative")
    data["production_mt"] = values.astype(float)

    expected_scenarios = list(scenario_config["scenarios"])
    expected_years = list(
        range(
            int(scenario_config["first_year"]),
            int(scenario_config["last_year"]) + 1,
        )
    )
    factor_keys = factors[["economy_id", "commodity"]].drop_duplicates()
    expected_accounts = sorted(factor_keys["economy_id"].astype(str).unique())
    expected_commodities = sorted(factor_keys["commodity"].astype(str).unique())
    if len(expected_accounts) != int(scenario_config["expected_model_accounts"]):
        raise ValueError("Factor table does not contain 193 model accounts")
    if len(expected_commodities) != int(scenario_config["expected_commodities"]):
        raise ValueError("Factor table does not contain 31 commodities")
    if set(data["scenario"]) != set(expected_scenarios):
        raise ValueError("Formal SSP input does not contain exactly SSP1--SSP5")
    if set(data["year"]) != set(expected_years):
        raise ValueError("Formal SSP input does not contain every year 2023--2050")
    if set(data["economy_id"]) != set(expected_accounts):
        raise ValueError("Formal SSP account universe differs from the factor table")
    if set(data["commodity"]) != set(expected_commodities):
        raise ValueError("Formal SSP commodity universe differs from the factor table")

    expected_rows = (
        len(expected_scenarios)
        * len(expected_years)
        * len(expected_accounts)
        * len(expected_commodities)
    )
    if len(data) != expected_rows:
        raise ValueError(
            f"Formal SSP row count is {len(data)}, expected {expected_rows}"
        )
    block_sizes = data.groupby(["scenario", "year"], observed=True).size()
    expected_block = len(expected_accounts) * len(expected_commodities)
    if len(block_sizes) != len(expected_scenarios) * len(expected_years) or not block_sizes.eq(
        expected_block
    ).all():
        raise ValueError("A formal SSP scenario/year block is incomplete")
    account_sizes = data.groupby(
        ["scenario", "year", "economy_id"], observed=True
    ).size()
    if not account_sizes.eq(len(expected_commodities)).all():
        raise ValueError("A formal SSP account lacks one or more commodities")

    return {
        "row_count": int(len(data)),
        "scenario_count": len(expected_scenarios),
        "year_count": len(expected_years),
        "model_account_count": len(expected_accounts),
        "commodity_count": len(expected_commodities),
        "scenario_year_block_count": int(len(block_sizes)),
        "duplicate_key_count": 0,
        "na_count": 0,
        "negative_production_count": 0,
        "minimum_production_mt": float(data["production_mt"].min()),
        "maximum_production_mt": float(data["production_mt"].max()),
        "status": "passed",
    }


def _common_base_spread(
    frame: pd.DataFrame,
    *,
    value_column: str,
    base_year: int,
) -> float:
    base = frame[frame["year"].eq(base_year)]
    spread = base.groupby(["economy_id", "commodity"], observed=True)[
        value_column
    ].agg(lambda values: float(values.max() - values.min()))
    return float(spread.max() if len(spread) else 0.0)


def _baseline_difference(
    scenario_rows: pd.DataFrame,
    baseline_rows: pd.DataFrame,
    *,
    value_column: str,
    base_year: int,
) -> float:
    scenario_base = scenario_rows[scenario_rows["year"].eq(base_year)][
        ["scenario", "economy_id", "commodity", value_column]
    ]
    baseline = baseline_rows[["economy_id", "commodity", value_column]].copy()
    joined = scenario_base.merge(
        baseline,
        on=["economy_id", "commodity"],
        how="left",
        suffixes=("_scenario", "_baseline"),
        validate="many_to_one",
    )
    baseline_column = f"{value_column}_baseline"
    scenario_column = f"{value_column}_scenario"
    if joined[baseline_column].isna().any():
        raise ValueError("The rebuilt 2023 baseline does not cover formal SSP keys")
    return float((joined[scenario_column] - joined[baseline_column]).abs().max())


def _conservation_diagnostic(
    reference: pd.DataFrame,
    comparison: pd.DataFrame,
    *,
    value_column: str,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> dict[str, Any]:
    keys = ["scenario", "year"]
    left = reference[keys + [value_column]].rename(
        columns={value_column: "reference_value"}
    )
    right = comparison[keys + [value_column]].rename(
        columns={value_column: "comparison_value"}
    )
    joined = left.merge(right, on=keys, how="outer", validate="one_to_one")
    if joined.isna().any().any():
        raise ValueError("Conservation comparison has incomplete scenario/year coverage")
    difference = (joined["reference_value"] - joined["comparison_value"]).abs()
    scale = np.maximum(
        joined["reference_value"].abs(), joined["comparison_value"].abs()
    )
    allowed = absolute_tolerance + relative_tolerance * scale
    relative = np.where(scale.gt(0), difference / scale, 0.0)
    return {
        "max_absolute_difference_mtco2e": float(difference.max()),
        "max_relative_difference": float(np.max(relative)),
        "failing_scenario_year_count": int((difference > allowed).sum()),
        "passed": bool((difference <= allowed).all()),
    }


def run_formal_ssp_ghg(project_root: str | Path = PROJECT_ROOT) -> dict[str, Any]:
    """Apply the rebuilt 2023 factors to the formal SSP production results."""

    root = Path(project_root).resolve()
    config = load_ghg_config(root / "config" / "ghg.yaml")
    scenario_config = config["scenario_postsolve"]

    # This is intentionally first: a stale factor table cannot be attached to
    # newly balanced or rerun SSP production.
    baseline_report = build_ghg_module(root)
    factors_path = root / config["outputs"]["factors"]
    baseline_path = root / config["outputs"]["base_postsolve"]
    factors = pd.read_csv(factors_path)
    rebuilt_baseline = pd.read_csv(baseline_path)

    source_path = root / scenario_config["input"]
    consumed_columns = list(scenario_config["consumed_columns"])
    production = pd.read_csv(source_path, usecols=consumed_columns)
    # pandas preserves the requested source ordering for this archive, but
    # make the contract exact before validation rather than relying on it.
    production = production[consumed_columns]
    input_audit = validate_ssp_production_input(production, factors, scenario_config)

    detail = postsolve(production, factors, production_column="production_mt")
    detail_columns = [
        "scenario",
        "year",
        "economy_id",
        "commodity",
        "production_mt",
        "coefficient_base_year",
        "coverage_status",
        "boundary_role",
        "fallback_level",
        OUTPUT_FACTOR_COLUMN,
        "emissions_mtco2e",
        "production_unit",
        "coefficient_unit",
        "emissions_unit",
        "emission_boundary",
    ]
    detail = detail[detail_columns].sort_values(
        ["scenario", "year", "economy_id", "commodity"]
    ).reset_index(drop=True)
    summaries = summarize_postsolve(
        detail, dimension_columns=["scenario", "year"]
    )
    country = summaries[summaries["aggregation_level"].eq("country")].reset_index(
        drop=True
    )
    product = summaries[summaries["aggregation_level"].eq("product")].reset_index(
        drop=True
    )
    world = summaries[summaries["aggregation_level"].eq("world")].reset_index(
        drop=True
    )

    base_year = int(scenario_config["first_year"])
    base_tolerance = float(scenario_config["base_absolute_tolerance_mt"])
    production_spread = _common_base_spread(
        detail, value_column="production_mt", base_year=base_year
    )
    emissions_spread = _common_base_spread(
        detail, value_column="emissions_mtco2e", base_year=base_year
    )
    baseline_production_difference = _baseline_difference(
        detail,
        rebuilt_baseline,
        value_column="production_mt",
        base_year=base_year,
    )
    baseline_emissions_difference = _baseline_difference(
        detail,
        rebuilt_baseline,
        value_column="emissions_mtco2e",
        base_year=base_year,
    )
    base_passed = max(
        production_spread,
        emissions_spread,
        baseline_production_difference,
        baseline_emissions_difference,
    ) <= base_tolerance
    if not base_passed:
        raise AssertionError(
            "Formal SSP 2023 rows do not reproduce one common rebuilt baseline"
        )

    reference = detail.groupby(["scenario", "year"], as_index=False).agg(
        emissions_mtco2e=("emissions_mtco2e", "sum")
    )
    country_totals = country.groupby(["scenario", "year"], as_index=False).agg(
        emissions_mtco2e=("emissions_mtco2e", "sum")
    )
    product_totals = product.groupby(["scenario", "year"], as_index=False).agg(
        emissions_mtco2e=("emissions_mtco2e", "sum")
    )
    world_totals = world[["scenario", "year", "emissions_mtco2e"]]
    absolute_tolerance = float(
        scenario_config["conservation_absolute_tolerance_mtco2e"]
    )
    relative_tolerance = float(scenario_config["conservation_relative_tolerance"])
    conservation = {
        "country_sum_vs_detail": _conservation_diagnostic(
            reference,
            country_totals,
            value_column="emissions_mtco2e",
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
        ),
        "product_sum_vs_detail": _conservation_diagnostic(
            reference,
            product_totals,
            value_column="emissions_mtco2e",
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
        ),
        "world_vs_detail": _conservation_diagnostic(
            reference,
            world_totals,
            value_column="emissions_mtco2e",
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
        ),
    }
    if not all(record["passed"] for record in conservation.values()):
        raise AssertionError("Formal SSP GHG WORLD conservation gate failed")

    frames = {
        "detail": detail,
        "country": country,
        "product": product,
        "world": world,
    }
    na_counts = {name: int(frame.isna().sum().sum()) for name, frame in frames.items()}
    negative_counts = {
        name: int(frame["emissions_mtco2e"].lt(0).sum())
        for name, frame in frames.items()
    }
    if any(na_counts.values()) or any(negative_counts.values()):
        raise AssertionError("Formal SSP GHG output contains NA or negative emissions")
    noncovered = detail[detail["coverage_status"].eq("noncovered")]
    noncovered_max = float(
        noncovered["emissions_mtco2e"].max() if len(noncovered) else 0.0
    )
    if noncovered_max != 0.0:
        raise AssertionError("A noncovered processed product received upstream emissions")

    output_paths = {
        key: root / value for key, value in config["scenario_outputs"].items()
    }
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(output_paths[name], index=False)

    expected_world_rows = (
        len(scenario_config["scenarios"])
        * (int(scenario_config["last_year"]) - base_year + 1)
    )
    if len(world) != expected_world_rows or world.duplicated(
        ["scenario", "year"]
    ).any():
        raise AssertionError("Formal WORLD output is not one row per SSP/year")
    world_2023 = world[world["year"].eq(base_year)].set_index("scenario")[
        "emissions_mtco2e"
    ]
    world_2050 = world[world["year"].eq(2050)].set_index("scenario")[
        "emissions_mtco2e"
    ]

    audit: dict[str, Any] = {
        "status": "passed_formal_ssp_ghg_postsolution",
        "execution_stage": "post_solution",
        "nitrogen_module_enabled": False,
        "coefficient_rule": scenario_config["coefficient_rule"],
        "baseline_rebuilt_before_scenario_accounting": True,
        "baseline_rebuild_status": baseline_report["status"],
        "baseline_modeled_attributed_mtco2e": float(
            baseline_report["baseline_modeled_attributed_mtco2e"]
        ),
        "scenario_source": str(source_path),
        "scenario_source_sha256": sha256_file(source_path),
        "production_source_columns_consumed": consumed_columns,
        "forbidden_quantity_columns_consumed": [],
        "demand_or_trade_quantities_used": False,
        "input_gate": input_audit,
        "scenarios": list(scenario_config["scenarios"]),
        "first_year": base_year,
        "last_year": int(scenario_config["last_year"]),
        "detail_row_count": int(len(detail)),
        "country_summary_row_count": int(len(country)),
        "product_summary_row_count": int(len(product)),
        "world_summary_row_count": int(len(world)),
        "output_na_counts": na_counts,
        "output_negative_emission_counts": negative_counts,
        "processed_noncovered_max_emissions_mtco2e": noncovered_max,
        "processed_upstream_double_counting_gate": "passed",
        "common_2023_gate": {
            "absolute_tolerance": base_tolerance,
            "max_production_spread_across_ssps_mt": production_spread,
            "max_emissions_spread_across_ssps_mtco2e": emissions_spread,
            "max_production_difference_from_rebuilt_baseline_mt": baseline_production_difference,
            "max_emissions_difference_from_rebuilt_baseline_mtco2e": baseline_emissions_difference,
            "passed": base_passed,
        },
        "world_conservation_gate": conservation,
        "world_emissions_2023_mtco2e": {
            str(key): float(value) for key, value in world_2023.items()
        },
        "world_emissions_2050_mtco2e": {
            str(key): float(value) for key, value in world_2050.items()
        },
        "factor_source": str(factors_path),
        "factor_source_sha256": sha256_file(factors_path),
        "factor_base_year": 2023,
        "emission_boundary": config["boundary"]["name"],
        "energy_is_unallocated_validation_control": True,
        "farm_gate_validation_not_forced": True,
        "outputs": {key: str(path) for key, path in output_paths.items()},
    }
    output_paths["audit"].write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--run-ssp",
        action="store_true",
        help="rebuild 2023 factors and apply them to formal SSP production",
    )
    args = parser.parse_args()
    report = (
        run_formal_ssp_ghg(args.project_root)
        if args.run_ssp
        else build_ghg_module(args.project_root)
    )
    print(
        json.dumps(
            report, indent=2, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
