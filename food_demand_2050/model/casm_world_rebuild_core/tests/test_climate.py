from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from casm_world.climate import (
    DIRECT_IPCC_SCENARIOS,
    build_climate_yield_paths,
    build_temperature_paths,
    load_climate_config,
    load_model_universe,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = load_climate_config(ROOT / "config/climate.yaml")


@pytest.fixture(scope="module")
def universe():
    return load_model_universe(ROOT, CONFIG)


@pytest.fixture(scope="module")
def full_paths(universe):
    accounts, commodities = universe
    return build_climate_yield_paths(accounts, commodities, CONFIG)


def test_source_lineage_separates_literature_mapping_and_author_assumptions():
    literature = CONFIG["literature_parameters"]
    assert "10.1073/pnas.1701762114" in literature["zhao_2017_crop_temperature"]["doi"]
    assert "IPCC_AR6_WGI_SPM_final.pdf" in literature["ipcc_ar6_wgi_spm_table_1"][
        "report_url"
    ]
    assert "10.5194/gmd-9-3461-2016" in literature["scenario_mip_ssp4_60"]["doi"]
    assert CONFIG["ssp_forcing_mapping"]["SSP4"]["temperature_node_source"] == (
        "author_forcing_interpolation"
    )
    assert not CONFIG["author_assumptions"]["ssp4_temperature_interpolation"][
        "publish_as_ipcc_direct"
    ]
    assert {
        scenario
        for scenario, record in CONFIG["ssp_forcing_mapping"].items()
        if record["temperature_node_source"] == "ipcc_ar6_direct"
    } == DIRECT_IPCC_SCENARIOS


def test_temperature_paths_are_complete_anchored_continuous_and_directional():
    temperature = build_temperature_paths(CONFIG)
    assert len(temperature) == 5 * 28
    assert not temperature.isna().any().any()
    assert not temperature.duplicated(["scenario", "year"]).any()
    assert set(temperature["year"]) == set(range(2023, 2051))
    anchor = temperature[temperature["year"].eq(2023)]
    assert anchor["global_temperature_anomaly_c"].eq(1.45).all()
    assert anchor["incremental_warming_from_2023_c"].eq(0.0).all()
    for _, group in temperature.groupby("scenario", observed=True):
        group = group.sort_values("year")
        assert (group["global_temperature_anomaly_c"].diff().dropna() >= 0).all()
        assert group["year"].diff().dropna().eq(1).all()
        # Piecewise annual interpolation cannot introduce discontinuous jumps.
        assert group["global_temperature_anomaly_c"].diff().dropna().max() < 0.05
    endpoint = temperature[temperature["year"].eq(2050)].set_index("scenario")
    assert endpoint["global_temperature_anomaly_c"].to_dict() == pytest.approx(
        {"SSP1": 1.7, "SSP2": 2.0, "SSP3": 2.1, "SSP4": 2.06, "SSP5": 2.4}
    )


def test_exact_193_by_31_universe_and_full_output_coverage(universe, full_paths):
    accounts, commodities = universe
    paths, report = full_paths
    assert len(accounts) == 193
    assert len(commodities) == 31
    assert len(paths) == 5 * 193 * 28 * 31
    assert report["expected_row_count"] == report["actual_row_count"] == len(paths)
    assert not paths.duplicated(["scenario", "economy_id", "year", "commodity"]).any()
    assert paths["economy_id"].nunique() == 193
    assert paths["commodity"].nunique() == 31
    assert paths["scenario"].nunique() == 5
    assert paths["year"].nunique() == 28
    assert not paths.isna().any().any()
    assert np.isfinite(paths.select_dtypes(include=[np.number]).to_numpy()).all()


def test_every_2023_index_is_exactly_one(full_paths):
    paths, report = full_paths
    anchor = paths.loc[paths["year"].eq(2023), "climate_yield_index_2023"]
    assert len(anchor) == 5 * 193 * 31
    assert np.array_equal(anchor.to_numpy(), np.ones(len(anchor)))
    assert report["anchor_violation_count"] == 0


def test_only_four_zhao_crops_receive_direct_shocks(full_paths):
    paths, report = full_paths
    assert set(paths.loc[paths["direct_climate_shock"], "commodity"].astype(str)) == {
        "RIC",
        "WHE",
        "CRN",
        "SBS",
    }
    assert report["direct_shock_commodities"] == ["CRN", "RIC", "SBS", "WHE"]
    direct = paths[paths["direct_climate_shock"]]
    assert (direct["yield_sensitivity_fraction_per_c"] < 0).all()
    assert direct["yield_parameter_source"].astype(str).eq("Zhao_et_al_2017_PNAS").all()


def test_processing_outputs_are_not_double_shocked(full_paths):
    paths, report = full_paths
    products = set(report["processing_no_double_shock_commodities"])
    processing = paths[paths["commodity"].astype(str).isin(products)]
    assert len(products) == 18
    assert not processing["direct_climate_shock"].any()
    assert processing["yield_sensitivity_fraction_per_c"].eq(0.0).all()
    assert processing["climate_yield_index_2023"].eq(1.0).all()
    assert processing["commodity_scope_status"].astype(str).eq(
        "processing_output_no_double_shock"
    ).all()


def test_unparameterized_primary_products_are_explicit_not_silent_zero(full_paths):
    paths, report = full_paths
    products = set(report["unparameterized_primary_commodities"])
    rows = paths[paths["commodity"].astype(str).isin(products)]
    assert len(products) == 9
    assert rows["yield_sensitivity_fraction_per_c"].eq(0.0).all()
    assert rows["commodity_scope_status"].astype(str).eq(
        "explicit_no_matching_authoritative_parameter"
    ).all()
    assert rows["yield_parameter_source"].astype(str).eq(
        "NONE_EXPLICIT_UNPARAMETERIZED_PRIMARY"
    ).all()


def test_warming_damage_direction_order_and_hard_bounds(full_paths):
    paths, _ = full_paths
    direct_2050 = paths[
        paths["year"].eq(2050)
        & paths["commodity"].astype(str).eq("CRN")
        & paths["economy_id"].astype(str).eq("CHN")
    ].set_index(paths.loc[
        paths["year"].eq(2050)
        & paths["commodity"].astype(str).eq("CRN")
        & paths["economy_id"].astype(str).eq("CHN"),
        "scenario",
    ].astype(str))
    index = direct_2050["climate_yield_index_2023"]
    assert index["SSP5"] < index["SSP3"] < index["SSP4"] < index["SSP2"] < index["SSP1"] < 1.0
    assert paths["climate_yield_index_2023"].between(0.5, 1.0, inclusive="both").all()


def test_global_regional_fallback_is_complete_and_explicit(full_paths):
    paths, report = full_paths
    assert report["regional_parameterization"] == (
        "global_coefficient_no_regional_differentiation"
    )
    assert report["regional_detail_fallback_account_count"] == 193
    assert len(report["regional_detail_fallback_accounts"]) == 193
    assert paths["regional_exposure_factor"].eq(1.0).all()
    assert paths["regional_parameter_status"].astype(str).eq(
        "explicit_global_parameter_no_regional_differentiation"
    ).all()


def test_missing_or_extra_commodity_cannot_be_silently_accepted(universe):
    accounts, commodities = universe
    with pytest.raises(ValueError, match="configured 31-product scope"):
        build_climate_yield_paths(accounts[:2], commodities[:-1], CONFIG)
