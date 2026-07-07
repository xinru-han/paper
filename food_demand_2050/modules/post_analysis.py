#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-hoc analyses for the China food demand 2050 paper (target: Nature Food).

Outputs (results/post_analysis/):
  1. ssr_paths.csv / ssr_2050_matrix.csv / import_dependence_soy_dairy.csv
  2. per_capita_footprints_vs_boundaries.csv
  3. mts_efficiency.csv
  4. diet_health_proxies_2050.csv
  5. README.md  (summary of all findings)

All heavy lifting reads only from results/ and scenarios/ csv files.
Run:  python3 modules/post_analysis.py
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "post_analysis")
SCN = os.path.join(ROOT, "scenarios")
os.makedirs(OUT, exist_ok=True)

CORE = {"BS": "BS", "A1": "PTS", "B1": "HDS", "C1": "MTS"}  # core scenarios
GROUP = {**{f"A{i}": "PTS" for i in range(1, 7)},
         **{f"B{i}": "HDS" for i in range(1, 7)},
         **{f"C{i}": "MTS" for i in range(1, 7)}, "BS": "BS"}

# ---------------------------------------------------------------- loaders
def load_long():
    df = pd.read_csv(os.path.join(RES, "results_long.csv"))
    df.columns = [c.strip("﻿") for c in df.columns]
    return df


def load_china_fp():
    return pd.read_csv(os.path.join(RES, "footprints", "china_footprints_summary.csv"))


def load_world_fp():
    return pd.read_csv(os.path.join(RES, "footprints", "world_footprints_summary.csv"))


def load_world_long():
    return pd.read_csv(os.path.join(RES, "world", "world_results_long.csv"))


def pivot(df, variable, scenarios=None, years=None, commodities=None):
    d = df[df.variable == variable]
    if scenarios is not None:
        d = d[d.scenario.isin(scenarios)]
    if years is not None:
        d = d[d.year.isin(years)]
    if commodities is not None:
        d = d[d.commodity.isin(commodities)]
    return d


# ---------------------------------------------------------------- 1. SSR
SSR_COMM = ["RICE", "WHEA", "MAIZ", "SOYS", "SUGA", "PIGM", "CATM",
            "SHGM", "CHKM", "EGGS", "MILK", "FISH", "FRTO", "VEGT"]
COMM_EN = {"RICE": "Rice", "WHEA": "Wheat", "MAIZ": "Maize", "SOYS": "Soybean",
           "SUGA": "Sugar", "PIGM": "Pork", "CATM": "Beef", "SHGM": "Mutton",
           "CHKM": "Poultry", "EGGS": "Eggs", "MILK": "Dairy", "FISH": "Aquatic",
           "FRTO": "Fruits", "VEGT": "Vegetables", "OTGR": "Other grains",
           "POTA": "Tubers", "SOYO": "Soybean oil", "RAPO": "Rapeseed oil",
           "GRDS": "Groundnut", "BARL": "Barley", "SORG": "Sorghum"}


def analysis_ssr(df):
    prod = pivot(df, "production", commodities=SSR_COMM).rename(columns={"value": "production"})
    ni = pivot(df, "net_import", commodities=SSR_COMM).rename(columns={"value": "net_import"})
    m = prod.merge(ni[["scenario", "commodity", "year", "net_import"]],
                   on=["scenario", "commodity", "year"])
    m["apparent_consumption"] = m.production + m.net_import
    m = m[m.apparent_consumption > 0]
    m["ssr"] = m.production / m.apparent_consumption
    m["import_dependence"] = 1 - m.ssr
    m["group"] = m.scenario.map(GROUP)
    keep = ["scenario", "group", "commodity", "year",
            "production", "net_import", "ssr", "import_dependence"]
    paths = m[m.scenario.isin(CORE)][keep].sort_values(["commodity", "scenario", "year"])
    paths.to_csv(os.path.join(OUT, "ssr_paths.csv"), index=False)

    mat = (m[m.year == 2050].pivot_table(index="commodity", columns="scenario", values="ssr")
           .reindex(SSR_COMM))
    mat24 = m[(m.year == 2024) & (m.scenario == "BS")].set_index("commodity").ssr
    mat.insert(0, "y2024", mat24.reindex(mat.index))
    mat.index = [COMM_EN.get(c, c) for c in mat.index]
    mat.round(4).to_csv(os.path.join(OUT, "ssr_2050_matrix.csv"))

    dep = m[(m.commodity.isin(["SOYS", "MILK"])) & (m.scenario.isin(CORE))]
    dep = dep[dep.year.isin([2024, 2030, 2035, 2040, 2045, 2050])]
    dep = dep[["scenario", "group", "commodity", "year", "net_import",
               "production", "import_dependence"]]
    dep.to_csv(os.path.join(OUT, "import_dependence_soy_dairy.csv"), index=False)
    return m, mat


# ------------------------------------------- 2. per-capita vs boundaries
# Planetary-boundary global budgets (food system), divided by 2050 world
# population of 9.7 bn (UN WPP 2024 medium) to obtain per-capita shares:
#   GHG   : 5 Gt CO2e/yr food-system boundary (EAT-Lancet, Willett et al. 2019)
#   Blue water: 2,500 km3/yr consumptive use (EAT-Lancet)
#   Nitrogen  : 90 Mt N/yr application (EAT-Lancet; PB zone 62-82+)
#   Cropland  : 13 M km2 = 1,300 Mha (EAT-Lancet)
BOUNDARIES = {
    "co2_faostat_cons": ("GHG (farm-gate, cons.)", "kg CO2e/cap/yr", 5000e6 / 9.7e9 * 1e3),
    "water_blue": ("Blue water", "m3/cap/yr", 2500 / 9.7e9 * 1e9),
    "nitrogen_total": ("Reactive N", "kg N/cap/yr", 90e6 / 9.7e9 * 1e3),
    "land_diet": ("Land (cradle, incl. pasture)", "ha/cap", 1300e6 / 9.7e9),
}
FP_TO_KG = {"co2_faostat_cons": 1e9,   # Mt -> kg
            "water_blue": 1e9,         # km3 -> m3
            "nitrogen_total": 1e9,     # Mt N -> kg N
            "land_diet": 1e6}          # Mha -> ha


def analysis_boundaries(df, cfp):
    pop = (pivot(df, "population_total", years=[2050]).groupby("scenario").value.first()
           * 1e4)  # 万人 -> persons
    rows = []
    for _, r in cfp[cfp.indicator.isin(BOUNDARIES)].iterrows():
        name, unit, bshare = BOUNDARIES[r.indicator]
        pc = r.y2050 * FP_TO_KG[r.indicator] / pop[r.scenario]
        rows.append({"scenario": r.scenario, "group": GROUP[r.scenario],
                     "indicator": name, "unit": unit,
                     "per_capita_2050": pc, "boundary_share": bshare,
                     "ratio_to_boundary": pc / bshare})
    out = pd.DataFrame(rows).sort_values(["indicator", "scenario"])
    out.round(3).to_csv(os.path.join(OUT, "per_capita_footprints_vs_boundaries.csv"),
                        index=False)
    return out


# ---------------------------------------------------- 3. MTS efficiency
def _real(pts, mts, hds):
    """Share of the PTS->HDS dividend realised by MTS (%).

    Returns NaN when the PTS->HDS dividend is <2% of the metric's scale
    (ratio not meaningful, e.g. China blue water where HDS ~= PTS)."""
    scale = max(abs(pts), abs(hds), 1e-9)
    if abs(hds - pts) < 0.02 * scale:
        return np.nan
    return (mts - pts) / (hds - pts) * 100.0


def analysis_mts(df, cfp, wfp, wl):
    rows = []

    def add(domain, metric, unit, pts, mts, hds, bs=np.nan):
        rows.append({"domain": domain, "metric": metric, "unit": unit,
                     "BS": bs, "PTS": pts, "MTS": mts, "HDS": hds,
                     "dividend_HDS_minus_PTS": hds - pts,
                     "MTS_realisation_pct": _real(pts, mts, hds)})

    # --- China nutrition / diet (results_long, 2050, ALL)
    def tot(var, scen):
        return pivot(df, var, [scen], [2050], ["ALL"]).value.iloc[0]

    for var, lab, unit in [("energy_pc_day_total", "Dietary energy", "kcal/cap/day"),
                           ("fat_pc_day_total", "Fat intake", "g/cap/day"),
                           ("protein_pc_day_total", "Protein intake", "g/cap/day")]:
        add("China diet", lab, unit, tot(var, "A1"), tot(var, "C1"), tot(var, "B1"),
            tot(var, "BS"))
    # fat energy share
    fes = {s: tot("fat_pc_day_total", s) * 9 / tot("energy_pc_day_total", s) * 100
           for s in CORE}
    add("China diet", "Fat energy share", "%", fes["A1"], fes["C1"], fes["B1"], fes["BS"])
    # red meat g/d (edible)
    ncoef = pd.read_csv(os.path.join(SCN, "nutrient_coefficients.csv"))
    ncoef.columns = [c.strip("﻿") for c in ncoef.columns]
    esh = ncoef.set_index("commodity_code").edible_share_pct / 100.0
    def redmeat(s):
        v = pivot(df, "food_demand_pc", [s], [2050], ["PIGM", "CATM", "SHGM"])
        return sum(r.value * esh.get(r.commodity, 1.0) for r in v.itertuples()) * 1000 / 365
    add("China diet", "Red meat intake", "g/cap/day",
        redmeat("A1"), redmeat("C1"), redmeat("B1"), redmeat("BS"))

    # --- China footprints (paper CO2 + fixed-coefficient footprints, 2050)
    co2p = {s: pivot(df, "co2_total", [s], [2050], ["ALL"]).value
            for s in CORE}
    co2p = {s: (v.iloc[0] / 100.0 if len(v) else np.nan) for s, v in co2p.items()}  # 万吨->Mt
    add("China footprint", "CO2 (paper, scenario EF)", "Mt CO2e",
        co2p["A1"], co2p["C1"], co2p["B1"], co2p["BS"])
    for ind, lab, unit in [("co2_faostat_cons", "CO2 (FAOSTAT cons., fixed EF)", "Mt CO2e"),
                           ("water_blue", "Blue water", "km3"),
                           ("nitrogen_total", "Reactive N", "Mt N"),
                           ("land_diet", "Diet land (cradle)", "Mha")]:
        g = cfp[cfp.indicator == ind].set_index("scenario").y2050
        add("China footprint", lab, unit, g["A1"], g["C1"], g["B1"], g["BS"])

    # --- World transmission (CASM-World, 2050)
    prf = wl[(wl.variable == "PRF") & (wl.region == "WLD") & (wl.year == 2050)]
    prf = prf.pivot_table(index="commodity", columns="scenario", values="value")
    for c, lab in [("PRK", "World pork price"), ("BFV", "World beef price"),
                   ("SBS", "World soybean price"), ("CRN", "World maize price"),
                   ("WDM", "World whole milk powder price")]:
        pct = (prf.loc[c] / prf.loc[c, "BS"] - 1) * 100
        add("World market", lab + " change vs BS", "%",
            pct["PTS"], pct["MTS"], pct["HDS"], 0.0)

    for ind, rg, lab, unit in [
            ("co2_faostat", "WLD", "Global agri CO2 (traded goods)", "Mt CO2e"),
            ("co2_faostat", "exCHN", "Rest-of-world agri CO2", "Mt CO2e"),
            ("water_blue", "WLD", "Global blue water (traded goods)", "km3"),
            ("nitrogen_total", "WLD", "Global reactive N (traded goods)", "Mt N"),
            ("land_harvested", "exCHN", "Rest-of-world harvested area", "Mha"),
            ("land_harvested", "WLD", "Global harvested area", "Mha")]:
        g = wfp[(wfp.indicator == ind) & (wfp.region_group == rg)]
        g = g.set_index("scenario").y2050
        add("Global net effect", lab, unit, g["PTS"], g["MTS"], g["HDS"], g["BS"])

    out = pd.DataFrame(rows)
    out.round(3).to_csv(os.path.join(OUT, "mts_efficiency.csv"), index=False)
    return out


# ------------------------------------------- 4. diet health proxies 2050
# Guideline reference values:
#   Red meat        : EAT-Lancet 14 (0-28) g/d; CDG-2022 livestock+poultry 40-75 g/d
#   Whole grains proxy (total cereals, edible g/d): CDG 200-300 g/d
#   Vegetables      : CDG 300-500 g/d          Fruits : CDG 200-350 g/d
#   Dairy           : CDG 300-500 g/d          Aquatic: CDG 40-75 g/d (2/wk)
#   Eggs            : CDG 40-50 g/d            Sugar  : CDG <50 g/d (WHO free sugars <10%E)
#   Fat energy share: WHO <30 %E               Carbohydrate share: CDG 50-65 %E
GUIDE = {
    "red_meat_g_d": ("Red meat (pork+beef+mutton)", "g/d", 14, 28),
    "meat_total_g_d": ("Meat total (incl. poultry)", "g/d", 40, 75),
    "cereals_g_d": ("Cereals (whole-grain proxy)", "g/d", 200, 300),
    "vegetables_g_d": ("Vegetables", "g/d", 300, 500),
    "fruits_g_d": ("Fruits", "g/d", 200, 350),
    "dairy_g_d": ("Dairy", "g/d", 300, 500),
    "aquatic_g_d": ("Aquatic products", "g/d", 40, 75),
    "eggs_g_d": ("Eggs", "g/d", 40, 50),
    "sugar_g_d": ("Added sugar", "g/d", 0, 50),
    "fat_energy_share": ("Fat energy share (WHO <30%)", "%E", 20, 30),
    "carb_energy_share": ("Carbohydrate energy share", "%E", 50, 65),
    "energy_kcal_d": ("Dietary energy", "kcal/d", 2000, 2600),
}
BASKETS = {
    "red_meat_g_d": ["PIGM", "CATM", "SHGM"],
    "meat_total_g_d": ["PIGM", "CATM", "SHGM", "CHKM"],
    "cereals_g_d": ["RICE", "WHEA", "MAIZ", "BARL", "SORG", "OTGR"],
    "vegetables_g_d": ["VEGT"], "fruits_g_d": ["FRTO"], "dairy_g_d": ["MILK"],
    "aquatic_g_d": ["FISH"], "eggs_g_d": ["EGGS"], "sugar_g_d": ["SUGA"],
}


def analysis_health(df):
    ncoef = pd.read_csv(os.path.join(SCN, "nutrient_coefficients.csv"))
    ncoef.columns = [c.strip("﻿") for c in ncoef.columns]
    esh = ncoef.set_index("commodity_code").edible_share_pct / 100.0
    fd = pivot(df, "food_demand_pc", years=[2050])
    fd = fd.assign(gday=lambda d: d.value * d.commodity.map(esh).fillna(1.0) * 1000 / 365)
    en = pivot(df, "energy_pc_day_total", years=[2050], commodities=["ALL"]) \
        .set_index("scenario").value
    fat = pivot(df, "fat_pc_day_total", years=[2050], commodities=["ALL"]) \
        .set_index("scenario").value
    carb = pivot(df, "carbohydrate_pc_day_total", years=[2050], commodities=["ALL"]) \
        .set_index("scenario").value

    rows = []
    for scen in sorted(df.scenario.unique(), key=lambda s: (s != "BS", s)):
        vals = {}
        sub = fd[fd.scenario == scen]
        for k, comms in BASKETS.items():
            vals[k] = sub[sub.commodity.isin(comms)].gday.sum()
        vals["fat_energy_share"] = fat[scen] * 9 / en[scen] * 100
        vals["carb_energy_share"] = carb[scen] * 4 / en[scen] * 100
        vals["energy_kcal_d"] = en[scen]
        for k, v in vals.items():
            lab, unit, lo, hi = GUIDE[k]
            dev = 0.0 if lo <= v <= hi else (v - hi if v > hi else v - lo)
            rows.append({"scenario": scen, "group": GROUP[scen], "indicator": lab,
                         "unit": unit, "value_2050": v, "guide_low": lo,
                         "guide_high": hi, "deviation": dev,
                         "pct_of_upper_bound": v / hi * 100 if hi else np.nan})
    out = pd.DataFrame(rows)
    out.round(2).to_csv(os.path.join(OUT, "diet_health_proxies_2050.csv"), index=False)
    return out


# ---------------------------------------------------------------- README
def write_readme(ssr_mat, bounds, mts, health):
    core_h = health[health.scenario.isin(CORE)]

    def hv(scen, lab):
        return core_h[(core_h.scenario == scen) & (core_h.indicator.str.startswith(lab))] \
            .value_2050.iloc[0]

    soy = ssr_mat.loc["Soybean"]
    dairy = ssr_mat.loc["Dairy"]
    key_mts = mts[mts.metric.isin([
        "Dietary energy", "Fat energy share", "Red meat intake",
        "CO2 (paper, scenario EF)", "Blue water", "Reactive N", "Diet land (cradle)",
        "World pork price change vs BS", "World soybean price change vs BS",
        "Rest-of-world harvested area", "Global agri CO2 (traded goods)"])]
    lines = [
        "# Post-hoc analyses — China food demand 2050 (Nature Food package)",
        "",
        "Generated by `modules/post_analysis.py` from `results/results_long.csv`, "
        "`results/world/world_results_long.csv` and `results/footprints/*`.",
        "All 2050 values; core scenarios BS / A1 (PTS) / C1 (MTS) / B1 (HDS).",
        "",
        "## 1. Self-sufficiency and trade dependence (`ssr_paths.csv`, "
        "`ssr_2050_matrix.csv`, `import_dependence_soy_dairy.csv`)",
        "",
        f"- Soybean SSR stays critically low in every scenario: 2024 = "
        f"{soy['y2024']:.2f}; 2050 BS = {soy['BS']:.2f}, PTS = {soy['A1']:.2f}, "
        f"MTS = {soy['C1']:.2f}, HDS = {soy['B1']:.2f} — the healthy-diet "
        "transition raises soybean self-sufficiency only marginally because "
        "food-soy demand partially replaces feed-soy demand.",
        f"- Dairy SSR 2050: BS = {dairy['BS']:.2f}, PTS = {dairy['A1']:.2f}, "
        f"MTS = {dairy['C1']:.2f}, HDS = {dairy['B1']:.2f} — dairy is the one "
        "commodity whose import dependence *rises* under the healthy diet "
        "(mirrors the counter-cyclical world milk-powder price, WDM +20% under HDS).",
        "- Staple grains (rice, wheat) move to full self-sufficiency and net-export "
        "pressure under MTS/HDS; maize import dependence falls sharply as feed "
        "demand contracts.",
        "",
        "## 2. Per-capita footprints vs planetary boundaries "
        "(`per_capita_footprints_vs_boundaries.csv`)",
        "",
        "Per-capita shares of EAT-Lancet food-system boundaries at 9.7 bn people "
        "(GHG 5 Gt CO2e, blue water 2,500 km3, N 90 Mt, cropland 1,300 Mha):",
        "",
        "| Indicator | Boundary/cap | BS | PTS | MTS | HDS |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for ind in bounds.indicator.unique():
        b = bounds[bounds.indicator == ind].set_index("scenario")
        lines.append(
            f"| {ind} ({b.unit.iloc[0]}) | {b.boundary_share.iloc[0]:.1f} | "
            + " | ".join(f"{b.loc[s].per_capita_2050:.1f} "
                         f"({b.loc[s].ratio_to_boundary:.2f}x)"
                         for s in ["BS", "A1", "C1", "B1"]) + " |")
    lines += [
        "",
        "Note: farm-gate GHG per capita sits almost exactly on the boundary share "
        "under BS and only diet-driven scenarios move it below; the land metric "
        "uses cradle land incl. pasture (P&N) and is not directly comparable with "
        "the cropland-only boundary — flagged in the csv.",
        "",
        "## 3. MTS efficiency — share of the PTS→HDS dividend realised at half "
        "the transition depth (`mts_efficiency.csv`)",
        "",
        "| Domain | Metric | PTS | MTS | HDS | MTS realisation % |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, r in key_mts.iterrows():
        lines.append(f"| {r.domain} | {r.metric} ({r.unit}) | {r.PTS:.1f} | "
                     f"{r.MTS:.1f} | {r.HDS:.1f} | **{r.MTS_realisation_pct:.0f}** |")
    med = mts.MTS_realisation_pct.median()
    lines += [
        "",
        f"- Median realisation across all {len(mts)} metrics: **{med:.0f}%** — a "
        "50% transition depth secures well over half of every health and global "
        "environmental dividend (declining marginal cost of transition).",
        "- Realisation >100% for fixed-coefficient consumption CO2/land occurs "
        "because HDS's large dairy/aquatic expansion partly offsets its red-meat "
        "cuts, while MTS avoids that rebound.",
        "",
        "## 4. Diet health proxies vs guidelines (`diet_health_proxies_2050.csv`)",
        "",
        "2050, edible g/day (purchase × edible share):",
        "",
        "| Indicator | Guide | BS | PTS | MTS | HDS |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for ind in core_h.indicator.unique():
        g = core_h[core_h.indicator == ind].set_index("scenario")
        lines.append(f"| {ind} | {g.guide_low.iloc[0]:g}-{g.guide_high.iloc[0]:g} "
                     f"{g.unit.iloc[0]} | "
                     + " | ".join(f"{g.loc[s].value_2050:.0f}"
                                  for s in ["BS", "A1", "C1", "B1"]) + " |")
    rm = {s: hv(s, "Red meat") for s in CORE}
    lines += [
        "",
        f"- Red meat: BS {rm['BS']:.0f} and PTS {rm['A1']:.0f} g/d are ~3-4x the "
        f"EAT-Lancet upper bound (28 g/d); MTS {rm['C1']:.0f} g/d roughly halves "
        f"the excess; HDS {rm['B1']:.0f} g/d reaches the healthy range.",
        f"- Fat energy share: PTS {hv('A1','Fat energy'):.0f}%E far above WHO 30%; "
        f"MTS {hv('C1','Fat energy'):.0f}%E; HDS {hv('B1','Fat energy'):.0f}%E.",
        "- Dairy remains below the CDG 300 g/d floor even under HDS "
        f"({hv('B1','Dairy'):.0f} g/d) — the guideline gap that drives the "
        "counter-cyclical global dairy price signal.",
        "",
        "## Files",
        "",
        "- `ssr_paths.csv` — SSR by commodity x year, core scenarios",
        "- `ssr_2050_matrix.csv` — SSR 2050, 14 commodities x 19 scenarios (+2024)",
        "- `import_dependence_soy_dairy.csv` — soybean & dairy import dependence",
        "- `per_capita_footprints_vs_boundaries.csv` — planetary-boundary ratios",
        "- `mts_efficiency.csv` — full MTS dividend-realisation table",
        "- `diet_health_proxies_2050.csv` — guideline deviations, all 19 scenarios",
    ]
    with open(os.path.join(OUT, "README.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    df = load_long()
    cfp = load_china_fp()
    wfp = load_world_fp()
    wl = load_world_long()
    _, ssr_mat = analysis_ssr(df)
    bounds = analysis_boundaries(df, cfp)
    mts = analysis_mts(df, cfp, wfp, wl)
    health = analysis_health(df)
    write_readme(ssr_mat, bounds, mts, health)
    print("post_analysis done ->", OUT)
    print(mts[["domain", "metric", "MTS_realisation_pct"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
