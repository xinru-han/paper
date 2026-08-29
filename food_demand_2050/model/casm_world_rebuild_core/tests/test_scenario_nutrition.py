from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest
import yaml

from casm_world.nutrition import COEFFICIENT_COLUMNS, EXPECTED_COMMODITIES, load_nutrition_config
from casm_world.scenario_nutrition import (
    REQUIRED_QUANTITY_COLUMN,
    ScenarioNutritionError,
    build_scenario_nutrition_tables,
    run_official_scenario_nutrition,
)


ROOT = Path(__file__).parents[1]
SCENARIOS = ["SSP1", "SSP2", "SSP3", "SSP4", "SSP5"]
YEARS = [2023, 2024]
ECONOMIES = ["CHN", "USA"]


def _coefficients(config: dict) -> pd.DataFrame:
    rows = []
    for commodity in EXPECTED_COMMODITIES:
        definition = config["commodities"][commodity]
        food_use = bool(definition["food_use"])
        rows.append(
            {
                "commodity": commodity,
                "food_use": food_use,
                "source_class": definition["source_class"],
                "energy_kcal_per_kg": 1000.0 if food_use else 0.0,
                "protein_g_per_kg": 100.0 if food_use else 0.0,
                "fat_g_per_kg": 50.0 if food_use else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _scenario_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    result_rows = []
    driver_rows = []
    for scenario_number, scenario in enumerate(SCENARIOS, start=1):
        for year in YEARS:
            for economy in ECONOMIES:
                base_population = 100.0 if economy == "CHN" else 50.0
                population = (
                    base_population
                    if year == 2023
                    else base_population * (1.0 + 0.01 * scenario_number)
                )
                driver_rows.append(
                    {
                        "scenario": scenario,
                        "year": year,
                        "economy_id": economy,
                        "population_million": population,
                    }
                )
                for commodity in EXPECTED_COMMODITIES:
                    food = 0.0
                    if commodity == "RIC":
                        base_food = 1.0 if economy == "CHN" else 2.0
                        food = (
                            base_food
                            if year == 2023
                            else base_food * (1.0 + 0.02 * scenario_number)
                        )
                    result_rows.append(
                        {
                            "scenario": scenario,
                            "year": year,
                            "economy_id": economy,
                            "commodity": commodity,
                            "food_demand_mt": food,
                            # Deliberately huge: a nutrition calculation that
                            # accidentally uses this field will fail the anchor.
                            "final_demand_mt": food + 1_000_000.0,
                        }
                    )
    return pd.DataFrame(result_rows), pd.DataFrame(driver_rows)


@pytest.fixture(scope="module")
def config() -> dict:
    return load_nutrition_config(ROOT / "config" / "nutrition.yaml")


def test_end_to_end_tables_use_food_not_final_demand(config: dict):
    results, drivers = _scenario_inputs()
    tables = build_scenario_nutrition_tables(
        results,
        drivers,
        _coefficients(config),
        expected_scenarios=SCENARIOS,
        expected_years=YEARS,
        expected_economy_count=len(ECONOMIES),
    )
    assert tables.audit["status"] == "passed_official_ssp_nutrition_postsolve"
    assert tables.audit["quantity_column_used"] == REQUIRED_QUANTITY_COLUMN
    assert tables.audit["forbidden_quantity_column_used"] is False
    assert "not a complete diet" in tables.audit["interpretation_scope"]
    assert len(tables.commodity_contributions) == 5 * 2 * 2 * 31
    assert len(tables.economy) == 5 * 2 * 2
    assert len(tables.world) == 5 * 2
    china = tables.economy.query(
        "scenario == 'SSP1' and year == 2023 and economy_id == 'CHN'"
    ).iloc[0]
    assert china["energy_kcal"] == pytest.approx(1.0e12)
    assert china["kcal_per_capita_day"] == pytest.approx(
        1.0e12 / (100.0e6 * 365.0)
    )
    assert tables.audit["nonfood"]["positive_food_demand_count"] == 0
    assert tables.audit["world_conservation"]["violation_count"] == 0
    assert tables.audit["base_year_consistency"]["economy_nutrition"]["maximum_absolute_range"] == 0.0
    assert not tables.economy.isna().any().any()
    assert not tables.world.isna().any().any()
    assert not tables.commodity_contributions.isna().any().any()


def test_base_year_ssp_inconsistency_is_rejected(config: dict):
    results, drivers = _scenario_inputs()
    key = (
        results["scenario"].eq("SSP5")
        & results["year"].eq(2023)
        & results["economy_id"].eq("CHN")
        & results["commodity"].eq("RIC")
    )
    results.loc[key, "food_demand_mt"] += 0.001
    with pytest.raises(ScenarioNutritionError, match="base-year SSP consistency"):
        build_scenario_nutrition_tables(
            results,
            drivers,
            _coefficients(config),
            expected_scenarios=SCENARIOS,
            expected_years=YEARS,
            expected_economy_count=2,
        )


def test_positive_nonfood_is_rejected(config: dict):
    results, drivers = _scenario_inputs()
    key = (
        results["scenario"].eq("SSP1")
        & results["year"].eq(2024)
        & results["economy_id"].eq("USA")
        & results["commodity"].eq("CTN")
    )
    results.loc[key, "food_demand_mt"] = 0.01
    with pytest.raises(ScenarioNutritionError, match="nonfood"):
        build_scenario_nutrition_tables(
            results,
            drivers,
            _coefficients(config),
            expected_scenarios=SCENARIOS,
            expected_years=YEARS,
            expected_economy_count=2,
        )


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "na"])
def test_grid_duplicate_missing_and_na_are_rejected(config: dict, mutation: str):
    results, drivers = _scenario_inputs()
    if mutation == "duplicate":
        results = pd.concat([results, results.iloc[[0]]], ignore_index=True)
        pattern = "duplicate"
    elif mutation == "missing":
        results = results.iloc[:-1].copy()
        pattern = "row count"
    else:
        results.loc[0, "food_demand_mt"] = float("nan")
        pattern = "NA"
    with pytest.raises(ScenarioNutritionError, match=pattern):
        build_scenario_nutrition_tables(
            results,
            drivers,
            _coefficients(config),
            expected_scenarios=SCENARIOS,
            expected_years=YEARS,
            expected_economy_count=2,
        )


def test_file_runner_writes_all_outputs_and_audit(tmp_path: Path, config: dict):
    results, drivers = _scenario_inputs()
    coefficients = _coefficients(config)
    result_path = tmp_path / "results.csv"
    driver_path = tmp_path / "drivers.csv"
    coefficient_path = tmp_path / "coefficients.csv"
    results.to_csv(result_path, index=False)
    drivers.to_csv(driver_path, index=False)
    coefficients.to_csv(coefficient_path, index=False)

    scenario_config = deepcopy(config)
    settings = scenario_config["scenario_postsolve"]
    settings["inputs"].update(
        {
            "scenario_results": str(result_path),
            "drivers": str(driver_path),
            "coefficients": str(coefficient_path),
        }
    )
    settings["expected_grid"].update(
        {"first_year": 2023, "last_year": 2024, "economy_count": 2}
    )
    settings["outputs"].update(
        {
            "economy_summary": str(tmp_path / "economy.csv"),
            "world_summary": str(tmp_path / "world.csv"),
            "commodity_contributions": str(tmp_path / "contributions.csv"),
            "audit": str(tmp_path / "audit.json"),
        }
    )
    config_path = tmp_path / "nutrition.yaml"
    config_path.write_text(yaml.safe_dump(scenario_config, sort_keys=False), encoding="utf-8")
    tables, paths = run_official_scenario_nutrition(config_path=config_path)
    assert tables.audit["status"] == "passed_official_ssp_nutrition_postsolve"
    assert all(path.is_file() for path in paths.values())
    assert paths["commodity_contributions"].stat().st_size > 0
    assert tables.audit["written_files"]["sha256"]["economy_summary"] != ""


def test_configuration_cannot_select_final_demand(tmp_path: Path, config: dict):
    scenario_config = deepcopy(config)
    scenario_config["scenario_postsolve"]["inputs"]["quantity_column"] = "final_demand_mt"
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(yaml.safe_dump(scenario_config, sort_keys=False), encoding="utf-8")
    with pytest.raises(ScenarioNutritionError, match="forbidden"):
        run_official_scenario_nutrition(config_path=config_path)
