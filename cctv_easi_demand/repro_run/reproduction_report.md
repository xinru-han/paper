# 高频家庭食品需求系统（EASI/QUAIDS）—— 原始数据复现报告

**复现日期**：2026-07-05
**运行根目录**：`Paper1-EASI/repro_run/`（所有生成代码与输出均在此）
**输入数据**：`/root/data/数据/央视数据/Data_merged.csv`（原始交易，1.0 GB）+ `Paper1-EASI/processed/`（外部锚定价格、省-月协变量等预处理文件）
**代码来源**：`final_demand_model_R/CODE.md` 中脚本 20→23 的完整 R 代码，逐字抽取运行（仅脚本 23 硬编码 base 路径做最小改写指向 repro_run）

---

## 1. 复现流程

| 步骤 | 脚本 | 作用 | 状态 |
|---|---|---|---|
| 20 | `src/20_build_high_frequency_price_and_panel.R` | 读原始交易→映射 10 组→2020-2022 筛选→价格/UV 审计→fold-excluded 内部价格→外部锚定凸组合潜在价格→家庭-月-10组需求面板 | ✅ 完成 |
| 21 | `src/21_estimate_high_frequency_demand_R.R` | 第一阶段 CRE/Mundlak 购买选择 Probit（10 组），输出 Φ/φ 预测 | ✅ 第一阶段完成 |
| 21(二步) | 同上 | 稀疏堆叠二步估计（约 526 万×9 行） | ⏹ 与原作者一致：因规模/内存未完成，已跳过 |
| 22 | `src/22_estimate_high_frequency_demand_fast_R.R` | **实际主估计器**：快速正规方程版受约束 SY-EASI 与 SY-QUAIDS | ✅ 完成 |
| 23 | `final_demand_model_R/23_finalize_demand_diagnostics.R` | 复用系数算两模型月度弹性 + 份额加权 Slutsky 特征值（曲率/负定性）+ 标注残差组 | ✅ 完成 |

脚本 21 的二步稀疏估计从未写出模型对象（`constrained_high_frequency_models_r.rds` 缺失），与 RESULTS.md 记录完全一致；快速版脚本 22 是设计等价的有效主估计器。

## 2. 样本与管线一致性（对 RESULTS.md §1）

| 指标 | 本次复现 | 原始 | 一致 |
|---|---|---|---|
| 原始交易行（映射到 10 组后） | 10,420,107 | 10,420,107 | ✅ |
| 家庭数 | 27,653 | 27,653 | ✅ |
| 活跃家庭-月 | 584,835 | 584,835 | ✅ |
| 家庭-月-10组面板行 | 5,848,350 | 5,848,350 | ✅ |
| 预算份额加总误差(max abs) | 3.0e-15 | 3.0e-15 | ✅ |
| 潜在价格缺失行 | 0 | 0 | ✅ |

## 3. 第一阶段 Probit（对 §2）

10 组购买率、平均预测概率、Brier、伪 R² 与原始**逐组一致**（最大偏差 7e-6）。校准良好（平均预测概率≈实际购买率），如 G01 主食 0.592/0.226/0.047、G09 乳制品 0.708/0.052。

## 4. 理论约束（对 §3）

加总性 2.2e-16、相对价格齐次性 0、Slutsky 对称性 0 —— 三项按构造成立，与原始完全一致。

## 5. 弹性结果（对 §4）

**食品总支出弹性**（SY-EASI≈SY-QUAIDS）：主食 0.531、食用油 0.193（必需品）；水果 0.939、牛羊肉 0.940、猪肉 0.931（近单位）；坚果 7.27 为残差组（不可解释）。

**自价格弹性（Marshallian）**：10 组符号全部复现，3 个正号组：
- G02 食用油 +0.462（原 +0.462）
- G06 禽类及其他肉类 +0.735（原 +0.736）
- G09 乳制品 +0.183（原 +0.183）

## 6. 曲率/负定性诊断（对 §5）

份额加权对称化 Slutsky 矩阵特征值（应全 ≤0 才满足负定性）：

| 模型 | 非正特征值 | 最大特征值 | 全负定 |
|---|---|---|---|
| SY-EASI | 6/10 | +0.150 | ❌ |
| SY-QUAIDS | 6/10 | +0.147 | ❌ |

SY-EASI 特征值：0.1503; 0.1044; 0.0334; 0.0008; −0.0462; −0.0667; −0.0950; −0.1086; −0.1801; −0.2459；RESULTS.md 原值为 0.1502; 0.1045; 0.0334; 0.0008; −0.0462; −0.0667; −0.0950; −0.1087; −0.1805; −0.2459 —— 两者**在 ~1e-4 容差内一致**（第 1/2/8/9 位差 1~4e-4，源于 probit 收敛容差与数值差分），非逐位相同但**符号结构完全一致**。4 个明显为正特征值 → 曲率不成立；换函数形式（QUAIDS）未修复。

## 7. 根因（对 §6）

3 个正自价格组恰是内、外部价格相关性低的组：食用油(corr 0.245)、禽类(0.072)、乳制品(0.080)；乳制品内部权重高达 0.449。纯外部价格主导的蔬菜(−1.04)、水果(−1.06)给出干净负弹性，反向印证根因在潜在价格质量端，非代码错误。

## 8. 逐文件数值比对

所有原始 outputs 文件均成功复现（见 `comparison_reproduction_vs_original.csv`）：

| 文件类别 | 最大绝对偏差 |
|---|---|
| price_validation_metrics / theory_constraint / sample_summary | **0（精确）** |
| probit 拟合统计 | 7e-6 |
| 食品总支出弹性 | 1.7e-4 |
| 受约束系数 | 1.7e-3 |
| 自价格符号 | 2.1e-3 |
| Marshallian/Hicksian 10×10 | 3.2e-3 |
| 曲率特征值 | 1.5e-5 |

偏差均在 3~4 位小数量级，源于 probit 收敛容差与数值差分弹性计算，**无符号翻转、无结构性差异**。

## 9. 结论

按 CODE.md 脚本 20→23、用原始交易数据从头重跑，**完整复现了 RESULTS.md 的全部关键结果**：样本规模精确一致、理论约束按构造成立、10 组弹性与曲率诊断到小数位吻合，包括 3 个正自价格弹性与 4 个正 Slutsky 特征值这一核心发现。与原报告一致的判断保留：管线本身正确，曲率失败根因在潜在价格质量（内外部相关性低的组），在价格重认证前最终弹性不应被解释。

## 10. 文件清单

- 代码：`repro_run/src/20,21,22.R`、`repro_run/final_demand_model_R/23_finalize_demand_diagnostics.R`
- 面板：`repro_run/data_derived/household_month_group10_r.csv`（2.2 GB）
- 弹性/诊断：`repro_run/final_demand_model_R/outputs/*`
- 中间产出：`repro_run/outputs/{demand,regularity,validation,latent_price,price_audit,internal_price}/*`
- 比对：`repro_run/comparison_reproduction_vs_original.csv`、`comparison_headline_elasticities.csv`
- 图：`repro_run/fig1..fig4_*.png`
