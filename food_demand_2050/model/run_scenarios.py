"""Reproduce every GAMS simulation of the paper
"Alternative pathways for China's diet transition ... to 2050"
with the Python port of CASM v2.2.7 (base year 2024, projections 2025-2050).

Scenario design (three folders under /root/data/Paper/食物预测2050/, which
differ only in 2simulation.xlsm, i.e. in the AFHGR0 diet-preference drift):

    folder               group  diet pathway            paper codes
    CASM20251118         PTS    past-trend shift         A1..A6
    CASM20251118diet     HDS    healthy-diet shift       B1..B6
    CASM20251118median   MTS    median transition        C1..C6

Within a folder GAMS runs BASE + SIM1..SIM6 (CASM.gms, $SETGLOBAL A 7).
BASE (afhgr0 = 0) is identical across the three folders and is run once
(paper code BS).  SIMn.gms repeats the BASE recursive loop verbatim with
SIMC = SIMn, so a scenario run only changes which SIM column of
2simulation.xlsm is read; that is what run_base(..., sim=) does.

Paper sub-scenario coding (预测结果整理/data.py SUB_SCENARIOS):
    X1 = SIM1 (representative), X2 = SIM4 (high urbanisation),
    X3 = SIM5 (low urbanisation), X4 = SIM2 (high population),
    X5 = SIM3 (low population),   X6 = SIM6 (ageing standard-person)

Outputs (in ../results):
    results_long.csv       tidy long table, all scenarios x variables x years
    scenario_summary.csv   key indicators at TSP years (2023/2024/2035/2050)
    run_log.txt            per-year solver residuals for all 19 runs

Usage:  python3 run_scenarios.py
"""

import os
import sys
import time
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from casm.data import Data, T, TSP
from casm.calib import Calibration
from casm.model import Model
from casm.simulate import run_base
from casm.output import Output

PAPER_DIR = "/root/data/Paper/食物预测2050"
FOLDERS = {
    "PTS": os.path.join(PAPER_DIR, "CASM20251118"),
    "HDS": os.path.join(PAPER_DIR, "CASM20251118diet"),
    "MTS": os.path.join(PAPER_DIR, "CASM20251118median"),
}
PREFIX = {"PTS": "A", "HDS": "B", "MTS": "C"}
SIM_TO_CODE = {"SIM1": 1, "SIM4": 2, "SIM5": 3, "SIM2": 4, "SIM3": 5, "SIM6": 6}
SIMS = ["SIM1", "SIM2", "SIM3", "SIM4", "SIM5", "SIM6"]

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "results")

# per-commodity variables written to the long table (X-parameter names of
# 4OUTPUT.gms -> human-readable variable label)
COMMODITY_VARS = {
    "QXX": "production",            # 万吨
    "ACX": "area",                  # 万公顷
    "YCX": "yield",                 # 吨/亩 (GAMS sheets show *1000)
    "QMX": "net_import",            # 万吨
    "QEX": "net_export",            # 万吨
    "QDFX": "food_demand_total",    # 万吨
    "QDFPCX": "food_demand_pc",     # kg/person/year
    "QDLX": "feed_demand",
    "QDSX": "seed_demand",
    "QDPX": "processing_demand",
    "QDCX": "crush_demand",
    "QDWX": "waste_demand",
    "QDOX": "other_demand",
    "STVX": "stock_change",
    "QDTX": "domestic_demand_total",
    "PDX": "consumer_price",
    "PXX": "producer_price",
}
NUTRI_VARS = {  # per commodity, per capita per day
    "ENERGY": "energy_pc_day",      # kcal
    "PROTEIN": "protein_pc_day",    # g
    "FAT": "fat_pc_day",            # g
    "CARBON": "carbohydrate_pc_day",  # g
}


def scenario_rows(group, sim, code, out):
    """Yield (scenario, group, sim, variable, commodity, year, value)."""
    X = out.X
    for xn, var in COMMODITY_VARS.items():
        df = X[xn]
        for c in df.index:
            for t in T:
                yield (code, group, sim, var, c, t, df.loc[c, t])
    for attr, var in NUTRI_VARS.items():
        df = getattr(out, attr)
        for c in df.index:
            for t in T:
                yield (code, group, sim, var, c, t, df.loc[c, t])
    for c in out.CO2.index:
        for t in T:
            yield (code, group, sim, "co2_emission", c, t, out.CO2.loc[c, t])
    # macro / aggregate series (commodity = ALL)
    agg = {
        "population_total": out.POPX,               # 万人
        "population_urban": out.POPHX.loc["HHDHU"],
        "gdp_per_capita": out.GDPTX / out.POPX,
        "co2_crop": out.CO2CRP,                     # 万吨 CO2e
        "co2_livestock": out.CO2LVS,
        "co2_total": out.CO2TOT,
        "energy_pc_day_total": out.ENERGY.sum(axis=0),
        "protein_pc_day_total": out.PROTEIN.sum(axis=0),
        "fat_pc_day_total": out.FAT.sum(axis=0),
        "carbohydrate_pc_day_total": out.CARBON.sum(axis=0),
    }
    for var, s in agg.items():
        for t in T:
            yield (code, group, sim, var, "ALL", t, s[t])


def run_all():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    log_path = os.path.join(RESULTS_DIR, "run_log.txt")
    log = open(log_path, "w", encoding="utf-8")

    long_path = os.path.join(RESULTS_DIR, "results_long.csv")
    flong = open(long_path, "w", newline="", encoding="utf-8-sig")
    wlong = csv.writer(flong)
    wlong.writerow(["scenario", "group", "sim", "variable", "commodity",
                    "year", "value"])

    summary = []   # (scenario, group, sim, variable, commodity, year, value)

    def do_run(folder, group, sim, code, prebuilt):
        t0 = time.time()
        log.write(f"===== {code} ({group}/{sim}) folder={folder}\n")
        d, cal, m, res = run_base(folder, sim=sim, prebuilt=prebuilt,
                                  progress=lambda s: log.write("  " + s + "\n"))
        out = Output(folder, d, m, res, sim=sim)
        nrow = 0
        for row in scenario_rows(group, sim, code, out):
            wlong.writerow(row[:6] + (repr(float(row[6])),))
            nrow += 1
            if row[5] in TSP:
                summary.append(row)
        dt = time.time() - t0
        print(f"{code:4s} ({group}/{sim}) solved+stored in {dt:5.1f}s "
              f"({nrow} rows)")
        log.write(f"done in {dt:.1f}s\n")
        log.flush()
        return out

    t_all = time.time()
    # BASE: identical in the three folders -> run once from the PTS folder
    folder = FOLDERS["PTS"]
    prebuilt = None
    d = Data(folder)
    cal = Calibration(d)
    m = Model(d, cal)
    prebuilt = (d, cal, m)
    do_run(folder, "ALL", "BASE", "BS", prebuilt)

    for group, folder in FOLDERS.items():
        if group != "PTS":  # 0data.xlsx identical, but rebuild per folder
            d = Data(folder)
            cal = Calibration(d)
            m = Model(d, cal)
            prebuilt = (d, cal, m)
        for sim in SIMS:
            code = f"{PREFIX[group]}{SIM_TO_CODE[sim]}"
            do_run(folder, group, sim, code, prebuilt)

    flong.close()

    sum_path = os.path.join(RESULTS_DIR, "scenario_summary.csv")
    with open(sum_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "group", "sim", "variable", "commodity",
                    "year", "value"])
        for row in summary:
            w.writerow(row[:6] + (repr(float(row[6])),))

    print(f"total {time.time() - t_all:.0f}s")
    print("wrote", long_path)
    print("wrote", sum_path)
    log.close()


if __name__ == "__main__":
    run_all()
