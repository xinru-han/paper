from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from casm_world.sensitivity import (
    SensitivityError,
    _add_all_price_comparisons,
    _parameter_matrix,
    _select_reported_groups,
    build_materiality_screen,
    load_sensitivity_config,
    scale_post_2035_tfp,
    solve_linked_equilibrium_ces,
)


ROOT = Path(__file__).resolve().parents[1]


def test_sensitivity_config_freezes_five_ssp_annual_envelope_and_pending_cases():
    config = load_sensitivity_config(ROOT / "config/sensitivity.yaml")
    assert config["scenarios"] == ["SSP1", "SSP2", "SSP3", "SSP4", "SSP5"]
    assert config["retained_summary_years"] == [2023, 2035, 2050]
    assert list(config["parameter_response_variants"]) == [
        "V2_LOW_RESPONSE",
        "V2_CENTRAL",
        "V2_HIGH_RESPONSE",
    ]
    assert config["tfp_variants"]["TFP_SLOW"][
        "post_2035_positive_log_growth_multiplier"
    ] == 0.75
    assert config["tfp_variants"]["TFP_FAST"][
        "post_2035_positive_log_growth_multiplier"
    ] == 1.25
    assert config["demand_substitution_ces"]["enabled"] is True
    assert set(config["demand_substitution_ces"]["nests"]) == {
        "grains",
        "vegetable_oils",
        "meals_feed_byproducts",
        "meats",
        "processed_dairy",
    }
    assert set(config["not_implemented_structural_sensitivities"]) == {
        "SHARED_CROP_RESOURCE"
    }
    assert len(config["primary_basket"]) == 13
    assert all(
        str(value).startswith("outputs/sensitivity/")
        for key, value in config["outputs"].items()
        if key != "directory"
    )


def test_post_2035_tfp_scaling_keeps_anchor_and_nonpositive_rate():
    positive_rate = 0.02
    negative_rate = -0.003
    frame = pd.DataFrame(
        {
            "scenario": ["SSP2"] * 5,
            "economy_id": ["AAA"] * 5,
            "year": [2033, 2034, 2035, 2036, 2037],
            "tfp_index_2023": [
                1.0,
                np.exp(0.01),
                np.exp(0.02),
                np.exp(0.02 + positive_rate),
                np.exp(0.02 + positive_rate + negative_rate),
            ],
        }
    )
    slow = scale_post_2035_tfp(frame, 0.75)
    assert np.array_equal(
        slow.loc[slow["year"] <= 2035, "tfp_index_2023"].to_numpy(),
        frame.loc[frame["year"] <= 2035, "tfp_index_2023"].to_numpy(),
    )
    expected_2036 = np.exp(0.02) * np.exp(positive_rate * 0.75)
    expected_2037 = expected_2036 * np.exp(negative_rate)
    assert slow.loc[slow["year"].eq(2036), "tfp_index_2023"].iloc[0] == pytest.approx(
        expected_2036
    )
    assert slow.loc[slow["year"].eq(2037), "tfp_index_2023"].iloc[0] == pytest.approx(
        expected_2037
    )


def test_post_2035_tfp_positive_rate_respects_upper_bound():
    frame = pd.DataFrame(
        {
            "scenario": ["SSP1", "SSP1"],
            "economy_id": ["AAA", "AAA"],
            "year": [2035, 2036],
            "tfp_index_2023": [1.0, np.exp(0.04)],
        }
    )
    fast = scale_post_2035_tfp(frame, 1.25)
    assert fast.loc[fast["year"].eq(2036), "tfp_index_2023"].iloc[0] == pytest.approx(
        np.exp(0.035)
    )


def test_parameter_matrix_rejects_missing_variant_column():
    frame = pd.DataFrame(
        {"economy_id": ["AAA"], "commodity": ["RIC"], "central": [0.2]}
    )
    with pytest.raises(SensitivityError, match="lacks required variant column"):
        _parameter_matrix(frame, ["AAA"], ["RIC"], "low")


def _screen_fixture(config):
    variants = [
        "V2_LOW_RESPONSE",
        "V2_CENTRAL",
        "V2_HIGH_RESPONSE",
        "TFP_SLOW",
        "TFP_FAST",
        "DEMAND_SUBSTITUTION_CES",
    ]
    families = {
        "V2_LOW_RESPONSE": "parameter_response_envelope",
        "V2_CENTRAL": "central_reference",
        "V2_HIGH_RESPONSE": "parameter_response_envelope",
        "TFP_SLOW": "tfp_model_form",
        "TFP_FAST": "tfp_model_form",
        "DEMAND_SUBSTITUTION_CES": "demand_model_form",
    }
    price_rows = []
    group_rows = []
    for variant in variants:
        price = 1.0
        production = 100.0
        if variant == "V2_HIGH_RESPONSE":
            price = 1.25
        if variant == "TFP_FAST":
            production = 111.0
        price_rows.append(
            {
                "variant": variant,
                "variant_family": families[variant],
                "scenario": "SSP2",
                "year": 2050,
                "commodity": "RIC",
                "world_price_index_2023": price,
            }
        )
        group_rows.append(
            {
                "variant": variant,
                "variant_family": families[variant],
                "scenario": "SSP2",
                "year": 2050,
                "group_system": "GLOBAL",
                "group_code": "WORLD",
                "group_name": "World",
                "primary_basket_production_mt": production,
                "primary_basket_food_demand_mt": 90.0,
                "primary_basket_net_import_mt": 0.0,
            }
        )
    return pd.DataFrame(price_rows), pd.DataFrame(group_rows)


def test_materiality_screen_reports_price_and_production_thresholds():
    config = load_sensitivity_config(ROOT / "config/sensitivity.yaml")
    prices, groups = _screen_fixture(config)
    screen = build_materiality_screen(prices, groups, config).set_index("variant")
    assert bool(screen.at["V2_HIGH_RESPONSE", "price_threshold_exceeded"])
    assert screen.at[
        "V2_HIGH_RESPONSE", "maximum_major_food_world_price_deviation_percent"
    ] == pytest.approx(25.0)
    assert bool(screen.at["TFP_FAST", "production_threshold_exceeded"])
    assert screen.at[
        "TFP_FAST", "maximum_primary_production_deviation_percent"
    ] == pytest.approx(11.0)
    assert not bool(screen.at["V2_CENTRAL", "either_threshold_exceeded"])
    assert screen.at["TFP_FAST", "interpretation"].startswith("section_8_5")
    premerged = _add_all_price_comparisons(prices)
    repeated = build_materiality_screen(premerged, groups, config).set_index("variant")
    assert repeated.at[
        "V2_HIGH_RESPONSE", "maximum_major_food_world_price_deviation_percent"
    ] == pytest.approx(25.0)


def test_two_product_cobb_douglas_nest_reproduces_base_and_clears():
    primary = np.array([[60.0, 40.0], [40.0, 60.0]])
    final = np.array([[55.0, 35.0], [45.0, 65.0]])
    result = solve_linked_equilibrium_ces(
        primary,
        final,
        supply_elasticity=0.3,
        demand_elasticity=-0.4,
        ces_nests={"two_products": ["A", "B"]},
        sigma=1.0,
        region_names=["R1", "R2"],
        product_names=["A", "B"],
    )
    assert result.prices == pytest.approx([1.0, 1.0], abs=1.0e-12)
    assert result.final_demand == pytest.approx(final, abs=1.0e-10)
    assert result.max_abs_residual <= 1.0e-10


def test_cobb_douglas_nest_reallocates_demand_after_relative_supply_shock():
    primary = np.array([[100.0, 100.0]])
    final = np.array([[100.0, 100.0]])
    result = solve_linked_equilibrium_ces(
        primary,
        final,
        supply_elasticity=0.3,
        demand_elasticity=-0.4,
        ces_nests={"two_products": ["A", "B"]},
        sigma=1.0,
        supply_shifter=np.array([[0.8, 1.2]]),
        product_names=["A", "B"],
    )
    assert result.max_abs_residual <= 1.0e-9
    assert result.prices[0] > result.prices[1]
    assert result.final_demand[0, 0] < result.final_demand[0, 1]


def test_reported_group_selection_keeps_nonoverlapping_un_reporting_areas():
    config = load_sensitivity_config(ROOT / "config/sensitivity.yaml")
    rows = []
    for variant, factor in (("V2_CENTRAL", 1.0), ("V2_LOW_RESPONSE", 0.9)):
        family = "central_reference" if variant == "V2_CENTRAL" else "parameter_response_envelope"
        for year, growth in ((2023, 1.0), (2050, 1.2)):
            for system, code, name in (
                ("GLOBAL", "WORLD", "World"),
                ("UN_REPORTING_AREA", "030", "Eastern Asia"),
                ("WB_INCOME_FY25", "HIC", "High income"),
            ):
                rows.append(
                    {
                        "variant": variant,
                        "variant_family": family,
                        "scenario": "SSP2",
                        "year": year,
                        "group_system": system,
                        "group_code": code,
                        "group_name": name,
                        "primary_basket_production_mt": 100.0 * growth * factor,
                        "primary_basket_food_demand_mt": 80.0 * growth * factor,
                        "primary_basket_net_import_mt": 5.0 * growth * factor,
                    }
                )
    selected = _select_reported_groups(pd.DataFrame(rows), config)
    assert set(selected["group_system"]) == {"GLOBAL", "UN_REPORTING_AREA"}
    eastern = selected[
        selected["variant"].eq("V2_LOW_RESPONSE")
        & selected["year"].eq(2050)
        & selected["group_code"].eq("030")
    ].iloc[0]
    assert eastern["primary_basket_production_mt_change_from_2023_percent"] == pytest.approx(
        20.0
    )
    assert eastern[
        "primary_basket_production_mt_relative_to_central_percent"
    ] == pytest.approx(-10.0)
