"""Build the complete CASM-World V2 own-price and income parameter table.

PEATSim is treated only as a frozen prior snapshot.  Its regional values are
collapsed to commodity medians before any CASM account is considered. Crop
supply combines aligned intensive- and extensive-margin responses. Final
demand combines food, feed, and other-use components with observed 2023 use
shares. CASM then applies explicit product-class, processing-chain, and World
Bank income-group rules. Missing values are errors; zero behavioural demand
parameters occur only for an explicitly zero balanced final-demand account.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from math import exp, isfinite, log
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from casm_world.paths import load_source_catalog, verify_source
from casm_world.reporting import (
    build_model_account_membership,
    load_reporting_config,
    load_world_bank_income_groups,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "parameters.yaml"
EXPECTED_ACCOUNTS = 193
EXPECTED_COMMODITIES = 31
EXPECTED_ROWS = EXPECTED_ACCOUNTS * EXPECTED_COMMODITIES
INCOME_GROUPS = ("LIC", "LMC", "UMC", "HIC", "NCL")


@dataclass(frozen=True)
class FrozenPriorTables:
    """Commodity medians extracted from the frozen PEATSim workbook."""

    ela_supply: Mapping[str, float]
    crop_total_supply_low: Mapping[str, float]
    crop_total_supply: Mapping[str, float]
    crop_total_supply_high: Mapping[str, float]
    meat_supply: Mapping[str, float]
    dairy_supply: Mapping[str, float]
    food_demand: Mapping[str, float]
    feed_demand: Mapping[str, float]
    income: Mapping[str, float]


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _project_path(project_root: Path, relative: str, label: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValueError(f"{label} must be relative to the clean project")
    root = project_root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the clean project: {candidate}") from exc
    return resolved


def _route_coverage(routes: Mapping[str, Any], family: str) -> dict[str, str]:
    """Return one route label per commodity and reject overlaps."""

    assigned: dict[str, str] = {}

    def add(products: Sequence[object], route: str) -> None:
        for raw_product in products:
            product = str(raw_product).strip().upper()
            if product in assigned:
                raise ValueError(
                    f"{family} prior route overlaps for {product}: "
                    f"{assigned[product]} and {route}"
                )
            assigned[product] = route

    for route, raw_spec in routes.items():
        if isinstance(raw_spec, list):
            add(raw_spec, str(route))
        elif route == "peatsim_dairy_milk_geometric_blend":
            spec = _mapping(raw_spec, f"{family}.{route}")
            products = spec.get("products")
            if not isinstance(products, list):
                raise ValueError(f"{family}.{route}.products must be a list")
            add(products, str(route))
        else:
            spec = _mapping(raw_spec, f"{family}.{route}")
            add(list(spec), str(route))
    return assigned


def load_parameter_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and strictly validate the frozen CASM parameter specification."""

    config_path = Path(path).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config = dict(_mapping(config, "parameter configuration"))
    if config.get("schema_version") != 2:
        raise ValueError("parameters.yaml schema_version must equal 2")
    if config.get("parameter_set") != "CASM_WORLD_ELASTICITIES_V2":
        raise ValueError("Unexpected CASM parameter-set identifier")
    if int(config.get("benchmark_year", -1)) != 2023:
        raise ValueError("CASM parameter benchmark year must equal 2023")

    sources = _mapping(config.get("sources"), "sources")
    if sources.get("frozen_prior_catalog_key") != "peatsim_parameter_priors":
        raise ValueError("Frozen prior must use the catalogued PEATSim snapshot")
    if sources.get("income_interface") != "WB_INCOME_FY25_via_reporting_module":
        raise ValueError("Income adjustment must use the formal reporting interface")
    gate = _mapping(config.get("coverage_gate"), "coverage_gate")
    expected = (
        int(gate.get("expected_model_accounts", -1)),
        int(gate.get("expected_commodities", -1)),
        int(gate.get("expected_rows", -1)),
    )
    if expected != (EXPECTED_ACCOUNTS, EXPECTED_COMMODITIES, EXPECTED_ROWS):
        raise ValueError("Parameter coverage gate must be 193 x 31 = 5983")
    if gate.get("missing_to_zero") != "forbidden":
        raise ValueError("Missing-to-zero parameter conversion must remain forbidden")

    roles = _mapping(config.get("chain_roles"), "chain_roles")
    if len(roles) != EXPECTED_COMMODITIES:
        raise ValueError("Exactly 31 commodity chain roles are required")
    route_families = (
        "supply_prior_routes",
        "food_price_prior_routes",
        "food_income_prior_routes",
        "feed_price_prior_routes",
    )
    commodity_set = set(roles)
    for family in route_families:
        coverage = _route_coverage(_mapping(config.get(family), family), family)
        if set(coverage) != commodity_set:
            raise ValueError(
                f"{family} must cover exactly the 31 commodities; "
                f"missing={sorted(commodity_set-set(coverage))}, "
                f"extra={sorted(set(coverage)-commodity_set)}"
            )

    composite = _mapping(
        config.get("final_demand_use_share_composite"),
        "final_demand_use_share_composite",
    )
    if composite.get("balanced_food_numerator") != "food_demand_2023":
        raise ValueError("Food share must use balanced 2023 food demand")
    if composite.get("balanced_total_denominator") != "final_demand_2023":
        raise ValueError("Food share must use balanced 2023 total final demand")
    positive_accounts = composite.get("positive_nonprocessing_nonfood_accounts")
    if positive_accounts != ["feed", "seed", "loss", "other_use", "energy_consumption"]:
        raise ValueError("Unexpected non-processing non-food use-account definition")
    if composite.get("explicit_feed_products") != ["DDG", "SBM", "NBM", "RBM"]:
        raise ValueError("DDG and the three oil meals must remain explicit feed uses")
    price_components = _mapping(composite.get("price_components"), "price_components")
    income_components = _mapping(composite.get("income_components"), "income_components")
    if float(price_components.get("other_use_author_prior_magnitude", -1)) != 0.10:
        raise ValueError("Other-use price prior magnitude must equal 0.10")
    if float(income_components.get("feed_author_prior", -1)) != 0.40:
        raise ValueError("Feed income prior must equal 0.40")
    if float(income_components.get("other_use_author_prior", -1)) != 0.10:
        raise ValueError("Other-use income prior must equal 0.10")
    envelope = _mapping(
        config.get("parameter_response_envelope"), "parameter_response_envelope"
    )
    if envelope.get("sets") != [
        "V2_LOW_RESPONSE",
        "V2_CENTRAL",
        "V2_HIGH_RESPONSE",
    ]:
        raise ValueError("Unexpected V2 parameter-response set identifiers")
    if envelope.get("crop_supply_quantiles") != {
        "low": 0.25,
        "central": 0.5,
        "high": 0.75,
    }:
        raise ValueError("Crop response envelope must use P25/median/P75")
    if envelope.get("feed_price_magnitude_factors") != {
        "low": 0.75,
        "central": 1.0,
        "high": 1.25,
    }:
        raise ValueError("Feed response envelope must use 0.75/1.00/1.25")

    class_rules = _mapping(config.get("class_rules"), "class_rules")
    for class_name, raw_rule in class_rules.items():
        rule = _mapping(raw_rule, f"class_rules.{class_name}")
        for parameter in ("supply", "demand", "income", "transmission"):
            _mapping(rule.get(parameter), f"class_rules.{class_name}.{parameter}")
    adjustments = _mapping(
        config.get("income_group_adjustments"), "income_group_adjustments"
    )
    if set(adjustments) != set(INCOME_GROUPS):
        raise ValueError("Income adjustments must cover LIC/LMC/UMC/HIC/NCL")
    if adjustments["NCL"].get("status") != "explicit_not_classified_fallback":
        raise ValueError("NCL must remain an explicit, labelled fallback")
    return config


def _median_by_product(
    frame: pd.DataFrame,
    product_column: str,
    value_column: str,
    *,
    positive: bool,
) -> dict[str, float]:
    work = frame[[product_column, value_column]].copy()
    work[product_column] = (
        work[product_column].astype("string").str.strip().str.upper()
    )
    work[value_column] = pd.to_numeric(work[value_column], errors="coerce")
    work = work[
        work[product_column].str.fullmatch(r"[A-Z]{3}", na=False)
        & work[value_column].map(lambda value: pd.notna(value) and isfinite(float(value)))
    ]
    if positive:
        work = work[work[value_column].gt(0)]
    else:
        work = work[work[value_column].lt(0)]
    medians = work.groupby(product_column)[value_column].median()
    return {str(key): float(value) for key, value in medians.items()}


def _diagonal_matrix_medians(path: Path, sheet: str) -> dict[str, float]:
    frame = pd.read_excel(path, sheet_name=sheet, header=0)
    if frame.shape[1] < 3:
        raise ValueError(f"PEATSim sheet {sheet} lacks its regional matrix")
    row_product = frame.iloc[:, 0].astype("string").str.strip().str.upper()
    column_product = frame.iloc[:, 1].astype("string").str.strip().str.upper()
    diagonal = frame.loc[row_product.eq(column_product)].copy()
    diagonal.insert(0, "_product", row_product[row_product.eq(column_product)].values)
    numeric = diagonal.iloc[:, 3:].apply(pd.to_numeric, errors="coerce")
    values = numeric.median(axis=1, skipna=True)
    result = {
        str(product): float(value)
        for product, value in zip(diagonal["_product"], values)
        if pd.notna(product)
        and pd.notna(value)
        and isfinite(float(value))
        and float(value) > 0
    }
    return result


def _aligned_crop_total_supply_medians(
    workbook: Path, ela: pd.DataFrame
) -> dict[str, dict[str, float]]:
    """Median of region-aligned ``ela.supela + yahela own diagonal``.

    Taking the two component medians separately would destroy their regional
    covariance.  The long-run total-production response is therefore summed
    inside each common frozen PEATSim region before the commodity median is
    calculated.
    """

    supply = ela[["product", "region", "supply"]].copy()
    supply["product"] = supply["product"].astype("string").str.strip().str.upper()
    supply["region"] = supply["region"].astype("string").str.strip().str.lower()
    supply["supply"] = pd.to_numeric(supply["supply"], errors="coerce")
    supply = supply[
        supply["product"].str.fullmatch(r"[A-Z]{3}", na=False)
        & supply["region"].ne("")
        & supply["supply"].map(
            lambda value: pd.notna(value)
            and isfinite(float(value))
            and float(value) > 0
        )
    ]
    if supply.duplicated(["product", "region"]).any():
        raise ValueError("PEATSim ela has duplicate product-region supply priors")

    yahela = pd.read_excel(workbook, sheet_name="yahela", header=0)
    if yahela.shape[1] < 3:
        raise ValueError("PEATSim yahela sheet lacks its regional matrix")
    row_product = yahela.iloc[:, 0].astype("string").str.strip().str.upper()
    column_product = yahela.iloc[:, 1].astype("string").str.strip().str.upper()
    diagonal = yahela.loc[row_product.eq(column_product)].copy()
    diagonal.insert(0, "_product", row_product[row_product.eq(column_product)].values)
    area = diagonal.melt(
        id_vars=["_product", diagonal.columns[1], diagonal.columns[2]],
        value_vars=list(diagonal.columns[3:]),
        var_name="region",
        value_name="area_response",
    )[["_product", "region", "area_response"]].rename(
        columns={"_product": "product"}
    )
    area["region"] = area["region"].astype("string").str.strip().str.lower()
    area["area_response"] = pd.to_numeric(area["area_response"], errors="coerce")
    area = area[
        area["area_response"].map(
            lambda value: pd.notna(value)
            and isfinite(float(value))
            and float(value) > 0
        )
    ]
    if area.duplicated(["product", "region"]).any():
        raise ValueError("PEATSim yahela has duplicate own-diagonal product-region priors")

    aligned = supply.merge(
        area, on=["product", "region"], how="inner", validate="one_to_one"
    )
    aligned["total_response"] = aligned["supply"] + aligned["area_response"]
    counts = aligned.groupby("product")["total_response"].size()
    if (counts < 1).any():
        raise ValueError("A crop total-supply prior lacks a common PEATSim region")
    return {
        variant: {
            str(product): float(value)
            for product, value in aligned.groupby("product")["total_response"]
            .quantile(quantile)
            .items()
        }
        for variant, quantile in (("low", 0.25), ("central", 0.50), ("high", 0.75))
    }


def _feed_own_price_medians(workbook: Path) -> dict[str, float]:
    """Reduce fedela own-price rows to signed feed-input commodity medians."""

    fedela = pd.read_excel(workbook, sheet_name="fedela", header=0)
    if fedela.shape[1] < 4:
        raise ValueError("PEATSim fedela sheet lacks its livestock-feed matrix")
    feed_input = fedela.iloc[:, 1].astype("string").str.strip().str.upper()
    price_input = fedela.iloc[:, 2].astype("string").str.strip().str.upper()
    diagonal = fedela.loc[feed_input.eq(price_input)].copy()
    diagonal.insert(0, "_feed", feed_input[feed_input.eq(price_input)].values)
    regional = diagonal.iloc[:, 4:].apply(pd.to_numeric, errors="coerce")
    # An own feed-price response must be negative. Structural zeros and any
    # cross-price values are not admissible substitutes for the own response.
    regional = regional.where(regional.lt(0.0))
    livestock_row_median = regional.median(axis=1, skipna=True)
    reduced = pd.DataFrame(
        {"feed": diagonal["_feed"].to_numpy(), "value": livestock_row_median}
    ).dropna(subset=["value"])
    medians = reduced.groupby("feed")["value"].median()
    return {
        str(product): float(value)
        for product, value in medians.items()
        if isfinite(float(value)) and float(value) < 0
    }


def read_frozen_peatsim_priors(path: str | Path) -> FrozenPriorTables:
    """Extract finite commodity medians, never PEATSim regional parameters."""

    workbook = Path(path)
    if not workbook.is_file():
        raise ValueError(f"Frozen PEATSim prior workbook is absent: {workbook}")

    ela = pd.read_excel(workbook, sheet_name="ela", header=None, usecols=range(5))
    ela.columns = ["product", "region", "supply", "input", "import"]
    ela_supply = _median_by_product(
        ela, "product", "supply", positive=True
    )
    crop_total_supply = _aligned_crop_total_supply_medians(workbook, ela)

    fodela = pd.read_excel(
        workbook,
        sheet_name="fodela",
        header=None,
        usecols=range(4),
        names=["row_product", "column_product", "region", "value"],
    )
    rows = fodela["row_product"].astype("string").str.strip().str.upper()
    columns = fodela["column_product"].astype("string").str.strip().str.upper()
    diagonal = fodela.loc[rows.eq(columns)].copy()
    diagonal["product"] = rows[rows.eq(columns)].values
    food_demand = _median_by_product(
        diagonal, "product", "value", positive=False
    )

    gdpela = pd.read_excel(workbook, sheet_name="GDPELA", header=0)
    if gdpela.shape[1] < 14:
        raise ValueError("PEATSim GDPELA sheet lacks the frozen regional columns")
    products = gdpela.iloc[:, 0].astype("string").str.strip().str.upper()
    regional = gdpela.iloc[:, 1:14].apply(pd.to_numeric, errors="coerce")
    income_values = regional.median(axis=1, skipna=True)
    income = {
        str(product): float(value)
        for product, value in zip(products, income_values)
        if pd.notna(product)
        and pd.notna(value)
        and isfinite(float(value))
        and float(value) > 0
    }

    meat_supply = _diagonal_matrix_medians(workbook, "metelap")
    dairy_supply = _diagonal_matrix_medians(workbook, "daielap")
    feed_demand = _feed_own_price_medians(workbook)
    return FrozenPriorTables(
        ela_supply=ela_supply,
        crop_total_supply_low=crop_total_supply["low"],
        crop_total_supply=crop_total_supply["central"],
        crop_total_supply_high=crop_total_supply["high"],
        meat_supply=meat_supply,
        dairy_supply=dairy_supply,
        food_demand=food_demand,
        feed_demand=feed_demand,
        income=income,
    )


def _positive(value: object, label: str) -> float:
    number = float(value)
    if not isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return number


def _negative(value: object, label: str) -> float:
    number = float(value)
    if not isfinite(number) or number >= 0:
        raise ValueError(f"{label} must be finite and negative")
    return number


def _route_lookup(routes: Mapping[str, Any]) -> dict[str, tuple[str, Any]]:
    lookup: dict[str, tuple[str, Any]] = {}
    for method, raw_spec in routes.items():
        if isinstance(raw_spec, list):
            for product in raw_spec:
                lookup[str(product).upper()] = (str(method), None)
        elif method == "peatsim_dairy_milk_geometric_blend":
            spec = _mapping(raw_spec, str(method))
            for product in spec["products"]:
                lookup[str(product).upper()] = (str(method), spec)
        else:
            spec = _mapping(raw_spec, str(method))
            for product, route_spec in spec.items():
                lookup[str(product).upper()] = (str(method), route_spec)
    return lookup


def _resolve_family(
    products: Sequence[str],
    routes: Mapping[str, Any],
    direct_sources: Mapping[str, Mapping[str, float]],
    *,
    sign: str,
) -> tuple[dict[str, float], dict[str, str]]:
    lookup = _route_lookup(routes)
    values: dict[str, float] = {}
    labels: dict[str, str] = {}
    active: set[str] = set()

    check: Callable[[object, str], float] = _positive if sign == "positive" else _negative

    def resolve(product: str) -> float:
        if product in values:
            return values[product]
        if product in active:
            raise ValueError(f"Cyclic prior route at {product}")
        active.add(product)
        try:
            method, raw_spec = lookup[product]
        except KeyError as exc:
            raise ValueError(f"No configured {sign} prior route for {product}") from exc

        if method in direct_sources:
            source = direct_sources[method]
            if product not in source:
                raise ValueError(f"PEATSim {method} prior is missing for {product}")
            value = check(source[product], f"{method}/{product}")
            label = method
        elif method == "peatsim_dairy_milk_geometric_blend":
            spec = _mapping(raw_spec, method)
            raw_input = str(spec["raw_input"]).upper()
            raw_weight = float(spec["raw_input_weight"])
            process_weight = float(spec["processing_diagonal_weight"])
            if abs(raw_weight + process_weight - 1.0) > 1e-12:
                raise ValueError("Dairy geometric-blend weights must sum to one")
            raw_value = resolve(raw_input)
            process_source = direct_sources.get("peatsim_dairy_diagonal_median", {})
            if product not in process_source:
                raise ValueError(f"Dairy processing prior is missing for {product}")
            process_value = _positive(
                process_source[product], f"dairy processing/{product}"
            )
            value = exp(raw_weight * log(raw_value) + process_weight * log(process_value))
            label = f"{method}:{raw_input}+{product}"
        elif method == "chain_parent":
            spec = _mapping(raw_spec, f"chain_parent/{product}")
            parent = str(spec["parent"]).upper()
            multiplier = _positive(spec["multiplier"], f"chain multiplier/{product}")
            value = resolve(parent) * multiplier
            label = f"chain_parent:{parent}<-{labels[parent]}"
        elif method == "resolved_product_median":
            if not isinstance(raw_spec, list) or not raw_spec:
                raise ValueError(f"Resolved-product median is empty for {product}")
            components = [str(item).upper() for item in raw_spec]
            value = float(np.median([resolve(component) for component in components]))
            label = f"resolved_product_median:{'|'.join(components)}"
        elif method == "explicit_author_default":
            value = check(raw_spec, f"explicit author default/{product}")
            label = "explicit_author_default"
        else:
            raise ValueError(f"Unsupported prior route {method} for {product}")

        value = check(value, f"resolved prior/{product}")
        values[product] = value
        labels[product] = label
        active.remove(product)
        return value

    for product in products:
        resolve(product)
    return values, labels


def build_commodity_priors(
    workbook: str | Path,
    config: Mapping[str, Any],
    commodity_classes: Mapping[str, str],
) -> pd.DataFrame:
    """Construct a complete, auditable 31-commodity prior interface."""

    products = list(config["chain_roles"])
    if set(products) != set(commodity_classes):
        raise ValueError("Parameter and commodity configurations disagree on products")
    frozen = read_frozen_peatsim_priors(workbook)
    envelope = _mapping(config["parameter_response_envelope"], "response envelope")
    supply_variants: dict[str, dict[str, float]] = {}
    supply_routes: dict[str, dict[str, str]] = {}
    crop_sources = {
        "low": frozen.crop_total_supply_low,
        "central": frozen.crop_total_supply,
        "high": frozen.crop_total_supply_high,
    }
    for variant in ("low", "central", "high"):
        variant_routes = deepcopy(config["supply_prior_routes"])
        variant_routes["explicit_author_default"].update(
            envelope["explicit_supply_priors"][variant]
        )
        supply_variants[variant], supply_routes[variant] = _resolve_family(
            products,
            variant_routes,
            {
                "peatsim_supela_plus_yahela_aligned_region_median": crop_sources[variant],
                "peatsim_meat_diagonal_median": frozen.meat_supply,
                "peatsim_dairy_diagonal_median": frozen.dairy_supply,
            },
            sign="positive",
        )
    supply = supply_variants["central"]
    supply_route = supply_routes["central"]
    food_price, food_price_route = _resolve_family(
        products,
        config["food_price_prior_routes"],
        {"peatsim_food_diagonal_median": frozen.food_demand},
        sign="negative",
    )
    feed_price, feed_price_route = _resolve_family(
        products,
        config["feed_price_prior_routes"],
        {"peatsim_feed_diagonal_median": frozen.feed_demand},
        sign="negative",
    )
    feed_price_variants: dict[str, dict[str, float]] = {
        "central": feed_price
    }
    for variant in ("low", "high"):
        factor = float(envelope["feed_price_magnitude_factors"][variant])
        scaled_direct = {
            product: float(value) * factor
            for product, value in frozen.feed_demand.items()
        }
        feed_price_variants[variant], _ = _resolve_family(
            products,
            config["feed_price_prior_routes"],
            {"peatsim_feed_diagonal_median": scaled_direct},
            sign="negative",
        )
    food_income, food_income_route = _resolve_family(
        products,
        config["food_income_prior_routes"],
        {"peatsim_gdpela_median": frozen.income},
        sign="positive",
    )
    composite = _mapping(
        config["final_demand_use_share_composite"],
        "final_demand_use_share_composite",
    )
    price_components = _mapping(composite["price_components"], "price_components")
    income_components = _mapping(composite["income_components"], "income_components")
    other_price = _positive(
        price_components["other_use_author_prior_magnitude"],
        "other-use price prior",
    )
    feed_income = _positive(
        income_components["feed_author_prior"], "feed income prior"
    )
    other_income = _positive(
        income_components["other_use_author_prior"], "other-use income prior"
    )
    return pd.DataFrame.from_records(
        [
            {
                "commodity": product,
                "commodity_class": commodity_classes[product],
                "chain_role": config["chain_roles"][product],
                "supply_prior_median": supply[product],
                "supply_prior_low": supply_variants["low"][product],
                "supply_prior_central": supply_variants["central"][product],
                "supply_prior_high": supply_variants["high"][product],
                "food_price_prior_magnitude": abs(food_price[product]),
                "feed_price_prior_magnitude": abs(feed_price[product]),
                "feed_price_prior_magnitude_low": abs(
                    feed_price_variants["low"][product]
                ),
                "feed_price_prior_magnitude_central": abs(
                    feed_price_variants["central"][product]
                ),
                "feed_price_prior_magnitude_high": abs(
                    feed_price_variants["high"][product]
                ),
                "other_use_price_prior_magnitude": other_price,
                "food_income_prior": food_income[product],
                "feed_income_prior": feed_income,
                "other_use_income_prior": other_income,
                "supply_prior_route": supply_route[product],
                "food_price_prior_route": food_price_route[product],
                "feed_price_prior_route": feed_price_route[product],
                "food_income_prior_route": food_income_route[product],
            }
            for product in products
        ]
    )


def _load_commodity_classes(path: Path) -> dict[str, str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    config = _mapping(raw, "commodity configuration")
    commodities = _mapping(config.get("commodities"), "commodities")
    result = {
        str(product).upper(): str(_mapping(spec, str(product)).get("class", ""))
        for product, spec in commodities.items()
    }
    if len(result) != EXPECTED_COMMODITIES or any(not value for value in result.values()):
        raise ValueError("Commodity configuration must define 31 nonblank classes")
    return result


def _load_benchmark(path: Path) -> pd.DataFrame:
    required = {
        "economy_id",
        "commodity",
        "structural_supply_zero",
        "structural_final_demand_zero",
        "food_demand_2023",
        "other_final_demand_2023",
        "final_demand_2023",
    }
    benchmark = pd.read_csv(path)
    if not required <= set(benchmark.columns):
        raise ValueError(f"Benchmark lacks: {sorted(required-set(benchmark.columns))}")
    benchmark = benchmark[list(required)].copy()
    benchmark["economy_id"] = benchmark["economy_id"].astype(str).str.strip().str.upper()
    benchmark["commodity"] = benchmark["commodity"].astype(str).str.strip().str.upper()
    key = ["economy_id", "commodity"]
    if benchmark.duplicated(key).any():
        raise ValueError("Benchmark account-commodity keys must be unique")
    if (
        benchmark["economy_id"].nunique() != EXPECTED_ACCOUNTS
        or benchmark["commodity"].nunique() != EXPECTED_COMMODITIES
        or len(benchmark) != EXPECTED_ROWS
    ):
        raise ValueError("Benchmark must be the complete 193 x 31 account universe")
    for column in ("structural_supply_zero", "structural_final_demand_zero"):
        if benchmark[column].dtype != bool:
            normalised = benchmark[column].astype(str).str.casefold().map(
                {"true": True, "false": False}
            )
            if normalised.isna().any():
                raise ValueError(f"Invalid benchmark Boolean column: {column}")
            benchmark[column] = normalised.astype(bool)
    quantity_columns = [
        "food_demand_2023",
        "other_final_demand_2023",
        "final_demand_2023",
    ]
    benchmark[quantity_columns] = benchmark[quantity_columns].apply(
        pd.to_numeric, errors="coerce"
    )
    if (
        not np.isfinite(benchmark[quantity_columns].to_numpy()).all()
        or benchmark[quantity_columns].lt(0).any().any()
    ):
        raise ValueError("Balanced final-demand components must be finite and nonnegative")
    residual = (
        benchmark["food_demand_2023"]
        + benchmark["other_final_demand_2023"]
        - benchmark["final_demand_2023"]
    ).abs()
    if float(residual.max()) > 1.0e-10:
        raise ValueError("Balanced food and other use do not sum to total final demand")
    return benchmark.sort_values(key).reset_index(drop=True)


def _build_final_demand_use_shares(
    benchmark: pd.DataFrame,
    unbalanced_path: Path,
    composite_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Build exact food/feed/other shares on the 193-account benchmark."""

    required = {"economy_id", "commodity", "role", "account", "unit", "value"}
    observations = pd.read_csv(unbalanced_path)
    if not required <= set(observations):
        raise ValueError(
            f"Unbalanced use benchmark lacks: {sorted(required-set(observations))}"
        )
    observations["economy_id"] = (
        observations["economy_id"].astype(str).str.strip().str.upper()
    )
    observations["commodity"] = (
        observations["commodity"].astype(str).str.strip().str.upper()
    )
    accounts = set(benchmark["economy_id"])
    products = set(benchmark["commodity"])
    use_accounts = list(composite_config["positive_nonprocessing_nonfood_accounts"])
    uses = observations[
        observations["economy_id"].isin(accounts)
        & observations["commodity"].isin(products)
        & observations["role"].eq(composite_config["unbalanced_role"])
        & observations["unit"].eq("Mt")
        & observations["account"].isin(use_accounts)
    ].copy()
    uses["value"] = pd.to_numeric(uses["value"], errors="coerce")
    if not np.isfinite(uses["value"]).all() or uses["value"].lt(0).any():
        raise ValueError("Non-processing non-food use observations must be nonnegative")
    if uses.duplicated(["economy_id", "commodity", "account"]).any():
        raise ValueError(
            "Unbalanced use aggregation is ambiguous: duplicate account observations"
        )
    pivot = uses.pivot_table(
        index=["economy_id", "commodity"],
        columns="account",
        values="value",
        aggfunc="sum",
        fill_value=0.0,
    )
    index = pd.MultiIndex.from_frame(benchmark[["economy_id", "commodity"]])
    pivot = pivot.reindex(index, fill_value=0.0)
    for account in use_accounts:
        if account not in pivot:
            pivot[account] = 0.0

    result = benchmark[
        [
            "economy_id",
            "commodity",
            "food_demand_2023",
            "other_final_demand_2023",
            "final_demand_2023",
            "structural_final_demand_zero",
        ]
    ].copy()
    result["benchmark_structural_final_demand_zero"] = result[
        "structural_final_demand_zero"
    ]
    # Behaviour is undefined only when the quantity actually solved by the
    # model is zero. This also catches ten tiny source anchors projected to an
    # exact zero even though the benchmark source-status flag remains false.
    result["structural_final_demand_zero"] = result["final_demand_2023"].eq(0.0)
    active = ~result["structural_final_demand_zero"]
    result["balanced_food_share"] = 0.0
    result.loc[active, "balanced_food_share"] = (
        result.loc[active, "food_demand_2023"]
        / result.loc[active, "final_demand_2023"]
    )
    if (
        result["balanced_food_share"].lt(0).any()
        or result["balanced_food_share"].gt(1.0 + 1.0e-12).any()
    ):
        raise ValueError("Balanced food share lies outside [0, 1]")
    result["balanced_food_share"] = result["balanced_food_share"].clip(0.0, 1.0)

    raw_feed = pivot[str(composite_config["feed_account"])].to_numpy(dtype=float)
    raw_total = pivot[use_accounts].sum(axis=1).to_numpy(dtype=float)
    result["raw_feed_use_mt"] = raw_feed
    result["raw_positive_nonprocessing_nonfood_use_mt"] = raw_total
    feed_fraction = np.zeros(len(result), dtype=float)
    observed_composition = raw_total > 0.0
    feed_fraction[observed_composition] = (
        raw_feed[observed_composition] / raw_total[observed_composition]
    )
    explicit_feed = result["commodity"].isin(
        composite_config["explicit_feed_products"]
    ).to_numpy()
    has_other = result["other_final_demand_2023"].gt(0.0).to_numpy()
    feed_fraction[explicit_feed & has_other] = 1.0

    remaining_share = 1.0 - result["balanced_food_share"].to_numpy(dtype=float)
    result["feed_share"] = remaining_share * feed_fraction
    # Calculate the final component as a remainder so active shares add to one
    # to machine precision rather than through a second independent division.
    result["other_use_share"] = 0.0
    result.loc[active, "other_use_share"] = (
        1.0
        - result.loc[active, "balanced_food_share"]
        - result.loc[active, "feed_share"]
    )
    result.loc[~active, ["balanced_food_share", "feed_share", "other_use_share"]] = 0.0
    shares = result[["balanced_food_share", "feed_share", "other_use_share"]]
    if shares.lt(-1.0e-12).any().any() or shares.gt(1.0 + 1.0e-12).any().any():
        raise ValueError("A final-demand use share lies outside [0, 1]")
    result[["balanced_food_share", "feed_share", "other_use_share"]] = shares.clip(
        0.0, 1.0
    )
    share_sum = result[["balanced_food_share", "feed_share", "other_use_share"]].sum(axis=1)
    if not np.allclose(share_sum[active], 1.0, atol=1.0e-14, rtol=0.0):
        raise ValueError("Active final-demand use shares do not sum to one")
    if not share_sum[~active].eq(0.0).all():
        raise ValueError("Zero final-demand rows must have zero component shares")

    status = np.full(len(result), "observed_use_composition", dtype=object)
    status[~observed_composition & has_other] = "explicit_no_observed_composition_to_other_use"
    status[explicit_feed & has_other] = "explicit_feed_product"
    status[~has_other & active] = "balanced_food_only"
    status[~active] = "explicit_zero_balanced_final_demand"
    result["use_share_status"] = status
    return result


def build_income_interface(
    project_root: Path,
    accounts: Sequence[str],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    """Use reporting.py's formal FY25 World Bank account membership."""

    source_config = _mapping(config["sources"], "sources")
    reporting_path = _project_path(
        project_root,
        str(source_config["reporting_config_path"]),
        "sources.reporting_config_path",
    )
    reporting_config = load_reporting_config(reporting_path)
    catalog = load_source_catalog(project_root / "config/data_sources.yaml")
    income_record = catalog.source("world_bank_income_classification")
    verify_source(income_record)
    income_groups = load_world_bank_income_groups(income_record.path, reporting_config)
    membership = build_model_account_membership(
        accounts, reporting_config, income_groups=income_groups
    )
    income_system = reporting_config["world_bank_income"]["group_system"]
    interface = membership.loc[
        membership["group_system"].eq(income_system),
        ["model_account_id", "group_code"],
    ].rename(
        columns={"model_account_id": "economy_id", "group_code": "income_group"}
    )
    if len(interface) != len(set(accounts)) or interface["economy_id"].duplicated().any():
        raise ValueError("Reporting income interface does not cover each model account once")
    if not set(interface["income_group"]).issubset(INCOME_GROUPS):
        raise ValueError("Reporting income interface contains an unknown income group")
    return interface.sort_values("economy_id").reset_index(drop=True)


def _bounds(raw: object, label: str) -> tuple[float, float]:
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError(f"{label} must contain two bounds")
    lower, upper = (float(raw[0]), float(raw[1]))
    if not (isfinite(lower) and isfinite(upper) and 0 < lower <= upper):
        raise ValueError(f"{label} bounds must be positive and ordered")
    return lower, upper


def _clip(value: float, bounds: tuple[float, float]) -> tuple[float, str]:
    lower, upper = bounds
    clipped = min(max(float(value), lower), upper)
    if clipped > value:
        status = "clipped_low"
    elif clipped < value:
        status = "clipped_high"
    else:
        status = "within_bounds"
    return clipped, status


def _provenance_status(row: pd.Series) -> str:
    routes = (
        str(row["supply_prior_route"]),
        str(row["food_price_prior_route"]),
        str(row["feed_price_prior_route"]),
        str(row["food_income_prior_route"]),
    )
    if any("explicit_author_default" in route for route in routes):
        return "explicit_author_rule_casm_transformed"
    if any(
        route.startswith(("chain_parent:", "resolved_product_median:"))
        or "geometric_blend" in route
        for route in routes
    ):
        return "frozen_prior_chain_derived_casm_transformed"
    return "frozen_prior_median_casm_transformed"


def _activity_status(row: pd.Series) -> str:
    supply_zero = bool(row["structural_supply_zero"])
    demand_zero = bool(row["structural_final_demand_zero"])
    if supply_zero and demand_zero:
        return "structural_supply_and_demand_zero"
    if supply_zero:
        return "structural_supply_zero"
    if demand_zero:
        return "structural_demand_zero"
    return "active_supply_and_demand"


def _range(frame: pd.DataFrame, column: str) -> dict[str, float]:
    return {
        "min": float(frame[column].min()),
        "max": float(frame[column].max()),
    }


def _response_set_hash(frame: pd.DataFrame, variant: str) -> str:
    """Hash the ordered final behavioural and transmission parameter payload."""

    columns = [
        "economy_id",
        "commodity",
        f"supply_price_elasticity_{variant}",
        f"demand_price_elasticity_{variant}",
        f"income_elasticity_{variant}",
        "exchange_rate_pass_through",
        "tariff_pass_through",
    ]
    payload = (
        frame[columns]
        .sort_values(["economy_id", "commodity"])
        .to_csv(index=False, float_format="%.17g", lineterminator="\n")
        .encode("utf-8")
    )
    return hashlib.sha256(payload).hexdigest()


def build_parameters(
    project_root: str | Path = PROJECT_ROOT,
    config_path: str | Path | None = None,
    *,
    income_interface: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build 5,983 complete account-product parameter rows and audit report."""

    root = Path(project_root).resolve()
    parameter_path = Path(config_path).resolve() if config_path else root / "config/parameters.yaml"
    config = load_parameter_config(parameter_path)
    source_config = _mapping(config["sources"], "sources")
    benchmark_path = _project_path(
        root, str(source_config["benchmark_path"]), "sources.benchmark_path"
    )
    unbalanced_use_path = _project_path(
        root,
        str(source_config["unbalanced_use_path"]),
        "sources.unbalanced_use_path",
    )
    commodity_path = _project_path(
        root,
        str(source_config["commodity_config_path"]),
        "sources.commodity_config_path",
    )
    benchmark = _load_benchmark(benchmark_path)
    use_shares = _build_final_demand_use_shares(
        benchmark,
        unbalanced_use_path,
        _mapping(
            config["final_demand_use_share_composite"],
            "final_demand_use_share_composite",
        ),
    )
    commodity_classes = _load_commodity_classes(commodity_path)
    if set(benchmark["commodity"]) != set(commodity_classes):
        raise ValueError("Benchmark and commodity configuration disagree")

    catalog = load_source_catalog(root / "config/data_sources.yaml")
    prior_record = catalog.source(str(source_config["frozen_prior_catalog_key"]))
    verify_source(prior_record)
    if prior_record.source_id != source_config["frozen_prior_source_id"]:
        raise ValueError("Configured PEATSim source ID differs from verified catalog")
    priors = build_commodity_priors(prior_record.path, config, commodity_classes)

    accounts = sorted(benchmark["economy_id"].unique())
    if income_interface is None:
        income = build_income_interface(root, accounts, config)
    else:
        required_income = {"economy_id", "income_group"}
        if not required_income <= set(income_interface.columns):
            raise ValueError(
                f"Income interface lacks: {sorted(required_income-set(income_interface.columns))}"
            )
        income = income_interface[list(required_income)].copy()
        income["economy_id"] = income["economy_id"].astype(str).str.strip().str.upper()
        income["income_group"] = income["income_group"].astype(str).str.strip().str.upper()
    if income["economy_id"].duplicated().any() or set(income["economy_id"]) != set(accounts):
        raise ValueError("Income interface must cover exactly the 193 model accounts")
    if not set(income["income_group"]).issubset(INCOME_GROUPS):
        raise ValueError("Income interface contains an unknown group")

    benchmark_base = benchmark.drop(
        columns=[
            "food_demand_2023",
            "other_final_demand_2023",
            "final_demand_2023",
            "structural_final_demand_zero",
        ]
    )
    frame = benchmark_base.merge(
        use_shares,
        on=["economy_id", "commodity"],
        how="left",
        validate="one_to_one",
    )
    frame = frame.merge(priors, on="commodity", how="left", validate="many_to_one")
    frame = frame.merge(income, on="economy_id", how="left", validate="many_to_one")
    if frame.isna().any().any():
        missing = frame.columns[frame.isna().any()].tolist()
        raise ValueError(f"Parameter inputs contain missing values: {missing}")

    for variant in ("low", "central", "high"):
        frame[f"demand_prior_{variant}"] = -(
            frame["balanced_food_share"] * frame["food_price_prior_magnitude"]
            + frame["feed_share"]
            * frame[f"feed_price_prior_magnitude_{variant}"]
            + frame["other_use_share"] * frame["other_use_price_prior_magnitude"]
        )
    frame["demand_prior_median"] = frame["demand_prior_central"]
    frame["income_prior_median"] = (
        frame["balanced_food_share"] * frame["food_income_prior"]
        + frame["feed_share"] * frame["feed_income_prior"]
        + frame["other_use_share"] * frame["other_use_income_prior"]
    )
    for variant in ("low", "central", "high"):
        frame[f"income_prior_{variant}"] = frame["income_prior_median"]
    frame["demand_prior_route"] = (
        "balanced_2023_use_share_composite:fodela_food|fedela_feed|author_other"
    )
    frame["income_prior_route"] = (
        "balanced_2023_use_share_composite:gdpela_food|author_feed|author_other"
    )
    inactive = frame["structural_final_demand_zero"]
    if not frame.loc[inactive, ["demand_prior_median", "income_prior_median"]].eq(0.0).all().all():
        raise ValueError("Zero final demand must produce exact zero composite priors")
    if frame.loc[~inactive, "demand_prior_median"].ge(0.0).any():
        raise ValueError("Active composite demand-price priors must be negative")
    if frame.loc[~inactive, "income_prior_median"].le(0.0).any():
        raise ValueError("Active composite income priors must be positive")

    variants = ("low", "central", "high")
    supply_values: dict[str, list[float]] = {variant: [] for variant in variants}
    demand_values: dict[str, list[float]] = {variant: [] for variant in variants}
    income_values: dict[str, list[float]] = {variant: [] for variant in variants}
    exchange_values: list[float] = []
    tariff_values: list[float] = []
    bound_statuses: dict[str, list[str]] = {variant: [] for variant in variants}
    for row in frame.itertuples(index=False):
        class_rule = _mapping(config["class_rules"][row.commodity_class], row.commodity_class)
        adjustment = _mapping(
            config["income_group_adjustments"][row.income_group], row.income_group
        )

        for variant in variants:
            supply_rule = _mapping(class_rule["supply"], "supply rule")
            supply_raw = (
                float(getattr(row, f"supply_prior_{variant}"))
                * float(supply_rule["multiplier"])
                * float(adjustment["supply"])
            )
            supply, supply_status = _clip(
                supply_raw, _bounds(supply_rule["bounds"], "supply bounds")
            )

            if row.structural_final_demand_zero:
                demand_magnitude = 0.0
                income_value = 0.0
                demand_status = "explicit_structural_zero"
                income_status = "explicit_structural_zero"
            else:
                demand_rule = _mapping(class_rule["demand"], "demand rule")
                demand_magnitude_raw = (
                    abs(float(getattr(row, f"demand_prior_{variant}")))
                    * float(demand_rule["multiplier"])
                    * float(adjustment["demand_magnitude"])
                )
                demand_magnitude, demand_status = _clip(
                    demand_magnitude_raw,
                    _bounds(demand_rule["magnitude_bounds"], "demand magnitude bounds"),
                )

                income_rule = _mapping(class_rule["income"], "income rule")
                income_raw = (
                    float(getattr(row, f"income_prior_{variant}"))
                    * float(income_rule["multiplier"])
                    * float(adjustment["income"])
                )
                income_value, income_status = _clip(
                    income_raw, _bounds(income_rule["bounds"], "income bounds")
                )

            supply_values[variant].append(supply)
            demand_values[variant].append(-demand_magnitude)
            income_values[variant].append(income_value)
            variant_statuses = {
                "supply": supply_status,
                "demand": demand_status,
                "income": income_status,
            }
            changed = [
                f"{name}_{status}"
                for name, status in variant_statuses.items()
                if status != "within_bounds"
            ]
            bound_statuses[variant].append(
                "|".join(changed) if changed else "within_configured_bounds"
            )

        transmission = _mapping(class_rule["transmission"], "transmission rule")
        transmission_factor = float(adjustment["transmission"])
        exchange, exchange_status = _clip(
            float(transmission["exchange_rate"]) * transmission_factor,
            _bounds(config["transmission_bounds"]["exchange_rate"], "exchange bounds"),
        )
        tariff, tariff_status = _clip(
            float(transmission["tariff"]) * transmission_factor,
            _bounds(config["transmission_bounds"]["tariff"], "tariff bounds"),
        )

        exchange_values.append(exchange)
        tariff_values.append(tariff)
        for variant in variants:
            transmission_changed = [
                f"{name}_{status}"
                for name, status in {
                    "exchange": exchange_status,
                    "tariff": tariff_status,
                }.items()
                if status != "within_bounds"
            ]
            if transmission_changed:
                current = bound_statuses[variant][-1]
                bound_statuses[variant][-1] = "|".join(
                    ([current] if current != "within_configured_bounds" else [])
                    + transmission_changed
                )

    for variant in variants:
        frame[f"supply_price_elasticity_{variant}"] = supply_values[variant]
        frame[f"demand_price_elasticity_{variant}"] = demand_values[variant]
        frame[f"income_elasticity_{variant}"] = income_values[variant]
        frame[f"bound_adjustment_status_{variant}"] = bound_statuses[variant]
    frame["supply_price_elasticity"] = frame["supply_price_elasticity_central"]
    frame["demand_price_elasticity"] = frame["demand_price_elasticity_central"]
    frame["income_elasticity"] = frame["income_elasticity_central"]
    frame["exchange_rate_pass_through"] = exchange_values
    frame["tariff_pass_through"] = tariff_values
    frame["parameter_set"] = config["parameter_set"]
    frame["parameter_status"] = "final_casm_v2_central"
    frame["supply_response_semantics"] = "long_run_total_production_own_price"
    frame["demand_response_semantics"] = (
        "balanced_2023_use_share_composite_final_demand_own_price"
    )
    frame["income_response_semantics"] = (
        "balanced_2023_use_share_composite_final_demand_income"
    )
    frame["provenance_status"] = frame.apply(_provenance_status, axis=1)
    frame["income_adjustment_status"] = np.where(
        frame["income_group"].eq("NCL"),
        "explicit_ncl_fallback_factor_applied",
        "wb_fy25_income_group_factor_applied",
    )
    frame["transmission_provenance_status"] = "casm_product_class_and_income_rule"
    frame["bound_adjustment_status"] = frame["bound_adjustment_status_central"]
    frame["activity_status"] = frame.apply(_activity_status, axis=1)
    frame["prior_source_id"] = prior_record.source_id

    parameter_columns = [
        "supply_price_elasticity",
        "demand_price_elasticity",
        "income_elasticity",
        "supply_price_elasticity_low",
        "supply_price_elasticity_central",
        "supply_price_elasticity_high",
        "demand_price_elasticity_low",
        "demand_price_elasticity_central",
        "demand_price_elasticity_high",
        "income_elasticity_low",
        "income_elasticity_central",
        "income_elasticity_high",
        "exchange_rate_pass_through",
        "tariff_pass_through",
    ]
    numeric = frame[parameter_columns]
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("Final parameter table contains missing or non-finite values")
    structural_final_zero = frame["structural_final_demand_zero"]
    for variant in variants:
        supply_column = f"supply_price_elasticity_{variant}"
        demand_column = f"demand_price_elasticity_{variant}"
        income_column = f"income_elasticity_{variant}"
        if frame[supply_column].le(0).any():
            raise ValueError(f"{variant} supply own-price elasticities must be positive")
        if frame.loc[~structural_final_zero, demand_column].ge(0).any():
            raise ValueError(f"Active {variant} demand elasticities must be negative")
        if frame.loc[~structural_final_zero, income_column].le(0).any():
            raise ValueError(f"Active {variant} income elasticities must be positive")
        if not frame.loc[
            structural_final_zero, [demand_column, income_column]
        ].eq(0.0).all().all():
            raise ValueError(
                f"Only zero final-demand rows may have zero {variant} demand parameters"
            )
    if not (
        frame["supply_price_elasticity_low"]
        .le(frame["supply_price_elasticity_central"] + 1.0e-15)
        .all()
        and frame["supply_price_elasticity_central"]
        .le(frame["supply_price_elasticity_high"] + 1.0e-15)
        .all()
    ):
        raise ValueError("Supply response envelope is not weakly ordered")
    if not (
        frame["demand_price_elasticity_low"]
        .ge(frame["demand_price_elasticity_central"] - 1.0e-15)
        .all()
        and frame["demand_price_elasticity_central"]
        .ge(frame["demand_price_elasticity_high"] - 1.0e-15)
        .all()
    ):
        raise ValueError("Demand response envelope is not weakly ordered")
    if not (
        frame["income_elasticity_low"].eq(frame["income_elasticity_central"]).all()
        and frame["income_elasticity_central"].eq(frame["income_elasticity_high"]).all()
    ):
        raise ValueError("Income elasticities must be identical across response sets")
    if frame[["exchange_rate_pass_through", "tariff_pass_through"]].le(0).any().any():
        raise ValueError("Transmission coefficients must be positive")
    if frame[["exchange_rate_pass_through", "tariff_pass_through"]].gt(1).any().any():
        raise ValueError("Transmission coefficients cannot exceed one")
    if len(frame) != EXPECTED_ROWS or frame.duplicated(["economy_id", "commodity"]).any():
        raise AssertionError("Final parameter table failed the 193 x 31 uniqueness gate")

    ncl_accounts = sorted(frame.loc[frame["income_group"].eq("NCL"), "economy_id"].unique())
    response_set_ids = config["parameter_response_envelope"]["sets"]
    response_hashes = {
        response_set: _response_set_hash(frame, variant)
        for response_set, variant in zip(response_set_ids, variants)
    }
    report: dict[str, Any] = {
        "status": "passed",
        "parameter_set": config["parameter_set"],
        "benchmark_year": 2023,
        "prior_source_id": prior_record.source_id,
        "prior_reduction": config["prior_reduction"],
        "response_set_sha256": response_hashes,
        "income_interface": source_config["income_interface"],
        "model_account_count": int(frame["economy_id"].nunique()),
        "commodity_count": int(frame["commodity"].nunique()),
        "parameter_row_count": int(len(frame)),
        "missing_parameter_count": int(numeric.isna().sum().sum()),
        "nonfinite_parameter_count": int((~np.isfinite(numeric.to_numpy())).sum()),
        "zero_supply_parameter_count": int(frame["supply_price_elasticity"].eq(0).sum()),
        "zero_demand_parameter_count": int(frame["demand_price_elasticity"].eq(0).sum()),
        "zero_income_parameter_count": int(frame["income_elasticity"].eq(0).sum()),
        "explicit_structural_final_demand_zero_count": int(
            frame["structural_final_demand_zero"].sum()
        ),
        "benchmark_structural_final_demand_zero_count": int(
            frame["benchmark_structural_final_demand_zero"].sum()
        ),
        "income_group_account_counts": dict(
            sorted(income["income_group"].value_counts().astype(int).to_dict().items())
        ),
        "ncl_fallback_accounts": ncl_accounts,
        "ncl_fallback_parameter_rows": int(frame["income_group"].eq("NCL").sum()),
        "supply_prior_route_counts_by_product": dict(
            sorted(Counter(priors["supply_prior_route"]).items())
        ),
        "food_price_prior_route_counts_by_product": dict(
            sorted(Counter(priors["food_price_prior_route"]).items())
        ),
        "feed_price_prior_route_counts_by_product": dict(
            sorted(Counter(priors["feed_price_prior_route"]).items())
        ),
        "food_income_prior_route_counts_by_product": dict(
            sorted(Counter(priors["food_income_prior_route"]).items())
        ),
        "explicit_author_default_products": sorted(
            priors.loc[
                priors[
                    [
                        "supply_prior_route",
                        "food_price_prior_route",
                        "feed_price_prior_route",
                        "food_income_prior_route",
                    ]
                ]
                .apply(lambda column: column.str.contains("explicit_author_default"))
                .any(axis=1),
                "commodity",
            ].tolist()
        ),
        "use_share_status_counts": dict(
            sorted(frame["use_share_status"].value_counts().astype(int).to_dict().items())
        ),
        "maximum_active_use_share_sum_residual": float(
            (
                frame.loc[
                    ~frame["structural_final_demand_zero"],
                    ["balanced_food_share", "feed_share", "other_use_share"],
                ].sum(axis=1)
                - 1.0
            ).abs().max()
        ),
        "crop_total_supply_priors": {
            product: float(value)
            for product, value in priors.set_index("commodity")["supply_prior_median"]
            .reindex(["RIC", "WHE", "CRN", "OCG", "SBS", "NBS", "RBS", "CTN", "SUG"])
            .items()
        },
        "feed_price_direct_priors": {
            product: float(value)
            for product, value in priors.set_index("commodity")["feed_price_prior_magnitude"]
            .reindex(["WHE", "CRN", "OCG", "SBM", "NBM", "RBM", "DDG"])
            .items()
        },
        "provenance_status_counts": dict(
            sorted(frame["provenance_status"].value_counts().astype(int).to_dict().items())
        ),
        "bound_adjustment_status_counts": dict(
            sorted(frame["bound_adjustment_status"].value_counts().astype(int).to_dict().items())
        ),
        "bound_adjustment_status_counts_by_response_set": {
            response_set: dict(
                sorted(
                    frame[f"bound_adjustment_status_{variant}"]
                    .value_counts()
                    .astype(int)
                    .to_dict()
                    .items()
                )
            )
            for response_set, variant in zip(response_set_ids, variants)
        },
        "activity_status_counts": dict(
            sorted(frame["activity_status"].value_counts().astype(int).to_dict().items())
        ),
        "observed_ranges": {column: _range(frame, column) for column in parameter_columns},
        "response_set_observed_ranges": {
            response_set: {
                family: _range(frame, f"{family}_{variant}")
                for family in (
                    "supply_price_elasticity",
                    "demand_price_elasticity",
                    "income_elasticity",
                )
            }
            for response_set, variant in zip(response_set_ids, variants)
        },
        "missing_to_zero": (
            "forbidden_and_not_used;zeros_are_explicit_balanced_final_demand_zeros"
        ),
        "response_semantics": {
            "supply": "long_run_total_production_own_price",
            "demand": "balanced_2023_use_share_composite_final_demand_own_price",
            "income": "balanced_2023_use_share_composite_final_demand_income",
        },
        "interpretation": (
            "CASM V2 central transformed parameters anchored to frozen commodity "
            "priors and balanced 2023 final-use shares; they are not economy-level "
            "econometric estimates."
        ),
    }

    ordered = [
        "economy_id",
        "commodity",
        "commodity_class",
        "chain_role",
        "income_group",
        "parameter_set",
        "parameter_status",
        "supply_response_semantics",
        "demand_response_semantics",
        "income_response_semantics",
        "supply_price_elasticity",
        "demand_price_elasticity",
        "income_elasticity",
        "supply_price_elasticity_low",
        "supply_price_elasticity_central",
        "supply_price_elasticity_high",
        "demand_price_elasticity_low",
        "demand_price_elasticity_central",
        "demand_price_elasticity_high",
        "income_elasticity_low",
        "income_elasticity_central",
        "income_elasticity_high",
        "exchange_rate_pass_through",
        "tariff_pass_through",
        "balanced_food_share",
        "feed_share",
        "other_use_share",
        "food_demand_2023",
        "other_final_demand_2023",
        "final_demand_2023",
        "raw_feed_use_mt",
        "raw_positive_nonprocessing_nonfood_use_mt",
        "supply_prior_median",
        "supply_prior_low",
        "supply_prior_central",
        "supply_prior_high",
        "demand_prior_median",
        "demand_prior_low",
        "demand_prior_central",
        "demand_prior_high",
        "income_prior_median",
        "income_prior_low",
        "income_prior_central",
        "income_prior_high",
        "food_price_prior_magnitude",
        "feed_price_prior_magnitude",
        "feed_price_prior_magnitude_low",
        "feed_price_prior_magnitude_central",
        "feed_price_prior_magnitude_high",
        "other_use_price_prior_magnitude",
        "food_income_prior",
        "feed_income_prior",
        "other_use_income_prior",
        "supply_prior_route",
        "demand_prior_route",
        "income_prior_route",
        "food_price_prior_route",
        "feed_price_prior_route",
        "food_income_prior_route",
        "structural_supply_zero",
        "structural_final_demand_zero",
        "benchmark_structural_final_demand_zero",
        "activity_status",
        "use_share_status",
        "provenance_status",
        "income_adjustment_status",
        "transmission_provenance_status",
        "bound_adjustment_status",
        "bound_adjustment_status_low",
        "bound_adjustment_status_central",
        "bound_adjustment_status_high",
        "prior_source_id",
    ]
    return (
        frame[ordered]
        .sort_values(["economy_id", "commodity"])
        .reset_index(drop=True),
        report,
    )


def write_parameter_outputs(
    project_root: str | Path = PROJECT_ROOT,
    config_path: str | Path | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    """Build and write the versioned parameter table and coverage report."""

    root = Path(project_root).resolve()
    parameter_path = Path(config_path).resolve() if config_path else root / "config/parameters.yaml"
    config = load_parameter_config(parameter_path)
    parameters, report = build_parameters(root, parameter_path)
    outputs = _mapping(config["outputs"], "outputs")
    table_path = _project_path(root, str(outputs["parameters"]), "outputs.parameters")
    report_path = _project_path(root, str(outputs["report"]), "outputs.report")
    table_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    parameters.to_csv(table_path, index=False)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return table_path, report_path, report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args(argv)
    table_path, report_path, report = write_parameter_outputs(
        args.project_root, args.config
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "rows": report["parameter_row_count"],
                "table": str(table_path),
                "report": str(report_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
