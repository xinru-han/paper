from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from casm_world.balancing import (
    build_joint_balanced_benchmark,
    weighted_nonnegative_projection,
)


ROOT = Path(__file__).resolve().parents[1]


def test_weighted_projection_respects_equalities_and_nonnegativity():
    anchors = np.array([10.0, 4.0, 3.0])
    precision = np.ones(3)
    from scipy.sparse import csr_matrix

    matrix = csr_matrix([[1.0, -1.0, -1.0]])
    result = weighted_nonnegative_projection(
        anchors, precision, matrix, np.zeros(1)
    )
    assert result.values.min() >= 0
    assert result.residuals[0] == pytest.approx(0.0, abs=1e-10)


def test_real_joint_benchmark_has_exact_market_and_processing_identities():
    observations = pd.read_csv(ROOT / "data/processed/benchmark_unbalanced_2023.csv")
    interim = pd.read_csv(ROOT / "data/processed/benchmark_equilibrium_interim_2023.csv")
    commodities = yaml.safe_load((ROOT / "config/commodities.yaml").read_text())
    balancing = yaml.safe_load((ROOT / "config/balancing.yaml").read_text())
    benchmark, activities, variables, report = build_joint_balanced_benchmark(
        observations,
        interim["economy_id"].unique().tolist(),
        commodities,
        balancing,
    )
    assert len(benchmark) == 193 * 31
    assert benchmark[["supply_2023", "demand_2023"]].min().min() >= 0
    assert np.allclose(
        benchmark["food_demand_2023"] + benchmark["other_final_demand_2023"],
        benchmark["final_demand_2023"],
    )
    assert (benchmark["food_demand_2023"] <= benchmark["final_demand_2023"]).all()
    residual = benchmark.groupby("commodity")["net_import_2023"].sum().abs().max()
    assert residual < 1e-8
    assert report["maximum_processing_residual_mt"] < 1e-8
    assert report["silent_missing_to_zero"] is False
    assert report["numeric_gate_passed"] is True
    assert report["domain_review_gate_passed"] is True
    assert report["cotton_material_missing_activity_count"] == 0
    assert 0.0 < report["unmodelled_dairy_solids_share"] < 0.30
    assert report["internal_review_not_independent_peer_review"] is True
    assert report["publishable"] is True
    assert not activities.empty and not variables.empty
