"""Annual SSP simulation orchestration for the rebuilt CASM-World model."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import yaml

from casm_world.linked_equilibrium import (
    LinkedEquilibriumResult,
    ProcessSpec,
    solve_linked_equilibrium,
)
from casm_world.system import ModelSystem, build_model_system


@dataclass(frozen=True)
class SimulationInputs:
    root: Path
    config: dict
    commodity_config: dict
    system: ModelSystem
    parameter_set: str
    parameter_table: str
    parameter_table_sha256: str
    simulation_config_sha256: str
    supply_elasticity: np.ndarray
    demand_elasticity: np.ndarray
    income_elasticity: np.ndarray
    exchange_pass_through: np.ndarray
    tariff_pass_through: np.ndarray
    tfp_exponents: np.ndarray
    supply_lag_by_product: np.ndarray
    process_lag_by_name: dict[str, float]
    food_share_of_final_demand: np.ndarray
    drivers: pd.DataFrame
    tfp: pd.DataFrame
    exchange: pd.DataFrame
    tariff: pd.DataFrame
    climate: pd.DataFrame


def _assert_unique_complete(
    frame: pd.DataFrame,
    keys: list[str],
    expected_rows: int,
    label: str,
) -> None:
    if not set(keys) <= set(frame):
        raise ValueError(f"{label} is missing keys: {sorted(set(keys)-set(frame))}")
    if frame.duplicated(keys).any():
        raise ValueError(f"{label} has duplicate keys")
    if len(frame) != expected_rows:
        raise ValueError(
            f"{label} coverage mismatch: expected {expected_rows}, received {len(frame)}"
        )


def _parameter_matrix(
    parameters: pd.DataFrame,
    regions: tuple[str, ...],
    products: tuple[str, ...],
    column: str,
) -> np.ndarray:
    table = parameters.pivot(index="economy_id", columns="commodity", values=column)
    table = table.reindex(index=regions, columns=products)
    if table.isna().any().any():
        raise ValueError(f"Parameter {column} is incomplete")
    values = table.to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError(f"Parameter {column} is non-finite")
    return values


def _validate_v2_parameter_contract(
    parameters: pd.DataFrame,
    parameter_config: dict,
) -> str:
    required_set = str(parameter_config["required_parameter_set"])
    if "parameter_set" not in parameters:
        raise ValueError("V2 parameter table is missing parameter_set")
    parameter_sets = set(parameters["parameter_set"].astype(str).unique())
    if parameter_sets != {required_set}:
        raise ValueError(
            f"Parameter set must be exactly {required_set!r}, received "
            f"{sorted(parameter_sets)}"
        )
    marker_column = str(parameter_config["marker_column"])
    if marker_column not in parameters:
        raise ValueError(f"V2 parameter table is missing {marker_column}")
    marker = str(parameter_config["marker_contains"]).casefold()
    statuses = parameters[marker_column].astype(str)
    if statuses.str.casefold().str.contains(marker, regex=False).ne(True).any():
        raise ValueError(f"Every {marker_column} must contain the V2 marker {marker!r}")
    semantic_contract = parameter_config.get("semantic_contract", {})
    for column, required_value in semantic_contract.items():
        if column not in parameters:
            raise ValueError(f"V2 parameter table is missing semantic field {column}")
        values = set(parameters[column].astype(str).unique())
        if values != {str(required_value)}:
            raise ValueError(
                f"Parameter semantic field {column} must be {required_value!r}, "
                f"received {sorted(values)}"
            )
    return required_set


def _validate_lag(value: object, label: str) -> float:
    try:
        lag = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not np.isfinite(lag) or lag < 0.0 or lag >= 1.0:
        raise ValueError(f"{label} must be finite and lie in [0, 1)")
    return lag


def _response_horizon_factor(
    year: int,
    benchmark_year: int,
    lag: np.ndarray | float,
) -> np.ndarray:
    """Return the frozen V2 partial-adjustment response factor.

    The normalized benchmark uses the long-run response directly.  For every
    subsequent year the factor is ``1-lambda**(year-benchmark_year)``.
    """

    if int(year) != year or int(benchmark_year) != benchmark_year:
        raise ValueError("Response-horizon years must be integers")
    if year < benchmark_year:
        raise ValueError("Response-horizon year cannot precede the benchmark")
    lags = np.asarray(lag, dtype=float)
    if not np.isfinite(lags).all() or (lags < 0.0).any() or (lags >= 1.0).any():
        raise ValueError("Response lags must be finite and lie in [0, 1)")
    if year == benchmark_year:
        return np.ones_like(lags, dtype=float)
    return 1.0 - np.power(lags, int(year - benchmark_year))


def _effective_supply_elasticity(
    long_run_elasticity: np.ndarray,
    lag_by_product: np.ndarray,
    year: int,
    benchmark_year: int,
) -> np.ndarray:
    long_run = np.asarray(long_run_elasticity, dtype=float)
    lags = np.asarray(lag_by_product, dtype=float)
    if long_run.ndim != 2 or lags.shape != (long_run.shape[1],):
        raise ValueError("Supply response grid and product lags are incompatible")
    if not np.isfinite(long_run).all() or (long_run < 0.0).any():
        raise ValueError("Long-run supply elasticities must be finite and nonnegative")
    return long_run * _response_horizon_factor(
        year, benchmark_year, lags
    )[None, :]


def _primary_supply_lags(
    system: ModelSystem,
    commodity_config: dict,
    response_config: dict,
) -> np.ndarray:
    """Map primary supply products to lags and reject unconfigured activity."""

    class_lags = response_config.get("lambda_by_commodity_class", {})
    product_lags = response_config.get("lambda_by_product", {})
    inactive_classes = set(
        response_config.get("inactive_classes_without_primary_supply", [])
    )
    unknown_product_overrides = set(product_lags) - set(system.products)
    if unknown_product_overrides:
        raise ValueError(
            "Primary-supply lag overrides reference unknown products: "
            f"{sorted(unknown_product_overrides)}"
        )
    result = np.zeros(len(system.products), dtype=float)
    for product_index, product in enumerate(system.products):
        try:
            commodity_class = commodity_config["commodities"][product]["class"]
        except KeyError as exc:
            raise ValueError(f"Missing commodity class for {product}") from exc
        has_primary_supply = bool(
            np.any(system.base_primary_supply[:, product_index] > 0.0)
        )
        if product in product_lags:
            result[product_index] = _validate_lag(
                product_lags[product], f"primary_supply.{product}.lambda"
            )
        elif commodity_class in class_lags:
            result[product_index] = _validate_lag(
                class_lags[commodity_class],
                f"primary_supply.{commodity_class}.lambda",
            )
        elif has_primary_supply:
            raise ValueError(
                f"Active primary supply {product} ({commodity_class}) has no V2 lag"
            )
        elif commodity_class not in inactive_classes:
            raise ValueError(
                f"Inactive primary-supply class {commodity_class} is not explicitly declared"
            )
    return result


def _fit_process_long_run_elasticities(
    processes: tuple[ProcessSpec, ...],
    supply_elasticity: np.ndarray,
    products: tuple[str, ...],
    response_config: dict,
) -> tuple[tuple[ProcessSpec, ...], dict[str, float]]:
    """Assign process-specific LR margin responses from a fail-closed map."""

    activities = response_config.get("activities", {})
    process_names = [process.name for process in processes]
    if len(process_names) != len(set(process_names)):
        raise ValueError("Process names must be unique")
    unknown = set(process_names) - set(activities)
    unused = set(activities) - set(process_names)
    if unknown or unused:
        raise ValueError(
            "V2 process response whitelist mismatch: "
            f"unconfigured={sorted(unknown)}, unused={sorted(unused)}"
        )
    product_index = {product: index for index, product in enumerate(products)}
    result: list[ProcessSpec] = []
    lags: dict[str, float] = {}
    for process in processes:
        definition = activities[process.name]
        method = definition.get("elasticity_method")
        if method in {"fixed", "fixed_zero"}:
            try:
                fixed = float(definition["long_run_elasticity"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Process {process.name} has no numeric long-run elasticity"
                ) from exc
            if not np.isfinite(fixed) or fixed < 0.0:
                raise ValueError(
                    f"Process {process.name} long-run elasticity is invalid"
                )
            if method == "fixed_zero" and fixed != 0.0:
                raise ValueError(
                    f"Process {process.name} fixed_zero elasticity must equal zero"
                )
            elasticity = np.full(len(process.base_activity), fixed, dtype=float)
        elif method == "product_parameter":
            parameter_product = str(definition.get("parameter_product", ""))
            if parameter_product not in product_index:
                raise ValueError(
                    f"Process {process.name} references unknown parameter product "
                    f"{parameter_product!r}"
                )
            elasticity = np.array(
                supply_elasticity[:, product_index[parameter_product]], copy=True
            )
        else:
            raise ValueError(
                f"Process {process.name} has unknown elasticity method {method!r}"
            )
        lags[process.name] = _validate_lag(
            definition.get("lambda"), f"processing.{process.name}.lambda"
        )
        result.append(replace(process, elasticity=elasticity))
    return tuple(result), lags


def _apply_process_response_horizon(
    processes: tuple[ProcessSpec, ...],
    lag_by_name: dict[str, float],
    year: int,
    benchmark_year: int,
) -> tuple[ProcessSpec, ...]:
    names = {process.name for process in processes}
    if names != set(lag_by_name):
        raise ValueError("Process response lags do not match model processes")
    return tuple(
        replace(
            process,
            elasticity=process.elasticity
            * _response_horizon_factor(
                year, benchmark_year, lag_by_name[process.name]
            ).item(),
        )
        for process in processes
    )


def _apply_process_supply_shifters(
    processes: tuple[ProcessSpec, ...],
    supply_shifter: np.ndarray,
) -> tuple[ProcessSpec, ...]:
    """Pass product supply shifts through to each process activity.

    A joint-output activity receives the output-coefficient-weighted geometric
    mean of its products' supply shifters.  This preserves a unit shifter in the
    2023 benchmark, lets a process with only one output inherit that output's
    full shift, and leaves an activity without a modelled output unchanged.
    """

    shifts = np.asarray(supply_shifter, dtype=float)
    if shifts.ndim != 2 or not np.isfinite(shifts).all() or (shifts < 0).any():
        raise ValueError("Process supply shifters must be a finite nonnegative matrix")
    result: list[ProcessSpec] = []
    for process in processes:
        if process.output_coefficients.shape != shifts.shape:
            raise ValueError(
                f"Process {process.name} output grid does not match supply shifters"
            )
        output_total = process.output_coefficients.sum(axis=1, keepdims=True)
        output_weights = np.divide(
            process.output_coefficients,
            output_total,
            out=np.zeros_like(process.output_coefficients),
            where=output_total > 0,
        )
        positive = shifts > 0
        weighted_log = np.sum(
            output_weights * np.where(positive, np.log(np.where(positive, shifts, 1.0)), 0.0),
            axis=1,
        )
        activity_shifter = np.exp(weighted_log)
        has_output = output_total.ravel() > 0
        has_zero_weighted_output = np.any((output_weights > 0) & ~positive, axis=1)
        activity_shifter[has_zero_weighted_output] = 0.0
        activity_shifter[~has_output] = 1.0
        result.append(replace(process, activity_shifter=activity_shifter))
    return tuple(result)


def load_simulation_inputs(project_root: Path | str) -> SimulationInputs:
    root = Path(project_root).resolve()
    simulation_config_path = root / "config/simulation.yaml"
    simulation_config_bytes = simulation_config_path.read_bytes()
    config = yaml.safe_load(simulation_config_bytes.decode("utf-8"))
    commodity_config = yaml.safe_load(
        (root / "config/commodities.yaml").read_text(encoding="utf-8")
    )
    benchmark = pd.read_csv(root / "data/processed/benchmark_equilibrium_2023.csv")
    activities = pd.read_csv(root / "data/processed/benchmark_processing_activities_2023.csv")
    system = build_model_system(benchmark, activities, commodity_config)
    required_food_columns = {"food_demand_2023", "final_demand_2023"}
    if not required_food_columns <= set(benchmark):
        raise ValueError(
            "Balanced benchmark must retain explicit food and total final demand"
        )
    food = benchmark.pivot(
        index="economy_id", columns="commodity", values="food_demand_2023"
    ).reindex(index=system.regions, columns=system.products)
    final = benchmark.pivot(
        index="economy_id", columns="commodity", values="final_demand_2023"
    ).reindex(index=system.regions, columns=system.products)
    if food.isna().any().any() or final.isna().any().any():
        raise ValueError("Food-demand benchmark grid is incomplete")
    food_values = food.to_numpy(float)
    final_values = final.to_numpy(float)
    if (food_values < 0).any() or (food_values > final_values + 1.0e-12).any():
        raise ValueError("Food demand must be a nonnegative subset of final demand")
    benchmark_food_share = np.divide(
        food_values,
        final_values,
        out=np.zeros_like(food_values),
        where=final_values > 0,
    )
    parameter_config = config["parameters"]
    parameter_source_config = yaml.safe_load(
        (root / parameter_config["config"]).read_text(encoding="utf-8")
    )
    try:
        parameter_path = parameter_source_config["outputs"][
            parameter_config["output_key"]
        ]
    except KeyError as exc:
        raise ValueError("V2 parameter output path is missing from parameters config") from exc
    parameter_file = root / parameter_path
    parameter_bytes = parameter_file.read_bytes()
    parameters = pd.read_csv(parameter_file)
    expected_parameters = len(system.regions) * len(system.products)
    _assert_unique_complete(
        parameters, ["economy_id", "commodity"], expected_parameters, "parameter table"
    )
    parameter_set = _validate_v2_parameter_contract(parameters, parameter_config)
    supply_elasticity = _parameter_matrix(
        parameters, system.regions, system.products, "supply_price_elasticity"
    )
    demand_elasticity = _parameter_matrix(
        parameters, system.regions, system.products, "demand_price_elasticity"
    )
    income_elasticity = _parameter_matrix(
        parameters, system.regions, system.products, "income_elasticity"
    )
    exchange_pass = _parameter_matrix(
        parameters, system.regions, system.products, "exchange_rate_pass_through"
    )
    tariff_pass = _parameter_matrix(
        parameters, system.regions, system.products, "tariff_pass_through"
    )
    food_share = _parameter_matrix(
        parameters, system.regions, system.products, "balanced_food_share"
    )
    feed_share = _parameter_matrix(
        parameters, system.regions, system.products, "feed_share"
    )
    other_share = _parameter_matrix(
        parameters, system.regions, system.products, "other_use_share"
    )
    if (
        (food_share < 0.0).any()
        or (feed_share < 0.0).any()
        or (other_share < 0.0).any()
        or (food_share > 1.0).any()
        or (feed_share > 1.0).any()
        or (other_share > 1.0).any()
    ):
        raise ValueError("V2 final-demand use shares must lie in [0, 1]")
    active_final = final_values > 0.0
    share_sum = food_share + feed_share + other_share
    if not np.allclose(share_sum[active_final], 1.0, atol=1.0e-12, rtol=0.0):
        raise ValueError("V2 active final-demand use shares must sum exactly to one")
    if not np.allclose(
        food_share, benchmark_food_share, atol=1.0e-12, rtol=0.0
    ):
        raise ValueError("V2 balanced food shares do not reproduce the benchmark")
    response_config = config["response_horizons"]
    supply_lags = _primary_supply_lags(
        system, commodity_config, response_config["primary_supply"]
    )
    processes, process_lags = _fit_process_long_run_elasticities(
        system.processes,
        supply_elasticity,
        system.products,
        response_config["processing"],
    )
    system = replace(
        system,
        processes=processes,
    )

    classes = {
        product: commodity_config["commodities"][product]["class"]
        for product in system.products
    }
    class_exponents = config["tfp_exponent_by_commodity_class"]
    missing_classes = set(classes.values()) - set(class_exponents)
    if missing_classes:
        raise ValueError(f"Missing TFP exponents for commodity classes: {sorted(missing_classes)}")
    tfp_exponents = np.array(
        [float(class_exponents[classes[product]]) for product in system.products]
    )

    drivers = pd.read_csv(root / "data/processed/ssp_drivers_2023_2050.csv")
    tfp = pd.read_csv(root / "data/processed/tfp_paths_2023_2050.csv")
    exchange = pd.read_csv(root / "data/processed/real_exchange_rate_paths_2023_2050.csv")
    tariff = pd.read_csv(root / "data/processed/tariff_paths_2023_2050.csv")
    climate = pd.read_csv(
        root / "data/processed/climate_yield_paths_2023_2050.csv",
        usecols=["scenario", "economy_id", "commodity", "year", "climate_yield_index_2023"],
    )
    scenarios = list(config["scenarios"])
    years = range(int(config["benchmark_year"]), int(config["projection_end"]) + 1)
    n_region_year_scenario = len(system.regions) * len(scenarios) * len(years)
    n_full = n_region_year_scenario * len(system.products)
    _assert_unique_complete(
        drivers, ["scenario", "economy_id", "year"], n_region_year_scenario, "SSP drivers"
    )
    _assert_unique_complete(
        tfp, ["scenario", "economy_id", "year"], n_region_year_scenario, "TFP paths"
    )
    _assert_unique_complete(
        exchange, ["scenario", "economy_id", "year"], n_region_year_scenario,
        "real exchange-rate paths",
    )
    _assert_unique_complete(
        tariff, ["scenario", "economy_id", "commodity", "year"], n_full,
        "tariff paths",
    )
    _assert_unique_complete(
        climate, ["scenario", "economy_id", "commodity", "year"], n_full,
        "climate-yield paths",
    )
    return SimulationInputs(
        root=root,
        config=config,
        commodity_config=commodity_config,
        system=system,
        parameter_set=parameter_set,
        parameter_table=str(parameter_path),
        parameter_table_sha256=hashlib.sha256(parameter_bytes).hexdigest(),
        simulation_config_sha256=hashlib.sha256(
            simulation_config_bytes
        ).hexdigest(),
        supply_elasticity=supply_elasticity,
        demand_elasticity=demand_elasticity,
        income_elasticity=income_elasticity,
        exchange_pass_through=exchange_pass,
        tariff_pass_through=tariff_pass,
        tfp_exponents=tfp_exponents,
        supply_lag_by_product=supply_lags,
        process_lag_by_name=process_lags,
        food_share_of_final_demand=food_share,
        drivers=drivers,
        tfp=tfp,
        exchange=exchange,
        tariff=tariff,
        climate=climate,
    )


def _region_vector(
    frame: pd.DataFrame,
    regions: tuple[str, ...],
    scenario: str,
    year: int,
    column: str,
) -> np.ndarray:
    subset = frame[frame["scenario"].eq(scenario) & frame["year"].eq(year)]
    series = subset.set_index("economy_id")[column].reindex(regions)
    if series.isna().any():
        raise ValueError(f"Missing {column} for {scenario} {year}")
    return series.to_numpy(float)


def _region_product_matrix(
    frame: pd.DataFrame,
    regions: tuple[str, ...],
    products: tuple[str, ...],
    scenario: str,
    year: int,
    column: str,
) -> np.ndarray:
    subset = frame[frame["scenario"].eq(scenario) & frame["year"].eq(year)]
    table = subset.pivot(index="economy_id", columns="commodity", values=column)
    table = table.reindex(index=regions, columns=products)
    if table.isna().any().any():
        raise ValueError(f"Missing {column} for {scenario} {year}")
    return table.to_numpy(float)


def _result_frames(
    scenario: str,
    year: int,
    result: LinkedEquilibriumResult,
    food_share_of_final_demand: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    region_grid = np.repeat(result.region_names, len(result.product_names))
    product_grid = np.tile(result.product_names, len(result.region_names))
    prices = np.tile(result.prices, len(result.region_names))
    country_product = pd.DataFrame(
        {
            "scenario": scenario,
            "year": year,
            "economy_id": region_grid,
            "commodity": product_grid,
            "world_price_index_2023": prices,
            "primary_supply_mt": result.primary_supply.ravel(),
            "processing_supply_mt": result.process_supply.ravel(),
            "production_mt": result.total_supply.ravel(),
            "final_demand_mt": result.final_demand.ravel(),
            "food_demand_mt": (
                result.final_demand * food_share_of_final_demand
            ).ravel(),
            "processing_demand_mt": result.process_demand.ravel(),
            "demand_mt": result.total_demand.ravel(),
        }
    )
    country_product["net_import_mt"] = (
        country_product["demand_mt"] - country_product["production_mt"]
    )
    price_frame = pd.DataFrame(
        {
            "scenario": scenario,
            "year": year,
            "commodity": result.product_names,
            "world_price_index_2023": result.prices,
            "global_supply_mt": result.global_supply,
            "global_demand_mt": result.global_demand,
            "relative_market_residual": result.relative_residuals,
        }
    )
    process_frames = []
    for process in result.processes:
        process_frames.append(
            pd.DataFrame(
                {
                    "scenario": scenario,
                    "year": year,
                    "economy_id": result.region_names,
                    "process": process.name,
                    "activity": process.activity,
                }
            )
        )
    process_frame = pd.concat(process_frames, ignore_index=True)
    accounting = (
        country_product["production_mt"]
        + country_product["net_import_mt"]
        - country_product["demand_mt"]
    )
    convergence = {
        "scenario": scenario,
        "year": year,
        "function_evaluations": result.function_evaluations,
        "maximum_market_relative_residual": result.max_abs_residual,
        "maximum_accounting_absolute_residual_mt": float(accounting.abs().max()),
        "minimum_world_price_index": float(result.prices.min()),
        "maximum_world_price_index": float(result.prices.max()),
        "converged": True,
        "accounting_passed": True,
    }
    return country_product, price_frame, process_frame, convergence


def run_simulation(
    inputs: SimulationInputs,
    *,
    scenarios: Sequence[str] | None = None,
    years: Iterable[int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    selected_scenarios = list(scenarios or inputs.config["scenarios"])
    selected_years = sorted(
        set(years or range(int(inputs.config["benchmark_year"]), int(inputs.config["projection_end"]) + 1))
    )
    if not set(selected_scenarios) <= set(inputs.config["scenarios"]):
        raise ValueError("Unknown simulation scenario")
    if not selected_years or selected_years[0] < 2023 or selected_years[-1] > 2050:
        raise ValueError("Simulation years must lie in 2023-2050")
    solver = inputs.config["solver"]
    benchmark_year = int(inputs.config["benchmark_year"])
    result_frames: list[pd.DataFrame] = []
    price_frames: list[pd.DataFrame] = []
    process_frames: list[pd.DataFrame] = []
    convergence_rows: list[dict] = []
    for scenario in selected_scenarios:
        initial_prices = np.ones(len(inputs.system.products))
        population_2023 = _region_vector(
            inputs.drivers, inputs.system.regions, scenario, 2023, "population_index_2025"
        )
        gdppc_2023 = _region_vector(
            inputs.drivers, inputs.system.regions, scenario, 2023,
            "gdp_ppp_per_capita_index_2025",
        )
        tariff_2023 = _region_product_matrix(
            inputs.tariff, inputs.system.regions, inputs.system.products,
            scenario, 2023, "tariff_wedge",
        )
        for year in selected_years:
            supply_elasticity = _effective_supply_elasticity(
                inputs.supply_elasticity,
                inputs.supply_lag_by_product,
                year,
                benchmark_year,
            )
            population = _region_vector(
                inputs.drivers, inputs.system.regions, scenario, year,
                "population_index_2025",
            ) / population_2023
            gdppc = _region_vector(
                inputs.drivers, inputs.system.regions, scenario, year,
                "gdp_ppp_per_capita_index_2025",
            ) / gdppc_2023
            demand_shifter = population[:, None] * np.power(
                gdppc[:, None], inputs.income_elasticity
            )
            tfp = _region_vector(
                inputs.tfp, inputs.system.regions, scenario, year, "tfp_index_2023"
            )
            climate = _region_product_matrix(
                inputs.climate, inputs.system.regions, inputs.system.products,
                scenario, year, "climate_yield_index_2023",
            )
            supply_shifter = np.power(tfp[:, None], inputs.tfp_exponents[None, :]) * climate
            rer = _region_vector(
                inputs.exchange, inputs.system.regions, scenario, year,
                "real_exchange_rate_index_2023",
            )
            tariff = _region_product_matrix(
                inputs.tariff, inputs.system.regions, inputs.system.products,
                scenario, year, "tariff_wedge",
            )
            local_price_wedge = np.power(
                rer[:, None], inputs.exchange_pass_through
            ) * np.power(tariff / tariff_2023, inputs.tariff_pass_through)
            processes = _apply_process_response_horizon(
                inputs.system.processes,
                inputs.process_lag_by_name,
                year,
                benchmark_year,
            )
            processes = _apply_process_supply_shifters(
                processes, supply_shifter
            )
            result = solve_linked_equilibrium(
                inputs.system.base_primary_supply,
                inputs.system.base_final_demand,
                supply_elasticity,
                inputs.demand_elasticity,
                processes=processes,
                supply_shifter=supply_shifter,
                demand_shifter=demand_shifter,
                producer_price_wedge=local_price_wedge,
                consumer_price_wedge=local_price_wedge,
                initial_prices=initial_prices,
                region_names=inputs.system.regions,
                product_names=inputs.system.products,
                clearance_tolerance=float(solver["market_relative_residual"]),
                max_abs_log_price=float(solver["maximum_absolute_log_price"]),
                maximum_evaluations=int(solver["maximum_evaluations"]),
            )
            initial_prices = result.prices
            country, prices, processes, convergence = _result_frames(
                scenario, year, result, inputs.food_share_of_final_demand
            )
            result_frames.append(country)
            price_frames.append(prices)
            process_frames.append(processes)
            convergence_rows.append(convergence)
    results = pd.concat(result_frames, ignore_index=True)
    prices = pd.concat(price_frames, ignore_index=True)
    processes = pd.concat(process_frames, ignore_index=True)
    convergence = pd.DataFrame.from_records(convergence_rows)
    max_market = float(convergence["maximum_market_relative_residual"].max())
    max_accounting = float(convergence["maximum_accounting_absolute_residual_mt"].max())
    all_passed = (
        max_market <= float(solver["market_relative_residual"])
        and max_accounting <= float(solver["accounting_relative_residual"])
        and convergence[["converged", "accounting_passed"]].all().all()
    )
    report = {
        "status": "passed" if all_passed else "failed",
        "scenarios": selected_scenarios,
        "year_start": min(selected_years),
        "year_end": max(selected_years),
        "annual_solution_count": int(len(convergence)),
        "economy_count": len(inputs.system.regions),
        "commodity_count": len(inputs.system.products),
        "parameter_set": inputs.parameter_set,
        "parameter_table": inputs.parameter_table,
        "parameter_table_sha256": inputs.parameter_table_sha256,
        "simulation_config_sha256": inputs.simulation_config_sha256,
        "response_horizon_version": inputs.config["version"],
        "supply_response": "long_run_times_one_minus_lambda_power_since_2023",
        "demand_response": "long_run_without_horizon_multiplier",
        "result_row_count": int(len(results)),
        "maximum_market_relative_residual": max_market,
        "maximum_accounting_absolute_residual_mt": max_accounting,
        "all_years_converged": bool(all_passed),
        "bilateral_trade": False,
        "silk_dependency": False,
        "world_price_per_commodity": True,
    }
    if not all_passed:
        raise RuntimeError(f"One or more annual CASM-World solutions failed: {report}")
    return results, prices, processes, convergence, report


def write_simulation_outputs(
    inputs: SimulationInputs,
    *,
    scenarios: Sequence[str] | None = None,
    years: Iterable[int] | None = None,
) -> dict:
    results, prices, processes, convergence, report = run_simulation(
        inputs, scenarios=scenarios, years=years
    )
    outputs = inputs.config["outputs"]
    paths = {key: inputs.root / value for key, value in outputs.items()}
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(paths["results"], index=False)
    prices.to_csv(paths["prices"], index=False)
    processes.to_csv(paths["processing"], index=False)
    convergence.to_csv(paths["convergence"], index=False)
    report["outputs"] = {key: str(path) for key, path in paths.items() if key != "report"}
    paths["report"].write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--scenarios", nargs="*")
    parser.add_argument("--start-year", type=int, default=2023)
    parser.add_argument("--end-year", type=int, default=2050)
    args = parser.parse_args()
    inputs = load_simulation_inputs(args.project_root)
    report = write_simulation_outputs(
        inputs,
        scenarios=args.scenarios or None,
        years=range(args.start_year, args.end_year + 1),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
