"""Audited SSP aggregation for the CASM-World paper outputs.

Solved quantities remain keyed to the 193 model accounts.  Account-basis
groups (World, China, USA, EU27, World Bank income classes and the operational
developing-economy group) are summed directly.  UN geography and UN special
groups use original source geography: a model account is split with fixed
2023 physical-quantity shares before aggregation.  The split is a reporting
bridge only; it never creates an additional model account or feeds back into
the equilibrium solution.
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from casm_world.balancing import _raw_anchors
from casm_world.geography import (
    territory_crosswalk,
    validate_territory_config,
)
from casm_world.paths import load_source_catalog, verify_source
from casm_world.reporting import (
    SOURCE_GROUP_SYSTEMS,
    _required_m49_table,
    account_coverage_report,
    aggregate_model_account_values,
    aggregate_source_geography_values,
    build_model_account_membership,
    build_source_geography,
    build_source_geography_membership,
    load_reporting_config,
    load_world_bank_income_groups,
)


DIMENSION_COLUMNS = ("scenario", "year", "commodity")
SOURCE_ID = "source_economy_id"
TARGET_ID = "accounting_target"
MODEL_ID = "economy_id"
WB_INCOME_SYSTEM = "WB_INCOME_FY25"


class AnalysisInputError(ValueError):
    """Raised when a formal reporting input fails an explicit contract."""


def load_analysis_config(path: str | Path) -> dict[str, Any]:
    """Load and validate the scenario-analysis configuration."""

    config_path = Path(path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise AnalysisInputError("analysis.yaml must contain a mapping")
    required = {
        "schema_version",
        "benchmark_year",
        "end_year",
        "inputs",
        "outputs",
        "source_geography_allocation",
        "un_special_groups",
        "developing_economies",
        "quantity_columns",
        "summary",
        "coverage_gate",
    }
    missing = required - set(config)
    if missing:
        raise AnalysisInputError(f"Analysis configuration is missing: {sorted(missing)}")
    if str(config["schema_version"]) != "1.0":
        raise AnalysisInputError("analysis.yaml schema_version must be 1.0")
    if int(config["benchmark_year"]) != 2023 or int(config["end_year"]) != 2050:
        raise AnalysisInputError("Formal analysis years must be 2023 and 2050")

    inputs = config["inputs"]
    outputs = config["outputs"]
    if not isinstance(inputs, Mapping) or not isinstance(outputs, Mapping):
        raise AnalysisInputError("inputs and outputs must be mappings")
    expected_inputs = {
        "scenario_results",
        "balanced_benchmark",
        "source_observations",
        "reporting_config",
        "territory_config",
        "commodity_config",
        "balancing_config",
        "data_source_config",
    }
    expected_outputs = {
        "group_results",
        "change_summary",
        "coverage_report",
        "model_membership",
        "source_membership",
        "source_allocation_weights",
    }
    if set(inputs) != expected_inputs or set(outputs) != expected_outputs:
        raise AnalysisInputError("Unexpected analysis input/output path keys")
    for section in (inputs, outputs):
        for raw_path in section.values():
            candidate = Path(str(raw_path))
            if candidate.is_absolute() or ".." in candidate.parts:
                raise AnalysisInputError("Analysis paths must be project-relative without '..'")

    special = config["un_special_groups"]
    if set(special.get("groups", {})) != {"LDC", "LLDC", "SIDS", "PACIFIC_ISLANDS"}:
        raise AnalysisInputError("UN special groups must be LDC/LLDC/SIDS/PACIFIC_ISLANDS")
    expected_counts = {
        "LDC": 44,
        "LLDC": 32,
        "SIDS": 53,
        "PACIFIC_ISLANDS": 23,
    }
    for code, count in expected_counts.items():
        if int(special["groups"][code].get("expected_source_count", -1)) != count:
            raise AnalysisInputError(f"Unexpected frozen {code} source count")
    pacific = {
        str(value).zfill(3)
        for value in special["groups"]["PACIFIC_ISLANDS"].get("subregion_codes", [])
    }
    if pacific != {"054", "057", "061"}:
        raise AnalysisInputError("Pacific Islands must use Melanesia/Micronesia/Polynesia")

    developing = config["developing_economies"]
    if set(developing.get("included_wb_income_codes", [])) != {"LIC", "LMC", "UMC"}:
        raise AnalysisInputError("Developing economies must be World Bank LIC/LMC/UMC")
    quantities = config["quantity_columns"]
    required_quantities = {
        "primary_supply_mt",
        "processing_supply_mt",
        "production_mt",
        "food_demand_mt",
        "final_demand_mt",
        "processing_demand_mt",
        "demand_mt",
        "net_import_mt",
    }
    if set(quantities.get("required", [])) != required_quantities:
        raise AnalysisInputError("Unexpected required solved-quantity columns")
    return config


def _project_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise AnalysisInputError(f"Path escapes project root: {relative}") from exc
    return path


def build_un_special_membership(
    un_m49_html: str | Path,
    source_geography: pd.DataFrame,
    analysis_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Build LDC, LLDC, SIDS and Pacific-Islands source memberships.

    LDC/LLDC/SIDS flags come directly from the frozen English M49 table.
    Pacific Islands is the transparent union of the three UN Oceania island
    subregions and therefore excludes Australia and New Zealand.
    """

    required_geo = {SOURCE_ID, TARGET_ID, "subregion_code"}
    if not required_geo <= set(source_geography):
        raise AnalysisInputError(
            f"Source geography is missing: {sorted(required_geo-set(source_geography))}"
        )
    if source_geography[SOURCE_ID].duplicated().any():
        raise AnalysisInputError("Source geography identifiers must be unique")
    special = analysis_config["un_special_groups"]
    table = _required_m49_table(Path(un_m49_html))
    iso = table["ISO-alpha3 Code"].astype("string").str.strip().str.upper()
    rows: list[dict[str, Any]] = []
    geography_target = source_geography.set_index(SOURCE_ID)[TARGET_ID]

    for code in ("LDC", "LLDC", "SIDS"):
        definition = special["groups"][code]
        source_column = definition["source_column"]
        if source_column not in table:
            raise AnalysisInputError(f"UN M49 table lacks {source_column!r}")
        flag = table[source_column].astype("string").str.strip().str.casefold().eq("x")
        members = sorted(iso.loc[flag].dropna().astype(str))
        expected = int(definition["expected_source_count"])
        if len(members) != expected:
            raise AnalysisInputError(
                f"Frozen {code} membership changed: expected {expected}, found {len(members)}"
            )
        missing_geo = set(members) - set(geography_target.index)
        if missing_geo:
            raise AnalysisInputError(f"{code} members lack source geography: {sorted(missing_geo)}")
        for member in members:
            rows.append(
                {
                    "membership_layer": "source_geography",
                    "group_system": special["group_system"],
                    "group_code": code,
                    "group_name": definition["group_name"],
                    SOURCE_ID: member,
                    TARGET_ID: geography_target.at[member],
                }
            )

    pacific_definition = special["groups"]["PACIFIC_ISLANDS"]
    pacific_codes = {
        str(value).zfill(3) for value in pacific_definition["subregion_codes"]
    }
    pacific = source_geography[
        source_geography["subregion_code"].astype(str).str.zfill(3).isin(pacific_codes)
    ]
    if len(pacific) != int(pacific_definition["expected_source_count"]):
        raise AnalysisInputError("Frozen Pacific-Islands membership count changed")
    for record in pacific[[SOURCE_ID, TARGET_ID]].to_dict("records"):
        rows.append(
            {
                "membership_layer": "source_geography",
                "group_system": special["group_system"],
                "group_code": "PACIFIC_ISLANDS",
                "group_name": pacific_definition["group_name"],
                SOURCE_ID: record[SOURCE_ID],
                TARGET_ID: record[TARGET_ID],
            }
        )

    membership = pd.DataFrame(rows)
    if membership.duplicated(["group_code", SOURCE_ID]).any():
        raise AssertionError("Duplicate UN special-group membership")
    return membership.sort_values(["group_code", SOURCE_ID]).reset_index(drop=True)


def build_developing_membership(
    model_membership: pd.DataFrame,
    analysis_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Select World Bank LIC/LMC/UMC accounts as developing economies."""

    required = {"group_system", "group_code", "model_account_id"}
    if not required <= set(model_membership):
        raise AnalysisInputError(
            f"Model membership is missing: {sorted(required-set(model_membership))}"
        )
    definition = analysis_config["developing_economies"]
    included = set(definition["included_wb_income_codes"])
    income = model_membership[
        model_membership["group_system"].eq(WB_INCOME_SYSTEM)
        & model_membership["group_code"].isin(included)
    ]
    rows = pd.DataFrame(
        {
            "membership_layer": "model_account",
            "group_system": definition["group_system"],
            "group_code": definition["group_code"],
            "group_name": definition["group_name"],
            "model_account_id": sorted(income["model_account_id"].unique()),
        }
    )
    if rows.empty or rows["model_account_id"].duplicated().any():
        raise AnalysisInputError("Developing-economy membership is empty or duplicated")
    return rows


def _normalised_weight(
    frame: pd.DataFrame,
    primary: str,
    fallbacks: Sequence[str],
    *,
    label: str,
) -> tuple[pd.Series, pd.Series]:
    """Normalize one anchor with audited fallbacks within target/product."""

    keys = [TARGET_ID, "commodity"]
    selected = frame[primary].clip(lower=0.0).astype(float).copy()
    method = pd.Series(primary, index=frame.index, dtype="object")
    total = selected.groupby([frame[key] for key in keys]).transform("sum")
    unresolved = total.le(0.0)
    for fallback in fallbacks:
        candidate = frame[fallback].clip(lower=0.0).astype(float)
        candidate_total = candidate.groupby([frame[key] for key in keys]).transform("sum")
        use = unresolved & candidate_total.gt(0.0)
        selected.loc[use] = candidate.loc[use]
        total.loc[use] = candidate_total.loc[use]
        method.loc[use] = f"fallback_{fallback}"
        unresolved = total.le(0.0)
    if unresolved.any():
        principal = unresolved & frame["principal_source"].astype(bool)
        selected.loc[unresolved] = principal.loc[unresolved].astype(float)
        total.loc[unresolved] = 1.0
        method.loc[unresolved] = "fallback_principal_source"
    weights = selected / total
    if not np.isfinite(weights).all() or (weights < 0.0).any():
        raise AssertionError(f"Invalid {label} allocation weights")
    # Each method is a target/product property, not a source-specific fact.
    method_count = method.groupby([frame[key] for key in keys]).transform("nunique")
    if method_count.ne(1).any():
        raise AssertionError(f"Inconsistent {label} fallback method within a slice")
    return weights.astype(float), method


def build_source_allocation_weights(
    model_accounts: Iterable[str],
    source_observations: pd.DataFrame,
    balanced_benchmark: pd.DataFrame,
    source_geography: pd.DataFrame,
    territory_config: Mapping[str, Any],
    commodity_codes: Sequence[str],
    *,
    ddg_ratio: float,
    food_commodities: Iterable[str],
    weight_sum_tolerance: float = 1.0e-12,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create the fixed-2023 source-geography allocation bridge."""

    validate_territory_config(territory_config)
    accounts = sorted({str(value).strip().upper() for value in model_accounts})
    commodities = [str(value).strip().upper() for value in commodity_codes]
    if not accounts or len(commodities) != len(set(commodities)):
        raise AnalysisInputError("Model accounts/commodities are empty or duplicated")
    territory_sources = set(territory_crosswalk(territory_config)[SOURCE_ID])
    surviving = set(accounts) & territory_sources
    if surviving:
        raise AnalysisInputError(f"Territory sources survived as model accounts: {sorted(surviving)}")

    geography = source_geography.copy()
    geography[SOURCE_ID] = geography[SOURCE_ID].astype(str).str.upper()
    geography[TARGET_ID] = geography[TARGET_ID].astype(str).str.upper()
    is_identity = geography[SOURCE_ID].eq(geography[TARGET_ID])
    is_mapped = geography.get("territory_aggregation_source", False)
    bridge = geography[
        geography[TARGET_ID].isin(accounts) & (is_identity | pd.Series(is_mapped, index=geography.index).astype(bool))
    ][[SOURCE_ID, TARGET_ID, "territory_aggregation_source"]].copy()
    missing_targets = set(accounts) - set(bridge[TARGET_ID])
    if missing_targets:
        raise AnalysisInputError(f"Model accounts lack a source-geography bridge: {sorted(missing_targets)}")
    if bridge[SOURCE_ID].duplicated().any():
        raise AnalysisInputError("A source geography maps to multiple model accounts")

    # The identity source is principal where it exists.  The sole synthetic
    # account OTHER_EASTERN_ASIA instead has TWN as its configured source.
    bridge["principal_source"] = bridge[SOURCE_ID].eq(bridge[TARGET_ID])
    principal_count = bridge.groupby(TARGET_ID)["principal_source"].transform("sum")
    no_identity_targets = set(bridge.loc[principal_count.eq(0), TARGET_ID])
    for target in no_identity_targets:
        candidates = bridge.index[bridge[TARGET_ID].eq(target)]
        if len(candidates) != 1:
            raise AnalysisInputError(
                f"Synthetic account {target} must have exactly one principal source"
            )
        bridge.loc[candidates[0], "principal_source"] = True
    if not bridge.groupby(TARGET_ID)["principal_source"].sum().eq(1).all():
        raise AssertionError("Each model account must have exactly one principal source")

    source_accounts = sorted(bridge[SOURCE_ID].unique())
    anchors, _ = _raw_anchors(
        source_observations,
        source_accounts,
        commodities,
        ddg_ratio=float(ddg_ratio),
        food_commodities=frozenset(str(value).strip().upper() for value in food_commodities),
    )
    anchors = anchors.rename(
        columns={
            MODEL_ID: SOURCE_ID,
            "source_supply": "source_supply_anchor_mt",
            "source_final_demand": "source_final_demand_anchor_mt",
            "source_food_demand": "source_food_demand_anchor_mt",
            "source_other_final_demand": "source_other_final_demand_anchor_mt",
        }
    )
    processing = source_observations[
        source_observations["role"].eq("balance")
        & source_observations["unit"].eq("Mt")
        & source_observations["account"].eq("processing")
    ][[MODEL_ID, "commodity", "value"]].copy()
    processing["value"] = pd.to_numeric(processing["value"], errors="coerce")
    if processing["value"].isna().any() or not np.isfinite(processing["value"]).all():
        raise AnalysisInputError("Source processing anchors are non-finite")
    processing = (
        processing.groupby([MODEL_ID, "commodity"], as_index=False)["value"]
        .sum()
        .rename(columns={MODEL_ID: SOURCE_ID, "value": "source_processing_anchor_mt"})
    )

    full = pd.MultiIndex.from_product(
        [bridge[SOURCE_ID], commodities], names=[SOURCE_ID, "commodity"]
    ).to_frame(index=False)
    full = full.merge(bridge, on=SOURCE_ID, how="left", validate="many_to_one")
    full = full.merge(anchors, on=[SOURCE_ID, "commodity"], how="left", validate="one_to_one")
    full = full.merge(processing, on=[SOURCE_ID, "commodity"], how="left", validate="one_to_one")
    anchor_columns = [
        "source_supply_anchor_mt",
        "source_final_demand_anchor_mt",
        "source_food_demand_anchor_mt",
        "source_other_final_demand_anchor_mt",
        "source_processing_anchor_mt",
    ]
    full[anchor_columns] = full[anchor_columns].fillna(0.0).clip(lower=0.0)

    full["supply_weight"], full["supply_weight_method"] = _normalised_weight(
        full,
        "source_supply_anchor_mt",
        ["source_final_demand_anchor_mt"],
        label="supply",
    )
    full["final_demand_weight"], full["final_demand_weight_method"] = _normalised_weight(
        full,
        "source_final_demand_anchor_mt",
        ["source_supply_anchor_mt"],
        label="final demand",
    )
    full["food_demand_weight"], full["food_demand_weight_method"] = _normalised_weight(
        full,
        "source_food_demand_anchor_mt",
        ["source_final_demand_anchor_mt", "source_supply_anchor_mt"],
        label="food demand",
    )
    full["other_final_demand_weight"], full["other_final_demand_weight_method"] = _normalised_weight(
        full,
        "source_other_final_demand_anchor_mt",
        ["source_final_demand_anchor_mt", "source_supply_anchor_mt"],
        label="other final demand",
    )
    full["processing_weight"], full["processing_weight_method"] = _normalised_weight(
        full,
        "source_processing_anchor_mt",
        ["source_supply_anchor_mt", "source_final_demand_anchor_mt"],
        label="processing",
    )

    weight_columns = [
        "supply_weight",
        "food_demand_weight",
        "other_final_demand_weight",
        "final_demand_weight",
        "processing_weight",
    ]
    weight_sums = full.groupby([TARGET_ID, "commodity"])[weight_columns].sum()
    maximum_weight_error = float((weight_sums - 1.0).abs().to_numpy().max(initial=0.0))
    if maximum_weight_error > float(weight_sum_tolerance):
        raise AssertionError(f"Source allocation weights do not sum to one: {maximum_weight_error}")

    benchmark_required = {
        MODEL_ID,
        "commodity",
        "source_supply_2023",
        "source_final_demand_2023",
        "source_food_demand_2023",
        "source_other_final_demand_2023",
    }
    if not benchmark_required <= set(balanced_benchmark):
        raise AnalysisInputError(
            f"Balanced benchmark is missing: {sorted(benchmark_required-set(balanced_benchmark))}"
        )
    reconstructed = (
        full.groupby([TARGET_ID, "commodity"], as_index=False)[
            [
                "source_supply_anchor_mt",
                "source_food_demand_anchor_mt",
                "source_other_final_demand_anchor_mt",
                "source_final_demand_anchor_mt",
            ]
        ]
        .sum()
        .rename(columns={TARGET_ID: MODEL_ID})
    )
    comparison = balanced_benchmark[
        [
            MODEL_ID,
            "commodity",
            "source_supply_2023",
            "source_food_demand_2023",
            "source_other_final_demand_2023",
            "source_final_demand_2023",
        ]
    ].merge(reconstructed, on=[MODEL_ID, "commodity"], how="left", validate="one_to_one")
    if comparison.isna().any().any():
        raise AnalysisInputError("Source anchors do not cover the balanced benchmark")
    supply_error = (
        comparison["source_supply_2023"] - comparison["source_supply_anchor_mt"]
    ).abs()
    final_error = (
        comparison["source_final_demand_2023"]
        - comparison["source_final_demand_anchor_mt"]
    ).abs()
    food_error = (
        comparison["source_food_demand_2023"]
        - comparison["source_food_demand_anchor_mt"]
    ).abs()
    other_error = (
        comparison["source_other_final_demand_2023"]
        - comparison["source_other_final_demand_anchor_mt"]
    ).abs()
    maximum_anchor_error = float(
        max(supply_error.max(), food_error.max(), other_error.max(), final_error.max())
    )
    if maximum_anchor_error > 1.0e-10:
        raise AssertionError(
            f"Source anchors do not reproduce model-account anchors: {maximum_anchor_error}"
        )

    method_counts: dict[str, dict[str, int]] = {}
    unique_slices = full.drop_duplicates([TARGET_ID, "commodity"])
    # Methods can differ between sources only in theory; _normalised_weight
    # already asserts that each target/product uses one method.
    for column in (
        "supply_weight_method",
        "food_demand_weight_method",
        "other_final_demand_weight_method",
        "final_demand_weight_method",
        "processing_weight_method",
    ):
        method_counts[column] = {
            str(key): int(value)
            for key, value in unique_slices[column].value_counts().sort_index().items()
        }
    source_anchor_totals = full.groupby(SOURCE_ID)[anchor_columns].sum().sum(axis=1)
    positive_territory_sources = sorted(
        set(source_anchor_totals[source_anchor_totals.gt(0.0)].index) & territory_sources
    )
    zero_anchor_territory_sources = sorted(territory_sources - set(positive_territory_sources))
    report = {
        "model_account_count": len(accounts),
        "source_geography_count_in_bridge": int(full[SOURCE_ID].nunique()),
        "territory_source_count_in_bridge": int(
            full.loc[full["territory_aggregation_source"].astype(bool), SOURCE_ID].nunique()
        ),
        "weight_row_count": int(len(full)),
        "maximum_weight_sum_error": maximum_weight_error,
        "maximum_source_anchor_reconstruction_error_mt": maximum_anchor_error,
        "weight_method_slice_counts": method_counts,
        "territory_sources_with_positive_2023_physical_anchor": positive_territory_sources,
        "territory_sources_with_zero_2023_physical_anchor": zero_anchor_territory_sources,
        "fixed_share_limitation": (
            "No within-account source has an independent SSP trajectory; a source with "
            "zero 2023 physical anchors retains zero separately reported future share."
        ),
        "territory_sources_surviving_as_model_accounts": sorted(surviving),
    }
    order = [
        TARGET_ID,
        SOURCE_ID,
        "commodity",
        "territory_aggregation_source",
        "principal_source",
        *anchor_columns,
        *weight_columns,
        "supply_weight_method",
        "food_demand_weight_method",
        "other_final_demand_weight_method",
        "final_demand_weight_method",
        "processing_weight_method",
    ]
    return full[order].sort_values([TARGET_ID, SOURCE_ID, "commodity"]).reset_index(drop=True), report


def _finite_quantities(frame: pd.DataFrame, columns: Sequence[str]) -> None:
    for column in columns:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        if numeric.isna().any() or not np.isfinite(numeric).all():
            raise AnalysisInputError(f"Solved quantity is non-finite: {column}")
        if column != "net_import_mt" and (numeric < -1.0e-10).any():
            raise AnalysisInputError(f"Solved quantity is negative: {column}")


def _prepare_solved_quantities(
    solved: pd.DataFrame, analysis_config: Mapping[str, Any]
) -> pd.DataFrame:
    """Validate food use and make non-food final use explicit."""

    result = solved.copy()
    if "food_demand_mt" not in result or "final_demand_mt" not in result:
        raise AnalysisInputError("Solved results must contain food and total final demand")
    food = pd.to_numeric(result["food_demand_mt"], errors="coerce")
    final = pd.to_numeric(result["final_demand_mt"], errors="coerce")
    if food.isna().any() or final.isna().any():
        raise AnalysisInputError("Food/final demand contains non-numeric values")
    remainder = final - food
    if remainder.min() < -1.0e-10:
        raise AnalysisInputError("Solved food demand exceeds total final demand")
    remainder = remainder.clip(lower=0.0)
    if "other_final_demand_mt" in result:
        observed = pd.to_numeric(result["other_final_demand_mt"], errors="coerce")
        if observed.isna().any() or (observed - remainder).abs().max() > 1.0e-8:
            raise AnalysisInputError("Other final demand disagrees with final minus food")
    result["other_final_demand_mt"] = remainder
    return result


def _identity_residuals(frame: pd.DataFrame) -> dict[str, float]:
    production = (
        frame["production_mt"]
        - frame["primary_supply_mt"]
        - frame["processing_supply_mt"]
    ).abs()
    demand = (
        frame["demand_mt"]
        - frame["final_demand_mt"]
        - frame["processing_demand_mt"]
    ).abs()
    net_import = (
        frame["net_import_mt"] - frame["demand_mt"] + frame["production_mt"]
    ).abs()
    result = {
        "maximum_production_identity_residual_mt": float(production.max()),
        "maximum_demand_identity_residual_mt": float(demand.max()),
        "maximum_net_import_identity_residual_mt": float(net_import.max()),
    }
    if {"food_demand_mt", "other_final_demand_mt"} <= set(frame):
        final = (
            frame["final_demand_mt"]
            - frame["food_demand_mt"]
            - frame["other_final_demand_mt"]
        ).abs()
        result["maximum_final_demand_component_residual_mt"] = float(final.max())
    return result


def allocate_results_to_source_geography(
    solved: pd.DataFrame,
    weights: pd.DataFrame,
    analysis_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Split solved account quantities into original source contributions."""

    solved = _prepare_solved_quantities(solved, analysis_config)
    required_quantities = list(analysis_config["quantity_columns"]["required"])
    optional = [
        column
        for column in analysis_config["quantity_columns"].get("optional", [])
        if column in solved
    ]
    required = {MODEL_ID, *DIMENSION_COLUMNS, *required_quantities}
    if not required <= set(solved):
        raise AnalysisInputError(f"Solved results are missing: {sorted(required-set(solved))}")
    key = [*DIMENSION_COLUMNS, MODEL_ID]
    if solved.duplicated(key).any():
        raise AnalysisInputError("Solved account/product slices are duplicated")
    _finite_quantities(solved, [*required_quantities, *optional])
    identities = _identity_residuals(solved)
    if max(identities.values()) > 1.0e-8:
        raise AnalysisInputError(f"Solved accounting identities failed: {identities}")

    merged = solved.merge(
        weights,
        left_on=[MODEL_ID, "commodity"],
        right_on=[TARGET_ID, "commodity"],
        how="left",
        validate="many_to_many",
    )
    if merged[SOURCE_ID].isna().any():
        missing = merged.loc[merged[SOURCE_ID].isna(), [MODEL_ID, "commodity"]].drop_duplicates()
        raise AnalysisInputError(
            f"Solved rows lack source allocation weights: {missing.head().to_dict('records')}"
        )

    result = merged[[*DIMENSION_COLUMNS, MODEL_ID, SOURCE_ID]].copy()
    for column in ("primary_supply_mt", "processing_supply_mt"):
        result[column] = merged[column] * merged["supply_weight"]
    result["food_demand_mt"] = (
        merged["food_demand_mt"] * merged["food_demand_weight"]
    )
    result["other_final_demand_mt"] = (
        merged["other_final_demand_mt"] * merged["other_final_demand_weight"]
    )
    result["final_demand_mt"] = (
        result["food_demand_mt"] + result["other_final_demand_mt"]
    )
    result["processing_demand_mt"] = (
        merged["processing_demand_mt"] * merged["processing_weight"]
    )
    result["production_mt"] = (
        result["primary_supply_mt"] + result["processing_supply_mt"]
    )
    result["demand_mt"] = (
        result["final_demand_mt"] + result["processing_demand_mt"]
    )
    result["net_import_mt"] = result["demand_mt"] - result["production_mt"]
    return result


def aggregate_solved_results(
    solved: pd.DataFrame,
    model_membership: pd.DataFrame,
    source_membership: pd.DataFrame,
    weights: pd.DataFrame,
    analysis_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Aggregate one or more SSP slices to all configured reporting groups."""

    solved = _prepare_solved_quantities(solved, analysis_config)
    required_quantities = list(analysis_config["quantity_columns"]["required"])
    optional = [
        column
        for column in analysis_config["quantity_columns"].get("optional", [])
        if column in solved
    ]
    quantities = [*required_quantities, *optional]
    # Keep configured order while removing duplicates.
    quantities = list(dict.fromkeys(quantities))
    price_column = analysis_config["quantity_columns"]["world_price_column"]
    required = {MODEL_ID, *DIMENSION_COLUMNS, price_column, *quantities}
    if not required <= set(solved):
        raise AnalysisInputError(f"Scenario results are missing: {sorted(required-set(solved))}")
    _finite_quantities(solved, quantities)

    price_nunique = solved.groupby(list(DIMENSION_COLUMNS))[price_column].nunique(dropna=False)
    if not price_nunique.eq(1).all():
        raise AnalysisInputError("World price differs across model accounts within a market")
    prices = solved[[*DIMENSION_COLUMNS, price_column]].drop_duplicates(DIMENSION_COLUMNS)

    account_groups = aggregate_model_account_values(
        solved,
        model_membership,
        value_columns=quantities,
        dimension_columns=DIMENSION_COLUMNS,
        entity_column=MODEL_ID,
    )
    source_values = allocate_results_to_source_geography(solved, weights, analysis_config)
    source_groups = aggregate_source_geography_values(
        source_values,
        source_membership,
        value_columns=quantities,
        dimension_columns=DIMENSION_COLUMNS,
        entity_column=SOURCE_ID,
    )
    combined = pd.concat([account_groups, source_groups], ignore_index=True)
    combined = combined.merge(prices, on=list(DIMENSION_COLUMNS), how="left", validate="many_to_one")
    order = [
        "scenario",
        "year",
        "group_system",
        "group_code",
        "group_name",
        "commodity",
        price_column,
        *quantities,
    ]
    return combined[order].sort_values(order[:6]).reset_index(drop=True)


def _max_reconstruction_error(
    solved: pd.DataFrame,
    grouped: pd.DataFrame,
    *,
    system: str,
    quantities: Sequence[str],
    group_code: str | None = None,
) -> float:
    expected = solved.groupby(list(DIMENSION_COLUMNS), as_index=False)[list(quantities)].sum()
    selected = grouped[grouped["group_system"].eq(system)]
    if group_code is not None:
        selected = selected[selected["group_code"].eq(group_code)]
    actual = selected.groupby(list(DIMENSION_COLUMNS), as_index=False)[list(quantities)].sum()
    comparison = expected.merge(
        actual,
        on=list(DIMENSION_COLUMNS),
        how="outer",
        suffixes=("_expected", "_actual"),
        validate="one_to_one",
    )
    if comparison.isna().any().any():
        return float("inf")
    errors = [
        (comparison[f"{column}_expected"] - comparison[f"{column}_actual"]).abs().max()
        for column in quantities
    ]
    return float(max(errors, default=0.0))


def build_change_summary(
    grouped: pd.DataFrame,
    analysis_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Create a wide 2023-to-2050 table suited to paper drafting."""

    base_year = int(analysis_config["summary"]["baseline_year"])
    end_year = int(analysis_config["summary"]["comparison_year"])
    floor = float(analysis_config["summary"]["percent_change_denominator_floor_mt"])
    id_columns = [
        "scenario",
        "group_system",
        "group_code",
        "group_name",
        "commodity",
    ]
    numeric = [
        column
        for column in grouped.columns
        if column not in {*id_columns, "year"}
    ]
    base = grouped[grouped["year"].eq(base_year)][[*id_columns, *numeric]].copy()
    end = grouped[grouped["year"].eq(end_year)][[*id_columns, *numeric]].copy()
    if base.empty or end.empty:
        raise AnalysisInputError("Change summary lacks 2023 or 2050 rows")
    summary = base.merge(
        end,
        on=id_columns,
        how="inner",
        suffixes=(f"_{base_year}", f"_{end_year}"),
        validate="one_to_one",
    )
    for column in numeric:
        baseline = summary[f"{column}_{base_year}"]
        comparison = summary[f"{column}_{end_year}"]
        summary[f"{column}_absolute_change"] = comparison - baseline
        denominator_ok = baseline.abs().gt(floor)
        summary[f"{column}_percent_change"] = np.where(
            denominator_ok,
            (comparison / baseline - 1.0) * 100.0,
            np.nan,
        )
    return summary.sort_values(id_columns).reset_index(drop=True)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def run_analysis(project_root: str | Path) -> dict[str, Any]:
    """Run the formal account/source-geography aggregation and write outputs."""

    root = Path(project_root).resolve()
    config = load_analysis_config(root / "config/analysis.yaml")
    paths = {
        section: {
            key: _project_path(root, value)
            for key, value in config[section].items()
        }
        for section in ("inputs", "outputs")
    }
    catalog = load_source_catalog(paths["inputs"]["data_source_config"])
    for source_key in ("un_m49", "world_bank_income_classification"):
        verify_source(catalog.source(source_key))

    reporting_config = load_reporting_config(paths["inputs"]["reporting_config"])
    territory_config = yaml.safe_load(
        paths["inputs"]["territory_config"].read_text(encoding="utf-8")
    )
    commodity_config = yaml.safe_load(
        paths["inputs"]["commodity_config"].read_text(encoding="utf-8")
    )
    balancing_config = yaml.safe_load(
        paths["inputs"]["balancing_config"].read_text(encoding="utf-8")
    )
    solved = _prepare_solved_quantities(
        pd.read_csv(paths["inputs"]["scenario_results"]), config
    )
    benchmark = pd.read_csv(paths["inputs"]["balanced_benchmark"])
    source_observations = pd.read_csv(paths["inputs"]["source_observations"])
    accounts = sorted(solved[MODEL_ID].astype(str).str.upper().unique())
    source_geography = build_source_geography(
        catalog.source("un_m49").path,
        reporting_config,
        territory_config,
    )
    source_membership = build_source_geography_membership(source_geography)
    special_membership = build_un_special_membership(
        catalog.source("un_m49").path,
        source_geography,
        config,
    )
    source_membership = pd.concat(
        [source_membership, special_membership], ignore_index=True
    ).sort_values(["group_system", "group_code", SOURCE_ID]).reset_index(drop=True)

    income = load_world_bank_income_groups(
        catalog.source("world_bank_income_classification").path,
        reporting_config,
    )
    model_membership = build_model_account_membership(
        accounts,
        reporting_config,
        income_groups=income,
        territory_config=territory_config,
    )
    developing = build_developing_membership(model_membership, config)
    model_membership = pd.concat(
        [model_membership, developing], ignore_index=True
    ).sort_values(["group_system", "group_code", "model_account_id"]).reset_index(drop=True)

    weights, weight_report = build_source_allocation_weights(
        accounts,
        source_observations,
        benchmark,
        source_geography,
        territory_config,
        list(commodity_config["commodities"]),
        ddg_ratio=float(
            balancing_config["processing"]["ddg_output_mass_per_mass_ethanol"]
        ),
        food_commodities=balancing_config["final_demand_components"][
            "food_commodities"
        ],
        weight_sum_tolerance=float(
            config["source_geography_allocation"]["weight_sum_tolerance"]
        ),
    )

    # Process scenarios separately to cap the temporary many-to-many merge.
    scenario_outputs = []
    for scenario in sorted(solved["scenario"].unique()):
        scenario_outputs.append(
            aggregate_solved_results(
                solved[solved["scenario"].eq(scenario)].copy(),
                model_membership,
                source_membership,
                weights,
                config,
            )
        )
    grouped = pd.concat(scenario_outputs, ignore_index=True)
    summary = build_change_summary(grouped, config)

    quantities = list(config["quantity_columns"]["required"])
    quantities.extend(
        column
        for column in config["quantity_columns"].get("optional", [])
        if column in solved
    )
    quantities = list(dict.fromkeys(quantities))
    tolerance = float(
        config["source_geography_allocation"]["reconstruction_tolerance_mt"]
    )
    reconstruction = {
        "GLOBAL_WORLD": _max_reconstruction_error(
            solved, grouped, system="GLOBAL", group_code="WORLD", quantities=quantities
        ),
        "WB_INCOME_FY25": _max_reconstruction_error(
            solved, grouped, system=WB_INCOME_SYSTEM, quantities=quantities
        ),
    }
    for system in sorted(SOURCE_GROUP_SYSTEMS):
        reconstruction[system] = _max_reconstruction_error(
            solved, grouped, system=system, quantities=quantities
        )
    identity_report = _identity_residuals(grouped)
    territory_sources = set(territory_crosswalk(territory_config)[SOURCE_ID])
    actual_scenarios = sorted(solved["scenario"].unique())
    actual_years = sorted(int(value) for value in solved["year"].unique())
    gate = config["coverage_gate"]
    expected_scenarios = list(gate["expected_scenarios"])
    account_report = account_coverage_report(
        accounts,
        model_membership,
        reporting_config,
        territory_config=territory_config,
    )
    special_counts = {
        code: int(
            special_membership.loc[special_membership["group_code"].eq(code), SOURCE_ID].nunique()
        )
        for code in ("LDC", "LLDC", "SIDS", "PACIFIC_ISLANDS")
    }
    represented_sources = set(weights[SOURCE_ID])
    represented_special_counts = {
        code: int(
            special_membership.loc[
                special_membership["group_code"].eq(code)
                & special_membership[SOURCE_ID].isin(represented_sources),
                SOURCE_ID,
            ].nunique()
        )
        for code in special_counts
    }
    maximum_reconstruction = max(reconstruction.values())
    maximum_identity = max(identity_report.values())
    world_net_import = grouped[
        grouped["group_system"].eq("GLOBAL") & grouped["group_code"].eq("WORLD")
    ]["net_import_mt"].abs().max()
    passed = (
        len(accounts) == int(gate["expected_model_accounts"])
        and solved["commodity"].nunique() == int(gate["expected_commodities"])
        and actual_scenarios == expected_scenarios
        and actual_years == list(
            range(int(gate["expected_year_start"]), int(gate["expected_year_end"]) + 1)
        )
        and not (set(accounts) & territory_sources)
        and maximum_reconstruction <= tolerance
        and maximum_identity <= tolerance
        and weight_report["maximum_weight_sum_error"]
        <= float(config["source_geography_allocation"]["weight_sum_tolerance"])
        and account_report["status"] == "passed"
    )
    report: dict[str, Any] = {
        "status": "passed" if passed else "blocked",
        "aggregation_scope": "reporting_postsolve_only",
        "model_account_count": len(accounts),
        "commodity_count": int(solved["commodity"].nunique()),
        "scenarios": actual_scenarios,
        "year_start": actual_years[0],
        "year_end": actual_years[-1],
        "group_result_row_count": int(len(grouped)),
        "change_summary_row_count": int(len(summary)),
        "world_generated_only_from_model_accounts": True,
        "source_geography_contains_world_group": bool(
            source_membership["group_code"].eq("WORLD").any()
        ),
        "territory_sources_surviving_as_model_accounts": sorted(
            set(accounts) & territory_sources
        ),
        "source_allocation_method": config["source_geography_allocation"]["method"],
        "source_allocation_fixed_year": int(config["benchmark_year"]),
        "source_allocation_report": weight_report,
        "un_special_classification_source_id": config["un_special_groups"]["source_id"],
        "un_special_official_source_counts": special_counts,
        "un_special_sources_represented_in_model_bridge": represented_special_counts,
        "developing_economy_definition": "World Bank FY25 LIC + LMC + UMC",
        "developing_model_account_count": int(developing["model_account_id"].nunique()),
        "maximum_reconstruction_error_mt": float(maximum_reconstruction),
        "reconstruction_error_by_exclusive_system_mt": reconstruction,
        **identity_report,
        "maximum_world_net_import_absolute_mt": float(world_net_import),
        "account_coverage": account_report,
        "outputs": {key: str(value) for key, value in paths["outputs"].items()},
    }

    for path in paths["outputs"].values():
        path.parent.mkdir(parents=True, exist_ok=True)
    grouped.to_csv(paths["outputs"]["group_results"], index=False)
    summary.to_csv(paths["outputs"]["change_summary"], index=False)
    model_membership.to_csv(paths["outputs"]["model_membership"], index=False)
    source_membership.to_csv(paths["outputs"]["source_membership"], index=False)
    weights.to_csv(paths["outputs"]["source_allocation_weights"], index=False)
    _write_json(paths["outputs"]["coverage_report"], report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    args = parser.parse_args()
    print(json.dumps(run_analysis(args.project_root), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
