from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from casm_world.drivers import (
    EXPECTED_NODES,
    EXPECTED_SCENARIOS,
    build_ssp_drivers,
    load_scenario_config,
    log_interpolate_nodes,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def built_drivers():
    return build_ssp_drivers(ROOT)


def test_scenario_config_locks_requested_iiasa_series():
    config = load_scenario_config(ROOT / "config/scenarios.yaml")
    population = config["series"]["population"]
    gdp = config["series"]["gdp_ppp_per_capita"]
    assert (population["model"], population["variable"], population["unit"]) == (
        "IIASA-WiC POP 2025",
        "Population",
        "million",
    )
    assert (gdp["model"], gdp["variable"], gdp["unit"]) == (
        "OECD ENV-Growth 2025",
        "GDP|PPP [per capita]",
        "USD_2015/yr",
    )
    assert tuple(config["scenarios"]) == EXPECTED_SCENARIOS
    assert tuple(config["projection_nodes"]) == EXPECTED_NODES
    assert config["interpolation"]["missing_to_zero"] == "forbidden"


def test_drivers_cover_exactly_193_accounts_five_ssps_and_every_year(built_drivers):
    drivers, report = built_drivers
    assert report["status"] == "passed"
    assert report["model_account_count"] == 193
    assert report["territory_mappings_applied"] == 25
    assert len(drivers) == 193 * 5 * 28
    assert drivers["economy_id"].nunique() == 193
    assert set(drivers["scenario"]) == set(EXPECTED_SCENARIOS)
    assert set(drivers["year"]) == set(range(2023, 2051))
    per_path = drivers.groupby(["economy_id", "scenario"])["year"].nunique()
    assert per_path.eq(28).all()


def test_indices_are_positive_finite_complete_and_equal_one_in_2025(built_drivers):
    drivers, report = built_drivers
    values = drivers[
        ["population_index_2025", "gdp_ppp_per_capita_index_2025"]
    ]
    assert not values.isna().any().any()
    assert np.isfinite(values.to_numpy()).all()
    assert values.gt(0).all().all()
    assert drivers.loc[drivers["year"].eq(2025), values.columns].eq(1.0).all().all()
    assert report["missing_value_count"] == 0
    assert report["zero_fill_count"] == 0


def test_absolute_population_and_gdp_paths_are_retained_and_reconcile(built_drivers):
    drivers, report = built_drivers
    absolute = drivers[
        ["population_million", "gdp_billion_2015", "gdp_pc_usd_2015"]
    ]
    assert np.isfinite(absolute.to_numpy()).all()
    assert absolute.gt(0).all().all()
    implied = drivers["gdp_pc_usd_2015"] * drivers["population_million"] / 1000.0
    assert implied.to_numpy() == pytest.approx(
        drivers["gdp_billion_2015"].to_numpy(), rel=1e-12
    )
    assert report["output_units"]["population_million"] == "million persons"


def test_five_year_nodes_are_interpolated_linearly_in_logs(built_drivers):
    drivers, _ = built_drivers
    path = drivers[
        drivers["economy_id"].eq("CHN") & drivers["scenario"].eq("SSP2")
    ].set_index("year")
    for column in ["population_index_2025", "gdp_ppp_per_capita_index_2025"]:
        expected_2027 = path.at[2030, column] ** (2.0 / 5.0)
        assert path.at[2027, column] == pytest.approx(expected_2027, rel=1e-12)


def test_2023_2024_history_bridge_is_scenario_independent(built_drivers):
    drivers, report = built_drivers
    early = drivers[drivers["year"].isin([2023, 2024])]
    spread = early.groupby(["economy_id", "year"])[
        ["population_index_2025", "gdp_ppp_per_capita_index_2025"]
    ].agg(lambda values: float(values.max() - values.min()))
    assert spread.to_numpy().max() < 1e-12
    assert report["pre_anchor_method"] == (
        "log_linear_historical_2020_to_historical_2025_then_rebased_ssp"
    )


def test_fallbacks_are_explicit_and_match_known_iiasa_gaps(built_drivers):
    _, report = built_drivers
    population = {
        row["economy_id"]: row for row in report["population_fallbacks"]
    }
    gdp = {row["economy_id"]: row for row in report["gdp_non_direct_routes"]}
    assert population["BMU"]["status"] == "fallback_proxy_growth"
    assert population["ASM"]["proxy_economy_id"] == "USA"
    assert gdp["AFG"]["status"] == "official_turbulent_supplement"
    assert gdp["CUB"]["status"] == "fallback_alternate_unit_rescaled"
    assert gdp["ASM"]["status"] == "fallback_proxy_growth_and_level"
    assert gdp["ESH"]["status"] == "gdp_scope_excluded_parent_inclusive"
    assert report["alternate_gdp_unit_to_2015_factor"] > 0


def test_taiwan_maps_only_to_other_eastern_asia(built_drivers):
    drivers, report = built_drivers
    assert "TWN" not in set(drivers["economy_id"])
    assert "OTHER_EASTERN_ASIA" in set(drivers["economy_id"])
    assert "CHN" in set(drivers["economy_id"])
    assert report["twn_accounting_target"] == "OTHER_EASTERN_ASIA"
    assert report["other_eastern_asia_source_components"] == ["TWN"]
    assert report["chn_contains_twn"] is False


def test_log_interpolation_rejects_missing_zero_and_extrapolation():
    with pytest.raises(ValueError, match="positive"):
        log_interpolate_nodes({2025: 1.0, 2030: 0.0}, range(2025, 2031))
    with pytest.raises(ValueError, match="extrapolate"):
        log_interpolate_nodes({2025: 1.0, 2030: 2.0}, [2024, 2025])
    result = log_interpolate_nodes({2025: 1.0, 2030: 4.0}, range(2025, 2031))
    assert result[2027] == pytest.approx(4.0 ** (2.0 / 5.0))
