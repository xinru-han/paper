from pathlib import Path

import pandas as pd
import pytest
import yaml

from casm_world.analysis import (
    aggregate_solved_results,
    build_change_summary,
    build_developing_membership,
    build_source_allocation_weights,
    build_un_special_membership,
    load_analysis_config,
)
from casm_world.geography import (
    EXPECTED_TERRITORIES,
    load_territory_config,
)
from casm_world.paths import load_source_catalog
from casm_world.reporting import (
    SOURCE_GROUP_SYSTEMS,
    build_model_account_membership,
    build_source_geography,
    build_source_geography_membership,
    load_reporting_config,
    load_world_bank_income_groups,
)


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = load_analysis_config(ROOT / "config/analysis.yaml")
REPORTING = load_reporting_config(ROOT / "config/reporting_groups.yaml")
TERRITORY = load_territory_config(ROOT / "config/territory_aggregation.yaml")
CATALOG = load_source_catalog(ROOT / "config/data_sources.yaml")
M49_PATH = CATALOG.source("un_m49").path
WB_INCOME_PATH = CATALOG.source("world_bank_income_classification").path


@pytest.fixture(scope="module")
def source_geography():
    return build_source_geography(M49_PATH, REPORTING, TERRITORY)


@pytest.fixture(scope="module")
def special_membership(source_geography):
    return build_un_special_membership(M49_PATH, source_geography, ANALYSIS)


@pytest.fixture(scope="module")
def model_accounts():
    benchmark = pd.read_csv(ROOT / "data/processed/benchmark_equilibrium_2023.csv")
    return sorted(benchmark["economy_id"].unique())


@pytest.fixture(scope="module")
def model_membership(model_accounts):
    income = load_world_bank_income_groups(WB_INCOME_PATH, REPORTING)
    base = build_model_account_membership(
        model_accounts,
        REPORTING,
        income_groups=income,
        territory_config=TERRITORY,
    )
    developing = build_developing_membership(base, ANALYSIS)
    return pd.concat([base, developing], ignore_index=True)


@pytest.fixture(scope="module")
def allocation(source_geography, model_accounts):
    benchmark = pd.read_csv(ROOT / "data/processed/benchmark_equilibrium_2023.csv")
    observations = pd.read_csv(
        ROOT / "data/interim/benchmark_source_observations_2023.csv"
    )
    commodity = yaml.safe_load(
        (ROOT / "config/commodities.yaml").read_text(encoding="utf-8")
    )
    balancing = yaml.safe_load(
        (ROOT / "config/balancing.yaml").read_text(encoding="utf-8")
    )
    return build_source_allocation_weights(
        model_accounts,
        observations,
        benchmark,
        source_geography,
        TERRITORY,
        list(commodity["commodities"]),
        ddg_ratio=balancing["processing"]["ddg_output_mass_per_mass_ethanol"],
        food_commodities=balancing["final_demand_components"]["food_commodities"],
    )


def test_analysis_configuration_freezes_requested_classifications():
    assert ANALYSIS["benchmark_year"] == 2023
    assert ANALYSIS["end_year"] == 2050
    assert ANALYSIS["developing_economies"]["included_wb_income_codes"] == [
        "LIC",
        "LMC",
        "UMC",
    ]
    groups = ANALYSIS["un_special_groups"]["groups"]
    assert {code: groups[code]["expected_source_count"] for code in groups} == {
        "LDC": 44,
        "LLDC": 32,
        "SIDS": 53,
        "PACIFIC_ISLANDS": 23,
    }


def test_un_special_membership_matches_frozen_m49_flags(special_membership):
    counts = special_membership.groupby("group_code")["source_economy_id"].nunique()
    assert counts.to_dict() == {
        "LDC": 44,
        "LLDC": 32,
        "PACIFIC_ISLANDS": 23,
        "SIDS": 53,
    }
    memberships = special_membership.groupby("group_code")["source_economy_id"].agg(set)
    assert {"AFG", "BGD", "YEM"} <= memberships["LDC"]
    assert {"AFG", "BTN", "MNG"} <= memberships["LLDC"]
    assert {"FJI", "KIR", "HTI"} <= memberships["SIDS"]
    assert {"FJI", "GUM", "WLF"} <= memberships["PACIFIC_ISLANDS"]
    assert not {"AUS", "NZL"} & memberships["PACIFIC_ISLANDS"]
    assert not special_membership["group_code"].eq("WORLD").any()


def test_developing_economies_are_exactly_wb_lic_lmc_umc(model_membership):
    income = model_membership[model_membership["group_system"].eq("WB_INCOME_FY25")]
    expected = set(
        income.loc[income["group_code"].isin(["LIC", "LMC", "UMC"]), "model_account_id"]
    )
    developing = set(
        model_membership.loc[
            model_membership["group_system"].eq("WB_DEVELOPMENT_STATUS"),
            "model_account_id",
        ]
    )
    assert developing == expected
    assert "CHN" in developing
    assert "USA" not in developing
    assert "OTHER_EASTERN_ASIA" not in developing


def test_fixed_source_weights_reconstruct_193_accounts_without_territory_accounts(
    allocation, model_accounts
):
    weights, report = allocation
    assert len(model_accounts) == 193
    assert weights["accounting_target"].nunique() == 193
    assert weights["source_economy_id"].nunique() == 217
    assert set(EXPECTED_TERRITORIES) <= set(weights["source_economy_id"])
    assert not set(EXPECTED_TERRITORIES) & set(weights["accounting_target"])
    assert report["territory_source_count_in_bridge"] == 25
    assert report["maximum_source_anchor_reconstruction_error_mt"] < 1.0e-12
    assert report["maximum_weight_sum_error"] < 1.0e-12

    sums = weights.groupby(["accounting_target", "commodity"])[
        [
            "supply_weight",
            "food_demand_weight",
            "other_final_demand_weight",
            "final_demand_weight",
            "processing_weight",
        ]
    ].sum()
    assert (sums - 1.0).abs().max().max() < 1.0e-12
    taiwan = weights[weights["source_economy_id"].eq("TWN")]
    assert set(taiwan["accounting_target"]) == {"OTHER_EASTERN_ASIA"}
    assert not taiwan["accounting_target"].eq("CHN").any()
    faroe = weights[weights["source_economy_id"].eq("FRO")]
    assert set(faroe["accounting_target"]) == {"DNK"}
    assert faroe[["supply_weight", "final_demand_weight"]].to_numpy().max() > 0.0


def test_aggregation_preserves_world_and_original_source_geography(
    source_geography, special_membership, model_membership, allocation
):
    weights, _ = allocation
    source_membership = pd.concat(
        [build_source_geography_membership(source_geography), special_membership],
        ignore_index=True,
    )
    accounts = ["CHN", "DNK", "OTHER_EASTERN_ASIA"]
    solved = pd.DataFrame(
        {
            "scenario": "SSP2",
            "year": 2030,
            "economy_id": accounts,
            "commodity": "RIC",
            "world_price_index_2023": 1.2,
            "primary_supply_mt": [10.0, 3.0, 2.0],
            "processing_supply_mt": [1.0, 0.5, 0.2],
            "production_mt": [11.0, 3.5, 2.2],
            "food_demand_mt": [8.0, 2.0, 1.5],
            "other_final_demand_mt": [1.0, 0.4, 0.2],
            "final_demand_mt": [9.0, 2.4, 1.7],
            "processing_demand_mt": [2.0, 1.1, 0.5],
            "demand_mt": [11.0, 3.5, 2.2],
            "net_import_mt": [0.0, 0.0, 0.0],
        }
    )
    result = aggregate_solved_results(
        solved,
        model_membership,
        source_membership,
        weights,
        ANALYSIS,
    )
    world = result[
        result["group_system"].eq("GLOBAL") & result["group_code"].eq("WORLD")
    ].iloc[0]
    assert world["production_mt"] == pytest.approx(16.7)
    assert world["food_demand_mt"] == pytest.approx(11.5)
    assert world["world_price_index_2023"] == pytest.approx(1.2)

    for system in SOURCE_GROUP_SYSTEMS:
        block = result[result["group_system"].eq(system)]
        assert block["production_mt"].sum() == pytest.approx(world["production_mt"])
        assert block["demand_mt"].sum() == pytest.approx(world["demand_mt"])

    eastern_asia = result[
        result["group_system"].eq("UN_SUBREGION")
        & result["group_code"].eq("030")
    ]
    # Both mainland China and the OTHER_EASTERN_ASIA/TWN source contribution
    # stay in Eastern Asia; TWN is never reassigned to the CHN focus account.
    assert eastern_asia["production_mt"].item() == pytest.approx(13.2)
    china = result[
        result["group_system"].eq("FOCUS")
        & result["group_code"].eq("CHINA_MAINLAND")
    ]
    assert china["production_mt"].item() == pytest.approx(11.0)


def test_change_summary_reports_absolute_and_percent_changes():
    grouped = pd.DataFrame(
        {
            "scenario": ["SSP1", "SSP1"],
            "year": [2023, 2050],
            "group_system": ["GLOBAL", "GLOBAL"],
            "group_code": ["WORLD", "WORLD"],
            "group_name": ["World", "World"],
            "commodity": ["RIC", "RIC"],
            "world_price_index_2023": [1.0, 1.25],
            "production_mt": [100.0, 120.0],
        }
    )
    summary = build_change_summary(grouped, ANALYSIS).iloc[0]
    assert summary["production_mt_absolute_change"] == pytest.approx(20.0)
    assert summary["production_mt_percent_change"] == pytest.approx(20.0)
    assert summary["world_price_index_2023_percent_change"] == pytest.approx(25.0)
