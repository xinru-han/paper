"""Audit the Stata-to-MAIDADS design and forecast interface."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr


ROOT = Path(__file__).resolve().parents[1]


def reconstruct(frame: pd.DataFrame, coefficients: pd.DataFrame) -> np.ndarray:
    value = np.zeros(len(frame))
    for row in coefficients.itertuples():
        if row.term == "_cons":
            value += row.coefficient
        elif row.coefficient != 0:
            value += row.coefficient * frame[row.term].to_numpy(float)
    return value


def audit_variant(number_goods: int) -> dict:
    output = ROOT / "outputs" / f"stata_stage1_{number_goods}"
    frame = pd.read_csv(output / "household_predictions.csv", dtype={"household_id": str})
    coeff = pd.read_csv(output / "coefficients.csv")
    status = pd.read_csv(output / "estimation_status.csv")
    valid = frame.fs_valid.eq(1)
    result = {
        "number_goods": number_goods,
        "observations": len(frame),
        "model_observations": int(frame.fs_sample_main.sum()),
        "raw_observations": int(frame.fs_sample_raw.sum()),
        "trimmed_observations": int(frame.fs_sample_income_trim.sum()),
        "all_observed_zero_food_budgets": int(frame.food_budget_pc_month.eq(0).sum()),
        "unknown_family_model_observations": int((frame.fs_sample_main.eq(1) & frame.family_type.eq(0)).sum()),
        "model_reconstruction": {},
    }
    for model, rows in coeff.groupby("model"):
        linear = reconstruct(frame, rows)
        if model.startswith("food_budget_"):
            suffix = model.removeprefix("food_budget_")
            expected = frame[f"food_budget_hat_{suffix}"].to_numpy(float)
            predicted = np.exp(linear)
            relative = np.abs(predicted[valid] / expected[valid] - 1)
            error = float(relative.max())
            assert error < 1e-10, (model, error)
            result["model_reconstruction"][model] = {"max_relative_error": error}
        else:
            good = int(model.removeprefix("participation_g"))
            expected = frame[f"participation_p{good}"].to_numpy(float)
            error = float(np.abs(ndtr(linear[valid]) - expected[valid]).max())
            assert error < 1e-10, (model, error)
            result["model_reconstruction"][model] = {"max_absolute_error": error}
    for row in status.itertuples():
        if row.method not in {"constant_probability", "sample_probability"}:
            assert row.return_code == 0 and row.converged == 1, row
    covariance = pd.read_csv(output / "covariance.csv")
    for model, rows in covariance.groupby("model"):
        matrix = rows.pivot(index="row_term", columns="column_term", values="covariance")
        values = matrix.to_numpy(float)
        assert np.max(np.abs(values - values.T)) < 1e-12, model
        assert np.linalg.eigvalsh(values).min() > -1e-9, model
    summaries = []
    for specification in ("main", "raw", "fooddeflated", "income_trim"):
        column = f"food_income_elast_{specification}"
        for family in ("all", *sorted(frame.loc[frame.fs_sample_main.eq(1), "family_type"].unique())):
            mask = frame.fs_sample_main.eq(1)
            if family != "all":
                mask &= frame.family_type.eq(family)
            values = frame.loc[mask, column]
            summaries.append({
                "model": f"food_budget_{specification}", "family_type": family,
                "N": len(values), "mean_income_elasticity": values.mean(),
                "p05": values.quantile(.05), "p50": values.quantile(.50),
                "p95": values.quantile(.95), "negative_slope_rate": values.lt(0).mean(),
                "empirical_1_99_income_support_rate": frame.loc[mask, "fs_income_supported"].mean(),
            })
    pd.DataFrame(summaries).to_csv(output / "income_slope_support_audit.csv", index=False)
    (output / "first_stage_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    for goods in (8, 10):
        result = audit_variant(goods)
        print(json.dumps(result, ensure_ascii=False))
