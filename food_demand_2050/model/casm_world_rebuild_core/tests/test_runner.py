from pathlib import Path

import pandas as pd
import yaml

from casm_world.runner import run_2023_smoke


ROOT = Path(__file__).resolve().parents[1]


def test_actual_interim_base_reaches_solver_and_reproduces_2023():
    path = ROOT / "data/processed/benchmark_equilibrium_interim_2023.csv"
    if not path.exists():
        raise AssertionError("Run python -m casm_world.calibration before this test")
    base = pd.read_csv(path)
    config = yaml.safe_load((ROOT / "config/model.yaml").read_text(encoding="utf-8"))
    economies, result = run_2023_smoke(base, list(config["commodities"]))
    assert len(economies) == 193
    assert result.max_abs_residual < 1e-10
    assert abs(result.prices - 1.0).max() < 1e-10

