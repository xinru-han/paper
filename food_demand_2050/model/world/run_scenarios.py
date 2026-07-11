"""CASM-World: China dietary-transition scenarios to 2050.

Runs the CASM-World (CASM China + PEATSim world) model for 2024-2050 under
four Chinese dietary scenarios (BS / PTS / HDS / MTS) and writes long-format
results to the repository-local results/world directory.

Method (least-intrusive, baseline-preserving):
  * The repository-local cw package is imported by default. Set
    CASM_WORLD_PATH to use an external copy for comparison.
  * Horizon extension 2036-2050: after Data() is built, the in-memory macro
    dict (POP, RGDP) is extrapolated with the 2030-2035 CAGR; RXCHRATE and
    tariffs (TMBASE/TM2BASE) are held at their 2035 values.
  * Dietary preference shifter (analogue of CASM's afhgr0/AFH mechanism):
    China's per-capita food-demand intercept consfoo[i, CHN] is multiplied
    by (1+g_i)^(t-2024) each year before solving, g_i being the scenario's
    annual preference growth rate.  Milk demand additionally scales the raw
    milk consumption intercept consmlk[CHN] (reporting; raw milk is
    non-traded - world transmission runs through dairy-product food demand).
    BS has all g=0 and reproduces the baseline exactly.

Scenario rates are the afhgr0 values from the single-country CASM paper,
mapped to CASM-World commodities (see MAPPING below; sheep meat, eggs,
fish, vegetables and fruit are outside the world model's commodity space).
"""

import os
import sys
import csv
import warnings

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CW_PATH = os.environ.get("CASM_WORLD_PATH", HERE)
sys.path.insert(0, CW_PATH)

import numpy as np

from cw.data import Data
from cw.calib import Calibration
from cw.model import Model

RESULTS = os.path.join(ROOT, "results", "world")
YEARS = [str(y) for y in range(2024, 2051)]
REPORT_YEARS = ["2024", "2030", "2035", "2040", "2045", "2050"]
EXPORT = ["PRD", "CON", "FOO", "FEE", "CRU", "EXP", "IMP", "AHV",
          "PDOM", "PCN", "PRF"]

# ---------------------------------------------------------------------------
# CASM afhgr0 (%/yr, 2025-2050) -> CASM-World commodities
#   RICE->RIC  WHEA->WHE  veg.oil->SBO/RBO/NBO  PIGM->PRK  CATM->BFV
#   CHKM->PLM  MILK->dairy foods BUT/CHE/NDM/FMK/WDM/ODA (+ raw-milk consmlk)
# Not representable: SHGM, EGGS, FISH, VEGT, FRTO (no world-model commodity);
# SUGR has no scenario rate in the paper.
DAIRY_FOODS = ["BUT", "CHE", "NDM", "FMK", "WDM", "ODA"]
OILS = ["SBO", "RBO", "NBO"]


def _expand(base):
    """Map paper commodity rates to world-model commodity rates (%/yr)."""
    g = {}
    g["RIC"] = base["RICE"]
    g["WHE"] = base["WHEA"]
    for c in OILS:
        g[c] = base["OILS"]
    g["PRK"] = base["PIGM"]
    g["BFV"] = base["CATM"]
    g["PLM"] = base["CHKM"]
    for c in DAIRY_FOODS:
        g[c] = base["MILK"]
    g["_MLK"] = base["MILK"]          # raw-milk consumption intercept
    return g


PTS = dict(RICE=-0.25, WHEA=-0.20, OILS=+0.20, PIGM=+0.40, CATM=+0.25,
           CHKM=+0.30, MILK=+0.75)
HDS = dict(RICE=-1.50, WHEA=-1.50, OILS=-2.25, PIGM=-4.69, CATM=-4.90,
           CHKM=+1.30, MILK=+3.00)
MTS = {k: (PTS[k] + HDS[k]) / 2.0 for k in PTS}

SCENARIOS = {
    "BS": {},
    "PTS": _expand(PTS),
    "HDS": _expand(HDS),
    "MTS": _expand(MTS),
}


# ---------------------------------------------------------------------------
def extend_to_2050(d):
    """Extrapolate in-memory macro drivers and tariffs from 2035 to 2050."""
    new_years = [str(y) for y in range(2036, 2051)]
    for sym in ("POP", "RGDP"):
        tbl = d.macro[sym]
        for r in d.R:
            v30, v35 = tbl.get((r, "2030")), tbl.get((r, "2035"))
            if not v30 or not v35:
                continue
            gr = (v35 / v30) ** (1.0 / 5.0)          # 2030-2035 CAGR
            for y in new_years:
                tbl[(r, y)] = v35 * gr ** (int(y) - 2035)
    tbl = d.macro["RXCHRATE"]
    for r in d.R:
        v35 = tbl.get((r, "2035"))
        if v35 is not None:
            for y in new_years:
                tbl[(r, y)] = v35
    for name in ("TMBASE", "TM2BASE"):
        tar = d.tar[name]
        at35 = {(i, r): v for (i, r, t), v in tar.items() if t == "2035"}
        for (i, r), v in at35.items():
            for y in new_years:
                tar[(i, r, y)] = v


def shifter_factors(d, growth, year):
    """(nI,) multiplicative factor on China's food intercept, and the raw
    milk factor, for calendar ``year``: (1+g)^(year-2024)."""
    t = int(year) - 2024
    fac = np.ones(d.nI)
    for c, g in growth.items():
        if c == "_MLK":
            continue
        fac[d.ii[c]] = (1.0 + g / 100.0) ** t
    fac_mlk = (1.0 + growth.get("_MLK", 0.0) / 100.0) ** t
    return fac, fac_mlk


def run_scenario(m, d, c, growth, consfoo0, consmlk0, progress=None):
    """Recursive 2024-2050 run with the China preference shifter applied."""
    chn = d.ri["CHN"]
    # base-year (2023) forward pass for the first lag
    m.set_year(d.base)
    m.inter["consfoo"] = consfoo0.copy()
    m.inter["consmlk"] = consmlk0.copy()
    v0 = m.forward(c.PRF0)
    res = {d.base: v0}
    lag = dict(AHV=v0["AHV"], YLD=v0["YLD"], PRD=v0["PRD"], CRU=v0["CRU"],
               CON=v0["CON"], EST=v0["EST"], PRFClag=v0["PRFC"])
    PRF = c.PRF0.copy()
    for y in YEARS:
        m.set_year(y)
        fac, fac_mlk = shifter_factors(d, growth, y)
        cf = consfoo0.copy()
        cf[:, chn] *= fac
        m.inter["consfoo"] = cf
        cm = consmlk0.copy()
        cm[chn] *= fac_mlk
        m.inter["consmlk"] = cm
        v = m.solve_world(PRF0=PRF, lag=lag)
        res[y] = v
        if progress:
            progress(f"  {y}: |excess|={v['resid']:.2e} iters={v['iters']}")
        lag = dict(AHV=v["AHV"], YLD=v["YLD"], PRD=v["PRD"], CRU=v["CRU"],
                   CON=v["CON"], EST=v["EST"], PRFClag=v["PRFC"])
        PRF = v["PRF"].copy()
    return res


# ---------------------------------------------------------------------------
def main():
    os.makedirs(RESULTS, exist_ok=True)
    print("loading data / calibrating ...")
    d = Data()
    extend_to_2050(d)
    c = Calibration(d)
    m = Model(d, c)
    consfoo0 = m.inter["consfoo"].copy()
    consmlk0 = m.inter["consmlk"].copy()

    inv = {v: k for k, v in d.ii.items()}
    path = os.path.join(RESULTS, "world_results_long.csv")
    conv = {}
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "commodity", "region", "year", "variable",
                    "value"])
        for scen, growth in SCENARIOS.items():
            print(f"\n=== scenario {scen} ===")
            res = run_scenario(m, d, c, growth, consfoo0, consmlk0,
                               progress=print)
            conv[scen] = max(res[y]["resid"] for y in YEARS)
            for year in REPORT_YEARS:
                v = res[year]
                for var in EXPORT:
                    arr = v.get(var)
                    if arr is None:
                        continue
                    if arr.ndim == 1:                     # PRF world price
                        for i in range(d.nI):
                            if abs(arr[i]) > 1e-12:
                                w.writerow([scen, inv[i], "WLD", year, var,
                                            f"{arr[i]:.6g}"])
                        continue
                    for i in range(d.nI):
                        for r in range(d.nR):
                            if abs(arr[i, r]) > 1e-9:
                                w.writerow([scen, inv[i], d.R[r], year, var,
                                            f"{arr[i, r]:.6g}"])
    print(f"\nwrote {path}")
    print("max world-clearing residual by scenario:")
    for s, r in conv.items():
        print(f"  {s}: {r:.2e}")


if __name__ == "__main__":
    main()
