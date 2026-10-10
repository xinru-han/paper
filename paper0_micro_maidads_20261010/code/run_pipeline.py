"""Checked Stata/Python orchestration with fresh completion markers and hashes."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import fcntl
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time
import uuid


SOURCE_ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("numpy", "pandas", "scipy", "matplotlib", "tabulate")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def stage_plan(root: Path, stata: Path) -> list[dict]:
    code, outputs = root / "code", root / "outputs"
    def python_stage(name: str, script: str, expected: list[Path], *arguments: str) -> dict:
        return {"name": name, "command": [sys.executable, str(code / script), *arguments],
                "script": str(code / script), "expected": [str(path) for path in expected]}
    stages = [python_stage("build_data", "01_build_data.py", [root / "data" / "analysis_8.dta", root / "data" / "analysis_10.dta", outputs / "data_validation.csv"])]
    stages.append({"name": "stata_first_stage", "command": [str(stata), "-b", "do", str(code / "02_first_stage.do"), str(root)],
        "script": str(code / "02_first_stage.do"), "expected": [str(outputs / f"stata_stage1_{k}" / filename)
            for k in (8,10) for filename in ("coefficients.csv", "covariance.csv", "model_metadata.csv", "household_predictions.csv", "estimation_status.csv")]})
    stages += [python_stage("validate_first_stage", "validate_first_stage.py", [outputs / f"stata_stage1_{k}" / "first_stage_validation.json" for k in (8,10)]),
        python_stage("validate_independent_participation", "05_validate_participation.py", [outputs / f"stata_stage1_{k}" / "participation_independence_summary.json" for k in (8,10)]),
        python_stage("fit_correlated_participation", "06_fit_correlated_hurdle.py", [outputs / f"stata_stage1_{k}" / "correlated_hurdle_fit.json" for k in (8,10)])]
    for k in (8,10):
        stages.append(python_stage(f"fit_second_stage_{k}", "03_fit_second_stage.py", [outputs / f"maidads_{k}" / filename for filename in ("aidads_fit.json","maidads_fit.json","model_comparison.csv")], "--goods", str(k), "--starts", "2", "--maxiter", "1500"))
    for k in (8,10):
        stages.append(python_stage(f"expanded_guard_sensitivity_{k}", "09_guard_sensitivity.py", [outputs / f"maidads_{k}" / filename for filename in ("maidads_expanded_guard_sensitivity.json", "maidads_expanded_guard_parameters.csv", "maidads_expanded_guard_comparison.csv")], "--goods", str(k), "--maxiter", "1500"))
    stages.append(python_stage("finalize_expanded_guard_fits", "11_finalize_fits.py", [outputs / f"maidads_{k}" / filename
        for k in (8,10) for filename in ("maidads_fit.json", "model_comparison.csv")]))
    for k in (8,10):
        stages.append(python_stage(f"audit_working_domain_{k}", "08_audit_working_domain.py", [outputs / f"maidads_{k}" / "maidads_working_domain_audit.json",outputs / f"maidads_{k}" / "maidads_working_domain_summary.csv"], "--goods", str(k)))
    stages.append({"name": "stata_budget_shape_sensitivity", "command": [str(stata), "-b", "do", str(code / "10_budget_shape_sensitivity.do"), str(root)],
        "script": str(code / "10_budget_shape_sensitivity.do"), "expected": [str(outputs / f"budget_shape_{k}" / filename)
            for k in (8,10) for filename in ("coefficients.csv", "covariance.csv", "model_metadata.csv", "household_predictions.csv", "modelcomparison.csv", "tests.csv")]})
    for k in (8,10):
        stages.append(python_stage(f"derive_results_{k}", "04_derive_results.py", [outputs / f"maidads_{k}" / filename for filename in ("baseline_elasticities.csv","province_income_growth_predictions.csv","family_income_growth_elasticities.csv","forecast_derivative_validation.json")], "--goods", str(k), "--batch", "24"))
    stages += [python_stage("structural_tests", "test_maidads_hurdle.py", [outputs / "structural_unit_tests.json"]),
        python_stage("report", "07_make_report.py", [outputs / "完整主要结果.txt", root / "documentation" / "RESULTS_SUMMARY.md"]),
        python_stage("verify_final_results", "12_check_all_results.py", [outputs / "FINAL_RESULTS_AUDIT.json"])]
    return stages


def check_inputs(root: Path, stata: Path, stages: list[dict]) -> dict:
    if root.resolve() != SOURCE_ROOT.resolve():
        raise ValueError("--root must be the directory containing this code/ tree; copied bundles can use their own location")
    if not stata.is_file() or not os.access(stata, os.X_OK):
        raise FileNotFoundError(f"Stata executable missing or not executable: {stata}")
    scripts = sorted({Path(stage["script"]) for stage in stages} | {root / "code" / "maidads_hurdle.py",Path(__file__),root / "code" / "00_run_all.do"})
    for script in scripts:
        if not script.is_file():
            raise FileNotFoundError(f"Pipeline source missing: {script}")
        if script.suffix == ".py":
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    raw = Path("/root/data/数据/食物消费调查数据/处理后的data")
    item = Path("/root/data/Paper/食物消费数据/paper0-EASI/item_level_food_descriptives/outputs")
    inputs = [raw / "户表数据_已清洗.dta", raw / "村表数据_已清洗.dta",raw / "村表数据_已清洗_变量标签.csv",
        item / "household_item_long.dta",item / "household_community_price_mapping.csv",item / "item_catalog.csv"]
    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(f"Required upstream input missing: {path}")
    return {"python": platform.python_version(), "python_executable": sys.executable,
        "packages": {name: version(name) for name in PACKAGES}, "stata_executable": str(stata),
        "source_sha256": {str(path.relative_to(root)): digest(path) for path in scripts},
        "input_sha256": {str(path): digest(path) for path in inputs},
        "thread_environment": {name: os.environ.get(name) for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS")},
        "child_thread_environment": {name:"1" for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS")}}


def validate_fresh_outputs(stage: dict, start_ns: int) -> dict:
    outputs = {}
    for name in stage["expected"]:
        path = Path(name)
        if not path.is_file() or path.stat().st_mtime_ns < start_ns:
            raise RuntimeError(f"Stage {stage['name']} did not create a fresh expected output: {path}")
        outputs[name] = {"sha256": digest(path),"bytes": path.stat().st_size}
    if stage["name"] == "structural_tests":
        result = json.loads(Path(stage["expected"][0]).read_text())
        if not result.get("numerical_tests_passed") or not result.get("optimizer_failure_rejection_passed"):
            raise RuntimeError("Structural test or unsuccessful-optimizer rejection check did not pass")
    if stage["name"] == "stata_first_stage":
        import pandas as pd
        for name in stage["expected"]:
            if name.endswith("estimation_status.csv"):
                status = pd.read_csv(name)
                primary = status.loc[status.model.eq("food_budget_main")]
                if len(primary)!=1 or primary.return_code.iloc[0]!=0 or primary.converged.iloc[0]!=1:
                    raise RuntimeError(f"Stata main first stage failed: {name}")
    if stage["name"] == "stata_budget_shape_sensitivity":
        import pandas as pd
        for name in stage["expected"]:
            if name.endswith("modelcomparison.csv"):
                comparison = pd.read_csv(name)
                if len(comparison) != 2 or not comparison.converged.eq(1).all() or comparison.N.nunique() != 1:
                    raise RuntimeError(f"Stata same-sample budget-shape sensitivity failed: {name}")
    if stage["name"].startswith("expanded_guard_sensitivity_"):
        result = json.loads(Path(stage["expected"][0]).read_text())
        if not result.get("accepted_stationary_candidate") or not result.get("primary_fit_unchanged"):
            raise RuntimeError("Expanded-guard sensitivity did not yield an accepted candidate with the primary fit unchanged")
    if stage["name"] == "finalize_expanded_guard_fits":
        for name in stage["expected"]:
            if name.endswith("maidads_fit.json"):
                path = Path(name)
                result = json.loads(path.read_text())
                sensitivity = path.with_name("maidads_expanded_guard_sensitivity.json")
                if not result.get("expanded_guards") or result.get("boundary_parameter_indices") or result.get("promotion_source_sha256") != digest(sensitivity):
                    raise RuntimeError(f"Finalized MAIDADS does not match the accepted interior expanded-guard solution: {path}")
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=SOURCE_ROOT)
    parser.add_argument("--stata",type=Path,default=Path("/usr/local/stata17/stata-se"))
    parser.add_argument("--check",action="store_true",help="Check source syntax, dependencies, paths and planned commands only")
    args = parser.parse_args()
    root = args.root.resolve()
    outputs, logs = root / "outputs",root / "logs"
    outputs.mkdir(parents=True,exist_ok=True)
    logs.mkdir(parents=True,exist_ok=True)
    check = args.check
    marker = outputs / ("PIPELINE_CHECK_COMPLETE.json" if check else "RUN_ALL_COMPLETE.json")
    marker.unlink(missing_ok=True)
    manifest_path = outputs / ("PIPELINE_CHECK_MANIFEST.json" if check else "RUN_ALL_MANIFEST.json")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8]
    archive_dir = logs / "pipeline_manifests"
    archive_dir.mkdir(exist_ok=True)
    archive = archive_dir / f"{run_id}.json"
    manifest = {"run_id": run_id,"mode": "source_and_path_check" if check else "full_pipeline",
        "started_utc":datetime.now(timezone.utc).isoformat(),"status":"running","stages":[]}
    write_json(manifest_path,manifest)
    write_json(archive,manifest)
    try:
        plan = stage_plan(root,args.stata)
        manifest["environment_and_identities"] = check_inputs(root,args.stata,plan)
        manifest["planned_stages"] = plan
        if check:
            manifest["status"] = "checks_passed_no_scientific_stages_executed"
        else:
            with (outputs / "RUN_ALL.lock").open("a") as lock:
                fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
                environment = os.environ.copy()
                environment.update(OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
                for stage in plan:
                    log = logs / f"pipeline_{run_id}_{stage['name']}.log"
                    record = {"name":stage["name"],"command":stage["command"],"log":str(log),"status":"running"}
                    manifest["stages"].append(record)
                    write_json(manifest_path,manifest)
                    write_json(archive,manifest)
                    print("RUN "+stage["name"]+": "+shlex.join(stage["command"]),flush=True)
                    started_ns = time.time_ns()
                    with log.open("w",encoding="utf-8") as stream:
                        result = subprocess.run(stage["command"],cwd=root,env=environment,stdout=stream,stderr=subprocess.STDOUT,check=False)
                    record["return_code"] = result.returncode
                    record["elapsed_seconds"] = (time.time_ns()-started_ns)/1e9
                    if result.returncode!=0:
                        raise RuntimeError(f"{stage['name']} failed with exit {result.returncode}; see {log}")
                    record["outputs"] = validate_fresh_outputs(stage,started_ns)
                    record["status"] = "completed"
                source_hashes = manifest["environment_and_identities"]["source_sha256"]
                if any(digest(root/name)!=value for name,value in source_hashes.items()):
                    raise RuntimeError("Source changed during the run; no complete marker will be written")
                manifest["status"] = "complete"
        manifest["completed_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(manifest_path,manifest)
        write_json(archive,manifest)
        write_json(marker,{"run_id":run_id,"mode":manifest["mode"],"status":manifest["status"],"manifest":str(manifest_path),"manifest_sha256":digest(manifest_path)})
        print(json.dumps({"status":manifest["status"],"marker":str(marker)},ensure_ascii=False),flush=True)
        return 0
    except Exception as error:
        if manifest["stages"] and manifest["stages"][-1]["status"]=="running":
            manifest["stages"][-1]["status"] = "failed"
        manifest["status"] = "failed"
        manifest["error"] = repr(error)
        manifest["failed_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(manifest_path,manifest)
        write_json(archive,manifest)
        print(f"PIPELINE FAILED: {error}",file=sys.stderr,flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
