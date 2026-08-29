"""Generic multi-region, multi-product partial-equilibrium solver.

The core deliberately has no dependency on CASM's data-loading code.  Each
product has one world price that applies to every region.  Regional supply and
demand are constant-own-price-elasticity curves anchored at base quantities
and base world prices::

    supply[r, p] = base_supply[r, p] * supply_shift[r, p]
                   * (price[p] / base_price[p]) ** supply_elasticity[r, p]

    demand[r, p] = base_demand[r, p] * demand_shift[r, p]
                   * (price[p] / base_price[p]) ** demand_elasticity[r, p]

Demand elasticities use their signed convention and therefore must be
non-positive.  Supply elasticities must be non-negative.  Structural zeros are
represented explicitly by a zero base quantity and remain zero in every
scenario.  Missing or non-finite values are rejected rather than silently
being interpreted as structural zeros.

Products are cleared independently in log relative prices with Brent's method.
Using log prices guarantees positive prices, while solving the difference of
log aggregate supply and log aggregate demand avoids overflow during root
bracketing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import brentq
from scipy.special import logsumexp


FloatArray = NDArray[np.float64]


class EquilibriumInputError(ValueError):
    """Raised when market inputs are missing, malformed, or inconsistent."""


class MarketStructureError(EquilibriumInputError):
    """Raised when structural zeros leave a product without a valid market."""


class EquilibriumConvergenceError(RuntimeError):
    """Raised when a positive market-clearing price cannot be found."""


@dataclass(frozen=True)
class EquilibriumResult:
    """Solution returned by :func:`solve_equilibrium`.

    Attributes
    ----------
    prices
        One market-clearing world price per product.
    supply, demand
        Regional quantities with shape ``(n_regions, n_products)``.
    global_supply, global_demand
        Quantities summed over regions for each product.
    excess_supply
        Absolute market residual, ``global_supply - global_demand``.
    residuals
        Scale-free residuals.  Each absolute residual is divided by the larger
        of global supply and global demand for that product.
    log_price_changes
        Natural log of the ratio between equilibrium and base world prices.
    function_evaluations
        Number of scalar market-function evaluations for each product.
    """

    prices: FloatArray
    supply: FloatArray
    demand: FloatArray
    global_supply: FloatArray
    global_demand: FloatArray
    excess_supply: FloatArray
    residuals: FloatArray
    log_price_changes: FloatArray
    function_evaluations: NDArray[np.int64]
    region_names: tuple[str, ...]
    product_names: tuple[str, ...]

    @property
    def max_abs_residual(self) -> float:
        """Largest absolute scale-free market-clearing residual."""

        return float(np.max(np.abs(self.residuals)))

    @property
    def market_clearing_residuals(self) -> FloatArray:
        """Alias for the scale-free per-product residuals."""

        return self.residuals

    @property
    def absolute_residuals(self) -> FloatArray:
        """Alias for absolute excess supply by product."""

        return self.excess_supply


def _numeric_array(name: str, values: ArrayLike) -> FloatArray:
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise EquilibriumInputError(f"{name} must contain numeric values") from exc

    if not np.all(np.isfinite(array)):
        locations = np.argwhere(~np.isfinite(array))
        preview = locations[:5].tolist()
        raise EquilibriumInputError(
            f"{name} contains missing or non-finite values at indices {preview}"
        )
    return array


def _quantity_array(name: str, values: ArrayLike) -> FloatArray:
    array = _numeric_array(name, values)
    if array.ndim != 2 or 0 in array.shape:
        raise EquilibriumInputError(
            f"{name} must be a non-empty two-dimensional region-by-product array"
        )
    if np.any(array < 0.0):
        locations = np.argwhere(array < 0.0)
        raise EquilibriumInputError(
            f"{name} contains negative quantities at indices {locations[:5].tolist()}"
        )
    return array


def _broadcast_array(
    name: str,
    values: ArrayLike,
    shape: tuple[int, ...],
) -> FloatArray:
    array = _numeric_array(name, values)
    try:
        return np.array(np.broadcast_to(array, shape), dtype=np.float64, copy=True)
    except ValueError as exc:
        raise EquilibriumInputError(
            f"{name} with shape {array.shape} cannot be broadcast to {shape}"
        ) from exc


def _validate_names(
    values: Sequence[str] | None,
    size: int,
    prefix: str,
) -> tuple[str, ...]:
    if values is None:
        return tuple(f"{prefix}_{index}" for index in range(size))
    names = tuple(str(value) for value in values)
    if len(names) != size:
        raise EquilibriumInputError(
            f"{prefix}_names must contain {size} labels, received {len(names)}"
        )
    if any(not name for name in names):
        raise EquilibriumInputError(f"{prefix}_names cannot contain empty labels")
    if len(set(names)) != size:
        raise EquilibriumInputError(f"{prefix}_names must be unique")
    return names


def _market_log_balance(
    log_relative_price: float,
    supply_anchors: FloatArray,
    demand_anchors: FloatArray,
    supply_elasticities: FloatArray,
    demand_elasticities: FloatArray,
) -> float:
    log_supply = logsumexp(
        np.log(supply_anchors) + supply_elasticities * log_relative_price
    )
    log_demand = logsumexp(
        np.log(demand_anchors) + demand_elasticities * log_relative_price
    )
    return float(log_supply - log_demand)


def _bracket_root(
    function,
    value_at_zero: float,
    max_abs_log_price: float,
) -> tuple[float, float, int]:
    """Find a sign-changing interval around the base log price."""

    evaluations = 1
    bound = 1.0

    if value_at_zero < 0.0:
        lower = 0.0
        while True:
            upper = min(bound, max_abs_log_price)
            value = function(upper)
            evaluations += 1
            if value >= 0.0:
                return lower, upper, evaluations
            if upper >= max_abs_log_price:
                break
            bound *= 2.0
    else:
        upper = 0.0
        while True:
            lower = -min(bound, max_abs_log_price)
            value = function(lower)
            evaluations += 1
            if value <= 0.0:
                return lower, upper, evaluations
            if -lower >= max_abs_log_price:
                break
            bound *= 2.0

    raise EquilibriumConvergenceError(
        "could not bracket a market-clearing positive price; check elasticities "
        "and scenario shifters"
    )


def _evaluate_quantities(
    anchors: FloatArray,
    elasticities: FloatArray,
    log_price_changes: FloatArray,
) -> FloatArray:
    quantities = np.zeros_like(anchors)
    active = anchors > 0.0
    _, product_index = np.nonzero(active)
    log_values = (
        np.log(anchors[active])
        + elasticities[active] * log_price_changes[product_index]
    )
    with np.errstate(over="ignore", under="ignore"):
        quantities[active] = np.exp(log_values)
    if not np.all(np.isfinite(quantities)):
        raise EquilibriumConvergenceError(
            "equilibrium quantities exceed floating-point range"
        )
    return quantities


def solve_equilibrium(
    base_supply: ArrayLike,
    base_demand: ArrayLike,
    supply_elasticity: ArrayLike,
    demand_elasticity: ArrayLike,
    *,
    supply_shifter: ArrayLike = 1.0,
    demand_shifter: ArrayLike = 1.0,
    base_prices: ArrayLike = 1.0,
    region_names: Sequence[str] | None = None,
    product_names: Sequence[str] | None = None,
    price_tolerance: float = 1.0e-12,
    clearance_tolerance: float = 1.0e-10,
    max_iterations: int = 200,
    max_abs_log_price: float = 100.0,
) -> EquilibriumResult:
    """Solve a multi-region partial equilibrium with one price per product.

    Parameters are scalar-broadcastable to the region-by-product quantity
    arrays, except ``base_prices``, which is scalar-broadcastable to the product
    dimension.  Exogenous shifters are multiplicative: a value of 1 leaves a
    curve unchanged and a value above 1 shifts it outward.

    A zero base quantity is a structural zero and is never activated by a
    shifter.  Each product must retain at least one positive supply anchor, one
    positive demand anchor, and some effective price response after applying
    the shifters.
    """

    supply_base = _quantity_array("base_supply", base_supply)
    demand_base = _quantity_array("base_demand", base_demand)
    if demand_base.shape != supply_base.shape:
        raise EquilibriumInputError(
            "base_supply and base_demand must have the same shape; "
            f"received {supply_base.shape} and {demand_base.shape}"
        )

    shape = supply_base.shape
    n_regions, n_products = shape
    supply_eps = _broadcast_array("supply_elasticity", supply_elasticity, shape)
    demand_eps = _broadcast_array("demand_elasticity", demand_elasticity, shape)
    supply_shift = _broadcast_array("supply_shifter", supply_shifter, shape)
    demand_shift = _broadcast_array("demand_shifter", demand_shifter, shape)
    prices_base = _broadcast_array("base_prices", base_prices, (n_products,))

    if np.any(supply_eps < 0.0):
        locations = np.argwhere(supply_eps < 0.0)
        raise EquilibriumInputError(
            "supply_elasticity must be non-negative; negative values occur at "
            f"{locations[:5].tolist()}"
        )
    if np.any(demand_eps > 0.0):
        locations = np.argwhere(demand_eps > 0.0)
        raise EquilibriumInputError(
            "demand_elasticity must use the signed, non-positive convention; "
            f"positive values occur at {locations[:5].tolist()}"
        )
    if np.any(supply_shift < 0.0) or np.any(demand_shift < 0.0):
        raise EquilibriumInputError(
            "supply_shifter and demand_shifter cannot be negative"
        )
    if np.any(prices_base <= 0.0):
        raise EquilibriumInputError("base_prices must be strictly positive")
    if not np.isfinite(price_tolerance) or price_tolerance <= 0.0:
        raise EquilibriumInputError("price_tolerance must be finite and positive")
    if not np.isfinite(clearance_tolerance) or clearance_tolerance <= 0.0:
        raise EquilibriumInputError("clearance_tolerance must be finite and positive")
    if not isinstance(max_iterations, (int, np.integer)) or max_iterations <= 0:
        raise EquilibriumInputError("max_iterations must be a positive integer")
    if not np.isfinite(max_abs_log_price) or max_abs_log_price <= 0.0:
        raise EquilibriumInputError("max_abs_log_price must be finite and positive")

    regions = _validate_names(region_names, n_regions, "region")
    products = _validate_names(product_names, n_products, "product")

    supply_anchors = supply_base * supply_shift
    demand_anchors = demand_base * demand_shift
    log_price_changes = np.empty(n_products, dtype=np.float64)
    function_evaluations = np.zeros(n_products, dtype=np.int64)

    for product in range(n_products):
        supply_active = supply_anchors[:, product] > 0.0
        demand_active = demand_anchors[:, product] > 0.0
        label = products[product]
        if not np.any(supply_active):
            raise MarketStructureError(
                f"product {label!r} has no positive supply after structural zeros "
                "and shifters are applied"
            )
        if not np.any(demand_active):
            raise MarketStructureError(
                f"product {label!r} has no positive demand after structural zeros "
                "and shifters are applied"
            )

        active_supply_eps = supply_eps[supply_active, product]
        active_demand_eps = demand_eps[demand_active, product]
        if not (
            np.any(active_supply_eps > 0.0) or np.any(active_demand_eps < 0.0)
        ):
            raise MarketStructureError(
                f"product {label!r} has no price-responsive supply or demand, so "
                "its world price is not identified"
            )

        product_supply = supply_anchors[supply_active, product]
        product_demand = demand_anchors[demand_active, product]

        def market_balance(log_price: float) -> float:
            return _market_log_balance(
                log_price,
                product_supply,
                product_demand,
                active_supply_eps,
                active_demand_eps,
            )

        at_base = market_balance(0.0)
        function_evaluations[product] = 1
        if abs(at_base) <= price_tolerance:
            log_price_changes[product] = 0.0
            continue

        try:
            lower, upper, bracket_evaluations = _bracket_root(
                market_balance,
                at_base,
                max_abs_log_price,
            )
            function_evaluations[product] = bracket_evaluations
            root, details = brentq(
                market_balance,
                lower,
                upper,
                xtol=price_tolerance,
                rtol=max(price_tolerance, 4.0 * np.finfo(np.float64).eps),
                maxiter=int(max_iterations),
                full_output=True,
                disp=False,
            )
        except EquilibriumConvergenceError as exc:
            raise EquilibriumConvergenceError(
                f"failed to clear product {label!r}: {exc}"
            ) from exc
        except (RuntimeError, ValueError) as exc:
            raise EquilibriumConvergenceError(
                f"root solver failed for product {label!r}: {exc}"
            ) from exc

        function_evaluations[product] += int(details.function_calls)
        if not details.converged:
            raise EquilibriumConvergenceError(
                f"root solver did not converge for product {label!r}"
            )
        log_price_changes[product] = float(root)

    with np.errstate(over="ignore"):
        prices = prices_base * np.exp(log_price_changes)
    if not np.all(np.isfinite(prices)) or np.any(prices <= 0.0):
        raise EquilibriumConvergenceError(
            "equilibrium world prices exceed floating-point range"
        )

    supply = _evaluate_quantities(supply_anchors, supply_eps, log_price_changes)
    demand = _evaluate_quantities(demand_anchors, demand_eps, log_price_changes)
    global_supply = np.sum(supply, axis=0)
    global_demand = np.sum(demand, axis=0)
    if np.any(global_supply <= 0.0) or np.any(global_demand <= 0.0):
        raise EquilibriumConvergenceError(
            "equilibrium quantities underflowed to zero for at least one product"
        )
    excess_supply = global_supply - global_demand
    scale = np.maximum(global_supply, global_demand)
    residuals = excess_supply / scale

    if np.any(np.abs(residuals) > clearance_tolerance):
        failures = {
            products[index]: float(residuals[index])
            for index in np.flatnonzero(np.abs(residuals) > clearance_tolerance)
        }
        raise EquilibriumConvergenceError(
            "market-clearing tolerance was not met for products " f"{failures}"
        )

    return EquilibriumResult(
        prices=prices,
        supply=supply,
        demand=demand,
        global_supply=global_supply,
        global_demand=global_demand,
        excess_supply=excess_supply,
        residuals=residuals,
        log_price_changes=log_price_changes,
        function_evaluations=function_evaluations,
        region_names=regions,
        product_names=products,
    )


__all__ = [
    "EquilibriumConvergenceError",
    "EquilibriumInputError",
    "EquilibriumResult",
    "MarketStructureError",
    "solve_equilibrium",
]
