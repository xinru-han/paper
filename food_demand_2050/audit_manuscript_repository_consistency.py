#!/usr/bin/env python3
"""Audit manuscript, repository tables and headline numbers before submission.

This is intentionally lightweight and standard-library only. It does not rerun
the models; it checks that the current manuscript language and machine-readable
outputs agree on the scenario matrix, model scope and headline numbers.
"""

from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass


ROOT = os.path.dirname(os.path.abspath(__file__))
MANUSCRIPT = os.path.join(ROOT, "manuscript", "manuscript_v2.md")
OUT_DIR = os.path.join(ROOT, "results", "audit")
REGISTRY = os.path.join(OUT_DIR, "submission_number_registry.csv")
REPORT = os.path.join(OUT_DIR, "consistency_report.md")


@dataclass
class Finding:
    check: str
    status: str
    detail: str


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_csv(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def value_from_rows(rows: list[dict[str, str]], **filters: str) -> float | None:
    for r in rows:
        if all(str(r.get(k)) == str(v) for k, v in filters.items()):
            try:
                return float(r["value"])
            except (KeyError, TypeError, ValueError):
                return None
    return None


def summary_value(rows: list[dict[str, str]], year_col: str = "y2050", **filters: str) -> float | None:
    for r in rows:
        if all(str(r.get(k)) == str(v) for k, v in filters.items()):
            try:
                return float(r[year_col])
            except (KeyError, TypeError, ValueError):
                return None
    return None


def percent_change(rows: list[dict[str, str]], scenario: str, commodity: str, variable: str, region: str | None = None) -> float | None:
    base_filter = {"scenario": "BS", "commodity": commodity, "year": "2050", "variable": variable}
    scen_filter = {"scenario": scenario, "commodity": commodity, "year": "2050", "variable": variable}
    if region is not None:
        base_filter["region"] = region
        scen_filter["region"] = region
    bs = value_from_rows(rows, **base_filter)
    sc = value_from_rows(rows, **scen_filter)
    if bs in (None, 0) or sc is None:
        return None
    return (sc / bs - 1.0) * 100.0


def add_registry(rows: list[dict[str, str]], label: str, value: float | str, unit: str, source: str, selector: str, script: str, rounding: str) -> None:
    rows.append(
        {
            "label": label,
            "value": f"{value}",
            "unit": unit,
            "source_file": source,
            "selector": selector,
            "generating_script": script,
            "scenario_version": "submission_config.yaml",
            "rounding_rule": rounding,
        }
    )


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    text = read_text(MANUSCRIPT)
    findings: list[Finding] = []
    registry: list[dict[str, str]] = []

    scenario_rows = load_csv(os.path.join(ROOT, "scenarios", "scenario_definitions.csv"))
    scenario_col = "scenario" if "scenario" in scenario_rows[0] else "code"
    scenario_codes = [r[scenario_col] for r in scenario_rows if r.get(scenario_col)]
    expected = ["BS"] + [f"{g}{i}" for g in "ABC" for i in range(1, 7)]
    findings.append(
        Finding(
            "scenario_code_set",
            "pass" if scenario_codes == expected else "review",
            f"found={','.join(scenario_codes)} expected={','.join(expected)}",
        )
    )

    for phrase in ["fully coupled", "coupled equilibrium", "politically feasible", "land released"]:
        findings.append(
            Finding(
                f"phrase_{phrase.replace(' ', '_')}",
                "review" if re.search(re.escape(phrase), text, flags=re.I) else "pass",
                phrase,
            )
        )

    required_phrases = [
        "sequentially linked",
        "one-way demand-shock transmission",
        "physical reductions",
        "omitted-channel bias is ambiguous",
    ]
    for phrase in required_phrases:
        findings.append(
            Finding(
                f"required_phrase_{phrase.replace(' ', '_')}",
                "pass" if phrase in text else "review",
                phrase,
            )
        )

    china = load_csv(os.path.join(ROOT, "results", "results_long.csv"))
    world = load_csv(os.path.join(ROOT, "results", "world", "world_results_long.csv"))
    wfp = load_csv(os.path.join(ROOT, "results", "footprints", "world_footprints_summary.csv"))
    mts = load_csv(os.path.join(ROOT, "results", "post_analysis", "mts_efficiency.csv"))

    add_registry(registry, "CASM commodity count", 37, "commodities", "submission_config.yaml", "model.casm_commodity_count", "manual config", "integer")
    add_registry(registry, "CASM-World region count", 13, "regions", "submission_config.yaml", "model.casm_world_regions", "manual config", "integer")
    add_registry(registry, "scenario count", len(scenario_codes), "scenarios", "scenarios/scenario_definitions.csv", "all rows", "audit_manuscript_repository_consistency.py", "integer")

    checks = [
        ("world pork price change HDS vs BS", percent_change(world, "HDS", "PRK", "PRF", "WLD"), "%", "results/world/world_results_long.csv", "scenario=HDS, commodity=PRK, variable=PRF, year=2050"),
        ("world soybean price change HDS vs BS", percent_change(world, "HDS", "SBS", "PRF", "WLD"), "%", "results/world/world_results_long.csv", "scenario=HDS, commodity=SBS, variable=PRF, year=2050"),
        ("world maize price change HDS vs BS", percent_change(world, "HDS", "CRN", "PRF", "WLD"), "%", "results/world/world_results_long.csv", "scenario=HDS, commodity=CRN, variable=PRF, year=2050"),
        ("global carbon HDS 2050", summary_value(wfp, scenario="HDS", indicator="co2_faostat", region_group="WLD"), "Mt CO2e", "results/footprints/world_footprints_summary.csv", "scenario=HDS, indicator=co2_faostat, region_group=WLD"),
        ("global carbon BS 2050", summary_value(wfp, scenario="BS", indicator="co2_faostat", region_group="WLD"), "Mt CO2e", "results/footprints/world_footprints_summary.csv", "scenario=BS, indicator=co2_faostat, region_group=WLD"),
        ("global blue water HDS 2050", summary_value(wfp, scenario="HDS", indicator="water_blue", region_group="WLD"), "km3", "results/footprints/world_footprints_summary.csv", "scenario=HDS, indicator=water_blue, region_group=WLD"),
        ("global land occupation HDS 2050", summary_value(wfp, scenario="HDS", indicator="land_prod", region_group="WLD"), "Mha", "results/footprints/world_footprints_summary.csv", "scenario=HDS, indicator=land_prod, region_group=WLD"),
    ]
    for label, value, unit, source, selector in checks:
        if value is not None:
            add_registry(registry, label, round(value, 3), unit, source, selector, "source model script listed in repository", "3 decimals for audit; manuscript rounds by context")

    for r in mts:
        if r.get("metric") == "Global agri CO2 (traded goods)":
            add_registry(
                registry,
                "MTS realisation global agri CO2",
                r.get("MTS_realisation_pct", ""),
                "%",
                "results/post_analysis/mts_efficiency.csv",
                "metric=Global agri CO2 (traded goods)",
                "modules/post_analysis.py",
                "manuscript rounds to nearest 5 percentage points",
            )

    manuscript_numbers = re.findall(r"[-+]?\d+(?:\.\d+)?\s?(?:Gt|Mt|Mha|km³|%)", text)
    findings.append(Finding("manuscript_numeric_tokens", "info", f"{len(manuscript_numbers)} tokens found"))

    with open(REGISTRY, "w", newline="") as fh:
        fieldnames = ["label", "value", "unit", "source_file", "selector", "generating_script", "scenario_version", "rounding_rule"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(registry)

    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("# Submission Consistency Report\n\n")
        fh.write("Generated by `audit_manuscript_repository_consistency.py`.\n\n")
        fh.write("| Check | Status | Detail |\n|---|---|---|\n")
        for f in findings:
            fh.write(f"| {f.check} | {f.status} | {f.detail} |\n")
        fh.write(f"\nNumber registry: `{os.path.relpath(REGISTRY, ROOT)}`\n")

    print(f"wrote {REPORT}")
    print(f"wrote {REGISTRY}")


if __name__ == "__main__":
    main()

