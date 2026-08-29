from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from casm_world.equilibrium import (  # noqa: E402
    EquilibriumInputError,
    MarketStructureError,
    solve_equilibrium,
)


@pytest.fixture
def balanced_markets() -> dict[str, np.ndarray | list[str]]:
    return {
        "base_supply": np.array([[60.0, 30.0], [40.0, 70.0]]),
        "base_demand": np.array([[55.0, 45.0], [45.0, 55.0]]),
        "supply_elasticity": np.array([[0.30, 0.40], [0.50, 0.20]]),
        "demand_elasticity": np.array([[-0.40, -0.60], [-0.30, -0.50]]),
        "base_prices": np.array([2.0, 3.0]),
        "region_names": ["North", "South"],
        "product_names": ["grain", "meat"],
    }


def test_base_equilibrium_reproduces_quantities_and_prices(balanced_markets) -> None:
    result = solve_equilibrium(**balanced_markets)

    np.testing.assert_allclose(result.prices, balanced_markets["base_prices"])
    np.testing.assert_allclose(result.supply, balanced_markets["base_supply"])
    np.testing.assert_allclose(result.demand, balanced_markets["base_demand"])
    np.testing.assert_allclose(result.log_price_changes, 0.0)
    assert result.max_abs_residual < 1.0e-12


def test_positive_demand_shift_raises_affected_world_price(balanced_markets) -> None:
    demand_shifter = np.ones((2, 2))
    demand_shifter[:, 0] = 1.10

    result = solve_equilibrium(
        **balanced_markets,
        demand_shifter=demand_shifter,
    )

    assert result.prices[0] > balanced_markets["base_prices"][0]
    assert result.prices[1] == pytest.approx(balanced_markets["base_prices"][1])
    assert result.max_abs_residual < 1.0e-9


def test_every_product_clears_after_region_specific_shifts(balanced_markets) -> None:
    result = solve_equilibrium(
        **balanced_markets,
        supply_shifter=np.array([[1.02, 0.97], [0.98, 1.04]]),
        demand_shifter=np.array([[1.08, 0.95], [1.03, 1.10]]),
    )

    assert np.all(np.abs(result.market_clearing_residuals) < 1.0e-9)
    assert np.all(np.abs(result.absolute_residuals) < 1.0e-9)
    np.testing.assert_allclose(
        result.global_supply,
        result.global_demand,
        rtol=1.0e-9,
        atol=1.0e-9,
    )


def test_structural_zeros_remain_zero() -> None:
    result = solve_equilibrium(
        base_supply=np.array([[100.0, 0.0], [0.0, 80.0]]),
        base_demand=np.array([[40.0, 0.0], [60.0, 80.0]]),
        supply_elasticity=np.array([[0.4, 0.0], [0.0, 0.3]]),
        demand_elasticity=np.array([[-0.2, 0.0], [-0.5, -0.4]]),
        supply_shifter=1.05,
        demand_shifter=1.05,
    )

    assert result.supply[0, 1] == 0.0
    assert result.supply[1, 0] == 0.0
    assert result.demand[0, 1] == 0.0
    assert result.max_abs_residual < 1.0e-9


def test_missing_values_are_not_treated_as_structural_zeros(
    balanced_markets,
) -> None:
    base_supply = balanced_markets["base_supply"].copy()
    base_supply[0, 0] = np.nan

    with pytest.raises(EquilibriumInputError, match="missing or non-finite"):
        solve_equilibrium(
            **{**balanced_markets, "base_supply": base_supply},
        )


def test_product_with_no_supply_is_rejected() -> None:
    with pytest.raises(MarketStructureError, match="no positive supply"):
        solve_equilibrium(
            base_supply=np.array([[10.0, 0.0], [5.0, 0.0]]),
            base_demand=np.array([[8.0, 4.0], [7.0, 6.0]]),
            supply_elasticity=0.4,
            demand_elasticity=-0.3,
            product_names=["active", "absent"],
        )
