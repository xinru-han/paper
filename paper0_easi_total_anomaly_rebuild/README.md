# Total-consumption anomaly rebuild

This project rebuilds the six-group rural food demand data from the household
acquisition modules and the village price questionnaire. It is independent of
the earlier curvature-constrained results.

## Estimand

- Quantity is total household consumption: purchased, self-produced, and
  received food.
- Every consumed unit is valued at the cleaned community replacement price.
- Purchase and self-production components are used only to identify data
  anomalies. Separate purchase or self-consumption elasticities are not treated
  as structural demand parameters.

## Rules fixed before estimation

1. Negative or internally inconsistent source quantities fail validation.
2. Generous physical upper bounds are applied to monthly per-capita total
   quantities.
3. Total, purchased, self-produced, and gift quantities are screened separately
   with one-sided log-MAD rules within province-year-food cells.
4. A robust tail is removed only when it exceeds both five scaled MADs and
   one-half of the category's generous physical ceiling. This prevents a narrow
   local distribution from classifying plausible quantities as errors. The
   preferred rule covers total consumption and self-production; all source
   components are screened in a stricter sensitivity sample.
5. Village price pairs with high below low are reordered. The high/low spread is
   reported but is not treated as an error because the two quotes can represent
   different quality items within the food group.
6. Main prices use comparable representative-product quotes. Missing villages
   are filled from same-town representative medians, the nearest representative
   village in the county, county medians, then province medians. Broad
   high/low-category midpoints are retained only for audit and corroboration.
7. Price outliers are removed before geographic imputation. Every imputation
   donor is a direct representative-product quote, never an already imputed
   value.
8. Household unit values never replace village prices; they are validation data.
9. No price floor is used. A low representative quote is removed only when it
   has one-outlet support, lies below three scaled MADs, and is corroborated by
   neither same-town villages nor the independently reported broad price.

The wide household file is reduced to the fields actually used by the model
through `code/extract_household_core.py`. This permits the complete pipeline to
run under Stata editions with a 2,048-variable limit without changing the
household sample or estimands.

## Estimation

The scripts estimate unrestricted AIDS, QUAIDS, and EASI systems with
Shonkwiler-Yen selection where identified and IV/GMM treatment of food
expenditure. Adding-up, homogeneity, and Slutsky symmetry are imposed by the
system parameterization. No Cholesky curvature parameterization, local/global
negative-semidefinite constraint, or post-estimation sign projection is used.

Run:

```stata
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_run_all.do"
```
