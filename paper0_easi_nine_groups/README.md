# Nine-group rural food demand system

This project estimates AIDS, QUAIDS, and cross-sectional EASI demand systems
for the user-specified nine-group classification. Bootstrap is deliberately
omitted in this exploratory run.

## Literal nine-group definition

1. Staples and processed staples
2. Pulses and pulse products
3. Livestock and poultry meat (unprocessed)
4. Eggs and egg products
5. Dairy
6. Aquatic foods and aquatic products
7. Oils and fats
8. Vegetables and vegetable products
9. Nuts/seeds and fruit products

The definition is applied literally. Fresh fruit, processed livestock meat,
condiments, tobacco, alcohol, sugar, and tea are outside the conditional
system. Expenditure and budget shares are therefore calculated only over the
nine included groups, so adding-up is exact within this conditional system.

## Methods

- Total quantity includes purchases consumed, own production consumed, and
  gifts consumed.
- Physically impossible group-level quantities and five-MAD upper tails in
  total and own-produced per-capita quantities are excluded from the preferred
  sample; raw values are not overwritten.
- Community prices use comparable representative products from the village
  questionnaire. Missing village prices follow the donor hierarchy: direct
  village, town-year median, nearest priced village in the same county-year,
  county-year median, province-year median, then year median.
- Shonkwiler-Yen selection terms address zero consumption.
- Log income and inverse income form the excluded-instrument set. AIDS, QUAIDS,
  and EASI are compared by NLSUR with an expenditure control function; the
  selected EASI order is also estimated by one- and two-step GMM-IV as a
  diagnostic sensitivity analysis.
- Province fixed effects are retained and the survey-year indicator is dropped:
  in these data the province-wave partition makes the two sets exactly collinear.
- All systems impose adding-up, homogeneity, and Slutsky symmetry. No curvature
  reparameterisation and no GEASI are used. High-dimensional exact AIDS/QUAIDS
  GMM needs an analytic Jacobian before it is practical for this nine-good run.
- The EASI GMM-IV fits converge numerically but are rejected for interpretation:
  the two-step Hansen test rejects and both weighting schemes produce almost no
  positive fitted-share vectors. The primary exploratory results are therefore
  the comparable NLSUR control-function estimates.

## Run

```bash
/usr/local/stata17/stata-se -b do code/00_run_all.do
```

The item-level household DTA must first be produced by
`paper0_item_level_food_descriptives/code/build_item_descriptives.py`.

## Main outputs

- `outputs/model_selection.csv`
- `outputs/easi_nlsur_reference_analytic.csv`
- `outputs/elasticities_reference_all_models.csv`
- `outputs/elasticity_distributions_all_models.csv`
- `outputs/own_price_and_expenditure_elasticities.csv`
- `outputs/easi_gmm_rejected_elasticities.csv`
- `outputs/gmm_diagnostic_comparison.csv`
- `outputs/tests_all_models.csv`
- `outputs/regularity_all_models.csv`
- `outputs/NINE_GROUP_MODEL_RESULTS.md`
- `outputs/NINE_GROUP_MODEL_RESULTS.txt`

Household-level analysis data and Stata estimates remain local and are excluded
from Git. Aggregate results, code, and audit tables are versioned.
