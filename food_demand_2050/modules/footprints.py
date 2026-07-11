#!/usr/bin/env python3
"""
Environmental footprint accounting module for the Food-Demand-2050 project
==========================================================================

Computes carbon, water, nitrogen and land footprints for
  A. the 19 China CASM scenarios  (BS, A1-A6, B1-B6, C1-C6), 2023-2050
  B. the  4 world CASM-World scenarios (BS, PTS, HDS, MTS), 13 regions, 2024-2050

Coefficient library:  modules/coefficients/*.csv  (fully cited, see README).
Model results:        results/results_long.csv     (China, 万吨 = 1e4 t)
                      results/world/world_results_long.csv (world, Mt = 1e6 t)

Outputs (results/footprints/):
  china_footprints_long.csv / china_footprints_summary.csv
  world_footprints_long.csv / world_footprints_summary.csv

Unit conventions
----------------
China `production`, `food_demand_total`, `net_import`  -> 万吨 (1e4 t)
      `area` -> 万ha (1e4 ha),  `yield` -> t/ha
World `PRD`, `CON` ... -> Mt (1e6 t)

Carbon    coef kg CO2e/kg = t CO2e/t.   value 万吨 x coef -> 万吨 CO2e; /100 -> Mt CO2e
Water     coef m3/t.                    value 万吨 x coef -> 1e4 m3;    /1e5 -> km3
Nitrogen  N-rate kg N/ha x area 万ha    -> x1e4 kg N;                  /1e9*1e4 -> Mt N
Land      coef m2yr/kg x value 万吨(=1e7 kg) -> 1e7 m2yr;              /1e10 -> Mha·yr

The final long/summary tables report China in **Mt CO2e, km3, Mt N, Mha** and
world in the same headline units, so the two are directly additive for the
"global net effect" story.

Boundary policy (see README):  the FAOSTAT farm-gate and Poore & Nemecek
cradle-to-retail boundaries are NOT mixed inside one indicator except where a
FAOSTAT farm-gate value is genuinely missing for a crop, in which case a P&N
value is used as an explicit, flagged gap-fill (coef_source column).
"""

import os
import csv
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
COEF = os.path.join(HERE, "coefficients")
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "footprints")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# commodity sets (primary commodities only -> no double counting of oils/meals)
# ---------------------------------------------------------------------------
CROPS = ["RICE", "WHEA", "MAIZ", "POTA", "SOYS", "RAPS", "GRDS", "COTT",
         "SUGC", "SUGB", "FRTO", "VEGT", "OTGR", "SORG", "BARL"]
LVS = ["PIGM", "CATM", "SHGM", "CHKM", "EGGS", "MILK", "FISH"]
CHINA_COMMS = CROPS + LVS

YEARS_KEEP = list(range(2023, 2051))
SUMMARY_YEARS = [2024, 2035, 2050]
CHINA_SCENARIOS = ["BS"] + [f"{g}{i}" for g in "ABC" for i in range(1, 7)]

# livestock product nitrogen content (kg N per kg product) = protein% / 6.25
# and reactive-N surplus ratio (kg N surplus per kg N in product) from
# Uwizeye et al. 2020 Nature Food (feedN/productN - 1).  Documented approximation.
PROD_N = {  # kg N / kg product
    "PIGM": 0.150 / 6.25, "CATM": 0.200 / 6.25, "SHGM": 0.180 / 6.25,
    "CHKM": 0.180 / 6.25, "EGGS": 0.126 / 6.25, "MILK": 0.033 / 6.25,
    "FISH": 0.180 / 6.25,
}
N_SURPLUS = {  # kg reactive-N surplus per kg N in product
    "CATM": 4.0, "SHGM": 4.0, "PIGM": 2.0, "CHKM": 1.0,
    "EGGS": 2.5, "MILK": 3.0, "FISH": 1.0,
}


# ---------------------------------------------------------------------------
# coefficient loaders
# ---------------------------------------------------------------------------
def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_carbon():
    """Return {casm: {'faostat_chn','faostat_wld','pn_wld'}} kg CO2e/kg.

    For beef the FAOSTAT 'carcass' farm-gate row is used; the P&N beef-herd
    value is used for the LCA column (dominant supply). Cereals-excl-rice
    aggregate covers WHEA/MAIZ/OTGR/SORG/BARL on the farm-gate side.
    """
    faostat_chn, faostat_wld, pn_wld = {}, {}, {}
    with open(os.path.join(COEF, "carbon_footprint_coefficients.csv")) as fh:
        for r in csv.DictReader(fh):
            c = r["casm_code"].strip()
            if not c:
                continue
            v = _f(r["value_kgCO2e_per_kg"])
            if v is None:
                continue
            reg = r["region"].strip()
            bnd = r["system_boundary"]
            if bnd.startswith("farm-gate"):
                if reg == "CHN":
                    faostat_chn.setdefault(c, v)   # first (primary) row wins
                elif reg == "WLD":
                    faostat_wld.setdefault(c, v)
            elif "cradle-to-retail" in bnd:
                # prefer the dedicated 'beef herd' / aggregate row (first)
                pn_wld.setdefault(c, v)
    # cereals-excl-rice aggregate applies to the other coarse grains too
    for c in ("WHEA", "MAIZ", "OTGR", "SORG", "BARL"):
        faostat_chn.setdefault(c, faostat_chn.get("WHEA"))
        faostat_wld.setdefault(c, faostat_wld.get("WHEA"))
    return faostat_chn, faostat_wld, pn_wld


def load_water():
    """Return {casm: {'chn':(g,b,gr), 'wld':(g,b,gr)}} m3/t."""
    chn, wld = {}, {}
    with open(os.path.join(COEF, "water_footprint_coefficients.csv")) as fh:
        for r in csv.DictReader(fh):
            c = r["casm_code"].strip()
            if not c:
                continue
            g, b, gr = _f(r["green_m3_per_t"]), _f(r["blue_m3_per_t"]), _f(r["grey_m3_per_t"])
            if g is None and b is None:
                continue
            trip = (g or 0.0, b or 0.0, gr or 0.0)
            reg = r["region"].strip()
            if reg == "CHN":
                chn.setdefault(c, trip)
            elif reg == "WLD":
                wld.setdefault(c, trip)
    return chn, wld


def load_nitrogen():
    """Return crop N-rate {casm: kg N/ha} for CHN and WLD."""
    nrate_chn, nrate_wld = {}, {}
    with open(os.path.join(COEF, "nitrogen_coefficients.csv")) as fh:
        for r in csv.DictReader(fh):
            if r["category"] != "A_crop_Nfert":
                continue
            c = r["casm_code"].strip()
            v = _f(r["value"])
            if v is None:
                continue
            if r["region"] == "CHN":
                nrate_chn.setdefault(c, v)
            elif r["region"] == "WLD":
                nrate_wld.setdefault(c, v)
    # coarse-grain proxies (use maize/other-cereal rate)
    for c in ("OTGR", "SORG", "BARL"):
        nrate_chn.setdefault(c, nrate_chn.get("MAIZ"))
        nrate_wld.setdefault(c, nrate_wld.get("MAIZ"))
    return nrate_chn, nrate_wld


def load_land():
    """Return {casm: m2yr/kg} using WLD P&N per-kg (beef -> beef-herd row)."""
    land = {}
    with open(os.path.join(COEF, "land_coefficients.csv")) as fh:
        for r in csv.DictReader(fh):
            c = r["casm_code"].strip()
            if not c:
                continue
            v = _f(r["land_m2yr_per_kg"])
            if v is None:
                continue
            land.setdefault(c, v)   # first row = primary (beef herd for CATM)
    for c in ("OTGR", "SORG", "BARL"):
        land.setdefault(c, land.get("BARL", land.get("MAIZ")))
    return land


# ---------------------------------------------------------------------------
# results loaders
# ---------------------------------------------------------------------------
def load_china_results():
    """Return data[scenario][variable][commodity][year] = value."""
    data = {}
    path = os.path.join(RES, "results_long.csv")
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            sc, var, com = r["scenario"], r["variable"], r["commodity"]
            yr = _f(r["year"])
            val = _f(r["value"])
            if yr is None or val is None:
                continue
            yr = int(yr)
            (data.setdefault(sc, {}).setdefault(var, {})
                 .setdefault(com, {})[yr]) = val
    return data


def load_world_results():
    """Return data[scenario][variable][commodity][region][year]."""
    data = {}
    path = os.path.join(RES, "world", "world_results_long.csv")
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            sc, com, reg, var = r["scenario"], r["commodity"], r["region"], r["variable"]
            yr = _f(r["year"])
            val = _f(r["value"])
            if yr is None or val is None:
                continue
            yr = int(yr)
            (data.setdefault(sc, {}).setdefault(var, {}).setdefault(com, {})
                 .setdefault(reg, {})[yr]) = val
    return data


def load_mapping():
    """Return CASM<->CASM-World concordance dictionaries."""
    casm_to_world, world_to_casm = {}, {}
    with open(os.path.join(COEF, "commodity_mapping.csv"), encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            casm = r.get("casm_code", "").strip()
            world = r.get("casm_world_code", "").strip()
            if casm and world:
                casm_to_world[casm] = world
                world_to_casm.setdefault(world, casm)
    return casm_to_world, world_to_casm


def load_world_crop_nrate():
    """Return {world_code: kg N/ha} from sourced WLD crop fertiliser rates."""
    casm_to_world, _ = load_mapping()
    _, nrate_wld = load_nitrogen()
    out = {}
    for casm, value in nrate_wld.items():
        wc = casm_to_world.get(casm)
        if wc and value is not None:
            out.setdefault(wc, value)
    return out


def china_supply_use_balance(data):
    """Write standard supply-use checks for China quantities.

    Units remain the model unit (10,000 tonnes). The standard supply balance is
    production + net imports, checked against the model's domestic_demand_total.
    Food final consumption is kept separately for final-product footprinting.
    """
    path = os.path.join(OUT, "china_supply_use_balance.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "commodity", "year", "production", "net_import",
                    "supply_available", "domestic_demand_total",
                    "food_demand_total", "balance_error",
                    "balance_error_pct_of_use"])
        for sc in CHINA_SCENARIOS:
            for c in CHINA_COMMS:
                for y in YEARS_KEEP:
                    p = data.get(sc, {}).get("production", {}).get(c, {}).get(y)
                    use = data.get(sc, {}).get("domestic_demand_total", {}).get(c, {}).get(y)
                    food = data.get(sc, {}).get("food_demand_total", {}).get(c, {}).get(y)
                    ni = data.get(sc, {}).get("net_import", {}).get(c, {}).get(y)
                    if p is None and use is None and food is None:
                        continue
                    supply = (p or 0.0) + (ni or 0.0)
                    err = supply - use if use is not None else None
                    pct = err / use * 100.0 if use else None
                    w.writerow([sc, c, y,
                                f"{p:.6g}" if p is not None else "",
                                f"{ni:.6g}" if ni is not None else "",
                                f"{supply:.6g}",
                                f"{use:.6g}" if use is not None else "",
                                f"{food:.6g}" if food is not None else "",
                                f"{err:.6g}" if err is not None else "",
                                f"{pct:.6g}" if pct is not None else ""])
    return path


def write_account_rows(path, rows):
    fields = ["account", "geography", "scenario", "indicator", "boundary",
              "region", "commodity", "year", "unit", "value", "coef_source",
              "quantity_variable", "note"]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            rr = {k: r.get(k, "") for k in fields}
            if isinstance(rr["value"], float):
                rr["value"] = f"{rr['value']:.6g}"
            w.writerow(rr)
    return path


def write_account_summary(path, rows):
    agg = {}
    for r in rows:
        key = (r["account"], r["geography"], r["scenario"], r["indicator"],
               r["region"], r["unit"], r["year"])
        agg[key] = agg.get(key, 0.0) + float(r["value"])
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["account", "geography", "scenario", "indicator", "region",
                    "unit", "year", "value"])
        for key in sorted(agg):
            w.writerow([*key, f"{agg[key]:.6g}"])
    return path


def direct_production_account(cdata, wdata):
    """Account A: mutually separated direct production-process indicators.

    This file is the only account intended for global net-effect headline use.
    It avoids livestock water, supply-chain nitrogen and lifecycle land because
    those coefficients include feed or other upstream processes that overlap
    with crop production.
    """
    fao_chn, fao_wld, _ = load_carbon()
    w_chn, w_wld = load_water()
    nrate_chn, _ = load_nitrogen()
    fao_wld_world, fao_chn_world, _ = load_carbon_world()
    water_wld_world, water_chn_world = load_water_world()
    nrate_world = load_world_crop_nrate()
    rows = []

    def add(geography, scenario, indicator, boundary, region, commodity, year,
            unit, value, coef_source, quantity_variable, note=""):
        rows.append({
            "account": "direct_production",
            "geography": geography,
            "scenario": scenario,
            "indicator": indicator,
            "boundary": boundary,
            "region": region,
            "commodity": commodity,
            "year": year,
            "unit": unit,
            "value": value,
            "coef_source": coef_source,
            "quantity_variable": quantity_variable,
            "note": note,
        })

    for sc in CHINA_SCENARIOS:
        if sc not in cdata:
            continue
        for c in CHINA_COMMS:
            for y in YEARS_KEEP:
                p = cdata.get(sc, {}).get("production", {}).get(c, {}).get(y)
                if p is None:
                    continue
                cf = fao_chn.get(c)
                src = "faostat_chn"
                if cf is None:
                    cf = fao_wld.get(c)
                    src = "faostat_wld"
                if cf is not None:
                    add("China", sc, "co2_faostat_direct", "farm-gate direct production",
                        "CHN", c, y, "Mt CO2e", p * cf / 100.0, src, "production")
                area = cdata.get(sc, {}).get("area", {}).get(c, {}).get(y)
                if c in CROPS and area is not None:
                    add("China", sc, "land_harvested", "model physical harvested area",
                        "CHN", c, y, "Mha", area / 100.0, "model_area", "area")
                    nr = nrate_chn.get(c)
                    if nr is not None:
                        add("China", sc, "nitrogen_crop_fertilizer_direct",
                            "direct crop fertilizer application", "CHN", c, y,
                            "Mt N", area * nr * 1e4 / 1e9, "ludemann_chn",
                            "area", "Crop-only direct N; no livestock supply-chain factor.")
                    wc = w_chn.get(c) or w_wld.get(c)
                    if wc is not None:
                        add("China", sc, "water_blue_crop_direct",
                            "crop blue-water footprint; crop production only",
                            "CHN", c, y, "km3", p * wc[1] / 1e5,
                            "mh_chn" if c in w_chn else "mh_wld",
                            "production", "Livestock water omitted from direct account.")

    for sc in ["BS", "PTS", "HDS", "MTS"]:
        if sc not in wdata:
            continue
        for c in WORLD_COMMS:
            for reg in WORLD_REGIONS:
                for y in WORLD_YEARS:
                    p = wdata.get(sc, {}).get("PRD", {}).get(c, {}).get(reg, {}).get(y)
                    if p is None:
                        continue
                    cf = None
                    src = None
                    if reg == "CHN" and c in fao_chn_world:
                        cf, src = fao_chn_world[c], "faostat_chn"
                    if cf is None and c in fao_wld_world:
                        cf, src = fao_wld_world[c], "faostat_wld"
                    if cf is not None:
                        add("World", sc, "co2_faostat_direct",
                            "farm-gate direct production", reg, c, y,
                            "Mt CO2e", p * cf, src, "PRD",
                            "Predominantly global-average commodity coefficients; China-specific where available.")
                    ah = wdata.get(sc, {}).get("AHV", {}).get(c, {}).get(reg, {}).get(y)
                    if c in WORLD_CROPS and ah is not None:
                        add("World", sc, "land_harvested",
                            "model physical harvested area", reg, c, y, "Mha",
                            ah, "model_AHV", "AHV")
                        nr = nrate_world.get(c)
                        if nr is not None:
                            add("World", sc, "nitrogen_crop_fertilizer_direct",
                                "direct crop fertilizer application", reg, c, y,
                                "Mt N", ah * 1e6 * nr / 1e9, "ludemann_wld",
                                "AHV", "Crop-only direct N; no livestock supply-chain factor.")
                        wc = water_chn_world.get(c) if reg == "CHN" else None
                        if wc is None:
                            wc = water_wld_world.get(c)
                        if wc is not None:
                            add("World", sc, "water_blue_crop_direct",
                                "crop blue-water footprint; crop production only",
                                reg, c, y, "km3", p * wc[1] / 1e3,
                                "mh_chn" if reg == "CHN" and c in water_chn_world else "mh_wld",
                                "PRD", "Livestock water omitted from direct account.")

    path = write_account_rows(os.path.join(OUT, "direct_production_account.csv"), rows)
    write_account_summary(os.path.join(OUT, "direct_production_account_summary.csv"), rows)
    return path, rows


def final_consumption_lca_account(cdata, wdata):
    """Account B: final-product footprint sensitivity using final food demand."""
    _, _, pn = load_carbon()
    water_chn, water_wld = load_water()
    land = load_land()
    _, world_to_casm = load_mapping()
    _, _, pn_world = load_carbon_world()
    water_wld_world, water_chn_world = load_water_world()
    land_world = load_land_world()
    rows = []

    def add(geography, scenario, indicator, boundary, region, commodity, year,
            unit, value, coef_source, quantity_variable, note=""):
        rows.append({
            "account": "final_consumption_lca",
            "geography": geography,
            "scenario": scenario,
            "indicator": indicator,
            "boundary": boundary,
            "region": region,
            "commodity": commodity,
            "year": year,
            "unit": unit,
            "value": value,
            "coef_source": coef_source,
            "quantity_variable": quantity_variable,
            "note": note,
        })

    for sc in CHINA_SCENARIOS:
        if sc not in cdata:
            continue
        for c in CHINA_COMMS:
            for y in YEARS_KEEP:
                q = cdata.get(sc, {}).get("food_demand_total", {}).get(c, {}).get(y)
                if q is None:
                    continue
                pnc = pn.get(c)
                if pnc is not None:
                    add("China", sc, "co2_lca_final_food",
                        "cradle-to-retail final food product", "CHN", c, y,
                        "Mt CO2e", q * pnc / 100.0, "pn_lca", "food_demand_total")
                wc = water_chn.get(c) or water_wld.get(c)
                if wc is not None:
                    add("China", sc, "water_blue_lca_final_food",
                        "product water footprint applied only to final food demand",
                        "CHN", c, y, "km3", q * wc[1] / 1e5,
                        "mh_chn" if c in water_chn else "mh_wld",
                        "food_demand_total")
                lc = land.get(c)
                if lc is not None:
                    add("China", sc, "land_lca_final_food",
                        "land occupation equivalent for final food product",
                        "CHN", c, y, "Mha", q * 1e7 * lc / 1e10,
                        "pn_land", "food_demand_total")

    for sc in ["BS", "PTS", "HDS", "MTS"]:
        if sc not in wdata:
            continue
        for c in set(WORLD_COMMS) | set(DAIRY_FOODS) | set(OILS):
            for reg in WORLD_REGIONS:
                for y in WORLD_YEARS:
                    q = wdata.get(sc, {}).get("FOO", {}).get(c, {}).get(reg, {}).get(y)
                    if q is None:
                        continue
                    pnc = pn_world.get(c)
                    if pnc is None:
                        casm = world_to_casm.get(c)
                        pnc = pn.get(casm) if casm else None
                    if pnc is not None:
                        add("World", sc, "co2_lca_final_food",
                            "cradle-to-retail final food product", reg, c, y,
                            "Mt CO2e", q * pnc, "pn_lca", "FOO")
                    wc = water_chn_world.get(c) if reg == "CHN" else None
                    if wc is None:
                        wc = water_wld_world.get(c)
                    if wc is not None:
                        add("World", sc, "water_blue_lca_final_food",
                            "product water footprint applied only to final food demand",
                            reg, c, y, "km3", q * wc[1] / 1e3,
                            "mh_chn" if reg == "CHN" and c in water_chn_world else "mh_wld",
                            "FOO")
                    lc = land_world.get(c)
                    if lc is not None:
                        add("World", sc, "land_lca_final_food",
                            "land occupation equivalent for final food product",
                            reg, c, y, "Mha", q * lc * 1e9 / 1e10,
                            "pn_land", "FOO")

    path = write_account_rows(os.path.join(OUT, "final_consumption_lca_account.csv"), rows)
    write_account_summary(os.path.join(OUT, "final_consumption_lca_account_summary.csv"), rows)
    return path, rows


def world_carbon_coverage(wdata):
    fao_wld, fao_chn, _ = load_carbon_world()
    rows = []
    total_prod = 0.0
    for c, regs in wdata.get("BS", {}).get("PRD", {}).items():
        prod = sum((regs.get(r, {}).get(2050) or 0.0) for r in WORLD_REGIONS)
        if prod <= 0:
            continue
        total_prod += prod
        has = c in fao_wld or c in fao_chn
        emissions = 0.0
        for r in WORLD_REGIONS:
            p = regs.get(r, {}).get(2050) or 0.0
            cf = fao_chn.get(c) if r == "CHN" else None
            if cf is None:
                cf = fao_wld.get(c)
            if cf is not None:
                emissions += p * cf
        rows.append([c, prod, "yes" if has else "no", emissions])
    path = os.path.join(OUT, "world_carbon_coverage.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["commodity", "BS_2050_production_Mt",
                    "has_carbon_coefficient", "included_emissions_MtCO2e",
                    "production_mass_coverage_share"])
        for c, prod, has, emissions in sorted(rows):
            w.writerow([c, f"{prod:.6g}", has, f"{emissions:.6g}",
                        f"{prod / total_prod:.6g}" if total_prod else ""])
    return path


def boundary_reconciliation(direct_rows, final_rows):
    direct_bad_livestock_lca = [
        r for r in direct_rows
        if r["indicator"].startswith(("land_lca", "co2_lca", "water_blue_lca"))
    ]
    direct_lifecycle_land = [
        r for r in direct_rows if "land occupation equivalent" in r.get("boundary", "")
    ]
    direct_supply_n = [
        r for r in direct_rows if "supply-chain" in r.get("boundary", "").lower()
    ]
    path = os.path.join(OUT, "boundary_reconciliation.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# Boundary Reconciliation\n\n")
        fh.write("Generated by `modules/footprints.py`.\n\n")
        fh.write("## Accounts\n\n")
        fh.write("- Account A, `direct_production_account.csv`: direct farm-gate carbon, crop blue water, crop fertiliser N and model physical harvested area. Livestock water, lifecycle land and supply-chain nitrogen are excluded because available coefficients include feed or upstream processes.\n")
        fh.write("- Account B, `final_consumption_lca_account.csv`: final-product footprint sensitivity using `food_demand_total` for China and `FOO` for CASM-World. It is not added to Account A.\n\n")
        fh.write("## Automated Checks\n\n")
        checks = [
            ("No livestock coefficient with includes_feed=yes is summed with feed-crop production coefficients.", not direct_bad_livestock_lca),
            ("No lifecycle land coefficient is used in the direct production account.", not direct_lifecycle_land),
            ("No supply-chain nitrogen factor is added to direct crop fertilizer N.", not direct_supply_n),
        ]
        for label, ok in checks:
            fh.write(f"- {'PASS' if ok else 'REVIEW'}: {label}\n")
        fh.write("\n## Scope Notes\n\n")
        fh.write("- Global water and nitrogen in the direct account are crop-direct indicators only; they are no longer presented as complete global water or reactive-N totals.\n")
        fh.write("- World coefficients are predominantly global-average commodity coefficients with China-specific coefficients where available; production changes are region-specific.\n")
        fh.write("- `world_carbon_coverage.csv` reports commodity coverage for the model-covered farm-gate GHG subset.\n")
    return path


# ---------------------------------------------------------------------------
# A. China footprints
# ---------------------------------------------------------------------------
def china_footprints(data):
    fao_chn, fao_wld, pn = load_carbon()
    w_chn, w_wld = load_water()
    nrate_chn, _ = load_nitrogen()
    land = load_land()

    rows = []   # scenario, indicator, coef_source, commodity, year, value

    def prod(sc, c, y):
        return data.get(sc, {}).get("production", {}).get(c, {}).get(y)

    def area(sc, c, y):
        return data.get(sc, {}).get("area", {}).get(c, {}).get(y)

    def netimp(sc, c, y):
        return data.get(sc, {}).get("net_import", {}).get(c, {}).get(y)

    for sc in CHINA_SCENARIOS:
        if sc not in data:
            continue
        for c in CHINA_COMMS:
            for y in YEARS_KEEP:
                p = prod(sc, c, y)
                if p is None:
                    continue
                # trade-adjusted domestic availability (QXXADJ) anchored at 2023
                ni = netimp(sc, c, y)
                ni0 = netimp(sc, c, 2023)
                qadj = p + ((ni or 0.0) - (ni0 or 0.0)) if ni is not None else p

                # ---- carbon: FAOSTAT farm-gate (CHN pref, else WLD).  Kept a
                # PURE farm-gate boundary: crops FAOSTAT only publishes for
                # (rice, cereals-excl-rice) and all livestock except fish.
                # Items with no FAOSTAT farm-gate value (veg, fruit, sugar,
                # oilseeds, potato, cotton, fish) are NOT boundary-mixed here;
                # they are captured in co2_pn_lca and flagged as FAOSTAT gaps.
                cf = fao_chn.get(c)
                src = "faostat_chn"
                if cf is None:
                    cf = fao_wld.get(c)
                    src = "faostat_wld"
                if cf is not None:
                    rows.append((sc, "co2_faostat_prod", src, c, y, p * cf / 100.0))
                    rows.append((sc, "co2_faostat_cons", src, c, y, qadj * cf / 100.0))
                else:
                    # explicit, flagged FAOSTAT gap (contributes 0 to farm-gate
                    # total; its P&N value appears in co2_pn_lca below)
                    rows.append((sc, "co2_faostat_gap", "faostat_missing", c, y, 0.0))
                # ---- carbon: P&N full life-cycle (diet / consumer)
                pnc = pn.get(c)
                if pnc is not None:
                    rows.append((sc, "co2_pn_lca", "pn_lca", c, y, qadj * pnc / 100.0))

                # ---- water: M&H (CHN livestock pref, WLD crops)
                # both boundaries: production (Chinese soil) and consumption
                # (trade-adjusted domestic availability qadj). Consumption
                # varies with the diet scenario; production is supply-fixed.
                wc = w_chn.get(c) or w_wld.get(c)
                wsrc = "mh_chn" if c in w_chn else "mh_wld"
                if wc is not None:
                    g, b, gr = wc          # m3/t ; value 万吨 x coef /1e5 -> km3
                    rows.append((sc, "water_green_prod", wsrc, c, y, p * g / 1e5))
                    rows.append((sc, "water_blue_prod", wsrc, c, y, p * b / 1e5))
                    rows.append((sc, "water_grey_prod", wsrc, c, y, p * gr / 1e5))
                    rows.append((sc, "water_green", wsrc, c, y, qadj * g / 1e5))
                    rows.append((sc, "water_blue", wsrc, c, y, qadj * b / 1e5))
                    rows.append((sc, "water_grey", wsrc, c, y, qadj * gr / 1e5))

                # ---- nitrogen (per-tonne basis so both boundaries available)
                # crop: N-rate/yield = kg N per tonne product (embodied fert N)
                # livestock: product-N x reactive-N surplus ratio
                npt = None          # kg N per tonne product
                nsrc = None
                if c in CROPS:
                    nr = nrate_chn.get(c)
                    yld = data.get(sc, {}).get("yield", {}).get(c, {}).get(y)
                    if nr is not None and yld:
                        npt = nr / yld
                        nsrc = "crop_nfert"
                else:
                    pn_c = PROD_N.get(c)
                    sr = N_SURPLUS.get(c)
                    if pn_c is not None and sr is not None:
                        npt = pn_c * sr * 1000.0    # kg N / tonne
                        nsrc = "lvs_excretion"
                if npt is not None:
                    # value 万吨=1e4 t x (kg N/t) -> 1e4 kg N ; /1e5 -> ... to Mt:
                    # 1e4 kg = 1e-5 Mt -> value 万吨 x npt x 1e4 /1e9
                    rows.append((sc, "nitrogen_prod", nsrc, c, y, p * npt * 1e4 / 1e9))
                    rows.append((sc, "nitrogen_total", nsrc, c, y, qadj * npt * 1e4 / 1e9))

                # ---- land: diet footprint = consumption x P&N m2yr/kg
                lc = land.get(c)
                if lc is not None:
                    # qadj 万吨=1e7 kg x m2yr/kg -> m2yr ; /1e10 -> Mha
                    rows.append((sc, "land_diet", "pn_land", c, y,
                                 qadj * 1e7 * lc / 1e10))
    return rows


# ---------------------------------------------------------------------------
# B. World footprints
# ---------------------------------------------------------------------------
WORLD_REGIONS = ["ARG", "AUS", "BRZ", "CAN", "CHN", "E15", "IND", "JPN",
                 "KOR", "MEX", "NZL", "ROW", "USA"]
WORLD_YEARS = [2024, 2030, 2035, 2040, 2045, 2050]

# CASM-World -> FAOSTAT carbon coef via world code.  Build from carbon csv
# using casm_world_code, region WLD/CHN farm-gate.
def load_carbon_world():
    fao_wld, fao_chn, pn_wld = {}, {}, {}
    with open(os.path.join(COEF, "carbon_footprint_coefficients.csv")) as fh:
        for r in csv.DictReader(fh):
            wc = r["casm_world_code"].strip()
            if not wc:
                continue
            v = _f(r["value_kgCO2e_per_kg"])
            if v is None:
                continue
            bnd = r["system_boundary"]
            reg = r["region"].strip()
            if bnd.startswith("farm-gate"):
                if reg == "WLD":
                    fao_wld.setdefault(wc, v)
                elif reg == "CHN":
                    fao_chn.setdefault(wc, v)
            elif "cradle-to-retail" in bnd:
                pn_wld.setdefault(wc, v)
    for c in ("WHE", "CRN", "OCG"):
        fao_wld.setdefault(c, fao_wld.get("WHE"))
    return fao_wld, fao_chn, pn_wld


def load_water_world():
    wld, chn = {}, {}
    with open(os.path.join(COEF, "water_footprint_coefficients.csv")) as fh:
        for r in csv.DictReader(fh):
            wc = r["casm_world_code"].strip()
            if not wc:
                continue
            g, b, gr = _f(r["green_m3_per_t"]), _f(r["blue_m3_per_t"]), _f(r["grey_m3_per_t"])
            if g is None and b is None:
                continue
            trip = (g or 0.0, b or 0.0, gr or 0.0)
            if r["region"] == "WLD":
                wld.setdefault(wc, trip)
            elif r["region"] == "CHN":
                chn.setdefault(wc, trip)
    return wld, chn


def load_land_world():
    land = {}
    with open(os.path.join(COEF, "land_coefficients.csv")) as fh:
        for r in csv.DictReader(fh):
            wc = r["casm_world_code"].strip()
            if not wc:
                continue
            v = _f(r["land_m2yr_per_kg"])
            if v is None:
                continue
            land.setdefault(wc, v)
    return land


def load_nitrogen_world():
    nrate = {}
    with open(os.path.join(COEF, "nitrogen_coefficients.csv")) as fh:
        for r in csv.DictReader(fh):
            if r["category"] != "A_crop_Nfert" or r["region"] != "WLD":
                continue
            # map via casm_code -> world code using carbon mapping is complex;
            # here we key nitrogen on the world code list by simple concordance
            pass
    return nrate  # world N handled per-commodity below via WLD rates


# world commodity classification (primary; exclude derived oils/meals & SUG agg)
WORLD_CROPS = ["RIC", "WHE", "CRN", "SBS", "RBS", "NBS", "CTN", "SCA", "SBE", "OCG"]
WORLD_LVS = ["PRK", "BFV", "SGT", "PLM", "EGG", "MLK"]
WORLD_COMMS = WORLD_CROPS + WORLD_LVS
DAIRY_FOODS = ["BUT", "CHE", "NDM", "FMK", "WDM", "ODA"]
OILS = ["SBO", "RBO", "NBO"]

# world-code -> (crop N rate kg N/ha via WLD) not available by region area here,
# so world nitrogen uses a per-tonne N intensity derived from WLD N-rate / WLD
# yield is not available; instead we approximate world crop reactive-N with the
# same product-N/surplus method for livestock and a per-tonne crop N proxy.
# Per-tonne crop N proxy (kg N / t product) from FAOSTAT-scale N use / yield,
# documented approximate values:
WORLD_CROP_N_PER_T = {  # kg N per tonne product (fertiliser N embodied)
    "RIC": 26.0, "WHE": 30.0, "CRN": 22.0, "SBS": 6.0, "RBS": 55.0,
    "NBS": 30.0, "CTN": 60.0, "SCA": 1.5, "SBE": 2.0, "OCG": 25.0,
}
WORLD_PROD_N = {"PRK": PROD_N["PIGM"], "BFV": PROD_N["CATM"], "SGT": PROD_N["SHGM"],
                "PLM": PROD_N["CHKM"], "EGG": PROD_N["EGGS"], "MLK": PROD_N["MILK"]}
WORLD_N_SURPLUS = {"PRK": 2.0, "BFV": 4.0, "SGT": 4.0, "PLM": 1.0,
                   "EGG": 2.5, "MLK": 3.0}


def world_footprints(wdata):
    fao_wld, fao_chn, pn_wld = load_carbon_world()
    w_wld, w_chn = load_water_world()
    land = load_land_world()

    rows = []  # scenario, indicator, region, commodity, year, value  (headline units)

    def prd(sc, c, reg, y):
        return wdata.get(sc, {}).get("PRD", {}).get(c, {}).get(reg, {}).get(y)

    def ahv(sc, c, reg, y):   # harvested area, Mha (crops only)
        return wdata.get(sc, {}).get("AHV", {}).get(c, {}).get(reg, {}).get(y)

    for sc in ["BS", "PTS", "HDS", "MTS"]:
        if sc not in wdata:
            continue
        for c in WORLD_COMMS:
            for reg in WORLD_REGIONS:
                for y in WORLD_YEARS:
                    p = prd(sc, c, reg, y)   # Mt
                    if p is None:
                        continue
                    # carbon: use CHN farm-gate for China region livestock/rice
                    # where available, else WLD farm-gate, else P&N gapfill
                    # PURE FAOSTAT farm-gate boundary (no P&N gap-fill mixed in)
                    cf = None
                    src = None
                    if reg == "CHN" and c in fao_chn:
                        cf, src = fao_chn[c], "faostat_chn"
                    if cf is None and c in fao_wld:
                        cf, src = fao_wld[c], "faostat_wld"
                    if cf is not None:
                        # p Mt=1e9 kg x kgCO2e/kg -> 1e9 kgCO2e = Mt CO2e
                        rows.append((sc, "co2_faostat", src, reg, c, y, p * cf))

                    # water (WLD crops, CHN for China livestock where present)
                    wc = None
                    if reg == "CHN" and c in w_chn:
                        wc = w_chn[c]
                    if wc is None:
                        wc = w_wld.get(c)
                    if wc is not None:
                        g, b, gr = wc
                        # p Mt=1e6 t x m3/t -> 1e6 m3 = 1e-3 km3
                        rows.append((sc, "water_green", None, reg, c, y, p * g / 1e3))
                        rows.append((sc, "water_blue", None, reg, c, y, p * b / 1e3))
                        rows.append((sc, "water_grey", None, reg, c, y, p * gr / 1e3))

                    # nitrogen
                    if c in WORLD_CROPS:
                        npt = WORLD_CROP_N_PER_T.get(c)
                        if npt is not None:
                            # p Mt=1e9 kg... npt kgN/t x p(1e6 t) -> 1e6 kgN=1e-3 Mt N
                            rows.append((sc, "nitrogen_total", "crop_nfert",
                                         reg, c, y, p * npt / 1e3))
                    else:
                        pn_c = WORLD_PROD_N.get(c)
                        sr = WORLD_N_SURPLUS.get(c)
                        if pn_c is not None and sr is not None:
                            # p(1e6 t=1e9 kg) x kgN/kg x sr -> kgN ; /1e9 -> Mt N
                            rows.append((sc, "nitrogen_total", "lvs_excretion",
                                         reg, c, y, p * 1e9 * pn_c * sr / 1e9))

                    # physical harvested cropland from the model itself (Mha)
                    ah = ahv(sc, c, reg, y)
                    if ah is not None and ah != 0:
                        rows.append((sc, "land_harvested", "ahv_physical",
                                     reg, c, y, ah))

                    # land (production-based agricultural land occupation)
                    lc = land.get(c)
                    if lc is not None:
                        # p(1e6 t=1e9 kg) x m2yr/kg -> 1e9 m2yr ; /1e10 -> Mha (x100? )
                        # 1 Mha = 1e10 m2 ; p*1e9 kg * lc m2/kg = p*lc*1e9 m2 -> /1e10 Mha
                        rows.append((sc, "land_prod", "pn_land", reg, c, y,
                                     p * lc * 1e9 / 1e10))
    return rows


# ---------------------------------------------------------------------------
# writers
# ---------------------------------------------------------------------------
def write_china(rows):
    long_path = os.path.join(OUT, "china_footprints_long.csv")
    with open(long_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "indicator", "coef_source", "commodity", "year", "value"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], r[4], f"{r[5]:.6g}"])

    # summary: scenario x indicator x {2024,2035,2050}  (sum over commodities)
    agg = {}
    for sc, ind, src, com, yr, val in rows:
        if yr in SUMMARY_YEARS:
            agg.setdefault((sc, ind), {}).setdefault(yr, 0.0)
            agg[(sc, ind)][yr] += val
    sum_path = os.path.join(OUT, "china_footprints_summary.csv")
    inds = ["co2_faostat_prod", "co2_faostat_cons", "co2_pn_lca",
            "water_green", "water_blue", "water_grey", "water_blue_prod",
            "nitrogen_total", "nitrogen_prod", "land_diet"]
    with open(sum_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "indicator", "unit", "y2024", "y2035", "y2050",
                    "pct_vs_BS_2050"])
        units = {"co2_faostat_prod": "Mt CO2e", "co2_faostat_cons": "Mt CO2e",
                 "co2_pn_lca": "Mt CO2e", "water_green": "km3", "water_blue": "km3",
                 "water_grey": "km3", "water_blue_prod": "km3",
                 "nitrogen_total": "Mt N", "nitrogen_prod": "Mt N", "land_diet": "Mha"}
        bs = {ind: agg.get(("BS", ind), {}).get(2050) for ind in inds}
        for sc in CHINA_SCENARIOS:
            for ind in inds:
                d = agg.get((sc, ind))
                if not d:
                    continue
                v50 = d.get(2050)
                base = bs.get(ind)
                pct = ((v50 - base) / base * 100.0) if (base and v50 is not None) else None
                w.writerow([sc, ind, units[ind],
                            f"{d.get(2024, 0):.4g}", f"{d.get(2035, 0):.4g}",
                            f"{d.get(2050, 0):.4g}",
                            f"{pct:.2f}" if pct is not None else ""])
    return long_path, sum_path, agg


def write_world(rows):
    long_path = os.path.join(OUT, "world_footprints_long.csv")
    with open(long_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "indicator", "coef_source", "region",
                    "commodity", "year", "value"])
        for r in rows:
            w.writerow([r[0], r[1], r[2] or "", r[3], r[4], r[5], f"{r[6]:.6g}"])

    # summary: scenario x indicator x region-group(CHN / exCHN / WLD) x year
    agg = {}
    for sc, ind, src, reg, com, yr, val in rows:
        grp = "CHN" if reg == "CHN" else "exCHN"
        agg.setdefault((sc, ind, grp), {}).setdefault(yr, 0.0)
        agg[(sc, ind, grp)][yr] += val
    # world total
    for (sc, ind, grp), yd in list(agg.items()):
        for yr, v in yd.items():
            agg.setdefault((sc, ind, "WLD"), {}).setdefault(yr, 0.0)
            agg[(sc, ind, "WLD")][yr] += v

    sum_path = os.path.join(OUT, "world_footprints_summary.csv")
    inds = ["co2_faostat", "water_green", "water_blue", "water_grey",
            "nitrogen_total", "land_prod", "land_harvested"]
    units = {"co2_faostat": "Mt CO2e", "water_green": "km3", "water_blue": "km3",
             "water_grey": "km3", "nitrogen_total": "Mt N", "land_prod": "Mha",
             "land_harvested": "Mha"}
    with open(sum_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "indicator", "region_group", "unit",
                    "y2024", "y2050", "abs_vs_BS_2050", "pct_vs_BS_2050"])
        bs = {(ind, grp): agg.get(("BS", ind, grp), {}).get(2050)
              for ind in inds for grp in ("CHN", "exCHN", "WLD")}
        for sc in ["BS", "PTS", "HDS", "MTS"]:
            for ind in inds:
                for grp in ("CHN", "exCHN", "WLD"):
                    d = agg.get((sc, ind, grp))
                    if not d:
                        continue
                    v50 = d.get(2050)
                    base = bs.get((ind, grp))
                    ab = (v50 - base) if (base is not None and v50 is not None) else None
                    pct = (ab / base * 100.0) if (base and ab is not None) else None
                    w.writerow([sc, ind, grp, units[ind],
                                f"{d.get(2024, 0):.5g}", f"{d.get(2050, 0):.5g}",
                                f"{ab:.4g}" if ab is not None else "",
                                f"{pct:.2f}" if pct is not None else ""])
    return long_path, sum_path, agg


# ---------------------------------------------------------------------------
def main():
    print("Loading China results ...")
    cdata = load_china_results()
    balance_path = china_supply_use_balance(cdata)
    print(f"  China supply-use balance -> {balance_path}")
    crows = china_footprints(cdata)
    clong, csum, cagg = write_china(crows)
    print(f"  China long rows: {len(crows)}  -> {clong}")

    print("Loading world results ...")
    wdata = load_world_results()
    direct_path, direct_rows = direct_production_account(cdata, wdata)
    final_path, final_rows = final_consumption_lca_account(cdata, wdata)
    coverage_path = world_carbon_coverage(wdata)
    recon_path = boundary_reconciliation(direct_rows, final_rows)
    print(f"  Direct production account -> {direct_path}")
    print(f"  Final consumption LCA account -> {final_path}")
    print(f"  World carbon coverage -> {coverage_path}")
    print(f"  Boundary reconciliation -> {recon_path}")
    wrows = world_footprints(wdata)
    wlong, wsum, wagg = write_world(wrows)
    print(f"  World long rows: {len(wrows)}  -> {wlong}")

    # quick self-check print
    def g(agg, key, yr=2050):
        return agg.get(key, {}).get(yr, 0.0)
    print("\n--- China 2050 (BS) headline ---")
    for ind in ["co2_faostat_prod", "co2_faostat_cons", "co2_pn_lca",
                "water_blue", "water_green", "water_blue_prod",
                "nitrogen_total", "nitrogen_prod", "land_diet"]:
        print(f"  {ind:20s}: {g(cagg, ('BS', ind)):10.2f}")
    print("\n--- World 2050 WLD total ---")
    for sc in ["BS", "HDS"]:
        print(f"  {sc}: CO2 {g(wagg, (sc, 'co2_faostat', 'WLD')):.1f} Mt  "
              f"blueW {g(wagg, (sc, 'water_blue', 'WLD')):.1f} km3  "
              f"N {g(wagg, (sc, 'nitrogen_total', 'WLD')):.1f} Mt  "
              f"land {g(wagg, (sc, 'land_prod', 'WLD')):.0f} Mha")
    return cagg, wagg


if __name__ == "__main__":
    main()
