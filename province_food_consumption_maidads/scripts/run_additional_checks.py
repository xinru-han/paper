from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

import run_maidads_pipeline as pipe


ROOT = pipe.ROOT
OUT = pipe.OUT
DATA_OUT = pipe.DATA_OUT
OOS_OUT = OUT / "OOS"


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


def params_from_csv(path: Path, model: str, group_names: list[str]) -> dict[str, np.ndarray | float]:
    df = pd.read_csv(path)
    order = {g: i for i, g in enumerate(group_names)}
    tmp = df[df["model"].eq(model)].copy()
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


def fit_rows(variant: str, fits: tuple[dict, dict], arr: pipe.ModelArrays) -> tuple[pd.DataFrame, pd.DataFrame]:
    param_rows = []
    fit_rows = []
    for fit in fits:
        params = fit["params"]
        xhat, _ = pipe.predict_x(params, arr)
        if xhat is None:
            continue
        eps = arr.x - xhat
        rmse = np.sqrt((eps**2).mean(axis=0))
        mae = np.abs(eps).mean(axis=0)
        for j, group in enumerate(arr.group_names):
            param_rows.append(
                {
                    "variant": variant,
                    "model": fit["model"],
                    "group": group,
                    "alpha": params["alpha"][j],
                    "beta": params["beta"][j],
                    "delta": params["delta"][j],
                    "tau": params["tau"][j],
                    "omega": params["omega"],
                    "kappa": params["kappa"],
                    "nll": fit["nll"],
                    "success": bool(fit["result"].success),
                    "message": str(fit["result"].message),
                }
            )
            fit_rows.append(
                {
                    "variant": variant,
                    "model": fit["model"],
                    "group": group,
                    "rmse_x": rmse[j],
                    "mae_x": mae[j],
                    "mean_x": arr.x[:, j].mean(),
                }
            )
    return pd.DataFrame(param_rows), pd.DataFrame(fit_rows)


def subset_arrays(arr: pipe.ModelArrays, mask: np.ndarray) -> pipe.ModelArrays:
    return pipe.ModelArrays(
        obs_ids=arr.obs_ids[mask],
        provinces=arr.provinces[mask],
        years=arr.years[mask],
        group_names=arr.group_names,
        x=arr.x[mask],
        p=arr.p[mask],
        m=arr.m[mask],
    )


def oos_split(
    panel: pd.DataFrame,
    variant: str,
    train_year_max: int,
    test_year_min: int,
    test_year_max: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, tuple[dict, dict]]:
    arr = pipe.panel_to_arrays(panel)
    train = subset_arrays(arr, arr.years <= train_year_max)
    test = subset_arrays(arr, (arr.years >= test_year_min) & (arr.years <= test_year_max))
    fits = pipe.fit_model(
        train,
        maidads_random_scales=(0.05,),
        maxiter_a=320,
        maxiter_m=460,
        progress=True,
        seed=seed,
    )
    rows = []
    split_label = f"{test_year_min}-{test_year_max}" if test_year_min != test_year_max else str(test_year_min)
    train_label = f"2015-{train_year_max}"
    for fit in fits:
        xhat, u = pipe.predict_x(fit["params"], test)
        if xhat is None:
            raise ValueError(
                f"OOS prediction failed for {variant}/{fit['model']}, train <= {train_year_max}, "
                f"test {test_year_min}-{test_year_max}."
            )
        model_rows = []
        for r in range(test.x.shape[0]):
            for j, group in enumerate(test.group_names):
                model_rows.append(
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
        pred_one = pd.DataFrame(model_rows)
        rows.extend(model_rows)
        safe_name = f"oos_predictions__{variant}__{fit['model']}__{train_label}_to_{split_label}.csv"
        pred_one.to_csv(OOS_OUT / safe_name.replace("/", "-"), index=False)
    pred = pd.DataFrame(rows)
    fit = pred.groupby(["variant", "model", "train_years", "test_years", "group"], as_index=False).agg(
        rmse_x=("error", lambda s: float(np.sqrt(np.mean(np.square(s))))),
        mae_x=("error", lambda s: float(np.mean(np.abs(s)))),
        mean_x=("observed_x", "mean"),
        n_test=("observed_x", "size"),
    )
    fit["relative_rmse"] = fit["rmse_x"] / fit["mean_x"].replace(0, np.nan)
    return fit, pred, fits


def oos_validations(panels: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    OOS_OUT.mkdir(parents=True, exist_ok=True)
    specs = [
        (2020, 2021, 2023, 20260608),
        (2022, 2023, 2023, 20260611),
        (2023, 2024, 2024, 20260624),  # 2024 holdout: fit 2015-2023, predict newest year
    ]
    fit_parts = []
    pred_parts = []
    for variant, panel in panels.items():
        for train_end, test_start, test_end, seed in specs:
            fit, pred, _ = oos_split(panel, variant, train_end, test_start, test_end, seed)
            fit_parts.append(fit)
            pred_parts.append(pred)
    all_fit = pd.concat(fit_parts, ignore_index=True)
    all_pred = pd.concat(pred_parts, ignore_index=True)
    duplicated = all_fit[["variant", "model", "train_years", "test_years", "group"]].duplicated().sum()
    if duplicated:
        raise RuntimeError(f"OOS fit has duplicated variant/model/split/group rows: {duplicated}")
    wide = (
        all_fit[all_fit["group"].ne("nonfood")]
        .groupby(["variant", "model", "train_years", "test_years"])["rmse_x"]
        .mean()
        .reset_index()
    )
    if wide.shape[0] > 1 and wide["rmse_x"].round(10).nunique() == 1:
        raise RuntimeError("OOS RMSE is identical across all models/variants/splits; check grouping or overwritten predictions.")
    return all_fit, all_pred


def fit_bootstrap_maidads(
    arr_boot: pipe.ModelArrays,
    raw_start: np.ndarray,
    maxiter: int = 260,
) -> tuple[dict[str, np.ndarray | float], object, float]:
    n = arr_boot.x.shape[1]
    bounds = [(-8, 8)] * n + [(-12, 8)] * n + [(-12, 8)] * n + [(-9, 3)] + [(-20, 20)]
    res = minimize(
        pipe.neg_loglike,
        raw_start,
        args=(arr_boot, "maidads"),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": maxiter, "ftol": 1e-7, "maxls": 25},
    )
    return pipe.unpack_maidads(res.x, n), res, float(res.fun)


def bootstrap_checks(panel: pd.DataFrame, nutrition: pd.DataFrame, b: int = 25) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    arr = pipe.panel_to_arrays(panel)
    full_params = params_from_csv(OUT / "parameter_estimates.csv", "MAIDADS_sat", arr.group_names)
    raw_start = raw_from_maidads_params(full_params)
    rng = np.random.default_rng(20260609)
    provinces = np.unique(arr.provinces)
    p_mean = panel[panel["year"] == 2023][[f"p_{g}_model" for g in arr.group_names]].mean().to_numpy(float)
    m_median = float(np.median(arr.m))

    metric_rows = []
    param_rows = []
    draw_rows = []
    for draw in range(1, b + 1):
        sampled = rng.choice(provinces, size=provinces.size, replace=True)
        idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
        arr_boot = subset_arrays(arr, idx)
        try:
            draw_start = raw_start + rng.normal(0, 0.05, size=raw_start.size)
            params, res, nll = fit_bootstrap_maidads(arr_boot, draw_start)
            eta, _, _, _ = pipe.elasticity_for_point(p_mean, m_median, params)
            projection = pipe.build_projection(panel, params, nutrition)
        except Exception as exc:
            draw_rows.append({"draw": draw, "success": False, "nll": np.nan, "message": str(exc)})
            continue
        draw_rows.append({"draw": draw, "success": bool(res.success), "nll": nll, "message": str(res.message)})
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
        if draw == 1 or draw % 5 == 0:
            print(f"Bootstrap draw {draw}/{b}: nll={nll:.3f}, success={res.success}", flush=True)

    metrics = pd.DataFrame(metric_rows)
    params = pd.DataFrame(param_rows)
    draws = pd.DataFrame(draw_rows)
    success_draws = set(draws.loc[draws["success"].astype(bool), "draw"]) if not draws.empty else set()
    metrics_ci = metrics[metrics["draw"].isin(success_draws)].copy() if success_draws else metrics.iloc[0:0].copy()
    params_ci_source = params[params["draw"].isin(success_draws)].copy() if success_draws else params.iloc[0:0].copy()
    if metrics_ci.empty:
        ci = pd.DataFrame()
    else:
        ci = (
            metrics_ci.groupby(["metric", "group_or_item", "year"], dropna=False)["value"]
            .quantile([0.025, 0.5, 0.975])
            .unstack()
            .reset_index()
            .rename(columns={0.025: "ci_2_5", 0.5: "median", 0.975: "ci_97_5"})
        )
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
            param_ci.append(tmp)
    param_ci_df = pd.concat(param_ci, ignore_index=True) if param_ci else pd.DataFrame()
    draws.to_csv(OUT / "bootstrap_draw_status.csv", index=False)
    metrics.to_csv(OUT / "bootstrap_draw_metrics.csv", index=False)
    params.to_csv(OUT / "bootstrap_parameter_draws.csv", index=False)
    return ci, param_ci_df, draws


def lr_bootstrap(panel: pd.DataFrame, observed_lr: float, b: int = 20) -> tuple[pd.DataFrame, pd.DataFrame]:
    arr = pipe.panel_to_arrays(panel)
    rng = np.random.default_rng(20260612)
    provinces = np.unique(arr.provinces)
    rows = []
    for draw in range(1, b + 1):
        sampled = rng.choice(provinces, size=provinces.size, replace=True)
        idx = np.concatenate([np.where(arr.provinces == p)[0] for p in sampled])
        arr_boot = subset_arrays(arr, idx)
        try:
            fits = pipe.fit_model(
                arr_boot,
                maidads_random_scales=(0.03,),
                maxiter_a=220,
                maxiter_m=320,
                progress=False,
                seed=20270000 + draw,
            )
            nll_a = float(fits[0]["nll"])
            nll_m = float(fits[1]["nll"])
            lr = 2 * (nll_a - nll_m)
            success = bool(fits[0]["result"].success) and bool(fits[1]["result"].success)
            message = "ok"
        except Exception as exc:
            nll_a = np.nan
            nll_m = np.nan
            lr = np.nan
            success = False
            message = str(exc)
        rows.append(
            {
                "draw": draw,
                "success": success,
                "nll_aidads": nll_a,
                "nll_maidads": nll_m,
                "lr_stat": lr,
                "message": message,
            }
        )
        if draw == 1 or draw % 5 == 0:
            print(f"LR bootstrap draw {draw}/{b}: lr={lr:.3f}, success={success}", flush=True)
    draws = pd.DataFrame(rows)
    success_lr = draws.loc[draws["success"].astype(bool) & draws["lr_stat"].notna(), "lr_stat"]
    if success_lr.empty:
        summary = pd.DataFrame(
            [
                {
                    "test": "MAIDADS_vs_AIDADS",
                    "observed_lr": observed_lr,
                    "bootstrap_reps": b,
                    "successful_reps": 0,
                    "cluster_bootstrap_tail_probability": np.nan,
                    "chi2_p_value_status": "invalid_not_reported",
                    "note": "No successful LR bootstrap draws.",
                }
            ]
        )
    else:
        scale = "formal" if b >= 500 else "pilot"
        summary = pd.DataFrame(
            [
                {
                    "test": "MAIDADS_vs_AIDADS",
                    "observed_lr": observed_lr,
                    "bootstrap_reps": b,
                    "successful_reps": int(success_lr.shape[0]),
                    "cluster_bootstrap_tail_probability": float(np.mean(success_lr >= observed_lr)),
                    "lr_bootstrap_median": float(success_lr.median()),
                    "lr_bootstrap_q95": float(success_lr.quantile(0.95)),
                    "chi2_p_value_status": "invalid_not_reported",
                    "note": f"Cluster bootstrap {scale}; chi-square reference not used.",
                }
            ]
        )
    draws.to_csv(OUT / "lr_bootstrap_draws.csv", index=False)
    summary.to_csv(OUT / "lr_test_chi2_and_bootstrap.csv", index=False)
    return summary, draws


def model_comparison(
    main_manifest: dict,
    robustness_manifest: dict,
    oos_fit: pd.DataFrame,
    lr_summary: pd.DataFrame,
) -> pd.DataFrame:
    n = main_manifest["n_obs"]
    n_goods = main_manifest["n_goods"]
    k_a = 2 * n_goods
    k_m = 3 * n_goods + 1
    rows = []
    for m in main_manifest["models"]:
        k = k_a if m["model"].startswith("AIDADS") else k_m
        rows.append(
            {
                "variant": "baseline_real_national_nonfood",
                "model": m["model"],
                "nll": m["nll"],
                "k_effective": k,
                "aic": 2 * k + 2 * m["nll"],
                "bic": k * math.log(n) + 2 * m["nll"],
                "success": m["success"],
            }
        )
    for m in robustness_manifest["models"]:
        k = k_a if m["model"].startswith("AIDADS") else k_m
        rows.append(
            {
                "variant": "robust_real_derived_cpi_nonfood",
                "model": m["model"],
                "nll": m["nll"],
                "k_effective": k,
                "aic": 2 * k + 2 * m["nll"],
                "bic": k * math.log(n) + 2 * m["nll"],
                "success": m["success"],
            }
        )
    lr = 2 * (main_manifest["models"][0]["nll"] - main_manifest["models"][1]["nll"])
    lr_boot_p = np.nan
    lr_boot_success = np.nan
    if not lr_summary.empty:
        lr_boot_p = lr_summary["cluster_bootstrap_tail_probability"].iloc[0]
        lr_boot_success = lr_summary["successful_reps"].iloc[0]
    rows.append(
        {
            "variant": "baseline_real_national_nonfood",
            "model": "LR_MAIDADS_vs_AIDADS",
            "nll": np.nan,
            "k_effective": k_m - k_a,
            "aic": np.nan,
            "bic": np.nan,
            "success": True,
            "lr_stat": lr,
            "p_value_chi2": np.nan,
            "chi2_p_value_status": "invalid_not_reported_unidentified_nuisance_under_H0",
            "cluster_bootstrap_tail_probability": lr_boot_p,
            "lr_bootstrap_successful_reps": lr_boot_success,
        }
    )
    out = pd.DataFrame(rows)
    oos_mean = (
        oos_fit[oos_fit["group"].ne("nonfood")]
        .groupby(["variant", "model"], as_index=False)["rmse_x"]
        .mean()
        .rename(columns={"rmse_x": "oos_food_rmse_mean"})
    )
    out = out.merge(oos_mean, on=["variant", "model"], how="left")
    return out


def write_additional_summary(
    robustness_manifest: dict,
    oos_fit: pd.DataFrame,
    boot_ci: pd.DataFrame,
    comparison: pd.DataFrame,
    lr_summary: pd.DataFrame,
) -> None:
    lines = []
    lines.append("# 追加处理与稳健性估计结果")
    lines.append("")
    lines.append("## 一、已补充内容")
    lines.append("")
    lines.append("- 主结果采用全国非食品 CPI；稳健性用食物支出份额近似反推出省级非食品 CPI。")
    lines.append("- 构造 `cpi_nonfood` 省级近似非食品价格口径并重新估计 AIDADS/MAIDADS。")
    lines.append("- 对每个 `variant × model` 分别用 2015-2020 年训练、2021-2023 年测试，以及 2015-2022 年训练、2023 年测试做样本外验证。")
    status_path = OUT / "bootstrap_draw_status.csv"
    if status_path.exists():
        status = pd.read_csv(status_path)
        success_count = int(status["success"].astype(bool).sum())
        total_count = int(status.shape[0])
        lines.append(f"- 做 {total_count} 次省份簇 bootstrap，其中 {success_count} 次完全收敛；关键区间仅用完全收敛 draw 汇总。")
    else:
        lines.append("- 做省份簇 bootstrap，给关键弹性、预测和饲料粮需求提供初步区间。")
    lines.append("")
    lines.append("## 二、CPI 非食品稳健性估计")
    for m in robustness_manifest["models"]:
        lines.append(f"- {m['model']}: nll={m['nll']:.3f}, success={m['success']}, message={m['message']}")
    lines.append("")
    lines.append("## 三、样本外验证")
    lines.append(pipe.markdown_table(oos_fit))
    lines.append("")
    lines.append("## 四、模型比较")
    lines.append(pipe.markdown_table(comparison))
    lines.append("")
    lr_reps = int(lr_summary["bootstrap_reps"].iloc[0]) if "bootstrap_reps" in lr_summary else 0
    lr_title = "LR bootstrap（正式规模）" if lr_reps >= 500 else "LR bootstrap（pilot）"
    lines.append(f"## 五、{lr_title}")
    lines.append("")
    lines.append("普通 χ² p 值因 MAIDADS 在 AIDADS 原假设下存在不可识别 nuisance parameter，本轮不作为有效推断报告。")
    lines.append(pipe.markdown_table(lr_summary))
    lines.append("")
    lines.append("## 六、bootstrap 关键区间")
    key = boot_ci[
        (boot_ci["metric"].isin(["daily_kcal_per_cap_weighted", "feed_grain_million_ton"]))
        & (boot_ci["year"].isin([2050]))
    ].copy()
    lines.append(pipe.markdown_table(key))
    lines.append("")
    lines.append("## 七、输出文件")
    lines.append("")
    lines.append("- `province_cpi_indices.csv`：省级总/食品/近似非食品 CPI 与 2023=100 指数。")
    lines.append("- `robustness_cpi_nonfood_parameter_estimates.csv`：CPI 非食品价格口径参数。")
    lines.append("- `robustness_cpi_nonfood_fit_by_group.csv`：CPI 非食品价格口径拟合误差。")
    lines.append("- `robustness_cpi_nonfood_projection_group_2030_2035_2050.csv`：CPI 稳健预测。")
    lines.append("- `oos_fit_by_group.csv`、`oos_predictions.csv` 与 `Results/OOS/oos_predictions__*.csv`：按口径、模型、样本切分独立保存的样本外验证。")
    lines.append("- `bootstrap_key_ci.csv`、`bootstrap_parameter_ci.csv`、`bootstrap_draw_metrics.csv`：bootstrap 区间和抽样明细。")
    lines.append("- `lr_test_chi2_and_bootstrap.csv`、`lr_bootstrap_draws.csv`：LR 检验的 cluster bootstrap 摘要和抽样明细。")
    lines.append("")
    lines.append("## 八、仍需人工确认")
    lines.append("")
    lines.append("- 食品 CPI 三个文件是分段表，本脚本按年份拼接；请后续核对 2015 年以前文件是否确为同一食品分类口径。")
    lines.append("- 省级非食品 CPI 由总 CPI、食品 CPI、食物支出份额反推，是近似值；更理想的是直接拿到省级非食品 CPI。")
    status_path = OUT / "bootstrap_draw_status.csv"
    boot_reps = pd.read_csv(status_path).shape[0] if status_path.exists() else 0
    if boot_reps >= 500 and lr_reps >= 500:
        lines.append("- 正式规模 bootstrap 与 LR bootstrap 已完成；若模型选择推断成为论文核心，可追加 parametric-null LR bootstrap 稳健性。")
    else:
        lines.append("- 当前 bootstrap 或 LR bootstrap 仍低于正式规模；正式论文版请把对应 reps 提高到 500-1000。")
    (OUT / "ADDITIONAL_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    pipe.ensure_dirs()
    OOS_OUT.mkdir(parents=True, exist_ok=True)
    panel, _, nutrition = pipe.build_model_data()
    main_manifest = json.loads((OUT / "run_manifest.json").read_text(encoding="utf-8"))

    print("Running CPI nonfood robustness...", flush=True)
    panel_cpi, _, _ = pipe.build_model_data(nonfood_price_mode="cpi_nonfood", output_suffix="_cpi_nonfood")
    arr_cpi = pipe.panel_to_arrays(panel_cpi)
    fits_cpi = pipe.fit_model(
        arr_cpi,
        maidads_random_scales=(0.05,),
        maxiter_a=340,
        maxiter_m=500,
        progress=True,
        seed=20260610,
    )
    params_cpi, fit_cpi = fit_rows("robust_real_derived_cpi_nonfood", fits_cpi, arr_cpi)
    diag_cpi = pd.DataFrame(fits_cpi[1].get("diagnostics", []))
    if not diag_cpi.empty:
        diag_cpi.to_csv(OUT / "robustness_cpi_nonfood_multistart_diagnostics.csv", index=False)
    params_cpi.to_csv(OUT / "robustness_cpi_nonfood_parameter_estimates.csv", index=False)
    fit_cpi.to_csv(OUT / "robustness_cpi_nonfood_fit_by_group.csv", index=False)
    proj_cpi = pipe.build_projection(panel_cpi, fits_cpi[1]["params"], nutrition)
    proj_cpi["projection_group"].to_csv(OUT / "robustness_cpi_nonfood_projection_group_2030_2035_2050.csv", index=False)
    proj_cpi["projection_items"].to_csv(OUT / "robustness_cpi_nonfood_projection_item_feed_2030_2035_2050.csv", index=False)
    proj_cpi["projection_growth_path"].to_csv(OUT / "robustness_cpi_nonfood_projection_growth_path.csv", index=False)
    robustness_manifest = {
        "models": [
            {
                "model": fit["model"],
                "nll": fit["nll"],
                "success": bool(fit["result"].success),
                "message": str(fit["result"].message),
            }
            for fit in fits_cpi
        ],
        "n_obs": int(arr_cpi.x.shape[0]),
        "n_goods": int(arr_cpi.x.shape[1]),
        "groups": arr_cpi.group_names,
    }
    (OUT / "robustness_cpi_nonfood_manifest.json").write_text(
        json.dumps(robustness_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Running OOS validations...", flush=True)
    oos_fit, oos_pred = oos_validations(
        {
            "baseline_real_national_nonfood": panel,
            "robust_real_derived_cpi_nonfood": panel_cpi,
        }
    )
    oos_fit.to_csv(OUT / "oos_fit_by_group.csv", index=False)
    oos_pred.to_csv(OUT / "oos_predictions.csv", index=False)
    oos_2023_fit = oos_fit[oos_fit["test_years"].eq("2023")].copy()
    oos_2023_pred = oos_pred[oos_pred["test_years"].eq("2023")].copy()
    oos_2023_fit.to_csv(OUT / "oos_2023_fit_by_group.csv", index=False)
    oos_2023_pred.to_csv(OUT / "oos_2023_predictions.csv", index=False)

    print("Running cluster bootstrap...", flush=True)
    boot_reps = int(os.environ.get("MAIDADS_BOOTSTRAP_REPS", "30"))
    boot_ci, param_ci, draws = bootstrap_checks(panel, nutrition, b=boot_reps)
    boot_ci.to_csv(OUT / "bootstrap_key_ci.csv", index=False)
    boot_ci.to_csv(OUT / "bootstrap_key_ci_success_only.csv", index=False)
    param_ci.to_csv(OUT / "bootstrap_parameter_ci.csv", index=False)

    print("Running LR bootstrap...", flush=True)
    observed_lr = 2 * (main_manifest["models"][0]["nll"] - main_manifest["models"][1]["nll"])
    lr_reps = int(os.environ.get("MAIDADS_LR_BOOTSTRAP_REPS", "12"))
    lr_summary, _ = lr_bootstrap(panel, observed_lr, b=lr_reps)

    comparison = model_comparison(main_manifest, robustness_manifest, oos_fit, lr_summary)
    comparison.to_csv(OUT / "model_comparison.csv", index=False)
    write_additional_summary(robustness_manifest, oos_fit, boot_ci, comparison, lr_summary)
    print(json.dumps({"robustness": robustness_manifest, "bootstrap_success": int(draws["success"].sum())}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
