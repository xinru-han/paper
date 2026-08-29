# CASM-World V2 long-run response specification

Status: frozen implementation specification, 2026-08-29  
Scope: parameter semantics and response horizons only  
Benchmark: 2023  
Projection: annual SSP1--SSP5 solutions, 2023--2050

This document defines the smallest correction needed before the scenario
results can be used as a publication baseline. It does **not** change the
193-economy/31-product accounting system, processing yields, non-spatial world
market closure, tariff paths, climate shocks, TFP paths, or reporting groups.
It also does not introduce bilateral trade or a SILK dependency.

The protocol was frozen after inspecting V1 and before running V2. It is a
prospective internal validation protocol, not a claim of blind or externally
registered preregistration. No V2 parameter may be changed after inspecting
the V2 holdout statistics unless the version is rejected, renamed, and rerun
under a newly dated specification.

## 1. Decision

V2 central makes three linked semantic corrections:

1. Crop price response is total long-run production response: the sum of the
   own-price acreage and yield elasticities. V1 used the PEATSim `ela/supela`
   field alone, although that field is a yield elasticity.
2. Processing activity responds to its processing margin using a
   process-specific elasticity. V1 inferred every process elasticity from the
   elasticities assigned to its outputs.
3. Final-demand own-price response is the 2023-use-share-weighted response of
   food, feed, and other final uses. V1 routed the food-demand diagonal to
   meals and other feed uses, even where the food-demand prior is structurally
   zero.

No TFP taper, shared-land/resource constraint, or new demand-substitution nest
is included in the V2 central run. Those changes address distinct model-form
questions and are frozen as sensitivities in section 8. Using them to repair
V1 prices would confound the correction of a parameter-definition error with
new assumptions about technology or market structure.

## 2. Evidence for the correction

### 2.1 What V1 currently computes

The linked solver evaluates primary supply and final demand as

\[
Q^S_{irt}=Q^S_{ir0}Z^S_{irt}(P^w_{it}W_{irt})^{\epsilon^S_{ir}},
\qquad
Q^D_{irt}=Q^D_{ir0}Z^D_{irt}(P^w_{it}W_{irt})^{\epsilon^D_{ir}},
\]

and process activity as

\[
A_{krt}=A_{kr0}Z^A_{krt}
\exp\{\psi_{kr}[\sum_i\omega^o_{kri}\ln P_{irt}
-\sum_i\omega^u_{kri}\ln P_{irt}]\}.
\]

These are the implemented equations in
`src/casm_world/linked_equilibrium.py:142-180`. The annual driver, TFP,
climate and policy construction is in `src/casm_world/simulation.py:378-422`.

V1 reads the first numeric supply column of the PEATSim `ela` sheet and names
it `ela_supply` (`src/casm_world/parameters.py:206-217`). It does not read the
`yahela` acreage-response sheet. The configuration then routes that single
series to all nine crop-like products (`config/parameters.yaml:62-84`). V1
also sets a process elasticity equal to the output-coefficient-weighted mean
of product supply elasticities, clipped to one
(`src/casm_world/simulation.py:75-91`).

### 2.2 Meaning of the PEATSim fields

The original PEATSim implementation is unambiguous:

- `yldela(i,r) = ela(i,r,"supela")` in
  `/root/data/CASM/PEATSim_Dist507/bench.gms:1028`;
- crop acreage uses the separate own- and cross-price matrix `yahela` in
  `bench.gms:1937-1941`;
- yield uses `yldela` in `bench.gms:1951-1956`;
- crop production is acreage times yield in `bench.gms:1959-1960`;
- acreage and yield response coefficients are multiplied by one minus their
  lag parameter in `bench.gms:1036-1060`.

The USDA ERS technical report *Dynamic PEATSim Model: Documenting Its Use in
Analyzing Global Commodity Markets* makes the same distinction: crop
production is acreage times yield, acreage responds to own and competing crop
prices, and yield has a separate own-price elasticity (Technical Bulletin
1933, pp. 5--6, local file
`/root/data/CASM/PEATSim_Dist507/Peatsim model document.pdf`). It describes the
constant-elasticity functions as local first-order approximations rather than
unbounded structural laws (p. 2).

PEATSim also uses separate behavioral blocks that V1 had conflated:

- food demand uses `fodela` (`bench.gms:2015-2020`);
- feed demand uses `fedela` and is linked to livestock output
  (`bench.gms:2026-2032`);
- oilseed crush responds to the output/input margin using `oilela`
  (`bench.gms:2034-2040`);
- raw-milk processing responds to the dairy-output/raw-milk margin using
  `mlkela` (`bench.gms:2062-2066`).

In the frozen release-507 workbook, the own crush-margin diagonal is 1.5 in
the named PEATSim regions (2.0 for ROW), and `mlkela` is 3.0 in every named
region. These values are read as long-run responses because the GAMS code
separately applies the adjustment multiplier.

### 2.3 JIRCAS time-horizon check

JIRCAS Working Report No. 89 derives crop supply elasticities from production
cost shares, labels them short-run supply elasticities, and models acreage
with adaptive expectations. Its default lag coefficient is 0.8 (report pp.
6--9). The US illustration reports positive own and negative cross-crop
responses and a separate lag coefficient (Table 5-3, p. 44). Its food-demand
system has own and cross-price effects derived from conditional cost
minimization (pp. 17--18; Table 5-9, p. 45). Source:
`/root/data/CASM/jircas_working_report89-_- (1).pdf`.

JIRCAS is therefore corroborating evidence about meanings and time horizons,
not a second parameter table to splice selectively into V2. In particular,
its lag coefficient must not be mistaken for an elasticity.

### 2.4 Diagnostic symptom

V1 clears every market numerically, but numerical closure does not establish
economic plausibility. Under SSP2 in 2050, its world price indices range from
0.0725 (rapeseed) to 12.1740 (cotton lint); across all SSPs the range is
0.0475--15.4983. Cotton has a quantity-weighted supply response of about
0.0415 and demand response of -0.0400, so even a modest physical expansion
requires a very large price change. This is the expected mathematical result
of applying a yield-only elasticity to the entire seed-cotton/ginning
activity, not evidence of a cotton scarcity prediction.

## 3. Central equations

Indices are economy `r`, product `i`, process `k`, scenario `s`, and year `t`.
All prices and exogenous shifters equal one in 2023.

### 3.1 Primary supply

Retain the V1 primary-supply equation, replacing its response parameter by a
semantically correct long-run parameter and a transparent horizon factor:

\[
Q^S_{irst}=Q^S_{ir,2023}Z^S_{irst}
             (P^w_{ist}W_{irst})^{a_g(t)\epsilon^{S,LR}_{ir}},
\]

where `g` is a response class and

\[
a_g(t)=
\begin{cases}
1, & t=2023,\\
1-\lambda_g^{t-2023}, & t\ge 2024.
\end{cases}
\]

The 2023 choice is immaterial because the normalized price is one. For a
permanent deviation after 2023, the second expression is the closed-form
cumulative response implied by partial adjustment. It preserves the present
independent annual equilibria; V2 must be described as an annual sequence of
medium/long-run equilibria, not as a stock-flow recursive forecast.

Frozen lag coefficients are:

| Response class | `lambda` | Evidence |
|---|---:|---|
| crop, cotton and sugar upstream | 0.10 | PEATSim `bench.gms:1036-1037` |
| livestock primary supply | 0.25 | PEATSim `bench.gms:1039` |
| oilseed crush | 0.10 | PEATSim `bench.gms:1041` |
| dairy raw-milk processing | 0.20 | PEATSim `bench.gms:1044` |
| CASM sugar refining, OTO and biofuel default | 0.10 | declared V2 convention |

At 2035 and 2050 these factors are effectively one for the chosen values;
their role is to distinguish a one-year response from a long-run response,
not to tune the endpoint.

### 3.2 Final demand

Retain the V1 population and real-income shifter but replace the single
mislabelled own-price elasticity:

\[
Q^D_{irst}=Q^D_{ir,2023}
 \frac{N_{rst}}{N_{r,2023}}
 \left(\frac{y_{rst}}{y_{r,2023}}\right)^{\eta_{ir}}
 (P^w_{ist}W_{irst})^{\epsilon^{D,LR}_{ir}},
\]

\[
\epsilon^{D,LR}_{ir}=
s^F_{ir}\epsilon^F_{ir}+
s^L_{ir}\epsilon^L_i+
s^O_{ir}\epsilon^O_{ir},
\qquad s^F_{ir}+s^L_{ir}+s^O_{ir}=1.
\]

Here `F`, `L`, and `O` denote food, feed, and other final use. `sF` is the
balanced 2023 food share. Split balanced non-food final demand using the
unbalanced source feed share:

\[
s^L=(1-s^F)\frac{FEE^{src}}
 {FEE^{src}+SEED^{src}+LOSS^{src}+OTHER^{src}},
\]

with zero when the denominator is zero; `sO=1-sF-sL`. This changes no 2023
quantity. Food response `epsilonF` and other-use response `epsilonO` retain
their valid V1 priors and income-group adjustments. Feed response `epsilonL`
uses the frozen feed-own reductions in section 4.2.

### 3.3 Processing

Keep every physical input and output coefficient fixed. Only replace the
misrouted activity elasticity:

\[
A_{krst}=A_{kr,2023}Z^A_{krst}
 \left[
 \frac{\prod_i(P^w_{ist}W_{irst})^{\omega^o_{kri}}}
      {\prod_i(P^w_{ist}W_{irst})^{\omega^u_{kri}}}
 \right]^{a_k(t)\psi^{LR}_k}.
\]

The coefficients `omega` remain the normalized physical output and input
weights already used by the linked solver. Outputs and inputs remain exact
multiples of the single activity, so oil/meal, sugar, cotton, ethanol/DDG and
dairy identities are unchanged.

## 4. Frozen central parameters

### 4.1 Crop and upstream supply

For each frozen PEATSim region with both terms, calculate

\[
e_{ig}=\texttt{ela.supela}_{ig}+\texttt{yahela}_{iig}.
\]

The product prior is the finite regional median. Apply the existing World
Bank income-class supply multiplier only after this reduction, then clip the
final economy-product parameter to `[0.15, 0.65]`. No structural-zero row is
converted to a zero elasticity.

| Product/role | low (P25) | central (median) | high (P75) |
|---|---:|---:|---:|
| RIC | 0.286 | 0.319 | 0.372 |
| WHE | 0.352 | 0.407 | 0.473 |
| CRN | 0.344 | 0.381 | 0.405 |
| OCG | 0.395 | 0.408 | 0.518 |
| SBS | 0.365 | 0.451 | 0.539 |
| NBS | 0.246 | 0.311 | 0.350 |
| RBS | 0.218 | 0.300 | 0.353 |
| CTN upstream/ginning activity | 0.437 | 0.456 | 0.494 |
| SCA and SBE upstream | 0.311 | 0.457 | 0.567 |

`SCA` and `SBE` receive the same aggregate sugar-upstream prior before the
income adjustment. `SUG` is a process output and receives no independent
primary-supply response. `CTN` remains cotton lint in the market accounts,
but its no-modelled-input ginning activity receives the upstream cotton
response shown above.

Existing livestock priors from the `metelap` diagonal and their current class
and income rules are retained because their source meaning is already a
livestock production response. Processed dairy-output `daielap` diagonals
must not be used as raw-milk processing elasticities.

`OTO` has no usable upstream crop/activity representation in the 31-product
boundary. Its frozen CASM prior is 0.50, labelled `explicit_author_prior`.

### 4.2 Feed demand

The following own-price elasticities are frozen reductions of the PEATSim
`fedela` block and are applied only to the 2023 feed share:

| Feed | central `epsilonL` | low-response | high-response |
|---|---:|---:|---:|
| WHE | -0.666 | -0.500 | -0.833 |
| CRN | -0.372 | -0.279 | -0.465 |
| OCG | -0.600 | -0.450 | -0.750 |
| SBM | -0.227 | -0.170 | -0.284 |
| NBM | -0.572 | -0.429 | -0.715 |
| RBM | -0.472 | -0.354 | -0.590 |

Low and high values are exactly 0.75 and 1.25 times the central magnitude,
rounded here to three decimals; implementation retains full precision.
`DDG` uses the unweighted median of the three meal central magnitudes,
`-0.424`, with low/high `-0.318/-0.530`. Products not listed retain their V1
other-use prior for the non-food share. Raw oilseed crushing is endogenous
process demand and is not reclassified as final feed demand.

### 4.3 Processing activity and other declared priors

| Activity/parameter | low | central | high | Status |
|---|---:|---:|---:|---|
| soybean crush margin | 1.35 | 1.50 | 2.00 | PEATSim semantic prior |
| sunflower crush margin | 1.35 | 1.50 | 2.00 | PEATSim semantic prior |
| rapeseed crush margin | 1.35 | 1.50 | 2.00 | PEATSim semantic prior |
| dairy raw-milk margin | 2.40 | 3.00 | 3.60 | PEATSim semantic prior |
| cane/beet sugar refining margin | 0.50 | 1.00 | 1.50 | explicit CASM prior |
| OTO primary supply | 0.30 | 0.50 | 0.80 | explicit CASM prior |
| ethanol joint activity | 0.1875 | 0.25 | 0.3125 | retained CASM prior |
| biodiesel primary supply | 0.1875 | 0.25 | 0.3125 | retained CASM prior |

All entries in this table are **long-run** parameters and therefore still
receive the annual horizon factor in section 3. The crush low value is a
conservative 10 percent reduction from 1.5 (numerically
`(1-0.10)*1.5`); the high value is the frozen ROW diagonal. The dairy low
value is a conservative 20 percent reduction from 3.0 (numerically
`(1-0.20)*3.0`); the high value is a symmetric 20 percent increase. Thus an
implementation must not treat 1.35 or 2.40 as an already horizon-adjusted
one-year coefficient. The sugar and OTO values are deliberately wide because
they are CASM priors, not estimates. They must be labelled as such in the
parameter audit and paper.

## 5. Exact-calibration and closure gates

V2 central, low and high must each pass all gates:

1. All 193 x 31 2023 model quantities reproduce the balanced benchmark to
   `1e-8 Mt`; every 2023 world price index equals one to `1e-12`.
2. Every processing activity reproduces its 2023 balanced activity to
   `1e-8`; all physical chain residuals are at most `1e-8 Mt`.
3. Each of 140 annual SSP equilibria converges with maximum world-market
   relative residual `<=1e-9` and maximum accounting residual `<=1e-9 Mt`.
4. There are no missing, non-finite or negative price/quantity results and no
   parameter is silently replaced by zero.
5. No solution touches the numerical log-price bound. A bound hit is failure,
   not a quantity to winsorize.
6. Bilateral-trade and SILK-dependency flags remain false. The system retains
   one world price for each product.

## 6. Prospective price plausibility gates

These gates detect another order-of-magnitude response failure; they are not
targets for calibration.

1. For every SSP/product, the 2050 world price index must lie in `[0.25, 4.0]`.
2. At least 95 percent of the 155 SSP-product 2050 indices must lie in
   `[0.50, 2.00]`.
3. For every SSP/product/year after 2023,
   `abs(log(P_t/P_(t-1))) <= 0.20`. The exogenous paths contain no discrete
   crisis shock that would justify a larger annual jump.
4. For RIC, WHE, CRN, OCG, SUG, BFV, PRK, PLM and MLK, no SSP may have a
   2050 price outside `[0.50, 2.50]`.

A failure rejects V2 central. It does not authorize changing one commodity's
parameter until its price passes.

## 7. OECD-FAO 2024--2035 holdout

The frozen external file is
`data/external/oecd_fao_outlook_2026_2035_selected_production.csv`, an extract
of the official OECD-FAO Agricultural Outlook 2026--2035 Aglink-Cosimo data
set. The protocol and concordance are in
`docs/EXTERNAL_MODEL_COMPARISON.md`. Compare percentage production changes
from 2024 to 2035 for nine matched commodities in World, China mainland and
EU27. Use SSP2 as the point comparison and report the full SSP range. Do not
extrapolate OECD-FAO after 2035 and do not use its values as calibration
targets.

V2 passes this holdout only if:

1. all 27 matched cells are present;
2. the direction of change agrees in at least 75 percent of cells;
3. the median absolute SSP2 difference is at most 12 percentage points and
   the 90th percentile is at most 25 points;
4. for the nine World cells, mean absolute difference is at most 8 points and
   direction agrees in at least eight of nine;
5. no matched absolute difference exceeds 35 points.

For context only, V1 has 85.2 percent sign agreement, a 10.1-point median
absolute difference, a 20.6-point 90th percentile, and a 6.36-point World
mean absolute difference. Reporting these diagnostics prevents the V2 gates
from being portrayed as blind preregistration. The official data source is
<https://data-explorer.oecd.org/vis?bp=true&df%5Bag%5D=OECD.TAD.ATM&df%5Bid%5D=DSD_AGR%40DF_OUTLOOK_2026_2035&df%5Bvs%5D=1.1>.

## 8. Frozen sensitivity design

### 8.1 Parameter-response envelope

Run the entire five-SSP annual system under three joint parameter sets:

- `V2_LOW_RESPONSE`: crop P25 values, feed elasticities at 0.75 central
  magnitude, and the low process/author priors in section 4;
- `V2_CENTRAL`: crop medians and all central values;
- `V2_HIGH_RESPONSE`: crop P75 values, feed elasticities at 1.25 central
  magnitude, and the high process/author priors.

All three retain the same 2023 quantities, exogenous paths and WB income
multipliers. Do not combine a low supply response with a high demand response
to manufacture a wider price range; such corner combinations may be reported
separately only if clearly labelled stress tests.

Report, at minimum, 2035 and 2050 World/China/EU27 and reporting-region
production, food demand, net imports, prices, nutrition and attributed GHG.
The central value and low/high response range must appear together.

### 8.2 TFP model-form sensitivity -- not central

The central run retains the existing country trend and SSP multipliers in
`config/tfp.yaml:1-15`. For years through 2035 all TFP runs are identical.
After 2035, multiply each positive annual log TFP rate by `0.75`, `1.00`, or
`1.25` for `TFP_SLOW`, central, and `TFP_FAST`, respectively; retain
non-positive rates and the existing `[-0.005, 0.035]` annual bounds. Rebuild
the index continuously from its 2035 level.

TFP tapering is not permitted as a central price remedy: V1's extremes follow
directly from elasticity misclassification, while TFP is an independently
specified productivity scenario.

### 8.3 Shared crop-resource sensitivity -- not central

Run one `SHARED_CROP_RESOURCE` case using 2023 harvested-area shares and a
Tornqvist crop-price index `P_A`. Decompose each PEATSim crop response into
yield `epsilonY`, own acreage `epsilonA`, and common land expansion
`epsilonLand=0.04` (the approximate median row sum of `yahela`). For an
economy with at least two active crops, replace the crop price term by

\[
(\epsilon^Y_i+\epsilon^{Land})\ln p_i+
\frac{\epsilon^A_i-\epsilon^{Land}}{1-w_{ir}}
\ln(p_i/P_{Ar}).
\]

This preserves the local own-price derivative
`epsilonY + epsilonA`, adds negative cross-crop competition, and allows only
the small common-area response when all crop prices move together. Use the
central semantic parameters, not retuned values. A one-active-crop account
retains its central own response.

This is a model-form sensitivity rather than a hard land identity because V2
does not endogenize hectares or land conversion.

### 8.4 Demand-substitution sensitivity -- not central

Run one calibrated inner CES allocation case with nests:

- grains: RIC, WHE, CRN, OCG;
- vegetable oils: SBO, NBO, RBO, OTO;
- meals/feed byproducts: SBM, NBM, RBM, DDG;
- meats: BFV, PRK, PLM;
- processed dairy: BUT, CHE, NDM, FMK, WDM, ODA.

Singletons and raw processing inputs remain outside these nests. Freeze 2023
within-nest quantity shares, use the Cobb-Douglas limit `sigma=1.0` for every
inner nest, and retain the central outer demand shifter. The normalized inner
demand is

\[
q_i=q_{i0}\,(Q_g/Q_{g0})(p_i/P_g)^{-\sigma_g},
\]

with the group scale chosen so the 2023 product quantities are reproduced
exactly. This sensitivity tests the omission of cross-price substitution; it
must not replace the central run merely because it produces smoother prices.

### 8.5 Promotion rule

Promote the shared-resource or demand-nest feature to a future central version
only if, relative to V2 central, it changes any major-food 2050 world price by
more than 20 percent or changes primary production in World, China, EU27, any
World Bank income group, LDC, or SIDS by more than 10 percent. Promotion
requires a new versioned specification and a fresh holdout; V2 itself remains
frozen.

## 9. Required audit outputs

Implementation must produce a machine-readable V2 parameter audit with:

- source sheet and semantic role for every parameter;
- raw regional reduction, income multiplier, bound, final long-run value,
  lag class and annual effective value;
- frozen food/feed/other shares and their source observations;
- explicit labels for every CASM author prior;
- counts of clipped parameters by reason;
- central, low and high parameter hashes;
- exact-calibration, closure, price-plausibility and OECD holdout results;
- a statement that external comparison data were not model inputs.

Until central and both response-envelope runs pass sections 5--7, V2 results
are diagnostic and must not replace the formal paper tables.
