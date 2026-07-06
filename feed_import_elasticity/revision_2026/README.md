# revision_2026 — QUAIDS论文修订工作目录

本目录包含针对《Conditional Feed-Grain Import Substitution in China》一文
根据"论文初稿审改意见_QUAIDS版"完整重建的数据管道、估计结果与修订文本。

## 目录结构

- `code/` — 全部可复现脚本，按管道顺序编号运行：
  - `01_build_panel.py` — 省-季度-品类面板重建(31省x28季度x5品类=4340格)
  - `02_build_bartik_instrument.py` — 非农进口Bartik工具变量("预测贸易水平"设计)
  - `03_merge_controls_build_wide.py` — 合并畜牧业控制变量，构建宽面板
  - `04_build_quality_adjusted_prices.py` — 质量调整价格(三种口径)
  - `05_sy_probit_bartik_first_stage.py` — SY参与方程 + Bartik第一阶段
  - `06_fit_fiml_aids_quaids.py` — FIML AIDS/QUAIDS估计 + Bewley检验 + Gamma联合
    检验 + 机械基准分解 + 曲率约束估计 + 弹性delta法SE
  - `07_province_cluster_bootstrap.py` — 300次省级聚类全管道bootstrap
  - `08_policy_event_identification.py` — 政策事件(高粱/大麦)价格识别
  - `fiml_aids_quaids.py` — FIML估计器核心模块(独立于R原始代码重新实现)

- `checkpoints/` — 各阶段中间数据(parquet/pickle)，避免重复计算全部管道

- `output/` — 全部数值结果表(CSV)与文字说明(MD)，详见下方"关键结果文件"

- `figures/` — 3张图: 政策事件研究(2张)、bootstrap vs delta method对比(1张)

- `MASTER_REVISION_DOCUMENT.md` — **修订说明主文档**，整合全部修订文本，
  按论文章节顺序给出"问题-依据-建议替换文本"

- `plan_quaids.json` — 本次修订的执行计划(10个步骤)

## 关键结果文件 (output/)

| 文件 | 内容 |
|---|---|
| `panel_reconciliation_report.md` | 面板重建对账(31省vs30正预算省份口径核实) |
| `quality_adjusted_price_diagnostics.csv` | 质量调整价格回归诊断(含/不含ln数量对照) |
| `bartik_design_search.csv` | 8种候选Bartik设计的完整搜索记录与partial F |
| `expenditure_first_stage_diagnostics.csv` | 支出方程第一阶段诊断(partial F=14.47) |
| `selection_stage_params.csv` | SY参与方程probit系数(5品类) |
| `bewley_model_selection.csv` | AIDS vs QUAIDS Bewley检验(3种价格口径) |
| `gamma_joint_wald_test.csv` | **H0:Gamma=0联合Wald检验**(核心新发现) |
| `mechanical_benchmark_decomposition.csv` | **Gamma贡献占比77-92%的完整分解** |
| `fiml_structural_parameters.csv` | 完整结构参数(alpha/beta/lambda/gamma) |
| `fiml_elasticities_full.csv` | 全部弹性(条件式主口径+SE+观测截尾对照口径) |
| `bootstrap_inference_summary.csv` | **300次bootstrap vs delta method对比表** |
| `bootstrap_vs_delta_comparison.csv` | bootstrap分布详细分位数 |
| `policy_event_did_summary.csv` | 政策事件DiD估计(高粱/大麦) |
| `policy_event_study_coefficients.csv` | 动态事件研究系数(按相对季度) |
| `policy_exposure_shares_by_province.csv` | 各省对涉案来源国的暴露份额 |
| `elasticity_convention_and_mechanical_benchmark_notes.md` | 弹性口径命名说明 |

## 与原稿的实质性差异摘要

原稿被审改意见诊断为"Gamma≈0，替代弹性~85%来自机械性adding-up"。重建管道
下，三种价格口径均**强烈拒绝**H0:Gamma=0 (p=1.9e-10至5.6e-14)，Gamma贡献
占77-92%。同时，300次省级聚类全管道bootstrap显示delta method严重低估
真实抽样不确定性(尤其corn/oats/barley)，而sorghum与cassava的负向替代
关系在绝大多数重抽样中保持稳健(符号一致率97.3%/94.7%)。政策事件识别
(2020-2023年澳大利亚大麦AD/CVD)提供了独立的外生价格变动证据。

由于原始估计代码(R)与原始数据管道细节均未能获取，本次重建的具体数值
与原稿存在差异属预期之内；核心定性发现(Gamma的真实性、弹性口径问题、
推断方法问题)均已直接回应审改意见的全部8项问题。详见
`MASTER_REVISION_DOCUMENT.md`。
