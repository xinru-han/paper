# Native (M)AIDADS Run Status

2026-10-13 follow-up: the first-round softmax results below remain historical.
Natural-simplex MAIDADS now has qualified local points for the eight-good coarse
cells and elderly cells, both independently repeated with two starts. Preferred
directories are `maidads_8_coarse_simplex_multistart` (KKT 1.429e-6, N=5,733)
and `maidads_family_3_simplex_multistart` (KKT 9.044e-7, N=1,437).
See `docs/SIMPLEX_ENDPOINTS.md` and the current main report. This does not certify
global optimality, joint sampling inference, zero-purchase fit or predictive
validation. Individual annual-budget coverage remains incomplete; representative
mean-budget scenarios are separate aggregation sensitivities, not replacements.

Updated 2026-10-12. All estimator-agent Stata sessions have completed, timed out
or been explicitly interrupted and closed. No required estimator process is
left running. All real fits use CCTV cells; no rural-survey parameter estimates
or rural-survey results were used as starts or substitutes.

## Completed Real-Data Runs

| Output directory | N | Model | Physical box-projected score | Qualified |
| --- | ---: | --- | ---: | --- |
| maidads_8_warm | 14,676 | MAIDADS, 3 starts | 0.2659144 | No |
| aidads_8_warm | 14,676 | AIDADS, 3 starts | 0.2713082 | No |
| maidads_8_init100 | 14,676 | MAIDADS, 1 numerical-check start | 0.1585227 | No |
| maidads_8_tangent | 14,676 | MAIDADS, 3 tangent-search starts | 0.0883799 | No |
| maidads_8_year | 3,730 | MAIDADS, 3 starts | 0.0678567 | No |
| aidads_8_year | 3,730 | AIDADS, 3 starts | 0.0990317 | No |
| maidads_family_1_current | 5,194 | MAIDADS, 3 starts | 0.1106445 | No |
| maidads_family_2_current | 4,337 | MAIDADS, 3 starts | 0.0014850 | No |
| maidads_family_3_current | 1,437 | MAIDADS, 3 starts | 0.0000038 | No: 2 logit guards |
| maidads_family_4_current | 3,708 | MAIDADS, 3 starts | 0.1333584 | No |

The separately coordinated `maidads_8_coarse` sensitivity completed with 5,733
cells, score 0.0002677 and a high-end seafood-share logit guard; it is also
unqualified. Its minimum supernumerary share is 0.1676, illustrating that not
every failure is a near-zero-budget frontier problem.

Every completed directory retains natural/raw parameters, representative full
price matrices, cell predictions, elasticity distributions, candidate ledgers
and root/derivative/rank audits. `converged=0` is authoritative: attractive
representative elasticities or lower objective values do not override it.
The warm-eight-good directory remains the fixed source for the separately
labelled diagnostic scenario forecasts; tangent or numerical-check directories
are not silently substituted into those forecasts.

Do not compare AIC/BIC or objectives across different samples, family groups or
aggregation levels. The covariance parameter count is included in completed
working-model AIC/BIC; these values are not formal LR-test p-values.

## Interpretation

Several candidate paths approach the lowest observed covered-food budget,
where commitment-cost slack and supernumerary budgets are near numerical zero.
They fail finite-root/gradient/stationarity diagnostics. The warm-eight-good
elasticity file deliberately retains extreme observations: oil, pork and other
meat have maximum conditional-budget elasticities around 4.9e15 and cell means
around 3.35e11, despite moderate medians and representative responses. These
distributions must not be presented as validated economic estimates or hidden
by post-estimation winsorization. Near-cancellation at these frontiers also
limits numerical interpretation of their extreme elasticities.

Other candidate paths hit alpha/beta logit guards. Natural alpha/beta zeros
could be legitimate nonnegative-simplex economic boundaries; a finite logit
guard is not the corresponding natural-coordinate KKT solution. Neither this
guard nor the observed frontier paths prove global nonexistence, global
infima, model falsification or exclusion of as-yet-unfound interior solutions.
The defensible conclusion is that this round did not obtain a real-data,
complete-free-endpoint finite fit satisfying all stated qualification gates.

No bootstrap, elasticity standard errors, confidence intervals or p-values
were invented. Hicksian signs arise from the original expenditure function,
not a Cholesky curvature repair or a post-estimation sign filter; their signs
do not independently validate prices or data quality.

## Numerical Evidence

`synthetic_identified` passes with score 3.56e-6 and recovers free positive
delta/tau endpoints, omega and kappa from a utility range [-4,4]. The separate
`synthetic_identified_tangent` run also passes (score 3.38e-5) with essentially
the same recovered parameters. The weaker `synthetic_test` hits an omega guard
and correctly remains unqualified. Root-edge tests, the point-only eclass API
test and the independent native provincial-function verification are retained.
Successful synthetic recovery validates the implementation in that informative
design, not real-data identification or a guarantee of global optimization.

## Incomplete And Preserved Runs

`maidads_9_current` timed out at 30 minutes with exit code 124 before completing
any unrestricted start. Its preference initialization is retained but is not
a fitted nine-good result. Earlier pooled eight/nine-good and sequential-family
runs were explicitly stopped after approximately 30-35 minutes with exit code
130; completed raw candidates remain in their original directories. Their
individual RUN_STATUS files distinguish completed starts from unstarted or
interrupted starts. `maidads_8_firstpass_candidate1` merely finalizes one
already-completed first-pass candidate for audit, with convergence forced to
zero and source recorded; it does not supply the scenario forecasts.
