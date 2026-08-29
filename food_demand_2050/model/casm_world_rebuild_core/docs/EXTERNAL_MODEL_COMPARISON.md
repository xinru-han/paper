# External-model comparison protocol

This note freezes the comparison rules used by the CASM-World manuscript. It
prevents differences in base year, commodity coverage, units, geographic
scope, or model identity from being presented as if they were prediction
errors.

## OECD-FAO Agricultural Outlook / Aglink-Cosimo

The official [OECD-FAO Agricultural Outlook 2026-2035 data
set](https://data-explorer.oecd.org/vis?bp=true&df%5Bag%5D=OECD.TAD.ATM&df%5Bid%5D=DSD_AGR%40DF_OUTLOOK_2026_2035&df%5Bvs%5D=1.1)
states that its internally consistent projections are produced with the joint
OECD-FAO Aglink-Cosimo system. It is therefore labelled “OECD-FAO
Aglink-Cosimo” in the paper, not simply “the OECD model.”

The reproducible comparison uses production (`QP`) for nine directly matched
products in World, China and the EU. It compares percentage changes from 2024
to 2035. The chosen overlap avoids extrapolating the OECD-FAO outlook beyond
its published endpoint and avoids treating CASM-World's 2023 benchmark as an
OECD-FAO forecast observation. CASM-World SSP2 is the point comparison; the
SSP1-SSP5 minimum and maximum are shown as a scenario envelope. Levels are not
used to rank models because definitions such as product-equivalent weight can
differ even after a label match.

The selected raw extract is
`data/external/oecd_fao_outlook_2026_2035_selected_production.csv`. The paper
build fails on an unmapped area or commodity. Its mapped output is
`paper/tables/table11_oecd_fao_comparison_2024_2035.csv`.

The frozen SDMX selection is `W+CHN+EU` × annual frequency ×
`CPC_0111+CPC_0112+CPC_0113+CPC_0114T0119+CPC_0141+CPC_01921+CPC_EX_BV+CPC_EX_PK+CPC_EX_PT`
× production (`QP`) × tonnes (`T`) × version `AO_2026_2035`, for 2023–2035.
It can be reproduced through the official [OECD SDMX
endpoint](https://sdmx.oecd.org/public/rest/data/OECD.TAD.ATM,DSD_AGR@DF_OUTLOOK_2026_2035,1.1/W+CHN+EU.A.CPC_0111+CPC_0112+CPC_0113+CPC_0114T0119+CPC_0141+CPC_01921+CPC_EX_BV+CPC_EX_PK+CPC_EX_PT.QP.T.AO_2026_2035?startPeriod=2023&endPeriod=2035&dimensionAtObservation=AllDimensions)
with an `Accept: text/csv` header.

### Current V2 diagnostic holdout result

These metrics are conditional diagnostics, not evidence that the current run
is a publication baseline. Across the 27 matched series, CASM-World SSP2 and
OECD-FAO agree on the direction of change in 23 cases (85.19%). The median
absolute error is 10.04 percentage points and the 90th percentile is 21.28
points. World sign agreement is 9/9 and mean absolute error is 5.79 points;
China sign agreement is 9/9 and mean absolute error 16.89 points; EU sign
agreement is 5/9 and mean absolute error 10.52 points. These values pass the
five frozen OECD holdout gates. The separate publication validation remains
18/20 because two processed-dairy 2050 price gates fail, so the model output
must still be labelled diagnostic conditional and not a publication baseline.
The exact product rows are in
`paper/tables/table11_oecd_fao_comparison_2024_2035.csv`.

## IFPRI/CGIAR IMPACT

The official [CGIAR Foresight model
description](https://foresight.cgiar.org/impact-model/) characterizes IMPACT
as a linked, global partial-equilibrium system covering 62 commodities and 158
countries. The 2025 IFPRI chapter by Cenacchi, Sulser and Mishra reports that
global production of all agricultural commodities rises by more than 40%
between 2020 and 2050; its full citation is available through the [IFPRI
catalogue](https://www.ifpri.org/publications/books/) and permanent handle
[10568/175534](https://hdl.handle.net/10568/175534).

That statement is used only as a broad directional benchmark. CASM-World's
published aggregate is a 13-product, non-overlapping primary basket from 2023
to 2050. The different initial year and substantially different commodity
universe rule out interpreting the difference in growth rates as a
model-forecast error.

IFPRI lists *Global agrifood systems outlook to 2050* as scheduled for release
on 10 September 2026 on its [IMPACT project
page](https://www.ifpri.org/project/ifpri-impact-model/). Because the analysis
date is 29 August 2026, no result from that embargoed report is used.

## JRC SUPREMA / AGMEMOD

The European Commission Joint Research Centre's official [SUPREMA
dataset](https://data.jrc.ec.europa.eu/dataset/d6ef74c6-ba91-4e37-827e-d0854fbe85dd)
documents harmonized multi-model baselines for 2030 and 2050 and includes
AGMEMOD in the model family. It is not valid to attribute every European
Commission agricultural outlook series to AGMEMOD, nor to compare a SUPREMA
variable to CASM-World solely because the labels look similar.

The [AGMEMOD consortium's model description](https://agmemod.eu/about-agmemod/model)
identifies it as a system of country-adapted partial-equilibrium models for
agricultural, fisheries and food sectors, mainly used for medium-term
baselines and policy scenarios. This differs from CASM-World's uniform global
account structure and 2050 SSP objective, so geographic and product matching
alone does not make the structural assumptions equivalent.

The present draft therefore reports the CASM-World EU27 pathway and treats
SUPREMA as a structured comparison protocol. A numerical AGMEMOD comparison
will be added only after the official baseline file supplies an identical
product concept, geographic coverage, unit, base year and endpoint. No
AGMEMOD number is imputed, copied from a secondary source, or inferred from a
chart.

## Aggregation rules shared by all comparisons

1. Raw and processed layers are never added to form a production total.
2. The aggregate CASM-World production indicator contains `RIC`, `WHE`,
   `CRN`, `OCG`, `SBS`, `NBS`, `RBS`, `SCA`, `SBE`, `BFV`, `PRK`, `PLM`, and
   `MLK` only.
3. Cotton lint is compared product by product; it is excluded from the
   aggregate because seed cotton is a satellite processing activity.
4. Nutrition uses only `food_demand_mt`, not total final demand.
5. GHG comparisons use the attributed biological farm-gate boundary and do
   not treat land-use change, agricultural energy, processing, transport or
   retail emissions as zero.
6. Every comparison reports the source model, scenario, initial year,
   endpoint, unit, geography and commodity concordance.
