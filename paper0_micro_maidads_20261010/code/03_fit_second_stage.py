"""Fit the positive-set MAIDADS likelihood; Stata supplies the first stage."""

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from maidads_hurdle import ConditionalMAIDADS


ROOT = Path(__file__).resolve().parents[1]
MONEY_SCALE = 100.0


def load_sample(k):
    df = pd.read_csv(ROOT / "data" / f"analysis_{k}.csv",
                     dtype={"household_id": str})
    df = df.loc[df.sample_model.eq(1)].copy().reset_index(drop=True)
    df["family_type"] = pd.to_numeric(df.family_type).astype(int)
    families = [int(i) for i in sorted(df.family_type.unique()) if i != 2]
    z = np.column_stack([df.family_type.eq(i).astype(float) for i in families])
    p = df[[f"p{i}" for i in range(1, k+1)]].to_numpy() / MONEY_SCALE
    m = df.food_budget_pc_month.to_numpy() / MONEY_SCALE
    w = df[[f"s{i}" for i in range(1, k+1)]].to_numpy()
    a = df[[f"d{i}" for i in range(1, k+1)]].to_numpy().astype(bool)
    return df, families, z, p, m, w, a


def structural_audit(model, theta, p, m, a, z):
    pred, eta, mar, h = model.responses(theta, p, m, a, z)
    n, k = p.shape
    q = np.where(a, pred.q, 1.)
    hlevels = h * q[:, :, None] / p[:, None, :]
    hlevels = np.nan_to_num(hlevels)
    eigen = np.linalg.eigvalsh(hlevels)
    adding = np.nansum(pred.shares * eta, axis=1)
    symmetry = np.max(np.abs(hlevels - hlevels.transpose(0, 2, 1)))
    alpha, beta, tau, omega, kappa, rho = model.unpack(theta, z)
    min_eu = np.inf
    nonmonotone = 0
    # The same diagnostic is repeated for actual and full participation sets.
    ix = np.unique(np.linspace(0, n-1, min(240, n)).astype(int))
    for utility in np.linspace(-16, 16, 161):
        for sets in (a[ix], np.ones_like(a[ix])):
            state = model._state(np.full(len(ix), utility), p[ix], sets,
                                 alpha[ix], beta[ix], tau, omega, kappa)
            min_eu = min(min_eu, float(state[1].min()))
            nonmonotone += int((state[1] <= 0).sum())
    return {
        "budget_max_relative_error": float(np.max(np.abs((p * pred.q).sum(1)-m)/m)),
        "zero_quantities_max": float(np.max(np.abs(pred.q[~a]))) if (~a).any() else 0.,
        "expenditure_adding_up_max_error": float(np.max(np.abs(adding-1))),
        "slutsky_level_symmetry_max_error": float(symmetry),
        "slutsky_largest_eigenvalue": float(eigen[:, -1].max()),
        "conditional_hicksian_positive_own_count": int((np.diagonal(h, axis1=1, axis2=2) > 1e-10).sum()),
        "utility_grid_min_eu": min_eu,
        "utility_grid_nonmonotone_points": nonmonotone,
        "utility_grid": [-16, 16, 161],
        "rho": rho,
        "omega": omega,
        "tau": tau.tolist(),
        "kappa": kappa,
        "monotonicity_scope": "sampled observed/full sets and utility grid, not a global proof",
    }


def run(k, starts=3, maxiter=800, refine=False):
    df, families, z, p, m, w, a = load_sample(k)
    out = ROOT / "outputs" / f"maidads_{k}"
    out.mkdir(parents=True, exist_ok=True)
    comparison = []
    for commitment in (False, True):
        name = "MAIDADS" if commitment else "AIDADS"
        path = out / f"{name.lower()}_fit.json"
        if refine and not commitment:
            saved = json.loads(path.read_text())
            comparison.append({key: saved[key] for key in ("k", "model", "n", "n_parameters", "log_likelihood", "aic", "bic")})
            continue
        model = ConditionalMAIDADS(k, len(families), commitment)
        initial = None
        if refine and path.exists():
            initial = np.asarray(json.loads(path.read_text())["theta"])
            shutil.copyfile(path, out / "bounded_initial_maidads_fit.json")
        elif commitment:
            aid = json.loads((out / "aidads_fit.json").read_text())["theta"]
            initial = model.initialize(w, a, z)
            initial[:model.base_count+model.d_count] = aid[:-2]
            j = model.base_count+model.d_count
            initial[j:j+k] = np.log(np.maximum(np.mean(m[:,None]*w/p,axis=0)*.15,1e-4))
            initial[-2:] = aid[-2:]
        theta, candidates = model.fit(p, m, a, z, w, starts=starts, maxiter=maxiter, initial_theta=initial)
        ll, scores, pred = model.objective(theta, p, m, a, z, w, return_scores=True)
        audit = structural_audit(model, theta, p, m, a, z)
        selected = min((c for c in candidates if c["success"] and c["projected_gradient_max"] < 1e-3
                        and c["positive_eu"] and c["budget_max_error"] < 1e-6), key=lambda c: c["objective"])
        bound = np.asarray(model.bounds())
        at_bounds = np.flatnonzero((theta <= bound[:, 0]+1e-5) | (theta >= bound[:, 1]-1e-5))
        record = dict(k=k, model=name, n=len(df), n_parameters=model.npar,
                      log_likelihood=float(ll.sum()), aic=float(2*model.npar-2*ll.sum()),
                      bic=float(model.npar*np.log(len(df))-2*ll.sum()),
                      family_base=2, family_shift_levels=families,
                      money_scale=MONEY_SCALE, price_unit="yuan/equivalent jin divided by 100",
                      budget_unit="yuan/person/month divided by 100", quantity_unit="equivalent jin/person/month",
                      theta=theta.tolist(), selected_candidate=selected,
                      boundary_parameter_indices=at_bounds.tolist(), structural_audit=audit,
                      likelihood_scope="conditional positive shares, actual nonempty food set, observed food budget",
                      low_utility_commitment_endpoint="fixed zero",
                      lr_p_value=None,
                      lr_p_value_reason="gamma-zero null has boundary parameters and unidentified omega")
        (out / f"{name.lower()}_fit.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / f"{name.lower()}_optimizer_candidates.json").write_text(json.dumps(candidates, indent=2), encoding="utf-8")
        comparison.append({key: record[key] for key in ("k", "model", "n", "n_parameters", "log_likelihood", "aic", "bic")})
        print(f"DONE K={k} {name}: AIC={record['aic']:.3f} BIC={record['bic']:.3f} bounds={len(at_bounds)} audit={audit}", flush=True)
    pd.DataFrame(comparison).to_csv(out / "model_comparison.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--goods", type=int, choices=[8, 10], required=True)
    parser.add_argument("--starts", type=int, default=3)
    parser.add_argument("--maxiter", type=int, default=800)
    parser.add_argument("--refine", action="store_true", help="warm-start MAIDADS and retain initial-bound diagnostic")
    args = parser.parse_args()
    run(args.goods, args.starts, args.maxiter, args.refine)
