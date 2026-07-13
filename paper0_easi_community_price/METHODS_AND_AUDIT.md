# Methods and audit record

## Scope

The implementation follows the transferable checks emphasized by Hovhannisyan
et al. (2025): common spatial prices rather than uncorrected household unit
values, sequential Engel-rank tests, demographic tests, expenditure endogeneity,
theoretical regularity, and conditional versus unconditional elasticities for an
incomplete food system. This household cross-sectional application does not run
GEASI. The purchase/own/gift addendum and current results are documented in
`HICKSIAN_SELFCONSUMPTION_CORRECTION.md`.

## Identifier and merge audit

- Raw household observations: 3,565.
- Household ID: exact 14-character string; village ID: its first 12 characters.
- Merge key: `village_id data_year`.
- Exact household-to-price-table matches: 3,565; unmatched households: zero.
- Village-year keys absent from the village questionnaire are retained in the
  target universe and receive explicitly sourced geographic fallbacks.

No identifier is converted to floating point. This avoids precision loss for
long survey codes.

## Price audit

All main prices originate in the village questionnaire and are denominated in
yuan per jin. The representative-product and calibrated-midpoint components are
screened separately and again after combination. Fallback medians use only
directly observed donors, so there is no recursive imputation or accidental
household weighting.

Village coordinates are used only to select the nearest direct-price donor
within county-year. The POI files describe market access but do not contain
comparable food quotes, so they are not used to manufacture prices; they remain
available for later heterogeneity analysis of accessibility.

Across 361 village-year cells, the final prices have 132-236 unique values by
group. Their coefficients of variation range from about 0.33 to 0.72. See
`outputs/table_price_variation.csv` for exact values and
`outputs/price_quote_audit.csv` for every screening count.

The corrected unit-value validation correlations with direct community prices
are positive for all groups but not close to one. This is expected because raw
unit values combine market prices, household quality choice, measurement error,
and purchase timing. The main specification therefore does not substitute unit
values for community prices.

The within-market unit-value decomposition identifies spatial log-price
components only under a common intercept normalization. It is consequently a
relative-price validation series, not an independently observed absolute price
level. The directly quoted village prices supply the level used in all main
models.

## Household data audit

Four invalid household-size entries were survey identifiers rather than counts;
each had two observed roster members and was repaired to two. Eighteen households
had neither a valid reported size nor roster members and were dropped. The
remaining household-size range is 1-10, with a mean of 2.96.

The raw sex code is `0=female, 1=male`; this is also supported by the
sex-specific adult height distribution. The head is found from relationship code
1 across all eight roster slots, not assumed to be member 01. The final female
head share is about 9.2%; missing head sex has its own indicator.

The source notes leave major quantity/frequency errors unresolved. Declared
monthly limits in jin per person are 90, 30, 60, 21, 150, and 120. They correspond
to generous daily kilogram limits of 1.5, 0.5, 1.0, 0.35, 2.5, and 2.0. This
screen removes 313 households. Final analysis N is 3,234; the IV estimation
sample is 3,200 because 34 households have nonpositive or missing annual income.

No documented household sampling-weight variable is present in the delivered
survey files. Descriptive and structural estimates are therefore household
unweighted, with inference clustered by village-year. This is an explicit data
limitation rather than an implicit unit-weight assumption hidden in the code.

## Zero consumption

Consumption rates are 100%, 99.57%, 100%, 99.54%, 100%, and 100%. A probit with
an almost constant dependent variable cannot identify a Shonkwiler-Yen inverse
Mills coefficient. `fooddem` therefore sets participation probability to one and
the density correction to zero whenever the positive rate is at least 98%. This
is an explicit identification rule, not zero replacement or deletion.

The reusable command estimates the full Shonkwiler-Yen correction when a good
has enough zeros and positives. Commodity-value income equations use PPML so
zero values are retained in the third-stage quality decomposition. For an active
correction, stored probit coefficients are used to recompute participation
probabilities under every price, expenditure, and demographic counterfactual;
elasticities therefore include the extensive margin. The analytic demand-system
covariance conditions on the first-stage probits, so materially censored
applications should cluster-bootstrap the entire command. All six probits are
bypassed only in the legacy aggregate-quantity baseline. The source-reconstructed
total, purchase, omit-self, and own systems activate different SY equations; the
omission contrast therefore bootstraps the complete two-system workflow by village.

## Model choice and restrictions

All systems omit the sixth share equation and recover it exactly by adding-up.
Homogeneity and symmetry are imposed through the parameterization, rather than
through post-estimation coefficient edits. EASI order must be below the number
of goods. Household demographics and province effects enter each structural
share equation; they are not treated as excluded instruments. Survey wave is
exactly `province_2 + province_4 + province_5 + province_6` in this sample, since
no province is observed in both waves. A separate wave effect is therefore not
identified once province effects are included and is omitted rather than silently
dropped. `table_province_year_support.csv` documents this support pattern.

For AIDS and QUAIDS, demographic coefficients and the control-function residual
translate the intercept vector both in the budget shares and in the translog
price index. Their coefficients sum to zero across goods. Omitting the price-index
translation, as in a simple share-shifter regression, violates conditional
Slutsky symmetry even if the price matrix itself is symmetric. The synthetic
NLSUR tests cover this distinction explicitly.

EASI estimation constructs exact implicit real expenditure as
`y = x - w'p + 0.5 p'Ap`, matching the supplied Lewbel-Pendakur iteration code,
and instruments its powers in GMM. Counterfactual prediction cannot hold observed
shares fixed. `fooddem_p` therefore writes the scalar fixed-point condition as
an exact polynomial, obtains all roots, and follows the real root closest to
observed implicit utility for every price or expenditure perturbation. It stops
explicitly if no stable real branch exists. Elasticities use central numerical
derivatives.
Ordinary EASI is linear conditional on implicit real expenditure, so `fooddem`
uses a constrained matrix-GMM solution as a stable initializer and then optimizes
the exact nonlinear moments in Mata with a clustered sandwich covariance. The
test suite compares the final ordinary-EASI coefficients directly with Stata's
numerical `gmm` evaluator and verifies GEASI's identity-weight moments against
the generic evaluator. The same Mata optimizer handles GEASI's additional
nonlinearity from precommitments and discretionary expenditure.

The empirical sequence is:

1. Estimate AIDS, QUAIDS, and EASI orders 1-3 by common-sample one-step GMM.
2. Report joint tests of the QUAIDS quadratic term and each EASI highest-order term.
3. Select order sequentially inside each nested family, then use residual BIC
   for the nonnested AIDS-family versus EASI comparison.
4. Warm-start clustered two-step GMM at the selected one-step solution.
5. Repeat functional-form selection by NLSUR with a control-function residual.
6. Reconstruct purchase, own, and gift quantities; estimate total, purchase,
   omit-self, and diagnostic own-consumption systems.

The reusable package retains an optional GEASI interface for other applications,
and its synthetic tests verify the extra moment conditions. It is not invoked by
this empirical pipeline and has no output in the current results directory.

An identity-weight one-step J statistic is not labeled Hansen. Hansen's J is
reported only for efficient two-step GMM. A rejected overidentification or
regularity test is evidence against the empirical specification and is retained
in the output; it is not overridden by the theoretical parameter constraints.

Because the cluster-robust joint first-stage F is below ten, the pipeline also
re-estimates the selected EASI(1) specification on the identical sample with
log income alone, inverse income alone, and expenditure treated as exogenous.
`fooddem_firststage` reports the joint and instrument-conditional cluster-robust
F tests plus OLS partial R-squared values. These checks diagnose sensitivity;
they do not turn conventional GMM inference into weak-IV-robust inference.

## Incomplete-system elasticities

The demand-system expenditure elasticities are conditional on total expenditure
for these six food groups. The reduced form regresses log six-group expenditure
on log annual income, inverse annual income, demographics, and province. A wave
effect cannot be separated from province for the support pattern described above.
Quantity income elasticity equals conditional expenditure elasticity times the
food-expenditure income elasticity. Commodity-value income elasticity is from a
PPML reduced form for reconstructed household purchase expenditure, retaining
zero purchases. At household level, the residual value-minus-quantity elasticity
can also reflect a shift between own production and market sourcing, so it is
reported as a quality/sourcing margin rather than asserted to be pure quality.
Purchase coverage is reported by food group. Reduced-form and commodity-value
equations use village-year clustered inference. Results are summarized overall,
by income decile, and by demographic group.

## Reproducibility checks

- All six shares sum to one within `1e-8` before estimation.
- Prices are positive and constant within village-year.
- Price sources, quote screening, fallback levels, merge results, unit-value
  reconstruction, household demographics, quantity screening, and sample flow
  are exported as separate audit tables.
- `tests/test_fooddem.do` covers arbitrary-good estimation, adding-up,
  AIDS/QUAIDS/EASI selection, GMM/NLSUR, prediction, elasticities, unit-value
  recovery, zero-consumption handling, first-stage diagnostics, and income/quality
  decomposition.
