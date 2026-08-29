import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from casm_world.concordance import load_concordance
from casm_world.ghg import (
    build_ghg_module,
    load_ghg_config,
    postsolve,
    run_formal_ssp_ghg,
    summarize_postsolve,
    validate_ssp_production_input,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = load_ghg_config(ROOT / "config" / "ghg.yaml")
CONCORDANCE = load_concordance(ROOT / "config" / "commodities.yaml")


@pytest.fixture(scope="module")
def completed_ghg():
    scenario_report = run_formal_ssp_ghg(ROOT)
    report = json.loads((ROOT / CONFIG["outputs"]["report"]).read_text())
    factors = pd.read_csv(ROOT / CONFIG["outputs"]["factors"])
    baseline = pd.read_csv(ROOT / CONFIG["outputs"]["base_postsolve"])
    aggregates = pd.read_csv(ROOT / CONFIG["outputs"]["base_aggregates"])
    validation = pd.read_csv(ROOT / CONFIG["outputs"]["validation_table"])
    return scenario_report, report, factors, baseline, aggregates, validation


@pytest.fixture(scope="module")
def built_ghg(completed_ghg):
    _, report, factors, baseline, aggregates, validation = completed_ghg
    return report, factors, baseline, aggregates, validation


@pytest.fixture(scope="module")
def formal_ssp_ghg(completed_ghg):
    scenario_report, *_ = completed_ghg
    country = pd.read_csv(ROOT / CONFIG["scenario_outputs"]["country"])
    product = pd.read_csv(ROOT / CONFIG["scenario_outputs"]["product"])
    world = pd.read_csv(ROOT / CONFIG["scenario_outputs"]["world"])
    return scenario_report, country, product, world


def test_config_covers_exact_model_products_and_keeps_nitrogen_deleted():
    assert set(CONFIG["products"]) == set(CONCORDANCE["commodities"])
    assert len(CONFIG["products"]) == 31
    assert CONFIG["module"]["execution_stage"] == "post_solution"
    assert CONFIG["module"]["nitrogen_module_enabled"] is False
    assert CONFIG["module"]["production_unit"] == "Mt"
    assert CONFIG["module"]["intensity_unit"] == "kg CO2e/kg product"
    assert CONFIG["module"]["emissions_unit"] == "Mt CO2e"


def test_factor_rectangle_has_explicit_fallback_and_no_missing_values(built_ghg):
    report, factors, *_ = built_ghg
    assert report["model_account_count"] == 193
    assert report["commodity_count"] == 31
    assert len(factors) == 193 * 31
    assert not factors.duplicated(["economy_id", "commodity"]).any()
    assert not factors.isna().any().any()
    numeric = [
        "country_coefficient_kgco2e_per_kg",
        "un_region_median_kgco2e_per_kg",
        "global_median_kgco2e_per_kg",
        "coefficient_kgco2e_per_kg",
    ]
    assert np.isfinite(factors[numeric].to_numpy()).all()
    assert (factors[numeric] >= 0).all().all()
    assert factors["coefficient_unit"].eq("kg CO2e/kg product").all()
    assert set(factors["coverage_status"]) == {"direct", "inherited", "noncovered"}
    assert set(factors["fallback_level"]) == {
        "country",
        "un_region_median",
        "global_median",
        "not_applicable_noncovered",
    }
    covered = factors[~factors["coverage_status"].eq("noncovered")]
    assert covered["fallback_level"].isin(
        ["country", "un_region_median", "global_median"]
    ).all()
    noncovered = factors[factors["coverage_status"].eq("noncovered")]
    assert noncovered["fallback_level"].eq("not_applicable_noncovered").all()
    assert noncovered["coefficient_kgco2e_per_kg"].eq(0).all()


def test_processing_boundary_books_upstream_once(built_ghg):
    _, factors, *_ = built_ghg
    product_status = factors.groupby("commodity")["coverage_status"].unique().map(
        lambda values: values.item()
    )
    expected_noncovered = {
        "SBO",
        "SBM",
        "NBO",
        "NBM",
        "RBO",
        "RBM",
        "DDG",
        "ETH",
        "BDI",
        "OTO",
        "CTN",
        "SUG",
        "BUT",
        "CHE",
        "NDM",
        "FMK",
        "WDM",
        "ODA",
    }
    assert set(product_status[product_status.eq("noncovered")].index) == expected_noncovered
    assert set(product_status[["SBS", "NBS", "RBS"]]) <= {"direct", "inherited"}
    assert set(product_status[["SCA", "SBE"]]) <= {"direct", "inherited"}
    assert product_status["MLK"] == "direct"

    china = factors[factors["economy_id"].eq("CHN")].set_index("commodity")
    for raw_input in ["SBS", "NBS", "RBS", "SCA", "SBE", "MLK"]:
        assert china.at[raw_input, "coefficient_kgco2e_per_kg"] >= 0
    for processed in expected_noncovered:
        assert china.at[processed, "coefficient_kgco2e_per_kg"] == 0
        assert china.at[processed, "upstream_booked_to"] != "none"


def test_postsolve_unit_identity_and_input_guards(built_ghg):
    _, factors, *_ = built_ghg
    sample = pd.DataFrame(
        {
            "scenario": ["SSP2", "SSP2"],
            "year": [2050, 2050],
            "economy_id": ["CHN", "CHN"],
            "commodity": ["RIC", "SUG"],
            "production_mt": [2.0, 5.0],
        }
    )
    result = postsolve(sample, factors)
    rice_factor = factors.loc[
        factors["economy_id"].eq("CHN") & factors["commodity"].eq("RIC"),
        "coefficient_kgco2e_per_kg",
    ].item()
    rice = result[result["commodity"].eq("RIC")].iloc[0]
    sugar = result[result["commodity"].eq("SUG")].iloc[0]
    assert rice["emissions_mtco2e"] == pytest.approx(2.0 * rice_factor)
    assert sugar["emissions_mtco2e"] == 0.0
    assert result["production_unit"].eq("Mt").all()
    assert result["emissions_unit"].eq("Mt CO2e").all()
    assert not result.isna().any().any()

    negative = sample.iloc[[0]].copy()
    negative["production_mt"] = -1.0
    with pytest.raises(ValueError, match="non-negative"):
        postsolve(negative, factors)
    unknown = sample.iloc[[0]].copy()
    unknown["economy_id"] = "UNKNOWN"
    with pytest.raises(ValueError, match="Missing GHG coefficient"):
        postsolve(unknown, factors)


def test_country_product_and_world_totals_are_additive(built_ghg):
    _, _, baseline, aggregates, _ = built_ghg
    rebuilt = summarize_postsolve(baseline, dimension_columns=["year"])
    pd.testing.assert_frame_equal(
        rebuilt.sort_values(list(rebuilt.columns)).reset_index(drop=True),
        aggregates.sort_values(list(aggregates.columns)).reset_index(drop=True),
        check_dtype=False,
    )
    detailed_total = baseline["emissions_mtco2e"].sum()
    country_total = aggregates.loc[
        aggregates["aggregation_level"].eq("country"), "emissions_mtco2e"
    ].sum()
    product_total = aggregates.loc[
        aggregates["aggregation_level"].eq("product"), "emissions_mtco2e"
    ].sum()
    world_total = aggregates.loc[
        aggregates["aggregation_level"].eq("world"), "emissions_mtco2e"
    ].item()
    assert country_total == pytest.approx(detailed_total)
    assert product_total == pytest.approx(detailed_total)
    assert world_total == pytest.approx(detailed_total)
    assert not aggregates.isna().any().any()


def test_fao_inventory_is_validation_only_and_controls_never_double_counted(
    built_ghg,
):
    report, _, _, _, validation = built_ghg
    assert report["status"] == "passed_postsolution_accounting_not_calibrated_to_fao_total"
    assert report["farm_gate_validation_not_forced"] is True
    assert report["faostat_total_plus_components_was_never_computed"] is True
    assert report["separate_controls_are_not_summed_or_added_to_postsolve"] is True
    assert report["energy_is_unallocated_validation_control"] is True
    assert report["nitrogen_module_enabled"] is False
    assert report["crop_component_diagnostics"][
        "forbidden_residue_component_codes_used"
    ] == []
    assert report["crop_component_diagnostics"]["selected_element_codes"] == [
        72257,
        72302,
        72307,
    ]
    assert validation["farm_gate_is_validation_only"].all()
    assert validation["controls_are_not_added_together"].all()
    assert not validation.isna().any().any()
    assert (validation["faostat_energy_unallocated_mtco2e"] >= 0).all()
    assert report["faostat_farm_gate_validation_mtco2e"] > 0
    assert report["baseline_modeled_attributed_mtco2e"] > 0


def test_all_declared_outputs_and_verified_source_lineage_exist(built_ghg):
    report, *_ = built_ghg
    expected_sources = {
        "fao_emissions_intensities",
        "fao_emissions_crops",
        "fao_emissions_livestock",
        "fao_emissions_agriculture_energy",
        "fao_emissions_totals",
        "fao_qcl",
        "un_m49",
    }
    assert set(report["verified_sources"]) == expected_sources
    for record in report["verified_sources"].values():
        assert record["source_id"]
        assert len(record["sha256"]) == 64
    for key, relative_path in CONFIG["outputs"].items():
        assert (ROOT / relative_path).is_file(), key
    on_disk_report = json.loads((ROOT / CONFIG["outputs"]["report"]).read_text())
    assert on_disk_report["factor_row_count"] == 5983
    assert on_disk_report["factor_table_has_na"] is False


def test_formal_ssp_run_consumes_production_only_and_has_complete_rectangle(
    formal_ssp_ghg,
):
    report, *_ = formal_ssp_ghg
    assert report["status"] == "passed_formal_ssp_ghg_postsolution"
    assert report["production_source_columns_consumed"] == [
        "scenario",
        "year",
        "economy_id",
        "commodity",
        "production_mt",
    ]
    assert report["forbidden_quantity_columns_consumed"] == []
    assert report["demand_or_trade_quantities_used"] is False
    assert report["input_gate"] == {
        "row_count": 837620,
        "scenario_count": 5,
        "year_count": 28,
        "model_account_count": 193,
        "commodity_count": 31,
        "scenario_year_block_count": 140,
        "duplicate_key_count": 0,
        "na_count": 0,
        "negative_production_count": 0,
        "minimum_production_mt": 0.0,
        "maximum_production_mt": report["input_gate"]["maximum_production_mt"],
        "status": "passed",
    }
    assert report["nitrogen_module_enabled"] is False
    assert report["coefficient_rule"] == "frozen_2023_production_side_coefficient"


def test_formal_ssp_common_2023_exactly_matches_rebuilt_baseline(formal_ssp_ghg):
    report, *_ = formal_ssp_ghg
    gate = report["common_2023_gate"]
    assert report["baseline_rebuilt_before_scenario_accounting"] is True
    assert gate["passed"] is True
    assert gate["max_production_spread_across_ssps_mt"] == 0.0
    assert gate["max_emissions_spread_across_ssps_mtco2e"] == 0.0
    assert gate["max_production_difference_from_rebuilt_baseline_mt"] <= gate[
        "absolute_tolerance"
    ]
    assert gate["max_emissions_difference_from_rebuilt_baseline_mtco2e"] <= gate[
        "absolute_tolerance"
    ]
    starts = report["world_emissions_2023_mtco2e"]
    assert set(starts) == {"SSP1", "SSP2", "SSP3", "SSP4", "SSP5"}
    assert max(starts.values()) - min(starts.values()) == 0.0
    assert next(iter(starts.values())) == pytest.approx(
        report["baseline_modeled_attributed_mtco2e"]
    )


def test_formal_country_product_world_summaries_are_complete_and_conserved(
    formal_ssp_ghg,
):
    report, country, product, world = formal_ssp_ghg
    assert len(country) == 5 * 28 * 193
    assert len(product) == 5 * 28 * 31
    assert len(world) == 5 * 28
    for frame in (country, product, world):
        assert not frame.isna().any().any()
        assert (frame["emissions_mtco2e"] >= 0).all()
        assert set(frame["scenario"]) == {"SSP1", "SSP2", "SSP3", "SSP4", "SSP5"}
        assert set(frame["year"]) == set(range(2023, 2051))
    assert not world.duplicated(["scenario", "year"]).any()
    assert world["aggregation_level"].eq("world").all()
    assert world["economy_id"].eq("ALL").all()
    assert world["commodity"].eq("ALL").all()

    for diagnostic in report["world_conservation_gate"].values():
        assert diagnostic["passed"] is True
        assert diagnostic["failing_scenario_year_count"] == 0
        assert diagnostic["max_absolute_difference_mtco2e"] <= 1.0e-9
    assert report["processed_noncovered_max_emissions_mtco2e"] == 0.0
    assert report["processed_upstream_double_counting_gate"] == "passed"
    assert report["output_na_counts"] == {
        "detail": 0,
        "country": 0,
        "product": 0,
        "world": 0,
    }


def test_formal_ssp_input_guard_rejects_demand_and_negative_production(built_ghg):
    _, factors, *_ = built_ghg
    scenario_config = CONFIG["scenario_postsolve"]
    row = pd.DataFrame(
        {
            "scenario": ["SSP1"],
            "year": [2023],
            "economy_id": ["CHN"],
            "commodity": ["RIC"],
            "production_mt": [1.0],
        }
    )
    with_demand = row.assign(demand_mt=99.0)
    with pytest.raises(ValueError, match="only the declared consumed columns"):
        validate_ssp_production_input(with_demand, factors, scenario_config)
    negative = row.copy()
    negative["production_mt"] = -1.0
    with pytest.raises(ValueError, match="finite and non-negative"):
        validate_ssp_production_input(negative, factors, scenario_config)


def test_formal_ssp_outputs_and_audit_are_materialized(formal_ssp_ghg):
    report, *_ = formal_ssp_ghg
    for key, relative_path in CONFIG["scenario_outputs"].items():
        path = ROOT / relative_path
        assert path.is_file(), key
        assert path.stat().st_size > 0
    disk = json.loads((ROOT / CONFIG["scenario_outputs"]["audit"]).read_text())
    assert disk["status"] == "passed_formal_ssp_ghg_postsolution"
    assert disk["scenario_source_sha256"] == report["scenario_source_sha256"]
    assert disk["factor_source_sha256"] == report["factor_source_sha256"]
    assert set(disk["world_emissions_2050_mtco2e"]) == {
        "SSP1",
        "SSP2",
        "SSP3",
        "SSP4",
        "SSP5",
    }
