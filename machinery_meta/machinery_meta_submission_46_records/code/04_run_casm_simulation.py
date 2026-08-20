# -*- coding: utf-8 -*-
"""Run BASE and nine unified-path scenarios with external CASM-Python.

CASM source code is intentionally not included. Set CASM_PYTHON_DIR and
CASM_TEMPLATE_DIR to override the default external locations.
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "casm"
PLAN_FILE = OUT / "scenario_plan.csv"
CASM_PYTHON_DIR = Path(os.environ.get("CASM_PYTHON_DIR", "/root/data/CASM/casm_python"))
CASM_TEMPLATE_DIR = Path(os.environ.get(
    "CASM_TEMPLATE_DIR", "/root/data/Paper/农机Meta/CASM20260410MACHINE2"
))
INPUT_COPY = OUT / "casm_inputs_used"
SHOCK_YEARS = [str(year) for year in range(2026, 2031)]
REPORT_YEAR = "2030"


def prepare_inputs():
    INPUT_COPY.mkdir(parents=True, exist_ok=True)
    names = ["0data.xlsx", "1parameter.xlsx", "2simulation.xlsm", "3RESULTCOM.XLSX"]
    for name in names:
        source = CASM_TEMPLATE_DIR / name
        if not source.exists():
            raise FileNotFoundError(source)
        shutil.copy2(source, INPUT_COPY / name)
    return INPUT_COPY


def import_casm():
    if not CASM_PYTHON_DIR.exists():
        raise FileNotFoundError(CASM_PYTHON_DIR)
    sys.path.insert(0, str(CASM_PYTHON_DIR))
    from casm.data import Data
    from casm.simulate import Growth, run_base
    return Data, Growth, run_base


def make_overrides(crops, base_growth, yield_shift, area_shift):
    overrides = {"AYGR0": {}, "AAGR0": {}}
    for crop in crops:
        for year in SHOCK_YEARS:
            base_yield = base_growth.raw["AYGR0"].get((crop, "BASE", year), 0.0)
            base_area = base_growth.raw["AAGR0"].get((crop, "BASE", year), 0.0)
            overrides["AYGR0"][(crop, year)] = base_yield + yield_shift
            overrides["AAGR0"][(crop, year)] = base_area + area_shift
    return overrides


def extract_core_results(result, data):
    output = {}
    for year in sorted(result["QX"]):
        imports = np.maximum(result["QM"][year] - result["QE"][year], 0.0)
        exports = np.maximum(result["QE"][year] - result["QM"][year], 0.0)
        output[year] = pd.DataFrame({
            "QX": result["QX"][year],
            "AC": result["AC"][year],
            "YC": result["YC"][year],
            "QM": imports,
            "QE": exports,
            "NETQM": imports - exports,
        }, index=data.C)
    return output


def aggregate(results, scenario, crops, year=REPORT_YEAR):
    d = results[scenario][year].loc[crops]
    production = d["QX"].sum()
    area = d["AC"].sum()
    net_import = d["NETQM"].sum()
    self_sufficiency = production / (production + net_import) * 100 \
        if production + net_import != 0 else np.nan
    yield_level = production / area if area != 0 else np.nan
    return production, area, net_import, self_sufficiency, yield_level


def write_long_results(results):
    rows = []
    for scenario, years in results.items():
        for year, frame in years.items():
            for crop in frame.index:
                row = {"scenario": scenario, "year": year, "crop": crop}
                row.update(frame.loc[crop, ["QX", "AC", "YC", "QM", "QE", "NETQM"]].to_dict())
                rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "casm_results_long.csv",
                              index=False, encoding="utf-8-sig")


def write_summary(plan, elasticities, grain, logs):
    lines = [
        "# Revised 46-record strict-path CASM results",
        "",
        "BASE and all nine scenarios completed without a solver exception. "
        "The shocks use the same strict MCI/AMS/AML dataset as the meta-analysis.",
        "",
        "## Path elasticities",
        "",
        elasticities[["Path", "Target", "k_elasticity", "elasticity_used", "record_ids"]]
        .to_markdown(index=False),
        "",
        "## Scenario shocks",
        "",
        plan[["scenario", "Path", "yield_shifter_pct_per_year",
              "area_shifter_pct_per_year"]].to_markdown(index=False),
        "",
        "## 2030 grain results",
        "",
        grain.to_markdown(index=False),
        "",
        f"Completed CASM runs: {len(logs)} (BASE plus nine scenarios).",
    ]
    (OUT / "casm_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    casm_inputs = prepare_inputs()
    Data, Growth, run_base = import_casm()
    plan = pd.read_csv(PLAN_FILE, encoding="utf-8-sig")
    elasticities = pd.read_csv(OUT / "path_elasticities.csv", encoding="utf-8-sig")

    initial_data = Data(str(casm_inputs))
    grain_crops, cereal_crops, staple_crops = initial_data.CGRN, initial_data.CCRL, initial_data.CKOUL
    base_growth = Growth(str(casm_inputs))
    runs = [{"scenario": "BASE", "yield_shift": 0.0, "area_shift": 0.0}]
    for row in plan.itertuples(index=False):
        runs.append({
            "scenario": row.scenario,
            "yield_shift": float(row.yield_shifter_pct_per_year),
            "area_shift": float(row.area_shifter_pct_per_year),
        })

    results = {}
    logs = []
    for run in runs:
        started = time.time()
        overrides = None
        if run["scenario"] != "BASE":
            overrides = make_overrides(grain_crops, base_growth,
                                       run["yield_shift"], run["area_shift"])
        progress = []
        data, calibration, model, result = run_base(
            str(casm_inputs), growth_overrides=overrides,
            progress=lambda message: progress.append(message),
        )
        results[run["scenario"]] = extract_core_results(result, data)
        elapsed = time.time() - started
        logs.append({
            "scenario": run["scenario"],
            "yield_shifter_pct_per_year": run["yield_shift"],
            "area_shifter_pct_per_year": run["area_shift"],
            "completed_without_exception": True,
            "elapsed_seconds": elapsed,
            "solver_progress": " | ".join(progress),
        })
        print(f"{run['scenario']:10s} yield={run['yield_shift']:.6f}% "
              f"area={run['area_shift']:.6f}% {elapsed:.1f}s", flush=True)

    write_long_results(results)
    log_frame = pd.DataFrame(logs)
    log_frame.to_csv(OUT / "casm_run_log.csv", index=False, encoding="utf-8-sig")

    base_production, base_area, base_net, base_ssr, base_yield = aggregate(
        results, "BASE", grain_crops
    )
    grain_rows = [{
        "scenario": "BASE",
        "production_10kt": round(base_production, 3),
        "production_change_pct": 0.0,
        "net_import_10kt": round(base_net, 3),
        "self_sufficiency_pct": round(base_ssr, 4),
        "area_million_mu": round(base_area * 15 / 10000, 6),
        "yield_change_pct": 0.0,
    }]
    for run in runs[1:]:
        production, area, net_import, ssr, yield_level = aggregate(
            results, run["scenario"], grain_crops
        )
        grain_rows.append({
            "scenario": run["scenario"],
            "production_10kt": round(production, 3),
            "production_change_pct": round((production / base_production - 1) * 100, 6),
            "net_import_10kt": round(net_import, 3),
            "self_sufficiency_pct": round(ssr, 4),
            "area_million_mu": round(area * 15 / 10000, 6),
            "yield_change_pct": round((yield_level / base_yield - 1) * 100, 6),
        })
    grain = pd.DataFrame(grain_rows)

    security_rows = []
    for run in runs:
        record = {"scenario": run["scenario"]}
        for label, crops in [
            ("grain", grain_crops), ("cereal", cereal_crops), ("staple", staple_crops)
        ]:
            production, area, net_import, ssr, yield_level = aggregate(
                results, run["scenario"], crops
            )
            record[f"{label}_production_10kt"] = round(production, 3)
            record[f"{label}_net_import_10kt"] = round(net_import, 3)
            record[f"{label}_self_sufficiency_pct"] = round(ssr, 4)
        security_rows.append(record)
    security = pd.DataFrame(security_rows)

    grain.to_csv(OUT / "table_grain_2030.csv", index=False, encoding="utf-8-sig")
    security.to_csv(OUT / "table_food_security_2030.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(OUT / "casm_simulation_outputs.xlsx", engine="openpyxl") as writer:
        plan.to_excel(writer, index=False, sheet_name="scenario_plan")
        elasticities.to_excel(writer, index=False, sheet_name="path_elasticities")
        grain.to_excel(writer, index=False, sheet_name="grain_2030")
        security.to_excel(writer, index=False, sheet_name="food_security_2030")
        log_frame.to_excel(writer, index=False, sheet_name="run_log")
    write_summary(plan, elasticities, grain, log_frame)
    print(f"Wrote {OUT / 'casm_simulation_outputs.xlsx'}")


if __name__ == "__main__":
    main()
