# 弹性口径命名与机械基准分解说明 (Step 5 deliverable)

## 1. 弹性定义口径 (Elasticity convention naming — review Issue 3)

本文报告的弹性遵循 **"条件式(集约边际)弹性" (conditional / intensive-margin elasticity)**
口径：对系统性(潜在)份额函数 g_i(lnp, lnX, Z) 在样本均值处取数值导数，
**未**乘以 Shonkwiler-Yen 参与概率 Phi_i-hat。即：

    Marshallian: eps_M_ij = -delta_ij + (1/g_i) * dg_i/dlnp_j
    Hicksian:    eps_H_ij = eps_M_ij + eta_i * g_j
    Expenditure: eta_i    = 1 + (1/g_i) * dg_i/dlnX

这些是"若该省该季度必然正向参与该品类进口贸易，需求会如何随价格/支出变化"的
条件式回答，并非对观测到的(截尾)预算份额 w_i = Phi_i * g_i + phi_i * psi_i 的
直接弹性。它们在集约边际(intensive margin)上是无偏的，但不包含参与概率
本身随价格/支出变化的外延边际(extensive margin)响应。

## 2. 观测/截尾口径对照 (Observed/censored contrast — review Issue 3 remedy b)

作为稳健性对照，我们同时报告 **"观测截尾弹性" (observed/censored elasticity)**，
将 Phi-hat 视为局部常数并相应缩放份额导数：dw_i/dz = Phi_i * dg_i/dz。

**解析结果**：在此近似下，Marshallian 与支出弹性在数值上与条件式口径
**完全相同**（因为 Phi_i 在分子分母中相消：
(Phi_i*dg_i/dz)/(Phi_i*g_i) = dg_i/dz / g_i）；只有 Hicksian 弹性因
补偿项 eta_i * w_j 中的 w_j 随口径变化（观测口径 w_j=Phi_j*g_j 而条件式
口径为 g_j）而产生差异，差异幅度约为 3-14%（各品类不同，见下表）。

因此审改意见所指出的"口径未言明"问题，其经济后果集中在 Hicksian
(替代)弹性上，而非 Marshallian 或支出弹性，这是本文附录新增的解析发现。

## 3. 机械基准分解 (Mechanical benchmark decomposition — review Issue 1)

将估得的 Gamma 矩阵设为全零(保持 alpha/beta/lambda/delta/cf/psi 不变)，
重新计算弹性，得到"若价格数据完全不含信息、纯由 Engel 曲线与 adding-up/
homogeneity/symmetry 恒等式决定"的机械基准。三种价格口径下，Hicksian
替代弹性矩阵中 |全模型-机械基准| 占 |全模型| 的比例：

| 价格口径 | Gamma贡献占比 |
|---|---|
| completed | 92.0% |
| loo_quarter_winsor | 90.6% |
| landed_proxy | 76.9% |

## 4. 与原稿结论的实质性差异 (Substantive divergence from original manuscript)

原稿(审改意见所评审版本)报告 Gamma 矩阵对 Hicksian 弹性的贡献仅约 15%，
且 Gamma=0 的联合检验被视为无法拒绝(机械性来源为主)。使用完整重建的
数据管道(全量海关微观数据 -> 省-季度-品类面板 -> 质量调整价格 -> SY
两步法 -> Bartik 控制函数 -> FIML AIDS/QUAIDS)，三种价格口径下:

- Bewley LR 检验: 均在 <0.1% 水平拒绝 AIDS，选择 QUAIDS (LRB=103.5/104.7/111.4)
- Gamma=0 联合 Wald 检验: 均强烈拒绝 (p=1.9e-10 / 3.9e-9 / 5.6e-14)
- Gamma 对 Hicksian 弹性的贡献占比: 77%-92%（而非原稿的~15%）
- Slutsky 矩阵负半定性: 在样本均值处近似满足(未约束时特征值介于
  -1.1e-13 到 +0.077之间)，施加曲率约束后目标函数损失可忽略不计

这一差异可能来自：(a) 重建的省-季度-品类面板与原稿使用的面板在数据来源
处理上的差异（例如质量调整价格回归中去除了 ln(数量)项以避免内生性问题，
Bartik 工具改用"预测贸易水平"设计而非可能的增长率设计）；(b) 原稿 Gamma
矩阵可能确因价格测量误差/内生性而向零收缩。论文修订应如实报告此差异，
并说明由于原始估计代码未能获取，无法逐行复现原稿的具体数值管道选择。
