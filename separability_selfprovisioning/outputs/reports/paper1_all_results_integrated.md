# Paper 1 All Results Integrated Package

Generated at: 2026-07-06 13:42:27

This file integrates the current Paper 1 result artifacts after kg/month conversion, quantity-outlier exclusion, and full R model reruns.

## 0. Execution Notes

- **Econometric estimation is R-only.** The Python files in `code/` (`15`–`17`) are manuscript-writing utilities, not statistical models.
- **One-command rerun:** `Rscript code/run_revised_pipeline.R` from the project root.
- **Recommended order:** `19` (data prep) → `01`–`14` (models) → `13` (this compile step).
- **Code review:** see `outputs/reports/paper1_econometric_code_review.md`.

Binary figures are embedded by path; CSV, JSON, and Markdown outputs are included as text blocks.

## 1. Artifact Inventory

| relative_path | size_kb | n_lines |
|---|---|---|
| outputs/reports/paper1_editor_revision_results_addendum.md | 9.3 | 142 |
| outputs/reports/paper1_kg_month_outlier_cleaning_report.md | 7.5 | 89 |
| outputs/reports/paper1_revised_results_package.md | 13.5 | 228 |
| outputs/logs/appendix_mechanism_diagnostics.md | 0.5 | 9 |
| outputs/logs/commercialization_rate_audit.md | 0.7 | 19 |
| outputs/logs/common_sample_log.md | 1.4 | 51 |
| outputs/logs/editor_review_action_log.md | 1.2 | 22 |
| outputs/logs/hedonic_price_imputation.md | 1.2 | 33 |
| outputs/logs/iv_diagnostics_appendix.md | 0.6 | 14 |
| outputs/logs/kg_month_outlier_cleaning.md | 0.5 | 16 |
| outputs/logs/price_robustness_issues.md | 0.7 | 15 |
| outputs/logs/revised_data_merge_log.md | 0.8 | 17 |
| outputs/logs/revised_variable_issues.md | 0.4 | 7 |
| outputs/logs/roulei_split_audit.md | 0.7 | 15 |
| outputs/logs/youzhi_definition_audit.md | 0.7 | 15 |
| outputs/tables/hedonic_price_imputation_source_summary.csv | 0.1 | 3 |
| outputs/tables/hedonic_price_imputation_summary_by_category.csv | 1.3 | 9 |
| outputs/tables/hedonic_price_model_diagnostics.csv | 0.3 | 4 |
| outputs/tables/paper1_category_descriptives_after_kg_outlier_cleaning.csv | 1 | 9 |
| outputs/tables/paper1_descriptives_after_kg_outlier_cleaning.csv | 3 | 19 |
| outputs/tables/paper1_kg_month_outlier_cleaning_summary.csv | 0.4 | 11 |
| outputs/tables/paper1_kg_month_outlier_counts_by_category.csv | 0.7 | 9 |
| outputs/tables/paper1_outlier_thresholds_price_spend.csv | 2.7 | 33 |
| outputs/tables/paper1_outlier_thresholds_quantity_kg_month.csv | 1.7 | 25 |
| outputs/tables/paper1_top_extreme_values_after_kg_outlier_cleaning.csv | 7.9 | 61 |
| outputs/tables/table1_category_participation_revised.csv | 0.9 | 9 |
| outputs/tables/table1_descriptive_statistics_revised.csv | 2.8 | 24 |
| outputs/tables/table1_missingness_revised.csv | 1.3 | 22 |
| outputs/tables/table1_observations_by_category_revised.csv | 0.2 | 9 |
| outputs/tables/table1_observations_by_year_revised.csv | 0 | 3 |
| outputs/tables/table1_sample_summary_revised.csv | 0.2 | 8 |
| outputs/tables/table2_common_sample_baseline_coefficients_raw.csv | 7.7 | 49 |
| outputs/tables/table2_common_sample_baseline.csv | 1.6 | 13 |
| outputs/tables/table3_baseline_coefficients_margins.csv | 13.5 | 49 |
| outputs/tables/table4_category_specific_nsi.csv | 4.6 | 9 |
| outputs/tables/table5_two_part_model.csv | 1.7 | 3 |
| outputs/tables/table6_alternative_composition_outcomes.csv | 2.4 | 13 |
| outputs/tables/table7_leave_one_province.csv | 1.2 | 9 |
| outputs/tables/table8_household_composition_permutation_draws.csv | 4.9 | 100 |
| outputs/tables/table8_household_composition_permutation.csv | 0.4 | 2 |
| outputs/tables/tableA_market_friction_interactions_appendix.csv | 1.7 | 10 |
| outputs/tables/tableA_market_friction_permutation_appendix.csv | 0.2 | 2 |
| outputs/tables/tableB_iv_diagnostics_appendix.csv | 0.9 | 6 |
| outputs/tables/tableB_iv_first_stage_detail_appendix.csv | 2.8 | 21 |
| outputs/tables/tableC_price_robustness.csv | 1.2 | 5 |
| outputs/tables/tableD_category_definition_audits.csv | 0.8 | 3 |
| outputs/tables/tableE_add_one_block_diagnostics.csv | 4.6 | 31 |
| outputs/tables/tableF_village_fe_robustness.csv | 2.3 | 12 |
| outputs/tables/tableG_binary_response_robustness.csv | 3.7 | 19 |
| outputs/tables/tableH_category_multiple_testing.csv | 1.7 | 9 |
| outputs/tables/tableI_category_variation_and_nsi_reframed.csv | 3.3 | 9 |
| outputs/tables/tableJ_fixed_common_sample_price_robustness.csv | 0.6 | 5 |
| outputs/tables/tableJ_fixed_common_sample_robustness.csv | 2.2 | 13 |
| outputs/tables/tableK_fixed_factors_bad_controls_robustness.csv | 1.2 | 10 |
| outputs/tables/tableL_participation_missingness_robustness.csv | 0.5 | 4 |
| outputs/tables/tableM_definition_diagnostics_editor.csv | 1.1 | 7 |
| outputs/tables/tableN_price_unit_value_diagnostics.csv | 0.6 | 6 |
| outputs/model_summaries/model2_common_sample_baseline.json | 3 | 16 |
| outputs/model_summaries/model3_baseline_coefficients_margins.json | 22.2 | 52 |
| outputs/model_summaries/model4_category_specific_nsi.json | 7.4 | 12 |
| outputs/model_summaries/model5_two_part_model.json | 2 | 6 |
| outputs/model_summaries/model6_robustness.json | 0.2 | 7 |
| outputs/model_summaries/modelA_market_interactions_appendix.json | 2.9 | 13 |
| outputs/model_summaries/modelB_iv_diagnostics_appendix.json | 1.6 | 9 |
| outputs/model_summaries/modelC_price_robustness.json | 1.7 | 8 |
| outputs/model_summaries/modelE_editor_revision_analyses.json | 0.7 | 14 |
| outputs/figures/figure1_conceptual_framework_placeholder.png | 51.5 | 382 |
| outputs/figures/figure2_editor_nsi_detectability.png | 60.6 | 325 |
| outputs/figures/figure2_nsi_by_category.png | 55 | 328 |
| outputs/figures/figure3_household_composition_coefficients.png | 44.5 | 295 |
| outputs/figures/figure4_household_composition_permutation.png | 35.6 | 225 |

## 2. Figures

### outputs/figures/figure1_conceptual_framework_placeholder.png

![figure1_conceptual_framework_placeholder.png](/root/data/Paper/食物消费数据/Paper1-Seperability/outputs/figures/figure1_conceptual_framework_placeholder.png)

### outputs/figures/figure2_editor_nsi_detectability.png

![figure2_editor_nsi_detectability.png](/root/data/Paper/食物消费数据/Paper1-Seperability/outputs/figures/figure2_editor_nsi_detectability.png)

### outputs/figures/figure2_nsi_by_category.png

![figure2_nsi_by_category.png](/root/data/Paper/食物消费数据/Paper1-Seperability/outputs/figures/figure2_nsi_by_category.png)

### outputs/figures/figure3_household_composition_coefficients.png

![figure3_household_composition_coefficients.png](/root/data/Paper/食物消费数据/Paper1-Seperability/outputs/figures/figure3_household_composition_coefficients.png)

### outputs/figures/figure4_household_composition_permutation.png

![figure4_household_composition_permutation.png](/root/data/Paper/食物消费数据/Paper1-Seperability/outputs/figures/figure4_household_composition_permutation.png)

## 3. Result Reports

## Report: `outputs/reports/paper1_editor_revision_results_addendum.md`

- Size: 9.3 KB
- Lines: 142

````markdown
# Paper 1 Editor-Revision Results Addendum

Generated at: 2026-07-06 13:42:27

This addendum implements the additional diagnostics requested in `paper1_editor_review_and_action_plan.md`. It should be read together with `paper1_revised_results_package.md`.

## 1. Revised Bottom Line / 修订后核心结论

- 最稳妥的正文表述应改为：在加入省份、市场可达性、农业生态、购买侧单位值和县级文本控制后，户内人口结构能够条件性预测自产自给参与；但该结果对控制集敏感，且不能通过村庄固定效应的参与边际稳健性检验。
- M1 以后数量边际整体较弱；固定共同样本下部分数量口径重新显著，说明数量结果具有样本和口径敏感性，应作为辅助描述而非主结论。
- logit/probit 对总体 M3 参与边际给出相近结论，说明 M3 的参与结果不是简单 LPM 泛函形式造成的。
- NSI 已重新定位为 Wald 检验统计量的相对可检测性排序，不是经济幅度指数；奶类因参与率接近 0 从主类别解释中剔除。

## 2. Add-One-Block Diagnostics: Participation

| label | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| B0_composition_category_year | 26271.0000 | 350.0000 | 6.6307 | 0.1567 |
| B1_plus_household_resources | 26271.0000 | 350.0000 | 7.1401 | 0.1287 |
| B1a_M1_plus_market | 26271.0000 | 350.0000 | 9.0067 | 0.0609 |
| B1b_M1_plus_GAEZ | 26271.0000 | 350.0000 | 10.5381 | 0.0323 |
| B1c_M1_plus_province_FE | 26271.0000 | 350.0000 | 11.9326 | 0.0179 |
| B1d_M1_plus_market_GAEZ | 26271.0000 | 350.0000 | 11.8941 | 0.0182 |
| B1e_M1_plus_market_province_FE | 26271.0000 | 350.0000 | 12.3144 | 0.0152 |
| B1f_M1_plus_GAEZ_province_FE | 26271.0000 | 350.0000 | 13.8475 | 0.0078 |
| B2_full_market_GAEZ_province_FE | 26271.0000 | 350.0000 | 13.7586 | 0.0081 |
| B3_plus_unit_value_text | 26271.0000 | 350.0000 | 15.0201 | 0.0047 |

## 3. Add-One-Block Diagnostics: Log Quantity

| label | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| B0_composition_category_year | 26271.0000 | 350.0000 | 19.8342 | 0.0005 |
| B1_plus_household_resources | 26271.0000 | 350.0000 | 5.1632 | 0.2710 |
| B1a_M1_plus_market | 26271.0000 | 350.0000 | 5.0524 | 0.2820 |
| B1b_M1_plus_GAEZ | 26271.0000 | 350.0000 | 4.6141 | 0.3292 |
| B1c_M1_plus_province_FE | 26271.0000 | 350.0000 | 4.5090 | 0.3415 |
| B1d_M1_plus_market_GAEZ | 26271.0000 | 350.0000 | 4.6931 | 0.3203 |
| B1e_M1_plus_market_province_FE | 26271.0000 | 350.0000 | 4.3142 | 0.3651 |
| B1f_M1_plus_GAEZ_province_FE | 26271.0000 | 350.0000 | 4.5995 | 0.3309 |
| B2_full_market_GAEZ_province_FE | 26271.0000 | 350.0000 | 4.3070 | 0.3661 |
| B3_plus_unit_value_text | 26271.0000 | 350.0000 | 4.3458 | 0.3612 |

## 4. Village Fixed Effects Robustness

| outcome | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| production_participation | 26271.0000 | 350.0000 | 4.1996 | 0.3797 |
| log_selfprod_amount | 26271.0000 | 350.0000 | 18.5739 | 0.0010 |
| ihs_selfprod_amount | 26271.0000 | 350.0000 | 18.1760 | 0.0011 |

Interpretation: village fixed effects shift identification to within-village household comparisons. In this check, the participation-margin Wald test is not significant, while the log/IHS quantity margins become significant. This weakens any claim that the M3 participation result is fully robust. Village-level market, GAEZ, province, and much of county text variation are absorbed or collinear, so this is a robustness check rather than the preferred mechanism specification.

## 5. Logit/Probit Participation Robustness

| model_family | n | n_clusters | outcome_mean | converged | wald_chisq | wald_p |
|---|---|---|---|---|---|---|
| logit | 26271.0000 | 350.0000 | 0.4320 | TRUE | 14.5705 | 0.0057 |
| probit | 26271.0000 | 350.0000 | 0.4320 | TRUE | 15.0861 | 0.0045 |

Category-specific logit/probit rows are in `outputs/tables/tableG_binary_response_robustness.csv`; extreme categories, especially dairy, should be read with separation/low-variation caution.

## 6. Category Multiple Testing and NSI Reframing

| food_category_label | participation_rate | mean_self_suff_rate | nsi | hhcomp_wald_p | p_bh_fdr | main_text_status |
|---|---|---|---|---|---|---|
| 蛋类 | 0.4366 | 0.2888 | 1.6913 | 0.0019 | 0.0115 | main_comparable_category |
| 油脂 | 0.3743 | 0.2674 | 1.5991 | 0.0029 | 0.0115 | definition_pending_human_review |
| 蔬菜 | 0.9336 | 0.5346 | 1.4627 | 0.0053 | 0.0141 | interpret_with_variation_caution |
| 水果 | 0.2899 | 0.0816 | 1.2290 | 0.0147 | 0.0294 | main_comparable_category |
| 豆类 | 0.2221 | 0.0973 | 0.8972 | 0.0601 | 0.0962 | main_comparable_category |
| 肉类和水产品及加工品 | 0.3347 | 0.1291 | 0.4423 | 0.3478 | 0.4606 | aggregate_meat_aquatic_limitations |
| 奶类 | 0.0013 | 0.0013 | 0.3992 | 0.4030 | 0.4606 | exclude_from_main_category_interpretation |
| 主食 | 0.8350 | 0.3300 | 0.2792 | 0.5895 | 0.5895 | interpret_with_variation_caution |

Interpretation: the category table now reports raw p-values and BH FDR q-values. NSI remains useful for describing where the Wald test is most detectable, but it is not an effect size. Participation and self-sufficiency are reported side by side to separate detectability from economic importance.

## 7. Fixed Common-Sample Composition Robustness

| composition_spec | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| proportion | 22211.0000 | 350.0000 | 20.7262 | 0.0004 |
| dependency | 22211.0000 | 350.0000 | 21.3809 | 0.0001 |
| counts | 22211.0000 | 350.0000 | 14.3356 | 0.0063 |

The original robustness table used different samples across proportion, dependency-ratio, and count specifications. This fixed-sample table uses the intersection of all variables needed by all composition definitions and outcomes.

## 8. Fixed-Factor / Bad-Control Sensitivity

| label | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| full_M3_resources | 26271.0000 | 350.0000 | 15.0201 | 0.0047 |
| fixed_factors_no_income_expense | 26271.0000 | 350.0000 | 16.7657 | 0.0021 |
| fixed_factors_no_income_expense_land_w99 | 26271.0000 | 350.0000 | 16.7657 | 0.0021 |

The no-income/no-expense specifications respond to the concern that income and expenditure may be jointly determined with self-provisioning. These should be discussed alongside the full M3 results.

## 9. Price and Unit-Value Diagnostics

| diagnostic | value | interpretation |
|---|---|---|
| observed_unit_value_share | 0.7299 | Observed variable is household purchase-side unit value, not pure exogenous price. |
| hedonic_imputed_share | 0.2701 | A sizeable share is imputed and should be disclosed. |
| county_hedonic_r_squared | 0.4433 | Hedonic imputation explains a moderate share of log unit-value variation. |
| county_hedonic_rmse_log | 0.6981 | RMSE implies noisy unit-value prediction. |
| observed_only_participation_p | 0.0040 | Observed-only robustness remains statistically similar for participation, but on a selected purchasing subsample. |

Price variables should be described as purchase-side unit values. The hedonic values are imputations for missing purchase unit values, not farm-gate selling prices. This limits how strongly price controls can be interpreted in a market-separability framework.

## 10. Data Definition Diagnostics

| diagnostic | value | numeric_value | decision |
|---|---|---|---|
| pooled_repeated_cross_section | min_years_per_nhCode=1; max_years_per_nhCode=1 | 1.0000 | No household fixed effects are feasible with current nhCode; use pooled repeated cross-section language. |
| households_at_roster_cap_8 | 18 of 3565 households | 0.0050 | Roster cap is visible but rare; disclose in data limitations. |
| total_sown_area_w99_max | max=317.965920000001; p99=316.261651200001 | 317.9659 | Winsorized total sown area is used as a sensitivity check; main setup still uses total_sown_area. |
| sex_coding_audit | household_head_gender_male inferred from earlier household relation cross-check, codebook confirmation still needed |  | Keep female_share interpretation conditional until HA2 coding is manually verified. |
| youzhi_definition | partially identified; item-code review required |  | Do not make strong substantive claims about oils before item-code review. |
| roulei_aggregation | meat plus aquatic plus processed products in current aggregate category |  | Use label meat/aquatic products and state aggregation limitation. |

## 11. Missingness Robustness Status

| diagnostic | value | implication |
|---|---|---|
| selfprod_monthly_total_missing_in_current_long_file | 0 | The current long files no longer preserve item-level source missingness. |
| production_participation_missing_in_current_long_file | 0 | Participation is fully populated after prior cleaning. |
| na_to_zero_robustness_status | not_reconstructable_from_current_analysis_ready_or_cleaned_long_files | Report as a limitation and rerun only if raw item-level missing codes are restored. |

## 12. New Artifacts

| output | rows |
|---|---|
| tableE_add_one_block_diagnostics.csv | 30 |
| tableF_village_fe_robustness.csv | 11 |
| tableG_binary_response_robustness.csv | 18 |
| tableH_category_multiple_testing.csv | 8 |
| tableI_category_variation_and_nsi_reframed.csv | 8 |
| tableJ_fixed_common_sample_robustness.csv | 12 |
| tableK_fixed_factors_bad_controls_robustness.csv | 9 |
| tableL_participation_missingness_robustness.csv | 3 |
| tableM_definition_diagnostics_editor.csv | 6 |
| tableN_price_unit_value_diagnostics.csv | 5 |
````

## Report: `outputs/reports/paper1_kg_month_outlier_cleaning_report.md`

- Size: 7.5 KB
- Lines: 89

````markdown
# Paper 1 kg/month Unit Conversion and Outlier Exclusion

Generated at: 2026-07-06 13:40:01

## Official Analysis Files Updated

- `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv`
- `data/cleaned/paper1_household_category_long.csv`
- `/root/data/Paper/食物消费数据/Paper1-Seperability/data/analysis_ready/paper1_reprocessed_analysis_ready_long_kg_month_outlier_cleaned.csv`

## Unit Rules

- Household food quantities are converted from jin/month to kg/month using `kg = jin * 0.5`.
- Unit values are converted from yuan/jin to yuan/kg using `yuan/kg = yuan/jin * 2`.
- `log_selfprod_amount` and `ihs_selfprod_amount` are recomputed from `selfprod_kg_month`.
- The quantities are household totals, so the model unit is kg/month/household, not kg/person/month.
- Legacy column names ending in `_jin` or `_yuan_per_jin` are retained for old scripts, but their values are now kg/month or yuan/kg. Clearly named kg/yuan-per-kg columns are also present.

## Outlier Rules

- Food quantity rows are excluded from model data when `cons_kg_month`, `selfprod_kg_month`, or `purchase_qty_kg_month` exceeds the food-category P99.5 threshold, provided the category has at least 30 positive observations for that variable.
- Observed household unit-value outliers are set to missing before observed-price-only robustness models.
- Village median unit-value outliers are set to missing before village-price robustness models; this removes the 30,000 yuan/kg village-price records.
- Hedonic main price outliers are replaced by the category median so the main price control remains complete.
- Spending outliers are flagged for audit but not used to drop rows, because spending is not a model outcome.

## Cleaning Summary

| metric | value |
|---|---|
| rows_before_outlier_exclusion | 27,510.000 |
| rows_after_outlier_exclusion | 27,190.000 |
| rows_dropped_for_quantity_outlier | 320.000 |
| households_before | 3,565.000 |
| households_after | 3,565.000 |
| food_categories | 8.000 |
| observed_price_cells_set_missing | 0.000 |
| hedonic_price_cells_replaced_by_category_median | 0.000 |
| village_price_cells_set_missing | 191.000 |
| spend_outlier_rows_flagged_not_dropped | 98.000 |

## Outlier Counts by Category

| food_category | food_category_label | outlier_cons_kg_month | outlier_selfprod_kg_month | outlier_purchase_qty_kg_month | outlier_quantity_any | outlier_observed_price_any | outlier_hedonic_price_any | outlier_village_price_any | outlier_spend_any | n_before | n_after |
|---|---|---|---|---|---|---|---|---|---|---|---|
| zhushi | 主食 | 18.000 | 15.000 | 17.000 | 50.000 | 0.000 | 0.000 | 29.000 | 17.000 | 3,423.000 | 3,373.000 |
| nailei | 奶类 | 15.000 | 0.000 | 8.000 | 23.000 | 0.000 | 0.000 | 28.000 | 9.000 | 3,485.000 | 3,462.000 |
| shuiguo | 水果 | 18.000 | 14.000 | 17.000 | 48.000 | 0.000 | 0.000 | 18.000 | 14.000 | 3,420.000 | 3,372.000 |
| youzhi | 油脂 | 16.000 | 2.000 | 0.000 | 18.000 | 0.000 | 0.000 | 28.000 | 5.000 | 3,438.000 | 3,420.000 |
| roulei | 肉类和水产品及加工品 | 16.000 | 18.000 | 17.000 | 48.000 | 0.000 | 0.000 | 29.000 | 15.000 | 3,435.000 | 3,387.000 |
| shucai | 蔬菜 | 18.000 | 18.000 | 13.000 | 44.000 | 0.000 | 0.000 | 20.000 | 14.000 | 3,437.000 | 3,393.000 |
| danlei | 蛋类 | 18.000 | 18.000 | 11.000 | 47.000 | 0.000 | 0.000 | 19.000 | 11.000 | 3,436.000 | 3,389.000 |
| doulei | 豆类 | 18.000 | 8.000 | 16.000 | 42.000 | 0.000 | 0.000 | 20.000 | 13.000 | 3,436.000 | 3,394.000 |

## Category Descriptives After Cleaning

| food_category | food_category_label | participation_rate | mean_cons_kg_month | mean_selfprod_kg_month | mean_self_suff_rate | mean_price_yuan_per_kg |
|---|---|---|---|---|---|---|
| zhushi | 主食 | 0.835 | 24.112 | 7.343 | 0.330 | 9.875 |
| nailei | 奶类 | 0.001 | 2.928 | 0.000 | 0.001 | 39.011 |
| shuiguo | 水果 | 0.290 | 12.150 | 0.909 | 0.082 | 8.283 |
| youzhi | 油脂 | 0.374 | 2.804 | 0.514 | 0.267 | 30.599 |
| roulei | 肉类和水产品及加工品 | 0.335 | 6.078 | 0.954 | 0.129 | 36.633 |
| shucai | 蔬菜 | 0.934 | 21.100 | 13.143 | 0.535 | 11.980 |
| danlei | 蛋类 | 0.437 | 1.986 | 0.516 | 0.289 | 25.925 |
| doulei | 豆类 | 0.222 | 1.997 | 0.153 | 0.097 | 13.250 |

## Key Descriptives After Cleaning

| module | variable | n | missing | missing_share | mean | sd | min | p01 | p05 | p25 | median | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kg_month_outlier_cleaned | production_participation | 27,190.000 | 0.000 | 0.000 | 0.430 | 0.495 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| kg_month_outlier_cleaned | cons_kg_month | 27,190.000 | 0.000 | 0.000 | 8.985 | 17.488 | 0.000 | 0.000 | 0.073 | 0.430 | 2.143 | 7.993 | 46.507 | 85.714 | 167.524 |
| kg_month_outlier_cleaned | selfprod_kg_month | 27,190.000 | 0.000 | 0.000 | 2.974 | 9.824 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.682 | 19.607 | 54.214 | 100.714 |
| kg_month_outlier_cleaned | purchase_qty_kg_month | 22,701.000 | 4,489.000 | 0.165 | 11.693 | 16.684 | 0.042 | 0.250 | 0.750 | 2.500 | 5.720 | 13.000 | 43.665 | 81.567 | 171.500 |
| kg_month_outlier_cleaned | self_suff_rate | 26,493.000 | 697.000 | 0.026 | 0.217 | 0.342 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.364 | 1.000 | 1.000 | 1.000 |
| kg_month_outlier_cleaned | log_selfprod_amount | 27,190.000 | 0.000 | 0.000 | 0.508 | 0.972 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.520 | 3.026 | 4.011 | 4.622 |
| kg_month_outlier_cleaned | ihs_selfprod_amount | 27,190.000 | 0.000 | 0.000 | 0.626 | 1.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.638 | 3.670 | 4.686 | 5.305 |
| kg_month_outlier_cleaned | price_hedonic_imputed_w99_yuan_per_kg | 27,190.000 | 0.000 | 0.000 | 21.862 | 25.246 | 0.618 | 1.371 | 3.600 | 9.091 | 16.756 | 27.798 | 52.060 | 97.075 | 400.000 |
| kg_month_outlier_cleaned | price_preferred_household_recalc_w99_yuan_per_kg | 19,813.000 | 7,377.000 | 0.271 | 22.441 | 33.510 | 0.033 | 1.074 | 2.877 | 8.250 | 14.667 | 26.667 | 60.000 | 120.000 | 638.800 |
| kg_month_outlier_cleaned | village_price_category_median_yuan_per_kg | 22,438.000 | 4,752.000 | 0.175 | 169.593 | 607.960 | 3.632 | 15.040 | 20.800 | 37.040 | 53.360 | 86.640 | 236.219 | 4,000.000 | 8,000.000 |
| kg_month_outlier_cleaned | spend_sum_yuan | 19,816.000 | 7,374.000 | 0.271 | 96.390 | 192.359 | 0.400 | 2.500 | 5.000 | 20.000 | 50.000 | 110.000 | 317.250 | 714.550 | 12,070.000 |
| kg_month_outlier_cleaned | household_size_reconstructed | 27,190.000 | 0.000 | 0.000 | 2.870 | 1.395 | 0.000 | 1.000 | 1.000 | 2.000 | 2.000 | 4.000 | 6.000 | 7.000 | 8.000 |
| kg_month_outlier_cleaned | child_share | 27,046.000 | 144.000 | 0.005 | 0.082 | 0.166 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 0.667 | 1.000 |
| kg_month_outlier_cleaned | elderly_share | 27,046.000 | 144.000 | 0.005 | 0.214 | 0.343 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.333 | 1.000 | 1.000 | 1.000 |
| kg_month_outlier_cleaned | female_share | 27,046.000 | 144.000 | 0.005 | 0.508 | 0.208 | 0.000 | 0.000 | 0.000 | 0.500 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 |
| kg_month_outlier_cleaned | agricultural_labor_days | 27,190.000 | 0.000 | 0.000 | 287.714 | 252.408 | 0.000 | 0.000 | 0.000 | 60.000 | 240.000 | 420.000 | 730.000 | 1,030.000 | 2,190.000 |
| kg_month_outlier_cleaned | offfarm_labor_days | 27,190.000 | 0.000 | 0.000 | 193.974 | 250.087 | 0.000 | 0.000 | 0.000 | 0.000 | 100.000 | 300.000 | 695.000 | 1,055.000 | 2,155.000 |
| kg_month_outlier_cleaned | total_sown_area | 27,190.000 | 0.000 | 0.000 | 22.979 | 52.196 | 0.000 | 0.000 | 0.000 | 1.000 | 5.200 | 16.000 | 120.220 | 314.588 | 317.966 |
````

## Report: `outputs/reports/paper1_revised_results_package.md`

- Size: 13.5 KB
- Lines: 228

````markdown
# Paper 1 Revised Results Package

Generated at: 2026-07-06 13:41:48

## 1. Executive summary

- MAIN RESULT: household composition predicts self-provisioning participation in the common-sample M3 model (Wald = 15.020, p = 0.005).
- MAIN RESULT: full-sample intensive amount margins are weaker (`log_selfprod_amount` p = 0.361; `ihs_selfprod_amount` p = 0.384), so participation remains the clearest margin.
- SUPPORTING RESULT: the two-part conditional-intensity model is weak, reinforcing the entry-margin interpretation.
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

- rows: 27190
- households: 3565
- food_categories: 8
- villages_clusters: 361
- provinces: 9
- counties: 44
- duplicate_household_category_keys: 0

### Observations by data_year

- 2023: 13496
- 2024: 13694

### Observations by food_category

- danlei / 蛋类: 3389
- doulei / 豆类: 3394
- nailei / 奶类: 3462
- roulei / 肉类和水产品及加工品: 3387
- shucai / 蔬菜: 3393
- shuiguo / 水果: 3372
- youzhi / 油脂: 3420
- zhushi / 主食: 3373

### Missingness by core variables

- outcome / `production_participation`: 0 missing
- outcome / `log_selfprod_amount`: 0 missing
- outcome / `ihs_selfprod_amount`: 0 missing
- outcome / `self_suff_rate`: 697 missing
- household_composition / `household_size_reconstructed`: 0 missing
- household_composition / `child_share`: 144 missing
- household_composition / `elderly_share`: 144 missing
- household_composition / `female_share`: 144 missing
- market / `market_friction_survey`: 689 missing
- market / `poi_market_friction_lag1`: 78 missing
- market / `combined_market_friction`: 0 missing
- price / `price_hedonic_imputed_w99_yuan_per_kg`: 0 missing
- price / `price_preferred_household_recalc_w99_yuan_per_kg`: 7377 missing
- price / `village_price_category_median_yuan_per_kg`: 4752 missing
- gaez / `gaez_overall_si_10km`: 78 missing
- gaez / `gaez_staple_si_10km`: 78 missing
- gaez / `gaez_soil_terrain_constraint_10km`: 78 missing
- text / `risk_salience_z_5yr_sum`: 8 missing
- text / `governance_capacity_z_5yr_sum`: 8 missing
- text / `trust_signal_z_5yr_sum`: 8 missing
- text / `attention_z_5yr_sum`: 8 missing

- M0-M3 common sample constructed: TRUE
- Common-sample N: 26271
- Common-sample cluster count: 350

## 3. Main baseline results

- Table: `outputs/tables/table2_common_sample_baseline.csv`
- Model summary: `outputs/model_summaries/model2_common_sample_baseline.json`

- `production_participation`: Wald = 15.020, df = 4, p = 0.005, N = 26271.
- `log_selfprod_amount`: Wald = 4.346, p = 0.361.
- `ihs_selfprod_amount`: Wald = 4.169, p = 0.384.

Interpretation: The evidence rejects separability restrictions on the self-provisioning participation margin, but provides weaker evidence on the self-production quantity margin. This is a reduced-form association, not a causal treatment effect.

## 4. Household-composition coefficient interpretation

- Table: `outputs/tables/table3_baseline_coefficients_margins.csv`
- Figure: `outputs/figures/figure3_household_composition_coefficients.png`

- `household_size_reconstructed`: beta = -0.0075, SE = 0.0031, p = 0.018, direction = negative, stable across M0-M3 = TRUE
- `child_share`: beta = 0.0436, SE = 0.0221, p = 0.048, direction = positive, stable across M0-M3 = FALSE
- `elderly_share`: beta = 0.0406, SE = 0.0132, p = 0.002, direction = positive, stable across M0-M3 = FALSE
- `female_share`: beta = 0.0104, SE = 0.0164, p = 0.526, direction = positive, stable across M0-M3 = FALSE

## 5. Category-specific non-separability and NSI

- Table: `outputs/tables/table4_category_specific_nsi.csv`
- Figure: `outputs/figures/figure2_nsi_by_category.png`

- Strong categories: 蛋类, 油脂, 蔬菜
- Weak categories: 主食, 豆类, 肉类和水产品及加工品, 奶类

- 主食: Wald = 2.813, p = 0.590, NSI = 0.279, signal = Weak, drivers = none_p_lt_0.10
- 豆类: Wald = 9.040, p = 0.060, NSI = 0.897, signal = Weak, drivers = elderly_share
- 肉类和水产品及加工品: Wald = 4.456, p = 0.348, NSI = 0.442, signal = Weak, drivers = elderly_share
- 蛋类: Wald = 17.042, p = 0.002, NSI = 1.691, signal = Strong, drivers = elderly_share
- 奶类: Wald = 4.022, p = 0.403, NSI = 0.399, signal = Weak, drivers = household_size_reconstructed;female_share
- 油脂: Wald = 16.113, p = 0.003, NSI = 1.599, signal = Strong, drivers = household_size_reconstructed;child_share;female_share
- 蔬菜: Wald = 14.739, p = 0.005, NSI = 1.463, signal = Strong, drivers = household_size_reconstructed;elderly_share
- 水果: Wald = 12.384, p = 0.015, NSI = 1.229, signal = Moderate, drivers = household_size_reconstructed

Possible substantive explanation: the signal is concentrated in categories where households may make discrete entry decisions into self-provisioning. Data-definition concerns remain for `youzhi` and the combined `roulei` category.

## 6. Two-part model: entry versus conditional intensity

- Table: `outputs/tables/table5_two_part_model.csv`

- Part 1 (all observations, outcome `production_participation`): Wald = 15.020, p = 0.005, N = 26271
- Part 2 (production_participation == 1, outcome `log_selfprod_amount`): Wald = 7.627, p = 0.106, N = 11348

Interpretation: Part 1 is significant and Part 2 is weak, so the main non-separability signal operates through entry into self-provisioning rather than conditional intensity.

## 7. Robustness checks

### 7.1 Alternative household composition and outcomes

- proportion / `production_participation`: Wald = 15.020, p = 0.005, N = 26271
- proportion / `log_selfprod_amount`: Wald = 4.346, p = 0.361, N = 26271
- proportion / `ihs_selfprod_amount`: Wald = 4.169, p = 0.384, N = 26271
- proportion / `self_suff_rate`: Wald = 10.533, p = 0.032, N = 25602
- dependency / `production_participation`: Wald = 23.030, p = <0.001, N = 22799
- dependency / `log_selfprod_amount`: Wald = 5.828, p = 0.120, N = 22799
- dependency / `ihs_selfprod_amount`: Wald = 5.592, p = 0.133, N = 22799
- dependency / `self_suff_rate`: Wald = 10.065, p = 0.018, N = 22211
- counts / `production_participation`: Wald = 18.000, p = 0.001, N = 26415
- counts / `log_selfprod_amount`: Wald = 7.430, p = 0.115, N = 26415
- counts / `ihs_selfprod_amount`: Wald = 7.364, p = 0.118, N = 26415
- counts / `self_suff_rate`: Wald = 14.328, p = 0.006, N = 25742

### 7.2 Province leave-one-out

- Minimum leave-one-province Wald: 9.505
- Maximum leave-one-province Wald: 18.280
- All leave-one-province estimates remain significant: TRUE
- Most influential drop by minimum Wald: 福建省

### 7.3 Household-composition permutation placebo

- Permutations: 99; true Wald = 15.020; placebo mean = 4.080; placebo P95 = 10.151; randomization p = 0.010.

## 8. Appendix mechanism diagnostics

### 8.1 Market-friction interactions

- survey_market_friction / `production_participation`: interaction Wald = 0.826, p = 0.935.
- survey_market_friction / `log_selfprod_amount`: interaction Wald = 4.451, p = 0.348.
- survey_market_friction / `ihs_selfprod_amount`: interaction Wald = 4.735, p = 0.316.
- poi_market_friction / `production_participation`: interaction Wald = 2.022, p = 0.732.
- poi_market_friction / `log_selfprod_amount`: interaction Wald = 3.709, p = 0.447.
- poi_market_friction / `ihs_selfprod_amount`: interaction Wald = 3.549, p = 0.471.
- combined_market_friction / `production_participation`: interaction Wald = 0.596, p = 0.964.
- combined_market_friction / `log_selfprod_amount`: interaction Wald = 4.014, p = 0.404.
- combined_market_friction / `ihs_selfprod_amount`: interaction Wald = 3.945, p = 0.413.

Default interpretation: Market-friction interactions do not provide strong support for a cross-sectional amplification mechanism if the p-values remain weak.

### 8.2 IV diagnostics

- terrain_town_2km: corr = 0.129, min F = 1.142, median F = 2.080, weak = TRUE.
- terrain_town_1km: corr = 0.133, min F = 0.981, median F = 2.025, weak = TRUE.
- terrain_town_5km: corr = 0.115, min F = 1.449, median F = 2.144, weak = TRUE.
- terrain_county_2km: corr = 0.134, min F = 2.029, median F = 2.118, weak = TRUE.
- early_ntl_9294: corr = 0.112, min F = 0.736, median F = 1.333, weak = TRUE.

Default interpretation: IV results are reported as diagnostics and should not be used as the main identification basis when first stages are weak.

## 9. Price robustness

- no_price_control: Wald = 14.926, p = 0.005, N = 26271.
- hedonic_price_main: Wald = 15.020, p = 0.005, N = 26271.
- observed_price_only: Wald = 15.361, p = 0.004, N = 19258.
- county_category_median_price: Wald = 8.493, p = 0.075, N = 22196.

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

The results indicate that household composition significantly predicts category-specific self-provisioning participation, providing reduced-form evidence inconsistent with separability. This evidence is strongest on the extensive margin: household composition predicts whether households enter self-provisioning, while conditional quantity responses are weaker. The category-specific analysis shows that non-separability is concentrated in eggs, oils, vegetables, fruits, and beans, rather than being uniform across food groups. Market-friction interactions and IV diagnostics provide weaker support for the market-friction amplification mechanism and are therefore interpreted as exploratory.
````

## 5. Logs

## Log: `outputs/logs/appendix_mechanism_diagnostics.md`

- Size: 0.5 KB
- Lines: 9

````markdown
# Appendix Mechanism Diagnostics

Generated at: 2026-07-06 13:41:39

## Market-friction interactions

- Market-friction interactions are appendix/exploratory diagnostics under the revised plan.
- They should not be used as the main identification claim unless strong and stable evidence emerges.
- Default interpretation if weak: Market-friction interactions do not provide strong support for a cross-sectional amplification mechanism in the current specification.
````

## Log: `outputs/logs/commercialization_rate_audit.md`

- Size: 0.7 KB
- Lines: 19

````markdown
# Commercialization Rate Audit

Generated at: 2026-07-06 13:40:13

## Finding

- `commercialization_rate` is not present in the current analysis-ready household-category file.
- Current analysis-ready columns only contain self-provisioning participation, self-production amount, consumption, self-sufficiency, and price variables.
- Raw labels indicate sales and self-use quantities exist for some production modules, but denominators differ by module and category.
- A clean commercialization rate therefore requires a separate denominator audit before inclusion.

## Matching variables found in analysis-ready data

- None.

## Decision

- Do not construct `commercialization_rate` in the revised main rerun.
- Record as HUMAN REVIEW REQUIRED: denominator unclear.
````

## Log: `outputs/logs/common_sample_log.md`

- Size: 1.4 KB
- Lines: 51

````markdown
# Common Sample Log

Generated at: 2026-07-06 13:40:20

- M0-M3 are estimated on the common complete-case M3 sample.
- Original revised rows: 27190
- Common M3 rows: 26271
- Common M3 clusters: 350
- Rows excluded from common M3 sample: 919
- Excluded share: 0.0338

## Variables defining the common M3 sample

- `production_participation`
- `log_selfprod_amount`
- `ihs_selfprod_amount`
- `household_size_reconstructed`
- `child_share`
- `elderly_share`
- `female_share`
- `log1p_total_income_w_w99_imp`
- `log1p_total_income_w_w99_missing`
- `log1p_agri_business_income_w99_imp`
- `log1p_agri_business_income_w99_missing`
- `log1p_annual_expense_total_w99_imp`
- `log1p_annual_expense_total_w99_missing`
- `total_sown_area`
- `agricultural_labor_days`
- `offfarm_labor_days`
- `household_assets_count_proxy_imp`
- `household_assets_count_proxy_missing`
- `household_head_age_imp`
- `household_head_age_missing`
- `household_head_education_imp`
- `household_head_education_missing`
- `household_head_gender_male_imp`
- `household_head_gender_male_missing`
- `market_friction_survey`
- `poi_market_friction_lag1`
- `gaez_overall_si_10km`
- `gaez_staple_si_10km`
- `gaez_soil_terrain_constraint_10km`
- `provn_std`
- `price_hedonic_imputed_w99_yuan_per_jin`
- `risk_salience_z_5yr_sum`
- `governance_capacity_z_5yr_sum`
- `trust_signal_z_5yr_sum`
- `attention_z_5yr_sum`
- `food_category`
- `data_year`
- `xzc12_for_merge_final`
````

## Log: `outputs/logs/editor_review_action_log.md`

- Size: 1.2 KB
- Lines: 22

````markdown
# Editor Review Action Log

Generated at: 2026-07-06 13:42:27

Completed with current analysis-ready data:

- Add-one-block diagnostics for M0/M1/M2/M3 sensitivity and M1-to-M2 block attribution.
- Village fixed-effects robustness for overall outcomes and category-specific participation.
- Logit/probit participation robustness for overall and category-specific models.
- Bonferroni, Holm, and BH FDR corrections for category-level Wald tests.
- NSI reframing with participation/self-sufficiency and low-variation flags.
- Fixed common-sample composition and price robustness checks.
- Fixed-factor/no-income/no-expense sensitivity checks.
- Price unit-value and hedonic imputation diagnostics.
- Definition diagnostics for repeated-cross-section status, roster cap, land winsorization, sex coding, oils, and meat/aquatic aggregation.

Still requires manual or raw-item-code work:

- HA2 sex-codebook verification for `female_share` interpretation.
- Item-code review for `youzhi` and detail-level rebuild if meat versus aquatic categories are to be split.
- Raw item-level missing-code recovery before a valid NA-to-zero versus missing-exclusion participation robustness can be run.
- Formal theoretical model and replacement of the placeholder conceptual framework figure.
````

## Log: `outputs/logs/hedonic_price_imputation.md`

- Size: 1.2 KB
- Lines: 33

````markdown
# Hedonic Price Imputation

Generated at: 2026-07-06 13:39:12

## Outcome

- Updated `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv` in place.
- Observed price is `price_recalc_spend_sum_over_purchase_qty_sum`.
- Fitting price is category-level P1/P99 winsorized observed household recalc price.
- Dependent variable is log fitting price.

## Imputation Hierarchy

1. Keep observed household-recalculated price when available.
2. Use county-level hedonic prediction for missing household price.
3. Use province-level hedonic prediction when county-level prediction is unavailable.
4. Use category-year hedonic prediction when province-level prediction is unavailable.
5. Use category median fallback if all model predictions fail.

## New Columns

- `price_hedonic_observed_fit_yuan_per_jin`
- `price_hedonic_predicted_yuan_per_jin`
- `price_hedonic_prediction_tier`
- `price_hedonic_imputed_yuan_per_jin`
- `price_hedonic_imputed_w99_yuan_per_jin`
- `price_hedonic_source`

## Outputs

- `outputs/tables/hedonic_price_model_diagnostics.csv`
- `outputs/tables/hedonic_price_imputation_summary_by_category.csv`
- `outputs/tables/hedonic_price_imputation_source_summary.csv`
````

## Log: `outputs/logs/iv_diagnostics_appendix.md`

- Size: 0.6 KB
- Lines: 14

````markdown
# IV Diagnostics Appendix

Generated at: 2026-07-06 13:41:47

- IV diagnostics are appendix/exploratory only under the revised plan.
- IV results are not used as the main identification basis.

## Summary

- terrain_town_2km: corr = 0.129, min F = 1.142, median F = 2.080, weak = TRUE.
- terrain_town_1km: corr = 0.133, min F = 0.981, median F = 2.025, weak = TRUE.
- terrain_town_5km: corr = 0.115, min F = 1.449, median F = 2.144, weak = TRUE.
- terrain_county_2km: corr = 0.134, min F = 2.029, median F = 2.118, weak = TRUE.
- early_ntl_9294: corr = 0.112, min F = 0.736, median F = 1.333, weak = TRUE.
````

## Log: `outputs/logs/kg_month_outlier_cleaning.md`

- Size: 0.5 KB
- Lines: 16

````markdown
# kg/month Unit Conversion and Outlier Cleaning Log

Generated at: 2026-07-06 13:40:01

- Converted official analysis data to kg/month/household and yuan/kg.
- Excluded quantity outlier household-category rows using category-specific P99.5 thresholds.
- Cleaned price outliers before robustness and main-price use.
- Backups of prior analysis files were written to `data/backups/`.

## Summary

- Rows before: 27510
- Rows after: 27190
- Rows dropped: 320
- Households before: 3565
- Households after: 3565
````

## Log: `outputs/logs/price_robustness_issues.md`

- Size: 0.7 KB
- Lines: 15

````markdown
# Price Robustness Issues

Generated at: 2026-07-06 13:40:32

## Notes

- Price variables are interpreted as yuan/kg in the cleaned analysis data.
- Main price variable: `price_hedonic_imputed_w99_yuan_per_kg`.
- Observed-price-only uses `price_preferred_household_recalc_w99_yuan_per_kg` and drops rows with missing observed recalculated price.
- County-category median price uses `village_price_category_median_yuan_per_kg` and drops rows with missing median price.
- The model still reads legacy compatibility aliases ending in `_yuan_per_jin`; those alias values were overwritten to yuan/kg by `code/19_apply_kg_units_drop_outliers_prepare_official_data.R`.

## Issues

- None. All requested price robustness variants were generated.
````

## Log: `outputs/logs/revised_data_merge_log.md`

- Size: 0.8 KB
- Lines: 17

````markdown
# Revised Data Merge Log

Generated at: 2026-07-06 13:40:13

- Input file: `/root/data/Paper/食物消费数据/Paper1-Seperability/data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv`.
- Output file: `/root/data/Paper/食物消费数据/Paper1-Seperability/data/analysis_ready/paper1_revised_analysis_ready_long.csv`.
- The revised analysis file inherits the cleaned geography, POI-year rule, hedonic price imputation, GAEZ, terrain, early NTL, county text, and household resource controls from the previously rebuilt analysis-ready long file.
- Food categories are restricted to the eight revised categories; condiments, sugar, and tea are excluded.

## Sample summary

- Rows: 27190
- Households: 3565
- Food categories: 8
- Villages/clusters: 361
- Provinces: 9
- Counties: 44
````

## Log: `outputs/logs/revised_variable_issues.md`

- Size: 0.4 KB
- Lines: 7

````markdown
# Revised Variable Issues

Generated at: 2026-07-06 13:40:13

- `commercialization_rate` is unavailable in the current analysis-ready data and is not constructed without denominator review.
- `roulei` split and `youzhi` definition require category-definition audit outputs.
- Main code variable remains `production_participation`; prose label should be self-provisioning participation.
````

## Log: `outputs/logs/roulei_split_audit.md`

- Size: 0.7 KB
- Lines: 15

````markdown
# Roulei Split Audit

Generated at: 2026-07-06 13:40:32

## Finding

- Raw labels contain meat-detail variables: TRUE.
- Raw labels contain aquatic-detail variables such as `shuichan_1`: TRUE.
- The current analysis-ready household-category long data contains only the aggregate `roulei` category and does not contain separate `meat` and `aquatic_products` outcomes.
- A split would require rebuilding consumption, self-provisioning participation, self-production amount, price, and self-sufficiency outcomes from item-level raw variables.

## Decision

- Roulei split is not performed in this revised rerun.
- Human review is required before making split-category claims.
````

## Log: `outputs/logs/youzhi_definition_audit.md`

- Size: 0.7 KB
- Lines: 15

````markdown
# Youzhi Definition Audit

Generated at: 2026-07-06 13:40:32

## Finding

- Raw labels contain aggregate `youzhi` consumption/source variables: TRUE.
- Raw labels contain oilseed production module variables (`youliao_shengchan`): TRUE.
- The food-category documentation defines `youzhi` as `油脂类`.
- The available labels do not clearly state whether the strong `youzhi` result reflects oil crops, home-produced edible oil, self-retained oilseeds, purchased oils with self-production source, or a mixture.

## Decision

- Keep `youzhi` as the aggregate oils category in revised models.
- Human review required before making strong substantive claims about the oil category.
````

## 6. Tables

## Table CSV: `outputs/tables/hedonic_price_imputation_source_summary.csv`

- Size: 0.1 KB
- Lines: 3

````csv
"price_hedonic_source","n_rows","share"
"hedonic_county",7430,0.270083605961469
"observed_household_recalc",20080,0.729916394038531
````

## Table CSV: `outputs/tables/hedonic_price_imputation_summary_by_category.csv`

- Size: 1.3 KB
- Lines: 9

````csv
"food_category","food_category_label","n","n_observed_household_recalc","n_hedonic_imputed","n_county_tier","n_province_tier","n_category_year_tier","n_category_median_fallback","observed_mean","hedonic_imputed_mean","hedonic_imputed_w99_mean","hedonic_imputed_p50","hedonic_imputed_p99","hedonic_imputed_max"
"zhushi","主食",3423,3266,157,157,0,0,0,10.1729255665026,10.1177089517705,9.87341834541291,9.48275862068964,31.6595856387058,231.085714285714
"doulei","豆类",3436,2494,942,942,0,0,0,14.308347461602,13.5897935313904,13.3076456080575,12,44.8306451612903,240
"roulei","肉类和水产品及加工品",3435,2842,593,593,0,0,0,39.5782913170734,37.6220570013512,36.7994900383036,29.7386197389849,144.103333333333,1118.78787878788
"danlei","蛋类",3436,2236,1200,1200,0,0,0,28.0315851366611,26.9765445979262,26.122687388955,24,80,2000
"nailei","奶类",3485,1632,1853,1853,0,0,0,55.6225454050436,41.4972424701972,38.1735504325748,27.993287295122,400,2823.3918128655
"youzhi","油脂",3438,2144,1294,1294,0,0,0,33.7259142908846,31.5802392234872,30.7829224911231,28,92.8400000000001,800
"shucai","蔬菜",3437,2699,738,738,0,0,0,13.0253883342607,12.2846469935604,11.9484114123284,9.57622300192668,60,200
"shuiguo","水果",3420,2767,653,653,0,0,0,8.8551584403535,8.40718742283808,8.28240690188389,6.41116366994324,35.2838095238095,102
````

## Table CSV: `outputs/tables/hedonic_price_model_diagnostics.csv`

- Size: 0.3 KB
- Lines: 4

````csv
"model","n_train","r_squared","adj_r_squared","rmse_log_in_sample"
"county",20080,0.443267689256615,0.44157118256487,0.69812876821501
"province",20080,0.434842806765902,0.434110044235403,0.703391232900072
"category_year",20080,0.416302505164342,0.41606985208484,0.714835703486572
````

## Table CSV: `outputs/tables/paper1_category_descriptives_after_kg_outlier_cleaning.csv`

- Size: 1 KB
- Lines: 9

````csv
"food_category","food_category_label","participation_rate","mean_cons_kg_month","mean_selfprod_kg_month","mean_self_suff_rate","mean_price_yuan_per_kg"
"zhushi","主食",0.834983498349835,24.1118178983184,7.3434433305156,0.329961210871232,9.87510230744788
"nailei","奶类",0.00130208333333333,2.92829785051959,0.000247920640116459,0.00125558035714286,39.01081817504
"shuiguo","水果",0.289880952380952,12.1501382113788,0.908546895730005,0.0816117329756171,8.28346823765439
"youzhi","油脂",0.374326750448833,2.80385018824736,0.513528258148052,0.267439441350403,30.5989752606168
"roulei","肉类和水产品及加工品",0.334715639810427,6.07757366756046,0.954126112319941,0.129072992503298,36.6334923784451
"shucai","蔬菜",0.933577087141987,21.0996473469639,13.1432534196113,0.534569009772548,11.9803756059981
"danlei","蛋类",0.436607142857143,1.98551156058016,0.515638588982067,0.288806955018255,25.9247405869283
"doulei","豆类",0.22209026128266,1.99720228096339,0.153061696425834,0.097302139641331,13.2502683106001
````

## Table CSV: `outputs/tables/paper1_descriptives_after_kg_outlier_cleaning.csv`

- Size: 3 KB
- Lines: 19

````csv
"module","variable","n","missing","missing_share","mean","sd","min","p01","p05","p25","median","p75","p95","p99","max"
"kg_month_outlier_cleaned","production_participation",27190,0,0,0.430194924604634,0.495112378280322,0,0,0,0,0,1,1,1,1
"kg_month_outlier_cleaned","cons_kg_month",27190,0,0,8.98517012410479,17.4880551934577,0,0,0.0725360576923077,0.429528846153846,2.14285714285715,7.99285714285715,46.5068896925509,85.7142857142855,167.524079321231
"kg_month_outlier_cleaned","selfprod_kg_month",27190,0,0,2.97434314015701,9.82359746917967,0,0,0,0,0,0.68181818181818,19.6071428571429,54.2142857142855,100.714285714285
"kg_month_outlier_cleaned","purchase_qty_kg_month",22701,4489,0.165097462302317,11.6934769613673,16.6843021067332,0.0415,0.25,0.75,2.5,5.72,13,43.665,81.5665,171.5
"kg_month_outlier_cleaned","self_suff_rate",26493,697,0.0256344244207429,0.217413157529161,0.341705807153218,0,0,0,0,0,0.363636363636364,1,1,1
"kg_month_outlier_cleaned","log_selfprod_amount",27190,0,0,0.508096763164872,0.972167041102068,0,0,0,0,0,0.519875459285908,3.0256377563329,4.01122171897216,4.62216776235666
"kg_month_outlier_cleaned","ihs_selfprod_amount",27190,0,0,0.626033240969081,1.18043091801,0,0,0,0,0,0.637707836941499,3.66969077493009,4.68617667497344,5.30545948005332
"kg_month_outlier_cleaned","price_hedonic_imputed_w99_yuan_per_kg",27190,0,0,21.8617369196707,25.2458230007276,0.618092514718252,1.37142857142857,3.6,9.09090909090908,16.7559523809524,27.7977220016612,52.0604674796747,97.0750476190478,400
"kg_month_outlier_cleaned","price_preferred_household_recalc_w99_yuan_per_kg",19813,7377,0.271312982714233,22.441180940029,33.5096080040123,0.0327421555252388,1.07373156126771,2.87671794871795,8.25,14.6666666666667,26.6666666666666,60,120,638.8
"kg_month_outlier_cleaned","village_price_category_median_yuan_per_kg",22438,4752,0.174770136079441,169.592989036456,607.960107536123,3.632,15.04,20.8,37.04,53.36,86.64,236.21919999999,4000,8000
"kg_month_outlier_cleaned","spend_sum_yuan",19816,7374,0.271202648032365,96.3895913403311,192.358768122219,0.4,2.5,5,20,50,110,317.25,714.549999999996,12070
"kg_month_outlier_cleaned","household_size_reconstructed",27190,0,0,2.86980507539537,1.39540380826094,0,1,1,2,2,4,6,7,8
"kg_month_outlier_cleaned","child_share",27046,144,0.00529606472968003,0.081536130683879,0.165929568910003,0,0,0,0,0,0,0.5,0.666666666666667,1
"kg_month_outlier_cleaned","elderly_share",27046,144,0.00529606472968003,0.213905233763993,0.343476014870995,0,0,0,0,0,0.333333333333333,1,1,1
"kg_month_outlier_cleaned","female_share",27046,144,0.00529606472968003,0.507568058651398,0.20836760002384,0,0,0,0.5,0.5,0.5,1,1,1
"kg_month_outlier_cleaned","agricultural_labor_days",27190,0,0,287.714490621552,252.407989665396,0,0,0,60,240,420,730,1030,2190
"kg_month_outlier_cleaned","offfarm_labor_days",27190,0,0,193.973593232806,250.086520542014,0,0,0,0,100,300,695,1055,2155
"kg_month_outlier_cleaned","total_sown_area",27190,0,0,22.9793949235013,52.1957701063426,0,0,0,1,5.2,16,120.22,314.58833,317.965920000001
````

## Table CSV: `outputs/tables/paper1_kg_month_outlier_cleaning_summary.csv`

- Size: 0.4 KB
- Lines: 11

````csv
"metric","value"
"rows_before_outlier_exclusion",27510
"rows_after_outlier_exclusion",27190
"rows_dropped_for_quantity_outlier",320
"households_before",3565
"households_after",3565
"food_categories",8
"observed_price_cells_set_missing",0
"hedonic_price_cells_replaced_by_category_median",0
"village_price_cells_set_missing",191
"spend_outlier_rows_flagged_not_dropped",98
````

## Table CSV: `outputs/tables/paper1_kg_month_outlier_counts_by_category.csv`

- Size: 0.7 KB
- Lines: 9

````csv
"food_category","food_category_label","outlier_cons_kg_month","outlier_selfprod_kg_month","outlier_purchase_qty_kg_month","outlier_quantity_any","outlier_observed_price_any","outlier_hedonic_price_any","outlier_village_price_any","outlier_spend_any","n_before","n_after"
"zhushi","主食",18,15,17,50,0,0,29,17,3423,3373
"nailei","奶类",15,0,8,23,0,0,28,9,3485,3462
"shuiguo","水果",18,14,17,48,0,0,18,14,3420,3372
"youzhi","油脂",16,2,0,18,0,0,28,5,3438,3420
"roulei","肉类和水产品及加工品",16,18,17,48,0,0,29,15,3435,3387
"shucai","蔬菜",18,18,13,44,0,0,20,14,3437,3393
"danlei","蛋类",18,18,11,47,0,0,19,11,3436,3389
"doulei","豆类",18,8,16,42,0,0,20,13,3436,3394
````

## Table CSV: `outputs/tables/paper1_outlier_thresholds_price_spend.csv`

- Size: 2.7 KB
- Lines: 33

````csv
"food_category","food_category_label","variable","threshold_quantile","n_nonmissing","n_positive","threshold"
"danlei","蛋类","price_preferred_household_recalc_w99_yuan_per_kg",0.995,2236,2236,86.6133333333336
"doulei","豆类","price_preferred_household_recalc_w99_yuan_per_kg",0.995,2494,2494,48
"nailei","奶类","price_preferred_household_recalc_w99_yuan_per_kg",0.995,1632,1632,638.8
"roulei","肉类和水产品及加工品","price_preferred_household_recalc_w99_yuan_per_kg",0.995,2842,2842,148.7075
"shucai","蔬菜","price_preferred_household_recalc_w99_yuan_per_kg",0.995,2699,2699,64
"shuiguo","水果","price_preferred_household_recalc_w99_yuan_per_kg",0.995,2767,2767,40
"youzhi","油脂","price_preferred_household_recalc_w99_yuan_per_kg",0.995,2144,2144,118.799999999999
"zhushi","主食","price_preferred_household_recalc_w99_yuan_per_kg",0.995,3266,3266,32.0851612903226
"danlei","蛋类","price_hedonic_imputed_w99_yuan_per_kg",0.995,3436,3436,80
"doulei","豆类","price_hedonic_imputed_w99_yuan_per_kg",0.995,3436,3436,43.33247311828
"nailei","奶类","price_hedonic_imputed_w99_yuan_per_kg",0.995,3485,3485,400
"roulei","肉类和水产品及加工品","price_hedonic_imputed_w99_yuan_per_kg",0.995,3435,3435,143.753333333333
"shucai","蔬菜","price_hedonic_imputed_w99_yuan_per_kg",0.995,3437,3437,60
"shuiguo","水果","price_hedonic_imputed_w99_yuan_per_kg",0.995,3420,3420,36
"youzhi","油脂","price_hedonic_imputed_w99_yuan_per_kg",0.995,3438,3438,90.7200000000004
"zhushi","主食","price_hedonic_imputed_w99_yuan_per_kg",0.995,3423,3423,31.8836363636364
"danlei","蛋类","village_price_category_median_yuan_per_kg",0.99,2896,2896,4000
"doulei","豆类","village_price_category_median_yuan_per_kg",0.99,2872,2872,4000
"nailei","奶类","village_price_category_median_yuan_per_kg",0.99,2941,2941,480
"roulei","肉类和水产品及加工品","village_price_category_median_yuan_per_kg",0.99,3216,3216,5200
"shucai","蔬菜","village_price_category_median_yuan_per_kg",0.99,2909,2909,8000
"shuiguo","水果","village_price_category_median_yuan_per_kg",0.99,2273,2273,204
"youzhi","油脂","village_price_category_median_yuan_per_kg",0.99,2759,2759,617.330000000001
"zhushi","主食","village_price_category_median_yuan_per_kg",0.99,3025,3025,2000
"danlei","蛋类","spend_sum_yuan",0.995,2236,2236,200
"doulei","豆类","spend_sum_yuan",0.995,2494,2494,126.721
"nailei","奶类","spend_sum_yuan",0.995,1633,1633,1771.79999999999
"roulei","肉类和水产品及加工品","spend_sum_yuan",0.995,2843,2843,1844.74
"shucai","蔬菜","spend_sum_yuan",0.995,2699,2699,276.039999999999
"shuiguo","水果","spend_sum_yuan",0.995,2767,2767,384.250000000002
"youzhi","油脂","spend_sum_yuan",0.995,2145,2145,1200
"zhushi","主食","spend_sum_yuan",0.995,3266,3266,867.562500000005
````

## Table CSV: `outputs/tables/paper1_outlier_thresholds_quantity_kg_month.csv`

- Size: 1.7 KB
- Lines: 25

````csv
"food_category","food_category_label","variable","threshold_quantile","n_nonmissing","n_positive","threshold"
"danlei","蛋类","cons_kg_month",0.995,3436,3436,16.6505524861878
"doulei","豆类","cons_kg_month",0.995,3436,3422,15.397375
"nailei","奶类","cons_kg_month",0.995,3485,3095,25.7142857142857
"roulei","肉类和水产品及加工品","cons_kg_month",0.995,3435,3435,42.8571428571428
"shucai","蔬菜","cons_kg_month",0.995,3437,3436,114.983571428571
"shuiguo","水果","cons_kg_month",0.995,3420,3420,85.9071132142855
"youzhi","油脂","cons_kg_month",0.995,3438,3422,28.5714285714286
"zhushi","主食","cons_kg_month",0.995,3423,3423,169.057749803502
"danlei","蛋类","selfprod_kg_month",0.995,3436,1518,8.42269854965483
"doulei","豆类","selfprod_kg_month",0.995,3436,775,6.42857142857145
"nailei","奶类","selfprod_kg_month",0.995,3485,4,NA
"roulei","肉类和水产品及加工品","selfprod_kg_month",0.995,3435,1174,20.6094746162928
"shucai","蔬菜","selfprod_kg_month",0.995,3437,3217,102.471428571429
"shuiguo","水果","selfprod_kg_month",0.995,3420,1014,30
"youzhi","油脂","selfprod_kg_month",0.995,3438,1320,10.7142857142857
"zhushi","主食","selfprod_kg_month",0.995,3423,2870,75
"danlei","蛋类","purchase_qty_kg_month",0.995,2512,2512,12
"doulei","豆类","purchase_qty_kg_month",0.995,3068,3068,14.0665
"nailei","奶类","purchase_qty_kg_month",0.995,2081,2081,20
"roulei","肉类和水产品及加工品","purchase_qty_kg_month",0.995,3276,3276,60.4375
"shucai","蔬菜","purchase_qty_kg_month",0.995,3029,3029,37
"shuiguo","水果","purchase_qty_kg_month",0.995,3204,3204,61.99475
"youzhi","油脂","purchase_qty_kg_month",0.995,2464,2464,50
"zhushi","主食","purchase_qty_kg_month",0.995,3359,3359,172.235
````

## Table CSV: `outputs/tables/paper1_top_extreme_values_after_kg_outlier_cleaning.csv`

- Size: 7.9 KB
- Lines: 61

````csv
"variable","rank","value","nhCode","data_year","provn","countyn","townn_std","viln_std","food_category","food_category_label"
"cons_kg_month",1,167.524079321231,"62052210821405",2023,"甘肃省","秦安县","安伏镇","陈河村","zhushi","主食"
"cons_kg_month",2,165.133893160663,"42038110020901",2024,"湖北省","丹江口市","土关垭镇","姚河村","zhushi","主食"
"cons_kg_month",3,165.071428571428,"22082210720202",2023,"吉林省","白城市通榆县","乌兰花镇","双龙村","zhushi","主食"
"cons_kg_month",4,158.988128571428,"42282820021001",2024,"湖北省","鹤峰县","铁炉乡","千户村","zhushi","主食"
"cons_kg_month",5,156.9415,"35018100320104",2024,"福建省","福清市","龙头街道","东刘村","zhushi","主食"
"cons_kg_month",6,156.779224095163,"62052210820103",2023,"甘肃省","秦安","安伏镇","安伏村","zhushi","主食"
"cons_kg_month",7,156.737568266743,"22082220520909",2023,"吉林省","白城市通榆县","什花道镇","春峰村","zhushi","主食"
"cons_kg_month",8,156.387342815915,"22082210220203",2023,"吉林省","通榆县","双岗镇","双岗村","zhushi","主食"
"cons_kg_month",9,153.246566744731,"35098200220702",2024,"福建省","福鼎市","桐城街道","董江村","zhushi","主食"
"cons_kg_month",10,152.771428571428,"35042610920101",2024,"福建省","尤溪县","联合镇","联东村","zhushi","主食"
"selfprod_kg_month",1,100.714285714285,"22082210720208",2023,"吉林省","白城市通榆县","乌兰花镇","双龙村","shucai","蔬菜"
"selfprod_kg_month",2,100.714285714285,"42038110220210",2024,"湖北省","丹江口市","丁家营镇","花园村","shucai","蔬菜"
"selfprod_kg_month",3,100.714285714285,"51018310621705",2024,"四川省","邛崃市","火井镇","常乐村","shucai","蔬菜"
"selfprod_kg_month",4,99.642857142857,"51018311520409",2024,"四川省","邛崃市","临济镇","瑞林村","shucai","蔬菜"
"selfprod_kg_month",5,99.002367797948,"62052211320402",2023,"甘肃省","秦安","刘坪镇","任吴村","shucai","蔬菜"
"selfprod_kg_month",6,98.8912579957355,"35062910520405",2024,"福建省","华安县","仙都镇","市后村","shucai","蔬菜"
"selfprod_kg_month",7,97.6962209302325,"51343710720709",2024,"四川省","凉山彝族自治州","雷波县马颈子镇","西苏角村","shucai","蔬菜"
"selfprod_kg_month",8,96.4696673189825,"62102210100104",2023,"甘肃省","庆阳市环县","曲子镇","双城村","shucai","蔬菜"
"selfprod_kg_month",9,96.4285714285715,"22022117131109",2023,"吉林省","永吉县","万昌镇","吴家村","shucai","蔬菜"
"selfprod_kg_month",10,96.4285714285715,"42100210220303",2024,"湖北省","沙市区","观音垱镇","皇屯村","shucai","蔬菜"
"purchase_qty_kg_month",1,171.5,"61083110920907",2023,"陕西省","子洲县","砖庙镇","暖泉沟村","zhushi","主食"
"purchase_qty_kg_month",2,171,"53252910220506",2024,"云南省","红河县","甲寅镇","他撒村","zhushi","主食"
"purchase_qty_kg_month",3,170,"22082220520106",2023,"吉林省","通榆县","什花道乡","光辉村","zhushi","主食"
"purchase_qty_kg_month",4,169.5,"51343710721305",2024,"四川省","雷波县","马颈子镇","马鞍村","zhushi","主食"
"purchase_qty_kg_month",5,168.79,"37078300421407",2023,"山东省","寿光市","古城街道","苗家桥村","zhushi","主食"
"purchase_qty_kg_month",6,168.3,"61083100122208",2023,"陕西省","子洲县","双湖峪街道","曹硷村","zhushi","主食"
"purchase_qty_kg_month",7,167.81,"61052310320708",2023,"陕西省","大荔县","安仁镇","黄都村","zhushi","主食"
"purchase_qty_kg_month",8,167.55,"22082210220405",2023,"吉林省","白城市通榆县","双岗镇","长青村","zhushi","主食"
"purchase_qty_kg_month",9,167.5,"61102610120607",2023,"陕西省","柞水县","营盘镇","龙潭村","zhushi","主食"
"purchase_qty_kg_month",10,167.19,"61052311421210",2023,"陕西省","大荔县","赵渡镇","严通村","zhushi","主食"
"price_hedonic_imputed_w99_yuan_per_kg",1,400,"22022110020904",2023,"吉林省","吉林市永吉县","口前镇","春登村","nailei","奶类"
"price_hedonic_imputed_w99_yuan_per_kg",2,400,"22022117131105",2023,"吉林省","永吉县","万昌镇","吴家村","nailei","奶类"
"price_hedonic_imputed_w99_yuan_per_kg",3,400,"22042110920310",2023,"吉林省","辽源市东丰县","沙河镇","盈仓村","nailei","奶类"
"price_hedonic_imputed_w99_yuan_per_kg",4,400,"35018110321103",2024,"福建省","福清市","海口镇","前村村","nailei","奶类"
"price_hedonic_imputed_w99_yuan_per_kg",5,400,"35018110321203",2024,"福建省","福清市","海口镇","城里村","nailei","奶类"
"price_hedonic_imputed_w99_yuan_per_kg",6,400,"35062910020208",2024,"福建省","漳州市福安县","华丰镇","绵良村","nailei","奶类"
"price_hedonic_imputed_w99_yuan_per_kg",7,400,"35062910521205",2024,"福建省","漳州市华安县","仙都镇","岭埔村","nailei","奶类"
"price_hedonic_imputed_w99_yuan_per_kg",8,400,"35062910521207",2024,"福建省","漳州市华安县","仙都镇","岭埔村","nailei","奶类"
"price_hedonic_imputed_w99_yuan_per_kg",9,400,"35072420020308",2024,"福建省","松溪县","河东乡","长江村","nailei","奶类"
"price_hedonic_imputed_w99_yuan_per_kg",10,400,"35072420020309",2024,"福建省","松溪县","河东乡","长江村","nailei","奶类"
"village_price_category_median_yuan_per_kg",1,8000,"42282810122901",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"village_price_category_median_yuan_per_kg",2,8000,"42282810122902",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"village_price_category_median_yuan_per_kg",3,8000,"42282810122903",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"village_price_category_median_yuan_per_kg",4,8000,"42282810122904",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"village_price_category_median_yuan_per_kg",5,8000,"42282810122905",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"village_price_category_median_yuan_per_kg",6,8000,"42282810122906",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"village_price_category_median_yuan_per_kg",7,8000,"42282810122907",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"village_price_category_median_yuan_per_kg",8,8000,"42282810122908",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"village_price_category_median_yuan_per_kg",9,8000,"42282810122909",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"village_price_category_median_yuan_per_kg",10,8000,"42282810122910",2024,"湖北省","鹤峰县","容美镇","杨柳坪村","shucai","蔬菜"
"total_sown_area",1,317.965920000001,"22042111020504",2023,"吉林省","辽源市东丰县","南屯基镇","团林村","zhushi","主食"
"total_sown_area",2,317.965920000001,"22042111020504",2023,"吉林省","辽源市东丰县","南屯基镇","团林村","doulei","豆类"
"total_sown_area",3,317.965920000001,"22042111020504",2023,"吉林省","辽源市东丰县","南屯基镇","团林村","roulei","肉类和水产品及加工品"
"total_sown_area",4,317.965920000001,"22042111020504",2023,"吉林省","辽源市东丰县","南屯基镇","团林村","danlei","蛋类"
"total_sown_area",5,317.965920000001,"22042111020504",2023,"吉林省","辽源市东丰县","南屯基镇","团林村","nailei","奶类"
"total_sown_area",6,317.965920000001,"22042111020504",2023,"吉林省","辽源市东丰县","南屯基镇","团林村","youzhi","油脂"
"total_sown_area",7,317.965920000001,"22042111020504",2023,"吉林省","辽源市东丰县","南屯基镇","团林村","shucai","蔬菜"
"total_sown_area",8,317.965920000001,"22042111020504",2023,"吉林省","辽源市东丰县","南屯基镇","团林村","shuiguo","水果"
"total_sown_area",9,317.965920000001,"22052110620104",2023,"吉林省","通化市通化县","兴林镇","兴林村","zhushi","主食"
"total_sown_area",10,317.965920000001,"22052110620104",2023,"吉林省","通化市通化县","兴林镇","兴林村","doulei","豆类"
````

## Table CSV: `outputs/tables/table1_category_participation_revised.csv`

- Size: 0.9 KB
- Lines: 9

````csv
"food_category","food_category_label","participation_rate","mean_cons_monthly_jin","mean_selfprod_monthly_total","mean_self_suff_rate"
"zhushi","主食",0.834983498349835,24.1118178983184,7.3434433305156,0.329961210871232
"nailei","奶类",0.00130208333333333,2.92829785051959,0.000247920640116459,0.00125558035714286
"shuiguo","水果",0.289880952380952,12.1501382113788,0.908546895730005,0.0816117329756171
"youzhi","油脂",0.374326750448833,2.80385018824736,0.513528258148052,0.267439441350403
"roulei","肉类和水产品及加工品",0.334715639810427,6.07757366756046,0.954126112319942,0.129072992503298
"shucai","蔬菜",0.933577087141987,21.0996473469639,13.1432534196113,0.534569009772548
"danlei","蛋类",0.436607142857143,1.98551156058016,0.515638588982067,0.288806955018255
"doulei","豆类",0.22209026128266,1.99720228096339,0.153061696425834,0.097302139641331
````

## Table CSV: `outputs/tables/table1_descriptive_statistics_revised.csv`

- Size: 2.8 KB
- Lines: 24

````csv
"module","variable","n","missing","mean","sd","min","p25","median","p75","max"
"revised_analysis","production_participation",27190,0,0.430194924604634,0.495112378280322,0,0,0,1,1
"revised_analysis","log_selfprod_amount",27190,0,0.508096763164872,0.972167041102068,0,0,0,0.519875459285908,4.62216776235666
"revised_analysis","ihs_selfprod_amount",27190,0,0.626033240969081,1.18043091801,0,0,0,0.637707836941499,5.30545948005332
"revised_analysis","self_suff_rate",26493,697,0.217413157529161,0.341705807153218,0,0,0,0.363636363636364,1
"revised_analysis","household_size_reconstructed",27190,0,2.86980507539537,1.39540380826094,0,2,2,4,8
"revised_analysis","child_share",27046,144,0.081536130683879,0.165929568910003,0,0,0,0,1
"revised_analysis","elderly_share",27046,144,0.213905233763993,0.343476014870995,0,0,0,0.333333333333333,1
"revised_analysis","female_share",27046,144,0.507568058651398,0.20836760002384,0,0.5,0.5,0.5,1
"revised_analysis","dependency_ratio",23452,3738,0.448386065154358,0.771954753292965,0,0,0,0.666666666666667,7
"revised_analysis","num_children",27190,0,0.336042662743656,0.717948674631121,0,0,0,0,5
"revised_analysis","num_elderly",27190,0,0.551930856932696,0.824301126129043,0,0,0,1,4
"revised_analysis","num_adult_male",27190,0,0.498823096726738,0.627547581824339,0,0,0,1,4
"revised_analysis","num_adult_female",27190,0,0.559286502390585,0.650921034061171,0,0,0,1,4
"revised_analysis","log1p_total_income_w_w99",27190,0,9.82948859493003,1.81461139417871,0,9.17274234156086,10.1362249355217,10.8836634638684,12.6731912420684
"revised_analysis","log1p_agri_business_income_w99",27190,0,3.05838604965117,4.38660499271088,0,0,0,7.75061473277041,12.4756457865728
"revised_analysis","log1p_annual_expense_total_w99",27190,0,9.86057530101605,0.762057291379809,7.9787683215572,9.33087517360492,9.84760479528845,10.3551044266654,11.846999342111
"revised_analysis","total_sown_area",27190,0,22.9793949235013,52.1957701063426,0,1,5.2,16,317.965920000001
"revised_analysis","agricultural_labor_days",27190,0,287.714490621552,252.407989665396,0,60,240,420,2190
"revised_analysis","offfarm_labor_days",27190,0,193.973593232806,250.086520542014,0,0,100,300,2155
"revised_analysis","market_friction_survey",26501,689,0.0242710254266609,0.577841569321816,-1.62167266191737,-0.35742998166833,0.0280966341103436,0.403517859017731,2.70979685096585
"revised_analysis","poi_market_friction_lag1",27112,78,-0.00230477813968816,1.00109253835852,-2.22723385733065,-0.854095487345426,-0.0184682202980518,0.830045272265226,1.50247630579959
"revised_analysis","combined_market_friction",27190,0,-0.00352596805119916,0.80862787075695,-1.83183417788482,-0.594306907509282,-0.0481387841928706,0.60827184606102,3.07756722306563
"revised_analysis","price_hedonic_imputed_w99_yuan_per_jin",27190,0,21.8617369196707,25.2458230007276,0.618092514718252,9.09090909090908,16.7559523809524,27.7977220016612,400
````

## Table CSV: `outputs/tables/table1_missingness_revised.csv`

- Size: 1.3 KB
- Lines: 22

````csv
"module","variable","n_rows","n_missing","missing_share"
"outcome","production_participation",27190,0,0
"outcome","log_selfprod_amount",27190,0,0
"outcome","ihs_selfprod_amount",27190,0,0
"outcome","self_suff_rate",27190,697,0.0256344244207429
"household_composition","household_size_reconstructed",27190,0,0
"household_composition","child_share",27190,144,0.00529606472968003
"household_composition","elderly_share",27190,144,0.00529606472968003
"household_composition","female_share",27190,144,0.00529606472968003
"market","market_friction_survey",27190,689,0.0253401986024274
"market","poi_market_friction_lag1",27190,78,0.00286870172857668
"market","combined_market_friction",27190,0,0
"price","price_hedonic_imputed_w99_yuan_per_jin",27190,0,0
"price","price_preferred_household_recalc_w99_yuan_per_jin",27190,7377,0.271312982714233
"price","village_price_category_median",27190,4752,0.174770136079441
"gaez","gaez_overall_si_10km",27190,78,0.00286870172857668
"gaez","gaez_staple_si_10km",27190,78,0.00286870172857668
"gaez","gaez_soil_terrain_constraint_10km",27190,78,0.00286870172857668
"text","risk_salience_z_5yr_sum",27190,8,0.000294225818315557
"text","governance_capacity_z_5yr_sum",27190,8,0.000294225818315557
"text","trust_signal_z_5yr_sum",27190,8,0.000294225818315557
"text","attention_z_5yr_sum",27190,8,0.000294225818315557
````

## Table CSV: `outputs/tables/table1_observations_by_category_revised.csv`

- Size: 0.2 KB
- Lines: 9

````csv
"food_category","n_rows","food_category_label"
"danlei",3389,"蛋类"
"doulei",3394,"豆类"
"nailei",3462,"奶类"
"roulei",3387,"肉类和水产品及加工品"
"shucai",3393,"蔬菜"
"shuiguo",3372,"水果"
"youzhi",3420,"油脂"
"zhushi",3373,"主食"
````

## Table CSV: `outputs/tables/table1_observations_by_year_revised.csv`

- Size: 0 KB
- Lines: 3

````csv
"data_year","n_rows"
"2023",13496
"2024",13694
````

## Table CSV: `outputs/tables/table1_sample_summary_revised.csv`

- Size: 0.2 KB
- Lines: 8

````csv
"item","value"
"rows",27190
"households",3565
"food_categories",8
"villages_clusters",361
"provinces",9
"counties",44
"duplicate_household_category_keys",0
````

## Table CSV: `outputs/tables/table2_common_sample_baseline_coefficients_raw.csv`

- Size: 7.7 KB
- Lines: 49

````csv
"outcome","spec","term","estimate","std_error_cluster","t_stat","p_value","direction","n","n_clusters","r_squared"
"production_participation","M0","household_size_reconstructed",-0.00356051008464596,0.00359781494920957,-0.989631244216216,0.322354392632454,"negative",26271,350,0.349507566058353
"production_participation","M0","child_share",-0.0480508258458052,0.0265508283532586,-1.80976748470855,0.0703318522473727,"negative",26271,350,0.349507566058353
"production_participation","M0","elderly_share",-0.00602660743293308,0.0123588884560286,-0.487633451371863,0.625809496962654,"negative",26271,350,0.349507566058353
"production_participation","M0","female_share",-0.00354594407565257,0.017953699969477,-0.19750491997087,0.843432431691248,"negative",26271,350,0.349507566058353
"production_participation","M1","household_size_reconstructed",-0.00626143995876518,0.00362209002296439,-1.72868148474142,0.0838661168920706,"negative",26271,350,0.364889476792063
"production_participation","M1","child_share",0.0423580015415294,0.0264416396119581,1.60194307777999,0.10916819741715,"positive",26271,350,0.364889476792063
"production_participation","M1","elderly_share",0.0301600346824936,0.0144987471512457,2.08018212662618,0.037508830987511,"positive",26271,350,0.364889476792063
"production_participation","M1","female_share",-0.00556426596709315,0.0186874387975947,-0.297754337946478,0.765890667602357,"negative",26271,350,0.364889476792063
"production_participation","M2","household_size_reconstructed",-0.00749500105617936,0.00314080860805316,-2.38632848781739,0.0170175431082165,"negative",26271,350,0.386680431035333
"production_participation","M2","child_share",0.037750281777694,0.023103622393565,1.63395510602738,0.102268277530041,"positive",26271,350,0.386680431035333
"production_participation","M2","elderly_share",0.0401218771136562,0.0133219001718852,3.01172329742645,0.00259769267519318,"positive",26271,350,0.386680431035333
"production_participation","M2","female_share",0.00782089856397889,0.0166259170209879,0.470404041720292,0.638066377110316,"positive",26271,350,0.386680431035333
"production_participation","M3","household_size_reconstructed",-0.00745271338359985,0.00314763847850775,-2.36771580805337,0.0178982782604796,"negative",26271,350,0.391872358879774
"production_participation","M3","child_share",0.0436331307470773,0.0220965970845026,1.97465386096393,0.0483074422710068,"positive",26271,350,0.391872358879774
"production_participation","M3","elderly_share",0.0405704139049397,0.0132110492263951,3.07094563116772,0.00213382001871375,"positive",26271,350,0.391872358879774
"production_participation","M3","female_share",0.0103987585691723,0.0164178915468625,0.633379660201222,0.526485744182708,"positive",26271,350,0.391872358879774
"log_selfprod_amount","M0","household_size_reconstructed",0.019625516256678,0.00723714078721535,2.71177759749364,0.00669234782069416,"positive",26271,350,0.365517398556356
"log_selfprod_amount","M0","child_share",-0.202977766469561,0.055440231611899,-3.66119982850137,0.00025103686023896,"negative",26271,350,0.365517398556356
"log_selfprod_amount","M0","elderly_share",-0.0152871742935356,0.0250683403247468,-0.609819959977346,0.541981077911695,"negative",26271,350,0.365517398556356
"log_selfprod_amount","M0","female_share",-0.0767531971085344,0.0363571980528618,-2.11108669587075,0.0347648607531261,"negative",26271,350,0.365517398556356
"log_selfprod_amount","M1","household_size_reconstructed",0.00972242809395763,0.00836282571625569,1.16257691166027,0.245001202831709,"positive",26271,350,0.370733232686332
"log_selfprod_amount","M1","child_share",-0.109445354478875,0.0556129393248065,-1.96798363488147,0.0490699207078029,"negative",26271,350,0.370733232686332
"log_selfprod_amount","M1","elderly_share",0.0253401052024991,0.0326715467629747,0.775601638524686,0.43798423262755,"positive",26271,350,0.370733232686332
"log_selfprod_amount","M1","female_share",-0.0240146161787312,0.0405740172851934,-0.591871788537311,0.553936446461111,"negative",26271,350,0.370733232686332
"log_selfprod_amount","M2","household_size_reconstructed",0.0045346231618855,0.00727808689509643,0.623051528134499,0.533250661106001,"positive",26271,350,0.410679420654463
"log_selfprod_amount","M2","child_share",-0.0655213497737676,0.0503441677339484,-1.30146852600733,0.193098131016328,"negative",26271,350,0.410679420654463
"log_selfprod_amount","M2","elderly_share",0.0406510489030707,0.028698401022264,1.41649177149396,0.156631571648773,"positive",26271,350,0.410679420654463
"log_selfprod_amount","M2","female_share",0.0180464374246508,0.0379917230381691,0.475009712155464,0.634780050816395,"positive",26271,350,0.410679420654463
"log_selfprod_amount","M3","household_size_reconstructed",0.00669240545304056,0.00692058295725893,0.967029149765623,0.333529461735619,"positive",26271,350,0.421796748396454
"log_selfprod_amount","M3","child_share",-0.0390084959019482,0.0483700462904163,-0.806459759573915,0.419977801608879,"negative",26271,350,0.421796748396454
"log_selfprod_amount","M3","elderly_share",0.0425605630789573,0.0269119596514347,1.58147394802178,0.113769711092498,"positive",26271,350,0.421796748396454
"log_selfprod_amount","M3","female_share",0.0225706124489076,0.0361996923013381,0.623502881212979,0.532954109481118,"positive",26271,350,0.421796748396454
"ihs_selfprod_amount","M0","household_size_reconstructed",0.0234852579804989,0.00882937045243716,2.65990175709711,0.00781634470943817,"positive",26271,350,0.368302125857523
"ihs_selfprod_amount","M0","child_share",-0.248218446711397,0.0676798997426585,-3.6675356738885,0.000244899391149266,"negative",26271,350,0.368302125857523
"ihs_selfprod_amount","M0","elderly_share",-0.0206322712504252,0.0306578901681731,-0.672984055238224,0.500957434896326,"negative",26271,350,0.368302125857523
"ihs_selfprod_amount","M0","female_share",-0.0942471721586088,0.0446731720717954,-2.10970405251595,0.0348838552235752,"negative",26271,350,0.368302125857523
"ihs_selfprod_amount","M1","household_size_reconstructed",0.0117526262900738,0.0102149562289834,1.1505312432693,0.249925133594747,"positive",26271,350,0.373636337265191
"ihs_selfprod_amount","M1","child_share",-0.13540462710512,0.0679924595424755,-1.99146534801454,0.0464297511620927,"negative",26271,350,0.373636337265191
"ihs_selfprod_amount","M1","elderly_share",0.0296456989064991,0.040128993686681,0.738760087979446,0.460052691436559,"positive",26271,350,0.373636337265191
"ihs_selfprod_amount","M1","female_share",-0.0305140858433775,0.0496959766541683,-0.614015216075206,0.539205272321742,"negative",26271,350,0.373636337265191
"ihs_selfprod_amount","M2","household_size_reconstructed",0.00514042007400585,0.00889053766208233,0.578190011604075,0.56313584160593,"positive",26271,350,0.413815453933876
"ihs_selfprod_amount","M2","child_share",-0.0803088710802217,0.0614796928094034,-1.30626662903459,0.191461901325434,"negative",26271,350,0.413815453933876
"ihs_selfprod_amount","M2","elderly_share",0.0488966840840022,0.0352390211037957,1.38757214452633,0.165267368509482,"positive",26271,350,0.413815453933876
"ihs_selfprod_amount","M2","female_share",0.0215006039559176,0.0464878606568315,0.462499320298536,0.643723289641639,"positive",26271,350,0.413815453933876
"ihs_selfprod_amount","M3","household_size_reconstructed",0.00783101170978188,0.00845288032858502,0.926431157826738,0.354221958037869,"positive",26271,350,0.42524354764847
"ihs_selfprod_amount","M3","child_share",-0.0473888666179329,0.059021016174349,-0.802915125655333,0.422023792898719,"negative",26271,350,0.42524354764847
"ihs_selfprod_amount","M3","elderly_share",0.0512896784411281,0.0330286568191597,1.5528841733393,0.120450808485702,"positive",26271,350,0.42524354764847
"ihs_selfprod_amount","M3","female_share",0.0269329740150778,0.0442179198239819,0.609096360079573,0.542460570108927,"positive",26271,350,0.42524354764847
````

## Table CSV: `outputs/tables/table2_common_sample_baseline.csv`

- Size: 1.6 KB
- Lines: 13

````csv
"outcome","conceptual_outcome","spec","common_m3_sample","n","n_clusters","r_squared","hhcomp_wald_chisq","hhcomp_wald_df","hhcomp_wald_p"
"production_participation","self_provisioning_participation","M0",TRUE,26271,350,0.349507566058353,6.63066387145665,4,0.156741443458961
"production_participation","self_provisioning_participation","M1",TRUE,26271,350,0.364889476792063,7.14014491875843,4,0.128664968153154
"production_participation","self_provisioning_participation","M2",TRUE,26271,350,0.386680431035333,13.7585700539984,4,0.00810683407667245
"production_participation","self_provisioning_participation","M3",TRUE,26271,350,0.391872358879774,15.0200890085389,4,0.00465973205206816
"log_selfprod_amount","log_selfprod_amount","M0",TRUE,26271,350,0.365517398556356,19.8341706315847,4,0.000538482104753046
"log_selfprod_amount","log_selfprod_amount","M1",TRUE,26271,350,0.370733232686332,5.1632195347439,4,0.270956384913444
"log_selfprod_amount","log_selfprod_amount","M2",TRUE,26271,350,0.410679420654463,4.3069920071452,4,0.366050373055893
"log_selfprod_amount","log_selfprod_amount","M3",TRUE,26271,350,0.421796748396454,4.34582986913326,4,0.361221393051786
"ihs_selfprod_amount","ihs_selfprod_amount","M0",TRUE,26271,350,0.368302125857523,19.7052535743733,4,0.000570943880314645
"ihs_selfprod_amount","ihs_selfprod_amount","M1",TRUE,26271,350,0.373636337265191,5.22541661981507,4,0.264940344220016
"ihs_selfprod_amount","ihs_selfprod_amount","M2",TRUE,26271,350,0.413815453933876,4.21816776523135,4,0.37728448600195
"ihs_selfprod_amount","ihs_selfprod_amount","M3",TRUE,26271,350,0.42524354764847,4.16930404078851,4,0.383577663351849
````

## Table CSV: `outputs/tables/table3_baseline_coefficients_margins.csv`

- Size: 13.5 KB
- Lines: 49

````csv
"outcome","conceptual_outcome","spec","term","estimate","std_error_cluster","t_stat","p_value","direction","marginal_effect_interpretation","sign_stable_across_M0_M3","stable_direction","n","n_clusters","r_squared"
"production_participation","self_provisioning_participation","M0","household_size_reconstructed",-0.00356051008464596,0.00359781494920957,-0.989631244216216,0.322354392632454,"negative","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",TRUE,"negative",26271,350,0.349507566058353
"production_participation","self_provisioning_participation","M1","household_size_reconstructed",-0.00626143995876518,0.00362209002296439,-1.72868148474142,0.0838661168920706,"negative","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",TRUE,"negative",26271,350,0.364889476792063
"production_participation","self_provisioning_participation","M2","household_size_reconstructed",-0.00749500105617936,0.00314080860805316,-2.38632848781739,0.0170175431082165,"negative","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",TRUE,"negative",26271,350,0.386680431035333
"production_participation","self_provisioning_participation","M3","household_size_reconstructed",-0.00745271338359985,0.00314763847850775,-2.36771580805337,0.0178982782604796,"negative","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",TRUE,"negative",26271,350,0.391872358879774
"production_participation","self_provisioning_participation","M0","child_share",-0.0480508258458052,0.0265508283532586,-1.80976748470855,0.0703318522473727,"negative","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.349507566058353
"production_participation","self_provisioning_participation","M1","child_share",0.0423580015415294,0.0264416396119581,1.60194307777999,0.10916819741715,"positive","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.364889476792063
"production_participation","self_provisioning_participation","M2","child_share",0.037750281777694,0.023103622393565,1.63395510602738,0.102268277530041,"positive","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.386680431035333
"production_participation","self_provisioning_participation","M3","child_share",0.0436331307470773,0.0220965970845026,1.97465386096393,0.0483074422710068,"positive","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.391872358879774
"production_participation","self_provisioning_participation","M0","elderly_share",-0.00602660743293308,0.0123588884560286,-0.487633451371863,0.625809496962654,"negative","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.349507566058353
"production_participation","self_provisioning_participation","M1","elderly_share",0.0301600346824936,0.0144987471512457,2.08018212662618,0.037508830987511,"positive","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.364889476792063
"production_participation","self_provisioning_participation","M2","elderly_share",0.0401218771136562,0.0133219001718852,3.01172329742645,0.00259769267519318,"positive","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.386680431035333
"production_participation","self_provisioning_participation","M3","elderly_share",0.0405704139049397,0.0132110492263951,3.07094563116772,0.00213382001871375,"positive","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.391872358879774
"production_participation","self_provisioning_participation","M0","female_share",-0.00354594407565257,0.017953699969477,-0.19750491997087,0.843432431691248,"negative","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.349507566058353
"production_participation","self_provisioning_participation","M1","female_share",-0.00556426596709315,0.0186874387975947,-0.297754337946478,0.765890667602357,"negative","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.364889476792063
"production_participation","self_provisioning_participation","M2","female_share",0.00782089856397889,0.0166259170209879,0.470404041720292,0.638066377110316,"positive","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.386680431035333
"production_participation","self_provisioning_participation","M3","female_share",0.0103987585691723,0.0164178915468625,0.633379660201222,0.526485744182708,"positive","LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",FALSE,"not_stable",26271,350,0.391872358879774
"log_selfprod_amount","log_selfprod_amount","M0","household_size_reconstructed",0.019625516256678,0.00723714078721535,2.71177759749364,0.00669234782069416,"positive","OLS coefficient for transformed self-production amount.",TRUE,"positive",26271,350,0.365517398556356
"log_selfprod_amount","log_selfprod_amount","M1","household_size_reconstructed",0.00972242809395763,0.00836282571625569,1.16257691166027,0.245001202831709,"positive","OLS coefficient for transformed self-production amount.",TRUE,"positive",26271,350,0.370733232686332
"log_selfprod_amount","log_selfprod_amount","M2","household_size_reconstructed",0.0045346231618855,0.00727808689509643,0.623051528134499,0.533250661106001,"positive","OLS coefficient for transformed self-production amount.",TRUE,"positive",26271,350,0.410679420654463
"log_selfprod_amount","log_selfprod_amount","M3","household_size_reconstructed",0.00669240545304056,0.00692058295725893,0.967029149765623,0.333529461735619,"positive","OLS coefficient for transformed self-production amount.",TRUE,"positive",26271,350,0.421796748396454
"log_selfprod_amount","log_selfprod_amount","M0","child_share",-0.202977766469561,0.055440231611899,-3.66119982850137,0.00025103686023896,"negative","OLS coefficient for transformed self-production amount.",TRUE,"negative",26271,350,0.365517398556356
"log_selfprod_amount","log_selfprod_amount","M1","child_share",-0.109445354478875,0.0556129393248065,-1.96798363488147,0.0490699207078029,"negative","OLS coefficient for transformed self-production amount.",TRUE,"negative",26271,350,0.370733232686332
"log_selfprod_amount","log_selfprod_amount","M2","child_share",-0.0655213497737676,0.0503441677339484,-1.30146852600733,0.193098131016328,"negative","OLS coefficient for transformed self-production amount.",TRUE,"negative",26271,350,0.410679420654463
"log_selfprod_amount","log_selfprod_amount","M3","child_share",-0.0390084959019482,0.0483700462904163,-0.806459759573915,0.419977801608879,"negative","OLS coefficient for transformed self-production amount.",TRUE,"negative",26271,350,0.421796748396454
"log_selfprod_amount","log_selfprod_amount","M0","elderly_share",-0.0152871742935356,0.0250683403247468,-0.609819959977346,0.541981077911695,"negative","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.365517398556356
"log_selfprod_amount","log_selfprod_amount","M1","elderly_share",0.0253401052024991,0.0326715467629747,0.775601638524686,0.43798423262755,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.370733232686332
"log_selfprod_amount","log_selfprod_amount","M2","elderly_share",0.0406510489030707,0.028698401022264,1.41649177149396,0.156631571648773,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.410679420654463
"log_selfprod_amount","log_selfprod_amount","M3","elderly_share",0.0425605630789573,0.0269119596514347,1.58147394802178,0.113769711092498,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.421796748396454
"log_selfprod_amount","log_selfprod_amount","M0","female_share",-0.0767531971085344,0.0363571980528618,-2.11108669587075,0.0347648607531261,"negative","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.365517398556356
"log_selfprod_amount","log_selfprod_amount","M1","female_share",-0.0240146161787312,0.0405740172851934,-0.591871788537311,0.553936446461111,"negative","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.370733232686332
"log_selfprod_amount","log_selfprod_amount","M2","female_share",0.0180464374246508,0.0379917230381691,0.475009712155464,0.634780050816395,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.410679420654463
"log_selfprod_amount","log_selfprod_amount","M3","female_share",0.0225706124489076,0.0361996923013381,0.623502881212979,0.532954109481118,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.421796748396454
"ihs_selfprod_amount","ihs_selfprod_amount","M0","household_size_reconstructed",0.0234852579804989,0.00882937045243716,2.65990175709711,0.00781634470943817,"positive","OLS coefficient for transformed self-production amount.",TRUE,"positive",26271,350,0.368302125857523
"ihs_selfprod_amount","ihs_selfprod_amount","M1","household_size_reconstructed",0.0117526262900738,0.0102149562289834,1.1505312432693,0.249925133594747,"positive","OLS coefficient for transformed self-production amount.",TRUE,"positive",26271,350,0.373636337265191
"ihs_selfprod_amount","ihs_selfprod_amount","M2","household_size_reconstructed",0.00514042007400585,0.00889053766208233,0.578190011604075,0.56313584160593,"positive","OLS coefficient for transformed self-production amount.",TRUE,"positive",26271,350,0.413815453933876
"ihs_selfprod_amount","ihs_selfprod_amount","M3","household_size_reconstructed",0.00783101170978188,0.00845288032858502,0.926431157826738,0.354221958037869,"positive","OLS coefficient for transformed self-production amount.",TRUE,"positive",26271,350,0.42524354764847
"ihs_selfprod_amount","ihs_selfprod_amount","M0","child_share",-0.248218446711397,0.0676798997426585,-3.6675356738885,0.000244899391149266,"negative","OLS coefficient for transformed self-production amount.",TRUE,"negative",26271,350,0.368302125857523
"ihs_selfprod_amount","ihs_selfprod_amount","M1","child_share",-0.13540462710512,0.0679924595424755,-1.99146534801454,0.0464297511620927,"negative","OLS coefficient for transformed self-production amount.",TRUE,"negative",26271,350,0.373636337265191
"ihs_selfprod_amount","ihs_selfprod_amount","M2","child_share",-0.0803088710802217,0.0614796928094034,-1.30626662903459,0.191461901325434,"negative","OLS coefficient for transformed self-production amount.",TRUE,"negative",26271,350,0.413815453933876
"ihs_selfprod_amount","ihs_selfprod_amount","M3","child_share",-0.0473888666179329,0.059021016174349,-0.802915125655333,0.422023792898719,"negative","OLS coefficient for transformed self-production amount.",TRUE,"negative",26271,350,0.42524354764847
"ihs_selfprod_amount","ihs_selfprod_amount","M0","elderly_share",-0.0206322712504252,0.0306578901681731,-0.672984055238224,0.500957434896326,"negative","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.368302125857523
"ihs_selfprod_amount","ihs_selfprod_amount","M1","elderly_share",0.0296456989064991,0.040128993686681,0.738760087979446,0.460052691436559,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.373636337265191
"ihs_selfprod_amount","ihs_selfprod_amount","M2","elderly_share",0.0488966840840022,0.0352390211037957,1.38757214452633,0.165267368509482,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.413815453933876
"ihs_selfprod_amount","ihs_selfprod_amount","M3","elderly_share",0.0512896784411281,0.0330286568191597,1.5528841733393,0.120450808485702,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.42524354764847
"ihs_selfprod_amount","ihs_selfprod_amount","M0","female_share",-0.0942471721586088,0.0446731720717954,-2.10970405251595,0.0348838552235752,"negative","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.368302125857523
"ihs_selfprod_amount","ihs_selfprod_amount","M1","female_share",-0.0305140858433775,0.0496959766541683,-0.614015216075206,0.539205272321742,"negative","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.373636337265191
"ihs_selfprod_amount","ihs_selfprod_amount","M2","female_share",0.0215006039559176,0.0464878606568315,0.462499320298536,0.643723289641639,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.413815453933876
"ihs_selfprod_amount","ihs_selfprod_amount","M3","female_share",0.0269329740150778,0.0442179198239819,0.609096360079573,0.542460570108927,"positive","OLS coefficient for transformed self-production amount.",FALSE,"not_stable",26271,350,0.42524354764847
````

## Table CSV: `outputs/tables/table4_category_specific_nsi.csv`

- Size: 4.6 KB
- Lines: 9

````csv
"food_category","food_category_label","outcome","conceptual_outcome","n","n_clusters","outcome_mean","r_squared","hhcomp_wald_chisq","hhcomp_wald_df","hhcomp_wald_p","household_size_reconstructed_coef","household_size_reconstructed_se","household_size_reconstructed_t","household_size_reconstructed_p","child_share_coef","child_share_se","child_share_t","child_share_p","elderly_share_coef","elderly_share_se","elderly_share_t","elderly_share_p","female_share_coef","female_share_se","female_share_t","female_share_p","main_coefficient_drivers","nsi","signal_label"
"zhushi","主食","production_participation","self_provisioning_participation",3261,350,0.836553204538485,0.236747902546114,2.81346505218962,4,0.589510647754488,-0.00828303542781982,0.00632255112973803,-1.31007804568961,0.190169434588946,0.0126563265822689,0.0457762162990484,0.276482584309443,0.782177434234558,0.00496890361769232,0.0265678205937417,0.187027144366625,0.85163935031748,0.025020139365708,0.0340517314081047,0.734768492851229,0.462480498644879,"none_p_lt_0.10",0.279216848565244,"Weak"
"doulei","豆类","production_participation","self_provisioning_participation",3279,350,0.22842329978652,0.120691921508641,9.03996075402772,4,0.0601083764695258,0.00683889376942999,0.00666004534305335,1.02685393524583,0.304489247946934,0.0568040989493146,0.0515445355579974,1.10203920424114,0.270444628093246,0.0500469789066594,0.0303116914332742,1.65107839715342,0.0987225678177883,0.0430019952252783,0.0389871818081978,1.10297777964131,0.27003681483803,"elderly_share",0.897153263350006,"Weak"
"roulei","肉类和水产品及加工品","production_participation","self_provisioning_participation",3270,350,0.340672782874618,0.317008744503539,4.45634677079505,4,0.347755050999264,-0.00161122225431782,0.00788744825791043,-0.204276744725634,0.838137241822688,0.0712858924029955,0.0501132687747437,1.42249536192543,0.154882497003156,0.0502710038681481,0.0291205330854675,1.72630781588389,0.0842920499990425,0.00929486560922475,0.0423187121639927,0.219639614107477,0.826151837066642,"elderly_share",0.442261438608208,"Weak"
"danlei","蛋类","production_participation","self_provisioning_participation",3274,350,0.436469150885767,0.274912883662847,17.0423151454831,4,0.0018966973586938,-0.00035732986491693,0.00806239360748147,-0.0443205680984549,0.96464887681064,0.014962416122934,0.053908907952871,0.277549976267645,0.781357836933287,0.131737776548813,0.033333166830848,3.95215303776348,7.74511801603978e-05,0.0403137429483363,0.0416332308861545,0.968306857053051,0.332891141221931,"elderly_share",1.6913313081583,"Strong"
"nailei","奶类","production_participation","self_provisioning_participation",3343,350,0.00119653006281783,0.0184064598093432,4.02225316435176,4,0.403002588633597,-0.000949173646681377,0.000496204032543381,-1.91286967543617,0.0557647385643444,0.00197896358069306,0.00152802444084294,1.29511251770381,0.195281417312155,-0.00145717149744315,0.00230171008666492,-0.633082118328174,0.526680018842594,0.00908427331181149,0.00496018258246522,1.83143929901399,0.0670350000877157,"household_size_reconstructed;female_share",0.399180665780024,"Weak"
"youzhi","油脂","production_participation","self_provisioning_participation",3308,350,0.391475211608223,0.199686543615812,16.1133890994157,4,0.00287072595210536,-0.0200587405661454,0.00784912847189169,-2.55553729792769,0.0106023997741448,0.180787075225689,0.0570638460075611,3.16815440728853,0.00153410019418664,0.0115392320436607,0.0338404766476355,0.340989051774097,0.733111823774201,-0.0845089065630953,0.0434410937199508,-1.94536783783332,0.0517307227681812,"household_size_reconstructed;child_share;female_share",1.59914185553608,"Strong"
"shucai","蔬菜","production_participation","self_provisioning_participation",3275,350,0.935572519083969,0.189606274704927,14.7385085615441,4,0.00527545949934982,-0.0100556688636303,0.00459827700333773,-2.18683408075051,0.0287546385411125,0.0285233533150584,0.0333530206174076,0.855195505146285,0.392442924169732,0.0511895018111236,0.0172726234835074,2.96362054438351,0.00304042951316218,-0.01654253311293,0.0193745554501226,-0.853827751326567,0.393200435648358,"household_size_reconstructed;elderly_share",1.46269451966481,"Strong"
"shuiguo","水果","production_participation","self_provisioning_participation",3261,350,0.295921496473474,0.149195056714175,12.3839414365772,4,0.0147132696875033,-0.0199033146727388,0.00712886674968128,-2.79193248683301,0.00523942868557597,-0.0300006561394873,0.0532473229019782,-0.563420929061821,0.573148288974944,0.0300415934174717,0.0329808256802917,0.910880573721464,0.362358302337178,0.0476955430800503,0.0415653848118844,1.14748229316075,0.251182347139136,"household_size_reconstructed",1.22902010033733,"Moderate"
````

## Table CSV: `outputs/tables/table5_two_part_model.csv`

- Size: 1.7 KB
- Lines: 3

````csv
"model_part","model_name","sample_definition","outcome","conceptual_outcome","n","n_clusters","outcome_mean","r_squared","hhcomp_wald_chisq","hhcomp_wald_df","hhcomp_wald_p","household_size_reconstructed_coef","household_size_reconstructed_se","household_size_reconstructed_t","household_size_reconstructed_p","child_share_coef","child_share_se","child_share_t","child_share_p","elderly_share_coef","elderly_share_se","elderly_share_t","elderly_share_p","female_share_coef","female_share_se","female_share_t","female_share_p","interpretation"
"Part 1","entry_all_observations","all observations","production_participation","self_provisioning_participation",26271,350,0.431959194549123,0.391872358879774,15.0200890085389,4,0.00465973205206816,-0.00745271338359985,0.00314763847850775,-2.36771580805337,0.0178982782604796,0.0436331307470773,0.0220965970845026,1.97465386096393,0.0483074422710068,0.0405704139049397,0.0132110492263951,3.07094563116772,0.00213382001871375,0.0103987585691723,0.0164178915468625,0.633379660201222,0.526485744182708,"Non-separability appears mainly on the entry margin rather than the conditional intensity margin."
"Part 2","conditional_intensity_positive_entry","production_participation == 1","log_selfprod_amount","log_selfprod_amount",11348,349,1.17303798531203,0.39272209013682,7.626875462203,4,0.106243016833968,0.0379507222748443,0.0145442562957193,2.60932711190011,0.009072047513673,-0.164436266504283,0.100871997250387,-1.63014782086761,0.103070258853464,0.0149621293009928,0.0553297388587978,0.270417493550374,0.786839083354946,0.0158725947266022,0.0724580650322407,0.21905904773388,0.826604051149692,"Non-separability appears mainly on the entry margin rather than the conditional intensity margin."
````

## Table CSV: `outputs/tables/table6_alternative_composition_outcomes.csv`

- Size: 2.4 KB
- Lines: 13

````csv
"composition_spec","outcome","conceptual_outcome","tested_terms","n","n_clusters","r_squared","wald_chisq","wald_df","wald_p"
"proportion","production_participation","self_provisioning_participation","household_size_reconstructed + child_share + elderly_share + female_share",26271,350,0.391872358879774,15.0200890085389,4,0.00465973205206816
"proportion","log_selfprod_amount","log_selfprod_amount","household_size_reconstructed + child_share + elderly_share + female_share",26271,350,0.421796748396454,4.34582986913326,4,0.361221393051786
"proportion","ihs_selfprod_amount","ihs_selfprod_amount","household_size_reconstructed + child_share + elderly_share + female_share",26271,350,0.42524354764847,4.16930404078851,4,0.383577663351849
"proportion","self_suff_rate","self_suff_rate","household_size_reconstructed + child_share + elderly_share + female_share",25602,350,0.270382435676842,10.5333830931844,4,0.0323402402742133
"dependency","production_participation","self_provisioning_participation","household_size_reconstructed + dependency_ratio + female_share",22799,350,0.393029213407017,23.0301327265296,3,3.98031896685636e-05
"dependency","log_selfprod_amount","log_selfprod_amount","household_size_reconstructed + dependency_ratio + female_share",22799,350,0.424434882467683,5.82827188479289,3,0.120270731606621
"dependency","ihs_selfprod_amount","ihs_selfprod_amount","household_size_reconstructed + dependency_ratio + female_share",22799,350,0.427956493327979,5.59190098016017,3,0.13324408825628
"dependency","self_suff_rate","self_suff_rate","household_size_reconstructed + dependency_ratio + female_share",22211,350,0.26793755205571,10.064959990396,3,0.0180219462702789
"counts","production_participation","self_provisioning_participation","num_children + num_elderly + num_adult_male + num_adult_female",26415,350,0.391954022688329,17.9995099818555,4,0.00123437019919626
"counts","log_selfprod_amount","log_selfprod_amount","num_children + num_elderly + num_adult_male + num_adult_female",26415,350,0.421433279979049,7.43003404815936,4,0.114834364520294
"counts","ihs_selfprod_amount","ihs_selfprod_amount","num_children + num_elderly + num_adult_male + num_adult_female",26415,350,0.424896498535595,7.36391228596718,4,0.117862081244392
"counts","self_suff_rate","self_suff_rate","num_children + num_elderly + num_adult_male + num_adult_female",25742,350,0.270587297548335,14.3278498081576,4,0.00631896495236306
````

## Table CSV: `outputs/tables/table7_leave_one_province.csv`

- Size: 1.2 KB
- Lines: 9

````csv
"dropped_province","outcome","conceptual_outcome","n","n_clusters","r_squared","wald_chisq","wald_df","wald_p"
"云南省","production_participation","self_provisioning_participation",22789,305,0.399652229211202,12.7734681050906,4,0.0124373858212705
"吉林省","production_participation","self_provisioning_participation",23317,310,0.380273015019623,18.2797926389082,4,0.00108799519572811
"四川省","production_participation","self_provisioning_participation",22918,306,0.39176833609078,13.9870098725986,4,0.00733663045865052
"山东省","production_participation","self_provisioning_participation",22909,305,0.393694583565862,13.5637982514223,4,0.00882559978869657
"湖北省","production_participation","self_provisioning_participation",22938,305,0.390753355692019,12.7369625463087,4,0.0126351880251375
"甘肃省","production_participation","self_provisioning_participation",23076,306,0.381056115504227,13.0956999696077,4,0.0108175308682446
"福建省","production_participation","self_provisioning_participation",23195,308,0.410825616013495,9.50512739951379,4,0.0496419973134724
"陕西省","production_participation","self_provisioning_participation",22755,305,0.404878339193866,14.7007179389352,4,0.00536395103971932
````

## Table CSV: `outputs/tables/table8_household_composition_permutation_draws.csv`

- Size: 4.9 KB
- Lines: 100

````csv
"draw","wald_chisq","wald_df","wald_p","n","n_clusters"
1,2.58062404772966,4,0.630259297703368,26279,350
2,1.69316264601146,4,0.791959260731186,26274,350
3,3.96136086166244,4,0.411260344308933,26281,350
4,2.54621081727504,4,0.636380584948792,26283,350
5,8.23623331626438,4,0.0832980510402221,26315,350
6,6.14131062299523,4,0.188840730528229,26284,350
7,10.1257023485559,4,0.0383626482712881,26279,350
8,5.43411542450871,4,0.24558177426255,26294,350
9,5.76653202147825,4,0.21727543255638,26295,350
10,1.07204308554809,4,0.898682135292694,26277,350
11,4.70368616047528,4,0.319073845470105,26301,350
12,1.24998624371148,4,0.869802122341937,26283,350
13,10.606600916909,4,0.031359843311997,26290,350
14,3.20543243852557,4,0.52405396158566,26283,350
15,10.4217553439881,4,0.033892028017001,26301,350
16,6.93773048744083,4,0.139215703104137,26286,350
17,5.51777589705907,4,0.238171376944379,26281,350
18,1.47504979206518,4,0.831051702356504,26285,350
19,4.07003189198291,4,0.396611023823153,26285,350
20,2.4100363412317,4,0.660814297003074,26272,350
21,8.34862918086653,4,0.0796106257000356,26307,350
22,3.73710218760714,4,0.442752641208748,26277,350
23,4.14087139788581,4,0.38727655609568,26281,350
24,6.21153240551891,4,0.183898036178831,26283,350
25,3.02212354605805,4,0.554129928258997,26285,350
26,5.16587518540355,4,0.270697160431661,26275,350
27,0.983917374194002,4,0.912224756889754,26277,350
28,3.69760117341697,4,0.448474915964426,26280,350
29,4.91725976133396,4,0.29589300539372,26295,350
30,13.4801833542747,4,0.00915295825843387,26277,350
31,10.38007385735,4,0.0344896542704319,26290,350
32,3.14316162530824,4,0.534159924570075,26294,350
33,2.37905166076928,4,0.666416235250638,26306,350
34,3.64833147915689,4,0.455685348885887,26296,350
35,3.80596374556107,4,0.432902204536291,26287,350
36,0.645157312290063,4,0.957915894351946,26275,350
37,7.85228834401104,4,0.0971414024096262,26295,350
38,0.691782225176589,4,0.952338460466428,26286,350
39,2.84467975024859,4,0.584145074627399,26283,350
40,2.55406815898001,4,0.634980921335054,26297,350
41,1.64823304105081,4,0.800098247846471,26286,350
42,0.870907104396005,4,0.92869705744235,26277,350
43,1.10977860491301,4,0.892717633951013,26287,350
44,2.76511521950806,4,0.597869322522836,26291,350
45,4.16985783369109,4,0.383505889408709,26288,350
46,1.14503353651418,4,0.887062891762108,26283,350
47,2.62664805085448,4,0.622109869250544,26299,350
48,2.67445433009171,4,0.613692119574022,26298,350
49,7.82170881721481,4,0.0983319314387974,26281,350
50,2.10046186805508,4,0.71728753298463,26279,350
51,1.6777911411323,4,0.794747827669743,26279,350
52,1.95449288991492,4,0.744128716908955,26316,350
53,5.50229985563838,4,0.239527394308674,26305,350
54,1.27719696925502,4,0.865232354070049,26291,350
55,6.28088966717599,4,0.179130336040821,26280,350
56,7.17899082210836,4,0.126726339410087,26278,350
57,5.71378873571892,4,0.221566595869361,26280,350
58,6.03569598894703,4,0.196498288047375,26293,350
59,1.01542353272375,4,0.907448329721779,26278,350
60,7.34106733260924,4,0.118925227260064,26290,350
61,0.0941066517365064,4,0.998927112740052,26283,350
62,4.02801122512443,4,0.402228215902033,26289,350
63,5.19444669211144,4,0.267921543100652,26287,350
64,2.13431409860694,4,0.711071144109278,26273,350
65,4.17761964857799,4,0.382501012863684,26301,350
66,2.87127354326367,4,0.579593350350015,26277,350
67,5.5218435760798,4,0.237816073548654,26285,350
68,2.03351457714088,4,0.729594506495885,26278,350
69,3.2937371950768,4,0.509925155701934,26293,350
70,1.67256417309724,4,0.795695133798247,26285,350
71,1.67164658356103,4,0.795861382793813,26287,350
72,1.45977265250915,4,0.833742541707139,26296,350
73,3.13431779218748,4,0.535604589348313,26288,350
74,1.82360312723208,4,0.768161302114516,26282,350
75,3.62964571524446,4,0.458441068772728,26280,350
76,0.800235774072774,4,0.938416452838022,26295,350
77,2.58824338239972,4,0.628907163925858,26282,350
78,3.29384757515698,4,0.509907645586613,26301,350
79,1.03140984715765,4,0.904996414885523,26289,350
80,3.42713991723109,4,0.489042998081137,26286,350
81,2.72870659730786,4,0.60420075480833,26291,350
82,1.76030070738672,4,0.779736992953447,26283,350
83,2.68813528485353,4,0.611292376225509,26286,350
84,2.68699321588446,4,0.611492543940274,26278,350
85,8.7263682448981,4,0.0683149758261683,26284,350
86,13.6073243213964,4,0.00865975342735337,26291,350
87,3.8810621449123,4,0.422341576009187,26277,350
88,6.31700007681939,4,0.176692278875194,26274,350
89,6.35714071644429,4,0.174017190311889,26279,350
90,3.48867822865443,4,0.479601931673379,26283,350
91,6.0863726927312,4,0.192790096339805,26293,350
92,3.88020603700213,4,0.42246089298217,26291,350
93,3.53513786539999,4,0.472555707523081,26288,350
94,4.59320636574854,4,0.331638226618415,26275,350
95,8.52572837187192,4,0.0741111870794203,26283,350
96,4.14407358430259,4,0.386858610471918,26283,350
97,2.0833136584411,4,0.720438532251135,26285,350
98,2.76237891866746,4,0.598344069361731,26273,350
99,1.46145128299195,4,0.833447242631351,26294,350
````

## Table CSV: `outputs/tables/table8_household_composition_permutation.csv`

- Size: 0.4 KB
- Lines: 2

````csv
"placebo_type","outcome","n_draws","true_wald_chisq","true_wald_df","true_wald_p","placebo_mean","placebo_p50","placebo_p90","placebo_p95","placebo_max","randomization_p_value","n","n_clusters"
"household_composition_permutation","production_participation",99,15.0200890085389,4,0.00465973205206816,4.07989638217803,3.42713991723109,7.92907733846171,10.1511394994353,13.6073243213964,0.01,26271,350
````

## Table CSV: `outputs/tables/tableA_market_friction_interactions_appendix.csv`

- Size: 1.7 KB
- Lines: 10

````csv
"friction_spec","friction_variable","outcome","n","n_clusters","r_squared","interaction_wald_chisq","interaction_wald_df","interaction_wald_p","evidence_label"
"survey_market_friction","market_friction_survey","production_participation",26271,350,0.391914845706467,0.826371761848548,4,0.934878003893171,"weak_or_no_amplification_evidence"
"survey_market_friction","market_friction_survey","log_selfprod_amount",26271,350,0.421996559894764,4.4512219411718,4,0.348370541923293,"weak_or_no_amplification_evidence"
"survey_market_friction","market_friction_survey","ihs_selfprod_amount",26271,350,0.425458625520134,4.73459097982119,4,0.315629698416514,"weak_or_no_amplification_evidence"
"poi_market_friction","poi_market_friction_lag1","production_participation",26271,350,0.39201868250617,2.0216597334547,4,0.731774874482501,"weak_or_no_amplification_evidence"
"poi_market_friction","poi_market_friction_lag1","log_selfprod_amount",26271,350,0.421996539655277,3.70932358282001,4,0.446771313954896,"weak_or_no_amplification_evidence"
"poi_market_friction","poi_market_friction_lag1","ihs_selfprod_amount",26271,350,0.425436709980477,3.54856769476627,4,0.470532048469824,"weak_or_no_amplification_evidence"
"combined_market_friction","combined_market_friction","production_participation",26960,360,0.394007995873762,0.595988731850842,4,0.963508385274311,"weak_or_no_amplification_evidence"
"combined_market_friction","combined_market_friction","log_selfprod_amount",26960,360,0.425185388150278,4.01356489817356,4,0.404173153182382,"weak_or_no_amplification_evidence"
"combined_market_friction","combined_market_friction","ihs_selfprod_amount",26960,360,0.428803555191878,3.94508923662911,4,0.413488217915617,"weak_or_no_amplification_evidence"
````

## Table CSV: `outputs/tables/tableA_market_friction_permutation_appendix.csv`

- Size: 0.2 KB
- Lines: 2

````csv
"placebo_type","outcome","n_draws","true_interaction_wald","placebo_mean","placebo_p95","randomization_p_value"
"market_friction_village_permutation","production_participation",99,0.826371761848548,4.6676191118728,9.79858849984731,0.95
````

## Table CSV: `outputs/tables/tableB_iv_diagnostics_appendix.csv`

- Size: 0.9 KB
- Lines: 6

````csv
"iv_spec","iv_variable","n_households_for_correlation","correlation_with_market_friction_survey","min_first_stage_F","median_first_stage_F","weak_iv_flag","appendix_only","interpretation"
"terrain_town_2km","iv_terrain_barrier_town_gee_2km",3475,0.128671825459449,1.14245362816427,2.08028056351296,TRUE,TRUE,"weak_first_stage_appendix_only"
"terrain_town_1km","iv_terrain_barrier_town_gee_1km",3475,0.133310083293457,0.981121240698883,2.02543657528539,TRUE,TRUE,"weak_first_stage_appendix_only"
"terrain_town_5km","iv_terrain_barrier_town_gee_5km",3475,0.115333253354737,1.44872385747282,2.14413706539563,TRUE,TRUE,"weak_first_stage_appendix_only"
"terrain_county_2km","iv_terrain_barrier_county_gee_2km",3475,0.133972334024346,2.02862334682898,2.11805726278348,TRUE,TRUE,"weak_first_stage_appendix_only"
"early_ntl_9294","iv_early_ntl_peak_dist_9294",3475,0.111676507881207,0.73619606155109,1.33309966059233,TRUE,TRUE,"weak_first_stage_appendix_only"
````

## Table CSV: `outputs/tables/tableB_iv_first_stage_detail_appendix.csv`

- Size: 2.8 KB
- Lines: 21

````csv
"iv_spec","iv_variable","endogenous_variable","first_stage_wald_chisq","first_stage_df","first_stage_F","first_stage_p","n","n_clusters"
"terrain_town_2km","iv_terrain_barrier_town_gee_2km","market_friction_survey",7.52484433023959,4,1.8812110825599,0.110618739639752,26271,350
"terrain_town_2km","iv_terrain_barrier_town_gee_2km","child_market",9.11740017786407,4,2.27935004446602,0.0582310940456569,26271,350
"terrain_town_2km","iv_terrain_barrier_town_gee_2km","elderly_market",12.0790733132279,4,3.01976832830697,0.0167728410570825,26271,350
"terrain_town_2km","iv_terrain_barrier_town_gee_2km","female_market",4.56981451265707,4,1.14245362816427,0.3343493624685,26271,350
"terrain_town_1km","iv_terrain_barrier_town_gee_1km","market_friction_survey",7.61298414096397,4,1.90324603524099,0.10682913909424,26271,350
"terrain_town_1km","iv_terrain_barrier_town_gee_1km","child_market",8.59050846131919,4,2.1476271153298,0.0721907585344059,26271,350
"terrain_town_1km","iv_terrain_barrier_town_gee_1km","elderly_market",10.8358379354088,4,2.7089594838522,0.0284722585238485,26271,350
"terrain_town_1km","iv_terrain_barrier_town_gee_1km","female_market",3.92448496279553,4,0.981121240698883,0.416322156057224,26271,350
"terrain_town_5km","iv_terrain_barrier_town_gee_5km","market_friction_survey",7.93944444934509,4,1.98486111233627,0.0938217778634336,26271,350
"terrain_town_5km","iv_terrain_barrier_town_gee_5km","child_market",9.21365207381994,4,2.30341301845498,0.0559754965112346,26271,350
"terrain_town_5km","iv_terrain_barrier_town_gee_5km","elderly_market",12.9951445730063,4,3.24878614325158,0.011299542808644,26271,350
"terrain_town_5km","iv_terrain_barrier_town_gee_5km","female_market",5.79489542989127,4,1.44872385747282,0.214998160198064,26271,350
"terrain_county_2km","iv_terrain_barrier_county_gee_2km","market_friction_survey",8.42544931035233,4,2.10636232758808,0.0771794561304359,26271,350
"terrain_county_2km","iv_terrain_barrier_county_gee_2km","child_market",8.51900879191554,4,2.12975219797889,0.0743131323710828,26271,350
"terrain_county_2km","iv_terrain_barrier_county_gee_2km","elderly_market",16.9145859810727,4,4.22864649526818,0.00200821943721374,26271,350
"terrain_county_2km","iv_terrain_barrier_county_gee_2km","female_market",8.11449338731592,4,2.02862334682898,0.0874730537543612,26271,350
"early_ntl_9294","iv_early_ntl_peak_dist_9294","market_friction_survey",3.29870077798073,4,0.824675194495182,0.50913813444404,26271,350
"early_ntl_9294","iv_early_ntl_peak_dist_9294","child_market",7.36609650675791,4,1.84152412668948,0.117760895534867,26271,350
"early_ntl_9294","iv_early_ntl_peak_dist_9294","elderly_market",10.6381159617668,4,2.65952899044169,0.0309467331634531,26271,350
"early_ntl_9294","iv_early_ntl_peak_dist_9294","female_market",2.94478424620436,4,0.73619606155109,0.567107743080913,26271,350
````

## Table CSV: `outputs/tables/tableC_price_robustness.csv`

- Size: 1.2 KB
- Lines: 5

````csv
"price_spec","model_compatibility_variable","price_variable","price_unit","outcome","conceptual_outcome","n","n_clusters","r_squared","hhcomp_wald_chisq","hhcomp_wald_df","hhcomp_wald_p","price_observed_share"
"no_price_control","none","none","none","production_participation","self_provisioning_participation",26271,350,0.391236186017817,14.925500854769,4,0.00485825384402538,0.733051653914963
"hedonic_price_main","price_hedonic_imputed_w99_yuan_per_jin","price_hedonic_imputed_w99_yuan_per_kg","yuan/kg","production_participation","self_provisioning_participation",26271,350,0.391872358879774,15.0200890085399,4,0.00465973205206593,0.733051653914963
"observed_price_only","price_preferred_household_recalc_w99_yuan_per_jin","price_preferred_household_recalc_w99_yuan_per_kg","yuan/kg","production_participation","self_provisioning_participation",19258,350,0.42870322554039,15.3611134432224,4,0.00400796736955511,1
"county_category_median_price","village_price_category_median","village_price_category_median_yuan_per_kg","yuan/kg","production_participation","self_provisioning_participation",22196,338,0.403288287256039,8.49257333051376,4,0.0751126613836567,0.742521174986484
````

## Table CSV: `outputs/tables/tableD_category_definition_audits.csv`

- Size: 0.8 KB
- Lines: 3

````csv
"audit_item","status","evidence","decision","human_review_required"
"roulei_split","partially_feasible_raw_detail_present","Variable labels include roulei meat-detail variables and shuichan/aquatic-detail variables: TRUE. Current analysis-ready long data has only aggregate `roulei` outcome.","Do not split roulei in the revised rerun without rebuilding detail-level outcomes and prices. Report as human-review flag.",TRUE
"youzhi_definition","partially_identified_human_review_required","Variable labels include youzhi consumption variables: TRUE; oilseed production module variables: TRUE. Item-level labels do not clearly map youzhi_1-youzhi_6 to oil crops versus edible oils.","Use current aggregate `youzhi` as oils category, but avoid strong substantive claims before item-code review.",TRUE
````

## Table CSV: `outputs/tables/tableE_add_one_block_diagnostics.csv`

- Size: 4.6 KB
- Lines: 31

````csv
"label","outcome","n","n_clusters","r_squared","wald_chisq","wald_df","wald_p","diagnostic_family","common_sample","spec_order"
"B0_composition_category_year","ihs_selfprod_amount",26271,350,0.368302125857523,19.7052535743733,4,0.000570943880314645,"add_one_block","M3_complete_case",1
"B1_plus_household_resources","ihs_selfprod_amount",26271,350,0.373636337265191,5.22541661981507,4,0.264940344220016,"add_one_block","M3_complete_case",2
"B1a_M1_plus_market","ihs_selfprod_amount",26271,350,0.378139633442228,5.0896589198402,4,0.278221030262182,"add_one_block","M3_complete_case",3
"B1b_M1_plus_GAEZ","ihs_selfprod_amount",26271,350,0.378863938019215,4.62243404689943,4,0.328275783396007,"add_one_block","M3_complete_case",4
"B1c_M1_plus_province_FE","ihs_selfprod_amount",26271,350,0.41232583821399,4.44202726401569,4,0.349476999417077,"add_one_block","M3_complete_case",5
"B1d_M1_plus_market_GAEZ","ihs_selfprod_amount",26271,350,0.383554832984338,4.66673143036263,4,0.323232565975588,"add_one_block","M3_complete_case",6
"B1e_M1_plus_market_province_FE","ihs_selfprod_amount",26271,350,0.413291650754246,4.2369635434247,4,0.374885174979397,"add_one_block","M3_complete_case",7
"B1f_M1_plus_GAEZ_province_FE","ihs_selfprod_amount",26271,350,0.412875093983543,4.52245540629568,4,0.339893147574255,"add_one_block","M3_complete_case",8
"B2_full_market_GAEZ_province_FE","ihs_selfprod_amount",26271,350,0.413815453933876,4.21816776523135,4,0.37728448600195,"add_one_block","M3_complete_case",9
"B3_plus_unit_value_text","ihs_selfprod_amount",26271,350,0.42524354764847,4.16930404078851,4,0.383577663351849,"add_one_block","M3_complete_case",10
"B0_composition_category_year","log_selfprod_amount",26271,350,0.365517398556356,19.8341706315847,4,0.000538482104753046,"add_one_block","M3_complete_case",1
"B1_plus_household_resources","log_selfprod_amount",26271,350,0.370733232686332,5.1632195347439,4,0.270956384913444,"add_one_block","M3_complete_case",2
"B1a_M1_plus_market","log_selfprod_amount",26271,350,0.375150621254129,5.05235661162143,4,0.281967446048879,"add_one_block","M3_complete_case",3
"B1b_M1_plus_GAEZ","log_selfprod_amount",26271,350,0.375884033195308,4.61409738238668,4,0.329232024998593,"add_one_block","M3_complete_case",4
"B1c_M1_plus_province_FE","log_selfprod_amount",26271,350,0.409276260957587,4.50895197527148,4,0.341487326533217,"add_one_block","M3_complete_case",5
"B1d_M1_plus_market_GAEZ","log_selfprod_amount",26271,350,0.380551890715997,4.69308996813832,4,0.320261791735201,"add_one_block","M3_complete_case",6
"B1e_M1_plus_market_province_FE","log_selfprod_amount",26271,350,0.410199820524906,4.31420306849189,4,0.365149958866743,"add_one_block","M3_complete_case",7
"B1f_M1_plus_GAEZ_province_FE","log_selfprod_amount",26271,350,0.40977478801243,4.59953459038248,4,0.330907848458903,"add_one_block","M3_complete_case",8
"B2_full_market_GAEZ_province_FE","log_selfprod_amount",26271,350,0.410679420654463,4.3069920071452,4,0.366050373055893,"add_one_block","M3_complete_case",9
"B3_plus_unit_value_text","log_selfprod_amount",26271,350,0.421796748396454,4.34582986913326,4,0.361221393051786,"add_one_block","M3_complete_case",10
"B0_composition_category_year","production_participation",26271,350,0.349507566058353,6.63066387145665,4,0.156741443458961,"add_one_block","M3_complete_case",1
"B1_plus_household_resources","production_participation",26271,350,0.364889476792063,7.14014491875843,4,0.128664968153154,"add_one_block","M3_complete_case",2
"B1a_M1_plus_market","production_participation",26271,350,0.369606044961669,9.00667230411401,4,0.0609329213048539,"add_one_block","M3_complete_case",3
"B1b_M1_plus_GAEZ","production_participation",26271,350,0.368406017836452,10.5381218164971,4,0.0322759037781494,"add_one_block","M3_complete_case",4
"B1c_M1_plus_province_FE","production_participation",26271,350,0.384257828456177,11.932615876865,4,0.0178594488843936,"add_one_block","M3_complete_case",5
"B1d_M1_plus_market_GAEZ","production_participation",26271,350,0.372895463635207,11.8941319468155,4,0.0181561385184945,"add_one_block","M3_complete_case",6
"B1e_M1_plus_market_province_FE","production_participation",26271,350,0.385378630579036,12.3143758962104,4,0.0151603655091683,"add_one_block","M3_complete_case",7
"B1f_M1_plus_GAEZ_province_FE","production_participation",26271,350,0.385779361166183,13.8475367243259,4,0.00779789490105787,"add_one_block","M3_complete_case",8
"B2_full_market_GAEZ_province_FE","production_participation",26271,350,0.386680431035333,13.7585700539984,4,0.00810683407667245,"add_one_block","M3_complete_case",9
"B3_plus_unit_value_text","production_participation",26271,350,0.391872358879774,15.0200890085389,4,0.00465973205206816,"add_one_block","M3_complete_case",10
````

## Table CSV: `outputs/tables/tableF_village_fe_robustness.csv`

- Size: 2.3 KB
- Lines: 12

````csv
"label","outcome","n","n_clusters","r_squared","wald_chisq","wald_df","wald_p","absorbed_controls","common_sample","food_category","food_category_label"
"village_FE_M3_like","production_participation",26271,350,0.455643163778301,4.19961059134752,4,0.379665000009871,"province_FE_market_GAEZ_text_absorbed_or_collinear_at_village_county_level","M3_complete_case",NA,NA
"village_FE_M3_like","log_selfprod_amount",26271,350,0.49474007494209,18.5738884524253,4,0.00095283511520583,"province_FE_market_GAEZ_text_absorbed_or_collinear_at_village_county_level","M3_complete_case",NA,NA
"village_FE_M3_like","ihs_selfprod_amount",26271,350,0.49888481177605,18.1759678615935,4,0.00114010042877621,"province_FE_market_GAEZ_text_absorbed_or_collinear_at_village_county_level","M3_complete_case",NA,NA
"village_FE_category_zhushi","production_participation",3261,350,0.6012359467242,0.892095789947133,4,0.925692058927537,"category_specific_village_FE","M3_complete_case","zhushi","主食"
"village_FE_category_doulei","production_participation",3279,350,0.420784692546018,7.1970348820402,4,0.125835033863709,"category_specific_village_FE","M3_complete_case","doulei","豆类"
"village_FE_category_roulei","production_participation",3270,350,0.661471115569969,3.05352058108082,4,0.548909154350132,"category_specific_village_FE","M3_complete_case","roulei","肉类和水产品及加工品"
"village_FE_category_danlei","production_participation",3274,350,0.638769467183521,10.9339485430397,4,0.0273164572844335,"category_specific_village_FE","M3_complete_case","danlei","蛋类"
"village_FE_category_nailei","production_participation",3343,350,0.11584800061577,3.69121818056721,4,0.449404478337972,"category_specific_village_FE","M3_complete_case","nailei","奶类"
"village_FE_category_youzhi","production_participation",3308,350,0.691152506237206,5.24239841478096,4,0.263317707211845,"category_specific_village_FE","M3_complete_case","youzhi","油脂"
"village_FE_category_shucai","production_participation",3275,350,0.702397157840605,8.34862912273022,4,0.0796106275669348,"category_specific_village_FE","M3_complete_case","shucai","蔬菜"
"village_FE_category_shuiguo","production_participation",3261,350,0.561509724856294,2.72474822170452,4,0.604890990427149,"category_specific_village_FE","M3_complete_case","shuiguo","水果"
````

## Table CSV: `outputs/tables/tableG_binary_response_robustness.csv`

- Size: 3.7 KB
- Lines: 19

````csv
"model_family","label","outcome","n","n_clusters","outcome_mean","converged","wald_chisq","wald_df","wald_p","low_variation_flag","recommended_use","warnings","food_category","food_category_label"
"logit","overall_M3","production_participation",26271,350,0.431959194549123,TRUE,14.5705366069513,4,0.00568008393610064,FALSE,"supporting_functional_form_check","",NA,NA
"logit","category_zhushi","production_participation",3261,350,0.836553204538485,TRUE,2.22693773137862,4,0.694100680705303,FALSE,"supporting_functional_form_check","","zhushi","主食"
"logit","category_doulei","production_participation",3279,350,0.22842329978652,TRUE,8.39076194640752,4,0.0782684247863639,FALSE,"supporting_functional_form_check","","doulei","豆类"
"logit","category_roulei","production_participation",3270,350,0.340672782874618,TRUE,5.04151019810553,4,0.283064748089565,FALSE,"supporting_functional_form_check","","roulei","肉类和水产品及加工品"
"logit","category_danlei","production_participation",3274,350,0.436469150885767,TRUE,17.634783556037,4,0.00145429171021794,FALSE,"supporting_functional_form_check","","danlei","蛋类"
"logit","category_nailei","production_participation",3343,350,0.00119653006281783,TRUE,4284.52620154113,4,0,TRUE,"do_not_interpret_low_variation_or_separation","glm.fit: fitted probabilities numerically 0 or 1 occurred","nailei","奶类"
"logit","category_youzhi","production_participation",3308,350,0.391475211608223,TRUE,15.2918393074738,4,0.00413266765004838,FALSE,"supporting_functional_form_check","","youzhi","油脂"
"logit","category_shucai","production_participation",3275,350,0.935572519083969,TRUE,19.0900565729293,4,0.000754561486462468,FALSE,"supporting_functional_form_check","glm.fit: fitted probabilities numerically 0 or 1 occurred","shucai","蔬菜"
"logit","category_shuiguo","production_participation",3261,350,0.295921496473474,TRUE,10.4149041914231,4,0.0339895697154994,FALSE,"supporting_functional_form_check","","shuiguo","水果"
"probit","overall_M3","production_participation",26271,350,0.431959194549123,TRUE,15.0860647815876,4,0.00452600165941464,FALSE,"supporting_functional_form_check","",NA,NA
"probit","category_zhushi","production_participation",3261,350,0.836553204538485,TRUE,2.30839057013264,4,0.679241836703496,FALSE,"supporting_functional_form_check","","zhushi","主食"
"probit","category_doulei","production_participation",3279,350,0.22842329978652,TRUE,8.7628212466753,4,0.0673090831817261,FALSE,"supporting_functional_form_check","","doulei","豆类"
"probit","category_roulei","production_participation",3270,350,0.340672782874618,TRUE,5.77353553499704,4,0.216711161871283,FALSE,"supporting_functional_form_check","","roulei","肉类和水产品及加工品"
"probit","category_danlei","production_participation",3274,350,0.436469150885767,TRUE,18.5316568501843,4,0.000971171314709252,FALSE,"supporting_functional_form_check","","danlei","蛋类"
"probit","category_nailei","production_participation",3343,350,0.00119653006281783,TRUE,8762.62027958606,4,0,TRUE,"do_not_interpret_low_variation_or_separation","glm.fit: fitted probabilities numerically 0 or 1 occurred","nailei","奶类"
"probit","category_youzhi","production_participation",3308,350,0.391475211608223,TRUE,14.5168296486296,4,0.0058157695377884,FALSE,"supporting_functional_form_check","","youzhi","油脂"
"probit","category_shucai","production_participation",3275,350,0.935572519083969,TRUE,20.1375720423862,4,0.000469117661147656,FALSE,"supporting_functional_form_check","glm.fit: fitted probabilities numerically 0 or 1 occurred","shucai","蔬菜"
"probit","category_shuiguo","production_participation",3261,350,0.295921496473474,TRUE,11.0133836639336,4,0.0264140114721558,FALSE,"supporting_functional_form_check","","shuiguo","水果"
````

## Table CSV: `outputs/tables/tableH_category_multiple_testing.csv`

- Size: 1.7 KB
- Lines: 9

````csv
"food_category","food_category_label","outcome_mean","hhcomp_wald_chisq","hhcomp_wald_df","hhcomp_wald_p","nsi","main_coefficient_drivers","p_bonferroni","p_holm","p_bh_fdr","significant_raw_5pct","significant_bh_fdr_5pct","significant_bonferroni_5pct"
"zhushi","主食",0.836553204538485,2.81346505218962,4,0.589510647754488,0.279216848565244,"none_p_lt_0.10",1,1,0.589510647754488,FALSE,FALSE,FALSE
"doulei","豆类",0.22842329978652,9.03996075402772,4,0.0601083764695258,0.897153263350006,"elderly_share",0.480867011756206,0.240433505878103,0.0961734023512413,FALSE,FALSE,FALSE
"roulei","肉类和水产品及加工品",0.340672782874618,4.45634677079505,4,0.347755050999264,0.442261438608208,"elderly_share",1,1,0.460574387009825,FALSE,FALSE,FALSE
"danlei","蛋类",0.436469150885767,17.0423151454831,4,0.0018966973586938,1.6913313081583,"elderly_share",0.0151735788695504,0.0151735788695504,0.0114829038084214,TRUE,TRUE,TRUE
"nailei","奶类",0.00119653006281783,4.02225316435176,4,0.403002588633597,0.399180665780024,"household_size_reconstructed;female_share",1,1,0.460574387009825,FALSE,FALSE,FALSE
"youzhi","油脂",0.391475211608223,16.1133890994157,4,0.00287072595210536,1.59914185553608,"household_size_reconstructed;child_share;female_share",0.0229658076168429,0.0200950816647375,0.0114829038084214,TRUE,TRUE,TRUE
"shucai","蔬菜",0.935572519083969,14.7385085615441,4,0.00527545949934982,1.46269451966481,"household_size_reconstructed;elderly_share",0.0422036759947986,0.0316527569960989,0.0140678919982662,TRUE,TRUE,TRUE
"shuiguo","水果",0.295921496473474,12.3839414365772,4,0.0147132696875033,1.22902010033733,"household_size_reconstructed",0.117706157500026,0.0735663484375165,0.0294265393750066,TRUE,TRUE,FALSE
````

## Table CSV: `outputs/tables/tableI_category_variation_and_nsi_reframed.csv`

- Size: 3.3 KB
- Lines: 9

````csv
"food_category","food_category_label","outcome_mean","hhcomp_wald_chisq","hhcomp_wald_df","hhcomp_wald_p","nsi","main_coefficient_drivers","p_bonferroni","p_holm","p_bh_fdr","significant_raw_5pct","significant_bh_fdr_5pct","significant_bonferroni_5pct","participation_rate","mean_self_suff_rate","mean_cons_monthly_jin","mean_selfprod_monthly_total","nsi_rank_detectability","self_suff_rank_economic_importance","variation_flag","main_text_status","nsi_interpretation"
"danlei","蛋类",0.436469150885767,17.0423151454831,4,0.0018966973586938,1.6913313081583,"elderly_share",0.0151735788695504,0.0151735788695504,0.0114829038084214,TRUE,TRUE,TRUE,0.436607142857143,0.288806955018255,1.98551156058016,0.515638588982067,1,3,"middle_range_variation","main_comparable_category","detectability_ranking_not_economic_magnitude"
"youzhi","油脂",0.391475211608223,16.1133890994157,4,0.00287072595210536,1.59914185553608,"household_size_reconstructed;child_share;female_share",0.0229658076168429,0.0200950816647375,0.0114829038084214,TRUE,TRUE,TRUE,0.374326750448833,0.267439441350403,2.80385018824736,0.513528258148052,2,4,"middle_range_variation","definition_pending_human_review","detectability_ranking_not_economic_magnitude"
"shucai","蔬菜",0.935572519083969,14.7385085615441,4,0.00527545949934982,1.46269451966481,"household_size_reconstructed;elderly_share",0.0422036759947986,0.0316527569960989,0.0140678919982662,TRUE,TRUE,TRUE,0.933577087141987,0.534569009772548,21.0996473469639,13.1432534196113,3,1,"high_participation_ceiling_caution","interpret_with_variation_caution","detectability_ranking_not_economic_magnitude"
"shuiguo","水果",0.295921496473474,12.3839414365772,4,0.0147132696875033,1.22902010033733,"household_size_reconstructed",0.117706157500026,0.0735663484375165,0.0294265393750066,TRUE,TRUE,FALSE,0.289880952380952,0.0816117329756171,12.1501382113788,0.908546895730005,4,7,"middle_range_variation","main_comparable_category","detectability_ranking_not_economic_magnitude"
"doulei","豆类",0.22842329978652,9.03996075402772,4,0.0601083764695258,0.897153263350006,"elderly_share",0.480867011756206,0.240433505878103,0.0961734023512413,FALSE,FALSE,FALSE,0.22209026128266,0.097302139641331,1.99720228096339,0.153061696425834,5,6,"middle_range_variation","main_comparable_category","detectability_ranking_not_economic_magnitude"
"roulei","肉类和水产品及加工品",0.340672782874618,4.45634677079505,4,0.347755050999264,0.442261438608208,"elderly_share",1,1,0.460574387009825,FALSE,FALSE,FALSE,0.334715639810427,0.129072992503298,6.07757366756046,0.954126112319942,6,5,"middle_range_variation","aggregate_meat_aquatic_limitations","detectability_ranking_not_economic_magnitude"
"nailei","奶类",0.00119653006281783,4.02225316435176,4,0.403002588633597,0.399180665780024,"household_size_reconstructed;female_share",1,1,0.460574387009825,FALSE,FALSE,FALSE,0.00130208333333333,0.00125558035714286,2.92829785051959,0.000247920640116459,7,8,"near_zero_variation_exclude_main","exclude_from_main_category_interpretation","detectability_ranking_not_economic_magnitude"
"zhushi","主食",0.836553204538485,2.81346505218962,4,0.589510647754488,0.279216848565244,"none_p_lt_0.10",1,1,0.589510647754488,FALSE,FALSE,FALSE,0.834983498349835,0.329961210871232,24.1118178983184,7.3434433305156,8,2,"high_participation_ceiling_caution","interpret_with_variation_caution","detectability_ranking_not_economic_magnitude"
````

## Table CSV: `outputs/tables/tableJ_fixed_common_sample_price_robustness.csv`

- Size: 0.6 KB
- Lines: 5

````csv
"label","outcome","n","n_clusters","r_squared","wald_chisq","wald_df","wald_p","fixed_common_sample"
"no_unit_value","production_participation",16481,338,0.438476670481332,9.24629701384925,4,0.0552295707390422,TRUE
"hedonic_unit_value","production_participation",16481,338,0.440045842275196,9.76398597618161,4,0.0445966140920849,TRUE
"observed_household_unit_value","production_participation",16481,338,0.439594246694776,9.83741619670062,4,0.0432572729131762,TRUE
"village_median_unit_value","production_participation",16481,338,0.438575920191339,9.26980072847508,4,0.0546983957305943,TRUE
````

## Table CSV: `outputs/tables/tableJ_fixed_common_sample_robustness.csv`

- Size: 2.2 KB
- Lines: 13

````csv
"composition_spec","outcome","fixed_common_sample","tested_terms","n","n_clusters","r_squared","wald_chisq","wald_df","wald_p"
"proportion","production_participation",TRUE,"household_size_reconstructed + child_share + elderly_share + female_share",22211,350,0.385447964379955,20.7261615518192,4,0.000358812279587117
"proportion","log_selfprod_amount",TRUE,"household_size_reconstructed + child_share + elderly_share + female_share",22211,350,0.417515661893586,9.48560450251539,4,0.0500438847765532
"proportion","ihs_selfprod_amount",TRUE,"household_size_reconstructed + child_share + elderly_share + female_share",22211,350,0.420880315238174,9.321854991125,4,0.0535392768182326
"proportion","self_suff_rate",TRUE,"household_size_reconstructed + child_share + elderly_share + female_share",22211,350,0.268137445040714,12.7693678736877,4,0.0124594510974622
"dependency","production_participation",TRUE,"household_size_reconstructed + dependency_ratio + female_share",22211,350,0.385411224036594,21.3808688404356,3,8.77412635005292e-05
"dependency","log_selfprod_amount",TRUE,"household_size_reconstructed + dependency_ratio + female_share",22211,350,0.417201272838493,5.44527887477483,3,0.141948427595466
"dependency","ihs_selfprod_amount",TRUE,"household_size_reconstructed + dependency_ratio + female_share",22211,350,0.42055891959158,5.17763934285145,3,0.159242172811171
"dependency","self_suff_rate",TRUE,"household_size_reconstructed + dependency_ratio + female_share",22211,350,0.26793755205571,10.064959990396,3,0.0180219462702789
"counts","production_participation",TRUE,"num_children + num_elderly + num_adult_male + num_adult_female",22211,350,0.385201671279634,14.3356124477815,4,0.00629747910879708
"counts","log_selfprod_amount",TRUE,"num_children + num_elderly + num_adult_male + num_adult_female",22211,350,0.417516744648619,10.2378807892963,4,0.0366056949393475
"counts","ihs_selfprod_amount",TRUE,"num_children + num_elderly + num_adult_male + num_adult_female",22211,350,0.420883605262016,10.132004052042,4,0.0382618377565496
"counts","self_suff_rate",TRUE,"num_children + num_elderly + num_adult_male + num_adult_female",22211,350,0.268132502299423,10.4115243851312,4,0.0340377884606521
````

## Table CSV: `outputs/tables/tableK_fixed_factors_bad_controls_robustness.csv`

- Size: 1.2 KB
- Lines: 10

````csv
"label","outcome","n","n_clusters","r_squared","wald_chisq","wald_df","wald_p","fixed_common_sample_across_bad_control_specs"
"full_M3_resources","production_participation",26271,350,0.391872358879774,15.0200890085389,4,0.00465973205206816,TRUE
"fixed_factors_no_income_expense","production_participation",26271,350,0.390293075354083,16.7656943816629,4,0.00214639854785192,TRUE
"fixed_factors_no_income_expense_land_w99","production_participation",26271,350,0.390293075354083,16.765694381663,4,0.00214639854785181,TRUE
"full_M3_resources","log_selfprod_amount",26271,350,0.421796748396454,4.34582986913326,4,0.361221393051786,TRUE
"fixed_factors_no_income_expense","log_selfprod_amount",26271,350,0.42089840940115,3.88342518159888,4,0.422012364687999,TRUE
"fixed_factors_no_income_expense_land_w99","log_selfprod_amount",26271,350,0.420898409401149,3.883425181599,4,0.422012364687983,TRUE
"full_M3_resources","ihs_selfprod_amount",26271,350,0.42524354764847,4.16930404078851,4,0.383577663351849,TRUE
"fixed_factors_no_income_expense","ihs_selfprod_amount",26271,350,0.424300972019256,3.73182371046765,4,0.443514278980701,TRUE
"fixed_factors_no_income_expense_land_w99","ihs_selfprod_amount",26271,350,0.424300972019256,3.73182371046773,4,0.443514278980689,TRUE
````

## Table CSV: `outputs/tables/tableL_participation_missingness_robustness.csv`

- Size: 0.5 KB
- Lines: 4

````csv
"diagnostic","value","implication"
"selfprod_monthly_total_missing_in_current_long_file","0","The current long files no longer preserve item-level source missingness."
"production_participation_missing_in_current_long_file","0","Participation is fully populated after prior cleaning."
"na_to_zero_robustness_status","not_reconstructable_from_current_analysis_ready_or_cleaned_long_files","Report as a limitation and rerun only if raw item-level missing codes are restored."
````

## Table CSV: `outputs/tables/tableM_definition_diagnostics_editor.csv`

- Size: 1.1 KB
- Lines: 7

````csv
"diagnostic","value","numeric_value","decision"
"pooled_repeated_cross_section","min_years_per_nhCode=1; max_years_per_nhCode=1",1,"No household fixed effects are feasible with current nhCode; use pooled repeated cross-section language."
"households_at_roster_cap_8","18 of 3565 households",0.00504908835904628,"Roster cap is visible but rare; disclose in data limitations."
"total_sown_area_w99_max","max=317.965920000001; p99=316.261651200001",317.965920000001,"Winsorized total sown area is used as a sensitivity check; main setup still uses total_sown_area."
"sex_coding_audit","household_head_gender_male inferred from earlier household relation cross-check, codebook confirmation still needed",NA,"Keep female_share interpretation conditional until HA2 coding is manually verified."
"youzhi_definition","partially identified; item-code review required",NA,"Do not make strong substantive claims about oils before item-code review."
"roulei_aggregation","meat plus aquatic plus processed products in current aggregate category",NA,"Use label meat/aquatic products and state aggregation limitation."
````

## Table CSV: `outputs/tables/tableN_price_unit_value_diagnostics.csv`

- Size: 0.6 KB
- Lines: 6

````csv
"diagnostic","value","interpretation"
"observed_unit_value_share",0.729916394038531,"Observed variable is household purchase-side unit value, not pure exogenous price."
"hedonic_imputed_share",0.270083605961469,"A sizeable share is imputed and should be disclosed."
"county_hedonic_r_squared",0.443267689256615,"Hedonic imputation explains a moderate share of log unit-value variation."
"county_hedonic_rmse_log",0.69812876821501,"RMSE implies noisy unit-value prediction."
"observed_only_participation_p",0.00400796736955511,"Observed-only robustness remains statistically similar for participation, but on a selected purchasing subsample."
````

## 7. Model Summaries JSON

## Model Summary JSON: `outputs/model_summaries/model2_common_sample_baseline.json`

- Size: 3 KB
- Lines: 16

````json
{
  "models": [
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M0","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.34950757,"hhcomp_wald_chisq":6.6306639,"hhcomp_wald_df":4,"hhcomp_wald_p":0.15674144},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M1","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.36488948,"hhcomp_wald_chisq":7.1401449,"hhcomp_wald_df":4,"hhcomp_wald_p":0.12866497},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M2","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.38668043,"hhcomp_wald_chisq":13.75857,"hhcomp_wald_df":4,"hhcomp_wald_p":0.0081068341},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M3","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.39187236,"hhcomp_wald_chisq":15.020089,"hhcomp_wald_df":4,"hhcomp_wald_p":0.0046597321},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M0","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.3655174,"hhcomp_wald_chisq":19.834171,"hhcomp_wald_df":4,"hhcomp_wald_p":0.0005384821},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M1","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.37073323,"hhcomp_wald_chisq":5.1632195,"hhcomp_wald_df":4,"hhcomp_wald_p":0.27095638},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M2","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.41067942,"hhcomp_wald_chisq":4.306992,"hhcomp_wald_df":4,"hhcomp_wald_p":0.36605037},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M3","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.42179675,"hhcomp_wald_chisq":4.3458299,"hhcomp_wald_df":4,"hhcomp_wald_p":0.36122139},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M0","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.36830213,"hhcomp_wald_chisq":19.705254,"hhcomp_wald_df":4,"hhcomp_wald_p":0.00057094388},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M1","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.37363634,"hhcomp_wald_chisq":5.2254166,"hhcomp_wald_df":4,"hhcomp_wald_p":0.26494034},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M2","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.41381545,"hhcomp_wald_chisq":4.2181678,"hhcomp_wald_df":4,"hhcomp_wald_p":0.37728449},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M3","common_m3_sample":"TRUE","n":26271,"n_clusters":350,"r_squared":0.42524355,"hhcomp_wald_chisq":4.169304,"hhcomp_wald_df":4,"hhcomp_wald_p":0.38357766}
  ]
}
````

## Model Summary JSON: `outputs/model_summaries/model3_baseline_coefficients_margins.json`

- Size: 22.2 KB
- Lines: 52

````json
{
  "coefficients": [
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M0","term":"household_size_reconstructed","estimate":-0.0035605101,"std_error_cluster":0.0035978149,"t_stat":-0.98963124,"p_value":0.32235439,"direction":"negative","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.34950757},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M1","term":"household_size_reconstructed","estimate":-0.00626144,"std_error_cluster":0.00362209,"t_stat":-1.7286815,"p_value":0.083866117,"direction":"negative","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.36488948},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M2","term":"household_size_reconstructed","estimate":-0.0074950011,"std_error_cluster":0.0031408086,"t_stat":-2.3863285,"p_value":0.017017543,"direction":"negative","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.38668043},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M3","term":"household_size_reconstructed","estimate":-0.0074527134,"std_error_cluster":0.0031476385,"t_stat":-2.3677158,"p_value":0.017898278,"direction":"negative","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.39187236},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M0","term":"child_share","estimate":-0.048050826,"std_error_cluster":0.026550828,"t_stat":-1.8097675,"p_value":0.070331852,"direction":"negative","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.34950757},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M1","term":"child_share","estimate":0.042358002,"std_error_cluster":0.02644164,"t_stat":1.6019431,"p_value":0.1091682,"direction":"positive","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.36488948},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M2","term":"child_share","estimate":0.037750282,"std_error_cluster":0.023103622,"t_stat":1.6339551,"p_value":0.10226828,"direction":"positive","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.38668043},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M3","term":"child_share","estimate":0.043633131,"std_error_cluster":0.022096597,"t_stat":1.9746539,"p_value":0.048307442,"direction":"positive","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.39187236},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M0","term":"elderly_share","estimate":-0.0060266074,"std_error_cluster":0.012358888,"t_stat":-0.48763345,"p_value":0.6258095,"direction":"negative","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.34950757},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M1","term":"elderly_share","estimate":0.030160035,"std_error_cluster":0.014498747,"t_stat":2.0801821,"p_value":0.037508831,"direction":"positive","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.36488948},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M2","term":"elderly_share","estimate":0.040121877,"std_error_cluster":0.0133219,"t_stat":3.0117233,"p_value":0.0025976927,"direction":"positive","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.38668043},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M3","term":"elderly_share","estimate":0.040570414,"std_error_cluster":0.013211049,"t_stat":3.0709456,"p_value":0.00213382,"direction":"positive","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.39187236},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M0","term":"female_share","estimate":-0.0035459441,"std_error_cluster":0.0179537,"t_stat":-0.19750492,"p_value":0.84343243,"direction":"negative","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.34950757},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M1","term":"female_share","estimate":-0.005564266,"std_error_cluster":0.018687439,"t_stat":-0.29775434,"p_value":0.76589067,"direction":"negative","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.36488948},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M2","term":"female_share","estimate":0.0078208986,"std_error_cluster":0.016625917,"t_stat":0.47040404,"p_value":0.63806638,"direction":"positive","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.38668043},
    {"outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","spec":"M3","term":"female_share","estimate":0.010398759,"std_error_cluster":0.016417892,"t_stat":0.63337966,"p_value":0.52648574,"direction":"positive","marginal_effect_interpretation":"LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.39187236},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M0","term":"household_size_reconstructed","estimate":0.019625516,"std_error_cluster":0.0072371408,"t_stat":2.7117776,"p_value":0.0066923478,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"positive","n":26271,"n_clusters":350,"r_squared":0.3655174},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M1","term":"household_size_reconstructed","estimate":0.0097224281,"std_error_cluster":0.0083628257,"t_stat":1.1625769,"p_value":0.2450012,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"positive","n":26271,"n_clusters":350,"r_squared":0.37073323},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M2","term":"household_size_reconstructed","estimate":0.0045346232,"std_error_cluster":0.0072780869,"t_stat":0.62305153,"p_value":0.53325066,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"positive","n":26271,"n_clusters":350,"r_squared":0.41067942},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M3","term":"household_size_reconstructed","estimate":0.0066924055,"std_error_cluster":0.006920583,"t_stat":0.96702915,"p_value":0.33352946,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"positive","n":26271,"n_clusters":350,"r_squared":0.42179675},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M0","term":"child_share","estimate":-0.20297777,"std_error_cluster":0.055440232,"t_stat":-3.6611998,"p_value":0.00025103686,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.3655174},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M1","term":"child_share","estimate":-0.10944535,"std_error_cluster":0.055612939,"t_stat":-1.9679836,"p_value":0.049069921,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.37073323},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M2","term":"child_share","estimate":-0.06552135,"std_error_cluster":0.050344168,"t_stat":-1.3014685,"p_value":0.19309813,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.41067942},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M3","term":"child_share","estimate":-0.039008496,"std_error_cluster":0.048370046,"t_stat":-0.80645976,"p_value":0.4199778,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.42179675},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M0","term":"elderly_share","estimate":-0.015287174,"std_error_cluster":0.02506834,"t_stat":-0.60981996,"p_value":0.54198108,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.3655174},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M1","term":"elderly_share","estimate":0.025340105,"std_error_cluster":0.032671547,"t_stat":0.77560164,"p_value":0.43798423,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.37073323},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M2","term":"elderly_share","estimate":0.040651049,"std_error_cluster":0.028698401,"t_stat":1.4164918,"p_value":0.15663157,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.41067942},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M3","term":"elderly_share","estimate":0.042560563,"std_error_cluster":0.02691196,"t_stat":1.5814739,"p_value":0.11376971,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.42179675},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M0","term":"female_share","estimate":-0.076753197,"std_error_cluster":0.036357198,"t_stat":-2.1110867,"p_value":0.034764861,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.3655174},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M1","term":"female_share","estimate":-0.024014616,"std_error_cluster":0.040574017,"t_stat":-0.59187179,"p_value":0.55393645,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.37073323},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M2","term":"female_share","estimate":0.018046437,"std_error_cluster":0.037991723,"t_stat":0.47500971,"p_value":0.63478005,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.41067942},
    {"outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","spec":"M3","term":"female_share","estimate":0.022570612,"std_error_cluster":0.036199692,"t_stat":0.62350288,"p_value":0.53295411,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.42179675},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M0","term":"household_size_reconstructed","estimate":0.023485258,"std_error_cluster":0.0088293705,"t_stat":2.6599018,"p_value":0.0078163447,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"positive","n":26271,"n_clusters":350,"r_squared":0.36830213},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M1","term":"household_size_reconstructed","estimate":0.011752626,"std_error_cluster":0.010214956,"t_stat":1.1505312,"p_value":0.24992513,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"positive","n":26271,"n_clusters":350,"r_squared":0.37363634},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M2","term":"household_size_reconstructed","estimate":0.0051404201,"std_error_cluster":0.0088905377,"t_stat":0.57819001,"p_value":0.56313584,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"positive","n":26271,"n_clusters":350,"r_squared":0.41381545},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M3","term":"household_size_reconstructed","estimate":0.0078310117,"std_error_cluster":0.0084528803,"t_stat":0.92643116,"p_value":0.35422196,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"positive","n":26271,"n_clusters":350,"r_squared":0.42524355},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M0","term":"child_share","estimate":-0.24821845,"std_error_cluster":0.0676799,"t_stat":-3.6675357,"p_value":0.00024489939,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.36830213},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M1","term":"child_share","estimate":-0.13540463,"std_error_cluster":0.06799246,"t_stat":-1.9914653,"p_value":0.046429751,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.37363634},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M2","term":"child_share","estimate":-0.080308871,"std_error_cluster":0.061479693,"t_stat":-1.3062666,"p_value":0.1914619,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.41381545},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M3","term":"child_share","estimate":-0.047388867,"std_error_cluster":0.059021016,"t_stat":-0.80291513,"p_value":0.42202379,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"TRUE","stable_direction":"negative","n":26271,"n_clusters":350,"r_squared":0.42524355},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M0","term":"elderly_share","estimate":-0.020632271,"std_error_cluster":0.03065789,"t_stat":-0.67298406,"p_value":0.50095743,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.36830213},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M1","term":"elderly_share","estimate":0.029645699,"std_error_cluster":0.040128994,"t_stat":0.73876009,"p_value":0.46005269,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.37363634},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M2","term":"elderly_share","estimate":0.048896684,"std_error_cluster":0.035239021,"t_stat":1.3875721,"p_value":0.16526737,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.41381545},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M3","term":"elderly_share","estimate":0.051289678,"std_error_cluster":0.033028657,"t_stat":1.5528842,"p_value":0.12045081,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.42524355},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M0","term":"female_share","estimate":-0.094247172,"std_error_cluster":0.044673172,"t_stat":-2.1097041,"p_value":0.034883855,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.36830213},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M1","term":"female_share","estimate":-0.030514086,"std_error_cluster":0.049695977,"t_stat":-0.61401522,"p_value":0.53920527,"direction":"negative","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.37363634},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M2","term":"female_share","estimate":0.021500604,"std_error_cluster":0.046487861,"t_stat":0.46249932,"p_value":0.64372329,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.41381545},
    {"outcome":"ihs_selfprod_amount","conceptual_outcome":"ihs_selfprod_amount","spec":"M3","term":"female_share","estimate":0.026932974,"std_error_cluster":0.04421792,"t_stat":0.60909636,"p_value":0.54246057,"direction":"positive","marginal_effect_interpretation":"OLS coefficient for transformed self-production amount.","sign_stable_across_M0_M3":"FALSE","stable_direction":"not_stable","n":26271,"n_clusters":350,"r_squared":0.42524355}
  ]
}
````

## Model Summary JSON: `outputs/model_summaries/model4_category_specific_nsi.json`

- Size: 7.4 KB
- Lines: 12

````json
{
  "categories": [
    {"food_category":"zhushi","food_category_label":"主食","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":3261,"n_clusters":350,"outcome_mean":0.8365532,"r_squared":0.2367479,"hhcomp_wald_chisq":2.8134651,"hhcomp_wald_df":4,"hhcomp_wald_p":0.58951065,"household_size_reconstructed_coef":-0.0082830354,"household_size_reconstructed_se":0.0063225511,"household_size_reconstructed_t":-1.310078,"household_size_reconstructed_p":0.19016943,"child_share_coef":0.012656327,"child_share_se":0.045776216,"child_share_t":0.27648258,"child_share_p":0.78217743,"elderly_share_coef":0.0049689036,"elderly_share_se":0.026567821,"elderly_share_t":0.18702714,"elderly_share_p":0.85163935,"female_share_coef":0.025020139,"female_share_se":0.034051731,"female_share_t":0.73476849,"female_share_p":0.4624805,"main_coefficient_drivers":"none_p_lt_0.10","nsi":0.27921685,"signal_label":"Weak"},
    {"food_category":"doulei","food_category_label":"豆类","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":3279,"n_clusters":350,"outcome_mean":0.2284233,"r_squared":0.12069192,"hhcomp_wald_chisq":9.0399608,"hhcomp_wald_df":4,"hhcomp_wald_p":0.060108376,"household_size_reconstructed_coef":0.0068388938,"household_size_reconstructed_se":0.0066600453,"household_size_reconstructed_t":1.0268539,"household_size_reconstructed_p":0.30448925,"child_share_coef":0.056804099,"child_share_se":0.051544536,"child_share_t":1.1020392,"child_share_p":0.27044463,"elderly_share_coef":0.050046979,"elderly_share_se":0.030311691,"elderly_share_t":1.6510784,"elderly_share_p":0.098722568,"female_share_coef":0.043001995,"female_share_se":0.038987182,"female_share_t":1.1029778,"female_share_p":0.27003681,"main_coefficient_drivers":"elderly_share","nsi":0.89715326,"signal_label":"Weak"},
    {"food_category":"roulei","food_category_label":"肉类和水产品及加工品","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":3270,"n_clusters":350,"outcome_mean":0.34067278,"r_squared":0.31700874,"hhcomp_wald_chisq":4.4563468,"hhcomp_wald_df":4,"hhcomp_wald_p":0.34775505,"household_size_reconstructed_coef":-0.0016112223,"household_size_reconstructed_se":0.0078874483,"household_size_reconstructed_t":-0.20427674,"household_size_reconstructed_p":0.83813724,"child_share_coef":0.071285892,"child_share_se":0.050113269,"child_share_t":1.4224954,"child_share_p":0.1548825,"elderly_share_coef":0.050271004,"elderly_share_se":0.029120533,"elderly_share_t":1.7263078,"elderly_share_p":0.08429205,"female_share_coef":0.0092948656,"female_share_se":0.042318712,"female_share_t":0.21963961,"female_share_p":0.82615184,"main_coefficient_drivers":"elderly_share","nsi":0.44226144,"signal_label":"Weak"},
    {"food_category":"danlei","food_category_label":"蛋类","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":3274,"n_clusters":350,"outcome_mean":0.43646915,"r_squared":0.27491288,"hhcomp_wald_chisq":17.042315,"hhcomp_wald_df":4,"hhcomp_wald_p":0.0018966974,"household_size_reconstructed_coef":-0.00035732986,"household_size_reconstructed_se":0.0080623936,"household_size_reconstructed_t":-0.044320568,"household_size_reconstructed_p":0.96464888,"child_share_coef":0.014962416,"child_share_se":0.053908908,"child_share_t":0.27754998,"child_share_p":0.78135784,"elderly_share_coef":0.13173778,"elderly_share_se":0.033333167,"elderly_share_t":3.952153,"elderly_share_p":7.745118e-05,"female_share_coef":0.040313743,"female_share_se":0.041633231,"female_share_t":0.96830686,"female_share_p":0.33289114,"main_coefficient_drivers":"elderly_share","nsi":1.6913313,"signal_label":"Strong"},
    {"food_category":"nailei","food_category_label":"奶类","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":3343,"n_clusters":350,"outcome_mean":0.0011965301,"r_squared":0.01840646,"hhcomp_wald_chisq":4.0222532,"hhcomp_wald_df":4,"hhcomp_wald_p":0.40300259,"household_size_reconstructed_coef":-0.00094917365,"household_size_reconstructed_se":0.00049620403,"household_size_reconstructed_t":-1.9128697,"household_size_reconstructed_p":0.055764739,"child_share_coef":0.0019789636,"child_share_se":0.0015280244,"child_share_t":1.2951125,"child_share_p":0.19528142,"elderly_share_coef":-0.0014571715,"elderly_share_se":0.0023017101,"elderly_share_t":-0.63308212,"elderly_share_p":0.52668002,"female_share_coef":0.0090842733,"female_share_se":0.0049601826,"female_share_t":1.8314393,"female_share_p":0.067035,"main_coefficient_drivers":"household_size_reconstructed;female_share","nsi":0.39918067,"signal_label":"Weak"},
    {"food_category":"youzhi","food_category_label":"油脂","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":3308,"n_clusters":350,"outcome_mean":0.39147521,"r_squared":0.19968654,"hhcomp_wald_chisq":16.113389,"hhcomp_wald_df":4,"hhcomp_wald_p":0.002870726,"household_size_reconstructed_coef":-0.020058741,"household_size_reconstructed_se":0.0078491285,"household_size_reconstructed_t":-2.5555373,"household_size_reconstructed_p":0.0106024,"child_share_coef":0.18078708,"child_share_se":0.057063846,"child_share_t":3.1681544,"child_share_p":0.0015341002,"elderly_share_coef":0.011539232,"elderly_share_se":0.033840477,"elderly_share_t":0.34098905,"elderly_share_p":0.73311182,"female_share_coef":-0.084508907,"female_share_se":0.043441094,"female_share_t":-1.9453678,"female_share_p":0.051730723,"main_coefficient_drivers":"household_size_reconstructed;child_share;female_share","nsi":1.5991419,"signal_label":"Strong"},
    {"food_category":"shucai","food_category_label":"蔬菜","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":3275,"n_clusters":350,"outcome_mean":0.93557252,"r_squared":0.18960627,"hhcomp_wald_chisq":14.738509,"hhcomp_wald_df":4,"hhcomp_wald_p":0.0052754595,"household_size_reconstructed_coef":-0.010055669,"household_size_reconstructed_se":0.004598277,"household_size_reconstructed_t":-2.1868341,"household_size_reconstructed_p":0.028754639,"child_share_coef":0.028523353,"child_share_se":0.033353021,"child_share_t":0.85519551,"child_share_p":0.39244292,"elderly_share_coef":0.051189502,"elderly_share_se":0.017272623,"elderly_share_t":2.9636205,"elderly_share_p":0.0030404295,"female_share_coef":-0.016542533,"female_share_se":0.019374555,"female_share_t":-0.85382775,"female_share_p":0.39320044,"main_coefficient_drivers":"household_size_reconstructed;elderly_share","nsi":1.4626945,"signal_label":"Strong"},
    {"food_category":"shuiguo","food_category_label":"水果","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":3261,"n_clusters":350,"outcome_mean":0.2959215,"r_squared":0.14919506,"hhcomp_wald_chisq":12.383941,"hhcomp_wald_df":4,"hhcomp_wald_p":0.01471327,"household_size_reconstructed_coef":-0.019903315,"household_size_reconstructed_se":0.0071288667,"household_size_reconstructed_t":-2.7919325,"household_size_reconstructed_p":0.0052394287,"child_share_coef":-0.030000656,"child_share_se":0.053247323,"child_share_t":-0.56342093,"child_share_p":0.57314829,"elderly_share_coef":0.030041593,"elderly_share_se":0.032980826,"elderly_share_t":0.91088057,"elderly_share_p":0.3623583,"female_share_coef":0.047695543,"female_share_se":0.041565385,"female_share_t":1.1474823,"female_share_p":0.25118235,"main_coefficient_drivers":"household_size_reconstructed","nsi":1.2290201,"signal_label":"Moderate"}
  ]
}
````

## Model Summary JSON: `outputs/model_summaries/model5_two_part_model.json`

- Size: 2 KB
- Lines: 6

````json
{
  "two_part_models": [
    {"model_part":"Part 1","model_name":"entry_all_observations","sample_definition":"all observations","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":26271,"n_clusters":350,"outcome_mean":0.43195919,"r_squared":0.39187236,"hhcomp_wald_chisq":15.020089,"hhcomp_wald_df":4,"hhcomp_wald_p":0.0046597321,"household_size_reconstructed_coef":-0.0074527134,"household_size_reconstructed_se":0.0031476385,"household_size_reconstructed_t":-2.3677158,"household_size_reconstructed_p":0.017898278,"child_share_coef":0.043633131,"child_share_se":0.022096597,"child_share_t":1.9746539,"child_share_p":0.048307442,"elderly_share_coef":0.040570414,"elderly_share_se":0.013211049,"elderly_share_t":3.0709456,"elderly_share_p":0.00213382,"female_share_coef":0.010398759,"female_share_se":0.016417892,"female_share_t":0.63337966,"female_share_p":0.52648574,"interpretation":"Non-separability appears mainly on the entry margin rather than the conditional intensity margin."},
    {"model_part":"Part 2","model_name":"conditional_intensity_positive_entry","sample_definition":"production_participation == 1","outcome":"log_selfprod_amount","conceptual_outcome":"log_selfprod_amount","n":11348,"n_clusters":349,"outcome_mean":1.173038,"r_squared":0.39272209,"hhcomp_wald_chisq":7.6268755,"hhcomp_wald_df":4,"hhcomp_wald_p":0.10624302,"household_size_reconstructed_coef":0.037950722,"household_size_reconstructed_se":0.014544256,"household_size_reconstructed_t":2.6093271,"household_size_reconstructed_p":0.0090720475,"child_share_coef":-0.16443627,"child_share_se":0.100872,"child_share_t":-1.6301478,"child_share_p":0.10307026,"elderly_share_coef":0.014962129,"elderly_share_se":0.055329739,"elderly_share_t":0.27041749,"elderly_share_p":0.78683908,"female_share_coef":0.015872595,"female_share_se":0.072458065,"female_share_t":0.21905905,"female_share_p":0.82660405,"interpretation":"Non-separability appears mainly on the entry margin rather than the conditional intensity margin."}
  ]
}
````

## Model Summary JSON: `outputs/model_summaries/model6_robustness.json`

- Size: 0.2 KB
- Lines: 7

````json
{
  "robustness_outputs": [
    {"model":"alternative_composition_outcomes","rows":12},
    {"model":"leave_one_province","rows":8},
    {"model":"household_composition_permutation","rows":1}
  ]
}
````

## Model Summary JSON: `outputs/model_summaries/modelA_market_interactions_appendix.json`

- Size: 2.9 KB
- Lines: 13

````json
{
  "market_interactions": [
    {"friction_spec":"survey_market_friction","friction_variable":"market_friction_survey","outcome":"production_participation","n":26271,"n_clusters":350,"r_squared":0.39191485,"interaction_wald_chisq":0.82637176,"interaction_wald_df":4,"interaction_wald_p":0.934878,"evidence_label":"weak_or_no_amplification_evidence"},
    {"friction_spec":"survey_market_friction","friction_variable":"market_friction_survey","outcome":"log_selfprod_amount","n":26271,"n_clusters":350,"r_squared":0.42199656,"interaction_wald_chisq":4.4512219,"interaction_wald_df":4,"interaction_wald_p":0.34837054,"evidence_label":"weak_or_no_amplification_evidence"},
    {"friction_spec":"survey_market_friction","friction_variable":"market_friction_survey","outcome":"ihs_selfprod_amount","n":26271,"n_clusters":350,"r_squared":0.42545863,"interaction_wald_chisq":4.734591,"interaction_wald_df":4,"interaction_wald_p":0.3156297,"evidence_label":"weak_or_no_amplification_evidence"},
    {"friction_spec":"poi_market_friction","friction_variable":"poi_market_friction_lag1","outcome":"production_participation","n":26271,"n_clusters":350,"r_squared":0.39201868,"interaction_wald_chisq":2.0216597,"interaction_wald_df":4,"interaction_wald_p":0.73177487,"evidence_label":"weak_or_no_amplification_evidence"},
    {"friction_spec":"poi_market_friction","friction_variable":"poi_market_friction_lag1","outcome":"log_selfprod_amount","n":26271,"n_clusters":350,"r_squared":0.42199654,"interaction_wald_chisq":3.7093236,"interaction_wald_df":4,"interaction_wald_p":0.44677131,"evidence_label":"weak_or_no_amplification_evidence"},
    {"friction_spec":"poi_market_friction","friction_variable":"poi_market_friction_lag1","outcome":"ihs_selfprod_amount","n":26271,"n_clusters":350,"r_squared":0.42543671,"interaction_wald_chisq":3.5485677,"interaction_wald_df":4,"interaction_wald_p":0.47053205,"evidence_label":"weak_or_no_amplification_evidence"},
    {"friction_spec":"combined_market_friction","friction_variable":"combined_market_friction","outcome":"production_participation","n":26960,"n_clusters":360,"r_squared":0.394008,"interaction_wald_chisq":0.59598873,"interaction_wald_df":4,"interaction_wald_p":0.96350839,"evidence_label":"weak_or_no_amplification_evidence"},
    {"friction_spec":"combined_market_friction","friction_variable":"combined_market_friction","outcome":"log_selfprod_amount","n":26960,"n_clusters":360,"r_squared":0.42518539,"interaction_wald_chisq":4.0135649,"interaction_wald_df":4,"interaction_wald_p":0.40417315,"evidence_label":"weak_or_no_amplification_evidence"},
    {"friction_spec":"combined_market_friction","friction_variable":"combined_market_friction","outcome":"ihs_selfprod_amount","n":26960,"n_clusters":360,"r_squared":0.42880356,"interaction_wald_chisq":3.9450892,"interaction_wald_df":4,"interaction_wald_p":0.41348822,"evidence_label":"weak_or_no_amplification_evidence"}
  ]
}
````

## Model Summary JSON: `outputs/model_summaries/modelB_iv_diagnostics_appendix.json`

- Size: 1.6 KB
- Lines: 9

````json
{
  "iv_diagnostics": [
    {"iv_spec":"terrain_town_2km","iv_variable":"iv_terrain_barrier_town_gee_2km","n_households_for_correlation":3475,"correlation_with_market_friction_survey":0.12867183,"min_first_stage_F":1.1424536,"median_first_stage_F":2.0802806,"weak_iv_flag":"TRUE","appendix_only":"TRUE","interpretation":"weak_first_stage_appendix_only"},
    {"iv_spec":"terrain_town_1km","iv_variable":"iv_terrain_barrier_town_gee_1km","n_households_for_correlation":3475,"correlation_with_market_friction_survey":0.13331008,"min_first_stage_F":0.98112124,"median_first_stage_F":2.0254366,"weak_iv_flag":"TRUE","appendix_only":"TRUE","interpretation":"weak_first_stage_appendix_only"},
    {"iv_spec":"terrain_town_5km","iv_variable":"iv_terrain_barrier_town_gee_5km","n_households_for_correlation":3475,"correlation_with_market_friction_survey":0.11533325,"min_first_stage_F":1.4487239,"median_first_stage_F":2.1441371,"weak_iv_flag":"TRUE","appendix_only":"TRUE","interpretation":"weak_first_stage_appendix_only"},
    {"iv_spec":"terrain_county_2km","iv_variable":"iv_terrain_barrier_county_gee_2km","n_households_for_correlation":3475,"correlation_with_market_friction_survey":0.13397233,"min_first_stage_F":2.0286233,"median_first_stage_F":2.1180573,"weak_iv_flag":"TRUE","appendix_only":"TRUE","interpretation":"weak_first_stage_appendix_only"},
    {"iv_spec":"early_ntl_9294","iv_variable":"iv_early_ntl_peak_dist_9294","n_households_for_correlation":3475,"correlation_with_market_friction_survey":0.11167651,"min_first_stage_F":0.73619606,"median_first_stage_F":1.3330997,"weak_iv_flag":"TRUE","appendix_only":"TRUE","interpretation":"weak_first_stage_appendix_only"}
  ]
}
````

## Model Summary JSON: `outputs/model_summaries/modelC_price_robustness.json`

- Size: 1.7 KB
- Lines: 8

````json
{
  "price_robustness": [
    {"price_spec":"no_price_control","model_compatibility_variable":"none","price_variable":"none","price_unit":"none","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":26271,"n_clusters":350,"r_squared":0.39123619,"hhcomp_wald_chisq":14.925501,"hhcomp_wald_df":4,"hhcomp_wald_p":0.0048582538,"price_observed_share":0.73305165},
    {"price_spec":"hedonic_price_main","model_compatibility_variable":"price_hedonic_imputed_w99_yuan_per_jin","price_variable":"price_hedonic_imputed_w99_yuan_per_kg","price_unit":"yuan/kg","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":26271,"n_clusters":350,"r_squared":0.39187236,"hhcomp_wald_chisq":15.020089,"hhcomp_wald_df":4,"hhcomp_wald_p":0.0046597321,"price_observed_share":0.73305165},
    {"price_spec":"observed_price_only","model_compatibility_variable":"price_preferred_household_recalc_w99_yuan_per_jin","price_variable":"price_preferred_household_recalc_w99_yuan_per_kg","price_unit":"yuan/kg","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":19258,"n_clusters":350,"r_squared":0.42870323,"hhcomp_wald_chisq":15.361113,"hhcomp_wald_df":4,"hhcomp_wald_p":0.0040079674,"price_observed_share":1},
    {"price_spec":"county_category_median_price","model_compatibility_variable":"village_price_category_median","price_variable":"village_price_category_median_yuan_per_kg","price_unit":"yuan/kg","outcome":"production_participation","conceptual_outcome":"self_provisioning_participation","n":22196,"n_clusters":338,"r_squared":0.40328829,"hhcomp_wald_chisq":8.4925733,"hhcomp_wald_df":4,"hhcomp_wald_p":0.075112661,"price_observed_share":0.74252117}
  ]
}
````

## Model Summary JSON: `outputs/model_summaries/modelE_editor_revision_analyses.json`

- Size: 0.7 KB
- Lines: 14

````json
{
  "editor_revision_outputs": [
    {"output":"tableE_add_one_block_diagnostics.csv","rows":30},
    {"output":"tableF_village_fe_robustness.csv","rows":11},
    {"output":"tableG_binary_response_robustness.csv","rows":18},
    {"output":"tableH_category_multiple_testing.csv","rows":8},
    {"output":"tableI_category_variation_and_nsi_reframed.csv","rows":8},
    {"output":"tableJ_fixed_common_sample_robustness.csv","rows":12},
    {"output":"tableK_fixed_factors_bad_controls_robustness.csv","rows":9},
    {"output":"tableL_participation_missingness_robustness.csv","rows":3},
    {"output":"tableM_definition_diagnostics_editor.csv","rows":6},
    {"output":"tableN_price_unit_value_diagnostics.csv","rows":5}
  ]
}
````

