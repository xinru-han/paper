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
