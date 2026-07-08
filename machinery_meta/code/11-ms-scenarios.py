# -*- coding: utf-8 -*-
"""ms版CASM模拟方案：与manuscript表7同构（3路径×3速度），
Shifter=弹性中位数×代理指标年均增速（式25），弹性用ms版重算中位数。

与manuscript的差异仅为数字更新与内部一致化：
  - 单产弹性：MCI 0.163(k=14) / AMS 0.164(k=6) / AML 0.185(k=5)
    （manuscript表6为0.171/0.147/0.185；本版按式25统一，修复表6-表7不一致）
  - 面积弹性：MCI 0（合并PCC为负，与manuscript一致不设正向冲击）；
    AMS 0.0235(P_12)；AML 0.015(P_19)——与manuscript同源同值；
    P_08(服务市场发育,半弹性0.407)按manuscript口径不纳入AML面积弹性。
输出 results/casm_ms/simulation_plan_ms.csv
"""
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(BASE, "results", "meta_ms")
OUT = os.path.join(BASE, "results", "casm_ms")
os.makedirs(OUT, exist_ok=True)

el = pd.read_csv(os.path.join(META, "elasticity_medians_ms.csv"),
                 encoding="utf-8-sig").set_index(["Target", "Path"])

E_Y = {p: float(el.loc[("Yield", p), "elast_median"]) for p in
       ["MCI", "AMS", "AML"]}
# 面积：MCI合并PCC为负不设正向冲击；AML按manuscript仅取P_19（排除P_08半弹性）
E_A = {"MCI": 0.0, "AMS": float(el.loc[("Area", "AMS"), "elast_median"]),
       "AML": 0.015}

S3_BASE = 76.7
PROXY = {
    "S1": dict(path="MCI", 路径="农机资本投入", 代理指标="全国农业机械总动力",
               速度={"Medium": 2.4, "High": 3.4, "Low": 1.4}),
    "S2": dict(path="AMS", 路径="农机社会化服务", 代理指标="全国农机托管作业面积",
               速度={"Medium": 2.8, "High": 3.8, "Low": 1.8}),
    "S3": dict(path="AML", 路径="综合机械化水平", 代理指标="耕种收综合机械化率",
               速度={"Medium": 0.86 / S3_BASE * 100,
                     "High": 1.86 / S3_BASE * 100,
                     "Low": 0.10 / S3_BASE * 100}),
}
NOTE = {
    "S1": "单产弹性0.163(k=14)；面积合并PCC为负→不设正向面积冲击（同manuscript）",
    "S2": "单产弹性0.164(k=6)；面积弹性0.0235(P_12,k=1)小幅冲击（同manuscript）",
    "S3": "单产弹性0.185(k=5,与manuscript表6一致)；面积弹性0.015(P_19,k=1)",
}

rows = []
for s, cfg in PROXY.items():
    p = cfg["path"]
    for spd, g in cfg["速度"].items():
        rows.append({
            "情景": f"{s}-{spd}",
            "机械化路径": f"{cfg['路径']}({p})",
            "代理指标": cfg["代理指标"],
            "代理指标年均增速(%)": round(g, 3),
            "单产弹性中位数": round(E_Y[p], 4),
            "面积弹性": round(E_A[p], 4),
            "每年单产Shifter(%)": round(E_Y[p] * g, 4),
            "每年面积Shifter(%)": round(E_A[p] * g, 4),
            "冲击作物": "CGRN(RICE,WHEA,MAIZ,SOYS,BARL,OTGR,SORG)",
            "冲击年份": "2026-2030",
            "施加方式": "叠加于基准AYGR0/AAGR0之上",
            "证据说明": NOTE[s],
        })

plan = pd.DataFrame(rows)
plan.to_csv(os.path.join(OUT, "simulation_plan_ms.csv"), index=False,
            encoding="utf-8-sig")
print(plan[["情景", "代理指标年均增速(%)", "每年单产Shifter(%)",
            "每年面积Shifter(%)"]].to_string(index=False))
print("\n已写入 results/casm_ms/simulation_plan_ms.csv")
