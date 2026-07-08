# -*- coding: utf-8 -*-
"""按 simulation_plan.csv 运行CASM（Python版）机械化情景模拟。

模型：/root/data/CASM/casm_py/base 的副本（casm_model/，含独立输入数据，
不触碰原模型）。冲击实现：把每年单产/面积Shifter叠加到基准 AYGR0/AAGR0
（粮食作物CGRN，2026-2030），通过 run_base(growth_overrides=...) 求解。

输出（results/casm/）：
  casm_results_long.csv     基线+9情景 × 品种 × 年份 明细
  table7_grain.csv          粮食总量：产量/净贸易/自给率/面积/单产（2030）
  table8_cereal_staple.csv  谷物与口粮安全（2030）
"""
import os
import sys
import time

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "casm_model"))
CASM_DIR = os.path.join(BASE, "casm_model", "inputs")
OUT = os.path.join(BASE, "results", "casm")
os.makedirs(OUT, exist_ok=True)

from casm.simulate import run_base, Growth
from casm.data import Data

SHOCK_YEARS = [str(y) for y in range(2026, 2031)]
REPORT_YEAR = "2030"

plan = pd.read_csv(os.path.join(OUT, "simulation_plan.csv"),
                   encoding="utf-8-sig")

d0 = Data(CASM_DIR)
CGRN, CCRL, CKOUL = d0.CGRN, d0.CCRL, d0.CKOUL
gr0 = Growth(CASM_DIR)   # 基准增长率（%）


def make_overrides(y_shift, a_shift):
    """基准AYGR0/AAGR0 + Shifter（百分点，%单位），粮食作物×冲击年份。"""
    ov = {"AYGR0": {}, "AAGR0": {}}
    for c in CGRN:
        for t in SHOCK_YEARS:
            base_y = gr0.raw["AYGR0"].get((c, "BASE", t), 0.0)
            base_a = gr0.raw["AAGR0"].get((c, "BASE", t), 0.0)
            ov["AYGR0"][(c, t)] = base_y + y_shift
            ov["AAGR0"][(c, t)] = base_a + a_shift
    return ov


def extract(res, d):
    """返回 DataFrame: index=crop, cols=[QX, AC, YC, QM, QE] at each year."""
    out = {}
    years = sorted(res["QX"].keys())
    for t in years:
        df = pd.DataFrame({
            "QX": res["QX"][t], "AC": res["AC"][t], "YC": res["YC"][t],
            "QM": np.maximum(res["QM"][t] - res["QE"][t], 0.0),
            "QE": np.maximum(res["QE"][t] - res["QM"][t], 0.0),
        }, index=d.C)
        out[t] = df
    return out


runs = [("BASE", 0.0, 0.0)]
for _, r in plan.iterrows():
    runs.append((r["情景"], float(r["每年单产Shifter(%)"]),
                 float(r["每年面积Shifter(%)"])))

results = {}
for name, ys, as_ in runs:
    t0 = time.time()
    ov = None if name == "BASE" else make_overrides(ys, as_)
    d, cal, m, res = run_base(CASM_DIR, growth_overrides=ov)
    results[name] = extract(res, d)
    print(f"{name:10s} 单产Shifter={ys:.4f}%/年 面积Shifter={as_:.4f}%/年 "
          f"求解完成 {time.time()-t0:.1f}s", flush=True)

# ------------------------------------------------------------- 明细长表
long_rows = []
for name, byyear in results.items():
    for t, df in byyear.items():
        for c in df.index:
            long_rows.append(dict(scenario=name, year=t, crop=c,
                                  QX=df.loc[c, "QX"], AC=df.loc[c, "AC"],
                                  YC=df.loc[c, "YC"], NETQM=df.loc[c, "QM"] - df.loc[c, "QE"]))
pd.DataFrame(long_rows).to_csv(os.path.join(OUT, "casm_results_long.csv"),
                               index=False, encoding="utf-8-sig")


def agg(name, crops, year=REPORT_YEAR):
    df = results[name][year].loc[crops]
    qx, ac = df["QX"].sum(), df["AC"].sum()
    net = (df["QM"] - df["QE"]).sum()
    ssr = qx / (qx + net) * 100
    return qx, ac, net, ssr


# ------------------------------------------------------------- 表7 粮食
b_qx, b_ac, b_net, b_ssr = agg("BASE", CGRN)
rows7 = [dict(情景="基准", 产量_万吨=round(b_qx, 0), 产量变化_pct="—",
              净贸易_万吨=round(b_net, 0), 自给率_pct=round(b_ssr, 2),
              面积_亿亩=round(b_ac * 15 / 10000, 4), 单产变化_pct="—")]
for name, _, _ in runs[1:]:
    qx, ac, net, ssr = agg(name, CGRN)
    yld_chg = (qx / ac) / (b_qx / b_ac) - 1
    rows7.append(dict(情景=name, 产量_万吨=round(qx, 0),
                      产量变化_pct=round((qx / b_qx - 1) * 100, 2),
                      净贸易_万吨=round(net, 0), 自给率_pct=round(ssr, 2),
                      面积_亿亩=round(ac * 15 / 10000, 4),
                      单产变化_pct=round(yld_chg * 100, 2)))
t7 = pd.DataFrame(rows7)
t7.to_csv(os.path.join(OUT, "table7_grain.csv"), index=False,
          encoding="utf-8-sig")
print("\n== 表7 粮食总量（2030）==")
print(t7.to_string(index=False))

# ------------------------------------------------- 表8 谷物与口粮
rows8 = []
for name, _, _ in runs:
    disp = "基准" if name == "BASE" else name
    rec = dict(情景=disp)
    for lab, cs in (("谷物", CCRL), ("口粮", CKOUL)):
        qx, ac, net, ssr = agg(name, cs)
        rec[f"{lab}产量_万吨"] = round(qx, 0)
        rec[f"{lab}自给率_pct"] = round(ssr, 2)
        rec[f"{lab}净贸易_万吨"] = round(net, 0)
    rows8.append(rec)
t8 = pd.DataFrame(rows8)
t8.to_csv(os.path.join(OUT, "table8_cereal_staple.csv"), index=False,
          encoding="utf-8-sig")
print("\n== 表8 谷物与口粮安全（2030）==")
print(t8.to_string(index=False))
