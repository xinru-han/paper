from __future__ import annotations

import argparse
import concurrent.futures as futures
import functools
import json
import math
import multiprocessing as mp
import os
import queue
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize

import run_maidads_pipeline as pipe
import run_split_pork_pgdp_models as model


ROOT = model.ROOT
PROJECT = model.PROJECT
OUT = model.OUT
FORMAL = OUT / "FormalBootstrap"
BOOT = FORMAL / "bootstrap"
LR = FORMAL / "lr_bootstrap"
OOS = OUT / "OOS"

VARIANTS = list(model.VARIANTS.keys())
GROUPS = model.GROUP_ORDER
FOOD_GROUPS = [g for g in GROUPS if g != "nonfood"]

_WORKER: dict[str, Any] = {}


def md_table(df: pd.DataFrame, digits: int = 4, max_rows: int | None = None) -> str:
    if df.empty:
        return "_无记录。_"
    tmp = df.copy()
    if max_rows is not None and tmp.shape[0] > max_rows:
        tmp = tmp.head(max_rows)
    for col in tmp.select_dtypes(include=[np.number]).columns:
        tmp[col] = tmp[col].map(lambda x: "" if pd.isna(x) else f"{x:.{digits}g}")
    tmp = tmp.fillna("").astype(str)
    lines = [
        "| " + " | ".join(map(str, tmp.columns)) + " |",
        "| " + " | ".join(["---"] * len(tmp.columns)) + " |",
    ]
    for row in tmp.itertuples(index=False):
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def ensure_dirs() -> None:
    for path in [FORMAL, BOOT, LR, OOS]:
        path.mkdir(parents=True, exist_ok=True)


def append_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if rows:
        pd.DataFrame(rows).to_csv(path, mode="a", index=False, header=not path.exists())


def completed_draws(path: Path) -> set[int]:
    if not path.exists():
        return set()
    return set(pd.read_csv(path, usecols=["draw"])["draw"].dropna().astype(int))


def dedupe(path: Path, key_cols: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty:
        return df
    df = df.drop_duplicates(key_cols, keep="last").sort_values(key_cols).reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def raw_from_maidads_params(params: dict[str, np.ndarray | float]) -> np.ndarray:
    alpha = np.asarray(params["alpha"], float)
    delta = np.asarray(params["delta"], float)
    tau = np.asarray(params["tau"], float)
    return np.r_[
        np.log(np.maximum(alpha, 1e-12)),
        np.log(np.maximum(delta, 1e-12)),
        np.log(np.maximum(tau, 1e-12)),
        math.log(max(float(params["omega"]), 1e-12)),
        float(params["kappa"]),
    ]


def params_from_csv(path: Path, model_name: str, group_names: list[str]) -> dict[str, np.ndarray | float]:
    df = pd.read_csv(path)
    order = {g: i for i, g in enumerate(group_names)}
    tmp = df[df["model"].eq(model_name)].copy()
    tmp["ord"] = tmp["group"].map(order)
    tmp = tmp.sort_values("ord")
    return {
        "alpha": tmp["alpha"].to_numpy(float),
        "beta": tmp["beta"].to_numpy(float),
        "delta": tmp["delta"].to_numpy(float),
        "tau": tmp["tau"].to_numpy(float),
        "omega": float(tmp["omega"].iloc[0]),
        "kappa": float(tmp["kappa"].iloc[0]),
    }


def subset_arrays(arr: pipe.ModelArrays, idx: np.ndarray) -> pipe.ModelArrays:
    return pipe.ModelArrays(
        obs_ids=arr.obs_ids[idx],
        provinces=arr.provinces[idx],
        years=arr.years[idx],
        group_names=arr.group_names,
        x=arr.x[idx],
        p=arr.p[idx],
        m=arr.m[idx],
    )


def fit_bootstrap_maidads(arr_boot: pipe.ModelArrays, raw_start: np.ndarray, maxiter: int) -> tuple[dict, object, float]:
    n = arr_boot.x.shape[1]
    bounds = [(-8, 8)] * n + [(-12, 8)] * n + [(-12, 8)] * n + [(-9, 3)] + [(-20, 20)]
    res = minimize(
        pipe.neg_loglike,
        raw_start,
        args=(arr_boot, "maidads"),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": maxiter, "maxfun": maxiter * 200, "ftol": 1e-7, "maxls": 30},
    )
    return pipe.unpack_maidads(res.x, n), res, float(res.fun)


def load_panel(variant: str) -> pd.DataFrame:
    path = OUT / f"{variant}__split_panel.csv"
    if path.exists():
        return pd.read_csv(path)
    panel = model.build_split_panel(variant)
    panel.to_csv(path, index=False)
    return panel


def init_worker(variant: str) -> None:
    panel = load_panel(variant)
    arr = model.panel_to_arrays(panel)
    params = params_from_csv(OUT / f"{variant}__parameter_estimates.csv", "MAIDADS_sat", arr.group_names)
    raw_start = raw_from_maidads_params(params)
    _WORKER.clear()
    _WORKER.update(
        {
            "variant": variant,
            "panel": panel,
            "arr": arr,
            "params": params,
            "raw_start": raw_start,
            "provinces": np.unique(arr.provinces),
            "p_mean": panel[panel["year"].eq(2023)][[f"p_{g}_model" for g in arr.group_names]].mean().to_numpy(float),
            "m_mean": float(panel["m"].mean()),
            "m_median": float(panel["m"].median()),
            "m_grid": np.array([30000.0, 50000.0, float(panel["m"].mean()), 80000.0, 120000.0]),
        }
    )


def bootstrap_draw(draw: int, maxiter: int) -> dict[str, Any]:
    t0 = time.time()
    arr: pipe.ModelArrays = _WORKER["arr"]
    raw_start: np.ndarray = _WORKER["raw_start"]
    provinces: np.ndarray = _WORKER["provinces"]
    rng = np.random.default_rng(2026061300 + draw)
    sampled = rng.choice(provinces, size=provinces.size, replace=True)
    idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
    arr_boot = subset_arrays(arr, idx)
    draw_start = raw_start + rng.normal(0, 0.05, size=raw_start.size)
    status = {
        "variant": _WORKER["variant"],
        "draw": draw,
        "success": False,
        "nll": np.nan,
        "message": "",
        "elapsed_seconds": np.nan,
        "n_sampled_provinces": int(provinces.size),
        "n_unique_sampled_provinces": int(pd.Series(sampled).nunique()),
    }
    param_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    try:
        params, res, nll = fit_bootstrap_maidads(arr_boot, draw_start, maxiter=maxiter)
        status.update({"success": bool(res.success), "nll": nll, "message": str(res.message)})
        for j, group in enumerate(arr.group_names):
            param_rows.append(
                {
                    "variant": _WORKER["variant"],
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
        p_mean = _WORKER["p_mean"]
        for income in _WORKER["m_grid"]:
            mar, hic, eta, budget_shares, _ = model.price_elasticities_for_point(
                p_mean, float(income), params, arr.group_names
            )
            _, xhat, _, _ = model.elasticity_for_point(p_mean, float(income), params, arr.group_names)
            for j, group in enumerate(arr.group_names):
                metric_rows.extend(
                    [
                        {
                            "variant": _WORKER["variant"],
                            "draw": draw,
                            "metric": "gdp_elasticity",
                            "income": float(income),
                            "group": group,
                            "value": eta[j],
                        },
                        {
                            "variant": _WORKER["variant"],
                            "draw": draw,
                            "metric": "marshallian_own_price",
                            "income": float(income),
                            "group": group,
                            "value": mar[j, j],
                        },
                        {
                            "variant": _WORKER["variant"],
                            "draw": draw,
                            "metric": "hicksian_own_price",
                            "income": float(income),
                            "group": group,
                            "value": hic[j, j],
                        },
                        {
                            "variant": _WORKER["variant"],
                            "draw": draw,
                            "metric": "budget_share",
                            "income": float(income),
                            "group": group,
                            "value": budget_shares[j],
                        },
                        {
                            "variant": _WORKER["variant"],
                            "draw": draw,
                            "metric": "xhat",
                            "income": float(income),
                            "group": group,
                            "value": xhat[j],
                        },
                    ]
                )
    except Exception as exc:
        status["message"] = repr(exc)
    status["elapsed_seconds"] = time.time() - t0
    return {"status": status, "params": param_rows, "metrics": metric_rows}


def lr_draw(draw: int, maxiter_a: int, maxiter_m: int) -> dict[str, Any]:
    t0 = time.time()
    arr: pipe.ModelArrays = _WORKER["arr"]
    provinces: np.ndarray = _WORKER["provinces"]
    rng = np.random.default_rng(2026061400 + draw)
    sampled = rng.choice(provinces, size=provinces.size, replace=True)
    idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
    arr_boot = subset_arrays(arr, idx)
    row = {
        "variant": _WORKER["variant"],
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
            seed=20280000 + draw,
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


def lr_failure_row(variant: str, draw: int, message: str, elapsed_seconds: float) -> dict[str, Any]:
    return {
        "variant": variant,
        "draw": draw,
        "success": False,
        "nll_aidads": np.nan,
        "nll_maidads": np.nan,
        "lr_stat": np.nan,
        "message": message,
        "elapsed_seconds": elapsed_seconds,
        "n_sampled_provinces": 31,
        "n_unique_sampled_provinces": np.nan,
    }


def lr_draw_process_entry(
    variant: str,
    draw: int,
    maxiter_a: int,
    maxiter_m: int,
    out_queue,
) -> None:
    try:
        init_worker(variant)
        out_queue.put(lr_draw(draw, maxiter_a=maxiter_a, maxiter_m=maxiter_m))
    except Exception as exc:
        out_queue.put(lr_failure_row(variant, draw, repr(exc), np.nan))


def run_pool(
    kind: str,
    variant: str,
    draws: list[int],
    workers: int,
    task_fn,
    append_fn,
    progress_every: int,
) -> None:
    if not draws:
        print(f"{kind}/{variant}: all requested draws already completed.", flush=True)
        return
    completed = 0
    started = time.time()
    with futures.ProcessPoolExecutor(max_workers=workers, initializer=init_worker, initargs=(variant,)) as ex:
        future_map = {ex.submit(task_fn, d): d for d in draws}
        for fut in futures.as_completed(future_map):
            draw = future_map[fut]
            result = fut.result()
            append_fn(result)
            completed += 1
            if completed == 1 or completed % progress_every == 0 or completed == len(draws):
                elapsed = time.time() - started
                rate = completed / elapsed if elapsed > 0 else float("nan")
                print(
                    f"{kind}/{variant}: completed {completed}/{len(draws)} queued draws "
                    f"(latest draw {draw}, {rate:.3f} draws/sec)",
                    flush=True,
                )


def summarize_bootstrap(target_reps: int) -> pd.DataFrame:
    status = dedupe(BOOT / "bootstrap_draw_status.csv", ["variant", "draw"])
    params = dedupe(BOOT / "bootstrap_parameter_draws.csv", ["variant", "draw", "group"])
    metrics = dedupe(BOOT / "bootstrap_metric_draws.csv", ["variant", "draw", "metric", "income", "group"])
    status.to_csv(OUT / "bootstrap_draw_status.csv", index=False)
    params.to_csv(OUT / "bootstrap_parameter_draws.csv", index=False)
    metrics.to_csv(OUT / "bootstrap_metric_draws.csv", index=False)

    metric_ci_parts = []
    param_ci_parts = []
    for variant, vstatus in status.groupby("variant"):
        success_draws = set(vstatus.loc[vstatus["success"].astype(bool), "draw"].astype(int))
        vmetrics = metrics[(metrics["variant"].eq(variant)) & (metrics["draw"].isin(success_draws))]
        vparams = params[(params["variant"].eq(variant)) & (params["draw"].isin(success_draws))]
        if not vmetrics.empty:
            ci = (
                vmetrics.groupby(["variant", "metric", "income", "group"], dropna=False)["value"]
                .quantile([0.025, 0.5, 0.975])
                .unstack()
                .reset_index()
                .rename(columns={0.025: "ci_2_5", 0.5: "median", 0.975: "ci_97_5"})
            )
            ci["n_success_draws"] = len(success_draws)
            ci["target_reps"] = target_reps
            metric_ci_parts.append(ci)
        if not vparams.empty:
            for parameter in ["alpha", "beta", "delta", "tau", "omega", "kappa"]:
                pci = (
                    vparams.groupby(["variant", "group"], dropna=False)[parameter]
                    .quantile([0.025, 0.5, 0.975])
                    .unstack()
                    .reset_index()
                    .rename(columns={0.025: "ci_2_5", 0.5: "median", 0.975: "ci_97_5"})
                )
                pci.insert(1, "parameter", parameter)
                pci["n_success_draws"] = len(success_draws)
                pci["target_reps"] = target_reps
                param_ci_parts.append(pci)

    metric_ci = pd.concat(metric_ci_parts, ignore_index=True) if metric_ci_parts else pd.DataFrame()
    param_ci = pd.concat(param_ci_parts, ignore_index=True) if param_ci_parts else pd.DataFrame()
    metric_ci.to_csv(OUT / "bootstrap_metric_ci.csv", index=False)
    metric_ci.to_csv(OUT / "bootstrap_key_ci.csv", index=False)
    param_ci.to_csv(OUT / "bootstrap_parameter_ci.csv", index=False)
    return status.groupby("variant", as_index=False).agg(
        target_reps=("draw", lambda _: target_reps),
        completed_reps=("draw", "count"),
        successful_reps=("success", lambda s: int(s.astype(bool).sum())),
        convergence_rate=("success", lambda s: float(s.astype(bool).mean())),
    )


def observed_lr(variant: str) -> float:
    comp = pd.read_csv(OUT / f"{variant}__model_comparison.csv")
    row = comp[comp["model"].eq("LR_MAIDADS_vs_AIDADS")]
    return float(row["lr_stat"].iloc[0])


def summarize_lr(target_reps: int) -> pd.DataFrame:
    draws = dedupe(LR / "lr_bootstrap_draws.csv", ["variant", "draw"])
    draws.to_csv(OUT / "lr_bootstrap_draws.csv", index=False)
    rows = []
    for variant, vdraws in draws.groupby("variant"):
        observed = observed_lr(variant)
        success = vdraws.loc[vdraws["success"].astype(bool) & vdraws["lr_stat"].notna(), "lr_stat"]
        rows.append(
            {
                "variant": variant,
                "test": "MAIDADS_vs_AIDADS",
                "observed_lr": observed,
                "bootstrap_reps": target_reps,
                "completed_reps": int(vdraws.shape[0]),
                "successful_reps": int(success.shape[0]),
                "convergence_rate": float(success.shape[0] / vdraws.shape[0]) if vdraws.shape[0] else np.nan,
                "cluster_bootstrap_tail_probability": float(np.mean(success >= observed)) if not success.empty else np.nan,
                "lr_bootstrap_median": float(success.median()) if not success.empty else np.nan,
                "lr_bootstrap_q95": float(success.quantile(0.95)) if not success.empty else np.nan,
                "lr_bootstrap_q99": float(success.quantile(0.99)) if not success.empty else np.nan,
                "chi2_p_value_status": "invalid_not_reported",
                "note": "Province-block cluster bootstrap; ordinary chi-square p-value not used.",
                "inference_scale": "formal" if target_reps >= 500 else "pilot",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "lr_test_chi2_and_bootstrap.csv", index=False)
    return out


def run_bootstrap(reps: int, workers: int, maxiter: int) -> pd.DataFrame:
    status_path = BOOT / "bootstrap_draw_status.csv"
    for variant in VARIANTS:
        existing = set()
        if status_path.exists():
            s = pd.read_csv(status_path, usecols=["variant", "draw"])
            existing = set(s.loc[s["variant"].eq(variant), "draw"].astype(int))
        draws = [d for d in range(1, reps + 1) if d not in existing]

        def append(result: dict[str, Any]) -> None:
            append_csv(BOOT / "bootstrap_parameter_draws.csv", result["params"])
            append_csv(BOOT / "bootstrap_metric_draws.csv", result["metrics"])
            append_csv(status_path, [result["status"]])

        run_pool(
            "Formal bootstrap",
            variant,
            draws,
            workers,
            functools.partial(bootstrap_draw, maxiter=maxiter),
            append,
            progress_every=max(1, min(25, reps // 20)),
        )
    return summarize_bootstrap(reps)


def run_lr_timed(
    variant: str,
    draws: list[int],
    workers: int,
    maxiter_a: int,
    maxiter_m: int,
    timeout_seconds: int,
    progress_every: int,
) -> None:
    if not draws:
        print(f"LR bootstrap/{variant}: all requested draws already completed.", flush=True)
        return
    ctx = mp.get_context("spawn")
    pending = iter(draws)
    active: dict[int, dict[str, Any]] = {}
    completed = 0
    started = time.time()
    lr_path = LR / "lr_bootstrap_draws.csv"

    def start_next() -> bool:
        try:
            draw = next(pending)
        except StopIteration:
            return False
        q = ctx.Queue(maxsize=1)
        proc = ctx.Process(
            target=lr_draw_process_entry,
            args=(variant, draw, maxiter_a, maxiter_m, q),
        )
        proc.start()
        active[int(proc.pid)] = {"process": proc, "queue": q, "draw": draw, "started": time.time()}
        return True

    while len(active) < workers and start_next():
        pass

    while active:
        time.sleep(1.0)
        for pid, info in list(active.items()):
            proc = info["process"]
            q = info["queue"]
            draw = int(info["draw"])
            elapsed_one = time.time() - float(info["started"])
            row = None
            try:
                row = q.get_nowait()
            except queue.Empty:
                row = None

            if row is not None:
                proc.join(timeout=2)
            elif not proc.is_alive():
                proc.join(timeout=2)
                row = lr_failure_row(variant, draw, f"worker_exitcode_{proc.exitcode}_without_result", elapsed_one)
            elif elapsed_one > timeout_seconds:
                proc.terminate()
                proc.join(timeout=5)
                if proc.is_alive():
                    proc.kill()
                    proc.join(timeout=5)
                row = lr_failure_row(variant, draw, f"timeout_after_{timeout_seconds}_seconds", elapsed_one)

            if row is not None:
                append_csv(lr_path, [row])
                try:
                    q.close()
                except Exception:
                    pass
                del active[pid]
                completed += 1
                if completed == 1 or completed % progress_every == 0 or completed == len(draws):
                    elapsed = time.time() - started
                    rate = completed / elapsed if elapsed > 0 else float("nan")
                    print(
                        f"LR bootstrap/{variant}: completed {completed}/{len(draws)} queued draws "
                        f"(latest draw {draw}, {rate:.3f} draws/sec)",
                        flush=True,
                    )
                while len(active) < workers and start_next():
                    pass


def run_lr(reps: int, workers: int, maxiter_a: int, maxiter_m: int) -> pd.DataFrame:
    lr_path = LR / "lr_bootstrap_draws.csv"
    for variant in VARIANTS:
        existing = set()
        if lr_path.exists():
            s = pd.read_csv(lr_path, usecols=["variant", "draw"])
            existing = set(s.loc[s["variant"].eq(variant), "draw"].astype(int))
        draws = [d for d in range(1, reps + 1) if d not in existing]

        run_lr_timed(
            variant,
            draws,
            workers,
            maxiter_a,
            maxiter_m,
            timeout_seconds=int(os.environ.get("SP_PGDP_LR_DRAW_TIMEOUT", "1800")),
            progress_every=max(1, min(10, reps // 25)),
        )
    return summarize_lr(reps)


def fit_oos_split(panel: pd.DataFrame, variant: str, train_end: int, test_start: int, test_end: int, seed: int):
    arr = model.panel_to_arrays(panel)
    train_idx = np.where(arr.years <= train_end)[0]
    test_idx = np.where((arr.years >= test_start) & (arr.years <= test_end))[0]
    train = subset_arrays(arr, train_idx)
    test = subset_arrays(arr, test_idx)
    fits = pipe.fit_model(
        train,
        maidads_random_scales=(0.03, 0.08, 0.15),
        maxiter_a=900,
        maxiter_m=1500,
        progress=False,
        seed=seed,
    )
    pred_rows = []
    split_label = f"{test_start}-{test_end}" if test_start != test_end else str(test_start)
    train_label = f"2015-{train_end}"
    for fit in fits:
        xhat, u = pipe.predict_x(fit["params"], test)
        if xhat is None or u is None:
            raise RuntimeError(f"OOS prediction failed for {variant}/{fit['model']}/{train_label}->{split_label}.")
        rows = []
        for r in range(test.x.shape[0]):
            for j, group in enumerate(test.group_names):
                rows.append(
                    {
                        "variant": variant,
                        "model": fit["model"],
                        "train_years": train_label,
                        "test_years": split_label,
                        "obs_id": test.obs_ids[r],
                        "province": test.provinces[r],
                        "year": test.years[r],
                        "group": group,
                        "observed_x": test.x[r, j],
                        "predicted_x": xhat[r, j],
                        "error": test.x[r, j] - xhat[r, j],
                        "u": u[r],
                    }
                )
        one = pd.DataFrame(rows)
        safe_name = f"oos_predictions__{variant}__{fit['model']}__{train_label}_to_{split_label}.csv"
        one.to_csv(OOS / safe_name, index=False)
        pred_rows.extend(rows)
    pred = pd.DataFrame(pred_rows)
    fit = pred.groupby(["variant", "model", "train_years", "test_years", "group"], as_index=False).agg(
        rmse_x=("error", lambda s: float(np.sqrt(np.mean(np.square(s))))),
        mae_x=("error", lambda s: float(np.mean(np.abs(s)))),
        mean_x=("observed_x", "mean"),
        n_test=("observed_x", "size"),
    )
    fit["relative_rmse"] = fit["rmse_x"] / fit["mean_x"].replace(0, np.nan)
    return fit, pred


def run_oos() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    specs = [(2020, 2021, 2023, 20260615), (2022, 2023, 2023, 20260616)]
    fits = []
    preds = []
    for variant in VARIANTS:
        panel = load_panel(variant)
        for train_end, test_start, test_end, seed in specs:
            fit, pred = fit_oos_split(panel, variant, train_end, test_start, test_end, seed)
            fits.append(fit)
            preds.append(pred)
    fit_all = pd.concat(fits, ignore_index=True)
    pred_all = pd.concat(preds, ignore_index=True)
    fit_all.to_csv(OUT / "oos_fit_by_group.csv", index=False)
    pred_all.to_csv(OUT / "oos_predictions.csv", index=False)
    food = fit_all[fit_all["group"].isin(FOOD_GROUPS)]
    summary = food.groupby(["variant", "model", "train_years", "test_years"], as_index=False).agg(
        oos_food_rmse_mean=("rmse_x", "mean"),
        oos_food_relative_rmse_mean=("relative_rmse", "mean"),
        oos_food_mae_mean=("mae_x", "mean"),
    )
    summary.to_csv(OUT / "oos_summary_by_model.csv", index=False)
    return fit_all, pred_all, summary


def oos_paired_bootstrap(pred: pd.DataFrame, reps: int = 1000) -> pd.DataFrame:
    rows = []
    food = pred[pred["group"].isin(FOOD_GROUPS)].copy()
    for keys, grp in food.groupby(["variant", "train_years", "test_years"]):
        pivot = grp.pivot_table(
            index=["obs_id", "province", "year", "group"],
            columns="model",
            values="error",
            aggfunc="first",
        ).reset_index()
        if not {"AIDADS_sat", "MAIDADS_sat"}.issubset(pivot.columns):
            continue
        pivot["se_diff_a_minus_m"] = pivot["AIDADS_sat"] ** 2 - pivot["MAIDADS_sat"] ** 2
        observed = float(pivot["se_diff_a_minus_m"].mean())
        provinces = pivot["province"].unique()
        rng = np.random.default_rng(20260617)
        draws = []
        for _ in range(reps):
            sampled = rng.choice(provinces, size=provinces.size, replace=True)
            b = pd.concat([pivot[pivot["province"].eq(p)] for p in sampled], ignore_index=True)
            draws.append(float(b["se_diff_a_minus_m"].mean()))
        arr = np.asarray(draws)
        variant, train_years, test_years = keys
        rows.append(
            {
                "variant": variant,
                "train_years": train_years,
                "test_years": test_years,
                "comparison": "AIDADS_MSE_minus_MAIDADS_MSE",
                "observed_mean_diff": observed,
                "ci_2_5": float(np.quantile(arr, 0.025)),
                "median": float(np.quantile(arr, 0.5)),
                "ci_97_5": float(np.quantile(arr, 0.975)),
                "p_share_diff_le_0": float(np.mean(arr <= 0)),
                "bootstrap_reps": reps,
                "note": "Positive observed_mean_diff means MAIDADS has lower food MSE than AIDADS.",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "oos_paired_bootstrap_model_comparison.csv", index=False)
    return out


def point_table_at_mean_pgdp() -> pd.DataFrame:
    rows = []
    for variant in VARIANTS:
        panel = load_panel(variant)
        params = params_from_csv(OUT / f"{variant}__parameter_estimates.csv", "MAIDADS_sat", GROUPS)
        p_mean = panel[panel["year"].eq(2023)][[f"p_{g}_model" for g in GROUPS]].mean().to_numpy(float)
        m_mean = float(panel["m"].mean())
        mar, hic, eta, budget_shares, _ = model.price_elasticities_for_point(p_mean, m_mean, params, GROUPS)
        _, xhat, _, _ = model.elasticity_for_point(p_mean, m_mean, params, GROUPS)
        for j, group in enumerate(GROUPS):
            rows.append(
                {
                    "variant": variant,
                    "income": m_mean,
                    "group": group,
                    "group_label_cn": model.GROUP_LABEL_CN[group],
                    "gdp_elasticity": eta[j],
                    "marshallian_own_price": mar[j, j],
                    "hicksian_own_price": hic[j, j],
                    "budget_share": budget_shares[j],
                    "xhat": xhat[j],
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "elasticity_at_mean_pgdp_summary.csv", index=False)
    return out


def compile_code_md() -> Path:
    output = OUT / "SplitPorkPGDP_完整代码整合.md"
    files = [
        PROJECT / "scripts" / "run_split_pork_pgdp_models.py",
        PROJECT / "scripts" / "run_split_pork_pgdp_formal_checks.py",
        PROJECT / "scripts" / "run_maidads_pipeline.py",
    ]
    lines = [
        "# 人均 GDP + 猪肉拆分 MAIDADS 完整代码整合",
        "",
        "本文件整合最终主模型设定涉及的主要代码。",
        "",
        "运行顺序：",
        "",
        "```bash",
        "python3 ProvinceMAIDADS/scripts/run_split_pork_pgdp_models.py",
        "python3 ProvinceMAIDADS/scripts/run_split_pork_pgdp_formal_checks.py --bootstrap-reps 1000 --lr-reps 500 --workers 6",
        "```",
        "",
    ]
    for path in files:
        rel = path.relative_to(ROOT)
        lines.extend([f"## {rel}", "", "```python", path.read_text(encoding="utf-8"), "```", ""])
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def compile_results_md(
    bootstrap_summary: pd.DataFrame,
    lr_summary: pd.DataFrame,
    oos_summary: pd.DataFrame,
    oos_pair: pd.DataFrame,
    point_mean: pd.DataFrame,
) -> Path:
    output = OUT / "SplitPorkPGDP_完整结果整合.md"
    lines = [
        "# 人均 GDP + 猪肉拆分 MAIDADS 完整结果整合",
        "",
        f"- 生成时间：{pd.Timestamp.now().isoformat()}",
        "- 主模型设定：预算变量使用实际人均 GDP，`m = pgdp / monetary_deflator`。",
        "- 分类：`grain / oil / vegfruit / pork / nonpork_meatsea / dairyegg / nonfood`。",
        "- `nonpork_meatsea = beef + mutton + poultry + aquatic`。",
        "- Bootstrap：省份簇重抽样，整省 2015-2023 年作为一个 block。",
        "",
        "## 一、模型品类",
        "",
        md_table(
            pd.DataFrame(
                {
                    "group": GROUPS,
                    "label_cn": [model.GROUP_LABEL_CN[g] for g in GROUPS],
                    "items": ["+".join(model.GROUPS_SPLIT[g]) for g in GROUPS],
                }
            )
        ),
        "",
    ]
    for variant in VARIANTS:
        lines.extend([f"## 二、点估计与诊断：{variant}", ""])
        panel = load_panel(variant)
        lines.extend(
            [
                "### m 口径描述",
                "",
                md_table(
                    panel[
                        [
                            "m",
                            "m_consumption_real",
                            "pgdp_nominal",
                            "covered_food_exp_split",
                            "nonfood_exp_split",
                        ]
                    ]
                    .describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
                    .T.reset_index(),
                    digits=6,
                ),
                "",
                "### 模型比较",
                "",
                md_table(pd.read_csv(OUT / f"{variant}__model_comparison.csv")),
                "",
                "### MAIDADS 分品类拟合误差",
                "",
                md_table(
                    pd.read_csv(OUT / f"{variant}__fit_by_group.csv")
                    .query("model == 'MAIDADS_sat'")
                    .sort_values("relative_rmse", ascending=False)
                ),
                "",
                "### 理论一致性最大误差",
                "",
            ]
        )
        cons = pd.read_csv(OUT / f"{variant}__elasticity_consistency_tests.csv")
        cons_cols = [
            "adding_up_income_error",
            "max_abs_price_adding_up_error",
            "max_abs_marshallian_homogeneity_error",
            "max_abs_hicksian_homogeneity_error",
            "max_abs_slutsky_symmetry_error",
        ]
        cons_summary = cons[cons_cols].abs().max().reset_index()
        cons_summary.columns = ["check", "max_abs_error"]
        lines.extend([md_table(cons_summary, digits=6), ""])

    lines.extend(["## 三、平均人均 GDP 水平弹性", ""])
    mean_pivot = point_mean[
        [
            "variant",
            "group",
            "group_label_cn",
            "gdp_elasticity",
            "marshallian_own_price",
            "hicksian_own_price",
            "budget_share",
        ]
    ]
    lines.extend([md_table(mean_pivot), ""])

    metric_ci = pd.read_csv(OUT / "bootstrap_metric_ci.csv")
    mean_income = float(load_panel(VARIANTS[0])["m"].mean())
    mean_ci = metric_ci[np.isclose(metric_ci["income"], mean_income)]
    lines.extend(["## 四、平均人均 GDP 水平弹性 bootstrap 区间", ""])
    for metric in ["gdp_elasticity", "marshallian_own_price", "hicksian_own_price", "budget_share"]:
        lines.extend([f"### {metric}", ""])
        show = mean_ci[mean_ci["metric"].eq(metric)].copy()
        show["group_label_cn"] = show["group"].map(model.GROUP_LABEL_CN)
        lines.extend([md_table(show[["variant", "group", "group_label_cn", "median", "ci_2_5", "ci_97_5", "n_success_draws"]]), ""])

    lines.extend(["## 五、Bootstrap 收敛状态", "", md_table(bootstrap_summary), ""])
    lines.extend(["## 六、LR Cluster Bootstrap", "", md_table(lr_summary), ""])
    lines.extend(["## 七、样本外验证", "", md_table(oos_summary), ""])
    lines.extend(["## 八、OOS 配对 Bootstrap：AIDADS vs MAIDADS", "", md_table(oos_pair), ""])

    lines.extend(["## 九、参数 Bootstrap 区间", ""])
    param_ci = pd.read_csv(OUT / "bootstrap_parameter_ci.csv")
    param_ci["group_label_cn"] = param_ci["group"].map(model.GROUP_LABEL_CN)
    for parameter in ["alpha", "delta", "tau", "omega", "kappa"]:
        lines.extend([f"### {parameter}", ""])
        lines.extend(
            [
                md_table(
                    param_ci[param_ci["parameter"].eq(parameter)][
                        ["variant", "group", "group_label_cn", "median", "ci_2_5", "ci_97_5", "n_success_draws"]
                    ]
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## 十、输出文件索引",
            "",
            "- `bootstrap_draw_status.csv`：bootstrap 每个 draw 的收敛状态。",
            "- `bootstrap_metric_draws.csv` / `bootstrap_metric_ci.csv`：弹性、预算份额和预测数量的 bootstrap 明细与区间。",
            "- `bootstrap_parameter_draws.csv` / `bootstrap_parameter_ci.csv`：参数 bootstrap 明细与区间。",
            "- `lr_bootstrap_draws.csv` / `lr_test_chi2_and_bootstrap.csv`：LR cluster bootstrap 明细与摘要。",
            "- `oos_fit_by_group.csv` / `oos_summary_by_model.csv` / `oos_paired_bootstrap_model_comparison.csv`：样本外验证。",
            "- `elasticity_at_mean_pgdp_summary.csv`：平均人均 GDP 点估计弹性。",
            "",
            "## 十一、解释提醒",
            "",
            "- 本设定模仿 Gouel-Guimbard 原文的人均 GDP 预算尺度。",
            "- 在省级 household demand 解释中，`nonfood` residual 是 `人均 GDP - 已覆盖食品支出`，不是严格居民非食品消费。",
            "- LR 普通 chi-square p 值不使用；表中仅报告 province-block cluster bootstrap tail probability。",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-reps", type=int, default=int(os.environ.get("SP_PGDP_BOOTSTRAP_REPS", "1000")))
    parser.add_argument("--lr-reps", type=int, default=int(os.environ.get("SP_PGDP_LR_REPS", "500")))
    parser.add_argument("--workers", type=int, default=int(os.environ.get("SP_PGDP_WORKERS", "6")))
    parser.add_argument("--bootstrap-maxiter", type=int, default=int(os.environ.get("SP_PGDP_BOOTSTRAP_MAXITER", "900")))
    parser.add_argument("--lr-maxiter-a", type=int, default=int(os.environ.get("SP_PGDP_LR_MAXITER_A", "650")))
    parser.add_argument("--lr-maxiter-m", type=int, default=int(os.environ.get("SP_PGDP_LR_MAXITER_M", "900")))
    parser.add_argument("--oos-paired-reps", type=int, default=1000)
    parser.add_argument("--skip-bootstrap", action="store_true")
    parser.add_argument("--skip-lr", action="store_true")
    parser.add_argument("--skip-oos", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    manifest = {
        "started_at": pd.Timestamp.now().isoformat(),
        "bootstrap_reps": args.bootstrap_reps,
        "lr_reps": args.lr_reps,
        "workers": args.workers,
        "bootstrap_maxiter": args.bootstrap_maxiter,
        "lr_maxiter_a": args.lr_maxiter_a,
        "lr_maxiter_m": args.lr_maxiter_m,
        "variants": VARIANTS,
        "groups": model.GROUPS_SPLIT,
        "budget_variable": "real_pgdp_per_capita",
        "budget_formula": "pgdp / monetary_deflator",
    }
    (FORMAL / "formal_checks_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.skip_bootstrap:
        bootstrap_summary = summarize_bootstrap(args.bootstrap_reps)
    else:
        bootstrap_summary = run_bootstrap(args.bootstrap_reps, args.workers, args.bootstrap_maxiter)
    if args.skip_lr:
        lr_summary = summarize_lr(args.lr_reps)
    else:
        lr_summary = run_lr(args.lr_reps, args.workers, args.lr_maxiter_a, args.lr_maxiter_m)
    if args.skip_oos:
        oos_summary = pd.read_csv(OUT / "oos_summary_by_model.csv")
        pred = pd.read_csv(OUT / "oos_predictions.csv")
    else:
        _, pred, oos_summary = run_oos()
    oos_pair = oos_paired_bootstrap(pred, reps=args.oos_paired_reps)
    point_mean = point_table_at_mean_pgdp()
    results_md = compile_results_md(bootstrap_summary, lr_summary, oos_summary, oos_pair, point_mean)
    code_md = compile_code_md()
    summary = {
        "finished_at": pd.Timestamp.now().isoformat(),
        "results_md": str(results_md),
        "code_md": str(code_md),
        "bootstrap": bootstrap_summary.to_dict(orient="records"),
        "lr": lr_summary.to_dict(orient="records"),
    }
    (FORMAL / "formal_checks_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
