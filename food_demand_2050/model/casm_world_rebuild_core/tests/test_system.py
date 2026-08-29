from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from casm_world.linked_equilibrium import solve_linked_equilibrium
from casm_world.system import build_model_system


ROOT = Path(__file__).resolve().parents[1]


def test_real_system_reproduces_balanced_base_and_clears_at_unit_prices():
    benchmark = pd.read_csv(ROOT / "data/processed/benchmark_equilibrium_2023.csv")
    activities = pd.read_csv(ROOT / "data/processed/benchmark_processing_activities_2023.csv")
    config = yaml.safe_load((ROOT / "config/commodities.yaml").read_text())
    system = build_model_system(benchmark, activities, config)
    result = solve_linked_equilibrium(
        system.base_primary_supply,
        system.base_final_demand,
        supply_elasticity=0.3,
        demand_elasticity=-0.3,
        processes=system.processes,
        region_names=system.regions,
        product_names=system.products,
    )
    assert result.max_abs_residual < 1e-10
    assert result.prices == pytest.approx(np.ones(31), abs=1e-9)
    assert result.total_supply.sum(axis=0) == pytest.approx(
        result.total_demand.sum(axis=0), rel=1e-10, abs=1e-10
    )
