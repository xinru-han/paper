# -*- coding: utf-8 -*-
"""CASM模拟方案 v3：基于扩充样本(419条效应量/48篇)的RVE估计。

参数映射（单锚点PCC校准法）：
  不同文献的弹性换算口径噪声大（level换算、虚拟变量半弹性等），而PCC是
  统一无量纲标准化效应。故用"单产维度"作锚：
      λ = E_yield_pooled / PCC_yield_pooled
  其中 E_yield_pooled = 单产全路径文献层面弹性中位数（先文献内中位、再
  文献间中位，|e|<1），PCC_yield_pooled = 单产RVE合并PCC。
  各 路径×维度 弹性 = λ × 该单元RVE合并PCC；
  单元合并PCC在10%水平不显著者冲击记0；
  Yield-AML子组文献不足，取中性假设（=单产全样本合并PCC），Meta回归显示
  的AML正溢价作为上行情景解释（notes注明）。

情景框架与代理指标增速沿用论文（3路径×3速度，"十四五"实际增速=Medium）。
输出：results/casm_v3/simulation_plan_v3.csv
"""
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(BASE, "results", "meta_v3")
OUT = os.path.join(BASE, "results", "casm_v3")
os.makedirs(OUT, exist_ok=True)

# ---- 锚点：单产全路径弹性中位数（两步中位） ----
eff = pd.read_csv(os.path.join(BASE, "data", "meta_effects_expanded.csv"),
                  encoding="utf-8-sig")
ely = eff[(eff["Target"] == "Yield") & (eff["elasticity"].abs() < 1)]
E_yield_pooled = ely.groupby("study_id")["elasticity"].median().median()

t2 = pd.read_csv(os.path.join(META, "table2_subgroup_rve.csv"),
                 encoding="utf-8-sig")


def pcc(dim, path):
    r = t2[(t2["维度"] == dim) & (t2["路径"] == path)]
    if len(r) == 0:
        return np.nan, np.nan
    return float(r["合并PCC"].iloc[0]), float(r["p值"].iloc[0])


PCC_Y_ALL, _ = pcc("粮食单产", "ALL")
lam = E_yield_pooled / PCC_Y_ALL
print(f"锚点: E_yield_pooled={E_yield_pooled:.4f}, PCC_yield_ALL={PCC_Y_ALL:.3f}, "
      f"λ={lam:.4f}")


def cell_elast(dim, path, neutral=None):
    """λ×合并PCC；不显著(10%)记0；neutral给出替代PCC。"""
    p, pv = pcc(dim, path)
    if not np.isfinite(p):
        if neutral is None:
            return 0.0, "无子组估计"
        return lam * neutral, f"子组文献不足，取中性假设PCC={neutral:.3f}"
    if pv > 0.10:
        return 0.0, f"合并PCC={p:+.3f}不显著(p={pv:.3f})，冲击=0"
    return lam * p, f"合并PCC={p:+.3f}(p={pv:.3f})"


E = {}
NOTES = {}
E[("Yield", "MCI")], NOTES[("Yield", "MCI")] = cell_elast("粮食单产", "MCI")
E[("Yield", "AMS")], NOTES[("Yield", "AMS")] = cell_elast("粮食单产", "AMS")
E[("Yield", "AML")], NOTES[("Yield", "AML")] = cell_elast("粮食单产", "AML",
                                                          neutral=PCC_Y_ALL)
E[("Area", "MCI")], NOTES[("Area", "MCI")] = cell_elast("播种面积", "MCI")
E[("Area", "AMS")], NOTES[("Area", "AMS")] = cell_elast("播种面积", "AMS")
E[("Area", "AML")], NOTES[("Area", "AML")] = cell_elast("播种面积", "AML")

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

rows = []
for s, cfg in PROXY.items():
    p = cfg["path"]
    for spd, g in cfg["速度"].items():
        ey, ea = E[("Yield", p)], E[("Area", p)]
        rows.append({
            "情景": f"{s}-{spd}",
            "机械化路径": f"{cfg['路径']}({p})",
            "代理指标": cfg["代理指标"],
            "代理指标年均增速(%)": round(g, 3),
            "单产弹性(λ×PCC)": round(ey, 4),
            "面积弹性(λ×PCC)": round(ea, 4),
            "每年单产Shifter(%)": round(ey * g, 4),
            "每年面积Shifter(%)": round(ea * g, 4),
            "冲击作物": "CGRN(RICE,WHEA,MAIZ,SOYS,BARL,OTGR,SORG)",
            "冲击年份": "2026-2030",
            "施加方式": "叠加于基准AYGR0/AAGR0之上",
            "单产证据": NOTES[("Yield", p)],
            "面积证据": NOTES[("Area", p)],
        })

plan = pd.DataFrame(rows)
meta_row = pd.DataFrame([{"情景": "映射公式",
                          "机械化路径": f"λ=E_yield_pooled/PCC_yield_ALL"
                                        f"={E_yield_pooled:.4f}/{PCC_Y_ALL:.3f}"
                                        f"={lam:.4f}",
                          "代理指标": "弹性=λ×单元RVE合并PCC；10%不显著记0"}])
pd.concat([plan, meta_row], ignore_index=True).to_csv(
    os.path.join(OUT, "simulation_plan_v3.csv"), index=False,
    encoding="utf-8-sig")
print(plan[["情景", "代理指标年均增速(%)", "每年单产Shifter(%)",
            "每年面积Shifter(%)"]].to_string(index=False))
print("\n已写入 results/casm_v3/simulation_plan_v3.csv")
