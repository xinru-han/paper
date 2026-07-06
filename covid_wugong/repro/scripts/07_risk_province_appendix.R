#!/usr/bin/env Rscript
# ============================================================================
# 07_risk_province_appendix.R
# Q2 / footnote 5: bring the OLD Stata pipeline's "available upon request"
# robustness checks into the R pipeline so they can go in the appendix.
#
# Old Stata do-file ran two blocks that are NOT reproducible from the shipped
# model dta alone (the variables were merged from external sources):
#   (i)  province-confirmed-cases spec:  reghdfe lna_workday2 lncovid_prov ...
#   (ii) risk-level spec:  reghdfe lna_workday2 highrisk_r / highmidrisk_r ...
#
# (i) is RECONSTRUCTIBLE: province-year cumulative confirmed cases are recovered
#     from the CCTV province series (province_covid_cases.csv) and merged by pid.
# (ii) is NOT reconstructible: highrisk_r/midrisk_r/lowrisk_r/highmidrisk do not
#     exist in either the model dta or the raw 农户数据.dta; the source risk-grade
#     data was an external merge absent from the provided materials. Documented,
#     not fabricated.
# ============================================================================
source("/root/data/Paper/covid/repro/scripts/00_common.R")
dt <- load_analysis()
dt0 <- dt[year<2023]

## ---- province cumulative cases -> lncovid_prov (accumulated to current year) ----
pv <- fread(file.path(D0,"province_covid_cases.csv"))
# pid in analysis panel is numeric (13/22/35/53); align types
pv[, pid := as.integer(pid)]
dt0[, pid := as.integer(pid)]
# accumulate-to-current-year province cases, mirroring the county covid_accum logic:
#   year>=2020 uses that year's province cumulative; pre-2020 = 0 (no covid)
pv_wide <- dcast(pv, pid ~ year, value.var="covid_prov_cum")
setnames(pv_wide, as.character(2020:2023), paste0("provcum_",2020:2023), skip_absent=TRUE)
dt0 <- merge(dt0, pv_wide[, .(pid, provcum_2020, provcum_2021, provcum_2022)], by="pid", all.x=TRUE)
dt0[, covid_prov := 0]
dt0[year==2020, covid_prov := provcum_2020]
dt0[year==2021, covid_prov := provcum_2021]
dt0[year==2022, covid_prov := provcum_2022]
dt0[, lncovid_prov := log(covid_prov + 1)]

cat("\n=== province cumulative cases merged (year>=2020) ===\n")
print(dt0[year>=2020, .(mean_prov=mean(covid_prov), lnmean=mean(lncovid_prov)), by=.(pid,year)][order(pid,year)])

## (i) province-cases robustness regression (same controls/FE as baseline)
m_prov <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid_prov + ",fc_full," | tid + year")),
                dt0, cluster=~tid)
cat("\n=== (i) Province-cases spec: lna_workday2 ~ ln(1+province cum cases) ===\n")
print(coeftable(m_prov)["lncovid_prov",c(1,2,4)])

save_tab(list("Province cases (lncovid_prov)"=m_prov), "tab_risk_province_appendix.md",
  "Table A-RP. Appendix robustness: province-level confirmed-case exposure (footnote 5, reconstructed)",
  coef_map=c("lncovid_prov"="Log(1+province cum. cases)"),
  notes="Note: SE clustered by township. Province-year cumulative confirmed cases reconstructed from the CCTV province series (2020-2022 cumulative, 0 pre-2020), merged by province. Same controls + township+year FE as the baseline. This reruns in R the old Stata pipeline's province-cases spec (previously 'available upon request').")

## (ii) risk-level: source data absent -> documented, not run
con <- file(file.path(O,"tab_risk_province_appendix.md"), open="a")
writeLines(c("",
 "### Risk-level specification (footnote 5) — NOT reproducible",
 "",
 "The old Stata do-file also ran a COVID risk-grade specification (reghdfe",
 "lna_workday2 highrisk_r ... and ... highmidrisk_r ...), setting the",
 "risk dummies to 0 for year<=2020. The variables highrisk_r, midrisk_r,",
 "lowrisk_r, and highmidrisk do NOT exist in either the shipped model dta",
 "(2013-2023 changmianban PDS model.dta) or the raw household data (nonghu shuju.dta).",
 "They were an external merge (county/period risk-grade classification) that is",
 "absent from the provided materials, so this specification CANNOT be rerun in",
 "the R pipeline without the original risk-grade source file. Recommendation:",
 "either obtain the risk-grade source and merge by county-period, or drop the",
 "footnote-5 promise and rely on the province-cases spec above + the main",
 "identification evidence (event study + province x year FE + county trends).",
 ""), con)
close(con)

sink(file.path(O,"key_numbers_risk_province.txt"))
cat("Province-cases spec (reconstructed from CCTV):\n")
print(coeftable(m_prov)["lncovid_prov",c(1,2,4)])
cat("N =", nobs(m_prov), "\n")
cat("\nRisk-level spec: NOT reproducible (highrisk_r/midrisk_r/highmidrisk absent from model dta AND raw 农户数据.dta).\n")
sink()
cat("\nDONE 07_risk_province_appendix.R\n")
