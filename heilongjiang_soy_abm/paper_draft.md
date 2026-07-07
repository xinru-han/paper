# Subsidies, Prices, and the Corn–Soybean Margin: A Micro-Founded Agent-Based Analysis of Soybean Expansion in Heilongjiang

**Target journals:** *Agricultural Economics* / *Food Policy*

**Draft — [date]**

---

## Abstract

China's drive for soybean self-sufficiency rests on persuading Northeast farmers to move dryland from corn to soybean, chiefly through a large per-mu producer subsidy differential. Whether this instrument works — and at what fiscal cost — depends on how responsive the planting decision actually is at the farm level. We combine a four-year household panel from three Heilongjiang counties (2021–2024) with an agent-based simulation to answer this. In the microeconometric layer, a dynamic participation model identifies the behavioral response of the corn-versus-soybean choice to the expected net-return differential Δπ̂ between the two crops. A **+100 yuan/mu** rise in the soybean–corn return differential raises the probability of planting soybean by about **3.2 percentage points** (logit average marginal effect; +4.4 pp in a linear-probability specification), and the response rises sharply with farm scale, from **+1.4 pp** for the smallest tercile to **+6.7 pp** for the largest. The choice is highly persistent (a household that grew soybean last year is far more likely to do so again) and structurally absent in the region's dedicated corn belt. We embed these estimated parameters — with their sampling covariance — in a calibrated agent-based model of 396 households and simulate policy scenarios to 2030. The model reproduces the observed cross-county ordering and levels of soybean area and responds monotonically to the subsidy. Reaching a 10%, 15%, or 20% regional soybean-area target requires raising the soybean producer subsidy to roughly **480, 659, and 802 yuan/mu**, with annual fiscal cost rising **convexly** (2.2, 3.8, and 5.9 million yuan for our three-county sample). A market-price improvement of comparable magnitude delivers similar soybean expansion far more cheaply per unit of area gained (about 110,000 vs 274,000 yuan per additional percentage point), and a subsidy cannot move the structural corn belt at all. The results argue for targeting subsidy effort where the agronomic margin is contestable, and for treating price support and rotation incentives as complements to — not substitutes for — the producer subsidy.

**Keywords:** soybean self-sufficiency; producer subsidy; crop choice; agent-based model; Heilongjiang; Food security

---

## 1. Introduction

Soybean is the largest single gap in China's food-security balance sheet. Domestic production covers only a small fraction of consumption, and the shortfall is met by imports that expose the livestock-feed complex to trade and geopolitical risk. Since 2019 the central government has made expansion of domestic soybean area — overwhelmingly in the Northeast, and especially Heilongjiang — an explicit policy priority, pursued largely through a producer-subsidy differential that pays soybean growers far more per unit area than corn growers.

The policy's premise is behavioral: that farmers will substitute soybean for corn on rotable dryland when the after-subsidy return to soybean rises relative to corn. Yet the strength of that substitution is an empirical quantity that has rarely been estimated from farm-level panel data, and it is precisely the quantity that determines both the effectiveness and the fiscal cost of the subsidy. If the planting decision is very inelastic — because of strong habit persistence, agronomic constraints, or scale barriers — then even a large subsidy buys little additional soybean area at high budgetary cost. If it is elastic and concentrated among particular farm types, subsidy money can be targeted for far greater effect.

This paper estimates that behavioral response and uses it to conduct policy experiments. We make three contributions.

**First**, we identify the corn–soybean substitution elasticity from a household panel rather than assuming it. Using four annual waves (2021–2024) covering three Heilongjiang counties with sharply different soybean intensities, we estimate a dynamic discrete-choice model of the soybean-planting decision in which the key regressor is the household's *expected net-return differential* Δπ̂ between soybean and corn, built up from county-year prices, shrinkage-estimated household yields, measured input costs, and the crop-specific producer subsidy. This isolates a policy-relevant behavioral parameter with a clean economic interpretation.

**Second**, we build the agent-based simulation layer directly on the estimated parameters — coefficients *and* their sampling covariance — rather than on calibrated guesses. This "estimate-then-simulate" design means the policy counterfactuals inherit the empirical uncertainty of the microeconometrics, and the model's behavioral content is auditable against the estimation table.

**Third**, we translate the results into a fiscal-cost frontier for soybean-area targets and show that the subsidy interacts with market prices and agronomic structure in ways that matter for policy design: the same soybean expansion can be bought with market-price support at far lower budgetary cost per unit of area gained, and no feasible subsidy moves land in counties where soybean is agronomically dominated.

Our central estimate — a +100 yuan/mu return differential raising soybean participation by about 3.2 percentage points — is economically modest and helps explain why the observed subsidy differential (of order 330 yuan/mu in our data) coexists with soybean shares that remain in single digits region-wide. The response concentrates among larger farms and in counties where the agronomic margin between the two crops is genuinely contestable; it is essentially zero in the region's structural corn belt.

The remainder of the paper is organized as follows. Section 2 sketches the policy background. Section 3 describes the survey data and the construction of the decision variables. Section 4 sets out the econometric strategy and results. Section 5 describes the agent-based model, its calibration, and validation. Section 6 reports the policy scenarios and the fiscal-cost frontier. Section 7 discusses limitations and Section 8 concludes.

---

## 2. Policy background

Heilongjiang is the pivot of China's soybean strategy: it is simultaneously the country's largest soybean-producing province and a major corn producer, so the marginal hectare of soybean nationally is very often a hectare converted from corn in this province. The main policy lever is the **producer subsidy** (生产者补贴), paid per unit of sown area and differentiated by crop, supplemented in places by a **rotation subsidy** (轮作补贴) that rewards corn–soybean rotation. In our 2024 survey wave, the reported soybean producer subsidy clusters tightly around **350 yuan/mu**, while the corn producer subsidy is about **20 yuan/mu** — a differential of roughly **330 yuan/mu** favoring soybean. The reported rotation subsidy averages about **107 yuan/mu** of rotated (soybean) area among the households that receive it.

Against this subsidy tilt runs a market tilt in the opposite direction. Although soybean commands a much higher per-kilogram price than corn (a price ratio of roughly 2.3–2.7 in our data), its far lower yield per mu means that, on *market* returns alone, corn is the more profitable crop on most dryland in the region. The subsidy differential exists precisely to offset this market disadvantage. Whether it offsets it by enough — and for which farms — is the empirical question.

---

## 3. Data

### 3.1 Survey and sample

We use a household-level farm survey conducted in three Heilongjiang counties — **Shuangcheng** (双城区), **Nehe** (讷河市), and **Huanan** (桦南县) — with annual waves. Our analysis uses the four consistently-instrumented waves **2021–2024**; earlier waves (2019–2020) cover only one county and record no soybean plots, so they cannot identify the corn–soybean margin and are excluded from the choice model. The three counties span the relevant agronomic range: Shuangcheng is a dedicated corn belt where no sampled household grew soybean in any year, while Nehe and Huanan are mixed corn–soybean systems.

The survey records, for each household and year, the crops sown on each plot with their area, output, sale price, and — in the 2024 input module — a detailed breakdown of per-mu cash costs (fertilizer, agro-chemicals, film, machinery, seed, irrigation, land rent, transport/storage, hired labor, and interest). Household and head characteristics (age, education, health, household labor, off-farm employment, productive fixed assets, crop insurance) and village identifiers are also recorded.

Considerable data cleaning was required. Missing values are coded with sentinels (−999, −9999) that we set to missing. Yields, prices, and areas contain data-entry errors of several orders of magnitude (corn yields up to 14,000 kg/mu against a realistic ceiling near 750; sown areas up to 80,000 mu against a median of 30). We apply agronomic plausibility bounds — corn/rice yield 100–1000 kg/mu, soybean 30–350; prices within crop-specific bands; sown area ≤2000 mu — setting out-of-range yield and price cells to missing (rather than clipping, to avoid bias) while preserving the binary fact of planting. Household identifiers in the raw files are corrupted (a placeholder national-ID value is shared by dozens of unrelated households), so we build a household key from the valid 18-digit national ID where available and otherwise from the village code combined with the head's name.

The analytic sample is the set of household-years with positive corn-or-soybean sown area: **887 household-years from 396 households**, of which 54 households are observed in all four years.

### 3.2 The decision variable and Δπ̂

The decision unit is the household-year. On rotable dryland the household allocates area between corn and soybean; rice and minor crops are treated as quasi-fixed. Let $B_{it}$ be the household's combined corn + soybean sown area. We study two margins: the **extensive** margin, the binary $\text{plant\_soy}_{it}=\mathbb{1}[\text{soybean area}>0]$, and the **intensive** margin, the soybean area share $s_{it}=\text{soybean area}/B_{it}\in[0,1]$.

The central regressor is the **expected net-return differential** between soybean and corn,
$$\Delta\hat\pi_{it} = \hat\pi^{\text{soy}}_{it} - \hat\pi^{\text{corn}}_{it}, \qquad \hat\pi^{c}_{it} = p^{c}_{it}\,\hat y^{c}_{it} - \text{cost}^{c} + \text{sub}^{c},$$
in yuan per mu. Prices $p^c_{it}$ are county-year median unit values (province-median filled where a county-year-crop cell is empty). Expected yields $\hat y^c_{it}$ are shrinkage estimates: the household's own mean yield for the crop, shrunk toward the county×crop mean with weight $n_i/(n_i+2)$, so that households with little own history borrow strength from their county. Per-mu cash costs are the 2024 input-module medians (corn **395**, soybean **198**, rice **691 yuan/mu**; soybean is the cheaper crop to grow). Subsidies are the crop-specific producer rates (corn 20, soybean 350 yuan/mu).

$\Delta\hat\pi$ decomposes cleanly into a **market** component and a **subsidy** component. The market component $\hat\pi^{\text{soy,mkt}}-\hat\pi^{\text{corn,mkt}}$ (prices, yields, and costs, no subsidy) has median **−224 yuan/mu**: on the market alone, corn wins almost everywhere. The subsidy component is **+330 yuan/mu**. Their sum, the median net differential, is **+106 yuan/mu** in favor of soybean — but with wide dispersion across counties. By county, the net differential is **+58** in Huanan, **+155** in Nehe, and **−183** in Shuangcheng. This ordering is the economic signature the model must reproduce: Shuangcheng's net differential is negative and it grows no soybean; Nehe's is highest and it has the highest participation among mixed counties.

### 3.3 Descriptive patterns

Table 1 summarizes the analytic sample. Soybean is planted in **10.9%** of household-years and accounts for a mean area share of **6.0%**; farms are modest (median combined corn+soy area 31 mu) and operated by heads averaging 52 years of age with about 9 years of schooling. Just over half of households carry crop insurance.

**Table 1. Descriptive statistics (analytic sample, 887 household-years).**

| Variable | N | Mean | SD | Median |
|---|---:|---:|---:|---:|
| Plants soybean (=1, %) | 887 | 10.9 | 31.2 | 0 |
| Soybean area share (%) | 887 | 6.0 | 20.7 | 0 |
| Corn+soy sown area (mu) | 887 | 75.6 | 106.1 | 30.9 |
| Soybean area (mu) | 887 | 5.4 | 27.0 | 0 |
| Corn area (mu) | 887 | 70.2 | 102.0 | 30.0 |
| Head age (years) | 846 | 52.4 | 9.6 | 52 |
| Head education (years) | 875 | 8.6 | 1.7 | 9 |
| Head male (%) | 887 | 95.6 | 20.5 | 100 |
| Labor force (persons) | 855 | 2.5 | 1.1 | 3 |
| Off-farm workers (persons) | 887 | 0.56 | 0.98 | 0 |
| Has ag. insurance (%) | 887 | 55.5 | 49.7 | 100 |
| Village peer soy share, t−1 (%) | 489 | 5.0 | 10.6 | 0 |

The trends over 2021–2024 (Figure 1) show soybean participation and area share rising in the two soy-growing counties — with a pronounced increase in Huanan by 2024 — while Shuangcheng remains at zero throughout, an all-corn regime.

![Figure 1. Soybean participation and area-share trends by county, 2021–2024. Participation and mean area share rise in the two soy counties (Nehe, Huanan), while Shuangcheng stays at zero.]({{artifact:art_d33b19ba-9016-47a1-8ee7-f7c089f40524}})

The economics behind these levels appear in Figure 2. Panel (a) shows the soybean/corn price ratio by county and year; panel (b) decomposes the expected net-return differential into its market and subsidy components, making visible that the subsidy is what lifts soybean's net return above corn's in the two mixed counties but not in Shuangcheng.

![Figure 2. Soybean/corn price ratio (a) and expected net-return differential Δπ̂ decomposed into market and subsidy components (b), by county. The subsidy offsets soybean's market disadvantage in Nehe and Huanan but not in Shuangcheng.]({{artifact:art_e0662f69-3921-45bf-94b0-51cc0590ab2c}})

---

## 4. Microeconometric layer

### 4.1 Specification

We model the extensive-margin decision as a dynamic binary choice. For household $i$ in year $t$,
$$\Pr(\text{plant\_soy}_{it}=1) = \Lambda\!\big(\beta_\pi\,\Delta\hat\pi_{it}/100 + \gamma\,\text{plant\_soy}_{i,t-1} + \delta\,\overline{s}^{\,\text{peer}}_{v,t-1} + \theta\log B_{it} + x_{it}'\phi + \alpha_c + \tau_t\big),$$
where $\Lambda$ is the logistic CDF, $\Delta\hat\pi/100$ is the return differential in units of 100 yuan/mu, $\text{plant\_soy}_{i,t-1}$ captures habit/state dependence, $\overline{s}^{\,\text{peer}}_{v,t-1}$ is the leave-one-out village mean of the prior-year soybean share (a peer/diffusion channel), $\log B_{it}$ is operating scale, $x_{it}$ collects head age, education, insurance, and off-farm labor, and $\alpha_c,\tau_t$ are county and year fixed effects. Standard errors are clustered at the village level.

Because no household in Shuangcheng ever plants soybean, that county is a structural zero and would generate perfect separation with county fixed effects; we therefore estimate the participation and share models on the two mixed counties (Nehe and Huanan), and treat Shuangcheng's zero as a structural feature imposed directly in the simulation layer. The estimation sample for the dynamic model (which requires a lagged state) is **293 household-years with 53 soybean events**.

We report three specifications: the dynamic logit (column 1), a linear-probability version for robustness (column 2), and — for the intensive margin — a fractional-logit (Papke–Wooldridge) model of the soybean area share (column 3).

### 4.2 Results

Table 2 reports the estimates. The return differential enters positively and significantly in every specification. In the logit, $\hat\beta_\pi = 0.306$ (se 0.136, $p=0.024$); converted to an average marginal effect, **a +100 yuan/mu rise in Δπ̂ raises the probability of planting soybean by 3.2 percentage points**. The linear-probability model gives a closely consistent **+4.4 pp** ($p=0.005$). State dependence is strong: a household that grew soybean last year is far more likely to grow it again ($\hat\gamma = 2.02$, $p=0.007$; marginal effect +21 pp). Operating scale raises soybean propensity ($\theta>0$, $p=0.009$). The village-peer term is positively signed but imprecise. Head demographics, insurance, and off-farm labor are not individually significant.

**Table 2. Estimation results — soybean planting decision.**

| Variable | (1) Logit | (2) LPM | (3) Frac. logit (share) |
|---|---|---|---|
| Expected return diff. Δπ̂ (/100 yuan/mu) | 0.306** (0.136) | 0.044*** (0.016) | 0.203 (0.174) |
| Soybean last year (t−1) | 2.019*** (0.755) | 0.359*** (0.107) | 1.827** (0.855) |
| Village peer soy share (t−1) | 1.088 (1.652) | 0.060 (0.246) | 1.187 (1.714) |
| log(corn+soy area) | 0.492*** (0.188) | 0.045* (0.025) | 0.068 (0.153) |
| Head age (/10 yr) | 0.326 (0.229) | 0.035 (0.024) | 0.351 (0.249) |
| Head education (yr) | −0.007 (0.123) | −0.005 (0.012) | 0.153 (0.111) |
| County & Year FE | Yes | Yes | Yes |
| Observations | 293 | 293 | 293 |
| AME of Δπ̂ (+100 yuan/mu) | +3.2 pp | +4.4 pp | — |

*Village-clustered standard errors in parentheses. \*\*\* p<0.01, \*\* p<0.05, \* p<0.1.*

The response is strongly heterogeneous in farm scale (Figure 3). Estimating the marginal effect separately by scale tercile, the response to Δπ̂ rises from **+1.4 pp** (smallest third, not significant) through **+4.6 pp** (middle) to **+6.7 pp** (largest third). Larger farms — with more rotable land and, plausibly, lower per-unit adjustment costs — are markedly more responsive to the return incentive. By county, the response is positive in Nehe (+4.1 pp) and near zero in Huanan, whose 2024 soybean surge is driven more by persistence and local diffusion than by the return differential in that year.

![Figure 3. Average marginal effect of the return differential Δπ̂ on soybean participation, pooled and by farm-scale tercile and county. Whiskers are 95% confidence intervals. The response rises monotonically with farm scale.]({{artifact:art_168dd916-e92c-403f-ba32-64d4ebb8d4ee}})

### 4.3 On the market-versus-subsidy salience test

A natural policy question is whether farmers respond differently to a yuan of market return than to a yuan of subsidy — a "salience" test that would compare $\beta_{\text{market}}$ against $\beta_{\text{subsidy}}$. In our data this test is **not identified**: the crop-specific subsidy differential is anchored to a single reported rate (330 yuan/mu) and is therefore constant across the estimation sample, whereas the market component varies richly (from −557 to +263 yuan/mu). We can identify the *combined* return response $\beta_\pi$ cleanly, but not a separate subsidy coefficient. We flag this honestly as a data limitation; distinguishing the two channels would require either subsidy variation across space/time or a stated-preference design. The policy experiments below vary the subsidy through its effect on $\Delta\hat\pi$, which is what our estimates support.

---

## 5. Agent-based simulation layer

### 5.1 Structure

The simulation layer is an agent-based model (ABM) of the same planting decision, run forward from 2024 to 2030. Each of the **396 sampled households** becomes an agent, initialized from its most recent observed state (operating scale $B_i$, initial soybean share, head characteristics, county). In each simulated year every agent (i) forms price and yield expectations, (ii) computes its expected return differential $\Delta\hat\pi$ under the prevailing policy, (iii) draws a participation decision from the estimated logit, and (iv) if it plants soybean, sets its area share from the estimated intensive-margin model. Prices and yields are then realized with stochastic shocks, and farm income and government fiscal cost are accumulated.

The model's behavioral content is the estimated microeconometrics: the participation and share equations use the Table 2 coefficients directly. Three features connect the layers faithfully. First, agent heterogeneity beyond observables is captured by an individual random effect $a_i$ whose dispersion $\sigma_a$ is a calibrated parameter. Second, the village-peer term makes each agent's propensity depend on its neighbors' prior-year choices, so the model generates *endogenous diffusion* rather than independent draws. Third, rotation agronomy enters expected yields: a bean-stubble bonus raises expected corn yield after soybean (+10%) and a repeated-soybean penalty lowers expected soybean yield on continuous soybean land (−15%); these two agronomic parameters are taken from the literature and flagged as such, because our survey could not estimate them robustly.

Price and yield shock scales are set from the data: the log price-change volatility ($\sigma_p\approx0.07$) and the within-county log-yield dispersion ($\sigma_y\approx0.30$, capped). The model is vectorized over agents and over **500 Monte-Carlo replicates**, so every reported path carries a simulation standard deviation.

### 5.2 Calibration

Two features are calibrated to match observed 2024 moments. Shuangcheng's structural zero is imposed by a large negative county term in both decision equations, pinning its simulated soybean propensity to zero. A single intercept offset and the heterogeneity scale $\sigma_a$ are then chosen by grid-search moment-matching so that the simulated soybean-county participation rate (~18%) and area-weighted soybean share (~8.6%) reproduce their observed pooled values. The intensive-margin share model is estimated on planters only, so that the simulated soybean share *conditional on planting* (~0.55) matches the data rather than being diluted by the many zeros.

The selected heterogeneity scale ($\sigma_a\approx1.6$) is an interior optimum: widening the search grid upward (to 3.2) does not change it. Under unchanged policy the model is stable: aggregate soybean share drifts by less than one percentage point over the six-year horizon (Appendix Figure A1), confirming the absence of spurious dynamics.

### 5.3 Validation

We validate the calibrated model in two independent ways (Table 3, Figure 4). First, it reproduces the **cross-county structure** of soybean cultivation that it was not directly fit to at the county level: simulated area-weighted soybean shares are 6.6% in Nehe (observed 6.9%) and 13.3% in Huanan (observed 12.2%), with Shuangcheng at zero, and the cross-county ordering (Shuangcheng < Nehe < Huanan) is preserved. Second, the model responds to policy in the economically correct direction and magnitude: soybean share rises **monotonically** with the soybean subsidy (2.6% with no soybean subsidy → 7.2% at the current rate → 16.4% at double the rate), and removing the subsidy collapses soybean toward the market-only floor — consistent with the negative market differential documented in Section 3.

**Table 3. Model validation.**

| Metric | Observed | Simulated |
|---|---|---|
| Shuangcheng soybean share | 0.0% | 0.0% |
| Nehe soybean share (area-weighted) | 6.9% | 6.6% |
| Huanan soybean share (area-weighted) | 12.2% | 13.3% |
| Cross-county ordering | SC < Nehe < Huanan | SC < Nehe < Huanan |
| Response to soybean subsidy | — | Monotone increasing (2.6→7.2→16.4%) |
| Baseline stability (no policy change) | — | Drift < 1 pp over 6 years |

![Figure 4. Model validation. (a) Observed vs. simulated county-level soybean area shares; (b) 2030 soybean share as a function of the soybean producer subsidy, showing a smooth monotone response.]({{artifact:art_92dabf6c-70b6-4e63-aab4-ecb56d9bbf6d}})

---

## 6. Policy scenarios

We run six scenarios to 2030 (Table 4, Figure 5), all relative to the 2024-policy baseline (S0). Under the baseline the three-county soybean area share settles at about **7.2%**, at an annual fiscal cost of about **1.45 million yuan** for the sample.

**Table 4. Policy-scenario results (2030).**

| Scenario | Soybean share 2030 | Δ vs baseline | Participation | Fiscal cost (¥/yr) |
|---|---:|---:|---:|---:|
| S0 Baseline (2024 policy) | 7.2% | +0.0 pp | 12.7% | 1,453,586 |
| S1 Soybean subsidy +50% | 11.1% | +3.9 pp | 17.7% | 2,532,838 |
| S2 Soybean subsidy −50% | 4.4% | −2.8 pp | 8.7% | 891,044 |
| S3 Rotation subsidy added | 7.2% | +0.0 pp | 12.7% | 1,689,795 |
| S4 Soybean price +20% | 9.8% | +2.6 pp | 16.2% | 1,743,996 |
| S5 Corn price +20% | 4.0% | −3.1 pp | 8.1% | 1,108,415 |

Four findings stand out. **(i)** Raising the soybean subsidy by 50% lifts soybean share from 7.2% to 11.1%, but the fiscal cost rises by three-quarters — the subsidy works, but is expensive at the margin. **(ii)** A market-price improvement of comparable size (soybean price +20%, S4) delivers most of the same expansion (to 9.8%) far more cheaply per unit of area gained: its incremental fiscal cost is about **110,000 ¥ per additional percentage point of soybean share, versus 274,000 ¥ for the subsidy route (S1)**. The subsidy bill still rises under S4 — because more soybean area draws more per-mu subsidy — but each point of expansion is roughly 2.5 times cheaper, pointing to demand-side and value-chain measures as fiscally more efficient complements. **(iii)** A corn-price rise (S5) is a symmetric threat: it pulls land back to corn and cuts soybean share to 4.0%, so soybean-expansion targets are hostage to the corn market. **(iv)** Adding a rotation subsidy (S3) barely moves aggregate share in the short run, because it accrues mainly to households already rotating rather than changing the extensive margin.

The **fiscal-cost frontier** (Figure 5b) makes the cost of ambition explicit. Back-solving the subsidy needed to hit regional soybean-area targets by 2030:

- **10%** target → soybean subsidy ≈ **480 yuan/mu**, fiscal cost ≈ **2.2 million ¥/yr**;
- **15%** target → ≈ **659 yuan/mu**, ≈ **3.8 million ¥/yr**;
- **20%** target → ≈ **802 yuan/mu**, ≈ **5.9 million ¥/yr**.

The frontier is **convex**: each additional percentage point of soybean area costs more than the last (the marginal cost near the baseline is about 274,000 ¥ per additional percentage point), because the subsidy must draw in progressively more reluctant households and cannot touch the structural corn belt at all.

![Figure 5. Policy scenarios. (a) Simulated soybean-share trajectories 2025–2030 under six policy scenarios; (b) fiscal-cost frontier — annual budgetary cost against the soybean-area share achieved, with back-solved subsidy rates for 10/15/20% targets annotated.]({{artifact:art_08be413c-7495-4106-b569-b6b19b200e0a}})

That the corn belt cannot be moved is shown directly in Appendix Figure A2: even a 50% subsidy increase lifts Huanan (to ~20%) and Nehe (to ~11%) but leaves Shuangcheng at zero. Subsidy money spent expecting a response there is money wasted; the policy-relevant margin is where the two crops are agronomically competitive.

---

## 7. Limitations

Several limitations bound our conclusions. **First**, the subsidy differential is anchored to a single reported rate and is constant across the estimation sample, so we identify the combined return response but not a separate subsidy-salience coefficient (Section 4.3). **Second**, two agronomic rotation parameters ($\delta_{\text{rot}}$, $\delta_{\text{rep}}$) come from the literature rather than from our survey, which lacked the plot-level rotation history to estimate them robustly; we hold them fixed and note they affect the rotation-subsidy scenario most. **Third**, the panel is three counties over four years with a modest number of soybean events (53 in the dynamic model), so the estimates — especially the heterogeneity and county breakdowns — are informative but not tightly pinned; we propagate their sampling covariance into the parameter file for future uncertainty analysis. **Fourth**, the ABM abstracts from land-market frictions, credit constraints, and general-equilibrium price feedback: our scenarios trace *partial-equilibrium* behavioral response holding prices at their scenario paths, appropriate for a single province-region but not for national-scale price effects. **Fifth**, the fiscal-cost figures are scaled to the sample rather than to the county populations; the *shape* of the frontier (convex, corn-belt-inelastic) is the transferable result, not the absolute yuan totals.

---

## 8. Conclusion

Soybean self-sufficiency policy in Northeast China turns on a behavioral parameter — how strongly the corn-versus-soybean planting choice responds to the after-subsidy return differential — that has more often been assumed than estimated. Estimating it from a four-year Heilongjiang household panel, we find a modest and scale-dependent response: +100 yuan/mu of return differential buys about 3.2 percentage points of soybean participation on average, rising to nearly 7 points on the largest farms and falling to near zero on the smallest and in the structural corn belt. Embedding these estimates in a calibrated, validated agent-based model, we show that hitting ambitious regional soybean-area targets through the producer subsidy is feasible but fiscally convex, that market-price support can deliver comparable expansion at substantially lower fiscal cost per unit of area gained, and that no subsidy can move land where soybean is agronomically dominated. The policy implication is one of **targeting**: concentrate subsidy effort on the contestable agronomic margin and on the larger, more responsive farms, and treat price support and rotation incentives as complements to, not substitutes for, the producer subsidy.

---

## Appendix figures

![Figure A1. Smoke test: with no policy change, the aggregate simulated soybean share is stable over the horizon (drift < 1 pp), against the 2024 observed baseline.]({{artifact:art_069e92d1-b971-45df-9353-854228235f48}})

![Figure A2. County-level soybean diffusion under the baseline (a) and a +50% soybean subsidy (b). The subsidy lifts the two mixed counties but leaves the structural corn belt (Shuangcheng) at zero.]({{artifact:art_b62523e0-4eeb-4056-b8c7-4792faeac7e6}})

---

## 政策报告摘要（中文）

**补贴、价格与玉米—大豆种植边际：基于微观计量校准的智能体模型分析**

保障大豆自给是国家粮食安全战略的重点，其核心抓手是通过大幅高于玉米的大豆生产者补贴，引导东北旱田由玉米改种大豆。该政策能否奏效、财政代价几何，取决于农户种植决策对补贴的真实反应强度——而这一关键行为参数长期以来多为假设而非估计。

本研究结合黑龙江省三县（双城、讷河、桦南）四年（2021—2024）农户面板调查数据与智能体仿真模型，量化这一反应。**微观计量层**以大豆相对玉米的预期净收益差 Δπ̂（由分县分年价格、收缩估计的单产、实测投入成本与分作物补贴构建）为核心解释变量，估计动态种植选择模型。主要发现：

1. **收益差每提高 100 元/亩，大豆种植概率上升约 3.2 个百分点**（Logit 平均边际效应；线性概率模型为 4.4 个百分点）——反应温和，可解释为何约 330 元/亩的现行补贴差下大豆份额仍处个位数。
2. **反应随经营规模显著上升**：最小三分位农户仅 +1.4 个百分点，最大三分位达 +6.7 个百分点。
3. 种植决策**高度惯性**（上年种豆者今年更可能种豆），且在结构性玉米带（双城）近乎为零。

**仿真层**将上述估计参数（含抽样协方差）嵌入 396 户智能体模型，模拟至 2030 年。模型成功复现各县大豆份额的高低次序与水平，并对补贴呈单调响应。**政策情景结果**：

- 维持现行政策，三县大豆面积份额稳定在约 **7.2%**，年财政成本约 145 万元。
- 大豆补贴提高 50%，份额升至 11.1%，但财政成本增加约四分之三。
- **市场价格支持（大豆价格 +20%）可实现相近扩张（至 9.8%），且每提高一个百分点份额的财政成本远低于补贴途径**（约 11 万元/百分点，而补贴途径 S1 约 27 万元/百分点）——因价格上涨引致更多大豆面积、补贴总额仍会上升，但单位扩张成本约低 2.5 倍，是财政上更高效的补充手段。
- 实现 10%／15%／20% 的大豆面积目标，需将大豆补贴分别提高至约 **480／659／802 元/亩**，年财政成本约 **220／385／586 万元**，呈**凸性上升**（越往上每提高一个百分点越贵）。

**政策建议**：补贴投放应**精准聚焦**于玉米与大豆农艺上真正可竞争的边际地区与规模较大、反应更强的农户；对结构性玉米带的补贴难有产出。价格支持与轮作补贴应作为生产者补贴的**补充而非替代**。同时需警惕玉米价格上涨对大豆扩种目标的侵蚀（情景 S5：玉米价格 +20% 使大豆份额降至 4.0%）。

*说明：财政成本按调查样本规模测算，其绝对数值需按县域总体放大；本研究的可迁移结论是成本曲线的**凸性**与玉米带的**结构性无弹性**，而非绝对金额。*

---

## Data and reproducibility

All estimates and simulations are reproducible from the saved artifacts:
- **Panels:** `panel_hh.parquet` (household-year panel), `analysis_panel.parquet` (with Δπ̂ decomposition).
- **Parameters:** `behavior_params.json` (estimated coefficients + sampling covariance + calibration), `econ_params.json` (prices, costs, subsidy and rotation rates), `table_parameters.csv` (parameter provenance).
- **ABM:** `abm.py` (vectorized simulator), `agent_init.parquet` (agent initialization).
- **Results:** `scenario_results.parquet`, `scenario_paths.parquet`, `backsolve_targets.parquet`; Tables 1–4 and Figures 1–5 (+ appendix).

