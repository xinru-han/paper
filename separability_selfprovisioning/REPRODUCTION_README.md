# Separability / Food Self-Provisioning — 复现说明

**论文**: *Farming for the Family Table: Household Composition and Food
Self-Provisioning in Rural China* (`paper1_manuscript_v4.docx`, 2026年7月版)

本目录是对该论文全部实证结果的**R语言复现**。原始 `code/` 目录已丢失，此处
所有脚本均从 `paper1_all_code_integrated.md` 中**逐字恢复**，并与随附的
`paper1_all_results_integrated.md` 及论文 docx 中的数字重新核对。

---

## 1. 快速运行

```bash
# 需要 R (>=4.1) 及 R 包: sandwich, MASS, lmtest, zoo
cd <本目录>
Rscript run_reproduction.R      # 端到端复现，约 4 分钟
Rscript verify_reproduction.R   # 打印“复现值 vs 论文值”对照表
```

结果写入 `outputs/`（主表、图、报告）与 `outputs/post_estimation_plan/`
（§5.6 后估计分析 A0–A5）。

## 2. 目录结构

```
run_reproduction.R          # 主控脚本（本次新增，编排下列脚本）
verify_reproduction.R       # 复现值与论文值对照（本次新增）
20_post_estimation_plan.R   # §5.6 后估计分析（A0–A5，Table 7）
code/                       # 从 integrated md 恢复的全部 R/Python 脚本
  00_setup.R                #   公用函数：聚类稳健 vcov、Wald 检验、M0–M3 设定
  02..14_*.R                #   主分析流水线（见下）
  01/04_export/05_hedonic/06_construct/18/19_*.R  # 原始数据构建脚本（见 §4）
raw_data/                   # 户表变量标签 csv（脚本 07 类别审计所需）
data/repro_inputs/          # 两个自洽的 analysis-ready 快照（zip，共约 6MB）
outputs/                    # 复现生成的表/图/报告
```

## 3. 数据说明（两个样本）

论文正文与 §5.6 使用了**两个略有差别的样本**，本复现分别对应：

| 样本 | 快照文件 | 行数 | 公共 M3 样本 | 用于 |
|---|---|---|---|---|
| 主样本 | `repro_inputs/main_analysis_ready_28520.csv.zip` | 28,520 | **27,568** | Table 1–6、类别异质性、村内固定效应、稳健性、附录 A1–A3 |
| kg 清洗样本 | `repro_inputs/kgclean_analysis_ready_28208.csv.zip` | 28,208 | 27,262 | §5.6 后估计（omnibus、Mundlak、RIF 分位、类别 meta、外部有效性）|

`run_reproduction.R` 会自动解压并在两个阶段间切换正确的输入文件。

## 4. 关于原始数据构建脚本

`code/` 中的 `04_export_*`、`05_hedonic_price_imputation.R`、
`06_construct_market_friction_and_external_controls.R`、`18_*`、`19_*`、
`01_rebuild_*` 用于从**原始调查数据**
（`/root/data/数据/食物消费调查数据/`）重建 analysis-ready 面板
（合并地理、POI、GAEZ、hedonic 价格、市场摩擦、县级政策文本等）。
它们**不在结果复现的必经路径上**——analysis-ready 面板已作为上述两个快照提供，
复现结果直接从快照开始。这些脚本予以保留以备数据溯源与审计。

> 注：`05_hedonic_price_imputation.R` 可独立运行以核对价格诊断，结果与论文一致：
> 观测占比 73.0%、插补 27.0%、县级 hedonic R²≈0.443、log-RMSE≈0.698
> （论文报告 73.1% / R²≈0.43 / RMSE≈0.72）。

## 5. 复现精度

| 结果 | 论文值 | 复现值 | 状态 |
|---|---|---|---|
| Table 3 M3 参与 Wald (N=27,568) | 16.73, p=0.002 | **16.733, p=0.0022** | ✅ 精确 |
| Table 3 M0/M1/M2 p | .178/.106/.004 | .178/.106/.004 | ✅ 精确 |
| 村内固定效应 log/ihs 数量 | 16.06/15.77, p=.003 | **16.06/15.77, p=.003** | ✅ 精确 |
| 村内固定效应 参与 | 6.41, p=.171 | **6.41, p=.171** | ✅ 精确 |
| Table 5 类别（蛋/油/菜/果显著，豆校正前显著）| — | 同一格局 | ✅ 精确 |
| A4 类别 meta ρ / slope | 0.77 / 7.91 | **0.767 / 7.910** | ✅ 精确(12位有效数字) |
| A0 omnibus (df=8) | 20.43, p=0.009 | 23.43, p=0.003 | ≈ 同结论* |
| A1 Mundlak 参与(within/between) | 16.53 / 10.89 | 16.94 / 11.11 | ≈ 同结论* |
| A5 外部有效性（逐省、分年）| 各结论 | 同一格局 | ≈ 同结论* |

\* §5.6 后估计的小幅数值差异源于：产生 26,926 行公共样本的那一份**确切的
27,861 行 kg 清洗快照已丢失**，此处使用可得的 28,208 行快照（公共样本 27,262）。
论文本身即说明该样本更新对主结论“无实质影响”（Wald 16.53 对 16.73）。所有
显著性判断与结论方向均一致。

## 6. 环境

R 4.1.2；包 `sandwich`、`MASS`、`lmtest`、`zoo`。全部使用 base `lm()` +
`sandwich::vcovCL()` 村级聚类稳健推断（HC1）。
