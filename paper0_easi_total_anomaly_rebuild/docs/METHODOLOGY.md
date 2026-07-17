# Rebuild methodology

## Why the previous sign repair is not used

The demand system is estimated without a Cholesky parameterization, local or
global curvature constraint, or post-estimation projection. A negative
semidefinite Slutsky matrix is a theoretical regularity condition, but imposing
it to change an empirical own-price sign prevents the data audit from revealing
whether the sign is driven by quantity or price measurement. Curvature remains
a reported diagnostic only.

## Quantity reconstruction

The item modules distinguish:

- purchased food directly consumed;
- a residual purchase fallback when acquisition balance components are
  available;
- typical purchase frequency times amount when direct consumption is missing;
- self-produced food consumed;
- food received from others.

All quantities are monthlyized using the module reference period. Total
consumption equals the sum of the three sources and this identity is asserted
for every household and food group.

## Quantity anomaly rules

Six generous physical ceilings are expressed in jin per person per month:

| Food | Ceiling | Equivalent kg/person/day |
|---|---:|---:|
| Staples | 90 | 1.50 |
| Beans | 30 | 0.50 |
| Meat | 60 | 1.00 |
| Edible oil | 21 | 0.35 |
| Vegetables | 150 | 2.50 |
| Fruit | 120 | 2.00 |

The second screen uses the positive-quantity distribution within
province-year-food-source cells. A province-year median and scaled MAD are used
when at least ten positive observations exist; otherwise the same-year positive
distribution is used. A quantity is removed only when it exceeds both five
scaled MADs and one-half of its physical ceiling. This combined rule prevents a
narrow local distribution from labeling plausible consumption as erroneous.

The preferred sample screens total consumption and self-production. Purchase
and gift components are also screened in a stricter sensitivity sample because
they are already contained in total consumption. Results at 4.5 MAD, 6 MAD, and
the positive p99 are retained.

## Community price construction

The village questionnaire is the price source. Household unit values are never
inserted into the demand-system price.

1. Invalid quotes at or below zero or above 200 yuan/jin are removed.
2. High/low entries recorded in reverse order are reordered.
3. Repeated questionnaire-row copies of the same price question are reduced
   first. Independent support is counted by outlet, not by raw column count.
4. Representative-product quotes are aggregated across outlets by the median.
5. Representative prices are screened on logs within province-year using five
   scaled MADs. A lower-tail value is retained when at least two villages in
   the same town-year lie within a 25 percent log band around the town median.
6. A representative price supported by only one outlet receives an additional
   one-sided three-scaled-MAD check. It is removed only when neither the local
   town price nor the independently reported, calibrated broad-category price
   corroborates it within a 25 percent log band. No category-specific minimum
   price or percentile floor is imposed.
7. Missing village prices are filled from the same-town representative median,
   the nearest representative village in the same county, the county
   representative median, then the province representative median.
8. Donor prices are always direct representative quotes. Imputed observations
   never become donors.

The questionnaire's broad high-price and low-price category quotes are retained
as an audit series. They can corroborate a weak representative quote but are
not themselves used in the main price or donor pool. They can represent
different qualities and, in the oil group, produced values above 60 yuan/jin
that had almost zero correlation with household purchase unit values. Allowing
those midpoints into the donor pool generated the positive compensated oil
own-price response.

This design follows the price-identification logic emphasized by Hovhannisyan
et al. (2025) and Deaton (1988): households in a sufficiently local geographic
market face a common price, while household unit values also contain quality,
quantity, store-format, and reporting components. Here actual village market
quotes are available, so household unit values remain validation data rather
than price replacements.

## Estimation and inference

AIDS, QUAIDS, and EASI candidates use the same preferred sample, demographic
controls, Shonkwiler-Yen zero-consumption treatment, excluded income
instruments, and village-clustered covariance. Functional form is selected by
nested Engel-order tests within model families and BIC across nonnested
families.

If AIDS is selected, that selection is reported as the preferred functional
form. EASI(1) remains the targeted nonlinear robustness model for the
own-price-sign investigation because the rejected correction was applied to the
EASI-GMM specification.

Main EASI inference for expenditure, Marshallian own-price, and Hicksian
own-price elasticities uses a 199-request village-cluster bootstrap. The bootstrap
reestimates the unrestricted system from the converged full-sample solution
with two-step GMM in every successful replicate and calculates
reference-point elasticities directly from each
replicate. It does not use a delta-method standard error or alter an elasticity
sign.

Household elasticity distributions are additionally reported on a common
interior support where all fitted shares exceed 0.5 percent. This is a
denominator-support diagnostic, not a curvature or sign restriction.
