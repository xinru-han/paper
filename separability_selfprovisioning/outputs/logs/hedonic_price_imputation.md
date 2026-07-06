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
