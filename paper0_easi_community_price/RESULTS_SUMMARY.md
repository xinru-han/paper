# Current empirical results

These results are from the final Stata 17 run on 12 July 2026. Food groups are
staples, beans/bean products, meat, edible oil, vegetables, and fruit, in that
order. All inference is household-unweighted and clustered by village-year.

## Data and prices

- All 3,565 household records match a community-price village-year key exactly.
- Eighteen records without a valid household size are removed, followed by 313
  records exceeding declared physical quantity limits. The analysis sample is
  3,234; 3,200 have complete positive income instruments.
- The final price panel contains 361 village-year cells. Each of the six prices
  is positive and constant within a village-year.
- Own-village direct quotes cover 54.9%-83.3% of households depending on the
  group. Remaining prices use same-town direct medians, the nearest direct
  county village, county direct medians, and finally province direct medians.
  No imputed observation is reused as a donor.
- Corrected unit values are positively correlated with community prices, but
  the correlations range only from 0.156 to 0.495. This supports keeping unit
  values out of the main price vector.

## Model selection and tests

- Within the AIDS family, the QUAIDS quadratic terms are jointly insignificant
  (`p=0.174`), so the sequential test retains AIDS.
- EASI(2) estimates but cannot supply stable real counterfactual utility roots
  across the full sample (`return_code=430`). EASI(3) is empirically unstable, with a very
  large residual sum of squares. The sequential EASI choice is therefore EASI(1).
- Among the valid family choices, one-step residual BIC favors EASI(1):
  `-62,707.3` versus `-62,412.3` for AIDS. This residual BIC is a nonnested
  selection diagnostic, not a formal GMM likelihood-ratio test.
- The preferred clustered two-step EASI(1) has `N=3,200`, Hansen
  `J=25.522`, `df=20`, and `p=0.182`.
- Core demographics are jointly significant (`p=9.77e-6`).
- The cluster-robust excluded-instrument first-stage statistic is `F=7.90`
  (`p=0.000439`). Its value below the conventional 10 benchmark is a material
  weak-instrument warning even though the instruments are jointly significant.
- GEASI precommitments are jointly indistinguishable from zero (`p=1.000`) and
  have very large standard errors. They are not used as the main specification.
- The NLSUR/control-function comparison selects AIDS by BIC. The joint control-
  function test rejects expenditure exogeneity (`p=0.000320`), supporting an
  endogenous-expenditure treatment but not resolving the IV-strength warning.

## Elasticities

Mean conditional expenditure elasticities from two-step EASI(1) are 0.531,
0.744, 1.401, 0.588, 0.621, and 1.363. Their household medians are 0.646,
0.884, 1.280, 0.726, 0.752, and 1.237. Means can be sensitive to observations
with very small fitted shares; the exported file therefore includes the
distribution standard deviation and p10/p50/p90 as well as the valid count.

The mean income elasticity of total six-group food expenditure is 0.082. Mean
income quantity elasticities by group are 0.044, 0.061, 0.116, 0.048, 0.051,
and 0.111. The corresponding value-minus-quantity quality/sourcing margins are
0.013, 0.071, -0.009, 0.213, 0.123, and 0.083. Purchase-value coverage ranges
from 62.5% for edible oil to 95.9% for staples, so these last margins should not
be interpreted as pure quality effects.

The `std_dev` field in elasticity files is cross-household dispersion, not a
delta-method parameter standard error. Coefficient tables use clustered standard
errors; elasticity inference should use a full village-year cluster bootstrap.

## Regularity and limitations

- Adding-up and numerical Slutsky symmetry pass. Symmetry errors are
  `2.40e-10` for the preferred GMM model and `1.54e-14` for NLSUR.
- Global curvature fails: the maximum Slutsky eigenvalues are 0.00635 and
  0.00868. Only 69.2% and 69.8% of valid own Hicksian elasticities are negative.
- Positive fitted-share rates are 94.4% for GMM and 98.4% for NLSUR. These
  empirical regularity failures are retained rather than hidden by trimming.
- No documented survey weight is available. Province and survey wave are
  perfectly confounded, so province effects are retained and a separate wave
  effect is not identified.
- Consumption is at least 99.54% positive for every group. SY participation
  equations are consequently bypassed under the declared 98% rule; zeros are
  neither replaced nor used to fit nearly unidentified probits.

See the CSV files in `outputs/` for full parameters, elasticity matrices,
distributions, price audits, and tests.
