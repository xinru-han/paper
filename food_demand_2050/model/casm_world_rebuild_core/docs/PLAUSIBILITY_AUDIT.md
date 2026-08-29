# CASM-World SSP Economic-Plausibility Audit

> **Superseded V1 historical diagnostic.** The body of this document is
> intentionally preserved as the audit record that motivated the V2 repair
> and re-parameterisation. Its V1 prices, China quantities, residuals, file
> state, and rerun instructions describe that historical snapshot; they must
> not be read as current V2 results.

## Current V2 status (2026-08-29)

- The process-output supply-shifter defect identified below remains repaired
  and test-covered.
- V2 replaces the V1 parameter semantics with a complete 5,983 × 72 table:
  [`casm_world_parameters_v2_2023.csv`](../data/processed/casm_world_parameters_v2_2023.csv),
  SHA-256
  `8b9d53bbfd9ce6662cbafdd1599fa86f76d4c74d42476cd4debbd95f9b90d698`.
- The full V2 central chain has been regenerated: SSP1--SSP5, 2023--2050,
  140 annual equilibria, 193 accounts, 31 products, and 837,620
  country-product rows. The maximum market residual is `5.0618e-15` and the
  maximum accounting residual is `1.4211e-14 Mt`.
- The frozen publication validator passes 18 of 20 gates. The failed gates
  are `price_range_2050` (SSP5 `ODA = 4.429`, above 4.0) and
  `price_central_band_2050` (`93.548%` in `[0.5, 2.0]`, below 95%). All 45
  essential-food price checks and all preregistered OECD--FAO thresholds pass.
- The OECD overlap remains regionally uneven despite passing the aggregate
  gates: 2024--2035 mean absolute errors are 5.79 percentage points for World,
  16.89 for China, and 10.52 for EU27; sign agreement is 100%, 100%, and 55.6%,
  respectively.
- A non-overlapping 13-primary-product SSP2 China basket changes from net
  imports of `183.37 Mt` in 2023 to net exports of `173.15 Mt` in 2050. This
  residual physical balance is a structural-risk diagnostic, not a value
  trade forecast.
- Parameter-response, post-2035 TFP, and demand-CES sensitivities are complete:
  all 840 annual solutions converge with maximum market and accounting
  residuals of `5.0618e-15` and `1.4211e-14 Mt`. Low response triggers the
  frozen screen through a 31.21% SSP3 sugar-price deviation; the other four
  noncentral cases do not trigger. The CES case reduces SSP5 ODA from 4.429 to
  1.887, showing that the failed dairy-price gates are model-form sensitive.
  A shared crop-resource or cross-commodity land-allocation mechanism remains
  unimplemented, and sensitivity nutrition/GHG post-solutions are not part of
  this runner.

Accordingly, the current V2 central result is a **computationally valid
diagnostic conditional scenario, not a publication baseline**. The live
decision record is [`BUILD_STATUS.md`](BUILD_STATUS.md); the machine-readable
decision is
[`publication_validation_report.json`](../outputs/publication_validation_report.json).

---

Date: 2026-08-29  
Scope: formal 2023--2050 SSP quantity and price solutions, with detailed checks of cotton, sugar, oilseed chains, other vegetable oils, dairy, and China's net-trade reversal.  
Decision: **the current formal SSP files are not a publication baseline**. One implementation bug has been fixed in code, but the formal files have deliberately not been overwritten pending a documented response/sensitivity design for the remaining economic outliers.

## 1. Executive finding

The model is numerically stable and accounting-consistent, but several markets are economically weakly identified. The extreme paths are not caused by failed convergence, a tonne/Mt conversion, a GDP/population unit error, the post-2035 tariff rule, or a solver bound. They arise mainly because modest exogenous supply-demand gaps are divided by very low effective price responsiveness, with additional amplification from rigid processing structures.

There was also one unambiguous implementation bug. Process outputs had zero primary supply by construction, while annual TFP/climate shifters were applied only to primary supply. Consequently, configured supply shifters were dead for process-only products; cotton lint was the clearest case because its seed-cotton input is outside the 31-product boundary. The minimal general repair is now implemented in [`simulation.py`](../src/casm_world/simulation.py#L94): each process activity inherits the output-coefficient-weighted geometric mean of its products' annual supply shifters. The shifter is applied when constructing each annual solve at [`simulation.py`](../src/casm_world/simulation.py#L409).

The repair changes SSP2 cotton's world price index as follows:

| Year | Before repair | After repair, diagnostic only |
|---:|---:|---:|
| 2023 | 1.000 | 1.000 |
| 2035 | 4.027 | 0.821 |
| 2050 | 12.174 | 0.301 |

The sign reversal confirms that the dead shifter was material. The repaired 2050 decline of 69.9% is still too large to adopt without sensitivity analysis: cotton's global effective own-price slope is only 0.0814, so a roughly 10% excess-supply gap at unit price requires a very large price adjustment.

The remaining headline outliers in SSP2 after the repair are unchanged: RBS 0.0725, NBS 0.1192, OTO 2.248, SUG 3.315, FMK 3.544 and BUT 2.957 in 2050. They should be treated as specification diagnostics, not publishable central projections.

## 2. What the model actually solves

For primary supply and final demand in economy \(r\), product \(i\), and year \(t\), the implemented equations are:

\[
Q^S_{rit}=Q^S_{ri,2023}\,A_{rit}\,(P_{it}W_{rit})^{\epsilon^S_{ri}},
\]

\[
Q^D_{rit}=Q^D_{ri,2023}\,B_{rit}\,(P_{it}W_{rit})^{\epsilon^D_{ri}},
\]

where

\[
A_{rit}=TFP_{rt}^{\alpha_i}\,ClimateYield_{rit}, \qquad
B_{rit}=Population_{rt}\,(GDPpc_{rt})^{\eta_{ri}},
\]

and \(W\) is the real-exchange-rate and tariff pass-through wedge. These equations are visible at [`simulation.py`](../src/casm_world/simulation.py#L378) and [`linked_equilibrium.py`](../src/casm_world/linked_equilibrium.py#L155).

A process \(j\) uses a fixed physical input/output recipe and has activity

\[
X_{rjt}=X_{rj,2023}\,Z_{rjt}
\exp\{\epsilon^X_{rj}[\ln P^{out}_{rjt}-\ln P^{in}_{rjt}]\}.
\]

The output and input signals are coefficient-weighted geometric price indices; see [`linked_equilibrium.py`](../src/casm_world/linked_equilibrium.py#L172). Process elasticities are currently derived from output-product supply elasticities, not independently estimated processing-margin or capacity elasticities; see [`simulation.py`](../src/casm_world/simulation.py#L75).

Every product has one world price and regional net imports are calculated residually as demand minus production. There is no bilateral trade, transport-cost, trade-inertia, land-allocation, feed-resource, or cross-commodity supply block. Process output products are explicitly removed from primary supply at [`system.py`](../src/casm_world/system.py#L70), and the processing recipes reproduce the 2023 physical benchmark exactly at [`system.py`](../src/casm_world/system.py#L197).

## 3. Quantitative diagnosis of the extreme markets

For each product, define the unit-price exogenous gap

\[
g_i=\ln[S_i(P=1)/D_i(P=1)].
\]

A positive value means excess supply at the 2023 relative price. The local derivative \(J_{ii}=\partial\ln(S_i/D_i)/\partial\ln P_i\) measures effective price responsiveness. When cross-market processing effects are absent, \(\ln P_i\simeq-g_i/J_{ii}\). The following values come from an in-memory SSP2 2050 solve after the process-shifter repair; no formal output file was overwritten.

| Product | 2050 price | Unit-price gap `g` | Own derivative `Jii` | Main cause | Classification |
|---|---:|---:|---:|---|---|
| CTN | 0.301 | +0.0977 | 0.0814 | repaired TFP shifter now creates modest excess supply, magnified by very low cotton supply and demand elasticities | bug repaired; residual parameter sensitivity |
| NBS | 0.119 | +0.2187 | 0.0977 | TFP-driven seed supply grows faster than final/crush demand; crush margin response is only about 0.054 | unstable specification, not unit bug |
| RBS | 0.0725 | +0.2567 | 0.0984 | same mechanism as NBS, with a larger exogenous gap | unstable specification, not unit bug |
| OTO | 2.248 | -0.2000 | 0.2468 | final-demand shifter 1.408 versus direct-supply shifter 1.153; TFP exponent is only 0.5 | conditional assumption result |
| SUG | 3.315 | -0.3397 | 0.2490 | demand grows faster than fixed-yield refinery activity; low margin response and falling cane/beet prices require a large sugar margin | processing-specification sensitivity |
| FMK | 3.544 | -0.5004 | 0.4256 | all six dairy products are tied to each country's fixed 2023 output mix while their demands grow differently | rigid joint-product specification |
| BUT | 2.957 | -0.4901 | 0.2054 | same dairy joint-product mechanism | rigid joint-product specification |

### 3.1 Cotton

Before the repair, cotton ginning had no modelled input and no annual activity shifter. Its activity could respond only to lint's own price with a base-activity-weighted elasticity of 0.0415. The supply block intentionally sets CTN primary supply to zero, and cotton ginning is created with no modelled input at [`system.py`](../src/casm_world/system.py#L126). Thus the fibre TFP exponent in [`simulation.yaml`](../config/simulation.yaml#L13) could not affect cotton output.

After the repair, the SSP2 2050 cotton-activity shifter is 1.352 when weighted by 2023 ginning activity. The new result reproduces 2023 exactly, but an effective own-price slope of 0.0814 converts a 9.8 log-percentage-point unit-price supply surplus into a price index of 0.301. This is an elasticity/TFP interaction and must be tested against documented alternative elasticities and TFP paths.

### 3.2 Sunflower and rapeseed

The NBS and RBS supply elasticities are almost entirely at the configured lower bound: their 2023-supply-weighted values are 0.04290 and 0.04289. The corresponding process elasticities, mechanically inherited from output supply elasticities, are about 0.0535 and 0.0533. At SSP2 2050 unit prices, supply exceeds total demand by only about 24% for NBS and 29% for RBS in level terms, but the effective own slopes are only about 0.098.

The price collapse is therefore an economically ill-conditioned response to a modest quantity gap. It is not a failed solve. Higher output-oil prices and very low input-seed prices jointly create the large crushing margin needed for activity to rise only 13.5% for sunflower and 14.7% for rapeseed. The current process elasticity is not a documented crushing-capacity or margin elasticity, so these prices cannot be defended as central forecasts without re-parameterisation or a high/central/low process-response design.

### 3.3 Sugar

At unit prices, SSP2 2050 sugar has a 28.8% level shortage (log gap -0.340). Final sugar demand's global shifter is about 1.402. Raw cane and beet supplies receive full agricultural TFP and have unit-price supply shifters around 1.32--1.35 globally, but refinery activity has no independent technology/capacity trend because processed-crop output has a zero TFP exponent. With refinery margin elasticities around 0.17--0.18, sugar must rise while cane and beet fall to induce only 27--31% more country-level processing activity.

The physical conversion identities are correct; the questionable element is the economic response of refining capacity and margins. SUG 3.315 is a conditional shadow-price result, not evidence of a coding or mass-unit error.

### 3.4 Other vegetable oils

OTO is not linked to an input process. Its direct supply receives \(TFP^{0.5}\), while demand receives population and income growth. In SSP2 2050, the global unit-price supply and demand shifters are 1.153 and 1.408, respectively. With an effective own response of 0.247, the analytical independent-market calculation gives \(\exp(0.200/0.247)=2.25\), exactly matching the solve. The result is internally correct conditional on the 0.5 TFP exponent and elasticities, but those assumptions require sensitivity testing because OTO aggregates many heterogeneous oils.

### 3.5 Dairy

The model uses one dairy activity per country, consumes raw milk, and supplies BUT/CHE/NDM/FMK/WDM/ODA in fixed country-specific 2023 physical proportions; see [`system.py`](../src/casm_world/system.py#L154). This preserves milk-fat and non-fat-solids accounting, but it does not allow the product mix to transform when relative demands change. Different dairy demands are therefore reconciled through large relative shadow-price movements: SSP2 FMK +254%, BUT +196%, WDM +92%, but CHE -14% by 2050.

This is not a mass-balance defect. It is a missing transformation/substitution margin. The accounting identities should be retained while allowing a calibrated CET-style product-mix response or another fat/SNF-conserving allocation mechanism.

## 4. China's production growth and trade reversal

### 4.1 What drives it

China's estimated agricultural TFP annual log trend is 0.016584 in SSP2, extrapolated without taper from 2023 to 2050. The path equation is a constant exponential trend at [`tfp.py`](../src/casm_world/tfp.py#L85). This gives a 2050 TFP index of 1.565. The same country TFP shifter is applied one-for-one to each crop, oilseed, livestock and raw-milk primary supply when the commodity-class exponent is 1.0.

For SSP2 China in 2050:

| Product | Supply shifter before price | Price-response factor | Production change | Demand change | Net imports 2023 -> 2050, Mt |
|---|---:|---:|---:|---:|---:|
| RIC | 1.537 | 1.006 | +54.7% | +7.2% | +13.9 -> -80.6 |
| WHE | 1.513 | 1.005 | +52.1% | +7.3% | +3.5 -> -62.7 |
| CRN | 1.501 | 1.026 | +54.1% | +5.8% | +29.8 -> -106.6 |
| OCG | 1.565 | 1.033 | +61.7% | +5.2% | +17.4 -> +12.8 |
| SBS | 1.538 | 0.982 | +51.0% | +9.5% | +101.0 -> +102.4 |
| PRK | 1.565 | 0.962 | +50.5% | +29.8% | +3.3 -> -7.5 |
| PLM | 1.565 | 1.049 | +64.1% | +21.9% | +2.5 -> -7.3 |
| MLK | 1.565 | 1.043 | +63.2% | +48.1% | -0.1 -> -7.0 |

The reversal is not primarily caused by prices: the cereal price-response factors are only 1.005--1.033. It is driven by the untapered, one-for-one TFP supply shift while population falls to 0.916 of its 2023 level and GDP per capita raises demand only through relatively low income elasticities.

Across a non-overlapping 13-primary-product diagnostic basket (RIC, WHE, CRN, OCG, SBS, NBS, RBS, SCA, SBE, BFV, PRK, PLM, MLK), SSP2 China changes from production 932.2 Mt, demand 1115.5 Mt and net imports +183.4 Mt in 2023 to production 1436.9 Mt, demand 1253.9 Mt and net imports -183.0 Mt in 2050. Production rises 54.1% while demand rises 12.4%. All five SSPs reverse this basket, with production growth of 41.0--61.7%.

### 4.2 Why it is not yet a defensible trade forecast

The model contains independent own-price supply curves and no shared land, feed, water, herd, or other resource constraint. Applying the same sector-wide TFP growth to every product can expand all products simultaneously and therefore can overstate aggregate output. It also has no cross-price allocation response. The core independent own-price form is documented in [`equilibrium.py`](../src/casm_world/equilibrium.py#L7), while the one-for-one commodity supply shift is constructed at [`simulation.py`](../src/casm_world/simulation.py#L390).

Regional net imports are a residual identity, not a separately estimated trade equation. With one world price and no bilateral block, a country can move from importer to exporter without a calibrated trade-capacity or inertia term. The sign reversal is therefore a model outcome conditional on supply and demand curves, not direct evidence about future Chinese trade policy or comparative advantage.

Finally, summing physical tonnes across unrelated products is not a value trade balance. Summing all 31 products also double-counts raw inputs and processed outputs. The paper should report product-level net imports and, if a basket is needed, use a non-overlapping basket valued at fixed 2023 prices. It must not label an all-product tonne sum as China's agricultural trade balance.

## 5. Overlapping comparison with OECD--FAO 2026--2035

The local official snapshot is [`oecd_fao_outlook_2026_2035_selected_production.csv`](../data/external/oecd_fao_outlook_2026_2035_selected_production.csv). It contains the OECD SDMX dataflow `OECD.TAD.ATM:DSD_AGR@DF_OUTLOOK_2026_2035(1.1)`, production measure `QP`, and tonnes with unit multiplier 3. Comparison uses 2024--2035 percentage growth, not 2023 levels, to reduce benchmark-year volatility. Rice levels are not yet harmonised: CASM RIC is explicitly paddy-equivalent, while the roughly 1.4 CASM/OECD level ratio indicates a basis mismatch whose exact OECD convention must be confirmed from the official metadata before any level comparison. Rice level ratios are therefore not interpreted here.

For nine mapped products, mean absolute CASM--OECD growth differences are 5.7 percentage points for World, 17.5 for China, and 10.4 for EU27. Selected China results are:

| Product | CASM SSP2 2024--2035 | OECD--FAO 2024--2035 | Difference, pp |
|---|---:|---:|---:|
| WHE | +20.3% | +1.3% | +19.0 |
| CRN | +20.9% | +9.3% | +11.6 |
| OCG | +22.4% | +5.7% | +16.6 |
| CTN, after repair | +19.2% | +5.3% | +13.9 |
| BFV | +26.7% | +11.9% | +14.8 |
| PRK | +20.4% | +2.4% | +18.1 |
| PLM | +23.9% | +10.5% | +13.4 |
| SBS | +19.4% | +48.6% | -29.2 |

The close 2024 level ratios for most non-rice products (generally about 0.91--1.08 for China) argue against a broad tonne/Mt conversion error. The growth comparison instead points to an overly strong, insufficiently differentiated Chinese supply trend. World growth is much closer to OECD for wheat, coarse grains, cotton, poultry and soybeans, suggesting that country composition and country TFP treatment, rather than the global benchmark total alone, are the main issue.

## 6. Numerical and unit checks

The following checks passed:

- Full test suite after the repair: **114 passed in 93.85 seconds**.
- SSP2 annual 2023--2050 diagnostic after the repair: maximum relative market residual `1.60e-15`; maximum function evaluations in any year `5`.
- Five-SSP diagnostic at 2023/2035/2050: maximum relative market residual `4.54e-14`; maximum accounting residual `1.42e-14 Mt`.
- SSP2 2050 log-price Jacobian singular-value condition number: about `20.1`. This is not a singular numerical system, although several product equations have economically low slopes.
- Largest SSP2 annual absolute log-price change among the audited outliers: `0.113` for RBS. Paths are smooth; NBS, RBS, OTO, SUG and FMK are monotonic. Cotton changes direction once near the benchmark and then declines smoothly.
- After the repair, the five-SSP 2050 price range is 0.0475--4.686, corresponding to log prices about -3.05 to +1.54. The solver bounds are +/-7 in [`simulation.yaml`](../config/simulation.yaml#L29), so no audited price is bound-constrained.
- SSP2 real-exchange-rate/tariff local price wedges are modest (roughly 0.90--1.12 across the audited products), and SSP2 tariffs remain at their reference path. They cannot explain 7--14-fold price changes.
- The post-2035 tariff hold is explicit in [`policy.yaml`](../config/policy.yaml#L23); no missing tariff is silently set to zero.
- Population, GDP and GDP-per-capita identities are internally consistent. SSP2 world 2023--2050 ratios are approximately 1.198, 2.039 and 1.702, respectively; China ratios are 0.916, 1.992 and 2.175. These are plausible magnitudes and not a million/billion unit mismatch.

## 7. Required publication-baseline response

### Gate A -- retain the implementation repair

Keep the new process supply-shifter pass-through and its tests at [`test_simulation.py`](../tests/test_simulation.py#L17). Require exact 2023 reproduction for every process and price index. Do not revert to the pre-repair cotton result.

### Gate B -- pre-specify, then run, an elasticity sensitivity matrix

Do not choose elasticities merely to force prices into a preferred range. Freeze documented central, low-response and high-response parameter sets before viewing final scenario results. At minimum vary:

1. primary supply and final-demand price elasticities;
2. process margin/capacity elasticities independently of output supply elasticities;
3. dairy output-transformation elasticities while retaining fat and non-fat-solids identities.

The diagnostic slopes show the required materiality. A 1% exogenous quantity-gap change induces roughly 12.3%, 10.2%, 10.2% and 4.1% price changes locally for CTN, NBS, RBS and OTO, respectively. Merely doubling all relevant response elasticities would approximately halve log-price changes; it would not by itself eliminate every outlier. For example, moving RBS from 0.0725 to 0.5 with the same exogenous gap would require about 3.8 times the current effective response. Such a change needs external parameter evidence, not an ex-post adjustment.

### Gate C -- pre-specify TFP alternatives

The current TFP path extrapolates a 2013--2023 log trend unchanged for 27 years. Run at least these declared alternatives:

- `TFP_CONSTANT_TREND`: current implementation;
- `TFP_TAPER_AFTER_2035`: country trend declines linearly toward a documented long-run regional/global rate or zero by 2050;
- `TFP_SHRUNK_LONG_RUN`: stronger shrinkage toward a regional long-run rate;
- commodity supply-shift exponents of 0.5, 0.75 and 1.0 where empirical product-specific productivity is unavailable.

Report China's 2023--2035 results against OECD--FAO before accepting any 2050 TFP variant. The comparison should be a validation diagnostic, not a calibration target hidden from the paper.

### Gate D -- add shared-resource or cross-commodity supply response

For a defensible central China result, introduce at least one transparent shared-resource mechanism. Preferred options are a land/feed/resource constraint with cross-price allocation, or a CET supply-allocation block whose elasticities and benchmark shares are explicit. A simpler aggregate cap may be used only as a labelled sensitivity, not silently as the central model. This is necessary because applying sector-wide TFP independently to every commodity is the principal driver of simultaneous 40--74% Chinese production increases.

### Gate E -- revise processing economics while preserving physical identities

- Estimate or document separate crushing/refining activity elasticities; do not infer them mechanically from product supply elasticities.
- Add explicit processing technology/capacity shifters where justified, with a no-double-counting rule relative to agricultural TFP.
- Replace the fixed dairy output mix with a fat/SNF-conserving transformation response.
- Review OTO's 0.5 TFP exponent and, if it remains, defend it as an aggregate of unmodelled oil crops.

### Gate F -- establish reporting rules

- Current V1 extreme price and China trade results are **diagnostic/sensitivity-only**.
- Report net trade by product. Any basket must be non-overlapping and valued at fixed base prices; do not sum all 31 physical tonnes.
- State that net trade is residual in a non-bilateral one-world-price model.
- Show 2024--2035 overlap with OECD--FAO, then 2035--2050 extension separately.
- Publish scenario ranges only after the TFP, elasticity and processing sensitivity gates pass.

## 8. Rerun dependency order

Formal outputs were intentionally not overwritten after the code repair. Once the publication response design is frozen, rerun in this order:

1. full unit/integration tests;
2. annual five-SSP equilibrium outputs;
3. convergence and price-plausibility gates;
4. country/group reporting;
5. nutrition and GHG post-solutions;
6. OECD--FAO overlap tables and manuscript figures.

Because the current files under `outputs/` were generated before the cotton repair, the equilibrium, group, nutrition and GHG files are mutually consistent with the old implementation but **must not be cited as final results**. Overwriting only the equilibrium files would make downstream post-solutions stale; the full chain must be regenerated together.

## 9. Bottom line

The accounting framework and annual solver are working. Cotton contained a real shifter-propagation bug, now repaired and test-covered. The oilseed, sugar, OTO and dairy extremes are reproducible conditional outcomes of low effective elasticities and rigid process equations, not numerical or unit mistakes. China's trade reversal is primarily the consequence of untapered country TFP applied independently to many commodities without shared-resource competition. Until the pre-specified elasticity, TFP, resource-allocation and processing sensitivities are implemented and validated, these results are not suitable as the paper's central 2050 projections.
