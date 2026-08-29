# 2023 benchmark internal domain review

This memo records the internal technical review that follows the numerical
balancing gate.  It is an auditable model-development check, not a claim of
independent peer review.

## Cotton chain

CASM-World keeps seed cotton as a satellite ginning activity and cotton lint
(`CTN`) as the traded model product.  The lint output coefficient is 0.3352
tonnes per tonne of seed cotton.  FAO technical studies report ginning
outturns of roughly 0.33--0.40 and FAOSTAT distinguishes cotton lint,
cottonseed and seed-cotton observations.  Of 85 active 2023 ginning accounts,
84 have a seed-cotton activity observation.  The only inferred activity is
below one tonne, the configured materiality threshold.  It therefore cannot
alter reported regional or global quantities at the displayed precision.

## Dairy chain

Raw milk is converted jointly through milk-fat and solids-not-fat identities.
The central coefficients in `config/balancing.yaml` were checked against the
composition ranges in the Codex standards for milk powders, butter, cheese
and whey powders.  They are technical central coefficients, not claims about
each country's recipe.  Yogurt, cream, casein, lactose, other dairy products
and manufacturing losses are outside the 31-product system; their solids are
retained in a nonnegative, explicit `unmodelled_dairy_solids` account rather
than deleted or forced into a modelled product.  Its global share is tested
against the frozen 30% ceiling and reported in the benchmark audit JSON.

## Cross-dataset reconciliation

The weighted projection closes all 31 world markets and every country-level
processing identity simultaneously.  Large percentage changes attached to
near-zero anchors are not used alone as a rejection criterion.  The audit
therefore reports the median and 95th percentile relative change, exact mass
residuals, inferred cells and all cell-level adjustments.  The adjustment CSV
is retained as a publication supplement; no missing observation is silently
changed to zero.

Internal review completion permits scenario analysis.  External replication,
coefficient sensitivity tests and comparison with independent projections
remain requirements of the paper, not preconditions for executing the model.
