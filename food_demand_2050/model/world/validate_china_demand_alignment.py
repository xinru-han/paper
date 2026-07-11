#!/usr/bin/env python3
"""Compare CASM China food targets with CASM-World equilibrium FOO.

The current CASM-World run uses preference shifters, not calibrated quantity
targets. This diagnostic writes the target-alignment table required by the
second-round audit so the mismatch is explicit and reproducible.
"""

from __future__ import annotations

import csv
import os


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "results", "world", "china_demand_target_alignment.csv")

SCENARIO_MAP = {"PTS": "A1", "HDS": "B1", "MTS": "C1"}
REPORT_YEARS = [2024, 2030, 2035, 2040, 2045, 2050]

# CASM quantity is 10,000 tonnes; CASM-World FOO is Mt.
MAPPINGS = [
    ("RICE", ["RIC"], "one-to-one"),
    ("WHEA", ["WHE"], "one-to-one"),
    ("PIGM", ["PRK"], "one-to-one"),
    ("CATM", ["BFV"], "one-to-one"),
    ("CHKM", ["PLM"], "one-to-one"),
    ("OILS", ["SBO", "RBO", "NBO"], "aggregate vegetable oils"),
    ("MILK", ["BUT", "CHE", "NDM", "FMK", "WDM", "ODA"], "dairy products; not raw-milk equivalent"),
]


def load_china():
    out = {}
    path = os.path.join(ROOT, "results", "results_long.csv")
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if r["variable"] != "food_demand_total":
                continue
            key = (r["scenario"], r["commodity"], int(float(r["year"])))
            out[key] = float(r["value"]) * 0.01
    return out


def load_world():
    out = {}
    path = os.path.join(ROOT, "results", "world", "world_results_long.csv")
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if r["variable"] != "FOO" or r["region"] != "CHN":
                continue
            key = (r["scenario"], r["commodity"], int(float(r["year"])))
            out[key] = float(r["value"])
    return out


def main() -> None:
    china = load_china()
    world = load_world()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["world_scenario", "casm_scenario", "year", "casm_commodity",
                    "world_commodities", "casm_target_Mt",
                    "casm_world_equilibrium_FOO_Mt", "relative_error_pct",
                    "mapping_note"])
        for wsc, csc in SCENARIO_MAP.items():
            for year in REPORT_YEARS:
                for casm_comm, world_comms, note in MAPPINGS:
                    target = china.get((csc, casm_comm, year))
                    actual = sum(world.get((wsc, wc, year), 0.0) for wc in world_comms)
                    if target is None:
                        continue
                    err = (actual - target) / target * 100.0 if target else None
                    w.writerow([wsc, csc, year, casm_comm, "+".join(world_comms),
                                f"{target:.6g}", f"{actual:.6g}",
                                f"{err:.6g}" if err is not None else "", note])
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

