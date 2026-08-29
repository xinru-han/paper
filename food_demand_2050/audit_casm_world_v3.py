#!/usr/bin/env python3
"""Audit the CASM-World V3 manuscript against generated study evidence."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results/casm_world_rebuild"
MANUSCRIPT = ROOT / "manuscript/manuscript_v3_casm_world.md"
SUPPLEMENT = ROOT / "manuscript/supplementary_information_v3_casm_world.md"
REPORT = RESULTS / "manuscript_v3_audit_report.json"


EXPECTED_METRICS = {
    "cgs_price_prk": -46.23490261638384,
    "cgs_price_ric": -14.601388061614015,
    "cgs_price_plm": 8.375080149439729,
    "cgs_price_fmk": 18.647903559933333,
    "cgs_price_wdm": 22.57344059910631,
    "china_cgs_net_import_prk": -32.33906562419244,
    "china_cgs_net_import_ric": -46.648259181356025,
    "china_cgs_net_import_fmk": 48.74046416866132,
    "world_cgs_ghg": -254.54279698304435,
    "china_cgs_ghg": -47.30313483570024,
    "ex_china_cgs_ghg": -207.23966214734412,
    "world_cgs_primary_production": -70.9664091845425,
}

REQUIRED_TEXT = {
    "193 economy accounts": "193 economy accounts",
    "31 products": "31 products",
    "diagnostic status": "diagnostic conditional scenario",
    "publication gates": "18 of 20",
    "model-covered diet boundary": "model-covered",
    "net trade boundary": "not bilateral",
    "demand-form sensitivity": "demand-system",
}

PROHIBITED_LEGACY_TEXT = {
    "legacy GHG result": "-495",
    "legacy outside-China share": "91% of the reduction",
    "legacy land result": "21.7 Mha",
    "legacy regional model presented as current": "13-region, 31-commodity world agricultural market model",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_metrics(path: Path) -> dict[str, float]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(stream)
        return {row["metric_id"]: float(row["value"]) for row in rows}


def main() -> int:
    checks: list[dict] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "status": "passed" if passed else "failed", "detail": detail})

    run = load_json(RESULTS / "counterfactual_run_report.json")
    analysis = load_json(RESULTS / "analysis_report.json")
    record("counterfactual_run_status", run.get("status") == "passed", str(run.get("status")))
    record("analysis_status", analysis.get("status") == "passed", str(analysis.get("status")))
    record("core_model_unchanged", run.get("core_model_files_modified") is False, str(run.get("core_model_files_modified")))
    record("solution_count", run.get("main_solution_count") == 144 and run.get("sensitivity_solution_count") == 16, f"main={run.get('main_solution_count')}, sensitivity={run.get('sensitivity_solution_count')}")
    record("market_residual", float(run["sensitivity_maximum_market_relative_residual"]) < 1e-9, f"max={run['sensitivity_maximum_market_relative_residual']:.3e}")
    record("benchmark_replication", float(run["common_2023_benchmark_maximum_absolute_error_mt"]) == 0.0, f"max={run['common_2023_benchmark_maximum_absolute_error_mt']}")
    record("excluded_food_count", len(run.get("excluded_prior_casm_foods", [])) == 6, f"count={len(run.get('excluded_prior_casm_foods', []))}")

    actual = load_metrics(RESULTS / "key_findings.csv")
    for metric_id, expected in EXPECTED_METRICS.items():
        value = actual.get(metric_id)
        passed = value is not None and math.isclose(value, expected, rel_tol=0.0, abs_tol=1e-9)
        record(f"metric_{metric_id}", passed, f"actual={value}, expected={expected}")

    main_text = MANUSCRIPT.read_text(encoding="utf-8")
    supplement_text = SUPPLEMENT.read_text(encoding="utf-8")
    combined = main_text + "\n" + supplement_text
    for label, fragment in REQUIRED_TEXT.items():
        record(f"required_text_{label}", fragment.lower() in combined.lower(), fragment)
    for label, fragment in PROHIBITED_LEGACY_TEXT.items():
        record(f"prohibited_text_{label}", fragment not in combined, fragment)

    table_header = (RESULTS / "tables/table1_world_price_impacts_2050.csv").read_text(
        encoding="utf-8"
    ).splitlines()[0]
    record(
        "price_table_year_label",
        "world_price_index_2050_2023eq1" in table_header
        and "world_price_index_2023_change_percent" not in table_header,
        table_header,
    )

    missing_figures = []
    for stem in (
        "figure1_china_diet_shifters",
        "figure2_world_price_transmission",
        "figure3_trade_and_production_redistribution",
        "figure4_farm_gate_ghg_redistribution",
    ):
        for suffix in (".png", ".pdf"):
            path = ROOT / "figures/casm_world_rebuild" / f"{stem}{suffix}"
            if not path.is_file() or path.stat().st_size == 0:
                missing_figures.append(str(path.relative_to(ROOT)))
    record("figure_bundle", not missing_figures, f"missing={missing_figures}")

    failed = [check for check in checks if check["status"] == "failed"]
    report = {
        "status": "passed" if not failed else "failed",
        "manuscript": str(MANUSCRIPT.relative_to(ROOT)),
        "supplement": str(SUPPLEMENT.relative_to(ROOT)),
        "check_count": len(checks),
        "failed_count": len(failed),
        "checks": checks,
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{report['status']}: {len(checks) - len(failed)}/{len(checks)} checks passed")
    print(f"wrote {REPORT}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
