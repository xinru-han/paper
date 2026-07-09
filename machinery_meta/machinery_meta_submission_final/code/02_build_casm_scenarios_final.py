# -*- coding: utf-8 -*-
"""Build CASM machinery scenarios from the verified final meta evidence.

Scenario design follows the first-draft 3 paths x 3 speeds structure:
S1=MCI, S2=AMS, S3=AML. Shifters are annual percentage-point additions to
CASM baseline growth rates, applied to CGRN in 2026-2030.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path("/root/data/Paper/农机Meta")
ARCHIVE = PROJECT / "machinery_meta_submission_final"
RESULTS = ARCHIVE / "results" / "casm"
DATA = ARCHIVE / "data"
REMOVE_IDS = {"E_22", "E_24"}

S3_BASE = 76.7
PROXY = {
    "S1": dict(path="MCI", path_cn="农机资本投入", proxy="全国农业机械总动力",
               speed={"Low": 1.4, "Medium": 2.4, "High": 3.4}),
    "S2": dict(path="AMS", path_cn="农机社会化服务", proxy="全国农机托管作业面积",
               speed={"Low": 1.8, "Medium": 2.8, "High": 3.8}),
    "S3": dict(path="AML", path_cn="综合机械化水平", proxy="耕种收综合机械化率",
               speed={"Low": 0.10 / S3_BASE * 100,
                      "Medium": 0.86 / S3_BASE * 100,
                      "High": 1.86 / S3_BASE * 100}),
}


def proxy_delta_per_year(scenario, speed_value_pct):
    """Annualized proxy change used in the first-draft Table 7 comparison.

    S1/S2 are stated as annual growth rates. The table converts the five-year
    cumulative change into an average annual change before multiplying by the
    meta elasticity. S3 is a percentage-point change divided by the 2025 base.
    """
    if scenario in {"S1", "S2"}:
        g = speed_value_pct / 100
        return ((1 + g) ** 5 - 1) / 5 * 100
    return speed_value_pct


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv("/root/paper/machinery_meta/data/meta_base_dataset.csv")
    df = df[~df["编号"].isin(REMOVE_IDS)].copy()
    df["elasticity"] = pd.to_numeric(df["elasticity"], errors="coerce")
    df["N"] = pd.to_numeric(df["N"], errors="coerce")
    df.to_csv(DATA / "meta_base_dataset_final.csv", index=False, encoding="utf-8-sig")

    work = df[df["elasticity"].notna() & (df["elasticity"].abs() < 0.99)].copy()
    elastic_rows = []
    for scenario, cfg in PROXY.items():
        for target in ["Yield", "Area"]:
            g = work[(work["Path"] == cfg["path"]) & (work["Target"] == target)]
            if len(g):
                med = g["elasticity"].median()
                mean = g["elasticity"].mean()
                wavg = np.average(g["elasticity"], weights=g["N"].fillna(0)) if g["N"].fillna(0).sum() > 0 else np.nan
            else:
                med = mean = wavg = np.nan
            used = med
            note = "按Path中位数；去除|elasticity|>=0.99；最终样本"
            if scenario == "S1" and target == "Area":
                used = 0.0
                note += "；沿用原方案S1不冲击面积"
            elastic_rows.append(dict(scenario=scenario, Path=cfg["path"], Target=target, k=len(g),
                                     elasticity_median=med, elasticity_mean=mean,
                                     elasticity_N_weighted=wavg,
                                     elasticity_used_for_shifter=used, note=note))
    elastic = pd.DataFrame(elastic_rows)

    rows = []
    for scenario, cfg in PROXY.items():
        ey = float(elastic[(elastic["scenario"] == scenario) & (elastic["Target"] == "Yield")]
                   ["elasticity_used_for_shifter"].iloc[0])
        ea = float(elastic[(elastic["scenario"] == scenario) & (elastic["Target"] == "Area")]
                   ["elasticity_used_for_shifter"].iloc[0])
        for level, raw_g in cfg["speed"].items():
            g = proxy_delta_per_year(scenario, raw_g)
            rows.append({
                "scenario": f"{scenario}-{level}",
                "scenario_group": scenario,
                "speed": level,
                "Path": cfg["path"],
                "机械化路径": f"{cfg['path_cn']}({cfg['path']})",
                "代理指标": cfg["proxy"],
                "代理指标原始速度(%)": round(raw_g, 6),
                "代理指标年均化增幅(%)": round(g, 6),
                "单产弹性": round(ey, 6),
                "面积弹性": round(ea, 6),
                "每年单产Shifter(%)": round(ey * g, 6),
                "每年面积Shifter(%)": round(ea * g, 6),
                "冲击作物": "CGRN(RICE,WHEA,MAIZ,SOYS,BARL,OTGR,SORG)",
                "冲击年份": "2026-2030",
                "施加方式": "叠加于基准AYGR0/AAGR0之上",
            })
    plan = pd.DataFrame(rows)

    with pd.ExcelWriter(RESULTS / "casm_scenario_plan_final.xlsx", engine="openpyxl") as writer:
        plan.to_excel(writer, index=False, sheet_name="simulation_plan")
        elastic.to_excel(writer, index=False, sheet_name="path_elasticities")
    plan.to_csv(RESULTS / "simulation_plan_final.csv", index=False, encoding="utf-8-sig")
    elastic.to_csv(RESULTS / "path_elasticities_final.csv", index=False, encoding="utf-8-sig")
    print(plan[["scenario", "代理指标年均化增幅(%)", "每年单产Shifter(%)", "每年面积Shifter(%)"]].to_string(index=False))


if __name__ == "__main__":
    main()
