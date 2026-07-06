### Table R2b. Event study extended through 2023 (exposure x year interactions, ref=2019)

| Variable | Event study (2013-2023) |
|---|---|
| year::2013:ln_exposure2022 | 0.0233 |
|  | (0.1073) |
| year::2014:ln_exposure2022 | -0.0231 |
|  | (0.1084) |
| year::2015:ln_exposure2022 | 0.0172 |
|  | (0.0965) |
| year::2016:ln_exposure2022 | 0.0225 |
|  | (0.1051) |
| year::2017:ln_exposure2022 | -0.0070 |
|  | (0.0903) |
| year::2018:ln_exposure2022 | -0.1549* |
|  | (0.0865) |
| year::2020:ln_exposure2022 | -0.3048** |
|  | (0.1231) |
| year::2021:ln_exposure2022 | -0.3662*** |
|  | (0.0857) |
| year::2022:ln_exposure2022 | -0.0126 |
|  | (0.0594) |
| year::2023:ln_exposure2022 | -0.0608 |
|  | (0.0864) |
| gender | 0.1783 |
|  | (0.1819) |
| age | -0.0015 |
|  | (0.0050) |
| health | 0.1708*** |
|  | (0.0493) |
| edu | -0.0175 |
|  | (0.0174) |
| labor_ratio | 0.3275* |
|  | (0.1882) |
| pilot | 0.1355* |
|  | (0.0717) |
| lnhouseholds | -0.0549 |
|  | (0.2123) |
| lnv_ainccpi | -0.0500 |
|  | (0.1493) |
| lnfar_station | 0.0221 |
|  | (0.0714) |
| lnfar_asale | 0.0926 |
|  | (0.1121) |
| lnfar_market | -0.1116 |
|  | (0.1186) |
| lnlandprice_sum | 0.0161 |
|  | (0.0482) |
| N | 15,165 |
| Within R2 | 0.013 |

Note: SE clustered by township in parentheses. * p<0.10, ** p<0.05, *** p<0.01.


### Direct persistence test: 2022 exposure -> 2023 outcome (cross-section, province FE, county-clustered SE)

| Model | Coefficient | Estimate | SE | p |
|---|---|---|---|---|
| 2022 cum. exposure ln(1+cases) -> 2023 ln(workday2) | ln_exposure2022 | 0.1277 | 0.1828 | 0.5006 |
| 2022 current-year lncovid -> 2023 ln(workday2) | lncovid_2022 | 0.0682 | 0.1632 | 0.6850 |

N(2022 cum exposure model)=1243; N(2022 current covid model)=1190. FE: province (pid); SE clustered by county (xid, 11-12 clusters -- see wild-bootstrap version in tab_inference_robustness.md).

### Pre-trend joint test (2013-2018 event-study coefficients = 0)

Wald F = 1.132, df1 = 6, df2 = 40, p = 0.3619

Note: exposure = ln(1+cumulative confirmed cases through 2022) x year dummy, ref=2019, township+year FE, controls (ctrl_2023, road_density2 excluded because 100% missing in 2023).

