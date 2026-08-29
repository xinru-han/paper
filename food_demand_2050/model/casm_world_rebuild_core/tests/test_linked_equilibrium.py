import numpy as np
import pytest

from casm_world.linked_equilibrium import ProcessSpec, solve_linked_equilibrium


def test_processing_links_clear_input_and_output_markets_at_base():
    # A: 100 primary supply = 40 final demand + 60 process input.
    # B: process output 0.5*60 = 30 final demand.
    primary = np.array([[60.0, 0.0], [40.0, 0.0]])
    final = np.array([[25.0, 18.0], [15.0, 12.0]])
    process = ProcessSpec(
        name="A_to_B",
        base_activity=np.array([35.0, 25.0]),
        input_coefficients=np.array([[1.0, 0.0], [1.0, 0.0]]),
        output_coefficients=np.array([[0.0, 0.5], [0.0, 0.5]]),
        elasticity=np.array([1.0, 1.0]),
    )
    result = solve_linked_equilibrium(
        primary,
        final,
        supply_elasticity=0.3,
        demand_elasticity=-0.4,
        processes=[process],
        region_names=["R1", "R2"],
        product_names=["A", "B"],
    )
    assert result.prices == pytest.approx([1.0, 1.0], abs=1e-10)
    assert result.max_abs_residual < 1e-10
    assert result.process_demand[:, 0].sum() == pytest.approx(60.0)
    assert result.process_supply[:, 1].sum() == pytest.approx(30.0)


def test_coupled_shock_changes_both_prices_and_still_clears():
    primary = np.array([[100.0, 0.0]])
    final = np.array([[40.0, 30.0]])
    process = ProcessSpec(
        name="A_to_B",
        base_activity=np.array([60.0]),
        input_coefficients=np.array([[1.0, 0.0]]),
        output_coefficients=np.array([[0.0, 0.5]]),
        elasticity=np.array([0.8]),
    )
    result = solve_linked_equilibrium(
        primary,
        final,
        supply_elasticity=np.array([[0.4, 0.0]]),
        demand_elasticity=np.array([[-0.3, -0.5]]),
        demand_shifter=np.array([[1.1, 1.2]]),
        processes=[process],
        product_names=["A", "B"],
    )
    assert result.max_abs_residual < 1e-9
    assert not np.allclose(result.prices, 1.0)
