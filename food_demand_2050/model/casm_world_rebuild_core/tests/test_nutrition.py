import csv
import io
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import pytest

from casm_world.nutrition import (
    COEFFICIENT_COLUMNS,
    EXPECTED_COMMODITIES,
    NutritionContractError,
    audit_food_and_diet_archive,
    derive_nutrition_coefficients,
    load_nutrition_config,
    postsolve_nutrition,
)


CONFIG_PATH = Path(__file__).parents[1] / "config" / "nutrition.yaml"


def _write_fbs_archive(path: Path, config: dict, *, bad_energy_unit: bool = False) -> None:
    columns = [
        "Area Code (M49)", "Item Code", "Element Code", "Year", "Unit", "Value"
    ]
    element_rows = {
        "food_quantity": (5142, "1000 t", 2.0),
        "energy": (661, "million Kcal", 6000.0),
        "protein": (671, "t", 200.0),
        "fat": (681, "t", 40.0),
    }
    item_codes = sorted(
        {
            int(item)
            for definition in config["commodities"].values()
            for item in definition.get("fbs_items", [])
        }
    )
    rows = []
    for item in item_codes:
        for component, (element, unit, value) in element_rows.items():
            if bad_energy_unit and item == 2807 and component == "energy":
                unit = "kcal/cap/d"
            rows.append(["'156", item, element, 2023, unit, value])
            # A different year must not enter the coefficient.
            rows.append(["'156", item, element, 2022, unit, value * 99.0])
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(columns)
    writer.writerows(rows)
    with zipfile.ZipFile(path, "w") as zipped:
        zipped.writestr("Synthetic_All_Data_(Normalized).csv", stream.getvalue())


def _write_food_and_diet_archive(path: Path) -> None:
    columns = [
        "Area Code (M49)", "Food Group Code", "Indicator Code", "Year", "Unit", "Value"
    ]
    indicators = [
        (4003, "kcal/cap/d", 3000.0),
        (4004, "g/cap/d", 100.0),
        (4005, "g/cap/d", 80.0),
    ]
    rows = []
    for food_group in ("FG0", "FG1"):
        for code, unit, value in indicators:
            rows.append(["'156", food_group, code, 2023, unit, value])
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(columns)
    writer.writerows(rows)
    with zipfile.ZipFile(path, "w") as zipped:
        zipped.writestr("Synthetic_All_Data_(Normalized).csv", stream.getvalue())


@pytest.fixture(scope="module")
def config() -> dict:
    return load_nutrition_config(CONFIG_PATH)


@pytest.fixture()
def synthetic_coefficients(tmp_path: Path, config: dict) -> pd.DataFrame:
    archive = tmp_path / "fbs.zip"
    _write_fbs_archive(archive, config)
    coefficients, _ = derive_nutrition_coefficients(
        config, archive, allowed_m49={"156"}, chunksize=50
    )
    return coefficients


def test_config_is_exhaustive_and_nonfood_is_explicit(config: dict):
    assert tuple(config["commodities"]) == EXPECTED_COMMODITIES
    counts = pd.Series(
        [definition["source_class"] for definition in config["commodities"].values()]
    ).value_counts()
    assert counts.to_dict() == {
        "direct": 14,
        "nonfood": 10,
        "fallback": 5,
        "aggregate": 2,
    }
    nonfood = {
        commodity
        for commodity, definition in config["commodities"].items()
        if definition["source_class"] == "nonfood"
    }
    assert nonfood == {"SBM", "NBM", "RBM", "DDG", "ETH", "BDI", "CTN", "SCA", "SBE", "MLK"}
    assert all(config["commodities"][code]["reason"] for code in nonfood)


def test_fbs_coefficient_units_methods_and_no_missing(
    synthetic_coefficients: pd.DataFrame,
):
    table = synthetic_coefficients.set_index("commodity")
    # million kcal / thousand tonnes is numerically kcal/kg.
    assert table.loc["RIC", "energy_kcal_per_kg"] == pytest.approx(3000.0)
    # tonnes nutrient / thousand tonnes food is numerically g/kg.
    assert table.loc["RIC", "protein_g_per_kg"] == pytest.approx(100.0)
    assert table.loc["RIC", "fat_g_per_kg"] == pytest.approx(20.0)
    assert table.loc["RIC", "source_class"] == "direct"
    assert table.loc["OCG", "source_class"] == "aggregate"
    assert table.loc["OCG", "paired_country_item_observations"] == 6
    assert table.loc["OCG", "paired_country_product_observations"] == 1
    assert table.loc["OCG", "fbs_food_quantity_mt"] == pytest.approx(0.012)
    assert table.loc["OCG", "physical_bound_adjustments"] == "none"
    assert table.loc["CHE", "source_class"] == "fallback"
    assert table.loc["CHE", "energy_kcal_per_kg"] == pytest.approx(4000.0)
    assert table.loc["CTN", "source_class"] == "nonfood"
    assert (table.loc["CTN", list(COEFFICIENT_COLUMNS)] == 0.0).all()
    assert len(table) == 31
    assert not table.isna().any().any()


def test_physical_bounds_are_explicitly_recorded(tmp_path: Path, config: dict):
    archive = tmp_path / "fbs.zip"
    _write_fbs_archive(archive, config)
    # Make the synthetic fat total imply 1,500 g/kg for the one RIC country.
    with zipfile.ZipFile(archive) as zipped:
        member = zipped.namelist()[0]
        text = zipped.read(member).decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    for row in rows:
        if row["Item Code"] == "2807" and row["Element Code"] == "681" and row["Year"] == "2023":
            row["Value"] = "3000"
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("Synthetic_All_Data_(Normalized).csv", stream.getvalue())
    table, _ = derive_nutrition_coefficients(config, archive, allowed_m49={"156"})
    rice = table.set_index("commodity").loc["RIC"]
    assert rice["fat_g_per_kg"] == 1000.0
    assert rice["physical_bound_adjustments"].startswith("fat_g_per_kg:1500->1000")


def test_unexpected_fbs_unit_is_rejected(tmp_path: Path, config: dict):
    archive = tmp_path / "bad_fbs.zip"
    _write_fbs_archive(archive, config, bad_energy_unit=True)
    with pytest.raises(NutritionContractError, match="unexpected unit"):
        derive_nutrition_coefficients(config, archive, allowed_m49={"156"})


def test_food_and_diet_energy_protein_fat_audit(tmp_path: Path):
    archive = tmp_path / "food_and_diet.zip"
    _write_food_and_diet_archive(archive)
    report = audit_food_and_diet_archive(archive, allowed_m49={"156"}, chunksize=2)
    assert report["status"] == "passed"
    assert report["food_groups_observed"] == ["FG0", "FG1"]
    assert report["country_food_group_records"] == 2
    assert report["complete_energy_protein_fat_records"] == 2
    assert report["countries_with_complete_all_food_groups_fg0"] == 1


def _postsolve_inputs(coefficients: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for economy in ("CHN", "USA"):
        for commodity in EXPECTED_COMMODITIES:
            quantity = 0.0
            if economy == "CHN" and commodity == "RIC":
                quantity = 1.0
            elif economy == "USA" and commodity == "WHE":
                quantity = 2.0
            rows.append(
                {
                    "scenario": "SSP2",
                    "year": 2030,
                    "economy_id": economy,
                    "commodity": commodity,
                    "food_quantity_mt": quantity,
                }
            )
    population = pd.DataFrame(
        [
            {"scenario": "SSP2", "year": 2030, "economy_id": "CHN", "population_million": 100.0},
            {"scenario": "SSP2", "year": 2030, "economy_id": "USA", "population_million": 50.0},
        ]
    )
    return pd.DataFrame(rows), population


def test_postsolve_unit_conversion_world_weighting_and_conservation(
    synthetic_coefficients: pd.DataFrame,
):
    quantities, population = _postsolve_inputs(synthetic_coefficients)
    result = postsolve_nutrition(quantities, population, synthetic_coefficients)
    country = result.economy.set_index("economy_id")
    world = result.world.iloc[0]

    assert country.loc["CHN", "energy_kcal"] == pytest.approx(3.0e12)
    assert country.loc["CHN", "protein_g"] == pytest.approx(1.0e11)
    assert country.loc["CHN", "fat_g"] == pytest.approx(2.0e10)
    assert country.loc["CHN", "kcal_per_capita_day"] == pytest.approx(
        3.0e12 / (100.0e6 * 365.0)
    )
    assert world["population_million"] == pytest.approx(150.0)
    assert world["energy_kcal"] == pytest.approx(9.0e12)
    assert world["kcal_per_capita_day"] == pytest.approx(
        9.0e12 / (150.0e6 * 365.0)
    )
    # World totals conserve country totals, while the per-capita result is
    # population weighted rather than a sum or simple average.
    for column in ("food_quantity_mt", "energy_kcal", "protein_g", "fat_g"):
        assert world[column] == pytest.approx(result.economy[column].sum())
    assert not result.summary.isna().any().any()
    assert set(result.summary["aggregation_level"]) == {"economy", "world"}
    assert len(result.commodity_contributions) == 2 * len(EXPECTED_COMMODITIES)


def test_positive_nonfood_food_quantity_is_rejected(
    synthetic_coefficients: pd.DataFrame,
):
    quantities, population = _postsolve_inputs(synthetic_coefficients)
    quantities.loc[
        quantities["economy_id"].eq("CHN") & quantities["commodity"].eq("CTN"),
        "food_quantity_mt",
    ] = 0.01
    with pytest.raises(NutritionContractError, match="nonfood"):
        postsolve_nutrition(quantities, population, synthetic_coefficients)


def test_duplicate_and_incomplete_food_grids_are_rejected(
    synthetic_coefficients: pd.DataFrame,
):
    quantities, population = _postsolve_inputs(synthetic_coefficients)
    duplicate = pd.concat([quantities, quantities.iloc[[0]]], ignore_index=True)
    with pytest.raises(NutritionContractError, match="duplicate"):
        postsolve_nutrition(duplicate, population, synthetic_coefficients)

    incomplete = quantities.iloc[:-1].copy()
    with pytest.raises(NutritionContractError, match="incomplete commodity grid"):
        postsolve_nutrition(incomplete, population, synthetic_coefficients)


def test_population_identity_must_match_food_accounts(
    synthetic_coefficients: pd.DataFrame,
):
    quantities, population = _postsolve_inputs(synthetic_coefficients)
    population = population[population["economy_id"].ne("USA")]
    with pytest.raises(NutritionContractError, match="do not match exactly"):
        postsolve_nutrition(quantities, population, synthetic_coefficients)
