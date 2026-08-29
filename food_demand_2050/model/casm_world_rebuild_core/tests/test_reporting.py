from pathlib import Path

import pandas as pd
import pytest
import yaml

from casm_world.geography import EXPECTED_TERRITORIES, load_territory_config
from casm_world.reporting import (
    ACCOUNT_GROUP_SYSTEMS,
    SOURCE_GROUP_SYSTEMS,
    account_coverage_report,
    aggregate_model_account_values,
    aggregate_source_geography_values,
    build_model_account_membership,
    build_source_geography,
    build_source_geography_membership,
    load_reporting_config,
    load_world_bank_income_groups,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTING_CONFIG = load_reporting_config(ROOT / "config/reporting_groups.yaml")
TERRITORY_CONFIG = load_territory_config(ROOT / "config/territory_aggregation.yaml")
DATA_CONFIG = yaml.safe_load((ROOT / "config/data_sources.yaml").read_text())
RAW_ROOT = Path(DATA_CONFIG["contract"]["trusted_raw_root"])
M49_PATH = RAW_ROOT / DATA_CONFIG["sources"]["un_m49"]["relative_path"]
WB_INCOME_PATH = (
    RAW_ROOT
    / DATA_CONFIG["sources"]["world_bank_income_classification"]["relative_path"]
)


@pytest.fixture(scope="module")
def source_geography():
    return build_source_geography(M49_PATH, REPORTING_CONFIG, TERRITORY_CONFIG)


@pytest.fixture(scope="module")
def source_membership(source_geography):
    return build_source_geography_membership(source_geography)


@pytest.fixture(scope="module")
def income_groups():
    return load_world_bank_income_groups(WB_INCOME_PATH, REPORTING_CONFIG)


def test_raw_m49_and_territory_mapping_create_250_source_geographies(source_geography):
    geography = source_geography.set_index("source_economy_id")
    assert len(geography) == 250
    assert geography.index.is_unique
    assert set(geography.index[geography["territory_aggregation_source"]]) == EXPECTED_TERRITORIES
    assert not geography.loc[list(EXPECTED_TERRITORIES), "source_model_entity"].astype(bool).any()

    # Accounting destination and geographic reporting destination are separate.
    assert geography.loc["FRA", ["accounting_target", "region_code", "subregion_code", "reporting_area_code"]].tolist() == [
        "FRA",
        "150",
        "155",
        "155",
    ]
    assert geography.loc["GUF", ["accounting_target", "region_code", "subregion_code", "reporting_area_code"]].tolist() == [
        "FRA",
        "019",
        "419",
        "005",
    ]
    assert geography.loc["REU", ["accounting_target", "region_code", "subregion_code", "reporting_area_code"]].tolist() == [
        "FRA",
        "002",
        "202",
        "014",
    ]
    assert geography.loc["ESH", ["accounting_target", "region_code", "reporting_area_code"]].tolist() == [
        "MAR",
        "002",
        "015",
    ]
    assert geography.loc["TWN", ["accounting_target", "region_code", "subregion_code"]].tolist() == [
        "OTHER_EASTERN_ASIA",
        "142",
        "030",
    ]


def test_source_geography_membership_is_exclusive_and_never_builds_world(
    source_membership,
):
    assert set(source_membership["group_system"]) == SOURCE_GROUP_SYSTEMS
    assert len(source_membership) == 250 * 3
    assert not source_membership["group_code"].eq("WORLD").any()
    assert not source_membership["group_system"].isin(ACCOUNT_GROUP_SYSTEMS).any()
    for system in SOURCE_GROUP_SYSTEMS:
        block = source_membership[source_membership["group_system"].eq(system)]
        assert len(block) == 250
        assert block["source_economy_id"].is_unique

    requested_subregions = {
        "030": "Eastern Asia",
        "035": "South-eastern Asia",
        "034": "Southern Asia",
        "145": "Western Asia",
        "015": "Northern Africa",
    }
    un_subregions = source_membership[
        source_membership["group_system"].eq("UN_SUBREGION")
    ][["group_code", "group_name"]].drop_duplicates()
    actual_subregions = un_subregions.set_index("group_code")["group_name"].to_dict()
    assert requested_subregions.items() <= actual_subregions.items()


def test_un_regions_keep_overseas_contributions_in_original_m49_geography(
    source_membership,
):
    values = pd.DataFrame(
        {
            "economy_id": ["FRA", "GUF", "REU", "TWN", "CHN"],
            "year": [2023] * 5,
            "commodity": ["RIC"] * 5,
            "value": [100.0, 2.0, 3.0, 4.0, 10.0],
        }
    )
    result = aggregate_source_geography_values(
        values,
        source_membership,
        value_columns=["value"],
        dimension_columns=["year", "commodity"],
    )

    regions = result[result["group_system"].eq("UN_REGION")].set_index("group_name")
    assert regions.at["Europe", "value"] == pytest.approx(100.0)
    assert regions.at["Americas", "value"] == pytest.approx(2.0)
    assert regions.at["Africa", "value"] == pytest.approx(3.0)
    assert regions.at["Asia", "value"] == pytest.approx(14.0)
    assert regions["value"].sum() == pytest.approx(values["value"].sum())

    areas = result[result["group_system"].eq("UN_REPORTING_AREA")].set_index(
        "group_name"
    )
    assert areas.at["Western Europe", "value"] == pytest.approx(100.0)
    assert areas.at["South America", "value"] == pytest.approx(2.0)
    assert areas.at["Eastern Africa", "value"] == pytest.approx(3.0)
    assert areas.at["Eastern Asia", "value"] == pytest.approx(14.0)
    assert areas["value"].sum() == pytest.approx(values["value"].sum())


def test_world_bank_fy25_interface_matches_2023_and_supports_synthetic_account(
    income_groups,
):
    income = income_groups.set_index("economy_id")
    assert income["classification_period"].nunique() == 1
    assert income["classification_period"].iloc[0] == "FY25"
    assert income["represented_calendar_year"].nunique() == 1
    assert income["represented_calendar_year"].iloc[0] == 2023
    assert income.at["TWN", "group_code"] == "HIC"
    assert income.at["XKX", "group_code"] == "UMC"


def test_actual_193_account_benchmark_has_exact_world_and_income_coverage(
    income_groups,
):
    benchmark = pd.read_csv(
        ROOT / "data/processed/benchmark_equilibrium_interim_2023.csv"
    )
    accounts = sorted(benchmark["economy_id"].unique())
    assert len(accounts) == 193

    membership = build_model_account_membership(
        accounts,
        REPORTING_CONFIG,
        income_groups=income_groups,
        territory_config=TERRITORY_CONFIG,
    )
    assert set(membership["group_system"]) == ACCOUNT_GROUP_SYSTEMS
    assert not membership["group_system"].isin(SOURCE_GROUP_SYSTEMS).any()

    world = membership[membership["group_system"].eq("GLOBAL")]
    assert len(world) == 193
    assert world["model_account_id"].is_unique
    assert set(world["model_account_id"]) == set(accounts)
    assert not (set(accounts) & EXPECTED_TERRITORIES)

    eu27 = membership[
        membership["group_system"].eq("ECONOMIC")
        & membership["group_code"].eq("EU27")
    ]
    assert len(eu27) == 27
    assert membership[
        membership["group_system"].eq("FOCUS")
        & membership["group_code"].eq("CHINA_MAINLAND")
    ]["model_account_id"].tolist() == ["CHN"]
    assert membership[
        membership["group_system"].eq("FOCUS")
        & membership["group_code"].eq("USA")
    ]["model_account_id"].tolist() == ["USA"]

    wb = membership[membership["group_system"].eq("WB_INCOME_FY25")]
    assert len(wb) == 193
    assert wb["model_account_id"].is_unique
    assert wb.loc[
        wb["model_account_id"].eq("OTHER_EASTERN_ASIA"), "group_code"
    ].item() == "HIC"

    report = account_coverage_report(
        accounts,
        membership,
        REPORTING_CONFIG,
        territory_config=TERRITORY_CONFIG,
    )
    assert report == {
        "model_account_count": 193,
        "expected_model_account_count": 193,
        "world_membership_rows": 193,
        "world_unique_accounts": 193,
        "world_missing_accounts": [],
        "world_duplicate_accounts": [],
        "wb_income_membership_rows": 193,
        "wb_income_missing_accounts": [],
        "wb_income_duplicate_accounts": [],
        "territory_sources_surviving_as_accounts": [],
        "status": "passed",
    }


def test_world_aggregation_counts_each_actual_model_account_once(income_groups):
    benchmark = pd.read_csv(
        ROOT / "data/processed/benchmark_equilibrium_interim_2023.csv"
    )
    accounts = sorted(benchmark["economy_id"].unique())
    membership = build_model_account_membership(
        accounts,
        REPORTING_CONFIG,
        income_groups=income_groups,
        territory_config=TERRITORY_CONFIG,
    )
    values = pd.DataFrame(
        {"economy_id": accounts, "year": 2023, "value": 1.0}
    )
    result = aggregate_model_account_values(
        values,
        membership,
        value_columns=["value"],
        dimension_columns=["year"],
    )
    world = result[
        result["group_system"].eq("GLOBAL") & result["group_code"].eq("WORLD")
    ]
    assert world["value"].item() == pytest.approx(193.0)

    wb = result[result["group_system"].eq("WB_INCOME_FY25")]
    assert wb["value"].sum() == pytest.approx(193.0)
    assert result.loc[
        result["group_system"].eq("ECONOMIC")
        & result["group_code"].eq("EU27"),
        "value",
    ].item() == pytest.approx(27.0)


def test_duplicate_world_membership_is_visible_in_coverage_report(income_groups):
    accounts = ["CHN", "USA"]
    membership = build_model_account_membership(
        accounts,
        REPORTING_CONFIG,
        income_groups=income_groups,
        territory_config=TERRITORY_CONFIG,
    )
    duplicate = pd.concat(
        [membership, membership[membership["group_system"].eq("GLOBAL")].iloc[[0]]],
        ignore_index=True,
    )
    report = account_coverage_report(
        accounts,
        duplicate,
        REPORTING_CONFIG,
        territory_config=TERRITORY_CONFIG,
    )
    assert report["status"] == "blocked"
    assert len(report["world_duplicate_accounts"]) == 1
