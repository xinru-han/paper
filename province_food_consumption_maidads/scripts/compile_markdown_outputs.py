from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "ProvinceMAIDADS" / "Results"
DATA_OUT = ROOT / "ProvinceMAIDADS" / "Data" / "output"
SCRIPTS = ROOT / "ProvinceMAIDADS" / "scripts"


RESULT_DESCRIPTIONS = {
    "parameter_estimates.csv": "主模型 AIDADS/MAIDADS 参数估计",
    "model_fit_by_group.csv": "主模型分组拟合误差",
    "elasticity_income_grid.csv": "收入网格弹性",
    "elasticity_expenditure_grid.csv": "数量、支出、预算份额三种弹性口径",
    "elasticity_price_marshallian_grid.csv": "Marshallian 自价格与交叉价格弹性",
    "elasticity_price_hicksian_grid.csv": "Hicksian 自价格与交叉价格弹性",
    "elasticity_consistency_tests.csv": "弹性理论一致性检验",
    "elasticity_observed_points.csv": "每个省-年观测点弹性",
    "multistart_diagnostics.csv": "主估计多起点与梯度诊断",
    "best_solution_gradient_report.csv": "最优解梯度诊断",
    "parameter_boundary_report.csv": "参数边界诊断",
    "projection_group_2030_2035_2050.csv": "主模型分组预测",
    "projection_item_feed_2030_2035_2050.csv": "主模型动物产品与饲料粮预测",
    "projection_province_path.csv": "主模型省级预测路径",
    "projection_growth_path.csv": "预测收入增长路径、Chen et al. (2020) SSP2 省级人口路径与 2024 桥接假设",
    "model_comparison.csv": "模型比较、AIC/BIC/OOS/LR bootstrap",
    "lr_test_chi2_and_bootstrap.csv": "LR 检验 bootstrap 摘要",
    "lr_bootstrap_draws.csv": "LR bootstrap 抽样明细",
    "oos_fit_by_group.csv": "样本外验证拟合误差",
    "oos_predictions.csv": "样本外逐省预测",
    "oos_2023_fit_by_group.csv": "2023 样本外验证拟合误差",
    "oos_2023_predictions.csv": "2023 样本外逐省预测",
    "bootstrap_draw_status.csv": "bootstrap 抽样收敛状态",
    "bootstrap_draw_metrics.csv": "bootstrap 抽样指标明细",
    "bootstrap_key_ci.csv": "关键指标 bootstrap 区间，收敛 draw 汇总",
    "bootstrap_key_ci_success_only.csv": "关键指标 bootstrap 区间备份，收敛 draw 汇总",
    "bootstrap_parameter_ci.csv": "参数 bootstrap 区间",
    "bootstrap_parameter_draws.csv": "参数 bootstrap 抽样明细",
    "robustness_cpi_nonfood_parameter_estimates.csv": "CPI 非食品口径参数估计",
    "robustness_cpi_nonfood_fit_by_group.csv": "CPI 非食品口径拟合误差",
    "robustness_cpi_nonfood_projection_group_2030_2035_2050.csv": "CPI 非食品口径分组预测",
    "robustness_cpi_nonfood_projection_item_feed_2030_2035_2050.csv": "CPI 非食品口径饲料粮预测",
    "robustness_cpi_nonfood_projection_growth_path.csv": "CPI 非食品口径预测增长路径与 SSP2 人口路径",
    "robustness_cpi_nonfood_multistart_diagnostics.csv": "CPI 非食品稳健性多起点诊断",
    "oos_summary_by_model.csv": "按口径、模型和样本切分的 OOS 汇总",
    "projection_decomposition_2030_2035_2050.csv": "预测变化的人口与人均需求贡献分解",
}

METHOD_MD_DESCRIPTIONS = {
    "CODE_AUDIT_FIX_REPORT.md": "代码审查修正状态报告",
    "data_quality_report.md": "数据质量与预算恒等式核查",
    "feed_demand_method.md": "饲料粮需求换算说明",
    "nonfood_cpi_quality_report.md": "非食品 CPI 质量报告",
    "model_equation_tests.md": "预算恒等式、弹性一致性和优化诊断测试",
    "nutrition_conversion_audit.md": "营养换算和主粮热量审计",
}


SCRIPT_DESCRIPTIONS = {
    "run_maidads_pipeline.py": "数据构造、MAIDADS/AIDADS 主估计、弹性、预测和主摘要生成",
    "run_additional_checks.py": "CPI 稳健性、样本外验证、bootstrap 和追加摘要生成",
    "run_formal_bootstrap.py": "正式规模省份簇 bootstrap 与 LR cluster bootstrap，可断点续跑并同步正式推断结果",
    "prepare_paper_workflow_outputs.py": "按论文写作 skill 要求整理结果目录、补充 gate 所需审计文件",
    "build_manuscript_draft.py": "生成 evidence ledger、论文初稿、表格、参考文献和本地审稿意见",
    "build_maidads_simulator_workbook.py": "生成无宏版省级 MAIDADS Excel 模拟器",
    "compile_markdown_outputs.py": "把所有结果与代码整合为两个 Markdown 归档文件",
}


def csv_shape(path: Path) -> tuple[int, int]:
    try:
        return pd.read_csv(path).shape
    except Exception:
        return -1, -1


def csv_block(path: Path) -> str:
    return "```csv\n" + path.read_text(encoding="utf-8").rstrip() + "\n```"


def json_block(path: Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```"


def build_results_markdown() -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = RESULTS / "省级MAIDADS_全部结果整合.md"
    result_csvs = sorted(
        p for p in RESULTS.rglob("*.csv") if not p.name.startswith("~") and p.name != output.name
    )
    result_jsons = sorted(RESULTS.glob("*.json"))
    method_mds = sorted(p for p in list(RESULTS.rglob("*.md")) + list(DATA_OUT.rglob("*.md")) if p.name in METHOD_MD_DESCRIPTIONS)
    data_csvs = sorted(DATA_OUT.glob("*.csv"))

    lines = [
        "# 中国省级 MAIDADS 全部结果整合",
        "",
        f"- 生成时间：{now}",
        f"- 工作目录：`{ROOT}`",
        f"- 主结果目录：`{RESULTS}`",
        f"- 数据构造输出目录：`{DATA_OUT}`",
        "",
        "## 一、主要结论",
        "",
        "- 主模型、稳健性、样本外验证和 bootstrap 的最新结果见后文摘要与完整 CSV。",
        "- 本版按两份审查文件修正：主口径改为 2023 实际价 + 全国非食品 CPI；省级反推非食品 CPI 作为稳健性；补齐价格弹性、理论一致性、诊断、OOS 分模型输出和正式规模 LR cluster bootstrap。",
        "- 预测人口路径已改用 Chen et al. (2020) Scientific Data 的 SSP2 省级人口预测；收入路径仍为全国增长率加省份收敛情景。",
        "- `省级需求弹性结果代码检查与修正方案.md` 与 `代码审查_问题与修复方案.md` 已纳入研究方案修订依据。",
        "",
        "## 二、研究方案修正说明",
        "",
    ]
    plan_path = ROOT / "省级MAIDADS顶刊研究方案_v4_代码审查修正版.md"
    if plan_path.exists():
        lines.append(plan_path.read_text(encoding="utf-8"))
    else:
        lines.append("_未找到 v4 研究方案修正版文件。_")
    lines.extend(
        [
            "",
            "## 三、主结果摘要",
            "",
            (RESULTS / "RESULTS_SUMMARY.md").read_text(encoding="utf-8"),
            "",
            "## 四、追加处理与稳健性摘要",
            "",
            (RESULTS / "ADDITIONAL_RESULTS.md").read_text(encoding="utf-8"),
            "",
            "## 五、结果文件索引",
            "",
            "| 文件 | 行数 | 列数 | 说明 |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for path in result_csvs:
        rows, cols = csv_shape(path)
        display_name = str(path.relative_to(RESULTS)) if path.is_relative_to(RESULTS) else path.name
        lines.append(f"| `{display_name}` | {rows} | {cols} | {RESULT_DESCRIPTIONS.get(path.name, '结果表')} |")
    lines.extend(["", "## 六、方法与审计说明文件", ""])
    for path in method_mds:
        lines.extend([f"### {path.name}", "", f"说明：{METHOD_MD_DESCRIPTIONS[path.name]}", "", path.read_text(encoding="utf-8"), ""])
    lines.extend(["", "## 七、Manifest JSON", ""])
    for path in result_jsons:
        lines.extend([f"### {path.name}", "", json_block(path), ""])
    lines.extend(
        [
            "## 八、全部结果 CSV 原文",
            "",
            "以下折叠块完整嵌入 `ProvinceMAIDADS/Results` 下所有 CSV，便于单文件归档。",
            "",
        ]
    )
    for path in result_csvs:
        rows, cols = csv_shape(path)
        display_name = str(path.relative_to(RESULTS)) if path.is_relative_to(RESULTS) else path.name
        lines.extend(
            [
                "<details>",
                f"<summary><strong>{display_name}</strong> ({rows} 行 x {cols} 列)</summary>",
                "",
                csv_block(path),
                "",
                "</details>",
                "",
            ]
        )
    lines.extend(
        [
            "## 九、数据构造输出 CSV 原文",
            "",
            "| 文件 | 行数 | 列数 |",
            "| --- | ---: | ---: |",
        ]
    )
    for path in data_csvs:
        rows, cols = csv_shape(path)
        lines.append(f"| `{path.name}` | {rows} | {cols} |")
    lines.append("")
    for path in data_csvs:
        rows, cols = csv_shape(path)
        lines.extend(
            [
                "<details>",
                f"<summary><strong>{path.name}</strong> ({rows} 行 x {cols} 列)</summary>",
                "",
                csv_block(path),
                "",
                "</details>",
                "",
            ]
        )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def build_code_markdown() -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = RESULTS / "省级MAIDADS_全部代码整合.md"
    script_files = [
        SCRIPTS / "run_maidads_pipeline.py",
        SCRIPTS / "run_additional_checks.py",
        SCRIPTS / "run_formal_bootstrap.py",
        SCRIPTS / "prepare_paper_workflow_outputs.py",
        SCRIPTS / "build_manuscript_draft.py",
        SCRIPTS / "build_maidads_simulator_workbook.py",
        SCRIPTS / "compile_markdown_outputs.py",
    ]
    lines = [
        "# 中国省级 MAIDADS 全部代码整合",
        "",
        f"- 生成时间：{now}",
        f"- 工作目录：`{ROOT}`",
        "",
        "## 一、运行顺序",
        "",
        "```bash",
        f"cd {ROOT}",
        "python3 ProvinceMAIDADS/scripts/run_maidads_pipeline.py",
        "python3 ProvinceMAIDADS/scripts/run_additional_checks.py",
        "python3 ProvinceMAIDADS/scripts/run_formal_bootstrap.py --bootstrap-reps 1000 --lr-reps 500 --workers 6",
        "python3 ProvinceMAIDADS/scripts/prepare_paper_workflow_outputs.py",
        "python3 .codex/skills/provincial-maidads-paper-writer/scripts/paper_gate_check.py --root ProvinceMAIDADS",
        "python3 ProvinceMAIDADS/scripts/build_manuscript_draft.py",
        "python3 ProvinceMAIDADS/scripts/build_maidads_simulator_workbook.py",
        "python3 ProvinceMAIDADS/scripts/compile_markdown_outputs.py",
        "```",
        "",
        "## 二、代码文件索引",
        "",
        "| 文件 | 行数 | 作用 |",
        "| --- | ---: | --- |",
    ]
    for path in script_files:
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        lines.append(f"| `{path.name}` | {line_count} | {SCRIPT_DESCRIPTIONS[path.name]} |")
    lines.extend(["", "## 三、完整源码", ""])
    for path in script_files:
        lines.extend(
            [
                f"### {path.name}",
                "",
                f"源文件：`{path}`",
                "",
                "```python",
                path.read_text(encoding="utf-8").rstrip(),
                "```",
                "",
            ]
        )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    results_md = build_results_markdown()
    code_md = build_code_markdown()
    print(results_md)
    print(code_md)


if __name__ == "__main__":
    main()
