"""Strict end-to-end nutrition postsolve for the official SSP result cube.

Only ``food_demand_mt`` is read from the scenario result file.  The connector
does not load or alias ``final_demand_mt`` and rejects any configuration that
attempts to use it as the nutrition quantity.  Population is the absolute
``population_million`` series from the SSP driver table.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from casm_world.nutrition import (
    COEFFICIENT_COLUMNS,
    EXPECTED_COMMODITIES,
    NutritionContractError,
    NutritionPostsolveResult,
    load_nutrition_config,
    postsolve_nutrition,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_QUANTITY_COLUMN = "food_demand_mt"
FORBIDDEN_QUANTITY_COLUMN = "final_demand_mt"
RESULT_KEY = ["scenario", "year", "economy_id", "commodity"]
ACCOUNT_KEY = ["scenario", "year", "economy_id"]
DRIVER_COLUMNS = [*ACCOUNT_KEY, "population_million"]
RESULT_COLUMNS = [*RESULT_KEY, REQUIRED_QUANTITY_COLUMN]
CONSERVATION_COLUMNS = [
    "population_million",
    REQUIRED_QUANTITY_COLUMN,
    "energy_kcal",
    "protein_g",
    "fat_g",
]


class ScenarioNutritionError(NutritionContractError):
    """Raised when the official SSP-to-nutrition interface is not auditable."""


@dataclass(frozen=True)
class ScenarioNutritionTables:
    """Scenario output tables and their audit metrics."""

    economy: pd.DataFrame
    world: pd.DataFrame
    commodity_contributions: pd.DataFrame
    audit: dict[str, Any]


def _scenario_settings(config: Mapping[str, Any]) -> Mapping[str, Any]:
    settings = config.get("scenario_postsolve")
    if not isinstance(settings, Mapping):
        raise ScenarioNutritionError("scenario_postsolve must be configured")
    inputs = settings.get("inputs")
    grid = settings.get("expected_grid")
    checks = settings.get("checks")
    outputs = settings.get("outputs")
    if not all(isinstance(value, Mapping) for value in (inputs, grid, checks, outputs)):
        raise ScenarioNutritionError(
            "scenario_postsolve inputs, expected_grid, checks and outputs must be mappings"
        )
    if not str(settings.get("interpretation_scope", "")).strip():
        raise ScenarioNutritionError("scenario nutrition interpretation_scope is required")
    if inputs.get("quantity_column") != REQUIRED_QUANTITY_COLUMN:
        raise ScenarioNutritionError(
            f"nutrition quantity must be {REQUIRED_QUANTITY_COLUMN}; "
            f"{FORBIDDEN_QUANTITY_COLUMN} is forbidden"
        )
    if inputs.get("forbidden_quantity_column") != FORBIDDEN_QUANTITY_COLUMN:
        raise ScenarioNutritionError(
            f"forbidden quantity sentinel must be {FORBIDDEN_QUANTITY_COLUMN}"
        )
    scenarios = grid.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ScenarioNutritionError("expected scenarios must be a non-empty list")
    if len(scenarios) != len(set(map(str, scenarios))):
        raise ScenarioNutritionError("expected scenarios contain duplicates")
    first_year = int(grid.get("first_year", -1))
    last_year = int(grid.get("last_year", -1))
    if first_year > last_year:
        raise ScenarioNutritionError("invalid scenario year range")
    if int(grid.get("commodity_count", -1)) != len(EXPECTED_COMMODITIES):
        raise ScenarioNutritionError("scenario commodity_count must equal 31")
    if int(grid.get("economy_count", -1)) <= 0:
        raise ScenarioNutritionError("scenario economy_count must be positive")
    for key in (
        "base_year_scenario_absolute_tolerance",
        "world_conservation_relative_tolerance",
        "nonfood_positive_tolerance_mt",
    ):
        value = float(checks.get(key, -1.0))
        if not isfinite(value) or value < 0:
            raise ScenarioNutritionError(f"invalid scenario check tolerance {key}")
    return settings


def _expected_axes(
    *,
    expected_scenarios: Sequence[str],
    expected_years: Sequence[int],
    expected_economy_count: int,
) -> tuple[list[str], list[int], int]:
    scenarios = [str(value) for value in expected_scenarios]
    years = [int(value) for value in expected_years]
    if not scenarios or len(scenarios) != len(set(scenarios)):
        raise ScenarioNutritionError("expected_scenarios must be unique and non-empty")
    if not years or len(years) != len(set(years)):
        raise ScenarioNutritionError("expected_years must be unique and non-empty")
    economy_count = int(expected_economy_count)
    if economy_count <= 0:
        raise ScenarioNutritionError("expected_economy_count must be positive")
    return scenarios, years, economy_count


def validate_official_scenario_grid(
    results: pd.DataFrame,
    drivers: pd.DataFrame,
    *,
    expected_scenarios: Sequence[str],
    expected_years: Sequence[int],
    expected_economy_count: int,
) -> dict[str, Any]:
    """Validate the complete scenario/account/product Cartesian grids."""

    scenarios, years, economy_count = _expected_axes(
        expected_scenarios=expected_scenarios,
        expected_years=expected_years,
        expected_economy_count=expected_economy_count,
    )
    missing_results = set(RESULT_COLUMNS) - set(results)
    missing_drivers = set(DRIVER_COLUMNS) - set(drivers)
    if missing_results:
        raise ScenarioNutritionError(
            f"scenario results missing columns: {sorted(missing_results)}"
        )
    if missing_drivers:
        raise ScenarioNutritionError(
            f"SSP drivers missing columns: {sorted(missing_drivers)}"
        )
    # The caller may hold final_demand_mt for other work, but this interface
    # never consumes it.  Only the explicitly named food column is validated.
    result = results[RESULT_COLUMNS].copy()
    driver = drivers[DRIVER_COLUMNS].copy()
    for frame in (result, driver):
        frame["scenario"] = frame["scenario"].astype(str).str.strip()
        frame["economy_id"] = frame["economy_id"].astype(str).str.strip().str.upper()
        frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    result["commodity"] = result["commodity"].astype(str).str.strip().str.upper()
    result[REQUIRED_QUANTITY_COLUMN] = pd.to_numeric(
        result[REQUIRED_QUANTITY_COLUMN], errors="coerce"
    )
    driver["population_million"] = pd.to_numeric(
        driver["population_million"], errors="coerce"
    )
    if result.isna().any().any() or driver.isna().any().any():
        raise ScenarioNutritionError("scenario nutrition inputs contain NA")
    result["year"] = result["year"].astype(int)
    driver["year"] = driver["year"].astype(int)
    food_values = result[REQUIRED_QUANTITY_COLUMN].to_numpy(dtype=float)
    population_values = driver["population_million"].to_numpy(dtype=float)
    if not np.isfinite(food_values).all() or (food_values < 0).any():
        raise ScenarioNutritionError("food_demand_mt must be finite and nonnegative")
    if not np.isfinite(population_values).all() or (population_values <= 0).any():
        raise ScenarioNutritionError("absolute population_million must be finite and positive")
    if result.duplicated(RESULT_KEY).any():
        raise ScenarioNutritionError("duplicate scenario/year/economy/commodity result key")
    if driver.duplicated(ACCOUNT_KEY).any():
        raise ScenarioNutritionError("duplicate scenario/year/economy SSP driver key")

    if set(result["scenario"]) != set(scenarios) or set(driver["scenario"]) != set(scenarios):
        raise ScenarioNutritionError("observed SSP scenarios do not match expected scenarios")
    if set(result["year"]) != set(years) or set(driver["year"]) != set(years):
        raise ScenarioNutritionError("observed SSP years do not match expected years")
    if set(result["commodity"]) != set(EXPECTED_COMMODITIES):
        raise ScenarioNutritionError("scenario results do not cover exactly 31 commodities")
    result_economies = set(result["economy_id"])
    driver_economies = set(driver["economy_id"])
    if result_economies != driver_economies or len(result_economies) != economy_count:
        raise ScenarioNutritionError(
            "result and driver economy universes must match the expected count"
        )

    expected_accounts = len(scenarios) * len(years) * economy_count
    expected_result_rows = expected_accounts * len(EXPECTED_COMMODITIES)
    if len(result) != expected_result_rows:
        raise ScenarioNutritionError(
            f"scenario result row count {len(result)} != {expected_result_rows}"
        )
    if len(driver) != expected_accounts:
        raise ScenarioNutritionError(
            f"SSP driver row count {len(driver)} != {expected_accounts}"
        )
    product_counts = result.groupby(ACCOUNT_KEY, dropna=False)["commodity"].nunique()
    if len(product_counts) != expected_accounts or not product_counts.eq(
        len(EXPECTED_COMMODITIES)
    ).all():
        raise ScenarioNutritionError("each scenario account must contain all 31 products")
    economy_counts = driver.groupby(["scenario", "year"], dropna=False)[
        "economy_id"
    ].nunique()
    if not economy_counts.eq(economy_count).all():
        raise ScenarioNutritionError("each scenario-year driver slice must contain all economies")

    result_accounts = result[ACCOUNT_KEY].drop_duplicates()
    driver_accounts = driver[ACCOUNT_KEY].drop_duplicates()
    account_match = result_accounts.merge(
        driver_accounts,
        on=ACCOUNT_KEY,
        how="outer",
        indicator=True,
        validate="one_to_one",
    )
    if not account_match["_merge"].eq("both").all():
        raise ScenarioNutritionError("scenario result and driver account keys do not match")
    return {
        "scenario_count": len(scenarios),
        "year_count": len(years),
        "economy_count": economy_count,
        "commodity_count": len(EXPECTED_COMMODITIES),
        "account_count": expected_accounts,
        "result_row_count": expected_result_rows,
        "driver_row_count": expected_accounts,
    }


def _base_year_consistency(
    frame: pd.DataFrame,
    *,
    base_year: int,
    key_without_scenario: Sequence[str],
    value_columns: Sequence[str],
    scenario_count: int,
    absolute_tolerance: float,
) -> dict[str, Any]:
    base = frame.loc[frame["year"].eq(base_year)].copy()
    if base.empty:
        raise ScenarioNutritionError(f"base year {base_year} is absent")
    counts = base.groupby(list(key_without_scenario), dropna=False)["scenario"].nunique()
    if not counts.eq(scenario_count).all():
        raise ScenarioNutritionError(
            f"base-year keys do not each contain {scenario_count} SSP observations"
        )
    maximum_range = 0.0
    violations = 0
    for column in value_columns:
        spread = base.groupby(list(key_without_scenario), dropna=False)[column].agg(
            lambda values: float(values.max() - values.min())
        )
        maximum_range = max(maximum_range, float(spread.max()))
        violations += int(spread.gt(absolute_tolerance).sum())
    if violations:
        raise ScenarioNutritionError(
            f"base-year SSP consistency failed: {violations} key/value ranges exceed "
            f"{absolute_tolerance}"
        )
    return {
        "base_year": int(base_year),
        "scenario_count_per_key": int(scenario_count),
        "absolute_tolerance": float(absolute_tolerance),
        "maximum_absolute_range": float(maximum_range),
        "violation_count": int(violations),
        "status": "passed",
    }


def _world_conservation_audit(
    economy: pd.DataFrame,
    world: pd.DataFrame,
    *,
    relative_tolerance: float,
) -> dict[str, Any]:
    recomputed = economy.groupby(["scenario", "year"], as_index=False)[
        CONSERVATION_COLUMNS
    ].sum()
    reference = world[["scenario", "year", *CONSERVATION_COLUMNS]].copy()
    comparison = recomputed.merge(
        reference,
        on=["scenario", "year"],
        suffixes=("_economies", "_world"),
        validate="one_to_one",
    )
    maximum_relative = 0.0
    maximum_absolute = 0.0
    violations = 0
    by_column: dict[str, dict[str, float | int]] = {}
    for column in CONSERVATION_COLUMNS:
        left = comparison[f"{column}_economies"].to_numpy(dtype=float)
        right = comparison[f"{column}_world"].to_numpy(dtype=float)
        absolute = np.abs(left - right)
        scale = np.maximum(np.abs(right), 1.0e-30)
        relative = absolute / scale
        column_max_abs = float(absolute.max(initial=0.0))
        column_max_rel = float(relative.max(initial=0.0))
        column_violations = int((relative > relative_tolerance).sum())
        maximum_absolute = max(maximum_absolute, column_max_abs)
        maximum_relative = max(maximum_relative, column_max_rel)
        violations += column_violations
        by_column[column] = {
            "maximum_absolute_residual": column_max_abs,
            "maximum_relative_residual": column_max_rel,
            "violation_count": column_violations,
        }
    if violations:
        raise ScenarioNutritionError(
            f"WORLD conservation failed for {violations} scenario-year fields"
        )
    return {
        "status": "passed",
        "relative_tolerance": float(relative_tolerance),
        "maximum_absolute_residual": maximum_absolute,
        "maximum_relative_residual": maximum_relative,
        "violation_count": violations,
        "by_column": by_column,
    }


def build_scenario_nutrition_tables(
    results: pd.DataFrame,
    drivers: pd.DataFrame,
    coefficients: pd.DataFrame,
    *,
    expected_scenarios: Sequence[str],
    expected_years: Sequence[int],
    expected_economy_count: int,
    base_year: int = 2023,
    base_year_absolute_tolerance: float = 1.0e-12,
    world_relative_tolerance: float = 1.0e-12,
    nonfood_positive_tolerance_mt: float = 1.0e-12,
) -> ScenarioNutritionTables:
    """Validate, calculate and audit all official SSP nutrition results."""

    grid = validate_official_scenario_grid(
        results,
        drivers,
        expected_scenarios=expected_scenarios,
        expected_years=expected_years,
        expected_economy_count=expected_economy_count,
    )
    result_input = results[RESULT_COLUMNS].copy()
    driver_input = drivers[DRIVER_COLUMNS].copy()
    food_consistency = _base_year_consistency(
        result_input,
        base_year=base_year,
        key_without_scenario=["year", "economy_id", "commodity"],
        value_columns=[REQUIRED_QUANTITY_COLUMN],
        scenario_count=len(expected_scenarios),
        absolute_tolerance=base_year_absolute_tolerance,
    )
    population_consistency = _base_year_consistency(
        driver_input,
        base_year=base_year,
        key_without_scenario=["year", "economy_id"],
        value_columns=["population_million"],
        scenario_count=len(expected_scenarios),
        absolute_tolerance=base_year_absolute_tolerance,
    )

    try:
        postsolve: NutritionPostsolveResult = postsolve_nutrition(
            result_input,
            driver_input,
            coefficients,
            quantity_column=REQUIRED_QUANTITY_COLUMN,
            nonfood_positive_tolerance_mt=nonfood_positive_tolerance_mt,
        )
    except NutritionContractError as exc:
        raise ScenarioNutritionError(str(exc)) from exc
    contribution_columns = [
        *RESULT_KEY,
        REQUIRED_QUANTITY_COLUMN,
        "food_use",
        "source_class",
        *COEFFICIENT_COLUMNS,
        "energy_kcal",
        "protein_g",
        "fat_g",
    ]
    contributions = postsolve.commodity_contributions[contribution_columns].copy()
    contributions = contributions.sort_values(RESULT_KEY).reset_index(drop=True)
    economy = postsolve.economy.sort_values(ACCOUNT_KEY).reset_index(drop=True)
    world = postsolve.world.sort_values(["scenario", "year"]).reset_index(drop=True)
    if any(frame.isna().any().any() for frame in (contributions, economy, world)):
        raise ScenarioNutritionError("scenario nutrition outputs contain NA")

    nonfood = contributions["source_class"].eq("nonfood")
    positive_nonfood = contributions.loc[
        nonfood, REQUIRED_QUANTITY_COLUMN
    ].gt(nonfood_positive_tolerance_mt)
    if positive_nonfood.any():
        raise ScenarioNutritionError("nonfood has positive food demand after postsolve")
    output_consistency = _base_year_consistency(
        economy,
        base_year=base_year,
        key_without_scenario=["year", "economy_id"],
        value_columns=[
            REQUIRED_QUANTITY_COLUMN,
            "energy_kcal",
            "protein_g",
            "fat_g",
            "kcal_per_capita_day",
            "protein_g_per_capita_day",
            "fat_g_per_capita_day",
        ],
        scenario_count=len(expected_scenarios),
        absolute_tolerance=base_year_absolute_tolerance,
    )
    world_consistency = _base_year_consistency(
        world,
        base_year=base_year,
        key_without_scenario=["year", "economy_id"],
        value_columns=[
            REQUIRED_QUANTITY_COLUMN,
            "energy_kcal",
            "protein_g",
            "fat_g",
            "kcal_per_capita_day",
            "protein_g_per_capita_day",
            "fat_g_per_capita_day",
        ],
        scenario_count=len(expected_scenarios),
        absolute_tolerance=base_year_absolute_tolerance,
    )
    conservation = _world_conservation_audit(
        economy, world, relative_tolerance=world_relative_tolerance
    )
    audit: dict[str, Any] = {
        "status": "passed_official_ssp_nutrition_postsolve",
        "interpretation_scope": (
            "model-covered 31-commodity edible food basket, not a complete diet"
        ),
        "quantity_column_used": REQUIRED_QUANTITY_COLUMN,
        "forbidden_quantity_column_used": False,
        "population_column_used": "population_million",
        "grid": grid,
        "expected_result_rows_formula": (
            f"{len(expected_scenarios)} scenarios x {len(expected_years)} years x "
            f"{expected_economy_count} economies x {len(EXPECTED_COMMODITIES)} commodities"
        ),
        "outputs": {
            "economy_row_count": int(len(economy)),
            "world_row_count": int(len(world)),
            "commodity_contribution_row_count": int(len(contributions)),
            "missing_value_count": 0,
        },
        "nonfood": {
            "row_count": int(nonfood.sum()),
            "positive_food_demand_count": int(positive_nonfood.sum()),
            "maximum_food_demand_mt": float(
                contributions.loc[nonfood, REQUIRED_QUANTITY_COLUMN].max()
            ),
            "status": "passed",
        },
        "base_year_consistency": {
            "food_demand": food_consistency,
            "population": population_consistency,
            "economy_nutrition": output_consistency,
            "world_nutrition": world_consistency,
        },
        "world_conservation": conservation,
    }
    return ScenarioNutritionTables(
        economy=economy,
        world=world,
        commodity_contributions=contributions,
        audit=audit,
    )


def _sha256(path: Path, *, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def _project_path(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else PROJECT_ROOT / path


def run_official_scenario_nutrition(
    *,
    config_path: str | Path = PROJECT_ROOT / "config" / "nutrition.yaml",
    write_commodity_contributions: bool | None = None,
) -> tuple[ScenarioNutritionTables, dict[str, Path]]:
    """Read official files, run the strict postsolve, and write audited CSVs."""

    config = load_nutrition_config(config_path)
    settings = _scenario_settings(config)
    inputs = settings["inputs"]
    grid = settings["expected_grid"]
    checks = settings["checks"]
    outputs = settings["outputs"]
    result_path = _project_path(inputs["scenario_results"])
    driver_path = _project_path(inputs["drivers"])
    coefficient_path = _project_path(inputs["coefficients"])
    for path in (result_path, driver_path, coefficient_path):
        if not path.is_file():
            raise ScenarioNutritionError(f"required scenario nutrition input is absent: {path}")

    # Deliberately excludes final_demand_mt from usecols.
    results = pd.read_csv(result_path, usecols=RESULT_COLUMNS)
    drivers = pd.read_csv(driver_path, usecols=DRIVER_COLUMNS)
    coefficients = pd.read_csv(coefficient_path)
    scenarios = [str(value) for value in grid["scenarios"]]
    years = list(range(int(grid["first_year"]), int(grid["last_year"]) + 1))
    tables = build_scenario_nutrition_tables(
        results,
        drivers,
        coefficients,
        expected_scenarios=scenarios,
        expected_years=years,
        expected_economy_count=int(grid["economy_count"]),
        base_year=int(config["benchmark_year"]),
        base_year_absolute_tolerance=float(
            checks["base_year_scenario_absolute_tolerance"]
        ),
        world_relative_tolerance=float(
            checks["world_conservation_relative_tolerance"]
        ),
        nonfood_positive_tolerance_mt=float(
            checks["nonfood_positive_tolerance_mt"]
        ),
    )

    output_paths = {
        "economy_summary": _project_path(outputs["economy_summary"]),
        "world_summary": _project_path(outputs["world_summary"]),
        "commodity_contributions": _project_path(outputs["commodity_contributions"]),
        "audit": _project_path(outputs["audit"]),
    }
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    tables.economy.to_csv(output_paths["economy_summary"], index=False)
    tables.world.to_csv(output_paths["world_summary"], index=False)
    write_contributions = (
        bool(outputs["write_commodity_contributions"])
        if write_commodity_contributions is None
        else bool(write_commodity_contributions)
    )
    if write_contributions:
        tables.commodity_contributions.to_csv(
            output_paths["commodity_contributions"], index=False
        )
    elif output_paths["commodity_contributions"].exists():
        # Never delete a prior material output implicitly.  The audit marks it
        # as not written in this run and omits its digest.
        pass

    audit = dict(tables.audit)
    audit["interpretation_scope"] = str(settings["interpretation_scope"])
    audit["inputs"] = {
        "scenario_results": str(result_path),
        "drivers": str(driver_path),
        "coefficients": str(coefficient_path),
        "sha256": {
            "scenario_results": _sha256(result_path),
            "drivers": _sha256(driver_path),
            "coefficients": _sha256(coefficient_path),
        },
    }
    audit["written_files"] = {
        "economy_summary": str(output_paths["economy_summary"]),
        "world_summary": str(output_paths["world_summary"]),
        "commodity_contributions": (
            str(output_paths["commodity_contributions"])
            if write_contributions else "not_written_this_run"
        ),
        "sha256": {
            "economy_summary": _sha256(output_paths["economy_summary"]),
            "world_summary": _sha256(output_paths["world_summary"]),
            "commodity_contributions": (
                _sha256(output_paths["commodity_contributions"])
                if write_contributions else "not_applicable"
            ),
        },
    }
    output_paths["audit"].write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    final_tables = ScenarioNutritionTables(
        economy=tables.economy,
        world=tables.world,
        commodity_contributions=tables.commodity_contributions,
        audit=audit,
    )
    return final_tables, output_paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "nutrition.yaml",
    )
    parser.add_argument(
        "--no-contributions",
        action="store_true",
        help="write economy/WORLD/audit only; retain contributions in memory",
    )
    args = parser.parse_args()
    tables, paths = run_official_scenario_nutrition(
        config_path=args.config,
        write_commodity_contributions=not args.no_contributions,
    )
    print(
        f"status={tables.audit['status']}; economy_rows={len(tables.economy)}; "
        f"world_rows={len(tables.world)}; "
        f"contribution_rows={len(tables.commodity_contributions)}; "
        f"audit={paths['audit']}"
    )


if __name__ == "__main__":
    main()
