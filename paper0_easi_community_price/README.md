# Food demand systems with community prices

This is a clean Stata 17 pipeline for the 2023-2024 food-consumption survey. It
does not overwrite the legacy EASI files. The final system contains six groups:
staples, beans/bean products, meat, edible oil, vegetables, and fruit.

## Run

```stata
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_run_all.do"
```

`04_estimate_easi.do` estimates several nonlinear systems on the full sample
and can take tens of minutes. Stata SE 17 is licensed in the current container.
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
- Demand expenditure and shares use village community prices, not household
  unit values. Thus own production and zero purchases do not create artificial
  household prices.
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

`fooddem_uvprice` separately implements a unit-value robustness series following
the common-market price, demographic-quality, and quantity-effect decomposition.
Those recovered prices validate but do not replace questionnaire community
prices in the main models.

## Estimation package

The `ado/fooddem*.ado` package accepts any number of goods greater than two.
`fooddem` estimates AIDS, QUAIDS, polynomial EASI, or GEASI precommitments by
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
- two-stage budgeting and third-stage quality decomposition, with PPML value
  equations retaining zero commodity expenditures and optional clustered inference;
- model-order, precommitment, demographic, endogeneity, overidentification, and
  demand-regularity diagnostics;
- joint and instrument-conditional first-stage F tests, partial R-squared, and
  same-sample instrument-set sensitivity estimates.

The supplied survey does not contain a documented household sampling weight;
reported estimates are household-unweighted and use village-year clustered
inference.

When SY participation equations are active, the analytic structural covariance
conditions on their estimated coefficients. Applications with material censoring
should bootstrap the whole estimator at the sampling-cluster level. This caveat
does not affect the present six-group estimates because every participation
equation is bypassed under the declared 98% identification rule.

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
- `geasi_*`: precommitment robustness at the preferred EASI order.
- `model_selection_nlsur_cf.csv`: NLSUR/control-function robustness.
- `income_elasticity_*`: overall, income-decile, and demographic distributions.
- `instrument_*`: excluded-instrument relevance and EASI(1) sensitivity results.

Household-level DTA files and estimation objects are intentionally ignored by
Git. Version-controlled CSV results contain aggregates, not household IDs.

See `METHODS_AND_AUDIT.md` for the methodological decisions and unresolved
interpretive cautions, and `RESULTS_SUMMARY.md` for the current empirical run.
