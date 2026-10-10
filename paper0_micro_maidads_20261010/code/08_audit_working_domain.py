"""Certify all sample price/family profiles and every nonempty food set.

A sufficient inequality proves E_u>0 for every real utility when it is below
one.  Uncertified profiles get a finite-grid audit with stationary-point and
near-flat refinements.  Numerical grids are explicitly not global proofs.
"""

import argparse
import hashlib
from importlib import import_module
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from maidads_hurdle import ConditionalMAIDADS
from test_maidads_hurdle import conditional_monotonicity_bound, safe_json


ROOT = Path(__file__).resolve().parents[1]
fit_code = import_module("03_fit_second_stage")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def conditional_interval_monotonicity_bound(model, theta, p, active, z=None, intervals=128, batch=8192):
    """Strict all-u sufficient bound using monotonic L(t), not a grid test.

    L(t)=sum((b-a)*log((a+(b-a)*t)/p)) has nonnegative derivative.
    On each interval, max t(1-t) times max(L(t_hi),0) bounds h(t).
    The partition covers closed [0,1], hence every real utility.
    """
    p, active = np.asarray(p, float), np.asarray(active, bool)
    if z is None:
        z = np.zeros((len(p), model.d))
    dyadic = 2.0**(-np.arange(1, 25))
    partition = np.unique(np.r_[np.linspace(0, 1, intervals+1), dyadic, 1-dyadic])
    lo, hi = partition[:-1], partition[1:]
    peak = np.where((lo <= .5) & (hi >= .5), .25,
                    np.maximum(lo*(1-lo), hi*(1-hi)))
    maximum = np.zeros(len(p))
    norm = np.zeros(len(p))
    valid_parameters = True
    for start in range(0, len(p), batch):
        stop = min(start+batch, len(p))
        aa, bb, tau, omega, _, _ = model.unpack(theta, z[start:stop])
        mask, prices = active[start:stop], p[start:stop]
        aa = aa*mask/(aa*mask).sum(1, keepdims=True)
        bb = bb*mask/(bb*mask).sum(1, keepdims=True)
        delta = bb-aa
        norm[start:stop] = np.abs(delta).sum(1)
        bound = np.zeros(stop-start)
        for right, parabola_peak in zip(hi, peak):
            weight = np.where(mask, aa*(1-right)+bb*right, 1.)
            L_right = np.sum(delta*np.log(weight/prices), axis=1)
            bound = np.maximum(bound, parabola_peak*np.maximum(L_right, 0))
        maximum[start:stop] = bound
        valid_parameters &= bool(omega > 0 and np.all(tau >= 0))
    return {"bound": maximum, "endpoint_L1_distance": norm,
            "certified_positive_slope": (maximum < 1-1e-10) & valid_parameters,
            "uniform_intervals": intervals, "partition_intervals": len(hi),
            "proof_scope": "All t in [0,1], thus every real u; monotonic L and exact interval parabola maximum."}


def scenario_budgets(k, df, observed):
    first = import_module("04_derive_results").FirstStage(k)
    if not np.array_equal(first.df.household_id.to_numpy(), df.household_id.to_numpy()):
        raise ValueError("First-stage and second-stage household order differs")
    budgets = [observed]
    names = ["observed_food_budget"]
    for specification, growth in [("main", g) for g in (1., 1.1, 1.25, 1.5, 2.)]+[
            ("income_trim", 1.), ("fooddeflated", 1.)]:
        p, m, *_ = first.evaluate(growth, specification)
        if not np.allclose(p, df[[f"p{i}" for i in range(1, k+1)]].to_numpy()/100,
                           rtol=0, atol=1e-14):
            raise ValueError("Income scenario changes prices; audit the new price profiles separately")
        if not np.isfinite(m).all() or (m <= 0).any():
            raise ValueError("Scenario has an invalid food budget")
        budgets.append(m)
        names.append(f"{specification}_growth_{growth:g}")
    return np.column_stack(budgets), names


def refine_uncertified(model, theta, p, active, z, budgets, lower, upper, step):
    alpha, beta, tau, omega, kappa, _ = model.unpack(theta, z)

    def state(u):
        values = np.atleast_1d(u).astype(float)
        return model._state(values, np.repeat(p, len(values), axis=0),
                            np.repeat(active, len(values), axis=0),
                            np.repeat(alpha, len(values), axis=0), np.repeat(beta, len(values), axis=0),
                            tau, omega, kappa)

    grid = np.arange(lower, upper+step/2, step)
    initial = state(grid)
    expenditure, eu = initial[0], initial[1]
    if not np.isfinite(expenditure).all() or not np.isfinite(eu).all():
        return {"passed": False, "reason": "nonfinite_grid", "scope": "finite_grid"}
    critical = []
    for j in np.flatnonzero(eu[:-1]*eu[1:] < 0):
        critical.append(float(brentq(lambda u: state(u)[1][0], grid[j], grid[j+1], xtol=1e-12)))
    near_flat = np.flatnonzero(np.abs(eu)/np.maximum(expenditure, 1e-250) < .05)
    extra = []
    for center in [*critical, *grid[near_flat]]:
        extra.extend(np.linspace(max(lower, center-step), min(upper, center+step), 25))
    refined_grid = np.unique(np.r_[grid, extra, critical])
    expenditure, eu = state(refined_grid)[:2]
    targets = np.unique(np.asarray(budgets, float).ravel())
    root_counts = []
    for budget in targets:
        v = expenditure-budget
        signs = np.sign(v)
        exact = signs == 0
        exact_count = np.sum(exact & ~np.r_[False, exact[:-1]])
        crosses = signs[:-1]*signs[1:] < 0
        root_counts.append(int(crosses.sum()+exact_count))
    endpoint_ok = bool(expenditure[0] < targets.min() and expenditure[-1] > targets.max())
    monotone = bool(np.all(eu > 0))
    unique = bool(np.all(np.asarray(root_counts) == 1))
    reasons = []
    if not endpoint_ok:
        reasons.append("budget_outside_checked_utility_bracket")
    if not monotone:
        reasons.append("nonpositive_expenditure_slope")
    if not unique:
        reasons.append("nonunique_or_absent_budget_root")
    return {"passed": not reasons, "reason": ";".join(reasons) if reasons else "passed_finite_grid",
            "scope": "finite_grid_with_stationary_point_and_near_flat_refinement_not_global_proof",
            "minimum_E_u": float(eu.min()), "minimum_E_u_over_E": float(np.min(eu/expenditure)),
            "root_count_min": int(min(root_counts)), "root_count_max": int(max(root_counts)),
            "target_budgets": len(targets), "critical_points": critical,
            "refined_grid_points": len(refined_grid), "interval": [lower, upper], "initial_step": step,
            "positive_endpoint_bracket": endpoint_ok}


def province_guard_reference():
    path = Path("/root/data/Paper/省级食物消费/paper-AE/submission_0921/replication/results/sensitivity/summary.csv")
    if not path.exists():
        return {"available": False}
    table = pd.read_csv(path)
    rows = table.loc[table.variant.eq("expanded_guards")].to_dict("records")
    return {"available": True, "source": str(path), "source_sha256": sha(path),
            "expanded_guards": {"gamma_times_quantity_scale": 24, "omega_upper": 40, "abs_kappa_upper": 40},
            "baseline_guards": {"gamma_times_quantity_scale": 12, "omega_upper": 20, "abs_kappa_upper": 25},
            "results": rows,
            "scope": "Upstream two-start local guard expansion, not a new global search; not a justification for a common physical micro tau cap."}


def run(args):
    k = args.goods
    folder = ROOT / "outputs" / f"maidads_{k}"
    fit_path = Path(args.fit) if args.fit else folder / f"{args.model}_fit.json"
    out = Path(args.output_dir) if args.output_dir else folder
    out.mkdir(parents=True, exist_ok=True)
    fit_bytes = fit_path.read_bytes()
    fit_hash = hashlib.sha256(fit_bytes).hexdigest()
    fit = json.loads(fit_bytes)
    data_path, source_path = ROOT / "data" / f"analysis_{k}.csv", ROOT / "code" / "maidads_hurdle.py"
    source_hash = sha(source_path)
    data_hash = sha(data_path)
    df, _, _, p, m, _, _ = fit_code.load_sample(k)
    families = fit["family_shift_levels"]
    z = np.column_stack([df.family_type.eq(i).astype(float) for i in families])
    model = ConditionalMAIDADS(k, len(families), args.model == "maidads",
                              expanded_guards=fit.get("expanded_guards", False))
    theta = np.asarray(fit["theta"], float)
    if len(theta) != model.npar:
        raise ValueError("Fit dimensions do not match requested model")
    profile, representative, inverse = np.unique(np.column_stack([p, z]), axis=0,
                                                  return_index=True, return_inverse=True)
    pp, zz = p[representative], z[representative]
    counts = np.bincount(inverse)
    families_by_profile = df.family_type.to_numpy()[representative]
    sets = ((np.arange(1, 2**k)[:, None] >> np.arange(k)) & 1).astype(bool)
    patterns = len(sets)
    records, uncertified = [], []
    maximum_bound, maximum_box_bound, maximum_simple_bound = 0., 0., 0.
    interval_checked, interval_rescue, interval_deeper = 0, 0, 0
    uncertified_household_combinations, box_uncertified_household_combinations = 0, 0
    for start in range(0, len(pp), args.batch):
        stop = min(start+args.batch, len(pp))
        npart = stop-start
        prices, covariates = np.repeat(pp[start:stop], patterns, 0), np.repeat(zz[start:stop], patterns, 0)
        active = np.tile(sets, (npart, 1))
        certificate = conditional_monotonicity_bound(model, theta, prices, active, covariates)
        maximum_simple_bound = max(maximum_simple_bound, float(certificate["bound"].max()))
        alpha, beta, tau, omega, _, _ = model.unpack(theta, covariates)
        aa = alpha*active/(alpha*active).sum(1, keepdims=True)
        bb = beta*active/(beta*active).sum(1, keepdims=True)
        effective_bound = certificate["bound"].copy()
        norm = np.abs(bb-aa).sum(1)
        original_certified = certificate["certified_positive_slope"]
        coarse_box_bound = effective_bound + args.price_log_radius*norm/4
        refine_indices = np.flatnonzero((~original_certified) | (coarse_box_bound >= 1-1e-10))
        if len(refine_indices):
            stronger = conditional_interval_monotonicity_bound(model, theta, prices[refine_indices],
                                                               active[refine_indices], covariates[refine_indices])
            effective_bound[refine_indices] = np.minimum(effective_bound[refine_indices], stronger["bound"])
            interval_checked += len(refine_indices)
            interval_rescue += int((stronger["certified_positive_slope"] & ~original_certified[refine_indices]).sum())
            still_uncertified = effective_bound[refine_indices] + args.price_log_radius*norm[refine_indices]/4 >= 1-1e-10
            deeper_indices = refine_indices[still_uncertified]
            if len(deeper_indices):
                deeper = conditional_interval_monotonicity_bound(model, theta, prices[deeper_indices],
                                                                 active[deeper_indices], covariates[deeper_indices], intervals=512)
                effective_bound[deeper_indices] = np.minimum(effective_bound[deeper_indices], deeper["bound"])
                interval_deeper += len(deeper_indices)
                interval_rescue += int((deeper["certified_positive_slope"] &
                                       (stronger["bound"][still_uncertified] >= 1-1e-10) &
                                       ~original_certified[deeper_indices]).sum())
        box_bound = effective_bound + args.price_log_radius*norm/4
        bounds = effective_bound.reshape(npart, patterns)
        box_bounds = box_bound.reshape(npart, patterns)
        certified = (bounds < 1-1e-10) & (omega > 0) & np.all(tau >= 0)
        box_certified = (box_bounds < 1-1e-10) & (omega > 0) & np.all(tau >= 0)
        maximum_bound = max(maximum_bound, float(bounds.max()))
        maximum_box_bound = max(maximum_box_bound, float(box_bounds.max()))
        for local in range(npart):
            idx = start+local
            bad = np.flatnonzero(~certified[local])
            box_bad = np.flatnonzero(~box_certified[local])
            uncertified_household_combinations += len(bad)*int(counts[idx])
            box_uncertified_household_combinations += len(box_bad)*int(counts[idx])
            worst = int(np.argmax(bounds[local]))
            records.append({"price_family_profile": idx, "family_type": int(families_by_profile[idx]),
                            "households_matching_profile": int(counts[idx]), "nonempty_sets": patterns,
                            "global_bound_max": float(bounds[local].max()),
                            "price_box_global_bound_max": float(box_bounds[local].max()),
                            "globally_uncertified_sets": len(bad), "price_box_uncertified_sets": len(box_bad),
                            "worst_set_code": worst+1, "worst_active_count": int(sets[worst].sum())})
            uncertified.extend((idx, int(pattern)) for pattern in bad)
    selected = fit.get("selected_candidate", {})
    fit_converged = bool(selected.get("success", False)) and float(selected.get("projected_gradient_max", np.inf)) < 1e-3
    target_budgets, budget_names = scenario_budgets(k, df, m)
    roots = []
    for i, (profile_index, pattern) in enumerate(uncertified[:args.max_grid_cases]):
        group_budgets = target_budgets[inverse == profile_index]
        result = refine_uncertified(model, theta, pp[profile_index:profile_index+1], sets[pattern:pattern+1],
                                   zz[profile_index:profile_index+1], group_budgets,
                                   args.grid_lower, args.grid_upper, args.grid_step)
        result.update(price_family_profile=profile_index, set_code=pattern+1)
        roots.append(result)
        if i % 100 == 0:
            print(f"K{k} refined grid {i+1}/{len(uncertified)}", flush=True)
    complete = len(roots) == len(uncertified)
    unchanged = sha(fit_path) == fit_hash and sha(source_path) == source_hash and sha(data_path) == data_hash
    numerical_pass = all(r["passed"] for r in roots) and complete
    report = {
        "goods": k, "model": args.model, "fit_path": str(fit_path), "fit_sha256": fit_hash,
        "commitment_specification": "delta_i fixed zero; tau_i>=0; unrestricted alpha and beta simplexes" if args.model == "maidads" else "gamma_i fixed zero; unrestricted alpha and beta simplexes",
        "is_full_free_two_endpoint_MAIDADS": False,
        "data_path": str(data_path), "data_sha256": data_hash, "source_sha256": source_hash,
        "audit_sha256": sha(__file__),
        "source_and_fit_unchanged_during_audit": unchanged,
        "fit_convergence_gate_passed": fit_converged,
        "expanded_guards": model.expanded_guards,
        "fit_boundary_parameter_indices": fit.get("boundary_parameter_indices", []),
        "does_not_certify_artificial_bound_sensitivity": True,
        "households": len(df), "unique_price_family_profiles": len(pp), "nonempty_sets": patterns,
        "all_household_set_combinations": len(df)*patterns,
        "unique_profile_set_combinations": len(pp)*patterns,
        "global_sufficient_bound_max": maximum_bound,
        "simple_range_based_bound_max": maximum_simple_bound,
        "interval_certificate_checked_unique_combinations": interval_checked,
        "interval_certificate_rescued_unique_combinations": interval_rescue,
        "interval_512_required_unique_combinations": interval_deeper,
        "certificate_method": "Simple endpoint-range bound where sufficient; monotone-L rigorous [0,1] partition bound otherwise, 128 then 512 plus dyadic endpoints.",
        "globally_uncertified_unique_combinations": len(uncertified),
        "globally_uncertified_household_combinations": uncertified_household_combinations,
        "all_sample_prices_families_sets_globally_certified": not uncertified,
        "all_positive_budgets_and_fixed_price_income_scenarios_have_unique_roots": not uncertified,
        "price_log_radius": args.price_log_radius, "price_box_global_bound_max": maximum_box_bound,
        "price_box_uncertified_household_combinations": box_uncertified_household_combinations,
        "all_price_box_families_sets_globally_certified": box_uncertified_household_combinations == 0,
        "budget_domains_explicitly_checked": budget_names,
        "positive_budget_range_model_money": [float(target_budgets.min()), float(target_budgets.max())],
        "finite_grid_required_unique_cases": len(uncertified), "finite_grid_checked_unique_cases": len(roots),
        "finite_grid_complete": complete, "finite_grid_checks": roots,
        "working_domain_passed": bool(fit_converged and unchanged and numerical_pass),
        "global_certificate_scope": "All sample fixed-price and family profiles, all nonempty sets, every real u and every positive m; plus stated price box where certified.",
        "finite_grid_scope": "For uncertified cases only: stationary points and near-flat intervals refined; finite grids do not prove uniqueness outside the checked interval or absence of unresolved narrow extrema.",
        "upstream_province_guard_reference": province_guard_reference(),
    }
    pd.DataFrame(records).to_csv(out / f"{args.model}_working_domain_summary.csv", index=False)
    (out / f"{args.model}_working_domain_audit.json").write_text(
        json.dumps(safe_json(report), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["goods", "model", "households",
                      "global_sufficient_bound_max", "globally_uncertified_unique_combinations",
                      "price_box_global_bound_max", "working_domain_passed"]}, ensure_ascii=False), flush=True)
    if not report["working_domain_passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--goods", type=int, choices=[8, 10], required=True)
    parser.add_argument("--model", choices=["maidads", "aidads"], default="maidads")
    parser.add_argument("--fit")
    parser.add_argument("--output-dir")
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--price-log-radius", type=float, default=.02)
    parser.add_argument("--grid-lower", type=float, default=-40.)
    parser.add_argument("--grid-upper", type=float, default=40.)
    parser.add_argument("--grid-step", type=float, default=.1)
    parser.add_argument("--max-grid-cases", type=int, default=10000)
    args = parser.parse_args()
    if args.price_log_radius < 0 or args.grid_step <= 0 or args.grid_lower >= args.grid_upper:
        parser.error("Invalid price radius or utility grid")
    run(args)
