import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from casm_world.linked_equilibrium import ProcessSpec
from casm_world.simulation import (
    _apply_process_response_horizon,
    _apply_process_supply_shifters,
    _effective_supply_elasticity,
    _fit_process_long_run_elasticities,
    _response_horizon_factor,
    _validate_v2_parameter_contract,
    load_simulation_inputs,
    run_simulation,
)


ROOT = Path(__file__).resolve().parents[1]


def test_v1_parameter_table_is_rejected_by_v2_contract():
    old = pd.DataFrame(
        {
            "parameter_set": ["CASM_WORLD_ELASTICITIES_V1"],
            "parameter_status": ["final_casm_v1"],
        }
    )
    contract = {
        "required_parameter_set": "CASM_WORLD_ELASTICITIES_V2",
        "marker_column": "parameter_status",
        "marker_contains": "v2",
    }
    with pytest.raises(ValueError, match="Parameter set must be exactly"):
        _validate_v2_parameter_contract(old, contract)


def test_v2_response_horizon_uses_long_run_at_base_and_partial_adjustment_after():
    lag = np.array([0.10, 0.25])
    assert _response_horizon_factor(2023, 2023, lag) == pytest.approx([1.0, 1.0])
    assert _response_horizon_factor(2024, 2023, lag) == pytest.approx([0.90, 0.75])
    assert _response_horizon_factor(2025, 2023, lag) == pytest.approx([0.99, 0.9375])

    long_run = np.array([[0.4, 0.8], [0.3, 0.6]])
    effective = _effective_supply_elasticity(long_run, lag, 2024, 2023)
    assert effective == pytest.approx(long_run * np.array([0.90, 0.75]))


def test_process_long_run_parameters_are_independent_and_horizon_adjusted():
    shape = (2, 2)
    processes = (
        ProcessSpec(
            name="soybean_crush",
            base_activity=np.ones(2),
            input_coefficients=np.zeros(shape),
            output_coefficients=np.ones(shape),
            elasticity=np.full(2, 99.0),
        ),
        ProcessSpec(
            name="cotton_ginning",
            base_activity=np.ones(2),
            input_coefficients=np.zeros(shape),
            output_coefficients=np.ones(shape),
            elasticity=np.full(2, 99.0),
        ),
        ProcessSpec(
            name="dairy_unmodelled_use",
            base_activity=np.ones(2),
            input_coefficients=np.ones(shape),
            output_coefficients=np.zeros(shape),
            elasticity=np.full(2, 99.0),
        ),
    )
    config = {
        "activities": {
            "soybean_crush": {
                "elasticity_method": "fixed",
                "long_run_elasticity": 1.5,
                "lambda": 0.10,
            },
            "cotton_ginning": {
                "elasticity_method": "product_parameter",
                "parameter_product": "CTN",
                "lambda": 0.10,
            },
            "dairy_unmodelled_use": {
                "elasticity_method": "fixed_zero",
                "long_run_elasticity": 0.0,
                "lambda": 0.20,
            },
        }
    }
    supply = np.array([[0.2, 0.4], [0.3, 0.5]])
    fitted, lags = _fit_process_long_run_elasticities(
        processes, supply, ("A", "CTN"), config
    )
    assert fitted[0].elasticity == pytest.approx([1.5, 1.5])
    assert fitted[1].elasticity == pytest.approx([0.4, 0.5])
    assert fitted[2].elasticity == pytest.approx([0.0, 0.0])

    base = _apply_process_response_horizon(fitted, lags, 2023, 2023)
    one_year = _apply_process_response_horizon(fitted, lags, 2024, 2023)
    assert base[0].elasticity == pytest.approx([1.5, 1.5])
    assert one_year[0].elasticity == pytest.approx([1.35, 1.35])
    assert one_year[1].elasticity == pytest.approx([0.36, 0.45])
    assert one_year[2].elasticity == pytest.approx([0.0, 0.0])


def test_unknown_process_response_fails_closed():
    process = ProcessSpec(
        name="new_unconfigured_process",
        base_activity=np.ones(1),
        input_coefficients=np.zeros((1, 1)),
        output_coefficients=np.ones((1, 1)),
        elasticity=np.ones(1),
    )
    with pytest.raises(ValueError, match="whitelist mismatch"):
        _fit_process_long_run_elasticities(
            (process,), np.ones((1, 1)), ("A",), {"activities": {}}
        )


def test_process_activity_inherits_output_weighted_geometric_supply_shift():
    process = ProcessSpec(
        name="joint_output",
        base_activity=np.ones(2),
        input_coefficients=np.zeros((2, 3)),
        output_coefficients=np.array([[1.0, 3.0, 0.0], [0.0, 0.0, 0.0]]),
        elasticity=np.full(2, 0.2),
    )
    supply_shifter = np.array([[4.0, 16.0, 9.0], [2.0, 3.0, 4.0]])

    shifted = _apply_process_supply_shifters((process,), supply_shifter)[0]

    assert shifted.activity_shifter[0] == pytest.approx(4.0**0.25 * 16.0**0.75)
    assert shifted.activity_shifter[1] == pytest.approx(1.0)


def test_single_output_process_inherits_full_supply_shift_and_unit_base():
    process = ProcessSpec(
        name="cotton_ginning",
        base_activity=np.ones(2),
        input_coefficients=np.zeros((2, 2)),
        output_coefficients=np.array([[0.0, 0.3352], [0.0, 0.3352]]),
        elasticity=np.full(2, 0.1),
    )
    shifted = _apply_process_supply_shifters(
        (process,), np.array([[1.0, 1.0], [1.0, 1.7]])
    )[0]

    assert shifted.activity_shifter == pytest.approx([1.0, 1.7])


def test_2023_ssp2_reproduces_balanced_base_and_passes_all_gates():
    inputs = load_simulation_inputs(ROOT)
    assert inputs.parameter_set == "CASM_WORLD_ELASTICITIES_V2"
    assert inputs.parameter_table == "data/processed/casm_world_parameters_v2_2023.csv"
    assert inputs.parameter_table_sha256 == hashlib.sha256(
        (ROOT / inputs.parameter_table).read_bytes()
    ).hexdigest()
    assert inputs.simulation_config_sha256 == hashlib.sha256(
        (ROOT / "config/simulation.yaml").read_bytes()
    ).hexdigest()
    process = {spec.name: spec for spec in inputs.system.processes}
    assert process["soybean_crush"].elasticity == pytest.approx(
        np.full(193, 1.5)
    )
    assert process["dairy_solids"].elasticity == pytest.approx(np.full(193, 3.0))
    cotton_index = inputs.system.products.index("CTN")
    assert process["cotton_ginning"].elasticity == pytest.approx(
        inputs.supply_elasticity[:, cotton_index]
    )
    assert process["dairy_unmodelled_use"].elasticity == pytest.approx(
        np.zeros(193)
    )
    results, prices, processes, convergence, report = run_simulation(
        inputs, scenarios=["SSP2"], years=[2023]
    )
    assert len(results) == 193 * 31
    assert prices["world_price_index_2023"].to_numpy() == pytest.approx(
        np.ones(31), abs=1e-12
    )
    assert report["all_years_converged"] is True
    assert report["parameter_table_sha256"] == inputs.parameter_table_sha256
    assert report["simulation_config_sha256"] == inputs.simulation_config_sha256
    assert report["maximum_market_relative_residual"] < 1e-9
    assert convergence["maximum_accounting_absolute_residual_mt"].max() < 1e-9
    assert (results["food_demand_mt"] >= 0).all()
    assert (results["food_demand_mt"] <= results["final_demand_mt"] + 1e-12).all()
    assert not processes.empty

    benchmark = pd.read_csv(ROOT / "data/processed/benchmark_equilibrium_2023.csv")
    exact = results.merge(
        benchmark,
        on=["economy_id", "commodity"],
        how="inner",
        validate="one_to_one",
    )
    quantity_pairs = {
        "production_mt": "supply_2023",
        "final_demand_mt": "final_demand_2023",
        "food_demand_mt": "food_demand_2023",
        "processing_demand_mt": "processing_demand_2023",
        "demand_mt": "demand_2023",
        "net_import_mt": "net_import_2023",
    }
    assert len(exact) == 193 * 31
    for model_column, benchmark_column in quantity_pairs.items():
        assert (
            exact[model_column] - exact[benchmark_column]
        ).abs().max() < 1.0e-8

    base_activities = pd.read_csv(
        ROOT / "data/processed/benchmark_processing_activities_2023.csv"
    ).pivot_table(
        index="economy_id",
        columns="process",
        values="balanced_activity_2023",
        aggfunc="sum",
    ).reindex(index=inputs.system.regions).fillna(0.0)
    solved_activities = processes.pivot(
        index="economy_id", columns="process", values="activity"
    ).reindex(index=inputs.system.regions).fillna(0.0)
    for name in (
        "soybean_crush",
        "sunflower_crush",
        "rapeseed_crush",
        "sugar_SCA",
        "sugar_SBE",
        "cotton_ginning",
    ):
        assert solved_activities[name].to_numpy() == pytest.approx(
            base_activities[name].to_numpy(), abs=1.0e-8
        )
    assert (
        solved_activities["dairy_solids"]
        + solved_activities["dairy_unmodelled_use"]
    ).to_numpy() == pytest.approx(
        base_activities["dairy_milk"].to_numpy(), abs=1.0e-8
    )
    ethanol_base = benchmark[benchmark["commodity"].eq("ETH")].set_index(
        "economy_id"
    )["supply_2023"].reindex(inputs.system.regions)
    assert solved_activities["ethanol"].to_numpy() == pytest.approx(
        ethanol_base.to_numpy(), abs=1.0e-8
    )


def test_2024_ssp2_converges_sequentially_and_is_not_the_base():
    inputs = load_simulation_inputs(ROOT)
    _, prices, _, convergence, report = run_simulation(
        inputs, scenarios=["SSP2"], years=[2023, 2024]
    )
    assert report["annual_solution_count"] == 2
    assert convergence["converged"].all()
    p2024 = prices[prices.year.eq(2024)]["world_price_index_2023"]
    assert not np.allclose(p2024, 1.0)
