"""Auditable nutrition post-solution for the 31-product CASM-World model.

The module intentionally accepts *food-use quantities*, not total demand or
domestic supply.  Product coefficients are derived from paired 2023 FAOSTAT
Food Balance Sheet observations whenever the model product has a matching FBS
item.  Frozen dairy-product coefficients and structural nonfood products are
explicit in ``config/nutrition.yaml``; neither is manufactured by filling a
missing FAOSTAT observation with zero.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import zipfile

import numpy as np
import pandas as pd
import yaml

from casm_world.benchmark import country_codebook
from casm_world.paths import load_source_catalog, verify_source


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "nutrition.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

EXPECTED_COMMODITIES = (
    "RIC", "WHE", "CRN", "OCG", "SBS", "SBO", "SBM", "NBS", "NBO",
    "NBM", "RBS", "RBO", "RBM", "DDG", "ETH", "BDI", "OTO", "CTN",
    "SUG", "SCA", "SBE", "BFV", "PRK", "PLM", "MLK", "BUT", "CHE",
    "NDM", "FMK", "WDM", "ODA",
)
SOURCE_CLASSES = frozenset({"direct", "aggregate", "fallback", "nonfood"})
COEFFICIENT_COLUMNS = (
    "energy_kcal_per_kg",
    "protein_g_per_kg",
    "fat_g_per_kg",
)
COMPONENT_COLUMNS = ("food_quantity", "energy", "protein", "fat")


class NutritionContractError(ValueError):
    """Raised when nutrition inputs violate an accounting or unit contract."""


@dataclass(frozen=True)
class NutritionPostsolveResult:
    """Long product contributions and correctly weighted summary outputs."""

    commodity_contributions: pd.DataFrame
    economy: pd.DataFrame
    world: pd.DataFrame

    @property
    def summary(self) -> pd.DataFrame:
        """Return economy and world results in one consistently shaped table."""

        return pd.concat([self.economy, self.world], ignore_index=True)


def _as_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise NutritionContractError(f"{label} must be a mapping")
    return value


def _positive_finite(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise NutritionContractError(f"{label} must be numeric") from exc
    if not isfinite(number) or number <= 0:
        raise NutritionContractError(f"{label} must be positive and finite")
    return number


def validate_nutrition_config(config: Mapping[str, Any]) -> None:
    """Validate exhaustive product coverage and mutually exclusive methods."""

    if config.get("schema_version") != 1:
        raise NutritionContractError("nutrition schema_version must equal 1")
    if int(config.get("benchmark_year", -1)) != 2023:
        raise NutritionContractError("nutrition benchmark_year must equal 2023")
    _positive_finite(config.get("days_per_year"), "days_per_year")
    if config.get("fbs_estimator") != "median_of_country_product_ratios":
        raise NutritionContractError(
            "fbs_estimator must be median_of_country_product_ratios"
        )
    bounds = _as_mapping(
        config.get("coefficient_upper_bounds"), "coefficient_upper_bounds"
    )
    if set(bounds) != set(COEFFICIENT_COLUMNS):
        raise NutritionContractError("coefficient_upper_bounds must cover all nutrients")
    for column in COEFFICIENT_COLUMNS:
        _positive_finite(bounds[column], f"coefficient_upper_bounds.{column}")

    products = _as_mapping(config.get("commodities"), "commodities")
    expected = set(EXPECTED_COMMODITIES)
    actual = {str(code).strip().upper() for code in products}
    if actual != expected or len(products) != len(expected):
        raise NutritionContractError(
            "nutrition coverage must be exactly the 31 model commodities: "
            f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )

    input_contract = _as_mapping(config.get("input_contract"), "input_contract")
    if input_contract.get("quantity_unit") != "Mt edible product/year":
        raise NutritionContractError("food quantity unit must be Mt edible product/year")
    if input_contract.get("population_unit") != "million persons":
        raise NutritionContractError("population unit must be million persons")
    if input_contract.get("require_complete_commodity_grid") is not True:
        raise NutritionContractError("the default postsolve must require a complete grid")
    tolerance = float(input_contract.get("nonfood_positive_tolerance_mt", -1.0))
    if not isfinite(tolerance) or tolerance < 0:
        raise NutritionContractError("nonfood_positive_tolerance_mt must be finite and nonnegative")

    elements = _as_mapping(config.get("fbs_elements"), "fbs_elements")
    if set(elements) != set(COMPONENT_COLUMNS):
        raise NutritionContractError("fbs_elements must define food, energy, protein and fat")
    element_codes: list[int] = []
    for component in COMPONENT_COLUMNS:
        definition = _as_mapping(elements[component], f"fbs_elements.{component}")
        code = int(definition.get("element_code", -1))
        unit = str(definition.get("expected_unit", "")).strip()
        if code <= 0 or not unit:
            raise NutritionContractError(f"invalid FBS element for {component}")
        element_codes.append(code)
    if len(element_codes) != len(set(element_codes)):
        raise NutritionContractError("FBS element codes must be unique")

    seen_items: dict[int, str] = {}
    for commodity in EXPECTED_COMMODITIES:
        definition = _as_mapping(products[commodity], f"commodities.{commodity}")
        food_use = definition.get("food_use")
        if not isinstance(food_use, bool):
            raise NutritionContractError(f"{commodity}.food_use must be boolean")
        source_class = str(definition.get("source_class", "")).strip()
        if source_class not in SOURCE_CLASSES:
            raise NutritionContractError(f"invalid source_class for {commodity}")
        items = definition.get("fbs_items", [])
        if not isinstance(items, list):
            raise NutritionContractError(f"{commodity}.fbs_items must be a list")
        item_codes = [int(item) for item in items]
        if len(item_codes) != len(set(item_codes)):
            raise NutritionContractError(f"duplicate FBS items within {commodity}")

        if source_class == "direct":
            if not food_use or len(item_codes) != 1:
                raise NutritionContractError(f"direct product {commodity} needs one FBS item")
        elif source_class == "aggregate":
            if not food_use or len(item_codes) < 2:
                raise NutritionContractError(f"aggregate product {commodity} needs multiple FBS items")
        elif source_class == "fallback":
            if not food_use or item_codes:
                raise NutritionContractError(f"fallback product {commodity} cannot have FBS items")
            coefficients = _as_mapping(
                definition.get("fallback_coefficients"),
                f"{commodity}.fallback_coefficients",
            )
            if set(coefficients) != set(COEFFICIENT_COLUMNS):
                raise NutritionContractError(f"incomplete fallback coefficients for {commodity}")
            for column in COEFFICIENT_COLUMNS:
                _positive_finite(coefficients[column], f"{commodity}.{column}")
            if not str(definition.get("fallback_family", "")).strip():
                raise NutritionContractError(f"fallback family is required for {commodity}")
        else:
            if food_use or item_codes or "fallback_coefficients" in definition:
                raise NutritionContractError(f"nonfood product {commodity} is not edible")
            if not str(definition.get("reason", "")).strip():
                raise NutritionContractError(f"nonfood reason is required for {commodity}")

        if food_use and not str(definition.get("food_group", "")).startswith("FG"):
            raise NutritionContractError(f"food group is required for {commodity}")
        for item in item_codes:
            previous = seen_items.get(item)
            if previous is not None:
                raise NutritionContractError(
                    f"FBS item {item} is assigned to both {previous} and {commodity}"
                )
            seen_items[item] = commodity


def load_nutrition_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and validate the nutrition configuration."""

    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config = dict(_as_mapping(raw, "nutrition configuration"))
    validate_nutrition_config(config)
    return config


def _m49(value: object) -> str | None:
    text = str(value).strip().lstrip("'")
    if not text.isdigit():
        return None
    return text.zfill(3)


def _normalized_member(zipped: zipfile.ZipFile) -> str:
    members = [
        name for name in zipped.namelist()
        if name.endswith("All_Data_(Normalized).csv")
    ]
    if len(members) != 1:
        raise NutritionContractError("expected one normalized all-data CSV in archive")
    return members[0]


def read_fbs_nutrient_components(
    archive: str | Path,
    config: Mapping[str, Any],
    *,
    allowed_m49: set[str] | None = None,
    chunksize: int = 250_000,
) -> pd.DataFrame:
    """Read paired country-item food and nutrient totals from the 2023 FBS.

    Unit identities used later are exact:

    * million kcal / thousand tonnes = kcal/kg;
    * tonnes nutrient / thousand tonnes food = g nutrient/kg food.

    Rows are paired before aggregation.  A positive food observation missing
    any nutrient component raises instead of being silently treated as zero.
    """

    validate_nutrition_config(config)
    year = int(config["benchmark_year"])
    elements = config["fbs_elements"]
    code_to_component = {
        int(definition["element_code"]): component
        for component, definition in elements.items()
    }
    expected_units = {
        int(definition["element_code"]): str(definition["expected_unit"])
        for definition in elements.values()
    }
    item_codes = {
        int(item)
        for definition in config["commodities"].values()
        for item in definition.get("fbs_items", [])
    }
    if chunksize <= 0:
        raise NutritionContractError("chunksize must be positive")

    wanted_columns = [
        "Area Code (M49)", "Item Code", "Element Code", "Year", "Unit", "Value"
    ]
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(Path(archive)) as zipped:
        member = _normalized_member(zipped)
        with zipped.open(member) as stream:
            for chunk in pd.read_csv(
                stream,
                usecols=wanted_columns,
                chunksize=chunksize,
                low_memory=False,
            ):
                item = pd.to_numeric(chunk["Item Code"], errors="coerce")
                element = pd.to_numeric(chunk["Element Code"], errors="coerce")
                years = pd.to_numeric(chunk["Year"], errors="coerce")
                keep = item.isin(item_codes) & element.isin(code_to_component) & years.eq(year)
                if not keep.any():
                    continue
                selected = chunk.loc[keep].copy()
                selected["m49"] = selected["Area Code (M49)"].map(_m49)
                selected = selected[selected["m49"].notna()]
                if allowed_m49 is not None:
                    selected = selected[selected["m49"].isin(allowed_m49)]
                if selected.empty:
                    continue
                selected["item_code"] = pd.to_numeric(
                    selected["Item Code"], errors="raise"
                ).astype(int)
                selected["element_code"] = pd.to_numeric(
                    selected["Element Code"], errors="raise"
                ).astype(int)
                selected["component"] = selected["element_code"].map(code_to_component)
                for code, rows in selected.groupby("element_code", sort=False):
                    actual_units = set(rows["Unit"].astype(str).str.strip())
                    expected_unit = expected_units[int(code)]
                    if actual_units != {expected_unit}:
                        raise NutritionContractError(
                            f"unexpected unit for FBS element {code}: "
                            f"expected {expected_unit!r}, got {sorted(actual_units)}"
                        )
                selected["value"] = pd.to_numeric(selected["Value"], errors="coerce")
                if selected["value"].isna().any():
                    raise NutritionContractError("nonnumeric FBS nutrient observation")
                values = selected["value"].to_numpy(dtype=float)
                if not np.isfinite(values).all() or (values < 0).any():
                    raise NutritionContractError("FBS food and nutrient totals must be finite and nonnegative")
                frames.append(selected[["m49", "item_code", "component", "value"]])

    if not frames:
        raise NutritionContractError("no matching 2023 FBS nutrient observations")
    long = pd.concat(frames, ignore_index=True)
    duplicate = long.duplicated(["m49", "item_code", "component"], keep=False)
    if duplicate.any():
        sample = long.loc[duplicate, ["m49", "item_code", "component"]].head(10)
        raise NutritionContractError(
            f"duplicate country-item-component FBS rows: {sample.to_dict('records')}"
        )
    wide = long.pivot(
        index=["m49", "item_code"], columns="component", values="value"
    ).reset_index()
    wide.columns.name = None
    for component in COMPONENT_COLUMNS:
        if component not in wide:
            wide[component] = np.nan

    positive_food = wide["food_quantity"].fillna(0.0).gt(0.0)
    incomplete = positive_food & wide[list(COMPONENT_COLUMNS)].isna().any(axis=1)
    if incomplete.any():
        sample = wide.loc[incomplete, ["m49", "item_code"]].head(10)
        raise NutritionContractError(
            "positive FBS food quantities have missing nutrient components: "
            f"{sample.to_dict('records')}"
        )
    paired = wide.loc[positive_food, ["m49", "item_code", *COMPONENT_COLUMNS]].copy()
    if paired.empty:
        raise NutritionContractError("no positive paired FBS food observations")
    return paired.sort_values(["m49", "item_code"]).reset_index(drop=True)


def derive_nutrition_coefficients(
    config: Mapping[str, Any],
    fbs_archive: str | Path,
    *,
    allowed_m49: set[str] | None = None,
    chunksize: int = 250_000,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build one complete, non-null coefficient row per model commodity."""

    validate_nutrition_config(config)
    paired = read_fbs_nutrient_components(
        fbs_archive, config, allowed_m49=allowed_m49, chunksize=chunksize
    )
    rows: list[dict[str, Any]] = []
    for commodity in EXPECTED_COMMODITIES:
        definition = config["commodities"][commodity]
        source_class = str(definition["source_class"])
        common: dict[str, Any] = {
            "commodity": commodity,
            "food_use": bool(definition["food_use"]),
            "source_class": source_class,
            "food_group": str(definition.get("food_group", "not_applicable")),
            "source_year": int(config["benchmark_year"]),
        }
        if source_class in {"direct", "aggregate"}:
            items = [int(item) for item in definition["fbs_items"]]
            observations = paired[paired["item_code"].isin(items)]
            observed_items = set(observations["item_code"].unique())
            missing_items = set(items) - observed_items
            if missing_items:
                raise NutritionContractError(
                    f"no positive paired FBS observations for {commodity} items "
                    f"{sorted(missing_items)}"
                )
            food = float(observations["food_quantity"].sum())
            if not isfinite(food) or food <= 0:
                raise NutritionContractError(f"nonpositive FBS food denominator for {commodity}")
            # Aggregate constituent items within a country first, then take
            # the global median of complete country-product ratios.  This is
            # robust to independently rounded FAOSTAT national totals and is
            # especially important for small reported quantities of oils.
            country_product = observations.groupby("m49", as_index=False)[
                list(COMPONENT_COLUMNS)
            ].sum()
            ratios = country_product[["energy", "protein", "fat"]].div(
                country_product["food_quantity"], axis=0
            )
            raw_coefficients = {
                "energy_kcal_per_kg": float(ratios["energy"].median()),
                "protein_g_per_kg": float(ratios["protein"].median()),
                "fat_g_per_kg": float(ratios["fat"].median()),
            }
            bounds = config["coefficient_upper_bounds"]
            bounded_coefficients = {
                column: min(value, float(bounds[column]))
                for column, value in raw_coefficients.items()
            }
            adjustments = [
                f"{column}:{raw_coefficients[column]:.12g}->{bounded_coefficients[column]:.12g}"
                for column in COEFFICIENT_COLUMNS
                if raw_coefficients[column] > bounded_coefficients[column]
            ]
            row = {
                **common,
                **bounded_coefficients,
                "source_detail": "FAOSTAT_FBS_2023_country_product_ratio_median",
                "fbs_item_codes": ",".join(str(item) for item in items),
                "paired_country_item_observations": int(len(observations)),
                "paired_country_product_observations": int(len(country_product)),
                "fbs_food_quantity_mt": food / 1000.0,
                "physical_bound_adjustments": ";".join(adjustments) or "none",
            }
        elif source_class == "fallback":
            fallback = definition["fallback_coefficients"]
            row = {
                **common,
                **{column: float(fallback[column]) for column in COEFFICIENT_COLUMNS},
                "source_detail": str(definition["fallback_family"]),
                "fbs_item_codes": "not_applicable",
                "paired_country_item_observations": 0,
                "paired_country_product_observations": 0,
                "fbs_food_quantity_mt": 0.0,
                "physical_bound_adjustments": "not_applicable",
            }
        else:
            row = {
                **common,
                **{column: 0.0 for column in COEFFICIENT_COLUMNS},
                "source_detail": str(definition["reason"]),
                "fbs_item_codes": "not_applicable",
                "paired_country_item_observations": 0,
                "paired_country_product_observations": 0,
                "fbs_food_quantity_mt": 0.0,
                "physical_bound_adjustments": "not_applicable",
            }
        rows.append(row)

    coefficients = pd.DataFrame(rows)
    numeric = coefficients[[*COEFFICIENT_COLUMNS, "fbs_food_quantity_mt"]]
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise NutritionContractError("coefficient table contains missing or nonfinite values")
    if coefficients.isna().any().any():
        raise NutritionContractError("coefficient table contains missing metadata")
    if (numeric < 0).any().any():
        raise NutritionContractError("nutrition coefficients must be nonnegative")
    food = coefficients["food_use"]
    if (coefficients.loc[food, "energy_kcal_per_kg"] <= 0).any():
        raise NutritionContractError("every edible commodity needs a positive energy coefficient")
    if (coefficients.loc[~food, list(COEFFICIENT_COLUMNS)] != 0).any().any():
        raise NutritionContractError("nonfood coefficients must be exactly zero")

    method_counts = Counter(coefficients["source_class"])
    derivation_report: dict[str, Any] = {
        "paired_country_item_observations": int(len(paired)),
        "paired_countries": int(paired["m49"].nunique()),
        "fbs_items_observed": int(paired["item_code"].nunique()),
        "source_class_counts": {
            method: int(method_counts.get(method, 0))
            for method in sorted(SOURCE_CLASSES)
        },
        "estimator": str(config["fbs_estimator"]),
        "physical_bound_adjustment_count": int(
            coefficients["physical_bound_adjustments"].ne("none").sum()
            - coefficients["physical_bound_adjustments"].eq("not_applicable").sum()
        ),
    }
    return coefficients, derivation_report


def audit_food_and_diet_archive(
    archive: str | Path,
    *,
    year: int = 2023,
    allowed_m49: set[str] | None = None,
    chunksize: int = 250_000,
) -> dict[str, Any]:
    """Audit the companion FAOSTAT Food-and-Diet nutrient supply snapshot."""

    indicators = {
        4003: ("energy", "kcal/cap/d"),
        4004: ("protein", "g/cap/d"),
        4005: ("fat", "g/cap/d"),
    }
    wanted_columns = [
        "Area Code (M49)", "Food Group Code", "Indicator Code", "Year", "Unit", "Value"
    ]
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(Path(archive)) as zipped:
        member = _normalized_member(zipped)
        with zipped.open(member) as stream:
            for chunk in pd.read_csv(
                stream,
                usecols=wanted_columns,
                chunksize=chunksize,
                low_memory=False,
            ):
                codes = pd.to_numeric(chunk["Indicator Code"], errors="coerce")
                years = pd.to_numeric(chunk["Year"], errors="coerce")
                keep = codes.isin(indicators) & years.eq(int(year))
                if not keep.any():
                    continue
                selected = chunk.loc[keep].copy()
                selected["m49"] = selected["Area Code (M49)"].map(_m49)
                selected = selected[selected["m49"].notna()]
                if allowed_m49 is not None:
                    selected = selected[selected["m49"].isin(allowed_m49)]
                if selected.empty:
                    continue
                selected["indicator_code"] = pd.to_numeric(
                    selected["Indicator Code"], errors="raise"
                ).astype(int)
                for code, rows in selected.groupby("indicator_code", sort=False):
                    actual = set(rows["Unit"].astype(str).str.strip())
                    expected = indicators[int(code)][1]
                    if actual != {expected}:
                        raise NutritionContractError(
                            f"unexpected Food-and-Diet unit for {code}: {sorted(actual)}"
                        )
                selected["nutrient"] = selected["indicator_code"].map(
                    lambda code: indicators[int(code)][0]
                )
                selected["value"] = pd.to_numeric(selected["Value"], errors="coerce")
                values = selected["value"].to_numpy(dtype=float)
                if selected["value"].isna().any() or not np.isfinite(values).all() or (values < 0).any():
                    raise NutritionContractError("invalid Food-and-Diet nutrient value")
                frames.append(
                    selected[["m49", "Food Group Code", "nutrient", "value"]].rename(
                        columns={"Food Group Code": "food_group"}
                    )
                )
    if not frames:
        raise NutritionContractError("no matching Food-and-Diet rows")
    data = pd.concat(frames, ignore_index=True)
    keys = ["m49", "food_group", "nutrient"]
    if data.duplicated(keys).any():
        raise NutritionContractError("duplicate Food-and-Diet country-group nutrient row")
    coverage = data.pivot(
        index=["m49", "food_group"], columns="nutrient", values="value"
    ).reset_index()
    complete = coverage[["energy", "protein", "fat"]].notna().all(axis=1)
    fg0 = coverage["food_group"].eq("FG0") & complete
    return {
        "status": "passed",
        "year": int(year),
        "food_groups_observed": sorted(data["food_group"].astype(str).unique()),
        "countries_observed": int(data["m49"].nunique()),
        "country_food_group_records": int(len(coverage)),
        "complete_energy_protein_fat_records": int(complete.sum()),
        "countries_with_complete_all_food_groups_fg0": int(fg0.sum()),
    }


def _coerce_bool(series: pd.Series, label: str) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(bool)
    values = series.astype(str).str.strip().str.casefold()
    mapping = {"true": True, "false": False, "1": True, "0": False}
    converted = values.map(mapping)
    if converted.isna().any():
        raise NutritionContractError(f"{label} contains non-boolean values")
    return converted.astype(bool)


def _validated_coefficient_table(coefficients: pd.DataFrame) -> pd.DataFrame:
    required = {"commodity", "food_use", "source_class", *COEFFICIENT_COLUMNS}
    missing = required - set(coefficients)
    if missing:
        raise NutritionContractError(f"coefficient table missing columns: {sorted(missing)}")
    result = coefficients.copy()
    result["commodity"] = result["commodity"].astype(str).str.strip().str.upper()
    if result["commodity"].duplicated().any():
        raise NutritionContractError("coefficient table has duplicate commodities")
    actual = set(result["commodity"])
    expected = set(EXPECTED_COMMODITIES)
    if actual != expected or len(result) != len(expected):
        raise NutritionContractError(
            f"coefficient table is not complete: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )
    result["food_use"] = _coerce_bool(result["food_use"], "food_use")
    if not set(result["source_class"]).issubset(SOURCE_CLASSES):
        raise NutritionContractError("coefficient table has invalid source_class")
    for column in COEFFICIENT_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    matrix = result[list(COEFFICIENT_COLUMNS)].to_numpy(dtype=float)
    if not np.isfinite(matrix).all() or (matrix < 0).any():
        raise NutritionContractError("coefficient values must be finite and nonnegative")
    nonfood = ~result["food_use"]
    if (result.loc[nonfood, list(COEFFICIENT_COLUMNS)] != 0).any().any():
        raise NutritionContractError("nonfood coefficient values must be zero")
    if (result.loc[nonfood, "source_class"] != "nonfood").any():
        raise NutritionContractError("nonfood rows must be labelled nonfood")
    if (result.loc[~nonfood, "source_class"] == "nonfood").any():
        raise NutritionContractError("edible rows cannot be labelled nonfood")
    return result


def postsolve_nutrition(
    food_quantities: pd.DataFrame,
    population: pd.DataFrame,
    coefficients: pd.DataFrame,
    *,
    identity_columns: Sequence[str] = ("scenario", "year"),
    economy_column: str = "economy_id",
    commodity_column: str = "commodity",
    quantity_column: str = "food_quantity_mt",
    population_column: str = "population_million",
    days_per_year: float = 365.0,
    require_complete_commodity_grid: bool = True,
    nonfood_positive_tolerance_mt: float = 1.0e-12,
) -> NutritionPostsolveResult:
    """Convert edible food quantities to country and population-weighted world nutrition.

    ``food_quantities`` must contain one row per identity/economy/commodity.
    Positive quantities for structural nonfood products are rejected.  World
    per-capita values are recalculated from summed nutrient totals and summed
    population; country per-capita results are never added or simply averaged.
    """

    days = _positive_finite(days_per_year, "days_per_year")
    tolerance = float(nonfood_positive_tolerance_mt)
    if not isfinite(tolerance) or tolerance < 0:
        raise NutritionContractError("nonfood tolerance must be finite and nonnegative")
    coefficient_table = _validated_coefficient_table(coefficients)

    food = food_quantities.copy()
    people = population.copy()
    dimensions: list[str] = []
    for column in identity_columns:
        in_food = column in food
        in_population = column in people
        if in_food != in_population:
            raise NutritionContractError(
                f"identity column {column!r} must occur in both inputs or neither"
            )
        if in_food:
            dimensions.append(column)
    required_food = {economy_column, commodity_column, quantity_column}
    required_population = {economy_column, population_column}
    if required_food - set(food):
        raise NutritionContractError(
            f"food input missing columns: {sorted(required_food - set(food))}"
        )
    if required_population - set(people):
        raise NutritionContractError(
            "population input missing columns: "
            f"{sorted(required_population - set(people))}"
        )

    food[economy_column] = food[economy_column].astype(str).str.strip().str.upper()
    people[economy_column] = people[economy_column].astype(str).str.strip().str.upper()
    food[commodity_column] = food[commodity_column].astype(str).str.strip().str.upper()
    if food[economy_column].eq("").any() or people[economy_column].eq("").any():
        raise NutritionContractError("blank economy identifiers are forbidden")
    if food[economy_column].eq("WORLD").any() or people[economy_column].eq("WORLD").any():
        raise NutritionContractError("WORLD is a derived aggregate, not an input economy")
    unknown = set(food[commodity_column]) - set(EXPECTED_COMMODITIES)
    if unknown:
        raise NutritionContractError(f"unknown food commodities: {sorted(unknown)}")

    food[quantity_column] = pd.to_numeric(food[quantity_column], errors="coerce")
    people[population_column] = pd.to_numeric(people[population_column], errors="coerce")
    quantities = food[quantity_column].to_numpy(dtype=float)
    populations = people[population_column].to_numpy(dtype=float)
    if not np.isfinite(quantities).all() or (quantities < 0).any():
        raise NutritionContractError("food quantities must be finite and nonnegative")
    if not np.isfinite(populations).all() or (populations <= 0).any():
        raise NutritionContractError("population must be finite and strictly positive")

    food_keys = [*dimensions, economy_column, commodity_column]
    population_keys = [*dimensions, economy_column]
    if food.duplicated(food_keys).any():
        raise NutritionContractError("duplicate identity/economy/commodity food rows")
    if people.duplicated(population_keys).any():
        raise NutritionContractError("duplicate identity/economy population rows")

    if require_complete_commodity_grid:
        expected = set(EXPECTED_COMMODITIES)
        for key, group in food.groupby(population_keys, dropna=False, sort=False):
            actual = set(group[commodity_column])
            if actual != expected or len(group) != len(expected):
                raise NutritionContractError(
                    f"incomplete commodity grid for {key}: "
                    f"missing={sorted(expected - actual)}"
                )

    food_accounts = food[population_keys].drop_duplicates()
    population_accounts = people[population_keys].drop_duplicates()
    account_check = food_accounts.merge(
        population_accounts,
        on=population_keys,
        how="outer",
        indicator=True,
        validate="one_to_one",
    )
    if not account_check["_merge"].eq("both").all():
        raise NutritionContractError("food and population economy identities do not match exactly")

    contributions = food.merge(
        coefficient_table[
            ["commodity", "food_use", "source_class", *COEFFICIENT_COLUMNS]
        ],
        left_on=commodity_column,
        right_on="commodity",
        how="left",
        validate="many_to_one",
    )
    if commodity_column != "commodity":
        contributions = contributions.drop(columns=["commodity"])
    positive_nonfood = (~contributions["food_use"]) & contributions[quantity_column].gt(tolerance)
    if positive_nonfood.any():
        sample = contributions.loc[
            positive_nonfood, [*population_keys, commodity_column, quantity_column]
        ].head(10)
        raise NutritionContractError(
            "structural nonfood products have positive edible-food quantity: "
            f"{sample.to_dict('records')}"
        )

    # 1 Mt = 1e9 kg.  Multiplication by g/kg directly yields total grams.
    kilograms = contributions[quantity_column] * 1.0e9
    contributions["energy_kcal"] = kilograms * contributions["energy_kcal_per_kg"]
    contributions["protein_g"] = kilograms * contributions["protein_g_per_kg"]
    contributions["fat_g"] = kilograms * contributions["fat_g_per_kg"]

    total_columns = [quantity_column, "energy_kcal", "protein_g", "fat_g"]
    economy = (
        contributions.groupby(population_keys, dropna=False, as_index=False)[total_columns]
        .sum()
        .merge(
            people[[*population_keys, population_column]],
            on=population_keys,
            how="left",
            validate="one_to_one",
        )
    )
    divisor = economy[population_column] * 1.0e6 * days
    economy["kcal_per_capita_day"] = economy["energy_kcal"] / divisor
    economy["protein_g_per_capita_day"] = economy["protein_g"] / divisor
    economy["fat_g_per_capita_day"] = economy["fat_g"] / divisor
    economy["aggregation_level"] = "economy"

    aggregate_columns = [population_column, *total_columns]
    if dimensions:
        world = economy.groupby(dimensions, dropna=False, as_index=False)[aggregate_columns].sum()
    else:
        world = pd.DataFrame(
            [{column: float(economy[column].sum()) for column in aggregate_columns}]
        )
    world[economy_column] = "WORLD"
    divisor = world[population_column] * 1.0e6 * days
    world["kcal_per_capita_day"] = world["energy_kcal"] / divisor
    world["protein_g_per_capita_day"] = world["protein_g"] / divisor
    world["fat_g_per_capita_day"] = world["fat_g"] / divisor
    world["aggregation_level"] = "world"

    ordered = [
        *dimensions, economy_column, "aggregation_level", population_column,
        quantity_column, "energy_kcal", "protein_g", "fat_g",
        "kcal_per_capita_day", "protein_g_per_capita_day", "fat_g_per_capita_day",
    ]
    economy = economy[ordered].sort_values([*dimensions, economy_column]).reset_index(drop=True)
    world = world[ordered].sort_values(dimensions or [economy_column]).reset_index(drop=True)

    summary_numeric = [
        population_column, quantity_column, "energy_kcal", "protein_g", "fat_g",
        "kcal_per_capita_day", "protein_g_per_capita_day", "fat_g_per_capita_day",
    ]
    if economy[summary_numeric].isna().any().any() or world[summary_numeric].isna().any().any():
        raise NutritionContractError("nutrition postsolve produced missing values")
    # The groupby construction is the accounting identity; retain a numerical
    # assertion so later refactors cannot accidentally average per-capita rows.
    for column in aggregate_columns:
        if dimensions:
            country_totals = economy.groupby(dimensions, dropna=False)[column].sum().sort_index()
            world_totals = world.set_index(dimensions)[column].sort_index()
            if not np.allclose(country_totals, world_totals, rtol=1.0e-12, atol=1.0e-6):
                raise NutritionContractError(f"world conservation failed for {column}")
        elif not np.isclose(economy[column].sum(), world[column].iat[0], rtol=1.0e-12, atol=1.0e-6):
            raise NutritionContractError(f"world conservation failed for {column}")

    return NutritionPostsolveResult(
        commodity_contributions=contributions,
        economy=economy,
        world=world,
    )


def build_nutrition_coefficients(
    *,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    verify_hashes: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build and write the coefficient table plus full 2023 coverage report."""

    config = load_nutrition_config(config_path)
    catalog = load_source_catalog()
    fbs = catalog.source("fao_fbs")
    food_and_diet = catalog.source("fao_nutrition")
    un_m49 = catalog.source("un_m49")
    if verify_hashes:
        for source in (fbs, food_and_diet, un_m49):
            verify_source(source)
    countries = country_codebook(un_m49.path)
    allowed_m49 = set(countries["m49"].astype(str).str.zfill(3))
    coefficients, derivation = derive_nutrition_coefficients(
        config, fbs.path, allowed_m49=allowed_m49
    )
    food_and_diet_audit = audit_food_and_diet_archive(
        food_and_diet.path,
        year=int(config["benchmark_year"]),
        allowed_m49=allowed_m49,
    )
    counts = Counter(coefficients["source_class"])
    report: dict[str, Any] = {
        "status": "passed_complete_31_commodity_coverage",
        "benchmark_year": int(config["benchmark_year"]),
        "commodity_count": int(len(coefficients)),
        "edible_commodity_count": int(coefficients["food_use"].sum()),
        "nonfood_commodity_count": int((~coefficients["food_use"]).sum()),
        "source_class_counts": {
            method: int(counts.get(method, 0)) for method in sorted(SOURCE_CLASSES)
        },
        "missing_coefficient_cells": int(
            coefficients[list(COEFFICIENT_COLUMNS)].isna().sum().sum()
        ),
        "nonfood_commodities": coefficients.loc[
            ~coefficients["food_use"], "commodity"
        ].tolist(),
        "fallback_commodities": coefficients.loc[
            coefficients["source_class"].eq("fallback"), "commodity"
        ].tolist(),
        "coefficient_units": dict(config["coefficient_units"]),
        "coefficient_upper_bounds": dict(config["coefficient_upper_bounds"]),
        "postsolve_input_contract": dict(config["input_contract"]),
        "fbs_derivation": derivation,
        "food_and_diet_audit": food_and_diet_audit,
        "source_ids": {
            "fbs": fbs.source_id,
            "food_and_diet": food_and_diet.source_id,
        },
        "publishability_note": (
            "FAOSTAT-derived rows are reproducible from the frozen 2023 snapshot; "
            "fallback dairy coefficients remain explicit frozen technical assumptions."
        ),
    }

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    coefficient_path = destination / "nutrition_coefficients_2023.csv"
    report_path = destination / "nutrition_coefficients_2023_coverage_report.json"
    coefficients.to_csv(coefficient_path, index=False)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return coefficients, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--skip-sha256",
        action="store_true",
        help="use the manifest/path contract without rereading source hashes",
    )
    args = parser.parse_args()
    coefficients, report = build_nutrition_coefficients(
        config_path=args.config,
        output_dir=args.output_dir,
        verify_hashes=not args.skip_sha256,
    )
    print(
        f"wrote {len(coefficients)} coefficients; status={report['status']}; "
        f"edible={report['edible_commodity_count']}; "
        f"nonfood={report['nonfood_commodity_count']}"
    )


if __name__ == "__main__":
    main()
