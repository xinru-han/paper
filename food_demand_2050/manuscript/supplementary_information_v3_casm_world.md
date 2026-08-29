# Supplementary Information

## China's dietary transition redistributes agricultural production and farm-gate emissions across global economies

Shengnan Huang, Xinru Han\*

**Version:** 29 August 2026  
**Status:** accompanies the CASM-World V2 diagnostic manuscript; not a final publication baseline.

This Supplementary Information documents the intervention boundary, scenario grid, China and global incidence, model-form sensitivity, partial nutrition diagnostic and computational/publication-readiness audits. Machine-readable tables contain all products, pathways, SSPs, economies and reporting groups; the compact tables below are selected views of those files.

## Supplementary Note 1 | Study design and boundary

### Source pathways

| Paper label | Source China-CASM scenario | Interpretation in this study |
|---|---|---|
| BASELINE | BS | Same-SSP reference with no additional China preference multiplier |
| PTS | A1 | Preference-driven dietary transition |
| MTS | C1 | Moderate transition |
| CGS | B1 | Partial composite-guideline transition in model-covered products |

All source paths use the medium-population, medium-urbanisation China scenario. The model experiment isolates pathway composition from the demographic variants analysed in the earlier China-only study. Population, GDP and other macro conditions instead enter through SSP1-SSP5 in CASM-World.

### Product mapping

| CASM-World product(s) | Source China product(s) | Multiplier rule |
|---|---|---|
| RIC | RICE | Rice ratio |
| WHE | WHEA | Wheat ratio |
| CRN | MAIZ | Maize ratio |
| OCG | SORG, BARL, OTGR | Ratio of summed quantities |
| SBS | SOYS | Edible-soybean ratio |
| SBO, NBO, RBO, OTO | SOYO, RAPO, GRDO | Common ratio of total edible oils |
| SUG | SUGA | Sugar ratio |
| BFV | CATM | Bovine-meat ratio; sheep/goat meat excluded |
| PRK | PIGM | Pigmeat ratio |
| PLM | CHKM | Poultry-meat ratio |
| BUT, CHE, NDM, FMK, WDM, ODA | MILK | Common dairy-food ratio |

The ratio for an aggregate is calculated after summing source quantities, not as a mean of commodity ratios. The mapped file contains 2,128 rows: four paths by 19 products by 28 years. Every 2023 multiplier equals one.

### Excluded source foods

| Source food | Exclusion reason | Consequence |
|---|---|---|
| Tubers | No world-model tuber market | CGS staple substitution is incomplete |
| Vegetables | No world-model vegetable market | No global horticultural supply response |
| Fruits | No world-model fruit market | No global horticultural supply response |
| Eggs | No world-model egg market | Animal-food substitution is incomplete |
| Aquatic foods | No world-model aquatic market | Fish/aquaculture and feed effects are absent |
| Sheep/goat meat | No corresponding meat market | Red-meat contraction is incomplete |

These exclusions prevent full-diet, health, land, water and lifecycle conclusions. They are not imputed.

## Supplementary Note 2 | Equilibrium intervention

Let `s` denote food's balanced 2023 share of final use, `m` the China pathway-to-baseline food multiplier and `Zmacro` the SSP population-income shifter. The total China final-demand shifter is

`Ztotal = Zmacro * [(1 - s) + s*m]`,

and the within-product food share after the shift is

`s_new = s*m / [(1 - s) + s*m]`.

This construction has three audited properties:

1. `m = 1` exactly preserves the SSP macro shifter and benchmark food share.
2. The non-food anchor is unchanged when the food multiplier changes.
3. The derived food share remains in `[0,1]` for all model inputs.

The intervention is applied only to the mainland China model account. World prices then clear every product and feed back into supply and demand in all accounts, including China. The original China-CASM run used to construct `m` is not re-solved with those world prices.

## Supplementary Table 1 | Run matrix

| Run family | SSPs | Years | Diet paths | Equilibria |
|---|---|---|---:|---:|
| Main annual | SSP2 | 2023-2050 annual | 4 | 112 |
| Main endpoint | SSP1, SSP3, SSP4, SSP5 | 2023 and 2050 | 4 | 32 |
| Response sensitivity | SSP2 | 2050 | 4 paths x 3 response sets | 12 |
| Demand-form sensitivity | SSP2 | 2050 | 4 | 4 |
| **Total** | | | | **160** |

The four 2023 solutions in every SSP share the same diet multiplier and reproduce the common benchmark. All effects are paired to BASELINE within the same SSP, year and sensitivity variant.

## Supplementary Table 2 | Selected CGS world-price effects across SSPs, 2050

Values are percentage changes relative to the baseline diet path in the same SSP.

| SSP | Pigmeat | Rice | Fluid milk | Whole-milk powder |
|---|---:|---:|---:|---:|
| SSP1 | -46.82 | -15.06 | +19.11 | +23.21 |
| SSP2 | -46.23 | -14.60 | +18.65 | +22.57 |
| SSP3 | -46.17 | -14.51 | +18.77 | +22.65 |
| SSP4 | -46.29 | -14.32 | +18.86 | +22.51 |
| SSP5 | -46.46 | -15.00 | +18.95 | +23.11 |

The narrow cross-SSP range applies to paired effects under the same central independent-product model. It does not represent total uncertainty.

## Supplementary Table 3 | Mainland China product effects under CGS, SSP2 2050

| Product | Food-demand change (Mt) | Production change (Mt) | Net-import-balance change (Mt) |
|---|---:|---:|---:|
| Rice | -62.96 | -15.94 | -46.65 |
| Wheat | -35.62 | -5.28 | -29.73 |
| Bovine meat | -9.82 | -0.88 | -8.95 |
| Pigmeat | -51.58 | -19.24 | -32.34 |
| Poultry meat | +11.85 | +1.58 | +10.27 |
| Fluid milk | +53.91 | +5.17 | +48.74 |
| Raw milk | 0.00 | +2.75 | +3.08 |

`Production` includes primary or processing supply as appropriate to the product. Raw milk is an input and fluid milk is processed output; they must not be summed. Net imports equal total demand minus total production and are not bilateral trade flows. Some baseline net balances are structurally implausible, so only the paired direction and conditional magnitude are reported.

## Supplementary Table 4 | Non-overlapping primary-production incidence under CGS, SSP2 2050

| Reporting group | Change (Mt) | Change (%) |
|---|---:|---:|
| World | -70.97 | -0.75 |
| Mainland China | -37.38 | -2.59 |
| Africa | -1.28 | -0.28 |
| Americas | -4.93 | -0.17 |
| Asia | -59.41 | -1.33 |
| Europe | -4.96 | -0.35 |
| Oceania | -0.39 | -0.25 |
| High income | -7.68 | -0.32 |
| Upper middle income | -45.72 | -1.09 |
| Lower middle income | -17.61 | -0.66 |
| Low income | -0.04 | -0.03 |
| Developing economies | -63.37 | -0.91 |

The basket contains rice, wheat, maize, other coarse grains, soybeans, sunflower seed, rapeseed, sugar cane, sugar beet, bovine meat, pigmeat, poultry meat and raw milk. It excludes processed outputs to avoid double counting. Summing tonnes across products is a physical diagnostic, not a value or welfare measure.

## Supplementary Table 5 | Selected economy-product production responses outside China, CGS, SSP2 2050

| Economy | Product | Change (Mt) | Change (%) |
|---|---|---:|---:|
| India | Fluid milk | +14.47 | +6.97 |
| India | Rice | -13.58 | -4.67 |
| India | Raw milk | +10.80 | +3.14 |
| United States | Raw milk | +4.11 | +3.64 |
| Indonesia | Rice | -4.10 | -5.14 |
| Viet Nam | Rice | -3.61 | -4.67 |
| India | Wheat | -3.58 | -2.12 |
| Pakistan | Fluid milk | +3.33 | +6.23 |
| Russian Federation | Wheat | -3.30 | -2.45 |
| Brazil | Fluid milk | +3.25 | +8.13 |
| United States | Pigmeat | -2.86 | -23.37 |
| Brazil | Pigmeat | -1.41 | -22.44 |
| Brazil | Bovine meat | -1.03 | -6.78 |
| United States | Poultry meat | +0.96 | +4.11 |

Rows identify exposure in the central model, not welfare gains or losses. Dairy input and output rows are adjacent physical stages and cannot be added.

## Supplementary Table 6 | Attributed biological farm-gate GHG effects, SSP2 2050

| Reporting group | PTS change (Mt CO2e) | MTS change (Mt CO2e) | CGS change (Mt CO2e) | CGS change (%) |
|---|---:|---:|---:|---:|
| World | +23.11 | -160.82 | -254.54 | -4.04 |
| Mainland China | +2.13 | -29.14 | -47.30 | -5.41 |
| Outside China | +20.98 | -131.69 | -207.24 | n/a |
| Africa | +2.77 | -11.82 | -18.21 | -2.73 |
| Americas | +10.77 | -60.89 | -97.56 | -5.50 |
| Asia | +4.06 | -67.92 | -106.75 | -3.48 |
| Europe | +4.65 | -15.80 | -25.08 | -3.88 |
| Oceania | +0.86 | -4.40 | -6.95 | -4.79 |
| High income | +8.42 | -35.34 | -56.49 | -4.52 |
| Upper middle income | +9.68 | -84.60 | -135.47 | -5.11 |
| Lower middle income | +3.12 | -35.55 | -54.63 | -2.74 |
| Low income | +1.60 | -4.05 | -5.95 | -1.69 |
| Developing economies | +14.39 | -124.20 | -196.04 | -3.92 |

CGS effects across SSP1-SSP5 are:

| SSP | Baseline (Mt CO2e) | Change (Mt CO2e) | Change (%) |
|---|---:|---:|---:|
| SSP1 | 6,431.00 | -266.13 | -4.14 |
| SSP2 | 6,295.78 | -254.54 | -4.04 |
| SSP3 | 6,037.50 | -244.16 | -4.04 |
| SSP4 | 6,215.81 | -251.04 | -4.04 |
| SSP5 | 6,642.46 | -273.38 | -4.12 |

The boundary uses frozen 2023 production-attributed biological farm-gate factors. It excludes lifecycle emissions and land-use change.

## Supplementary Table 7 | Price-model sensitivity for CGS, SSP2 2050

| Product | Low response (%) | Central (%) | High response (%) | Five-nest demand (%) | Evaluated range |
|---|---:|---:|---:|---:|---:|
| Pigmeat | -46.23 | -46.23 | -46.23 | -21.19 | -46.23 to -21.19 |
| Rice | -15.80 | -14.60 | -13.00 | -5.05 | -15.80 to -5.05 |
| Bovine meat | -12.07 | -12.07 | -12.07 | -9.17 | -12.07 to -9.17 |
| Soybean oil | -17.31 | -16.60 | -15.88 | -9.27 | -17.31 to -9.27 |
| Poultry meat | +8.38 | +8.38 | +8.38 | -10.84 | -10.84 to +8.38 |
| Fluid milk | +19.66 | +18.65 | +17.91 | +23.45 | +17.91 to +23.45 |
| Whole-milk powder | +24.08 | +22.57 | +21.38 | +24.91 | +21.38 to +24.91 |

Low/high response sets do not vary every livestock parameter, explaining identical entries for some meat products. The five-nest result is the primary model-form sensitivity. Because it changes the poultry sign and materially narrows the pigmeat effect, central independent-product estimates are not presented as structurally invariant.

## Supplementary Table 8 | Model-covered nutrition diagnostic, SSP2 2050

| Geography | Path | Food demand (Mt) | Energy (kcal cap-1 d-1) | Protein (g cap-1 d-1) | Fat (g cap-1 d-1) | Energy change vs baseline |
|---|---|---:|---:|---:|---:|---:|
| China | BASELINE | 538.26 | 2,668.68 | 89.50 | 81.34 | 0.00 |
| China | PTS | 541.89 | 2,650.66 | 91.36 | 86.55 | -18.02 |
| China | MTS | 475.80 | 2,216.04 | 76.51 | 65.12 | -452.64 |
| China | CGS | 440.02 | 1,914.69 | 68.06 | 52.42 | -753.99 |
| World | BASELINE | 3,464.77 | 2,399.20 | 65.81 | 75.24 | 0.00 |
| World | PTS | 3,465.50 | 2,395.91 | 65.95 | 75.76 | -3.29 |
| World | MTS | 3,411.59 | 2,347.96 | 64.35 | 73.54 | -51.24 |
| World | CGS | 3,382.21 | 2,314.79 | 63.44 | 72.27 | -84.41 |

These values cover only edible products present in the 31-product world model. The low China CGS value mainly exposes missing vegetables, fruit, eggs, aquatic foods, tubers and sheep/goat meat. It must not be interpreted as total energy intake, dietary adequacy, undernutrition risk or health effect.

## Supplementary Note 3 | Numerical audit

### Counterfactual run

- Main equilibria: 144 of 144 converged.
- Sensitivity equilibria: 16 of 16 converged.
- Main country-product observations: 861,552.
- Maximum main relative market residual: `5.253e-15`.
- Maximum sensitivity relative market residual: `7.253e-15`.
- Maximum accounting residual: `1.421e-14 Mt`.
- Maximum 2023 benchmark error: zero.

### Post-solution analysis

- Reporting-group observations: 258,912.
- Country-product contrasts: 89,745.
- Group-product contrasts: 26,970.
- Economy GHG observations: 27,792.
- Group GHG observations: 8,352.
- Maximum world-versus-economy GHG conservation error: `9.09e-13 Mt CO2e`.
- Positive food demand assigned to non-food products: zero.

### Underlying model publication gates

The full rebuilt CASM-World V2 baseline passes 18 of 20 frozen publication gates. It passes exact benchmark replication, accounting, all 45 essential-food price checks and aggregate OECD-FAO holdout thresholds. It fails:

1. `price_range_2050`: SSP5 other dairy (`ODA`) has an index of 4.429, above the declared upper limit of 4.0.
2. `price_central_band_2050`: 93.548% of 2050 prices lie in `[0.5,2.0]`, below the declared 95% threshold.

The model also lacks a shared crop-resource or land-allocation mechanism. Under baseline SSP2, China's non-overlapping primary basket changes from net imports in 2023 to net-export pressure in 2050. This is a structural-risk diagnostic and is why neither baseline trade levels nor land effects are used as headline results.

### Promotion conditions

Before journal submission, the evidence package should be promoted only after:

1. both frozen price gates pass without post-hoc threshold changes;
2. a shared crop-resource mechanism is implemented or its effect is bounded by a pre-specified sensitivity;
3. the complete counterfactual chain is rerun from the accepted baseline hash;
4. all tables, figures, claims and manuscript numbers are regenerated from that same chain;
5. model-covered language and the demand-form sensitivity remain in the main text.

## Supplementary Note 4 | Machine-readable evidence

| Evidence | Repository path |
|---|---|
| Mapped China paths | `model/casm_world_rebuild_study/inputs/china_diet_paths_mapped.csv` |
| Mapping audit | `model/casm_world_rebuild_study/inputs/china_diet_paths_report.json` |
| Run report | `results/casm_world_rebuild/counterfactual_run_report.json` |
| Analysis report | `results/casm_world_rebuild/analysis_report.json` |
| World prices | `results/casm_world_rebuild/counterfactual_world_prices.csv` |
| Country-product results | `results/casm_world_rebuild/counterfactual_country_product.csv.gz` |
| Country contrasts | `results/casm_world_rebuild/country_contrasts_2050.csv.gz` |
| Group contrasts | `results/casm_world_rebuild/group_contrasts_2050.csv.gz` |
| GHG by economy/group | `results/casm_world_rebuild/ghg_country.csv.gz`, `ghg_group.csv.gz` |
| Sensitivity prices | `results/casm_world_rebuild/sensitivity_world_prices_2050.csv` |
| Publication tables | `results/casm_world_rebuild/tables/` |
| Figures | `figures/casm_world_rebuild/` |
| Claim registry | `results/casm_world_rebuild/claims_registry.csv` |

