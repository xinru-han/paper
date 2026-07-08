# -*- coding: utf-8 -*-
"""Build the CASM policy-scenario matrix (manuscript Section 5, Table 6-7).

3 mechanisation paths x 3 speeds (Medium/High/Low). Yield/area technology
shifters follow Eq.(25): shifter = path-dimension elasticity median x annual
growth rate of the proxy indicator. Elasticities are recomputed from the final
dataset so that Table 6 (elasticities) and Table 7 (shifters) are internally
consistent.

Proxy indicators and annual growth (14th Five-Year actual = Medium):
  S1 (MCI) total agricultural machinery power   2.4 / 3.4 / 1.4  %/yr
  S2 (AMS) machinery trusteeship service area   2.8 / 3.8 / 1.8  %/yr
  S3 (AML) comprehensive mechanisation rate     +0.86/+1.86/+0.10 pp/yr (base 76.7%)

Area shifters: MCI = 0 (subgroup PCC negative, no positive area shock, per
manuscript); AMS = 0.0235 (P_12); AML = 0.015 (P_19).

Output: data/scenario_design.csv
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, "..", "data"), exist_ok=True)

df = pd.read_csv(os.path.join(HERE, "..", "data", "meta_dataset.csv"),
                 encoding="utf-8-sig")
el = df[df["elasticity"].abs() < 1]


def med(tg, p):
    c = el[(el["Target"] == tg) & (el["Path"] == p)]
    return float(c["elasticity"].median()) if len(c) else np.nan


E_yield = {p: med("Yield", p) for p in ["MCI", "AMS", "AML"]}
E_area = {"MCI": 0.0, "AMS": 0.0235, "AML": 0.015}   # per manuscript Table 6

S3_BASE = 76.7
PROXY = {
    "S1": dict(path="MCI", name="Machinery capital input",
               proxy="Total agricultural machinery power",
               speed={"Medium": 2.4, "High": 3.4, "Low": 1.4}),
    "S2": dict(path="AMS", name="Machinery socialised services",
               proxy="Machinery trusteeship service area",
               speed={"Medium": 2.8, "High": 3.8, "Low": 1.8}),
    "S3": dict(path="AML", name="Comprehensive mechanisation",
               proxy="Comprehensive mechanisation rate",
               speed={"Medium": 0.86 / S3_BASE * 100,
                      "High": 1.86 / S3_BASE * 100,
                      "Low": 0.10 / S3_BASE * 100}),
}

rows = []
for s, cfg in PROXY.items():
    p = cfg["path"]
    for spd, g in cfg["speed"].items():
        rows.append(dict(scenario=f"{s}-{spd}", path=f"{cfg['name']} ({p})",
                         proxy_indicator=cfg["proxy"],
                         annual_growth_pct=round(g, 3),
                         yield_elasticity=round(E_yield[p], 4),
                         area_elasticity=round(E_area[p], 4),
                         yield_shifter_pct_per_yr=round(E_yield[p] * g, 4),
                         area_shifter_pct_per_yr=round(E_area[p] * g, 4),
                         shock_crops="CGRN (rice,wheat,maize,soybean,barley,"
                                     "other grain,sorghum)",
                         shock_years="2026-2030"))
plan = pd.DataFrame(rows)
plan.to_csv(os.path.join(HERE, "..", "data", "scenario_design.csv"), index=False,
            encoding="utf-8-sig")
print(plan[["scenario", "annual_growth_pct", "yield_shifter_pct_per_yr",
            "area_shifter_pct_per_yr"]].to_string(index=False))
print("\nElasticities  yield:", {k: round(v, 3) for k, v in E_yield.items()},
      " area:", E_area)
