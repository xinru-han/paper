# Food demand systems with community prices

This is a clean Stata 17 pipeline for the 2023-2024 food-consumption survey. It
does not overwrite the legacy EASI files. The final system contains six groups:
staples, beans/bean products, meat, edible oil, vegetables, and fruit.

## Run

```stata
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_run_all.do"
```

`04_estimate_easi.do` estimates the legacy comparison systems, while `07`-`11`
reconstruct purchase/own/gift quantities, estimate the source-corrected systems,
request 199 village-bootstrap replications (with failed joint-support draws
reported separately), and assemble the main tables. The full run can take more
than one hour. Stata 17 is licensed in the current container.
`06_instrument_sensitivity.do` runs the same-sample weak-instrument sensitivity
specifications, and `05_validate_outputs.do` then rejects incomplete, stale, or
internally inconsistent model-selection and postestimation files.

To install only the reusable command set in another Stata project:

```stata
net install fooddem, from("/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/ado") replace
help fooddem
```

## Data construction

- Household and village identifiers remain strings. The exact merge key is the
  first 12 characters of the 14-character household ID plus survey year.
- Household unit values are reconstructed from original module-level purchased
  quantities and expenditures. Legacy `*_price_wavg` fields are not used.
- Replacement-cost total demand values every consumed unit at the village retail
  price. Purchase demand uses purchased quantities only. Own consumption is also
  valued separately at a screened village farmgate opportunity price built from
  questionnaire item 08; this separate system is a diagnostic because production
  choice makes the farmgate price endogenous.
- Invalid household size is repaired from the eight-member roster only when the
  reported size is invalid and the roster is observed. All repairs and deletions
  are counted in `outputs/household_demographic_audit.csv`.
- Extreme raw quantity/frequency errors are removed with declared physical
  per-capita bounds; observations are not winsorized into plausible values.

## Community prices

`01_build_village_prices.do` uses questionnaire prices in yuan per jin. Direct
prices have two components:

1. The explicitly requested representative products: rice/flour, tofu/soybean,
   pork, rapeseed oil, greens/cabbage, and apple/orange.
2. The midpoint of valid high/low outlet quotations, calibrated within year to
   the representative-product basket. Fruit uses fresh-fruit subcategories only.

Component and combined log prices are screened at five median absolute
deviations. Missing village-group prices are filled from direct-price donors in
this order: same-town median, nearest directly reporting village in the same
county-year, county-year median, and province-year median. Imputed values never
become donors for later levels. Price source is retained in `p#_source`.

`01b_build_self_prices.do` separately builds question-08 farmgate opportunity
prices. It uses an own-village median only with at least three producers, then
the median from other eligible villages in the same town, the nearest eligible
county village, the county eligible-village median, and province/year retail
price wedges estimated from eligible village medians. The target village is
excluded from the town donor pool, and neither ineligible target reports nor
imputed prices can propagate to another tier.

`fooddem_uvprice` separately implements a unit-value robustness series following
the common-market price, demographic-quality, and quantity-effect decomposition.
Those recovered prices validate but do not replace questionnaire community
prices in the main models.

`13_fruit_price_diagnostics.do` audits the remaining fruit-specific boundary
mismatch. Household group 6 contains fresh fruit, nuts, preserved fruit, and
dried fruit, whereas the main representative price is apple/orange based. The
diagnostic constructs all seven village subcategory prices, fills each category
before aggregation, and applies fixed pooled purchase-expenditure weights. It
then recomputes fruit value, total food expenditure, and all six shares before
repeating model selection and clustered GMM estimation.

## Estimation package

The `ado/fooddem*.ado` package accepts any number of goods greater than two.
`fooddem` estimates AIDS, QUAIDS, polynomial EASI, or optional GEASI precommitments by
GMM or NLSUR while imposing adding-up, homogeneity, and symmetry by construction.
It supports:

- Shonkwiler-Yen zero-consumption correction, with an explicit bypass when a
  participation equation is unidentified because consumption is nearly universal;
  active probabilities are recomputed in every price, expenditure, and
  demographic counterfactual;
- IV-GMM or control-function treatment of endogenous total expenditure;
- arbitrary demographic variables and additional selection/instrument controls;
- demographic translating in the AIDS/QUAIDS price index, including the
  control-function term, so conditional Slutsky symmetry is preserved;
- one-step model screening and clustered efficient two-step GMM;
- a constrained linear initializer followed by exact nonlinear Mata-GMM for
  EASI and GEASI, including the `0.5 p'Ap` implicit-utility correction;
- Marshallian, Hicksian, expenditure, demographic, income, quantity, value, and
  quality elasticities;
- local and global curvature-constrained EASI-GMM plus sample-average
  delta-method elasticity inference;
- two-stage budgeting and third-stage quality decomposition, with PPML value
  equations retaining zero commodity expenditures and optional clustered inference;
- model-order, precommitment, demographic, endogeneity, overidentification, and
  demand-regularity diagnostics;
- joint and instrument-conditional first-stage F tests, partial R-squared, and
  same-sample instrument-set sensitivity estimates.

The empirical pipeline does not run GEASI for this cross-sectional application.
The generic package retains the optional interface for other research designs.

The supplied survey does not contain a documented household sampling weight;
reported estimates are household-unweighted and use village-year clustered
inference.

When SY participation equations are active, the analytic structural covariance
conditions on their estimated coefficients. Applications with material censoring
should bootstrap the whole estimator at the sampling-cluster level. This caveat
matters for the source-specific systems: the total, purchase, omit-self, and own
systems activate different participation equations. The omission-bias test
therefore bootstraps the complete two-system workflow by village.

Prices passed to `fooddem, prices()` and expenditure passed to
`expenditure()` must be in logs. See `help fooddem` after adding `ado/` to the
Stata adopath. [`ADO_REFERENCE.md`](ADO_REFERENCE.md) documents every public
and internal ado file, its interface, outputs, diagnostics, and current
identification limits.

## Main outputs

- `table_descriptives*.csv`, `table_price_*.csv`: data and price diagnostics.
- `table_province_year_support.csv`: province-wave support and fixed-effect identification.
- `table_purchase_coverage.csv`: observed household purchase-value coverage.
- `model_selection_gmm_onestep.csv`: AIDS/QUAIDS/EASI functional-form comparison.
- `selected_model_*`: preferred clustered two-step GMM estimates and tests.
- `model_selection_nlsur_cf.csv`: NLSUR/control-function robustness.
- `income_elasticity_*`: overall, income-decile, and demographic distributions.
- `instrument_*`: excluded-instrument relevance and EASI(1) sensitivity results.
- `source_*`: source-corrected prices, total/purchase/own diagnostic systems,
  elasticity comparisons, curvature projection/constrained reestimation, and
  omission-bias bootstrap.
- `fruit_*`: seven-category fruit weights/prices, price-identification audit,
  functional-form selection, and formally comparable fruit elasticity results.

Household-level DTA files and estimation objects are intentionally ignored by
Git. Version-controlled CSV results contain aggregates, not household IDs.

See `METHODS_AND_AUDIT.md` for the audit trail. `RESULTS_SUMMARY.md` and
`MAIN_RESULTS_PRESENTATION.md` are retained as explicitly marked legacy
baselines. The authoritative current report is
[`HICKSIAN_SELFCONSUMPTION_CORRECTION.md`](HICKSIAN_SELFCONSUMPTION_CORRECTION.md),
which contains the corrected price-sign, own-consumption, curvature, and
omission-bias analysis. The focused follow-up is
[`FRUIT_SIGNIFICANCE_DIAGNOSTICS.md`](FRUIT_SIGNIFICANCE_DIAGNOSTICS.md).

The preferred total-consumption system can be re-estimated with a village-year
cluster bootstrap using `code/14_total_bootstrap.do`; `code/15_finalize_total_bootstrap.do`
post-processes the saved replicates into `outputs/total_bootstrap_elasticities.csv`
and `outputs/total_bootstrap_tests.csv`. The bootstrap keeps total consumption,
community prices, SY participation correction, expenditure IVs, and local
Slutsky curvature fixed as the main specification.
