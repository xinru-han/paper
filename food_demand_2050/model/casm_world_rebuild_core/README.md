# CASM-World 2050 — clean rebuild

This directory contains a clean rebuild of CASM-World. It does not import
code, workbooks, parameters, scenarios, or results from the legacy
`casm_world`, `SILK Model`, or bilateral-trade projects.

## Current decision

The current V2 central run is a **computationally valid diagnostic conditional
scenario, not a publication baseline**. All 140 annual scenario equilibria
converge and all accounting identities close, but the frozen publication
validation accepts only 18 of 20 gates. The two failed gates concern the 2050
price distribution:

- SSP5 `ODA` reaches `4.429`, outside the declared all-product band
  `[0.25, 4.0]`;
- `93.548%` of 2050 scenario-product prices are within `[0.5, 2.0]`, below
  the preregistered `95%` requirement.

All 45 essential-food price checks pass. All preregistered OECD--FAO holdout
thresholds also pass: full-sample sign agreement is `85.19%`, median absolute
error is `10.04` percentage points, p90 error is `21.28` points, World mean
absolute error is `5.79` points, and World sign agreement is 9 of 9. These
successes do not override either failed publication gate. See
[`docs/BUILD_STATUS.md`](docs/BUILD_STATUS.md) and the machine-readable
[`publication_validation_report.json`](outputs/publication_validation_report.json).

## Frozen scope

- benchmark year: 2023;
- annual sequence of conditional SSP equilibria: 2024--2050;
- non-spatial partial equilibrium with one world reference price per traded
  commodity;
- 193 solved economy accounts and 31 products;
- no bilateral trade flows, partner substitution, or SILK dependency;
- no global `ROW` balancing entity;
- the 25 small or scope-ambiguous source territories identified in the audit
  are not independent solution units; each is assigned exactly once to a
  named country or regional account, while source geography is retained for
  reporting;
- nutrition and agricultural GHG are post-solution modules; there is no
  nitrogen-balance module.

This is a sequence of annual equilibria under SSP drivers and declared model
assumptions. It is not an unconditional forecast and should not be described
as a recursive forecast.

## Data policy

Only immutable, hash-verified raw snapshots from the preceding data audit may
be reused. Reuse of raw files is not reuse of the old model: concordances,
benchmark construction, parameters, equations, scenarios, and outputs were
rebuilt here. Credentials are never stored in the project.

## Product and processing system

The system contains 31 products:

`RIC WHE CRN OCG SBS SBO SBM NBS NBO NBM RBS RBO RBM DDG ETH BDI OTO CTN SUG SCA SBE BFV PRK PLM MLK BUT CHE NDM FMK WDM ODA`.

Rice, sugar, cotton, oilseed crushing, and dairy use explicit processing
identities so raw and processed layers are not added twice. The process-output
supply-shifter bug found in the V1 audit has been repaired and covered by
tests. V1 results are retained only as historical diagnostics in
[`docs/PLAUSIBILITY_AUDIT.md`](docs/PLAUSIBILITY_AUDIT.md).

## V2 parameter and run contract

The central solution uses
[`casm_world_parameters_v2_2023.csv`](data/processed/casm_world_parameters_v2_2023.csv),
a complete `5,983 × 72` account-product parameter table. Its SHA-256 is
`8b9d53bbfd9ce6662cbafdd1599fa86f76d4c74d42476cd4debbd95f9b90d698`.
The table contains central, low-response, and high-response columns and uses
long-run total-production supply responses plus frozen 2023 use-share
composite final-demand responses. The adjacent
[`V2 parameter report`](data/processed/casm_world_parameters_v2_report.json)
records all transformations and provenance.

The V2 central diagnostic covers SSP1--SSP5 annually from 2023 through 2050:

- 5 scenarios × 28 years = 140 converged equilibria;
- 193 accounts × 31 products = 5,983 observations per equilibrium;
- 837,620 country-product observations in total;
- maximum relative world-market residual: `5.0618e-15`;
- maximum absolute accounting residual: `1.4211e-14 Mt`;
- no bilateral trade, SILK dependency, or nitrogen module.

Post-solution files report World, China mainland, the United States, EU27,
World Bank income classes, UN regions and subregions, least developed
countries, landlocked developing countries, small-island developing States,
Pacific islands, and a documented developing-economy group. Nutrition uses
the explicit edible `food_demand_mt` component; agricultural GHG uses
production and frozen 2023 intensities.

One material structural diagnostic remains: for a non-overlapping 13-primary-
product basket, SSP2 China changes from net imports of `183.37 Mt` in 2023 to
net exports of `173.15 Mt` in 2050. This is a residual physical balance, not a
value trade forecast. Because the model has independent product supply curves
and no shared crop-resource block, the reversal must be disclosed as a
structural risk, not promoted as a robust China trade conclusion.

## Reproduction commands

```bash
export PYTHONPATH="$PWD/src"
python3 -m casm_world.paths
python3 -m casm_world.benchmark
python3 -m casm_world.balancing
python3 -m casm_world.parameters
python3 -m casm_world.drivers
python3 -m casm_world.tfp
python3 -m casm_world.exchange_rates
python3 -m casm_world.policy
python3 -m casm_world.climate
python3 -m casm_world.simulation
python3 -m casm_world.analysis
python3 -m casm_world.scenario_nutrition
python3 -m casm_world.ghg --run-ssp
python3 -m casm_world.validation
python3 -m casm_world.sensitivity
python3 scripts/build_paper_analysis.py --diagnostic-draft
python3 -m pytest -q -p no:cacheprovider
```

`python3 -m casm_world.validation --require-passed` is the strict publication
gate and currently exits nonzero by design. The parameter-response,
post-2035 TFP, and demand-CES sensitivities are complete: all 840 annual
solutions converge and retain exact accounting closure. The low-response case
crosses the preregistered materiality screen because its SSP3 sugar price is
31.21% away from V2 central; the high-response, TFP-slow, TFP-fast and CES
cases remain below their respective major-food-price and primary-production
thresholds. A shared crop-resource or cross-commodity land-allocation block
has not been implemented, and sensitivity nutrition/GHG post-solutions have
not been generated. The explicit
`--diagnostic-draft` switch permits a watermarked diagnostic paper build; the
default paper builder correctly refuses to treat an 18/20 result as a
publication baseline.

Machine-readable diagnostic results are under [`outputs/`](outputs/). Do not
label them as the paper's central publication baseline until all frozen gates
and the declared sensitivity review have passed.
