from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from casm_world.parameters import (
    EXPECTED_ACCOUNTS,
    EXPECTED_COMMODITIES,
    EXPECTED_ROWS,
    build_parameters,
    load_parameter_config,
    read_frozen_peatsim_priors,
)
from casm_world.paths import load_source_catalog


ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("low", "central", "high")


@pytest.fixture(scope="module")
def parameter_config():
    return load_parameter_config(ROOT / "config/parameters.yaml")


@pytest.fixture(scope="module")
def built_parameters():
    return build_parameters(ROOT)


def test_config_locks_v2_complete_contract_and_response_envelope(parameter_config):
    assert parameter_config["schema_version"] == 2
    assert parameter_config["parameter_set"] == "CASM_WORLD_ELASTICITIES_V2"
    assert parameter_config["sources"]["frozen_prior_catalog_key"] == "peatsim_parameter_priors"
    assert parameter_config["sources"]["benchmark_path"] == "data/processed/benchmark_equilibrium_2023.csv"
    assert parameter_config["sources"]["unbalanced_use_path"] == "data/processed/benchmark_unbalanced_2023.csv"
    assert parameter_config["outputs"]["parameters"].endswith("casm_world_parameters_v2_2023.csv")
    assert parameter_config["coverage_gate"] == {
        "expected_model_accounts": EXPECTED_ACCOUNTS,
        "expected_commodities": EXPECTED_COMMODITIES,
        "expected_rows": EXPECTED_ROWS,
        "missing_to_zero": "forbidden",
        "require_unique_account_commodity": True,
    }
    assert parameter_config["parameter_response_envelope"]["sets"] == [
        "V2_LOW_RESPONSE", "V2_CENTRAL", "V2_HIGH_RESPONSE"
    ]
    assert parameter_config["parameter_response_envelope"]["crop_supply_quantiles"] == {
        "low": 0.25, "central": 0.50, "high": 0.75
    }


def test_frozen_workbook_reduces_aligned_crop_and_feed_semantics():
    catalog = load_source_catalog(ROOT / "config/data_sources.yaml")
    frozen = read_frozen_peatsim_priors(catalog.source("peatsim_parameter_priors").path)
    assert frozen.ela_supply["RIC"] == pytest.approx(0.12)
    expected_crop = {
        "RIC": (0.28587, 0.31871, 0.37220),
        "WHE": (0.35167, 0.406725, 0.4729125),
        "CRN": (0.3440275, 0.381185, 0.40525),
        "OCG": (0.39502, 0.40788, 0.5184425),
        "SBS": (0.36529, 0.45117, 0.53923),
        "NBS": (0.24622, 0.31139, 0.34959),
        "RBS": (0.21777, 0.29967, 0.35335),
        "CTN": (0.43712, 0.45636, 0.49425),
        "SUG": (0.31052, 0.45733, 0.56730),
    }
    for product, (low, central, high) in expected_crop.items():
        assert frozen.crop_total_supply_low[product] == pytest.approx(low)
        assert frozen.crop_total_supply[product] == pytest.approx(central)
        assert frozen.crop_total_supply_high[product] == pytest.approx(high)
    assert frozen.meat_supply["BFV"] == pytest.approx(0.8)
    assert frozen.dairy_supply["WDM"] == pytest.approx(1.30745)
    assert frozen.food_demand["RIC"] == pytest.approx(-0.071465, abs=1e-6)
    assert frozen.income["RIC"] == pytest.approx(0.3)
    for product, expected in {
        "WHE": -0.6655, "CRN": -0.3715, "OCG": -0.5995,
        "SBM": -0.227, "NBM": -0.572, "RBM": -0.4715,
    }.items():
        assert frozen.feed_demand[product] == pytest.approx(expected)


def test_final_table_is_complete_finite_and_central_aliases_are_exact(built_parameters):
    parameters, report = built_parameters
    assert len(parameters) == EXPECTED_ROWS
    assert parameters["economy_id"].nunique() == EXPECTED_ACCOUNTS
    assert parameters["commodity"].nunique() == EXPECTED_COMMODITIES
    assert not parameters.duplicated(["economy_id", "commodity"]).any()
    assert not parameters.isna().any().any()
    assert parameters["parameter_set"].eq("CASM_WORLD_ELASTICITIES_V2").all()
    assert parameters["parameter_status"].eq("final_casm_v2_central").all()
    for family in ("supply_price_elasticity", "demand_price_elasticity", "income_elasticity"):
        assert parameters[family].equals(parameters[f"{family}_central"])
        values = parameters[[f"{family}_{variant}" for variant in VARIANTS]]
        assert np.isfinite(values.to_numpy()).all()
    inactive = parameters["structural_final_demand_zero"]
    for variant in VARIANTS:
        assert parameters[f"supply_price_elasticity_{variant}"].gt(0).all()
        assert parameters.loc[~inactive, f"demand_price_elasticity_{variant}"].lt(0).all()
        assert parameters.loc[~inactive, f"income_elasticity_{variant}"].gt(0).all()
        assert parameters.loc[inactive, [
            f"demand_price_elasticity_{variant}", f"income_elasticity_{variant}"
        ]].eq(0.0).all().all()
    assert report["missing_parameter_count"] == 0
    assert report["nonfinite_parameter_count"] == 0
    assert report["zero_supply_parameter_count"] == 0
    assert report["zero_demand_parameter_count"] == int(inactive.sum())
    assert report["zero_income_parameter_count"] == int(inactive.sum())


def test_balanced_use_shares_sum_and_reproduce_account_composites(built_parameters):
    parameters, report = built_parameters
    shares = ["balanced_food_share", "feed_share", "other_use_share"]
    inactive = parameters["structural_final_demand_zero"]
    np.testing.assert_allclose(
        parameters.loc[~inactive, shares].sum(axis=1).to_numpy(),
        1.0, rtol=0.0, atol=5.0e-15,
    )
    assert parameters.loc[inactive, shares].eq(0.0).all().all()
    np.testing.assert_allclose(
        parameters.loc[~inactive, "balanced_food_share"],
        parameters.loc[~inactive, "food_demand_2023"] / parameters.loc[~inactive, "final_demand_2023"],
        rtol=0.0, atol=2.0e-15,
    )
    explicit_feed = parameters["commodity"].isin(["DDG", "SBM", "NBM", "RBM"]) & ~inactive
    assert parameters.loc[explicit_feed, "feed_share"].eq(1.0).all()
    assert parameters.loc[explicit_feed, "other_use_share"].eq(0.0).all()
    row = parameters.set_index(["economy_id", "commodity"]).loc[("CHN", "WHE")]
    for variant in VARIANTS:
        expected = -(
            row["balanced_food_share"] * row["food_price_prior_magnitude"]
            + row["feed_share"] * row[f"feed_price_prior_magnitude_{variant}"]
            + row["other_use_share"] * row["other_use_price_prior_magnitude"]
        )
        assert row[f"demand_prior_{variant}"] == pytest.approx(expected)
    expected_income = (
        row["balanced_food_share"] * row["food_income_prior"]
        + row["feed_share"] * row["feed_income_prior"]
        + row["other_use_share"] * row["other_use_income_prior"]
    )
    assert row["income_prior_central"] == pytest.approx(expected_income)
    assert report["maximum_active_use_share_sum_residual"] <= 5.0e-15


def test_unbalanced_feed_aggregation_is_193_account_and_unambiguous(built_parameters):
    parameters, _ = built_parameters
    raw = pd.read_csv(ROOT / "data/processed/benchmark_unbalanced_2023.csv")
    model_accounts = set(parameters["economy_id"])
    uses = raw[
        raw["economy_id"].isin(model_accounts)
        & raw["role"].eq("balance") & raw["unit"].eq("Mt")
        & raw["account"].isin(["feed", "seed", "loss", "other_use", "energy_consumption"])
    ]
    assert not uses.duplicated(["economy_id", "commodity", "account"]).any()
    expected_feed = uses.loc[
        uses["economy_id"].eq("CHN") & uses["commodity"].eq("WHE") & uses["account"].eq("feed"),
        "value",
    ].sum()
    observed = parameters.set_index(["economy_id", "commodity"]).at[
        ("CHN", "WHE"), "raw_feed_use_mt"
    ]
    assert observed == pytest.approx(expected_feed)


def test_crop_feed_and_declared_author_prior_envelope(built_parameters):
    parameters, _ = built_parameters
    priors = parameters.drop_duplicates("commodity").set_index("commodity")
    assert priors.at["WHE", "supply_prior_central"] == pytest.approx(0.406725)
    assert priors.at["SUG", "supply_prior_central"] == pytest.approx(0.45733)
    for sugar_input in ("SCA", "SBE"):
        for variant in VARIANTS:
            assert priors.at[sugar_input, f"supply_prior_{variant}"] == pytest.approx(
                priors.at["SUG", f"supply_prior_{variant}"]
            )
    assert priors.loc["OTO", ["supply_prior_low", "supply_prior_central", "supply_prior_high"]].tolist() == pytest.approx([0.30, 0.50, 0.80])
    assert priors.loc["ETH", ["supply_prior_low", "supply_prior_central", "supply_prior_high"]].tolist() == pytest.approx([0.1875, 0.25, 0.3125])
    for meal, central in {"SBM": 0.227, "NBM": 0.572, "RBM": 0.4715}.items():
        assert priors.at[meal, "feed_price_prior_magnitude_central"] == pytest.approx(central)
        assert priors.at[meal, "feed_price_prior_magnitude_low"] == pytest.approx(0.75 * central)
        assert priors.at[meal, "feed_price_prior_magnitude_high"] == pytest.approx(1.25 * central)
    meal_median = np.median([0.227, 0.572, 0.4715])
    assert priors.at["DDG", "feed_price_prior_magnitude_central"] == pytest.approx(meal_median)
    assert priors.at["RIC", "feed_price_prior_magnitude_central"] == pytest.approx(0.10)
    assert priors.at["RIC", "feed_price_prior_route"] == "explicit_author_default"


def test_final_response_envelope_is_ordered_and_crop_bounds_apply(built_parameters):
    parameters, _ = built_parameters
    assert parameters["supply_price_elasticity_low"].le(parameters["supply_price_elasticity_central"] + 1e-15).all()
    assert parameters["supply_price_elasticity_central"].le(parameters["supply_price_elasticity_high"] + 1e-15).all()
    assert parameters["demand_price_elasticity_low"].ge(parameters["demand_price_elasticity_central"] - 1e-15).all()
    assert parameters["demand_price_elasticity_central"].ge(parameters["demand_price_elasticity_high"] - 1e-15).all()
    assert parameters["income_elasticity_low"].equals(parameters["income_elasticity_central"])
    assert parameters["income_elasticity_central"].equals(parameters["income_elasticity_high"])
    crop_classes = {"crop", "crop_aggregate", "oilseed", "fibre", "processed_crop", "processing_crop"}
    crop = parameters[parameters["commodity_class"].isin(crop_classes)]
    for variant in VARIANTS:
        assert crop[f"supply_price_elasticity_{variant}"].between(0.15, 0.65).all()


def test_reporting_income_groups_adjust_parameters_and_ncl_is_explicit(built_parameters):
    parameters, report = built_parameters
    account_groups = parameters[["economy_id", "income_group"]].drop_duplicates()
    assert account_groups["income_group"].value_counts().to_dict() == {
        "HIC": 64, "UMC": 52, "LMC": 50, "LIC": 26, "NCL": 1,
    }
    assert report["ncl_fallback_accounts"] == ["VEN"]
    assert report["ncl_fallback_parameter_rows"] == EXPECTED_COMMODITIES
    assert parameters.loc[parameters["economy_id"].eq("VEN"), "income_adjustment_status"].eq("explicit_ncl_fallback_factor_applied").all()
    rice = parameters[parameters["commodity"].eq("RIC") & ~parameters["structural_final_demand_zero"]]
    by_group = rice.groupby("income_group").first()
    assert (
        by_group.at["LIC", "income_elasticity"]
        > by_group.at["LMC", "income_elasticity"]
        > by_group.at["UMC", "income_elasticity"]
        > by_group.at["HIC", "income_elasticity"]
    )


def test_processing_chain_supply_routes_remain_explicit(built_parameters):
    parameters, _ = built_parameters
    priors = parameters.drop_duplicates("commodity").set_index("commodity")
    for input_product, output_products in {
        "SBS": ("SBO", "SBM"), "NBS": ("NBO", "NBM"), "RBS": ("RBO", "RBM"),
    }.items():
        for output_product in output_products:
            for variant in VARIANTS:
                assert priors.at[output_product, f"supply_prior_{variant}"] == pytest.approx(
                    1.25 * priors.at[input_product, f"supply_prior_{variant}"]
                )
            assert priors.at[output_product, "supply_prior_route"].startswith(f"chain_parent:{input_product}")
    for variant in VARIANTS:
        assert priors.at["DDG", f"supply_prior_{variant}"] == pytest.approx(
            priors.at["ETH", f"supply_prior_{variant}"]
        )
    assert all(
        "geometric_blend" in priors.at[product, "supply_prior_route"]
        for product in ("BUT", "CHE", "NDM", "FMK", "WDM", "ODA")
    )


def test_provenance_status_ranges_and_response_hashes_are_complete(built_parameters):
    parameters, report = built_parameters
    for column in [
        "parameter_status", "provenance_status", "income_adjustment_status",
        "transmission_provenance_status", "bound_adjustment_status",
        "bound_adjustment_status_low", "bound_adjustment_status_central",
        "bound_adjustment_status_high", "activity_status", "use_share_status",
    ]:
        assert parameters[column].astype(str).str.strip().ne("").all()
    assert report["status"] == "passed"
    assert report["parameter_row_count"] == EXPECTED_ROWS
    assert report["observed_ranges"]["supply_price_elasticity"]["min"] > 0
    assert report["observed_ranges"]["demand_price_elasticity"]["max"] == 0
    hashes = report["response_set_sha256"]
    assert set(hashes) == {"V2_LOW_RESPONSE", "V2_CENTRAL", "V2_HIGH_RESPONSE"}
    assert len(set(hashes.values())) == 3
    assert all(len(value) == 64 for value in hashes.values())
    assert report["missing_to_zero"].startswith("forbidden_and_not_used")


def test_incomplete_income_interface_is_rejected_instead_of_zero_filled():
    benchmark = pd.read_csv(ROOT / "data/processed/benchmark_equilibrium_2023.csv", usecols=["economy_id"])
    accounts = sorted(benchmark["economy_id"].unique())
    incomplete = pd.DataFrame({"economy_id": accounts[:-1], "income_group": "NCL"})
    with pytest.raises(ValueError, match="exactly the 193 model accounts"):
        build_parameters(ROOT, income_interface=incomplete)
