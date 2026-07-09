# 结果汇总 v2（2026-07-09，REV-1 全量方法修正后）

> 本文件取代 `results_summary.md`（旧版作废草稿）。所有数字溯源 `out/` CSV；
> 外部常数见 `constants.py`；方法修订轨迹见 `docs/rev_log.md`；表见 `tables/T1–T9`。
> 每节结论已按 `revision_directives_v2.md` §1"禁止表述清单"逐条自查（见文末)。

数据：省级面板 2004–2024，5 要素（labor/mach/fert/seed/other=numeraire）。
样本：corn 427 / wheat 325 / soybean 240 / japonica 278 / mid_indica 237 /
early_indica 189 / late_indica 189 / peanut 222 / rapeseed 302（cotton 79 排除）。
基线 = cc（Terrell 1996 逐观测曲率惩罚 κ=1e6）+ 省 FE + F-4 可积项。

---

## ① 数据与规格（含识别诊断）

**识别诊断（T1，M13a）**：劳动日工价（daywage，全国记账口径）ln(w/w_other) 对年份哑变量
R²=0.78–0.89——**几乎零省际变异**，劳动参数识别高度依赖函数形式；雇工工价（hired，
市场价）R²=0.47–0.73，省际变异明显更大。故雇工工价升格为**并列基线**（§②双栏），
daywage 结果的劳动弹性须带"识别依赖函数形式"的 caveat。

**F-4 可积性修复**：份额方程含省截距时，成本方程按 Shephard 引理加入 Σfe_np·lnw_n。
修复后玉米分解残差 0.18→0.007（§⑦）；升级版 CD 回归测试（`test_cd.R`）验证含可积项的
恢复精度，且删除该项时测试如期失败（守门有效）。

**诚实披露**：w_labor 全国统一（零省际变异，corr(lnw,t)≈0.9）；曲率约束对 M_ml 的抬升
（§②M3a）；w_mach 的 2004–05 外推 / 2011,2013 插值 / 2024 仅 1–3 月；w_other 以毒死蜱×
地膜代理；OCR 修正 1,573 值 + 补录 4,823 行（详见 `docs/data_appendix.md`）。

## ② 弹性主表（daywage | hired 双栏，plain | cc 并列，M1 CI）

自价格弹性 eps_ll、eps_mm 与 M_ML（工资→机械替代），cc 基线 + 省级 block bootstrap
B=500 percentile CI（`out/bootstrap_ci_cc.csv`；T2）：

| crop | eps_ll (cc, daywage) | eps_mm (cc) | **M_ML** [95% CI] | eps_ll (hired) | M_ML (hired) |
|---|---|---|---|---|---|
| corn | −0.30 [−0.36,−0.22] | −0.96 [−1.11,−0.82] | **0.94 [0.72, 1.15]** | −0.32 | 0.86 |
| wheat | −0.40 [−0.56,−0.27] | −0.81 | **0.73 [0.49, 1.02]** | −0.45 | 0.80 |
| soybean | −0.39 [−0.57,−0.27] | −1.05 | **1.17 [0.87, 1.55]** | −0.34 | 0.92 |
| rice_japonica | −0.26 [−0.33,−0.18] | −0.70 | **0.62 [0.37, 0.79]** | −0.41 | 0.91 |
| rice_mid_indica | −0.28 | −0.75 | **0.76 [0.51, 0.94]** | −0.32 | 0.85 |
| rice_early_indica | −0.22 | −0.63 | **0.53 [0.36, 0.67]** | −0.36 | 0.79 |
| rice_late_indica | −0.23 | −0.66 | **0.57 [0.34, 0.81]** | −0.30 | 0.69 |
| peanut | −0.25 | −0.91 | **0.87 [0.64, 1.09]** | −0.29 | 0.90 |
| rapeseed | −0.25 | −1.01 | **1.00 [0.66, 1.25]** | −0.26 | 0.97 |

**M_ML 全 9 品种 95% CI 下界均 >0**（替代而非互补，稳健）。eps_ll 在两种工资度量下同号同量级。

**M3a plain/cc 位移（T9d 注 + `plaincc_compare.csv`）**：曲率约束把 M_ML 抬升——
corn +0.18、wheat +0.15、peanut +0.30、rapeseed +0.34（plain 凹性违反率 28–49%）；
rice_early/late 近零位移（plain 本已凹）。**故"旱作 M_ML≈1"对 peanut/rapeseed 部分是约束
产物**，须如实标注；玉米/稻作的 M_ML 排序不依赖约束。
**M3b κ 敏感性**：max|ΔM_ml(κ=1e6→1e7)|=0.024（soybean，余 <0.013），近硬约束收敛；
soybean 边际敏感 0.024 仍落在其 bootstrap CI 内。

**双 block 敏感性（M1e）**：玉米省×时期双重 block（每省×期作独立 FE 单元）M_ML=0.60
[0.53, 0.75]——较省级 block 低，反映更细的 FE 划分；替代仍正且离零。

## ③ 跨品种对比（差异 CI）

同 draw 配对的 M_ML 差异 percentile CI（`crosscrop_Mml_ci.csv`；T3）：
- **旱作组均值 − 稻作组均值 = 0.329 [0.137, 0.479]，CI 排除零** → "旱作替代弹性高于稻作"
  这一排序**有推断支撑**（旱作=corn/wheat/soybean/peanut/rapeseed；稻作=四种稻）。
- 逐对：corn、soybean 的 M_ML 显著高于全部四种稻（CI 排除零）；wheat<soybean。
- 机制：稻作移栽/收获环节机械化更难，替代空间小。

## ④ Γ 断点检验与"稳定性"表述（M6，核心叙事修正）

**旧稿"替代弹性稳定"是函数形式性质，非经验发现**。Γ 结构断点（2004–13 vs 2014–24，
Δγ df=10）：**9 品种全部拒绝 Γ 稳定**（LR 43–149，解析 p 1e-6~1e-27；T4），
且**共同评估点 M_ML 一律后段更高**（pre≈0.2–0.9 → post≈1.5–1.9，Δ+0.64~+1.60）。
**M9 省级 block bootstrap 化 LR**：玉米/粳稻断点 bootstrap 非拒绝率 0.0–0.5%——
**断点在省内序列相关下依然稳健**，非 iid 假象。Δλ_nt：6/9 品种劳动节约偏向 2014 后加速。

→ **叙事定稿：替代弹性并非稳定，而是刘易斯转折后显著上升**（工资加速上涨→机械替代
劳动的空间被激活），与工资诱致机械化一致。这比 pooled 规格更支持 H1（部分复活）。

## ⑤ 偏向一致性表与限定结论（M7）

品种×要素跨规格一致性（S1 λ_nt 符号 + M1 CI 排除零 + S2 δ_2024 + hired + 6f 同向；
`bias_consistency.csv`；T5）。**仅允许引用 consistent=TRUE 的单元**：
- **劳动节约**（consistent）：**corn、rice_japonica、rice_mid_indica**（B_labor 分别
  −0.006/−0.022/−0.009，M1 CI 均排除零）。
- **机械使用**（consistent）：**四种稻**（japonica/mid/early/late）。
- **wheat、soybean、peanut、rapeseed 跨规格不一致**（B_labor CI 含零或 hired/6f 变号）→
  **不对其技术偏向方向下结论**。
机制诊断（`bias_mach_mechanism.csv`）：去趋势后 δ_mach 与 lnw_mach 相对价格相关——
支持"年哑变量吸收价格趋势"的解释。

## ⑥ 对偶技术率 τ_C（撤除 RTS/TFP）

ε_Cy 病态（除法偏误 + 无外生 y 变异；Spec B 下 rapeseed 100% 为负、mid_indica 62%），
**RTS=1/ε_Cy、TFP=−τ_C/ε_Cy 不可发表 → 停产**（`scale_tfp_*` 已改名 `_deprecated`）。
只保留对偶技术率 τ_C 分期路径（`tauC_period_summary.csv`；T6）：全品种 τ_C≈−0.01~−0.04/年
（成本节约型技术进步），soybean/rapeseed 后期趋缓（rapeseed −0.033→−0.007）。

## ⑦ 成本增长分解（名义口径；实际口径待 INPUT）

玉米全国 2004–2024（`decomp_corn.csv`；T7）：dlnC=1.10，**要素价格贡献 1.41（劳动独占
0.93）**，技术 −0.36，产量 +0.04，残差 0.007（F-4 修复后近零）。2013 年前后断点显著：
2004–13 dlnC=1.01 vs 2013–24 dlnC=0.10——价格推动与技术抵消同时减弱，与刘易斯转折后
工资增速放缓一致。产量项 =ε̂_Cy·Δlny，**ε̂_Cy 识别薄弱、占比 <5%**，故分解结论不依赖它。
**M5 实际平减 + 分省产量权重 + 残差追因待 INPUT-1（播种面积）/INPUT-2（农村CPI），排在最后。**

## ⑧ 诱致性创新（M8 区域×品种，按 G4 结局）

第一阶段下沉 NBS 四大区域×品种（corn/wheat/japonica），第二阶段 sb=−Δδ 对滞后区域相对
雇工工价 + **年份 FE（吸收全国共同趋势）** + 区域×品种 FE，DK 与 wild(区域×品种) 双 SE
（`induced_regional.csv`；T8）。**结果较 pooled 规格根本改善**：
- **劳动**：Σψ **转正且显著**（k1–5：Σψ=0.344，t_DK=3.86，t_wild=2.95；**placebo 干净**
  F1_t=0.72/F2_t=0.94）——**Hicks 诱致方向（Σψ>0）**。**G4 → k1–5 规格达 "suggestive
  evidence"，回归正文**（k1–3 Σψ=0.223 t=2.38 但 2 期前置 placebo t=2.17 边界，作 caveat）。
- **机械**：placebo 显著失败（F1_t≈−3.2）→ 降级为**描述性**，删因果语言。

→ 与 §④断点证据相互印证：两条独立线索（替代弹性 2014 后上升 + 劳动侧区域诱致系数
转正）共同支持工资诱致机械化。

## ⑨ 份额 OOS 预测

translog RMSE 0.027–0.049，全面优于 Cobb-Douglas（0.051–0.076）；与随机游走互有胜负
（early_indica、wheat 胜，余略逊 0.003–0.010）——面板短期份额惯性强，属预期。

## ⑩ 稳健性总矩阵（T9）

| 扰动 | 对核心结论的影响 |
|---|---|
| Spec B 预期产量（M2/G2） | \|ΔM_ml\|<0.15 全品种，无变号，**基线不动**；ε_Cy 仍病态（佐证 §⑥） |
| 6 要素含地（robust_6f） | eps_ll 略增、M_ML±0.1–0.3，符号与旱>稻排序不变；eps_land −0.4~−0.7 |
| 雇工工价并列基线（M12a） | eps_ll/M_ML 同号同量级（§②） |
| κ 网格（M3b） | 近收敛（soybean 边际 0.024） |
| 剔 w_mach 构造年（M10） | 见 `robust_wmach_years.csv` |
| 仅原生 xls 年（M11，风险定界） | 核心弹性同号（`robust_xlsonly.csv`） |
| 剔疫情 2020–22（M13c） | `robust_dropcovid.csv` |
| **区域×时期 FE（M13b）** | M_ML **一律小降 −0.05~−0.15**（corn/soybean 触 0.15 线）→ 吸收区域×时期共同
冲击后替代估计**软化 ~10–15%**，符号与排序不变；识别一节据此加限定 |
| 发改委三肥替代 w_fert（M12c） | 核心弹性同号（`robust_fertndrc.csv`） |
| 价格交叉验证（M12b） | w_fert 单位值 vs 发改委三肥几何均值 corr 0.51–0.94，价格构造可信 |

## ⑪ 数据附录索引

见 `docs/data_appendix.md`：15 条价格构建全文 + 插补计数 + 毒死蜱代理局限 +
OCR 修正/补录规模与抽查 + F4 二轮补录完成性核验。

## ⑫ 未结事项

M5 实际口径分解（待 INPUT-1/2）；生猪系统、E2 影子地租、气象 IV（Spec C）为下一轮扩展项；
发改委价格 IV 未做。early/late indica 联合重抽 ok 率 91%（省份少，joint 交集偶 <4 省），
其 CI 基于 ~455 draws，已披露。

---

### 禁止表述清单自查（`revision_directives_v2.md` §1）

1. ✓ 全文无 "TFP=x%/年"、"RTS=x"（§⑥ 已撤，`scale_tfp` 改 `_deprecated`）。
2. ✓ 无 "M_ML 随工资升而增大/H1 成立" 的无条件断言——§④以 M6 断点检验（已拒绝且后段更高）
   支撑，措辞为"部分复活/suggestive"。
3. ✓ 技术偏向"劳动节约"只对 M7 consistent 品种（corn+japonica+mid_indica）陈述（§⑤）。
4. ✓ "旱作替代弹性高于稻作"带 M1 差异 CI 排除零（§③ 0.329[0.137,0.479]）。
5. ✓ 诱致性因果语言只在 M8 placebo 干净的 labor k1–5（suggestive）；mach 降描述性（§⑧）。
6. ✓ 无 "位似性全部被拒绝"——wheat 位似性未拒（analytic p=0.070，bootstrap 非拒绝 27.5%，§④/T4注）。
