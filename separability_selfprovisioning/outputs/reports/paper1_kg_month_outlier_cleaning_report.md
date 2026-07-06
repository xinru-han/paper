# Paper 1 kg/month Unit Conversion and Outlier Exclusion

Generated at: 2026-07-06 14:10:28

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
| rows_before_outlier_exclusion | 28,520.000 |
| rows_after_outlier_exclusion | 28,208.000 |
| rows_dropped_for_quantity_outlier | 312.000 |
| households_before | 3,565.000 |
| households_after | 3,565.000 |
| food_categories | 8.000 |
| observed_price_cells_set_missing | 0.000 |
| hedonic_price_cells_replaced_by_category_median | 0.000 |
| village_price_cells_set_missing | 188.000 |
| spend_outlier_rows_flagged_not_dropped | 107.000 |

## Outlier Counts by Category

| food_category | food_category_label | outlier_cons_kg_month | outlier_selfprod_kg_month | outlier_purchase_qty_kg_month | outlier_quantity_any | outlier_observed_price_any | outlier_hedonic_price_any | outlier_village_price_any | outlier_spend_any | n_before | n_after |
|---|---|---|---|---|---|---|---|---|---|---|---|
| zhushi | 主食 | 18.000 | 18.000 | 18.000 | 38.000 | 0.000 | 0.000 | 30.000 | 18.000 | 3,565.000 | 3,527.000 |
| nailei | 奶类 | 16.000 | 0.000 | 11.000 | 27.000 | 0.000 | 0.000 | 29.000 | 9.000 | 3,565.000 | 3,538.000 |
| shuiguo | 水果 | 18.000 | 17.000 | 17.000 | 43.000 | 0.000 | 0.000 | 20.000 | 15.000 | 3,565.000 | 3,522.000 |
| youzhi | 油脂 | 18.000 | 18.000 | 13.000 | 37.000 | 0.000 | 0.000 | 19.000 | 12.000 | 3,565.000 | 3,528.000 |
| roulei | 肉类和水产品及加工品 | 18.000 | 16.000 | 17.000 | 41.000 | 0.000 | 0.000 | 30.000 | 13.000 | 3,565.000 | 3,524.000 |
| shucai | 蔬菜 | 18.000 | 18.000 | 16.000 | 43.000 | 0.000 | 0.000 | 20.000 | 15.000 | 3,565.000 | 3,522.000 |
| danlei | 蛋类 | 18.000 | 16.000 | 13.000 | 42.000 | 0.000 | 0.000 | 20.000 | 12.000 | 3,565.000 | 3,523.000 |
| doulei | 豆类 | 18.000 | 11.000 | 16.000 | 41.000 | 0.000 | 0.000 | 20.000 | 13.000 | 3,565.000 | 3,524.000 |

## Category Descriptives After Cleaning

| food_category | food_category_label | participation_rate | mean_cons_kg_month | mean_selfprod_kg_month | mean_self_suff_rate | mean_price_yuan_per_kg |
|---|---|---|---|---|---|---|
| zhushi | 主食 | 0.839 | 29.321 | 9.026 | 0.333 | 4.906 |
| nailei | 奶类 | 0.001 | 3.361 | 0.000 | 0.001 | 19.385 |
| shuiguo | 水果 | 0.302 | 14.258 | 1.627 | 0.091 | 4.120 |
| youzhi | 油脂 | 0.378 | 3.746 | 0.728 | 0.270 | 15.284 |
| roulei | 肉类和水产品及加工品 | 0.344 | 7.151 | 1.293 | 0.135 | 18.440 |
| shucai | 蔬菜 | 0.934 | 23.731 | 15.092 | 0.536 | 5.964 |
| danlei | 蛋类 | 0.441 | 2.402 | 0.667 | 0.293 | 12.886 |
| doulei | 豆类 | 0.230 | 2.374 | 0.267 | 0.103 | 6.585 |

## Key Descriptives After Cleaning

| module | variable | n | missing | missing_share | mean | sd | min | p01 | p05 | p25 | median | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kg_month_outlier_cleaned | production_participation | 28,208.000 | 0.000 | 0.000 | 0.437 | 0.496 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| kg_month_outlier_cleaned | cons_kg_month | 28,208.000 | 0.000 | 0.000 | 10.638 | 23.881 | 0.000 | 0.000 | 0.078 | 0.460 | 2.276 | 8.977 | 52.613 | 108.271 | 754.309 |
| kg_month_outlier_cleaned | selfprod_kg_month | 28,208.000 | 0.000 | 0.000 | 3.653 | 12.779 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.822 | 22.500 | 64.286 | 270.060 |
| kg_month_outlier_cleaned | purchase_qty_kg_month | 23,597.000 | 4,611.000 | 0.163 | 12.958 | 22.120 | 0.042 | 0.250 | 0.750 | 2.500 | 6.000 | 14.000 | 49.500 | 100.808 | 502.500 |
| kg_month_outlier_cleaned | self_suff_rate | 27,494.000 | 714.000 | 0.025 | 0.222 | 0.345 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.375 | 1.000 | 1.000 | 1.000 |
| kg_month_outlier_cleaned | log_selfprod_amount | 28,208.000 | 0.000 | 0.000 | 0.549 | 1.034 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.600 | 3.157 | 4.179 | 5.602 |
| kg_month_outlier_cleaned | ihs_selfprod_amount | 28,208.000 | 0.000 | 0.000 | 0.673 | 1.248 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.750 | 3.807 | 4.857 | 6.292 |
| kg_month_outlier_cleaned | price_hedonic_imputed_w99_yuan_per_kg | 28,208.000 | 0.000 | 0.000 | 10.881 | 12.582 | 0.309 | 0.651 | 1.739 | 4.500 | 8.287 | 13.866 | 26.073 | 49.202 | 200.000 |
| kg_month_outlier_cleaned | price_preferred_household_recalc_w99_yuan_per_kg | 20,635.000 | 7,573.000 | 0.268 | 11.158 | 16.698 | 0.016 | 0.476 | 1.400 | 4.067 | 7.200 | 13.333 | 30.000 | 59.932 | 319.400 |
| kg_month_outlier_cleaned | village_price_category_median_yuan_per_kg | 23,288.000 | 4,920.000 | 0.174 | 42.238 | 152.214 | 0.908 | 3.760 | 5.200 | 9.200 | 13.340 | 21.600 | 58.888 | 1,000.000 | 2,000.000 |
| kg_month_outlier_cleaned | spend_sum_yuan | 20,638.000 | 7,570.000 | 0.268 | 105.036 | 227.048 | 0.400 | 2.500 | 5.300 | 20.000 | 50.000 | 115.000 | 343.150 | 900.000 | 12,070.000 |
| kg_month_outlier_cleaned | household_size_reconstructed | 28,208.000 | 0.000 | 0.000 | 2.885 | 1.403 | 0.000 | 1.000 | 1.000 | 2.000 | 2.000 | 4.000 | 6.000 | 7.000 | 8.000 |
| kg_month_outlier_cleaned | child_share | 28,064.000 | 144.000 | 0.005 | 0.082 | 0.166 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 0.667 | 1.000 |
| kg_month_outlier_cleaned | elderly_share | 28,064.000 | 144.000 | 0.005 | 0.214 | 0.343 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.333 | 1.000 | 1.000 | 1.000 |
| kg_month_outlier_cleaned | female_share | 28,064.000 | 144.000 | 0.005 | 0.507 | 0.208 | 0.000 | 0.000 | 0.000 | 0.500 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 |
| kg_month_outlier_cleaned | agricultural_labor_days | 28,208.000 | 0.000 | 0.000 | 289.116 | 253.281 | 0.000 | 0.000 | 0.000 | 65.000 | 240.000 | 420.000 | 730.000 | 1,030.000 | 2,190.000 |
| kg_month_outlier_cleaned | offfarm_labor_days | 28,208.000 | 0.000 | 0.000 | 194.615 | 250.428 | 0.000 | 0.000 | 0.000 | 0.000 | 100.000 | 305.000 | 698.250 | 1,055.000 | 2,155.000 |
| kg_month_outlier_cleaned | total_sown_area | 28,208.000 | 0.000 | 0.000 | 23.229 | 52.610 | 0.000 | 0.000 | 0.000 | 1.000 | 5.200 | 16.030 | 122.000 | 317.966 | 317.966 |
