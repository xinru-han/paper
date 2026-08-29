# CASM-World 2050 build status

This page separates computational validity from publication readiness. A
`PASS` means the stated invariant is machine checked. It does not mean that a
parameter prior is an econometric estimate, that uncertainty analysis is
complete, or that the current central run is fit for publication.

## Decision

**Current V2 central classification: computationally valid diagnostic
conditional scenario, not publication baseline.**

The annual model, reporting, nutrition, and GHG chain is internally
consistent. The frozen publication validator reports 18 of 20 gates passed.
Because publication readiness is conjunctive, either failed gate is sufficient
to withhold the publication-baseline label.

| Gate | Status | Machine-readable evidence | Interpretation or remaining limitation |
|---|---|---|---|
| Clean independent project and dependency boundary | PASS | `README.md`; `config/model.yaml` | No legacy CASM, SILK, or bilateral-trade code is imported. |
| Immutable raw-data source contract | PASS | 27/27 snapshots verified by `casm_world.paths` | Credentials are not stored; raw snapshots remain external to this rebuild's generated-data layer. |
| Twenty-five-source aggregation | PASS | `config/territory_aggregation.yaml`; geography and reporting tests | The 25 sources are never solved as accounts. Frozen 2023 source shares are used only to recover reporting geography. |
| Complete 31-product concordance | PASS | benchmark and concordance tests | DDG and several composites are constructed rather than direct one-to-one FAOSTAT series. |
| Balanced 2023 benchmark | PASS | `data/processed/benchmark_equilibrium_report_2023.json` | Constrained balancing changes noisy anchors; tiny anchors can have large relative adjustments. |
| Rice, sugar, cotton, oilseed, and dairy identities | PASS | processing-identity tests; `BENCHMARK_DOMAIN_REVIEW.md` | Physical accounting passes; some processing economics remain model assumptions. |
| V1 process-output shifter defect | FIXED / SUPERSEDED | simulation tests; `PLAUSIBILITY_AUDIT.md` | V1 files and price diagnostics are historical only and are not the current result set. |
| V2 behavioral parameter table | PASS | `casm_world_parameters_v2_2023.csv`; `casm_world_parameters_v2_report.json` | 5,983 × 72, SHA-256 `8b9d53bb…b90d698`; contains central/low/high responses. Parameters are transformed priors and declared author rules, not 5,983 independent estimates. |
| SSP population and GDP paths | PASS | 27,020 rows; `ssp_driver_coverage_report.json` | Source gaps use explicit aggregation or fallback routes recorded in the audit. |
| TFP and real exchange-rate paths | PASS | respective path CSV and JSON reports | Scenario extensions are conditional assumptions, not forecasts with confidence intervals. |
| Tariff paths through 2050 | PASS | 837,620 rows; `tariff_paths_report.json` | Every 2036--2050 value is held at its 2035 scenario value; missing later values are never silently set to zero. |
| Climate-yield shocks | PASS | 837,620 rows; `climate_yield_paths_report.json` | Direct effects cover four major crops; exposure coefficients remain spatially coarse. |
| V2 central joint equilibrium | COMPUTATIONAL PASS | `outputs/ssp_run_report.json` | 140/140 equilibria converged; one world price per commodity; no bilateral allocation. |
| 2023 replication and annual accounting | PASS | `outputs/publication_validation_gates.csv` | Maximum market residual `5.0618e-15`; maximum accounting residual `1.4211e-14 Mt`; base price, quantity, and process gates pass. |
| Overall 2050 price band | FAIL | `price_range_2050` | SSP5 `ODA = 4.429`, above the declared upper bound 4.0. |
| Central 2050 price band | FAIL | `price_central_band_2050` | `93.548%` lie in `[0.5, 2.0]`, below the required 95%. |
| Essential-food 2050 price band | PASS | `essential_food_prices_2050` | All 45 SSP-product checks lie in `[0.5, 2.5]`. |
| Annual price smoothness | PASS | `annual_price_change` | Maximum annual absolute log change is `0.09922`, below 0.20. |
| OECD--FAO 2024--2035 holdout | PASS | `outputs/oecd_fao_holdout_2024_2035.csv` | All preregistered thresholds pass: sign 85.19%, median error 10.04 pp, p90 21.28 pp, World MAE 5.79 pp, World signs 9/9. |
| Reporting groups and territory geography | PASS | 251,720 rows; `ssp_group_analysis_report.json` | A zero-anchor source has zero separately recovered future share because it has no independent SSP path. |
| Nutrition post-solution | COMPUTATIONAL PASS | `ssp_nutrition_audit_2023_2050.json` | Covers the edible part of the 31-product basket, not a complete diet or adequacy diagnosis. It inherits the diagnostic status of the equilibrium. |
| Agricultural GHG post-solution | COMPUTATIONAL PASS | `ssp_ghg_audit_2023_2050.json` | Farm-gate production attribution with frozen 2023 intensities, not a dynamic mitigation or life-cycle model. It inherits the diagnostic status of the equilibrium. |
| Nitrogen module | NOT IN SCOPE | `nitrogen_module_enabled: false` | Removed at the user's instruction. |
| Parameter-response sensitivity | COMPUTATIONAL PASS / MATERIAL | `outputs/sensitivity/v2_sensitivity_report.json` | All 420 low/central/high annual solutions converge and calibrate exactly. Low response triggers the frozen screen: SSP3 sugar is 31.21% from central; high response does not trigger. |
| Post-2035 TFP sensitivity | COMPUTATIONAL PASS | `outputs/sensitivity/v2_sensitivity_report.json` | All 280 slow/fast annual solutions converge, equal central exactly through 2035, and remain below the frozen materiality thresholds. |
| Demand-CES structural sensitivity | COMPUTATIONAL PASS | `outputs/sensitivity/v2_sensitivity_report.json` | All 140 annual solutions converge. The frozen screen does not trigger, but SSP5 ODA falls from 4.429 to 1.887 and the diagnostic price bands pass, demonstrating material model-form relevance outside the nine-food screen. |
| Shared crop-resource / land-allocation response | NOT IMPLEMENTED | listed in `V2_SPECIFICATION.md` and `PLAUSIBILITY_AUDIT.md` | Simultaneous commodity expansion remains conditional on independent supply curves. |
| China 13-primary-product trade reversal | STRUCTURAL RISK | current V2 country-product results | SSP2 changes from `183.37 Mt` net imports in 2023 to `173.15 Mt` net exports in 2050. This is a non-overlapping physical basket and residual identity, not a value trade forecast; no shared crop-resource block constrains simultaneous expansion. |
| Paper analysis build | DIAGNOSTIC ONLY | `python3 scripts/build_paper_analysis.py --diagnostic-draft` | The explicit switch marks generated tables, figures, and report as not publication baseline; the default strict build refuses while a gate is failed. |
| Publication validation | FAIL (18/20) | `outputs/publication_validation_report.json` | Current files must not be presented as the paper's publication baseline. |

## OECD--FAO holdout detail

The preregistered aggregate thresholds all pass, but regional diagnostics are
still heterogeneous and must be reported rather than hidden:

| Area | 2024--2035 mean absolute error | Sign agreement |
|---|---:|---:|
| World | 5.79 percentage points | 100% (9/9) |
| China | 16.89 percentage points | 100% (9/9) |
| EU27 | 10.52 percentage points | 55.6% (5/9) |

Passing the aggregate OECD gate therefore does not establish uniformly strong
regional predictive performance.

## Current V2 diagnostic outputs

- `outputs/ssp_results_country_product_2023_2050.csv`: 837,620
  country-product observations;
- `outputs/ssp_results_group_product_2023_2050.csv`: 251,720
  reporting-group observations;
- `outputs/ssp_group_product_change_2023_2050.csv`: 8,990 base-to-2050
  comparisons;
- `outputs/ssp_nutrition_world_2023_2050.csv` and
  `outputs/ssp_ghg_world_2023_2050.csv`: post-solution world paths;
- `outputs/publication_validation_gates.csv`: all 20 frozen gate decisions;
- `outputs/publication_validation_report.json`: decision, price and OECD
  metrics, and input hashes.
- `outputs/sensitivity/v2_sensitivity_report.json`: six-variant, 840-solution
  convergence, calibration, provenance and materiality results.

All current files are internally aligned to the V2 central result SHA chain.
They are conditional diagnostic outputs. Do not describe them as formal
publication projections while either price gate remains failed.

## Publication promotion rule

Promotion requires, at minimum:

1. all frozen validation gates pass without silently changing thresholds;
2. parameter-response, post-2035 TFP, and demand-CES sensitivities remain
   reported, including the adverse low-response result and the CES dairy-price
   diagnosis;
3. the effect of the unimplemented shared crop-resource mechanism is either
   implemented and tested or explicitly bounded and accepted as a central
   model limitation;
4. every group, nutrition, GHG, table, figure, and manuscript output is
   regenerated from the same accepted equilibrium SHA chain.

Until then, the scientifically accurate label is **computationally valid
diagnostic conditional scenario**.
