"""Fail closed on stale fit/forecast identities and broken aggregate budgets."""

from datetime import datetime, timezone
import hashlib
from importlib import import_module
import json
from pathlib import Path

import numpy as np
import pandas as pd

from maidads_hurdle import ConditionalMAIDADS


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    kernel = ROOT / "code" / "maidads_hurdle.py"
    tests = json.loads((OUT / "structural_unit_tests.json").read_text())
    if not tests["numerical_tests_passed"]:
        raise RuntimeError("Structural numerical tests failed")
    fit_module = import_module("03_fit_second_stage")
    results_module = import_module("04_derive_results")
    result = {"audit_utc":datetime.now(timezone.utc).isoformat(), "mode":"verification of actually executed incremental scientific stages",
              "full_pipeline_marker_claimed":False, "bootstrapped":False, "results":[]}
    for k in (8,10):
        folder = OUT / f"maidads_{k}"
        path = folder / "maidads_fit.json"
        fit = json.loads(path.read_text())
        working = json.loads((folder / "maidads_working_domain_audit.json").read_text())
        if working["fit_sha256"]!=sha(path) or working["source_sha256"]!=sha(kernel) or not working["working_domain_passed"]:
            raise RuntimeError("Working-domain audit is stale or failed")
        if not fit["selected_candidate"]["success"] or fit["selected_candidate"]["projected_gradient_max"]>=1e-3 or fit["boundary_parameter_indices"]:
            raise RuntimeError("Final fit fails the convergence or numerical-boundary gate")
        df, families, z, p, m, w, active = fit_module.load_sample(k)
        first = results_module.FirstStage(k)
        if not df.household_id.equals(first.df.household_id):
            raise RuntimeError("First and second stage household identity/order mismatch")
        if not df.family_type.equals(first.df.family_type):
            raise RuntimeError("First and second stage family classifications differ")
        model = ConditionalMAIDADS(k,len(families),True,expanded_guards=True)
        ll,_,_=model.objective(np.asarray(fit["theta"]),p,m,active,z,w,return_scores=True)
        if abs(ll.sum()-fit["log_likelihood"])>1e-5:
            raise RuntimeError("Saved likelihood does not match final parameters")
        scenarios = pd.read_csv(folder / "income_growth_scenarios.csv",dtype={"stratum":str})
        if len(scenarios)!=9*14*k:
            raise RuntimeError("Missing scenario, family or province rows")
        errors = []
        for spec,g in scenarios[["specification","growth_multiplier"]].drop_duplicates().itertuples(index=False):
            first_spec = "main" if spec=="independent_hurdle" else spec
            mhat = first.evaluate(g,first_spec)[1]*100.
            expected = np.average(mhat,weights=first.df.hhsize)
            reported = scenarios.loc[scenarios.specification.eq(spec)&scenarios.growth_multiplier.eq(g)&scenarios.dimension.eq("all"),"predicted_value_pc_month"].sum()
            errors.append(abs(reported-expected)/expected)
        if max(errors)>1e-7:
            raise RuntimeError("Published scenario quantities/values do not close the first-stage budget")
        audits = json.loads((folder / "hurdle_integration_audit.json").read_text())
        if max(a["budget_max_relative_error"] for a in audits)>1e-7:
            raise RuntimeError("Hurdle integration fails budget closure")
        derivatives = json.loads((folder / "forecast_derivative_validation.json").read_text())
        if max(derivatives["income_derivative_max_scaled_error"],derivatives["price_derivative_max_scaled_error"])>1e-6:
            raise RuntimeError("Final forecast derivatives fail independent differences")
        baseline = scenarios.loc[scenarios.specification.eq("main")&scenarios.growth_multiplier.eq(1)&scenarios.dimension.eq("all")]
        families_table = scenarios.loc[scenarios.specification.eq("main")&scenarios.growth_multiplier.eq(1)&scenarios.dimension.eq("family")]
        result["results"].append(dict(goods=k,households=len(df),final_fit_sha256=sha(path),kernel_sha256=sha(kernel),
            working_domain_passed=True,fit_likelihood_recalculation_error=float(abs(ll.sum()-fit["log_likelihood"])),
            aggregate_budget_max_relative_error=float(max(errors)),
            finite_difference_income_error=derivatives["income_derivative_max_scaled_error"],
            finite_difference_price_error=derivatives["price_derivative_max_scaled_error"],
            aggregate_positive_income_count=int((baseline.income_elasticity>0).sum()),
            aggregate_negative_total_own_price_count=int((baseline.total_own_price_response<0).sum()),
            aggregate_negative_hicksian_fixed_set_count=int((baseline.hicksian_own_fixed_set_average<0).sum()),
            family_baseline_negative_income_count=int((families_table.income_elasticity<0).sum()),
            family_negative_inference="no full-system standard error; do not conclude significant inferiority"))
    result["public_summary_files"] = {str(path.relative_to(ROOT)):sha(path) for path in
        (OUT / "完整主要结果.txt", ROOT / "documentation" / "RESULTS_SUMMARY.md")}
    result["source_sha256"] = {str(path.relative_to(ROOT)):sha(path) for path in sorted((ROOT / "code").glob("*.py"))}
    result["status"] = "all_result_checks_passed"
    (OUT / "FINAL_RESULTS_AUDIT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)


if __name__ == "__main__":
    main()
