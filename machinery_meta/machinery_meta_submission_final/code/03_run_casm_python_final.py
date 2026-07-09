# -*- coding: utf-8 -*-
"""Run CASM-Python for the final machinery scenarios.

The CASM source code is not copied into this archive. Set CASM_PYTHON_DIR to
the external CASM-Python repository if it is not located at
/root/data/CASM/casm_python.
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path("/root/data/Paper/农机Meta")
ARCHIVE = PROJECT / "machinery_meta_submission_final"
RESULTS = ARCHIVE / "results" / "casm"
PLAN_FILE = RESULTS / "simulation_plan_final.csv"
CASM_TEMPLATE = PROJECT / "CASM20260410MACHINE2"
CASM_INPUT_COPY = RESULTS / "casm_inputs_used"
CASM_PYTHON_DIR = Path(os.environ.get("CASM_PYTHON_DIR", "/root/data/CASM/casm_python"))
SHOCK_YEARS = [str(y) for y in range(2026, 2031)]
REPORT_YEAR = "2030"


def prepare_inputs():
    CASM_INPUT_COPY.mkdir(parents=True, exist_ok=True)
    for name in ["0data.xlsx", "1parameter.xlsx", "2simulation.xlsm", "3RESULTCOM.XLSX"]:
        shutil.copy2(CASM_TEMPLATE / name, CASM_INPUT_COPY / name)
    return CASM_INPUT_COPY


def import_casm():
    sys.path.insert(0, str(CASM_PYTHON_DIR))
    from casm.data import Data
    from casm.output import Output
    from casm.simulate import Growth, run_base

    return Data, Growth, Output, run_base


def make_overrides(cgrn, base_growth, y_shift, a_shift):
    """Baseline AYGR0/AAGR0 plus annual shifter, both in percent units."""
    overrides = {"AYGR0": {}, "AAGR0": {}}
    for c in cgrn:
        for t in SHOCK_YEARS:
            base_y = base_growth.raw["AYGR0"].get((c, "BASE", t), 0.0)
            base_a = base_growth.raw["AAGR0"].get((c, "BASE", t), 0.0)
            overrides["AYGR0"][(c, t)] = base_y + y_shift
            overrides["AAGR0"][(c, t)] = base_a + a_shift
    return overrides


def extract_core_results(res, d):
    out = {}
    years = sorted(res["QX"].keys())
    for t in years:
        qm = np.maximum(res["QM"][t] - res["QE"][t], 0.0)
        qe = np.maximum(res["QE"][t] - res["QM"][t], 0.0)
        out[t] = pd.DataFrame({
            "QX": res["QX"][t],
            "AC": res["AC"][t],
            "YC": res["YC"][t],
            "QM": qm,
            "QE": qe,
            "NETQM": qm - qe,
        }, index=d.C)
    return out


def aggregate(results, scenario, crops, year=REPORT_YEAR):
    df = results[scenario][year].loc[crops]
    qx = df["QX"].sum()
    ac = df["AC"].sum()
    net = df["NETQM"].sum()
    ssr = qx / (qx + net) * 100 if (qx + net) != 0 else np.nan
    yld = qx / ac if ac != 0 else np.nan
    return qx, ac, net, ssr, yld


def write_long_results(results):
    rows = []
    for scenario, by_year in results.items():
        for year, df in by_year.items():
            for crop in df.index:
                rows.append({
                    "scenario": scenario,
                    "year": year,
                    "crop": crop,
                    "QX": df.loc[crop, "QX"],
                    "AC": df.loc[crop, "AC"],
                    "YC": df.loc[crop, "YC"],
                    "QM": df.loc[crop, "QM"],
                    "QE": df.loc[crop, "QE"],
                    "NETQM": df.loc[crop, "NETQM"],
                })
    pd.DataFrame(rows).to_csv(RESULTS / "casm_results_long_final.csv",
                              index=False, encoding="utf-8-sig")


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    casm_dir = prepare_inputs()
    Data, Growth, Output, run_base = import_casm()

    plan = pd.read_csv(PLAN_FILE, encoding="utf-8-sig")
    d0 = Data(str(casm_dir))
    cgrn, ccrl, ckou = d0.CGRN, d0.CCRL, d0.CKOUL
    base_growth = Growth(str(casm_dir))

    runs = [dict(scenario="BASE", y_shift=0.0, a_shift=0.0)]
    for _, r in plan.iterrows():
        runs.append(dict(scenario=r["scenario"],
                         y_shift=float(r["每年单产Shifter(%)"]),
                         a_shift=float(r["每年面积Shifter(%)"])))

    results = {}
    logs = []
    for r in runs:
        t0 = time.time()
        overrides = None
        if r["scenario"] != "BASE":
            overrides = make_overrides(cgrn, base_growth, r["y_shift"], r["a_shift"])
        progress_lines = []
        d, cal, m, res = run_base(str(casm_dir), growth_overrides=overrides,
                                  progress=lambda s: progress_lines.append(s))
        results[r["scenario"]] = extract_core_results(res, d)
        elapsed = time.time() - t0
        logs.append({
            "scenario": r["scenario"],
            "yield_shifter_pct_per_year": r["y_shift"],
            "area_shifter_pct_per_year": r["a_shift"],
            "elapsed_seconds": elapsed,
            "solver_progress": " | ".join(progress_lines),
        })
        print(f"{r['scenario']:10s} yield={r['y_shift']:.6f}% area={r['a_shift']:.6f}% {elapsed:.1f}s", flush=True)

    write_long_results(results)
    pd.DataFrame(logs).to_csv(RESULTS / "casm_run_log_final.csv",
                              index=False, encoding="utf-8-sig")

    # Summary tables for manuscript upload.
    b_qx, b_ac, b_net, b_ssr, b_yld = aggregate(results, "BASE", cgrn)
    grain_rows = [{
        "scenario": "BASE",
        "production_10kt": round(b_qx, 3),
        "production_change_pct": 0.0,
        "net_import_10kt": round(b_net, 3),
        "self_sufficiency_pct": round(b_ssr, 4),
        "area_million_mu": round(b_ac * 15 / 10000, 6),
        "yield_change_pct": 0.0,
    }]
    for r in runs[1:]:
        qx, ac, net, ssr, yld = aggregate(results, r["scenario"], cgrn)
        grain_rows.append({
            "scenario": r["scenario"],
            "production_10kt": round(qx, 3),
            "production_change_pct": round((qx / b_qx - 1) * 100, 6),
            "net_import_10kt": round(net, 3),
            "self_sufficiency_pct": round(ssr, 4),
            "area_million_mu": round(ac * 15 / 10000, 6),
            "yield_change_pct": round((yld / b_yld - 1) * 100, 6),
        })
    grain = pd.DataFrame(grain_rows)

    security_rows = []
    for r in runs:
        rec = {"scenario": r["scenario"]}
        for label, crops in [("grain", cgrn), ("cereal", ccrl), ("staple", ckou)]:
            qx, ac, net, ssr, yld = aggregate(results, r["scenario"], crops)
            rec[f"{label}_production_10kt"] = round(qx, 3)
            rec[f"{label}_net_import_10kt"] = round(net, 3)
            rec[f"{label}_self_sufficiency_pct"] = round(ssr, 4)
        security_rows.append(rec)
    security = pd.DataFrame(security_rows)

    with pd.ExcelWriter(RESULTS / "casm_simulation_outputs_final.xlsx", engine="openpyxl") as writer:
        plan.to_excel(writer, index=False, sheet_name="scenario_plan")
        grain.to_excel(writer, index=False, sheet_name="grain_2030")
        security.to_excel(writer, index=False, sheet_name="food_security_2030")
        pd.DataFrame(logs).to_excel(writer, index=False, sheet_name="run_log")

    grain.to_csv(RESULTS / "table_grain_2030_final.csv", index=False, encoding="utf-8-sig")
    security.to_csv(RESULTS / "table_food_security_2030_final.csv", index=False, encoding="utf-8-sig")
    print(f"wrote {RESULTS / 'casm_simulation_outputs_final.xlsx'}")


if __name__ == "__main__":
    main()
