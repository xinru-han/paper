#!/usr/bin/env python3
"""Generate transition-depth target paths for second-round audit.

This script creates target-path inputs for three interpolation constructions and
five transition depths. It is a diagnostic input generator; it does not claim
that CASM/CASM-World have been solved for every generated path.
"""

from __future__ import annotations

import csv
import math
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "sensitivity")
DEPTHS = [0.0, 0.25, 0.5, 0.75, 1.0]


def load_paths():
    data = {}
    path = os.path.join(ROOT, "scenarios", "per_capita_paths.csv")
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            key = (r["scenario_group"], r["commodity_code"], int(r["year"]))
            data[key] = float(r["kg_per_capita"])
    return data


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    data = load_paths()
    commodities = sorted({c for _, c, _ in data})
    years = sorted({y for _, _, y in data if 2023 <= y <= 2050})
    out_csv = os.path.join(OUT, "transition_depth_input.csv")
    with open(out_csv, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["construction", "depth", "commodity", "year",
                    "kg_per_capita", "note"])
        for commodity in commodities:
            q0 = data.get(("BS", commodity, 2023))
            pts_2050 = data.get(("PTS", commodity, 2050))
            hds_2050 = data.get(("HDS", commodity, 2050))
            if q0 is None or pts_2050 is None or hds_2050 is None:
                continue
            for depth in DEPTHS:
                for year in years:
                    pts = data.get(("PTS", commodity, year))
                    hds = data.get(("HDS", commodity, year))
                    if pts is None or hds is None:
                        continue
                    # 1. Current growth-rate/path interpolation as represented
                    # by the existing PTS/HDS paths.
                    q_growth = (1 - depth) * pts + depth * hds
                    w.writerow(["annual_growth_path_linear", depth, commodity, year,
                                f"{q_growth:.6g}",
                                "Target-path diagnostic; model not solved here."])
                    # 2. Endpoint level interpolation, smoothed from 2023.
                    endpoint = (1 - depth) * pts_2050 + depth * hds_2050
                    if q0 > 0 and endpoint > 0:
                        r = (endpoint / q0) ** (1 / 27) - 1
                        q_endpoint = q0 * (1 + r) ** (year - 2023)
                    else:
                        q_endpoint = endpoint if year == 2050 else q0
                    w.writerow(["endpoint_level_linear", depth, commodity, year,
                                f"{q_endpoint:.6g}",
                                "Target-path diagnostic; model not solved here."])
                    # 3. Log-level interpolation between existing paths.
                    if pts > 0 and hds > 0:
                        q_log = math.exp((1 - depth) * math.log(pts) + depth * math.log(hds))
                    else:
                        q_log = q_growth
                    w.writerow(["log_level_path", depth, commodity, year,
                                f"{q_log:.6g}",
                                "Target-path diagnostic; model not solved here."])
    report = os.path.join(OUT, "transition_depth_status.md")
    with open(report, "w", encoding="utf-8") as fh:
        fh.write("# Transition Depth Sensitivity Status\n\n")
        fh.write("Generated target paths for annual-growth/path interpolation, 2050 endpoint-level interpolation, and log-level interpolation at depths 0, 0.25, 0.50, 0.75 and 1.00.\n\n")
        fh.write("These files are inputs for the required full model reruns. They do not replace solving CASM and CASM-World for each path.\n")
    print(f"wrote {out_csv}")
    print(f"wrote {report}")


if __name__ == "__main__":
    main()

