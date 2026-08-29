"""Transparent climate-yield shocks for the CASM-World 2023-2050 rebuild.

The module applies only the four global crop-temperature coefficients reported
by Zhao et al. (2017).  It does not invent coefficients for livestock, raw
milk, crop aggregates, or processing outputs.  Processing products receive an
explicit index of one so a primary-crop shock cannot be counted twice.
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "climate.yaml"
EXPECTED_SCENARIOS = ("SSP1", "SSP2", "SSP3", "SSP4", "SSP5")
DIRECT_IPCC_SCENARIOS = frozenset({"SSP1", "SSP2", "SSP3", "SSP5"})
DIRECT_PARAMETER_COMMODITIES = frozenset({"RIC", "WHE", "CRN", "SBS"})


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _project_path(project_root: Path, relative: object, label: str) -> Path:
    path = Path(str(relative))
    if path.is_absolute():
        raise ValueError(f"{label} must be relative to the new project")
    root = project_root.resolve()
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the new project: {path}") from exc
    return resolved


def load_climate_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and validate source lineage, assumptions, and impact scope."""

    config_path = Path(path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Climate configuration must be a mapping")
    validate_climate_config(config)
    return config


def validate_climate_config(config: Mapping[str, Any]) -> None:
    if int(config.get("schema_version", -1)) != 1:
        raise ValueError("climate.yaml schema_version must equal one")
    if int(config.get("benchmark_year", -1)) != 2023:
        raise ValueError("Climate benchmark year must be 2023")
    if int(config.get("projection_end", -1)) != 2050:
        raise ValueError("Climate projection end must be 2050")
    if tuple(config.get("scenarios", ())) != EXPECTED_SCENARIOS:
        raise ValueError("Climate scenarios must be SSP1-SSP5 in order")

    literature = _mapping(config.get("literature_parameters"), "literature_parameters")
    zhao = _mapping(literature.get("zhao_2017_crop_temperature"), "Zhao parameters")
    sensitivities = _mapping(zhao.get("commodity_parameters"), "crop sensitivities")
    if set(sensitivities) != DIRECT_PARAMETER_COMMODITIES:
        raise ValueError("Zhao scope must be exactly RIC/WHE/CRN/SBS")
    for commodity, value in sensitivities.items():
        parameter = float(value)
        if not isfinite(parameter) or not -1.0 < parameter < 0.0:
            raise ValueError(f"Invalid warming sensitivity for {commodity}")
    if "10.1073/pnas.1701762114" not in str(zhao.get("doi", "")):
        raise ValueError("Zhao DOI is missing or incorrect")

    ipcc = _mapping(literature.get("ipcc_ar6_wgi_spm_table_1"), "IPCC parameters")
    direct_values = _mapping(ipcc.get("direct_scenario_values"), "IPCC scenario values")
    expected_forcing_paths = {"SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"}
    if set(direct_values) != expected_forcing_paths:
        raise ValueError("IPCC direct values must contain the four mapped pathways")
    for pathway, values in direct_values.items():
        values = _mapping(values, pathway)
        near = float(values.get("near_term_2021_2040", float("nan")))
        mid = float(values.get("mid_term_2041_2060", float("nan")))
        if not (isfinite(near) and isfinite(mid) and mid >= near > 0):
            raise ValueError(f"Invalid IPCC warming nodes for {pathway}")

    wmo = _mapping(literature.get("wmo_2023_temperature_anchor"), "WMO anchor")
    if float(wmo.get("global_temperature_anomaly_2023", float("nan"))) != 1.45:
        raise ValueError("The WMO 2023 anchor must be 1.45 degree C")

    scenario_map = _mapping(config.get("ssp_forcing_mapping"), "SSP forcing mapping")
    if tuple(scenario_map) != EXPECTED_SCENARIOS:
        raise ValueError("SSP forcing mapping must contain SSP1-SSP5 in order")
    if scenario_map["SSP4"].get("temperature_node_source") != "author_forcing_interpolation":
        raise ValueError("SSP4 temperature nodes must remain an author assumption")
    for scenario in DIRECT_IPCC_SCENARIOS:
        if scenario_map[scenario].get("temperature_node_source") != "ipcc_ar6_direct":
            raise ValueError(f"{scenario} must use IPCC direct nodes")

    assumptions = _mapping(config.get("author_assumptions"), "author assumptions")
    regional = _mapping(assumptions.get("regional_exposure"), "regional exposure")
    if regional.get("method") != "global_coefficient" or float(
        regional.get("exposure_factor", float("nan"))
    ) != 1.0:
        raise ValueError("Regional exposure must explicitly use the global factor 1.0")
    ssp4 = _mapping(assumptions.get("ssp4_temperature_interpolation"), "SSP4 assumption")
    if ssp4.get("publish_as_ipcc_direct") is not False:
        raise ValueError("SSP4 interpolation must never be labelled IPCC-direct")
    if float(ssp4.get("weight_on_upper", float("nan"))) != 0.6:
        raise ValueError("SSP4 forcing interpolation weight must equal 0.6")
    equation = _mapping(assumptions.get("impact_equation"), "impact equation")
    if equation.get("clipping") != "forbidden":
        raise ValueError("Climate yield indices must not be silently clipped")
    bounds = tuple(float(value) for value in equation.get("hard_validation_bounds", ()))
    if len(bounds) != 2 or not 0 < bounds[0] < bounds[1] <= 1:
        raise ValueError("Impact validation bounds must lie within (0,1]")

    scope = _mapping(config.get("commodity_scope"), "commodity scope")
    direct = set(scope.get("direct_primary_with_peer_reviewed_parameter", ()))
    unparameterized = set(scope.get("primary_without_matching_authoritative_parameter", ()))
    processing = set(scope.get("processing_outputs_no_double_shock", ()))
    if direct != DIRECT_PARAMETER_COMMODITIES:
        raise ValueError("Direct climate scope must equal the Zhao commodity scope")
    if direct & unparameterized or direct & processing or unparameterized & processing:
        raise ValueError("Climate commodity-scope partitions must be disjoint")
    if len(direct | unparameterized | processing) != int(scope.get("expected_count", -1)):
        raise ValueError("Climate commodity-scope partition must contain 31 products")

    universe = _mapping(config.get("model_universe"), "model universe")
    if int(universe.get("expected_accounts", -1)) != 193:
        raise ValueError("Climate module must target 193 model accounts")
    if int(universe.get("expected_commodities", -1)) != 31:
        raise ValueError("Climate module must target 31 commodities")


def _temperature_nodes(config: Mapping[str, Any], scenario: str) -> tuple[dict[int, float], str, str]:
    literature = config["literature_parameters"]
    anchor = float(
        literature["wmo_2023_temperature_anchor"]["global_temperature_anomaly_2023"]
    )
    scenario_record = config["ssp_forcing_mapping"][scenario]
    forcing_path = str(scenario_record["forcing_path"])
    source_status = str(scenario_record["temperature_node_source"])
    if source_status == "ipcc_ar6_direct":
        published = literature["ipcc_ar6_wgi_spm_table_1"]["direct_scenario_values"][
            forcing_path
        ]
        near = float(published["near_term_2021_2040"])
        mid = float(published["mid_term_2041_2060"])
    elif source_status == "author_forcing_interpolation":
        derived = config["author_assumptions"]["ssp4_temperature_interpolation"][
            "derived_values"
        ]
        near = float(derived["near_term_2021_2040"])
        mid = float(derived["mid_term_2041_2060"])
    else:
        raise ValueError(f"Unknown temperature-node source for {scenario}")
    return {2023: anchor, 2030: near, 2050: mid}, forcing_path, source_status


def _linear_interpolate(nodes: Mapping[int, float], years: Sequence[int]) -> dict[int, float]:
    ordered = sorted((int(year), float(value)) for year, value in nodes.items())
    requested = sorted(set(int(year) for year in years))
    if not requested or requested[0] < ordered[0][0] or requested[-1] > ordered[-1][0]:
        raise ValueError("Temperature interpolation cannot extrapolate beyond 2023-2050")
    node_years = np.array([year for year, _ in ordered], dtype=float)
    node_values = np.array([value for _, value in ordered], dtype=float)
    values = np.interp(np.array(requested, dtype=float), node_years, node_values)
    return dict(zip(requested, values.tolist()))


def build_temperature_paths(
    config: Mapping[str, Any], years: Iterable[int] = range(2023, 2051)
) -> pd.DataFrame:
    """Build annual scenario temperature nodes with a common observed anchor."""

    validate_climate_config(config)
    requested = tuple(sorted(set(int(year) for year in years)))
    if 2023 not in requested:
        raise ValueError("Temperature paths must include the 2023 benchmark anchor")
    records: list[dict[str, Any]] = []
    for scenario in EXPECTED_SCENARIOS:
        nodes, forcing_path, source_status = _temperature_nodes(config, scenario)
        path = _linear_interpolate(nodes, requested)
        anchor = path[2023]
        previous = None
        for year in requested:
            temperature = float(path[year])
            incremental = temperature - anchor
            if incremental < -1e-12:
                raise ValueError(f"Temperature path falls below 2023 for {scenario}/{year}")
            if previous is not None and temperature < previous - 1e-12:
                raise ValueError(f"Temperature path is not monotone for {scenario}")
            records.append(
                {
                    "scenario": scenario,
                    "forcing_path": forcing_path,
                    "year": year,
                    "global_temperature_anomaly_c": temperature,
                    "incremental_warming_from_2023_c": max(0.0, incremental),
                    "temperature_node_source": source_status,
                }
            )
            previous = temperature
    result = pd.DataFrame.from_records(records)
    if result.isna().any().any() or not np.isfinite(
        result[["global_temperature_anomaly_c", "incremental_warming_from_2023_c"]]
    ).all().all():
        raise ValueError("Temperature paths contain missing or non-finite values")
    return result


def load_model_universe(
    project_root: str | Path, config: Mapping[str, Any]
) -> tuple[list[str], list[str]]:
    """Load the exact 193-account and 31-product universes from the rebuild."""

    validate_climate_config(config)
    root = Path(project_root).resolve()
    universe = config["model_universe"]
    benchmark_path = _project_path(root, universe["benchmark_path"], "benchmark_path")
    economy_column = str(universe["economy_column"])
    benchmark = pd.read_csv(benchmark_path, usecols=[economy_column])
    accounts = sorted(
        benchmark[economy_column].astype(str).str.strip().str.upper().unique().tolist()
    )
    if len(accounts) != int(universe["expected_accounts"]):
        raise ValueError(f"Expected 193 model accounts, found {len(accounts)}")
    if any(not account for account in accounts):
        raise ValueError("Blank model-account identifiers are forbidden")

    model_path = _project_path(root, universe["model_config_path"], "model_config_path")
    model_config = yaml.safe_load(model_path.read_text(encoding="utf-8"))
    commodities = [str(code).strip().upper() for code in model_config.get("commodities", [])]
    if len(commodities) != int(universe["expected_commodities"]) or len(set(commodities)) != len(
        commodities
    ):
        raise ValueError("Model configuration must contain 31 unique commodities")
    scope = config["commodity_scope"]
    configured = set(scope["direct_primary_with_peer_reviewed_parameter"]) | set(
        scope["primary_without_matching_authoritative_parameter"]
    ) | set(scope["processing_outputs_no_double_shock"])
    if set(commodities) != configured:
        raise ValueError(
            "Climate commodity partition does not match the model: "
            f"missing={sorted(set(commodities)-configured)}, "
            f"extra={sorted(configured-set(commodities))}"
        )
    return accounts, commodities


def _commodity_parameter_table(
    commodities: Sequence[str], config: Mapping[str, Any]
) -> pd.DataFrame:
    scope = config["commodity_scope"]
    direct = set(scope["direct_primary_with_peer_reviewed_parameter"])
    unparameterized = set(scope["primary_without_matching_authoritative_parameter"])
    processing = set(scope["processing_outputs_no_double_shock"])
    sensitivities = config["literature_parameters"]["zhao_2017_crop_temperature"][
        "commodity_parameters"
    ]
    records = []
    for commodity in commodities:
        if commodity in direct:
            records.append(
                {
                    "commodity": commodity,
                    "yield_sensitivity_fraction_per_c": float(sensitivities[commodity]),
                    "direct_climate_shock": True,
                    "commodity_scope_status": "direct_zhao_2017_global_parameter",
                    "yield_parameter_source": "Zhao_et_al_2017_PNAS",
                }
            )
        elif commodity in unparameterized:
            records.append(
                {
                    "commodity": commodity,
                    "yield_sensitivity_fraction_per_c": 0.0,
                    "direct_climate_shock": False,
                    "commodity_scope_status": "explicit_no_matching_authoritative_parameter",
                    "yield_parameter_source": "NONE_EXPLICIT_UNPARAMETERIZED_PRIMARY",
                }
            )
        elif commodity in processing:
            records.append(
                {
                    "commodity": commodity,
                    "yield_sensitivity_fraction_per_c": 0.0,
                    "direct_climate_shock": False,
                    "commodity_scope_status": "processing_output_no_double_shock",
                    "yield_parameter_source": "NOT_APPLICABLE_PROCESSING_OUTPUT",
                }
            )
        else:
            raise ValueError(f"Commodity lacks explicit climate scope: {commodity}")
    return pd.DataFrame.from_records(records)


def build_climate_yield_paths(
    model_accounts: Sequence[str],
    commodities: Sequence[str],
    config: Mapping[str, Any],
    years: Iterable[int] = range(2023, 2051),
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build complete SSP/account/year/product climate yield indices."""

    validate_climate_config(config)
    accounts = sorted(set(str(value).strip().upper() for value in model_accounts))
    products = [str(value).strip().upper() for value in commodities]
    if not accounts or any(not value for value in accounts):
        raise ValueError("Model accounts must be nonempty unique identifiers")
    if len(products) != len(set(products)) or any(not value for value in products):
        raise ValueError("Commodities must be nonempty unique identifiers")
    configured_products = (
        set(config["commodity_scope"]["direct_primary_with_peer_reviewed_parameter"])
        | set(config["commodity_scope"]["primary_without_matching_authoritative_parameter"])
        | set(config["commodity_scope"]["processing_outputs_no_double_shock"])
    )
    if set(products) != configured_products:
        raise ValueError("Requested commodities must equal the configured 31-product scope")

    requested_years = tuple(sorted(set(int(year) for year in years)))
    if 2023 not in requested_years:
        raise ValueError("Climate yield paths must include the 2023 benchmark anchor")
    temperature = build_temperature_paths(config, requested_years)
    account_frame = pd.DataFrame({"economy_id": accounts})
    product_frame = _commodity_parameter_table(products, config)
    universe = account_frame.merge(product_frame, how="cross")
    result = temperature.merge(universe, how="cross")
    regional = config["author_assumptions"]["regional_exposure"]
    exposure_factor = float(regional["exposure_factor"])
    result["regional_exposure_factor"] = exposure_factor
    result["regional_parameter_status"] = str(regional["status"])
    result["climate_yield_index_2023"] = 1.0 + (
        result["yield_sensitivity_fraction_per_c"]
        * result["regional_exposure_factor"]
        * result["incremental_warming_from_2023_c"]
    )

    key = ["scenario", "economy_id", "year", "commodity"]
    if result.duplicated(key).any():
        raise ValueError("Climate yield output contains duplicate keys")
    if result.isna().any().any():
        raise ValueError("Climate yield output contains missing values")
    numeric = result.select_dtypes(include=[np.number])
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("Climate yield output contains non-finite values")
    anchor = result.loc[result["year"].eq(2023), "climate_yield_index_2023"]
    if len(anchor) != len(accounts) * len(products) * len(EXPECTED_SCENARIOS) or not np.array_equal(
        anchor.to_numpy(), np.ones(len(anchor))
    ):
        raise AssertionError("Every climate yield path must equal exactly one in 2023")
    lower, upper = (
        float(value)
        for value in config["author_assumptions"]["impact_equation"][
            "hard_validation_bounds"
        ]
    )
    indices = result["climate_yield_index_2023"]
    if not indices.between(lower, upper, inclusive="both").all():
        outside = result.loc[~indices.between(lower, upper, inclusive="both"), key + [
            "climate_yield_index_2023"
        ]]
        raise ValueError(f"Climate yield index outside validation bounds: {outside.head().to_dict('records')}")

    direct_products = sorted(
        config["commodity_scope"]["direct_primary_with_peer_reviewed_parameter"]
    )
    unparameterized = sorted(
        config["commodity_scope"]["primary_without_matching_authoritative_parameter"]
    )
    processing = sorted(config["commodity_scope"]["processing_outputs_no_double_shock"])
    expected_rows = (
        len(EXPECTED_SCENARIOS)
        * len(accounts)
        * len(products)
        * len(requested_years)
    )
    report: dict[str, Any] = {
        "status": "complete_global_parameters_with_explicit_scope_limits",
        "benchmark_year": 2023,
        "projection_end": 2050,
        "model_account_count": len(accounts),
        "commodity_count": len(products),
        "scenario_count": len(EXPECTED_SCENARIOS),
        "year_count": len(requested_years),
        "expected_row_count": expected_rows,
        "actual_row_count": len(result),
        "direct_shock_commodity_count": len(direct_products),
        "direct_shock_commodities": direct_products,
        "unparameterized_primary_commodity_count": len(unparameterized),
        "unparameterized_primary_commodities": unparameterized,
        "processing_no_double_shock_commodity_count": len(processing),
        "processing_no_double_shock_commodities": processing,
        "regional_parameterization": "global_coefficient_no_regional_differentiation",
        "regional_detail_fallback_account_count": len(accounts),
        "regional_detail_fallback_accounts": accounts,
        "ipcc_direct_scenarios": sorted(DIRECT_IPCC_SCENARIOS),
        "author_interpolated_scenarios": ["SSP4"],
        "anchor_violation_count": int((anchor != 1.0).sum()),
        "missing_value_count": int(result.isna().sum().sum()),
        "minimum_yield_index": float(indices.min()),
        "maximum_yield_index": float(indices.max()),
        "clipping_applied": False,
        "source_lineage": {
            "crop_sensitivity": "Zhao et al. 2017 PNAS; DOI 10.1073/pnas.1701762114",
            "temperature_projection": "IPCC AR6 WGI Table SPM.1",
            "benchmark_temperature": "WMO State of the Global Climate 2023",
            "ssp4_definition": "O'Neill et al. 2016 ScenarioMIP; DOI 10.5194/gmd-9-3461-2016",
        },
    }

    category_columns = [
        "scenario",
        "forcing_path",
        "temperature_node_source",
        "economy_id",
        "commodity",
        "commodity_scope_status",
        "yield_parameter_source",
        "regional_parameter_status",
    ]
    for column in category_columns:
        result[column] = result[column].astype("category")
    result = result[
        [
            "scenario",
            "forcing_path",
            "economy_id",
            "year",
            "commodity",
            "global_temperature_anomaly_c",
            "incremental_warming_from_2023_c",
            "temperature_node_source",
            "yield_sensitivity_fraction_per_c",
            "regional_exposure_factor",
            "regional_parameter_status",
            "direct_climate_shock",
            "commodity_scope_status",
            "yield_parameter_source",
            "climate_yield_index_2023",
        ]
    ]
    return result, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CASM-World climate yield paths")
    parser.add_argument(
        "--project-root", type=Path, default=PROJECT_ROOT, help="CASM-World rebuild root"
    )
    args = parser.parse_args()
    root = args.project_root.resolve()
    config = load_climate_config(root / "config/climate.yaml")
    accounts, commodities = load_model_universe(root, config)
    temperature = build_temperature_paths(config)
    paths, report = build_climate_yield_paths(accounts, commodities, config)

    outputs = config["outputs"]
    temperature_path = _project_path(root, outputs["temperature_paths"], "temperature output")
    yield_path = _project_path(root, outputs["yield_paths"], "yield output")
    report_path = _project_path(root, outputs["coverage_report"], "coverage report")
    for output in (temperature_path, yield_path, report_path):
        output.parent.mkdir(parents=True, exist_ok=True)
    temperature.to_csv(temperature_path, index=False)
    paths.to_csv(yield_path, index=False)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
