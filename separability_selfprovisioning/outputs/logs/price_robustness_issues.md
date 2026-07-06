# Price Robustness Issues

Generated at: 2026-07-06 14:26:59

## Notes

- Price variables are interpreted as yuan/kg in the cleaned analysis data.
- Main price variable: `price_hedonic_imputed_w99_yuan_per_kg`.
- Observed-price-only uses `price_preferred_household_recalc_w99_yuan_per_kg` and drops rows with missing observed recalculated price.
- County-category median price uses `village_price_category_median_yuan_per_kg` and drops rows with missing median price.
- The model still reads legacy compatibility aliases ending in `_yuan_per_jin`; those alias values were overwritten to yuan/kg by `code/19_apply_kg_units_drop_outliers_prepare_official_data.R`.

## Issues

- None. All requested price robustness variants were generated.
