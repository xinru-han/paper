# 人均 GDP + 猪肉拆分 MAIDADS 完整代码整合

本文件整合最终主模型设定涉及的主要代码。

运行顺序：

```bash
python3 ProvinceMAIDADS/scripts/run_split_pork_pgdp_models.py
python3 ProvinceMAIDADS/scripts/run_split_pork_pgdp_formal_checks.py --bootstrap-reps 1000 --lr-reps 500 --workers 6
```

## ProvinceMAIDADS/scripts/run_split_pork_pgdp_models.py

```python
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
OUT = RESULTS / "SplitPorkPGDP"

GROUPS_SPLIT = {
    "grain": ["grain"],
    "oil": ["oil"],
    "vegfruit": ["vegetable", "fruit"],
    "pork": ["pork"],
    "nonpork_meatsea": ["beef", "mutton", "poultry", "aquatic"],
    "dairyegg": ["milk", "egg"],
    "nonfood": [],
}

GROUP_ORDER = list(GROUPS_SPLIT.keys())

GROUP_LABEL_CN = {
    "grain": "粮食/主粮",
    "oil": "食用油",
    "vegfruit": "蔬菜水果",
    "pork": "猪肉",
    "nonpork_meatsea": "非猪肉肉类及水产品(牛羊禽水产)",
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


def nutrition_lookup() -> dict[str, float]:
    nutrition = pipe.read_nutrition()
    grain_weights, grain_kcal = pipe.read_grain_weights(nutrition)
    lookup = dict(zip(nutrition["code"], nutrition["kcal_per_kg_as_purchased"]))
    lookup["GRAIN"] = grain_kcal
    lookup["OIL"] = float(
        nutrition.loc[nutrition["code"].isin(["SOYO", "RAPO", "GRDO"]), "kcal_per_kg_as_purchased"].mean()
    )
    grain_weights.to_csv(OUT / "split_grain_weights_used.csv", index=False)
    nutrition.to_csv(OUT / "split_nutrition_used.csv", index=False)
    return lookup


def build_split_panel(variant: str) -> pd.DataFrame:
    spec = VARIANTS[variant]
    base = pd.read_csv(spec["base_panel"])
    raw = pd.read_stata(ROOT / "ProvinceData" / "workdata" / "data.dta")
    raw_cols = ["province", "year", "pgdp"] + sorted(
        {v for item in pipe.FOOD_ITEMS.values() for v in [item["q"], item["p"]]}
    )
    data = base[
        [
            "obs_id",
            "province",
            "provincechn",
            "year",
            "population_10k",
            "m",
            "monetary_deflator",
            "food_price_index_2023",
            spec["nonfood_price_column"],
        ]
    ].merge(raw[raw_cols], on=["province", "year"], how="left")
    data = data.rename(columns={"m": "m_consumption_real"})
    data["pgdp_nominal"] = pd.to_numeric(data["pgdp"], errors="coerce")
    data["m"] = data["pgdp_nominal"] / data["monetary_deflator"]
    data["food_price_deflator"] = data["food_price_index_2023"] / 100.0
    kcal = nutrition_lookup()

    for item, item_spec in pipe.FOOD_ITEMS.items():
        q = pd.to_numeric(data[item_spec["q"]], errors="coerce")
        p = pd.to_numeric(data[item_spec["p"]], errors="coerce") / data["food_price_deflator"]
        kcal_kg = kcal[item_spec["code"]]
        data[f"{item}_x"] = q * kcal_kg / 365.0 / 2000.0
        data[f"{item}_exp"] = p * q
        data[f"{item}_kg_per_cap_year"] = q
        data[f"{item}_kcal_per_kg"] = kcal_kg

    food_exp_cols = []
    food_x_cols = []
    for group, items in GROUPS_SPLIT.items():
        if group == "nonfood":
            continue
        data[f"x_{group}"] = data[[f"{item}_x" for item in items]].sum(axis=1)
        data[f"e_{group}"] = data[[f"{item}_exp" for item in items]].sum(axis=1)
        data[f"p_{group}_model"] = data[f"e_{group}"] / data[f"x_{group}"]
        food_exp_cols.append(f"e_{group}")
        food_x_cols.append(f"x_{group}")

    data["covered_food_exp_split"] = data[food_exp_cols].sum(axis=1)
    data["nonfood_exp_split"] = data["m"] - data["covered_food_exp_split"]
    data["x_nonfood"] = data["nonfood_exp_split"] / data[spec["nonfood_price_column"]]
    data["p_nonfood_model"] = data[spec["nonfood_price_column"]]
    data["covered_daily_kcal_split"] = data[food_x_cols].sum(axis=1) * 2000

    cols = [
        "obs_id",
        "province",
        "provincechn",
        "year",
        "population_10k",
        "m",
        "m_consumption_real",
        "pgdp_nominal",
        "monetary_deflator",
        "food_price_index_2023",
        "covered_food_exp_split",
        "nonfood_exp_split",
        "covered_daily_kcal_split",
    ]
    for group in GROUP_ORDER:
        cols += [f"x_{group}", f"p_{group}_model"]
    panel = data[cols].copy()

    diagnostics = []
    for group in GROUP_ORDER:
        diagnostics.append(
            {
                "variant": variant,
                "group": group,
                "group_label_cn": GROUP_LABEL_CN[group],
                "items": "+".join(GROUPS_SPLIT[group]),
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
            }
        )
    pd.DataFrame(diagnostics).to_csv(OUT / f"{variant}__data_diagnostics.csv", index=False)
    if (panel["nonfood_exp_split"] <= 0).any():
        raise RuntimeError(f"{variant}: nonfood residual has non-positive values.")
    model_cols = [f"x_{g}" for g in GROUP_ORDER] + [f"p_{g}_model" for g in GROUP_ORDER]
    if panel[model_cols].isna().any().any():
        raise RuntimeError(f"{variant}: missing model x or p values.")
    if (panel[model_cols] <= 0).any().any():
        raise RuntimeError(f"{variant}: non-positive model x or p values.")
    return panel


def panel_to_arrays(panel: pd.DataFrame) -> pipe.ModelArrays:
    return pipe.ModelArrays(
        obs_ids=panel["obs_id"].astype(str).to_numpy(),
        provinces=panel["province"].to_numpy(int),
        years=panel["year"].to_numpy(int),
        group_names=GROUP_ORDER,
        x=panel[[f"x_{g}" for g in GROUP_ORDER]].to_numpy(float),
        p=panel[[f"p_{g}_model" for g in GROUP_ORDER]].to_numpy(float),
        m=panel["m"].to_numpy(float),
    )


def elasticity_for_point(
    p: np.ndarray,
    m: float,
    params: dict[str, np.ndarray | float],
    group_names: list[str],
) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    def pred_at_income(income: float) -> tuple[np.ndarray, float]:
        tmp = pipe.ModelArrays(
            obs_ids=np.array(["elasticity_point"]),
            provinces=np.array([0]),
            years=np.array([0]),
            group_names=group_names,
            x=np.zeros((1, len(group_names))),
            p=np.asarray(p, dtype=float)[None, :],
            m=np.asarray([income], dtype=float),
        )
        xhat_tmp, u_tmp = pipe.predict_x(params, tmp)
        if xhat_tmp is None or u_tmp is None:
            raise ValueError("utility solve failed")
        return xhat_tmp[0], float(u_tmp[0])

    xhat, u = pred_at_income(m)
    step = max(1e-4, 1e-4 * m)
    m_minus = max(m - step, 1e-6)
    x_minus, _ = pred_at_income(m_minus)
    x_plus, _ = pred_at_income(m + step)
    eta = (np.log(x_plus) - np.log(x_minus)) / (np.log(m + step) - np.log(m_minus))
    phi, _ = pipe.phi_gamma(
        u,
        np.asarray(params["alpha"], float),
        np.asarray(params["beta"], float),
        np.asarray(params["delta"], float),
        np.asarray(params["tau"], float),
        float(params["omega"]),
    )
    return eta, xhat, u, phi


def price_elasticities_for_point(
    p: np.ndarray,
    m: float,
    params: dict[str, np.ndarray | float],
    group_names: list[str],
    step_pct: float = 1e-4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    eta, xhat, u, _ = elasticity_for_point(p, m, params, group_names)
    marshallian = np.full((len(group_names), len(group_names)), np.nan)
    p = np.asarray(p, dtype=float)
    for j in range(len(group_names)):
        p_minus = p.copy()
        p_plus = p.copy()
        p_minus[j] *= 1 - step_pct
        p_plus[j] *= 1 + step_pct
        try:
            _, x_minus, _, _ = elasticity_for_point(p_minus, m, params, group_names)
            _, x_plus, _, _ = elasticity_for_point(p_plus, m, params, group_names)
            marshallian[:, j] = (np.log(x_plus) - np.log(x_minus)) / (
                np.log(p_plus[j]) - np.log(p_minus[j])
            )
        except Exception:
            continue
    budget_shares = p * xhat / m
    hicksian = marshallian + eta[:, None] * budget_shares[None, :]
    return marshallian, hicksian, eta, budget_shares, u


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
                    "items": "+".join(GROUPS_SPLIT[group]),
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
                    "items": "+".join(GROUPS_SPLIT[group]),
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


def elasticity_outputs(variant: str, panel: pd.DataFrame, params: dict[str, np.ndarray | float]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    p_mean = panel[panel["year"].eq(2023)][[f"p_{g}_model" for g in GROUP_ORDER]].mean().to_numpy(float)
    incomes = np.array(
        sorted(
            set(
                list(np.quantile(panel["m"], [0.05, 0.25, 0.5, 0.75, 0.95]))
                + [10000, 20000, 30000, 50000, 80000, 120000, 160000, 200000]
            )
        )
    )
    rows = []
    price_m = []
    price_h = []
    consistency = []
    for income in incomes:
        try:
            mar, hic, eta, budget_shares, u = price_elasticities_for_point(p_mean, float(income), params, GROUP_ORDER)
            _, xhat, _, phi = elasticity_for_point(p_mean, float(income), params, GROUP_ORDER)
        except Exception as exc:
            rows.append(
                {
                    "variant": variant,
                    "income": income,
                    "group": "ALL",
                    "error": repr(exc),
                    "support_flag": pipe.support_flag(float(income), float(panel["m"].min()), float(panel["m"].max())),
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
                    "items": "+".join(GROUPS_SPLIT[group]),
                    "quantity_2000kcal_elasticity": eta[i],
                    "expenditure_elasticity": eta[i],
                    "budget_share_elasticity": eta[i] - 1,
                    "xhat": xhat[i],
                    "budget_share": budget_shares[i],
                    "phi": phi[i],
                    "u": u,
                    "support_flag": pipe.support_flag(float(income), float(panel["m"].min()), float(panel["m"].max())),
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
                    "support_flag": pipe.support_flag(float(income), float(panel["m"].min()), float(panel["m"].max())),
                }
                price_m.append({**base, "elasticity": mar[i, j]})
                price_h.append({**base, "elasticity": hic[i, j]})
        consistency.append(
            {
                "variant": variant,
                **pipe.elasticity_consistency_row(
                    "split_income_grid",
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
        & (
            (params["alpha"] < 1e-4)
            | (params["delta"] < 1e-4)
            | (params["tau"] < 1e-4)
        )
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
    ie = income_elasticity[
        income_elasticity["group"].ne("ALL") & income_elasticity["quantity_2000kcal_elasticity"].notna()
    ]
    extreme = ie[ie["quantity_2000kcal_elasticity"].abs() > 5]
    if not extreme.empty:
        issues.append(
            "收入弹性绝对值 > 5 的点："
            + ", ".join(
                f"{r.group}@{r.income:.0f}={r.quantity_2000kcal_elasticity:.2f}"
                for r in extreme.head(12).itertuples()
            )
            + (" 等。" if extreme.shape[0] > 12 else "。")
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
    print(f"Building split panel for {variant}...", flush=True)
    panel = build_split_panel(variant)
    panel.to_csv(OUT / f"{variant}__split_panel.csv", index=False)
    arr = panel_to_arrays(panel)
    print(f"Fitting split AIDADS/MAIDADS for {variant}...", flush=True)
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
        "# 猪肉拆分 MAIDADS/AIDADS 结果与异常检查：人均 GDP 预算口径",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 开始时间：{started_at}",
        "- 本轮不做 bootstrap。",
        "- 本轮把模型预算变量 `m` 从实际人均消费支出改为实际人均 GDP：`m = pgdp / monetary_deflator`。",
        "- 注意：此设定模仿 Gouel-Guimbard 原文的人均 GDP 预算尺度；但省级 household demand 解释应谨慎，因为 `nonfood` residual 变成 `人均 GDP - covered food expenditure`。",
        "- 分类：保留 `grain / oil / vegfruit / dairyegg / nonfood`；把原 `meatsea` 拆为 `pork / nonpork_meatsea(牛羊禽+水产品)`。",
        "",
        "## 模型品类",
        "",
        md_table(
            pd.DataFrame(
                {
                    "group": GROUP_ORDER,
                    "label_cn": [GROUP_LABEL_CN[g] for g in GROUP_ORDER],
                    "items": ["+".join(GROUPS_SPLIT[g]) for g in GROUP_ORDER],
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
                md_table(out["comparison"]),
                "",
            ]
        )
        lines.extend(
            [
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

        incomes = sorted(out["income_elasticity"]["income"].dropna().unique())
        mid = incomes[len(incomes) // 2]
        mid_el = out["income_elasticity"][
            out["income_elasticity"]["income"].eq(mid) & out["income_elasticity"]["group"].ne("ALL")
        ][["group", "group_label_cn", "quantity_2000kcal_elasticity", "budget_share", "support_flag"]]
        lines.extend([f"### 中位收入网格附近收入弹性：income={mid:.0f}", "", md_table(mid_el), ""])
    lines.extend(
        [
            "## 输出文件",
            "",
            "- `*__split_panel.csv`：拆分品类估计面板。",
            "- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。",
            "- `*__fit_by_group.csv`：分品类拟合误差。",
            "- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。",
            "- `*__elasticity_income_grid.csv`：拆分品类收入弹性。",
            "- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。",
            "- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。",
        ]
    )
    (OUT / "SPLIT_PORK_PGDP_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", nargs="+", default=list(VARIANTS.keys()), choices=list(VARIANTS.keys()))
    parser.add_argument("--maxiter-a", type=int, default=620)
    parser.add_argument("--maxiter-m", type=int, default=850)
    parser.add_argument("--seed", type=int, default=20260612)
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
        "groups": GROUPS_SPLIT,
        "budget_variable": "real_pgdp_per_capita",
        "budget_formula": "pgdp / monetary_deflator",
        "bootstrap": False,
        "maxiter_a": args.maxiter_a,
        "maxiter_m": args.maxiter_m,
    }
    (OUT / "split_run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT / "SPLIT_PORK_PGDP_RESULTS.md")


if __name__ == "__main__":
    main()

```

## ProvinceMAIDADS/scripts/run_split_pork_pgdp_formal_checks.py

```python
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

```

## ProvinceMAIDADS/scripts/run_maidads_pipeline.py

```python
from __future__ import annotations

import json
import math
import re
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ProvinceMAIDADS" / "Results"
DATA_OUT = ROOT / "ProvinceMAIDADS" / "Data" / "output"

FOOD_ITEMS = {
    "grain": {"q": "q_grain", "p": "p_grain", "code": "GRAIN"},
    "oil": {"q": "q_oil", "p": "p_oil", "code": "OIL"},
    "vegetable": {"q": "q_vegetable", "p": "p_vegetable", "code": "VEGT"},
    "fruit": {"q": "q_fruit", "p": "p_fruit", "code": "FRTO"},
    "pork": {"q": "q_pork", "p": "p_pork", "code": "PIGM"},
    "beef": {"q": "q_beef", "p": "p_beef", "code": "CATM"},
    "mutton": {"q": "q_mutton", "p": "p_mutton", "code": "SHGM"},
    "poultry": {"q": "q_poultry", "p": "p_poultry", "code": "CHKM"},
    "aquatic": {"q": "q_aquaticprod", "p": "p_aquaticprod", "code": "FISH"},
    "egg": {"q": "q_egg", "p": "p_egg", "code": "EGGS"},
    "milk": {"q": "q_milk", "p": "p_milk", "code": "MILK"},
}

GROUPS = {
    "grain": ["grain"],
    "oil": ["oil"],
    "vegfruit": ["vegetable", "fruit"],
    "pork": ["pork"],
    "meatother": ["beef", "mutton", "poultry", "aquatic"],
    "dairyegg": ["milk", "egg"],
    "nonfood": [],
}

GROUP_LABELS = {
    "grain": "Staples",
    "oil": "Oils and fats",
    "vegfruit": "Vegetables and fruits",
    "pork": "Pork",
    "meatother": "Non-pork meat/aquatic",
    "dairyegg": "Dairy and eggs",
    "nonfood": "Other/non-covered residual",
}

FEED_COEFF = {
    "pork": 3.88,
    "poultry": 3.10,
    "egg": 2.46,
    "milk": 0.62,
    "aquatic": 1.35,
    "beef": 9.80,
    "mutton": 9.80,
}

# The user supplied these coefficients as feed-grain conversion factors.  Keep a
# separate share column so the output can be replaced by total-feed coefficients
# plus cereal shares when a sourced feed-conversion table is added.
FEED_CEREAL_SHARE = {
    "pork": 1.0,
    "poultry": 1.0,
    "egg": 1.0,
    "milk": 1.0,
    "aquatic": 1.0,
    "beef": 1.0,
    "mutton": 1.0,
}

PROVINCE_CODE = {
    "北京": 11,
    "天津": 12,
    "河北": 13,
    "山西": 14,
    "内蒙古": 15,
    "辽宁": 21,
    "吉林": 22,
    "黑龙江": 23,
    "上海": 31,
    "江苏": 32,
    "浙江": 33,
    "安徽": 34,
    "福建": 35,
    "江西": 36,
    "山东": 37,
    "河南": 41,
    "湖北": 42,
    "湖南": 43,
    "广东": 44,
    "广西": 45,
    "海南": 46,
    "重庆": 50,
    "四川": 51,
    "贵州": 52,
    "云南": 53,
    "西藏": 54,
    "陕西": 61,
    "甘肃": 62,
    "青海": 63,
    "宁夏": 64,
    "新疆": 65,
}

PROJECTION_PROVINCE_MAP = {
    "Beijing": "北京",
    "Tianjin": "天津",
    "Hebei": "河北",
    "Shanxi": "山西",
    "Inner Mongolia": "内蒙古",
    "Liaoning": "辽宁",
    "Jilin": "吉林",
    "Heilongjiang": "黑龙江",
    "Shanghai": "上海",
    "jiangsu": "江苏",
    "Jiangsu": "江苏",
    "Zhejiang": "浙江",
    "Anhui": "安徽",
    "Fujian": "福建",
    "Jiangxi": "江西",
    "Shandong": "山东",
    "Henan": "河南",
    "Hubei": "湖北",
    "Hunan": "湖南",
    "Guangdong": "广东",
    "Guangxi": "广西",
    "Hainan": "海南",
    "Chongqing": "重庆",
    "Sichuan": "四川",
    "Guizhou": "贵州",
    "Yunnan": "云南",
    "Tibet": "西藏",
    "Shaanxi": "陕西",
    "Gansu": "甘肃",
    "Qinghai": "青海",
    "Ningxia": "宁夏",
    "Xinjiang": "新疆",
}

POPULATION_PROJECTION_SOURCE = (
    "Chen, Y., Guo, F., Wang, J. et al. (2020) Sci Data 7, 83; "
    "doi:10.1038/s41597-020-0421-y"
)


def ensure_dirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)


def clean_province(name: str) -> str:
    s = str(name).strip()
    replacements = {
        "北京市": "北京",
        "天津市": "天津",
        "河北省": "河北",
        "山西省": "山西",
        "内蒙古自治区": "内蒙古",
        "辽宁省": "辽宁",
        "吉林省": "吉林",
        "黑龙江省": "黑龙江",
        "上海市": "上海",
        "江苏省": "江苏",
        "浙江省": "浙江",
        "安徽省": "安徽",
        "福建省": "福建",
        "江西省": "江西",
        "山东省": "山东",
        "河南省": "河南",
        "湖北省": "湖北",
        "湖南省": "湖南",
        "广东省": "广东",
        "广西壮族自治区": "广西",
        "海南省": "海南",
        "重庆市": "重庆",
        "四川省": "四川",
        "贵州省": "贵州",
        "云南省": "云南",
        "西藏自治区": "西藏",
        "陕西省": "陕西",
        "甘肃省": "甘肃",
        "青海省": "青海",
        "宁夏回族自治区": "宁夏",
        "新疆维吾尔自治区": "新疆",
    }
    return replacements.get(s, s)


def numeric(x) -> pd.Series:
    return pd.to_numeric(x, errors="coerce")


def read_nutrition() -> pd.DataFrame:
    path = ROOT / "营养成分表.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df.rename(
        columns={
            "Unnamed: 0": "item_name",
            "Unnamed: 1": "code",
            "能量": "energy",
            "蛋白质": "protein",
            "脂肪": "fat",
            "碳水化合物": "carb",
            "毛-纯": "edible_share",
        }
    )
    df = df[df["code"].notna()].copy()
    df = df[df["code"].astype(str).str.upper() != "CODE"].copy()
    for col in ["energy", "protein", "fat", "carb", "edible_share"]:
        df[col] = numeric(df[col])
    df["kcal_per_100g_edible"] = df["energy"]
    missing_energy = df["kcal_per_100g_edible"].fillna(0) <= 0
    df.loc[missing_energy, "kcal_per_100g_edible"] = (
        4 * df.loc[missing_energy, "protein"]
        + 9 * df.loc[missing_energy, "fat"]
        + 4 * df.loc[missing_energy, "carb"]
    )
    df["kcal_per_kg_as_purchased"] = (
        df["kcal_per_100g_edible"] * 10 * df["edible_share"] / 100
    )
    return df


def read_grain_weights(nutrition: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    path = ROOT / "粮食细类消费.csv"
    raw = pd.read_csv(path, encoding="utf-8-sig").rename(
        columns={"Unnamed: 0": "code", "2024": "qty", "Unnamed: 2": "label"}
    )
    raw["qty"] = numeric(raw["qty"])
    grain_codes = ["RICE", "WHEA", "MAIZ", "POTA", "SORG", "BARL", "SOYS", "OTGR"]
    grain = raw[raw["code"].isin(grain_codes)].copy()
    grain["grain_equiv_qty"] = grain["qty"]
    grain.loc[grain["code"] == "POTA", "grain_equiv_qty"] = (
        grain.loc[grain["code"] == "POTA", "qty"] / 5
    )
    merged = grain.merge(
        nutrition[["code", "kcal_per_kg_as_purchased"]], on="code", how="left"
    )
    if merged["kcal_per_kg_as_purchased"].isna().any():
        missing = merged.loc[merged["kcal_per_kg_as_purchased"].isna(), "code"].tolist()
        raise ValueError(f"Missing nutrition rows for grain components: {missing}")
    merged["grain_equiv_weight"] = merged["grain_equiv_qty"] / merged["grain_equiv_qty"].sum()
    # For calories, use each component's actual as-purchased kcal/kg.  The
    # potato /5 conversion is a grain-equivalent accounting convention, not a
    # calorie conversion.
    merged["kcal_weight"] = merged["qty"] / merged["qty"].sum()
    grain_kcal = float((merged["kcal_weight"] * merged["kcal_per_kg_as_purchased"]).sum())
    return merged, grain_kcal


def read_population() -> pd.DataFrame:
    raw = pd.read_csv(ROOT / "分省年度人口.csv", encoding="utf-8-sig", header=None)
    header_row = raw.index[raw.iloc[:, 0].astype(str).str.strip().eq("时间")][0]
    cols = raw.iloc[header_row].tolist()
    data = raw.iloc[header_row + 1 :].copy()
    data.columns = cols
    data = data[data["时间"].astype(str).str.contains(r"\d{4}", na=False)].copy()
    data["year"] = data["时间"].astype(str).str.extract(r"(\d{4})").astype(int)
    rows = []
    for col in data.columns:
        if col in ["时间", "year"] or pd.isna(col):
            continue
        prov = clean_province(col)
        if prov not in PROVINCE_CODE:
            continue
        tmp = data[["year", col]].copy()
        tmp["provincechn"] = prov
        tmp["province"] = PROVINCE_CODE[prov]
        tmp["population_10k"] = numeric(tmp[col])
        tmp = tmp.drop(columns=[col])
        rows.append(tmp)
    out = pd.concat(rows, ignore_index=True)
    return out.dropna(subset=["population_10k"])


def read_forecast() -> pd.DataFrame:
    raw = pd.read_csv(ROOT / "副本2026-2050预测数据.csv", encoding="utf-8-sig")
    raw = raw.rename(
        columns={
            "Unnamed: 0": "year",
            "基准情景": "gdp_growth_pct",
            "基准方案": "population_10k",
            "基准情景.1": "urban_rate",
            "基准方案.1": "exchange_rate",
        }
    )
    raw["year"] = numeric(raw["year"])
    raw = raw.dropna(subset=["year"]).copy()
    raw["year"] = raw["year"].astype(int)
    for col in ["gdp_growth_pct", "population_10k", "urban_rate", "exchange_rate"]:
        raw[col] = numeric(raw[col])
    return raw


def read_provincial_population_projection(ssp: str = "SSP2") -> pd.DataFrame:
    path = ROOT / "DATA_Provincial_Population_Projection" / "Pop_TOTAL.csv"
    raw = pd.read_csv(path, encoding="utf-8-sig")
    raw = raw[(raw["X"].ne("TOTAL")) & (raw["X.1"].eq(ssp))].copy()
    raw["provincechn"] = raw["X"].map(PROJECTION_PROVINCE_MAP)
    if raw["provincechn"].isna().any():
        missing = sorted(raw.loc[raw["provincechn"].isna(), "X"].astype(str).unique())
        raise ValueError(f"Unmapped population projection provinces: {missing}")
    raw["province"] = raw["provincechn"].map(PROVINCE_CODE)
    year_cols = [c for c in raw.columns if re.fullmatch(r"X\d{4}", str(c))]
    out = raw.melt(
        id_vars=["X", "X.1", "provincechn", "province"],
        value_vars=year_cols,
        var_name="year",
        value_name="population_person",
    )
    out["year"] = out["year"].str.replace("X", "", regex=False).astype(int)
    out["population_person"] = numeric(out["population_person"])
    out["population_10k"] = out["population_person"] / 10000.0
    out["population_projection_source"] = POPULATION_PROJECTION_SOURCE
    out["population_scenario"] = ssp
    out = out[
        [
            "province",
            "provincechn",
            "year",
            "population_10k",
            "population_person",
            "population_scenario",
            "population_projection_source",
        ]
    ].sort_values(["province", "year"])
    expected = set(PROVINCE_CODE.values())
    found = set(out.loc[out["year"].eq(2030), "province"].astype(int))
    if found != expected:
        raise ValueError(f"Population projection province coverage mismatch: {sorted(expected - found)}")
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(DATA_OUT / f"provincial_population_projection_{ssp.lower()}.csv", index=False)
    return out


def read_nonfood_cpi() -> pd.DataFrame:
    path = ROOT / "中国_CPI_非食品.csv"
    raw = pd.read_csv(path, encoding="gb18030", header=None, names=["date", "value"])
    raw = raw[raw["date"].astype(str).str.match(r"\d{4}-")].copy()
    raw["year"] = raw["date"].astype(str).str.slice(0, 4).astype(int)
    raw["nonfood_cpi_yoy"] = numeric(raw["value"])
    raw = raw[["year", "nonfood_cpi_yoy"]].groupby("year", as_index=False).mean()
    raw = raw.sort_values("year")
    raw["national_nonfood_price_index_2023"] = np.nan
    raw.loc[raw["year"] == 2023, "national_nonfood_price_index_2023"] = 100.0
    for idx in raw.index[raw["year"] > 2023]:
        prev_idx = raw.index[raw.index.get_loc(idx) - 1]
        raw.loc[idx, "national_nonfood_price_index_2023"] = (
            raw.loc[prev_idx, "national_nonfood_price_index_2023"] * raw.loc[idx, "nonfood_cpi_yoy"] / 100
        )
    for idx in list(raw.index[raw["year"] < 2023])[::-1]:
        next_idx = raw.index[raw.index.get_loc(idx) + 1]
        raw.loc[idx, "national_nonfood_price_index_2023"] = (
            raw.loc[next_idx, "national_nonfood_price_index_2023"] / (raw.loc[next_idx, "nonfood_cpi_yoy"] / 100)
        )
    if raw["year"].min() > 2015 and 2016 in set(raw["year"]):
        row_2016 = raw.loc[raw["year"].eq(2016)].iloc[0]
        raw = pd.concat(
            [
                pd.DataFrame(
                    [
                        {
                            "year": 2015,
                            "nonfood_cpi_yoy": np.nan,
                            "national_nonfood_price_index_2023": row_2016["national_nonfood_price_index_2023"]
                            / (row_2016["nonfood_cpi_yoy"] / 100),
                            "national_nonfood_bridge": "backcast_from_2016_yoy",
                        }
                    ]
                ),
                raw.assign(national_nonfood_bridge="observed_yoy_chain"),
            ],
            ignore_index=True,
        )
    else:
        raw["national_nonfood_bridge"] = "observed_yoy_chain"
    return raw


def read_province_cpi_table(filename: str, value_name: str) -> pd.DataFrame:
    path = ROOT / filename
    rows = []
    header = None
    with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            cells = [c.replace("\t", "").strip() for c in line.strip().split(",")]
            cells = [c for c in cells if c != ""]
            if not cells:
                continue
            if cells[0] == "数据时间":
                header = cells
                continue
            if header is None or not re.match(r"^\d{4}年$", cells[0]):
                continue
            year = int(cells[0].replace("年", ""))
            for prov_name, value in zip(header[1:], cells[1:]):
                prov = clean_province(prov_name)
                if prov not in PROVINCE_CODE:
                    continue
                rows.append(
                    {
                        "year": year,
                        "province": PROVINCE_CODE[prov],
                        "provincechn": prov,
                        value_name: pd.to_numeric(value, errors="coerce"),
                    }
                )
    return pd.DataFrame(rows).dropna(subset=[value_name])


def index_from_yoy(df: pd.DataFrame, yoy_col: str, index_col: str, base_year: int = 2023) -> pd.DataFrame:
    out = df.copy()
    out[index_col] = np.nan
    pieces = []
    for province, tmp in out.groupby("province", sort=False):
        tmp = tmp.sort_values("year").copy()
        if base_year not in set(tmp["year"]):
            pieces.append(tmp)
            continue
        tmp.loc[tmp["year"] == base_year, index_col] = 100.0
        for idx in tmp.index[tmp["year"] > base_year]:
            pos = tmp.index.get_loc(idx)
            prev_idx = tmp.index[pos - 1]
            if pd.isna(tmp.loc[prev_idx, index_col]) or pd.isna(tmp.loc[idx, yoy_col]):
                continue
            tmp.loc[idx, index_col] = tmp.loc[prev_idx, index_col] * tmp.loc[idx, yoy_col] / 100
        for idx in list(tmp.index[tmp["year"] < base_year])[::-1]:
            pos = tmp.index.get_loc(idx)
            next_idx = tmp.index[pos + 1]
            if pd.isna(tmp.loc[next_idx, index_col]) or pd.isna(tmp.loc[next_idx, yoy_col]):
                continue
            tmp.loc[idx, index_col] = tmp.loc[next_idx, index_col] / (tmp.loc[next_idx, yoy_col] / 100)
        pieces.append(tmp)
    return pd.concat(pieces, ignore_index=True)


def build_province_cpi_indices(data: pd.DataFrame | None = None) -> pd.DataFrame:
    total = read_province_cpi_table("消费价格指数上年=100.csv", "total_cpi_yoy")
    food = pd.concat(
        [
            read_province_cpi_table("食品类消费价格指数1上年=100.csv", "food_cpi_yoy"),
            read_province_cpi_table("食品类消费价格指数2上年=100.csv", "food_cpi_yoy"),
            read_province_cpi_table("食品类消费价格指数3上年=100.csv", "food_cpi_yoy"),
        ],
        ignore_index=True,
    )
    food = food.sort_values(["province", "year"]).drop_duplicates(["province", "year"], keep="last")
    out = total.merge(food[["year", "province", "food_cpi_yoy"]], on=["year", "province"], how="left")
    if data is not None:
        share = data[["year", "province"]].copy()
        if {"exp_food_nominal", "expenditure_nominal"}.issubset(data.columns):
            share["food_budget_share_all"] = (
                numeric(data["exp_food_nominal"]) / numeric(data["expenditure_nominal"])
            )
        else:
            share["food_budget_share_all"] = numeric(data["exp_food"]) / numeric(data["m"])
        out = out.merge(share[["year", "province", "food_budget_share_all"]], on=["year", "province"], how="left")
    else:
        out["food_budget_share_all"] = np.nan
    s = out["food_budget_share_all"].clip(lower=0.01, upper=0.80)
    out["nonfood_cpi_yoy_approx"] = (out["total_cpi_yoy"] - s * out["food_cpi_yoy"]) / (1 - s)
    invalid = (out["nonfood_cpi_yoy_approx"] < 70) | (out["nonfood_cpi_yoy_approx"] > 140)
    out.loc[invalid, "nonfood_cpi_yoy_approx"] = np.nan
    for yoy_col, index_col in [
        ("total_cpi_yoy", "total_price_index_2023"),
        ("food_cpi_yoy", "food_price_index_2023"),
        ("nonfood_cpi_yoy_approx", "nonfood_price_index_2023"),
    ]:
        out = index_from_yoy(out, yoy_col, index_col)
    national_nonfood = read_nonfood_cpi()
    out = out.merge(national_nonfood, on="year", how="left")
    out["nonfood_price_source"] = "derived_from_total_food_cpi"
    missing_nonfood = out["nonfood_price_index_2023"].isna()
    out.loc[missing_nonfood, "nonfood_price_index_2023"] = out.loc[
        missing_nonfood, "national_nonfood_price_index_2023"
    ]
    out.loc[missing_nonfood, "nonfood_price_source"] = "national_nonfood_cpi_fallback"
    out["nonfood_relative_price_index_2023"] = (
        out["nonfood_price_index_2023"] / out["total_price_index_2023"] * 100
    )
    return out.sort_values(["province", "year"])


def build_model_data(
    nonfood_price_mode: str = "national_nonfood_cpi",
    output_suffix: str = "",
    monetary_mode: str = "real_2023_cpi",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nutrition = read_nutrition()
    grain_weights, grain_kcal = read_grain_weights(nutrition)
    pop = read_population()

    data = pd.read_stata(ROOT / "ProvinceData" / "workdata" / "data.dta")
    data = data.merge(pop[["year", "province", "population_10k"]], on=["year", "province"], how="left")
    data["obs_id"] = data["province"].astype(int).astype(str) + "_" + data["year"].astype(int).astype(str)
    data["expenditure_nominal"] = numeric(data["expenditure"])
    data["exp_food_nominal"] = numeric(data["exp_food"])

    cpi_panel = build_province_cpi_indices(data)
    cpi_panel.to_csv(DATA_OUT / "province_cpi_indices.csv", index=False)
    cpi_cols = [
        "total_cpi_yoy",
        "food_cpi_yoy",
        "nonfood_cpi_yoy_approx",
        "total_price_index_2023",
        "food_price_index_2023",
        "nonfood_price_index_2023",
        "nonfood_relative_price_index_2023",
        "national_nonfood_price_index_2023",
        "food_budget_share_all",
    ]
    data = data.merge(cpi_panel[["year", "province", *cpi_cols]], on=["year", "province"], how="left")

    if monetary_mode == "real_2023_cpi":
        data["deflator_total_2015"] = numeric(data["fixed_cpi"])
        data["monetary_deflator"] = data["total_price_index_2023"] / 100.0
        data["food_price_deflator"] = data["food_price_index_2023"] / 100.0
    elif monetary_mode == "real_fixed_cpi_2015":
        data["deflator_total_2015"] = numeric(data["fixed_cpi"])
        data["monetary_deflator"] = data["deflator_total_2015"] / 100.0
        data["food_price_deflator"] = data["monetary_deflator"]
    elif monetary_mode == "nominal":
        data["deflator_total_2015"] = 100.0
        data["monetary_deflator"] = 1.0
        data["food_price_deflator"] = 1.0
    else:
        raise ValueError(f"Unknown monetary_mode: {monetary_mode}")
    data["m"] = data["expenditure_nominal"] / data["monetary_deflator"]

    kcal_lookup = dict(zip(nutrition["code"], nutrition["kcal_per_kg_as_purchased"]))
    kcal_lookup["GRAIN"] = grain_kcal
    kcal_lookup["OIL"] = float(
        nutrition.loc[nutrition["code"].isin(["SOYO", "RAPO", "GRDO"]), "kcal_per_kg_as_purchased"].mean()
    )

    for item, spec in FOOD_ITEMS.items():
        q = numeric(data[spec["q"]])
        p = numeric(data[spec["p"]]) / data["food_price_deflator"]
        kcal_kg = kcal_lookup[spec["code"]]
        data[f"{item}_kcal_year"] = q * kcal_kg
        data[f"{item}_x"] = data[f"{item}_kcal_year"] / 365 / 2000
        data[f"{item}_exp"] = q * p
        data[f"{item}_kg"] = q
        data[f"{item}_kcal_per_kg"] = kcal_kg

    for group, items in GROUPS.items():
        if group == "nonfood":
            continue
        data[f"x_{group}"] = data[[f"{i}_x" for i in items]].sum(axis=1)
        data[f"e_{group}"] = data[[f"{i}_exp" for i in items]].sum(axis=1)
        data[f"p_{group}_model"] = data[f"e_{group}"] / data[f"x_{group}"]

    food_exp_cols = [f"e_{g}" for g in GROUPS if g != "nonfood"]
    data["covered_food_exp"] = data[food_exp_cols].sum(axis=1)
    data["nonfood_exp"] = data["m"] - data["covered_food_exp"]
    data["other_noncovered_exp"] = data["nonfood_exp"]
    if nonfood_price_mode == "national_nonfood_cpi":
        data["p_nonfood_model"] = data["national_nonfood_price_index_2023"]
    elif nonfood_price_mode == "flat":
        data["p_nonfood_model"] = 100.0
    elif nonfood_price_mode == "cpi_nonfood":
        data["p_nonfood_model"] = data["nonfood_price_index_2023"]
    elif nonfood_price_mode == "relative_cpi_nonfood":
        data["p_nonfood_model"] = data["nonfood_relative_price_index_2023"]
    else:
        raise ValueError(f"Unknown nonfood_price_mode: {nonfood_price_mode}")
    data["x_nonfood"] = data["nonfood_exp"] / data["p_nonfood_model"]
    data["covered_daily_kcal"] = data[[f"x_{g}" for g in GROUPS if g != "nonfood"]].sum(axis=1) * 2000
    data["covered_food_budget_share"] = data["covered_food_exp"] / data["m"]

    keep_groups = list(GROUPS.keys())
    rows = []
    for _, row in data.iterrows():
        for group in keep_groups:
            rows.append(
                {
                    "obs_id": row["obs_id"],
                    "province": int(row["province"]),
                    "provincechn": row["provincechn"],
                    "year": int(row["year"]),
                    "population_10k": row["population_10k"],
                    "group": group,
                    "group_label": GROUP_LABELS[group],
                    "x": row[f"x_{group}"],
                    "p": row[f"p_{group}_model"],
                    "m": row["m"],
                }
            )
    long_df = pd.DataFrame(rows)

    panel_cols = [
        "obs_id",
        "province",
        "provincechn",
        "year",
        "population_10k",
        "expenditure_nominal",
        "exp_food_nominal",
        "deflator_total_2015",
        "monetary_deflator",
        "m",
        "covered_food_exp",
        "nonfood_exp",
        "covered_daily_kcal",
        "covered_food_budget_share",
    ]
    panel_cols += cpi_cols
    for group in keep_groups:
        panel_cols += [f"x_{group}", f"p_{group}_model"]
    panel = data[panel_cols].copy()
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna()
    long_df = long_df[long_df["obs_id"].isin(panel["obs_id"])].copy()

    if (panel["nonfood_exp"] <= 0).any():
        bad = panel.loc[panel["nonfood_exp"] <= 0, ["obs_id", "nonfood_exp"]]
        raise ValueError(f"Non-positive nonfood residuals:\n{bad.head()}")
    if (long_df["x"] <= 0).any() or (long_df["p"] <= 0).any():
        raise ValueError("Non-positive model quantity or price found.")

    nutrition_out = nutrition.copy()
    nutrition_out.to_csv(DATA_OUT / "nutrition_processed.csv", index=False)
    grain_weights.to_csv(DATA_OUT / "grain_weights_processed.csv", index=False)
    panel.to_csv(DATA_OUT / f"maidads6_panel{output_suffix}.csv", index=False)
    long_df.to_csv(DATA_OUT / f"maidads6_long{output_suffix}.csv", index=False)
    return panel, long_df, nutrition_out


@dataclass
class ModelArrays:
    obs_ids: np.ndarray
    provinces: np.ndarray
    years: np.ndarray
    group_names: list[str]
    x: np.ndarray
    p: np.ndarray
    m: np.ndarray


def panel_to_arrays(panel: pd.DataFrame) -> ModelArrays:
    group_names = list(GROUPS.keys())
    x = panel[[f"x_{g}" for g in group_names]].to_numpy(float)
    p = panel[[f"p_{g}_model" for g in group_names]].to_numpy(float)
    m = panel["m"].to_numpy(float)
    return ModelArrays(
        obs_ids=panel["obs_id"].to_numpy(),
        provinces=panel["province"].to_numpy(int),
        years=panel["year"].to_numpy(int),
        group_names=group_names,
        x=x,
        p=p,
        m=m,
    )


def softmax(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    z = z - np.max(z)
    e = np.exp(z)
    return e / e.sum()


def sigmoid_safe(x: float | np.ndarray) -> float | np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60, 60)))


def phi_gamma(
    u: float, alpha: np.ndarray, beta: np.ndarray, delta: np.ndarray, tau: np.ndarray, omega: float
) -> tuple[np.ndarray, np.ndarray]:
    s1 = sigmoid_safe(u)
    phi = alpha * (1 - s1) + beta * s1
    if omega <= 1e-12:
        s2 = 0.5
    else:
        s2 = sigmoid_safe(omega * u)
    gamma = delta * (1 - s2) + tau * s2
    return phi, gamma


def phi_gamma_matrix(
    u: np.ndarray, alpha: np.ndarray, beta: np.ndarray, delta: np.ndarray, tau: np.ndarray, omega: float
) -> tuple[np.ndarray, np.ndarray]:
    u = np.asarray(u, dtype=float)
    s1 = sigmoid_safe(u)[:, None]
    phi = alpha[None, :] * (1 - s1) + beta[None, :] * s1
    if omega <= 1e-12:
        s2 = np.full((u.size, 1), 0.5)
    else:
        s2 = sigmoid_safe(omega * u)[:, None]
    gamma = delta[None, :] * (1 - s2) + tau[None, :] * s2
    return phi, gamma


def unpack_aidads(raw: np.ndarray, n: int) -> dict[str, np.ndarray | float]:
    alpha = softmax(raw[:n])
    beta = np.zeros(n)
    beta[-1] = 1.0
    gamma = np.exp(np.clip(raw[n : 2 * n], -30, 12))
    kappa = float(raw[2 * n])
    return {"alpha": alpha, "beta": beta, "delta": gamma, "tau": gamma, "omega": 0.0, "kappa": kappa}


def unpack_maidads(raw: np.ndarray, n: int) -> dict[str, np.ndarray | float]:
    alpha = softmax(raw[:n])
    beta = np.zeros(n)
    beta[-1] = 1.0
    delta = np.exp(np.clip(raw[n : 2 * n], -30, 12))
    tau = np.exp(np.clip(raw[2 * n : 3 * n], -30, 12))
    omega = float(np.exp(np.clip(raw[3 * n], -9, 4)))
    kappa = float(raw[3 * n + 1])
    return {"alpha": alpha, "beta": beta, "delta": delta, "tau": tau, "omega": omega, "kappa": kappa}


def utility_gap_vector(
    u: np.ndarray,
    p: np.ndarray,
    m: np.ndarray,
    alpha: np.ndarray,
    beta: np.ndarray,
    delta: np.ndarray,
    tau: np.ndarray,
    omega: float,
    kappa: float,
) -> np.ndarray:
    phi, gamma = phi_gamma_matrix(u, alpha, beta, delta, tau, omega)
    disc = m - np.sum(p * gamma, axis=1)
    qdisc = phi * disc[:, None] / p
    out = np.sum(phi * np.log(np.maximum(qdisc, 1e-300)), axis=1) - u - kappa
    out[(disc <= 0) | ~np.isfinite(out)] = np.nan
    return out


def solve_u_vectorized(
    p: np.ndarray,
    m: np.ndarray,
    alpha: np.ndarray,
    beta: np.ndarray,
    delta: np.ndarray,
    tau: np.ndarray,
    omega: float,
    kappa: float,
) -> np.ndarray | None:
    p = np.asarray(p, dtype=float)
    m = np.asarray(m, dtype=float)
    c = m.size
    grid = np.linspace(-35, 35, 71)
    vals = np.vstack(
        [
            utility_gap_vector(np.full(c, u), p, m, alpha, beta, delta, tau, omega, kappa)
            for u in grid
        ]
    )
    ok = np.isfinite(vals)
    crosses = ok[:-1] & ok[1:] & (vals[:-1] * vals[1:] <= 0)
    has = crosses.any(axis=0)
    if not np.all(has):
        return None

    first = np.argmax(crosses, axis=0)
    rows = np.arange(c)
    lo = grid[first].astype(float)
    hi = grid[first + 1].astype(float)
    glo = vals[first, rows].astype(float)

    for _ in range(64):
        mid = (lo + hi) / 2
        gmid = utility_gap_vector(mid, p, m, alpha, beta, delta, tau, omega, kappa)
        if np.any(~np.isfinite(gmid)):
            return None
        same_side = glo * gmid > 0
        lo[same_side] = mid[same_side]
        glo[same_side] = gmid[same_side]
        hi[~same_side] = mid[~same_side]
    return (lo + hi) / 2


def solve_u_for_obs(
    p: np.ndarray,
    m: float,
    alpha: np.ndarray,
    beta: np.ndarray,
    delta: np.ndarray,
    tau: np.ndarray,
    omega: float,
    kappa: float,
) -> float | None:
    u = solve_u_vectorized(
        np.asarray(p, dtype=float)[None, :],
        np.asarray([m], dtype=float),
        alpha,
        beta,
        delta,
        tau,
        omega,
        kappa,
    )
    if u is None:
        return None
    return float(u[0])


def predict_x(params: dict[str, np.ndarray | float], arr: ModelArrays) -> tuple[np.ndarray | None, np.ndarray | None]:
    alpha = np.asarray(params["alpha"], float)
    beta = np.asarray(params["beta"], float)
    delta = np.asarray(params["delta"], float)
    tau = np.asarray(params["tau"], float)
    omega = float(params["omega"])
    kappa = float(params["kappa"])
    uvec = solve_u_vectorized(arr.p, arr.m, alpha, beta, delta, tau, omega, kappa)
    if uvec is None:
        return None, None
    phi, gamma = phi_gamma_matrix(uvec, alpha, beta, delta, tau, omega)
    disc = arr.m - np.sum(arr.p * gamma, axis=1)
    if np.any(disc <= 0):
        return None, None
    xhat = gamma + phi * disc[:, None] / arr.p
    if np.any(~np.isfinite(xhat)) or np.any(xhat <= 0):
        return None, None
    return xhat, uvec


def neg_loglike(raw: np.ndarray, arr: ModelArrays, model: str) -> float:
    n = arr.x.shape[1]
    try:
        params = unpack_aidads(raw, n) if model == "aidads" else unpack_maidads(raw, n)
        xhat, _ = predict_x(params, arr)
        if xhat is None:
            return 1e12
        eps = arr.x - xhat
        w = eps.T @ eps / eps.shape[0]
        w = w + np.eye(w.shape[0]) * 1e-10
        sign, logdet = np.linalg.slogdet(w)
        if sign <= 0 or not np.isfinite(logdet):
            return 1e12
        c, n2 = arr.x.shape
        nll = 0.5 * c * (n2 * (1 + math.log(2 * math.pi)) + logdet)
        if not np.isfinite(nll):
            return 1e12
        return float(nll)
    except Exception:
        return 1e12


def initial_aidads(arr: ModelArrays) -> np.ndarray:
    n = arr.x.shape[1]
    shares = (arr.p * arr.x) / arr.m[:, None]
    alpha0 = shares.mean(axis=0)
    alpha0 = np.maximum(alpha0, 1e-4)
    alpha0 = alpha0 / alpha0.sum()
    gamma0 = np.maximum(arr.x.min(axis=0) / 4, 1e-4)
    raw = np.r_[np.log(alpha0), np.log(gamma0), 1.0]
    return raw


def raw_param_names(model: str, group_names: list[str]) -> list[str]:
    if model == "aidads":
        return (
            [f"raw_alpha[{g}]" for g in group_names]
            + [f"log_gamma[{g}]" for g in group_names]
            + ["kappa"]
        )
    return (
        [f"raw_alpha[{g}]" for g in group_names]
        + [f"log_delta[{g}]" for g in group_names]
        + [f"log_tau[{g}]" for g in group_names]
        + ["log_omega", "kappa"]
    )


def optimizer_diagnostics(
    res,
    bounds: list[tuple[float, float]],
    names: list[str],
    model: str,
    start_id: str,
    selected: bool,
) -> dict:
    jac = getattr(res, "jac", None)
    if jac is None:
        grad_norm = np.nan
        max_abs_gradient = np.nan
    else:
        jac = np.asarray(jac, dtype=float)
        grad_norm = float(np.linalg.norm(jac))
        max_abs_gradient = float(np.nanmax(np.abs(jac)))
    boundary_params = []
    x = np.asarray(getattr(res, "x", np.full(len(bounds), np.nan)), dtype=float)
    for name, value, (lo, hi) in zip(names, x, bounds):
        if np.isfinite(value) and (abs(value - lo) < 1e-5 or abs(value - hi) < 1e-5):
            boundary_params.append(name)
    return {
        "model": "AIDADS_sat" if model == "aidads" else "MAIDADS_sat",
        "start_id": start_id,
        "selected": selected,
        "success": bool(getattr(res, "success", False)),
        "nll": float(getattr(res, "fun", np.nan)),
        "n_iter": int(getattr(res, "nit", -1)) if getattr(res, "nit", None) is not None else -1,
        "grad_norm": grad_norm,
        "max_abs_gradient": max_abs_gradient,
        "hessian_status": "not_available_lbfgsb",
        "n_boundary_raw_params": len(boundary_params),
        "boundary_raw_params": ";".join(boundary_params),
        "message": str(getattr(res, "message", "")),
    }


def parameter_boundary_rows(fits: tuple[dict, dict], group_names: list[str]) -> list[dict]:
    rows = []
    for fit in fits:
        params = fit["params"]
        for j, group in enumerate(group_names):
            for name in ["alpha", "beta", "delta", "tau"]:
                value = float(params[name][j])
                if name == "beta":
                    imposed = (group != "nonfood" and abs(value) < 1e-12) or (
                        group == "nonfood" and abs(value - 1.0) < 1e-12
                    )
                else:
                    imposed = False
                rows.append(
                    {
                        "model": fit["model"],
                        "group": group,
                        "parameter": name,
                        "value": value,
                        "near_lower_boundary": bool(value < 1e-4),
                        "near_upper_boundary": bool(name in ["alpha", "beta"] and value > 1 - 1e-4),
                        "imposed_by_saturation": imposed,
                    }
                )
        for name in ["omega", "kappa"]:
            value = float(params[name])
            rows.append(
                {
                    "model": fit["model"],
                    "group": "all",
                    "parameter": name,
                    "value": value,
                    "near_lower_boundary": bool(name == "omega" and value < 1e-4),
                    "near_upper_boundary": False,
                    "imposed_by_saturation": False,
                }
            )
    return rows


def fit_model(
    arr: ModelArrays,
    maidads_random_scales: tuple[float, ...] = (0.05, 0.15),
    maxiter_a: int = 450,
    maxiter_m: int = 650,
    progress: bool = True,
    seed: int = 20260607,
    wide_multistart: bool = True,
) -> tuple[dict, dict]:
    n = arr.x.shape[1]
    group_names = arr.group_names
    raw0 = initial_aidads(arr)
    bounds_a = [(-8, 8)] * n + [(-12, 8)] * n + [(-20, 20)]
    diagnostics: list[dict] = []

    def callback(label: str):
        state = {"i": 0}

        def _cb(xk: np.ndarray) -> None:
            if not progress:
                return
            state["i"] += 1
            if state["i"] == 1 or state["i"] % 25 == 0:
                val = neg_loglike(xk, arr, "aidads" if label.startswith("AIDADS") else "maidads")
                print(f"{label}: iter={state['i']}, nll={val:.3f}", flush=True)

        return _cb

    if progress:
        print("Fitting AIDADS_sat baseline...", flush=True)
    res_a = minimize(
        neg_loglike,
        raw0,
        args=(arr, "aidads"),
        method="L-BFGS-B",
        bounds=bounds_a,
        callback=callback("AIDADS_sat"),
        options={"maxiter": maxiter_a, "maxfun": maxiter_a * 200, "ftol": 1e-8, "maxls": 30},
    )
    if progress:
        print(
            f"AIDADS_sat finished: nll={res_a.fun:.3f}, success={res_a.success}, message={res_a.message}",
            flush=True,
        )
    diagnostics.append(
        optimizer_diagnostics(
            res_a,
            bounds_a,
            raw_param_names("aidads", group_names),
            "aidads",
            "warm_start",
            True,
        )
    )

    aparams = unpack_aidads(res_a.x, n)
    gamma = np.asarray(aparams["delta"], float)
    raw_nested_m0 = np.r_[
        res_a.x[:n],
        np.log(np.maximum(gamma, 1e-12)),
        np.log(np.maximum(gamma, 1e-12)),
        -9.0,
        res_a.x[-1],
    ]
    raw_m0 = np.r_[
        res_a.x[:n],
        np.log(gamma),
        np.log(gamma * 1.02 + 1e-8),
        math.log(0.2),
        res_a.x[-1],
    ]
    bounds_m = [(-8, 8)] * n + [(-12, 8)] * n + [(-12, 8)] * n + [(-9, 3)] + [(-20, 20)]
    best = None

    def is_usable_result(res) -> bool:
        return bool(res.success) and np.isfinite(res.fun) and float(res.fun) < 1e11

    def is_better_result(candidate, incumbent) -> bool:
        if incumbent is None:
            return True
        candidate_ok = is_usable_result(candidate)
        incumbent_ok = is_usable_result(incumbent)
        if candidate_ok != incumbent_ok:
            return candidate_ok
        return float(candidate.fun) < float(incumbent.fun)

    starts = [raw_nested_m0, raw_m0]
    # Warm-start from an externally verified global optimum (7-group split-pork
    # MAIDADS has a deep basin the AIDADS-anchored starts miss).  The saved
    # vector is a strong seed even for bootstrap resamples; L-BFGS-B refines it.
    _ws_path = Path(__file__).with_name("maidads_warmstart_7g.npy")
    if _ws_path.exists():
        try:
            _ws = np.load(_ws_path)
            if _ws.shape == raw_m0.shape:
                _lo = np.array([b[0] for b in bounds_m])
                _hi = np.array([b[1] for b in bounds_m])
                starts.insert(0, np.clip(_ws.astype(float), _lo, _hi))
        except Exception:
            pass
    rng = np.random.default_rng(seed)
    _scales = tuple(maidads_random_scales)
    if wide_multistart:
        _scales = _scales + (0.3, 0.6, 0.6, 1.0)
    for scale in _scales:
        starts.append(raw_m0 + rng.normal(0, scale, size=raw_m0.size))
    for i, start in enumerate(starts, start=1):
        if progress:
            print(f"Fitting MAIDADS_sat start {i}/{len(starts)}...", flush=True)
        res = minimize(
            neg_loglike,
            start,
            args=(arr, "maidads"),
            method="L-BFGS-B",
            bounds=bounds_m,
            callback=callback(f"MAIDADS_sat start {i}"),
            options={"maxiter": maxiter_m, "maxfun": maxiter_m * 200, "ftol": 1e-8, "maxls": 30},
        )
        if progress:
            print(
                f"MAIDADS_sat start {i} finished: nll={res.fun:.3f}, success={res.success}, message={res.message}",
                flush=True,
            )
        diagnostics.append(
            optimizer_diagnostics(
                res,
                bounds_m,
                raw_param_names("maidads", group_names),
                "maidads",
                f"start_{i}",
                False,
            )
        )
        if is_better_result(res, best):
            best = res

    mparams = unpack_maidads(best.x, n)
    for row in diagnostics:
        if row["model"] == "MAIDADS_sat" and np.isclose(row["nll"], float(best.fun), rtol=0, atol=1e-8):
            row["selected"] = True
            break
    return (
        {
            "model": "AIDADS_sat",
            "result": res_a,
            "params": aparams,
            "nll": float(res_a.fun),
            "diagnostics": diagnostics,
        },
        {
            "model": "MAIDADS_sat",
            "result": best,
            "params": mparams,
            "nll": float(best.fun),
            "diagnostics": diagnostics,
        },
    )


def elasticity_for_point(
    p: np.ndarray,
    m: float,
    params: dict[str, np.ndarray | float],
) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    alpha = np.asarray(params["alpha"], float)
    beta = np.asarray(params["beta"], float)
    delta = np.asarray(params["delta"], float)
    tau = np.asarray(params["tau"], float)
    omega = float(params["omega"])
    kappa = float(params["kappa"])

    def pred_at_income(income: float) -> tuple[np.ndarray, float]:
        tmp_arr = ModelArrays(
            obs_ids=np.array(["elasticity_point"]),
            provinces=np.array([0]),
            years=np.array([0]),
            group_names=list(GROUPS.keys()),
            x=np.zeros((1, len(GROUPS))),
            p=np.asarray(p, dtype=float)[None, :],
            m=np.asarray([income], dtype=float),
        )
        xhat_tmp, u_tmp = predict_x(
            {"alpha": alpha, "beta": beta, "delta": delta, "tau": tau, "omega": omega, "kappa": kappa},
            tmp_arr,
        )
        if xhat_tmp is None or u_tmp is None:
            raise ValueError("Could not solve utility for elasticity point.")
        return xhat_tmp[0], float(u_tmp[0])

    xhat, u = pred_at_income(m)
    step = max(1e-4, 1e-4 * m)
    m_minus = max(m - step, 1e-6)
    m_plus = m + step
    try:
        x_minus, _ = pred_at_income(m_minus)
        x_plus, _ = pred_at_income(m_plus)
    except Exception as exc:
        raise ValueError("Could not solve utility for elasticity point.")
    eta = (np.log(x_plus) - np.log(x_minus)) / (np.log(m_plus) - np.log(m_minus))
    phi, _ = phi_gamma(u, alpha, beta, delta, tau, omega)
    return eta, xhat, u, phi


def price_elasticities_for_point(
    p: np.ndarray,
    m: float,
    params: dict[str, np.ndarray | float],
    step_pct: float = 1e-4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    eta, xhat, u, _ = elasticity_for_point(p, m, params)
    p = np.asarray(p, dtype=float)
    marshallian = np.full((p.size, p.size), np.nan)
    for j in range(p.size):
        h = max(step_pct, 1e-8)
        p_minus = p.copy()
        p_plus = p.copy()
        p_minus[j] *= 1 - h
        p_plus[j] *= 1 + h
        try:
            _, x_minus, _, _ = elasticity_for_point(p_minus, m, params)
            _, x_plus, _, _ = elasticity_for_point(p_plus, m, params)
        except Exception:
            continue
        marshallian[:, j] = (np.log(x_plus) - np.log(x_minus)) / (
            np.log(p_plus[j]) - np.log(p_minus[j])
        )
    budget_shares = p * xhat / m
    hicksian = marshallian + eta[:, None] * budget_shares[None, :]
    return marshallian, hicksian, eta, budget_shares, u


def elasticity_consistency_row(
    location: str,
    income: float,
    group_names: list[str],
    marshallian: np.ndarray,
    hicksian: np.ndarray,
    eta: np.ndarray,
    budget_shares: np.ndarray,
) -> dict:
    adding_up_income = float(np.nansum(budget_shares * eta) - 1.0)
    price_adding = np.nansum(budget_shares[:, None] * marshallian, axis=0) + budget_shares
    marshallian_homogeneity = np.nansum(marshallian, axis=1) + eta
    hicksian_homogeneity = np.nansum(hicksian, axis=1)
    slutsky_errors = []
    for i in range(len(group_names)):
        for j in range(len(group_names)):
            slutsky_errors.append(budget_shares[i] * hicksian[i, j] - budget_shares[j] * hicksian[j, i])
    own_price_positive = [
        group_names[i]
        for i in range(len(group_names))
        if np.isfinite(marshallian[i, i]) and marshallian[i, i] > 0
    ]
    return {
        "location": location,
        "income": income,
        "adding_up_income_error": adding_up_income,
        "max_abs_price_adding_up_error": float(np.nanmax(np.abs(price_adding))),
        "max_abs_marshallian_homogeneity_error": float(np.nanmax(np.abs(marshallian_homogeneity))),
        "max_abs_hicksian_homogeneity_error": float(np.nanmax(np.abs(hicksian_homogeneity))),
        "max_abs_slutsky_symmetry_error": float(np.nanmax(np.abs(slutsky_errors))),
        "n_positive_own_price_marshallian": len(own_price_positive),
        "positive_own_price_groups": ";".join(own_price_positive),
    }


def support_flag(value: float, lower: float, upper: float) -> str:
    return "in_support" if lower <= value <= upper else "extrapolation"


def build_results(panel: pd.DataFrame, arr: ModelArrays, fits: tuple[dict, dict], nutrition: pd.DataFrame) -> dict:
    group_names = arr.group_names
    diagnostics = pd.DataFrame(fits[1].get("diagnostics", []))
    if not diagnostics.empty:
        diagnostics.to_csv(OUT / "multistart_diagnostics.csv", index=False)
        diagnostics[diagnostics["selected"].astype(bool)].to_csv(
            OUT / "best_solution_gradient_report.csv", index=False
        )
    pd.DataFrame(parameter_boundary_rows(fits, group_names)).to_csv(
        OUT / "parameter_boundary_report.csv", index=False
    )

    fit_rows = []
    for fit in fits:
        params = fit["params"]
        xhat, u = predict_x(params, arr)
        eps = arr.x - xhat
        rmse = np.sqrt((eps**2).mean(axis=0))
        mae = np.abs(eps).mean(axis=0)
        for j, group in enumerate(group_names):
            fit_rows.append(
                {
                    "model": fit["model"],
                    "group": group,
                    "rmse_x": rmse[j],
                    "mae_x": mae[j],
                    "mean_x": arr.x[:, j].mean(),
                }
            )
        fit["xhat"] = xhat
        fit["u"] = u
    pd.DataFrame(fit_rows).to_csv(OUT / "model_fit_by_group.csv", index=False)

    param_rows = []
    for fit in fits:
        p = fit["params"]
        for j, group in enumerate(group_names):
            param_rows.append(
                {
                    "model": fit["model"],
                    "group": group,
                    "alpha": p["alpha"][j],
                    "beta": p["beta"][j],
                    "delta": p["delta"][j],
                    "tau": p["tau"][j],
                    "omega": p["omega"],
                    "kappa": p["kappa"],
                    "nll": fit["nll"],
                    "success": bool(fit["result"].success),
                    "message": str(fit["result"].message),
                }
            )
    pd.DataFrame(param_rows).to_csv(OUT / "parameter_estimates.csv", index=False)

    main = fits[1]
    p_mean = panel[panel["year"] == 2023][[f"p_{g}_model" for g in group_names]].mean().to_numpy(float)
    m_support_min = float(panel["m"].min())
    m_support_max = float(panel["m"].max())
    income_grid = np.array(
        sorted(
            set(
                list(np.quantile(panel["m"], [0.05, 0.25, 0.5, 0.75, 0.95]))
                + [10000, 20000, 30000, 50000, 80000, 120000, 160000, 200000]
            )
        )
    )
    el_rows = []
    exp_el_rows = []
    price_m_rows = []
    price_h_rows = []
    consistency_rows = []
    for m in income_grid:
        try:
            eta, xhat, u, phi = elasticity_for_point(p_mean, float(m), main["params"])
            mar, hic, eta_p, budget_shares, _ = price_elasticities_for_point(p_mean, float(m), main["params"])
        except Exception:
            continue
        for j, group in enumerate(group_names):
            budget_share = p_mean[j] * xhat[j] / m
            el_rows.append(
                {
                    "income": m,
                    "group": group,
                    "eta": eta[j],
                    "quantity_2000kcal_elasticity": eta[j],
                    "expenditure_elasticity": eta[j],
                    "budget_share_elasticity": eta[j] - 1,
                    "xhat": xhat[j],
                    "budget_share": budget_share,
                    "u": u,
                    "phi": phi[j],
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
            )
            exp_el_rows.append(
                {
                    "income": m,
                    "group": group,
                    "quantity_2000kcal_elasticity": eta[j],
                    "expenditure_elasticity": eta[j],
                    "budget_share_elasticity": eta[j] - 1,
                    "budget_share": budget_share,
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
            )
        for i, group_i in enumerate(group_names):
            for j, group_j in enumerate(group_names):
                base = {
                    "income": m,
                    "demand_group": group_i,
                    "price_group": group_j,
                    "is_own_price": group_i == group_j,
                    "budget_share_demand_group": budget_shares[i],
                    "budget_share_price_group": budget_shares[j],
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
                price_m_rows.append({**base, "elasticity": mar[i, j]})
                price_h_rows.append({**base, "elasticity": hic[i, j]})
        consistency_rows.append(
            elasticity_consistency_row(
                "income_grid",
                float(m),
                group_names,
                mar,
                hic,
                eta_p,
                budget_shares,
            )
        )
        food_eta = float(np.average(eta[:-1], weights=xhat[:-1]))
        food_exp_eta = float(np.average(eta[:-1], weights=p_mean[:-1] * xhat[:-1]))
        animal_idx = [group_names.index("pork"), group_names.index("meatother"), group_names.index("dairyegg")]
        plant_idx = [group_names.index("grain"), group_names.index("oil"), group_names.index("vegfruit")]
        aggregates = [
            ("all_food", list(range(len(group_names) - 1))),
            ("plant_food", plant_idx),
            ("animal_food", animal_idx),
        ]
        for agg_name, idx in aggregates:
            q_eta = float(np.average(eta[idx], weights=xhat[idx]))
            e_eta = float(np.average(eta[idx], weights=p_mean[idx] * xhat[idx]))
            bshare = float(np.dot(p_mean[idx], xhat[idx]) / m)
            el_rows.append(
                {
                    "income": m,
                    "group": agg_name,
                    "eta": q_eta if agg_name != "all_food" else food_eta,
                    "quantity_2000kcal_elasticity": q_eta if agg_name != "all_food" else food_eta,
                    "expenditure_elasticity": e_eta if agg_name != "all_food" else food_exp_eta,
                    "budget_share_elasticity": (e_eta if agg_name != "all_food" else food_exp_eta) - 1,
                    "xhat": xhat[idx].sum(),
                    "budget_share": bshare,
                    "u": u,
                    "phi": np.nan,
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
            )
            exp_el_rows.append(
                {
                    "income": m,
                    "group": agg_name,
                    "quantity_2000kcal_elasticity": q_eta if agg_name != "all_food" else food_eta,
                    "expenditure_elasticity": e_eta if agg_name != "all_food" else food_exp_eta,
                    "budget_share_elasticity": (e_eta if agg_name != "all_food" else food_exp_eta) - 1,
                    "budget_share": bshare,
                    "support_flag": support_flag(float(m), m_support_min, m_support_max),
                }
            )
    pd.DataFrame(el_rows).to_csv(OUT / "elasticity_income_grid.csv", index=False)
    pd.DataFrame(exp_el_rows).to_csv(OUT / "elasticity_expenditure_grid.csv", index=False)
    pd.DataFrame(price_m_rows).to_csv(OUT / "elasticity_price_marshallian_grid.csv", index=False)
    pd.DataFrame(price_h_rows).to_csv(OUT / "elasticity_price_hicksian_grid.csv", index=False)
    pd.DataFrame(consistency_rows).to_csv(OUT / "elasticity_consistency_tests.csv", index=False)

    obs_el_rows = []
    for r in range(arr.x.shape[0]):
        eta, xhat, u, phi = elasticity_for_point(arr.p[r], arr.m[r], main["params"])
        for j, group in enumerate(group_names):
            obs_el_rows.append(
                {
                    "obs_id": arr.obs_ids[r],
                    "province": arr.provinces[r],
                    "year": arr.years[r],
                    "group": group,
                    "eta": eta[j],
                    "quantity_2000kcal_elasticity": eta[j],
                    "expenditure_elasticity": eta[j],
                    "budget_share_elasticity": eta[j] - 1,
                    "xhat": xhat[j],
                    "observed_x": arr.x[r, j],
                    "u": u,
                    "support_flag": "in_support",
                }
            )
    pd.DataFrame(obs_el_rows).to_csv(OUT / "elasticity_observed_points.csv", index=False)

    prediction = build_projection(panel, main["params"], nutrition)
    prediction["projection_group"].to_csv(OUT / "projection_group_2030_2035_2050.csv", index=False)
    prediction["projection_items"].to_csv(OUT / "projection_item_feed_2030_2035_2050.csv", index=False)
    prediction["projection_path"].to_csv(OUT / "projection_province_path.csv", index=False)
    prediction["projection_growth_path"].to_csv(OUT / "projection_growth_path.csv", index=False)
    write_method_reports(panel, prediction)

    manifest = {
        "models": [
            {
                "model": fit["model"],
                "nll": fit["nll"],
                "success": bool(fit["result"].success),
                "message": str(fit["result"].message),
            }
            for fit in fits
        ],
        "n_obs": int(arr.x.shape[0]),
        "n_goods": int(arr.x.shape[1]),
        "groups": group_names,
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def group_item_shares(panel_base: pd.DataFrame, nutrition: pd.DataFrame) -> pd.DataFrame:
    # Rebuild item-level 2023 shares from the original data for projection allocation.
    data = pd.read_stata(ROOT / "ProvinceData" / "workdata" / "data.dta")
    data = data[data["year"] == 2023].copy()
    _, grain_kcal = read_grain_weights(nutrition)
    kcal_lookup = dict(zip(nutrition["code"], nutrition["kcal_per_kg_as_purchased"]))
    kcal_lookup["GRAIN"] = grain_kcal
    kcal_lookup["OIL"] = float(
        nutrition.loc[nutrition["code"].isin(["SOYO", "RAPO", "GRDO"]), "kcal_per_kg_as_purchased"].mean()
    )
    rows = []
    for item, spec in FOOD_ITEMS.items():
        group = next(g for g, items in GROUPS.items() if item in items)
        kcal_kg = kcal_lookup[spec["code"]]
        tmp = data[["province", "provincechn"]].copy()
        tmp["item"] = item
        tmp["group"] = group
        tmp["kg"] = numeric(data[spec["q"]])
        tmp["kcal"] = tmp["kg"] * kcal_kg
        tmp["kcal_per_kg"] = kcal_kg
        rows.append(tmp)
    out = pd.concat(rows, ignore_index=True)
    totals = out.groupby(["province", "group"], as_index=False)["kcal"].sum().rename(columns={"kcal": "group_kcal"})
    out = out.merge(totals, on=["province", "group"], how="left")
    out["kcal_share"] = out["kcal"] / out["group_kcal"]
    return out


def build_projection(panel: pd.DataFrame, params: dict[str, np.ndarray | float], nutrition: pd.DataFrame) -> dict[str, pd.DataFrame]:
    group_names = list(GROUPS.keys())
    base = panel[panel["year"] == 2023].copy()
    forecast = read_forecast()
    population_projection = read_provincial_population_projection("SSP2")
    targets = [2030, 2035, 2050]
    forecast = forecast[forecast["year"].between(2025, 2050)].copy()
    population_targets = population_projection[population_projection["year"].isin(targets)].copy()
    pop_lookup = {
        (int(r.province), int(r.year)): float(r.population_10k)
        for r in population_targets.itertuples()
    }
    pop_total_lookup = population_targets.groupby("year")["population_10k"].sum().to_dict()

    # The forecast file starts in 2025. Use the first available growth rate as a
    # 2024 bridge and record that assumption explicitly.
    first_growth = float(forecast.loc[forecast["year"] == forecast["year"].min(), "gdp_growth_pct"].iloc[0]) / 100
    growth = {2024: first_growth}
    growth.update({int(r.year): float(r.gdp_growth_pct) / 100 for r in forecast.itertuples()})

    national_m = float(np.average(base["m"], weights=base["population_10k"]))
    national_m_path = {}
    m_nat = national_m
    for year in range(2024, 2051):
        m_nat *= 1 + growth.get(year, 0.0)
        national_m_path[year] = m_nat

    future_rows = []
    growth_rows = []
    for _, row in base.iterrows():
        m = float(row["m"])
        for year in range(2024, 2051):
            gap = math.log(max(national_m_path[year], 1e-9)) - math.log(max(m, 1e-9))
            convergence_adjustment = float(np.clip(0.02 * gap, -0.015, 0.015))
            income_growth = growth.get(year, 0.0) + convergence_adjustment
            m *= 1 + income_growth
            growth_rows.append(
                {
                    "province": int(row["province"]),
                    "provincechn": row["provincechn"],
                    "year": year,
                    "national_growth_rate_used": growth.get(year, 0.0),
                    "province_income_growth_rate_used": income_growth,
                    "convergence_adjustment": convergence_adjustment,
                    "income_growth_source": "bridge_first_available_forecast_plus_convergence"
                    if year == 2024
                    else "national_forecast_plus_convergence",
                    "population_share_source": "chen_guo_wang_2020_ssp2_provincial_projection",
                    "population_scenario": "SSP2",
                    "population_projection_source": POPULATION_PROJECTION_SOURCE,
                }
            )
            if year in targets:
                pop = pop_lookup.get((int(row["province"]), year), np.nan)
                total_pop = pop_total_lookup.get(year, np.nan)
                pop_share = pop / total_pop if total_pop and not pd.isna(pop) else np.nan
                future_rows.append(
                    {
                        "province": int(row["province"]),
                        "provincechn": row["provincechn"],
                        "year": year,
                        "m": m,
                        "population_10k": pop,
                        "income_support_flag": support_flag(m, float(panel["m"].min()), float(panel["m"].max())),
                        "population_share_projected": pop_share,
                        "population_share_source": "chen_guo_wang_2020_ssp2_provincial_projection",
                        "population_scenario": "SSP2",
                        "population_projection_source": POPULATION_PROJECTION_SOURCE,
                        **{f"p_{g}_model": row[f"p_{g}_model"] for g in group_names},
                    }
                )
    growth_path = pd.DataFrame(growth_rows)
    future = pd.DataFrame(future_rows)
    arr = ModelArrays(
        obs_ids=(future["province"].astype(str) + "_" + future["year"].astype(str)).to_numpy(),
        provinces=future["province"].to_numpy(int),
        years=future["year"].to_numpy(int),
        group_names=group_names,
        x=np.zeros((future.shape[0], len(group_names))),
        p=future[[f"p_{g}_model" for g in group_names]].to_numpy(float),
        m=future["m"].to_numpy(float),
    )
    xhat, u = predict_x(params, arr)
    if xhat is None:
        raise ValueError("Projection failed to solve.")
    for j, group in enumerate(group_names):
        future[f"xhat_{group}"] = xhat[:, j]
        if group == "nonfood":
            future[f"daily_kcal_{group}"] = np.nan
            future[f"annual_kcal_total_{group}"] = np.nan
        else:
            future[f"daily_kcal_{group}"] = xhat[:, j] * 2000
            future[f"annual_kcal_total_{group}"] = xhat[:, j] * 2000 * 365 * future["population_10k"] * 10000
    future["u"] = u

    rows = []
    for _, row in future.iterrows():
        for group in group_names:
            rows.append(
                {
                    "province": row["province"],
                    "provincechn": row["provincechn"],
                    "year": row["year"],
                    "group": group,
                    "xhat_per_cap": row[f"xhat_{group}"],
                    "daily_kcal_per_cap": row[f"daily_kcal_{group}"],
                    "annual_kcal_total": row[f"annual_kcal_total_{group}"],
                    "population_10k": row["population_10k"],
                    "m": row["m"],
                    "income_support_flag": row["income_support_flag"],
                    "population_share_projected": row["population_share_projected"],
                    "population_share_source": row["population_share_source"],
                    "population_scenario": row["population_scenario"],
                    "population_projection_source": row["population_projection_source"],
                }
            )
    group_proj = pd.DataFrame(rows)
    national = group_proj.groupby(["year", "group"], as_index=False).agg(
        daily_kcal_per_cap_weighted=("daily_kcal_per_cap", lambda s: np.nan),
        annual_kcal_total=("annual_kcal_total", lambda s: s.sum(min_count=1)),
        xhat_per_cap_weighted=("xhat_per_cap", lambda s: np.nan),
        population_10k=("population_10k", "sum"),
        m_mean=("m", "mean"),
        population_scenario=("population_scenario", "first"),
        population_projection_source=("population_projection_source", "first"),
    )
    # Recompute weighted daily kcal and model quantity explicitly.
    national_weighted = []
    for (year, group), tmp in group_proj.groupby(["year", "group"]):
        w = tmp["population_10k"].to_numpy(float)
        kcal = tmp["daily_kcal_per_cap"].to_numpy(float)
        xidx = tmp["xhat_per_cap"].to_numpy(float)
        national_weighted.append(
            {
                "year": year,
                "group": group,
                "daily_kcal_per_cap_weighted": np.nan if np.all(pd.isna(kcal)) else float(np.average(kcal[~pd.isna(kcal)], weights=w[~pd.isna(kcal)])),
                "xhat_per_cap_weighted": float(np.average(xidx, weights=w)),
            }
        )
    nw = pd.DataFrame(national_weighted)
    national = national.drop(columns=["daily_kcal_per_cap_weighted", "xhat_per_cap_weighted"]).merge(nw, on=["year", "group"])

    shares = group_item_shares(panel, nutrition)
    item_rows = []
    for _, row in future.iterrows():
        pshares = shares[shares["province"] == row["province"]]
        for _, sh in pshares.iterrows():
            if sh["item"] not in FEED_COEFF:
                continue
            group_kcal_day = row[f"daily_kcal_{sh['group']}"]
            item_kcal_day = group_kcal_day * sh["kcal_share"]
            kg_per_cap_year = item_kcal_day * 365 / sh["kcal_per_kg"]
            total_kg = kg_per_cap_year * row["population_10k"] * 10000
            feed_coeff = FEED_COEFF.get(sh["item"], 0.0)
            cereal_share = FEED_CEREAL_SHARE.get(sh["item"], 1.0)
            feed = total_kg * feed_coeff * cereal_share
            item_rows.append(
                {
                    "province": row["province"],
                    "provincechn": row["provincechn"],
                    "year": row["year"],
                    "group": sh["group"],
                    "item": sh["item"],
                    "kg_per_cap_year": kg_per_cap_year,
                    "total_kg": total_kg,
                    "feed_kg_per_kg_product": feed_coeff,
                    "feed_cereal_share": cereal_share,
                    "feed_grain_kg": feed,
                    "feed_coefficient_source": "user_supplied_feed_grain_equivalent_coefficients",
                }
            )
    items = pd.DataFrame(item_rows)
    feed_nat = items.groupby(["year", "item"], as_index=False).agg(
        total_kg=("total_kg", "sum"),
        feed_kg_per_kg_product=("feed_kg_per_kg_product", "first"),
        feed_cereal_share=("feed_cereal_share", "first"),
        feed_grain_kg=("feed_grain_kg", "sum"),
        feed_coefficient_source=("feed_coefficient_source", "first"),
    )
    return {
        "projection_group": national,
        "projection_items": feed_nat,
        "projection_path": future,
        "projection_growth_path": growth_path,
    }


def markdown_table(df: pd.DataFrame, digits: int = 6) -> str:
    if df.empty:
        return "_No rows._"
    tmp = df.copy()
    for col in tmp.select_dtypes(include=[np.number]).columns:
        tmp[col] = tmp[col].map(lambda x: "" if pd.isna(x) else f"{x:.{digits}g}")
    tmp = tmp.fillna("").astype(str)
    headers = [str(col) for col in tmp.columns]
    rows = tmp.values.tolist()
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def write_method_reports(panel: pd.DataFrame, prediction: dict[str, pd.DataFrame]) -> None:
    budget_error = panel["m"] - panel["covered_food_exp"] - panel["nonfood_exp"]
    quality_lines = [
        "# 数据质量与口径核查",
        "",
        "## 预算恒等式",
        "",
        f"- 最大绝对预算残差：{float(np.nanmax(np.abs(budget_error))):.6g}",
        f"- 覆盖食品支出份额均值：{float(panel['covered_food_budget_share'].mean()):.6g}",
        f"- 覆盖食品每日 kcal 均值：{float(panel['covered_daily_kcal'].mean()):.6g}",
        f"- 覆盖食品每日 kcal 最小/最大：{float(panel['covered_daily_kcal'].min()):.6g} / {float(panel['covered_daily_kcal'].max()):.6g}",
        "",
        "## 价格与金额口径",
        "",
        "- 主估计使用 2023 年实际价口径：总支出用省级总 CPI 平减，食品价格用省级食品 CPI 平减。",
        "- 主估计非覆盖支出价格使用全国非食品 CPI，2023=100；省级反推非食品 CPI 仅作稳健性。",
        "- `nonfood` 在模型内部保留为兼容变量名，经济含义为“其他/未覆盖支出”，包含未覆盖食品、烟酒、在外就餐和真正非食品。",
        "",
        "## 样本支撑",
        "",
        f"- 实际消费支出 m 的样本范围：{float(panel['m'].min()):.6g} 到 {float(panel['m'].max()):.6g}。",
        "- 弹性和预测表中的 `support_flag` / `income_support_flag` 标明样本支撑内估计或外推。",
    ]
    (OUT / "data_quality_report.md").write_text("\n".join(quality_lines), encoding="utf-8")

    if (DATA_OUT / "province_cpi_indices.csv").exists():
        cpi = pd.read_csv(DATA_OUT / "province_cpi_indices.csv")
        if "nonfood_price_source" in cpi.columns:
            source_counts = cpi["nonfood_price_source"].value_counts(dropna=False).reset_index()
            source_counts.columns = ["source", "n_rows"]
        else:
            source_counts = pd.DataFrame()
        cpi_lines = [
            "# 非食品 CPI 质量报告",
            "",
            "- 主估计使用全国非食品 CPI，避免用被解释变量相关的食品支出份额反推主价格。",
            "- 稳健性口径使用省级总 CPI、食品 CPI 与食品支出份额反推省级非食品 CPI，标记为 approximate。",
            "- 全国非食品 CPI 的 2015 年指数由 2016 年同比向前反推。",
            "",
            "## 省级反推来源计数",
            "",
            markdown_table(source_counts) if not source_counts.empty else "_未生成来源计数。_",
        ]
        (OUT / "nonfood_cpi_quality_report.md").write_text("\n".join(cpi_lines), encoding="utf-8")

    feed_lines = [
        "# 饲料粮需求方法说明",
        "",
        "- 本轮 `projection_item_feed_2030_2035_2050.csv` 只输出动物产品 item。",
        "- 用户提供的系数被解释为“饲料粮等价 kg / kg 产品”：猪肉 3.88，禽肉 3.10，蛋 2.46，奶 0.62，水产品 1.35，牛肉和羊肉 9.80。",
        "- 代码保留 `feed_cereal_share` 字段；当前因输入已经是饲料粮系数，设为 1.0。若后续换成总饲料系数，应补充各产品谷物占比。",
        "- 产品拆分使用 2023 年各省组内动物产品 kcal 份额，并固定到预测期。",
    ]
    (OUT / "feed_demand_method.md").write_text("\n".join(feed_lines), encoding="utf-8")

    audit_lines = [
        "# CODE_AUDIT_FIX_REPORT",
        "",
        "| 审查项 | 本轮处理 | 输出文件 | 剩余限制 |",
        "| --- | --- | --- | --- |",
        "| A1/OOS 指标广播 | 已改为按 variant/model/split/group 输出；追加脚本会重跑 AIDADS 与 MAIDADS | `oos_fit_by_group.csv`, `oos_predictions.csv` | 朴素基线、留一省/留一区域仍待增强 |",
        "| A2/bootstrap 过少 | 追加正式规模 `run_formal_bootstrap.py`，记录省份簇 bootstrap 成功率与区间 | `bootstrap_*`, `FormalBootstrap/*` | 若模型或数据变更，需重新跑正式规模 bootstrap |",
        "| A3/LR χ² 不合法 | 删除把 χ² p 作为最终证据的表述，追加 cluster bootstrap LR；普通 χ² p 不报告 | `lr_test_chi2_and_bootstrap.csv` | 严格 parametric-null bootstrap 仍可增强 |",
        "| A4/价格口径 | 主估计改为 2023 实际价；食品价格和总支出分别用食品/总 CPI 平减 | `maidads6_panel.csv` | 缺分项食品 CPI |",
        "| A5/省级预测路径 | 人口路径改用 Chen et al. (2020) Sci Data 的 SSP2 省级人口预测；收入仍用全国增长率加省份收敛情景 | `projection_growth_path.csv`, `Data/output/provincial_population_projection_ssp2.csv` | 需补正式分省收入、城镇化和年龄结构预测 |",
        "| A6/价格弹性与一致性 | 新增 Marshallian/Hicksian 价格弹性和理论一致性误差表 | `elasticity_price_*`, `elasticity_consistency_tests.csv` | 解析式(7)(8)单元测试仍可进一步补强 |",
        "| B3/饲料粮 | 只输出动物产品，并保留 feed_cereal_share 字段 | `feed_demand_method.md` | 若系数为总饲料而非饲料粮，需补谷物占比 |",
        "| B4/未覆盖食品 | 把展示标签改为其他/未覆盖支出，并写入口径说明 | `data_quality_report.md` | 需外部总热量/FAOSTAT 对账 |",
        "| B5/grain kcal | 马铃薯 /5 只保留为粮食当量权重，热量按实际 kcal/kg 加权 | `grain_weights_processed.csv` | 仍缺分省主粮细类结构 |",
    ]
    (OUT / "CODE_AUDIT_FIX_REPORT.md").write_text("\n".join(audit_lines), encoding="utf-8")


def write_summary(manifest: dict) -> None:
    params = pd.read_csv(OUT / "parameter_estimates.csv")
    fit = pd.read_csv(OUT / "model_fit_by_group.csv")
    elast = pd.read_csv(OUT / "elasticity_income_grid.csv")
    price_m = pd.read_csv(OUT / "elasticity_price_marshallian_grid.csv")
    consistency = pd.read_csv(OUT / "elasticity_consistency_tests.csv")
    proj = pd.read_csv(OUT / "projection_group_2030_2035_2050.csv")
    feed = pd.read_csv(OUT / "projection_item_feed_2030_2035_2050.csv")
    lines = []
    lines.append("# 中国省级 MAIDADS 估计结果总览")
    lines.append("")
    lines.append("## 一、运行状态")
    lines.append("")
    lines.append(f"- 样本：{manifest['n_obs']} 个省-年观测，{manifest['n_goods']} 个消费组。")
    lines.append(f"- 消费组：{', '.join(manifest['groups'])}。")
    for m in manifest["models"]:
        lines.append(f"- {m['model']}: nll={m['nll']:.3f}, success={m['success']}, message={m['message']}")
    lines.append("")
    lines.append("## 二、核心数据口径")
    lines.append("")
    lines.append("- 食物数量统一换算为每日每人 2000 kcal 的数量单位；非食品为支出余额除以价格指数后的数量指数。")
    lines.append("- 主估计采用 2023 年实际价口径：总支出用省级总 CPI 平减，食品价格用省级食品 CPI 平减，保证 `price * quantity = real expenditure`。")
    lines.append("- 营养换算使用 `营养成分表.csv`，先乘以可食用部分；能量缺失或为 0 时用 `4*蛋白质 + 9*脂肪 + 4*碳水化合物` 补算。")
    lines.append("- 主粮聚合权重来自 `粮食细类消费.csv`；大豆和马铃薯计入粮食。马铃薯 `/5` 只保留为粮食当量权重，热量换算使用实际 kcal/kg。")
    lines.append("- 预测使用全国收入增长路径作为外生基准，并加入省份收入收敛情景；省级人口路径使用 Chen et al. (2020) Sci Data 的 SSP2 省级人口预测。")
    lines.append("- 主估计非覆盖支出价格使用全国非食品 CPI；省级反推非食品 CPI 只作为稳健性。")
    lines.append("")
    lines.append("## 三、MAIDADS 参数估计")
    lines.append(markdown_table(params[params["model"] == "MAIDADS_sat"]))
    lines.append("")
    lines.append("## 四、分组拟合误差")
    lines.append(markdown_table(fit))
    lines.append("")
    lines.append("## 五、收入弹性")
    lines.append("")
    lines.append("收入弹性使用同一 MAIDADS 预测函数做中心差分计算，避免解析导数在当前尺度下不稳定。")
    selected = elast[elast["income"].isin(sorted(elast["income"].unique())[:: max(1, len(elast["income"].unique()) // 8)])]
    lines.append(markdown_table(selected.pivot_table(index="group", columns="income", values="eta").reset_index()))
    lines.append("")
    lines.append("## 六、价格弹性与理论一致性")
    lines.append("")
    own_price = price_m[price_m["is_own_price"].astype(bool)].copy()
    lines.append("Marshallian 自价格弹性如下；MAIDADS 的价格弹性由 LES 型预算结构机械决定，不作为本文方法贡献。")
    lines.append(markdown_table(own_price.pivot_table(index="demand_group", columns="income", values="elasticity").reset_index()))
    lines.append("")
    lines.append("理论一致性误差摘要：")
    lines.append(markdown_table(consistency.describe(include="all").reset_index()))
    lines.append("")
    lines.append("## 七、全国加权预测：每日每人 kcal")
    lines.append(markdown_table(proj.pivot_table(index="group", columns="year", values="daily_kcal_per_cap_weighted").reset_index()))
    lines.append("")
    lines.append("非食品是模型数量指数，不是 kcal；因此非食品的每日 kcal 项留空。")
    lines.append("")
    lines.append("## 八、动物产品对应饲料粮需求：百万吨")
    feed2 = feed.copy()
    feed2["feed_grain_million_ton"] = feed2["feed_grain_kg"] / 1e9
    lines.append(markdown_table(feed2.pivot_table(index="item", columns="year", values="feed_grain_million_ton").reset_index()))
    lines.append("")
    lines.append("## 九、主要结果文件")
    lines.append("")
    lines.append("- `parameter_estimates.csv`：AIDADS 与 MAIDADS 的参数估计。")
    lines.append("- `model_fit_by_group.csv`：分消费组 RMSE/MAE 拟合误差。")
    lines.append("- `elasticity_income_grid.csv`：不同收入水平的收入弹性。")
    lines.append("- `elasticity_expenditure_grid.csv`：数量/支出/预算份额三种支出弹性口径。")
    lines.append("- `elasticity_price_marshallian_grid.csv`、`elasticity_price_hicksian_grid.csv`：价格弹性矩阵。")
    lines.append("- `elasticity_consistency_tests.csv`：加总、齐次性与 Slutsky 对称性误差。")
    lines.append("- `elasticity_observed_points.csv`：每个省-年观测点的收入弹性。")
    lines.append("- `projection_group_2030_2035_2050.csv`：2030/2035/2050 分组全国加权预测。")
    lines.append("- `projection_item_feed_2030_2035_2050.csv`：动物产品总量和饲料粮需求预测。")
    lines.append("- `projection_province_path.csv`：省级 2030/2035/2050 预测路径。")
    lines.append("- `projection_growth_path.csv`：预测收入增长路径和 2024 桥接假设。")
    lines.append("- `multistart_diagnostics.csv`、`parameter_boundary_report.csv`、`best_solution_gradient_report.csv`：估计收敛与边界诊断。")
    lines.append("- `data_quality_report.md`、`nonfood_cpi_quality_report.md`、`feed_demand_method.md`、`CODE_AUDIT_FIX_REPORT.md`：审计和方法说明。")
    lines.append("")
    lines.append("## 十、重要限制")
    lines.append("")
    lines.append("- 本机 PATH 中没有 `gams`，因此使用 Python Track-P 复现 MAIDADS，而不是原 GAMS 程序。")
    lines.append("- 本轮预测已接入 Chen et al. (2020) SSP2 省级人口预测；收入、城镇化和年龄结构路径仍需进一步补充。")
    lines.append("- 2024 收入增长因预测文件从 2025 年开始，使用首个可得预测增速桥接；该假设已写入 `projection_growth_path.csv`。")
    lines.append("- 省级非食品 CPI 仍为由总 CPI、食品 CPI 与食品支出份额反推的近似值；本轮已把它降为稳健性口径，若后续取得直接省级非食品 CPI，应替换该口径。")
    (OUT / "RESULTS_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ensure_dirs()
    panel, _, nutrition = build_model_data()
    arr = panel_to_arrays(panel)
    fits = fit_model(arr)
    manifest = build_results(panel, arr, fits, nutrition)
    write_summary(manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

```
