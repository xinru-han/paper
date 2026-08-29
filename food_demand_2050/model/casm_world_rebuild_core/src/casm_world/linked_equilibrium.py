"""Coupled non-spatial world equilibrium with explicit processing activities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares


FloatArray = NDArray[np.float64]


class LinkedEquilibriumInputError(ValueError):
    """Raised when a coupled market system is malformed."""


class LinkedEquilibriumConvergenceError(RuntimeError):
    """Raised when the coupled world-price system does not clear."""


def _array(name: str, values: ArrayLike, shape: tuple[int, ...]) -> FloatArray:
    try:
        array = np.asarray(values, dtype=float)
        result = np.array(np.broadcast_to(array, shape), dtype=float, copy=True)
    except (TypeError, ValueError) as exc:
        raise LinkedEquilibriumInputError(
            f"{name} cannot be broadcast to {shape}"
        ) from exc
    if not np.isfinite(result).all():
        raise LinkedEquilibriumInputError(f"{name} contains missing or non-finite values")
    return result


@dataclass(frozen=True)
class ProcessSpec:
    """One region-specific constant-yield processing technology.

    Coefficients have shape region-by-product. Activity is measured in the
    configured input/activity unit. An activity may have no modelled input
    (for example seed-cotton ginning, whose agricultural input is a satellite).
    """

    name: str
    base_activity: FloatArray
    input_coefficients: FloatArray
    output_coefficients: FloatArray
    elasticity: FloatArray
    activity_shifter: FloatArray | float = 1.0


@dataclass(frozen=True)
class ProcessResult:
    name: str
    activity: FloatArray
    inputs: FloatArray
    outputs: FloatArray


@dataclass(frozen=True)
class LinkedEquilibriumResult:
    prices: FloatArray
    primary_supply: FloatArray
    process_supply: FloatArray
    total_supply: FloatArray
    final_demand: FloatArray
    process_demand: FloatArray
    total_demand: FloatArray
    processes: tuple[ProcessResult, ...]
    global_supply: FloatArray
    global_demand: FloatArray
    relative_residuals: FloatArray
    log_price_changes: FloatArray
    region_names: tuple[str, ...]
    product_names: tuple[str, ...]
    function_evaluations: int

    @property
    def max_abs_residual(self) -> float:
        return float(np.max(np.abs(self.relative_residuals)))


@dataclass(frozen=True)
class _PreparedProcess:
    name: str
    base_activity: FloatArray
    inputs: FloatArray
    outputs: FloatArray
    elasticity: FloatArray
    shifter: FloatArray
    input_weights: FloatArray
    output_weights: FloatArray


def _names(values: Sequence[str] | None, size: int, prefix: str) -> tuple[str, ...]:
    if values is None:
        return tuple(f"{prefix}_{index}" for index in range(size))
    result = tuple(str(value) for value in values)
    if len(result) != size or len(set(result)) != size or any(not value for value in result):
        raise LinkedEquilibriumInputError(
            f"{prefix} names must contain {size} unique non-empty labels"
        )
    return result


def _prepare_process(
    process: ProcessSpec,
    shape: tuple[int, int],
) -> _PreparedProcess:
    regions, _ = shape
    base = _array(f"{process.name}.base_activity", process.base_activity, (regions,))
    inputs = _array(f"{process.name}.input_coefficients", process.input_coefficients, shape)
    outputs = _array(f"{process.name}.output_coefficients", process.output_coefficients, shape)
    elasticity = _array(f"{process.name}.elasticity", process.elasticity, (regions,))
    shifter = _array(f"{process.name}.activity_shifter", process.activity_shifter, (regions,))
    if (base < 0).any() or (inputs < 0).any() or (outputs < 0).any():
        raise LinkedEquilibriumInputError(f"{process.name} has negative activity/coefficients")
    if (elasticity < 0).any() or (shifter < 0).any():
        raise LinkedEquilibriumInputError(f"{process.name} elasticity/shifter cannot be negative")
    active = base > 0
    no_modelled_output = active & (outputs.sum(axis=1) <= 0)
    if np.any(no_modelled_output & (elasticity > 0)):
        raise LinkedEquilibriumInputError(
            f"{process.name} active rows without a modelled output must have zero elasticity"
        )
    output_total = outputs.sum(axis=1, keepdims=True)
    input_total = inputs.sum(axis=1, keepdims=True)
    output_weights = np.divide(
        outputs, output_total, out=np.zeros_like(outputs), where=output_total > 0
    )
    input_weights = np.divide(
        inputs, input_total, out=np.zeros_like(inputs), where=input_total > 0
    )
    return _PreparedProcess(
        process.name, base, inputs, outputs, elasticity, shifter,
        input_weights, output_weights,
    )


def _evaluate(
    log_prices: FloatArray,
    *,
    base_primary_supply: FloatArray,
    base_final_demand: FloatArray,
    supply_elasticity: FloatArray,
    demand_elasticity: FloatArray,
    supply_shifter: FloatArray,
    demand_shifter: FloatArray,
    producer_price_wedge: FloatArray,
    consumer_price_wedge: FloatArray,
    processes: tuple[_PreparedProcess, ...],
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray, tuple[ProcessResult, ...]]:
    world_prices = np.exp(log_prices)[None, :]
    producer_prices = world_prices * producer_price_wedge
    consumer_prices = world_prices * consumer_price_wedge
    with np.errstate(over="raise", invalid="raise"):
        primary = (
            base_primary_supply
            * supply_shifter
            * np.power(producer_prices, supply_elasticity)
        )
        final = (
            base_final_demand
            * demand_shifter
            * np.power(consumer_prices, demand_elasticity)
        )
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


def solve_linked_equilibrium(
    base_primary_supply: ArrayLike,
    base_final_demand: ArrayLike,
    supply_elasticity: ArrayLike,
    demand_elasticity: ArrayLike,
    *,
    processes: Sequence[ProcessSpec] = (),
    supply_shifter: ArrayLike = 1.0,
    demand_shifter: ArrayLike = 1.0,
    producer_price_wedge: ArrayLike = 1.0,
    consumer_price_wedge: ArrayLike = 1.0,
    initial_prices: ArrayLike = 1.0,
    region_names: Sequence[str] | None = None,
    product_names: Sequence[str] | None = None,
    clearance_tolerance: float = 1.0e-9,
    max_abs_log_price: float = 7.0,
    maximum_evaluations: int = 2_000,
) -> LinkedEquilibriumResult:
    """Solve all product prices jointly under processing input/output links."""

    primary_base = np.asarray(base_primary_supply, dtype=float)
    final_base = np.asarray(base_final_demand, dtype=float)
    if primary_base.ndim != 2 or 0 in primary_base.shape or final_base.shape != primary_base.shape:
        raise LinkedEquilibriumInputError(
            "base_primary_supply and base_final_demand must be equal non-empty matrices"
        )
    if not np.isfinite(primary_base).all() or not np.isfinite(final_base).all():
        raise LinkedEquilibriumInputError("Base quantities contain missing/non-finite values")
    if (primary_base < 0).any() or (final_base < 0).any():
        raise LinkedEquilibriumInputError("Base quantities cannot be negative")
    shape = primary_base.shape
    regions_n, products_n = shape
    supply_eps = _array("supply_elasticity", supply_elasticity, shape)
    demand_eps = _array("demand_elasticity", demand_elasticity, shape)
    supply_shift = _array("supply_shifter", supply_shifter, shape)
    demand_shift = _array("demand_shifter", demand_shifter, shape)
    producer_wedge = _array("producer_price_wedge", producer_price_wedge, shape)
    consumer_wedge = _array("consumer_price_wedge", consumer_price_wedge, shape)
    initial = _array("initial_prices", initial_prices, (products_n,))
    if (supply_eps < 0).any() or (demand_eps > 0).any():
        raise LinkedEquilibriumInputError(
            "Supply elasticities must be non-negative and demand elasticities non-positive"
        )
    if (
        (supply_shift < 0).any()
        or (demand_shift < 0).any()
        or (producer_wedge <= 0).any()
        or (consumer_wedge <= 0).any()
        or (initial <= 0).any()
    ):
        raise LinkedEquilibriumInputError("Shifters must be non-negative and prices/wedges positive")
    prepared = tuple(_prepare_process(process, shape) for process in processes)
    regions = _names(region_names, regions_n, "region")
    products = _names(product_names, products_n, "product")

    def residual(log_prices: FloatArray) -> FloatArray:
        try:
            primary, process_supply, final, process_demand, _ = _evaluate(
                log_prices,
                base_primary_supply=primary_base,
                base_final_demand=final_base,
                supply_elasticity=supply_eps,
                demand_elasticity=demand_eps,
                supply_shifter=supply_shift,
                demand_shifter=demand_shift,
                producer_price_wedge=producer_wedge,
                consumer_price_wedge=consumer_wedge,
                processes=prepared,
            )
        except FloatingPointError:
            return np.full(products_n, 1.0e6)
        supply = (primary + process_supply).sum(axis=0)
        demand = (final + process_demand).sum(axis=0)
        if (supply <= 0).any() or (demand <= 0).any():
            raise LinkedEquilibriumInputError(
                "Every product needs positive global supply and demand at all trial prices"
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
    primary, process_supply, final, process_demand, process_results = _evaluate(
        log_prices,
        base_primary_supply=primary_base,
        base_final_demand=final_base,
        supply_elasticity=supply_eps,
        demand_elasticity=demand_eps,
        supply_shifter=supply_shift,
        demand_shifter=demand_shift,
        producer_price_wedge=producer_wedge,
        consumer_price_wedge=consumer_wedge,
        processes=prepared,
    )
    total_supply = primary + process_supply
    total_demand = final + process_demand
    global_supply = total_supply.sum(axis=0)
    global_demand = total_demand.sum(axis=0)
    relative = (global_supply - global_demand) / np.maximum(global_supply, global_demand)
    if not solution.success or np.max(np.abs(relative)) > clearance_tolerance:
        raise LinkedEquilibriumConvergenceError(
            "Coupled market did not converge: "
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
