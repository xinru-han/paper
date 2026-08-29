from pathlib import Path

import pandas as pd
import pytest

from casm_world.validation import (
    _sign_agrees,
    build_oecd_holdout,
    load_validation_config,
    oecd_holdout_metrics,
)


ROOT = Path(__file__).resolve().parents[1]


def test_validation_configuration_freezes_full_oecd_holdout():
    config = load_validation_config(ROOT / "config/validation.yaml")
    assert config["benchmark_year"] == 2023
    assert config["projection_end"] == 2050
    assert config["central_scenario"] == "SSP2"
    assert len(config["oecd_fao_holdout"]["commodities"]) == 9
    assert set(config["oecd_fao_holdout"]["areas"]) == {"W", "CHN", "EU"}


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(1.0, 2.0, True), (-1.0, -0.1, True), (1.0, -1.0, False), (0.0, 0.0, True)],
)
def test_sign_agreement_is_directional(left, right, expected):
    assert _sign_agrees(left, right) is expected


def test_oecd_holdout_is_exact_3_by_9_grid_and_metrics_are_reproducible():
    config = load_validation_config(ROOT / "config/validation.yaml")
    results = pd.read_csv(ROOT / config["inputs"]["results"])
    membership = pd.read_csv(ROOT / config["inputs"]["model_membership"])
    oecd = pd.read_csv(ROOT / config["inputs"]["oecd_fao"])
    comparison = build_oecd_holdout(results, membership, oecd, config)
    metrics = oecd_holdout_metrics(comparison)
    assert len(comparison) == 27
    assert comparison.groupby("area_external").size().to_dict() == {
        "CHN": 9, "EU": 9, "W": 9
    }
    assert metrics["comparison_count"] == 27
    assert metrics["world_comparison_count"] == 9
    assert 0 <= metrics["sign_agreement_share"] <= 1
