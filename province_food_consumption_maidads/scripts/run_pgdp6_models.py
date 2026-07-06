from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import run_maidads_pipeline as pipe


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ProvinceMAIDADS"
DATA_OUT = PROJECT / "Data" / "output"
RESULTS = PROJECT / "Results"
OUT = RESULTS / "PGDP6"

GROUP_ORDER = list(pipe.GROUPS.keys())
GROUP_LABEL_CN = {
    "grain": "粮食/主粮",
    "oil": "食用油",
    "vegfruit": "蔬菜水果",
    "pork": "猪肉",
    "meatother": "非猪肉肉类及水产品",
    "meatsea": "肉类及水产品",
    "dairyegg": "奶蛋类",
    "nonfood": "其他/未覆盖支出",
}

VARIANTS = {
    "baseline_real_national_nonfood": {
        "base_panel": DATA_OUT / "maidads6_panel.csv",
        "nonfood_price_column": "p_nonfood_model",
        "description": "2023 real prices, provincial food CPI deflator, national non-food CPI residual price.",
    },
    "robust_real_derived_cpi_nonfood": {
        "base_panel": DATA_OUT / "maidads6_panel_cpi_nonfood.csv",
        "nonfood_price_column": "p_nonfood_model",
        "description": "2023 real prices, provincial food CPI deflator, derived provincial non-food CPI residual price.",
    },
}


def md_table(df: pd.DataFrame, digits: int = 4) -> str:
    if df.empty:
        return "_无记录。_"
    tmp = df.copy()
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


def build_pgdp_panel(variant: str) -> pd.DataFrame:
    spec = VARIANTS[variant]
    base = pd.read_csv(spec["base_panel"])
    raw = pd.read_stata(ROOT / "ProvinceData" / "workdata" / "data.dta")
    raw = raw[["province", "year", "pgdp"]].copy()
    data = base.merge(raw, on=["province", "year"], how="left")
    data["m_consumption_real"] = data["m"]
    data["pgdp_nominal"] = pd.to_numeric(data["pgdp"], errors="coerce")
    data["m"] = data["pgdp_nominal"] / data["monetary_deflator"]
    data["nonfood_exp"] = data["m"] - data["covered_food_exp"]
    data["x_nonfood"] = data["nonfood_exp"] / data[spec["nonfood_price_column"]]
    data["p_nonfood_model"] = data[spec["nonfood_price_column"]]

    keep_cols = [
        "obs_id",
        "province",
        "provincechn",
        "year",
        "population_10k",
        "m",
        "m_consumption_real",
        "pgdp_nominal",
        "monetary_deflator",
        "covered_food_exp",
        "nonfood_exp",
        "covered_daily_kcal",
        "covered_food_budget_share",
    ]
    for group in GROUP_ORDER:
        keep_cols += [f"x_{group}", f"p_{group}_model"]
    panel = data[keep_cols].copy()

    model_cols = [f"x_{g}" for g in GROUP_ORDER] + [f"p_{g}_model" for g in GROUP_ORDER] + ["m"]
    if panel[model_cols].isna().any().any():
        raise RuntimeError(f"{variant}: missing model x, p, or pgdp-budget values.")
    if (panel[model_cols] <= 0).any().any():
        raise RuntimeError(f"{variant}: non-positive model x, p, or pgdp-budget values.")
    if (panel["nonfood_exp"] <= 0).any():
        raise RuntimeError(f"{variant}: non-positive nonfood residual under pgdp budget.")

    diagnostics = []
    budget_error = panel["m"] - panel["covered_food_exp"] - panel["nonfood_exp"]
    for group in GROUP_ORDER:
        diagnostics.append(
            {
                "variant": variant,
                "group": group,
                "group_label_cn": GROUP_LABEL_CN[group],
                "items": "+".join(pipe.GROUPS[group]),
                "n_missing_x": int(panel[f"x_{group}"].isna().sum()),
                "n_nonpositive_x": int((panel[f"x_{group}"] <= 0).sum()),
                "n_missing_p": int(panel[f"p_{group}_model"].isna().sum()),
                "n_nonpositive_p": int((panel[f"p_{group}_model"] <= 0).sum()),
                "x_min": float(panel[f"x_{group}"].min()),
                "x_median": float(panel[f"x_{group}"].median()),
                "x_max": float(panel[f"x_{group}"].max()),
                "p_min": float(panel[f"p_{group}_model"].min()),
                "p_median": float(panel[f"p_{group}_model"].median()),
                "p_max": float(panel[f"p_{group}_model"].max()),
                "budget_max_abs_residual": float(budget_error.abs().max()),
            }
        )
    pd.DataFrame(diagnostics).to_csv(OUT / f"{variant}__data_diagnostics.csv", index=False)
    return panel


def fit_rows(variant: str, fits: tuple[dict, dict], arr: pipe.ModelArrays) -> tuple[pd.DataFrame, pd.DataFrame]:
    param_rows = []
    fit_rows_out = []
    for fit in fits:
        params = fit["params"]
        xhat, _ = pipe.predict_x(params, arr)
        if xhat is None:
            raise RuntimeError(f"{variant}/{fit['model']}: in-sample prediction failed.")
        eps = arr.x - xhat
        rmse = np.sqrt((eps**2).mean(axis=0))
        mae = np.abs(eps).mean(axis=0)
        for j, group in enumerate(arr.group_names):
            param_rows.append(
                {
                    "variant": variant,
                    "model": fit["model"],
                    "group": group,
                    "group_label_cn": GROUP_LABEL_CN[group],
                    "items": "+".join(pipe.GROUPS[group]),
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
            fit_rows_out.append(
                {
                    "variant": variant,
                    "model": fit["model"],
                    "group": group,
                    "group_label_cn": GROUP_LABEL_CN[group],
                    "items": "+".join(pipe.GROUPS[group]),
                    "rmse_x": rmse[j],
                    "mae_x": mae[j],
                    "mean_x": arr.x[:, j].mean(),
                    "relative_rmse": rmse[j] / arr.x[:, j].mean(),
                }
            )
    return pd.DataFrame(param_rows), pd.DataFrame(fit_rows_out)


def model_comparison(variant: str, fits: tuple[dict, dict], fit_by_group: pd.DataFrame, n_obs: int) -> pd.DataFrame:
    k = {"AIDADS_sat": 2 * len(GROUP_ORDER) + 1, "MAIDADS_sat": 3 * len(GROUP_ORDER) + 2}
    rows = []
    for fit in fits:
        rows.append(
            {
                "variant": variant,
                "model": fit["model"],
                "nll": fit["nll"],
                "k_effective": k[fit["model"]],
                "aic": 2 * fit["nll"] + 2 * k[fit["model"]],
                "bic": 2 * fit["nll"] + math.log(n_obs) * k[fit["model"]],
                "success": bool(fit["result"].success),
                "message": str(fit["result"].message),
                "mean_food_relative_rmse": float(
                    fit_by_group[
                        fit_by_group["model"].eq(fit["model"]) & fit_by_group["group"].ne("nonfood")
                    ]["relative_rmse"].mean()
                ),
            }
        )
    rows.append(
        {
            "variant": variant,
            "model": "LR_MAIDADS_vs_AIDADS",
            "nll": np.nan,
            "k_effective": k["MAIDADS_sat"] - k["AIDADS_sat"],
            "aic": np.nan,
            "bic": np.nan,
            "success": bool(fits[0]["result"].success) and bool(fits[1]["result"].success),
            "message": "Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS.",
            "mean_food_relative_rmse": np.nan,
            "lr_stat": 2 * (fits[0]["nll"] - fits[1]["nll"]),
            "chi2_p_value_status": "invalid_not_reported_unidentified_nuisance_under_H0",
        }
    )
    return pd.DataFrame(rows)


def elasticity_outputs(
    variant: str, panel: pd.DataFrame, params: dict[str, np.ndarray | float]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    p_mean = panel[panel["year"].eq(2023)][[f"p_{g}_model" for g in GROUP_ORDER]].mean().to_numpy(float)
    incomes = np.array(
        sorted(
            set(
                list(np.quantile(panel["m"], [0.05, 0.25, 0.5, 0.75, 0.95]))
                + [30000, 50000, 80000, 120000, 160000, 200000]
            )
        )
    )
    rows = []
    price_m = []
    price_h = []
    consistency = []
    m_min = float(panel["m"].min())
    m_max = float(panel["m"].max())
    for income in incomes:
        try:
            mar, hic, eta, budget_shares, u = pipe.price_elasticities_for_point(p_mean, float(income), params)
            _, xhat, _, phi = pipe.elasticity_for_point(p_mean, float(income), params)
        except Exception as exc:
            rows.append(
                {
                    "variant": variant,
                    "income": income,
                    "group": "ALL",
                    "error": repr(exc),
                    "support_flag": pipe.support_flag(float(income), m_min, m_max),
                }
            )
            continue
        for i, group in enumerate(GROUP_ORDER):
            rows.append(
                {
                    "variant": variant,
                    "income": income,
                    "group": group,
                    "group_label_cn": GROUP_LABEL_CN[group],
                    "items": "+".join(pipe.GROUPS[group]),
                    "quantity_2000kcal_elasticity": eta[i],
                    "expenditure_elasticity": eta[i],
                    "budget_share_elasticity": eta[i] - 1,
                    "xhat": xhat[i],
                    "budget_share": budget_shares[i],
                    "phi": phi[i],
                    "u": u,
                    "support_flag": pipe.support_flag(float(income), m_min, m_max),
                }
            )
            for j, pgroup in enumerate(GROUP_ORDER):
                base = {
                    "variant": variant,
                    "income": income,
                    "demand_group": group,
                    "demand_group_label_cn": GROUP_LABEL_CN[group],
                    "price_group": pgroup,
                    "price_group_label_cn": GROUP_LABEL_CN[pgroup],
                    "is_own_price": group == pgroup,
                    "budget_share_demand_group": budget_shares[i],
                    "budget_share_price_group": budget_shares[j],
                    "support_flag": pipe.support_flag(float(income), m_min, m_max),
                }
                price_m.append({**base, "elasticity": mar[i, j]})
                price_h.append({**base, "elasticity": hic[i, j]})
        consistency.append(
            {
                "variant": variant,
                **pipe.elasticity_consistency_row(
                    "pgdp6_income_grid",
                    float(income),
                    GROUP_ORDER,
                    mar,
                    hic,
                    eta,
                    budget_shares,
                ),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(price_m), pd.DataFrame(price_h), pd.DataFrame(consistency)


def anomaly_lines(
    comparison: pd.DataFrame,
    fit_by_group: pd.DataFrame,
    params: pd.DataFrame,
    income_elasticity: pd.DataFrame,
    price_m: pd.DataFrame,
    consistency: pd.DataFrame,
    diagnostics: pd.DataFrame,
) -> list[str]:
    issues = []
    if not comparison[comparison["model"].isin(["AIDADS_sat", "MAIDADS_sat"])]["success"].all():
        issues.append("至少一个模型 optimizer 未报告 success。")
    bad_starts = diagnostics[
        diagnostics["model"].eq("MAIDADS_sat")
        & ((~diagnostics["success"].astype(bool)) | (diagnostics["nll"] >= 1e11))
    ]
    if not bad_starts.empty:
        issues.append(
            "部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解："
            + ", ".join(
                f"{r.start_id}(success={bool(r.success)}, nll={r.nll:.3g})"
                for r in bad_starts.itertuples()
            )
            + "。"
        )
    selected = diagnostics[diagnostics["selected"].astype(bool)]
    if not selected.empty and selected["grad_norm"].max() > 1.0:
        issues.append(f"选中解梯度范数偏大：max grad_norm={selected['grad_norm'].max():.4g}。")
    boundary = params[
        params["model"].eq("MAIDADS_sat")
        & params["group"].ne("nonfood")
        & ((params["alpha"] < 1e-4) | (params["delta"] < 1e-4) | (params["tau"] < 1e-4))
    ]
    if not boundary.empty:
        issues.append(
            "MAIDADS 存在贴近下边界的 alpha/delta/tau 参数："
            + ", ".join(sorted(boundary["group"].unique()))
            + "。"
        )
    high_fit = fit_by_group[
        fit_by_group["model"].eq("MAIDADS_sat")
        & fit_by_group["group"].ne("nonfood")
        & (fit_by_group["relative_rmse"] > 0.5)
    ]
    if not high_fit.empty:
        issues.append(
            "MAIDADS 部分食品相对 RMSE > 0.5："
            + ", ".join(f"{r.group}={r.relative_rmse:.2f}" for r in high_fit.itertuples())
            + "。"
        )
    own = price_m[price_m["is_own_price"].astype(bool) & price_m["elasticity"].notna()]
    positive_own = own[(own["demand_group"].ne("nonfood")) & (own["elasticity"] > 0)]
    if not positive_own.empty:
        issues.append(
            "出现正的 Marshallian 自价格弹性："
            + ", ".join(sorted(positive_own["demand_group"].unique()))
            + "。"
        )
    cons_cols = [
        "adding_up_income_error",
        "max_abs_price_adding_up_error",
        "max_abs_marshallian_homogeneity_error",
        "max_abs_hicksian_homogeneity_error",
        "max_abs_slutsky_symmetry_error",
    ]
    max_cons = float(consistency[cons_cols].abs().max().max()) if not consistency.empty else np.nan
    if np.isfinite(max_cons) and max_cons > 1e-5:
        issues.append(f"弹性理论一致性误差偏大：max={max_cons:.3g}。")
    return issues or ["未发现明显数值异常。"]


def run_variant(variant: str, maxiter_a: int, maxiter_m: int, seed: int) -> dict:
    print(f"Building PGDP 6-group panel for {variant}...", flush=True)
    panel = build_pgdp_panel(variant)
    panel.to_csv(OUT / f"{variant}__pgdp6_panel.csv", index=False)
    arr = pipe.panel_to_arrays(panel)
    print(f"Fitting PGDP 6-group AIDADS/MAIDADS for {variant}...", flush=True)
    fits = pipe.fit_model(
        arr,
        maidads_random_scales=(0.03, 0.08, 0.15),
        maxiter_a=maxiter_a,
        maxiter_m=maxiter_m,
        progress=True,
        seed=seed,
    )
    params, fit_by_group = fit_rows(variant, fits, arr)
    comparison = model_comparison(variant, fits, fit_by_group, arr.x.shape[0])
    diagnostics = pd.DataFrame(fits[0]["diagnostics"])
    boundary = pd.DataFrame(pipe.parameter_boundary_rows(fits, arr.group_names))
    income_elasticity, price_m, price_h, consistency = elasticity_outputs(variant, panel, fits[1]["params"])

    prefix = OUT / f"{variant}__"
    params.to_csv(str(prefix) + "parameter_estimates.csv", index=False)
    fit_by_group.to_csv(str(prefix) + "fit_by_group.csv", index=False)
    comparison.to_csv(str(prefix) + "model_comparison.csv", index=False)
    diagnostics.to_csv(str(prefix) + "multistart_diagnostics.csv", index=False)
    boundary.to_csv(str(prefix) + "parameter_boundary_report.csv", index=False)
    income_elasticity.to_csv(str(prefix) + "elasticity_income_grid.csv", index=False)
    price_m.to_csv(str(prefix) + "elasticity_price_marshallian_grid.csv", index=False)
    price_h.to_csv(str(prefix) + "elasticity_price_hicksian_grid.csv", index=False)
    consistency.to_csv(str(prefix) + "elasticity_consistency_tests.csv", index=False)
    return {
        "variant": variant,
        "panel": panel,
        "params": params,
        "fit_by_group": fit_by_group,
        "comparison": comparison,
        "diagnostics": diagnostics,
        "boundary": boundary,
        "income_elasticity": income_elasticity,
        "price_m": price_m,
        "price_h": price_h,
        "consistency": consistency,
    }


def write_summary(outputs: list[dict], started_at: str) -> None:
    lines = [
        "# 原始 6 类 MAIDADS/AIDADS：人均 GDP 预算口径敏感性结果",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 开始时间：{started_at}",
        "- 本轮不做 bootstrap。",
        "- 分类：`grain / oil / vegfruit / meatsea / dairyegg / nonfood`，与最早 6 类主模型一致。",
        "- 本轮把模型预算变量 `m` 从实际人均消费支出改为实际人均 GDP：`m = pgdp / monetary_deflator`。",
        "- 注意：此设定模仿 Gouel-Guimbard 原文的人均 GDP 预算尺度；但省级 household demand 解释应谨慎，因为 `nonfood` residual 变成 `人均 GDP - covered food expenditure`。",
        "",
        "## 模型品类",
        "",
        md_table(
            pd.DataFrame(
                {
                    "group": GROUP_ORDER,
                    "label_cn": [GROUP_LABEL_CN[g] for g in GROUP_ORDER],
                    "items": ["+".join(pipe.GROUPS[g]) for g in GROUP_ORDER],
                }
            )
        ),
        "",
    ]
    cons_cols = [
        "adding_up_income_error",
        "max_abs_price_adding_up_error",
        "max_abs_marshallian_homogeneity_error",
        "max_abs_hicksian_homogeneity_error",
        "max_abs_slutsky_symmetry_error",
    ]
    for out in outputs:
        variant = out["variant"]
        panel = out["panel"]
        lines.extend(
            [
                f"## {variant}",
                "",
                "### m 口径描述",
                "",
                md_table(
                    panel[
                        ["m", "m_consumption_real", "pgdp_nominal", "covered_food_exp", "nonfood_exp"]
                    ].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T.reset_index(),
                    digits=6,
                ),
                "",
                "### 模型比较",
                "",
                md_table(out["comparison"]),
                "",
                "### 分品类拟合误差",
                "",
                md_table(out["fit_by_group"].sort_values(["model", "relative_rmse"], ascending=[True, False])),
                "",
                "### 异常检查",
                "",
            ]
        )
        for issue in anomaly_lines(
            out["comparison"],
            out["fit_by_group"],
            out["params"],
            out["income_elasticity"],
            out["price_m"],
            out["consistency"],
            out["diagnostics"],
        ):
            lines.append(f"- {issue}")
        lines.extend(["", "### 弹性一致性最大误差", ""])
        cons_summary = out["consistency"][cons_cols].abs().max().reset_index()
        cons_summary.columns = ["check", "max_abs_error"]
        lines.extend([md_table(cons_summary, digits=6), ""])

        for target in [30000, 50000, 80000]:
            el = out["income_elasticity"][
                out["income_elasticity"]["income"].eq(target) & out["income_elasticity"]["group"].ne("ALL")
            ][["group", "group_label_cn", "quantity_2000kcal_elasticity", "budget_share", "support_flag"]]
            if not el.empty:
                own = out["price_m"][
                    out["price_m"]["income"].eq(target) & out["price_m"]["is_own_price"].astype(bool)
                ][["demand_group", "demand_group_label_cn", "elasticity", "support_flag"]]
                lines.extend([f"### 收入弹性：income={target}", "", md_table(el), ""])
                lines.extend([f"### Marshallian 自价格弹性：income={target}", "", md_table(own), ""])
    lines.extend(
        [
            "## 输出文件",
            "",
            "- `*__pgdp6_panel.csv`：人均 GDP 预算口径估计面板。",
            "- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。",
            "- `*__fit_by_group.csv`：分品类拟合误差。",
            "- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。",
            "- `*__elasticity_income_grid.csv`：人均 GDP 网格下的收入/GDP 弹性。",
            "- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。",
            "- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。",
        ]
    )
    (OUT / "PGDP6_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", nargs="+", default=list(VARIANTS.keys()), choices=list(VARIANTS.keys()))
    parser.add_argument("--maxiter-a", type=int, default=700)
    parser.add_argument("--maxiter-m", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260613)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    started = datetime.now().isoformat(timespec="seconds")
    outputs = []
    for i, variant in enumerate(args.variants):
        outputs.append(run_variant(variant, args.maxiter_a, args.maxiter_m, args.seed + 100 * i))
    write_summary(outputs, started)
    manifest = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "started": started,
        "variants": args.variants,
        "groups": pipe.GROUPS,
        "budget_variable": "real_pgdp_per_capita",
        "budget_formula": "pgdp / monetary_deflator",
        "bootstrap": False,
        "maxiter_a": args.maxiter_a,
        "maxiter_m": args.maxiter_m,
    }
    (OUT / "pgdp6_run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT / "PGDP6_RESULTS.md")


if __name__ == "__main__":
    main()
