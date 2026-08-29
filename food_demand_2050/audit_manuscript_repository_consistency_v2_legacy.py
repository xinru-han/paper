#!/usr/bin/env python3
"""Legacy audit for manuscript_v2 and the superseded 13-region result set.

Do not use this script to audit the canonical CASM-World V3 manuscript. It is
retained only to preserve the old result chain's provenance.
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
CLAIMS = os.path.join(OUT_DIR, "claims_registry.csv")
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


def add_claim(rows: list[dict[str, str]], claim_id: str, section: str,
              text: str, source_file: str, selector: str, operation: str,
              expected: float, actual: float | None, tolerance: float,
              unit: str) -> None:
    if actual is None:
        status = "missing"
        diff = ""
    else:
        diff_value = actual - expected
        diff = f"{diff_value:.6g}"
        status = "pass" if abs(diff_value) <= tolerance else "review"
    rows.append({
        "claim_id": claim_id,
        "manuscript_section": section,
        "claim_text": text,
        "source_file": source_file,
        "filter": selector,
        "operation": operation,
        "expected_value": f"{expected}",
        "actual_value": "" if actual is None else f"{actual:.6g}",
        "tolerance": f"{tolerance}",
        "unit": unit,
        "difference": diff,
        "status": status,
    })


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    text = read_text(MANUSCRIPT)
    findings: list[Finding] = []
    registry: list[dict[str, str]] = []
    claims: list[dict[str, str]] = []

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
    direct = load_csv(os.path.join(ROOT, "results", "footprints", "direct_production_account_summary.csv"))
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

    def direct_total(scenario: str, indicator: str, region: str, year: str = "2050") -> float | None:
        total = 0.0
        found = False
        for r in direct:
            if (r.get("scenario") == scenario and r.get("indicator") == indicator
                    and r.get("year") == year and r.get("geography") == "World"):
                if region == "WLD" or r.get("region") == region:
                    total += float(r["value"])
                    found = True
        return total if found else None

    def direct_ex_china(scenario: str, indicator: str, year: str = "2050") -> float | None:
        total = 0.0
        found = False
        for r in direct:
            if (r.get("scenario") == scenario and r.get("indicator") == indicator
                    and r.get("year") == year and r.get("geography") == "World"
                    and r.get("region") != "CHN"):
                total += float(r["value"])
                found = True
        return total if found else None

    carbon_bs = direct_total("BS", "co2_faostat_direct", "WLD")
    carbon_hds = direct_total("HDS", "co2_faostat_direct", "WLD")
    carbon_delta = carbon_hds - carbon_bs if carbon_bs is not None and carbon_hds is not None else None
    carbon_ex_delta = None
    ex_bs = direct_ex_china("BS", "co2_faostat_direct")
    ex_hds = direct_ex_china("HDS", "co2_faostat_direct")
    if ex_bs is not None and ex_hds is not None:
        carbon_ex_delta = ex_hds - ex_bs
    ex_share = carbon_ex_delta / carbon_delta * 100 if carbon_delta not in (None, 0) and carbon_ex_delta is not None else None
    ahv_bs = direct_ex_china("BS", "land_harvested")
    ahv_hds = direct_ex_china("HDS", "land_harvested")
    ahv_delta = ahv_hds - ahv_bs if ahv_bs is not None and ahv_hds is not None else None

    add_claim(claims, "abs_price_pork_hds", "Abstract",
              "HDS cuts world pork prices by 56%.",
              "results/world/world_results_long.csv",
              "scenario=HDS, commodity=PRK, variable=PRF, year=2050",
              "percent_change_vs_BS", -56.0,
              percent_change(world, "HDS", "PRK", "PRF", "WLD"), 0.6, "%")
    add_claim(claims, "abs_price_soybean_hds", "Abstract",
              "HDS cuts world soybean prices by 35%.",
              "results/world/world_results_long.csv",
              "scenario=HDS, commodity=SBS, variable=PRF, year=2050",
              "percent_change_vs_BS", -35.0,
              percent_change(world, "HDS", "SBS", "PRF", "WLD"), 0.6, "%")
    add_claim(claims, "abs_carbon_model_covered_hds", "Abstract",
              "Model-covered farm-gate GHG changes by -0.50 Gt CO2e.",
              "results/footprints/direct_production_account_summary.csv",
              "scenario=HDS, indicator=co2_faostat_direct, year=2050",
              "HDS_minus_BS", -500.0, carbon_delta, 10.0, "Mt CO2e")
    add_claim(claims, "abs_carbon_exchina_share", "Abstract",
              "91% of model-covered carbon reduction occurs outside China.",
              "results/footprints/direct_production_account_summary.csv",
              "scenario=HDS, indicator=co2_faostat_direct, year=2050",
              "exCHN_delta / WLD_delta", 91.0, ex_share, 1.0, "%")
    add_claim(claims, "abs_exchina_harvested_area_hds", "Abstract",
              "Harvested cropland outside China changes by -21.7 Mha.",
              "results/footprints/direct_production_account_summary.csv",
              "scenario=HDS, indicator=land_harvested, year=2050",
              "HDS_minus_BS exCHN", -21.7, ahv_delta, 0.2, "Mha")

    manuscript_numbers = re.findall(r"[-+]?\d+(?:\.\d+)?\s?(?:Gt|Mt|Mha|km³|%)", text)
    findings.append(Finding("manuscript_numeric_tokens", "info", f"{len(manuscript_numbers)} tokens found"))
    review_claims = sum(1 for c in claims if c["status"] != "pass")
    findings.append(Finding("claims_registry_status", "pass" if review_claims == 0 else "review",
                            f"{len(claims)} claims, {review_claims} non-pass"))

    with open(REGISTRY, "w", newline="") as fh:
        fieldnames = ["label", "value", "unit", "source_file", "selector", "generating_script", "scenario_version", "rounding_rule"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(registry)

    with open(CLAIMS, "w", newline="") as fh:
        fieldnames = ["claim_id", "manuscript_section", "claim_text", "source_file",
                      "filter", "operation", "expected_value", "actual_value",
                      "tolerance", "unit", "difference", "status"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(claims)

    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("# Submission Consistency Report\n\n")
        fh.write("Generated by `audit_manuscript_repository_consistency.py`.\n\n")
        fh.write("| Check | Status | Detail |\n|---|---|---|\n")
        for f in findings:
            fh.write(f"| {f.check} | {f.status} | {f.detail} |\n")
        fh.write(f"\nNumber registry: `{os.path.relpath(REGISTRY, ROOT)}`\n")
        fh.write(f"\nClaims registry: `{os.path.relpath(CLAIMS, ROOT)}`\n")

    print(f"wrote {REPORT}")
    print(f"wrote {REGISTRY}")
    print(f"wrote {CLAIMS}")


if __name__ == "__main__":
    main()
