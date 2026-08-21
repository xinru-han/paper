#!/usr/bin/env python3
"""Build comparison tables and the Chinese replication summary."""

from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "output"
INPUT = PROJECT / "input"
GOODS = ["corn", "sorghum", "cassava", "oats", "barley"]
ZH = {"corn": "玉米", "sorghum": "高粱", "cassava": "木薯干", "oats": "燕麦", "barley": "大麦"}


def reference(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["demand_good_name"] = df["demand_good"].map(lambda x: GOODS[int(x) - 1])
    df["shock_good_name"] = df["shock_good"].map(
        lambda x: "" if int(x) == 0 else GOODS[int(x) - 1]
    )
    return df


def build_comparison() -> pd.DataFrame:
    old = pd.read_csv(INPUT / "old_r_core_results.csv")
    old["shock_good"] = old["shock_good"].fillna("")
    same_parts = []
    for model, spec in [("AIDS", "aids"), ("QUAIDS", "quaids")]:
        d = reference(OUT / f"reference_nlsur_cf_{spec}.csv")
        d = d.rename(columns={"elasticity_type": "metric", "elasticity": "stata_same_model_sy"})
        d["model"] = model
        same_parts.append(
            d[["model", "metric", "demand_good_name", "shock_good_name", "stata_same_model_sy"]]
        )
    same = pd.concat(same_parts, ignore_index=True)
    same = same.rename(columns={"demand_good_name": "demand_good", "shock_good_name": "shock_good"})

    preferred = reference(OUT / "reference_nlsur_cf_no_sy_easi3.csv")
    preferred = preferred[[
        "elasticity_type", "demand_good_name", "shock_good_name", "elasticity"
    ]].rename(
        columns={
            "elasticity_type": "metric",
            "demand_good_name": "demand_good",
            "shock_good_name": "shock_good",
            "elasticity": "stata_preferred_easi3_no_sy",
        }
    )

    out = old.rename(columns={"value": "old_r_value", "model": "old_r_model"})
    out = out.merge(
        same,
        left_on=["old_r_model", "metric", "demand_good", "shock_good"],
        right_on=["model", "metric", "demand_good", "shock_good"],
        how="left",
    ).drop(columns="model")
    out = out.merge(preferred, on=["metric", "demand_good", "shock_good"], how="left")
    out.loc[out["old_r_model"].ne("QUAIDS"), "stata_preferred_easi3_no_sy"] = pd.NA
    out["stata_minus_r_same_model"] = out["stata_same_model_sy"] - out["old_r_value"]
    out["stata_preferred_minus_r_quaids"] = out["stata_preferred_easi3_no_sy"] - out["old_r_value"]
    out["demand_good_zh"] = out["demand_good"].map(ZH)
    out["shock_good_zh"] = out["shock_good"].map(ZH).fillna("")
    out.to_csv(OUT / "r_vs_stata_core_comparison.csv", index=False)
    return out


def build_model_comparison() -> pd.DataFrame:
    sy = pd.read_csv(OUT / "model_selection_nlsur_cf.csv")
    sy.insert(0, "design", "SY + Stata FE control function")
    no_sy = pd.read_csv(OUT / "model_selection_nlsur_cf_no_sy.csv")
    no_sy.insert(0, "design", "No SY + Stata FE control function")
    result = pd.concat([sy, no_sy], ignore_index=True)
    result.to_csv(OUT / "stata_model_comparison_all.csv", index=False)
    return result


def key_elasticities(path: Path, design: str) -> pd.DataFrame:
    df = reference(path)
    own = df.loc[
        df["elasticity_type"].eq("expenditure")
        | df["demand_good"].eq(df["shock_good"])
    ].copy()
    own.insert(0, "design", design)
    own["demand_good_zh"] = own["demand_good_name"].map(ZH)
    return own


def fmt(value: float, digits: int = 3) -> str:
    return "NA" if pd.isna(value) else f"{value:.{digits}f}"


def main() -> None:
    comparison = build_comparison()
    models = build_model_comparison()
    sy_key = key_elasticities(OUT / "reference_nlsur_cf_quaids.csv", "SY-QUAIDS baseline")
    easi_key = key_elasticities(OUT / "reference_nlsur_cf_no_sy_easi3.csv", "No-SY EASI(3) robustness")
    pd.concat([sy_key, easi_key], ignore_index=True).to_csv(
        OUT / "stata_key_reference_elasticities.csv", index=False
    )

    fs = pd.read_csv(OUT / "first_stage_stata.csv").iloc[0]
    sy_sel = models.loc[(models.design.str.startswith("SY")) & models.model.eq("quaids")].iloc[0]
    easi_sel = models.loc[(models.design.str.startswith("No SY")) & models.model.eq("easi") & models.order.eq(3)].iloc[0]
    sy_reg = pd.read_csv(OUT / "regularity_nlsur_cf_quaids_latent.csv").set_index("diagnostic")
    easi_reg = pd.read_csv(OUT / "regularity_nlsur_cf_no_sy_easi3_latent.csv").set_index("diagnostic")

    exp = sy_key.loc[sy_key.elasticity_type.eq("expenditure")]
    marsh = sy_key.loc[sy_key.elasticity_type.eq("marshallian")]
    hicks = sy_key.loc[sy_key.elasticity_type.eq("hicksian")]
    lines = [
        "# Stata AIDS/QUAIDS/EASI 复现与 R 结果比较",
        "",
        "## 结论",
        "",
        "- 样本为 634 个正进口预算省份-季度观测，五类商品顺序为玉米、高粱、木薯干、燕麦、大麦；大麦由加总约束恢复。",
        f"- Stata 双向固定效应第一阶段复现得到传统 F={fs.F_conventional:.3f}、省级聚类 F={fs.F_cluster:.3f}，明显低于旧 R 文档报告的 88.83。",
        f"- 与旧 R 最可比的 SY+控制函数设计选择 QUAIDS：二次 Engel 项联合 p={sy_sel.Engel_order_p:.3g}，BIC={sy_sel.bic:.1f}。",
        f"- 去除 QUAIDS 中不显著的 SY 项后，三阶 EASI 在无 SY 家族中胜出：三阶项 p={easi_sel.Engel_order_p:.3g}，BIC={easi_sel.bic:.1f}。",
        "- 论文替换旧 R 数值时，以 Stata SY-QUAIDS 为基准；EASI(3) 无 SY 作为函数形式/零值处理稳健性。所有弹性均须注明是条件进口预算弹性。",
        "",
        "## Stata 基准弹性",
        "",
        "下表是在样本均值价格、支出和控制变量处计算的潜在（条件）弹性，与旧 R 的参考点口径最接近。",
        "",
        "| 商品 | 支出 | Marshallian 自价格 | Hicksian 自价格 |",
        "|---|---:|---:|---:|",
    ]
    for good in GOODS:
        lines.append(
            f"| {ZH[good]} | {fmt(exp.loc[exp.demand_good_name.eq(good), 'elasticity'].iloc[0])} "
            f"| {fmt(marsh.loc[marsh.demand_good_name.eq(good), 'elasticity'].iloc[0])} "
            f"| {fmt(hicks.loc[hicks.demand_good_name.eq(good), 'elasticity'].iloc[0])} |"
        )

    lines += [
        "",
        "## R 与 Stata 差异",
        "",
        "| 商品 | 指标 | 旧 R QUAIDS | Stata SY-QUAIDS | 差值 | Stata EASI(3) 无 SY |",
        "|---|---|---:|---:|---:|---:|",
    ]
    rquaids = comparison.loc[comparison.old_r_model.eq("QUAIDS")]
    for _, row in rquaids.iterrows():
        metric = {"expenditure": "支出", "marshallian": "Marshallian 自价格", "hicksian": "Hicksian 自价格"}[row.metric]
        lines.append(
            f"| {row.demand_good_zh} | {metric} | {fmt(row.old_r_value)} | "
            f"{fmt(row.stata_same_model_sy)} | {fmt(row.stata_minus_r_same_model)} | "
            f"{fmt(row.stata_preferred_easi3_no_sy)} |"
        )

    lines += [
        "",
        "差异不是软件舍入误差。Stata 使用 revision_2026 的 completed 质量调整价格、Stata 重估的 FE 控制函数、`fooddem` 自带的 SY probit 与省级聚类 VCE；旧 R 的选择方程、协方差和参考价格实现不同。",
        "",
        "## 检验与正则性",
        "",
        "- SY-QUAIDS 的二次 Engel 项强显著；SY 校正项联合 p=0.328；控制函数项联合 p=0.384。",
        "- 无 SY EASI(3) 的三阶 Engel 项 p=3.66e-5；控制函数项联合 p=0.083。",
        f"- SY-QUAIDS：加总误差={sy_reg.loc['adding_up_max_abs_error','value']:.1g}，Slutsky 对称误差={sy_reg.loc['slutsky_symmetry_max_abs_error','value']:.2g}，最大特征值={sy_reg.loc['slutsky_max_eigenvalue','value']:.2g}。",
        f"- 无 SY EASI(3)：加总误差={easi_reg.loc['adding_up_max_abs_error','value']:.1g}，Slutsky 对称误差={easi_reg.loc['slutsky_symmetry_max_abs_error','value']:.2g}，最大特征值={easi_reg.loc['slutsky_max_eigenvalue','value']:.2g}。",
        f"- 全样本五类潜在预测份额同时为正的比例仅为 {100*sy_reg.loc['positive_fitted_share_rate','value']:.1f}%（SY-QUAIDS）和 {100*easi_reg.loc['positive_fitted_share_rate','value']:.1f}%（无 SY EASI(3)）。因此只能声称局部正则，不能沿用旧 R 文档的全局正则表述。",
        "",
        "## 使用规则",
        "",
        "1. 论文主表和后续基准分析采用 `reference_nlsur_cf_quaids.csv` 及 `elasticities_nlsur_cf_quaids_latent.csv`。",
        "2. 政策或总体进口反应同时报告 `preferred_elasticities_nlsur_cf_unconditional.csv`，不要把潜在条件弹性解释成无条件进口弹性。",
        "3. EASI 稳健性采用 `reference_nlsur_cf_no_sy_easi3.csv`；SY-EASI(2) 返回 430，不能据此伪造连续阶数选择。",
        "4. 价格弹性只在 `minshare(.001)` 的共同内部支持上汇总，并同时报告 support_rate。",
        "5. 当前结果没有把未完成的两步 IV-GMM 当成估计结果；全部正式表来自收敛的 Stata NLSUR、聚类 VCE 与 Stata 后估计。",
    ]
    (PROJECT / "RESULTS_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote comparison tables and RESULTS_SUMMARY.md")


if __name__ == "__main__":
    main()
