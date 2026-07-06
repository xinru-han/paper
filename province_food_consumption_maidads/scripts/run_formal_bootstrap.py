from __future__ import annotations

import argparse
import concurrent.futures as futures
from functools import partial
import json
import math
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import run_additional_checks as checks
import run_maidads_pipeline as pipe


ROOT = pipe.ROOT
OUT = pipe.OUT
DATA_OUT = pipe.DATA_OUT
FORMAL = OUT / "FormalBootstrap"
BOOT = FORMAL / "bootstrap"
LR = FORMAL / "lr_bootstrap"

_WORKER: dict[str, Any] = {}


def _ensure_dirs() -> None:
    FORMAL.mkdir(parents=True, exist_ok=True)
    BOOT.mkdir(parents=True, exist_ok=True)
    LR.mkdir(parents=True, exist_ok=True)


def _append_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    pd.DataFrame(rows).to_csv(path, mode="a", index=False, header=not path.exists())


def _completed_draws(path: Path) -> set[int]:
    if not path.exists():
        return set()
    df = pd.read_csv(path, usecols=["draw"])
    return set(df["draw"].dropna().astype(int))


def _init_worker() -> None:
    panel = pd.read_csv(DATA_OUT / "maidads6_panel.csv")
    nutrition = pipe.read_nutrition()
    arr = pipe.panel_to_arrays(panel)
    full_params = checks.params_from_csv(OUT / "parameter_estimates.csv", "MAIDADS_sat", arr.group_names)
    raw_start = checks.raw_from_maidads_params(full_params)
    _WORKER.update(
        {
            "panel": panel,
            "nutrition": nutrition,
            "arr": arr,
            "raw_start": raw_start,
            "provinces": np.unique(arr.provinces),
            "p_mean": panel[panel["year"] == 2023][[f"p_{g}_model" for g in arr.group_names]].mean().to_numpy(float),
            "m_median": float(np.median(arr.m)),
        }
    )


def _bootstrap_draw(draw: int, maxiter: int) -> dict[str, Any]:
    t0 = time.time()
    arr: pipe.ModelArrays = _WORKER["arr"]
    panel: pd.DataFrame = _WORKER["panel"]
    nutrition: pd.DataFrame = _WORKER["nutrition"]
    raw_start: np.ndarray = _WORKER["raw_start"]
    provinces: np.ndarray = _WORKER["provinces"]
    rng = np.random.default_rng(2026060900 + draw)

    sampled = rng.choice(provinces, size=provinces.size, replace=True)
    idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
    arr_boot = checks.subset_arrays(arr, idx)
    draw_start = raw_start + rng.normal(0, 0.05, size=raw_start.size)
    status = {
        "draw": draw,
        "success": False,
        "nll": np.nan,
        "message": "",
        "elapsed_seconds": np.nan,
        "n_sampled_provinces": int(provinces.size),
        "n_unique_sampled_provinces": int(pd.Series(sampled).nunique()),
    }
    metric_rows: list[dict[str, Any]] = []
    param_rows: list[dict[str, Any]] = []
    try:
        params, res, nll = checks.fit_bootstrap_maidads(arr_boot, draw_start, maxiter=maxiter)
        eta, _, _, _ = pipe.elasticity_for_point(_WORKER["p_mean"], _WORKER["m_median"], params)
        projection = pipe.build_projection(panel, params, nutrition)
        status.update({"success": bool(res.success), "nll": nll, "message": str(res.message)})
        for j, group in enumerate(arr.group_names):
            param_rows.append(
                {
                    "draw": draw,
                    "group": group,
                    "alpha": params["alpha"][j],
                    "beta": params["beta"][j],
                    "delta": params["delta"][j],
                    "tau": params["tau"][j],
                    "omega": params["omega"],
                    "kappa": params["kappa"],
                }
            )
            metric_rows.append(
                {
                    "draw": draw,
                    "metric": "income_elasticity_median_income",
                    "group_or_item": group,
                    "year": np.nan,
                    "value": eta[j],
                }
            )
        proj = projection["projection_group"]
        for _, row in proj[proj["year"].isin([2030, 2050]) & proj["group"].ne("nonfood")].iterrows():
            metric_rows.append(
                {
                    "draw": draw,
                    "metric": "daily_kcal_per_cap_weighted",
                    "group_or_item": row["group"],
                    "year": int(row["year"]),
                    "value": row["daily_kcal_per_cap_weighted"],
                }
            )
        feed = projection["projection_items"].copy()
        feed["feed_grain_million_ton"] = feed["feed_grain_kg"] / 1e9
        for _, row in feed[feed["year"].isin([2030, 2050]) & (feed["feed_grain_million_ton"] > 0)].iterrows():
            metric_rows.append(
                {
                    "draw": draw,
                    "metric": "feed_grain_million_ton",
                    "group_or_item": row["item"],
                    "year": int(row["year"]),
                    "value": row["feed_grain_million_ton"],
                }
            )
    except Exception as exc:
        status["message"] = repr(exc)
    status["elapsed_seconds"] = time.time() - t0
    return {"status": status, "metrics": metric_rows, "params": param_rows}


def _lr_draw(draw: int, maxiter_a: int, maxiter_m: int) -> dict[str, Any]:
    t0 = time.time()
    arr: pipe.ModelArrays = _WORKER["arr"]
    provinces: np.ndarray = _WORKER["provinces"]
    rng = np.random.default_rng(2026061200 + draw)
    sampled = rng.choice(provinces, size=provinces.size, replace=True)
    idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
    arr_boot = checks.subset_arrays(arr, idx)
    row = {
        "draw": draw,
        "success": False,
        "nll_aidads": np.nan,
        "nll_maidads": np.nan,
        "lr_stat": np.nan,
        "message": "",
        "elapsed_seconds": np.nan,
        "n_sampled_provinces": int(provinces.size),
        "n_unique_sampled_provinces": int(pd.Series(sampled).nunique()),
    }
    try:
        fits = pipe.fit_model(
            arr_boot,
            maidads_random_scales=(0.03,),
            maxiter_a=maxiter_a,
            maxiter_m=maxiter_m,
            progress=False,
            seed=20270000 + draw,
            wide_multistart=False,
        )
        nll_a = float(fits[0]["nll"])
        nll_m = float(fits[1]["nll"])
        row.update(
            {
                "success": bool(fits[0]["result"].success) and bool(fits[1]["result"].success),
                "nll_aidads": nll_a,
                "nll_maidads": nll_m,
                "lr_stat": 2 * (nll_a - nll_m),
                "message": "ok",
            }
        )
    except Exception as exc:
        row["message"] = repr(exc)
    row["elapsed_seconds"] = time.time() - t0
    return row


def _dedupe(path: Path, key_cols: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty:
        return df
    df = df.drop_duplicates(key_cols, keep="last").sort_values(key_cols).reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def _summarize_bootstrap(target_reps: int) -> dict[str, Any]:
    draws = _dedupe(BOOT / "formal_bootstrap_draw_status.csv", ["draw"])
    metrics = _dedupe(BOOT / "formal_bootstrap_draw_metrics.csv", ["draw", "metric", "group_or_item", "year"])
    params = _dedupe(BOOT / "formal_bootstrap_parameter_draws.csv", ["draw", "group"])

    success_draws = set(draws.loc[draws["success"].astype(bool), "draw"].astype(int)) if not draws.empty else set()
    metrics_ci_source = metrics[metrics["draw"].isin(success_draws)].copy() if success_draws else metrics.iloc[0:0].copy()
    params_ci_source = params[params["draw"].isin(success_draws)].copy() if success_draws else params.iloc[0:0].copy()

    if metrics_ci_source.empty:
        ci = pd.DataFrame()
    else:
        ci = (
            metrics_ci_source.groupby(["metric", "group_or_item", "year"], dropna=False)["value"]
            .quantile([0.025, 0.5, 0.975])
            .unstack()
            .reset_index()
            .rename(columns={0.025: "ci_2_5", 0.5: "median", 0.975: "ci_97_5"})
        )
        ci["n_success_draws"] = len(success_draws)
        ci["target_reps"] = target_reps

    param_ci = []
    if not params_ci_source.empty:
        for name in ["alpha", "beta", "delta", "tau", "omega", "kappa"]:
            tmp = (
                params_ci_source.groupby("group")[name]
                .quantile([0.025, 0.5, 0.975])
                .unstack()
                .reset_index()
                .rename(columns={0.025: "ci_2_5", 0.5: "median", 0.975: "ci_97_5"})
            )
            tmp.insert(0, "parameter", name)
            tmp["n_success_draws"] = len(success_draws)
            tmp["target_reps"] = target_reps
            param_ci.append(tmp)
    param_ci_df = pd.concat(param_ci, ignore_index=True) if param_ci else pd.DataFrame()

    draws.to_csv(OUT / "bootstrap_draw_status.csv", index=False)
    metrics.to_csv(OUT / "bootstrap_draw_metrics.csv", index=False)
    params.to_csv(OUT / "bootstrap_parameter_draws.csv", index=False)
    ci.to_csv(OUT / "bootstrap_key_ci.csv", index=False)
    ci.to_csv(OUT / "bootstrap_key_ci_success_only.csv", index=False)
    param_ci_df.to_csv(OUT / "bootstrap_parameter_ci.csv", index=False)
    ci.to_csv(BOOT / "bootstrap_key_ci.csv", index=False)
    param_ci_df.to_csv(BOOT / "bootstrap_parameter_ci.csv", index=False)
    return {
        "target_reps": target_reps,
        "completed_reps": int(draws.shape[0]),
        "successful_reps": int(len(success_draws)),
        "convergence_rate": float(len(success_draws) / draws.shape[0]) if draws.shape[0] else np.nan,
    }


def _observed_lr() -> float:
    comparison = pd.read_csv(OUT / "model_comparison.csv")
    row = comparison[comparison["model"].eq("LR_MAIDADS_vs_AIDADS")]
    if not row.empty and "lr_stat" in row:
        return float(row["lr_stat"].iloc[0])
    params = pd.read_csv(OUT / "parameter_estimates.csv")
    nll_a = float(params.loc[params["model"].eq("AIDADS_sat"), "nll"].iloc[0])
    nll_m = float(params.loc[params["model"].eq("MAIDADS_sat"), "nll"].iloc[0])
    return 2 * (nll_a - nll_m)


def _summarize_lr(target_reps: int) -> dict[str, Any]:
    observed_lr = _observed_lr()
    draws = _dedupe(LR / "formal_lr_bootstrap_draws.csv", ["draw"])
    success_lr = draws.loc[draws["success"].astype(bool) & draws["lr_stat"].notna(), "lr_stat"] if not draws.empty else pd.Series(dtype=float)
    if success_lr.empty:
        summary = pd.DataFrame(
            [
                {
                    "test": "MAIDADS_vs_AIDADS",
                    "observed_lr": observed_lr,
                    "bootstrap_reps": target_reps,
                    "completed_reps": int(draws.shape[0]),
                    "successful_reps": 0,
                    "convergence_rate": 0.0,
                    "cluster_bootstrap_tail_probability": np.nan,
                    "chi2_p_value_status": "invalid_not_reported",
                    "note": "No successful LR bootstrap draws.",
                    "inference_scale": "formal" if target_reps >= 500 else "pilot",
                }
            ]
        )
    else:
        summary = pd.DataFrame(
            [
                {
                    "test": "MAIDADS_vs_AIDADS",
                    "observed_lr": observed_lr,
                    "bootstrap_reps": target_reps,
                    "completed_reps": int(draws.shape[0]),
                    "successful_reps": int(success_lr.shape[0]),
                    "convergence_rate": float(success_lr.shape[0] / draws.shape[0]),
                    "cluster_bootstrap_tail_probability": float(np.mean(success_lr >= observed_lr)),
                    "lr_bootstrap_median": float(success_lr.median()),
                    "lr_bootstrap_q95": float(success_lr.quantile(0.95)),
                    "lr_bootstrap_q99": float(success_lr.quantile(0.99)),
                    "chi2_p_value_status": "invalid_not_reported",
                    "note": "Cluster bootstrap with province-block resampling; chi-square p-value not used.",
                    "inference_scale": "formal" if target_reps >= 500 else "pilot",
                }
            ]
        )
    draws.to_csv(OUT / "lr_bootstrap_draws.csv", index=False)
    summary.to_csv(OUT / "lr_test_chi2_and_bootstrap.csv", index=False)
    draws.to_csv(LR / "lr_bootstrap_draws.csv", index=False)
    summary.to_csv(LR / "lr_test_chi2_and_bootstrap.csv", index=False)
    _update_model_comparison(summary)
    return summary.iloc[0].to_dict()


def _update_model_comparison(lr_summary: pd.DataFrame) -> None:
    path = OUT / "model_comparison.csv"
    if not path.exists() or lr_summary.empty:
        return
    comparison = pd.read_csv(path)
    mask = comparison["model"].eq("LR_MAIDADS_vs_AIDADS")
    if not mask.any():
        return
    row = lr_summary.iloc[0]
    comparison.loc[mask, "cluster_bootstrap_tail_probability"] = row.get("cluster_bootstrap_tail_probability", np.nan)
    comparison.loc[mask, "lr_bootstrap_successful_reps"] = row.get("successful_reps", np.nan)
    comparison.loc[mask, "lr_bootstrap_completed_reps"] = row.get("completed_reps", np.nan)
    comparison.loc[mask, "lr_bootstrap_reps"] = row.get("bootstrap_reps", np.nan)
    comparison.loc[mask, "lr_bootstrap_inference_scale"] = row.get("inference_scale", "")
    comparison.to_csv(path, index=False)


def _run_pool(kind: str, draws: list[int], workers: int, task_fn, append_fn, progress_every: int) -> None:
    if not draws:
        print(f"{kind}: all requested draws already completed.", flush=True)
        return
    completed = 0
    started = time.time()

    def _report(draw: int) -> None:
        if completed == 1 or completed % progress_every == 0 or completed == len(draws):
            elapsed = time.time() - started
            rate = completed / elapsed if elapsed > 0 else float("nan")
            print(
                f"{kind}: completed {completed}/{len(draws)} queued draws "
                f"(latest draw {draw}, {rate:.3f} draws/sec)",
                flush=True,
            )

    use_serial = workers is not None and workers <= 1
    if not use_serial:
        # Prefer a fork-context multiprocessing.Pool: the macOS/sandbox default
        # "spawn" start method trips a semaphore syscall that is not permitted
        # here, but "fork" works and lets children inherit the parent's memory.
        try:
            import multiprocessing as _mp
            ctx = _mp.get_context("fork")
            draw_order = list(draws)
            with ctx.Pool(processes=workers, initializer=_init_worker) as pool:
                for draw, result in zip(
                    draw_order, pool.imap(task_fn, draw_order, chunksize=1)
                ):
                    append_fn(result)
                    completed += 1
                    _report(draw)
            return
        except (PermissionError, OSError, NotImplementedError, ValueError) as exc:
            print(
                f"{kind}: process pool unavailable ({exc}); falling back to serial execution.",
                flush=True,
            )
            completed = 0
            started = time.time()

    # Serial fallback: initialise worker state once in-process, run draws sequentially.
    _init_worker()
    for draw in draws:
        result = task_fn(draw)
        append_fn(result)
        completed += 1
        _report(draw)


def _run_bootstrap(reps: int, workers: int, maxiter: int) -> dict[str, Any]:
    status_path = BOOT / "formal_bootstrap_draw_status.csv"
    existing = _completed_draws(status_path)
    draws = [d for d in range(1, reps + 1) if d not in existing]

    def append(result: dict[str, Any]) -> None:
        _append_csv(BOOT / "formal_bootstrap_parameter_draws.csv", result["params"])
        _append_csv(BOOT / "formal_bootstrap_draw_metrics.csv", result["metrics"])
        _append_csv(status_path, [result["status"]])

    _run_pool(
        "Formal parameter bootstrap",
        draws,
        workers,
        partial(_bootstrap_draw, maxiter=maxiter),
        append,
        progress_every=max(1, min(25, reps // 20)),
    )
    return _summarize_bootstrap(reps)


def _run_lr(reps: int, workers: int, maxiter_a: int, maxiter_m: int) -> dict[str, Any]:
    status_path = LR / "formal_lr_bootstrap_draws.csv"
    existing = _completed_draws(status_path)
    draws = [d for d in range(1, reps + 1) if d not in existing]

    def append(row: dict[str, Any]) -> None:
        _append_csv(status_path, [row])

    _run_pool(
        "Formal LR bootstrap",
        draws,
        workers,
        partial(_lr_draw, maxiter_a=maxiter_a, maxiter_m=maxiter_m),
        append,
        progress_every=max(1, min(10, reps // 25)),
    )
    return _summarize_lr(reps)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-reps", type=int, default=int(os.environ.get("MAIDADS_BOOTSTRAP_REPS", "1000")))
    parser.add_argument("--lr-reps", type=int, default=int(os.environ.get("MAIDADS_LR_BOOTSTRAP_REPS", "500")))
    parser.add_argument("--workers", type=int, default=int(os.environ.get("MAIDADS_BOOTSTRAP_WORKERS", "6")))
    parser.add_argument("--bootstrap-maxiter", type=int, default=int(os.environ.get("MAIDADS_BOOTSTRAP_MAXITER", "650")))
    parser.add_argument("--lr-maxiter-a", type=int, default=int(os.environ.get("MAIDADS_LR_MAXITER_A", "320")))
    parser.add_argument("--lr-maxiter-m", type=int, default=int(os.environ.get("MAIDADS_LR_MAXITER_M", "460")))
    parser.add_argument("--skip-bootstrap", action="store_true")
    parser.add_argument("--skip-lr", action="store_true")
    args = parser.parse_args()

    _ensure_dirs()
    manifest = {
        "bootstrap_target_reps": args.bootstrap_reps,
        "lr_target_reps": args.lr_reps,
        "workers": args.workers,
        "bootstrap_maxiter": args.bootstrap_maxiter,
        "lr_maxiter_a": args.lr_maxiter_a,
        "lr_maxiter_m": args.lr_maxiter_m,
        "started_at": pd.Timestamp.now().isoformat(),
    }
    (FORMAL / "formal_bootstrap_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    out: dict[str, Any] = {}
    if not args.skip_bootstrap:
        out["bootstrap"] = _run_bootstrap(args.bootstrap_reps, args.workers, args.bootstrap_maxiter)
    else:
        out["bootstrap"] = _summarize_bootstrap(args.bootstrap_reps)
    if not args.skip_lr:
        out["lr"] = _run_lr(args.lr_reps, args.workers, args.lr_maxiter_a, args.lr_maxiter_m)
    else:
        out["lr"] = _summarize_lr(args.lr_reps)

    out["finished_at"] = pd.Timestamp.now().isoformat()
    (FORMAL / "formal_bootstrap_summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
