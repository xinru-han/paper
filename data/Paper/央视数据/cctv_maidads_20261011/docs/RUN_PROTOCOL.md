# CCTV MAIDADS execution protocol

This new study uses only CCTV household purchase records, 2020-2022. It does
not reuse rural survey estimates. Outputs are point estimates and validation,
not bootstrap intervals or significance claims.

## Data and price commitments

- Eight groups: staples, oil, vegetables, fruit, pork, other meat, seafood, dairy.
- Nine groups split other meat into poultry/other meat and beef/lamb.
- A ten-group model requires an independent defensible nut price. Oil is not a
  nut-price proxy. No ten-group price elasticity is silently substituted.
- Positive spending with zero recorded volume is a purchase with unrecorded
  quantity. Purchase participation uses spending, never raw zero volume.
- Absent whole household-months are not filled as zero purchases. Quarter
  averages use recorded active months; complete-quarter sensitivity is separate.
- Price aggregation uses fixed observed-category weights. Conditional quantity
  equals covered per-proxy-person budget times share divided by a price index;
  it is not kilograms or total dietary intake.
- The baseline uses the last observed size-band proxy within each window.
  A separate per-month-size sensitivity divides each month's expenditure by
  that month's proxy before averaging; neither proxy is exact household size.
- Income and household size are reported intervals. Income reporting frequency
  is unverified. A conditional interval-lognormal projection is a maintained
  assumption, not an observed exact income series or a valid budget instrument.

## Statistical specifications

The native AIDADS/MAIDADS benchmark fits unconditional cell-mean purchase shares
on province-quarter-family type-income band-size band cells. Zero purchasers
remain in cell means. This is not a micro corner likelihood. Both alpha and
beta add to one; unlike the provincial GDP/outside-good model, all food beta
parameters cannot simultaneously be zero in a closed food-only budget.

The model comparison uses Gaussian concentrated quasi-likelihood on an
orthonormal basis of the K-1 dimensional share subspace. The same basis and
outcome scale are used for AIDS, QUAIDS, AIDADS and MAIDADS. Covariance parameters
are counted in descriptive QML AIC/BIC. These are not robust likelihood tests.

MAIDADS low and high commitment endpoints are estimated, not silently fixed to
zero. Weak endpoint identification, artificial bounds, utility-root failures,
nonstationarity and support failures must be disclosed. Numerical and economic
audits are not sampling inference or proofs of global optimality.

The separate translated-log corner extension changes the original interpretation
of positive minimum consumption quantities. It must first pass KKT, root,
monotonicity and Hicksian checks. Synthetic results are never labelled CCTV
estimates. Random preference integration is not resampling households.

## Validation and scenarios

Temporal holdout: train 2020-2021, evaluate 2022. Province validation: five fixed
whole-province folds on all 24 provinces. Price-basket weights and fitted input
transformations must be constructed only from the training data. All held-out
failures remain visible; no selective pooling of successful rows or folds.

Comparators include a training mean and a province-history persistence baseline.
Validation conditional on realized test prices is not an ex ante forecast.

Income-growth scenarios hold the baseline price and demographic composition
fixed. The first-stage log-budget projection converts proportional latent-income
growth into budget multipliers. Baseline observed budgets anchor the scenarios;
no missing household consumption or saving series is fabricated. Predictions
are first constructed for each positive-budget 2022 household, once per household,
using its observed annual monthly-equivalent budget, and then aggregated. Province
means are sample means, not probability-weighted population parameters. Scenario
ranges and alternative income distributions are not confidence intervals.

An unqualified native estimate can produce explicitly labelled diagnostic
scenarios, but not formal MAIDADS forecasts. Its source directory, score and
qualification flags are retained in every aggregate. Invalid household predictions
block complete province/family summaries; they are never silently dropped.

The separate restricted corner scenario applies a quarter-estimated purchase
kernel to each household's annual active-month average budget and fixed annual
price anchor. This cross-frequency use is an additional maintained assumption,
not an annually refitted model or inventory/recording-horizon model. Its
participation probabilities are conditional kernel probabilities, not the
probability of buying at least once over a year. The same caveat applies to
using a quarter-fitted native demand kernel with the annual budget anchor.

## Reproducibility

The source data remain local. Code, aggregate result files, logs and audits are
delivered in this directory. Household-level data and restricted original retail
exports are excluded from GitHub. Existing unrelated worktree changes are not
modified.
