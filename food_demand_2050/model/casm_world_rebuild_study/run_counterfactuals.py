"""Run China diet counterfactuals in the rebuilt CASM-World equilibrium."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from typing import Iterable

import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from casm_world.linked_equilibrium import solve_linked_equilibrium  # noqa: E402
from casm_world.sensitivity import (  # noqa: E402
    build_response_variant_inputs,
    load_variant_parameters,
    solve_linked_equilibrium_ces,
)
from casm_world.simulation import (  # noqa: E402
    SimulationInputs,
    _apply_process_response_horizon,
    _apply_process_supply_shifters,
    _effective_supply_elasticity,
    _region_product_matrix,
    _region_vector,
    _result_frames,
    load_simulation_inputs,
)


DEFAULT_CONFIG = Path(__file__).with_name("config.yaml")


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


def combine_food_and_nonfood_shifters(
    macro_shifter: np.ndarray,
    benchmark_food_share: np.ndarray,
    food_preference_multiplier: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return total-demand shifter and the resulting within-product food share.

    Food and non-food final uses retain the same product own-price elasticity.
    This identity changes only the food demand anchor while preserving the SSP
    path for feed and other final uses.
    """

    macro = np.asarray(macro_shifter, dtype=float)
    share = np.asarray(benchmark_food_share, dtype=float)
    preference = np.asarray(food_preference_multiplier, dtype=float)
    if macro.shape != share.shape or share.shape != preference.shape:
        raise ValueError("Demand-shifter arrays must have identical shapes")
    if (
        not np.isfinite(macro).all()
        or not np.isfinite(share).all()
        or not np.isfinite(preference).all()
        or (macro <= 0.0).any()
        or (preference <= 0.0).any()
        or (share < 0.0).any()
        or (share > 1.0).any()
    ):
        raise ValueError("Demand-shifter inputs are outside their valid domains")
    composition = (1.0 - share) + share * preference
    total_shifter = macro * composition
    realized_food_share = np.divide(
        share * preference,
        composition,
        out=np.zeros_like(share),
        where=composition > 0.0,
    )
    if (realized_food_share < 0.0).any() or (realized_food_share > 1.0).any():
        raise AssertionError("Derived food shares must lie in [0, 1]")
    return total_shifter, realized_food_share


def _load_diet_multipliers(config: dict, inputs: SimulationInputs) -> dict:
    path = _project_path(config["inputs"]["mapped_diet_paths"])
    frame = pd.read_csv(path)
    required = {
        "diet_pathway",
        "year",
        "world_commodity",
        "preference_multiplier_vs_baseline",
    }
    if not required <= set(frame):
        raise ValueError(f"Mapped diet paths are missing {sorted(required-set(frame))}")
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame["preference_multiplier_vs_baseline"] = pd.to_numeric(
        frame["preference_multiplier_vs_baseline"], errors="raise"
    ).astype(float)
    pathways = list(config["diet_pathways"])
    products = list(config["product_mapping"])
    years = list(range(int(config["benchmark_year"]), int(config["projection_end"]) + 1))
    expected = len(pathways) * len(products) * len(years)
    if len(frame) != expected or frame.duplicated(
        ["diet_pathway", "year", "world_commodity"]
    ).any():
        raise ValueError("Mapped diet path grid is incomplete or duplicated")
    if set(frame["diet_pathway"]) != set(pathways):
        raise ValueError("Mapped diet pathways do not match the study config")
    if set(frame["world_commodity"]) != set(products):
        raise ValueError("Mapped world products do not match the study config")
    unknown = set(products) - set(inputs.system.products)
    if unknown:
        raise ValueError(f"Diet mapping references unknown world products: {sorted(unknown)}")
    return {
        (str(row.diet_pathway), int(row.year), str(row.world_commodity)): float(
            row.preference_multiplier_vs_baseline
        )
        for row in frame.itertuples(index=False)
    }


def _policy_matrix(
    inputs: SimulationInputs,
    multipliers: dict,
    pathway: str,
    year: int,
) -> np.ndarray:
    matrix = np.ones_like(inputs.system.base_final_demand, dtype=float)
    region_index = {value: index for index, value in enumerate(inputs.system.regions)}
    product_index = {value: index for index, value in enumerate(inputs.system.products)}
    china = region_index["CHN"]
    for product in product_index:
        key = (pathway, int(year), product)
        if key in multipliers:
            matrix[china, product_index[product]] = multipliers[key]
    return matrix


def _year_inputs(inputs: SimulationInputs, base_ssp: str, year: int) -> dict:
    benchmark_year = int(inputs.config["benchmark_year"])
    population_2023 = _region_vector(
        inputs.drivers,
        inputs.system.regions,
        base_ssp,
        benchmark_year,
        "population_index_2025",
    )
    gdppc_2023 = _region_vector(
        inputs.drivers,
        inputs.system.regions,
        base_ssp,
        benchmark_year,
        "gdp_ppp_per_capita_index_2025",
    )
    tariff_2023 = _region_product_matrix(
        inputs.tariff,
        inputs.system.regions,
        inputs.system.products,
        base_ssp,
        benchmark_year,
        "tariff_wedge",
    )
    population = _region_vector(
        inputs.drivers,
        inputs.system.regions,
        base_ssp,
        year,
        "population_index_2025",
    ) / population_2023
    gdppc = _region_vector(
        inputs.drivers,
        inputs.system.regions,
        base_ssp,
        year,
        "gdp_ppp_per_capita_index_2025",
    ) / gdppc_2023
    macro_demand = population[:, None] * np.power(
        gdppc[:, None], inputs.income_elasticity
    )
    tfp = _region_vector(
        inputs.tfp, inputs.system.regions, base_ssp, year, "tfp_index_2023"
    )
    climate = _region_product_matrix(
        inputs.climate,
        inputs.system.regions,
        inputs.system.products,
        base_ssp,
        year,
        "climate_yield_index_2023",
    )
    supply_shifter = np.power(
        tfp[:, None], inputs.tfp_exponents[None, :]
    ) * climate
    rer = _region_vector(
        inputs.exchange,
        inputs.system.regions,
        base_ssp,
        year,
        "real_exchange_rate_index_2023",
    )
    tariff = _region_product_matrix(
        inputs.tariff,
        inputs.system.regions,
        inputs.system.products,
        base_ssp,
        year,
        "tariff_wedge",
    )
    local_price_wedge = np.power(
        rer[:, None], inputs.exchange_pass_through
    ) * np.power(tariff / tariff_2023, inputs.tariff_pass_through)
    supply_elasticity = _effective_supply_elasticity(
        inputs.supply_elasticity,
        inputs.supply_lag_by_product,
        year,
        benchmark_year,
    )
    processes = _apply_process_response_horizon(
        inputs.system.processes,
        inputs.process_lag_by_name,
        year,
        benchmark_year,
    )
    processes = _apply_process_supply_shifters(processes, supply_shifter)
    return {
        "macro_demand": macro_demand,
        "supply_shifter": supply_shifter,
        "local_price_wedge": local_price_wedge,
        "supply_elasticity": supply_elasticity,
        "processes": processes,
    }


def _solve(
    inputs: SimulationInputs,
    config: dict,
    multipliers: dict,
    *,
    base_ssp: str,
    pathway: str,
    year: int,
    initial_prices: np.ndarray,
    demand_model_form: str = "independent_product_own_price",
):
    prepared = _year_inputs(inputs, base_ssp, year)
    policy = _policy_matrix(inputs, multipliers, pathway, year)
    demand_shifter, food_share = combine_food_and_nonfood_shifters(
        prepared["macro_demand"], inputs.food_share_of_final_demand, policy
    )
    solver = inputs.config["solver"]
    common = dict(
        processes=prepared["processes"],
        supply_shifter=prepared["supply_shifter"],
        demand_shifter=demand_shifter,
        producer_price_wedge=prepared["local_price_wedge"],
        consumer_price_wedge=prepared["local_price_wedge"],
        initial_prices=initial_prices,
        region_names=inputs.system.regions,
        product_names=inputs.system.products,
        clearance_tolerance=float(solver["market_relative_residual"]),
        max_abs_log_price=float(solver["maximum_absolute_log_price"]),
        maximum_evaluations=int(solver["maximum_evaluations"]),
    )
    if demand_model_form == "independent_product_own_price":
        solved = solve_linked_equilibrium(
            inputs.system.base_primary_supply,
            inputs.system.base_final_demand,
            prepared["supply_elasticity"],
            inputs.demand_elasticity,
            **common,
        )
    elif demand_model_form == "five_inner_cobb_douglas_nests":
        sensitivity_config = yaml.safe_load(
            (PROJECT_ROOT / "config/sensitivity.yaml").read_text(encoding="utf-8")
        )
        ces = sensitivity_config["demand_substitution_ces"]
        solved = solve_linked_equilibrium_ces(
            inputs.system.base_primary_supply,
            inputs.system.base_final_demand,
            prepared["supply_elasticity"],
            inputs.demand_elasticity,
            ces_nests=ces["nests"],
            sigma=float(ces["sigma"]),
            **common,
        )
    else:
        raise ValueError(f"Unknown demand model form: {demand_model_form}")
    return solved, food_share


def _tag(frame: pd.DataFrame, base_ssp: str, pathway: str) -> pd.DataFrame:
    result = frame.copy()
    result.insert(1, "base_ssp", base_ssp)
    result.insert(2, "diet_pathway", pathway)
    return result


def _run_main(inputs: SimulationInputs, config: dict, multipliers: dict):
    country_frames: list[pd.DataFrame] = []
    price_frames: list[pd.DataFrame] = []
    process_frames: list[pd.DataFrame] = []
    convergence_rows: list[dict] = []
    pathways = list(config["diet_pathways"])
    for base_ssp, raw_years in config["main_run_grid"].items():
        years: Iterable[int]
        if raw_years == "annual":
            years = range(int(config["benchmark_year"]), int(config["projection_end"]) + 1)
        else:
            years = [int(value) for value in raw_years]
        for pathway in pathways:
            scenario = f"{base_ssp}__{pathway}"
            initial_prices = np.ones(len(inputs.system.products), dtype=float)
            for year in years:
                solved, food_share = _solve(
                    inputs,
                    config,
                    multipliers,
                    base_ssp=base_ssp,
                    pathway=pathway,
                    year=int(year),
                    initial_prices=initial_prices,
                )
                initial_prices = solved.prices
                country, prices, processes, convergence = _result_frames(
                    scenario, int(year), solved, food_share
                )
                country_frames.append(_tag(country, base_ssp, pathway))
                price_frames.append(_tag(prices, base_ssp, pathway))
                process_frames.append(_tag(processes, base_ssp, pathway))
                convergence.update(
                    {"base_ssp": base_ssp, "diet_pathway": pathway}
                )
                convergence_rows.append(convergence)
                print(
                    f"main {scenario} {year}: max residual "
                    f"{convergence['maximum_market_relative_residual']:.3e}"
                )
    return (
        pd.concat(country_frames, ignore_index=True),
        pd.concat(price_frames, ignore_index=True),
        pd.concat(process_frames, ignore_index=True),
        pd.DataFrame.from_records(convergence_rows),
    )


def _run_sensitivity(
    inputs: SimulationInputs,
    config: dict,
    multipliers: dict,
    main_country: pd.DataFrame,
    main_prices: pd.DataFrame,
    main_convergence: pd.DataFrame,
):
    settings = config["sensitivity"]
    base_ssp = str(settings["base_ssp"])
    year = int(settings["year"])
    pathways = list(config["diet_pathways"])
    country_frames: list[pd.DataFrame] = []
    price_frames: list[pd.DataFrame] = []
    convergence_rows: list[dict] = []

    central_country = main_country[
        main_country["base_ssp"].eq(base_ssp)
        & main_country["diet_pathway"].isin(pathways)
        & main_country["year"].eq(year)
    ].copy()
    central_prices = main_prices[
        main_prices["base_ssp"].eq(base_ssp)
        & main_prices["diet_pathway"].isin(pathways)
        & main_prices["year"].eq(year)
    ].copy()
    central_convergence = main_convergence[
        main_convergence["base_ssp"].eq(base_ssp)
        & main_convergence["diet_pathway"].isin(pathways)
        & main_convergence["year"].eq(year)
    ].copy()
    for frame in (central_country, central_prices, central_convergence):
        frame.insert(0, "response_variant", "V2_CENTRAL")
        frame.insert(1, "demand_model_form", "independent_product_own_price")
    country_frames.append(central_country)
    price_frames.append(central_prices)
    convergence_rows.extend(central_convergence.to_dict("records"))

    sensitivity_config = yaml.safe_load(
        (PROJECT_ROOT / "config/sensitivity.yaml").read_text(encoding="utf-8")
    )
    parameters = load_variant_parameters(PROJECT_ROOT, sensitivity_config, inputs)
    for variant in settings["response_variants"]:
        if variant == "V2_CENTRAL":
            continue
        variant_inputs, _ = build_response_variant_inputs(
            inputs, parameters, sensitivity_config, str(variant)
        )
        for pathway in pathways:
            scenario = f"{base_ssp}__{pathway}"
            solved, food_share = _solve(
                variant_inputs,
                config,
                multipliers,
                base_ssp=base_ssp,
                pathway=pathway,
                year=year,
                initial_prices=np.ones(len(inputs.system.products)),
            )
            country, prices, _, convergence = _result_frames(
                scenario, year, solved, food_share
            )
            country = _tag(country, base_ssp, pathway)
            prices = _tag(prices, base_ssp, pathway)
            for frame in (country, prices):
                frame.insert(0, "response_variant", str(variant))
                frame.insert(1, "demand_model_form", "independent_product_own_price")
            country_frames.append(country)
            price_frames.append(prices)
            convergence.update(
                {
                    "base_ssp": base_ssp,
                    "diet_pathway": pathway,
                    "response_variant": str(variant),
                    "demand_model_form": "independent_product_own_price",
                }
            )
            convergence_rows.append(convergence)
            print(f"sensitivity {variant} {pathway} {year}")

    ces_variant = str(settings["demand_model_form_variant"])
    for pathway in pathways:
        scenario = f"{base_ssp}__{pathway}"
        solved, food_share = _solve(
            inputs,
            config,
            multipliers,
            base_ssp=base_ssp,
            pathway=pathway,
            year=year,
            initial_prices=np.ones(len(inputs.system.products)),
            demand_model_form="five_inner_cobb_douglas_nests",
        )
        country, prices, _, convergence = _result_frames(
            scenario, year, solved, food_share
        )
        country = _tag(country, base_ssp, pathway)
        prices = _tag(prices, base_ssp, pathway)
        for frame in (country, prices):
            frame.insert(0, "response_variant", ces_variant)
            frame.insert(1, "demand_model_form", "five_inner_cobb_douglas_nests")
        country_frames.append(country)
        price_frames.append(prices)
        convergence.update(
            {
                "base_ssp": base_ssp,
                "diet_pathway": pathway,
                "response_variant": ces_variant,
                "demand_model_form": "five_inner_cobb_douglas_nests",
            }
        )
        convergence_rows.append(convergence)
        print(f"sensitivity {ces_variant} {pathway} {year}")
    return (
        pd.concat(country_frames, ignore_index=True),
        pd.concat(price_frames, ignore_index=True),
        pd.DataFrame.from_records(convergence_rows),
    )


def _validate_common_benchmark(country: pd.DataFrame, tolerance: float = 1.0e-8) -> float:
    base = country[country["year"].eq(2023)].copy()
    keys = ["economy_id", "commodity"]
    values = [
        "primary_supply_mt",
        "processing_supply_mt",
        "production_mt",
        "final_demand_mt",
        "food_demand_mt",
        "processing_demand_mt",
        "demand_mt",
        "net_import_mt",
    ]
    spread = base.groupby(keys)[values].agg(lambda series: series.max() - series.min())
    maximum = float(spread.to_numpy(float).max(initial=0.0))
    if maximum > tolerance:
        raise AssertionError(f"Counterfactuals do not share the benchmark: {maximum}")
    return maximum


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    inputs = load_simulation_inputs(PROJECT_ROOT)
    multipliers = _load_diet_multipliers(config, inputs)
    country, prices, processes, convergence = _run_main(inputs, config, multipliers)
    benchmark_error = _validate_common_benchmark(country)
    sensitivity_country, sensitivity_prices, sensitivity_convergence = _run_sensitivity(
        inputs, config, multipliers, country, prices, convergence
    )

    outputs = {key: _project_path(value) for key, value in config["outputs"].items()}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    country.to_csv(outputs["country_product"], index=False, compression="gzip")
    prices.to_csv(outputs["world_prices"], index=False, lineterminator="\n")
    processes.to_csv(outputs["processing"], index=False, compression="gzip")
    convergence.to_csv(outputs["convergence"], index=False, lineterminator="\n")
    sensitivity_country.to_csv(
        outputs["sensitivity_country_product"], index=False, compression="gzip"
    )
    sensitivity_prices.to_csv(
        outputs["sensitivity_world_prices"], index=False, lineterminator="\n"
    )
    sensitivity_convergence.to_csv(
        outputs["sensitivity_convergence"], index=False, lineterminator="\n"
    )
    maximum_market = float(convergence["maximum_market_relative_residual"].max())
    maximum_accounting = float(
        convergence["maximum_accounting_absolute_residual_mt"].max()
    )
    sensitivity_market = float(
        sensitivity_convergence["maximum_market_relative_residual"].max()
    )
    report = {
        "status": "passed",
        "study_id": config["study_id"],
        "scenario_type": config["interpretation"]["scenario_type"],
        "model_source": "isolated copy of /root/data/CASM/casm_world_rebuild_2050",
        "core_model_files_modified": False,
        "main_solution_count": int(len(convergence)),
        "sensitivity_solution_count": int(len(sensitivity_convergence)),
        "country_product_row_count": int(len(country)),
        "maximum_market_relative_residual": maximum_market,
        "maximum_accounting_absolute_residual_mt": maximum_accounting,
        "sensitivity_maximum_market_relative_residual": sensitivity_market,
        "common_2023_benchmark_maximum_absolute_error_mt": benchmark_error,
        "main_grid": config["main_run_grid"],
        "pathways": list(config["diet_pathways"]),
        "mapped_products": list(config["product_mapping"]),
        "excluded_prior_casm_foods": config["excluded_prior_casm_foods"],
        "food_nonfood_decomposition": (
            "Food preference multipliers change only the China food component; "
            "non-food final demand keeps the SSP macro shifter."
        ),
        "ces_food_decomposition_warning": (
            "CES sensitivity is used for prices, production and net trade only; its "
            "within-product food split is not used for nutrition claims."
        ),
        "inputs_sha256": {
            "study_config": _sha256(args.config),
            "mapped_diet_paths": _sha256(
                _project_path(config["inputs"]["mapped_diet_paths"])
            ),
            "simulation_config": inputs.simulation_config_sha256,
            "parameter_table": inputs.parameter_table_sha256,
        },
        "outputs": {
            key: {"path": str(path), "sha256": _sha256(path)}
            for key, path in outputs.items()
            if path.is_file() and key != "run_report"
        },
    }
    outputs["run_report"].write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {outputs['country_product']} ({len(country)} rows)")
    print(f"wrote {outputs['run_report']}")


if __name__ == "__main__":
    main()

