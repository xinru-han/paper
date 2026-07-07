# 结果汇总（2026-07-07，补录+底库修正后全量运行）

数据：省级面板 2004–2024，5 要素（labor / mach / fert / seed / other=numeraire）。
底库 OCR 污染 1,411 值已按 PDF 直读修正、续表缺页补录 4,571 行已合入
（`docs/patch_ocr_gaps_notes.md`）。样本：corn 421 / wheat 299 / soybean 240 /
japonica 278 / mid_indica 237 / early & late_indica 189 / peanut 222 / rapeseed 297
（cotton 37 排除主分析）。

**基线规格 = "cc"**：ITSUR + Terrell (1996) 逐观测曲率惩罚（κ=1e6）。
9 品种凹性 96.4–100%、单调性 ≥99.5%。plain（无约束）仅用于 LR 检验与
numeraire 不变性（均 <2e-11）。

## 1. 自价格弹性（cc，全样本评估点）

| crop | labor | mach | fert | seed | other |
|---|---|---|---|---|---|
| corn | −0.28 | −0.95 | −0.46 | −0.44 | −0.96 |
| wheat | −0.45 | −0.78 | −0.74 | −0.56 | −1.02 |
| soybean | −0.37 | −0.99 | −0.83 | −0.50 | −1.13 |
| rice_japonica | −0.28 | −0.73 | −0.40 | −0.55 | −0.72 |
| rice_mid_indica | −0.27 | −0.73 | −0.43 | −0.76 | −0.76 |
| rice_early_indica | −0.27 | −0.63 | −0.38 | −0.68 | −0.80 |
| rice_late_indica | −0.27 | −0.68 | −0.34 | −0.71 | −0.66 |
| peanut | −0.31 | −0.93 | −0.73 | −0.44 | −1.00 |
| rapeseed | −0.26 | −0.98 | −0.58 | −0.70 | −0.88 |

全部为负（凹性约束保证）；劳动需求最缺乏弹性（−0.26 ~ −0.45），
机械与 other 接近单位弹性——与要素市场直觉一致。

## 2. 劳动→机械替代 M_ML（工资上涨引致的机械替代劳动）

| crop | all | 04-08 | 09-14 | 15-19 | 20-24 |
|---|---|---|---|---|---|
| corn | 0.90 | 0.89 | 0.90 | 0.91 | 0.89 |
| wheat | 0.83 | 0.82 | 0.82 | 0.83 | 0.83 |
| soybean | 1.06 | 1.06 | 1.05 | 1.06 | 1.07 |
| rice_japonica | 0.68 | 0.65 | 0.68 | 0.70 | 0.67 |
| rice_mid_indica | 0.72 | 0.71 | 0.72 | 0.73 | 0.73 |
| rice_early_indica | 0.63 | 0.61 | 0.63 | 0.65 | 0.62 |
| rice_late_indica | 0.64 | 0.61 | 0.64 | 0.66 | 0.63 |
| peanut | 1.03 | 1.02 | 1.03 | 1.05 | 1.03 |
| rapeseed | 0.98 | 0.98 | 0.98 | 0.98 | 0.98 |

均显著为正（替代而非互补）；旱作（大豆/花生/玉米/油菜）≈1，
稻作 0.6–0.7（移栽/收获环节机械化更难）。时期内呈 15-19 年前小幅上升。
玉米 bootstrap（B=200 省级block，ok率100%）：
M_ML 0.966 [0.761, 1.172]，M_LM 1.177 [1.012, 1.344]，
eps_ll −0.293 [−0.367, −0.227]，eps_mm −0.981 [−1.116, −0.858]，
B_labor −0.007 [−0.012, −0.002]（劳动节约偏向显著）。

## 3. 技术偏向 B_n = λ_nt / S̄_n（cc）

粮食四大类（corn + 三籼稻 + 粳稻）一致表现**劳动节约**（B_labor −0.7% ~ −2.1%/年）
且**机械/化肥使用**偏向；wheat/soybean/peanut 的 λ_labor 在 cc 下不显著为负
（小麦机械化早已完成、大豆黑龙江主导样本）。LR 检验 9 品种全部拒绝
Cobb-Douglas、Hicks 中性与无技术变迁（p<0.02）。

## 4. 诱致性创新两阶段（S2 general index，pooled 5 大粮作）

偏向路径对滞后 3 期相对价格回归：labor Σψ=−0.236 (t=−5.2)、
mach Σψ=−0.109 (t=−4.7) —— 工资相对上涨 → 后续技术路径向劳动节约移动，
方向符合 Hicks 诱致性创新假说。
**注意**：labor 的 placebo（未来一期价格）t=−3.8 显著，说明存在共同趋势/
预期问题，论文中应作为"相关性证据"谨慎表述（mach 的 placebo 干净）。

## 5. Törnqvist 成本增长分解（名义，2004–2024）

各作物亩成本对数增长 0.93–1.26，其中**要素价格贡献 1.26–1.58**
（劳动价格独占 0.74–1.22），技术进步抵消 −0.18 ~ −0.53，产量规模贡献很小。
2013 年后成本增长骤降（如玉米 0.10 vs 前期 1.01），价格推动与技术抵消同时减弱
——与刘易斯转折后工资增速放缓叙事一致。

## 6. 份额 OOS 预测（留出 2021–2024）

translog RMSE 0.028–0.052，全面优于 Cobb-Douglas（0.051–0.076）；
与随机游走互有胜负（early_indica 胜、其余略逊 0.003–0.011）——
面板短期份额惯性强，属预期内。

## 7. 文件索引

- 估计输出：`out/{params,gamma,elasticities,bias,tests,scale_tfp,concavity,fitted_shares}_{crop}[_cc].csv`
- bootstrap：`out/bootstrap_draws_corn_cc.csv`
- S2/诱致性：`out/bias_path_{crop}.csv`、`out/induced_innovation.csv`
- 分解/OOS：`out/decomp_{crop}.csv`、`out/oos_{crop}.csv`
- 图：`figs/F1–F5_*.png`（9 品种）
- 一键复现：`scripts/run_pipeline.sh`（build_panel.R → estimate → s2 → decomp → bootstrap → figs）
