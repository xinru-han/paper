"""Jointly balance the 2023 benchmark under market and processing identities.

The projection minimizes weighted squared changes from reported anchors.  It
uses sparse equality constraints and an active set for non-negativity.  Missing
terms required by a processing identity are variables with low statistical
weight; unrelated missing cells remain explicitly labelled inactive rather
than being silently interpreted as reported zeros.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable
import warnings

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, csr_matrix, diags
from scipy.sparse.linalg import MatrixRankWarning, lsmr, spsolve
import yaml


USE_ACCOUNTS = ("food", "feed", "processing", "other_use", "seed", "loss", "residual")
EXPLICIT_PROCESS_INPUTS = frozenset({"SBS", "NBS", "RBS", "SCA", "SBE", "MLK"})
DAIRY_OUTPUTS = ("BUT", "CHE", "NDM", "FMK", "WDM", "ODA")


@dataclass(frozen=True)
class ProjectionResult:
    values: np.ndarray
    residuals: np.ndarray
    active_bound_count: int
    iterations: int


class BalanceInputError(ValueError):
    """Raised when benchmark or balancing inputs are incomplete or malformed."""


def weighted_nonnegative_projection(
    anchors: np.ndarray,
    precisions: np.ndarray,
    matrix: csr_matrix,
    rhs: np.ndarray,
    *,
    nonnegative_tolerance: float = 1.0e-10,
    equality_tolerance: float = 1.0e-8,
    maximum_iterations: int = 50,
) -> ProjectionResult:
    """Project anchors onto ``A x = b, x >= 0`` with diagonal precision.

    The equality projection has a closed-form KKT solution. Variables that
    cross the lower bound are fixed at zero and the equality projection is
    repeated on the remaining variables.
    """

    anchors = np.asarray(anchors, dtype=float)
    precisions = np.asarray(precisions, dtype=float)
    rhs = np.asarray(rhs, dtype=float)
    if anchors.ndim != 1 or precisions.shape != anchors.shape:
        raise BalanceInputError("Anchors and precisions must be equal-length vectors")
    if matrix.shape != (len(rhs), len(anchors)):
        raise BalanceInputError("Constraint matrix dimensions do not match vectors")
    if (
        not np.isfinite(anchors).all()
        or not np.isfinite(precisions).all()
        or not np.isfinite(rhs).all()
        or (anchors < 0).any()
        or (precisions <= 0).any()
    ):
        raise BalanceInputError("Projection inputs must be finite with valid signs")

    fixed = np.zeros(len(anchors), dtype=bool)
    values = anchors.copy()
    for iteration in range(1, maximum_iterations + 1):
        free = ~fixed
        free_matrix = matrix[:, free].tocsr()
        free_anchor = anchors[free]
        inverse_precision = 1.0 / precisions[free]

        # Normalize equality rows by their uncertainty-scaled norm. This does
        # not change the feasible set but greatly improves the KKT solve.
        uncertainty = np.sqrt(inverse_precision)
        row_norm = np.sqrt(
            np.asarray(free_matrix.power(2) @ (uncertainty**2)).ravel()
        )
        nonzero_row = row_norm > 1.0e-18
        if not nonzero_row.all():
            impossible = (~nonzero_row) & (np.abs(rhs) > equality_tolerance)
            if impossible.any():
                raise BalanceInputError("Active bounds made an equality infeasible")
        scale = np.ones_like(row_norm)
        scale[nonzero_row] = 1.0 / row_norm[nonzero_row]
        scaled_matrix = diags(scale) @ free_matrix
        scaled_rhs = rhs * scale

        kkt = scaled_matrix @ diags(inverse_precision) @ scaled_matrix.T
        dual_rhs = np.asarray(scaled_matrix @ free_anchor - scaled_rhs).ravel()
        # The normalized Schur complement is normally nonsingular. Direct
        # sparse solution gives identities close to machine precision; LSMR is
        # retained for rank-deficient but consistent synthetic systems.
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", MatrixRankWarning)
                dual = np.asarray(spsolve(kkt.tocsc(), dual_rhs), dtype=float)
        except Exception:
            dual = np.full_like(dual_rhs, np.nan)
        if not np.isfinite(dual).all():
            dual = lsmr(
                kkt, dual_rhs, atol=1.0e-14, btol=1.0e-14, maxiter=100_000
            )[0]
        free_values = free_anchor - inverse_precision * np.asarray(
            scaled_matrix.T @ dual
        ).ravel()
        # Rank-deficient Schur complements can leave a small numerical
        # equality residual even when the original system is consistent. A
        # minimum-norm correction on A itself restores the identities without
        # changing the statistical projection materially.
        for _ in range(3):
            correction_rhs = rhs - np.asarray(free_matrix @ free_values).ravel()
            if np.max(np.abs(correction_rhs), initial=0.0) <= equality_tolerance / 10:
                break
            correction = lsmr(
                free_matrix,
                correction_rhs,
                atol=1.0e-15,
                btol=1.0e-15,
                maxiter=100_000,
            )[0]
            free_values = free_values + correction
        values[:] = 0.0
        values[free] = free_values

        negative_free = free_values < -nonnegative_tolerance
        if not negative_free.any():
            values[(values < 0) & (values >= -nonnegative_tolerance)] = 0.0
            residuals = np.asarray(matrix @ values - rhs).ravel()
            if np.max(np.abs(residuals), initial=0.0) > equality_tolerance:
                raise BalanceInputError(
                    "Equality projection did not reach the requested tolerance; "
                    f"maximum residual={np.max(np.abs(residuals)):.6g}"
                )
            return ProjectionResult(
                values=values,
                residuals=residuals,
                active_bound_count=int(fixed.sum()),
                iterations=iteration,
            )
        free_indices = np.flatnonzero(free)
        fixed[free_indices[negative_free]] = True

    raise BalanceInputError("Nonnegative projection exceeded its active-set iterations")


def _benchmark_pivot(observations: pd.DataFrame) -> tuple[pd.DataFrame, set[tuple[str, str, str]]]:
    required = {"economy_id", "commodity", "role", "account", "unit", "value"}
    if not required <= set(observations):
        raise BalanceInputError(f"Missing benchmark columns: {sorted(required-set(observations))}")
    balance = observations[
        observations["role"].eq("balance") & observations["unit"].eq("Mt")
    ].copy()
    balance["value"] = pd.to_numeric(balance["value"], errors="coerce")
    if balance.empty or not np.isfinite(balance["value"]).all():
        raise BalanceInputError("Balance observations are empty or non-finite")
    observed = set(
        balance[["economy_id", "commodity", "account"]]
        .astype(str)
        .itertuples(index=False, name=None)
    )
    pivot = balance.pivot_table(
        index=["economy_id", "commodity"], columns="account", values="value", aggfunc="sum"
    )
    return pivot, observed


def _series(pivot: pd.DataFrame, account: str) -> pd.Series:
    if account not in pivot:
        return pd.Series(0.0, index=pivot.index, dtype=float)
    return pivot[account].fillna(0.0).astype(float)


def _raw_anchors(
    observations: pd.DataFrame,
    economies: list[str],
    commodities: list[str],
    *,
    ddg_ratio: float,
    food_commodities: frozenset[str],
) -> tuple[pd.DataFrame, set[tuple[str, str, str]]]:
    pivot, observed = _benchmark_pivot(observations)
    full_index = pd.MultiIndex.from_product(
        [economies, commodities], names=["economy_id", "commodity"]
    )
    pivot = pivot.reindex(full_index)
    production = _series(pivot, "production")
    energy_production = _series(pivot, "energy_production")
    energy_consumption = _series(pivot, "energy_consumption")
    domestic = _series(pivot, "domestic_supply")
    processing = _series(pivot, "processing")
    food = _series(pivot, "food").clip(lower=0.0)
    uses = sum((_series(pivot, name) for name in USE_ACCOUNTS), start=production * 0.0)

    frame = pd.DataFrame(index=full_index)
    frame["source_supply"] = production.clip(lower=0.0)
    product_index = frame.index.get_level_values("commodity")
    bio = product_index.isin(["ETH", "BDI"])
    frame.loc[bio, "source_supply"] = energy_production.loc[bio].clip(lower=0.0)
    fmk = product_index == "FMK"
    frame.loc[fmk, "source_supply"] = _series(pivot, "food").loc[fmk].clip(lower=0.0)

    final = uses.copy()
    has_domestic = domestic.gt(0.0)
    final.loc[has_domestic] = domestic.loc[has_domestic]
    linked_input = product_index.isin(EXPLICIT_PROCESS_INPUTS)
    final.loc[linked_input] = (final.loc[linked_input] - processing.loc[linked_input]).clip(lower=0.0)
    final.loc[bio] = energy_consumption.loc[bio].clip(lower=0.0)
    final = final.clip(lower=0.0)
    edible = product_index.isin(food_commodities)
    frame["source_food_demand"] = 0.0
    frame.loc[edible, "source_food_demand"] = food.loc[edible]
    # The source tables occasionally imply food use slightly above a separately
    # rounded domestic-supply total.  Preserve the observed food component and
    # put only the nonnegative remainder into other final use.
    frame["source_other_final_demand"] = (
        final - frame["source_food_demand"]
    ).clip(lower=0.0)
    frame["source_final_demand"] = (
        frame["source_food_demand"] + frame["source_other_final_demand"]
    )

    # DDG is a transparent derived coproduct and initially clears at its
    # derived output; the joint constraints retain the 0.75 identity exactly.
    ethanol_supply = frame.xs("ETH", level="commodity")["source_supply"]
    ddg_index = pd.MultiIndex.from_product([economies, ["DDG"]], names=full_index.names)
    frame.loc[ddg_index, "source_supply"] = ethanol_supply.reindex(economies).to_numpy() * ddg_ratio
    frame.loc[ddg_index, "source_food_demand"] = 0.0
    frame.loc[ddg_index, "source_other_final_demand"] = ethanol_supply.reindex(economies).to_numpy() * ddg_ratio
    frame.loc[ddg_index, "source_final_demand"] = ethanol_supply.reindex(economies).to_numpy() * ddg_ratio
    return frame.reset_index(), observed


class _SystemBuilder:
    def __init__(self, floor_scale: dict[str, float], uncertainty: dict[str, float]):
        self.floor_scale = floor_scale
        self.uncertainty = uncertainty
        self.variables: list[dict] = []
        self.variable_index: dict[str, int] = {}
        self.rows: list[int] = []
        self.columns: list[int] = []
        self.coefficients: list[float] = []
        self.constraints: list[dict] = []

    def add_variable(
        self,
        name: str,
        *,
        kind: str,
        economy: str,
        commodity: str,
        anchor: float,
        status: str,
        uncertainty_key: str,
    ) -> int:
        if name in self.variable_index:
            return self.variable_index[name]
        relative = float(self.uncertainty[uncertainty_key])
        scale = anchor if anchor > 0 else self.floor_scale.get(commodity, 1.0e-6)
        scale = max(float(scale), 1.0e-9)
        precision = 1.0 / (relative * scale) ** 2
        index = len(self.variables)
        self.variable_index[name] = index
        self.variables.append(
            {
                "name": name,
                "kind": kind,
                "economy_id": economy,
                "commodity": commodity,
                "anchor": float(anchor),
                "anchor_status": status,
                "relative_uncertainty": relative,
                "precision": precision,
            }
        )
        return index

    def add_constraint(self, name: str, kind: str, terms: Iterable[tuple[int, float]]) -> None:
        row = len(self.constraints)
        count = 0
        for column, coefficient in terms:
            if coefficient == 0:
                continue
            self.rows.append(row)
            self.columns.append(int(column))
            self.coefficients.append(float(coefficient))
            count += 1
        if count == 0:
            raise BalanceInputError(f"Empty balancing constraint: {name}")
        self.constraints.append({"name": name, "kind": kind})

    def matrix(self) -> csr_matrix:
        return coo_matrix(
            (self.coefficients, (self.rows, self.columns)),
            shape=(len(self.constraints), len(self.variables)),
        ).tocsr()


def build_joint_balanced_benchmark(
    observations: pd.DataFrame,
    interim_accounts: list[str],
    commodity_config: dict,
    balancing_config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Return a nonnegative 2023 benchmark satisfying all frozen identities."""

    economies = sorted(set(interim_accounts))
    commodities = list(commodity_config["commodities"])
    ddg_ratio = float(
        balancing_config["processing"]["ddg_output_mass_per_mass_ethanol"]
    )
    food_commodities = frozenset(
        balancing_config["final_demand_components"]["food_commodities"]
    )
    if not food_commodities <= set(commodities):
        raise BalanceInputError(
            "Unknown food commodities in final-demand decomposition: "
            f"{sorted(food_commodities - set(commodities))}"
        )
    anchors, observed = _raw_anchors(
        observations,
        economies,
        commodities,
        ddg_ratio=ddg_ratio,
        food_commodities=food_commodities,
    )
    anchor_keyed = anchors.set_index(["economy_id", "commodity"])
    product_totals = anchors.groupby("commodity")[["source_supply", "source_final_demand"]].sum()
    floor_scale = {
        product: max(float(row.max()) / max(len(economies), 1), 1.0e-6)
        for product, row in product_totals.iterrows()
    }
    milk_scale = max(
        float(product_totals.loc["MLK", "source_supply"]) / max(len(economies), 1),
        1.0e-3,
    )
    floor_scale["dairy_fat"] = milk_scale * 0.04
    floor_scale["dairy_snf"] = milk_scale * 0.087
    uncertainty = {
        key: float(value) for key, value in balancing_config["relative_uncertainty"].items()
    }
    builder = _SystemBuilder(floor_scale, uncertainty)
    supply_var: dict[tuple[str, str], int] = {}
    food_var: dict[tuple[str, str], int] = {}
    other_final_var: dict[tuple[str, str], int] = {}

    def ensure_supply(economy: str, product: str, required: bool = False) -> int | None:
        key = (economy, product)
        if key in supply_var:
            return supply_var[key]
        anchor = float(anchor_keyed.at[key, "source_supply"])
        reported = (economy, product, "production") in observed or product in {"ETH", "BDI"}
        if anchor <= 0 and not required:
            return None
        status = "reported_or_domain_anchor" if reported else (
            "derived_anchor" if anchor > 0 else "required_missing_processing_term"
        )
        uncertainty_key = (
            "derived_bioenergy" if product in {"ETH", "BDI", "DDG"}
            else "reported_supply" if anchor > 0
            else "required_missing_term"
        )
        index = builder.add_variable(
            f"S|{economy}|{product}", kind="supply", economy=economy,
            commodity=product, anchor=anchor, status=status,
            uncertainty_key=uncertainty_key,
        )
        supply_var[key] = index
        return index

    def ensure_final(
        economy: str, product: str, required: bool = False
    ) -> tuple[int, ...]:
        key = (economy, product)
        columns: list[int] = []
        food_anchor = float(anchor_keyed.at[key, "source_food_demand"])
        other_anchor = float(anchor_keyed.at[key, "source_other_final_demand"])
        if food_anchor > 0:
            if key not in food_var:
                food_var[key] = builder.add_variable(
                    f"FF|{economy}|{product}", kind="food_demand",
                    economy=economy, commodity=product, anchor=food_anchor,
                    status="reported_food_use",
                    uncertainty_key="reported_food_demand",
                )
            columns.append(food_var[key])
        if other_anchor > 0 or (required and not columns):
            if key not in other_final_var:
                other_final_var[key] = builder.add_variable(
                    f"FO|{economy}|{product}", kind="other_final_demand",
                    economy=economy, commodity=product, anchor=other_anchor,
                    status=(
                        "reported_or_derived_other_final_use"
                        if other_anchor > 0
                        else "required_missing_demand_term"
                    ),
                    uncertainty_key=(
                        "reported_other_final_demand"
                        if other_anchor > 0
                        else "required_missing_term"
                    ),
                )
            columns.append(other_final_var[key])
        return tuple(columns)

    for row in anchors.itertuples(index=False):
        ensure_supply(row.economy_id, row.commodity)
        ensure_final(row.economy_id, row.commodity)

    pivot, _ = _benchmark_pivot(observations)
    activity_obs = observations[
        observations["role"].eq("activity")
        & observations["account"].eq("production")
        & observations["unit"].eq("Mt")
    ].groupby(["economy_id", "commodity"])["value"].sum()
    process_var: dict[tuple[str, str], int] = {}
    process_consumption: dict[str, list[int]] = {product: [] for product in commodities}

    def process_anchor(economy: str, product: str) -> float:
        key = (economy, product)
        return float(pivot.at[key, "processing"]) if key in pivot.index and "processing" in pivot and pd.notna(pivot.at[key, "processing"]) else 0.0

    systems = commodity_config["processing_systems"]
    oil_specs = (
        ("soybean_crush", "SBS"),
        ("sunflower_crush", "NBS"),
        ("rapeseed_crush", "RBS"),
    )
    for process, input_product in oil_specs:
        outputs = systems[process]["outputs"]
        for economy in economies:
            input_anchor = process_anchor(economy, input_product)
            active = input_anchor > 0 or any(
                float(anchor_keyed.at[(economy, output), "source_supply"]) > 0
                for output in outputs
            )
            if not active:
                continue
            x = builder.add_variable(
                f"X|{economy}|{process}", kind="processing_activity",
                economy=economy, commodity=input_product, anchor=input_anchor,
                status="reported_processing" if input_anchor > 0 else "required_missing_processing_term",
                uncertainty_key="reported_processing_activity" if input_anchor > 0 else "required_missing_term",
            )
            process_var[(economy, process)] = x
            process_consumption[input_product].append(x)
            for output, coefficient in outputs.items():
                supply = ensure_supply(economy, output, required=True)
                builder.add_constraint(
                    f"{economy}:{process}:{output}", "processing_identity",
                    [(supply, 1.0), (x, -float(coefficient))],
                )

    sugar = systems["sugar_refining"]
    for economy in economies:
        raw = {product: process_anchor(economy, product) for product in sugar["inputs"]}
        output_anchor = float(anchor_keyed.at[(economy, sugar["output"]), "source_supply"])
        if output_anchor <= 0 and not any(value > 0 for value in raw.values()):
            continue
        terms: list[tuple[int, float]] = [
            (ensure_supply(economy, sugar["output"], required=True), 1.0)
        ]
        for product, coefficient in sugar["inputs"].items():
            x = builder.add_variable(
                f"X|{economy}|sugar_{product}", kind="processing_activity",
                economy=economy, commodity=product, anchor=raw[product],
                status="reported_processing" if raw[product] > 0 else "required_missing_processing_term",
                uncertainty_key="reported_processing_activity" if raw[product] > 0 else "required_missing_term",
            )
            process_var[(economy, f"sugar_{product}")] = x
            process_consumption[product].append(x)
            terms.append((x, -float(coefficient)))
        builder.add_constraint(
            f"{economy}:sugar_refining:SUG", "processing_identity", terms
        )

    cotton = systems["cotton_ginning"]
    cotton_yield = float(cotton["outputs"]["CTN"])
    for economy in economies:
        seed_anchor = float(activity_obs.get((economy, "CTN"), 0.0))
        lint_anchor = float(anchor_keyed.at[(economy, "CTN"), "source_supply"])
        if seed_anchor <= 0 and lint_anchor <= 0:
            continue
        x = builder.add_variable(
            f"X|{economy}|cotton_ginning", kind="satellite_activity",
            economy=economy, commodity="seed_cotton", anchor=seed_anchor,
            status="reported_seed_cotton" if seed_anchor > 0 else "required_missing_seed_cotton",
            uncertainty_key="reported_processing_activity" if seed_anchor > 0 else "required_missing_term",
        )
        process_var[(economy, "cotton_ginning")] = x
        builder.add_constraint(
            f"{economy}:cotton_ginning:CTN", "processing_identity",
            [(ensure_supply(economy, "CTN", required=True), 1.0), (x, -cotton_yield)],
        )

    # Ethanol and DDG are country-level coproducts.
    for economy in economies:
        eth = ensure_supply(economy, "ETH")
        if eth is None:
            continue
        ddg = ensure_supply(economy, "DDG", required=True)
        ensure_final(economy, "DDG", required=True)
        builder.add_constraint(
            f"{economy}:ethanol:DDG", "processing_identity",
            [(ddg, 1.0), (eth, -ddg_ratio)],
        )

    dairy = balancing_config["processing"]["dairy"]
    raw_fat = float(dairy["raw_milk"]["fat_share"])
    raw_snf = float(dairy["raw_milk"]["nonfat_solids_share"])
    composition = dairy["product_composition"]
    whey_ratio = float(dairy["dry_whey_output_per_cheese"])
    for economy in economies:
        active = float(anchor_keyed.at[(economy, "MLK"), "source_supply"]) > 0 or any(
            float(anchor_keyed.at[(economy, product), "source_supply"]) > 0
            for product in DAIRY_OUTPUTS
        )
        if not active:
            continue
        milk_anchor = float(anchor_keyed.at[(economy, "MLK"), "source_supply"])
        milk = builder.add_variable(
            f"X|{economy}|dairy_milk", kind="processing_activity",
            economy=economy, commodity="MLK", anchor=milk_anchor,
            status="raw_milk_production_proxy" if milk_anchor > 0 else "required_missing_processing_term",
            uncertainty_key="reported_processing_activity" if milk_anchor > 0 else "required_missing_term",
        )
        process_var[(economy, "dairy_milk")] = milk
        process_consumption["MLK"].append(milk)
        output_vars = {
            product: ensure_supply(economy, product, required=True)
            for product in DAIRY_OUTPUTS
        }
        builder.add_constraint(
            f"{economy}:dairy:dry_whey", "processing_identity",
            [(output_vars["ODA"], 1.0), (output_vars["CHE"], -whey_ratio)],
        )
        slack_fat = builder.add_variable(
            f"Z|{economy}|dairy_fat", kind="unmodelled_dairy_solids",
            economy=economy, commodity="dairy_fat", anchor=0.0,
            status="explicit_unmodelled_output_or_loss",
            uncertainty_key="unmodelled_dairy_solids",
        )
        slack_snf = builder.add_variable(
            f"Z|{economy}|dairy_snf", kind="unmodelled_dairy_solids",
            economy=economy, commodity="dairy_snf", anchor=0.0,
            status="explicit_unmodelled_output_or_loss",
            uncertainty_key="unmodelled_dairy_solids",
        )
        builder.add_constraint(
            f"{economy}:dairy:fat", "dairy_solids_identity",
            [(milk, raw_fat)]
            + [(output_vars[p], -float(composition[p]["fat_share"])) for p in DAIRY_OUTPUTS]
            + [(slack_fat, -1.0)],
        )
        builder.add_constraint(
            f"{economy}:dairy:snf", "dairy_solids_identity",
            [(milk, raw_snf)]
            + [(output_vars[p], -float(composition[p]["nonfat_solids_share"])) for p in DAIRY_OUTPUTS]
            + [(slack_snf, -1.0)],
        )

    # One non-spatial world-clearing equation per commodity. Processing inputs
    # enter demand only once and therefore cannot be hidden in final use.
    for product in commodities:
        terms: list[tuple[int, float]] = []
        for economy in economies:
            supply = ensure_supply(economy, product)
            final = ensure_final(economy, product)
            if supply is not None:
                terms.append((supply, 1.0))
            terms.extend((column, -1.0) for column in final)
        terms.extend((column, -1.0) for column in process_consumption[product])
        builder.add_constraint(f"WORLD:{product}", "world_market", terms)

    variables = pd.DataFrame.from_records(builder.variables)
    matrix = builder.matrix()
    settings = balancing_config["active_set"]
    projection = weighted_nonnegative_projection(
        variables["anchor"].to_numpy(float),
        variables["precision"].to_numpy(float),
        matrix,
        np.zeros(matrix.shape[0]),
        nonnegative_tolerance=float(settings["nonnegative_tolerance"]),
        equality_tolerance=float(settings["equality_tolerance"]),
        maximum_iterations=int(settings["maximum_iterations"]),
    )
    variables["balanced_value"] = projection.values
    variables["absolute_adjustment"] = variables["balanced_value"] - variables["anchor"]
    variables["relative_adjustment"] = np.where(
        variables["anchor"].gt(0),
        variables["absolute_adjustment"] / variables["anchor"],
        np.nan,
    )

    values = dict(zip(variables["name"], variables["balanced_value"]))
    activity_rows: list[dict] = []
    process_demand: dict[tuple[str, str], float] = {}
    for (economy, process), column in process_var.items():
        row = variables.iloc[column]
        value = float(projection.values[column])
        activity_rows.append(
            {
                "economy_id": economy,
                "process": process,
                "input_or_activity": row["commodity"],
                "source_activity_2023": float(row["anchor"]),
                "balanced_activity_2023": value,
                "anchor_status": row["anchor_status"],
            }
        )
        if row["commodity"] in commodities and process != "cotton_ginning":
            key = (economy, row["commodity"])
            process_demand[key] = process_demand.get(key, 0.0) + value

    benchmark_rows: list[dict] = []
    for row in anchors.itertuples(index=False):
        supply = float(values.get(f"S|{row.economy_id}|{row.commodity}", 0.0))
        food = float(values.get(f"FF|{row.economy_id}|{row.commodity}", 0.0))
        other_final = float(values.get(f"FO|{row.economy_id}|{row.commodity}", 0.0))
        final = food + other_final
        processing_demand = float(process_demand.get((row.economy_id, row.commodity), 0.0))
        total_demand = final + processing_demand
        benchmark_rows.append(
            {
                "economy_id": row.economy_id,
                "commodity": row.commodity,
                "source_supply_2023": row.source_supply,
                "source_final_demand_2023": row.source_final_demand,
                "source_food_demand_2023": row.source_food_demand,
                "source_other_final_demand_2023": row.source_other_final_demand,
                "supply_2023": supply,
                "food_demand_2023": food,
                "other_final_demand_2023": other_final,
                "final_demand_2023": final,
                "processing_demand_2023": processing_demand,
                "demand_2023": total_demand,
                "net_import_2023": total_demand - supply,
                "price_index_2023": 1.0,
                "structural_supply_zero": supply == 0.0 and row.source_supply == 0.0,
                "structural_final_demand_zero": final == 0.0 and row.source_final_demand == 0.0,
                "zero_status": (
                    "positive_or_inferred"
                    if supply > 0 or final > 0 or processing_demand > 0
                    else "unobserved_inactive_or_observed_zero"
                ),
            }
        )
    benchmark = pd.DataFrame.from_records(benchmark_rows)
    activities = pd.DataFrame.from_records(activity_rows)
    constraints = pd.DataFrame.from_records(builder.constraints)
    constraints["residual_mt"] = projection.residuals

    market_residual = benchmark.groupby("commodity")["net_import_2023"].sum()
    process_residual = constraints.loc[
        ~constraints["kind"].eq("world_market"), "residual_mt"
    ]
    adjusted = variables[variables["anchor"].gt(0)]["relative_adjustment"].abs()
    inferred = variables[
        variables["anchor"].eq(0) & variables["balanced_value"].gt(1.0e-12)
    ]
    gate = balancing_config["publication_gate"]
    numeric_gate = (
        market_residual.abs().max() <= float(gate["maximum_market_residual_mt"])
        and process_residual.abs().max() <= float(gate["maximum_processing_residual_mt"])
        and adjusted.quantile(0.95) <= float(gate["maximum_p95_relative_adjustment"])
    )
    review = balancing_config["domain_review"]
    cotton_rows = variables[variables["kind"].eq("satellite_activity")]
    cotton_missing = cotton_rows[
        cotton_rows["anchor_status"].eq("required_missing_seed_cotton")
    ]
    cotton_material_threshold = float(
        review["cotton_missing_activity_materiality_mt"]
    )
    material_missing_cotton = cotton_missing[
        cotton_missing["balanced_value"].ge(cotton_material_threshold)
    ]
    cotton_yield = float(
        commodity_config["processing_systems"]["cotton_ginning"]["outputs"]["CTN"]
    )
    cotton_range = review["cotton_ginning_outturn_review_range"]
    cotton_review_passed = (
        bool(review["cotton_chain_internal_review_completed"])
        and material_missing_cotton.empty
        and float(cotton_range["minimum"])
        <= cotton_yield
        <= float(cotton_range["maximum"])
    )

    dairy_rows = variables[variables["kind"].eq("unmodelled_dairy_solids")]
    dairy_activity = variables[
        variables["kind"].eq("processing_activity")
        & variables["commodity"].eq("MLK")
    ]["balanced_value"].sum()
    raw_dairy_solids = dairy_activity * (raw_fat + raw_snf)
    unmodelled_dairy_solids = dairy_rows["balanced_value"].sum()
    unmodelled_dairy_share = (
        float(unmodelled_dairy_solids / raw_dairy_solids)
        if raw_dairy_solids > 0
        else 0.0
    )
    dairy_review_passed = (
        bool(review["dairy_coefficients_internal_review_completed"])
        and unmodelled_dairy_share
        <= float(review["maximum_unmodelled_dairy_solids_share"])
    )
    reviewed_gate = (
        bool(gate["internal_domain_review_required"])
        and cotton_review_passed
        and dairy_review_passed
        and bool(
            review[
                "high_adjustment_cells_reviewed_as_explicit_cross_dataset_reconciliation"
            ]
        )
    )
    passed = bool(numeric_gate and reviewed_gate)
    report = {
        "status": "passed" if passed else "jointly_balanced_requires_domain_review",
        "economy_count": len(economies),
        "commodity_count": len(commodities),
        "row_count": int(len(benchmark)),
        "variable_count": int(len(variables)),
        "constraint_count": int(len(constraints)),
        "world_market_constraint_count": int(constraints["kind"].eq("world_market").sum()),
        "processing_constraint_count": int((~constraints["kind"].eq("world_market")).sum()),
        "maximum_world_market_residual_mt": float(market_residual.abs().max()),
        "maximum_processing_residual_mt": float(process_residual.abs().max()),
        "median_absolute_relative_adjustment": float(adjusted.median()),
        "p95_absolute_relative_adjustment": float(adjusted.quantile(0.95)),
        "maximum_absolute_relative_adjustment": float(adjusted.max()),
        "explicitly_inferred_variable_count": int(len(inferred)),
        "active_nonnegative_bound_count": projection.active_bound_count,
        "active_set_iterations": projection.iterations,
        "numeric_gate_passed": bool(numeric_gate),
        "domain_review_gate_passed": bool(reviewed_gate),
        "cotton_ginning_outturn": cotton_yield,
        "cotton_missing_activity_count": int(len(cotton_missing)),
        "cotton_material_missing_activity_count": int(len(material_missing_cotton)),
        "cotton_missing_activity_materiality_mt": cotton_material_threshold,
        "cotton_chain_internal_review_passed": bool(cotton_review_passed),
        "unmodelled_dairy_solids_mt": float(unmodelled_dairy_solids),
        "unmodelled_dairy_solids_share": unmodelled_dairy_share,
        "dairy_coefficients_internal_review_passed": bool(dairy_review_passed),
        "internal_review_not_independent_peer_review": True,
        "publishable": passed,
        "silent_missing_to_zero": False,
        "next_gate": (
            "external_validation_and_sensitivity_analysis"
            if passed
            else "review_dairy_solids_cottonseed_and_high_adjustment_cells"
        ),
    }
    return benchmark, activities, variables, report


def build_project_benchmark(project_root: Path) -> dict:
    root = project_root.resolve()
    observations = pd.read_csv(root / "data/processed/benchmark_unbalanced_2023.csv")
    interim = pd.read_csv(root / "data/processed/benchmark_equilibrium_interim_2023.csv")
    commodities = yaml.safe_load((root / "config/commodities.yaml").read_text(encoding="utf-8"))
    balancing = yaml.safe_load((root / "config/balancing.yaml").read_text(encoding="utf-8"))
    benchmark, activities, variables, report = build_joint_balanced_benchmark(
        observations,
        interim["economy_id"].unique().tolist(),
        commodities,
        balancing,
    )
    processed = root / "data/processed"
    benchmark_path = processed / "benchmark_equilibrium_2023.csv"
    activities_path = processed / "benchmark_processing_activities_2023.csv"
    adjustments_path = processed / "benchmark_balancing_adjustments_2023.csv"
    benchmark.to_csv(benchmark_path, index=False)
    activities.to_csv(activities_path, index=False)
    variables.to_csv(adjustments_path, index=False)
    report.update(
        {
            "benchmark_output": str(benchmark_path),
            "activities_output": str(activities_path),
            "adjustments_output": str(adjustments_path),
        }
    )
    (processed / "benchmark_equilibrium_report_2023.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    print(json.dumps(build_project_benchmark(args.project_root), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
