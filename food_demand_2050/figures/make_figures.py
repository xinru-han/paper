#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure factory for the China food demand 2050 paper (target: Nature Food).

Main figures (png 300 dpi + pdf):
  fig1_scenarios          - per-capita food change 2023->2050, three diet pathways
  fig2_china_multidim     - China nutrition structure + environmental footprints
  fig3_global_transmission- world prices / producer responses / China net imports
  fig4_global_net_effect  - within- vs outside-China net effects + MTS dividend curve
Extended-data figures:
  ed1_scenario_matrix, ed2_carbon_sensitivity, ed3_ssr_change, ed4_validation

Run:  python3 figures/make_figures.py   (after modules/post_analysis.py)
"""
import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")
SCN = os.path.join(ROOT, "scenarios")
PA = os.path.join(RES, "post_analysis")
os.makedirs(FIG, exist_ok=True)

# ------------------------------------------------------------ style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 7.5, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.grid": False, "savefig.dpi": 300, "pdf.fonttype": 42,
})
# Okabe-Ito colourblind-safe palette
OI = {"black": "#000000", "orange": "#E69F00", "sky": "#56B4E9",
      "green": "#009E73", "yellow": "#F0E442", "blue": "#0072B2",
      "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#999999"}
CS = {"BS": OI["grey"], "PTS": OI["vermillion"], "MTS": OI["blue"],
      "HDS": OI["green"]}
LONG = {"BS": "BS (baseline, fixed elasticities)",
        "PTS": "PTS (past-trend scenario, A1)",
        "MTS": "MTS (moderate-transition scenario, C1)",
        "HDS": "HDS (healthy-diet scenario, B1)"}
CORE = {"BS": "BS", "A1": "PTS", "C1": "MTS", "B1": "HDS"}


def save(fig, name):
    for ext in ("png", "pdf"):
        p = os.path.join(FIG, f"{name}.{ext}")
        fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    sz = os.path.getsize(os.path.join(FIG, name + ".png"))
    assert sz > 10240, f"{name}.png only {sz} bytes"
    print(f"  {name}: png {sz/1024:.0f} KB")


def panel_label(ax, s, dx=-0.08, dy=1.05):
    ax.text(dx, dy, s, transform=ax.transAxes, fontsize=10,
            fontweight="bold", va="bottom", ha="right")


# ------------------------------------------------------------ data
DF = pd.read_csv(os.path.join(RES, "results_long.csv"))
DF.columns = [c.strip("﻿") for c in DF.columns]
WL = pd.read_csv(os.path.join(RES, "world", "world_results_long.csv"))
CFP = pd.read_csv(os.path.join(RES, "footprints", "china_footprints_summary.csv"))
WFP = pd.read_csv(os.path.join(RES, "footprints", "world_footprints_summary.csv"))
NC = pd.read_csv(os.path.join(SCN, "nutrient_coefficients.csv"))
NC.columns = [c.strip("﻿") for c in NC.columns]
HB = pd.read_csv(os.path.join(SCN, "healthy_diet_benchmark.csv"))
HB.columns = [c.strip("﻿") for c in HB.columns]
MTS_EFF = pd.read_csv(os.path.join(PA, "mts_efficiency.csv"))


def val(variable, scenario, year, commodity="ALL"):
    d = DF[(DF.variable == variable) & (DF.scenario == scenario) &
           (DF.year == year) & (DF.commodity == commodity)]
    return d.value.iloc[0] if len(d) else np.nan


def fdpc(scenario, year, comms):
    d = DF[(DF.variable == "food_demand_pc") & (DF.scenario == scenario) &
           (DF.year == year) & (DF.commodity.isin(comms))]
    return d.value.sum()


# =====================================================================
# Fig 1 — three diet pathways, per-capita food 2023 -> 2050 (dumbbell)
# =====================================================================
def fig1():
    items = [  # (label, commodity list, healthy-benchmark group or None)
        ("Cereals (total)", ["RICE", "WHEA", "MAIZ", "OTGR", "BARL", "SORG"], "谷物"),
        ("Rice", ["RICE"], None),
        ("Wheat", ["WHEA"], None),
        ("Tubers", ["POTA"], "薯类"),
        ("Vegetable oils", ["SOYO", "RAPO", "GRDO"], "食用油"),
        ("Vegetables", ["VEGT"], "蔬菜"),
        ("Fruits", ["FRTO"], "水果"),
        ("Meat (total)", ["PIGM", "CATM", "SHGM", "CHKM"], "肉类"),
        ("Pork", ["PIGM"], None),
        ("Beef", ["CATM"], None),
        ("Mutton", ["SHGM"], None),
        ("Poultry", ["CHKM"], None),
        ("Eggs", ["EGGS"], "蛋类"),
        ("Dairy", ["MILK"], "奶类"),
        ("Aquatic products", ["FISH"], "水产品"),
        ("Sugar", ["SUGA"], "糖"),
    ]
    bench = HB.set_index("food_group_cn")
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    ylab, y = [], []
    n = len(items)
    for i, (lab, comms, bg) in enumerate(items):
        yy = n - 1 - i
        y.append(yy)
        ylab.append(lab)
        v23 = fdpc("BS", 2023, comms)
        if bg is not None:  # healthy-diet composite benchmark band (kg/yr purchase)
            lo = bench.loc[bg, "purchase_composite_min_kg_yr"]
            hi = bench.loc[bg, "purchase_composite_max_kg_yr"]
            ax.plot([lo, hi], [yy, yy], lw=6, color=OI["yellow"], alpha=0.9,
                    solid_capstyle="butt", zorder=1)
        for scen, grp in [("A1", "PTS"), ("C1", "MTS"), ("B1", "HDS")]:
            v50 = fdpc(scen, 2050, comms)
            ax.plot([v23, v50], [yy, yy], lw=0.8, color=CS[grp], alpha=0.45, zorder=2)
            ax.plot(v50, yy, "o", ms=4.5, mec="white", mew=0.4, color=CS[grp], zorder=4)
        ax.plot(v23, yy, "o", ms=4.5, color=OI["black"], zorder=5)
        if lab in ("Cereals (total)", "Meat (total)"):
            ax.axhspan(yy - 0.5, yy + 0.5, color="0.93", zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels(ylab)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlim(0, 215)
    ax.set_xlabel("Per-capita food purchases (kg per capita per year)")
    handles = [Line2D([], [], marker="o", ls="none", ms=5, color=OI["black"],
                      label="2023 (base year)")]
    handles += [Line2D([], [], marker="o", ls="none", ms=5, color=CS[g],
                       mec="white", mew=0.4, label=f"2050 {LONG[g]}")
                for g in ("PTS", "MTS", "HDS")]
    handles.append(Patch(color=OI["yellow"], alpha=0.9,
                         label="Healthy-diet benchmark range (composite of six guidelines)"))
    ax.legend(handles=handles, loc="lower right", frameon=False,
              borderaxespad=0.2, handlelength=1.4)
    ax.set_title("China's per-capita food demand, 2023 → 2050, under three diet pathways",
                 loc="left")
    save(fig, "fig1_scenarios")


# =====================================================================
# Fig 2 — China domestic multi-dimensional effects (nutrition + footprints)
# =====================================================================
def fig2():
    scens = ["BS", "A1", "C1", "B1"]
    grps = [CORE[s] for s in scens]
    # (a) dietary energy split into macronutrient contributions
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 3.0),
                             gridspec_kw={"width_ratios": [1.1, 1.0, 1.6]})
    ax = axes[0]
    base = {"energy": val("energy_pc_day_total", "BS", 2023),
            "prot": val("protein_pc_day_total", "BS", 2023),
            "fat": val("fat_pc_day_total", "BS", 2023),
            "carb": val("carbohydrate_pc_day_total", "BS", 2023)}
    cols = {"Carbohydrate": OI["sky"], "Fat": OI["orange"], "Protein": OI["purple"]}
    xt, xl = [], []
    entries = [("2023", "BS", 2023, "0.35")] + [
        (g, s, 2050, CS[g]) for s, g in zip(scens, grps)]
    for i, (lab, scen, yr, _c) in enumerate(entries):
        en = val("energy_pc_day_total", scen, yr)
        pe = val("protein_pc_day_total", scen, yr) * 4
        fe = val("fat_pc_day_total", scen, yr) * 9
        ce = val("carbohydrate_pc_day_total", scen, yr) * 4
        tot = pe + fe + ce
        pe, fe, ce = (x / tot * en for x in (pe, fe, ce))
        ax.bar(i, ce, 0.62, color=cols["Carbohydrate"])
        ax.bar(i, fe, 0.62, bottom=ce, color=cols["Fat"])
        ax.bar(i, pe, 0.62, bottom=ce + fe, color=cols["Protein"])
        ax.text(i, en + 45, f"{fe/en*100:.0f}%", ha="center", fontsize=6.5,
                color=OI["vermillion"])
        xt.append(i)
        xl.append(lab)
    ax.set_xticks(xt)
    ax.set_xticklabels(xl)
    ax.set_ylabel("Dietary energy (kcal per capita per day)")
    ax.set_ylim(0, 4150)
    ax.legend(handles=[Patch(color=c, label=k) for k, c in cols.items()],
              frameon=False, loc="upper right", fontsize=6,
              handlelength=1.2, borderaxespad=0.1)
    ax.set_title("Numbers: fat energy share\n(WHO limit 30%)", fontsize=6.5,
                 color=OI["vermillion"])
    panel_label(ax, "a")

    # (b) diet-quality proxies vs guideline bands (2050)
    ax = axes[1]
    esh = NC.set_index("commodity_code").edible_share_pct / 100.0
    def gday(scen, comms):
        d = DF[(DF.variable == "food_demand_pc") & (DF.scenario == scen) &
               (DF.year == 2050) & (DF.commodity.isin(comms))]
        return sum(r.value * esh.get(r.commodity, 1.0) for r in d.itertuples()) * 1000 / 365
    metrics = [("Red meat", ["PIGM", "CATM", "SHGM"], 14, 28),
               ("Dairy", ["MILK"], 300, 500),
               ("Aquatic", ["FISH"], 40, 75),
               ("Fruits", ["FRTO"], 200, 350)]
    for j, (lab, comms, lo, hi) in enumerate(metrics):
        ax.plot([lo, hi], [len(metrics) - 1 - j] * 2, lw=6, color=OI["yellow"],
                alpha=.9, solid_capstyle="butt", zorder=1)
        for s, g in zip(scens, grps):
            ax.plot(gday(s, comms), len(metrics) - 1 - j, "o", ms=4.5,
                    color=CS[g], mec="white", mew=0.4, zorder=3)
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels([m[0] for m in metrics][::-1])
    ax.set_xlabel("Edible intake, 2050 (g per capita per day)")
    ax.set_xlim(0, 430)
    ax.set_ylim(-0.6, len(metrics) - 0.4)
    ax.legend(handles=[Line2D([], [], marker="o", ls="none", ms=4, color=CS[g],
                              mec="white", mew=0.3, label=g)
                       for g in ("BS", "PTS", "MTS", "HDS")],
              frameon=False, fontsize=5.5, loc="lower right", ncol=2,
              columnspacing=0.8, handletextpad=0.2, borderaxespad=0.1)
    ax.set_title("Intakes vs guideline ranges\n(yellow bands)", fontsize=6.5)
    panel_label(ax, "b")

    # (c) environmental footprints, % change vs BS 2050 (whiskers = scenario spread)
    ax = axes[2]
    inds = [("co2_faostat_cons", "Carbon\n(Mt CO2e)"),
            ("water_blue", "Blue water\n(km$^3$)"),
            ("nitrogen_total", "Reactive N\n(Mt N)"),
            ("land_diet", "Land\n(Mha)")]
    scen_sets = {"PTS": [f"A{i}" for i in range(1, 7)],
                 "MTS": [f"C{i}" for i in range(1, 7)],
                 "HDS": [f"B{i}" for i in range(1, 7)]}
    w = 0.24
    for k, (grp, ss) in enumerate(scen_sets.items()):
        xs, ys, ylo, yhi = [], [], [], []
        for j, (ind, _lab) in enumerate(inds):
            g = CFP[CFP.indicator == ind].set_index("scenario").pct_vs_BS_2050
            centre = g[ss[0]]           # A1/C1/B1 = central assumptions
            spread = g.reindex(ss).dropna()
            xs.append(j + (k - 1) * w)
            ys.append(centre)
            ylo.append(centre - spread.min())
            yhi.append(spread.max() - centre)
        ax.bar(xs, ys, w * 0.88, color=CS[grp], label=LONG[grp])
        ax.errorbar(xs, ys, yerr=[ylo, yhi], fmt="none", ecolor="0.25",
                    elinewidth=0.7, capsize=1.8)
    ax.axhline(0, color="0.2", lw=0.7)
    ax.set_xticks(range(len(inds)))
    ax.set_xticklabels([l for _, l in inds])
    ax.set_ylabel("Change vs BS, 2050 (%)")
    ax.set_ylim(-12, 17)
    ax.legend([Patch(color=CS[g]) for g in scen_sets],
              [f"{g} ({s})" for g, s in
               [("PTS", "A1"), ("MTS", "C1"), ("HDS", "B1")]],
              frameon=False, loc="upper left", fontsize=6, ncol=3,
              columnspacing=0.9, handlelength=1.1, borderaxespad=0.1)
    ax.set_title("Consumption footprints, fixed 2023 coefficients\n"
                 "(whiskers: population / urbanisation / ageing variants)",
                 fontsize=6.5)
    panel_label(ax, "c")

    fig.suptitle("China's domestic nutrition and environmental effects in 2050",
                 x=0.02, ha="left", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, "fig2_china_multidim")


# =====================================================================
# Fig 3 — global transmission
# =====================================================================
WC_EN = {"RIC": "Rice", "WHE": "Wheat", "CRN": "Maize", "SBS": "Soybean",
         "SBO": "Soybean oil", "SBM": "Soybean meal", "RBS": "Rapeseed",
         "BFV": "Beef", "PRK": "Pork", "PLM": "Poultry", "BUT": "Butter",
         "NDM": "Skim milk powder", "WDM": "Whole milk powder", "SUG": "Sugar"}


def fig3():
    fig = plt.figure(figsize=(7.2, 5.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1], hspace=0.52, wspace=0.32)

    # (a) world price change, 2050 vs BS
    ax = fig.add_subplot(gs[0, 0])
    prf = WL[(WL.variable == "PRF") & (WL.region == "WLD") & (WL.year == 2050)]
    prf = prf.pivot_table(index="commodity", columns="scenario", values="value")
    order = ["PRK", "SBO", "RBS", "BFV", "SBS", "CRN", "RIC", "WHE",
             "PLM", "SUG", "SBM", "BUT", "NDM", "WDM"]
    ypos = np.arange(len(order))[::-1]
    h = 0.26
    for k, g in enumerate(["PTS", "MTS", "HDS"]):
        pct = (prf.loc[order, g] / prf.loc[order, "BS"] - 1) * 100
        ax.barh(ypos + (1 - k) * h, pct.values, h * 0.9, color=CS[g],
                label=f"{g} ({dict(PTS='A1', MTS='C1', HDS='B1')[g]})")
    ax.axvline(0, color="0.2", lw=0.7)
    ax.set_yticks(ypos)
    ax.set_yticklabels([WC_EN[c] for c in order])
    ax.set_xlabel("World price change vs BS, 2050 (%)")
    ax.legend(frameon=False, loc="lower left", fontsize=6)
    panel_label(ax, "a", dx=-0.22)

    # (b) production response of major exporters, HDS 2050 (% vs BS)
    ax = fig.add_subplot(gs[0, 1])
    regions = ["BRZ", "ARG", "USA", "AUS", "NZL", "E15"]
    comms = ["SBS", "CRN", "BFV", "PRK", "PLM", "WDM"]
    prd = WL[(WL.variable == "PRD") & (WL.year == 2050) &
             (WL.region.isin(regions)) & (WL.commodity.isin(comms))]
    prd = prd.pivot_table(index=["region", "commodity"], columns="scenario",
                          values="value")
    M = np.full((len(regions), len(comms)), np.nan)
    for i, r in enumerate(regions):
        for j, c in enumerate(comms):
            try:
                row = prd.loc[(r, c)]
                if row["BS"] > 0.05:  # skip negligible sectors
                    M[i, j] = (row["HDS"] / row["BS"] - 1) * 100
            except KeyError:
                pass
    im = ax.imshow(M, cmap="RdBu", vmin=-50, vmax=50, aspect="auto")
    for i in range(len(regions)):
        for j in range(len(comms)):
            if np.isfinite(M[i, j]):
                ax.text(j, i, f"{M[i,j]:+.0f}", ha="center", va="center",
                        fontsize=6.5,
                        color="white" if abs(M[i, j]) > 32 else "0.15")
    ax.set_xticks(range(len(comms)))
    ax.set_xticklabels([WC_EN[c] for c in comms], rotation=30, ha="right")
    ax.set_yticks(range(len(regions)))
    ax.set_yticklabels(["Brazil", "Argentina", "United States", "Australia",
                        "New Zealand", "EU-15"])
    cb = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cb.set_label("Production change, HDS vs BS, 2050 (%)", fontsize=6.5)
    cb.ax.tick_params(labelsize=6)
    panel_label(ax, "b", dx=-0.28)

    # (c) China net imports, 2050
    ax = fig.add_subplot(gs[1, :])
    comms = ["SBS", "CRN", "WHE", "RIC", "SBM", "PRK", "BFV", "SBO", "PLM", "WDM"]
    ni = WL[(WL.region == "CHN") & (WL.year == 2050) &
            (WL.variable.isin(["IMP", "EXP"])) & (WL.commodity.isin(comms))]
    ni = ni.pivot_table(index="commodity", columns=["scenario", "variable"],
                        values="value")
    x = np.arange(len(comms))
    w = 0.2
    for k, g in enumerate(["BS", "PTS", "MTS", "HDS"]):
        imp = ni[(g, "IMP")] if (g, "IMP") in ni else 0.0
        exp = ni[(g, "EXP")] if (g, "EXP") in ni else 0.0
        v = (pd.Series(imp, index=ni.index).fillna(0)
             - pd.Series(exp, index=ni.index).fillna(0)).reindex(comms)
        ax.bar(x + (k - 1.5) * w, v.values, w * 0.9, color=CS[g], label=LONG[g])
    ax.axhline(0, color="0.2", lw=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([WC_EN[c].replace("Whole milk powder", "Whole milk\npowder")
                        for c in comms])
    ax.set_ylabel("China net imports, 2050 (Mt)\n(negative = net exports)")
    ax.legend(frameon=False, ncol=2, loc="upper right", fontsize=6)
    ax.annotate("China exits the world pork-import market\n(net-export pressure under HDS)",
                xy=(4.7, -50), fontsize=6, color="0.3")
    panel_label(ax, "c", dx=-0.055)

    fig.suptitle("Global transmission of China's dietary transition (CASM–World, 2050)",
                 x=0.02, ha="left", fontsize=9)
    save(fig, "fig3_global_transmission")


# =====================================================================
# Fig 4 — global net environmental effect + MTS dividend curve
# =====================================================================
def fig4():
    fig = plt.figure(figsize=(7.5, 3.4))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 1, 2.3], wspace=0.75,
                          left=0.07, right=0.99, top=0.80, bottom=0.20)

    inds = [("co2_faostat", "Carbon", "Mt CO2e"),
            ("water_blue", "Blue water", "km$^3$"),
            ("nitrogen_total", "Reactive N", "Mt N"),
            ("land_harvested", "Harvested area", "Mha")]
    for j, (ind, lab, unit) in enumerate(inds):
        ax = fig.add_subplot(gs[0, j])
        for k, g in enumerate(["MTS", "HDS"]):
            chn = WFP[(WFP.indicator == ind) & (WFP.scenario == g) &
                      (WFP.region_group == "CHN")].abs_vs_BS_2050.iloc[0]
            exc = WFP[(WFP.indicator == ind) & (WFP.scenario == g) &
                      (WFP.region_group == "exCHN")].abs_vs_BS_2050.iloc[0]
            ax.bar(k, chn, 0.55, color=CS[g], label="China" if k == 0 else None)
            ax.bar(k, exc, 0.55, bottom=chn, color=CS[g], alpha=0.45)
            ax.text(k, chn + exc - abs(chn + exc) * 0.02, f"{chn+exc:.0f}",
                    ha="center", va="top", fontsize=6)
        ax.axhline(0, color="0.2", lw=0.7)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["MTS", "HDS"])
        ax.set_title(f"{lab}\n({unit})", fontsize=7)
        if j == 0:
            ax.set_ylabel("Change vs BS, 2050")
            panel_label(ax, "a", dx=-0.62, dy=1.14)
    fig.legend(handles=[Patch(color="0.35", label="within China"),
                        Patch(color="0.35", alpha=0.45, label="outside China")],
               frameon=False, loc="lower center", ncol=2,
               bbox_to_anchor=(0.34, -0.03), fontsize=6.5)

    # (b) transition depth vs dividend realisation
    ax = fig.add_subplot(gs[0, 4])
    curves = [("Dietary energy", "China: dietary energy", OI["purple"]),
              ("Fat energy share", "China: fat energy share", OI["orange"]),
              ("Red meat intake", "China: red meat intake", OI["vermillion"]),
              ("CO2 (paper, scenario EF)", "China: CO$_2$ emissions", OI["black"]),
              ("Global agri CO2 (traded goods)", "Global: agricultural CO$_2$", OI["blue"]),
              ("Global blue water (traded goods)", "Global: blue water", OI["sky"]),
              ("Global reactive N (traded goods)", "Global: reactive N", OI["green"]),
              ("Rest-of-world harvested area", "Outside China: cropland release", OI["yellow"])]
    ax.plot([0, 100], [0, 100], ls="--", lw=0.8, color="0.6", zorder=1)
    ax.text(72, 62, "proportional\nbenefit", fontsize=6, color="0.5", rotation=38)
    for metric, lab, c in curves:
        r = MTS_EFF[MTS_EFF.metric == metric]
        if not len(r) or not np.isfinite(r.MTS_realisation_pct.iloc[0]):
            continue
        y50 = r.MTS_realisation_pct.iloc[0]
        ax.plot([0, 50, 100], [0, y50, 100], "-o", ms=3.5, lw=1.1, color=c,
                mec="white", mew=0.3, label=f"{lab} ({y50:.0f}%)")
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0\nPTS", "50\nMTS", "100\nHDS"])
    ax.set_xlabel("Transition depth, PTS → HDS (%)")
    ax.set_ylabel("Share of HDS dividend realised (%)")
    ax.set_ylim(0, 102)
    ax.legend(frameon=False, fontsize=5.4, loc="upper left", handlelength=1.2,
              borderaxespad=0.1, labelspacing=0.35)
    ax.set_title("Half the transition, ~60–70% of the dividend", fontsize=7.5)
    panel_label(ax, "b", dx=-0.14, dy=1.14)

    fig.suptitle("Global net environmental effect of China's dietary transition, 2050",
                 x=0.02, y=0.985, ha="left", fontsize=9)
    save(fig, "fig4_global_net_effect")


# =====================================================================
# ED 1 — 19-scenario matrix heat map
# =====================================================================
def ed1():
    scens = ["A1", "A2", "A3", "A4", "A5", "A6",
             "C1", "C2", "C3", "C4", "C5", "C6",
             "B1", "B2", "B3", "B4", "B5", "B6"]
    variant = {"1": "central", "2": "high pop.", "3": "low pop.",
               "4": "high urb.", "5": "low urb.", "6": "ageing (AE)"}
    cols = []
    # population & diet indicators from results_long (% vs BS 2050)
    def pct(var, scen):
        return (val(var, scen, 2050) / val(var, "BS", 2050) - 1) * 100
    MEATS = ["PIGM", "CATM", "SHGM", "CHKM"]
    def meat_tot(scen):
        d = DF[(DF.variable == "food_demand_total") & (DF.scenario == scen) &
               (DF.year == 2050) & (DF.commodity.isin(MEATS))]
        return d.value.sum()
    M, rowlab = [], []
    fps = [("co2_faostat_cons", "Carbon (cons.)"), ("co2_pn_lca", "Carbon (LCA)"),
           ("water_blue", "Blue water"), ("nitrogen_total", "Reactive N"),
           ("land_diet", "Diet land")]
    collab = (["Population", "Meat demand", "Energy p.c.", "Fat p.c."] +
              [l for _, l in fps])
    for s in scens:
        row = [pct("population_total", s),
               (meat_tot(s) / meat_tot("BS") - 1) * 100,
               pct("energy_pc_day_total", s), pct("fat_pc_day_total", s)]
        for ind, _l in fps:
            row.append(CFP[(CFP.indicator == ind) & (CFP.scenario == s)]
                       .pct_vs_BS_2050.iloc[0])
        M.append(row)
        g = {"A": "PTS", "B": "HDS", "C": "MTS"}[s[0]]
        rowlab.append(f"{s} {g}, {variant[s[1]]}")
    M = np.array(M)
    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-60, vmax=60, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i,j]:+.0f}", ha="center", va="center", fontsize=6,
                    color="white" if abs(M[i, j]) > 40 else "0.15")
    ax.set_xticks(range(len(collab)))
    ax.set_xticklabels(collab, rotation=35, ha="right")
    ax.set_yticks(range(len(rowlab)))
    ax.set_yticklabels(rowlab, fontsize=6.5)
    for k in (5.5, 11.5):
        ax.axhline(k, color="white", lw=2)
    cb = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cb.set_label("Change vs BS, 2050 (%)")
    ax.set_title("All 19 scenarios: demographic sensitivity of 2050 outcomes\n"
                 "(% vs BS; footprints at fixed 2023 coefficients)", loc="left")
    save(fig, "ed1_scenario_matrix")


# =====================================================================
# ED 2 — carbon coefficient-boundary sensitivity
# =====================================================================
def ed2():
    scens = ["A1", "C1", "B1"]
    grp = ["PTS", "MTS", "HDS"]
    sources = [("paper", "China inventory EF\n(scenario-specific, farm-gate)"),
               ("co2_faostat_cons", "FAOSTAT farm-gate\n(fixed 2023, consumption)"),
               ("co2_pn_lca", "Poore & Nemecek LCA\n(cradle-to-retail)")]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8),
                             gridspec_kw={"width_ratios": [1, 1.2]})
    # levels
    ax = axes[0]
    bs_lvl = {"paper": val("co2_total", "BS", 2050) / 100,
              "co2_faostat_cons": CFP[(CFP.indicator == "co2_faostat_cons") &
                                      (CFP.scenario == "BS")].y2050.iloc[0],
              "co2_pn_lca": CFP[(CFP.indicator == "co2_pn_lca") &
                                (CFP.scenario == "BS")].y2050.iloc[0]}
    ax.bar(range(3), [bs_lvl[k] for k, _ in sources],
           color=[OI["grey"], OI["sky"], OI["blue"]], width=0.6)
    for i, (k, _) in enumerate(sources):
        ax.text(i, bs_lvl[k] * 1.02, f"{bs_lvl[k]:,.0f}", ha="center", fontsize=6.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels([l for _, l in sources], fontsize=6)
    ax.set_ylabel("BS 2050 emissions (Mt CO$_2$e)")
    ax.set_yscale("log")
    ax.set_title("Boundary matters ~12× in level", fontsize=7.5)
    panel_label(ax, "a", dx=-0.2)
    # % vs BS
    ax = axes[1]
    w = 0.26
    for k, (src, lab) in enumerate(sources):
        ys = []
        for s in scens:
            if src == "paper":
                ys.append((val("co2_total", s, 2050) / val("co2_total", "BS", 2050)
                           - 1) * 100)
            else:
                ys.append(CFP[(CFP.indicator == src) & (CFP.scenario == s)]
                          .pct_vs_BS_2050.iloc[0])
        ax.bar(np.arange(3) + (k - 1) * w, ys, w * 0.9,
               color=[OI["grey"], OI["sky"], OI["blue"]][k], label=lab.replace("\n", " "))
    ax.axhline(0, color="0.2", lw=0.7)
    ax.set_xticks(range(3))
    ax.set_xticklabels([LONG[g].split(" (")[0] for g in grp])
    ax.set_ylabel("Change vs BS, 2050 (%)")
    ax.legend(frameon=False, fontsize=5.6, loc="lower left")
    ax.set_title("Scenario ranking is robust; magnitude is boundary-dependent",
                 fontsize=7.5)
    panel_label(ax, "b", dx=-0.12)
    fig.tight_layout()
    save(fig, "ed2_carbon_sensitivity")


# =====================================================================
# ED 3 — self-sufficiency ratio change 2024 vs 2050
# =====================================================================
def ed3():
    mat = pd.read_csv(os.path.join(PA, "ssr_2050_matrix.csv"), index_col=0)
    order = ["Rice", "Wheat", "Maize", "Soybean", "Sugar", "Pork", "Beef",
             "Mutton", "Poultry", "Eggs", "Dairy", "Aquatic", "Fruits",
             "Vegetables"]
    mat = mat.reindex(order)
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    y = np.arange(len(order))[::-1]
    for scen, g in [("A1", "PTS"), ("C1", "MTS"), ("B1", "HDS")]:
        ax.plot(mat[scen] * 100, y, "o", ms=4.5, color=CS[g], mec="white",
                mew=0.4, label=f"2050 {LONG[g]}", zorder=3)
    ax.plot(mat["BS"] * 100, y, "o", ms=4.5, color=CS["BS"], mec="white",
            mew=0.4, label="2050 BS", zorder=3)
    ax.plot(mat["y2024"] * 100, y, "x", ms=5, color=OI["black"],
            label="2024 (base)", zorder=4)
    for yy in y:
        ax.axhline(yy, color="0.9", lw=0.5, zorder=1)
    ax.axvline(100, color="0.4", lw=0.7, ls=":")
    ax.set_yticks(y)
    ax.set_yticklabels(order)
    ax.set_xlabel("Self-sufficiency ratio: production / (production + net imports) (%)")
    ax.set_xlim(0, 108)
    ax.legend(frameon=False, loc="center left", fontsize=6)
    ax.set_title("China's self-sufficiency, 2024 vs 2050 by diet pathway", loc="left")
    save(fig, "ed3_ssr_change")


# =====================================================================
# ED 4 — model validation: Python port vs GAMS
# =====================================================================
def ed4():
    txt = open(os.path.join(RES, "validation_report.md")).read()
    sec = txt.split("## Key indicators, 2050")[1].split("##")[0]
    labels = ["Rice demand (kg/cap)", "Pork demand (kg/cap)",
              "Dairy demand (kg/cap)", "Energy (kcal/cap/day)",
              "CO$_2$ (10 kt CO$_2$e)"]
    pts = {l: [] for l in labels}
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or "/" not in cells[1]:
            continue
        for lab, cell in zip(labels, cells[1:6]):
            m = re.match(r"([\d.]+)\s*/\s*([\d.]+)", cell)
            if m and float(m.group(2)) > 0:
                pts[lab].append((float(m.group(2)), float(m.group(1))))
    fig, ax = plt.subplots(figsize=(3.6, 3.4))
    colors = [OI["vermillion"], OI["blue"], OI["green"], OI["purple"], OI["black"]]
    allv = []
    for lab, c in zip(labels, colors):
        arr = np.array(pts[lab])
        ax.plot(arr[:, 0], arr[:, 1], "o", ms=4, color=c, mec="white", mew=0.3,
                label=f"{lab} (n={len(arr)})", alpha=0.85)
        allv += arr.flatten().tolist()
    lim = [min(allv) * 0.7, max(allv) * 1.4]
    ax.plot(lim, lim, ls="--", lw=0.8, color="0.5", zorder=1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("GAMS CASM v2.2.7 (original)")
    ax.set_ylabel("Python port (this study)")
    ax.legend(frameon=False, fontsize=5.5, loc="upper left")
    ax.set_title("Validation: 2050 key indicators, 19 scenarios\n"
                 "(median cell-level rel. deviation < 1e-15)", loc="left", fontsize=7.5)
    save(fig, "ed4_validation")


if __name__ == "__main__":
    print("making figures ->", FIG)
    fig1(); fig2(); fig3(); fig4()
    ed1(); ed2(); ed3(); ed4()
    print("all figures done")
