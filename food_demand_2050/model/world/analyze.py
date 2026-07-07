"""Build world_impacts_summary.md tables from world_results_long.csv.

Computes, for each scenario relative to BS in 2050:
  * world price (PRF) % change, main commodities;
  * China net imports (IMP-EXP) change, Mt;
  * major exporters (BRZ/USA/ARG/AUS/NZL): production & harvested area change;
  * world-excl-China total harvested area change.
Prints tables (markdown) to stdout; the narrative summary md is assembled
separately from this output.
"""

import csv
import collections

RESULTS = "/root/paper/food_demand_2050/results/world"
D = collections.defaultdict(float)   # (scen, com, reg, year, var) -> value

with open(f"{RESULTS}/world_results_long.csv") as fh:
    for row in csv.DictReader(fh):
        D[(row["scenario"], row["commodity"], row["region"], row["year"],
           row["variable"])] = float(row["value"])

SCEN = ["PTS", "MTS", "HDS"]
COMS = ["RIC", "WHE", "CRN", "OCG", "SBS", "SBO", "SBM", "RBS", "RBO", "RBM",
        "NBS", "NBO", "NBM", "BFV", "PRK", "PLM", "BUT", "CHE", "NDM", "WDM",
        "SUG", "CTN"]
EXPORTERS = ["BRZ", "USA", "ARG", "AUS", "NZL", "E15"]
REGIONS = ["USA", "E15", "JPN", "CAN", "MEX", "BRZ", "ARG", "CHN", "AUS",
           "NZL", "KOR", "IND", "ROW"]
Y = "2050"


def g(s, c, r, v, y=Y):
    return D.get((s, c, r, y, v), 0.0)


def pct(a, b):
    return 100.0 * (a - b) / b if abs(b) > 1e-9 else float("nan")


print("## World prices (PRF, % change vs BS, 2050)")
print("| commodity | BS level | " + " | ".join(SCEN) + " |")
print("|---|---:|" + "---:|" * len(SCEN))
for c in COMS:
    bs = g("BS", c, "WLD", "PRF")
    if bs <= 0:
        continue
    cells = [f"{pct(g(s, c, 'WLD', 'PRF'), bs):+.1f}%" for s in SCEN]
    print(f"| {c} | {bs*1000:.0f} $/t | " + " | ".join(cells) + " |")

print("\n## China net imports (IMP-EXP, Mt, 2050)")
print("| commodity | BS | " + " | ".join(f"{s} (Δ)" for s in SCEN) + " |")
print("|---|---:|" + "---:|" * len(SCEN))
for c in COMS:
    bs = g("BS", c, "CHN", "IMP") - g("BS", c, "CHN", "EXP")
    row = []
    for s in SCEN:
        v = g(s, c, "CHN", "IMP") - g(s, c, "CHN", "EXP")
        row.append(f"{v - bs:+.2f}")
    if abs(bs) > 0.05 or any(abs(float(x)) > 0.05 for x in row):
        print(f"| {c} | {bs:.2f} | " + " | ".join(row) + " |")

print("\n## China FOO / FEE change (Mt, 2050, HDS vs BS)")
for c in COMS:
    dfoo = g("HDS", c, "CHN", "FOO") - g("BS", c, "CHN", "FOO")
    dfee = g("HDS", c, "CHN", "FEE") - g("BS", c, "CHN", "FEE")
    dcru = g("HDS", c, "CHN", "CRU") - g("BS", c, "CHN", "CRU")
    if max(abs(dfoo), abs(dfee), abs(dcru)) > 0.1:
        print(f"  {c}: dFOO={dfoo:+.2f} dFEE={dfee:+.2f} dCRU={dcru:+.2f}")

print("\n## Major exporters: production % change vs BS, 2050")
KEY = ["SBS", "SBM", "SBO", "CRN", "WHE", "RIC", "BFV", "PRK", "PLM",
       "NDM", "WDM", "BUT", "CHE"]
for s in SCEN:
    print(f"\n### {s}")
    print("| commodity | " + " | ".join(EXPORTERS) + " |")
    print("|---|" + "---:|" * len(EXPORTERS))
    for c in KEY:
        cells = []
        for r in EXPORTERS:
            bs = g("BS", c, r, "PRD")
            cells.append(f"{pct(g(s, c, r, 'PRD'), bs):+.1f}%" if bs > 0.01
                         else "-")
        print(f"| {c} | " + " | ".join(cells) + " |")

print("\n## Harvested area (total AHV, Mha, 2050)")
print("| region | BS | " + " | ".join(f"{s} Δ" for s in SCEN) + " |")
print("|---|---:|" + "---:|" * len(SCEN))
tot = {s: 0.0 for s in ["BS"] + SCEN}
tot_xchn = {s: 0.0 for s in ["BS"] + SCEN}
for r in REGIONS:
    vals = {}
    for s in ["BS"] + SCEN:
        v = sum(g(s, c, r, "AHV") for c in
                {k[1] for k in D if k[4] == "AHV"})
        vals[s] = v
        tot[s] += v
        if r != "CHN":
            tot_xchn[s] += v
    print(f"| {r} | {vals['BS']:.1f} | " +
          " | ".join(f"{vals[s]-vals['BS']:+.2f}" for s in SCEN) + " |")
print(f"| **World** | {tot['BS']:.1f} | " +
      " | ".join(f"{tot[s]-tot['BS']:+.2f}" for s in SCEN) + " |")
print(f"| **World excl. CHN** | {tot_xchn['BS']:.1f} | " +
      " | ".join(f"{tot_xchn[s]-tot_xchn['BS']:+.2f}" for s in SCEN) + " |")

print("\n## Exporter soybean & dairy detail (HDS vs BS, 2050)")
for r in ["BRZ", "USA", "ARG"]:
    for c in ["SBS"]:
        bs_p, bs_a = g("BS", c, r, "PRD"), g("BS", c, r, "AHV")
        hp, ha = g("HDS", c, r, "PRD"), g("HDS", c, r, "AHV")
        bs_e = g("BS", c, r, "EXP")
        he = g("HDS", c, r, "EXP")
        print(f"  {r} {c}: PRD {bs_p:.1f}->{hp:.1f} ({pct(hp,bs_p):+.1f}%), "
              f"AHV {bs_a:.1f}->{ha:.1f} Mha ({pct(ha,bs_a):+.1f}%), "
              f"EXP {bs_e:.1f}->{he:.1f} Mt")
for r in ["NZL", "AUS", "E15", "USA"]:
    for c in ["NDM", "WDM", "BUT", "CHE"]:
        bs_e = g("BS", c, r, "EXP")
        he = g("HDS", c, r, "EXP")
        if bs_e > 0.01 or he > 0.01:
            print(f"  {r} {c}: EXP {bs_e:.3f}->{he:.3f} Mt "
                  f"({pct(he, bs_e):+.1f}%)")
