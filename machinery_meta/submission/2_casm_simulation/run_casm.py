# -*- coding: utf-8 -*-
"""Run the CASM (China Agricultural Sector Model) mechanisation scenarios.

Baseline + 9 scenarios (manuscript Section 5). Yield/area shifters from
data/scenario_design.csv are added on top of the baseline growth rates
(AYGR0/AAGR0) for the grain-crop set CGRN over 2026-2030, then the partial-
equilibrium model is solved recursively.

CASM Python port under ./casm ; Excel inputs under ./casm_inputs .

Outputs (results/):
  results_by_crop_long.csv   baseline + 9 scenarios x crop x year
  Table8_grain.csv           grain totals (output / net-trade / SSR, 2030)
  Table9_cereal_staple.csv   cereal and staple-grain security (2030)
"""
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CASM_DIR = os.path.join(HERE, "casm_inputs")
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

from casm.simulate import run_base, Growth
from casm.data import Data

SHOCK_YEARS = [str(y) for y in range(2026, 2031)]
YEAR = "2030"

plan = pd.read_csv(os.path.join(HERE, "data", "scenario_design.csv"),
                   encoding="utf-8-sig")
d0 = Data(CASM_DIR)
CGRN, CCRL, CKOUL = d0.CGRN, d0.CCRL, d0.CKOUL
gr0 = Growth(CASM_DIR)


def overrides(y_shift, a_shift):
    ov = {"AYGR0": {}, "AAGR0": {}}
    for c in CGRN:
        for t in SHOCK_YEARS:
            ov["AYGR0"][(c, t)] = gr0.raw["AYGR0"].get((c, "BASE", t), 0.0) + y_shift
            ov["AAGR0"][(c, t)] = gr0.raw["AAGR0"].get((c, "BASE", t), 0.0) + a_shift
    return ov


def extract(res, d):
    out = {}
    for t in res["QX"]:
        out[t] = pd.DataFrame({
            "QX": res["QX"][t], "AC": res["AC"][t], "YC": res["YC"][t],
            "NET": np.maximum(res["QM"][t] - res["QE"][t], 0.0)
            - np.maximum(res["QE"][t] - res["QM"][t], 0.0),
        }, index=d.C)
    return out


runs = [("BASE", 0.0, 0.0)] + [
    (r["scenario"], float(r["yield_shifter_pct_per_yr"]),
     float(r["area_shifter_pct_per_yr"])) for _, r in plan.iterrows()]

results = {}
for name, ys, as_ in runs:
    t0 = time.time()
    ov = None if name == "BASE" else overrides(ys, as_)
    d, cal, m, res = run_base(CASM_DIR, growth_overrides=ov)
    results[name] = extract(res, d)
    print(f"{name:10s} yield_shift={ys:.4f} area_shift={as_:.4f}  "
          f"solved {time.time()-t0:.1f}s", flush=True)

# long table
lr = []
for name, by in results.items():
    for t, dfx in by.items():
        for c in dfx.index:
            lr.append(dict(scenario=name, year=t, crop=c, QX=dfx.loc[c, "QX"],
                           AC=dfx.loc[c, "AC"], YC=dfx.loc[c, "YC"],
                           NET=dfx.loc[c, "NET"]))
pd.DataFrame(lr).to_csv(os.path.join(OUT, "results_by_crop_long.csv"),
                        index=False, encoding="utf-8-sig")


def agg(name, crops):
    x = results[name][YEAR].loc[crops]
    qx, ac, net = x["QX"].sum(), x["AC"].sum(), x["NET"].sum()
    return qx, ac, net, qx / (qx + net) * 100


# Table 8 grain totals
bq, ba, bn, bs = agg("BASE", CGRN)
r8 = [dict(scenario="Baseline", output_10kt=round(bq), output_chg_pct="-",
           net_trade_10kt=round(bn), SSR_pct=round(bs, 2),
           sown_area_100Mmu=round(ba * 15 / 10000, 4), yield_chg_pct="-")]
for name, _, _ in runs[1:]:
    qx, ac, net, ssr = agg(name, CGRN)
    r8.append(dict(scenario=name, output_10kt=round(qx),
                   output_chg_pct=round((qx / bq - 1) * 100, 2),
                   net_trade_10kt=round(net), SSR_pct=round(ssr, 2),
                   sown_area_100Mmu=round(ac * 15 / 10000, 4),
                   yield_chg_pct=round(((qx / ac) / (bq / ba) - 1) * 100, 2)))
t8 = pd.DataFrame(r8)
t8.to_csv(os.path.join(OUT, "Table8_grain.csv"), index=False,
          encoding="utf-8-sig")
print("\n== Table 8 grain totals (2030) ==")
print(t8.to_string(index=False))

# Table 9 cereal & staple
r9 = []
for name, _, _ in runs:
    disp = "Baseline" if name == "BASE" else name
    rec = dict(scenario=disp)
    for lab, cs in (("cereal", CCRL), ("staple", CKOUL)):
        qx, ac, net, ssr = agg(name, cs)
        rec[f"{lab}_output_10kt"] = round(qx)
        rec[f"{lab}_SSR_pct"] = round(ssr, 2)
        rec[f"{lab}_net_trade_10kt"] = round(net)
    r9.append(rec)
t9 = pd.DataFrame(r9)
t9.to_csv(os.path.join(OUT, "Table9_cereal_staple.csv"), index=False,
          encoding="utf-8-sig")
print("\n== Table 9 cereal & staple security (2030) ==")
print(t9.to_string(index=False))
