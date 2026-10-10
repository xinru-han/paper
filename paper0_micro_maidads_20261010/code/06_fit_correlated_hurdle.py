"""Single-common-factor probit participation with fixed Stata marginal offsets.

The nonnegative factor loadings model positive dependence only. Marginal
probabilities remain Phi(xb). Joint patterns are conditioned on at least one
positive food. Offset uncertainty is not propagated into factor inference.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.polynomial.hermite import hermgauss
from scipy.optimize import minimize
from scipy.special import log_ndtr, logsumexp


ROOT = Path(__file__).resolve().parents[1]
LOG_SQRT_TWO_PI = .5 * np.log(2 * np.pi)
LOADING_UPPER_BOUND = .92


def normal_quadrature(nodes: int) -> tuple[np.ndarray, np.ndarray]:
    points, weights = hermgauss(nodes)
    return np.sqrt(2) * points, weights / np.sqrt(np.pi)


def node_arrays(xb: np.ndarray, loadings: np.ndarray, nodes: int) -> tuple:
    points, weights = normal_quadrature(nodes)
    scales = np.sqrt(1 - loadings**2)
    eta = (xb[:, None, :] + points[None, :, None] * loadings[None, None, :]) / scales
    log_positive, log_negative = log_ndtr(eta), log_ndtr(-eta)
    log_density = -.5 * eta**2 - LOG_SQRT_TWO_PI
    positive_score = np.exp(log_density - log_positive) / scales
    negative_score = -np.exp(log_density - log_negative) / scales
    return points, weights, eta, log_positive, log_negative, positive_score, negative_score


def joint_pattern_weights(xb: np.ndarray, loadings: np.ndarray, sets: np.ndarray,
                          dy_xb: np.ndarray | None = None,
                          price_xb: np.ndarray | None = None,
                          nodes: int = 32) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None]:
    """Return pattern probabilities and derivatives with respect to log covariates.

    xb is observations x goods, sets is patterns x goods, dy_xb is observations
    x goods, and price_xb is observations x goods x price covariates. Derivatives
    include the nonempty-pattern normalizer. Use batches for large pattern sets.
    """
    xb, loadings, sets = np.asarray(xb, float), np.asarray(loadings, float), np.asarray(sets, float)
    if xb.ndim == 1:
        xb = xb[None, :]
    if sets.ndim != 2 or sets.shape[1] != xb.shape[1] or np.any(sets.sum(axis=1) == 0):
        raise ValueError("sets must contain nonempty binary patterns x goods")
    if not np.all((sets == 0) | (sets == 1)):
        raise ValueError("patterns must be binary")
    _, weights, _, log_pos, log_neg, positive_score, negative_score = node_arrays(xb, loadings, nodes)
    log_joint = (np.einsum("nfk,sk->nfs", log_pos, sets, optimize=True)
                 + np.einsum("nfk,sk->nfs", log_neg, 1 - sets, optimize=True))
    weighted_mass = np.exp(log_joint) * weights[None, :, None]
    raw_probability = weighted_mass.sum(axis=1)
    empty_mass = np.exp(log_neg.sum(axis=2)) * weights[None, :]
    empty_probability = empty_mass.sum(axis=1)
    denominator = 1 - empty_probability
    if np.any(denominator <= 0):
        raise FloatingPointError("No positive-probability nonempty consumption pattern")
    probability = raw_probability / denominator[:, None]
    derivative_y = None if dy_xb is None else np.zeros_like(raw_probability)
    derivative_price = None if price_xb is None else np.zeros((*raw_probability.shape, price_xb.shape[2]))
    empty_derivative_y = np.zeros(len(xb))
    empty_derivative_price = None if price_xb is None else np.zeros((len(xb), price_xb.shape[2]))
    if dy_xb is not None or price_xb is not None:
        for j in range(xb.shape[1]):
            derivative_xb = (np.einsum("nfs,nf->ns", weighted_mass, positive_score[:, :, j]) * sets[None, :, j]
                + np.einsum("nfs,nf->ns", weighted_mass, negative_score[:, :, j]) * (1 - sets[None, :, j]))
            empty_derivative = np.sum(empty_mass * negative_score[:, :, j], axis=1)
            if dy_xb is not None:
                derivative_y += derivative_xb * dy_xb[:, j, None]
                empty_derivative_y += empty_derivative * dy_xb[:, j]
            if price_xb is not None:
                derivative_price += derivative_xb[:, :, None] * price_xb[:, j, None, :]
                empty_derivative_price += empty_derivative[:, None] * price_xb[:, j, :]
        if derivative_y is not None:
            derivative_y = (derivative_y / denominator[:, None]
                + probability * empty_derivative_y[:, None] / denominator[:, None])
        if derivative_price is not None:
            derivative_price = (derivative_price / denominator[:, None, None]
                + probability[:, :, None] * empty_derivative_price[:, None, :] / denominator[:, None, None])
    return probability, derivative_y, derivative_price


def conditional_loglikelihood(xb: np.ndarray, observed: np.ndarray, loadings: np.ndarray,
                             nodes: int = 32, gradient: bool = False) -> tuple[np.ndarray, np.ndarray | None]:
    points, weights, eta, log_pos, log_neg, pos_score, neg_score = node_arrays(xb, loadings, nodes)
    log_weights = np.log(weights)[None, :]
    log_observed = np.sum(log_pos * observed[:, None, :] + log_neg * (1 - observed[:, None, :]), axis=2)
    log_empty = np.sum(log_neg, axis=2)
    log_joint = logsumexp(log_observed + log_weights, axis=1)
    log_empty_probability = logsumexp(log_empty + log_weights, axis=1)
    empty_probability = np.exp(log_empty_probability)
    normalizer = 1 - empty_probability
    if np.any(normalizer <= 0):
        raise FloatingPointError("Nonempty likelihood normalization fails")
    loglik = log_joint - np.log1p(-empty_probability)
    if not gradient:
        return loglik, None
    scales = np.sqrt(1 - loadings**2)
    eta_loading_derivative = ((points[None, :, None] + loadings[None, None, :] * xb[:, None, :])
                              / scales[None, None, :]**3)
    # node_arrays' index scores already divide by sqrt(1-lambda^2).
    node_score = (observed[:, None, :] * pos_score + (1 - observed[:, None, :]) * neg_score)
    node_score *= scales[None, None, :] * eta_loading_derivative
    posterior = np.exp(log_observed + log_weights - log_joint[:, None])
    likelihood_score = np.sum(posterior[:, :, None] * node_score, axis=1)
    empty_weighted = np.exp(log_empty + log_weights)
    empty_node_score = neg_score * scales[None, None, :] * eta_loading_derivative
    empty_derivative = np.sum(empty_weighted[:, :, None] * empty_node_score, axis=1)
    likelihood_score += empty_derivative / normalizer[:, None]
    return loglik, likelihood_score


def calibration(xb: np.ndarray, observed: np.ndarray, loadings: np.ndarray,
                nodes: int = 32) -> tuple[pd.DataFrame, dict]:
    n, k = observed.shape
    masks = np.arange(1, 2**k)
    powers = 2**np.arange(k)
    sets = ((masks[:, None] & powers[None, :]) > 0).astype(int)
    counts = np.bincount(observed @ powers, minlength=2**k)[1:]
    expected = np.zeros(len(sets))
    max_sum_error = 0.
    for start in range(0, n, 48):
        probability = joint_pattern_weights(xb[start:start+48], loadings, sets, nodes=nodes)[0]
        max_sum_error = max(max_sum_error, float(np.max(np.abs(probability.sum(axis=1) - 1))))
        expected += probability.sum(axis=0)
    assert max_sum_error < 1e-10
    result = pd.DataFrame({"mask": masks,
        "binary_goods_1_to_K": ["".join(str(x) for x in row) for row in sets],
        "number_positive_goods": sets.sum(axis=1), "observed_count": counts,
        "observed_share": counts/n, "predicted_count": expected, "predicted_share": expected/n,
        "observed_minus_expected_count": counts - expected})
    summary = {"N": n, "total_variation_distance": float(.5*np.sum(np.abs(counts-expected))/n),
        "all_positive_observed_share": float(counts[-1]/n),
        "all_positive_predicted_share": float(expected[-1]/n),
        "max_pattern_probability_sum_error": max_sum_error,
        "max_absolute_share_gap": float(np.max(np.abs(counts-expected))/n)}
    return result, summary


def finite_difference_audit(xb: np.ndarray, observed: np.ndarray, loadings: np.ndarray) -> dict:
    step = 1e-5
    _, analytical = conditional_loglikelihood(xb, observed, loadings, gradient=True)
    gradient_errors = []
    for j in range(xb.shape[1]):
        plus, minus = loadings.copy(), loadings.copy()
        plus[j] += step
        minus[j] -= step
        difference = (conditional_loglikelihood(xb, observed, plus)[0]
                      - conditional_loglikelihood(xb, observed, minus)[0]) / (2*step)
        gradient_errors.append(float(np.max(np.abs(difference - analytical[:, j]))))
    k = xb.shape[1]
    masks = np.arange(1, 2**k)
    sets = ((masks[:, None] & (2**np.arange(k))[None, :]) > 0).astype(int)
    direction = np.linspace(-.2, .2, k)[None, :] * np.ones((len(xb), 1))
    price_direction = np.repeat(direction[:, :, None], 2, axis=2)
    price_direction[:, :, 1] *= -2
    probability, derivative_y, derivative_price = joint_pattern_weights(
        xb, loadings, sets, direction, price_direction)
    plus = joint_pattern_weights(xb + step*direction, loadings, sets)[0]
    minus = joint_pattern_weights(xb - step*direction, loadings, sets)[0]
    probability_error = float(np.max(np.abs((plus-minus)/(2*step)-derivative_y)))
    price_plus = joint_pattern_weights(xb + step*price_direction[:, :, 1], loadings, sets)[0]
    price_minus = joint_pattern_weights(xb - step*price_direction[:, :, 1], loadings, sets)[0]
    price_error = float(np.max(np.abs((price_plus-price_minus)/(2*step)-derivative_price[:, :, 1])))
    sum_error = float(np.max(np.abs(probability.sum(axis=1)-1)))
    derivative_sum_error = float(np.max(np.abs(derivative_y.sum(axis=1))))
    assert max(gradient_errors) < 1e-5, gradient_errors
    assert probability_error < 1e-6, probability_error
    assert price_error < 1e-6 and sum_error < 1e-10 and derivative_sum_error < 1e-10
    return {"likelihood_loading_gradient_max_absolute_error": max(gradient_errors),
        "income_probability_derivative_max_absolute_error": probability_error,
        "price_probability_derivative_interface_max_absolute_error": price_error,
        "probability_sum_error": sum_error, "derivative_sum_error": derivative_sum_error}


def fit_variant(k: int) -> dict:
    output = ROOT / "outputs" / f"stata_stage1_{k}"
    frame = pd.read_csv(output / "household_predictions.csv")
    frame = frame.loc[frame.fs_sample_main.eq(1)].reset_index(drop=True)
    status = pd.read_csv(output / "estimation_status.csv").fillna("")
    xb = frame[[f"participation_xb{j}" for j in range(1, k+1)]].to_numpy(float)
    observed = frame[[f"positive_q{j}" for j in range(1, k+1)]].to_numpy(int)
    if not np.isfinite(xb).all():
        raise ValueError("Finite Stata xb required for common-factor offsets")
    fixed = []
    for j in range(1, k+1):
        row = status.loc[status.model.eq(f"participation_g{j}")].iloc[0]
        if row.fallback or row.method != "probit":
            fixed.append(j-1)
    free = [j for j in range(k) if j not in fixed]
    def objective(raw: np.ndarray) -> tuple[float, np.ndarray]:
        loadings = np.zeros(k)
        loadings[free] = raw
        loglik, score = conditional_loglikelihood(xb, observed, loadings, gradient=True)
        return float(-loglik.mean()), -score[:, free].mean(axis=0)
    attempts = []
    solutions = []
    for initial in (.2, .45, .65):
        fit = minimize(objective, np.full(len(free), initial), jac=True, method="L-BFGS-B",
                       bounds=[(0, LOADING_UPPER_BOUND)]*len(free),
                       options={"maxiter": 400, "ftol": 1e-13, "gtol": 1e-8, "maxls": 40})
        solutions.append(fit)
        attempts.append({"initial_loading": initial, "success": bool(fit.success),
            "message": str(fit.message), "iterations": int(fit.nit),
            "negative_mean_log_likelihood": float(fit.fun), "loadings_free": fit.x.tolist()})
    best = min(solutions, key=lambda value: value.fun)
    loadings = np.zeros(k)
    loadings[free] = best.x
    loglik, scores = conditional_loglikelihood(xb, observed, loadings, 32, True)
    ll32 = float(loglik.sum())
    ll64 = float(conditional_loglikelihood(xb, observed, loadings, 64)[0].sum())
    independent_ll = float(conditional_loglikelihood(xb, observed, np.zeros(k))[0].sum())
    patterns, calibration_summary = calibration(xb, observed, loadings)
    patterns.to_csv(output / "correlated_hurdle_pattern_calibration.csv", index=False)
    patterns.nlargest(20,"observed_count").to_csv(output / "correlated_hurdle_pattern_calibration_top20.csv", index=False)
    gradient = -scores[:, free].mean(axis=0)
    projected = gradient.copy()
    projected[(best.x<=1e-7)&(gradient>0)] = 0
    projected[(best.x>=LOADING_UPPER_BOUND-1e-7)&(gradient<0)] = 0
    validation = finite_difference_audit(xb[:8], observed[:8], loadings)
    result = {"system_goods": k, "N": len(frame), "loadings": loadings.tolist(),
        "lambda": loadings.tolist(), "fixed_zero_goods": [j+1 for j in fixed],
        "quadrature_nodes": 32, "log_likelihood": ll32,
        "fixed_parameter_log_likelihood_64_nodes": ll64,
        "quadrature_64_minus_32_log_likelihood": ll64-ll32,
        "independent_log_likelihood": independent_ll,
        "descriptive_twice_loglikelihood_gain": 2*(ll32-independent_ll),
        "number_factor_parameters": len(free), "AIC_conditional_offsets": -2*ll32+2*len(free),
        "BIC_conditional_offsets": -2*ll32+len(free)*np.log(len(frame)),
        "optimizer_success": bool(best.success), "projected_mean_score_max": float(np.max(np.abs(projected))),
        "attempts": attempts, "calibration": calibration_summary, "derivative_validation": validation,
        "limitations": ["Nonnegative single factor permits only positive latent participation dependence",
            "Stata marginal probit xb offsets are held fixed; their uncertainty is not propagated",
            "Common participation factor is assumed independent of conditional Dirichlet demand error",
            "No conventional LR p-value: the independence null is a singular boundary loading null",
            "This is a participation extension of MAIDADS; not a utility-theoretic full corner-solution model"]}
    (output / "correlated_hurdle_fit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    descriptions = pd.read_csv(ROOT / "outputs" / "food_group_descriptives.csv")
    names = dict(zip(descriptions.loc[descriptions.system_goods.eq(k), "group"],
                     descriptions.loc[descriptions.system_goods.eq(k), "group_name"]))
    pd.DataFrame([{"good": j+1,"group_name": names[j+1], "loading": loadings[j],
        "fixed_zero_weak_or_universal_margin": j in fixed,
        "loading_at_upper_guard": loadings[j]>=LOADING_UPPER_BOUND-1e-6}
        for j in range(k)]).to_csv(output / "correlated_hurdle_loadings.csv",index=False)
    independent_summary = json.loads((output / "participation_independence_summary.json").read_text())
    comparison = [{"model": "independent", "log_likelihood": independent_ll,"factor_parameters": 0,
        "AIC_conditional_offsets": -2*independent_ll,"BIC_conditional_offsets": -2*independent_ll,
        "total_variation_distance": independent_summary["total_variation_distance"],
        "all_positive_observed_share": calibration_summary["all_positive_observed_share"],
        "all_positive_predicted_share": independent_summary["predicted_all_positive_share"]},
        {"model": "single_factor", "log_likelihood": ll32,"factor_parameters":len(free),
        "AIC_conditional_offsets":result["AIC_conditional_offsets"],"BIC_conditional_offsets":result["BIC_conditional_offsets"],
        "total_variation_distance":calibration_summary["total_variation_distance"],
        "all_positive_observed_share":calibration_summary["all_positive_observed_share"],
        "all_positive_predicted_share":calibration_summary["all_positive_predicted_share"]}]
    pd.DataFrame(comparison).to_csv(output / "correlated_hurdle_comparison.csv",index=False)
    print(json.dumps({key:result[key] for key in ("system_goods","loadings","log_likelihood", "quadrature_64_minus_32_log_likelihood", "projected_mean_score_max", "calibration")},ensure_ascii=False),flush=True)
    return result


if __name__ == "__main__":
    for goods in (8, 10):
        fit_variant(goods)
