"""Publication-gate validation for the rebuilt CASM-World projections.

Solver convergence is necessary but not sufficient for a publishable central
scenario.  This module applies frozen numerical, price-plausibility and
OECD--FAO holdout gates without changing any model parameter or solution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import yaml

from casm_world.system import build_model_system


class ValidationInputError(ValueError):
    """Raised when a validation input violates its declared data contract."""


def _project_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValidationInputError(f"Path escapes project root: {relative}") from exc
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_validation_config(path: str | Path) -> dict[str, Any]:
    config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValidationInputError("validation.yaml must contain a mapping")
    required = {
        "version", "benchmark_year", "projection_end", "central_scenario",
        "inputs", "outputs", "numerical_gates", "price_plausibility_gates",
        "oecd_fao_holdout",
    }
    missing = required - set(config)
    if missing:
        raise ValidationInputError(f"validation configuration is missing {sorted(missing)}")
    if int(config["benchmark_year"]) != 2023 or int(config["projection_end"]) != 2050:
        raise ValidationInputError("Publication validation is frozen to 2023--2050")
    for section in ("inputs", "outputs"):
        for raw in config[section].values():
            path_value = Path(str(raw))
            if path_value.is_absolute() or ".." in path_value.parts:
                raise ValidationInputError("Validation paths must be project-relative")
    holdout = config["oecd_fao_holdout"]
    if set(holdout["areas"]) != {"W", "CHN", "EU"}:
        raise ValidationInputError("OECD holdout must contain World, China and EU27")
    if len(holdout["commodities"]) != 9:
        raise ValidationInputError("OECD holdout must contain exactly nine products")
    return config


def _pct_change(end: float, start: float) -> float:
    if not np.isfinite(start) or start <= 0:
        raise ValidationInputError("Holdout production levels must be positive and finite")
    return 100.0 * (end / start - 1.0)


def _sign_agrees(left: float, right: float, tolerance: float = 1.0e-10) -> bool:
    left_sign = 0 if abs(left) <= tolerance else int(np.sign(left))
    right_sign = 0 if abs(right) <= tolerance else int(np.sign(right))
    return left_sign == right_sign


def build_oecd_holdout(
    results: pd.DataFrame,
    membership: pd.DataFrame,
    oecd: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    """Return the frozen 27-series SSP2 versus OECD--FAO comparison."""

    required_results = {"scenario", "year", "economy_id", "commodity", "production_mt"}
    required_oecd = {
        "REF_AREA", "COMMODITY", "MEASURE", "UNIT_MEASURE", "VERSION_ID",
        "TIME_PERIOD", "OBS_VALUE",
    }
    if not required_results <= set(results):
        raise ValidationInputError("Scenario results lack holdout columns")
    if not required_oecd <= set(oecd):
        raise ValidationInputError("OECD--FAO extract lacks holdout columns")
    holdout = config["oecd_fao_holdout"]
    central = str(config["central_scenario"])
    start = int(holdout["start_year"])
    end = int(holdout["end_year"])
    area_map = {str(key): str(value) for key, value in holdout["areas"].items()}
    commodity_map = {
        str(key): str(value) for key, value in holdout["commodities"].items()
    }

    selected = oecd[
        oecd["REF_AREA"].isin(area_map)
        & oecd["COMMODITY"].isin(commodity_map)
        & oecd["TIME_PERIOD"].isin([start, end])
    ].copy()
    selected["area_code"] = selected["REF_AREA"].map(area_map)
    selected["commodity"] = selected["COMMODITY"].map(commodity_map)
    expected = len(area_map) * len(commodity_map) * 2
    if len(selected) != expected or selected.duplicated(
        ["area_code", "commodity", "TIME_PERIOD"]
    ).any():
        raise ValidationInputError("OECD--FAO holdout is not a complete 3x9x2 grid")
    if not selected["MEASURE"].eq("QP").all() or not selected["UNIT_MEASURE"].eq("T").all():
        raise ValidationInputError("OECD--FAO holdout must be production in tonnes")

    eu_accounts = set(
        membership.loc[
            membership["group_system"].eq("ECONOMIC")
            & membership["group_code"].eq("EU27"),
            "model_account_id",
        ].astype(str)
    )
    if len(eu_accounts) != 27:
        raise ValidationInputError(f"EU27 membership has {len(eu_accounts)} accounts")

    central_results = results[
        results["scenario"].eq(central)
        & results["year"].isin([start, end])
    ]
    rows: list[dict[str, Any]] = []
    for area_external, area_internal in area_map.items():
        for product_external, product_internal in commodity_map.items():
            ext = selected[
                selected["REF_AREA"].eq(area_external)
                & selected["COMMODITY"].eq(product_external)
            ].set_index("TIME_PERIOD")
            external_change = _pct_change(
                float(ext.at[end, "OBS_VALUE"]), float(ext.at[start, "OBS_VALUE"])
            )
            model = central_results[central_results["commodity"].eq(product_internal)]
            if area_internal == "CHN":
                model = model[model["economy_id"].eq("CHN")]
            elif area_internal == "EU27":
                model = model[model["economy_id"].isin(eu_accounts)]
            model_levels = model.groupby("year")["production_mt"].sum()
            if set(model_levels.index) != {start, end}:
                raise ValidationInputError(
                    f"CASM holdout is incomplete for {area_internal}/{product_internal}"
                )
            model_change = _pct_change(float(model_levels.at[end]), float(model_levels.at[start]))
            error = model_change - external_change
            rows.append(
                {
                    "area_external": area_external,
                    "area": area_internal,
                    "commodity_external": product_external,
                    "commodity": product_internal,
                    "start_year": start,
                    "end_year": end,
                    "oecd_fao_change_percent": external_change,
                    "casm_world_ssp2_change_percent": model_change,
                    "error_percentage_points": error,
                    "absolute_error_percentage_points": abs(error),
                    "sign_agreement": _sign_agrees(model_change, external_change),
                    "oecd_version": str(ext["VERSION_ID"].iloc[0]),
                }
            )
    comparison = pd.DataFrame.from_records(rows).sort_values(
        ["area_external", "commodity"]
    ).reset_index(drop=True)
    if len(comparison) != 27:
        raise AssertionError("OECD holdout must contain 27 comparisons")
    return comparison


def oecd_holdout_metrics(comparison: pd.DataFrame) -> dict[str, Any]:
    world = comparison[comparison["area_external"].eq("W")]
    metrics: dict[str, Any] = {
        "comparison_count": int(len(comparison)),
        "sign_agreement_share": float(comparison["sign_agreement"].mean()),
        "median_absolute_error_percentage_points": float(
            comparison["absolute_error_percentage_points"].median()
        ),
        "p90_absolute_error_percentage_points": float(
            comparison["absolute_error_percentage_points"].quantile(0.90)
        ),
        "world_mean_absolute_error_percentage_points": float(
            world["absolute_error_percentage_points"].mean()
        ),
        "world_sign_agreement_count": int(world["sign_agreement"].sum()),
        "world_comparison_count": int(len(world)),
    }
    metrics["by_area"] = {
        str(area): {
            "comparison_count": int(len(frame)),
            "sign_agreement_share": float(frame["sign_agreement"].mean()),
            "mean_absolute_error_percentage_points": float(
                frame["absolute_error_percentage_points"].mean()
            ),
            "median_absolute_error_percentage_points": float(
                frame["absolute_error_percentage_points"].median()
            ),
            "p90_absolute_error_percentage_points": float(
                frame["absolute_error_percentage_points"].quantile(0.90)
            ),
        }
        for area, frame in comparison.groupby("area_external", sort=True)
    }
    return metrics


def _gate(
    rows: list[dict[str, Any]],
    gate_id: str,
    description: str,
    value: float | int | bool,
    criterion: str,
    passed: bool,
) -> None:
    rows.append(
        {
            "gate_id": gate_id,
            "description": description,
            "value": value,
            "criterion": criterion,
            "passed": bool(passed),
        }
    )


def evaluate_publication_gates(
    results: pd.DataFrame,
    prices: pd.DataFrame,
    processes: pd.DataFrame,
    convergence: pd.DataFrame,
    benchmark: pd.DataFrame,
    benchmark_activities: pd.DataFrame,
    commodity_config: Mapping[str, Any],
    oecd_metrics: Mapping[str, float | int],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    """Evaluate frozen gates and return one auditable row per test."""

    required_result = {
        "scenario", "year", "economy_id", "commodity", "world_price_index_2023",
        "primary_supply_mt", "processing_supply_mt", "production_mt",
        "final_demand_mt", "food_demand_mt", "processing_demand_mt", "demand_mt",
        "net_import_mt",
    }
    if not required_result <= set(results):
        raise ValidationInputError("Scenario result columns are incomplete")
    key = ["scenario", "year", "economy_id", "commodity"]
    if results.duplicated(key).any():
        raise ValidationInputError("Scenario result keys are not unique")
    scenarios = sorted(results["scenario"].astype(str).unique())
    years = sorted(results["year"].astype(int).unique())
    economies = sorted(results["economy_id"].astype(str).unique())
    products = sorted(results["commodity"].astype(str).unique())
    expected_rows = len(scenarios) * len(years) * len(economies) * len(products)
    complete_grid = (
        len(results) == expected_rows
        and years == list(range(int(config["benchmark_year"]), int(config["projection_end"]) + 1))
        and set(scenarios) == {"SSP1", "SSP2", "SSP3", "SSP4", "SSP5"}
    )

    numerical = config["numerical_gates"]
    price_gate = config["price_plausibility_gates"]
    holdout_gate = config["oecd_fao_holdout"]
    rows: list[dict[str, Any]] = []
    _gate(rows, "complete_grid", "Complete SSP1--SSP5 annual result grid", len(results),
          f"equals {expected_rows}", complete_grid)

    numeric_columns = sorted(required_result - set(key))
    finite = np.isfinite(results[numeric_columns].to_numpy(float)).all()
    _gate(rows, "finite_results", "No NA or non-finite solved values", bool(finite),
          "true", bool(finite))
    nonnegative_columns = [
        "world_price_index_2023", "primary_supply_mt", "processing_supply_mt",
        "production_mt", "final_demand_mt", "food_demand_mt",
        "processing_demand_mt", "demand_mt",
    ]
    minimum = float(results[nonnegative_columns].min().min())
    nonnegative_tolerance = float(numerical["nonnegative_tolerance"])
    _gate(rows, "nonnegative_quantities", "No materially negative price or quantity",
          minimum, f">= {-nonnegative_tolerance}", minimum >= -nonnegative_tolerance)

    base = results[results["year"].eq(int(config["benchmark_year"]))]
    base_price_error = float((base["world_price_index_2023"] - 1.0).abs().max())
    base_price_tolerance = float(numerical["base_price_absolute_tolerance"])
    _gate(rows, "base_prices", "Every 2023 world price index equals one", base_price_error,
          f"<= {base_price_tolerance}", base_price_error <= base_price_tolerance)

    base_model = base.merge(
        benchmark[
            ["economy_id", "commodity", "supply_2023", "final_demand_2023",
             "processing_demand_2023", "demand_2023", "net_import_2023"]
        ],
        on=["economy_id", "commodity"], how="left", validate="many_to_one",
    )
    if base_model[["supply_2023", "final_demand_2023", "processing_demand_2023"]].isna().any().any():
        raise ValidationInputError("2023 benchmark does not cover every result key")
    base_quantity_error = max(
        # The balanced supply column is the total market output.  For an
        # explicitly processed product it is carried by processing_supply_mt,
        # whereas raw biological products are carried by primary_supply_mt.
        float((base_model["production_mt"] - base_model["supply_2023"]).abs().max()),
        float((base_model["final_demand_mt"] - base_model["final_demand_2023"]).abs().max()),
        float((base_model["processing_demand_mt"] - base_model["processing_demand_2023"]).abs().max()),
        float((base_model["demand_mt"] - base_model["demand_2023"]).abs().max()),
        float((base_model["net_import_mt"] - base_model["net_import_2023"]).abs().max()),
    )
    base_quantity_tolerance = float(numerical["base_quantity_absolute_tolerance_mt"])
    _gate(rows, "base_quantities", "Every 2023 scenario reproduces balanced quantities",
          base_quantity_error, f"<= {base_quantity_tolerance} Mt",
          base_quantity_error <= base_quantity_tolerance)

    system = build_model_system(benchmark, benchmark_activities, dict(commodity_config))
    expected_process = pd.concat(
        [
            pd.DataFrame(
                {
                    "economy_id": system.regions,
                    "process": process.name,
                    "balanced_activity_2023": process.base_activity,
                }
            )
            for process in system.processes
        ],
        ignore_index=True,
    )
    base_processes = processes[processes["year"].eq(int(config["benchmark_year"]))]
    base_processes = base_processes.merge(
        expected_process, on=["economy_id", "process"], how="left",
        validate="many_to_one",
    )
    if base_processes["balanced_activity_2023"].isna().any():
        raise ValidationInputError("2023 process output contains an unknown activity")
    process_error = float(
        (base_processes["activity"] - base_processes["balanced_activity_2023"]).abs().max()
    )
    process_tolerance = float(
        numerical["base_process_activity_absolute_tolerance"]
    )
    _gate(rows, "base_process_activities", "Every 2023 process activity reproduces its base",
          process_error, f"<= {process_tolerance}", process_error <= process_tolerance)

    market_residual = float(convergence["maximum_market_relative_residual"].abs().max())
    market_tolerance = float(numerical["market_relative_residual_tolerance"])
    _gate(rows, "market_identity", "All annual world markets clear", market_residual,
          f"<= {market_tolerance}", market_residual <= market_tolerance)
    accounting_residual = float(
        convergence["maximum_accounting_absolute_residual_mt"].abs().max()
    )
    accounting_tolerance = float(
        numerical["accounting_absolute_residual_tolerance_mt"]
    )
    _gate(rows, "accounting_identity", "All country-product accounting identities hold",
          accounting_residual, f"<= {accounting_tolerance} Mt",
          accounting_residual <= accounting_tolerance)
    converged = bool(
        convergence["converged"].astype(bool).all()
        and convergence["accounting_passed"].astype(bool).all()
    )
    _gate(rows, "solver_status", "Every annual solution reports convergence", converged,
          "true", converged)

    price_key = ["scenario", "year", "commodity"]
    if prices.duplicated(price_key).any():
        raise ValidationInputError("World-price keys are not unique")
    p2050 = prices[prices["year"].eq(int(config["projection_end"]))][
        "world_price_index_2023"
    ].astype(float)
    pmin = float(p2050.min())
    pmax = float(p2050.max())
    price_lower = float(price_gate["all_2050_price_lower"])
    price_upper = float(price_gate["all_2050_price_upper"])
    _gate(rows, "price_range_2050", "Every 2050 world price is in the broad band",
          min(pmin / price_lower, price_upper / pmax),
          f"all in [{price_lower}, {price_upper}]",
          pmin >= price_lower and pmax <= price_upper)
    band_lower = float(price_gate["central_band_lower"])
    band_upper = float(price_gate["central_band_upper"])
    share_in_band = float(p2050.between(band_lower, band_upper, inclusive="both").mean())
    minimum_share = float(price_gate["minimum_share_in_central_band"])
    _gate(rows, "price_central_band_2050", "Share of 2050 prices in central band",
          share_in_band, f">= {minimum_share}", share_in_band >= minimum_share)
    ordered = prices.sort_values(["scenario", "commodity", "year"]).copy()
    ordered["absolute_log_change"] = ordered.groupby(
        ["scenario", "commodity"]
    )["world_price_index_2023"].transform(lambda values: np.log(values).diff().abs())
    maximum_log_change = float(ordered["absolute_log_change"].max())
    maximum_allowed_log_change = float(price_gate["maximum_annual_absolute_log_change"])
    _gate(rows, "annual_price_change", "Maximum annual absolute log-price change",
          maximum_log_change, f"<= {maximum_allowed_log_change}",
          maximum_log_change <= maximum_allowed_log_change)
    essential_products = set(map(str, price_gate["essential_food_products"]))
    if not essential_products <= set(prices["commodity"].astype(str)):
        raise ValidationInputError("Essential-food price gate contains an unknown product")
    essential = prices[
        prices["year"].eq(int(config["projection_end"]))
        & prices["commodity"].isin(essential_products)
    ]["world_price_index_2023"].astype(float)
    essential_lower = float(price_gate["essential_food_price_lower"])
    essential_upper = float(price_gate["essential_food_price_upper"])
    essential_passed = bool(
        essential.min() >= essential_lower and essential.max() <= essential_upper
    )
    _gate(rows, "essential_food_prices_2050",
          "Every SSP essential-food 2050 price is in its declared band",
          int(essential.between(essential_lower, essential_upper, inclusive="both").sum()),
          f"all {len(essential)} in [{essential_lower}, {essential_upper}]",
          essential_passed)

    sign_share = float(oecd_metrics["sign_agreement_share"])
    min_sign_share = float(holdout_gate["minimum_full_sign_agreement"])
    _gate(rows, "oecd_full_sign", "OECD holdout full-sample sign agreement", sign_share,
          f">= {min_sign_share}", sign_share >= min_sign_share)
    median_error = float(oecd_metrics["median_absolute_error_percentage_points"])
    max_median = float(holdout_gate["maximum_full_median_absolute_error_pp"])
    _gate(rows, "oecd_full_median", "OECD holdout median absolute error", median_error,
          f"<= {max_median} percentage points", median_error <= max_median)
    p90_error = float(oecd_metrics["p90_absolute_error_percentage_points"])
    max_p90 = float(holdout_gate["maximum_full_p90_absolute_error_pp"])
    _gate(rows, "oecd_full_p90", "OECD holdout p90 absolute error", p90_error,
          f"<= {max_p90} percentage points", p90_error <= max_p90)
    world_mae = float(oecd_metrics["world_mean_absolute_error_percentage_points"])
    max_world_mae = float(holdout_gate["maximum_world_mean_absolute_error_pp"])
    _gate(rows, "oecd_world_mae", "OECD holdout World mean absolute error", world_mae,
          f"<= {max_world_mae} percentage points", world_mae <= max_world_mae)
    world_signs = int(oecd_metrics["world_sign_agreement_count"])
    min_world_signs = int(holdout_gate["minimum_world_sign_agreement_count"])
    _gate(rows, "oecd_world_sign", "OECD holdout World sign agreements", world_signs,
          f">= {min_world_signs} of 9", world_signs >= min_world_signs)
    return pd.DataFrame.from_records(rows)


def run_publication_validation(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    config = load_validation_config(root / "config/validation.yaml")
    paths = {
        key: _project_path(root, value) for key, value in config["inputs"].items()
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise ValidationInputError(f"Validation inputs are missing: {missing}")
    results = pd.read_csv(paths["results"])
    prices = pd.read_csv(paths["prices"])
    processes = pd.read_csv(paths["processes"])
    convergence = pd.read_csv(paths["convergence"])
    benchmark = pd.read_csv(paths["benchmark"])
    benchmark_activities = pd.read_csv(paths["benchmark_activities"])
    commodity_config = yaml.safe_load(paths["commodity_config"].read_text(encoding="utf-8"))
    run_report = json.loads(paths["run_report"].read_text(encoding="utf-8"))
    parameter_report = json.loads(
        paths["parameter_report"].read_text(encoding="utf-8")
    )
    membership = pd.read_csv(paths["model_membership"])
    oecd = pd.read_csv(paths["oecd_fao"])
    comparison = build_oecd_holdout(results, membership, oecd, config)
    metrics = oecd_holdout_metrics(comparison)
    gates = evaluate_publication_gates(
        results, prices, processes, convergence, benchmark, benchmark_activities,
        commodity_config, metrics, config
    )
    provenance_rows: list[dict[str, Any]] = []
    parameter_contract_passed = bool(
        parameter_report.get("status") == "passed"
        and parameter_report.get("parameter_set") == "CASM_WORLD_ELASTICITIES_V2"
        and parameter_report.get("parameter_row_count") == 5983
        and parameter_report.get("missing_parameter_count") == 0
        and len(parameter_report.get("response_set_sha256", {})) == 3
    )
    _gate(
        provenance_rows,
        "parameter_contract",
        "V2 parameter report covers central, low and high response sets",
        parameter_contract_passed,
        "passed V2 report, 5,983 rows, zero missing, three response hashes",
        parameter_contract_passed,
    )
    run_provenance_passed = bool(
        run_report.get("status") == "passed"
        and run_report.get("parameter_set") == "CASM_WORLD_ELASTICITIES_V2"
        and run_report.get("parameter_table_sha256") == _sha256(paths["parameter_table"])
        and run_report.get("simulation_config_sha256") == _sha256(paths["simulation_config"])
        and run_report.get("annual_solution_count") == 140
        and run_report.get("result_row_count") == 837620
    )
    _gate(
        provenance_rows,
        "simulation_provenance",
        "Formal results match the frozen V2 parameter table and simulation config",
        run_provenance_passed,
        "matching SHA256 and complete 140-solution run",
        run_provenance_passed,
    )
    gates = pd.concat([gates, pd.DataFrame.from_records(provenance_rows)], ignore_index=True)
    passed = bool(gates["passed"].all())
    price_gate = config["price_plausibility_gates"]
    prices_2050 = prices[prices["year"].eq(int(config["projection_end"]))].copy()
    central_lower = float(price_gate["central_band_lower"])
    central_upper = float(price_gate["central_band_upper"])
    central_outliers = prices_2050.loc[
        ~prices_2050["world_price_index_2023"].between(
            central_lower, central_upper, inclusive="both"
        ),
        ["scenario", "commodity", "world_price_index_2023"],
    ].sort_values(["scenario", "commodity"])
    price_metrics = {
        "minimum_2050_world_price_index": float(
            prices_2050["world_price_index_2023"].min()
        ),
        "maximum_2050_world_price_index": float(
            prices_2050["world_price_index_2023"].max()
        ),
        "share_2050_prices_in_central_band": float(
            prices_2050["world_price_index_2023"]
            .between(central_lower, central_upper, inclusive="both")
            .mean()
        ),
        "central_band": [central_lower, central_upper],
        "central_band_outlier_count": int(len(central_outliers)),
        "central_band_outliers": central_outliers.to_dict("records"),
    }
    output_paths = {
        key: _project_path(root, value) for key, value in config["outputs"].items()
    }
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    gates.to_csv(output_paths["gate_table"], index=False)
    comparison.to_csv(output_paths["oecd_comparison"], index=False)
    report = {
        "status": "publication_gate_passed" if passed else "diagnostic_only_gate_failed",
        "publication_baseline": passed,
        "gate_count": int(len(gates)),
        "passed_gate_count": int(gates["passed"].sum()),
        "failed_gates": gates.loc[~gates["passed"], "gate_id"].astype(str).tolist(),
        "price_plausibility_metrics": price_metrics,
        "oecd_fao_holdout_metrics": metrics,
        "input_sha256": {key: _sha256(path) for key, path in paths.items()},
        "outputs": {
            "gate_table": str(output_paths["gate_table"]),
            "oecd_comparison": str(output_paths["oecd_comparison"]),
        },
    }
    output_paths["report"].write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--require-passed", action="store_true")
    args = parser.parse_args()
    report = run_publication_validation(args.project_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.require_passed and not report["publication_baseline"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
