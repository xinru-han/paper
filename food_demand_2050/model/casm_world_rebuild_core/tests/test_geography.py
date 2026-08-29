from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from casm_world.geography import (  # noqa: E402
    EXPECTED_TERRITORIES,
    aggregate_additive_values,
    attach_territory_mapping,
    load_territory_config,
    territory_crosswalk,
    validate_parent_scope_gdp,
)


CONFIG_PATH = ROOT / "config/territory_aggregation.yaml"


@pytest.fixture(scope="module")
def config():
    return load_territory_config(CONFIG_PATH)


def test_crosswalk_is_exactly_25_unique_non_model_sources(config):
    crosswalk = territory_crosswalk(config)

    assert len(crosswalk) == 25
    assert crosswalk["source_economy_id"].is_unique
    assert set(crosswalk["source_economy_id"]) == EXPECTED_TERRITORIES
    assert not crosswalk["model_entity"].any()
    assert crosswalk["retain_classification_metadata"].all()
    assert crosswalk["accounting_target"].notna().all()
    assert crosswalk["reporting_region_target"].notna().all()
    assert crosswalk["reporting_subregion_target"].notna().all()


def test_required_accounting_targets_and_gdp_scopes_are_locked(config):
    crosswalk = territory_crosswalk(config).set_index("source_economy_id")

    expected_targets = {
        "ASM": "USA",
        "BES": "NLD",
        "BLM": "FRA",
        "ESH": "MAR",
        "FLK": "GBR",
        "FRO": "DNK",
        "GGY": "GBR",
        "GIB": "GBR",
        "GLP": "FRA",
        "GUF": "FRA",
        "GUM": "USA",
        "IMN": "GBR",
        "JEY": "GBR",
        "MAF": "FRA",
        "MNP": "USA",
        "MTQ": "FRA",
        "MYT": "FRA",
        "NIU": "NZL",
        "REU": "FRA",
        "SHN": "GBR",
        "SPM": "FRA",
        "TKL": "NZL",
        "TWN": "OTHER_EASTERN_ASIA",
        "VIR": "USA",
        "WLF": "FRA",
    }
    assert crosswalk["accounting_target"].to_dict() == expected_targets

    assert crosswalk.at["TWN", "accounting_target"] == "OTHER_EASTERN_ASIA"
    assert crosswalk.at["TWN", "accounting_target_type"] == "named_regional_account"
    assert crosswalk.at["TWN", "accounting_target"] != "CHN"
    assert crosswalk.at["ESH", "accounting_target"] == "MAR"

    included = set(
        crosswalk.index[
            crosswalk["gdp_scope_action"].eq("already_in_accounting_target")
        ]
    )
    assert included == {"ESH", "GLP", "GUF", "MAF", "MTQ", "MYT", "REU"}
    assert int(
        crosswalk["gdp_scope_action"].eq(
            "add_source_gdp_to_accounting_target"
        ).sum()
    ) == 18


def test_original_m49_reporting_geography_survives_parent_aggregation(config):
    crosswalk = territory_crosswalk(config).set_index("source_economy_id")
    expected_geography = {
        "ASM": ("009", "061"),
        "BES": ("019", "029"),
        "BLM": ("019", "029"),
        "ESH": ("002", "015"),
        "FLK": ("019", "005"),
        "FRO": ("150", "154"),
        "GGY": ("150", "154"),
        "GIB": ("150", "039"),
        "GLP": ("019", "029"),
        "GUF": ("019", "005"),
        "GUM": ("009", "057"),
        "IMN": ("150", "154"),
        "JEY": ("150", "154"),
        "MAF": ("019", "029"),
        "MNP": ("009", "057"),
        "MTQ": ("019", "029"),
        "MYT": ("002", "014"),
        "NIU": ("009", "061"),
        "REU": ("002", "014"),
        "SHN": ("002", "011"),
        "SPM": ("019", "021"),
        "TKL": ("009", "061"),
        "TWN": ("142", "030"),
        "VIR": ("019", "029"),
        "WLF": ("009", "061"),
    }
    actual_geography = {
        code: (
            crosswalk.at[code, "reporting_region_target"],
            crosswalk.at[code, "reporting_subregion_target"],
        )
        for code in crosswalk.index
    }
    assert actual_geography == expected_geography

    source = pd.DataFrame(
        {
            "economy_id": ["GUF", "REU", "WLF", "TWN", "CHN"],
            "value": [1, 2, 3, 4, 5],
        }
    )
    mapped = attach_territory_mapping(source, config).set_index("economy_id")

    assert mapped.loc["GUF", ["accounting_target", "reporting_region_target", "reporting_subregion_target"]].tolist() == [
        "FRA",
        "019",
        "005",
    ]
    assert mapped.loc["REU", ["accounting_target", "reporting_region_target", "reporting_subregion_target"]].tolist() == [
        "FRA",
        "002",
        "014",
    ]
    assert mapped.loc["WLF", ["accounting_target", "reporting_region_target", "reporting_subregion_target"]].tolist() == [
        "FRA",
        "009",
        "061",
    ]
    assert mapped.loc["TWN", ["accounting_target", "reporting_region_target", "reporting_subregion_target"]].tolist() == [
        "OTHER_EASTERN_ASIA",
        "142",
        "030",
    ]
    assert mapped.at["CHN", "accounting_target"] == "CHN"
    assert pd.isna(mapped.at["CHN", "reporting_region_target"])


def _complete_accounting_slice(config) -> pd.DataFrame:
    crosswalk = territory_crosswalk(config)
    included_gdp = set(
        crosswalk.loc[
            crosswalk["gdp_scope_action"].eq("already_in_accounting_target"),
            "source_economy_id",
        ]
    )
    receiver_rows = [
        {"economy_id": code, "year": 2023, "population": 1000.0, "gdp": 10000.0, "product_quantity": 100.0}
        for code in ["USA", "NLD", "FRA", "MAR", "GBR", "DNK", "NZL", "CHN"]
    ]
    source_rows = []
    for index, code in enumerate(sorted(EXPECTED_TERRITORIES), start=1):
        source_rows.append(
            {
                "economy_id": code,
                "year": 2023,
                "population": float(index),
                # Zero is the exclusive contribution when published parent GDP
                # already includes the territory; other territories must add GDP.
                "gdp": 0.0 if code in included_gdp else float(index * 10),
                "product_quantity": float(index * 3),
            }
        )
    return pd.DataFrame(receiver_rows + source_rows)


def test_population_gdp_and_product_values_are_conserved_without_standalone_territories(
    config,
):
    source = _complete_accounting_slice(config)
    validate_parent_scope_gdp(source, config, gdp_column="gdp")
    result = aggregate_additive_values(
        source,
        config,
        value_columns=["population", "gdp", "product_quantity"],
        dimension_columns=["year"],
        require_all_territories=True,
    ).set_index("economy_id")

    for column in ["population", "gdp", "product_quantity"]:
        assert result[column].sum() == pytest.approx(source[column].sum())
    assert not (set(result.index) & EXPECTED_TERRITORIES)

    crosswalk = territory_crosswalk(config).set_index("source_economy_id")
    usa_sources = set(
        crosswalk.index[crosswalk["accounting_target"].eq("USA")]
    )
    expected_usa_population = 1000.0 + source.loc[
        source["economy_id"].isin(usa_sources), "population"
    ].sum()
    assert result.at["USA", "population"] == pytest.approx(expected_usa_population)

    twn = source.loc[source["economy_id"].eq("TWN")].iloc[0]
    assert result.at["OTHER_EASTERN_ASIA", "population"] == pytest.approx(
        twn["population"]
    )
    assert result.at["OTHER_EASTERN_ASIA", "gdp"] == pytest.approx(twn["gdp"])
    assert result.at["CHN", "population"] == pytest.approx(1000.0)
    assert result.at["CHN", "gdp"] == pytest.approx(10000.0)


def test_product_quantities_close_separately_for_every_product(config):
    rows = []
    for product_index, product in enumerate(["rice", "sugar", "cotton"], start=1):
        rows.append(
            {
                "economy_id": "FRA",
                "year": 2023,
                "product": product,
                "quantity": float(100 * product_index),
            }
        )
        for source_index, code in enumerate(sorted(EXPECTED_TERRITORIES), start=1):
            rows.append(
                {
                    "economy_id": code,
                    "year": 2023,
                    "product": product,
                    "quantity": float(product_index * source_index),
                }
            )
    source = pd.DataFrame(rows)
    result = aggregate_additive_values(
        source,
        config,
        value_columns=["quantity"],
        dimension_columns=["year", "product"],
        require_all_territories=True,
    )

    before = source.groupby(["year", "product"])["quantity"].sum().sort_index()
    after = result.groupby(["year", "product"])["quantity"].sum().sort_index()
    pd.testing.assert_series_equal(before, after)


def test_duplicate_source_rows_are_rejected_before_they_can_inflate_a_target(config):
    source = pd.DataFrame(
        {
            "economy_id": ["ASM", "ASM"],
            "year": [2023, 2023],
            "quantity": [1.0, 1.0],
        }
    )
    with pytest.raises(ValueError, match="Duplicate source rows"):
        aggregate_additive_values(
            source,
            config,
            value_columns=["quantity"],
            dimension_columns=["year"],
        )


def test_parent_scope_gdp_validation_blocks_double_count_and_missing_additions(config):
    double_count = pd.DataFrame(
        {"economy_id": ["FRA", "GLP"], "gdp": [100.0, 1.0]}
    )
    with pytest.raises(ValueError, match="double count"):
        validate_parent_scope_gdp(double_count, config, gdp_column="gdp")

    missing_addition = pd.DataFrame(
        {"economy_id": ["USA", "GUM"], "gdp": [100.0, None]}
    )
    with pytest.raises(ValueError, match="Supplemental GDP is required"):
        validate_parent_scope_gdp(missing_addition, config, gdp_column="gdp")
