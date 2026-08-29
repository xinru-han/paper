"""Create publication figures for the China diet CASM-World counterfactuals."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path(__file__).with_name("config.yaml")
COLORS = {
    "BASELINE": "#4D4D4D",
    "PTS": "#D55E00",
    "MTS": "#0072B2",
    "CGS": "#009E73",
    "range": "#B8B8B8",
    "china": "#E69F00",
    "outside": "#56B4E9",
}
PRODUCT_LABELS = {
    "RIC": "Rice",
    "WHE": "Wheat",
    "CRN": "Maize",
    "SBS": "Soybeans",
    "SBO": "Vegetable oils",
    "BFV": "Bovine meat",
    "PRK": "Pigmeat",
    "PLM": "Poultry meat",
    "MLK": "Raw milk",
    "FMK": "Fluid milk",
    "WDM": "Whole milk powder",
}


def _project_path(value: str) -> Path:
    path = (PROJECT_ROOT / value).resolve()
    path.relative_to(PROJECT_ROOT)
    return path


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.dpi": 300,
            "figure.dpi": 130,
        }
    )


def _save(fig: plt.Figure, directory: Path, stem: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    fig.savefig(directory / f"{stem}.png", bbox_inches="tight", facecolor="white")
    fig.savefig(directory / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def figure1(config: dict, directory: Path) -> None:
    paths = pd.read_csv(_project_path(config["inputs"]["mapped_diet_paths"]))
    selected = ["RIC", "PRK", "BFV", "PLM", "SBO", "FMK"]
    fig, axes = plt.subplots(2, 3, figsize=(10.2, 5.8), sharex=True)
    for index, (axis, product) in enumerate(zip(axes.flat, selected)):
        subset = paths[paths["world_commodity"].eq(product)]
        for pathway in ("PTS", "MTS", "CGS"):
            line = subset[subset["diet_pathway"].eq(pathway)]
            axis.plot(
                line["year"],
                line["preference_multiplier_vs_baseline"],
                color=COLORS[pathway],
                linewidth=1.8,
                label=pathway,
            )
        axis.axhline(1.0, color="#777777", linewidth=0.8, linestyle="--")
        axis.set_title(PRODUCT_LABELS[product], loc="left", fontweight="bold")
        axis.grid(axis="y", color="#E6E6E6", linewidth=0.6)
        axis.set_xlim(2023, 2050)
        axis.set_xticks([2023, 2035, 2050])
        if index % 3 == 0:
            axis.set_ylabel("Preference multiplier vs baseline")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.945),
        ncol=3,
        frameon=False,
    )
    fig.suptitle(
        "China food-demand shifts applied to the world equilibrium",
        y=0.995,
        fontsize=12,
        fontweight="bold",
    )
    fig.text(
        0.01,
        0.01,
        "Multipliers are annual pathway-to-BS ratios from the China CASM solution; only the food component is shifted.",
        fontsize=7.5,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.88))
    _save(fig, directory, "figure1_china_diet_shifters")


def _price_contrasts(config: dict) -> pd.DataFrame:
    prices = pd.read_csv(_project_path(config["outputs"]["world_prices"]))
    prices = prices[prices["year"].eq(2050)].copy()
    base = prices[prices["diet_pathway"].eq("BASELINE")][
        ["base_ssp", "commodity", "world_price_index_2023"]
    ].rename(columns={"world_price_index_2023": "baseline"})
    result = prices[~prices["diet_pathway"].eq("BASELINE")].merge(
        base, on=["base_ssp", "commodity"], validate="many_to_one"
    )
    result["change_percent"] = 100.0 * (
        result["world_price_index_2023"] / result["baseline"] - 1.0
    )
    return result


def figure2(config: dict, directory: Path) -> None:
    products = ["PRK", "RIC", "SBO", "BFV", "WHE", "PLM", "FMK", "WDM"]
    contrasts = _price_contrasts(config)
    central = contrasts[
        contrasts["base_ssp"].eq(config["central_ssp"])
        & contrasts["commodity"].isin(products)
    ]
    sensitivity = pd.read_csv(
        _project_path(config["outputs"]["tables_directory"])
        / "table7_price_sensitivity_ssp2_2050.csv"
    )
    sensitivity = sensitivity[
        sensitivity["diet_pathway"].eq("CGS")
        & sensitivity["commodity"].isin(products)
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8), sharey=True)
    y = np.arange(len(products))
    offsets = {"PTS": -0.20, "MTS": 0.0, "CGS": 0.20}
    for pathway in ("PTS", "MTS", "CGS"):
        values = (
            central[central["diet_pathway"].eq(pathway)]
            .set_index("commodity")
            .reindex(products)["change_percent"]
        )
        axes[0].scatter(
            values,
            y + offsets[pathway],
            s=34,
            color=COLORS[pathway],
            label=pathway,
            zorder=3,
        )
    axes[0].axvline(0, color="#555555", linewidth=0.8)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([PRODUCT_LABELS[value] for value in products])
    axes[0].invert_yaxis()
    axes[0].set_xlabel("World-price change vs same-SSP baseline (%)")
    axes[0].set_title("a  Central SSP2 counterfactual", loc="left", fontweight="bold")
    axes[0].legend(frameon=False, loc="lower right")
    axes[0].grid(axis="x", color="#E6E6E6", linewidth=0.6)

    for position, product in enumerate(products):
        values = sensitivity[sensitivity["commodity"].eq(product)][
            "world_price_index_2050_change_percent"
        ]
        central_value = sensitivity[
            sensitivity["commodity"].eq(product)
            & sensitivity["response_variant"].eq("V2_CENTRAL")
        ]["world_price_index_2050_change_percent"].iloc[0]
        ces_value = sensitivity[
            sensitivity["commodity"].eq(product)
            & sensitivity["response_variant"].eq("DEMAND_SUBSTITUTION_CES")
        ]["world_price_index_2050_change_percent"].iloc[0]
        axes[1].plot([values.min(), values.max()], [position, position], color=COLORS["range"], linewidth=4)
        axes[1].scatter(central_value, position, color=COLORS["CGS"], s=34, zorder=3, label="Central" if position == 0 else None)
        axes[1].scatter(ces_value, position, color="#CC79A7", marker="D", s=28, zorder=3, label="CES" if position == 0 else None)
    axes[1].axvline(0, color="#555555", linewidth=0.8)
    axes[1].set_xlabel("CGS world-price effect (%)")
    axes[1].set_title("b  Parameter and demand-form sensitivity", loc="left", fontweight="bold")
    axes[1].grid(axis="x", color="#E6E6E6", linewidth=0.6)
    axes[1].legend(frameon=False, loc="lower right")
    fig.suptitle("China's diet transition reprices globally traded products", y=1.01, fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, directory, "figure2_world_price_transmission")


def figure3(config: dict, directory: Path) -> None:
    country = pd.read_csv(_project_path(config["outputs"]["country_contrasts_2050"]))
    group = pd.read_csv(
        _project_path(config["outputs"]["tables_directory"])
        / "table8_primary_basket_group_impacts_2050.csv"
    )
    central_country = country[
        country["base_ssp"].eq(config["central_ssp"])
        & country["diet_pathway"].eq("CGS")
    ].copy()
    china = central_country[
        central_country["economy_id"].eq("CHN")
        & central_country["commodity"].isin(["RIC", "WHE", "PRK", "BFV", "PLM", "FMK", "WDM"])
    ].set_index("commodity")
    china_products = ["RIC", "WHE", "PRK", "BFV", "PLM", "FMK", "WDM"]

    economies = central_country[
        ~central_country["economy_id"].eq("CHN")
        & central_country["production_mt_baseline"].gt(0.1)
    ].copy()
    economies["absolute_change"] = economies["production_mt_change"].abs()
    top = economies.nlargest(12, "absolute_change").sort_values("production_mt_change")
    top["label"] = top["economy_id"] + "  " + top["commodity"].map(PRODUCT_LABELS).fillna(top["commodity"])

    regions = group[
        group["base_ssp"].eq(config["central_ssp"])
        & group["diet_pathway"].eq("CGS")
        & group["group_system"].eq("UN_REGION")
        & ~group["group_code"].eq("000")
    ].sort_values("primary_production_mt_change")

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.8), gridspec_kw={"width_ratios": [1.0, 1.25, 1.0]})
    colors = np.where(china.loc[china_products, "net_import_mt_change"] >= 0, COLORS["outside"], COLORS["china"])
    axes[0].barh(
        np.arange(len(china_products)),
        china.loc[china_products, "net_import_mt_change"],
        color=colors,
    )
    axes[0].set_yticks(np.arange(len(china_products)))
    axes[0].set_yticklabels([PRODUCT_LABELS[p] for p in china_products])
    axes[0].invert_yaxis()
    axes[0].axvline(0, color="#555555", linewidth=0.8)
    axes[0].set_xlabel("China net-import change (Mt)")
    axes[0].set_title("a  China's trade balance", loc="left", fontweight="bold")

    axes[1].barh(
        np.arange(len(top)),
        top["production_mt_change"],
        color=np.where(top["production_mt_change"] >= 0, COLORS["outside"], COLORS["china"]),
    )
    axes[1].set_yticks(np.arange(len(top)))
    axes[1].set_yticklabels(top["label"])
    axes[1].axvline(0, color="#555555", linewidth=0.8)
    axes[1].set_xlabel("Production change (Mt)")
    axes[1].set_title("b  Largest economy-product responses", loc="left", fontweight="bold")

    axes[2].barh(
        np.arange(len(regions)),
        regions["primary_production_mt_change"],
        color="#7A7A7A",
    )
    axes[2].set_yticks(np.arange(len(regions)))
    axes[2].set_yticklabels(regions["group_name"])
    axes[2].axvline(0, color="#555555", linewidth=0.8)
    axes[2].set_xlabel("Primary-basket production change (Mt)")
    axes[2].set_title("c  UN-region response", loc="left", fontweight="bold")
    for axis in axes:
        axis.grid(axis="x", color="#E6E6E6", linewidth=0.6)
    fig.suptitle("The CGS counterfactual redistributes demand and production", y=1.01, fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, directory, "figure3_trade_and_production_redistribution")


def figure4(config: dict, directory: Path) -> None:
    ghg = pd.read_csv(_project_path(config["outputs"]["ghg_group"]))
    world = ghg[
        ghg["base_ssp"].eq(config["central_ssp"])
        & ghg["group_system"].eq("GLOBAL")
        & ghg["group_code"].eq("WORLD")
    ].copy()
    baseline = world[world["diet_pathway"].eq("BASELINE")][
        ["year", "emissions_mtco2e"]
    ].rename(columns={"emissions_mtco2e": "baseline"})
    world = world.merge(baseline, on="year", validate="many_to_one")
    world["change"] = world["emissions_mtco2e"] - world["baseline"]

    regions = ghg[
        ghg["base_ssp"].eq(config["central_ssp"])
        & ghg["diet_pathway"].eq("CGS")
        & ghg["year"].eq(2050)
        & ghg["group_system"].eq("UN_REGION")
        & ~ghg["group_code"].eq("000")
    ].copy()
    region_base = ghg[
        ghg["base_ssp"].eq(config["central_ssp"])
        & ghg["diet_pathway"].eq("BASELINE")
        & ghg["year"].eq(2050)
        & ghg["group_system"].eq("UN_REGION")
        & ~ghg["group_code"].eq("000")
    ][["group_code", "emissions_mtco2e"]].rename(columns={"emissions_mtco2e": "baseline"})
    regions = regions.merge(region_base, on="group_code", validate="one_to_one")
    regions["change"] = regions["emissions_mtco2e"] - regions["baseline"]
    regions = regions.sort_values("change")

    focus = ghg[
        ghg["base_ssp"].eq(config["central_ssp"])
        & ghg["year"].eq(2050)
        & ghg["group_system"].isin(["GLOBAL", "FOCUS"])
    ]
    values = []
    for pathway in ("PTS", "MTS", "CGS"):
        world_value = focus[
            focus["diet_pathway"].eq(pathway)
            & focus["group_system"].eq("GLOBAL")
            & focus["group_code"].eq("WORLD")
        ]["emissions_mtco2e"].iloc[0]
        world_base = focus[
            focus["diet_pathway"].eq("BASELINE")
            & focus["group_system"].eq("GLOBAL")
            & focus["group_code"].eq("WORLD")
        ]["emissions_mtco2e"].iloc[0]
        china_value = focus[
            focus["diet_pathway"].eq(pathway)
            & focus["group_system"].eq("FOCUS")
            & focus["group_code"].eq("CHINA_MAINLAND")
        ]["emissions_mtco2e"].iloc[0]
        china_base = focus[
            focus["diet_pathway"].eq("BASELINE")
            & focus["group_system"].eq("FOCUS")
            & focus["group_code"].eq("CHINA_MAINLAND")
        ]["emissions_mtco2e"].iloc[0]
        values.append((pathway, china_value - china_base, (world_value - world_base) - (china_value - china_base)))

    fig, axes = plt.subplots(1, 3, figsize=(11.8, 4.5), gridspec_kw={"width_ratios": [1.35, 1.0, 1.0]})
    for pathway in ("PTS", "MTS", "CGS"):
        line = world[world["diet_pathway"].eq(pathway)]
        axes[0].plot(line["year"], line["change"], color=COLORS[pathway], linewidth=2.0, label=pathway)
    axes[0].axhline(0, color="#555555", linewidth=0.8)
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("World farm-gate GHG change (Mt CO$_2$e)")
    axes[0].set_title("a  SSP2 annual pathway", loc="left", fontweight="bold")
    axes[0].legend(frameon=False)

    axes[1].barh(np.arange(len(regions)), regions["change"], color="#7A7A7A")
    axes[1].set_yticks(np.arange(len(regions)))
    axes[1].set_yticklabels(regions["group_name"])
    axes[1].axvline(0, color="#555555", linewidth=0.8)
    axes[1].set_xlabel("GHG change (Mt CO$_2$e)")
    axes[1].set_title("b  CGS by UN region", loc="left", fontweight="bold")

    labels = [value[0] for value in values]
    china_values = np.array([value[1] for value in values])
    outside_values = np.array([value[2] for value in values])
    x = np.arange(len(labels))
    axes[2].bar(x, china_values, color=COLORS["china"], label="China")
    axes[2].bar(x, outside_values, bottom=china_values, color=COLORS["outside"], label="Outside China")
    axes[2].axhline(0, color="#555555", linewidth=0.8)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(labels)
    axes[2].set_ylabel("GHG change (Mt CO$_2$e)")
    axes[2].set_title("c  Domestic and external effects", loc="left", fontweight="bold")
    axes[2].legend(frameon=False, loc="lower left")
    for axis in axes:
        axis.grid(axis="y" if axis is axes[2] else "x", color="#E6E6E6", linewidth=0.6)
    fig.suptitle("Most model-covered emission change occurs outside China", y=1.01, fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, directory, "figure4_farm_gate_ghg_redistribution")


def write_captions(directory: Path) -> None:
    text = """# Figure captions

**Figure 1 | China food-demand shifts applied to the world equilibrium.** Annual pathway-to-baseline food-preference multipliers derived from the prior China CASM solutions. The intervention changes only mainland China's food component; feed and other final uses retain their SSP paths. Vegetables, fruit, eggs, aquatic foods, tubers and sheep/goat meat are outside the 31-product world equilibrium.

**Figure 2 | China's diet transition reprices globally traded products.** **a**, SSP2 world-price effects in 2050 relative to the same-SSP baseline. **b**, CGS effects under low, central and high response parameters and the five-nest inner-Cobb-Douglas (CES) demand sensitivity. Grey bars span all four variants; circles show central and diamonds show CES. Poultry illustrates a model-form-sensitive sign, whereas the dairy increase is directionally stable.

**Figure 3 | The CGS counterfactual redistributes demand and production.** **a**, China's net-import changes. Positive values denote increased net imports. **b**, the 12 largest absolute production responses outside China among economy-product observations with baseline production above 0.1 Mt. **c**, changes in the non-overlapping primary-production basket by UN region. Trade is a net-balance identity; bilateral partners are not modelled.

**Figure 4 | Most model-covered emission change occurs outside China.** **a**, annual SSP2 change in attributed biological farm-gate GHG emissions relative to the same-year baseline. **b**, CGS change by UN region in 2050. **c**, decomposition between mainland China and all other economies. Coefficients are frozen at 2023 levels and exclude land-use change, processing, transport and other life-cycle stages.
"""
    (directory / "figure_captions.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    directory = _project_path(config["outputs"]["figures_directory"])
    _style()
    figure1(config, directory)
    figure2(config, directory)
    figure3(config, directory)
    figure4(config, directory)
    write_captions(directory)
    print(f"wrote figures and captions under {directory}")


if __name__ == "__main__":
    main()
