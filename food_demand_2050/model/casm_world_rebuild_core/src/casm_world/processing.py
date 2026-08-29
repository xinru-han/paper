"""Auditable processing-chain diagnostics and linear constraint interfaces.

This module reads the clean rebuild's commodity definitions and unbalanced
benchmark observations.  It never edits, fills, scales, or balances those
observations.  Missing source cells remain ``NaN`` in the constraint vector,
whereas an explicit observed zero remains a valid observation.

The numeric constraint system contains only independent equations suitable
for a later weighted constrained-balancing step:

* two output-yield equations for each oilseed crush chain;
* one sugar-output equation using cane and beet processing quantities; and
* one cotton-lint yield equation using seed-cotton activity.

Oilseed mass equations are also reported as diagnostics, but are not inserted
into the matrix because they are linear combinations of the two output-yield
equations.  Full cotton mass balance is unavailable without the configured
cottonseed satellite observation.  Dairy is diagnostic-only until milk-fat
and non-fat-solids coefficients and allocation/loss terms are frozen.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
import pandas as pd
from scipy.sparse import csr_matrix
import yaml


FloatArray = NDArray[np.float64]

REQUIRED_COLUMNS = {
    "year",
    "commodity",
    "role",
    "account",
    "unit",
    "economy_id",
    "value",
}

OILSEED_CHAINS = (
    "soybean_crush",
    "sunflower_crush",
    "rapeseed_crush",
)


class ProcessingInputError(ValueError):
    """Raised when processing configuration or observations are ambiguous."""


@dataclass(frozen=True, order=True)
class SeriesKey:
    """A source-auditable benchmark series used by a processing equation."""

    commodity: str
    role: str
    account: str
    unit: str = "Mt"

    @property
    def label(self) -> str:
        return f"{self.commodity}:{self.role}:{self.account}:{self.unit}"


@dataclass(frozen=True)
class EquationSpec:
    """One homogeneous linear processing identity."""

    chain: str
    name: str
    kind: str
    terms: tuple[tuple[SeriesKey, float], ...]
    reference_inputs: tuple[SeriesKey, ...]
    expression: str
    independent: bool


@dataclass(frozen=True)
class ProcessingConstraintSystem:
    """Sparse ``A @ x = rhs`` interface for later constrained balancing.

    ``variables`` maps each column of ``matrix`` to a country/source series and
    records its untouched observed value.  Missing cells are represented by
    ``observed=False`` and ``observed_value=NaN``.  ``equations`` maps matrix
    rows to chains, economies, and human-readable equations.
    """

    matrix: csr_matrix
    rhs: FloatArray
    variables: pd.DataFrame
    equations: pd.DataFrame

    def evaluate(self, values: ArrayLike) -> FloatArray:
        """Evaluate every constraint for a complete candidate variable vector."""

        vector = np.asarray(values, dtype=np.float64)
        if vector.shape != (self.matrix.shape[1],):
            raise ProcessingInputError(
                "constraint values must have shape "
                f"({self.matrix.shape[1]},), received {vector.shape}"
            )
        if not np.all(np.isfinite(vector)):
            raise ProcessingInputError("constraint values must all be finite")
        return np.asarray(self.matrix @ vector - self.rhs, dtype=np.float64)

    def evaluate_observed(self) -> FloatArray:
        """Evaluate complete observed rows and return ``NaN`` for incomplete rows."""

        observed = self.variables["observed"].to_numpy(dtype=bool)
        values = self.variables["observed_value"].to_numpy(dtype=float)
        missing = (~observed).astype(np.int8)
        incomplete = np.asarray(self.matrix.astype(bool) @ missing).ravel() > 0
        residuals = np.asarray(
            self.matrix @ np.nan_to_num(values, nan=0.0) - self.rhs,
            dtype=np.float64,
        )
        residuals[incomplete] = np.nan
        return residuals


@dataclass(frozen=True)
class ProcessingAudit:
    """Processing diagnostics without any adjustment to source observations."""

    country_diagnostics: pd.DataFrame
    global_diagnostics: pd.DataFrame
    chain_status: pd.DataFrame
    constraints: ProcessingConstraintSystem
    report: dict


def load_processing_config(path: Path) -> dict:
    """Load and validate the clean rebuild's commodity-processing config."""

    with Path(path).open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ProcessingInputError("commodity configuration must be a mapping")
    _validate_processing_config(config)
    return config


def _as_float(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ProcessingInputError(f"{label} must be numeric") from exc
    if not np.isfinite(number) or number < 0.0:
        raise ProcessingInputError(f"{label} must be finite and non-negative")
    return number


def _validate_processing_config(config: Mapping) -> None:
    commodities = config.get("commodities")
    systems = config.get("processing_systems")
    if not isinstance(commodities, Mapping) or not isinstance(systems, Mapping):
        raise ProcessingInputError(
            "configuration requires commodities and processing_systems mappings"
        )

    for chain in OILSEED_CHAINS:
        system = systems.get(chain)
        if not isinstance(system, Mapping):
            raise ProcessingInputError(f"missing processing system {chain}")
        input_code = str(system.get("input", ""))
        outputs = system.get("outputs")
        if input_code not in commodities or not isinstance(outputs, Mapping):
            raise ProcessingInputError(f"invalid input or outputs for {chain}")
        if len(outputs) != 2 or any(
            str(code) not in commodities for code in outputs
        ):
            raise ProcessingInputError(f"{chain} must define two modelled outputs")
        yields = [
            _as_float(value, f"{chain} output coefficient")
            for value in outputs.values()
        ]
        residual = _as_float(system.get("residual"), f"{chain} residual")
        if not np.isclose(sum(yields) + residual, 1.0, atol=1.0e-10, rtol=0.0):
            raise ProcessingInputError(f"{chain} mass coefficients do not sum to one")

    sugar = systems.get("sugar_refining")
    if not isinstance(sugar, Mapping) or not isinstance(sugar.get("inputs"), Mapping):
        raise ProcessingInputError("invalid sugar_refining definition")
    if str(sugar.get("output", "")) not in commodities:
        raise ProcessingInputError("sugar_refining output is not a model commodity")
    for code, coefficient in sugar["inputs"].items():
        if str(code) not in commodities:
            raise ProcessingInputError(f"unknown sugar input commodity {code}")
        _as_float(coefficient, f"sugar_refining coefficient for {code}")

    cotton = systems.get("cotton_ginning")
    if not isinstance(cotton, Mapping) or not isinstance(
        cotton.get("outputs"), Mapping
    ):
        raise ProcessingInputError("invalid cotton_ginning definition")
    cotton_outputs = cotton["outputs"]
    if (
        "CTN" not in cotton_outputs
        or "cottonseed_satellite" not in cotton_outputs
    ):
        raise ProcessingInputError(
            "cotton_ginning requires lint and cottonseed outputs"
        )
    cotton_total = sum(
        _as_float(value, "cotton_ginning output coefficient")
        for value in cotton_outputs.values()
    ) + _as_float(cotton.get("residual"), "cotton_ginning residual")
    if not np.isclose(cotton_total, 1.0, atol=1.0e-10, rtol=0.0):
        raise ProcessingInputError("cotton_ginning mass coefficients do not sum to one")

    dairy = systems.get("dairy_solids")
    if not isinstance(dairy, Mapping) or not isinstance(dairy.get("outputs"), list):
        raise ProcessingInputError("invalid dairy_solids definition")
    if str(dairy.get("input", "")) not in commodities:
        raise ProcessingInputError("dairy input is not a model commodity")
    if any(str(code) not in commodities for code in dairy["outputs"]):
        raise ProcessingInputError("dairy outputs contain an unknown commodity")


def _production_key(commodity: str) -> SeriesKey:
    return SeriesKey(commodity, "balance", "production")


def _independent_equations(config: Mapping) -> list[EquationSpec]:
    systems = config["processing_systems"]
    equations: list[EquationSpec] = []

    for chain in OILSEED_CHAINS:
        system = systems[chain]
        input_key = SeriesKey(str(system["input"]), "balance", "processing")
        for output_code, coefficient_value in system["outputs"].items():
            coefficient = float(coefficient_value)
            output_key = _production_key(str(output_code))
            equations.append(
                EquationSpec(
                    chain=chain,
                    name=f"{output_code}_yield",
                    kind="output_yield",
                    terms=((output_key, 1.0), (input_key, -coefficient)),
                    reference_inputs=(input_key,),
                    expression=(
                        f"{output_key.label} - {coefficient:.10g} * "
                        f"{input_key.label} = 0"
                    ),
                    independent=True,
                )
            )

    sugar = systems["sugar_refining"]
    sugar_output = _production_key(str(sugar["output"]))
    sugar_inputs = tuple(
        (
            SeriesKey(str(code), "balance", "processing"),
            -float(coefficient),
        )
        for code, coefficient in sugar["inputs"].items()
    )
    sugar_expression = " - ".join(
        f"{abs(coefficient):.10g} * {key.label}"
        for key, coefficient in sugar_inputs
    )
    equations.append(
        EquationSpec(
            chain="sugar_refining",
            name="sugar_output",
            kind="conversion_yield",
            terms=((sugar_output, 1.0), *sugar_inputs),
            reference_inputs=tuple(key for key, _ in sugar_inputs),
            expression=f"{sugar_output.label} - {sugar_expression} = 0",
            independent=True,
        )
    )

    cotton = systems["cotton_ginning"]
    seed_cotton = SeriesKey("CTN", "activity", "production")
    cotton_lint = _production_key("CTN")
    lint_yield = float(cotton["outputs"]["CTN"])
    equations.append(
        EquationSpec(
            chain="cotton_ginning",
            name="cotton_lint_yield",
            kind="output_yield",
            terms=((cotton_lint, 1.0), (seed_cotton, -lint_yield)),
            reference_inputs=(seed_cotton,),
            expression=(
                f"{cotton_lint.label} - {lint_yield:.10g} * "
                f"{seed_cotton.label} = 0"
            ),
            independent=True,
        )
    )
    return equations


def _mass_diagnostic_equations(config: Mapping) -> list[EquationSpec]:
    systems = config["processing_systems"]
    equations: list[EquationSpec] = []
    for chain in OILSEED_CHAINS:
        system = systems[chain]
        input_key = SeriesKey(str(system["input"]), "balance", "processing")
        output_keys = tuple(_production_key(str(code)) for code in system["outputs"])
        modelled_share = 1.0 - float(system["residual"])
        output_expression = " + ".join(key.label for key in output_keys)
        equations.append(
            EquationSpec(
                chain=chain,
                name="mass_balance",
                kind="mass_balance",
                terms=(
                    *((key, 1.0) for key in output_keys),
                    (input_key, -modelled_share),
                ),
                reference_inputs=(input_key,),
                expression=(
                    f"{output_expression} - {modelled_share:.10g} * "
                    f"{input_key.label} = 0"
                ),
                independent=False,
            )
        )
    return equations


def _target_observations(
    observations: pd.DataFrame,
    *,
    year: int,
) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(observations.columns)
    if missing:
        raise ProcessingInputError(
            f"benchmark is missing required columns: {sorted(missing)}"
        )

    years = pd.to_numeric(observations["year"], errors="coerce")
    if years.isna().any():
        raise ProcessingInputError(
            "benchmark year contains missing or non-numeric values"
        )
    target = observations.loc[years.eq(year)].copy()
    if target.empty:
        raise ProcessingInputError(f"benchmark contains no observations for {year}")
    if target["economy_id"].isna().any():
        raise ProcessingInputError("benchmark contains missing economy identifiers")
    target["economy_id"] = target["economy_id"].astype(str)
    return target


def _observation_lookup(
    target: pd.DataFrame,
    relevant_series: Iterable[SeriesKey],
) -> tuple[dict[tuple[str, SeriesKey], float], dict[tuple[str, SeriesKey], str]]:
    series = set(relevant_series)
    selected = target[
        target.apply(
            lambda row: SeriesKey(
                str(row["commodity"]),
                str(row["role"]),
                str(row["account"]),
                str(row["unit"]),
            )
            in series,
            axis=1,
        )
    ].copy()
    selected["value"] = pd.to_numeric(selected["value"], errors="coerce")
    if not np.isfinite(selected["value"].to_numpy(dtype=float)).all():
        raise ProcessingInputError(
            "processing observations contain missing or non-finite values"
        )
    if (selected["value"] < 0.0).any():
        bad = selected.loc[
            selected["value"].lt(0.0),
            ["economy_id", "commodity", "role", "account"],
        ].head(5)
        raise ProcessingInputError(
            "processing quantities cannot be negative: "
            f"{bad.to_dict(orient='records')}"
        )

    key_columns = ["economy_id", "commodity", "role", "account", "unit"]
    duplicated = selected.duplicated(key_columns, keep=False)
    if duplicated.any():
        keys = selected.loc[duplicated, key_columns].head(5).to_dict(orient="records")
        raise ProcessingInputError(
            f"processing observations contain duplicate source cells: {keys}"
        )

    values: dict[tuple[str, SeriesKey], float] = {}
    sources: dict[tuple[str, SeriesKey], str] = {}
    for row in selected.itertuples(index=False):
        key = SeriesKey(
            str(row.commodity),
            str(row.role),
            str(row.account),
            str(row.unit),
        )
        identity = (str(row.economy_id), key)
        values[identity] = float(row.value)
        sources[identity] = str(getattr(row, "source_domain", ""))
    return values, sources


def _resolve_economies(
    target: pd.DataFrame,
    economies: Sequence[str] | None,
) -> tuple[str, ...]:
    if economies is None:
        result = tuple(sorted(target["economy_id"].astype(str).unique()))
    else:
        result = tuple(str(value) for value in economies)
    if not result:
        raise ProcessingInputError("at least one economy is required")
    if len(set(result)) != len(result):
        raise ProcessingInputError("economy identifiers must be unique")
    if any(not value for value in result):
        raise ProcessingInputError("economy identifiers cannot be empty")
    return result


def _equation_diagnostic(
    economy: str,
    spec: EquationSpec,
    values: Mapping[tuple[str, SeriesKey], float],
) -> dict:
    observed_values = {
        key: values.get((economy, key), np.nan) for key, _ in spec.terms
    }
    observed_terms = sum(np.isfinite(value) for value in observed_values.values())
    complete = observed_terms == len(spec.terms)
    positive_total = sum(
        coefficient * observed_values[key]
        for key, coefficient in spec.terms
        if coefficient > 0.0 and np.isfinite(observed_values[key])
    )
    expected_total = -sum(
        coefficient * observed_values[key]
        for key, coefficient in spec.terms
        if coefficient < 0.0 and np.isfinite(observed_values[key])
    )
    reference_input = sum(
        values.get((economy, key), 0.0)
        for key in spec.reference_inputs
        if np.isfinite(values.get((economy, key), np.nan))
    )
    if complete:
        residual = sum(
            coefficient * observed_values[key] for key, coefficient in spec.terms
        )
        relative = residual / expected_total if expected_total > 0.0 else np.nan
    else:
        residual = np.nan
        relative = np.nan

    return {
        "chain": spec.chain,
        "diagnostic": spec.name,
        "kind": spec.kind,
        "economy_id": economy,
        "in_constraint_matrix": spec.independent,
        "complete": bool(complete),
        "observed_terms": int(observed_terms),
        "required_terms": len(spec.terms),
        "reference_input_mt": float(reference_input),
        "observed_output_mt": float(positive_total),
        "expected_output_mt": float(expected_total),
        "residual_mt": float(residual),
        "relative_residual": float(relative),
        "output_input_ratio": (
            float(positive_total / reference_input) if reference_input > 0.0 else np.nan
        ),
        "equation": spec.expression,
    }


def build_processing_constraints(
    observations: pd.DataFrame,
    config: Mapping,
    *,
    economies: Sequence[str] | None = None,
) -> ProcessingConstraintSystem:
    """Build independent country processing equations without balancing data."""

    _validate_processing_config(config)
    year = int(config.get("benchmark_year", 2023))
    target = _target_observations(observations, year=year)
    economy_ids = _resolve_economies(target, economies)
    specs = _independent_equations(config)
    series = sorted({key for spec in specs for key, _ in spec.terms})
    values, sources = _observation_lookup(target, series)

    variable_rows: list[dict] = []
    column_by_key: dict[tuple[str, SeriesKey], int] = {}
    for economy in economy_ids:
        for key in series:
            column = len(variable_rows)
            identity = (economy, key)
            observed = identity in values
            column_by_key[identity] = column
            variable_rows.append(
                {
                    "column": column,
                    "economy_id": economy,
                    "commodity": key.commodity,
                    "role": key.role,
                    "account": key.account,
                    "unit": key.unit,
                    "source_domain": sources.get(identity, ""),
                    "observed": observed,
                    "observed_value": values.get(identity, np.nan),
                }
            )

    row_indices: list[int] = []
    column_indices: list[int] = []
    coefficients: list[float] = []
    equation_rows: list[dict] = []
    for economy in economy_ids:
        for spec in specs:
            row = len(equation_rows)
            diagnostic = _equation_diagnostic(economy, spec, values)
            for key, coefficient in spec.terms:
                row_indices.append(row)
                column_indices.append(column_by_key[(economy, key)])
                coefficients.append(coefficient)
            equation_rows.append(
                {
                    "row": row,
                    "chain": spec.chain,
                    "equation_name": spec.name,
                    "kind": spec.kind,
                    "economy_id": economy,
                    "equation": spec.expression,
                    "required_terms": diagnostic["required_terms"],
                    "observed_terms": diagnostic["observed_terms"],
                    "complete": diagnostic["complete"],
                    "observed_residual_mt": diagnostic["residual_mt"],
                }
            )

    matrix = csr_matrix(
        (coefficients, (row_indices, column_indices)),
        shape=(len(equation_rows), len(variable_rows)),
        dtype=np.float64,
    )
    rhs = np.zeros(len(equation_rows), dtype=np.float64)
    return ProcessingConstraintSystem(
        matrix=matrix,
        rhs=rhs,
        variables=pd.DataFrame.from_records(variable_rows),
        equations=pd.DataFrame.from_records(equation_rows),
    )


def _dairy_keys(config: Mapping) -> tuple[SeriesKey, dict[str, SeriesKey]]:
    dairy = config["processing_systems"]["dairy_solids"]
    input_key = _production_key(str(dairy["input"]))
    outputs = {
        str(code): (
            SeriesKey(str(code), "balance", "food")
            if str(code) == "FMK"
            else _production_key(str(code))
        )
        for code in dairy["outputs"]
    }
    return input_key, outputs


def _dairy_country_rows(
    economies: Sequence[str],
    config: Mapping,
    values: Mapping[tuple[str, SeriesKey], float],
) -> list[dict]:
    input_key, outputs = _dairy_keys(config)
    rows: list[dict] = []
    for economy in economies:
        raw_milk = values.get((economy, input_key), np.nan)
        for code, output_key in outputs.items():
            output = values.get((economy, output_key), np.nan)
            complete = np.isfinite(raw_milk) and np.isfinite(output)
            rows.append(
                {
                    "chain": "dairy_solids",
                    "diagnostic": f"{code}_to_raw_milk_ratio",
                    "kind": "ratio_only",
                    "economy_id": economy,
                    "in_constraint_matrix": False,
                    "complete": bool(complete),
                    "observed_terms": int(np.isfinite(raw_milk))
                    + int(np.isfinite(output)),
                    "required_terms": 2,
                    "reference_input_mt": float(raw_milk),
                    "observed_output_mt": float(output),
                    "expected_output_mt": np.nan,
                    "residual_mt": np.nan,
                    "relative_residual": np.nan,
                    "output_input_ratio": (
                        float(output / raw_milk)
                        if complete and raw_milk > 0.0
                        else np.nan
                    ),
                    "equation": (
                        f"diagnostic only: {output_key.label} / {input_key.label}"
                    ),
                }
            )
    return rows


def _global_equation_row(
    spec: EquationSpec,
    country: pd.DataFrame,
    economies: Sequence[str],
    values: Mapping[tuple[str, SeriesKey], float],
) -> dict:
    selected = country[
        country["chain"].eq(spec.chain)
        & country["diagnostic"].eq(spec.name)
    ]
    complete = selected[selected["complete"]]
    paired_input = float(complete["reference_input_mt"].sum())
    total_input = sum(
        values.get((economy, key), 0.0)
        for economy in economies
        for key in spec.reference_inputs
        if np.isfinite(values.get((economy, key), np.nan))
    )
    paired_expected = float(complete["expected_output_mt"].sum())
    paired_residual = float(complete["residual_mt"].sum())

    observed_term_totals: dict[SeriesKey, float] = {}
    observed_term_counts: dict[SeriesKey, int] = {}
    for key, _ in spec.terms:
        available = [
            values[(economy, key)]
            for economy in economies
            if (economy, key) in values
        ]
        observed_term_totals[key] = float(sum(available))
        observed_term_counts[key] = len(available)
    global_observed_residual = sum(
        coefficient * observed_term_totals[key] for key, coefficient in spec.terms
    )
    global_expected = -sum(
        coefficient * observed_term_totals[key]
        for key, coefficient in spec.terms
        if coefficient < 0.0
    )
    observed_cells = sum(observed_term_counts.values())
    required_cells = len(economies) * len(spec.terms)

    return {
        "chain": spec.chain,
        "diagnostic": spec.name,
        "kind": spec.kind,
        "in_constraint_matrix": spec.independent,
        "economy_count": len(economies),
        "countries_with_any_term": int((selected["observed_terms"] > 0).sum()),
        "complete_country_count": int(selected["complete"].sum()),
        "country_completion_rate": float(selected["complete"].mean()),
        "observed_term_cells": int(observed_cells),
        "required_term_cells": int(required_cells),
        "term_coverage_rate": float(observed_cells / required_cells),
        "observed_reference_input_mt": float(total_input),
        "paired_reference_input_mt": paired_input,
        "input_volume_coverage_rate": (
            float(paired_input / total_input) if total_input > 0.0 else np.nan
        ),
        "paired_expected_output_mt": paired_expected,
        "paired_residual_mt": paired_residual,
        "paired_relative_residual": (
            float(paired_residual / paired_expected)
            if paired_expected > 0.0
            else np.nan
        ),
        "all_observed_expected_output_mt": float(global_expected),
        "all_observed_residual_mt": float(global_observed_residual),
        "all_observed_relative_residual": (
            float(global_observed_residual / global_expected)
            if global_expected > 0.0
            else np.nan
        ),
        "equation": spec.expression,
    }


def _global_dairy_rows(
    country: pd.DataFrame,
    economies: Sequence[str],
    config: Mapping,
    values: Mapping[tuple[str, SeriesKey], float],
) -> list[dict]:
    input_key, outputs = _dairy_keys(config)
    rows: list[dict] = []
    for code, output_key in outputs.items():
        diagnostic = f"{code}_to_raw_milk_ratio"
        selected = country[
            country["chain"].eq("dairy_solids")
            & country["diagnostic"].eq(diagnostic)
        ]
        complete = selected[selected["complete"]]
        paired_input = float(complete["reference_input_mt"].sum())
        paired_output = float(complete["observed_output_mt"].sum())
        all_input = sum(
            values[(economy, input_key)]
            for economy in economies
            if (economy, input_key) in values
        )
        all_output = sum(
            values[(economy, output_key)]
            for economy in economies
            if (economy, output_key) in values
        )
        rows.append(
            {
                "chain": "dairy_solids",
                "diagnostic": diagnostic,
                "kind": "ratio_only",
                "in_constraint_matrix": False,
                "economy_count": len(economies),
                "countries_with_any_term": int(
                    (selected["observed_terms"] > 0).sum()
                ),
                "complete_country_count": int(selected["complete"].sum()),
                "country_completion_rate": float(selected["complete"].mean()),
                "observed_term_cells": int(selected["observed_terms"].sum()),
                "required_term_cells": int(2 * len(economies)),
                "term_coverage_rate": float(
                    selected["observed_terms"].sum() / (2 * len(economies))
                ),
                "observed_reference_input_mt": float(all_input),
                "paired_reference_input_mt": paired_input,
                "input_volume_coverage_rate": (
                    float(paired_input / all_input) if all_input > 0.0 else np.nan
                ),
                "paired_expected_output_mt": np.nan,
                "paired_residual_mt": np.nan,
                "paired_relative_residual": (
                    float(paired_output / paired_input)
                    if paired_input > 0.0
                    else np.nan
                ),
                "all_observed_expected_output_mt": np.nan,
                "all_observed_residual_mt": np.nan,
                "all_observed_relative_residual": (
                    float(all_output / all_input) if all_input > 0.0 else np.nan
                ),
                "equation": (
                    f"diagnostic only: {output_key.label} / {input_key.label}"
                ),
            }
        )
    return rows


def _chain_status(
    global_diagnostics: pd.DataFrame,
    country_diagnostics: pd.DataFrame,
    config: Mapping,
) -> pd.DataFrame:
    systems = config["processing_systems"]
    rows: list[dict] = []
    for chain in OILSEED_CHAINS:
        mass = global_diagnostics[
            global_diagnostics["chain"].eq(chain)
            & global_diagnostics["diagnostic"].eq("mass_balance")
        ].iloc[0]
        system = systems[chain]
        input_code = str(system["input"])
        output_equations = "; ".join(
            f"{code}_production = {float(coefficient):.10g} * {input_code}_processing"
            for code, coefficient in system["outputs"].items()
        )
        rows.append(
            {
                "chain": chain,
                "closure_capability": "full_oil_meal_mass_constraint",
                "numeric_constraint_ready": True,
                "full_requested_chain_ready": True,
                "complete_country_count": int(mass["complete_country_count"]),
                "economy_count": int(mass["economy_count"]),
                "term_coverage_rate": float(mass["term_coverage_rate"]),
                "input_volume_coverage_rate": float(
                    mass["input_volume_coverage_rate"]
                ),
                "paired_residual_mt": float(mass["paired_residual_mt"]),
                "paired_relative_residual": float(mass["paired_relative_residual"]),
                "all_observed_residual_mt": float(mass["all_observed_residual_mt"]),
                "all_observed_relative_residual": float(
                    mass["all_observed_relative_residual"]
                ),
                "balancing_equations": output_equations,
                "limitation": (
                    "Country equations with missing source cells require explicit "
                    "balancing variables; missing cells are not structural zeros."
                ),
            }
        )

    sugar = global_diagnostics[
        global_diagnostics["chain"].eq("sugar_refining")
    ].iloc[0]
    sugar_system = systems["sugar_refining"]
    sugar_terms = " + ".join(
        f"{float(coefficient):.10g} * {code}_processing"
        for code, coefficient in sugar_system["inputs"].items()
    )
    rows.append(
        {
            "chain": "sugar_refining",
            "closure_capability": "sugar_output_conversion_constraint",
            "numeric_constraint_ready": True,
            "full_requested_chain_ready": True,
            "complete_country_count": int(sugar["complete_country_count"]),
            "economy_count": int(sugar["economy_count"]),
            "term_coverage_rate": float(sugar["term_coverage_rate"]),
            "input_volume_coverage_rate": float(sugar["input_volume_coverage_rate"]),
            "paired_residual_mt": float(sugar["paired_residual_mt"]),
            "paired_relative_residual": float(sugar["paired_relative_residual"]),
            "all_observed_residual_mt": float(sugar["all_observed_residual_mt"]),
            "all_observed_relative_residual": float(
                sugar["all_observed_relative_residual"]
            ),
            "balancing_equations": f"SUG_production = {sugar_terms}",
            "limitation": (
                "Bagasse, molasses, and refining losses are outside this "
                "output equation."
            ),
        }
    )

    cotton = global_diagnostics[
        global_diagnostics["chain"].eq("cotton_ginning")
    ].iloc[0]
    cotton_system = systems["cotton_ginning"]
    lint = float(cotton_system["outputs"]["CTN"])
    seed = float(cotton_system["outputs"]["cottonseed_satellite"])
    residual = float(cotton_system["residual"])
    rows.append(
        {
            "chain": "cotton_ginning",
            "closure_capability": "lint_yield_constraint_only",
            "numeric_constraint_ready": True,
            "full_requested_chain_ready": False,
            "complete_country_count": int(cotton["complete_country_count"]),
            "economy_count": int(cotton["economy_count"]),
            "term_coverage_rate": float(cotton["term_coverage_rate"]),
            "input_volume_coverage_rate": float(cotton["input_volume_coverage_rate"]),
            "paired_residual_mt": float(cotton["paired_residual_mt"]),
            "paired_relative_residual": float(cotton["paired_relative_residual"]),
            "all_observed_residual_mt": float(cotton["all_observed_residual_mt"]),
            "all_observed_relative_residual": float(
                cotton["all_observed_relative_residual"]
            ),
            "balancing_equations": (
                f"CTN_production = {lint:.10g} * seed_cotton; "
                f"cottonseed_satellite = {seed:.10g} * seed_cotton; "
                f"unmodelled_residual = {residual:.10g} * seed_cotton"
            ),
            "limitation": (
                "The benchmark observes seed cotton and lint but has no "
                "cottonseed_satellite series, so full mass closure is unavailable."
            ),
        }
    )

    dairy = global_diagnostics[global_diagnostics["chain"].eq("dairy_solids")]
    dairy_country = country_diagnostics[
        country_diagnostics["chain"].eq("dairy_solids")
    ]
    fully_observed_dairy = dairy_country.groupby("economy_id")["complete"].all()
    rows.append(
        {
            "chain": "dairy_solids",
            "closure_capability": "output_to_raw_milk_ratios_only",
            "numeric_constraint_ready": False,
            "full_requested_chain_ready": False,
            "complete_country_count": int(fully_observed_dairy.sum()),
            "economy_count": int(dairy["economy_count"].max()),
            "term_coverage_rate": float(dairy["term_coverage_rate"].mean()),
            "input_volume_coverage_rate": float(
                dairy["input_volume_coverage_rate"].min()
            ),
            "paired_residual_mt": np.nan,
            "paired_relative_residual": np.nan,
            "all_observed_residual_mt": np.nan,
            "all_observed_relative_residual": np.nan,
            "balancing_equations": (
                "milk_fat_in_raw_milk = sum(product_quantity * product_fat_share) "
                "+ fat_losses; nonfat_solids_in_raw_milk = "
                "sum(product_quantity * product_snf_share) + snf_losses"
            ),
            "limitation": (
                "Product fat/SNF contents, raw-milk allocation, and losses are "
                "not yet configured; product tonnes cannot be summed as milk mass."
            ),
        }
    )
    return pd.DataFrame.from_records(rows)


def diagnose_processing(
    observations: pd.DataFrame,
    config: Mapping,
    *,
    economies: Sequence[str] | None = None,
) -> ProcessingAudit:
    """Diagnose configured processing chains without modifying observations."""

    _validate_processing_config(config)
    year = int(config.get("benchmark_year", 2023))
    target = _target_observations(observations, year=year)
    economy_ids = _resolve_economies(target, economies)
    independent = _independent_equations(config)
    mass = _mass_diagnostic_equations(config)
    dairy_input, dairy_outputs = _dairy_keys(config)
    relevant_series = {
        key for spec in (*independent, *mass) for key, _ in spec.terms
    } | {dairy_input, *dairy_outputs.values()}
    values, _ = _observation_lookup(target, relevant_series)

    country_rows = [
        _equation_diagnostic(economy, spec, values)
        for economy in economy_ids
        for spec in (*independent, *mass)
    ]
    country_rows.extend(_dairy_country_rows(economy_ids, config, values))
    country = pd.DataFrame.from_records(country_rows)

    global_rows = [
        _global_equation_row(spec, country, economy_ids, values)
        for spec in (*independent, *mass)
    ]
    global_rows.extend(
        _global_dairy_rows(country, economy_ids, config, values)
    )
    global_diagnostics = pd.DataFrame.from_records(global_rows)
    constraints = build_processing_constraints(
        observations,
        config,
        economies=economy_ids,
    )
    status = _chain_status(global_diagnostics, country, config)

    report = {
        "benchmark_year": year,
        "status": "diagnostic_only_no_source_data_modified",
        "economy_count": len(economy_ids),
        "country_diagnostic_rows": int(len(country)),
        "global_diagnostic_rows": int(len(global_diagnostics)),
        "constraint_matrix_rows": int(constraints.matrix.shape[0]),
        "constraint_matrix_columns": int(constraints.matrix.shape[1]),
        "complete_observed_constraint_rows": int(
            constraints.equations["complete"].sum()
        ),
        "chains_with_full_numeric_equations": status.loc[
            status["full_requested_chain_ready"], "chain"
        ].tolist(),
        "chains_without_full_numeric_equations": status.loc[
            ~status["full_requested_chain_ready"], "chain"
        ].tolist(),
        "source_data_modified": False,
    }
    return ProcessingAudit(
        country_diagnostics=country,
        global_diagnostics=global_diagnostics,
        chain_status=status,
        constraints=constraints,
        report=report,
    )


def audit_project(project_root: Path) -> ProcessingAudit:
    """Load the clean project's YAML and unbalanced benchmark for diagnosis."""

    root = Path(project_root).resolve()
    config = load_processing_config(root / "config/commodities.yaml")
    observations = pd.read_csv(
        root / "data/processed/benchmark_unbalanced_2023.csv"
    )
    return diagnose_processing(observations, config)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args()
    audit = audit_project(args.project_root)
    payload = {
        **audit.report,
        "chains": audit.chain_status.replace({np.nan: None}).to_dict(orient="records"),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()


__all__ = [
    "ProcessingAudit",
    "ProcessingConstraintSystem",
    "ProcessingInputError",
    "SeriesKey",
    "audit_project",
    "build_processing_constraints",
    "diagnose_processing",
    "load_processing_config",
]
