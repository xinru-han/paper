# Paper 1 Revised Results Package

Generated at: 2026-07-06 14:28:07

## 1. Executive summary

- MAIN RESULT: household composition predicts self-provisioning participation in the common-sample M3 model (Wald = 16.733, p = 0.002).
- MAIN RESULT: full-sample intensive amount margins are weaker (`log_selfprod_amount` p = 0.163; `ihs_selfprod_amount` p = 0.179), so participation remains the clearest margin.
- SUPPORTING RESULT: the formal two-part model also finds a conditional-intensity signal among self-provisioning entrants (Part 2 p = 0.046), so the intensive-margin conclusion should be stated cautiously.
- MAIN RESULT: category heterogeneity is strong; top NSI categories are 蛋类, 油脂, 蔬菜, 水果, 豆类.
- SUPPORTING RESULT: self-sufficiency and alternative household-composition specifications are reported as robustness checks.
- ROBUSTNESS RESULT: leave-one-province baseline Wald remains significant in all drops = TRUE.
- APPENDIX / EXPLORATORY RESULT: market-friction interactions and IV diagnostics are appendix-only.
- FAILED OR WEAK EVIDENCE: IV first stages remain weak.
- HUMAN REVIEW REQUIRED: roulei split feasibility, youzhi definition, and commercialization-rate denominator.

## 2. Data and sample checks

### Unit and outlier handling

- Food quantities are household totals in kg/month/household after converting from jin/month with `kg = jin * 0.5`.
- Unit values are yuan/kg after converting from yuan/jin with `yuan/kg = yuan/jin * 2`; legacy model aliases ending in `_yuan_per_jin` are retained only for script compatibility.
- Food quantity outliers were excluded by food-category P99.5 thresholds; the cleaned model file drops 312 category-level rows and retains all 3,565 households.
- Main outcome transforms, `log_selfprod_amount` and `ihs_selfprod_amount`, are recomputed from `selfprod_kg_month`.

- rows: 28208
- households: 3565
- food_categories: 8
- villages_clusters: 361
- provinces: 9
- counties: 44
- duplicate_household_category_keys: 0

### Observations by data_year

- 2023: 13953
- 2024: 14255

### Observations by food_category

- danlei / 蛋类: 3523
- doulei / 豆类: 3524
- nailei / 奶类: 3538
- roulei / 肉类和水产品及加工品: 3524
- shucai / 蔬菜: 3522
- shuiguo / 水果: 3522
- youzhi / 油脂: 3528
- zhushi / 主食: 3527

### Missingness by core variables

- outcome / `production_participation`: 0 missing
- outcome / `log_selfprod_amount`: 0 missing
- outcome / `ihs_selfprod_amount`: 0 missing
- outcome / `self_suff_rate`: 714 missing
- household_composition / `household_size_reconstructed`: 0 missing
- household_composition / `child_share`: 144 missing
- household_composition / `elderly_share`: 144 missing
- household_composition / `female_share`: 144 missing
- market / `market_friction_survey`: NA missing
- market / `poi_market_friction_lag1`: NA missing
- market / `combined_market_friction`: NA missing
- price / `price_hedonic_imputed_w99_yuan_per_kg`: 0 missing
- price / `price_preferred_household_recalc_w99_yuan_per_kg`: 7573 missing
- price / `village_price_category_median_yuan_per_kg`: 4920 missing
- gaez / `gaez_overall_si_10km`: NA missing
- gaez / `gaez_staple_si_10km`: NA missing
- gaez / `gaez_soil_terrain_constraint_10km`: NA missing
- text / `risk_salience_z_5yr_sum`: NA missing
- text / `governance_capacity_z_5yr_sum`: NA missing
- text / `trust_signal_z_5yr_sum`: NA missing
- text / `attention_z_5yr_sum`: NA missing

- M0-M3 common sample constructed: TRUE
- Common-sample N: 27568
- Common-sample cluster count: 350

## 3. Main baseline results

- Table: `outputs/tables/table2_common_sample_baseline.csv`
- Model summary: `outputs/model_summaries/model2_common_sample_baseline.json`

- `production_participation`: Wald = 16.733, df = 4, p = 0.002, N = 27568.
- `log_selfprod_amount`: Wald = 6.537, p = 0.163.
- `ihs_selfprod_amount`: Wald = 6.282, p = 0.179.

Interpretation: The evidence rejects separability restrictions on the self-provisioning participation margin, but provides weaker evidence on the self-production quantity margin. This is a reduced-form association, not a causal treatment effect.

## 4. Household-composition coefficient interpretation

- Table: `outputs/tables/table3_baseline_coefficients_margins.csv`
- Figure: `outputs/figures/figure3_household_composition_coefficients.png`

- `household_size_reconstructed`: beta = -0.0070, SE = 0.0031, p = 0.024, direction = negative, stable across M0-M3 = TRUE
- `child_share`: beta = 0.0425, SE = 0.0221, p = 0.054, direction = positive, stable across M0-M3 = FALSE
- `elderly_share`: beta = 0.0436, SE = 0.0129, p = <0.001, direction = positive, stable across M0-M3 = FALSE
- `female_share`: beta = 0.0114, SE = 0.0163, p = 0.482, direction = positive, stable across M0-M3 = FALSE

## 5. Category-specific non-separability and NSI

- Table: `outputs/tables/table4_category_specific_nsi.csv`
- Figure: `outputs/figures/figure2_nsi_by_category.png`

- Strong categories: 蛋类, 油脂, 蔬菜
- Weak categories: 主食, 肉类和水产品及加工品, 奶类

- 主食: Wald = 4.526, p = 0.340, NSI = 0.419, signal = Weak, drivers = household_size_reconstructed
- 豆类: Wald = 10.271, p = 0.036, NSI = 0.950, signal = Moderate, drivers = elderly_share
- 肉类和水产品及加工品: Wald = 6.791, p = 0.147, NSI = 0.628, signal = Weak, drivers = elderly_share
- 蛋类: Wald = 19.813, p = <0.001, NSI = 1.833, signal = Strong, drivers = elderly_share
- 奶类: Wald = 4.023, p = 0.403, NSI = 0.372, signal = Weak, drivers = household_size_reconstructed;female_share
- 油脂: Wald = 15.870, p = 0.003, NSI = 1.468, signal = Strong, drivers = household_size_reconstructed;child_share;female_share
- 蔬菜: Wald = 13.920, p = 0.008, NSI = 1.288, signal = Strong, drivers = household_size_reconstructed;elderly_share
- 水果: Wald = 11.244, p = 0.024, NSI = 1.040, signal = Moderate, drivers = household_size_reconstructed

Possible substantive explanation: the signal is concentrated in categories where households may make discrete entry decisions into self-provisioning. Data-definition concerns remain for `youzhi` and the combined `roulei` category.

## 6. Two-part model: entry versus conditional intensity

- Table: `outputs/tables/table5_two_part_model.csv`

- Part 1 (all observations, outcome `production_participation`): Wald = 16.733, p = 0.002, N = 27568
- Part 2 (production_participation == 1, outcome `log_selfprod_amount`): Wald = 9.696, p = 0.046, N = 12140

Interpretation: Part 1 is significant and Part 2 is also significant at the 5% level. The clearest main result remains entry into self-provisioning, while the conditional-intensity result should be treated as supporting but more cautious evidence because full-sample log/IHS amount models are weaker.

## 7. Robustness checks

### 7.1 Alternative household composition and outcomes

- proportion / `production_participation`: Wald = 16.733, p = 0.002, N = 27568
- proportion / `log_selfprod_amount`: Wald = 6.537, p = 0.163, N = 27568
- proportion / `ihs_selfprod_amount`: Wald = 6.282, p = 0.179, N = 27568
- proportion / `self_suff_rate`: Wald = 11.083, p = 0.026, N = 26867
- dependency / `production_participation`: Wald = 21.923, p = <0.001, N = 23952
- dependency / `log_selfprod_amount`: Wald = 5.312, p = 0.150, N = 23952
- dependency / `ihs_selfprod_amount`: Wald = 5.143, p = 0.162, N = 23952
- dependency / `self_suff_rate`: Wald = 9.004, p = 0.029, N = 23335
- counts / `production_participation`: Wald = 20.898, p = <0.001, N = 27712
- counts / `log_selfprod_amount`: Wald = 9.328, p = 0.053, N = 27712
- counts / `ihs_selfprod_amount`: Wald = 9.426, p = 0.051, N = 27712
- counts / `self_suff_rate`: Wald = 15.212, p = 0.004, N = 27007

### 7.2 Province leave-one-out

- Minimum leave-one-province Wald: 10.814
- Maximum leave-one-province Wald: 20.286
- All leave-one-province estimates remain significant: TRUE
- Most influential drop by minimum Wald: 福建省

### 7.3 Household-composition permutation placebo

- Permutations: 99; true Wald = 16.733; placebo mean = 4.105; placebo P95 = 9.284; randomization p = 0.010.

## 8. Appendix mechanism diagnostics

### 8.1 Market-friction interactions

- survey_market_friction / `production_participation`: interaction Wald = 1.237, p = 0.872.
- survey_market_friction / `log_selfprod_amount`: interaction Wald = 3.694, p = 0.449.
- survey_market_friction / `ihs_selfprod_amount`: interaction Wald = 3.934, p = 0.415.
- poi_market_friction / `production_participation`: interaction Wald = 2.367, p = 0.669.
- poi_market_friction / `log_selfprod_amount`: interaction Wald = 4.728, p = 0.316.
- poi_market_friction / `ihs_selfprod_amount`: interaction Wald = 4.528, p = 0.339.
- combined_market_friction / `production_participation`: interaction Wald = 0.652, p = 0.957.
- combined_market_friction / `log_selfprod_amount`: interaction Wald = 5.836, p = 0.212.
- combined_market_friction / `ihs_selfprod_amount`: interaction Wald = 5.614, p = 0.230.

Default interpretation: Market-friction interactions do not provide strong support for a cross-sectional amplification mechanism if the p-values remain weak.

### 8.2 IV diagnostics

- terrain_town_2km: corr = 0.129, min F = 1.074, median F = 2.178, weak = TRUE.
- terrain_town_1km: corr = 0.133, min F = 0.922, median F = 2.127, weak = TRUE.
- terrain_town_5km: corr = 0.115, min F = 1.377, median F = 2.247, weak = TRUE.
- terrain_county_2km: corr = 0.134, min F = 1.871, median F = 2.203, weak = TRUE.
- early_ntl_9294: corr = 0.112, min F = 0.668, median F = 1.212, weak = TRUE.

Default interpretation: IV results are reported as diagnostics and should not be used as the main identification basis when first stages are weak.

## 9. Price robustness

- no_price_control: Wald = 16.614, p = 0.002, N = 27568.
- hedonic_price_main: Wald = 16.733, p = 0.002, N = 27568.
- observed_price_only: Wald = 16.656, p = 0.002, N = 20281.
- county_category_median_price: Wald = 10.795, p = 0.029, N = 23496.

Interpretation: Compare Wald p-values across no-price, hedonic-price, observed-price-only, and county-median-price specifications to assess dependence on price imputation.

## 10. Category-definition audits

- roulei_split: partially_feasible_raw_detail_present; decision: Do not split roulei in the revised rerun without rebuilding detail-level outcomes and prices. Report as human-review flag.
- youzhi_definition: partially_identified_human_review_required; decision: Use current aggregate `youzhi` as oils category, but avoid strong substantive claims before item-code review.

## 11. Table and figure inventory

| Item | File path | Placement | Purpose | Status | Human review |
|---|---|---|---|---|---|
| Table 1 | `outputs/tables/table1_descriptive_statistics_revised.csv` | Main text | Descriptive statistics and sample checks | Generated | No |
| Table 2 | `outputs/tables/table2_common_sample_baseline.csv` | Main text | Common-sample baseline separability tests | Generated | No |
| Table 3 | `outputs/tables/table3_baseline_coefficients_margins.csv` | Main text | Household-composition coefficient interpretation | Generated | No |
| Table 4 | `outputs/tables/table4_category_specific_nsi.csv` | Main text | Category-specific NSI | Generated | No |
| Table 5 | `outputs/tables/table5_two_part_model.csv` | Main text | Two-part entry versus conditional intensity | Generated | No |
| Table 6 | `outputs/tables/table6_alternative_composition_outcomes.csv` | Main text | Alternative composition and outcomes | Generated | No |
| Table 7 | `outputs/tables/table7_leave_one_province.csv` | Main text | Province leave-one-out | Generated | No |
| Table 8 | `outputs/tables/table8_household_composition_permutation.csv` | Main text | Household-composition permutation placebo | Generated | No |
| Appendix Table A | `outputs/tables/tableA_market_friction_interactions_appendix.csv` | Appendix | Market-friction interactions | Generated | No |
| Appendix Table B | `outputs/tables/tableB_iv_diagnostics_appendix.csv` | Appendix | IV diagnostics | Generated | No |
| Appendix Table C | `outputs/tables/tableC_price_robustness.csv` | Appendix | Price robustness | Generated | No |
| Appendix Table D | `outputs/tables/tableD_category_definition_audits.csv` | Appendix | Category-definition audits | Generated | Yes |
| Figure 1 | `outputs/figures/figure1_conceptual_framework_placeholder.png` | Main text | Conceptual framework | Generated | No |
| Figure 2 | `outputs/figures/figure2_nsi_by_category.png` | Main text | NSI ranking by category | Generated | No |
| Figure 3 | `outputs/figures/figure3_household_composition_coefficients.png` | Main text | Baseline coefficient plot | Generated | No |
| Figure 4 | `outputs/figures/figure4_household_composition_permutation.png` | Main text | Permutation distribution | Generated | No |

## 12. Human-review flags

- roulei split not performed; raw detail exists but analysis-ready split outcome is not cleanly available.
- youzhi definition requires human review before strong substantive claims about oils.
- IV first stages are weak; IV remains appendix-only.
- Market-friction interactions are non-significant.
- commercialization_rate denominator unclear; not included in revised rerun.

Rerun complete: all required completion-criteria files exist.

## 13. Recommended manuscript language

The results indicate that household composition significantly predicts category-specific self-provisioning participation, providing reduced-form evidence inconsistent with separability. The clearest evidence is on the extensive margin: household composition predicts whether households enter self-provisioning, while full-sample quantity-margin tests are weaker. A formal two-part model also suggests some conditional-intensity association among households that enter self-provisioning, so the intensive-margin evidence should be interpreted cautiously rather than dismissed. The category-specific analysis shows that non-separability is concentrated in eggs, oils, vegetables, fruits, and beans, rather than being uniform across food groups. Market-friction interactions and IV diagnostics provide weaker support for the market-friction amplification mechanism and are therefore interpreted as exploratory.
