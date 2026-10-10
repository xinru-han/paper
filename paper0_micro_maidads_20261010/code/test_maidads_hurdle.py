"""Independent numerical checks for conditional and hurdle MAIDADS.

Run this script after changes to the kernel.  Diagnostics are retained even when
an assertion fails, and a failed optimizer or ambiguous utility root is never
converted to a passing estimation status.
"""

import hashlib
from importlib import import_module
import itertools
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from scipy.special import expit, ndtr

from maidads_hurdle import ConditionalMAIDADS


BASE = Path(__file__).resolve().parents[1]


def conditional_monotonicity_bound(model, theta, p, active, z=None):
    """Sufficient global E_u>0 bound; a bound >=1 is inconclusive.

    Restricted weights are a logistic mixture of normalized endpoint weights.
    Centering the log price ratios removes arbitrary common monetary units.
    With tau>=0 and omega>0, a strictly positive Q_u also ensures E_u>0.
    """
    p, active = np.asarray(p, float), np.asarray(active, bool)
    if z is None:
        z = np.zeros((len(p), model.d))
    alpha, beta, tau, omega, _, _ = model.unpack(theta, z)
    a = alpha * active / (alpha * active).sum(axis=1, keepdims=True)
    b = beta * active / (beta * active).sum(axis=1, keepdims=True)
    high = np.where(active, np.log(np.where(active, np.maximum(a, b), 1) / p), -np.inf).max(axis=1)
    low = np.where(active, np.log(np.where(active, np.minimum(a, b), 1) / p), np.inf).min(axis=1)
    bound = np.abs(b-a).sum(axis=1) * (high-low) / 8.0
    return {
        "bound": bound,
        "certified_positive_slope": (bound < 1) & (omega > 0) & np.all(tau >= 0),
        "lower_Q_u_over_Q": 1-bound,
    }


def conditional_root_grid_audit(model, theta, p, m, active, z=None,
                                lower=-40.0, upper=40.0, step=0.1):
    """Finite-grid root/slope audit, not a proof of global uniqueness.

    Fine grids can still miss a narrow pair of roots or a tangent root.  The
    caller should retain the sufficient global bound and independently refine
    derivative sign changes/near-zero slopes for an admissibility decision.
    """
    p, m, active = np.asarray(p, float), np.asarray(m, float), np.asarray(active, bool)
    if z is None:
        z = np.zeros((len(m), model.d))
    a, b, tau, omega, kappa, _ = model.unpack(theta, z)
    grid = np.arange(lower, upper+step/2, step)
    values, slopes = [], []
    for u in grid:
        expenditure, eu, *_ = model._state(np.full(len(m), u), p, active, a, b, tau, omega, kappa)
        values.append(expenditure-m)
        slopes.append(eu)
    values, slopes = np.asarray(values), np.asarray(slopes)
    cross = values[:-1] * values[1:] < 0
    zero = values == 0
    exact_roots = (zero & ~np.vstack([np.zeros((1, len(m)), bool), zero[:-1]])).sum(axis=0)
    root_count = cross.sum(axis=0) + exact_roots
    slope_cross = slopes[:-1] * slopes[1:] < 0
    return {
        "interval": [lower, upper], "step": step,
        "root_count": root_count,
        "minimum_E_u": slopes.min(axis=0),
        "slope_sign_changes": slope_cross.sum(axis=0),
        "endpoint_bracket": (values[0] < 0) & (values[-1] > 0),
        "finite_grid": np.isfinite(values).all(axis=0) & np.isfinite(slopes).all(axis=0),
    }


def numerical_gradient(function, theta, step=2e-5):
    gradient = np.empty(len(theta))
    for j in range(len(theta)):
        delta = step * max(1.0, abs(theta[j]))
        plus, minus = theta.copy(), theta.copy()
        plus[j] += delta
        minus[j] -= delta
        gradient[j] = (function(plus)-function(minus)) / (2*delta)
    return gradient


def safe_json(value):
    if isinstance(value, dict):
        return {str(k): safe_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [safe_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return safe_json(value.tolist())
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def fixture(k, commitment, demographics=2, n=16):
    rng = np.random.default_rng(90210+k+int(commitment))
    model = ConditionalMAIDADS(k, demographics, commitment)
    active = rng.random((n, k)) > 0.3
    active[:, 0] = True
    active[0] = False
    active[0, 0] = True
    active[1] = True
    p = np.exp(rng.normal(-1.3, 0.3, (n, k)))
    m = np.exp(rng.normal(1.1, 0.5, n))
    z = rng.normal(0, 0.4, (n, demographics))
    observed = active / active.sum(axis=1, keepdims=True)
    theta = model.initialize(observed, active, z)
    theta[:model.base_count] += rng.normal(0, 0.18, model.base_count)
    theta[model.base_count:model.base_count+model.d_count] = rng.normal(0, 0.1, model.d_count)
    predicted = model.predict(theta, p, m, active, z)
    for i, mask in enumerate(active):
        if mask.sum() > 1:
            observed[i, mask] = rng.dirichlet(predicted.shares[i, mask]*12)
    return model, theta, p, m, active, z, observed


class Checks:
    def __init__(self):
        self.records = []

    def record(self, name, passed, metrics=None):
        self.records.append({"test": name, "passed": bool(passed), "metrics": safe_json(metrics or {})})


def check_conditional(checks, k, commitment, demographics):
    model, theta, p, m, active, z, observed = fixture(k, commitment, demographics)
    label = f"K{k}_commitment{int(commitment)}_demographics{demographics}"
    predicted, eta, mar, hicks = model.responses(theta, p, m, active, z)
    budget_error = np.max(np.abs((p*predicted.q).sum(axis=1)-m)/m)
    checks.record(label+"_budget_and_zero", budget_error < 2e-8 and
                  np.all(predicted.q[~active] == 0) and np.all(predicted.q[active] > 0),
                  {"max_relative_budget_error": budget_error, "minimum_E_u": predicted.eu.min()})

    value, analytic = model.objective(theta, p, m, active, z, observed)
    numeric = numerical_gradient(lambda t: model.objective(t, p, m, active, z, observed)[0], theta)
    error = np.max(np.abs(numeric-analytic) / (1+np.abs(numeric)))
    ll, scores, _ = model.objective(theta, p, m, active, z, observed, return_scores=True)
    checks.record(label+"_Dirichlet_gradient", error < 2e-6 and
                  np.max(abs(scores.mean(axis=0)+analytic)) < 1e-10,
                  {"max_normalized_gradient_error": error, "objective": value,
                   "gradient_max": np.abs(analytic).max(), "single_active_loglik": ll[0]})
    row = 2
    row_numeric = numerical_gradient(lambda t: model.objective(t, p, m, active, z, observed,
                                                             return_scores=True)[0][row], theta)
    row_error = np.max(abs(row_numeric-scores[row]) / (1+abs(row_numeric)))
    checks.record(label+"_individual_score", row_error < 2e-6,
                  {"max_normalized_score_error": row_error})

    h = 2e-5
    plus = model.predict(theta, p, m*np.exp(h), active, z).q
    minus = model.predict(theta, p, m*np.exp(-h), active, z).q
    spend_fd = (plus-minus)/(2*h)/np.where(active, predicted.q, np.nan)
    spend_error = np.nanmax(abs(spend_fd-eta)/(1+abs(spend_fd)))
    checks.record(label+"_food_budget_elasticity", spend_error < 2e-6,
                  {"max_normalized_finite_difference_error": spend_error})

    alpha, beta, tau, omega, kappa, _ = model.unpack(theta, z)
    price_errors, compensated_errors = [], []
    hessian = np.zeros((len(m), k, k))
    for j in range(k):
        pp, pm = p.copy(), p.copy()
        pp[:, j] *= np.exp(h)
        pm[:, j] *= np.exp(-h)
        mar_fd = (model.predict(theta, pp, m, active, z).q-
                  model.predict(theta, pm, m, active, z).q)/(2*h)/np.where(active, predicted.q, np.nan)
        hp = model._state(predicted.utility, pp, active, alpha, beta, tau, omega, kappa)[2]
        hm = model._state(predicted.utility, pm, active, alpha, beta, tau, omega, kappa)[2]
        h_fd = (hp-hm)/(2*h)/np.where(active, predicted.q, np.nan)
        price_errors.append(np.nanmax(abs(mar_fd-mar[:, :, j])/(1+abs(mar_fd))))
        compensated_errors.append(np.nanmax(abs(h_fd-hicks[:, :, j])/(1+abs(h_fd))))
        hessian[:, :, j] = np.nan_to_num(hicks[:, :, j])*predicted.q/p[:, j, None]
    checks.record(label+"_Marshallian_price", max(price_errors) < 2e-6,
                  {"max_normalized_finite_difference_error": max(price_errors)})
    checks.record(label+"_Hicksian_price", max(compensated_errors) < 2e-6,
                  {"max_normalized_finite_difference_error": max(compensated_errors)})
    symmetry = np.max(abs(hessian-hessian.transpose(0, 2, 1)))
    curvature = np.linalg.eigvalsh((hessian+hessian.transpose(0, 2, 1))/2).max()
    engel = np.max(abs(np.nansum(predicted.shares*eta, axis=1)-1))
    homogeneity = np.nanmax(abs(np.nansum(mar, axis=2)+eta))
    price_adding = np.max(abs(np.nansum(predicted.shares[:, :, None]*mar, axis=1)+predicted.shares))
    checks.record(label+"_Slutsky_and_adding_up", max(symmetry, curvature, engel,
                  homogeneity, price_adding) < 2e-7,
                  {"max_Slutsky_asymmetry": symmetry, "max_Slutsky_eigenvalue": curvature,
                   "Engel_adding_up_error": engel, "homogeneity_error": homogeneity,
                   "price_adding_up_error": price_adding})

    scaled = model.predict(theta, p/100, m/100, active, z)
    scaled_value, scaled_grad = model.objective(theta, p/100, m/100, active, z, observed)
    currency_error = max(np.max(abs(scaled.q-predicted.q)), np.max(abs(scaled.utility-predicted.utility)))
    checks.record(label+"_common_currency_divide_100", currency_error < 2e-7 and
                  abs(scaled_value-value) < 1e-8 and np.max(abs(scaled_grad-analytic)) < 2e-7,
                  {"max_quantity_or_utility_difference": currency_error,
                   "objective_difference": abs(scaled_value-value),
                   "gradient_difference": np.max(abs(scaled_grad-analytic))})

    bound = conditional_monotonicity_bound(model, theta, p, active, z)
    grid = conditional_root_grid_audit(model, theta, p, m, active, z, step=.2)
    checks.record(label+"_root_and_monotonicity", np.all(grid["root_count"] == 1) and
                  np.all(grid["endpoint_bracket"]) and np.all(grid["minimum_E_u"] > 0),
                  {"global_sufficient_bound_max": bound["bound"].max(),
                   "all_globally_certified": bound["certified_positive_slope"].all(),
                   "finite_grid_root_count": grid["root_count"],
                   "finite_grid_minimum_E_u": grid["minimum_E_u"].min(),
                   "finite_grid_interval": grid["interval"], "finite_grid_step": grid["step"]})


def participation_law(a, derivative):
    probabilities = ndtr(a)
    pdf = np.exp(-a*a/2)/np.sqrt(2*np.pi)
    dpi = pdf*derivative
    sets = np.asarray([r for r in itertools.product([False, True], repeat=len(a)) if any(r)])
    raw = np.prod(np.where(sets, probabilities, 1-probabilities), axis=1)
    pzero = np.prod(1-probabilities)
    normalizer = 1-pzero
    normalizer_derivative = pzero*np.sum(dpi/(1-probabilities))
    normalized = raw/normalizer
    score = np.sum(np.where(sets, dpi/probabilities, -dpi/(1-probabilities)), axis=1)
    dnormalized = normalized*(score-normalizer_derivative/normalizer)
    return sets, normalized, dnormalized


def check_hurdle(checks):
    model, theta, p0, _, _, z0, _ = fixture(3, True, 1, n=16)
    p0, z0 = p0[:1], z0[:1]
    income_slopes = np.array([.15, .3, -.08])
    price_slopes = np.array([-.08, -.2, .1])
    indices = np.array([.4, -.2, .8])
    budget_income, budget_price = .65, -.12

    def evaluate(lnincome=0., lnprice=0.):
        p = p0.copy()
        p[:, 1] *= np.exp(lnprice)
        m = 3.0*np.exp(budget_income*lnincome+budget_price*lnprice)
        a = indices+income_slopes*lnincome+price_slopes*lnprice
        active, pr, _ = participation_law(a, np.zeros(3))
        pp, zz = np.repeat(p, len(active), 0), np.repeat(z0, len(active), 0)
        pred, eta, mar, _ = model.responses(theta, pp, np.full(len(active), m), active, zz)
        return np.sum(pr[:, None]*pred.q, axis=0), pred, eta, mar, pr

    mean, pred, eta, mar, pr = evaluate()
    _, _, dpi_income = participation_law(indices, income_slopes)
    _, _, dpi_price = participation_law(indices, price_slopes)
    income_intensive = np.sum(pr[:, None]*pred.q*np.nan_to_num(eta)*budget_income, axis=0)
    income_extensive = np.sum(dpi_income[:, None]*pred.q, axis=0)
    price_intensive = np.sum(pr[:, None]*pred.q*(np.nan_to_num(mar[:, :, 1])+
                             np.nan_to_num(eta)*budget_price), axis=0)
    price_extensive = np.sum(dpi_price[:, None]*pred.q, axis=0)
    h = 2e-5
    income_fd = (evaluate(lnincome=h)[0]-evaluate(lnincome=-h)[0])/(2*h)
    price_fd = (evaluate(lnprice=h)[0]-evaluate(lnprice=-h)[0])/(2*h)
    income_error = np.max(abs(income_fd-income_intensive-income_extensive)/(1+abs(income_fd)))
    price_error = np.max(abs(price_fd-price_intensive-price_extensive)/(1+abs(price_fd)))
    checks.record("hurdle_income_two_margin_derivative", income_error < 2e-6,
                  {"max_normalized_finite_difference_error": income_error,
                   "income_elasticity": (income_intensive+income_extensive)/mean})
    checks.record("hurdle_total_price_two_margin_derivative", price_error < 2e-6,
                  {"max_normalized_finite_difference_error": price_error,
                   "price_response_elasticity_not_Hicksian": (price_intensive+price_extensive)/mean})
    checks.record("nonempty_participation_probability_derivatives", abs(pr.sum()-1) < 1e-12 and
                  max(abs(dpi_income.sum()), abs(dpi_price.sum())) < 1e-12,
                  {"probability_sum": pr.sum(), "income_derivative_sum": dpi_income.sum(),
                   "price_derivative_sum": dpi_price.sum(),
                   "population_budget_error": abs(np.sum(p0[0]*mean)-3.)})


def diagnostic_counterexamples():
    model = ConditionalMAIDADS(2, 0, False)
    theta = np.array([5., -5., 0., 1.])
    p, m, active = np.array([[10., .00001]]), np.array([.01]), np.ones((1, 2), bool)
    grid = conditional_root_grid_audit(model, theta, p, m, active, step=.01)
    bound = conditional_monotonicity_bound(model, theta, p, active)
    try:
        prediction = model.predict(theta, p, m, active)
        accepted = True
        result = {"utility": prediction.utility, "E_u": prediction.eu,
                  "relative_budget_error": abs((p*prediction.q).sum()/m[0]-1)}
    except (ValueError, RuntimeError, FloatingPointError) as exc:
        accepted = False
        result = {"exception": str(exc)}
    nonunique = {"fixture": "K2 alpha_logit=5 beta_logit=-5 p=(10,0.00001) m=0.01",
                 "known_nonunique_roots_detected": bool(grid["root_count"][0] >= 3),
                 "kernel_accepts_ambiguous_root": accepted, "prediction": result,
                 "grid_diagnostic": grid, "sufficient_bound": bound,
                 "interpretation": "Local positive E_u and budget closure do not establish unique utility."}

    valid_model, valid_theta, pp, mm, aa, zz, obs = fixture(3, True, 0)
    def failed_optimizer(fun, start, args, **kwargs):
        value, _ = fun(start, *args)
        return SimpleNamespace(x=start, fun=value, jac=np.full(len(start), .2),
                               nit=1, success=False, message="TEST iteration limit reached")
    try:
        with patch("maidads_hurdle.minimize", failed_optimizer):
            _, candidates = valid_model.fit(pp, mm, aa, zz, obs, starts=1, maxiter=1)
        failed_accepted = True
        failed_details = candidates
    except (ValueError, RuntimeError, FloatingPointError) as exc:
        failed_accepted = False
        failed_details = {"exception": str(exc)}
    failed = {"kernel_accepts_unsuccessful_optimizer": failed_accepted,
              "details": failed_details,
              "interpretation": "A feasible last iterate is not a converged estimator."}
    return {"multiple_roots": nonunique, "optimizer_failure": failed}


def check_interval_certificate(checks):
    certify = import_module("08_audit_working_domain").conditional_interval_monotonicity_bound
    model, theta, p, _, active, z, _ = fixture(10, True, 2, n=128)
    rng = np.random.default_rng(80410)
    theta[:model.base_count] += rng.normal(0, 3, model.base_count)
    p *= np.exp(rng.normal(0, 3, p.shape))
    result = certify(model, theta, p, active, z)
    alpha, beta, _, _, _, _ = model.unpack(theta, z)
    aa = alpha*active/(alpha*active).sum(1, keepdims=True)
    bb = beta*active/(beta*active).sum(1, keepdims=True)
    delta = bb-aa
    maximum_sampled = np.full(len(p), -np.inf)
    minimum_L_increment = np.inf
    previous_L = None
    for t in np.linspace(0, 1, 4097):
        weight = np.where(active, aa*(1-t)+bb*t, 1.)
        L = np.sum(delta*np.log(weight/p), axis=1)
        maximum_sampled = np.maximum(maximum_sampled, t*(1-t)*L)
        if previous_L is not None:
            minimum_L_increment = min(minimum_L_increment, float(np.min(L-previous_L)))
        previous_L = L
    slack = result["bound"]-maximum_sampled
    checks.record("interval_certificate_bounds_dense_h_grid", np.all(slack >= -1e-12) and
                  minimum_L_increment >= -1e-12,
                  {"minimum_bound_minus_dense_h": slack.min(),
                   "minimum_L_increment": minimum_L_increment,
                   "cases": len(p), "dense_points": 4097,
                   "scope": "Numerical implementation check; the analytic monotonic-L inequality supplies the all-u proof."})
    scaled = certify(model, theta, p/100, active, z)
    currency_error = np.max(np.abs(scaled["bound"]-result["bound"]))
    checks.record("interval_certificate_currency_invariance", currency_error < 2e-12,
                  {"max_bound_change": currency_error})
    counter_model = ConditionalMAIDADS(2, 0, commitment=False)
    counter_theta = np.array([5., -5., 0., 1.])
    counter = certify(counter_model, counter_theta, np.array([[10., .00001]]),
                      np.array([[True, True]]))
    checks.record("interval_certificate_rejects_nonunique_root_counterexample",
                  not counter["certified_positive_slope"][0], {"bound": counter["bound"][0]})


def main():
    source = BASE / "code" / "maidads_hurdle.py"
    source_hash_before = hashlib.sha256(source.read_bytes()).hexdigest()
    checks = Checks()
    for k, commitment, demographics in [(3, False, 0), (4, True, 2), (8, True, 2), (10, True, 2)]:
        try:
            check_conditional(checks, k, commitment, demographics)
        except Exception as exc:
            checks.record(f"K{k}_uncaught_test_exception", False, {"exception": repr(exc)})
    try:
        check_hurdle(checks)
    except Exception as exc:
        checks.record("hurdle_uncaught_test_exception", False, {"exception": repr(exc)})
    try:
        check_interval_certificate(checks)
    except Exception as exc:
        checks.record("interval_certificate_uncaught_test_exception", False, {"exception": repr(exc)})
    counterexamples = diagnostic_counterexamples()
    source_hash_after = hashlib.sha256(source.read_bytes()).hexdigest()
    checks.record("source_unchanged_during_test", source_hash_before == source_hash_after,
                  {"source_sha256_before": source_hash_before, "source_sha256_after": source_hash_after})
    report = {
        "source_sha256": source_hash_after,
        "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "numerical_tests_passed": all(r["passed"] for r in checks.records),
        "tests": checks.records,
        "diagnostic_counterexamples": counterexamples,
        "optimizer_failure_rejection_passed": not counterexamples["optimizer_failure"]["kernel_accepts_unsuccessful_optimizer"],
        "universal_root_safety_established": False,
        "fitted_data_and_forecast_working_domains_audited": False,
        "scope": "Synthetic structural and derivative tests; not evidence of fitted-data convergence or sampling inference.",
    }
    output = BASE / "outputs" / "structural_unit_tests.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(safe_json(report), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    failures = [r["test"] for r in checks.records if not r["passed"]]
    print(json.dumps({"output": str(output), "numerical_tests": len(checks.records),
                      "failed_tests": failures,
                      "optimizer_failure_rejection_passed": report["optimizer_failure_rejection_passed"],
                      "universal_root_safety_established": False},
                     ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
