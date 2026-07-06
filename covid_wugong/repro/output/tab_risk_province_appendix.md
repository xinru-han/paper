### Table A-RP. Appendix robustness: province-level confirmed-case exposure (footnote 5, reconstructed)

| Variable | Province cases (lncovid_prov) |
|---|---|
| Log(1+province cum. cases) | -0.1778** |
|  | (0.0694) |
| N | 13,787 |
| Within R2 | 0.014 |

Note: SE clustered by township. Province-year cumulative confirmed cases reconstructed from the CCTV province series (2020-2022 cumulative, 0 pre-2020), merged by province. Same controls + township+year FE as the baseline. This reruns in R the old Stata pipeline's province-cases spec (previously 'available upon request').


### Risk-level specification (footnote 5) — NOT reproducible

The old Stata do-file also ran a COVID risk-grade specification (reghdfe
lna_workday2 highrisk_r ... and ... highmidrisk_r ...), setting the
risk dummies to 0 for year<=2020. The variables highrisk_r, midrisk_r,
lowrisk_r, and highmidrisk do NOT exist in either the shipped model dta
(2013-2023 changmianban PDS model.dta) or the raw household data (nonghu shuju.dta).
They were an external merge (county/period risk-grade classification) that is
absent from the provided materials, so this specification CANNOT be rerun in
the R pipeline without the original risk-grade source file. Recommendation:
either obtain the risk-grade source and merge by county-period, or drop the
footnote-5 promise and rely on the province-cases spec above + the main
identification evidence (event study + province x year FE + county trends).

