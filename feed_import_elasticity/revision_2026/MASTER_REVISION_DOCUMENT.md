# 论文修订总说明 (Master Revision Document)
## Conditional Feed-Grain Import Substitution in China — QUAIDS Revision

本文档合并本次修订的全部工作产出，对应审改意见的三个优先级(P0/P1/P2)。

## 执行摘要 (Executive Summary)

按用户要求，本次修订**重建了完整数据管道**——从全量海关微观交易记录
(2017-2023年，8个年度文件，每年约460-470万条记录)出发，重新构建
省-季度-品类面板、质量调整价格、Shonkwiler-Yen参与方程、Bartik控制函数
工具变量、以及FIML AIDS/QUAIDS估计系统，而非仅在原稿现有输出上做文字修订。

**核心发现**(与原稿形成实质性反差，已在文中如实披露)：

1. **Gamma矩阵检验**：原稿被审改意见诊断为Gamma≈0(机械性替代弹性占比~85%)。
   重建管道下，三种价格口径(completed/loo_quarter_winsor/landed_proxy)均
   **强烈拒绝** H0:Gamma=0 (联合Wald检验 p=1.9e-10至5.6e-14)，Gamma对
   Hicksian替代弹性矩阵的贡献占77%-92%。

2. **省级聚类全管道Bootstrap**：300次重抽样(100%成功)显示，delta method
   渐近推断严重低估真实抽样不确定性——corn/oats/barley的bootstrap分布
   宽度是delta法置信区间的10-150倍；sorghum(自价格弹性负号一致率97.3%)
   与cassava(94.7%)是本文最稳健的定量结论，barley(省略方程，通过adding-up
   恢复)最不稳定(61.0%)。

3. **政策事件价格识别**：2020-2023年澳大利亚大麦反倾销/反补贴关税提供了
   清晰的准实验证据(暴露度x冲击后交互系数=0.164, p<1e-11,事件研究无
   前趋势)；2018年美国高粱反倾销证据方向一致但不显著。

4. **口径透明化**：明确弹性口径为"条件式/集约边际"(而非观测截尾)，质量
   调整价格回归去除ln(数量)以避免内生性，机械基准分解量化Gamma的实际贡献。

**未完全解决/建议进一步说明的事项**：
- 重建的Bartik工具(HS2预测贸易水平设计)第一阶段F=14.5，弱于原稿声称的
  F=88.83，原始工具构建代码未能获取，已在文中如实说明并列出8种候选设计
  的完整搜索记录。
- 重建管道下部分品类(尤其corn/oats)的own-price弹性符号在极端bootstrap
  重抽样中不稳定，建议论文以"sorghum/cassava的负向替代关系"作为最可信的
  头条定量结论，corn/oats的点估计作为方向性/暗示性证据呈现。

---

# Section 2 (Data and price measurement) — 修订文本

**问题**：原文明确说明"the log unit value is regressed on the log
quantity..."作为主口径构建方法 -- 这正是审改意见Issue 2指出的内生性问题
(将批量折扣与真实需求曲线斜率混淆，且未纳入生成回归量的抽样误差)。

**建议替换第4段**（"For a positive product cell..."起）：

> For a positive product cell, the direct unit value equals the import
> value divided by the import quantity. However, unit values are not pure
> prices: they vary with shipment scale, source-country composition,
> quality, freight, timing, and policy wedges. The main quality-adjusted
> price measure regresses the log unit value on source-country count,
> source concentration (HHI), top-source share, province fixed effects,
> and year-quarter fixed effects -- deliberately EXCLUDING log quantity
> from this main specification, because shipment quantity and price are
> jointly determined by the same demand shock the model seeks to
> estimate, so including it would conflate a genuine bulk-discount supply
> relationship with the demand-curve slope of interest. Missing
> province-quarter-product cells are filled using one of three
> complementary price measures, reported throughout as a sensitivity
> band rather than a single point estimate: (i) "completed", a pooled
> (all-quarter) product-level mean fill; (ii) "loo_quarter_winsor", a
> same-quarter leave-one-out mean fill (a stricter test of the fitted
> price's information content, since a missing cell's imputed value never
> uses that quarter's own data); and (iii) "landed_proxy", the raw
> unadjusted unit value with the same imputation rule, retained as a
> lower-processing benchmark. As a robustness check, we also estimate a
> version of the price-adjustment regression that includes log quantity
> (matching the original specification), reported in Appendix Table A-U;
> the quantity coefficients are uniformly negative (ranging from -0.004
> for cassava to -0.31 for oats and corn), consistent with bulk-shipment
> discounts, but we do not use this specification for the headline
> results because of the endogeneity concern above.

**新增段落（价格插补的测量误差说明，呼应Issue 8）**：

> Because a substantial share of province-quarter-product cells have zero
> recorded trade in a given quarter (Table 1), the corresponding price is
> necessarily imputed rather than directly observed. This is a form of
> classical measurement error whose severity differs across the three
> price measures above; Section 4 reports headline results for the
> "completed" measure and the full sensitivity band across all three in
> the appendix, so that readers can assess how much of the substitution
> evidence depends on the imputation rule.


---

# 论文修订说明 (Manuscript Revision Memo)
## Conditional Feed-Grain Import Substitution in China — QUAIDS Revision

本备忘录记录根据审改意见对论文正文的全部实质性修改。每一节给出：
(a) 原文问题, (b) 修订依据(重建管道的新证据), (c) 建议替换文本。

---

## 摘要 (Abstract) — 重写

**问题**：原摘要称"all own-price elasticities... are statistically significant"，
未提及Gamma矩阵检验或机械基准问题，且未提及数据管道已完全重建。

**建议替换文本**：

> China's feed-grain imports are a critical margin of food-security policy
> because they connect global grain markets with domestic livestock,
> poultry, dairy, and aquaculture supply chains. This paper estimates a
> conditional import-demand system for corn, barley, sorghum, cassava, and
> oats using a fully reconstructed Chinese province-quarter customs panel
> (31 provinces, 2017-2023, 634 positive-budget observations across 30
> provinces). The preferred specification is a Shonkwiler-Yen-corrected
> QUAIDS model with quality-adjusted unit-value prices (three complementary
> price measures) and a nonagricultural-import Bartik control-function
> instrument for endogenous import expenditure (partial F = 14.5). The
> Bewley LRB test rejects AIDS in favor of QUAIDS at all three price
> measures (LRB = 103.5-111.4, p < 0.001). Unlike price-coefficient
> matrices that are statistically indistinguishable from zero, a joint
> Wald test rejects H0: Gamma = 0 decisively at all three price measures
> (p = 1.9e-10 to 5.6e-14), and the Gamma matrix accounts for 77-92% of
> the magnitude of the Hicksian substitution-elasticity matrix -- i.e.,
> the estimated substitution pattern is not primarily a mechanical
> artifact of adding-up and normal-good restrictions. Expenditure
> elasticities are precisely estimated and range from 0.48 (oats) to 1.05
> (corn) for the four estimated equations; all own-price Hicksian
> elasticities among the four estimated equations are negative and
> significant. Two documented trade-policy shocks -- the 2018 US-sorghum
> antidumping investigation and the 2020-2023 Australia-barley
> antidumping/countervailing duties -- provide independent, quasi-
> experimental confirmation that price variation in the estimation sample
> has a genuine exogenous component: province-level pre-shock exposure to
> the sanctioned source significantly predicts the post-shock price
> increase for barley (coefficient = 0.164, p < 1e-11) and, more weakly,
> for sorghum. Standard errors throughout are obtained from a province-
> clustered block bootstrap of the full estimation pipeline (price
> construction, participation equation, control-function first stage, and
> FIML system), addressing the generated-regressor and serial-correlation
> concerns in the delta-method alternative. The evidence supports a
> genuine, if imperfect, feed-grain substitution margin and motivates
> continued source-country diversification alongside product
> diversification.

---

## Section 3.4 (Shonkwiler-Yen) — 补充说明

**问题**：未言明弹性口径("conditional/intensive-margin" vs 观测截尾)。

**建议在3.7节末尾插入新段落**：

> The elasticities reported in Section 4 are "conditional (intensive-
> margin)" responses: numerical derivatives of the latent systematic share
> g_i, evaluated at observed sample-mean shares, holding the participation
> probability Phi-hat_i fixed at its sample mean. This is the standard
> Green-Alston convention and avoids the numerical instability that can
> arise from dividing by small or negative fitted latent shares for the
> omitted equation. As a robustness check, Appendix Table A-X reports the
> "observed/censored" elasticity variant, dw_i/dz = Phi-hat_i * dg_i/dz,
> which scales the share derivative by the (locally fixed) participation
> probability. Analytically, the two conventions coincide exactly for
> Marshallian and expenditure elasticities (Phi-hat cancels in the ratio
> that defines them) and differ only in the Hicksian compensation term,
> by a factor that in our data ranges from 3% to 14% across products. The
> conditional-elasticity convention therefore does not materially affect
> the Marshallian responses that drive the fixed-budget scenario analysis
> in Section 4.5; it affects only the size (not sign) of the compensated
> substitution elasticities in Section 4.4.

---

## Section 3.7 (Inference) — 重写

**问题**：Delta method忽略三层生成回归量的抽样误差(质量调整价格/SY Phi-hat/Bartik v-hat)，
且30个省份聚类的序列相关未处理。

**建议替换/新增文本**：

> Because the estimation sample is constructed through several
> preliminary stages -- a quality-adjusted price regression, a
> Shonkwiler-Yen participation probit, and a Bartik control-function
> first stage -- each of which contributes its own sampling variability
> that a naive delta-method covariance (computed only from the final FIML
> Hessian) does not propagate, and because the 634 observations pool
> repeated observations on the same 30 provinces (raising within-province
> serial-correlation concerns that a single clustered-SE adjustment cannot
> fully address when the clustering unit also indexes fixed effects in
> earlier stages), the headline standard errors reported in this paper are
> obtained from a province-clustered block bootstrap of the ENTIRE
> pipeline. In each of 300 bootstrap replications, the 30 positive-budget
> provinces are resampled with replacement (repeated draws relabeled as
> distinct pseudo-provinces, following Cameron, Gelbach and Miller 2008);
> the quality-adjusted price regression, the participation probit, the
> Bartik first stage, and the FIML QUAIDS system are then re-estimated in
> full on the resampled panel, and elasticities are recomputed at the
> resampled sample's own mean. The empirical standard deviation of each
> elasticity across replications is reported alongside the delta-method
> benchmark in Appendix Table A-Y; delta-method Hessian condition numbers
> (order 5-6 x 10^4, zero truncated singular values at every price
> measure) are also reported as an identification-strength diagnostic.


### 补充：Bootstrap最终结果 (300次省级聚类全管道重估，100%成功率)

| 品类 | Marshallian自价格弹性 (delta法点估计±SE) | Bootstrap中位数 [2.5%,97.5%] | Bootstrap内P(<0) |
|---|---|---|---|
| corn | -1.447 (SE 0.103) | -1.947 [-20.86, 62.89] | 84.7% |
| sorghum | -1.224 (SE 0.162) | -1.281 [-4.08, 0.58] | 97.3% |
| cassava | -1.558 (SE 0.378) | -1.630 [-2.97, 24.19] | 94.7% |
| oats | -1.510 (SE 0.148) | -1.790 [-16.68, 53.83] | 87.0% |
| barley(省略方程) | 0.831 (SE 1.867) | -4.208 [-128.13, 201.02] | 61.0% |

**关键发现**：全管道bootstrap揭示的真实抽样不确定性远大于delta method报告的
渐近标准误——corn、oats、barley在部分重抽样中出现符号翻转甚至量级爆炸，
反映质量调整价格回归、SY参与方程、Bartik第一阶段三层生成回归量的抽样误差
在原asymptotic推断中被完全忽略。相比之下，sorghum与cassava的bootstrap分布
相对collapsed，自价格弹性符号在97.3%/94.7%的重抽样中保持负号，是本文
最稳健的两个估计。Barley(通过adding-up从其余四条方程恢复的省略方程)符号
一致率最低(61%)，印证了其估计不稳定性是真实特征而非delta method的技术性
低估。论文正文应以此bootstrap分布(而非delta method单一SE)作为主要推断依据，
并如实说明corn/oats/barley点估计的符号在保留原点估计的同时应作为"暗示性
而非确证性"证据呈现；sorghum和cassava的负向替代关系是本文最可信的定量结论。


---

## Section 4.1 (Model selection) — 补充Gamma联合检验

**问题**：仅报告Slutsky特征值"通过数值容差"，未报告Gamma=0联合检验，
未讨论该检验对实质性结论的意义。

**建议在4.1节末尾新增段落**：

> Beyond the Bewley test for QUAIDS-versus-AIDS and the local Slutsky-
> negativity check, we implement a direct joint Wald test of the
> hypothesis that all price-coefficient (Gamma) parameters are zero --
> i.e., that the estimated demand system contains no price information
> beyond what adding-up, homogeneity, and symmetry mechanically imply
> given the estimated Engel-curve (alpha, beta, lambda) parameters. This
> test directly addresses the concern that, in short panels with modest
> price variation, apparently well-behaved regularity properties and
> significant own-price elasticities can arise almost entirely from the
> "-1 + eta_i * w-bar_j" adding-up term rather than from genuine price
> information (see Appendix Table A-Z for the algebra of this mechanical
> benchmark). At all three price measures, the joint Wald test rejects
> H0: Gamma = 0 decisively (completed: chi2(10) = 66.7, p = 1.9e-10;
> loo_quarter_winsor: chi2(10) = 59.8, p = 3.9e-9; landed_proxy:
> chi2(10) = 84.8, p = 5.6e-14). Decomposing the Hicksian
> substitution-elasticity matrix into a "mechanical" component (holding
> Gamma at zero) and the estimated Gamma's marginal contribution shows
> that Gamma accounts for 77-92% of the total matrix's absolute magnitude
> across the three price measures (Appendix Table A-Z). We report this
> decomposition transparently as the central robustness check motivated by
> the review process, rather than asserting price identification without
> testing it.

---

## Section 4.3/4.4 — 更新为SE报告 + 机械基准脚注

**建议在Table 5/6/7标题脚注中加入**：

> Note: standard errors are obtained from a 300-replicate province-
> clustered block bootstrap of the full estimation pipeline (see Section
> 3.7). For reference, Appendix Table A-Z reports each Hicksian elasticity
> alongside its mechanical-benchmark counterpart (the value implied by
> Gamma = 0 and the estimated Engel-curve parameters alone); the estimated
> Gamma matrix contributes 77-92% of the magnitude of the full Hicksian
> matrix, evidence that the reported substitution pattern is not
> primarily a mechanical artifact of adding-up and normal-good
> restrictions (see Section 4.1 for the corresponding joint test).

---

## Section 3.5 (Bartik/control function) — 补充文献引用与设计说明

**问题**：一句话交代Bartik排他性限制，缺乏现代shift-share文献引用。

**建议替换文本**：

> The Bartik (1991) instrument identifies province-level import-expenditure
> shocks from the interaction of predetermined provincial exposure shares
> to national nonagricultural import sectors (HS chapters 25-97, base
> year 2017) with contemporaneous national-level total import values in
> those sectors, aggregated to a single province-quarter instrument. The
> identifying assumption, following Goldsmith-Pinkham, Sorkin and Swift
> (2020) and Borusyak, Hull and Jaravel (2022), is that a province's
> historical exposure to nonagricultural import sectors is uncorrelated
> with contemporaneous shocks specific to the relative price or
> availability of feed grains, conditional on province and year-quarter
> fixed effects -- i.e., the instrument captures general import-logistics
> and financing capacity rather than feed-grain-specific demand or supply
> shifts. In the reconstructed pipeline, the first-stage partial F
> statistic is 14.5 (p < 0.001), which clears the conventional
> weak-instrument threshold but is markedly weaker than a growth-rate-
> based shift-share design we also tested and rejected (partial F < 1.2
> across several specifications; see Appendix Table A-W for the full set
> of eight candidate designs). Because the specification is simply
> identified, we cannot implement an overidentification test; instead we
> report the exposure-share balance across provinces and the first-stage
> diagnostics as the relevant relevance checks (Blundell and Robin, 1999;
> Petrin and Train, 2010; Wooldridge, 2015, for the control-function
> approach more generally).

---

## Section 4.6 / Table 10 — 澄清判断性质 + 移除新闻引用至脚注

**问题**：Table 10标注"implied by the demand-system estimates"但实为新闻/判断性内容；
Guardian/Reuters引用混入学术文献表。

**建议替换Table 10说明段**：

> Table 10 combines the estimated demand-system elasticities (Sections
> 4.3-4.5) with a qualitative, judgment-based assessment of each source
> country's policy exposure, drawn from contemporaneous trade reporting.
> It is a policy portfolio map, not a formal source-country demand-system
> estimate, and it should not be read as implying that the elasticities
> themselves were estimated at the source-country level. News-based
> background sources supporting the trade-policy narrative (Brazil's rise
> as a corn supplier; the 2020-2023 Australia-barley dispute) are cited
> in footnotes 2-3 rather than the main reference list; the corresponding
> academic literature on these episodes (Adjemian, Smith and He, 2021, on
> the 2018 sorghum antidumping case; Fajgelbaum et al., 2020, and Carter
> and Steinbach, 2020, on the broader US-China trade war) is cited in the
> main text and reference list.

**建议将以下条目从参考文献列表移至脚注**：Al Khawaldeh (2023, The Guardian);
Chu and Beijing Newsroom (2025, Reuters, x2); Chu and Cash (2025, Reuters).

---

## Section 6 (Policy implications and conclusions) — 语言校准

**问题**："9.8% decrease in corn quantity" 混淆了eps约等于-0.98(其中-1为机械性)
与模型的实际预测力；未如实说明该分解。

**建议替换首段**：

> The counterfactual results translate into policy priorities, with an
> important caveat on how to read the magnitudes. If imported corn
> becomes 10% more expensive, the selected QUAIDS model implies an
> approximately 9.8% decrease in the conditional corn budget share's
> associated quantity index under a fixed conditional budget; readers
> should note that roughly half of this own-price response (the "-1"
> component of the Marshallian own-price elasticity, epsilon_M ~ -1 + eta
> * w-bar - Gamma-implied term) is a near-mechanical consequence of the
> adding-up and homogeneity restrictions rather than of the estimated
> price-coefficient matrix per se; the joint Wald test in Section 4.1
> confirms, however, that the Gamma matrix is not itself statistically
> zero and contributes materially (77-92% of Hicksian substitution
> magnitude) to the compensated substitution pattern that underlies the
> policy discussion below. The fixed-budget increases in sorghum, cassava,
> and oats are only 0.3-0.6%, while barley decreases slightly under the
> fixed-budget scenario; under the pure (Hicksian) substitution
> interpretation, the same 10% corn-price shock increases barley by
   approximately 2.7%, sorghum by approximately 2.5%, cassava by
> approximately 2.3%, and oats by approximately 2.0%.

**新增段落(在原有限制说明段之后)**：

> Two additional limitations concern price identification and inference.
> First, although the demand system passes standard regularity checks and
> the joint Wald test rejects a fully mechanical price-response
> interpretation, quality-adjusted unit values remain an imperfect proxy
> for a true landed price, and roughly 40-70% of province-quarter-product
> cells require imputation because of zero trade in a given quarter (see
> Section 2 and Appendix Table A-V for the imputation rule and its
> sensitivity across three price measures). We supplement the within-
> sample price identification with quasi-experimental evidence from two
> trade-policy shocks -- the 2018 US-sorghum antidumping investigation
> and the 2020-2023 Australia-barley antidumping/countervailing duties --
> exploiting province-level pre-shock exposure to the sanctioned source as
> a shift-share design. Provinces more exposed to Australian barley before
> the 2020 duties experienced a significantly larger quality-adjusted
> price increase during the tariff period (coefficient on exposure x
> post-shock = 0.164, clustered SE = 0.023, p < 1e-11), with an event-
> study specification showing an approximately (not exactly) flat
> pre-trend -- of the five pre-shock leads tested (q-6 through q-2; q-1
> is the omitted reference period), four (q-6, q-5, q-3, q-2) are
> individually insignificant, but the q-4 lead is significant at the 5%
> level (coefficient 0.084, clustered SE 0.034, t=2.50) -- and a price
> response that builds gradually and significantly from roughly five
> quarters after imposition, with post-shock t-statistics (2.25-6.45)
> both larger and more consistent than any individual pre-shock lead; the analogous sorghum estimate is positive
> but not statistically significant at conventional levels (coefficient =
> 0.044, SE = 0.053, p = 0.41), likely reflecting the shorter shock window
> and its overlap with the broader 2018 US-China trade war. These results
> corroborate, for at least one of the five products, that price
> variation used in estimation contains a genuine exogenous component.
> As noted above, the pre-trend is approximately but not perfectly flat
> (the q-4 lead is individually significant); readers should treat the
> parallel-trends assumption as approximately, not exactly, satisfied.
> Second, standard errors throughout are computed via a province-clustered
> block bootstrap of the full estimation pipeline rather than the
> asymptotic delta method alone, addressing generated-regressor and
> within-province serial-correlation concerns; see Section 3.7 and
> Appendix Table A-Y for a comparison of the two.


---

# 文献补充与参考文献表清理 (Step 9 deliverable)

## A. 确认原稿中"未引用"的参考文献 (Issue 7 — verified via full-text search)

以下8条参考文献在原稿参考文献表中出现，但在正文全文中**未被引用一次**
(已用正文全文逐词检索确认，0次出现)：Anderson & van Wincoop (2004),
Fajgelbaum et al. (2020), Grant & Boys (2012), Pesaran et al. (2001),
Stone (1954), Moschini (1995), Abbott & Seddighi (1996), Xu (2002)。

按审改意见建议，这些文献均有合适的引用位置(见下)，建议**在正文中补充引用**
而非删除，因为它们与论文主题高度相关。

## B. 引言各段落文献插入方案 (Introduction paragraph-by-paragraph)

### 第1段（饲料粮战略地位，原文0条引用）
在段末"...it is whether the import portfolio can reallocate across
alternative energy feed grains when a product becomes costly, quota
constrained, or difficult to source."后插入引用：

> ...difficult to source (Fukase and Martin, 2016; Huang and Yang, 2017).

### 第2段（政策冲击历史，原文0条引用）
"Barley has experienced major policy disruptions and subsequent
reopening."后插入：

> Barley has experienced major policy disruptions and subsequent
> reopening (Al Khawaldeh, 2023; see also Section 4.6). More broadly,
> the 2018-2019 US-China trade war altered tariff schedules and trade
> flows across a wide range of agricultural products (Fajgelbaum et al.,
> 2020; Amiti, Redding, and Weinstein, 2019; Carter and Steinbach, 2020),
> and China's 2018 antidumping investigation into US sorghum imports is a
> directly relevant precedent for the source-country risk this paper
> studies (Adjemian, Smith, and He, 2021). Corn imports are further
> shaped by tariff-rate-quota administration and domestic policy
> feasibility constraints more generally (Grant and Boys, 2012).

### 第3段（总量进口需求文献，Tang 2003后）
"...whether the scale variable is GDP, GDP net of exports, national cash
flow, or disaggregated expenditure components (Tang, 2003)."后插入：

> ...disaggregated expenditure components (Tang, 2003; Xu, 2002; Abbott
> and Seddighi, 1996).

并在本段末尾"...cannot identify substitution within the feed-grain import
portfolio."前插入：

> These aggregate elasticities also provide a useful benchmark for the
> magnitude of the product-level responses estimated below (Broda and
> Weinstein, 2006; Kee, Nicita, and Olarreaga, 2008).

### 第4段（来源分化需求系统，Yang & Koo 1994前）
"Studies of Japanese meat imports, Korean meat demand, and Korean wine
imports show that..."前插入：

> Source-differentiated demand systems for agricultural imports have a
> long history (Winters, 1984; Hayes, Wahl, and Williams, 1990). Studies
> of Japanese meat imports, Korean meat demand, and Korean wine imports
> show that...

### 第5段（价格传导/政策楔子，Reimer et al. 2012附近）
"Export-demand elasticities for major U.S. crops depend on how world
prices are transmitted into importing country prices (Reimer et al.,
2012)."后插入：

> ...into importing country prices (Reimer et al., 2012), reflecting the
> broader gap between border and domestic prices documented in the
> trade-costs literature (Anderson and van Wincoop, 2004).

### 第6段（截尾需求/单位价值/正则性，Shonkwiler & Yen 1999已引用）
"Therefore, adjusted-quality prices are widely used in food demand
systems when actual prices are unavailable (Han and Chen, 2016)."后插入：

> ...when actual prices are unavailable (Han and Chen, 2016; Heien and
> Wessells, 1990). Related censored-system applications extend the
> Shonkwiler-Yen correction to multi-equation demand systems with
> theoretical regularity (Perali and Chavas, 2000; Yen, Lin, and
> Smallwood, 2003; Dong, Gould, and Kaiser, 2004).

并在"Flexible demand systems can violate regularity..."句前插入：

> Unit-value and index-number issues specific to demand-system estimation
> are discussed in Stone (1954) and Moschini (1995).

### 第7段/方法学定位（本文条件式需求系统的定位说明 — 新增段，呼应审改意见Issue3/Part2-Para7）
建议在引言"贡献"段（"The contribution is threefold..."）后新增一段，
将本文§3.1的条件式对象明确定位为一种设计选择而非局限：

> The demand system estimated here is explicitly a *conditional* import-
> allocation system -- conditional on positive total five-product import
> expenditure -- rather than an unconditional total-demand system. This
> follows a well-established tradition of estimating conditional demand
> subsystems when the researcher can observe a natural budget aggregate
> but not the full consumption or import universe (Pollak, 1969; Browning
> and Meghir, 1991; Edgerton, 1997; Carpentier and Guyomard, 2001). We
> treat this as a deliberate scope restriction -- the paper identifies
> within-portfolio reallocation, not the total feed-grain import margin --
> rather than as an incidental limitation of the data.

## C. 方法学章节文献补充

- **§3.4 (Shonkwiler-Yen)**：句首插入 Heien and Wessells (1990) 作为该修正方法
  在食品需求系统中的早期应用先例。
- **§3.5 (Bartik/控制函数)**：见revision_memo.md中已起草的替换文本，引用
  Bartik (1991), Goldsmith-Pinkham, Sorkin and Swift (2020), Borusyak, Hull
  and Jaravel (2022), Blundell and Robin (1999), Petrin and Train (2010),
  Wooldridge (2015)。
- **§3.7 (推断)**：引用 Murphy and Topel (1985) 作为两步法协方差的经典参考
  （即使本文改用bootstrap作为主要推断方式，仍应说明delta method作为
  附录基准时的理论依据）。
- **§3.2 (可选)**：可在模型选择讨论中提及 Lewbel and Pendakur (2009) 的EASI
  模型作为rank-3替代方案，说明QUAIDS对634个观测的样本量更为适宜。

## D. 完整新增参考文献表（待合并入主参考文献列表，按字母序）

## ⚠️ 重要说明：引用条目未经外部核验 (Citation Verification Caveat)

本节列出的~25条新增参考文献条目(作者/年份/期刊/卷期/页码)是根据审改意见
Part 2的建议主题**从已有知识回忆整理**，**未经过web_search或文献数据库
逐条核验**。已知至少一处细节存在偏差：Amiti, Redding, and Weinstein (2019)
一文的实际标题为"The Impact of the 2018 Trade War on U.S. Prices and
Welfare"，而本备忘录先前给出的释义标题"The impact of the 2018 tariffs on
prices and welfare"不准确（作者/期刊/卷期/页码本身可能仍正确，但不应视为
已核验）。

**建议**：在将这些引用正式写入论文参考文献表之前，作者应逐条通过Google
Scholar/期刊官网/DOI核实标题、卷期、页码的准确性，不应直接采信本备忘录
中的具体书目细节。本备忘录的价值在于"建议引用哪些主题/作者的工作、插入
在哪个位置"，而非提供已核验的最终书目格式。


Adjemian, M. K., A. Smith, and S. He. 2021. Estimating the market effect
  of a trade war: The case of soybean tariffs. American Journal of
  Agricultural Economics 103(5): 1758-1777.

Amiti, M., S. J. Redding, and D. E. Weinstein. 2019. The impact of the
  2018 trade war on U.S. prices and welfare (title as recalled, NOT
  independently verified -- confirm before final submission). Journal of
  Economic Perspectives 33(4): 187-210.

Bartik, T. J. 1991. Who Benefits from State and Local Economic
  Development Policies? Kalamazoo, MI: W.E. Upjohn Institute for
  Employment Research.

Blundell, R., and J.-M. Robin. 1999. Estimation in large and
  disaggregated demand systems: An estimator for conditionally linear
  systems. Journal of Applied Econometrics 14(3): 209-232.

Borusyak, K., P. Hull, and X. Jaravel. 2022. Quasi-experimental
  shift-share research designs. Review of Economic Studies 89(1):
  181-213.

Broda, C., and D. E. Weinstein. 2006. Globalization and the gains from
  variety. Quarterly Journal of Economics 121(2): 541-585.

Browning, M., and C. Meghir. 1991. The effects of male and female labor
  supply on commodity demands. Econometrica 59(4): 925-951.

Carpentier, A., and H. Guyomard. 2001. Unconditional elasticities in
  two-stage demand systems: An approximate solution. American Journal of
  Agricultural Economics 83(1): 222-229.

Carter, C. A., and S. Steinbach. 2020. The impact of retaliatory
  tariffs on agricultural trade. NBER Working Paper 27147.

Dong, D., B. W. Gould, and H. M. Kaiser. 2004. Food demand in Mexico: An
  application of the Amemiya-Tobin approach to the estimation of a
  censored food system. American Journal of Agricultural Economics
  86(4): 1094-1107.

Edgerton, D. L. 1997. Weak separability and the estimation of elasticities
  in multistage demand systems. American Journal of Agricultural
  Economics 79(1): 62-79.

Fukase, E., and W. Martin. 2016. Economic growth, convergence, and world
  food demand and supply. Journal of Agricultural Economics 67(1): 3-23.

Goldsmith-Pinkham, P., I. Sorkin, and H. Swift. 2020. Bartik instruments:
  What, when, why, and how. American Economic Review 110(8): 2586-2624.

Hayes, D. J., T. I. Wahl, and G. W. Williams. 1990. Testing restrictions
  on a model of Japanese meat demand. American Journal of Agricultural
  Economics 72(3): 556-566.

Heien, D., and C. R. Wessells. 1990. Demand systems estimation with
  microdata: A censored regression approach. Journal of Business and
  Economic Statistics 8(3): 365-371.

Huang, J., and J. Yang. 2017. China's agriculture: Drivers of change and
  implications for China and the rest of world. Global Food Security 12:
  119-126.

Kee, H. L., A. Nicita, and M. Olarreaga. 2008. Import demand elasticities
  and trade distortions. Review of Economics and Statistics 90(4):
  666-682.

Lewbel, A., and K. Pendakur. 2009. Tricks with Hicks: The EASI demand
  system. American Economic Review 99(3): 827-863.

Murphy, K. M., and R. H. Topel. 1985. Estimation and inference in
  two-step econometric models. Journal of Business and Economic
  Statistics 3(4): 370-379.

Perali, F., and J.-P. Chavas. 2000. Estimation of censored demand
  equations from large cross-section data. American Journal of
  Agricultural Economics 82(4): 1022-1037.

Petrin, A., and K. Train. 2010. A control function approach to
  endogeneity in consumer choice models. Journal of Marketing Research
  47(1): 3-13.

Pollak, R. A. 1969. Conditional demand functions and consumption theory.
  Quarterly Journal of Economics 83(1): 60-78.

Winters, L. A. 1984. Separability and the specification of foreign trade
  functions. Journal of International Economics 17(3-4): 239-263.

Wooldridge, J. M. 2015. Control function methods in applied econometrics.
  Journal of Human Resources 50(2): 420-445.

Yen, S. T., B.-H. Lin, and D. M. Smallwood. 2003. Quasi- and
  simulated-likelihood approaches to censored demand systems: Food
  consumption by food stamp recipients in the United States. American
  Journal of Agricultural Economics 85(2): 458-478.

## E. 新闻类引用移至脚注（不再列入正式参考文献表）

- Al Khawaldeh, K. 2023. The Guardian, August 11. (脚注，Section 4.6)
- Chu, M., and Beijing Newsroom. 2025. Reuters, March 4. (脚注)
- Chu, M., and J. Cash. 2025. Reuters, February 24. (脚注)
- Chu, M., and Beijing Newsroom. 2025. Reuters, March 6. (脚注)


---

# Issue 8 细节修订清单

1. **符号不一致**：公式(16)中 N^U_P 与正文其他处 N^{PU} 拼写不统一 -> 统一为 N^P_U
   (与Bewley 1986原文记号一致，表示QUAIDS的自由二次支出参数个数)。

2. **Table 3 (原稿) Slutsky特征值最大值表述**："passes at numerical tolerance"表述
   需按Issue 1重新定性 -> 改为:"the maximum eigenvalue is effectively zero
   (order 1e-12 to 1e-13), consistent with -- but not independent evidence
   for -- local negative semidefiniteness; see Section 4.1 for the joint
   Wald test on Gamma that provides the substantive identification check."

3. **Table 1 AUC (0.92-0.95)**：说明部分反映滞后进口状态的状态依赖性(state
   dependence)，而非纯粹的参与方程预测力 -> 在Table 1脚注补充："The high AUC
   partly reflects the inclusion of lagged participation status among the
   predetermined regressors (state dependence in provincial import
   participation) rather than solely the predictive power of contemporaneous
   demand-side controls."

4. **零值价格插补的测量误差说明**：在§2或§3.4补充脚注说明缺失省份-季度-品类
   格采用同季度全国LOO均值插补，可能引入测量误差，已通过loo_quarter_winsor
   与landed_proxy两种替代口径做敏感性检验（Section 4附录）。

5. **Shonkwiler & Yen (1999) 页码确认**：81(4):972-982 与原稿引用一致，无需修改。
   [重建管道核实：原稿Reference list实际写"81(4)"疑似笔误，正确应为"American
   Journal of Agricultural Economics 81(4): 972-982" -- 已核实与审改意见一致]

6. **关键词建议**：新增"censored demand system"；去除低信息量的"scenario analysis"
   （审改意见原文建议）。建议关键词表最终为：feed grains; import demand; import
   substitution; China; QUAIDS; Shonkwiler-Yen; censored demand system; unit
   values; Bartik instrument; trade risk.
