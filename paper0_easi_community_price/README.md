# Community-price EASI pipeline

Run `code/00_run_all.do` from Stata 17 or later. The pipeline is intentionally
separate from the legacy EASI scripts and never overwrites their data.

## Inputs and keys

- Household input: `/root/data/数据/食物消费调查数据/处理后的data/户表数据_已清洗.dta`
- Village input: `/root/data/数据/食物消费调查数据/处理后的data/村表数据_已清洗.dta`
- Household IDs remain text. The join uses `substr(nhCode,1,12)` and `data_year`
  against the village `xzcCode_clean` and `data_year`; no floating-point household
  ID is constructed.

## Community-price construction

For each of six food groups, the code collects valid (`0 < price <= 200`) item
quotes from the village questionnaire's supermarket, grocery, free-market, and
meat-shop modules. It uses the within-village median of the available high/low
product quotations. This is a market price measure, not a household unit value.

Missing village-group prices are filled in this fixed order and the source is
saved in `p#_source`: same-township median, nearest reporting village in the same
county-year, county-year median, then province-year median. There is no national
fallback: any remaining missing price stops the analysis-data build.

## Estimation

`ado/easi_sy3sls.ado` estimates the first five equations and recovers the sixth
share by adding-up. Relative prices impose homogeneity and symmetry is imposed on
the unrestricted price block. `04_estimate_easi.do` adds Shonkwiler-Yen probits
for zero consumption before calling the constrained iterated 3SLS estimator.

The output tables include descriptive statistics, zero-consumption rates, price
sources, the exact merge audit, and fitted-share adding-up diagnostics.

## Execution note

The current container has a Stata executable but no usable license, so model
estimation cannot be executed here. The do/ado files are written for a licensed
Stata session and fail loudly on unmatched villages, invalid prices, missing
prices, nonconvergence, or adding-up violations.
