### Table R-Attr. Attrition test: does county COVID exposure predict household dropout?

| Variable | Attrition (2020-22) ~ county exposure |
|---|---|
| County mean ln(1+covid) | 0.0015 |
|  | (0.0241) |
| N | 4,828 |
| Within R2 | 0.000 |

Note: SE clustered by county. Outcome = 1[household present in year t-1 but absent in year t]. County+year FE. A positive/significant coefficient would indicate COVID-exposure-driven selective attrition, which could bias the event-study/DiD estimates in the COVID years via differential sample composition.


### 2019-cohort-specific test: P(absent in 2020 wave) ~ county 2020 exposure + 2019 outcome level

County 2020 exposure (lncovid_mean_2020): b=-0.1070, se=0.0439, p=0.0373
2019 outcome level (ln_a_workday2_2019): b=0.0042, se=0.0052, p=0.4421
N=1437, overall 2019->2020 attrition rate=27.8%

Two-sample t-test, 2019 ln(workday2) by 2020-attrition status: stayers mean=2.824, attriters mean=4.305, t=-12.290, p=0.0000

### Attrition rate by year (descriptive, all households with a valid prior-year observation)

| Year | Attrition rate | N (at risk) |
|---|---|---|
| 2014 | 0.4% | 2603 |
| 2015 | 0.3% | 2601 |
| 2016 | 0.6% | 2612 |
| 2017 | 0.2% | 2607 |
| 2018 | 21.6% | 2631 |
| 2019 | 45.8% | 2155 |
| 2020 | 27.8% | 1894 |
| 2021 | 7.5% | 1393 |
| 2022 | 16.7% | 1900 |

Note: the panel has substantial rotation unrelated to COVID (e.g., 2018-2019 turnover exceeds 45%, reflecting a documented survey sample refresh), so the 2019->2020 attrition rate (27.8%) is elevated but within the range seen in non-COVID years. Two results require disclosure rather than a clean pass: (1) pooled across 2020-2022 (county+year FE), attrition is NOT significantly related to county exposure (b=0.0015, p=0.952); BUT (2) the more targeted 2019-cohort test (which households present in 2019 are absent in 2020, county 2020 exposure, province FE) finds a SIGNIFICANT NEGATIVE relationship (b=-0.107, p=0.037) -- i.e., households in HIGHER-exposure counties were somewhat LESS, not more, likely to drop out of the 2020 wave. This is the opposite of the 'COVID hit hardest households leave the sample' selection story that would inflate the estimated effect, so it does not explain away the 2020/2021 event-study coefficients; if anything it suggests the true effect may be marginally UNDERSTATED by differential retention of relatively resilient households in hard-hit counties. (3) Separately, households that attrited between 2019 and 2020 had markedly HIGHER 2019 workdays than those who stayed (4.30 vs. 2.82 log-points, t=-12.29, p<0.001) -- a real compositional shift, but one whose direction is unrelated to county exposure and therefore attributable to the general (non-COVID) sample-refresh pattern documented above rather than to the pandemic itself.
