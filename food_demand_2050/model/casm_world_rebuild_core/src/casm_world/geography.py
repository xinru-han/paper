"""Audited territory-to-model-account aggregation for CASM-World.

The module has no dependency on SILK or on an earlier world-model codebase.
It treats the configured territories as source/reporting records, not model
entities, and applies only additive many-to-one transformations.
"""

from __future__ import annotations

from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd
import yaml


EXPECTED_TERRITORIES = frozenset(
    {
        "ASM",
        "BES",
        "BLM",
        "ESH",
        "FLK",
        "FRO",
        "GGY",
        "GIB",
        "GLP",
        "GUF",
        "GUM",
        "IMN",
        "JEY",
        "MAF",
        "MNP",
        "MTQ",
        "MYT",
        "NIU",
        "REU",
        "SHN",
        "SPM",
        "TKL",
        "TWN",
        "VIR",
        "WLF",
    }
)

GDP_SCOPE_ACTIONS = frozenset(
    {
        "already_in_accounting_target",
        "add_source_gdp_to_accounting_target",
    }
)

REQUIRED_MAPPING_FIELDS = frozenset(
    {
        "source_economy_id",
        "source_name",
        "source_m49",
        "model_entity",
        "retain_classification_metadata",
        "accounting_target",
        "reporting_region_target",
        "reporting_subregion_target",
        "gdp_scope_action",
        "scope_evidence",
    }
)


def load_territory_config(path: str | Path) -> dict[str, Any]:
    """Load and fully validate the territory aggregation configuration."""

    config_path = Path(path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError(f"Territory configuration must be a mapping: {config_path}")
    validate_territory_config(config)
    return config


def _mapping_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = config.get("territory_mappings")
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise ValueError("territory_mappings must be a list of mappings")
    return records


def validate_territory_config(config: Mapping[str, Any]) -> None:
    """Enforce the 25-row crosswalk and its non-negotiable scope rules."""

    records = _mapping_records(config)
    invariants = config.get("invariants", {})
    expected_count = int(invariants.get("expected_source_territories", -1))
    if expected_count != len(EXPECTED_TERRITORIES) or len(records) != expected_count:
        raise ValueError(
            "Territory crosswalk must contain exactly "
            f"{len(EXPECTED_TERRITORIES)} mappings"
        )

    missing_fields = [
        (index, sorted(REQUIRED_MAPPING_FIELDS - set(record)))
        for index, record in enumerate(records)
        if REQUIRED_MAPPING_FIELDS - set(record)
    ]
    if missing_fields:
        raise ValueError(f"Territory mappings have missing fields: {missing_fields}")

    sources = [str(record["source_economy_id"]).strip().upper() for record in records]
    if len(sources) != len(set(sources)):
        raise ValueError("source_economy_id must be unique")
    if set(sources) != EXPECTED_TERRITORIES:
        raise ValueError(
            "Unexpected territory set: "
            f"missing={sorted(EXPECTED_TERRITORIES - set(sources))}, "
            f"extra={sorted(set(sources) - EXPECTED_TERRITORIES)}"
        )

    m49_codes = [str(record["source_m49"]).zfill(3) for record in records]
    if len(m49_codes) != len(set(m49_codes)):
        raise ValueError("source_m49 must be unique")

    targets = config.get("accounting_targets")
    regions = config.get("reporting_regions")
    subregions = config.get("reporting_subregions")
    evidence = config.get("scope_evidence")
    if not all(isinstance(section, dict) for section in (targets, regions, subregions, evidence)):
        raise ValueError(
            "accounting_targets, reporting_regions, reporting_subregions and "
            "scope_evidence must be mappings"
        )

    source_set = set(sources)
    for record in records:
        source = str(record["source_economy_id"]).strip().upper()
        target = str(record["accounting_target"]).strip().upper()
        region = str(record["reporting_region_target"]).zfill(3)
        subregion = str(record["reporting_subregion_target"]).zfill(3)
        action = str(record["gdp_scope_action"])

        if record["model_entity"] is not False:
            raise ValueError(f"{source} must have model_entity=false")
        if record["retain_classification_metadata"] is not True:
            raise ValueError(f"{source} must retain classification metadata")
        if target not in targets:
            raise ValueError(f"{source} has undefined accounting target {target}")
        if target in source_set:
            raise ValueError(f"Aggregation chains are forbidden: {source} -> {target}")
        if targets[target].get("model_entity") is not True:
            raise ValueError(f"Accounting target {target} must be a model entity")
        if region not in regions:
            raise ValueError(f"{source} has undefined M49 region {region}")
        if subregion not in subregions:
            raise ValueError(f"{source} has undefined M49 reporting area {subregion}")
        if action not in GDP_SCOPE_ACTIONS:
            raise ValueError(f"{source} has invalid GDP scope action {action}")
        if record["scope_evidence"] not in evidence:
            raise ValueError(f"{source} refers to missing scope evidence")

    rows = {source: record for source, record in zip(sources, records)}
    if str(rows["TWN"]["accounting_target"]).upper() != "OTHER_EASTERN_ASIA":
        raise ValueError("TWN must map to OTHER_EASTERN_ASIA")
    if str(rows["TWN"]["accounting_target"]).upper() == "CHN":
        raise ValueError("TWN must not enter the CHN account")
    if str(rows["ESH"]["accounting_target"]).upper() != "MAR":
        raise ValueError("ESH must map to MAR")

    already_in_target = {
        source
        for source, record in rows.items()
        if record["gdp_scope_action"] == "already_in_accounting_target"
    }
    expected_included = {"ESH", "GLP", "GUF", "MAF", "MTQ", "MYT", "REU"}
    if already_in_target != expected_included:
        raise ValueError(
            "GDP parent-scope set is wrong: "
            f"expected={sorted(expected_included)}, actual={sorted(already_in_target)}"
        )


def territory_crosswalk(config: Mapping[str, Any]) -> pd.DataFrame:
    """Return the validated 25-row mapping as a stable audit table."""

    validate_territory_config(config)
    frame = pd.DataFrame(_mapping_records(config)).copy()
    frame["source_economy_id"] = (
        frame["source_economy_id"].astype(str).str.strip().str.upper()
    )
    frame["accounting_target"] = (
        frame["accounting_target"].astype(str).str.strip().str.upper()
    )
    frame["source_m49"] = frame["source_m49"].astype(str).str.zfill(3)
    frame["reporting_region_target"] = (
        frame["reporting_region_target"].astype(str).str.zfill(3)
    )
    frame["reporting_subregion_target"] = (
        frame["reporting_subregion_target"].astype(str).str.zfill(3)
    )
    target_metadata = config["accounting_targets"]
    frame["accounting_target_name"] = frame["accounting_target"].map(
        lambda code: target_metadata[code]["name"]
    )
    frame["accounting_target_type"] = frame["accounting_target"].map(
        lambda code: target_metadata[code]["target_type"]
    )
    return frame.sort_values("source_economy_id").reset_index(drop=True)


def attach_territory_mapping(
    frame: pd.DataFrame,
    config: Mapping[str, Any],
    *,
    entity_column: str = "economy_id",
) -> pd.DataFrame:
    """Attach accounting and original-M49 reporting destinations to rows.

    Non-mapped economies retain themselves as their accounting target. The
    reporting destinations are populated only for the 25 mapped territories;
    upstream master geography remains authoritative for all other economies.
    """

    validate_territory_config(config)
    if entity_column not in frame.columns:
        raise ValueError(f"Missing entity column: {entity_column}")
    output_columns = {
        "accounting_target",
        "territory_aggregation_source",
        "reporting_region_target",
        "reporting_subregion_target",
        "gdp_scope_action",
        "source_model_entity",
        "retain_classification_metadata",
    }
    conflicts = output_columns & set(frame.columns)
    if conflicts:
        raise ValueError(f"Mapping output columns already exist: {sorted(conflicts)}")

    result = frame.copy()
    result[entity_column] = result[entity_column].astype(str).str.strip().str.upper()
    if result[entity_column].eq("").any():
        raise ValueError("Blank economy identifiers are forbidden")

    crosswalk = territory_crosswalk(config).set_index("source_economy_id")
    source = result[entity_column]
    result["territory_aggregation_source"] = source.isin(crosswalk.index)
    result["accounting_target"] = source.map(crosswalk["accounting_target"]).fillna(source)
    result["reporting_region_target"] = source.map(
        crosswalk["reporting_region_target"]
    )
    result["reporting_subregion_target"] = source.map(
        crosswalk["reporting_subregion_target"]
    )
    result["gdp_scope_action"] = source.map(crosswalk["gdp_scope_action"]).fillna(
        "direct_account_value"
    )
    result["source_model_entity"] = source.map(crosswalk["model_entity"])
    result["retain_classification_metadata"] = source.map(
        crosswalk["retain_classification_metadata"]
    )
    return result


def _normalise_columns(columns: Iterable[str], label: str) -> list[str]:
    result = list(columns)
    if not result:
        raise ValueError(f"{label} must not be empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicates")
    return result


def _assert_slice_conservation(
    before: pd.DataFrame,
    after: pd.DataFrame,
    value_columns: Sequence[str],
    dimension_columns: Sequence[str],
    *,
    relative_tolerance: float,
    absolute_tolerance: float,
) -> None:
    if dimension_columns:
        before_totals = (
            before.groupby(list(dimension_columns), dropna=False, as_index=False)[
                list(value_columns)
            ]
            .sum()
            .sort_values(list(dimension_columns))
            .reset_index(drop=True)
        )
        after_totals = (
            after.groupby(list(dimension_columns), dropna=False, as_index=False)[
                list(value_columns)
            ]
            .sum()
            .sort_values(list(dimension_columns))
            .reset_index(drop=True)
        )
        joined = before_totals.merge(
            after_totals,
            on=list(dimension_columns),
            how="outer",
            suffixes=("__before", "__after"),
            validate="one_to_one",
        )
    else:
        joined = pd.DataFrame(
            {
                f"{column}__before": [float(before[column].sum())]
                for column in value_columns
            }
            | {
                f"{column}__after": [float(after[column].sum())]
                for column in value_columns
            }
        )

    failures: list[str] = []
    for column in value_columns:
        left = joined[f"{column}__before"]
        right = joined[f"{column}__after"]
        for index, (before_value, after_value) in enumerate(zip(left, right)):
            if not isfinite(float(before_value)) or not isfinite(float(after_value)):
                failures.append(f"{column}[{index}]: non-finite total")
            elif abs(float(before_value) - float(after_value)) > (
                absolute_tolerance
                + relative_tolerance * max(abs(float(before_value)), abs(float(after_value)))
            ):
                failures.append(
                    f"{column}[{index}]: before={before_value}, after={after_value}"
                )
    if failures:
        raise AssertionError("Additive aggregation failed conservation: " + "; ".join(failures))


def aggregate_additive_values(
    frame: pd.DataFrame,
    config: Mapping[str, Any],
    *,
    value_columns: Sequence[str],
    dimension_columns: Sequence[str],
    entity_column: str = "economy_id",
    require_all_territories: bool = False,
    relative_tolerance: float = 1e-12,
    absolute_tolerance: float = 1e-9,
) -> pd.DataFrame:
    """Sum population, scope-exclusive GDP, or product quantities to targets.

    Each source economy may occur at most once in a dimension slice. This
    catches duplicate observations before they can inflate a receiver. Totals
    are then checked independently for every dimension slice, so neither a
    global offset nor cancellation between years/products can hide an error.

    ``value_columns`` can contain population, GDP and any physical product
    quantities together. GDP must first satisfy the scope contract documented
    in the configuration: a territory already embedded in published parent GDP
    contributes zero separately; an excluded territory contributes its full
    supplemental GDP.
    """

    validate_territory_config(config)
    values = _normalise_columns(value_columns, "value_columns")
    dimensions = list(dimension_columns)
    if len(dimensions) != len(set(dimensions)):
        raise ValueError("dimension_columns contains duplicates")
    if entity_column in dimensions or entity_column in values:
        raise ValueError("entity_column cannot also be a dimension or value column")
    if set(values) & set(dimensions):
        raise ValueError("Value and dimension columns must be disjoint")

    required = [entity_column, *dimensions, *values]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing aggregation columns: {missing}")

    work = frame[required].copy()
    work[entity_column] = work[entity_column].astype(str).str.strip().str.upper()
    if work[entity_column].eq("").any():
        raise ValueError("Blank economy identifiers are forbidden")
    duplicate_key = [*dimensions, entity_column]
    if work.duplicated(duplicate_key).any():
        duplicates = work.loc[work.duplicated(duplicate_key, keep=False), duplicate_key]
        raise ValueError(
            "Duplicate source rows within an accounting slice: "
            f"{duplicates.drop_duplicates().to_dict('records')}"
        )

    for column in values:
        numeric = pd.to_numeric(work[column], errors="coerce")
        if numeric.isna().any():
            bad = work.loc[numeric.isna(), duplicate_key].to_dict("records")
            raise ValueError(f"Null or non-numeric {column} values: {bad}")
        if not numeric.map(lambda value: isfinite(float(value))).all():
            raise ValueError(f"Non-finite values are forbidden in {column}")
        work[column] = numeric

    source_values = work.copy()

    crosswalk = territory_crosswalk(config)
    source_to_target = crosswalk.set_index("source_economy_id")["accounting_target"]
    present_sources = set(work[entity_column]) & EXPECTED_TERRITORIES
    if require_all_territories and present_sources != EXPECTED_TERRITORIES:
        raise ValueError(
            "Input does not cover all configured territories: "
            f"missing={sorted(EXPECTED_TERRITORIES - present_sources)}"
        )

    work[entity_column] = work[entity_column].map(source_to_target).fillna(
        work[entity_column]
    )
    result = (
        work.groupby([*dimensions, entity_column], as_index=False, dropna=False)[values]
        .sum(min_count=1)
        .sort_values([*dimensions, entity_column])
        .reset_index(drop=True)
    )

    surviving_sources = set(result[entity_column]) & EXPECTED_TERRITORIES
    if surviving_sources:
        raise AssertionError(
            f"Mapped territories survived as model accounts: {sorted(surviving_sources)}"
        )
    _assert_slice_conservation(
        source_values,
        result,
        values,
        dimensions,
        relative_tolerance=relative_tolerance,
        absolute_tolerance=absolute_tolerance,
    )
    return result


def validate_parent_scope_gdp(
    frame: pd.DataFrame,
    config: Mapping[str, Any],
    *,
    gdp_column: str,
    entity_column: str = "economy_id",
    zero_tolerance: float = 1e-12,
) -> None:
    """Prevent double counting when receiver rows use published parent GDP.

    Territory GDP rows whose activity is already embedded in the parent must
    be zero in the scope-exclusive additive panel. Territories excluded from
    the parent must have a finite supplemental contribution if present.
    """

    required = {entity_column, gdp_column}
    if not required <= set(frame.columns):
        raise ValueError(f"Missing GDP scope columns: {sorted(required-set(frame.columns))}")
    crosswalk = territory_crosswalk(config).set_index("source_economy_id")
    work = frame[[entity_column, gdp_column]].copy()
    work[entity_column] = work[entity_column].astype(str).str.strip().str.upper()
    mapped = work[work[entity_column].isin(crosswalk.index)].copy()
    mapped["gdp_scope_action"] = mapped[entity_column].map(crosswalk["gdp_scope_action"])
    numeric = pd.to_numeric(mapped[gdp_column], errors="coerce")

    additions = mapped["gdp_scope_action"].eq("add_source_gdp_to_accounting_target")
    if numeric[additions].isna().any():
        missing = sorted(mapped.loc[additions & numeric.isna(), entity_column].unique())
        raise ValueError(f"Supplemental GDP is required for: {missing}")
    included = mapped["gdp_scope_action"].eq("already_in_accounting_target")
    nonzero = included & numeric.notna() & numeric.abs().gt(zero_tolerance)
    if nonzero.any():
        duplicate_scope = sorted(mapped.loc[nonzero, entity_column].unique())
        raise ValueError(
            "Published parent GDP already includes these territories; a separate "
            f"additive GDP would double count: {duplicate_scope}"
        )
