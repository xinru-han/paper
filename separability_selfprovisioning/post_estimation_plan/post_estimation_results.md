# Post-Estimation Results for Paper 1

Generated at: 2026-07-04 20:29:36

All models use R/base `lm()` with village-clustered `sandwich::vcovCL()` inference, following the existing project pipeline.

## Sample

| input_rows | common_m3_rows | common_m3_households | common_m3_village_clusters | self_suff_nonmissing_rows |
|---|---|---|---|---|
| 27861 | 26926 | 3446 | 350 | 26249 |

## A0. Two-margin omnibus test

| analysis | outcome | block | n | n_clusters | r_squared | wald_chisq | wald_df | wald_p |
|---|---|---|---|---|---|---|---|---|
| A0 | participation_and_ihs_stacked | composition_ext_and_int | 53852 | 350 | 0.4191 | 20.43 | 8 | 0.008813 |

## A1. Mundlak between-within decomposition

| outcome | block | n | n_clusters | wald_chisq | wald_df | wald_p |
|---|---|---|---|---|---|---|
| production_participation | between_village_means | 26926 | 350 | 10.890 | 4 | 0.027880 |
| production_participation | within_household_deviation | 26926 | 350 | 16.530 | 4 | 0.002382 |
| self_suff_rate | between_village_means | 26249 | 350 | 16.540 | 4 | 0.002379 |
| self_suff_rate | within_household_deviation | 26249 | 350 | 7.555 | 4 | 0.109300 |
| ihs_selfprod_amount | between_village_means | 26926 | 350 | 7.828 | 4 | 0.098080 |
| ihs_selfprod_amount | within_household_deviation | 26926 | 350 | 9.127 | 4 | 0.058000 |

## A1b. Component and leave-one-out tests

See `A1b_component_leave_one_out_wald.csv` and `A1b_component_coefficients.csv`.

## A2. RIF quantile profile

| tau | term | estimate | std_error_cluster | p_value |
|---|---|---|---|---|
| 0.5 | elderly_share | 0.001658 | 0.001225 | 0.17590 |
| 0.6 | elderly_share | 0.001996 | 0.001852 | 0.28110 |
| 0.7 | elderly_share | 0.039710 | 0.027460 | 0.14830 |
| 0.8 | elderly_share | 0.074910 | 0.038890 | 0.05408 |
| 0.9 | elderly_share | 0.040880 | 0.022830 | 0.07332 |

| block | wald_chisq | wald_df | wald_p |
|---|---|---|---|
| elderly_share_by_tau | 78.15 | 1 | 0 |
| all_composition_by_tau | 2679.00 | 4 | 0 |

## A3. Composition by market friction interactions

| outcome | block | wald_chisq | wald_df | wald_p |
|---|---|---|---|---|
| ihs_selfprod_amount | all_composition_market_interactions | 8.116 | 8 | 0.4222 |
| ihs_selfprod_amount | elderly_market_interactions | 2.995 | 2 | 0.2237 |
| self_suff_rate | all_composition_market_interactions | 5.881 | 8 | 0.6606 |
| self_suff_rate | elderly_market_interactions | 1.190 | 2 | 0.5515 |

## A4. Category-attribute meta-regression

| analysis | n_categories | spearman_rho | spearman_p | wls_bandwidth_coef | wls_bandwidth_se | wls_bandwidth_p |
|---|---|---|---|---|---|---|
| A4_category_attribute_meta | 7 | 0.7672 | 0.04411 | 7.91 | 3.164 | 0.0545 |

## A5. External validity

See `A5_external_validity_wald.csv`.
