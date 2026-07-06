### Table R-FF. Functional-form robustness of the exposure variable (log(x+1) zero-value critique)

| Variable | Baseline: log(1+covid) | (a) PPML, levels | (b) asinh(covid) | (c) 1[covid>0], own-year |
|---|---|---|---|---|
| Log(1+Covid) | -0.1186*** | -0.0776*** |  |  |
|  | (0.0424) | (0.0197) |  |  |
| asinh(Covid) |  |  | -0.1155*** |  |
|  |  |  | (0.0405) |  |
| 1[Covid>0] (extensive margin) |  |  |  | -0.3827 |
|  |  |  |  | (0.3864) |
| N | 13,787 | 13,787 | 13,787 | 13,787 |
| Within R2 | 0.015 | NA | 0.015 | 0.014 |

Note: SE clustered by township. * p<0.10, ** p<0.05, *** p<0.01. Zero share of `covid`: 84.2% (all years), 28.9% (2020-2022). (a) PPML = Poisson pseudo-maximum-likelihood on workday LEVELS (fixest::fepois), coefficient is a semi-elasticity, same lncovid exposure as baseline. (b) keeps ln(workday) outcome, replaces the exposure transform lncovid -> asinh(covid). (c) 1[covid>0] is constructed directly from the case COUNT (NOT the pre-built `covid_dummy`, which is actually a post-2020 indicator collinear with year FE and unusable). Every county has covid=0 in 2013-2019 and covid>0 in ALL of 2020 and 2022, so column (c) is identified ONLY from within-2021 cross-sectional variation (74.4% of counties report zero cases that year) -- a much weaker/narrower test than (a)/(b), reported for completeness rather than as an equal-power robustness check. Sample and controls identical to the baseline (year<2023, N as reported).

