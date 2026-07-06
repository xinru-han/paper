# Paper 1 Editor-Revision Results Addendum

Generated at: 2026-07-06 14:28:46

This addendum implements the additional diagnostics requested in `paper1_editor_review_and_action_plan.md`. It should be read together with `paper1_revised_results_package.md`.

## 1. Revised Bottom Line / 修订后核心结论

- 最稳妥的正文表述应改为：在加入省份、市场可达性、农业生态、购买侧单位值和县级文本控制后，户内人口结构能够条件性预测自产自给参与；但该结果对控制集敏感，且不能通过村庄固定效应的参与边际稳健性检验。
- M1 以后数量边际整体较弱；固定共同样本下部分数量口径重新显著，说明数量结果具有样本和口径敏感性，应作为辅助描述而非主结论。
- logit/probit 对总体 M3 参与边际给出相近结论，说明 M3 的参与结果不是简单 LPM 泛函形式造成的。
- NSI 已重新定位为 Wald 检验统计量的相对可检测性排序，不是经济幅度指数；奶类因参与率接近 0 从主类别解释中剔除。

## 2. Add-One-Block Diagnostics: Participation

| label | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| B0_composition_category_year | 27568.0000 | 350.0000 | 6.2996 | 0.1779 |
| B1_plus_household_resources | 27568.0000 | 350.0000 | 7.6402 | 0.1057 |
| B1a_M1_plus_market | 27568.0000 | 350.0000 | 9.6661 | 0.0464 |
| B1b_M1_plus_GAEZ | 27568.0000 | 350.0000 | 11.4971 | 0.0215 |
| B1c_M1_plus_province_FE | 27568.0000 | 350.0000 | 12.9083 | 0.0117 |
| B1d_M1_plus_market_GAEZ | 27568.0000 | 350.0000 | 13.0472 | 0.0110 |
| B1e_M1_plus_market_province_FE | 27568.0000 | 350.0000 | 13.3309 | 0.0098 |
| B1f_M1_plus_GAEZ_province_FE | 27568.0000 | 350.0000 | 15.2842 | 0.0041 |
| B2_full_market_GAEZ_province_FE | 27568.0000 | 350.0000 | 15.1969 | 0.0043 |
| B3_plus_unit_value_text | 27568.0000 | 350.0000 | 16.7326 | 0.0022 |

## 3. Add-One-Block Diagnostics: Log Quantity

| label | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| B0_composition_category_year | 27568.0000 | 350.0000 | 22.7961 | 0.0001 |
| B1_plus_household_resources | 27568.0000 | 350.0000 | 5.4421 | 0.2449 |
| B1a_M1_plus_market | 27568.0000 | 350.0000 | 5.6563 | 0.2263 |
| B1b_M1_plus_GAEZ | 27568.0000 | 350.0000 | 5.1192 | 0.2753 |
| B1c_M1_plus_province_FE | 27568.0000 | 350.0000 | 5.8614 | 0.2097 |
| B1d_M1_plus_market_GAEZ | 27568.0000 | 350.0000 | 5.4932 | 0.2403 |
| B1e_M1_plus_market_province_FE | 27568.0000 | 350.0000 | 5.7399 | 0.2194 |
| B1f_M1_plus_GAEZ_province_FE | 27568.0000 | 350.0000 | 6.3351 | 0.1755 |
| B2_full_market_GAEZ_province_FE | 27568.0000 | 350.0000 | 6.0431 | 0.1960 |
| B3_plus_unit_value_text | 27568.0000 | 350.0000 | 6.5366 | 0.1625 |

## 4. Village Fixed Effects Robustness

| outcome | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| production_participation | 27568.0000 | 350.0000 | 6.4085 | 0.1706 |
| log_selfprod_amount | 27568.0000 | 350.0000 | 16.0595 | 0.0029 |
| ihs_selfprod_amount | 27568.0000 | 350.0000 | 15.7716 | 0.0033 |

Interpretation: village fixed effects shift identification to within-village household comparisons. In this check, the participation-margin Wald test is not significant, while the log/IHS quantity margins become significant. This weakens any claim that the M3 participation result is fully robust. Village-level market, GAEZ, province, and much of county text variation are absorbed or collinear, so this is a robustness check rather than the preferred mechanism specification.

## 5. Logit/Probit Participation Robustness

| model_family | n | n_clusters | outcome_mean | converged | wald_chisq | wald_p |
|---|---|---|---|---|---|---|
| logit | 27568.0000 | 350.0000 | 0.4404 | TRUE | 16.4175 | 0.0025 |
| probit | 27568.0000 | 350.0000 | 0.4404 | TRUE | 16.8168 | 0.0021 |

Category-specific logit/probit rows are in `outputs/tables/tableG_binary_response_robustness.csv`; extreme categories, especially dairy, should be read with separation/low-variation caution.

## 6. Category Multiple Testing and NSI Reframing

| food_category_label | participation_rate | mean_self_suff_rate | nsi | hhcomp_wald_p | p_bh_fdr | main_text_status |
|---|---|---|---|---|---|---|
| 蛋类 | 0.4413 | 0.2929 | 1.8334 | 0.0005 | 0.0043 | main_comparable_category |
| 油脂 | 0.3781 | 0.2698 | 1.4684 | 0.0032 | 0.0128 | definition_pending_human_review |
| 蔬菜 | 0.9336 | 0.5355 | 1.2880 | 0.0076 | 0.0201 | interpret_with_variation_caution |
| 水果 | 0.3025 | 0.0907 | 1.0404 | 0.0240 | 0.0479 | main_comparable_category |
| 豆类 | 0.2298 | 0.1030 | 0.9504 | 0.0361 | 0.0578 | main_comparable_category |
| 肉类和水产品及加工品 | 0.3437 | 0.1348 | 0.6283 | 0.1474 | 0.1965 | aggregate_meat_aquatic_limitations |
| 主食 | 0.8386 | 0.3328 | 0.4188 | 0.3395 | 0.3880 | interpret_with_variation_caution |
| 奶类 | 0.0013 | 0.0012 | 0.3723 | 0.4029 | 0.4029 | exclude_from_main_category_interpretation |

Interpretation: the category table now reports raw p-values and BH FDR q-values. NSI remains useful for describing where the Wald test is most detectable, but it is not an effect size. Participation and self-sufficiency are reported side by side to separate detectability from economic importance.

## 7. Fixed Common-Sample Composition Robustness

| composition_spec | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| proportion | 23335.0000 | 350.0000 | 20.1512 | 0.0005 |
| dependency | 23335.0000 | 350.0000 | 20.4460 | 0.0001 |
| counts | 23335.0000 | 350.0000 | 15.5963 | 0.0036 |

The original robustness table used different samples across proportion, dependency-ratio, and count specifications. This fixed-sample table uses the intersection of all variables needed by all composition definitions and outcomes.

## 8. Fixed-Factor / Bad-Control Sensitivity

| label | n | n_clusters | wald_chisq | wald_p |
|---|---|---|---|---|
| full_M3_resources | 27568.0000 | 350.0000 | 16.7326 | 0.0022 |
| fixed_factors_no_income_expense | 27568.0000 | 350.0000 | 18.3264 | 0.0011 |
| fixed_factors_no_income_expense_land_w99 | 27568.0000 | 350.0000 | 18.3264 | 0.0011 |

The no-income/no-expense specifications respond to the concern that income and expenditure may be jointly determined with self-provisioning. These should be discussed alongside the full M3 results.

## 9. Price and Unit-Value Diagnostics

| diagnostic | value | interpretation |
|---|---|---|
| observed_unit_value_share | 0.7299 | Observed variable is household purchase-side unit value, not pure exogenous price. |
| hedonic_imputed_share | 0.2701 | A sizeable share is imputed and should be disclosed. |
| county_hedonic_r_squared | 0.4433 | Hedonic imputation explains a moderate share of log unit-value variation. |
| county_hedonic_rmse_log | 0.6981 | RMSE implies noisy unit-value prediction. |
| observed_only_participation_p | 0.0023 | Observed-only robustness remains statistically similar for participation, but on a selected purchasing subsample. |

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
