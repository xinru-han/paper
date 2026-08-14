# -*- coding: utf-8 -*-
"""Combine all unified-path results into one submission workbook and summary."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
META = RESULTS / "meta"
CASM = RESULTS / "casm"


def main():
    strict = pd.read_csv(DATA / "analysis_dataset_strict.csv", encoding="utf-8-sig")
    counts = pd.crosstab(strict["Target"], strict["Path"], margins=True) \
        .rename_axis("Target").reset_index()
    meta = pd.read_csv(META / "meta_random_effects.csv", encoding="utf-8-sig")
    wls = pd.read_csv(META / "wls_meta_regression.csv", encoding="utf-8-sig")
    wls_notes = pd.read_excel(META / "meta_analysis_results.xlsx", sheet_name="wls_model_notes")
    fat = pd.read_csv(META / "fat_pet_peese.csv", encoding="utf-8-sig")
    drops = pd.read_csv(META / "outlier_filter_log.csv", encoding="utf-8-sig")
    elasticities = pd.read_csv(CASM / "path_elasticities.csv", encoding="utf-8-sig")
    plan = pd.read_csv(CASM / "scenario_plan.csv", encoding="utf-8-sig")
    grain = pd.read_csv(CASM / "table_grain_2030.csv", encoding="utf-8-sig")
    security = pd.read_csv(CASM / "table_food_security_2030.csv", encoding="utf-8-sig")
    run_log = pd.read_csv(CASM / "casm_run_log.csv", encoding="utf-8-sig")

    with pd.ExcelWriter(RESULTS / "all_results_summary.xlsx", engine="openpyxl") as writer:
        counts.to_excel(writer, index=False, sheet_name="sample_counts")
        meta.to_excel(writer, index=False, sheet_name="meta_random_effects")
        wls.to_excel(writer, index=False, sheet_name="wls_meta_regression")
        wls_notes.to_excel(writer, index=False, sheet_name="wls_model_notes")
        fat.to_excel(writer, index=False, sheet_name="fat_pet_peese")
        drops.to_excel(writer, index=False, sheet_name="outlier_filter_log")
        elasticities.to_excel(writer, index=False, sheet_name="path_elasticities")
        plan.to_excel(writer, index=False, sheet_name="scenario_shocks")
        grain.to_excel(writer, index=False, sheet_name="casm_grain_2030")
        security.to_excel(writer, index=False, sheet_name="casm_food_security")
        run_log.to_excel(writer, index=False, sheet_name="casm_run_log")

    overall = meta[(meta["stage"] == "overall_full") & (meta["Path"] == "ALL")]
    subgroup = meta[meta["stage"] == "path_subgroup"]
    lines = [
        "# Unified MCI/AMS/AML results",
        "",
        "## Strict analysis sample",
        "",
        counts.to_markdown(index=False),
        "",
        "## Overall DL random-effects results",
        "",
        overall[["Target", "k", "PCC", "SE", "p", "significance",
                 "CI_low", "CI_high", "I2"]].to_markdown(index=False),
        "",
        "## Path subgroup results",
        "",
        subgroup[["Target", "Path", "k", "PCC", "p", "significance",
                  "interpretation_note"]].to_markdown(index=False),
        "",
        "Yield-AML and Efficiency-AML each contain one record. Area contains no MCI "
        "record; its WLS path comparison therefore uses AMS as the estimable baseline "
        "and should be interpreted as exploratory.",
        "",
        "## CASM shocks",
        "",
        plan[["scenario", "Path", "yield_shifter_pct_per_year",
              "area_shifter_pct_per_year"]].to_markdown(index=False),
        "",
        "## CASM 2030 grain results",
        "",
        grain.to_markdown(index=False),
        "",
        "All ten CASM runs completed without an exception: "
        f"{bool(run_log['completed_without_exception'].all())}.",
    ]
    (RESULTS / "RESULTS_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {RESULTS / 'all_results_summary.xlsx'}")


if __name__ == "__main__":
    main()
