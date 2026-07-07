#!/usr/bin/env python3
"""
sensitivity_eps.py  ─  Robustness of the bounded benchmark to the choice of ε
==============================================================================

Purpose
-------
The main paper uses ε = 0.02 as the lower/upper bound when clipping predicted
at-home ratios before converting to the adjustment-factor (AF) scale:

    r_tilde = min{max(r_hat, ε), 1 - ε}
    AF_tilde = 1 / r_tilde

This script re-evaluates the unified bounded benchmark at
    ε ∈ {0.005, 0.01, 0.02, 0.05, 0.10}
using the already-trained, already-saved OOS predictions produced by
`unified_bounded_model_benchmark_fast.py`. It therefore does NOT retrain any
model; it only re-clips and re-aggregates the saved predictions.

This is the script that fills the sentence in Section 5.5 of the paper:

    "Re-running the unified benchmark for ε ∈ {0.005, 0.01, 0.02, 0.05, 0.10}
     leaves the model ordering unchanged: the FT-Transformer remains the
     lowest-AF-MAE model at every value, and the relative AF-MAE differences
     between the top three models are stable to within ±5%."

Expected input
--------------
A detail CSV produced by the unified benchmark, with one row per
(model, category, fold, observation) containing at minimum:
    - model           : str
    - category        : str
    - fold            : int
    - y_true_ratio    : float in (0, 1]
    - y_pred_ratio    : float (pre-clip model output)

Default input path:
    final/unified_bounded_fast_detail.csv
Fallback to repo root if final/ copy not present.

Outputs (all under final/):
    final/tableA6_eps_sensitivity.csv       Summary: AF-MAE by (eps, model),
                                            model ranking and %-diff vs top.
    final/tableA6_eps_by_category.csv       AF-MAE by (eps, model, category).
    final/tidy_eps_sensitivity.csv          Tidy long-form file for plotting.
    final/figures/figA6_eps_sensitivity.pdf Optional ε-sensitivity plot
                                            (created only if matplotlib is
                                            available).

Usage
-----
    python sensitivity_eps.py
    python sensitivity_eps.py --input custom/detail.csv
    python sensitivity_eps.py --eps-grid 0.005 0.01 0.02 0.05 0.10 0.20
    python sensitivity_eps.py --skip-figure

Notes
-----
• If your detail CSV uses different column names, override them via
  --col-true, --col-pred, --col-model, --col-cat.
• Sugar and mutton are excluded by default (consistent with the main paper's
  headline tables); pass --keep-all to include them.
• Ranking is reported as (a) lowest AF-MAE across all categories included,
  and (b) lowest AF-MAE averaged across per-category ranks (category-robust).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
FINAL_DIR = BASE_DIR / "final"
FIG_DIR = FINAL_DIR / "figures"

DEFAULT_INPUT_CANDIDATES = [
    FINAL_DIR / "unified_bounded_fast_detail.csv",
    BASE_DIR / "unified_bounded_fast_detail.csv",
    FINAL_DIR / "data" / "unified_bounded_fast_detail.csv",
]

DEFAULT_EPS_GRID = [0.005, 0.01, 0.02, 0.05, 0.10]

# Categories excluded from headline tables in the main paper.
EXCLUDED_CATEGORIES = {"q_yangrou", "q_tang", "mutton", "sugar"}

MODEL_DISPLAY = {
    "fttransformer":  "FT-Transformer",
    "lightgbm":       "LightGBM",
    "randomforest":   "Random Forest",
    "linear":         "Ridge",
    "ridge":          "Ridge",
    "xgboost":        "XGBoost",
    "tabm":           "TabM",
    "lasso":          "Lasso",
    "catboost":       "CatBoost",
    "resnet_tabular": "Tabular ResNet",
    "resnet":         "Tabular ResNet",
    "mlp":            "MLP",
    "tabnet":         "TabNet",
    "ft":             "FT-Transformer",
}


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    print(msg, flush=True)


def _find_input(cli_path: str | None) -> Path:
    if cli_path:
        p = Path(cli_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Input file not found: {p}")
        return p
    for cand in DEFAULT_INPUT_CANDIDATES:
        if cand.exists():
            return cand
    hint = (
        "\n\nThis CSV is produced by the unified bounded benchmark pipeline "
        "(see docstring: `unified_bounded_model_benchmark_fast.py`), not by "
        "`predict_tabpfn.py`. You must either:\n"
        "  (1) Run that benchmark once so it writes "
        "`final/unified_bounded_fast_detail.csv`, or\n"
        "  (2) Copy your existing detail file into one of the paths above, or\n"
        "  (3) Pass an explicit path: python sensitivity_eps.py --input YOUR.csv\n"
    )
    raise FileNotFoundError(
        "Could not locate unified_bounded_fast_detail.csv in any of:\n  "
        + "\n  ".join(str(c) for c in DEFAULT_INPUT_CANDIDATES)
        + hint
    )


def _normalize_columns(
    df: pd.DataFrame,
    col_true: str,
    col_pred: str,
    col_model: str,
    col_cat: str,
) -> pd.DataFrame:
    """Map to canonical column names; also tolerate common aliases."""
    aliases = {
        col_true:  ["y_true_ratio", "y_true", "ratio", "target", "target_y", "y"],
        col_pred:  ["y_pred_ratio", "y_pred", "pred", "prediction", "ratio_pred"],
        col_model: ["model", "model_name", "method"],
        col_cat:   ["category", "food_category", "food", "item", "varname", "q_col"],
    }
    resolved = {}
    for canonical, candidates in aliases.items():
        if canonical in df.columns:
            resolved[canonical] = canonical
            continue
        for c in candidates:
            if c in df.columns:
                resolved[canonical] = c
                break
        else:
            raise KeyError(
                f"Required column '{canonical}' not found in input; "
                f"looked for aliases {candidates}. Available: {list(df.columns)}"
            )
    rename_map = {v: k for k, v in resolved.items() if v != k}
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def _apply_eps_and_compute_af(
    df: pd.DataFrame, eps: float, col_true: str, col_pred: str
) -> tuple[np.ndarray, np.ndarray]:
    """Return (AF_true, AF_tilde) for a given ε."""
    r_true = df[col_true].to_numpy(dtype=float)
    r_pred = df[col_pred].to_numpy(dtype=float)
    # Bound predictions only; true values are left as-is, but also clipped to
    # (eps, 1-eps) purely to avoid dividing by zero in AF_true (edge cases).
    r_pred_tilde = np.clip(r_pred, eps, 1.0 - eps)
    r_true_safe = np.clip(r_true, eps, 1.0)  # true is strictly positive
    AF_true = 1.0 / r_true_safe
    AF_tilde = 1.0 / r_pred_tilde
    return AF_true, AF_tilde


def _af_metrics(af_true: np.ndarray, af_pred: np.ndarray) -> dict:
    err = af_pred - af_true
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    return {"AF_MAE": mae, "AF_RMSE": rmse}


def _ratio_metrics(
    df: pd.DataFrame, eps: float, col_true: str, col_pred: str
) -> dict:
    r_true = df[col_true].to_numpy(dtype=float)
    r_pred = np.clip(df[col_pred].to_numpy(dtype=float), eps, 1.0 - eps)
    err = r_pred - r_true
    return {
        "Ratio_MAE":  float(np.mean(np.abs(err))),
        "Ratio_RMSE": float(np.sqrt(np.mean(err**2))),
    }


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def run(
    input_path: Path,
    eps_grid: Iterable[float],
    col_true: str,
    col_pred: str,
    col_model: str,
    col_cat: str,
    keep_all: bool,
    skip_figure: bool,
) -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    _log(f"[sensitivity_eps] input: {input_path}")
    df = pd.read_csv(input_path)
    _log(f"[sensitivity_eps] raw rows: {len(df):,}")

    df = _normalize_columns(df, col_true, col_pred, col_model, col_cat)

    # Drop rows with missing required values.
    req = [col_true, col_pred, col_model, col_cat]
    before = len(df)
    df = df.dropna(subset=req).copy()
    _log(f"[sensitivity_eps] after dropna: {len(df):,}  (-{before - len(df):,})")

    if not keep_all:
        df = df[~df[col_cat].isin(EXCLUDED_CATEGORIES)].copy()
        _log(
            f"[sensitivity_eps] excluded {sorted(EXCLUDED_CATEGORIES)}; "
            f"categories kept: {df[col_cat].nunique()}"
        )

    eps_grid = sorted(set(float(e) for e in eps_grid))
    _log(f"[sensitivity_eps] ε grid: {eps_grid}")

    # ── Aggregate metrics by (eps, model) ──────────────────────
    rows_summary = []
    rows_bycat = []

    for eps in eps_grid:
        AF_true_all, AF_pred_all = _apply_eps_and_compute_af(
            df, eps, col_true, col_pred
        )
        df_eps = df.assign(AF_true=AF_true_all, AF_pred=AF_pred_all)

        # Overall by model.
        for model, sub in df_eps.groupby(col_model, sort=False):
            m_af = _af_metrics(
                sub["AF_true"].to_numpy(), sub["AF_pred"].to_numpy()
            )
            m_r = _ratio_metrics(sub, eps, col_true, col_pred)
            rows_summary.append(
                {
                    "eps": eps,
                    "model": model,
                    "model_display": MODEL_DISPLAY.get(str(model).lower(), model),
                    "n_obs": len(sub),
                    **m_r,
                    **m_af,
                }
            )

        # By (model, category).
        for (model, cat), sub in df_eps.groupby(
            [col_model, col_cat], sort=False
        ):
            m_af = _af_metrics(
                sub["AF_true"].to_numpy(), sub["AF_pred"].to_numpy()
            )
            m_r = _ratio_metrics(sub, eps, col_true, col_pred)
            rows_bycat.append(
                {
                    "eps": eps,
                    "model": model,
                    "model_display": MODEL_DISPLAY.get(str(model).lower(), model),
                    "category": cat,
                    "n_obs": len(sub),
                    **m_r,
                    **m_af,
                }
            )

    summary = pd.DataFrame(rows_summary).sort_values(
        ["eps", "AF_MAE"]
    ).reset_index(drop=True)
    bycat = pd.DataFrame(rows_bycat).sort_values(
        ["eps", "category", "AF_MAE"]
    ).reset_index(drop=True)

    # Rank within each ε.
    summary["rank_AF_MAE"] = (
        summary.groupby("eps")["AF_MAE"].rank(method="min").astype(int)
    )

    # % deviation from best-in-eps.
    best_by_eps = summary.loc[summary["rank_AF_MAE"] == 1, ["eps", "AF_MAE"]]
    best_by_eps = best_by_eps.rename(columns={"AF_MAE": "AF_MAE_best"})
    summary = summary.merge(best_by_eps, on="eps", how="left")
    summary["pct_vs_best"] = 100.0 * (
        summary["AF_MAE"] / summary["AF_MAE_best"] - 1.0
    )

    # ── Tidy long-form for plotting ────────────────────────────
    tidy = summary[
        ["eps", "model", "model_display", "AF_MAE", "rank_AF_MAE", "pct_vs_best"]
    ].copy()

    # ── Write outputs ─────────────────────────────────────────
    out_summary = FINAL_DIR / "tableA6_eps_sensitivity.csv"
    out_bycat = FINAL_DIR / "tableA6_eps_by_category.csv"
    out_tidy = FINAL_DIR / "tidy_eps_sensitivity.csv"

    summary.to_csv(out_summary, index=False)
    bycat.to_csv(out_bycat, index=False)
    tidy.to_csv(out_tidy, index=False)

    _log(f"[sensitivity_eps] wrote {out_summary}  ({len(summary)} rows)")
    _log(f"[sensitivity_eps] wrote {out_bycat}    ({len(bycat)} rows)")
    _log(f"[sensitivity_eps] wrote {out_tidy}     ({len(tidy)} rows)")

    # ── Print headline table to stdout ────────────────────────
    _log("\n[sensitivity_eps] Headline AF-MAE by (ε, model):")
    pivot = summary.pivot(index="model_display", columns="eps", values="AF_MAE")
    with pd.option_context("display.float_format", "{:.4f}".format):
        _log(pivot.to_string())

    _log("\n[sensitivity_eps] Rank by (ε, model):")
    rank_pivot = summary.pivot(
        index="model_display", columns="eps", values="rank_AF_MAE"
    )
    _log(rank_pivot.to_string())

    # Check the claim used in the paper:
    #   top model is invariant across ε, top-3 gap stable to within ±5%
    top_models = {
        eps: summary[summary.eps == eps].sort_values("AF_MAE").iloc[0]["model_display"]
        for eps in eps_grid
    }
    invariant = len(set(top_models.values())) == 1
    _log(f"\n[sensitivity_eps] Top model invariant across ε? {invariant}")
    _log(f"[sensitivity_eps] Top model by ε: {top_models}")

    top3_gaps = []
    for eps in eps_grid:
        sub = summary[summary.eps == eps].sort_values("AF_MAE").head(3)
        if len(sub) == 3:
            gap = 100.0 * (sub["AF_MAE"].iloc[2] / sub["AF_MAE"].iloc[0] - 1.0)
            top3_gaps.append(gap)
    if top3_gaps:
        _log(
            f"[sensitivity_eps] Top-3 AF-MAE spread (3rd vs 1st) across ε: "
            f"min={min(top3_gaps):.2f}%, max={max(top3_gaps):.2f}%"
        )

    # ── Optional figure ───────────────────────────────────────
    if not skip_figure:
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(7.0, 4.5))
            for model, sub in summary.groupby("model_display"):
                sub = sub.sort_values("eps")
                plt.plot(sub["eps"], sub["AF_MAE"], marker="o", label=model)
            plt.xscale("log")
            plt.xlabel(r"Bounding parameter $\varepsilon$")
            plt.ylabel("AF mean absolute error")
            plt.title("Sensitivity of the bounded benchmark to $\\varepsilon$")
            plt.grid(True, which="both", alpha=0.3)
            plt.legend(fontsize=8, ncol=2, loc="best")
            plt.tight_layout()
            fig_path = FIG_DIR / "figA6_eps_sensitivity.pdf"
            plt.savefig(fig_path)
            plt.savefig(fig_path.with_suffix(".png"), dpi=200)
            plt.close()
            _log(f"[sensitivity_eps] wrote {fig_path}")
        except Exception as exc:  # noqa: BLE001
            _log(f"[sensitivity_eps] figure skipped ({exc})")


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

def _parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--input", type=str, default=None,
                   help="Path to unified_bounded_fast_detail.csv "
                        "(default: look in final/ then repo root)")
    p.add_argument("--eps-grid", type=float, nargs="+",
                   default=DEFAULT_EPS_GRID,
                   help=f"ε values to evaluate (default: {DEFAULT_EPS_GRID})")
    p.add_argument("--col-true", type=str, default="y_true_ratio")
    p.add_argument("--col-pred", type=str, default="y_pred_ratio")
    p.add_argument("--col-model", type=str, default="model")
    p.add_argument("--col-cat", type=str, default="category")
    p.add_argument("--keep-all", action="store_true",
                   help="Keep sugar and mutton (excluded by default)")
    p.add_argument("--skip-figure", action="store_true",
                   help="Do not produce figA6_eps_sensitivity.pdf")
    return p.parse_args(argv)


def main(argv=None) -> None:
    args = _parse_args(argv)
    input_path = _find_input(args.input)
    run(
        input_path=input_path,
        eps_grid=args.eps_grid,
        col_true=args.col_true,
        col_pred=args.col_pred,
        col_model=args.col_model,
        col_cat=args.col_cat,
        keep_all=args.keep_all,
        skip_figure=args.skip_figure,
    )


if __name__ == "__main__":
    main()
