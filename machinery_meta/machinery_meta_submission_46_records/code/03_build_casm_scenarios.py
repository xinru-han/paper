# -*- coding: utf-8 -*-
"""Build CASM shocks from the same unified strict-path analysis dataset."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "results" / "casm"
INPUT = DATA / "analysis_dataset_strict.csv"

S3_BASE = 76.7
PROXIES = {
    "S1": {
        "Path": "MCI",
        "path_name": "Machinery capital input",
        "proxy": "Total agricultural machinery power",
        "speeds": {"Low": 1.4, "Medium": 2.4, "High": 3.4},
    },
    "S2": {
        "Path": "AMS",
        "path_name": "Agricultural machinery services",
        "proxy": "Machinery trusteeship operation area",
        "speeds": {"Low": 1.8, "Medium": 2.8, "High": 3.8},
    },
    "S3": {
        "Path": "AML",
        "path_name": "Comprehensive mechanisation level",
        "proxy": "Comprehensive cultivation-planting-harvesting mechanisation rate",
        "speeds": {
            "Low": 0.10 / S3_BASE * 100,
            "Medium": 0.86 / S3_BASE * 100,
            "High": 1.86 / S3_BASE * 100,
        },
    },
}


def annualized_proxy_change(scenario, raw_speed_pct):
    if scenario in {"S1", "S2"}:
        growth = raw_speed_pct / 100
        return ((1 + growth) ** 5 - 1) / 5 * 100
    return raw_speed_pct


def build_path_elasticities(df):
    valid = df[df["elasticity"].notna() & (df["elasticity"].abs() < 0.99)].copy()
    rows = []
    for scenario, config in PROXIES.items():
        for target in ["Yield", "Area"]:
            cell = valid[(valid["Path"] == config["Path"]) & (valid["Target"] == target)]
            median = cell["elasticity"].median() if len(cell) else np.nan
            mean = cell["elasticity"].mean() if len(cell) else np.nan
            n_weighted = (
                np.average(cell["elasticity"], weights=cell["N"])
                if len(cell) and cell["N"].sum() > 0 else np.nan
            )
            used = median
            note = "Strict Path median; records with |elasticity| >= 0.99 excluded"
            if scenario == "S1" and target == "Area":
                used = 0.0
                note += "; original S1 design retains zero area shock"
            rows.append({
                "scenario_group": scenario,
                "Path": config["Path"],
                "Target": target,
                "k_elasticity": len(cell),
                "record_ids": ";".join(cell["编号"].astype(str)),
                "elasticity_median": median,
                "elasticity_mean": mean,
                "elasticity_N_weighted": n_weighted,
                "elasticity_used": used,
                "note": note,
            })
    return pd.DataFrame(rows)


def build_plan(elasticities):
    rows = []
    for scenario, config in PROXIES.items():
        yield_elasticity = elasticities.loc[
            (elasticities["scenario_group"] == scenario)
            & (elasticities["Target"] == "Yield"), "elasticity_used"
        ].iloc[0]
        area_elasticity = elasticities.loc[
            (elasticities["scenario_group"] == scenario)
            & (elasticities["Target"] == "Area"), "elasticity_used"
        ].iloc[0]
        if pd.isna(yield_elasticity) or pd.isna(area_elasticity):
            raise ValueError(f"Missing scenario elasticity for {scenario}")
        for speed, raw_speed in config["speeds"].items():
            annual_change = annualized_proxy_change(scenario, raw_speed)
            rows.append({
                "scenario": f"{scenario}-{speed}",
                "scenario_group": scenario,
                "speed": speed,
                "Path": config["Path"],
                "path_name": config["path_name"],
                "proxy_indicator": config["proxy"],
                "proxy_raw_speed_pct": round(raw_speed, 6),
                "proxy_annualized_change_pct": round(annual_change, 6),
                "yield_elasticity": round(yield_elasticity, 6),
                "area_elasticity": round(area_elasticity, 6),
                "yield_shifter_pct_per_year": round(yield_elasticity * annual_change, 6),
                "area_shifter_pct_per_year": round(area_elasticity * annual_change, 6),
                "shocked_crops": "CGRN(RICE,WHEA,MAIZ,SOYS,BARL,OTGR,SORG)",
                "shock_years": "2026-2030",
                "application": "Added to baseline AYGR0 and AAGR0 growth rates",
            })
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT, encoding="utf-8-sig")
    for column in ["N", "elasticity"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if not set(df["Path"]).issubset({"MCI", "AMS", "AML"}):
        raise ValueError("CASM input contains a non-analysis path")

    elasticities = build_path_elasticities(df)
    plan = build_plan(elasticities)
    elasticities.to_csv(OUT / "path_elasticities.csv", index=False, encoding="utf-8-sig")
    plan.to_csv(OUT / "scenario_plan.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(OUT / "casm_scenario_plan.xlsx", engine="openpyxl") as writer:
        plan.to_excel(writer, index=False, sheet_name="scenario_plan")
        elasticities.to_excel(writer, index=False, sheet_name="path_elasticities")
    print(plan[["scenario", "Path", "yield_shifter_pct_per_year",
                "area_shifter_pct_per_year"]].to_string(index=False))


if __name__ == "__main__":
    main()
