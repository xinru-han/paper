from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "ProvinceMAIDADS"
RESULTS = PROJECT / "Results"
DATA_OUT = PROJECT / "Data" / "output"

DIAG = RESULTS / "Diagnostics"
ELAST = RESULTS / "Elasticities"
BOOT = RESULTS / "Bootstrap"
PROJ = RESULTS / "Projection"
OOS = RESULTS / "OOS"
PAPER_WORK = PROJECT / ".paper_work"


def ensure_dirs() -> None:
    for path in [DIAG, ELAST, BOOT, PROJ, OOS, PAPER_WORK]:
        path.mkdir(parents=True, exist_ok=True)


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def build_oos_summary() -> None:
    src = RESULTS / "oos_fit_by_group.csv"
    if not src.exists():
        return
    oos = pd.read_csv(src)
    oos["split"] = oos["train_years"].astype(str) + " -> " + oos["test_years"].astype(str)
    cols = [
        "variant",
        "model",
        "split",
        "train_years",
        "test_years",
        "group",
        "rmse_x",
        "mae_x",
        "mean_x",
        "relative_rmse",
        "n_test",
    ]
    oos[cols].to_csv(OOS / "oos_summary_by_model.csv", index=False)
    # Compatibility copies requested by the writing skill.
    copy_if_exists(src, OOS / "oos_fit_by_group.csv")
    copy_if_exists(RESULTS / "oos_predictions.csv", OOS / "oos_predictions_all_models.csv")


def build_diagnostics() -> None:
    mapping = {
        "multistart_diagnostics.csv": "multistart_diagnostics.csv",
        "best_solution_gradient_report.csv": "best_solution_gradient_report.csv",
        "lr_bootstrap_draws.csv": "lr_bootstrap_draws.csv",
    }
    for src_name, dst_name in mapping.items():
        copy_if_exists(RESULTS / src_name, DIAG / dst_name)

    boundary_src = RESULTS / "parameter_boundary_report.csv"
    if boundary_src.exists():
        boundary = pd.read_csv(boundary_src)
        boundary["fixed_by_restriction"] = boundary.get("imposed_by_saturation", False).astype(bool)
        near_lower = boundary.get("near_lower_boundary", False).astype(bool)
        near_upper = boundary.get("near_upper_boundary", False).astype(bool)
        boundary["estimated_on_boundary"] = (near_lower | near_upper) & (~boundary["fixed_by_restriction"])
        boundary.to_csv(DIAG / "parameter_boundary_report.csv", index=False)

    lr_src = RESULTS / "lr_test_chi2_and_bootstrap.csv"
    if lr_src.exists():
        lr = pd.read_csv(lr_src)
        out = pd.DataFrame()
        out["test"] = lr.get("test", pd.Series(["MAIDADS_vs_AIDADS"]))
        out["lr_observed"] = lr.get("observed_lr", pd.Series([np.nan]))
        out["df_naive"] = 7
        out["p_chi2_naive"] = np.nan
        out["p_bootstrap_cluster"] = lr.get("cluster_bootstrap_tail_probability", pd.Series([np.nan]))
        out["n_bootstrap"] = lr.get("bootstrap_reps", pd.Series([np.nan]))
        out["successful_reps"] = lr.get("successful_reps", pd.Series([np.nan]))
        out["convergence_rate"] = out["successful_reps"] / out["n_bootstrap"]
        out["status"] = np.where(out["n_bootstrap"] >= 500, "formal", "pilot_only")
        out["note"] = lr.get("note", pd.Series(["Cluster bootstrap; chi-square reference not used."]))
        out.to_csv(DIAG / "lr_test_chi2_and_bootstrap.csv", index=False)

    build_model_equation_tests()


def build_elasticity_package() -> None:
    for name in [
        "elasticity_income_grid.csv",
        "elasticity_expenditure_grid.csv",
        "elasticity_price_marshallian_grid.csv",
        "elasticity_price_hicksian_grid.csv",
        "elasticity_consistency_tests.csv",
        "elasticity_observed_points.csv",
    ]:
        copy_if_exists(RESULTS / name, ELAST / name)


def build_bootstrap_package() -> None:
    for name in [
        "bootstrap_draw_status.csv",
        "bootstrap_draw_metrics.csv",
        "bootstrap_key_ci.csv",
        "bootstrap_key_ci_success_only.csv",
        "bootstrap_parameter_ci.csv",
        "bootstrap_parameter_draws.csv",
    ]:
        copy_if_exists(RESULTS / name, BOOT / name)


def build_projection_decomposition() -> None:
    panel_path = DATA_OUT / "maidads6_panel.csv"
    proj_path = RESULTS / "projection_group_2030_2035_2050.csv"
    if not panel_path.exists() or not proj_path.exists():
        return
    panel = pd.read_csv(panel_path)
    proj = pd.read_csv(proj_path)
    base = panel[panel["year"].eq(2023)].copy()
    rows = []
    base_pop = float(base["population_10k"].sum())
    scenario_name = "ssp2_population_income_convergence"
    if "population_scenario" in proj.columns:
        scenarios = sorted(str(x) for x in proj["population_scenario"].dropna().unique())
        if scenarios:
            scenario_name = f"{scenarios[0].lower()}_population_income_convergence"
    for group in ["grain", "oil", "vegfruit", "pork", "meatother", "dairyegg"]:
        x_col = f"x_{group}"
        base_daily = float(np.average(base[x_col] * 2000, weights=base["population_10k"]))
        base_total = base_daily * 365 * base_pop * 10000
        for _, row in proj[proj["group"].eq(group)].iterrows():
            pop = float(row["population_10k"])
            full_total = float(row["annual_kcal_total"])
            population_only_total = base_daily * 365 * pop * 10000
            rows.append(
                {
                    "scenario": scenario_name,
                    "year": int(row["year"]),
                    "group": group,
                    "base_2023_daily_kcal_per_cap": base_daily,
                    "projection_daily_kcal_per_cap": row["daily_kcal_per_cap_weighted"],
                    "base_2023_total_kcal": base_total,
                    "population_only_total_kcal": population_only_total,
                    "full_total_kcal": full_total,
                    "population_contribution_kcal": population_only_total - base_total,
                    "per_cap_demand_contribution_kcal": full_total - population_only_total,
                    "total_change_kcal": full_total - base_total,
                }
            )
    pd.DataFrame(rows).to_csv(PROJ / "projection_decomposition_2030_2035_2050.csv", index=False)


def build_projection_package() -> None:
    for name in [
        "projection_group_2030_2035_2050.csv",
        "projection_item_feed_2030_2035_2050.csv",
        "projection_province_path.csv",
        "projection_growth_path.csv",
        "robustness_cpi_nonfood_projection_group_2030_2035_2050.csv",
        "robustness_cpi_nonfood_projection_item_feed_2030_2035_2050.csv",
    ]:
        copy_if_exists(RESULTS / name, PROJ / name)
    copy_if_exists(RESULTS / "feed_demand_method.md", PROJ / "feed_demand_method.md")
    build_projection_decomposition()


def build_nutrition_audit() -> None:
    nutrition_path = DATA_OUT / "nutrition_processed.csv"
    grain_path = DATA_OUT / "grain_weights_processed.csv"
    lines = [
        "# Nutrition Conversion Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    if nutrition_path.exists():
        nutrition = pd.read_csv(nutrition_path)
        lines += [
            "## Nutrition table",
            "",
            f"- Processed rows: {nutrition.shape[0]}",
            "- `kcal_per_kg_as_purchased = kcal_per_100g_edible * 10 * edible_share / 100`.",
            "- If reported energy is missing or zero, energy is reconstructed from protein, fat and carbohydrate.",
            f"- Non-positive kcal rows after processing: {int((nutrition['kcal_per_kg_as_purchased'] <= 0).sum())}",
            "",
        ]
    if grain_path.exists():
        grain = pd.read_csv(grain_path)
        potato_rows = grain[grain["code"].eq("POTA")]
        potato_note = "not present"
        if not potato_rows.empty:
            potato_note = (
                f"grain_equiv_weight={float(potato_rows['grain_equiv_weight'].iloc[0]):.6g}; "
                f"kcal_weight={float(potato_rows['kcal_weight'].iloc[0]):.6g}"
            )
        lines += [
            "## Grain aggregation",
            "",
            "- Grain-equivalent weights are retained for accounting, including potato divided by 5.",
            "- Calorie aggregation uses actual consumption-quantity weights and actual kcal/kg, not the potato /5 grain-equivalent conversion.",
            f"- Potato audit: {potato_note}.",
            f"- Sum of kcal weights: {float(grain['kcal_weight'].sum()):.12g}",
            f"- Sum of grain-equivalent weights: {float(grain['grain_equiv_weight'].sum()):.12g}",
            "",
        ]
    (DATA_OUT / "nutrition_conversion_audit.md").write_text("\n".join(lines), encoding="utf-8")


def build_model_equation_tests() -> None:
    lines = [
        "# Model Equation Tests",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    panel_path = DATA_OUT / "maidads6_panel.csv"
    if panel_path.exists():
        panel = pd.read_csv(panel_path)
        budget_error = panel["m"] - panel["covered_food_exp"] - panel["nonfood_exp"]
        lines += [
            "## Budget Identity",
            "",
            f"- Max absolute budget residual: {float(np.nanmax(np.abs(budget_error))):.8g}",
            f"- Mean covered food budget share: {float(panel['covered_food_budget_share'].mean()):.8g}",
            "",
        ]
    consistency_path = RESULTS / "elasticity_consistency_tests.csv"
    if consistency_path.exists():
        cons = pd.read_csv(consistency_path)
        cols = [c for c in cons.columns if c.startswith("max_abs") or c.endswith("_error")]
        lines += ["## Elasticity Consistency", ""]
        for col in cols:
            lines.append(f"- {col}: max={float(cons[col].abs().max()):.8g}")
        lines.append("")
    grad_path = RESULTS / "best_solution_gradient_report.csv"
    if grad_path.exists():
        grad = pd.read_csv(grad_path)
        lines += [
            "## Optimizer Diagnostics",
            "",
            f"- Selected rows: {grad.shape[0]}",
            f"- Max absolute gradient among selected rows: {float(grad['max_abs_gradient'].max()):.8g}",
            f"- Gradient norm among selected rows: {float(grad['grad_norm'].max()):.8g}",
            "",
        ]
    (DIAG / "model_equation_tests.md").write_text("\n".join(lines), encoding="utf-8")


def copy_fix_report() -> None:
    copy_if_exists(RESULTS / "CODE_AUDIT_FIX_REPORT.md", PROJECT / "CODE_AUDIT_FIX_REPORT.md")


def markdown_table(df: pd.DataFrame, digits: int = 3) -> str:
    if df is None or df.empty:
        return "_无可用记录。_"
    tmp = df.copy()
    tmp.columns = [str(c) for c in tmp.columns]
    for col in tmp.select_dtypes(include=[np.number]).columns:
        tmp[col] = tmp[col].map(lambda x: "" if pd.isna(x) else f"{x:.{digits}f}")
    tmp = tmp.fillna("").astype(str)
    lines = [
        "| " + " | ".join(tmp.columns) + " |",
        "| " + " | ".join(["---"] * len(tmp.columns)) + " |",
    ]
    for row in tmp.itertuples(index=False):
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def refresh_additional_results_summary() -> None:
    """Rewrite the additional-results note from the synchronized formal outputs."""
    lines: list[str] = [
        "# 追加处理与稳健性估计结果",
        "",
        "## 一、已补充内容",
        "",
        "- 主结果采用全国非食品 CPI；稳健性用食物支出份额近似反推出省级非食品 CPI。",
        "- 构造 `cpi_nonfood` 省级近似非食品价格口径并重新估计 AIDADS/MAIDADS。",
        "- 对每个 `variant × model` 分别用 2015-2020 年训练、2021-2023 年测试，以及 2015-2022 年训练、2023 年测试做样本外验证。",
    ]

    status_path = RESULTS / "bootstrap_draw_status.csv"
    if status_path.exists():
        status = pd.read_csv(status_path)
        success_count = int(status["success"].astype(bool).sum())
        total_count = int(status.shape[0])
        scale = "正式规模" if total_count >= 500 else "pilot"
        lines.append(
            f"- 做 {total_count} 次省份簇 bootstrap（{scale}），其中 {success_count} 次完全收敛；关键区间仅用完全收敛 draw 汇总。"
        )
    else:
        lines.append("- 尚未找到省份簇 bootstrap 状态表。")

    lr_path = RESULTS / "lr_test_chi2_and_bootstrap.csv"
    if lr_path.exists():
        lr = pd.read_csv(lr_path)
        if not lr.empty:
            lr_row = lr.iloc[0]
            lr_reps = int(lr_row.get("bootstrap_reps", lr_row.get("n_bootstrap", 0)))
            lr_success = int(lr_row.get("successful_reps", 0))
            lr_scale = "正式规模" if lr_reps >= 500 else "pilot"
            lines.append(
                f"- LR cluster bootstrap 已完成 {lr_reps} 次（{lr_scale}），其中 {lr_success} 次成功；普通 χ² p 值不作为有效推断。"
            )

    lines.append("")
    lines.append("## 二、CPI 非食品稳健性估计")
    manifest_path = RESULTS / "robustness_cpi_nonfood_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        robustness = pd.DataFrame(manifest.get("models", []))
        lines.append(markdown_table(robustness))
    else:
        lines.append("_未找到 CPI 非食品稳健性 manifest。_")

    lines.append("")
    lines.append("## 三、样本外验证")
    oos_path = RESULTS / "oos_fit_by_group.csv"
    lines.append(markdown_table(pd.read_csv(oos_path)) if oos_path.exists() else "_未找到样本外验证表。_")

    lines.append("")
    lines.append("## 四、模型比较")
    comparison_path = RESULTS / "model_comparison.csv"
    lines.append(markdown_table(pd.read_csv(comparison_path)) if comparison_path.exists() else "_未找到模型比较表。_")

    lines.append("")
    lines.append("## 五、LR cluster bootstrap")
    lines.append("")
    lines.append("普通 χ² p 值因 MAIDADS 在 AIDADS 原假设下存在不可识别 nuisance parameter，本轮不作为有效推断报告。")
    lines.append(markdown_table(pd.read_csv(lr_path)) if lr_path.exists() else "_未找到 LR bootstrap 摘要。_")

    lines.append("")
    lines.append("## 六、bootstrap 关键区间")
    ci_path = RESULTS / "bootstrap_key_ci.csv"
    if ci_path.exists():
        boot_ci = pd.read_csv(ci_path)
        key = boot_ci[
            (boot_ci["metric"].isin(["daily_kcal_per_cap_weighted", "feed_grain_million_ton"]))
            & (boot_ci["year"].isin([2050]))
        ].copy()
        lines.append(markdown_table(key))
    else:
        lines.append("_未找到 bootstrap 关键区间。_")

    lines.extend(
        [
            "",
            "## 七、输出文件",
            "",
            "- `province_cpi_indices.csv`：省级总/食品/近似非食品 CPI 与 2023=100 指数。",
            "- `robustness_cpi_nonfood_parameter_estimates.csv`：CPI 非食品价格口径参数。",
            "- `robustness_cpi_nonfood_fit_by_group.csv`：CPI 非食品价格口径拟合误差。",
            "- `robustness_cpi_nonfood_projection_group_2030_2035_2050.csv`：CPI 稳健预测。",
            "- `oos_fit_by_group.csv`、`oos_predictions.csv` 与 `Results/OOS/oos_predictions__*.csv`：按口径、模型、样本切分独立保存的样本外验证。",
            "- `bootstrap_key_ci.csv`、`bootstrap_parameter_ci.csv`、`bootstrap_draw_metrics.csv`：bootstrap 区间和抽样明细。",
            "- `lr_test_chi2_and_bootstrap.csv`、`lr_bootstrap_draws.csv`：LR 检验的 cluster bootstrap 摘要和抽样明细。",
            "",
            "## 八、仍需人工确认",
            "",
            "- 食品 CPI 三个文件是分段表，本脚本按年份拼接；请后续核对 2015 年以前文件是否确为同一食品分类口径。",
            "- 省级非食品 CPI 由总 CPI、食品 CPI、食物支出份额反推，是近似值；更理想的是直接拿到省级非食品 CPI。",
            "- 正式规模 bootstrap 与 LR cluster bootstrap 已完成；若模型选择推断成为论文核心，可追加 parametric-null LR bootstrap 稳健性。",
            "- 预测人口路径已改用 Chen et al. (2020) SSP2 省级人口预测；收入、城镇化和年龄结构路径仍需更正式的数据来源。",
        ]
    )
    (RESULTS / "ADDITIONAL_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def build_file_inventory() -> None:
    files = sorted(
        str(path.relative_to(PROJECT))
        for path in PROJECT.rglob("*")
        if path.is_file() and ".paper_work" not in path.parts
    )
    (PAPER_WORK / "file_inventory.txt").write_text("\n".join(files) + "\n", encoding="utf-8")


def write_manifest() -> None:
    manifest = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Prepare ProvinceMAIDADS result outputs for provincial-maidads-paper-writer gate checks and manuscript drafting.",
        "directories": {
            "diagnostics": str(DIAG.relative_to(PROJECT)),
            "elasticities": str(ELAST.relative_to(PROJECT)),
            "bootstrap": str(BOOT.relative_to(PROJECT)),
            "projection": str(PROJ.relative_to(PROJECT)),
            "oos": str(OOS.relative_to(PROJECT)),
        },
    }
    (PAPER_WORK / "paper_workflow_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    build_oos_summary()
    build_diagnostics()
    build_elasticity_package()
    build_bootstrap_package()
    build_projection_package()
    build_nutrition_audit()
    copy_fix_report()
    refresh_additional_results_summary()
    build_file_inventory()
    write_manifest()
    print(PROJECT / ".paper_work")


if __name__ == "__main__":
    main()
