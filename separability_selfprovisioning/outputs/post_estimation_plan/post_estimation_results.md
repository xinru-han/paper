# Post-Estimation Results for Paper 1

Generated at: 2026-07-06 14:30:39

All models use R/base `lm()` with village-clustered `sandwich::vcovCL()` inference, following the existing project pipeline.

## Sample

| input_rows | common_m3_rows | common_m3_households | common_m3_village_clusters | self_suff_nonmissing_rows |
|---|---|---|---|---|
| 28208 | 27262 | 3446 | 350 | 26578 |

## A0. Two-margin omnibus test

| analysis | outcome | block | n | n_clusters | r_squared | wald_chisq | wald_df | wald_p |
|---|---|---|---|---|---|---|---|---|
| A0 | participation_and_ihs_stacked | composition_ext_and_int | 54524 | 350 | 0.4123 | 23.43 | 8 | 0.002858 |

## A1. Mundlak between-within decomposition

| outcome | block | n | n_clusters | wald_chisq | wald_df | wald_p |
|---|---|---|---|---|---|---|
| production_participation | between_village_means | 27262 | 350 | 11.110 | 4 | 0.025330 |
| production_participation | within_household_deviation | 27262 | 350 | 16.940 | 4 | 0.001984 |
| self_suff_rate | between_village_means | 26578 | 350 | 15.760 | 4 | 0.003357 |
| self_suff_rate | within_household_deviation | 26578 | 350 | 8.819 | 4 | 0.065790 |
| ihs_selfprod_amount | between_village_means | 27262 | 350 | 7.015 | 4 | 0.135100 |
| ihs_selfprod_amount | within_household_deviation | 27262 | 350 | 11.170 | 4 | 0.024730 |

## A1b. Component and leave-one-out tests

See `A1b_component_leave_one_out_wald.csv` and `A1b_component_coefficients.csv`.

## A2. RIF quantile profile

| tau | term | estimate | std_error_cluster | p_value |
|---|---|---|---|---|
| 0.5 | elderly_share | 0.001924 | 0.001232 | 0.11840 |
| 0.6 | elderly_share | 0.002736 | 0.001936 | 0.15750 |
| 0.7 | elderly_share | 0.048470 | 0.028030 | 0.08379 |
| 0.8 | elderly_share | 0.085660 | 0.039040 | 0.02823 |
| 0.9 | elderly_share | 0.041450 | 0.022570 | 0.06627 |

| block | wald_chisq | wald_df | wald_p |
|---|---|---|---|
| elderly_share_by_tau | 80.3 | 1 | 0 |
| all_composition_by_tau | 2756.0 | 4 | 0 |

## A3. Composition by market friction interactions

| outcome | block | wald_chisq | wald_df | wald_p |
|---|---|---|---|---|
| ihs_selfprod_amount | all_composition_market_interactions | 9.5720 | 8 | 0.2964 |
| ihs_selfprod_amount | elderly_market_interactions | 2.9840 | 2 | 0.2249 |
| self_suff_rate | all_composition_market_interactions | 6.0280 | 8 | 0.6441 |
| self_suff_rate | elderly_market_interactions | 0.8517 | 2 | 0.6532 |

## A4. Category-attribute meta-regression

| analysis | n_categories | spearman_rho | spearman_p | wls_bandwidth_coef | wls_bandwidth_se | wls_bandwidth_p |
|---|---|---|---|---|---|---|
| A4_category_attribute_meta | 7 | 0.7672 | 0.04411 | 7.91 | 3.164 | 0.0545 |

## A5. External validity

See `A5_external_validity_wald.csv`.
