"""Diagnose the conditional-independence approximation of participation probits.

Residual cross-moment tests use village-year cluster sandwiches, including
probit-parameter estimation through the stacked estimating-equation influence
function. Pattern frequencies are descriptive calibration checks, not likelihood
ratio tests, because the fitted household probabilities are heterogeneous.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
PROBABILITY_GUARD = 1e-9


def bh_adjust(values: np.ndarray) -> np.ndarray:
    result = np.full(len(values), np.nan)
    valid = np.flatnonzero(np.isfinite(values))
    order = valid[np.argsort(values[valid])]
    adjusted = values[order] * len(valid) / np.arange(1, len(valid) + 1)
    if len(order):
        result[order] = np.minimum(1, np.minimum.accumulate(adjusted[::-1])[::-1])
    return result


def margin_influence(frame: pd.DataFrame, coefficients: pd.DataFrame, good: int) -> dict:
    probability = frame[f"participation_p{good}"].to_numpy(float)
    observed = frame[f"positive_q{good}"].to_numpy(float)
    guarded = np.clip(probability, PROBABILITY_GUARD, 1 - PROBABILITY_GUARD)
    variance = guarded * (1 - guarded)
    residual = (observed - guarded) / np.sqrt(variance)
    rows = coefficients.loc[coefficients.model.eq(f"participation_g{good}")]
    rows = rows.loc[rows.zero_variance.eq(0)]
    if not len(rows):
        return {"p": probability, "d": observed, "z": residual, "X": np.empty((len(frame), 0)),
                "score": np.empty((len(frame), 0)), "bread_inverse": np.empty((0, 0)),
                "residual_eta_derivative": np.zeros(len(frame)), "bread_min_eigenvalue": None,
                "guarded_probability_count": int(np.sum(probability != guarded))}
    terms = rows.term.tolist()
    design = np.column_stack([np.ones(len(frame)) if name == "_cons" else frame[name].to_numpy(float)
                              for name in terms])
    eta = design @ rows.coefficient.to_numpy(float)
    assert np.max(np.abs(ndtr(eta) - probability)) < 1e-10
    density = np.exp(-.5 * eta**2) / np.sqrt(2 * np.pi)
    difference = observed - guarded
    score_scalar = density * difference / variance
    # Negative derivative of the probit score with respect to its linear index.
    information_weight = (eta * density * difference / variance + density**2 / variance
                          + density**2 * difference * (1 - 2 * guarded) / variance**2)
    bread = (design.T * information_weight) @ design / len(frame)
    inverse = np.linalg.pinv(bread, rcond=1e-11)
    residual_derivative = density * (-1 / np.sqrt(variance)
                          - .5 * difference * (1 - 2 * guarded) / variance**1.5)
    return {"p": probability, "d": observed, "z": residual, "X": design,
            "score": design * score_scalar[:, None], "bread_inverse": inverse,
            "residual_eta_derivative": residual_derivative,
            "bread_min_eigenvalue": float(np.linalg.eigvalsh(bread).min()),
            "guarded_probability_count": int(np.sum(probability != guarded))}


def association_rows(frame: pd.DataFrame, coefficients: pd.DataFrame, names: dict[int, str], k: int) -> pd.DataFrame:
    n = len(frame)
    cluster, cluster_names = pd.factorize(frame.village_cluster, sort=True)
    groups = len(cluster_names)
    margins = [margin_influence(frame, coefficients, good) for good in range(1, k + 1)]
    rows = []
    for left, right in combinations(range(k), 2):
        a, b = margins[left], margins[right]
        product = a["z"] * b["z"]
        mean = product.mean()
        influence = product - mean
        for own, other in ((a, b), (b, a)):
            if own["X"].shape[1]:
                gradient = ((other["z"] * own["residual_eta_derivative"]) @ own["X"]) / n
                influence += own["score"] @ (own["bread_inverse"] @ gradient)
        cluster_score = np.bincount(cluster, weights=influence, minlength=groups)
        variance = groups / (groups - 1) * np.sum(cluster_score**2) / n**2
        se = float(np.sqrt(variance))
        no_variation = a["d"].std() == 0 or b["d"].std() == 0
        p = float(2 * student_t.sf(abs(mean / se), groups - 1)) if se > 0 and not no_variation else np.nan
        correlation = float(np.corrcoef(a["z"], b["z"])[0, 1]) if not no_variation else np.nan
        rows.append({"good_i": left + 1, "good_j": right + 1,
                     "name_i": names[left + 1], "name_j": names[right + 1],
                     "N": n, "clusters": groups, "standardized_residual_correlation": correlation,
                     "mean_standardized_residual_product": mean, "cluster_std_error": se,
                     "cluster_t_statistic": mean / se if se > 0 else np.nan,
                     "p_value_cluster_adjusted_for_probit_estimation": p,
                     "bread_min_eigenvalue_i": a["bread_min_eigenvalue"],
                     "bread_min_eigenvalue_j": b["bread_min_eigenvalue"],
                     "guarded_probability_count_i": a["guarded_probability_count"],
                     "guarded_probability_count_j": b["guarded_probability_count"],
                     "no_outcome_variation": no_variation})
    output = pd.DataFrame(rows)
    values = output.p_value_cluster_adjusted_for_probit_estimation.to_numpy(float)
    output["p_value_bh_fdr"] = bh_adjust(values)
    output["p_value_bonferroni"] = np.minimum(1, values * np.isfinite(values).sum())
    return output


def pattern_calibration(frame: pd.DataFrame, k: int) -> tuple[pd.DataFrame, dict]:
    n = len(frame)
    probabilities = frame[[f"participation_p{j}" for j in range(1, k + 1)]].to_numpy(float)
    observed = frame[[f"positive_q{j}" for j in range(1, k + 1)]].to_numpy(int)
    powers = 2 ** np.arange(k)
    masks = np.arange(2**k)
    bits = ((masks[:, None] & powers[None, :]) > 0).astype(int)
    # Exact heterogeneous independent-Bernoulli pattern probabilities.
    probability = np.prod(np.where(bits[None, :, :] == 1,
                         probabilities[:, None, :], 1 - probabilities[:, None, :]), axis=2)
    assert np.max(np.abs(probability.sum(axis=1) - 1)) < 1e-12
    conditioned = probability.copy()
    conditioned[:, 0] = 0
    conditioned /= (1 - probability[:, 0])[:, None]
    observed_masks = observed @ powers
    counts = np.bincount(observed_masks, minlength=2**k)
    expected = probability.sum(axis=0)
    conditional_expected = conditioned.sum(axis=0)
    variance = (conditioned * (1 - conditioned)).sum(axis=0)
    residual = (counts - conditional_expected) / np.sqrt(np.maximum(variance, 1e-15))
    output = pd.DataFrame({"mask": masks,
        "binary_goods_1_to_K": ["".join(str(x) for x in row) for row in bits],
        "number_positive_goods": bits.sum(axis=1), "observed_count": counts,
        "observed_share": counts / n, "predicted_independent_count": expected,
        "predicted_nonempty_conditioned_count": conditional_expected,
        "predicted_nonempty_conditioned_share": conditional_expected / n,
        "observed_minus_expected_count": counts - conditional_expected,
        "descriptive_standardized_count_gap": residual})
    summary = {"N": n, "possible_patterns_including_empty": int(2**k),
        "observed_distinct_patterns": int(np.sum(counts > 0)),
        "observed_empty_patterns": int(counts[0]),
        "predicted_unconditioned_empty_count": float(expected[0]),
        "total_variation_distance": float(.5 * np.sum(np.abs(counts - conditional_expected)) / n),
        "count_RMSE": float(np.sqrt(np.mean((counts - conditional_expected)**2))),
        "max_absolute_share_gap": float(np.max(np.abs(counts - conditional_expected)) / n),
        "observed_all_positive_share": float(counts[-1] / n),
        "predicted_all_positive_share": float(conditional_expected[-1] / n),
        "definition": "Heterogeneous household independent probits; exact patterns conditioned on at least one positive food",
        "calibration_inference": "Pattern standardized gaps are descriptive; no chi-square p-values are claimed"}
    return output, summary


def main() -> None:
    all_summary = []
    descriptions = pd.read_csv(ROOT / "outputs" / "food_group_descriptives.csv")
    for k in (8, 10):
        output = ROOT / "outputs" / f"stata_stage1_{k}"
        frame = pd.read_csv(output / "household_predictions.csv")
        frame = frame.loc[frame.fs_sample_main.eq(1)].reset_index(drop=True)
        coefficients = pd.read_csv(output / "coefficients.csv")
        description = descriptions.loc[descriptions.system_goods.eq(k) & descriptions["sample"].eq("model")]
        names = dict(zip(description.group.astype(int), description.group_name))
        associations = association_rows(frame, coefficients, names, k)
        associations.to_csv(output / "residual_association.csv", index=False)
        calibration, summary = pattern_calibration(frame, k)
        calibration.to_csv(output / "participation_pattern_calibration.csv", index=False)
        calibration.nlargest(20, "observed_count").to_csv(output / "participation_pattern_calibration_top20.csv", index=False)
        summary.update({"system_goods": k, "pairwise_tests": len(associations),
            "pairs_nominal_p_below_05": int(associations.p_value_cluster_adjusted_for_probit_estimation.lt(.05).sum()),
            "pairs_BH_FDR_below_05": int(associations.p_value_bh_fdr.lt(.05).sum()),
            "pairs_Bonferroni_below_05": int(associations.p_value_bonferroni.lt(.05).sum()),
            "residual_inference": "Village-year cluster sandwich with probit-estimation influence correction; asymptotic diagnostic, not structural identification"})
        (output / "participation_independence_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rates = [{"good": j, "group_name": names[j], "N": len(frame),
                  "observed_participation_rate": frame[f"positive_q{j}"].mean(),
                  "predicted_probability_mean": frame[f"participation_p{j}"].mean(),
                  "probability_p01": frame[f"participation_p{j}"].quantile(.01),
                  "probability_p99": frame[f"participation_p{j}"].quantile(.99)}
                 for j in range(1, k + 1)]
        pd.DataFrame(rates).to_csv(output / "participation_rates.csv", index=False)
        all_summary.append(summary)
        print(json.dumps(summary, ensure_ascii=False))
    pd.DataFrame(all_summary).to_csv(ROOT / "outputs" / "participation_independence_summary.csv", index=False)


if __name__ == "__main__":
    main()
