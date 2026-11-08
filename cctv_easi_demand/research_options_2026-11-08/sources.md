# 来源、基点与下载

## 方法文献

1. Andrews, Isaiah; Simon Essig Aberg; Jesse M. Shapiro. 2026. *An LLM Workflow for Functional Form Sensitivity Analysis*. NBER Working Paper 35947, October. DOI: 10.3386/w35947。[NBER](https://www.nber.org/papers/w35947)、[作者页面](https://shapiro.scholars.harvard.edu/publication/llm-workflow-functional-form-sensitivity-analysis)、[PDF](https://shapiro.scholars.harvard.edu/sites/g/files/omnuum7731/files/2026-10/Fragility_0.pdf)。这是工作论文，不按已发表期刊论文描述。
2. [JMSLab/DirectedSensitivity](https://github.com/JMSLab/DirectedSensitivity)：[模板](https://github.com/JMSLab/DirectedSensitivity/blob/main/workflow/TEMPLATE.md)、[流程](https://github.com/JMSLab/DirectedSensitivity/blob/main/workflow/WORKFLOW.md)、[报告](https://github.com/JMSLab/DirectedSensitivity/blob/main/workflow/REPORT.md)。本次只查阅设计，没有运行该程序，也不把远端执行指令当本地任务授权。
3. MacKinnon, James G.; Morten Ørregaard Nielsen; Matthew D. Webb. *Cluster-Robust Inference: A Guide to Empirical Practice*。[2022 年作者预印本](https://arxiv.org/abs/2205.03285)，页面标注获 Journal of Econometrics 接收。用于聚类与有限聚类诊断，不表示任意 bootstrap 自动适用于本模型。
4. [国家统计局四大区域划分](https://www.stats.gov.cn/zt_18555/zthd/sjtjr/dejtjkfr/tjkp/202302/t20230216_1909741.htm)：省份分组依据，不证明全国代表性。

网络核验：2026-11-08。实际实施时锁定论文版本和工具库 commit。

本轮查阅的工具库 `main` 指向 [`ebd0e8c3cd19b79a9090e9a97f91a788f3d8a01a`](https://github.com/JMSLab/DirectedSensitivity/commit/ebd0e8c3cd19b79a9090e9a97f91a788f3d8a01a)，日期为 2026-10-15；作为方法参考版本记录，不表示已安装或执行。

## 本地依据

| 相对 Paper1-EASI 的路径 | 用途 | 不能推出 |
| --- | --- | --- |
| `welfare_revision_2026-10-13/code/00_config.do` | 上游路径和控制设置 | 模型刚重新运行 |
| `welfare_revision_2026-10-13/code/01_curvature_fit.do` | 曲率、矩压缩与边界说明 | 旧协方差可作新分组 Wald |
| `welfare_revision_2026-10-13/ado/cctv_exact.do` | exact 准则与工具；首行明确 No SY | exact 与两阶段是同一模型 |
| `welfare_revision_2026-10-13/outputs/exact/curvature_fit.csv` | 已有数值诊断 | 本次异质性结果 |
| `welfare_revision_2026-10-13/journal_revision_2026-11-08/README.txt` | 原文模型来源、上轮运行范围 | 成本重算等于需求系统重估 |
| `meat_merge_trial_2026-10-11/data/analysis_monthly.dta` | 后续月度复现基点，本次不改 | 可以公开微观数据 |
| `/root/data/数据/央视数据/Data_merged.csv` | 字段标签初核，非全量分组计数 | 局部扫描可填报全样本组别数 |

本轮不声称完成中英文异质性文献的系统查重。确认主线后，须围绕最终家庭、食品与目标补做专题检索；贡献是待验证设计，不作“首次研究”断言。

## 下载

下方列表仅注册方案、状态清单和核验材料。可下载各节 Markdown 和 `design_manifest.json`。不注册原始交易、家庭标识、微观预测或旧审阅数据库。
