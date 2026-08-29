"""Reproducible CASM-World V2 parameter and TFP sensitivity runs.

The runner deliberately writes only below ``outputs/sensitivity``.  It solves
the full annual 2023--2050 path for every SSP so each solve receives the same
warm-start convention as the central simulation, then retains compact price,
convergence and reporting-group summaries.  It implements all five inner-CES
nests frozen in V2 section 8.4 as one structural case.  The shared
crop-resource supply equation in section 8.3 remains explicitly pending.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
import yaml

from casm_world.analysis import aggregate_solved_results, load_analysis_config
from casm_world.linked_equilibrium import (
    LinkedEquilibriumConvergenceError,
    LinkedEquilibriumInputError,
    LinkedEquilibriumResult,
    ProcessResult,
    _array,
    _names,
    _prepare_process,
)
from casm_world.simulation import (
    SimulationInputs,
    _apply_process_response_horizon,
    _apply_process_supply_shifters,
    _effective_supply_elasticity,
    _region_product_matrix,
    _region_vector,
    _result_frames,
    load_simulation_inputs,
    run_simulation,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "sensitivity.yaml"
EXPECTED_SCENARIOS = ("SSP1", "SSP2", "SSP3", "SSP4", "SSP5")
EXPECTED_RESPONSE_VARIANTS = (
    "V2_LOW_RESPONSE",
    "V2_CENTRAL",
    "V2_HIGH_RESPONSE",
)
EXPECTED_TFP_VARIANTS = ("TFP_SLOW", "TFP_FAST")
PARAMETER_BASE_COLUMNS = (
    "supply_price_elasticity",
    "demand_price_elasticity",
    "income_elasticity",
)
QUANTITY_COLUMNS = (
    "primary_supply_mt",
    "processing_supply_mt",
    "production_mt",
    "final_demand_mt",
    "food_demand_mt",
    "processing_demand_mt",
    "demand_mt",
    "net_import_mt",
)


class SensitivityError(ValueError):
    """Raised when the frozen sensitivity contract is incomplete or invalid."""


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SensitivityError(f"{label} must be a mapping")
    return value


def _project_path(root: Path, relative: object, label: str) -> Path:
    raw = Path(str(relative))
    if raw.is_absolute():
        raise SensitivityError(f"{label} must be relative to the project")
    resolved = (root / raw).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise SensitivityError(f"{label} escapes the project: {raw}") from exc
    return resolved


def _output_path(root: Path, relative: object, label: str) -> Path:
    path = _project_path(root, relative, label)
    sensitivity_root = (root / "outputs" / "sensitivity").resolve()
    try:
        path.relative_to(sensitivity_root)
    except ValueError as exc:
        raise SensitivityError(
            f"{label} must remain below outputs/sensitivity"
        ) from exc
    return path


def load_sensitivity_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Load and fail-closed validate the frozen V2 sensitivity specification."""

    config_path = Path(path).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config = dict(_mapping(config, "sensitivity configuration"))
    if int(config.get("schema_version", -1)) != 1:
        raise SensitivityError("sensitivity schema_version must equal 1")
    if int(config.get("benchmark_year", -1)) != 2023:
        raise SensitivityError("sensitivity benchmark year must equal 2023")
    if int(config.get("projection_end", -1)) != 2050:
        raise SensitivityError("sensitivity projection end must equal 2050")
    if tuple(config.get("scenarios", ())) != EXPECTED_SCENARIOS:
        raise SensitivityError("sensitivity scenarios must be SSP1--SSP5")
    if config.get("retained_summary_years") != [2023, 2035, 2050]:
        raise SensitivityError("retained sensitivity years must be 2023/2035/2050")
    if config.get("annual_warm_start_required") is not True:
        raise SensitivityError("annual 2023--2050 warm-start runs are mandatory")

    response = _mapping(
        config.get("parameter_response_variants"),
        "parameter_response_variants",
    )
    if tuple(response) != EXPECTED_RESPONSE_VARIANTS:
        raise SensitivityError("response variants must be low/central/high in order")
    expected_suffix = {
        "V2_LOW_RESPONSE": "low",
        "V2_CENTRAL": "central",
        "V2_HIGH_RESPONSE": "high",
    }
    for variant, suffix in expected_suffix.items():
        if _mapping(response[variant], variant).get("column_suffix") != suffix:
            raise SensitivityError(f"{variant} must use the {suffix} parameter columns")

    tfp = _mapping(config.get("tfp_variants"), "tfp_variants")
    if not set(EXPECTED_TFP_VARIANTS) <= set(tfp):
        raise SensitivityError("TFP_SLOW and TFP_FAST must both be configured")
    if tfp.get("central_reference_variant") != "V2_CENTRAL":
        raise SensitivityError("TFP central reference must be V2_CENTRAL")
    if int(tfp.get("unchanged_through_year", -1)) != 2035:
        raise SensitivityError("TFP sensitivities must be unchanged through 2035")
    multipliers = {
        name: float(_mapping(tfp[name], name)["post_2035_positive_log_growth_multiplier"])
        for name in EXPECTED_TFP_VARIANTS
    }
    if multipliers != {"TFP_SLOW": 0.75, "TFP_FAST": 1.25}:
        raise SensitivityError("TFP multipliers must be 0.75 and 1.25")
    if tfp.get("annual_log_growth_bounds") != [-0.005, 0.035]:
        raise SensitivityError("TFP annual log-growth bounds must be [-0.005, 0.035]")
    if tfp.get("retain_nonpositive_rates") is not True:
        raise SensitivityError("non-positive TFP rates must remain unscaled")

    basket = list(config.get("primary_basket", ()))
    if len(basket) != 13 or len(set(basket)) != 13:
        raise SensitivityError("primary basket must contain 13 unique products")
    foods = list(config.get("major_food_prices", ()))
    if len(foods) != 9 or len(set(foods)) != 9:
        raise SensitivityError("major-food price screen must contain nine products")
    process = _mapping(
        config.get("process_long_run_elasticities"),
        "process_long_run_elasticities",
    )
    for name, raw in process.items():
        definition = _mapping(raw, f"process {name}")
        method = definition.get("method")
        if method == "fixed":
            values = [float(definition[key]) for key in ("low", "central", "high")]
            if not all(isfinite(value) and value >= 0.0 for value in values):
                raise SensitivityError(f"process {name} has an invalid response")
        elif method == "product_parameter":
            if not str(definition.get("parameter_product", "")):
                raise SensitivityError(f"process {name} lacks parameter_product")
        else:
            raise SensitivityError(f"process {name} has unknown method {method!r}")

    ces = _mapping(config.get("demand_substitution_ces"), "demand_substitution_ces")
    if ces.get("enabled") is not True or ces.get("variant") != "DEMAND_SUBSTITUTION_CES":
        raise SensitivityError("the frozen demand-CES sensitivity must be enabled")
    if float(ces.get("sigma", -1.0)) != 1.0:
        raise SensitivityError("every frozen inner CES nest must use sigma=1")
    expected_nests = {
        "grains": ["RIC", "WHE", "CRN", "OCG"],
        "vegetable_oils": ["SBO", "NBO", "RBO", "OTO"],
        "meals_feed_byproducts": ["SBM", "NBM", "RBM", "DDG"],
        "meats": ["BFV", "PRK", "PLM"],
        "processed_dairy": ["BUT", "CHE", "NDM", "FMK", "WDM", "ODA"],
    }
    if ces.get("nests") != expected_nests:
        raise SensitivityError("all five frozen section-8.4 nests must be configured")
    nested_products = [product for products in expected_nests.values() for product in products]
    if len(nested_products) != len(set(nested_products)):
        raise SensitivityError("a product cannot occur in more than one CES nest")
    expected_methods = {
        "share_basis": "frozen_2023_final_demand_quantity",
        "composite_price": "cobb_douglas_frozen_2023_quantity_share",
        "outer_demand_shifter": (
            "frozen_share_arithmetic_mean_of_central_product_shifters"
        ),
        "outer_price_elasticity": (
            "frozen_share_arithmetic_mean_of_central_product_elasticities"
        ),
    }
    for field, value in expected_methods.items():
        if ces.get(field) != value:
            raise SensitivityError(f"unexpected demand-CES convention for {field}")

    pending = set(config.get("not_implemented_structural_sensitivities", ()))
    if pending != {"SHARED_CROP_RESOURCE"}:
        raise SensitivityError("structural sensitivity pending list changed")
    outputs = _mapping(config.get("outputs"), "outputs")
    required_outputs = {
        "directory",
        "annual_convergence",
        "annual_world_prices",
        "major_food_prices",
        "primary_basket_groups",
        "materiality_screen",
        "report",
    }
    if set(outputs) != required_outputs:
        raise SensitivityError("unexpected sensitivity output contract")
    root = config_path.parents[1]
    for key, value in outputs.items():
        _output_path(root, value, f"outputs.{key}")
    return config


def _parameter_matrix(
    parameters: pd.DataFrame,
    regions: Sequence[str],
    products: Sequence[str],
    column: str,
) -> np.ndarray:
    if column not in parameters:
        raise SensitivityError(f"parameter table lacks required variant column {column}")
    table = parameters.pivot(index="economy_id", columns="commodity", values=column)
    table = table.reindex(index=regions, columns=products)
    if table.isna().any().any():
        raise SensitivityError(f"parameter variant column {column} is incomplete")
    values = table.to_numpy(float)
    if not np.isfinite(values).all():
        raise SensitivityError(f"parameter variant column {column} is non-finite")
    return values


def _canonical_frame_sha256(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    ordered = frame.sort_values(["economy_id", "commodity"])[list(columns)]
    payload = ordered.to_csv(index=False, float_format="%.17g", lineterminator="\n")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_variant_parameters(
    root: Path,
    config: Mapping[str, Any],
    inputs: SimulationInputs,
) -> pd.DataFrame:
    """Load the three complete parameter grids promised by the V2 audit."""

    path = _project_path(root, config["inputs"]["parameter_table"], "parameter_table")
    parameters = pd.read_csv(path)
    keys = ["economy_id", "commodity"]
    expected = len(inputs.system.regions) * len(inputs.system.products)
    if len(parameters) != expected or parameters.duplicated(keys).any():
        raise SensitivityError(f"parameter table must contain {expected} unique rows")
    if set(parameters["economy_id"]) != set(inputs.system.regions):
        raise SensitivityError("parameter economies do not match the simulation system")
    if set(parameters["commodity"]) != set(inputs.system.products):
        raise SensitivityError("parameter products do not match the simulation system")
    required = {
        f"{base}_{suffix}"
        for base in PARAMETER_BASE_COLUMNS
        for suffix in ("low", "central", "high")
    }
    missing = required - set(parameters)
    if missing:
        raise SensitivityError(
            "V2 parameter table lacks frozen low/high columns; parameters.py must "
            f"produce them before sensitivities run: {sorted(missing)}"
        )
    for base in PARAMETER_BASE_COLUMNS:
        if base not in parameters:
            raise SensitivityError(f"parameter table lacks central interface {base}")
        if not np.array_equal(
            parameters[base].to_numpy(float),
            parameters[f"{base}_central"].to_numpy(float),
        ):
            raise SensitivityError(f"{base} is not exactly its frozen central column")
    return parameters


def _variant_processes(
    inputs: SimulationInputs,
    supply_elasticity: np.ndarray,
    suffix: str,
    config: Mapping[str, Any],
):
    definitions = config["process_long_run_elasticities"]
    process_names = {process.name for process in inputs.system.processes}
    if process_names != set(definitions):
        raise SensitivityError(
            "process sensitivity whitelist mismatch: "
            f"model_only={sorted(process_names-set(definitions))}, "
            f"config_only={sorted(set(definitions)-process_names)}"
        )
    product_index = {product: index for index, product in enumerate(inputs.system.products)}
    variants = []
    for process in inputs.system.processes:
        definition = definitions[process.name]
        if definition["method"] == "fixed":
            elasticity = np.full(
                len(inputs.system.regions), float(definition[suffix]), dtype=float
            )
        else:
            product = str(definition["parameter_product"])
            if product not in product_index:
                raise SensitivityError(
                    f"process {process.name} references unknown product {product}"
                )
            elasticity = np.array(supply_elasticity[:, product_index[product]], copy=True)
        variants.append(replace(process, elasticity=elasticity))
    return tuple(variants)


def build_response_variant_inputs(
    inputs: SimulationInputs,
    parameters: pd.DataFrame,
    config: Mapping[str, Any],
    variant: str,
) -> tuple[SimulationInputs, str]:
    """Inject one internally coherent low/central/high LR response set."""

    variants = config["parameter_response_variants"]
    if variant not in variants:
        raise SensitivityError(f"unknown response variant {variant}")
    suffix = str(variants[variant]["column_suffix"])
    regions = inputs.system.regions
    products = inputs.system.products
    supply = _parameter_matrix(
        parameters, regions, products, f"supply_price_elasticity_{suffix}"
    )
    demand = _parameter_matrix(
        parameters, regions, products, f"demand_price_elasticity_{suffix}"
    )
    income = _parameter_matrix(
        parameters, regions, products, f"income_elasticity_{suffix}"
    )
    if (supply <= 0.0).any() or (demand > 0.0).any() or (income < 0.0).any():
        raise SensitivityError(f"{variant} has invalid own-price or income responses")
    processes = _variant_processes(inputs, supply, suffix, config)
    system = replace(inputs.system, processes=processes)
    variant_inputs = replace(
        inputs,
        parameter_set=variant,
        supply_elasticity=supply,
        demand_elasticity=demand,
        income_elasticity=income,
        system=system,
    )
    if variant == "V2_CENTRAL":
        arrays = (
            (supply, inputs.supply_elasticity, "supply"),
            (demand, inputs.demand_elasticity, "demand"),
            (income, inputs.income_elasticity, "income"),
        )
        for selected, loaded, label in arrays:
            if not np.array_equal(selected, loaded):
                raise SensitivityError(
                    f"central {label} sensitivity grid differs from simulation input"
                )
        for selected, loaded in zip(processes, inputs.system.processes):
            if not np.array_equal(selected.elasticity, loaded.elasticity):
                raise SensitivityError(
                    f"central process response differs for {selected.name}"
                )
    columns = ["economy_id", "commodity"] + [
        f"{base}_{suffix}" for base in PARAMETER_BASE_COLUMNS
    ]
    return variant_inputs, _canonical_frame_sha256(parameters, columns)


def scale_post_2035_tfp(
    tfp: pd.DataFrame,
    multiplier: float,
    *,
    unchanged_through_year: int = 2035,
    annual_log_growth_bounds: tuple[float, float] = (-0.005, 0.035),
) -> pd.DataFrame:
    """Scale only positive post-2035 annual log TFP growth and rebuild indices."""

    required = {"scenario", "economy_id", "year", "tfp_index_2023"}
    if not required <= set(tfp):
        raise SensitivityError(f"TFP input is missing {sorted(required-set(tfp))}")
    keys = ["scenario", "economy_id", "year"]
    if tfp.duplicated(keys).any():
        raise SensitivityError("TFP input contains duplicate economy-year rows")
    if not isfinite(float(multiplier)) or float(multiplier) <= 0.0:
        raise SensitivityError("TFP growth multiplier must be finite and positive")
    lower, upper = map(float, annual_log_growth_bounds)
    if not (isfinite(lower) and isfinite(upper) and lower <= 0.0 < upper):
        raise SensitivityError("TFP log-growth bounds are invalid")

    result = tfp.copy()
    result["year"] = pd.to_numeric(result["year"], errors="raise").astype(int)
    result["tfp_index_2023"] = pd.to_numeric(
        result["tfp_index_2023"], errors="raise"
    )
    if (
        not np.isfinite(result["tfp_index_2023"].to_numpy(float)).all()
        or result["tfp_index_2023"].le(0.0).any()
    ):
        raise SensitivityError("TFP indices must be finite and strictly positive")
    for _, group in result.groupby(["scenario", "economy_id"], sort=False):
        ordered = group.sort_values("year")
        years = ordered["year"].to_numpy(int)
        if unchanged_through_year not in set(years):
            raise SensitivityError("every TFP path must contain the 2035 anchor")
        if len(years) > 1 and not np.all(np.diff(years) == 1):
            raise SensitivityError("TFP paths must be annual and consecutive")
        original = ordered["tfp_index_2023"].to_numpy(float)
        rebuilt = original.copy()
        for position in range(1, len(years)):
            if years[position] <= unchanged_through_year:
                continue
            raw_rate = float(np.log(original[position] / original[position - 1]))
            adjusted = raw_rate * float(multiplier) if raw_rate > 0.0 else raw_rate
            adjusted = min(max(adjusted, lower), upper)
            rebuilt[position] = rebuilt[position - 1] * float(np.exp(adjusted))
        result.loc[ordered.index, "tfp_index_2023"] = rebuilt
    before = tfp["year"].astype(int).le(unchanged_through_year)
    if not np.array_equal(
        result.loc[before, "tfp_index_2023"].to_numpy(float),
        tfp.loc[before, "tfp_index_2023"].to_numpy(float),
    ):
        raise AssertionError("TFP sensitivity changed an index through 2035")
    return result


def _prepare_ces_nests(
    base_final_demand: np.ndarray,
    product_names: Sequence[str],
    nests: Mapping[str, Sequence[str]],
) -> tuple[tuple[str, np.ndarray, np.ndarray, np.ndarray], ...]:
    """Freeze one 2023 quantity-share matrix for each disjoint inner nest."""

    product_index = {str(product): index for index, product in enumerate(product_names)}
    used: set[str] = set()
    prepared = []
    for name, products in nests.items():
        labels = [str(product) for product in products]
        unknown = set(labels) - set(product_index)
        overlap = set(labels) & used
        if unknown or overlap or len(labels) < 2:
            raise SensitivityError(
                f"invalid CES nest {name}: unknown={sorted(unknown)}, "
                f"overlap={sorted(overlap)}, product_count={len(labels)}"
            )
        used.update(labels)
        indices = np.array([product_index[product] for product in labels], dtype=int)
        base = np.asarray(base_final_demand[:, indices], dtype=float)
        totals = base.sum(axis=1)
        shares = np.divide(
            base,
            totals[:, None],
            out=np.zeros_like(base),
            where=totals[:, None] > 0.0,
        )
        active = totals > 0.0
        if active.any() and not np.allclose(
            shares[active].sum(axis=1), 1.0, atol=1.0e-14, rtol=0.0
        ):
            raise AssertionError(f"CES nest shares do not sum to one for {name}")
        prepared.append((str(name), indices, shares, active))
    return tuple(prepared)


def _evaluate_ces(
    log_prices: np.ndarray,
    *,
    base_primary_supply: np.ndarray,
    base_final_demand: np.ndarray,
    supply_elasticity: np.ndarray,
    demand_elasticity: np.ndarray,
    supply_shifter: np.ndarray,
    demand_shifter: np.ndarray,
    producer_price_wedge: np.ndarray,
    consumer_price_wedge: np.ndarray,
    processes,
    ces_nests: tuple[tuple[str, np.ndarray, np.ndarray, np.ndarray], ...],
    sigma: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, tuple[ProcessResult, ...]]:
    """Evaluate supply, processing and the frozen inner-CES final demand."""

    world_prices = np.exp(log_prices)[None, :]
    producer_prices = world_prices * producer_price_wedge
    consumer_prices = world_prices * consumer_price_wedge
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        primary = (
            base_primary_supply
            * supply_shifter
            * np.power(producer_prices, supply_elasticity)
        )
        # Products outside a configured nest retain their central independent
        # demand equation.  Nested columns are replaced below as one group.
        final = (
            base_final_demand
            * demand_shifter
            * np.power(consumer_prices, demand_elasticity)
        )
        log_consumer_prices = np.log(consumer_prices)
        for _, indices, shares, active in ces_nests:
            if not active.any():
                continue
            local_prices = consumer_prices[:, indices]
            log_composite = np.sum(shares * log_consumer_prices[:, indices], axis=1)
            composite_price = np.exp(log_composite)
            outer_shifter = np.sum(shares * demand_shifter[:, indices], axis=1)
            outer_elasticity = np.sum(shares * demand_elasticity[:, indices], axis=1)
            outer_scale = outer_shifter * np.power(composite_price, outer_elasticity)
            allocation = np.power(
                local_prices / composite_price[:, None], -float(sigma)
            )
            nested = base_final_demand[:, indices] * outer_scale[:, None] * allocation
            final[:, indices] = np.where(active[:, None], nested, final[:, indices])

    process_supply = np.zeros_like(primary)
    process_demand = np.zeros_like(final)
    process_results: list[ProcessResult] = []
    log_producer_prices = np.log(producer_prices)
    for process in processes:
        output_signal = np.sum(process.output_weights * log_producer_prices, axis=1)
        input_signal = np.sum(process.input_weights * log_producer_prices, axis=1)
        activity = (
            process.base_activity
            * process.shifter
            * np.exp(process.elasticity * (output_signal - input_signal))
        )
        outputs = activity[:, None] * process.outputs
        inputs = activity[:, None] * process.inputs
        process_supply += outputs
        process_demand += inputs
        process_results.append(ProcessResult(process.name, activity, inputs, outputs))
    return primary, process_supply, final, process_demand, tuple(process_results)


def solve_linked_equilibrium_ces(
    base_primary_supply,
    base_final_demand,
    supply_elasticity,
    demand_elasticity,
    *,
    ces_nests: Mapping[str, Sequence[str]],
    sigma: float = 1.0,
    processes=(),
    supply_shifter=1.0,
    demand_shifter=1.0,
    producer_price_wedge=1.0,
    consumer_price_wedge=1.0,
    initial_prices=1.0,
    region_names: Sequence[str] | None = None,
    product_names: Sequence[str] | None = None,
    clearance_tolerance: float = 1.0e-9,
    max_abs_log_price: float = 7.0,
    maximum_evaluations: int = 2_000,
) -> LinkedEquilibriumResult:
    """Solve the linked system with all frozen section-8.4 nests together."""

    primary_base = np.asarray(base_primary_supply, dtype=float)
    final_base = np.asarray(base_final_demand, dtype=float)
    if (
        primary_base.ndim != 2
        or 0 in primary_base.shape
        or final_base.shape != primary_base.shape
    ):
        raise LinkedEquilibriumInputError(
            "base_primary_supply and base_final_demand must be equal non-empty matrices"
        )
    if (
        not np.isfinite(primary_base).all()
        or not np.isfinite(final_base).all()
        or (primary_base < 0.0).any()
        or (final_base < 0.0).any()
    ):
        raise LinkedEquilibriumInputError("CES base quantities must be finite and nonnegative")
    if not isfinite(float(sigma)) or float(sigma) <= 0.0:
        raise LinkedEquilibriumInputError("CES sigma must be finite and positive")
    shape = primary_base.shape
    regions_n, products_n = shape
    supply_eps = _array("supply_elasticity", supply_elasticity, shape)
    demand_eps = _array("demand_elasticity", demand_elasticity, shape)
    supply_shift = _array("supply_shifter", supply_shifter, shape)
    demand_shift = _array("demand_shifter", demand_shifter, shape)
    producer_wedge = _array("producer_price_wedge", producer_price_wedge, shape)
    consumer_wedge = _array("consumer_price_wedge", consumer_price_wedge, shape)
    initial = _array("initial_prices", initial_prices, (products_n,))
    if (supply_eps < 0.0).any() or (demand_eps > 0.0).any():
        raise LinkedEquilibriumInputError("CES response signs are invalid")
    if (
        (supply_shift < 0.0).any()
        or (demand_shift < 0.0).any()
        or (producer_wedge <= 0.0).any()
        or (consumer_wedge <= 0.0).any()
        or (initial <= 0.0).any()
    ):
        raise LinkedEquilibriumInputError("CES shifters/prices are invalid")
    prepared_processes = tuple(_prepare_process(process, shape) for process in processes)
    regions = _names(region_names, regions_n, "region")
    products = _names(product_names, products_n, "product")
    prepared_nests = _prepare_ces_nests(final_base, products, ces_nests)

    def residual(log_price_vector: np.ndarray) -> np.ndarray:
        try:
            primary, process_supply, final, process_demand, _ = _evaluate_ces(
                log_price_vector,
                base_primary_supply=primary_base,
                base_final_demand=final_base,
                supply_elasticity=supply_eps,
                demand_elasticity=demand_eps,
                supply_shifter=supply_shift,
                demand_shifter=demand_shift,
                producer_price_wedge=producer_wedge,
                consumer_price_wedge=consumer_wedge,
                processes=prepared_processes,
                ces_nests=prepared_nests,
                sigma=float(sigma),
            )
        except FloatingPointError:
            return np.full(products_n, 1.0e6)
        supply = (primary + process_supply).sum(axis=0)
        demand = (final + process_demand).sum(axis=0)
        if (supply <= 0.0).any() or (demand <= 0.0).any():
            raise LinkedEquilibriumInputError(
                "every CES product needs positive global supply and demand"
            )
        return np.log(supply) - np.log(demand)

    solution = least_squares(
        residual,
        np.log(initial),
        bounds=(-float(max_abs_log_price), float(max_abs_log_price)),
        xtol=1.0e-13,
        ftol=1.0e-13,
        gtol=1.0e-13,
        max_nfev=int(maximum_evaluations),
    )
    log_prices = solution.x
    primary, process_supply, final, process_demand, process_results = _evaluate_ces(
        log_prices,
        base_primary_supply=primary_base,
        base_final_demand=final_base,
        supply_elasticity=supply_eps,
        demand_elasticity=demand_eps,
        supply_shifter=supply_shift,
        demand_shifter=demand_shift,
        producer_price_wedge=producer_wedge,
        consumer_price_wedge=consumer_wedge,
        processes=prepared_processes,
        ces_nests=prepared_nests,
        sigma=float(sigma),
    )
    total_supply = primary + process_supply
    total_demand = final + process_demand
    global_supply = total_supply.sum(axis=0)
    global_demand = total_demand.sum(axis=0)
    relative = (global_supply - global_demand) / np.maximum(global_supply, global_demand)
    if not solution.success or np.max(np.abs(relative)) > float(clearance_tolerance):
        raise LinkedEquilibriumConvergenceError(
            "CES linked market did not converge: "
            f"success={solution.success}, max residual={np.max(np.abs(relative)):.6g}, "
            f"message={solution.message}"
        )
    return LinkedEquilibriumResult(
        prices=np.exp(log_prices),
        primary_supply=primary,
        process_supply=process_supply,
        total_supply=total_supply,
        final_demand=final,
        process_demand=process_demand,
        total_demand=total_demand,
        processes=process_results,
        global_supply=global_supply,
        global_demand=global_demand,
        relative_residuals=relative,
        log_price_changes=log_prices,
        region_names=regions,
        product_names=products,
        function_evaluations=int(solution.nfev),
    )


def run_ces_simulation(
    inputs: SimulationInputs,
    ces_config: Mapping[str, Any],
    *,
    scenarios: Sequence[str],
    years: Sequence[int] | range,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Run the five-nest demand sensitivity with central supply parameters."""

    selected_scenarios = list(scenarios)
    selected_years = sorted(set(int(year) for year in years))
    if not selected_scenarios or not selected_years:
        raise SensitivityError("CES simulation needs scenarios and years")
    solver = inputs.config["solver"]
    benchmark_year = int(inputs.config["benchmark_year"])
    result_frames: list[pd.DataFrame] = []
    price_frames: list[pd.DataFrame] = []
    process_frames: list[pd.DataFrame] = []
    convergence_rows: list[dict[str, Any]] = []
    for scenario in selected_scenarios:
        initial_prices = np.ones(len(inputs.system.products))
        population_2023 = _region_vector(
            inputs.drivers,
            inputs.system.regions,
            scenario,
            benchmark_year,
            "population_index_2025",
        )
        gdppc_2023 = _region_vector(
            inputs.drivers,
            inputs.system.regions,
            scenario,
            benchmark_year,
            "gdp_ppp_per_capita_index_2025",
        )
        tariff_2023 = _region_product_matrix(
            inputs.tariff,
            inputs.system.regions,
            inputs.system.products,
            scenario,
            benchmark_year,
            "tariff_wedge",
        )
        for year in selected_years:
            effective_supply = _effective_supply_elasticity(
                inputs.supply_elasticity,
                inputs.supply_lag_by_product,
                year,
                benchmark_year,
            )
            population = _region_vector(
                inputs.drivers,
                inputs.system.regions,
                scenario,
                year,
                "population_index_2025",
            ) / population_2023
            gdppc = _region_vector(
                inputs.drivers,
                inputs.system.regions,
                scenario,
                year,
                "gdp_ppp_per_capita_index_2025",
            ) / gdppc_2023
            demand_shifter = population[:, None] * np.power(
                gdppc[:, None], inputs.income_elasticity
            )
            tfp = _region_vector(
                inputs.tfp,
                inputs.system.regions,
                scenario,
                year,
                "tfp_index_2023",
            )
            climate = _region_product_matrix(
                inputs.climate,
                inputs.system.regions,
                inputs.system.products,
                scenario,
                year,
                "climate_yield_index_2023",
            )
            supply_shifter = (
                np.power(tfp[:, None], inputs.tfp_exponents[None, :]) * climate
            )
            rer = _region_vector(
                inputs.exchange,
                inputs.system.regions,
                scenario,
                year,
                "real_exchange_rate_index_2023",
            )
            tariff = _region_product_matrix(
                inputs.tariff,
                inputs.system.regions,
                inputs.system.products,
                scenario,
                year,
                "tariff_wedge",
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
            processes = _apply_process_supply_shifters(processes, supply_shifter)
            solved = solve_linked_equilibrium_ces(
                inputs.system.base_primary_supply,
                inputs.system.base_final_demand,
                effective_supply,
                inputs.demand_elasticity,
                ces_nests=ces_config["nests"],
                sigma=float(ces_config["sigma"]),
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
            initial_prices = solved.prices
            country, price, process, convergence = _result_frames(
                scenario,
                year,
                solved,
                inputs.food_share_of_final_demand,
            )
            result_frames.append(country)
            price_frames.append(price)
            process_frames.append(process)
            convergence_rows.append(convergence)
    results = pd.concat(result_frames, ignore_index=True)
    prices = pd.concat(price_frames, ignore_index=True)
    activities = pd.concat(process_frames, ignore_index=True)
    convergence = pd.DataFrame.from_records(convergence_rows)
    max_market = float(convergence["maximum_market_relative_residual"].max())
    max_accounting = float(convergence["maximum_accounting_absolute_residual_mt"].max())
    passed = (
        max_market <= float(solver["market_relative_residual"])
        and max_accounting <= float(solver["accounting_relative_residual"])
        and convergence[["converged", "accounting_passed"]].all().all()
    )
    report = {
        "status": "passed" if passed else "failed",
        "scenarios": selected_scenarios,
        "year_start": min(selected_years),
        "year_end": max(selected_years),
        "annual_solution_count": int(len(convergence)),
        "economy_count": len(inputs.system.regions),
        "commodity_count": len(inputs.system.products),
        "parameter_set": inputs.parameter_set,
        "demand_model_form": "five_frozen_2023_share_inner_cobb_douglas_nests",
        "ces_sigma": float(ces_config["sigma"]),
        "ces_nests": dict(ces_config["nests"]),
        "result_row_count": int(len(results)),
        "maximum_market_relative_residual": max_market,
        "maximum_accounting_absolute_residual_mt": max_accounting,
        "all_years_converged": bool(passed),
        "bilateral_trade": False,
        "silk_dependency": False,
        "world_price_per_commodity": True,
    }
    if not passed:
        raise RuntimeError(f"one or more CES annual solutions failed: {report}")
    return results, prices, activities, convergence, report


def _calibration_metrics(
    inputs: SimulationInputs,
    results: pd.DataFrame,
    prices: pd.DataFrame,
    activities: pd.DataFrame,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    benchmark_year = int(config["benchmark_year"])
    scenarios = list(config["scenarios"])
    base_primary = inputs.system.base_primary_supply
    base_final = inputs.system.base_final_demand
    base_process_supply = np.zeros_like(base_primary)
    base_process_demand = np.zeros_like(base_primary)
    for process in inputs.system.processes:
        base_process_supply += process.output_coefficients * process.base_activity[:, None]
        base_process_demand += process.input_coefficients * process.base_activity[:, None]
    expected_arrays = {
        "primary_supply_mt": base_primary,
        "processing_supply_mt": base_process_supply,
        "production_mt": base_primary + base_process_supply,
        "final_demand_mt": base_final,
        "processing_demand_mt": base_process_demand,
        "demand_mt": base_final + base_process_demand,
    }
    selected = results[results["year"].eq(benchmark_year)]
    maximum_quantity_error = 0.0
    for scenario in scenarios:
        scenario_rows = selected[selected["scenario"].eq(scenario)]
        for column, expected in expected_arrays.items():
            actual = scenario_rows.pivot(
                index="economy_id", columns="commodity", values=column
            ).reindex(index=inputs.system.regions, columns=inputs.system.products)
            if actual.isna().any().any():
                raise SensitivityError(f"benchmark result is incomplete for {column}")
            maximum_quantity_error = max(
                maximum_quantity_error,
                float(np.max(np.abs(actual.to_numpy(float) - expected))),
            )
    benchmark_prices = prices[prices["year"].eq(benchmark_year)][
        "world_price_index_2023"
    ].to_numpy(float)
    maximum_price_error = float(np.max(np.abs(benchmark_prices - 1.0)))

    selected_activity = activities[activities["year"].eq(benchmark_year)]
    maximum_activity_error = 0.0
    for scenario in scenarios:
        for process in inputs.system.processes:
            actual = selected_activity[
                selected_activity["scenario"].eq(scenario)
                & selected_activity["process"].eq(process.name)
            ].set_index("economy_id")["activity"].reindex(inputs.system.regions)
            if actual.isna().any():
                raise SensitivityError(
                    f"benchmark process activity is incomplete for {process.name}"
                )
            maximum_activity_error = max(
                maximum_activity_error,
                float(np.max(np.abs(actual.to_numpy(float) - process.base_activity))),
            )
    gates = config["calibration_gates"]
    passed = (
        maximum_quantity_error <= float(gates["quantity_absolute_tolerance_mt"])
        and maximum_activity_error
        <= float(gates["process_activity_absolute_tolerance"])
        and maximum_price_error <= float(gates["world_price_absolute_tolerance"])
    )
    return {
        "status": "passed" if passed else "failed",
        "maximum_2023_quantity_absolute_error_mt": maximum_quantity_error,
        "maximum_2023_process_activity_absolute_error": maximum_activity_error,
        "maximum_2023_world_price_absolute_error": maximum_price_error,
    }


def _validate_run_frames(
    results: pd.DataFrame,
    prices: pd.DataFrame,
    convergence: pd.DataFrame,
    inputs: SimulationInputs,
    config: Mapping[str, Any],
) -> None:
    expected_solutions = len(config["scenarios"]) * (
        int(config["projection_end"]) - int(config["benchmark_year"]) + 1
    )
    if len(convergence) != expected_solutions:
        raise SensitivityError(
            f"sensitivity run has {len(convergence)} rather than {expected_solutions} solutions"
        )
    expected_results = expected_solutions * len(inputs.system.regions) * len(
        inputs.system.products
    )
    if len(results) != expected_results:
        raise SensitivityError("sensitivity country-product grid is incomplete")
    for frame, columns, label in (
        (results, QUANTITY_COLUMNS, "quantity"),
        (
            prices,
            ("world_price_index_2023", "global_supply_mt", "global_demand_mt"),
            "price",
        ),
    ):
        values = frame[list(columns)].to_numpy(float)
        if not np.isfinite(values).all():
            raise SensitivityError(f"sensitivity {label} results are non-finite")
    nonnegative = [column for column in QUANTITY_COLUMNS if column != "net_import_mt"]
    if (results[nonnegative].to_numpy(float) < -1.0e-12).any():
        raise SensitivityError("sensitivity results contain negative physical quantities")
    if (prices["world_price_index_2023"] <= 0.0).any():
        raise SensitivityError("sensitivity results contain non-positive prices")
    maximum_log_price = float(
        np.max(np.abs(np.log(prices["world_price_index_2023"].to_numpy(float))))
    )
    if maximum_log_price >= float(inputs.config["solver"]["maximum_absolute_log_price"]):
        raise SensitivityError("a sensitivity solution touched its log-price bound")


def _aggregate_endpoint_groups(
    results: pd.DataFrame,
    root: Path,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    analysis_config = load_analysis_config(
        _project_path(root, config["inputs"]["analysis_config"], "analysis_config")
    )
    model_membership = pd.read_csv(
        _project_path(root, config["inputs"]["model_membership"], "model_membership")
    )
    source_membership = pd.read_csv(
        _project_path(root, config["inputs"]["source_membership"], "source_membership")
    )
    weights = pd.read_csv(
        _project_path(
            root,
            config["inputs"]["source_allocation_weights"],
            "source_allocation_weights",
        )
    )
    outputs = []
    for scenario in config["scenarios"]:
        outputs.append(
            aggregate_solved_results(
                results[results["scenario"].eq(scenario)].copy(),
                model_membership,
                source_membership,
                weights,
                analysis_config,
            )
        )
    return pd.concat(outputs, ignore_index=True)


def _primary_basket_group_summary(
    grouped: pd.DataFrame,
    config: Mapping[str, Any],
    variant: str,
    family: str,
) -> pd.DataFrame:
    basket = grouped[grouped["commodity"].isin(config["primary_basket"])]
    keys = [
        "scenario",
        "year",
        "group_system",
        "group_code",
        "group_name",
    ]
    summary = (
        basket.groupby(keys, as_index=False)
        .agg(
            primary_basket_production_mt=("primary_supply_mt", "sum"),
            primary_basket_food_demand_mt=("food_demand_mt", "sum"),
            primary_basket_net_import_mt=("net_import_mt", "sum"),
        )
        .sort_values(keys)
        .reset_index(drop=True)
    )
    summary.insert(0, "variant_family", family)
    summary.insert(0, "variant", variant)
    return summary


def _relative_percent(numerator: pd.Series, denominator: pd.Series, floor: float) -> np.ndarray:
    usable = denominator.abs().gt(float(floor))
    return np.where(usable, 100.0 * (numerator / denominator - 1.0), np.nan)


def _add_price_comparisons(
    prices: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    keep = prices[
        prices["year"].isin(config["retained_summary_years"])
        & prices["commodity"].isin(config["major_food_prices"])
    ].copy()
    keys = ["variant", "scenario", "commodity"]
    base = keep[keep["year"].eq(int(config["benchmark_year"]))][
        [*keys, "world_price_index_2023"]
    ].rename(columns={"world_price_index_2023": "benchmark_price"})
    keep = keep.merge(base, on=keys, how="left", validate="many_to_one")
    keep["price_change_from_2023_percent"] = _relative_percent(
        keep["world_price_index_2023"], keep["benchmark_price"], 1.0e-15
    )
    if "central_price" not in keep or "price_relative_to_central_percent" not in keep:
        central = keep[keep["variant"].eq("V2_CENTRAL")][
            ["scenario", "year", "commodity", "world_price_index_2023"]
        ].rename(columns={"world_price_index_2023": "central_price"})
        keep = keep.merge(
            central,
            on=["scenario", "year", "commodity"],
            how="left",
            validate="many_to_one",
        )
        keep["price_relative_to_central_percent"] = _relative_percent(
            keep["world_price_index_2023"], keep["central_price"], 1.0e-15
        )
    return keep.sort_values(["variant", "scenario", "year", "commodity"]).reset_index(
        drop=True
    )


def _add_all_price_comparisons(prices: pd.DataFrame) -> pd.DataFrame:
    central = prices[prices["variant"].eq("V2_CENTRAL")][
        ["scenario", "year", "commodity", "world_price_index_2023"]
    ].rename(columns={"world_price_index_2023": "central_price"})
    result = prices.merge(
        central,
        on=["scenario", "year", "commodity"],
        how="left",
        validate="many_to_one",
    )
    if result["central_price"].isna().any():
        raise SensitivityError("annual price comparisons lack a central reference")
    result["price_relative_to_central_percent"] = _relative_percent(
        result["world_price_index_2023"], result["central_price"], 1.0e-15
    )
    return result.sort_values(
        ["variant", "scenario", "year", "commodity"]
    ).reset_index(drop=True)


def _select_reported_groups(
    summary: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    group_config = config["reported_groups"]
    selected = pd.Series(False, index=summary.index)
    for definition in group_config["fixed"]:
        selected |= summary["group_system"].eq(definition["group_system"]) & summary[
            "group_code"
        ].eq(str(definition["group_code"]))
    selected |= summary["group_system"].isin(group_config["include_all_group_systems"])
    result = summary[selected].copy()
    id_keys = ["variant", "scenario", "group_system", "group_code"]
    measures = [
        "primary_basket_production_mt",
        "primary_basket_food_demand_mt",
        "primary_basket_net_import_mt",
    ]
    base = result[result["year"].eq(int(config["benchmark_year"]))][
        [*id_keys, *measures]
    ].rename(columns={measure: f"{measure}_2023" for measure in measures})
    result = result.merge(base, on=id_keys, how="left", validate="many_to_one")
    floor = float(config["materiality_screen"]["denominator_floor_mt"])
    for measure in measures:
        result[f"{measure}_change_from_2023_percent"] = _relative_percent(
            result[measure], result[f"{measure}_2023"], floor
        )
    central = result[result["variant"].eq("V2_CENTRAL")][
        ["scenario", "year", "group_system", "group_code", *measures]
    ].rename(columns={measure: f"{measure}_central" for measure in measures})
    result = result.merge(
        central,
        on=["scenario", "year", "group_system", "group_code"],
        how="left",
        validate="many_to_one",
    )
    for measure in measures:
        result[f"{measure}_relative_to_central_percent"] = _relative_percent(
            result[measure], result[f"{measure}_central"], floor
        )
    return result.sort_values(
        ["variant", "scenario", "group_system", "group_code", "year"]
    ).reset_index(drop=True)


def _materiality_groups(
    groups: pd.DataFrame,
    definitions: Sequence[Mapping[str, Any]],
) -> pd.DataFrame:
    selected = pd.Series(False, index=groups.index)
    for definition in definitions:
        mask = groups["group_system"].eq(definition["group_system"])
        code = str(definition["group_code"])
        if code != "*":
            mask &= groups["group_code"].eq(code)
        selected |= mask
    return groups[selected].copy()


def build_materiality_screen(
    prices: pd.DataFrame,
    group_summary: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    """Apply the section-8.5 numerical thresholds as a diagnostic screen."""

    screen = config["materiality_screen"]
    year = int(screen["comparison_year"])
    price_rows = prices[
        prices["year"].eq(year)
        & prices["commodity"].isin(config["major_food_prices"])
    ].copy()
    if "central_price" not in price_rows:
        central_price = price_rows[price_rows["variant"].eq("V2_CENTRAL")][
            ["scenario", "commodity", "world_price_index_2023"]
        ].rename(columns={"world_price_index_2023": "central_price"})
        price_rows = price_rows.merge(
            central_price,
            on=["scenario", "commodity"],
            how="left",
            validate="many_to_one",
        )
    price_rows["absolute_relative_percent"] = np.abs(
        _relative_percent(
            price_rows["world_price_index_2023"], price_rows["central_price"], 1.0e-15
        )
    )

    production = _materiality_groups(
        group_summary[group_summary["year"].eq(year)], screen["production_groups"]
    )
    central_production = production[production["variant"].eq("V2_CENTRAL")][
        [
            "scenario",
            "group_system",
            "group_code",
            "primary_basket_production_mt",
        ]
    ].rename(columns={"primary_basket_production_mt": "central_production_mt"})
    production = production.merge(
        central_production,
        on=["scenario", "group_system", "group_code"],
        how="left",
        validate="many_to_one",
    )
    production["absolute_relative_percent"] = np.abs(
        _relative_percent(
            production["primary_basket_production_mt"],
            production["central_production_mt"],
            float(screen["denominator_floor_mt"]),
        )
    )

    variants = (
        list(config["parameter_response_variants"])
        + list(EXPECTED_TFP_VARIANTS)
        + [str(config["demand_substitution_ces"]["variant"])]
    )
    families = {
        name: config["parameter_response_variants"][name]["family"]
        for name in config["parameter_response_variants"]
    }
    families.update(
        {name: config["tfp_variants"][name]["family"] for name in EXPECTED_TFP_VARIANTS}
    )
    families[str(config["demand_substitution_ces"]["variant"])] = str(
        config["demand_substitution_ces"]["family"]
    )
    rows: list[dict[str, Any]] = []
    for variant in variants:
        variant_prices = price_rows[price_rows["variant"].eq(variant)]
        variant_production = production[production["variant"].eq(variant)]
        if variant_prices.empty or variant_production.empty:
            raise SensitivityError(f"materiality screen lacks {variant}")
        price_index = variant_prices["absolute_relative_percent"].idxmax()
        production_index = variant_production["absolute_relative_percent"].idxmax()
        price_peak = variant_prices.loc[price_index]
        production_peak = variant_production.loc[production_index]
        max_price = float(price_peak["absolute_relative_percent"])
        max_production = float(production_peak["absolute_relative_percent"])
        price_exceeded = max_price > float(
            screen["major_food_world_price_relative_change_percent"]
        )
        production_exceeded = max_production > float(
            screen["primary_production_relative_change_percent"]
        )
        rows.append(
            {
                "variant": variant,
                "variant_family": families[variant],
                "comparison_year": year,
                "maximum_major_food_world_price_deviation_percent": max_price,
                "price_trigger_scenario": price_peak["scenario"],
                "price_trigger_commodity": price_peak["commodity"],
                "price_threshold_percent": float(
                    screen["major_food_world_price_relative_change_percent"]
                ),
                "price_threshold_exceeded": bool(price_exceeded),
                "maximum_primary_production_deviation_percent": max_production,
                "production_trigger_scenario": production_peak["scenario"],
                "production_trigger_group_system": production_peak["group_system"],
                "production_trigger_group_code": production_peak["group_code"],
                "production_threshold_percent": float(
                    screen["primary_production_relative_change_percent"]
                ),
                "production_threshold_exceeded": bool(production_exceeded),
                "either_threshold_exceeded": bool(price_exceeded or production_exceeded),
                "interpretation": screen["label"],
            }
        )
    return pd.DataFrame(rows)


def _tfp_2035_identity(
    central_results: pd.DataFrame,
    variant_results: pd.DataFrame,
    central_prices: pd.DataFrame,
    variant_prices: pd.DataFrame,
) -> dict[str, float | str]:
    keys = ["scenario", "year", "economy_id", "commodity"]
    selected_central = central_results[central_results["year"].eq(2035)]
    selected_variant = variant_results[variant_results["year"].eq(2035)]
    merged = selected_variant.merge(
        selected_central,
        on=keys,
        how="inner",
        suffixes=("_variant", "_central"),
        validate="one_to_one",
    )
    if len(merged) != len(selected_central):
        raise SensitivityError("TFP 2035 identity grid is incomplete")
    quantity_error = max(
        float(
            np.max(
                np.abs(
                    merged[f"{column}_variant"].to_numpy(float)
                    - merged[f"{column}_central"].to_numpy(float)
                )
            )
        )
        for column in QUANTITY_COLUMNS
    )
    price_keys = ["scenario", "year", "commodity"]
    price_merge = variant_prices[variant_prices["year"].eq(2035)].merge(
        central_prices[central_prices["year"].eq(2035)],
        on=price_keys,
        how="inner",
        suffixes=("_variant", "_central"),
        validate="one_to_one",
    )
    price_error = float(
        np.max(
            np.abs(
                price_merge["world_price_index_2023_variant"].to_numpy(float)
                - price_merge["world_price_index_2023_central"].to_numpy(float)
            )
        )
    )
    return {
        "status": "passed" if quantity_error <= 1.0e-8 and price_error <= 1.0e-12 else "failed",
        "maximum_2035_quantity_absolute_difference_mt": quantity_error,
        "maximum_2035_world_price_absolute_difference": price_error,
    }


def _assert_final_output_contract(
    convergence: pd.DataFrame,
    annual_prices: pd.DataFrame,
    major_prices: pd.DataFrame,
    groups: pd.DataFrame,
    materiality: pd.DataFrame,
    config: Mapping[str, Any],
) -> None:
    """Validate every compact merge and grid before the first output write."""

    variant_count = 6
    scenario_count = len(config["scenarios"])
    annual_count = int(config["projection_end"]) - int(config["benchmark_year"]) + 1
    commodity_count = 31
    expected_convergence = variant_count * scenario_count * annual_count
    expected_prices = expected_convergence * commodity_count
    expected_major = (
        variant_count
        * scenario_count
        * len(config["retained_summary_years"])
        * len(config["major_food_prices"])
    )
    checks = (
        (
            convergence,
            ["variant", "scenario", "year"],
            expected_convergence,
            "annual convergence",
        ),
        (
            annual_prices,
            ["variant", "scenario", "year", "commodity"],
            expected_prices,
            "annual prices",
        ),
        (
            major_prices,
            ["variant", "scenario", "year", "commodity"],
            expected_major,
            "major-food prices",
        ),
    )
    for frame, keys, expected, label in checks:
        if len(frame) != expected or frame.duplicated(keys).any():
            raise SensitivityError(
                f"{label} output grid mismatch: rows={len(frame)}, expected={expected}"
            )
    required_price_columns = {
        "world_price_index_2023",
        "central_price",
        "price_relative_to_central_percent",
    }
    if not required_price_columns <= set(annual_prices):
        raise SensitivityError(
            f"annual price merge lacks {sorted(required_price_columns-set(annual_prices))}"
        )
    if annual_prices[list(required_price_columns)].isna().any().any():
        raise SensitivityError("annual price comparisons contain missing values")
    group_keys = [
        "variant",
        "scenario",
        "year",
        "group_system",
        "group_code",
    ]
    if groups.empty or groups.duplicated(group_keys).any():
        raise SensitivityError("reported primary-basket group grid is empty or duplicated")
    counts = groups.groupby(["variant", "scenario", "year"]).size()
    if counts.nunique() != 1 or len(counts) != variant_count * scenario_count * len(
        config["retained_summary_years"]
    ):
        raise SensitivityError("reported group coverage differs across variants/slices")
    required_group_columns = {
        "primary_basket_production_mt_relative_to_central_percent",
        "primary_basket_food_demand_mt_relative_to_central_percent",
        "primary_basket_net_import_mt_relative_to_central_percent",
    }
    if not required_group_columns <= set(groups):
        raise SensitivityError(
            f"group merge lacks {sorted(required_group_columns-set(groups))}"
        )
    if len(materiality) != variant_count or materiality["variant"].duplicated().any():
        raise SensitivityError("materiality screen must contain one row per variant")
    required_materiality = {
        "maximum_major_food_world_price_deviation_percent",
        "maximum_primary_production_deviation_percent",
        "either_threshold_exceeded",
    }
    if not required_materiality <= set(materiality):
        raise SensitivityError("materiality merge is incomplete")


def run_sensitivity(
    project_root: str | Path = PROJECT_ROOT,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """Solve the V2 response envelope, TFP cases and five-nest demand case."""

    root = Path(project_root).resolve()
    sensitivity_path = Path(config_path).resolve() if config_path else root / "config/sensitivity.yaml"
    config = load_sensitivity_config(sensitivity_path)
    inputs = load_simulation_inputs(root)
    if tuple(inputs.config["scenarios"]) != EXPECTED_SCENARIOS:
        raise SensitivityError("central simulation SSP contract differs from sensitivity")
    parameters = load_variant_parameters(root, config, inputs)
    years = range(int(config["benchmark_year"]), int(config["projection_end"]) + 1)
    retained_years = set(config["retained_summary_years"])

    variants: list[tuple[str, str, SimulationInputs, str]] = []
    for name in EXPECTED_RESPONSE_VARIANTS:
        variant_inputs, parameter_hash = build_response_variant_inputs(
            inputs, parameters, config, name
        )
        family = str(config["parameter_response_variants"][name]["family"])
        variants.append((name, family, variant_inputs, parameter_hash))
    tfp_bounds = tuple(float(value) for value in config["tfp_variants"]["annual_log_growth_bounds"])
    for name in EXPECTED_TFP_VARIANTS:
        definition = config["tfp_variants"][name]
        transformed_tfp = scale_post_2035_tfp(
            inputs.tfp,
            float(definition["post_2035_positive_log_growth_multiplier"]),
            unchanged_through_year=int(config["tfp_variants"]["unchanged_through_year"]),
            annual_log_growth_bounds=tfp_bounds,
        )
        tfp_hash = hashlib.sha256(
            transformed_tfp.sort_values(["scenario", "economy_id", "year"])
            .to_csv(index=False, float_format="%.17g", lineterminator="\n")
            .encode("utf-8")
        ).hexdigest()
        variants.append(
            (
                name,
                str(definition["family"]),
                replace(inputs, parameter_set=name, tfp=transformed_tfp),
                tfp_hash,
            )
        )
    ces = config["demand_substitution_ces"]
    ces_hash_payload = json.dumps(
        ces, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("utf-8")
    variants.append(
        (
            str(ces["variant"]),
            str(ces["family"]),
            replace(inputs, parameter_set=str(ces["variant"])),
            hashlib.sha256(ces_hash_payload).hexdigest(),
        )
    )

    convergence_frames: list[pd.DataFrame] = []
    price_frames: list[pd.DataFrame] = []
    group_frames: list[pd.DataFrame] = []
    variant_reports: dict[str, Any] = {}
    central_2035_results: pd.DataFrame | None = None
    central_prices: pd.DataFrame | None = None
    tfp_identity: dict[str, Any] = {}
    for name, family, variant_inputs, variant_hash in variants:
        if name == str(ces["variant"]):
            results, prices, activities, convergence, run_report = run_ces_simulation(
                variant_inputs,
                ces,
                scenarios=config["scenarios"],
                years=years,
            )
        else:
            results, prices, activities, convergence, run_report = run_simulation(
                variant_inputs,
                scenarios=config["scenarios"],
                years=years,
            )
        _validate_run_frames(results, prices, convergence, variant_inputs, config)
        calibration = _calibration_metrics(
            variant_inputs, results, prices, activities, config
        )
        if calibration["status"] != "passed":
            raise SensitivityError(f"{name} failed exact 2023 calibration: {calibration}")
        convergence.insert(0, "variant_family", family)
        convergence.insert(0, "variant", name)
        prices.insert(0, "variant_family", family)
        prices.insert(0, "variant", name)
        convergence_frames.append(convergence)
        price_frames.append(prices)

        endpoint_results = results[results["year"].isin(retained_years)].copy()
        grouped = _aggregate_endpoint_groups(endpoint_results, root, config)
        group_frames.append(
            _primary_basket_group_summary(grouped, config, name, family)
        )
        if name == "V2_CENTRAL":
            central_2035_results = results[results["year"].eq(2035)].copy()
            central_prices = prices.copy()
        elif name in EXPECTED_TFP_VARIANTS:
            if central_2035_results is None or central_prices is None:
                raise AssertionError("central response must run before TFP variants")
            tfp_identity[name] = _tfp_2035_identity(
                central_2035_results,
                results[results["year"].eq(2035)].copy(),
                central_prices,
                prices,
            )
            if tfp_identity[name]["status"] != "passed":
                raise SensitivityError(f"{name} changed the path through 2035")
        variant_reports[name] = {
            "family": family,
            "variant_input_sha256": variant_hash,
            "run": run_report,
            "calibration": calibration,
        }

    all_convergence = pd.concat(convergence_frames, ignore_index=True)
    all_prices = _add_all_price_comparisons(
        pd.concat(price_frames, ignore_index=True)
    )
    all_groups = pd.concat(group_frames, ignore_index=True)
    major_prices = _add_price_comparisons(all_prices, config)
    reported_groups = _select_reported_groups(all_groups, config)
    materiality = build_materiality_screen(all_prices, all_groups, config)
    _assert_final_output_contract(
        all_convergence,
        all_prices,
        major_prices,
        reported_groups,
        materiality,
        config,
    )

    outputs = {
        key: _output_path(root, value, f"outputs.{key}")
        for key, value in config["outputs"].items()
    }
    outputs["directory"].mkdir(parents=True, exist_ok=True)
    frame_outputs = {
        "annual_convergence": all_convergence,
        "annual_world_prices": all_prices,
        "major_food_prices": major_prices,
        "primary_basket_groups": reported_groups,
        "materiality_screen": materiality,
    }
    for key, frame in frame_outputs.items():
        frame.to_csv(outputs[key], index=False)
    output_hashes = {key: _file_sha256(outputs[key]) for key in frame_outputs}

    gates = config["calibration_gates"]
    max_market = float(all_convergence["maximum_market_relative_residual"].max())
    max_accounting = float(
        all_convergence["maximum_accounting_absolute_residual_mt"].max()
    )
    all_converged = bool(all_convergence[["converged", "accounting_passed"]].all().all())
    passed = (
        all_converged
        and max_market <= float(gates["market_relative_residual"])
        and max_accounting <= float(gates["accounting_absolute_residual_mt"])
        and all(
            report["calibration"]["status"] == "passed"
            for report in variant_reports.values()
        )
        and all(value["status"] == "passed" for value in tfp_identity.values())
    )
    report: dict[str, Any] = {
        "status": "passed" if passed else "failed",
        "scope_status": (
            "response_envelope_tfp_and_demand_ces_complete_shared_resource_pending"
        ),
        "frozen_section_8_complete": False,
        "version": config["version"],
        "scenarios": list(config["scenarios"]),
        "year_start": int(config["benchmark_year"]),
        "year_end": int(config["projection_end"]),
        "unique_variant_count": len(variants),
        "variant_names": [name for name, _, _, _ in variants],
        "response_envelope_full_five_ssp_annual": True,
        "tfp_sensitivity_full_five_ssp_annual": True,
        "demand_ces_full_five_ssp_annual": True,
        "total_annual_solution_count": int(len(all_convergence)),
        "expected_total_annual_solution_count": 840,
        "maximum_market_relative_residual": max_market,
        "maximum_accounting_absolute_residual_mt": max_accounting,
        "all_annual_solutions_converged": all_converged,
        "variant_reports": variant_reports,
        "tfp_2035_identity": tfp_identity,
        "materiality_screen_label": config["materiality_screen"]["label"],
        "materiality_threshold_exceeded_variants": materiality.loc[
            materiality["either_threshold_exceeded"], "variant"
        ].tolist(),
        "not_implemented_structural_sensitivities": config[
            "not_implemented_structural_sensitivities"
        ],
        "nutrition_and_ghg_sensitivity_postsolutions_in_this_runner": False,
        "formal_central_outputs_overwritten": False,
        "bilateral_trade": False,
        "silk_dependency": False,
        "external_comparison_data_used_as_model_input": False,
        "primary_basket": list(config["primary_basket"]),
        "primary_basket_aggregation": "nonoverlapping_biological_primary_supply_mt",
        "outputs": {
            key: str(path) for key, path in outputs.items() if key != "directory"
        },
        "output_sha256": output_hashes,
    }
    if len(all_convergence) != 840:
        raise SensitivityError("six variants x five SSPs x 28 years must equal 840 solves")
    outputs["report"].write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    if not passed:
        raise RuntimeError(f"V2 sensitivity gates failed: {report}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            run_sensitivity(args.project_root, args.config),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
