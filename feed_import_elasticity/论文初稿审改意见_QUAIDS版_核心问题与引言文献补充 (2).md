# 论文初稿审改意见：Conditional Feed-Grain Import Substitution in China（QUAIDS-SY-Bartik 版）

审阅时间：2026-06-14
审阅对象：论文初稿 docx + `cf_aids_quaids_代码整合总览.md` + `cf_aids_quaids_结果整合总览.md`
总判断：**论文框架、写作和自我限定已经达到可投稿的成熟度（conditional 对象界定、SY、FIML 约束系统、Bewley 选择、delta 推断都齐了）。但存在一个核心实证问题：价格系数矩阵 Γ 在经济上≈0，全套价格/替代弹性约 85% 的量级来自"Γ=0 + 商品正常"的机械恒等式，连 regularity 通过也近乎机械必然。这不一定否定论文，但必须（a）如实检验并披露，（b）把替代结论的表述改为与证据强度匹配，或（c）用政策事件强化价格识别。此外还有推断（三层生成回归量+无聚类）、质量调整价格内生性、弹性口径命名三个方法问题，以及引言引用不足和文献表不一致。** 逐条如下，每条给出可执行的修改方案。

---

## 第一部分：逻辑与方法问题（按严重性排序）

### 问题 1（核心）：价格系数 Γ ≈ 0，替代弹性主要是机械恒等式，而非价格证据

**证据（用你自己的表算出）**。在 Γ=0 时，Hicksian 弹性有一个纯机械基准：`ε^H_ij = η_i·w̄_j − δ_ij`（由加总性与 Slutsky 关系直接推出，与价格数据无关）。把表 7 与该基准对比：

| 项 | 报告值 | Γ=0 机械基准 | 差（=γ 的贡献） |
|---|---:|---:|---:|
| 玉米自身 | −0.735 | −0.755 | +0.020 |
| 高粱自身 | −0.803 | −0.857 | +0.054 |
| 木薯自身 | −0.827 | −0.863 | +0.036 |
| 燕麦自身 | −0.911 | −0.960 | +0.049 |
| 大麦自身 | −0.681 | −0.565 | −0.116 |
| 燕麦-大麦（最大交叉） | +0.351 | +0.185 | +0.166 |

整张 Hicksian 矩阵：**Σ|γ 贡献| / Σ|弹性| = 1.20/7.91 ≈ 15%**。Morishima 全表 ≈ 0.93–1.03，与机械基准 `1 + w̄_j(η_k − η_j)` 差距 ≤0.28。表 6 的 Marshallian **所有交叉项都没有星号**（个个不显著）——这与自身价格弹性"高度显著"并存，正说明显著性来自 `−1 + η w` 的机械部分而非 γ。

**连 regularity 通过也近乎机械**：Γ=0、η 取估计值时，对称化 Slutsky 特征值为 [−0.288, −0.206, −0.172, −0.080, **+0.003**]——本来就在负半定边缘（η 全为 1 时 `S = w̄w̄′ − diag(w̄)` 由柯西-施瓦茨不等式恒负半定）。所以"通过 local negativity（max eig ≈ 1e-13）"主要是 Γ 被压到≈0 的副产品，不宜作为独立成就大书特书（4.1 与 Discussion 目前的写法正是如此）。

**后果**：
- 摘要/4.4/5/6 中"compensated substitution is positive""five products behave as substitutes""barley is a strong compensated substitute"等结论，目前的证据基础是"商品是正常品 + 加总性"，而非"数据识别出了价格替代"。Hicksian 交叉项在 Γ=0、η>0 时**必然为正**——"全部为正所以互为替代品"接近循环论证。
- 情景分析（表 9）的 Hicksian 替代量（+2.0%~+2.7%）本质上是 `η_k·w̄_corn×shock` 的算术，不是价格反应的测量。
- delta 法的 `H0: 弹性=0` 是错误的原假设：机械基准本身远离 0，显著性不含信息。

**为什么 Γ 会≈0（两种解释，必须区分）**：
(a) 真实替代弹性确实近于 Cobb-Douglas（份额对相对价格不敏感）；
(b) 质量调整 + 填补后的价格变量已无有效识别变异（调整回归 R²=0.59–0.89 吸走大半变异；868 格全部填补，缺格用 LOO 全国价——大量价格变异是"全国×品种×季度"层面的，省内相对价格变异所剩无几），γ 被衰减到 0。
这两种解释的政策含义完全相反（"替代确实有限" vs "数据识别不了"），**论文现在无法区分，必须补检验**。

**修改方案（按力度递增，至少做 1–3）**：
1. **报告 Γ 矩阵本身**（点估计+SE），并做 `H0: 所有 γ_ij=0` 的联合 LR/Wald 检验（AIDS 对"γ=0 的 Engel-only 嵌套模型"）。若拒绝不了，全文措辞必须改写。
2. **把弹性对照机械基准检验**：报告 `ε^H_ij − η_i w̄_j`（交叉）与 `ε^H_ii − (η_i w̄_i − 1)`（自身）的估计与 CI，即"价格数据贡献了多少"。这一列才是有信息的推断。
3. **改写结论语言**：把"limited but positive compensated substitution"改为如实版本——"经质量调整与理论约束后，相对价格对份额的解释力在统计上不可区分于零；替代弹性的数值主要由预算结构（Engel 异质性 + 加总性）决定，应视为理论一致的基准刻度而非价格反应的测量"。论文真正被识别、真正站得住的贡献是 **Engel 异质性**（QUAIDS λ 显著、支出弹性排序 0.56→1.31）——把它提为第一贡献。
4. **强化价格识别（治本）**：把 2018Q2 对美高粱 AD、2020Q2 澳麦 80.5% AD/CVD（及 2023Q3 解除）、贸易战关税窗口作为价格的外生移动源，对价格加控制函数（政策工具→相对价格→份额），或至少做"政策窗口内外的 γ 子样本/交互"检验。这些事件制造过真实的大幅相对价格变动；若加了政策识别后 γ 仍≈0，"替代有限"才成为**被识别的结论**而非机械产物——那will be a much stronger paper。

### 问题 2：质量调整价格的构造存在内生性，且是生成回归量

调整回归把 **ln 数量放在右边**（表 2 系数 −0.11~−0.33）。数量与价格由供需同时决定，该系数混合了"批量折扣"与"需求曲线斜率"，据此剔除数量效应会把部分需求侧价格变异一并剔除（方向不明的污染）。同时 adjusted price 是**生成回归量**，其抽样误差没有进入后续推断。

**修改**：(a) 主规格的调整回归**去掉 ln 数量**，只用来源国构成变量 + 省 FE + 年季 FE（构成调整，不做数量调整），把含数量的版本降为稳健性并在正文承认数量系数的同时性问题；(b) 报告 raw LOO 单位价值与 adjusted 两种价格下的弹性作为敏感带（前几轮已证明结果对价格口径敏感，这个敏感带必须进论文而不是只在内部）；(c) 生成回归量问题并入问题 4 的 bootstrap 一起解决。

### 问题 3：弹性口径与代码不一致的表述——现在报告的是"潜在（latent/intensive）"弹性

代码中弹性对**潜在系统份额 g** 求数值导数（`predict_systematic`，未乘 Φ̂），而观测份额是 `Φ̂g + ψφ̂`。所以报告的是"参与概率固定下的内涵边际弹性"，且分母用观测均值份额（Green–Alston 惯例）——这是一个混合口径。论文 3.7 没有说明这一点，而审稿人（和你们前几轮自己的框架）都区分 latent vs observed-censored。

**修改**：(a) 在 3.7 明确命名："elasticities are conditional (intensive-margin) responses holding participation fixed, evaluated at observed mean shares"；(b) 增补 observed-censored 版本（∂w/∂lnp = Φ̂·∂g/∂lnp，因参与方程不含当期价格）作为对照表或附录——两者相差约一个 Φ̂ 倍数，量级差异不小；(c) 在 Discussion 说明外延边际（参与）不在这些弹性里，与政策情景的关系（短期内涵 vs 中期含参与）。

### 问题 4：推断——三层生成回归量 + 面板相关全部被忽略

当前 delta 法基于 `2[Hessian(obj)]^{-1}`（截断 SVD 伪逆），隐含 iid 正态，且把三组前置估计量当作已知：质量调整价格（问题 2）、SY 的 Φ̂/φ̂、Bartik 第一阶段残差 v̂。另外 634 个观测来自 30 省×28 季度，省内序列相关未处理。**当前 SE 几乎必然被低估**；截断 SVD 伪逆还会把弱识别方向（正是 γ 方向！）的方差截掉，让价格弹性显得比实际更精确。

**修改**：主推断改为**省级聚类 block bootstrap 贯穿全管道**（重抽省份 → 重做价格调整、probit、Bartik 第一阶段、FIML → 重算弹性），delta 法降为附录快速参考；至少报告 Hessian 条件数与被截断的奇异值个数，作为识别强度的披露。两步修正的理论参照引 Murphy–Topel (1985)。

### 问题 5：Bartik 工具的引用与论证缺失

正文使用 Bartik 工具但**没有引用任何 Bartik 文献**，也没有按现代标准论证。3.5 的排除限制只有一句话。

**修改**：(a) 引用 Bartik (1991)、Goldsmith-Pinkham, Sorkin & Swift (2020)、Borusyak, Hull & Jaravel (2022)；控制函数引 Blundell & Robin (1999)（需求系统支出内生性的经典 CF 处理，与本文场景完全对口）、Petrin & Train (2010) 或 Wooldridge (2015)。(b) 增加一小段暴露设计论证：识别来自"全国非农进口冲击对不同省份基期暴露的差异"，说明基期份额的确定方式、以及为何该冲击不通过相对饲料粮价格影响份额（排除限制的经济通道）。(c) 承认 just-identified 无法做过度识别检验的地方，补一个 GPSS 式的份额平衡性/敏感性诊断代替。

### 问题 6：Discussion/Conclusion 的因果与政策语言超出证据

- 6 中"the selected QUAIDS model predicts an approximately 9.8% decrease in corn quantity"——这是把 ε≈−0.98（其中 −1 是机械部分）说成模型的预测能力。按问题 1 的措辞方案改写。
- 表 10（来源国风险映射）内容合理，但其依据是新闻报道 + 判断，不是本文估计。Note 已声明，但正文 4.6 的写法（"the demand-system estimates imply..."）会让审稿人质疑。建议明确写"Table 10 is a policy synthesis based on public trade reporting; it is not derived from the econometric model"。
- Guardian/Reuters 新闻条目混在学术参考文献表里（AJAE/Food Policy 格式都不接受）：**改为脚注引用**，并尽量以学术文献替代可替代者（高粱 AD → Adjemian, Smith & He；关税战 → Fajgelbaum et al. 2020 / Carter & Steinbach）。

### 问题 7：参考文献表与正文不一致

文献表中**出现但正文从未引用**（要么补引、要么删除）：Anderson & van Wincoop (2004)、Fajgelbaum et al. (2020)、Grant & Boys (2012)、Pesaran et al. (2001)、Stone (1954)、Moschini (1995)、Abbott & Seddighi (1996)、Xu (2002)。其中 Fajgelbaum、Stone、Moschini、Xu、Abbott & Seddighi 都很容易在引言/方法里找到自然落点（见第二部分），建议补引而非删除。

### 问题 8（小项，快速修）

- 3.6 式(16) 记号 `Nᵁ_P` 与文中 `Nᴾᵁ` 不一致；统一。
- 表 3 中 QUAIDS 最大 Slutsky 特征值 +8.3e-13 写"passes at numerical tolerance"没问题，但按问题 1 改写其解读。
- 表 1 注明 AUC 0.92–0.95 部分来自滞后进口状态的持续性（state dependence），避免被读成参与方程"预测力极强"。
- 2 中 adjusted price "fills all 868 cells"：补一句零格填补价的测量误差方向与参与相关的 caveat。
- Shonkwiler & Yen 页码：81(4): 972–982（正文引用格式已对，确认全文一致）。
- 关键词建议加 "censored demand system"、去掉重复度低的 "scenario analysis"。

---

## 第二部分：引言文献补充（逐段、可直接粘贴）

原则：你要求补的是"表达观点但非本文结论"的句子的经典引用。以下按引言段落给出插入点、建议引文与改写句（英文可直接用）。**所有新增条目集中在文末"新增参考文献清单"，投稿前请逐条核对卷期页码。**

### 第 1 段（饲料粮的战略地位）——目前 0 引用
插入句（段末）：
> "Feed demand has become the dominant driver of China's grain balance as diets shift toward animal protein, and feed-grain trade is correspondingly central to national food-security strategy (Fukase and Martin, 2016; Huang and Yang, 2017; Zhan and Chen, 2021*)."
（*Zhan & Chen 条目请核实；若不稳妥就保留前两条。）

### 第 2 段（各品种的政策扰动史）——目前 0 引用，全是可引证的事实性判断
- 贸易战与农产品报复性关税：
> "...trade-policy shocks have repeatedly affected the landed cost and availability of key feed ingredients (Fajgelbaum et al., 2020; Amiti, Redding and Weinstein, 2019; Carter and Steinbach, 2020*)."
- 高粱暴露于双边摩擦——有一篇专门研究 2018 中国对美高粱反倾销的 AJAE 论文，务必引：
> "Sorghum ... is highly exposed to source-country concentration and bilateral frictions: China's 2018 antidumping investigation against U.S. sorghum triggered large, rapid trade reallocation (Adjemian, Smith and He, 2021*)."
- 玉米配额管理可引 WTO 争端相关分析或综述性贸易政策文献（Grant & Boys, 2012 已在你文献表中，正好补引在"policy feasibility"一句后）。

### 第 3 段（总量进口需求文献）——已有引用，补两条经典
在 "(Tang, 2003)" 之后补：
> "(Xu, 2002; Abbott and Seddighi, 1996)"（两条都在你的文献表里但正文没引；Xu 2002 正是 national cash flow 一句的原始出处，现在这句话观点悬空）。
段末可加一句国际经典弹性文献，供审稿人定位量级：
> "Large cross-country compilations of import-demand elasticities provide the benchmark magnitudes against which product-level estimates can be judged (Kee, Nicita and Olarreaga, 2008; Broda and Weinstein, 2006)."

### 第 4 段（来源国差异化需求系统）——补上经典先行者
在 Yang & Koo (1994) 前补 Hayes, Wahl & Williams (1990)（来源差异化肉类进口需求的更早经典）；Winters (1984)（进口需求中的可分性假设检验，是"product-level system 合理性"的理论出处）：
> "(Winters, 1984; Hayes, Wahl and Williams, 1990; Yang and Koo, 1994; ...)"

### 第 5 段（价格传导与政策楔子）——可保留，补一条
在 Reimer et al. (2012) 处补 Anderson & van Wincoop (2004)（贸易成本楔子的权威综述，已在文献表未被引用）。

### 第 6 段（删截、单位价值、regularity）——补三处经典
- 删截需求的先行方法与后续发展：
> "(Heien and Wessells, 1990; Shonkwiler and Yen, 1999; Perali and Chavas, 2000; Yen, Lin and Smallwood, 2003; Dong, Gould and Kaiser, 2004)"
- 单位价值与质量：Deaton (1988) 已引，建议加 Deaton (1990)（或保持不变）；
- Stone (1954) 与 Moschini (1995)：3.2/3.7 用了 Stone 型指数与单位问题，正文补引这两条（都在文献表里悬空）。

### 第 7 段（本文对象：conditional 系统）——方法框架的经典出处目前缺失
条件需求/两阶段预算的理论谱系必须引，否则 3.1 的对象界定像自创：
> "The conditional import-allocation object follows the theory of conditional demand functions and multistage budgeting (Pollak, 1969; Browning and Meghir, 1991; Edgerton, 1997); conditional elasticities can be converted to total elasticities only with an estimate of the group-expenditure response (Carpentier and Guyomard, 2001), which we leave to future work."
这段同时把你 6 中的 limitation 提前变成有文献支撑的设计选择——审稿人观感完全不同。

### 方法节顺带补引（非引言但同批加入）
- 3.4：Heien & Wessells (1990)（SY 的先行者）；
- 3.5：Bartik (1991)、Goldsmith-Pinkham et al. (2020)、Borusyak et al. (2022)、Blundell & Robin (1999)；
- 3.7：Murphy & Topel (1985)（两步估计的协方差）；
- 3.2 若愿意提替代模型一句话：Lewbel & Pendakur (2009)（EASI 作为 rank-3 备选，说明为何本文选 QUAIDS——参数更少、约束成熟，适合 634 观测的样本）。

### 新增参考文献清单（投稿前逐条核对卷期页码；带 * 的需重点核实）

- Adjemian, M. K., Smith, A., and He, W. 2021. Estimating the market effect of a trade war: The case of sorghum antidumping duties on U.S. exports. *American Journal of Agricultural Economics* 103(5): 1758–1777. *
- Amiti, M., Redding, S. J., and Weinstein, D. E. 2019. The impact of the 2018 tariffs on prices and welfare. *Journal of Economic Perspectives* 33(4): 187–210.
- Bartik, T. J. 1991. *Who Benefits from State and Local Economic Development Policies?* Kalamazoo, MI: W.E. Upjohn Institute.
- Blundell, R., and Robin, J.-M. 1999. Estimation in large and disaggregated demand systems: An estimator for conditionally linear systems. *Journal of Applied Econometrics* 14(3): 209–232.
- Borusyak, K., Hull, P., and Jaravel, X. 2022. Quasi-experimental shift-share research designs. *Review of Economic Studies* 89(1): 181–213.
- Broda, C., and Weinstein, D. E. 2006. Globalization and the gains from variety. *Quarterly Journal of Economics* 121(2): 541–585.
- Browning, M., and Meghir, C. 1991. The effects of male and female labor supply on commodity demands. *Econometrica* 59(4): 925–951.
- Carpentier, A., and Guyomard, H. 2001. Unconditional elasticities in two-stage demand systems: An approximate solution. *American Journal of Agricultural Economics* 83(1): 222–229.
- Carter, C. A., and Steinbach, S. 2020. The impact of retaliatory tariffs on agricultural and food trade. NBER Working Paper 27147. *
- Dong, D., Gould, B. W., and Kaiser, H. M. 2004. Food demand in Mexico: An application of the Amemiya–Tobin approach to the estimation of a censored food system. *American Journal of Agricultural Economics* 86(4): 1094–1107.
- Edgerton, D. L. 1997. Weak separability and the estimation of elasticities in multistage demand systems. *American Journal of Agricultural Economics* 79(1): 62–79.
- Fukase, E., and Martin, W. 2016. Who will feed China in the 21st century? Income growth and food demand and supply in China. *Journal of Agricultural Economics* 67(1): 3–23.
- Goldsmith-Pinkham, P., Sorkin, I., and Swift, H. 2020. Bartik instruments: What, when, why, and how. *American Economic Review* 110(8): 2586–2624.
- Hayes, D. J., Wahl, T. I., and Williams, G. W. 1990. Testing restrictions on a model of Japanese meat demand. *American Journal of Agricultural Economics* 72(3): 556–566.
- Heien, D., and Wessells, C. R. 1990. Demand systems estimation with microdata: A censored regression approach. *Journal of Business & Economic Statistics* 8(3): 365–371.
- Huang, J., and Yang, G. 2017. Understanding recent challenges and new food policy in China. *Global Food Security* 12: 119–126.
- Kee, H. L., Nicita, A., and Olarreaga, M. 2008. Import demand elasticities and trade distortions. *Review of Economics and Statistics* 90(4): 666–682.
- Lewbel, A., and Pendakur, K. 2009. Tricks with Hicks: The EASI demand system. *American Economic Review* 99(3): 827–863.
- Murphy, K. M., and Topel, R. H. 1985. Estimation and inference in two-step econometric models. *Journal of Business & Economic Statistics* 3(4): 370–379.
- Perali, F., and Chavas, J.-P. 2000. Estimation of censored demand equations from large cross-section data. *American Journal of Agricultural Economics* 82(4): 1022–1037.
- Petrin, A., and Train, K. 2010. A control function approach to endogeneity in consumer choice models. *Journal of Marketing Research* 47(1): 3–13.
- Pollak, R. A. 1969. Conditional demand functions and consumption theory. *Quarterly Journal of Economics* 83(1): 60–78.
- Winters, L. A. 1984. Separability and the specification of foreign trade functions. *Journal of International Economics* 17(3–4): 239–263.
- Wooldridge, J. M. 2015. Control function methods in applied econometrics. *Journal of Human Resources* 50(2): 420–445.
- Yen, S. T., Lin, B.-H., and Smallwood, D. M. 2003. Quasi- and simulated-likelihood approaches to censored demand systems: Food consumption by food stamp recipients in the United States. *American Journal of Agricultural Economics* 85(2): 458–478.

---

## 第三部分：修改优先级路线图

| 优先级 | 事项 | 工作量 | 不做的后果 |
|---|---|---|---|
| P0 | 问题 1 之 1–3：报告 Γ + 联合检验 + 对照机械基准 + 改写替代结论 | 中（代码已有参数，主要是新表+改稿） | 审稿人自己算出机械基准，直接质疑核心结论 |
| P0 | 问题 6/7：新闻引用移脚注、文献表一致性、补 Bartik 引用 | 小 | desk reject 风险的格式硬伤 |
| P1 | 问题 3：弹性口径命名 + observed-censored 对照表 | 小-中 | 口径被质疑时无从回应 |
| P1 | 问题 4：省级聚类全管道 bootstrap | 中 | SE 可信度被否 |
| P1 | 第二部分全部引言补引 | 小 | 引言单薄，观点悬空 |
| P2 | 问题 2：去数量的构成调整价 + 两口径敏感带 | 中 | 价格构造被质疑 |
| P2 | 问题 1 之 4：政策事件强化价格识别 | 大 | 论文停留在"理论基准刻度"层级；做了则可上一个档次 |

一个诚实的定位建议：如果不做 P2 的政策识别，这篇论文的可辩护贡献是"**中国饲料粮进口组合的删截、理论一致的 Engel 结构 + 理论约束下的替代基准刻度**"，适合 Food Policy / JAE / AEPP 定位；做了政策价格识别、且 γ 从政策变异中活过来（或被更有力地判零），才是冲 AJAE 的形态。
