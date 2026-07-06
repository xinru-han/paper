# Provincial Food Demand Elasticities and Nutrition Transition in China: A First-Pass MAIDADS Working Paper

**Manuscript status:** Working-paper draft generated under a YELLOW audit gate. Formal-scale bootstrap inference is included; conditional scenario projections are explicitly labeled.



# Abstract

This paper develops a first-pass province-level application of the modified implicitly additive demand system (MAIDADS) to study food demand, nutrition transition, and conditional food-demand projections in China. The estimating sample contains 279 province-year observations for 31 provinces over 2015--2023. Food consumption is aggregated into five covered food groups measured in daily 2,000-kcal units, while remaining expenditure is treated as an other/non-covered residual. The main specification uses 2023 real-price units and a national non-food CPI for the residual price index.

The current results should be read as a working-paper draft rather than final journal evidence. The audit gate status is **YELLOW** because the projection module still relies on conditional income-convergence assumptions. Inference has been upgraded to formal-scale resampling: the parameter and projection bootstrap uses 1000 province-block draws, of which 998 converge, and the LR cluster bootstrap uses 500 draws. Population paths now use the Chen et al. (2020) SSP2 provincial projection. Within these limits, MAIDADS improves in-sample fit relative to AIDADS and modestly improves out-of-sample food-demand prediction. The estimated demand system passes adding-up, homogeneity, and Slutsky-consistency checks at numerical tolerances. Conditional projections suggest continued reallocation away from staples and toward animal products, although total covered-food calories change less than composition. The paper concludes by identifying the data additions needed for a journal-ready version: direct provincial non-food CPI, province-level income, urbanization, and age-structure paths, and broader food-group coverage.

Unsupported or weak claims to resolve:
- Add province-level income, urbanization, and age-structure paths before presenting projections as forecasts rather than scenario simulations.


# 1. Introduction

China's food system is moving through a nutrition transition in which rising incomes, urbanization, demographic change, and relative prices reshape the composition of diets. A central empirical challenge is that food demand does not respond linearly to income: staples tend to saturate, animal-source foods may rise over a longer range, and the expenditure residual absorbs both uncovered foods and non-food consumption. These features make constant-elasticity or locally linear demand specifications poorly suited for long-run scenario analysis.

This paper adapts the MAIDADS framework of Gouel and Guimbard (2019), building on the modified implicitly additive demand system of Preckel, Cranfield, and Hertel (2010), to a Chinese provincial panel. The goal is not merely to report a table of elasticities. Instead, the paper asks whether a structural, income-flexible demand system can summarize provincial nutrition transition patterns and produce transparent conditional scenarios for 2030, 2035, and 2050.

The contribution is threefold. First, the analysis constructs a province-year demand-system panel in which covered foods are converted to daily 2,000-kcal units and prices are harmonized in 2023 real terms. Second, it estimates saturated AIDADS and MAIDADS systems, reports income and price elasticities, and audits the theoretical restrictions implied by the demand system. Third, it links the estimated demand system to conditional projection paths and animal-product feed-grain equivalents, while making clear which parts of the evidence are preliminary.

This draft deliberately adopts a conservative writing stance. The current bootstrap exercises are now formal-scale, but the projection path combines a sourced SSP2 population projection with conditional income assumptions rather than a complete official provincial forecast system. The quantitative results are therefore useful for model inference and research design, while long-run projection statements remain scenario simulations rather than official forecasts.

Unsupported or weak claims to resolve:
- Add a fuller China food-demand literature review and verified citations.
- Strengthen identification discussion around unit values, quality, and price endogeneity.


# 2. Related Literature

The paper is closest to the literature on income-flexible demand systems for global food demand and nutrition transition. Gouel and Guimbard (2019) use MAIDADS to model global food demand and show why demand saturation is central for long-run food projections. The present project follows that structural logic but shifts the unit of observation from countries to Chinese provinces and from a global income distribution to a province-year panel.

The methodological foundation is the modified implicitly additive demand system of Preckel, Cranfield, and Hertel (2010). MAIDADS nests AIDADS by allowing subsistence consumption to vary with utility, while imposing saturation restrictions that prevent covered food demand from growing without bound at high income levels. This feature is useful for studying diets in an economy where total calories may stabilize even as composition continues to change.

For population inputs, the projection module uses the provincial SSP population data of Chen et al. (2020), which provide province-level and gridded population projections for China from 2010 to 2100. This improves the demographic basis of the scenario exercise relative to the earlier population-share extrapolation, although income, urbanization, and age-composition assumptions remain simplified.

The draft still requires a fuller literature review on China-specific food demand, household demand systems, nutrition transition, and feed-grain implications. Those references should be added only after a verified bibliography is supplied.

Unsupported or weak claims to resolve:
- Add verified references for China demand-system estimates, nutrition transition evidence, and feed conversion assumptions.


# 3. Data and Variable Construction

The estimating sample contains 279 observations for 31 provinces from 2015 to 2023. The model uses six aggregate demand categories: staples, oils and fats, vegetables and fruits, meat and aquatic products, dairy and eggs, and an other/non-covered residual. The residual is retained internally under the code name `nonfood`, but it should not be interpreted as a strict outside good. It includes uncovered foods, eating away from home, alcohol and tobacco components when present in the residual, and true non-food expenditure.

Food quantities are converted to daily 2,000-kcal units. The nutrition table is adjusted for edible shares. When reported energy is missing or zero, energy is reconstructed from macronutrients. Grain aggregation includes soybeans and potatoes. The potato division by five is retained only for grain-equivalent accounting; calorie aggregation uses actual kcal per kilogram and consumption-quantity weights.

The main monetary specification uses 2023 real-price terms. Total expenditure is deflated by the provincial total CPI index, covered-food prices by provincial food CPI, and the other/non-covered residual price by national non-food CPI. A robustness specification uses a derived provincial non-food CPI from total CPI, food CPI, and food expenditure shares. Because direct provincial non-food CPI is not yet available, residual-price variation should be interpreted cautiously.

Projection-year population is taken from the Chen et al. (2020) provincial population projection under SSP2. The raw projection table is reported in persons and is converted to the model's `population_10k` unit before aggregation.

Unsupported or weak claims to resolve:
- Add direct provincial non-food CPI or official CPI weights.
- Add an external covered-calorie benchmark against FAOSTAT or statistical yearbook food balance data.


# 4. Model

The empirical model is a saturated six-good MAIDADS demand system. For province-year observation c and good i, fitted demand is

```text
x_ci = gamma_i(u_c) + phi_i(u_c) [m_c - sum_j p_cj gamma_j(u_c)] / p_ci .
```

The marginal budget share is

```text
phi_i(u) = [alpha_i + beta_i exp(u)] / [1 + exp(u)],
```

and the subsistence term is

```text
gamma_i(u) = [delta_i + tau_i exp(omega u)] / [1 + exp(omega u)].
```

Utility is solved from the implicit equation

```text
sum_i phi_i(u_c) ln[x_ci - gamma_i(u_c)] - u_c - kappa = 0.
```

The saturated specification imposes beta equal to zero for covered food groups and one for the other/non-covered residual. The model is estimated by concentrated likelihood using quantity errors. AIDADS is estimated first and then used to initialize MAIDADS. Multi-start diagnostics, boundary reports, and gradient summaries are retained as part of the paper evidence package.

Income elasticities are computed by the model's prediction function using central differences. Marshallian price elasticities and Hicksian elasticities are reported for completeness and for demand-system checks, but price elasticity is not positioned as the main contribution because MAIDADS has limited independent price flexibility and provincial unit values may contain quality variation.

Unsupported or weak claims to resolve:
- Add direct analytic-vs-numeric elasticity unit tests before final submission.
- Add a stronger treatment of panel dependence beyond cluster bootstrap.


# 5. Estimation, Fit, and Diagnostics

Table 1 summarizes the fit of AIDADS and MAIDADS under the main and robustness price specifications.

| variant | model | nll | aic | bic | oos_food_rmse_mean |
| --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -3008.279 | -5992.558 | -5948.984 | 0.039 |
| baseline_real_national_nonfood | MAIDADS_sat | -3228.932 | -6419.865 | -6350.872 | 0.038 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -3013.916 | -6003.832 | -5960.257 | 0.039 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -3232.579 | -6427.158 | -6358.165 | 0.037 |

In the main specification, MAIDADS lowers the concentrated negative log likelihood relative to AIDADS. Out-of-sample validation is now computed separately for each model and specification, avoiding the earlier error in which a single OOS statistic could be broadcast across rows. The main-specification mean food RMSE is lower for MAIDADS than AIDADS, but the improvement is modest and should be interpreted together with the split-specific group errors.

The LR statistic comparing MAIDADS and AIDADS is 441.306. However, the standard chi-square reference distribution is not used for inference because nuisance parameters are not identified under the restricted model. The current LR bootstrap is formal-scale: 462 successful draws out of 500, with a cluster-bootstrap tail probability of 0.297. This result cautions against interpreting the large in-sample LR statistic as decisive model-selection evidence.

The theoretical consistency checks are numerically tight. The maximum absolute consistency error across the recorded adding-up, homogeneity, and Slutsky checks is 9.25e-08. Parameter boundary reports distinguish restrictions imposed by saturation from parameters estimated near a boundary.

Unsupported or weak claims to resolve:
- Clarify the null-resampling interpretation of the LR bootstrap and consider a parametric-null bootstrap robustness check.
- Add a table of split-specific OOS results in the appendix.


# 6. Demand Elasticities

Table 2 reports income elasticities at the sample median-income grid point.

| income | group | quantity_2000kcal_elasticity | expenditure_elasticity | budget_share |
| --- | --- | --- | --- | --- |
| 17951.507 | grain | -0.550 | -0.550 | 0.020 |
| 17951.507 | oil | -0.335 | -0.335 | 0.036 |
| 17951.507 | vegfruit | 0.522 | 0.522 | 0.024 |
| 17951.507 | meatsea | 0.075 | 0.075 | 0.040 |
| 17951.507 | dairyegg | 0.419 | 0.419 | 0.005 |
| 17951.507 | all_food | -0.282 | -0.040 | 0.126 |
| 17951.507 | plant_food | -0.410 | -0.128 | 0.080 |
| 17951.507 | animal_food | 0.134 | 0.115 | 0.046 |

The current estimates imply declining covered-kcal demand for staples and oils at the median grid point, positive responsiveness for vegetables and fruits, mild positive responsiveness for meat and aquatic products, and relatively strong positive responsiveness for dairy and eggs. Aggregated across groups, all covered foods and plant foods have negative median-income elasticities, while animal foods remain positive. These patterns are consistent with a nutrition-transition interpretation in which the main response to income growth is compositional rather than a uniform expansion of total covered calories.

Table 5 summarizes Marshallian own-price elasticities over the income grid.

| group | min | median_own_price_elasticity | max |
| --- | --- | --- | --- |
| dairyegg | -0.628 | -0.367 | -0.358 |
| grain | -0.082 | -0.076 | 0.020 |
| meatsea | -0.808 | -0.786 | -0.582 |
| nonfood | -1.085 | -1.022 | -1.004 |
| oil | -0.000 | 0.001 | 0.053 |
| vegfruit | -0.056 | -0.001 | -0.000 |

Price elasticities should be treated as auxiliary outputs. Some own-price elasticities are close to zero and may be positive for certain groups and income points. This pattern reinforces the need to avoid making price responsiveness the core contribution until price measurement and quality adjustment are strengthened.

Unsupported or weak claims to resolve:
- Investigate positive own-price elasticities for selected plant-food groups.
- Add robustness using a price-flexible demand system such as QUAIDS or EASI if price effects become central.


# 7. Conditional Projections to 2030, 2035, and 2050

The projection exercise is a conditional scenario simulation. It uses national growth paths, province-specific income convergence adjustments, and the Chen et al. (2020) SSP2 provincial population projection. It is not an official province-level forecast because province-level income, urbanization, and age-structure paths remain simplified.

Table 3 reports national weighted daily kcal per capita by covered-food group.

| group | 2030 | 2035 | 2050 |
| --- | --- | --- | --- |
| dairyegg | 69.0 | 69.7 | 70.4 |
| grain | 738.1 | 732.3 | 729.9 |
| meatsea | 360.9 | 365.6 | 372.0 |
| oil | 234.5 | 233.2 | 232.6 |
| vegfruit | 114.4 | 115.1 | 115.6 |

Under the scenario, staples remain the largest covered-food source in 2050, while meat and aquatic products account for a substantial share of covered-food calories. Total covered-food calories are relatively stable compared with the compositional changes across groups.

Animal-product quantities are mapped into feed-grain equivalents using the user-supplied conversion factors. Table 4 reports the implied national feed-grain equivalents in million tons.

| item | 2030 | 2035 | 2050 |
| --- | --- | --- | --- |
| aquatic | 25.0 | 25.1 | 24.2 |
| beef | 40.4 | 40.7 | 39.7 |
| egg | 49.0 | 49.2 | 47.7 |
| milk | 11.3 | 11.4 | 11.0 |
| mutton | 26.1 | 26.5 | 26.4 |
| pork | 155.5 | 156.8 | 153.1 |
| poultry | 48.0 | 48.5 | 47.7 |

The feed-grain module should be interpreted as an accounting translation rather than a behavioral supply-chain model. The coefficients are currently treated as feed-grain equivalent factors; if they are instead total-feed coefficients, feed cereal shares must be added.

Unsupported or weak claims to resolve:
- Replace the income-convergence assumption with sourced province-level income, urbanization, and age-structure paths; retain or compare alternative SSP population scenarios.
- Add sourced feed conversion coefficients and cereal shares.


# 8. Robustness and Audit Findings

The main robustness exercise replaces the national non-food CPI residual price with a derived provincial non-food CPI. The resulting MAIDADS fit remains better than AIDADS within that specification. Cross-specification AIC and BIC comparisons should not be over-interpreted because the residual-price construction differs across specifications.

The code audit also changed several data and reporting conventions. The residual category is described as other/non-covered expenditure rather than strict non-food consumption. The grain-calorie calculation uses actual calorie weights rather than the potato grain-equivalent conversion. OOS files are stored separately by variant, model, and split. The projection module now uses Chen et al. (2020) SSP2 provincial population paths rather than population-share trend extrapolation. The paper workflow records a YELLOW gate status because the income side of projections remains a conditional scenario, not because bootstrap inference is still pilot-scale.

Unsupported or weak claims to resolve:
- Add official non-food CPI or CPI category weights.
- Add leave-one-province and leave-one-region validation.


# 9. Conclusion

This draft shows that a province-level MAIDADS framework can organize evidence on China's nutrition transition and produce transparent conditional food-demand scenarios. The first-pass results support a compositional interpretation: income growth does not simply raise all covered foods proportionally; it changes the relative importance of staples, animal products, dairy and eggs, and plant foods.

The current contribution is methodological and diagnostic as much as substantive. The project now has a reproducible data pipeline, model estimates, OOS validation by model, price-elasticity matrices, theoretical consistency checks, formal-scale bootstrap status records, and a simulator workbook. These are necessary building blocks for a journal paper.

The draft is not yet a final submission version. Formal-scale bootstrap inference has been completed, but the LR comparison should still be interpreted through the cluster-bootstrap result rather than the invalid naive chi-square reference. Long-run projections now have a sourced provincial SSP2 population path, but still require stronger province-level income, urbanization, and age-structure scenarios. Direct provincial non-food CPI and broader food-group coverage would materially improve identification and interpretation. Once these additions are made, the paper can move from a working-paper draft to a journal-style submission.

Unsupported or weak claims to resolve:
- Upgrade projection inputs before removing the working-paper caveats.


# References

Gouel, C., and H. Guimbard. 2019. “Nutrition Transition and the Structure of Global Food Demand.” *American Journal of Agricultural Economics* 101(2): 383--403.

Preckel, P. V., J. A. L. Cranfield, and T. W. Hertel. 2010. “A Modified, Implicitly Additive Demand System.” *Applied Economics* 42(2): 143--155.

Chen, Y., F. Guo, J. Wang, et al. 2020. “Provincial and Gridded Population Projection for China under Shared Socioeconomic Pathways from 2010 to 2100.” *Scientific Data* 7: 83. https://doi.org/10.1038/s41597-020-0421-y.

TODO: Add verified China food-demand, nutrition-transition, and feed-conversion references.
