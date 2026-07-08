# -*- coding: utf-8 -*-
"""CASM模拟方案设计：把新Meta证据映射为"十五五"机械化政策情景。

沿用论文的 3路径 × 3速度 设计（S1农机资本投入 / S2农机社会化服务 /
S3综合机械化水平 × Medium/High/Low），但技术冲击参数改用check后数据
重新估计的 路径×维度 弹性中位数，并按以下证据规则设定：

  单产Shifter(%/年) = 弹性中位数 × 代理指标年均增速(%)
  面积Shifter(%/年) = 弹性中位数 × 代理指标年均增速(%)

  纳入规则（保守）：
  - 单产冲击：合并PCC为正，且(PCC显著(10%,KH) 或 弹性样本k>=3)时按中位数纳入；
    证据不足(k=1)的AML路径仍纳入以保持三路径可比，但标记高不确定性。
  - 面积冲击：check后 MCI 仅有单篇宏观极端值(E_24, e=0.584)不予采信，设0；
    AMS 合并PCC不显著且唯一弹性为服务价格弹性(P_31, -0.221)，无法映射为
    数量冲击，设0（与原论文正向小幅冲击不同——check后证据不再支持）；
    AML 保留小幅冲击(P_19, e=0.015)，标记探索性。

代理指标增速沿用论文（"十四五"实际增速为Medium）：
  S1 农机总动力      2.4 / 3.4 / 1.4  %/年
  S2 农机托管作业面积 2.8 / 3.8 / 1.8  %/年
  S3 耕种收综合机械化率 +0.86 / +1.86 / +0.10 个百分点/年（2025基期76.7%）

冲击对象：CASM粮食作物集合 CGRN = RICE WHEA MAIZ SOYS BARL OTGR SORG，
冲击期：2026-2030（"十五五"），叠加在基准增长率之上。

输出：results/casm/simulation_plan.csv
"""
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(BASE, "results", "meta")
OUT = os.path.join(BASE, "results", "casm")
os.makedirs(OUT, exist_ok=True)

el = pd.read_csv(os.path.join(META, "elasticity_track.csv"),
                 encoding="utf-8-sig").set_index(["Target", "Path"])


def emed(target, path):
    try:
        r = el.loc[(target, path)]
        return float(r["elast_median"]), int(r["k_elast"]), str(r["elast_type"])
    except KeyError:
        return np.nan, 0, "none"


E_Y_MCI, kY_MCI, tY_MCI = emed("Yield", "MCI")
E_Y_AMS, kY_AMS, tY_AMS = emed("Yield", "AMS")
E_Y_AML, kY_AML, tY_AML = emed("Yield", "AML")
E_A_AML, kA_AML, _ = emed("Area", "AML")

# 面积冲击证据规则（见docstring）
AREA_E = {"MCI": 0.0, "AMS": 0.0, "AML": E_A_AML}

# 代理指标年均增速（%）；S3由百分点换算：pp/76.7*100
S3_BASE = 76.7
PROXY = {
    "S1": dict(path="MCI", 路径="农机资本投入", 代理指标="全国农业机械总动力",
               速度={"Medium": 2.4, "High": 3.4, "Low": 1.4}, 单位="%/年",
               E_yield=E_Y_MCI, k_yield=kY_MCI, 弹性口径=tY_MCI),
    "S2": dict(path="AMS", 路径="农机社会化服务", 代理指标="全国农机托管作业面积",
               速度={"Medium": 2.8, "High": 3.8, "Low": 1.8}, 单位="%/年",
               E_yield=E_Y_AMS, k_yield=kY_AMS, 弹性口径=tY_AMS),
    "S3": dict(path="AML", 路径="综合机械化水平", 代理指标="耕种收综合机械化率",
               速度={"Medium": 0.86 / S3_BASE * 100,
                     "High": 1.86 / S3_BASE * 100,
                     "Low": 0.10 / S3_BASE * 100}, 单位="个百分点→%/年",
               E_yield=E_Y_AML, k_yield=kY_AML, 弹性口径=tY_AML),
}

NOTES = {
    "S1": "单产弹性0.178(k=6,全弹性)；合并PCC=+0.097经KH校正后不显著，"
          "结果作政策潜力解释；面积冲击=0（单篇极端值不采信）",
    "S2": "单产弹性0.164(k=6,半弹性近似,虚拟变量文献)；合并PCC=+0.095***稳健；"
          "面积冲击=0（check后AMS面积证据不再支持正向冲击）",
    "S3": "单产弹性0.182(k=1,P_02,高不确定性)；面积弹性0.015(k=1,P_19,探索性)",
}

rows = []
for s, cfg in PROXY.items():
    for spd, g in cfg["速度"].items():
        y_shift = cfg["E_yield"] * g
        a_shift = AREA_E[cfg["path"]] * g
        rows.append({
            "情景": f"{s}-{spd}",
            "机械化路径": f"{cfg['路径']}({cfg['path']})",
            "代理指标": cfg["代理指标"],
            "代理指标年均增速(%)": round(g, 3),
            "单产弹性中位数": round(cfg["E_yield"], 4),
            "单产弹性样本k": cfg["k_yield"],
            "单产弹性口径": cfg["弹性口径"],
            "面积弹性": round(AREA_E[cfg["path"]], 4),
            "每年单产Shifter(%)": round(y_shift, 4),
            "每年面积Shifter(%)": round(a_shift, 4),
            "冲击作物": "CGRN(RICE,WHEA,MAIZ,SOYS,BARL,OTGR,SORG)",
            "冲击年份": "2026-2030",
            "施加方式": "叠加于基准AYGR0/AAGR0之上",
            "证据说明": NOTES[s],
        })

plan = pd.DataFrame(rows)
plan.to_csv(os.path.join(OUT, "simulation_plan.csv"),
            index=False, encoding="utf-8-sig")
print(plan[["情景", "代理指标年均增速(%)", "每年单产Shifter(%)",
            "每年面积Shifter(%)"]].to_string(index=False))
print("\n模拟方案已写入 results/casm/simulation_plan.csv")
