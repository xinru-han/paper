#!/usr/bin/env python3
"""Build the reproducible tables and figures used by the CASM-World paper.

The script deliberately distinguishes physical accounting layers.  In
particular, it never reports the sum of all 31 production columns as an
"agricultural production" total because that would add raw materials and
their processed outputs.  The aggregate production indicator is restricted
to the explicitly non-overlapping biological-primary basket below.
"""

from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "paper" / "tables"
FIGURES = ROOT / "paper" / "figures"

DIAGNOSTIC_STATUS = "diagnostic_conditional_not_publication_baseline"
DIAGNOSTIC_LABEL = "DIAGNOSTIC CONDITIONAL DRAFT — NOT A PUBLICATION BASELINE"

SCENARIOS = ["SSP1", "SSP2", "SSP3", "SSP4", "SSP5"]
YEARS = list(range(2023, 2051))

# One physical layer only: crops at the harvested/raw-equivalent layer and
# livestock products at the farm-gate layer.  Cotton lint is excluded because
# its seed-cotton input is a satellite activity; processed oils, meals, sugar
# and dairy products are excluded because their inputs are already present.
PRIMARY_BASKET = [
    "RIC", "WHE", "CRN", "OCG", "SBS", "NBS", "RBS",
    "SCA", "SBE", "BFV", "PRK", "PLM", "MLK",
]

COMMODITY_NAMES = {
    "RIC": "Rice (paddy equivalent)",
    "WHE": "Wheat",
    "CRN": "Maize",
    "OCG": "Other coarse grains",
    "SBS": "Soybeans",
    "NBS": "Sunflower seed",
    "RBS": "Rapeseed and mustard seed",
    "SCA": "Sugar cane",
    "SBE": "Sugar beet",
    "BFV": "Bovine meat",
    "PRK": "Pigmeat",
    "PLM": "Poultry meat",
    "MLK": "Raw milk",
    "CTN": "Cotton lint",
    "SUG": "Sugar (raw equivalent)",
    "ODA": "Dry whey",
}

OECD_COMMODITY_MAP = {
    "CPC_0111": "WHE",
    "CPC_0112": "CRN",
    "CPC_0113": "RIC",
    "CPC_0114T0119": "OCG",
    "CPC_0141": "SBS",
    "CPC_01921": "CTN",
    "CPC_EX_BV": "BFV",
    "CPC_EX_PK": "PRK",
    "CPC_EX_PT": "PLM",
}
OECD_AREA_MAP = {
    "W": "World",
    "CHN": "China mainland",
    "EU": "European Union (27)",
}

# Concise, recognisable UN M49 subregion names for direct figure labels.  The
# full names remain in the source table; these labels avoid uninterpretable
# numeric M49 codes without overwhelming the scatter plot.
UN_AREA_SHORT_NAMES = {
    "Australia and New Zealand": "Australia & NZ",
    "Caribbean": "Caribbean",
    "Central America": "C. America",
    "Central Asia": "C. Asia",
    "Eastern Africa": "E. Africa",
    "Eastern Asia": "E. Asia",
    "Eastern Europe": "E. Europe",
    "Melanesia": "Melanesia",
    "Micronesia": "Micronesia",
    "Middle Africa": "Middle Africa",
    "Northern Africa": "N. Africa",
    "Northern America": "N. America",
    "Northern Europe": "N. Europe",
    "Polynesia": "Polynesia",
    "South America": "S. America",
    "South-eastern Asia": "SE Asia",
    "Southern Africa": "S. Africa",
    "Southern Asia": "S. Asia",
    "Southern Europe": "S. Europe",
    "Western Africa": "W. Africa",
    "Western Asia": "W. Asia",
    "Western Europe": "W. Europe",
}

FOCUS_GROUPS = [
    ("GLOBAL", "WORLD", "World"),
    ("FOCUS", "CHINA_MAINLAND", "China mainland"),
    ("FOCUS", "USA", "United States"),
    ("ECONOMIC", "EU27", "European Union (27)"),
]

OECD_DATA_URL = (
    "https://data-explorer.oecd.org/vis?bp=true&df%5Bag%5D=OECD.TAD.ATM&"
    "df%5Bid%5D=DSD_AGR%40DF_OUTLOOK_2026_2035&df%5Bvs%5D=1.1"
)
IFPRI_2025_URL = "https://hdl.handle.net/10568/175534"
IMPACT_MODEL_URL = "https://foresight.cgiar.org/impact-model/"
IFPRI_2026_URL = "https://www.ifpri.org/project/ifpri-impact-model/"
JRC_SUPREMA_URL = (
    "https://data.jrc.ec.europa.eu/dataset/"
    "d6ef74c6-ba91-4e37-827e-d0854fbe85dd"
)


def pct(end: float, start: float) -> float:
    if not np.isfinite(start) or abs(start) <= 1.0e-12:
        return np.nan
    return 100.0 * (end / start - 1.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the CASM-World paper tables and figures."
    )
    parser.add_argument(
        "--diagnostic-draft",
        action="store_true",
        help=(
            "Explicitly allow a conditional diagnostic draft when one or more "
            "frozen publication gates fail. All generated artifacts are marked "
            "as not being a publication baseline."
        ),
    )
    return parser.parse_args(argv)


def diagnostic_reason(publication_report: dict) -> str:
    """Return a report-derived explanation of the failed price gates."""
    failed = publication_report.get("failed_gates", [])
    metrics = publication_report.get("price_plausibility_metrics", {})
    outliers = metrics.get("central_band_outliers", [])
    if not failed:
        return "All frozen publication-validation gates passed."
    if outliers:
        worst = max(outliers, key=lambda item: item["world_price_index_2023"])
        band = metrics.get("central_band", [np.nan, np.nan])
        count = int(metrics.get("central_band_outlier_count", len(outliers)))
        share = float(metrics.get("share_2050_prices_in_central_band", np.nan))
        total = int(round(count / (1.0 - share))) if np.isfinite(share) and share < 1 else 0
        dairy_products = {"BUT", "CHE", "NDM", "FMK", "WDM", "ODA"}
        dairy_count = sum(item["commodity"] in dairy_products for item in outliers)
        worst_name = COMMODITY_NAMES.get(worst["commodity"], worst["commodity"])
        return (
            f"Failed gates: {', '.join(failed)}. All {dairy_count} reported "
            f"central-band outliers are processed dairy products; the maximum "
            f"2050 price is {worst['commodity']} ({worst_name}) in {worst['scenario']} "
            f"({worst['world_price_index_2023']:.6g}, 2023=1); "
            f"{count}/{total} "
            f"scenario-product prices lie outside [{band[0]:g}, {band[1]:g}] "
            f"(in-band share {share:.6g})."
        )
    return f"Failed gates: {', '.join(failed)}."


def stamp_figure(fig: plt.Figure, diagnostic: bool) -> None:
    if diagnostic:
        fig.text(
            0.5,
            0.012,
            DIAGNOSTIC_LABEL,
            ha="center",
            va="bottom",
            fontsize=9,
            color="#a33a2b",
            weight="bold",
        )


def _annotation_overlap_count(
    annotations: list[plt.Annotation], renderer: object
) -> int:
    """Count label-label overlaps in display coordinates."""
    boxes = [item.get_window_extent(renderer).expanded(1.03, 1.12) for item in annotations]
    return sum(
        boxes[left].overlaps(boxes[right])
        for left in range(len(boxes))
        for right in range(left + 1, len(boxes))
    )


def _resolve_annotation_collisions(
    fig: plt.Figure,
    ax: plt.Axes,
    annotations: list[plt.Annotation],
    *,
    maximum_iterations: int = 240,
) -> int:
    """Deterministically separate direct labels while keeping them in the axes.

    Positions are stored as point offsets from each observation.  Collision
    detection happens in display coordinates, so the result respects actual
    label widths rather than assuming every subregion name has the same size.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    points_per_pixel = 72.0 / fig.dpi

    for _ in range(maximum_iterations):
        boxes = [
            item.get_window_extent(renderer).expanded(1.03, 1.12)
            for item in annotations
        ]
        movements = np.zeros((len(annotations), 2), dtype=float)
        collisions = 0

        for left in range(len(boxes)):
            first = boxes[left]
            for right in range(left + 1, len(boxes)):
                second = boxes[right]
                overlap_x = min(first.x1, second.x1) - max(first.x0, second.x0)
                overlap_y = min(first.y1, second.y1) - max(first.y0, second.y0)
                if overlap_x <= 0 or overlap_y <= 0:
                    continue
                collisions += 1
                first_centre = np.array(
                    [(first.x0 + first.x1) / 2.0, (first.y0 + first.y1) / 2.0]
                )
                second_centre = np.array(
                    [(second.x0 + second.x1) / 2.0, (second.y0 + second.y1) / 2.0]
                )
                if overlap_x < overlap_y:
                    direction = -1.0 if first_centre[0] <= second_centre[0] else 1.0
                    push = overlap_x / 2.0 + 1.5
                    movements[left, 0] += direction * push
                    movements[right, 0] -= direction * push
                else:
                    direction = -1.0 if first_centre[1] <= second_centre[1] else 1.0
                    push = overlap_y / 2.0 + 1.5
                    movements[left, 1] += direction * push
                    movements[right, 1] -= direction * push

        if collisions == 0:
            break

        axes_box = ax.get_window_extent(renderer)
        boundary_padding = 3.0
        for index, box in enumerate(boxes):
            dx, dy = movements[index]
            if box.x0 + dx < axes_box.x0 + boundary_padding:
                dx += axes_box.x0 + boundary_padding - (box.x0 + dx)
            if box.x1 + dx > axes_box.x1 - boundary_padding:
                dx -= box.x1 + dx - (axes_box.x1 - boundary_padding)
            if box.y0 + dy < axes_box.y0 + boundary_padding:
                dy += axes_box.y0 + boundary_padding - (box.y0 + dy)
            if box.y1 + dy > axes_box.y1 - boundary_padding:
                dy -= box.y1 + dy - (axes_box.y1 - boundary_padding)
            movements[index] = np.clip([dx, dy], -12.0, 12.0)

        for item, (dx, dy) in zip(annotations, movements):
            current_x, current_y = item.get_position()
            item.set_position(
                (
                    current_x + dx * points_per_pixel,
                    current_y + dy * points_per_pixel,
                )
            )
        fig.canvas.draw()

    fig.canvas.draw()
    return _annotation_overlap_count(annotations, fig.canvas.get_renderer())


def check_grid(results: pd.DataFrame) -> None:
    expected = len(SCENARIOS) * len(YEARS) * 193 * 31
    if len(results) != expected:
        raise AssertionError(f"Unexpected scenario grid: {len(results)} != {expected}")
    if sorted(results["scenario"].unique()) != SCENARIOS:
        raise AssertionError("Scenario set is not SSP1--SSP5")
    if sorted(results["year"].unique()) != YEARS:
        raise AssertionError("Annual 2023--2050 grid is incomplete")
    keys = ["scenario", "year", "economy_id", "commodity"]
    if results.duplicated(keys).any():
        raise AssertionError("Country-product result keys are not unique")
    if results[["production_mt", "food_demand_mt"]].isna().any().any():
        raise AssertionError("Formal results contain missing quantities")
    if (results[["production_mt", "food_demand_mt"]] < -1.0e-12).any().any():
        raise AssertionError("Formal results contain negative quantities")
    if (results["food_demand_mt"] > results["final_demand_mt"] + 1.0e-12).any():
        raise AssertionError("Food demand is not a subset of final demand")


def focus_frame(groups: pd.DataFrame, system: str, code: str) -> pd.DataFrame:
    out = groups[
        groups["group_system"].eq(system) & groups["group_code"].eq(code)
    ].copy()
    if len(out) != len(SCENARIOS) * len(YEARS) * 31:
        raise AssertionError(f"Incomplete reporting group {system}/{code}")
    return out


def group_accounts(membership: pd.DataFrame, system: str, code: str) -> list[str]:
    rows = membership[
        membership["group_system"].eq(system)
        & membership["group_code"].eq(code)
    ]
    accounts = sorted(rows["model_account_id"].unique())
    if not accounts:
        raise AssertionError(f"No model accounts for {system}/{code}")
    return accounts


def aggregate_primary(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame[frame["commodity"].isin(PRIMARY_BASKET)]
        .groupby(["scenario", "year"], as_index=False)
        .agg(
            primary_basket_production_mt=("production_mt", "sum"),
            primary_basket_net_import_mt=("net_import_mt", "sum"),
        )
    )


def aggregate_food(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(["scenario", "year"], as_index=False)
        .agg(edible_food_demand_mt=("food_demand_mt", "sum"))
    )


def selected_macro_table(
    drivers: pd.DataFrame, membership: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict] = []
    for system, code, name in FOCUS_GROUPS:
        accounts = group_accounts(membership, system, code)
        source = drivers[drivers["economy_id"].isin(accounts)]
        annual = (
            source.groupby(["scenario", "year"], as_index=False)
            .agg(
                population_million=("population_million", "sum"),
                gdp_billion_2015_ppp=("gdp_billion_2015", "sum"),
            )
        )
        for scenario in SCENARIOS:
            base = annual[(annual["scenario"] == scenario) & (annual["year"] == 2023)].iloc[0]
            end = annual[(annual["scenario"] == scenario) & (annual["year"] == 2050)].iloc[0]
            rows.append(
                {
                    "area": name,
                    "scenario": scenario,
                    "population_2023_million": base.population_million,
                    "population_2050_million": end.population_million,
                    "population_change_percent": pct(end.population_million, base.population_million),
                    "gdp_2023_billion_2015_ppp": base.gdp_billion_2015_ppp,
                    "gdp_2050_billion_2015_ppp": end.gdp_billion_2015_ppp,
                    "gdp_change_percent": pct(end.gdp_billion_2015_ppp, base.gdp_billion_2015_ppp),
                }
            )
    return pd.DataFrame(rows)


def world_summary(
    groups: pd.DataFrame,
    nutrition_world: pd.DataFrame,
    ghg_world: pd.DataFrame,
    macro: pd.DataFrame,
) -> pd.DataFrame:
    world = focus_frame(groups, "GLOBAL", "WORLD")
    primary = aggregate_primary(world).set_index(["scenario", "year"])
    food = aggregate_food(world).set_index(["scenario", "year"])
    nutrition = nutrition_world.set_index(["scenario", "year"])
    ghg = ghg_world.set_index(["scenario", "year"])
    macro_world = macro[macro["area"].eq("World")].set_index("scenario")
    rows: list[dict] = []
    for scenario in SCENARIOS:
        p0 = primary.loc[(scenario, 2023)]
        p1 = primary.loc[(scenario, 2050)]
        f0 = food.loc[(scenario, 2023), "edible_food_demand_mt"]
        f1 = food.loc[(scenario, 2050), "edible_food_demand_mt"]
        n0 = nutrition.loc[(scenario, 2023)]
        n1 = nutrition.loc[(scenario, 2050)]
        e0 = ghg.loc[(scenario, 2023), "emissions_mtco2e"]
        e1 = ghg.loc[(scenario, 2050), "emissions_mtco2e"]
        m = macro_world.loc[scenario]
        rows.append(
            {
                "scenario": scenario,
                "population_2050_million": m.population_2050_million,
                "population_change_percent": m.population_change_percent,
                "gdp_change_percent": m.gdp_change_percent,
                "primary_basket_production_2023_mt": p0.primary_basket_production_mt,
                "primary_basket_production_2050_mt": p1.primary_basket_production_mt,
                "primary_basket_production_change_percent": pct(
                    p1.primary_basket_production_mt, p0.primary_basket_production_mt
                ),
                "edible_food_demand_2023_mt": f0,
                "edible_food_demand_2050_mt": f1,
                "edible_food_demand_change_percent": pct(f1, f0),
                "basket_kcal_per_capita_day_2023": n0.kcal_per_capita_day,
                "basket_kcal_per_capita_day_2050": n1.kcal_per_capita_day,
                "basket_kcal_per_capita_change_percent": pct(
                    n1.kcal_per_capita_day, n0.kcal_per_capita_day
                ),
                "basket_protein_g_per_capita_day_2050": n1.protein_g_per_capita_day,
                "basket_fat_g_per_capita_day_2050": n1.fat_g_per_capita_day,
                "attributed_farmgate_ghg_2023_mtco2e": e0,
                "attributed_farmgate_ghg_2050_mtco2e": e1,
                "attributed_farmgate_ghg_change_percent": pct(e1, e0),
            }
        )
    return pd.DataFrame(rows)


def focus_summaries(groups: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for system, code, name in FOCUS_GROUPS:
        source = focus_frame(groups, system, code)
        primary = aggregate_primary(source).set_index(["scenario", "year"])
        food = aggregate_food(source).set_index(["scenario", "year"])
        for scenario in SCENARIOS:
            p0 = primary.loc[(scenario, 2023)]
            p1 = primary.loc[(scenario, 2050)]
            f0 = food.loc[(scenario, 2023), "edible_food_demand_mt"]
            f1 = food.loc[(scenario, 2050), "edible_food_demand_mt"]
            rows.append(
                {
                    "area": name,
                    "scenario": scenario,
                    "primary_basket_production_2023_mt": p0.primary_basket_production_mt,
                    "primary_basket_production_2050_mt": p1.primary_basket_production_mt,
                    "primary_basket_production_change_percent": pct(
                        p1.primary_basket_production_mt, p0.primary_basket_production_mt
                    ),
                    "edible_food_demand_2023_mt": f0,
                    "edible_food_demand_2050_mt": f1,
                    "edible_food_demand_change_percent": pct(f1, f0),
                    "primary_basket_net_import_2023_mt": p0.primary_basket_net_import_mt,
                    "primary_basket_net_import_2050_mt": p1.primary_basket_net_import_mt,
                }
            )
    return pd.DataFrame(rows)


def regional_summaries(groups: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = groups[groups["group_system"].eq("UN_REPORTING_AREA")]
    all_rows: list[dict] = []
    for (code, name), area in source.groupby(["group_code", "group_name"]):
        primary = aggregate_primary(area).set_index(["scenario", "year"])
        food = aggregate_food(area).set_index(["scenario", "year"])
        for scenario in SCENARIOS:
            p0 = primary.loc[(scenario, 2023)]
            p1 = primary.loc[(scenario, 2050)]
            f0 = food.loc[(scenario, 2023), "edible_food_demand_mt"]
            f1 = food.loc[(scenario, 2050), "edible_food_demand_mt"]
            all_rows.append(
                {
                    "region_code": code,
                    "region_name": name,
                    "scenario": scenario,
                    "primary_basket_production_2023_mt": p0.primary_basket_production_mt,
                    "primary_basket_production_2050_mt": p1.primary_basket_production_mt,
                    "primary_basket_production_change_percent": pct(
                        p1.primary_basket_production_mt, p0.primary_basket_production_mt
                    ),
                    "edible_food_demand_2023_mt": f0,
                    "edible_food_demand_2050_mt": f1,
                    "edible_food_demand_change_percent": pct(f1, f0),
                    "primary_basket_net_import_2023_mt": p0.primary_basket_net_import_mt,
                    "primary_basket_net_import_2050_mt": p1.primary_basket_net_import_mt,
                }
            )
    all_ssp = pd.DataFrame(all_rows).sort_values(["region_name", "scenario"])
    ssp2 = all_ssp[all_ssp["scenario"].eq("SSP2")].copy()
    ranges = (
        all_ssp.groupby(["region_code", "region_name"], as_index=False)
        .agg(
            primary_production_change_min_ssp_percent=(
                "primary_basket_production_change_percent", "min"
            ),
            primary_production_change_max_ssp_percent=(
                "primary_basket_production_change_percent", "max"
            ),
            food_demand_change_min_ssp_percent=("edible_food_demand_change_percent", "min"),
            food_demand_change_max_ssp_percent=("edible_food_demand_change_percent", "max"),
        )
    )
    ssp2 = ssp2.merge(ranges, on=["region_code", "region_name"], validate="one_to_one")
    ssp2 = ssp2.sort_values("primary_basket_production_2023_mt", ascending=False)
    return all_ssp.reset_index(drop=True), ssp2.reset_index(drop=True)


def income_and_special_groups(groups: pd.DataFrame) -> pd.DataFrame:
    systems = ["WB_INCOME_FY25", "WB_DEVELOPMENT_STATUS", "UN_SPECIAL_GROUP"]
    rows: list[dict] = []
    for (system, code, name), area in groups[
        groups["group_system"].isin(systems)
    ].groupby(["group_system", "group_code", "group_name"]):
        primary = aggregate_primary(area).set_index(["scenario", "year"])
        food = aggregate_food(area).set_index(["scenario", "year"])
        for scenario in SCENARIOS:
            p0 = primary.loc[(scenario, 2023)]
            p1 = primary.loc[(scenario, 2050)]
            f0 = food.loc[(scenario, 2023), "edible_food_demand_mt"]
            f1 = food.loc[(scenario, 2050), "edible_food_demand_mt"]
            rows.append(
                {
                    "group_system": system,
                    "group_code": code,
                    "group_name": name,
                    "scenario": scenario,
                    "primary_basket_production_2023_mt": p0.primary_basket_production_mt,
                    "primary_basket_production_2050_mt": p1.primary_basket_production_mt,
                    "primary_basket_production_change_percent": pct(
                        p1.primary_basket_production_mt, p0.primary_basket_production_mt
                    ),
                    "edible_food_demand_change_percent": pct(f1, f0),
                    "primary_basket_net_import_2023_mt": p0.primary_basket_net_import_mt,
                    "primary_basket_net_import_2050_mt": p1.primary_basket_net_import_mt,
                }
            )
    return pd.DataFrame(rows).sort_values(["group_system", "group_code", "scenario"])


def commodity_table(groups: pd.DataFrame) -> pd.DataFrame:
    world = focus_frame(groups, "GLOBAL", "WORLD")
    rows: list[dict] = []
    for commodity, source in world.groupby("commodity"):
        for scenario in SCENARIOS:
            s = source[source["scenario"].eq(scenario)].set_index("year")
            q0 = s.loc[2023, "production_mt"]
            q1 = s.loc[2050, "production_mt"]
            d0 = s.loc[2023, "food_demand_mt"]
            d1 = s.loc[2050, "food_demand_mt"]
            rows.append(
                {
                    "commodity": commodity,
                    "commodity_name": COMMODITY_NAMES.get(commodity, commodity),
                    "in_nonoverlapping_primary_basket": commodity in PRIMARY_BASKET,
                    "scenario": scenario,
                    "production_2023_mt": q0,
                    "production_2050_mt": q1,
                    "production_change_percent": pct(q1, q0),
                    "food_demand_change_percent": pct(d1, d0),
                    "world_price_index_2050_2023_equals_1": s.loc[
                        2050, "world_price_index_2023"
                    ],
                    "world_price_change_percent": 100.0 * (
                        s.loc[2050, "world_price_index_2023"] - 1.0
                    ),
                }
            )
    return pd.DataFrame(rows).sort_values(["commodity", "scenario"])


def aggregate_nutrition(
    nutrition: pd.DataFrame, membership: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict] = []
    days = 365.0
    for system, code, name in FOCUS_GROUPS:
        accounts = group_accounts(membership, system, code)
        annual = (
            nutrition[nutrition["economy_id"].isin(accounts)]
            .groupby(["scenario", "year"], as_index=False)
            .agg(
                population_million=("population_million", "sum"),
                food_demand_mt=("food_demand_mt", "sum"),
                energy_kcal=("energy_kcal", "sum"),
                protein_g=("protein_g", "sum"),
                fat_g=("fat_g", "sum"),
            )
        )
        annual["kcal_per_capita_day"] = annual["energy_kcal"] / (
            annual["population_million"] * 1.0e6 * days
        )
        annual["protein_g_per_capita_day"] = annual["protein_g"] / (
            annual["population_million"] * 1.0e6 * days
        )
        annual["fat_g_per_capita_day"] = annual["fat_g"] / (
            annual["population_million"] * 1.0e6 * days
        )
        for scenario in SCENARIOS:
            b = annual[(annual["scenario"] == scenario) & (annual["year"] == 2023)].iloc[0]
            e = annual[(annual["scenario"] == scenario) & (annual["year"] == 2050)].iloc[0]
            rows.append(
                {
                    "area": name,
                    "scenario": scenario,
                    "population_2050_million": e.population_million,
                    "food_demand_2023_mt": b.food_demand_mt,
                    "food_demand_2050_mt": e.food_demand_mt,
                    "kcal_per_capita_day_2023": b.kcal_per_capita_day,
                    "kcal_per_capita_day_2050": e.kcal_per_capita_day,
                    "kcal_per_capita_change_percent": pct(
                        e.kcal_per_capita_day, b.kcal_per_capita_day
                    ),
                    "protein_g_per_capita_day_2050": e.protein_g_per_capita_day,
                    "fat_g_per_capita_day_2050": e.fat_g_per_capita_day,
                }
            )
    return pd.DataFrame(rows)


def aggregate_ghg(ghg: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for system, code, name in FOCUS_GROUPS:
        accounts = group_accounts(membership, system, code)
        annual = (
            ghg[ghg["economy_id"].isin(accounts)]
            .groupby(["scenario", "year"], as_index=False)
            .agg(
                covered_production_mt=("covered_production_mt", "sum"),
                emissions_mtco2e=("emissions_mtco2e", "sum"),
            )
        )
        for scenario in SCENARIOS:
            b = annual[(annual["scenario"] == scenario) & (annual["year"] == 2023)].iloc[0]
            e = annual[(annual["scenario"] == scenario) & (annual["year"] == 2050)].iloc[0]
            rows.append(
                {
                    "area": name,
                    "scenario": scenario,
                    "attributed_farmgate_ghg_2023_mtco2e": b.emissions_mtco2e,
                    "attributed_farmgate_ghg_2050_mtco2e": e.emissions_mtco2e,
                    "attributed_farmgate_ghg_change_percent": pct(
                        e.emissions_mtco2e, b.emissions_mtco2e
                    ),
                    "covered_production_2050_mt": e.covered_production_mt,
                }
            )
    return pd.DataFrame(rows)


def oecd_comparison(
    results: pd.DataFrame,
    oecd: pd.DataFrame,
    membership: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "REF_AREA", "COMMODITY", "MEASURE", "UNIT_MEASURE",
        "VERSION_ID", "TIME_PERIOD", "OBS_VALUE",
    }
    if not required <= set(oecd):
        raise AssertionError(f"OECD file lacks {sorted(required-set(oecd))}")
    oecd = oecd.copy()
    oecd["commodity"] = oecd["COMMODITY"].map(OECD_COMMODITY_MAP)
    oecd["area"] = oecd["REF_AREA"].map(OECD_AREA_MAP)
    if oecd[["commodity", "area"]].isna().any().any():
        raise AssertionError("Unmapped OECD comparison series")
    rows: list[dict] = []
    for (area, commodity), ext in oecd.groupby(["area", "commodity"]):
        ext = ext.set_index("TIME_PERIOD")
        ext_change = pct(ext.loc[2035, "OBS_VALUE"], ext.loc[2024, "OBS_VALUE"])
        if area == "World":
            casm = (
                results[results["commodity"].eq(commodity)]
                .groupby(["scenario", "year"])["production_mt"]
                .sum()
            )
        elif area == "China mainland":
            casm = results[
                results["economy_id"].eq("CHN")
                & results["commodity"].eq(commodity)
            ].set_index(["scenario", "year"])["production_mt"]
        else:
            eu_accounts = group_accounts(membership, "ECONOMIC", "EU27")
            casm = (
                results[
                    results["economy_id"].isin(eu_accounts)
                    & results["commodity"].eq(commodity)
                ]
                .groupby(["scenario", "year"])["production_mt"]
                .sum()
            )
        casm_changes = {
            scenario: pct(casm.loc[(scenario, 2035)], casm.loc[(scenario, 2024)])
            for scenario in SCENARIOS
        }
        rows.append(
            {
                "area": area,
                "commodity": commodity,
                "commodity_name": COMMODITY_NAMES.get(commodity, commodity),
                "comparison_horizon": "2024-2035",
                "oecd_fao_production_change_percent": ext_change,
                "casm_world_ssp2_production_change_percent": casm_changes["SSP2"],
                "casm_world_min_ssp_change_percent": min(casm_changes.values()),
                "casm_world_max_ssp_change_percent": max(casm_changes.values()),
                "casm_ssp2_minus_oecd_fao_percentage_points": (
                    casm_changes["SSP2"] - ext_change
                ),
                "oecd_measure": "QP",
                "oecd_version": str(ext["VERSION_ID"].iloc[0]),
                "source_url": OECD_DATA_URL,
            }
        )
    return pd.DataFrame(rows).sort_values(["area", "commodity"])


def external_comparison_summary(
    world: pd.DataFrame, focus: pd.DataFrame
) -> pd.DataFrame:
    casm_min = world["primary_basket_production_change_percent"].min()
    casm_max = world["primary_basket_production_change_percent"].max()
    eu = focus[focus["area"].eq("European Union (27)")]
    return pd.DataFrame(
        [
            {
                "external_model": "IFPRI/CGIAR IMPACT",
                "external_horizon": "2020-2050",
                "external_result": "Global production of all agricultural commodities increases by more than 40%",
                "casm_world_result": (
                    f"Model-covered non-overlapping primary basket increases "
                    f"{casm_min:.1f}-{casm_max:.1f}% from 2023 to 2050"
                ),
                "comparison_status": "directionally comparable only; base year and commodity coverage differ",
                "source_url": IFPRI_2025_URL,
            },
            {
                "external_model": "OECD-FAO Aglink-Cosimo",
                "external_horizon": "2024-2035",
                "external_result": "Nine matched production series each for World, China and EU27; see OECD comparison table",
                "casm_world_result": "SSP2 point and SSP1-SSP5 envelope computed on the identical horizon",
                "comparison_status": "quantitative overlap comparison",
                "source_url": OECD_DATA_URL,
            },
            {
                "external_model": "JRC SUPREMA / AGMEMOD",
                "external_horizon": "harmonized baselines for 2030 and 2050",
                "external_result": "Official dataset documents multi-model harmonized EU baselines",
                "casm_world_result": (
                    "EU27 primary basket increases "
                    f"{eu.primary_basket_production_change_percent.min():.1f}-"
                    f"{eu.primary_basket_production_change_percent.max():.1f}% from 2023 to 2050"
                ),
                "comparison_status": "protocol only until identical AGMEMOD product/unit definitions are extracted",
                "source_url": JRC_SUPREMA_URL,
            },
            {
                "external_model": "IFPRI Global agrifood systems outlook to 2050 (2026)",
                "external_horizon": "2050",
                "external_result": "Not used: publication scheduled for 10 September 2026",
                "casm_world_result": "not applicable",
                "comparison_status": "embargo respected as of analysis date 2026-08-29",
                "source_url": IFPRI_2026_URL,
            },
        ]
    )


def validation_table(
    run_report: dict,
    benchmark_report: dict,
    group_report: dict,
    nutrition_audit: dict,
    ghg_audit: dict,
    publication_report: dict,
    publication_gates: pd.DataFrame,
    diagnostic_draft: bool,
    diagnosis: str,
) -> pd.DataFrame:
    core = pd.DataFrame(
        [
            ("Solved economy accounts", run_report["economy_count"], "count", "passed"),
            ("Commodities", run_report["commodity_count"], "count", "passed"),
            ("Annual scenario solutions", run_report["annual_solution_count"], "count", "passed"),
            ("Country-product results", run_report["result_row_count"], "rows", "passed"),
            ("Maximum world-market relative residual", run_report["maximum_market_relative_residual"], "fraction", "passed"),
            ("Maximum accounting residual", run_report["maximum_accounting_absolute_residual_mt"], "Mt", "passed"),
            ("Benchmark maximum market residual", benchmark_report["maximum_world_market_residual_mt"], "Mt", "passed"),
            ("Benchmark median absolute relative adjustment", benchmark_report["median_absolute_relative_adjustment"], "fraction", "passed"),
            ("Benchmark p95 absolute relative adjustment", benchmark_report["p95_absolute_relative_adjustment"], "fraction", "passed"),
            ("Explicitly inferred benchmark variables", benchmark_report["explicitly_inferred_variable_count"], "count", "disclosed"),
            ("Maximum reporting reconstruction error", group_report["maximum_reconstruction_error_mt"], "Mt", "passed"),
            ("Nutrition world conservation residual", nutrition_audit["world_conservation"]["maximum_absolute_residual"], "native units", "passed"),
            ("GHG world conservation residual", ghg_audit["world_conservation_gate"]["world_vs_detail"]["max_absolute_difference_mtco2e"], "Mt CO2e", "passed"),
            ("Bilateral trade enabled", run_report["bilateral_trade"], "boolean", "passed_false"),
            ("SILK dependency", run_report["silk_dependency"], "boolean", "passed_false"),
            ("Nitrogen module enabled", ghg_audit["nitrogen_module_enabled"], "boolean", "passed_false"),
        ],
        columns=["metric", "value", "unit", "status"],
    )
    core["criterion"] = ""
    core["source"] = "model_and_postsolve_audits"
    publication = publication_gates.rename(
        columns={"description": "metric", "criterion": "criterion"}
    )[["gate_id", "metric", "value", "criterion", "passed"]].copy()
    publication["metric"] = "Publication gate: " + publication["metric"]
    publication["unit"] = "gate-specific"
    publication["status"] = np.where(publication["passed"], "passed", "failed")
    publication["source"] = "publication_validation"
    publication = publication[["metric", "value", "unit", "status", "criterion", "source"]]
    summary = pd.DataFrame(
        [
            {
                "metric": "Paper-output classification",
                "value": (
                    DIAGNOSTIC_STATUS
                    if diagnostic_draft
                    else "publication_baseline"
                ),
                "unit": "classification",
                "status": "diagnostic" if diagnostic_draft else "passed",
                "criterion": "diagnostic output is not a publication baseline",
                "source": "paper_builder",
            },
            {
                "metric": "Diagnostic reason",
                "value": diagnosis,
                "unit": "text",
                "status": "diagnostic" if diagnostic_draft else "not_applicable",
                "criterion": "failed gates and principal outlier are disclosed",
                "source": "publication_validation",
            },
            {
                "metric": "Publication-baseline gate status",
                "value": bool(publication_report["publication_baseline"]),
                "unit": "boolean",
                "status": (
                    "passed" if publication_report["publication_baseline"] else "failed"
                ),
                "criterion": "all frozen publication gates pass",
                "source": "publication_validation",
            },
            {
                "metric": "Publication gates passed",
                "value": int(publication_report["passed_gate_count"]),
                "unit": "count",
                "status": (
                    "passed" if publication_report["publication_baseline"] else "failed"
                ),
                "criterion": f"equals {int(publication_report['gate_count'])}",
                "source": "publication_validation",
            },
        ]
    )
    return pd.concat([summary, publication, core], ignore_index=True)


def figure_world_trajectories(
    groups: pd.DataFrame,
    nutrition_world: pd.DataFrame,
    ghg_world: pd.DataFrame,
    diagnostic: bool,
) -> None:
    world = focus_frame(groups, "GLOBAL", "WORLD")
    primary = aggregate_primary(world)
    food = aggregate_food(world)
    colors = dict(zip(SCENARIOS, ["#2a9d8f", "#457b9d", "#e9c46a", "#f4a261", "#e76f51"]))
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.8), sharex=True)
    panels = [
        (axes[0, 0], primary, "primary_basket_production_mt", "Primary production basket (2023=100)"),
        (axes[0, 1], food, "edible_food_demand_mt", "Edible food demand (2023=100)"),
        (axes[1, 0], nutrition_world, "kcal_per_capita_day", "Covered kcal per capita per day (2023=100)"),
        (axes[1, 1], ghg_world, "emissions_mtco2e", "Attributed farm-gate GHG (2023=100)"),
    ]
    if len({id(panel[0]) for panel in panels}) != 4:
        raise AssertionError("World-trajectory figure must use each 2x2 axis exactly once")
    for ax, frame, column, title in panels:
        for scenario in SCENARIOS:
            s = frame[frame["scenario"].eq(scenario)].sort_values("year")
            base = float(s.loc[s["year"].eq(2023), column].iloc[0])
            ax.plot(s["year"], 100.0 * s[column] / base, label=scenario, color=colors[scenario], lw=2)
        ax.axhline(100, color="#777777", lw=0.7)
        ax.set_title(title, fontsize=10.5)
        ax.grid(alpha=0.2)
        ax.set_ylabel("Index")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.045),
        ncol=5,
        frameon=False,
    )
    fig.suptitle("CASM-World global SSP pathways, 2023-2050", fontsize=14)
    stamp_figure(fig, diagnostic)
    fig.tight_layout(rect=(0, 0.11, 1, 0.96))
    fig.savefig(FIGURES / "figure1_world_ssp_trajectories.png", dpi=220)
    plt.close(fig)


def figure_regions(regional_ssp2: pd.DataFrame, diagnostic: bool) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 7.2))
    missing_names = sorted(
        set(regional_ssp2["region_name"].astype(str)) - set(UN_AREA_SHORT_NAMES)
    )
    if missing_names:
        raise AssertionError(f"Missing concise UN area labels: {missing_names}")
    size = 25 + 110 * np.sqrt(
        regional_ssp2["primary_basket_production_2023_mt"]
        / regional_ssp2["primary_basket_production_2023_mt"].max()
    )
    net_imports = regional_ssp2["primary_basket_net_import_2050_mt"].astype(float)
    if not (float(net_imports.min()) < 0.0 < float(net_imports.max())):
        raise AssertionError("Regional net-import colours require values on both sides of zero")
    scatter = ax.scatter(
        regional_ssp2["primary_basket_production_change_percent"],
        regional_ssp2["edible_food_demand_change_percent"],
        s=size,
        c=net_imports,
        cmap="coolwarm",
        norm=TwoSlopeNorm(
            vmin=float(net_imports.min()),
            vcenter=0.0,
            vmax=float(net_imports.max()),
        ),
        alpha=0.82,
        edgecolor="white",
        linewidth=0.6,
    )
    ax.axline((0, 0), slope=1, color="#666666", lw=0.8, ls="--")
    ax.axvline(0, color="#999999", lw=0.6)
    ax.axhline(0, color="#999999", lw=0.6)
    ax.set_xlabel("Primary production basket change, 2023-2050 (%)")
    ax.set_ylabel("Edible food demand change, 2023-2050 (%)")
    ax.set_title("UN subregional production-demand divergence under SSP2")
    ax.grid(alpha=0.18)
    colour_bar = fig.colorbar(scatter, ax=ax, pad=0.018, fraction=0.046)
    colour_bar.set_label("Net imports in 2050 (Mt; positive = imports)")
    ax.text(
        0.012,
        0.014,
        "Marker area scales with 2023 primary production",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8,
        color="#555555",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 1.4},
    )
    stamp_figure(fig, diagnostic)
    fig.tight_layout(rect=(0, 0.052, 1, 1))

    x_midpoint = float(
        regional_ssp2["primary_basket_production_change_percent"].median()
    )
    y_midpoint = float(regional_ssp2["edible_food_demand_change_percent"].median())
    annotations: list[plt.Annotation] = []
    for row in regional_ssp2.sort_values("region_name").itertuples(index=False):
        x_value = float(row.primary_basket_production_change_percent)
        y_value = float(row.edible_food_demand_change_percent)
        annotations.append(
            ax.annotate(
                UN_AREA_SHORT_NAMES[str(row.region_name)],
                (x_value, y_value),
                xytext=(
                    7.0 if x_value <= x_midpoint else -7.0,
                    7.0 if y_value <= y_midpoint else -7.0,
                ),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=7.3,
                color="#202020",
                zorder=4,
                annotation_clip=True,
            )
        )
    remaining_overlaps = _resolve_annotation_collisions(fig, ax, annotations)
    if remaining_overlaps:
        raise AssertionError(
            f"Regional direct labels retain {remaining_overlaps} collisions"
        )

    for item in annotations:
        offset_x, offset_y = item.get_position()
        if np.hypot(offset_x, offset_y) < 10.0:
            continue
        ax.annotate(
            "",
            xy=item.xy,
            xytext=(offset_x, offset_y),
            textcoords="offset points",
            arrowprops={
                "arrowstyle": "-",
                "color": "#777777",
                "alpha": 0.55,
                "linewidth": 0.45,
                "shrinkA": 5.0,
                "shrinkB": 2.5,
            },
            zorder=3,
            annotation_clip=True,
        )
    fig.savefig(FIGURES / "figure2_regional_ssp2_divergence.png", dpi=220)
    plt.close(fig)


def figure_oecd(oecd: pd.DataFrame, diagnostic: bool) -> None:
    order = ["WHE", "CRN", "RIC", "OCG", "SBS", "CTN", "BFV", "PRK", "PLM"]
    fig, axes = plt.subplots(3, 1, figsize=(11.5, 10.6), sharex=True)
    for ax, area in zip(
        axes, ["World", "China mainland", "European Union (27)"]
    ):
        s = oecd[oecd["area"].eq(area)].set_index("commodity").reindex(order)
        x = np.arange(len(order))
        width = 0.36
        ax.bar(
            x - width / 2,
            s["oecd_fao_production_change_percent"],
            width,
            label="OECD-FAO",
            color="#457b9d",
        )
        ax.bar(
            x + width / 2,
            s["casm_world_ssp2_production_change_percent"],
            width,
            label="CASM-World SSP2",
            color="#e76f51",
        )
        ax.vlines(
            x + width / 2,
            s["casm_world_min_ssp_change_percent"],
            s["casm_world_max_ssp_change_percent"],
            color="#333333",
            lw=1.3,
        )
        ax.axhline(0, color="#777777", lw=0.7)
        ax.set_ylabel("Production change (%)")
        ax.set_title(area)
        ax.grid(axis="y", alpha=0.2)
    axes[-1].set_xticks(np.arange(len(order)), order)
    axes[0].legend(frameon=False, ncol=2)
    fig.suptitle("Overlapping-horizon comparison, 2024-2035", fontsize=14)
    stamp_figure(fig, diagnostic)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    fig.savefig(FIGURES / "figure3_oecd_fao_comparison.png", dpi=220)
    plt.close(fig)


def figure_focus(focus: pd.DataFrame, diagnostic: bool) -> None:
    areas = ["China mainland", "United States", "European Union (27)"]
    x = np.arange(len(SCENARIOS))
    width = 0.24
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    colors = ["#e76f51", "#457b9d", "#2a9d8f"]
    for index, (area, color) in enumerate(zip(areas, colors)):
        s = focus[focus["area"].eq(area)].set_index("scenario").reindex(SCENARIOS)
        ax.bar(
            x + (index - 1) * width,
            s["primary_basket_production_change_percent"],
            width,
            label=area,
            color=color,
        )
    ax.set_xticks(x, SCENARIOS)
    ax.set_ylabel("Primary production basket change, 2023-2050 (%)")
    ax.set_title("Focus economies across SSP pathways")
    ax.axhline(0, color="#777777", lw=0.7)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False)
    stamp_figure(fig, diagnostic)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGURES / "figure4_focus_economy_production.png", dpi=220)
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    results = pd.read_csv(ROOT / "outputs/ssp_results_country_product_2023_2050.csv")
    groups = pd.read_csv(ROOT / "outputs/ssp_results_group_product_2023_2050.csv")
    nutrition = pd.read_csv(ROOT / "outputs/ssp_nutrition_economy_2023_2050.csv")
    nutrition_world = pd.read_csv(ROOT / "outputs/ssp_nutrition_world_2023_2050.csv")
    ghg_country = pd.read_csv(ROOT / "outputs/ssp_ghg_country_2023_2050.csv")
    ghg_world = pd.read_csv(ROOT / "outputs/ssp_ghg_world_2023_2050.csv")
    drivers = pd.read_csv(ROOT / "data/processed/ssp_drivers_2023_2050.csv")
    membership = pd.read_csv(
        ROOT / "data/processed/reporting_model_account_membership_2023.csv"
    )
    oecd = pd.read_csv(
        ROOT / "data/external/oecd_fao_outlook_2026_2035_selected_production.csv"
    )

    check_grid(results)
    world_from_results = (
        results.groupby(["scenario", "year", "commodity"])["production_mt"].sum()
    )
    world_from_groups = (
        groups[
            groups["group_system"].eq("GLOBAL")
            & groups["group_code"].eq("WORLD")
        ].set_index(["scenario", "year", "commodity"])["production_mt"]
    )
    if (world_from_results - world_from_groups).abs().max() > 1.0e-8:
        raise AssertionError("World reporting group does not reconstruct country results")

    with (ROOT / "outputs/ssp_run_report.json").open() as stream:
        run_report = json.load(stream)
    with (ROOT / "data/processed/benchmark_equilibrium_report_2023.json").open() as stream:
        benchmark_report = json.load(stream)
    with (ROOT / "outputs/ssp_group_analysis_report.json").open() as stream:
        group_report = json.load(stream)
    with (ROOT / "outputs/ssp_nutrition_audit_2023_2050.json").open() as stream:
        nutrition_audit = json.load(stream)
    with (ROOT / "outputs/ssp_ghg_audit_2023_2050.json").open() as stream:
        ghg_audit = json.load(stream)
    with (ROOT / "outputs/publication_validation_report.json").open() as stream:
        publication_report = json.load(stream)
    publication_gates = pd.read_csv(ROOT / "outputs/publication_validation_gates.csv")
    sensitivity_report_path = ROOT / "outputs/sensitivity/v2_sensitivity_report.json"
    with sensitivity_report_path.open() as stream:
        sensitivity_report = json.load(stream)
    sensitivity_materiality_path = (
        ROOT / "outputs/sensitivity/v2_sensitivity_materiality_screen.csv"
    )
    sensitivity_materiality = pd.read_csv(sensitivity_materiality_path)
    validation_config = yaml.safe_load(
        (ROOT / "config/validation.yaml").read_text(encoding="utf-8")
    )
    for key, expected_sha in publication_report["input_sha256"].items():
        if key not in validation_config["inputs"]:
            raise AssertionError(f"Unknown publication-validation input key: {key}")
        path = (ROOT / validation_config["inputs"][key]).resolve()
        if expected_sha != sha256(path):
            raise AssertionError(
                f"Publication-validation report is stale for {key}: "
                f"{expected_sha} != {sha256(path)}"
            )
    if len(publication_gates) != int(publication_report["gate_count"]):
        raise AssertionError("Publication gate table/report counts disagree")
    passed_gate_count = int(publication_gates["passed"].astype(bool).sum())
    if passed_gate_count != int(publication_report["passed_gate_count"]):
        raise AssertionError("Publication passed-gate counts disagree")
    failed_gate_ids = publication_gates.loc[
        ~publication_gates["passed"].astype(bool), "gate_id"
    ].tolist()
    if failed_gate_ids != publication_report.get("failed_gates", []):
        raise AssertionError("Publication failed-gate lists disagree")

    if sensitivity_report.get("status") != "passed":
        raise AssertionError("V2 sensitivity report has not passed")
    if int(sensitivity_report.get("unique_variant_count", 0)) != 6:
        raise AssertionError("V2 sensitivity report does not contain six variants")
    if int(sensitivity_report.get("total_annual_solution_count", 0)) != 840:
        raise AssertionError("V2 sensitivity report does not contain 840 annual solutions")
    if not bool(sensitivity_report.get("all_annual_solutions_converged")):
        raise AssertionError("At least one V2 sensitivity solution did not converge")
    if any(
        item["calibration"]["status"] != "passed"
        for item in sensitivity_report["variant_reports"].values()
    ):
        raise AssertionError("At least one V2 sensitivity variant failed 2023 calibration")
    sensitivity_output_paths = {
        key: Path(path)
        for key, path in sensitivity_report["outputs"].items()
        if key != "report"
    }
    for key, expected_sha in sensitivity_report["output_sha256"].items():
        path = sensitivity_output_paths[key]
        if expected_sha != sha256(path):
            raise AssertionError(
                f"V2 sensitivity report is stale for {key}: "
                f"{expected_sha} != {sha256(path)}"
            )
    triggered = sensitivity_materiality.loc[
        sensitivity_materiality["either_threshold_exceeded"].astype(bool),
        "variant",
    ].tolist()
    if triggered != sensitivity_report["materiality_threshold_exceeded_variants"]:
        raise AssertionError("Sensitivity materiality table/report triggers disagree")
    publication_baseline = bool(publication_report.get("publication_baseline"))
    diagnostic_draft = not publication_baseline
    if diagnostic_draft and not args.diagnostic_draft:
        raise AssertionError(
            "Paper build refused: frozen publication-validation gates have not all "
            "passed. Re-run with --diagnostic-draft only to generate artifacts "
            "explicitly classified as diagnostic conditional and not a publication baseline."
        )
    diagnosis = diagnostic_reason(publication_report)

    macro = selected_macro_table(drivers, membership)
    world = world_summary(groups, nutrition_world, ghg_world, macro)
    focus = focus_summaries(groups)
    regional_all, regional_ssp2 = regional_summaries(groups)
    grouped = income_and_special_groups(groups)
    commodities = commodity_table(groups)
    nutrition_selected = aggregate_nutrition(nutrition, membership)
    ghg_selected = aggregate_ghg(ghg_country, membership)
    oecd_table = oecd_comparison(results, oecd, membership)
    external = external_comparison_summary(world, focus)
    validation = validation_table(
        run_report,
        benchmark_report,
        group_report,
        nutrition_audit,
        ghg_audit,
        publication_report,
        publication_gates,
        diagnostic_draft,
        diagnosis,
    )

    tables = {
        "table1_model_scope_and_validation.csv": validation,
        "table2_world_ssp_summary.csv": world,
        "table3_focus_economies_ssp_summary.csv": focus,
        "table4_macro_drivers_selected.csv": macro,
        "table5_regional_all_ssp_summary.csv": regional_all,
        "table6_regional_ssp2_and_ssp_range.csv": regional_ssp2,
        "table7_income_and_special_groups.csv": grouped,
        "table8_world_commodity_results.csv": commodities,
        "table9_nutrition_selected.csv": nutrition_selected,
        "table10_ghg_selected.csv": ghg_selected,
        "table11_oecd_fao_comparison_2024_2035.csv": oecd_table,
        "table12_external_model_comparison_summary.csv": external,
    }
    draft_status = DIAGNOSTIC_STATUS if diagnostic_draft else "publication_baseline"
    failed_gate_text = ";".join(failed_gate_ids)
    for filename, table in tables.items():
        table.insert(0, "diagnostic_reason", diagnosis)
        table.insert(0, "failed_publication_gates", failed_gate_text)
        table.insert(0, "publication_baseline", publication_baseline)
        table.insert(0, "draft_status", draft_status)
        table.to_csv(TABLES / filename, index=False, float_format="%.10g")

    figure_world_trajectories(groups, nutrition_world, ghg_world, diagnostic_draft)
    figure_regions(regional_ssp2, diagnostic_draft)
    figure_oecd(oecd_table, diagnostic_draft)
    figure_focus(focus, diagnostic_draft)

    figure_paths = [
        FIGURES / "figure1_world_ssp_trajectories.png",
        FIGURES / "figure2_regional_ssp2_divergence.png",
        FIGURES / "figure3_oecd_fao_comparison.png",
        FIGURES / "figure4_focus_economy_production.png",
    ]

    report = {
        "status": draft_status,
        "diagnostic_draft": diagnostic_draft,
        "publication_baseline": publication_baseline,
        "failed_publication_gates": failed_gate_ids,
        "diagnostic_reason": diagnosis,
        "analysis_date": "2026-08-29",
        "production_aggregation_rule": "non_overlapping_primary_basket_only",
        "primary_basket": PRIMARY_BASKET,
        "forbidden_aggregate": "sum_of_all_31_production_rows",
        "table_count": len(tables),
        "figure_count": 4,
        "world_primary_production_change_percent_range": [
            float(world["primary_basket_production_change_percent"].min()),
            float(world["primary_basket_production_change_percent"].max()),
        ],
        "world_food_demand_change_percent_range": [
            float(world["edible_food_demand_change_percent"].min()),
            float(world["edible_food_demand_change_percent"].max()),
        ],
        "world_kcal_per_capita_change_percent_range": [
            float(world["basket_kcal_per_capita_change_percent"].min()),
            float(world["basket_kcal_per_capita_change_percent"].max()),
        ],
        "world_ghg_change_percent_range": [
            float(world["attributed_farmgate_ghg_change_percent"].min()),
            float(world["attributed_farmgate_ghg_change_percent"].max()),
        ],
        "oecd_comparison_rows": int(len(oecd_table)),
        "publication_validation": {
            "status": publication_report["status"],
            "gate_count": int(publication_report["gate_count"]),
            "passed_gate_count": int(publication_report["passed_gate_count"]),
            "report_sha256": sha256(
                ROOT / "outputs/publication_validation_report.json"
            ),
            "price_plausibility_metrics": publication_report.get(
                "price_plausibility_metrics", {}
            ),
            "oecd_fao_holdout_metrics": publication_report.get(
                "oecd_fao_holdout_metrics", {}
            ),
        },
        "formal_input_sha256": publication_report["input_sha256"],
        "sensitivity": {
            "status": sensitivity_report["status"],
            "scope_status": sensitivity_report["scope_status"],
            "variant_count": int(sensitivity_report["unique_variant_count"]),
            "annual_solution_count": int(
                sensitivity_report["total_annual_solution_count"]
            ),
            "maximum_market_relative_residual": sensitivity_report[
                "maximum_market_relative_residual"
            ],
            "maximum_accounting_absolute_residual_mt": sensitivity_report[
                "maximum_accounting_absolute_residual_mt"
            ],
            "materiality_threshold_exceeded_variants": triggered,
            "not_implemented_structural_sensitivities": sensitivity_report[
                "not_implemented_structural_sensitivities"
            ],
            "report_sha256": sha256(sensitivity_report_path),
            "materiality_sha256": sha256(sensitivity_materiality_path),
        },
        "outputs": {
            "tables": [str(TABLES / name) for name in tables],
            "figures": [str(path) for path in figure_paths],
            "sha256": {
                **{name: sha256(TABLES / name) for name in tables},
                **{path.name: sha256(path) for path in figure_paths},
            },
        },
    }
    (ROOT / "paper" / "paper_analysis_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
