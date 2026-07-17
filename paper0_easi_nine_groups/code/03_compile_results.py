#!/usr/bin/env python3
"""Compile labeled nine-group model comparisons and diagnostics."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/root/data/Paper/食物消费数据/paper0-EASI/easi_nine_groups")
OUT = ROOT / "outputs"
GROUP_NAMES = {
    1: "主食及加工品", 2: "豆类及加工品", 3: "畜禽肉", 4: "蛋类及制品",
    5: "奶类", 6: "水产品及制品", 7: "油脂", 8: "蔬菜及制品", 9: "干果及制品",
}


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / name, encoding="utf-8-sig")


def label(frame: pd.DataFrame, model: str) -> pd.DataFrame:
    result = frame.copy()
    result.insert(0, "model", model)
    result["demand_good_name"] = result["demand_good"].map(GROUP_NAMES)
    result["shock_good_name"] = result["shock_good"].map(GROUP_NAMES).fillna("总支出")
    return result


def distribution_points(frame: pd.DataFrame, model: str) -> pd.DataFrame:
    # Household means are unstable when a fitted share approaches zero.  Use the
    # 1--99% trimmed, quantity-weighted aggregate for exploratory model comparison.
    result = frame[
        ["elasticity_type", "demand_good", "shock_good", "trimmed_aggregate", "support_rate"]
    ].copy()
    result = result.rename(columns={"trimmed_aggregate": "elasticity"})
    result.insert(0, "evaluation", "trimmed_quantity_weighted_aggregate_1_99")
    result["reference_share"] = np.nan
    for column in ["std_error", "z_value", "p_value", "ci_low", "ci_high"]:
        result[column] = np.nan
    return label(result, model)


def fmt(value: float, digits: int = 3) -> str:
    return "NA" if pd.isna(value) else f"{value:.{digits}f}"


def main() -> None:
    selection = read("model_selection.csv")
    status = read("estimation_status.csv")

    distribution_specs = [
        ("AIDS NLSUR-CF", "aids"),
        ("QUAIDS NLSUR-CF", "quaids"),
        ("EASI NLSUR-CF", "easi_nlsur"),
    ]
    rejected_gmm_specs = [
        ("EASI GMM-IV two-step (rejected)", "easi"),
        ("EASI GMM-IV one-step (rejected)", "easi_gmm1"),
    ]
    distributions = []
    for model, stem in distribution_specs:
        distributions.append(label(read(f"{stem}_elasticities.csv"), model))
    all_distributions = pd.concat(distributions, ignore_index=True)
    all_distributions.to_csv(
        OUT / "elasticity_distributions_all_models.csv", index=False, encoding="utf-8-sig"
    )

    points = [
        distribution_points(read("aids_elasticities.csv"), "AIDS NLSUR-CF"),
        distribution_points(read("quaids_elasticities.csv"), "QUAIDS NLSUR-CF"),
        label(read("easi_nlsur_reference_analytic.csv"), "EASI NLSUR-CF"),
    ]
    all_points = pd.concat(points, ignore_index=True)
    all_points.to_csv(OUT / "elasticities_reference_all_models.csv", index=False, encoding="utf-8-sig")

    rejected_points = pd.concat(
        [label(read(f"{stem}_reference_analytic.csv"), model) for model, stem in rejected_gmm_specs],
        ignore_index=True,
    )
    rejected_points.to_csv(
        OUT / "easi_gmm_rejected_elasticities.csv", index=False, encoding="utf-8-sig"
    )

    tests, regularity = [], []
    for model, stem in distribution_specs + rejected_gmm_specs:
        test = read(f"{stem}_tests.csv")
        test.insert(0, "model", model)
        tests.append(test)
        reg = read(f"{stem}_regularity.csv")
        reg.insert(0, "model", model)
        regularity.append(reg)
    all_tests = pd.concat(tests, ignore_index=True)
    all_regularity = pd.concat(regularity, ignore_index=True)
    all_tests.to_csv(OUT / "tests_all_models.csv", index=False, encoding="utf-8-sig")
    all_regularity.to_csv(OUT / "regularity_all_models.csv", index=False, encoding="utf-8-sig")

    def test_value(stem: str, test_name: str, column: str = "statistic") -> float:
        frame = read(f"{stem}_tests.csv")
        row = frame.loc[frame["test"].eq(test_name), column]
        return np.nan if row.empty else float(row.iloc[0])

    def reg_value(stem: str, diagnostic: str) -> float:
        frame = read(f"{stem}_regularity.csv")
        row = frame.loc[frame["diagnostic"].eq(diagnostic), "value"]
        return np.nan if row.empty else float(row.iloc[0])

    gmm_diagnostics = pd.DataFrame([
        {
            "model": "EASI GMM-IV two-step",
            "weighting": "two-step robust",
            "converged": 1,
            "overidentification_statistic": test_value("easi", "Hansen_overidentification"),
            "overidentification_df": test_value("easi", "Hansen_overidentification", "df"),
            "overidentification_p": test_value("easi", "Hansen_overidentification", "p_value"),
            "positive_fitted_share_rate": reg_value("easi", "positive_fitted_share_rate"),
            "negative_hicksian_own_rate": reg_value("easi", "negative_hicksian_own_elasticities"),
            "slutsky_max_eigenvalue": reg_value("easi", "slutsky_max_eigenvalue"),
            "accepted_for_interpretation": 0,
            "reason": "Hansen test rejects; fitted shares are almost always nonpositive",
        },
        {
            "model": "EASI GMM-IV one-step",
            "weighting": "identity",
            "converged": 1,
            "overidentification_statistic": test_value(
                "easi_gmm1", "GMM_overidentification_identity_weight"
            ),
            "overidentification_df": test_value(
                "easi_gmm1", "GMM_overidentification_identity_weight", "df"
            ),
            "overidentification_p": test_value(
                "easi_gmm1", "GMM_overidentification_identity_weight", "p_value"
            ),
            "positive_fitted_share_rate": reg_value("easi_gmm1", "positive_fitted_share_rate"),
            "negative_hicksian_own_rate": reg_value(
                "easi_gmm1", "negative_hicksian_own_elasticities"
            ),
            "slutsky_max_eigenvalue": reg_value("easi_gmm1", "slutsky_max_eigenvalue"),
            "accepted_for_interpretation": 0,
            "reason": "identity-weight sensitivity also produces almost universally nonpositive shares",
        },
    ])
    gmm_diagnostics.to_csv(
        OUT / "gmm_diagnostic_comparison.csv", index=False, encoding="utf-8-sig"
    )

    expenditure = all_points.loc[all_points["elasticity_type"].eq("expenditure")].copy()
    own = all_points.loc[
        all_points["elasticity_type"].isin(["marshallian", "hicksian"])
        & all_points["demand_good"].eq(all_points["shock_good"])
    ].copy()
    compact = pd.concat([expenditure, own], ignore_index=True)
    compact.to_csv(
        OUT / "own_price_and_expenditure_elasticities.csv", index=False, encoding="utf-8-sig"
    )

    preferred = selection.loc[selection["bic_preferred"].eq(1)]
    preferred_text = "unresolved"
    if len(preferred):
        row = preferred.iloc[0]
        preferred_text = f"{str(row['model']).upper()} order {int(row['order'])}"
    sample = read("sample_flow.csv")
    model_n = int(sample.loc[sample["stage"].eq("complete IV model sample"), "observations"].iloc[0])
    desc = read("nine_group_descriptives.csv")
    desc = desc.loc[desc["sample"].eq("model")]

    lines = [
        "# 九类食物需求系统结果（未Bootstrap）",
        "",
        "本轮按九类字面定义估计。鲜果、畜禽肉制品、调料和烟酒糖茶不进入份额分母，因此是九类内部的条件需求弹性。",
        "",
        f"- 完整模型样本：{model_n:,}户年。",
        f"- NLSUR-CF同估计器比较的BIC/族内顺序选择：{preferred_text}。",
        "- AIDS、QUAIDS和EASI都使用Shonkwiler-Yen零消费修正、收入工具变量控制函数和村年聚类标准误。",
        "- 省份固定效应与调查年份完全共线；最终设计保留省份固定效应、删除年份指标，设计矩阵满秩。",
        "- AIDS/QUAIDS使用1%--99%修剪后的数量加权聚合弹性，避免近零预测份额支配简单均值。",
        "- EASI报告样本参考点解析弹性及delta-method p值；本轮未运行bootstrap。",
        "- EASI GMM-IV虽数值收敛，但两种权重矩阵均未通过事后诊断，已从主弹性结果剔除。",
        "- 所有模型均未施加Slutsky负半定曲率参数化。",
        "",
        "## 模型选择（NLSUR-CF）",
        "",
        "|模型|阶数|收敛|参数数|BIC|Engel高阶项p值|族内推荐|最终推荐|",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in selection.itertuples(index=False):
        lines.append(
            f"|{str(row.model).upper()}|{int(row.order)}|{int(row.converged)}|"
            f"{fmt(row.parameters,0)}|{fmt(row.bic,1)}|{fmt(row.Engel_order_p,4)}|"
            f"{int(row.family_test_preferred)}|{int(row.bic_preferred)}|"
        )

    lines.extend([
        "", "## 样本统计", "",
        "|类别|消费参与率|平均预算份额|消费户月数量中位数|社区价格中位数|",
        "|---|---:|---:|---:|---:|",
    ])
    for row in desc.itertuples(index=False):
        lines.append(
            f"|{row.group_name}|{row.participation:.1%}|{row.budget_share_mean:.1%}|"
            f"{row.quantity_p50_consumers:.3f}|{row.price_p50:.3f}|"
        )

    for model, _ in distribution_specs:
        model_compact = compact.loc[compact["model"].eq(model)]
        lines.extend([
            "", f"## {model}主要弹性", "",
            "|类别|支出弹性(p值)|Marshallian自价格(p值)|Hicksian自价格(p值)|",
            "|---|---:|---:|---:|",
        ])
        for group, name in GROUP_NAMES.items():
            exp = model_compact.loc[
                model_compact["elasticity_type"].eq("expenditure")
                & model_compact["demand_good"].eq(group)
            ].iloc[0]
            mar = model_compact.loc[
                model_compact["elasticity_type"].eq("marshallian")
                & model_compact["demand_good"].eq(group)
            ].iloc[0]
            hic = model_compact.loc[
                model_compact["elasticity_type"].eq("hicksian")
                & model_compact["demand_good"].eq(group)
            ].iloc[0]
            lines.append(
                f"|{name}|{fmt(exp.elasticity)} ({fmt(exp.p_value,4)})|"
                f"{fmt(mar.elasticity)} ({fmt(mar.p_value,4)})|"
                f"{fmt(hic.elasticity)} ({fmt(hic.p_value,4)})|"
            )

    lines.extend([
        "", "## EASI GMM-IV失败诊断（不用于经济解释）", "",
        "|规格|过度识别统计量|自由度|p值|正预测份额率|负Hicksian自价格率|Slutsky最大特征值|采用|",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in gmm_diagnostics.itertuples(index=False):
        lines.append(
            f"|{row.model}|{fmt(row.overidentification_statistic,3)}|"
            f"{fmt(row.overidentification_df,0)}|{fmt(row.overidentification_p,6)}|"
            f"{fmt(row.positive_fitted_share_rate,4)}|{fmt(row.negative_hicksian_own_rate,4)}|"
            f"{fmt(row.slutsky_max_eigenvalue,4)}|{int(row.accepted_for_interpretation)}|"
        )

    lines.extend([
        "", "## 估计与识别诊断", "",
        "|模型|估计器|GMM步数|收敛|返回码|Hansen p值|首阶段F|首阶段p值|首阶段R²|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in status.itertuples(index=False):
        lines.append(
            f"|{str(row.model).upper()}|{row.estimator}|{int(row.gmm_steps)}|"
            f"{int(row.converged)}|{int(row.return_code)}|{fmt(row.J_p,4)}|"
            f"{fmt(row.firststage_F,2)}|{fmt(row.firststage_p,4)}|{fmt(row.firststage_r2,3)}|"
        )

    lines.extend([
        "", "## 联合检验", "",
        "|模型|检验|统计量|自由度|p值|",
        "|---|---|---:|---:|---:|",
    ])
    for row in all_tests.itertuples(index=False):
        lines.append(
            f"|{row.model}|{row.test}|{fmt(row.statistic,3)}|{fmt(row.df,0)}|{fmt(row.p_value,4)}|"
        )

    lines.extend([
        "", "## 常规性诊断", "",
        "|模型|诊断|数值|阈值|通过|",
        "|---|---|---:|---:|---:|",
    ])
    for row in all_regularity.itertuples(index=False):
        lines.append(
            f"|{row.model}|{row.diagnostic}|{fmt(row.value,5)}|{fmt(row.threshold,5)}|{int(row.passed)}|"
        )

    lines.extend([
        "", "## 解释限制", "",
        "九类不是全部食品，特别是鲜果被排除，因此支出弹性是给定九类总支出的条件支出弹性。水产品只有42个村年直接报价，且需要较多省年/年份中位数填补，该类价格弹性的识别明显弱于其他类别。三种NLSUR-CF模型都不能在全样本满足曲率，正的Hicksian自价格点估计不能解释为可靠需求反应。正式结果需在最终分类确定后重新bootstrap，并重新设计水产品等低覆盖类别；高维GMM还需要更强工具变量和解析雅可比。",
    ])
    report = "\n".join(lines) + "\n"
    (OUT / "NINE_GROUP_MODEL_RESULTS.md").write_text(report, encoding="utf-8")
    (OUT / "NINE_GROUP_MODEL_RESULTS.txt").write_text(report, encoding="utf-8")
    print(f"Compiled {len(all_points)} point elasticities; preferred {preferred_text}")


if __name__ == "__main__":
    main()
