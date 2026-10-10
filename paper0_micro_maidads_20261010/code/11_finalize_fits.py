"""Adopt only accepted expanded-guard solutions, preserving every prior fit."""

import hashlib
from importlib import import_module
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from maidads_hurdle import ConditionalMAIDADS


ROOT = Path(__file__).resolve().parents[1]
MODULE = import_module("03_fit_second_stage")


def run(k):
    folder = ROOT / "outputs" / f"maidads_{k}"
    path = folder / "maidads_fit.json"
    sensitivity_path = folder / "maidads_expanded_guard_sensitivity.json"
    primary = json.loads(path.read_text())
    sensitivity = json.loads(sensitivity_path.read_text())
    source_hash = hashlib.sha256(sensitivity_path.read_bytes()).hexdigest()
    if primary.get("promotion_source_sha256") == source_hash:
        print(f"K={k} expanded guard already finalized", flush=True)
        return
    if not sensitivity["accepted_stationary_candidate"]:
        raise RuntimeError(f"K={k} expanded numerical guards did not converge; primary is not certified guard-stable")
    if hashlib.sha256(path.read_bytes()).hexdigest() != sensitivity["primary_fit_sha256"]:
        raise RuntimeError("Guard sensitivity refers to a different primary fit")
    df, families, z, p, m, w, active = MODULE.load_sample(k)
    model = ConditionalMAIDADS(k, len(families), True, expanded_guards=True)
    theta = np.asarray(sensitivity["theta"])
    ll, score, prediction = model.objective(theta, p, m, active, z, w, return_scores=True)
    if ll.sum()+1e-6 < primary["log_likelihood"]:
        raise RuntimeError("An expanded-guard solution has a worse likelihood")
    if sensitivity["boundary_parameter_indices"]:
        raise RuntimeError("Expanded-guard solution still reaches a guard; profile investigation required")
    audit = MODULE.structural_audit(model, theta, p, m, active, z)
    shutil.copyfile(path, folder / "standard_guard_maidads_fit.json")
    primary.update(theta=theta.tolist(), log_likelihood=float(ll.sum()),
                   aic=float(2*model.npar-2*ll.sum()), bic=float(model.npar*np.log(len(df))-2*ll.sum()),
                   expanded_guards=True, optimizer_bounds=sensitivity["bounds"],
                   promotion_source_sha256=source_hash,
                   previous_guard_fit_sha256=sensitivity["primary_fit_sha256"],
                   boundary_parameter_indices=[], structural_audit=audit,
                   optimizer_protocol="original multistart fit followed by accepted warm-start numerical-guard expansion",
                   guard_sensitivity_max_elasticity_change=sensitivity["max_quantity_weighted_elasticity_change"],
                   long_run_endpoint_identification_warning="tau/kappa can lie on a flat ridge; in-sample and x2 income forecasts do not identify infinite-income commitments")
    primary["selected_candidate"] = {key:sensitivity[key] for key in
                                      ("success","message","iterations","gradient_max","projected_gradient_max","theta")}
    primary["selected_candidate"].update(start="expanded numerical guard continuation",
                                         objective=float(-ll.mean()), positive_eu=True,
                                         budget_max_error=float(np.max(np.abs((p*prediction.q).sum(1)-m)/m)))
    path.write_text(json.dumps(primary, ensure_ascii=False, indent=2), encoding="utf-8")
    comparison = pd.read_csv(folder / "model_comparison.csv")
    for name in ("log_likelihood","aic","bic"):
        comparison.loc[comparison.model.eq("MAIDADS"),name] = primary[name]
    comparison.to_csv(folder / "model_comparison.csv",index=False)
    print(f"K={k} accepted expanded guard finalized; likelihood={ll.sum():.8f}", flush=True)


if __name__ == "__main__":
    for goods in (8,10):
        run(goods)
