"""One-start local numerical-guard sensitivity; never overwrites primary fits."""

import argparse
import hashlib
from importlib import import_module
import json
import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from maidads_hurdle import ConditionalMAIDADS


ROOT = Path(__file__).resolve().parents[1]
FIT_CODE = import_module("03_fit_second_stage")


class ExpandedGuardMAIDADS(ConditionalMAIDADS):
    def bounds(self):
        bounds = [(-12., 12.)] * self.base_count + [(-3., 3.)] * self.d_count
        if self.commitment:
            bounds += [(-18., 8.)] * self.k + [(-3.5, 3.)]
        return bounds + [(-8., 8.), (-3., 6.)]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def projected_gradient(theta, gradient, bounds):
    value = np.asarray(gradient, float).copy()
    box = np.asarray(bounds, float)
    value[(theta <= box[:, 0] + 1e-7) & (value > 0)] = 0
    value[(theta >= box[:, 1] - 1e-7) & (value < 0)] = 0
    return float(np.max(np.abs(value)))


def parameter_names(model, families):
    names = [f"alpha_logit_{i}" for i in range(1, model.k)]
    names += [f"beta_logit_{i}" for i in range(1, model.k)]
    names += [f"family_{family}_shift_{i}" for family in families for i in range(1, model.k)]
    if model.commitment:
        names += [f"log_tau_{i}" for i in range(1, model.k + 1)] + ["log_omega"]
    return names + ["kappa", "log_rho"]


def quantity_weighted(q, elasticity, population_weights):
    weighted_q = q * population_weights[:, None]
    valid = np.isfinite(elasticity) & (q > 0)
    denominator = np.where(valid, weighted_q, 0).sum(axis=0)
    numerator = np.where(valid, weighted_q * np.nan_to_num(elasticity), 0).sum(axis=0)
    return numerator / denominator


def response_summary(model, theta, p, m, active, z, population_weights):
    pred, expense, marshall, hicks = model.responses(theta, p, m, active, z)
    return pred, {
        "expenditure_elasticity": quantity_weighted(pred.q, expense, population_weights),
        "marshallian_own_elasticity": quantity_weighted(pred.q, np.diagonal(marshall, axis1=1, axis2=2), population_weights),
        "hicksian_own_elasticity": quantity_weighted(pred.q, np.diagonal(hicks, axis1=1, axis2=2), population_weights),
    }


def run(k, maxiter, recompute_saved=False, continue_saved=False, maxcor=10):
    folder = ROOT / "outputs" / f"maidads_{k}"
    primary_path = folder / "maidads_fit.json"
    primary_hash = digest(primary_path)
    saved = json.loads(primary_path.read_text(encoding="utf-8"))
    theta = np.asarray(saved["theta"], float)
    df, _, _, p, m, shares, active = FIT_CODE.load_sample(k)
    families = saved["family_shift_levels"]
    z = np.column_stack([df.family_type.eq(i).astype(float) for i in families])
    population_weights = df.hhsize.to_numpy(float)
    model = ExpandedGuardMAIDADS(k, len(families), commitment=True)
    baseline_model = ConditionalMAIDADS(k, len(families), commitment=True)
    if len(theta) != model.npar or saved["n"] != len(df):
        raise ValueError("Primary parameter or sample dimensions differ")
    bounds = model.bounds()
    optimizer_start = theta.copy()
    history = []
    if recompute_saved or continue_saved:
        previous = json.loads((folder / "maidads_expanded_guard_sensitivity.json").read_text(encoding="utf-8"))
        if previous["primary_fit_sha256"] != primary_hash or not np.array_equal(np.asarray(previous["start_theta"]), theta):
            raise ValueError("Saved sensitivity does not refer to this primary fit")
        current = np.asarray(previous["theta"], float)
        history = previous.get("continuation_history", [])
        if recompute_saved:
            maxcor = previous.get("optimizer_maxcor", maxcor)
        if continue_saved:
            history = history + [{key: previous[key] for key in ["success", "message", "iterations", "projected_gradient_max", "log_likelihood_change"]}]
            optimizer_start = current.copy()
    if recompute_saved:
        _, gradient = model.objective(current, p, m, active, z, shares)
        result = SimpleNamespace(x=current, jac=gradient, success=previous["success"],
                                 message=previous["message"], nit=previous["iterations"])
    else:
        result = minimize(model.objective, optimizer_start, args=(p, m, active, z, shares),
                          jac=True, method="L-BFGS-B", bounds=bounds,
                          options={"maxiter": maxiter, "ftol": 1e-11, "gtol": 2e-6, "maxls": 30, "maxcor": maxcor})
    final = np.asarray(result.x, float)
    pg = projected_gradient(final, result.jac, bounds)
    record = {
        "k": k, "model": "MAIDADS", "scope": "single warm-start local numerical-guard sensitivity, not global multistart estimation",
        "primary_fit_path": str(primary_path), "primary_fit_sha256": primary_hash,
        "family_shift_levels": families, "family_base": saved["family_base"],
        "money_scale": saved["money_scale"], "price_unit": saved["price_unit"],
        "budget_unit": saved["budget_unit"], "quantity_unit": saved["quantity_unit"],
        "success": bool(result.success), "message": str(result.message), "iterations": int(result.nit),
        "gradient_max": float(np.max(np.abs(result.jac))), "projected_gradient_max": pg,
        "n": len(df), "theta": final.tolist(), "bounds": [list(pair) for pair in bounds],
        "primary_bounds": [list(pair) for pair in baseline_model.bounds()],
        "start_theta": theta.tolist(), "uncertainty_scope": "point sensitivity only; no standard error, p value or inference claim",
        "optimizer_start_theta": previous.get("optimizer_start_theta") if recompute_saved else optimizer_start.tolist(),
        "continuation_history": history,
        "optimizer_maxcor": maxcor,
        "elasticity_aggregation": "predicted conditional quantity times household size, matching primary conditional-table population weighting",
        "feasibility_scope": "observed budgets and actual participation sets; not an all-choice-set monotonicity certificate",
    }
    names = parameter_names(model, families)
    box = np.asarray(bounds, float)
    touched = np.flatnonzero((final <= box[:, 0] + 1e-5) | (final >= box[:, 1] - 1e-5))
    record["boundary_parameter_indices"] = touched.tolist()
    record["boundary_parameter_names"] = [names[i] for i in touched]
    comparison = None
    try:
        new_pred, new_elasticity = response_summary(model, final, p, m, active, z, population_weights)
        old_pred, old_elasticity = response_summary(model, theta, p, m, active, z, population_weights)
        record["positive_E_u"] = bool(np.all(new_pred.eu > 0))
        record["budget_max_relative_error"] = float(np.max(np.abs((p * new_pred.q).sum(axis=1) - m) / m))
        old_ll = model.objective(theta, p, m, active, z, shares, return_scores=True)[0].sum()
        new_ll = model.objective(final, p, m, active, z, shares, return_scores=True)[0].sum()
        record["primary_log_likelihood_recalculated"] = float(old_ll)
        record["expanded_log_likelihood"] = float(new_ll)
        record["log_likelihood_change"] = float(new_ll - old_ll)
        record["accepted_stationary_candidate"] = bool(result.success and pg < 1e-3 and record["positive_E_u"] and record["budget_max_relative_error"] < 1e-6)
        record["rejected_candidate_diagnostic_only"] = not record["accepted_stationary_candidate"]
        rows = []
        for j in range(k):
            consumed = active[:, j]
            row = {
                "k": k, "group": j + 1,
                "accepted_stationary_candidate": record["accepted_stationary_candidate"],
                "comparison_scope": "accepted_local_candidate" if record["accepted_stationary_candidate"] else "REJECTED_candidate_diagnostic_only",
                "primary_q_mean": float(np.average(old_pred.q[:, j], weights=population_weights)),
                "expanded_q_mean": float(np.average(new_pred.q[:, j], weights=population_weights)),
                "q_mean_change": float(np.average(new_pred.q[:, j] - old_pred.q[:, j], weights=population_weights)),
                "q_max_absolute_change": float(np.max(np.abs(new_pred.q[:, j] - old_pred.q[:, j]))),
                "q_max_relative_change_consumers": float(np.max(np.abs(new_pred.q[consumed, j] / old_pred.q[consumed, j] - 1))),
                "primary_log_likelihood": float(old_ll), "expanded_log_likelihood": float(new_ll),
                "log_likelihood_change": float(new_ll - old_ll), "expanded_boundary_count": len(touched),
                "expanded_projected_gradient_max": pg,
            }
            for kind in old_elasticity:
                row[f"primary_{kind}"] = float(old_elasticity[kind][j])
                row[f"expanded_{kind}"] = float(new_elasticity[kind][j])
                row[f"change_{kind}"] = float(new_elasticity[kind][j] - old_elasticity[kind][j])
            rows.append(row)
        comparison = pd.DataFrame(rows)
        changes = comparison[[f"change_{kind}" for kind in old_elasticity]].abs().to_numpy()
        record["max_quantity_weighted_elasticity_change"] = float(changes.max())
        record["max_observed_conditional_quantity_change"] = float(comparison.q_max_absolute_change.max())
        record["max_observed_conditional_quantity_relative_change"] = float(comparison.q_max_relative_change_consumers.max())
        record["requires_primary_refit_elasticity_threshold_0_01"] = bool(changes.max() > .01)
    except ValueError as exc:
        record["accepted_stationary_candidate"] = False
        record["prediction_failure"] = str(exc)
    if digest(primary_path) != primary_hash:
        raise RuntimeError("Primary fit changed while sensitivity was running; do not use these comparisons")
    record["primary_fit_unchanged"] = True
    target = folder / "maidads_expanded_guard_sensitivity.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    if record["accepted_stationary_candidate"]:
        expanded_fit = dict(saved)
        expanded_fit.update(theta=final.tolist(), log_likelihood=float(new_ll),
                            aic=float(2 * model.npar - 2 * new_ll),
                            bic=float(model.npar * np.log(len(df)) - 2 * new_ll),
                            boundary_parameter_indices=touched.tolist(),
                            structural_audit=FIT_CODE.structural_audit(model, final, p, m, active, z),
                            optimizer_bounds=record["bounds"],
                            primary_fit_sha256=primary_hash,
                            estimation_scope=record["scope"],
                            continuation_history=history)
        expanded_fit["selected_candidate"] = {
            "success": record["success"], "message": record["message"], "iterations": record["iterations"],
            "objective": float(-new_ll / len(df)), "gradient_max": record["gradient_max"],
            "projected_gradient_max": pg, "positive_eu": record["positive_E_u"],
            "budget_max_error": record["budget_max_relative_error"], "theta": final.tolist(),
        }
        (folder / "maidads_expanded_guard_fit.json").write_text(json.dumps(expanded_fit, ensure_ascii=False, indent=2), encoding="utf-8")
    parameters = pd.DataFrame({"parameter": names, "primary_theta": theta, "expanded_theta": final,
                               "expanded_lower": box[:, 0], "expanded_upper": box[:, 1],
                               "expanded_at_boundary": np.isin(np.arange(model.npar), touched).astype(int)})
    parameters.to_csv(folder / "maidads_expanded_guard_parameters.csv", index=False)
    if comparison is not None:
        comparison.to_csv(folder / "maidads_expanded_guard_comparison.csv", index=False)
        combined_path = ROOT / "outputs" / "guard_sensitivity_comparison.csv"
        if combined_path.exists():
            previous = pd.read_csv(combined_path)
            comparison = pd.concat([previous.loc[previous.k.ne(k)], comparison], ignore_index=True)
        comparison.sort_values(["k", "group"]).to_csv(combined_path, index=False)
    print(json.dumps({key: record.get(key) for key in ["k", "success", "iterations", "projected_gradient_max", "accepted_stationary_candidate", "log_likelihood_change", "max_quantity_weighted_elasticity_change", "requires_primary_refit_elasticity_threshold_0_01", "boundary_parameter_names"]}), flush=True)
    if not record["accepted_stationary_candidate"]:
        raise RuntimeError(f"Expanded-guard candidate rejected; see {target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--goods", type=int, choices=[8, 10], required=True)
    parser.add_argument("--maxiter", type=int, default=1000)
    parser.add_argument("--recompute-saved", action="store_true", help="recompute diagnostics for saved candidate without another optimization")
    parser.add_argument("--continue-saved", action="store_true", help="continue saved candidate optimization while retaining primary comparison")
    parser.add_argument("--maxcor", type=int, default=10)
    args = parser.parse_args()
    if args.recompute_saved and args.continue_saved:
        parser.error("recompute-saved and continue-saved are mutually exclusive")
    run(args.goods, args.maxiter, args.recompute_saved, args.continue_saved, args.maxcor)
