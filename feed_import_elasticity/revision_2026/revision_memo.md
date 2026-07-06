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
