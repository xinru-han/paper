#!/usr/bin/env Rscript
# ============================================================================
# 06_wage_subsample_attrition.R
# P1-3 (modification plan Sec 3.6 + 3.5 attrition): 
#   (A) Wage-income variable has a questionnaire-item break exactly at the
#       treatment period (2013-2020: itemized hg02_1..hg11_1; 2021-2022: new
#       aggregated items) -- re-run the M2 income-shock mechanism test
#       restricted to 2013-2020 (single questionnaire generation, no break)
#       as a robustness check on whether the "income shock" mechanism
#       finding depends on the post-break years.
#   (B) Attrition test: is household attrition in 2020/2021 (present in the
#       prior wave, absent in the COVID wave) systematically related to
#       county-level COVID exposure? If attrition is exposure-driven, the
#       event-study/DiD coefficients in the COVID years could reflect
#       selective sample composition rather than a true behavioral effect.
#   (C) Effect-size unit correction: the manuscript's discarded "100 cases ->
#       63 fewer days" linear-extrapolation claim is invalid under a log-log
#       elasticity with 84% zero exposure; here we compute the CORRECT
#       interpretation -- the semi-elasticity/percentage effect implied by
#       the baseline coefficient, evaluated at representative case counts
#       from the data (not a constant days-per-100-cases slope).
# ============================================================================
source("/opt/data/research/Paper/新冠对务工的影响/revision2/scripts/00_common.R")
dt <- load_analysis()
dt0 <- dt[year<2023]

########################################################################
## (A) Wage income, 2013-2020 same-definition subsample
##     Variable construction matches revision/scripts/07_mechanisms.R exactly:
##     winsorize wage_built_r at 1%/99% (INCLUDING zeros, i.e. wage_built_r>=0),
##     then asinh-transform. This reproduces the original M2 wage-income
##     coefficient (-0.2646***) as the "Full sample" column here, so the
##     2013-2020 subsample is a like-for-like comparison, not a redefinition.
########################################################################
winz <- function(x,p=.01){ q<-quantile(x,c(p,1-p),na.rm=TRUE)
  x[!is.na(x) & x<q[1]]<-q[1]; x[!is.na(x) & x>q[2]]<-q[2]; x }

dt0[is.finite(wage_built_r) & wage_built_r>=0, wage_rw := winz(wage_built_r)]
dt0[, asinh_wage := asinh(wage_rw)]

dt_wage_full <- dt0[is.finite(asinh_wage)]
m_wage_full <- feols(as.formula(paste0("asinh_wage ~ lncovid + ",fc_full," | tid + year")),
                      dt_wage_full, cluster=~tid)

dt_wage_2013_2020 <- dt0[year<=2020 & is.finite(asinh_wage)]
m_wage_2013_2020 <- feols(as.formula(paste0("asinh_wage ~ lncovid + ",fc_full," | tid + year")),
                           dt_wage_2013_2020, cluster=~tid)

cat("\n=== (A) Wage income, FULL sample (2013-2022, includes questionnaire break) ===\n")
print(coeftable(m_wage_full)["lncovid",c(1,2,4)]); cat("N:",nobs(m_wage_full),"\n")
cat("\n=== (A) Wage income, 2013-2020 SAME-DEFINITION subsample (no questionnaire break) ===\n")
print(coeftable(m_wage_2013_2020)["lncovid",c(1,2,4)]); cat("N:",nobs(m_wage_2013_2020),"\n")

save_tab(list("Full sample (2013-2022)"=m_wage_full, "2013-2020 subsample (pre-break)"=m_wage_2013_2020),
         "tab_wage_subsample.md",
         "Table R-Wage. Wage-income mechanism: full sample vs. 2013-2020 same-questionnaire-definition subsample",
         coef_map=c("lncovid"="Log(Covid)"),
         notes="Note: SE clustered by township. Outcome = asinh(real wage income), self-built from itemized survey questions (hg02_1..hg11_1, 2013-2020) or aggregated new items (2021-2022) -- see revision/scripts/08_income_build.py, winsorized at 1%/99% before the asinh transform (identical construction to revision/07_mechanisms.R; the Full-sample column exactly reproduces the original M2 wage coefficient, -0.2646***, N=11,258). The questionnaire item set changes exactly at 2021, coinciding with the treatment period; the 2013-2020 subsample avoids this break entirely at the cost of dropping 2021-2022 variation, which also means 2020 is the ONLY post-treatment year identifying the coefficient in that column -- the much larger point estimate (-1.63 vs. -0.26) and wider SE should be read as reflecting this thinner identification (fewer post-treatment year x county cells), not necessarily a larger true effect. The two columns AGREE in sign and both remain significant at conventional levels, which is the robustness claim being tested here; the magnitude is not comparable across columns.")

########################################################################
## (B) Attrition test
########################################################################
setorder(dt, nid, year)
dt[, present := TRUE]
## build a household x year presence panel to detect attrition
hh_years <- dt[, .(nid, year)]
all_years <- 2013:2022
hh_ids <- unique(dt$nid)
grid <- CJ(nid=hh_ids, year=all_years)
grid <- merge(grid, hh_years[,.(nid,year,present=TRUE)], by=c("nid","year"), all.x=TRUE)
grid[is.na(present), present := FALSE]
setorder(grid, nid, year)
grid[, present_prev := shift(present,1,type="lag"), by=nid]
grid[, attrited := as.integer(present_prev==TRUE & present==FALSE)]

## merge county-level exposure (year-specific lncovid at county level, using county mean)
county_exp <- dt[, .(covid_mean=mean(covid,na.rm=TRUE), lncovid_mean=mean(lncovid,na.rm=TRUE)), by=.(xid,year)]
nid_xid <- unique(dt[,.(nid,xid)])
grid <- merge(grid, nid_xid, by="nid", all.x=TRUE)
grid <- merge(grid, county_exp, by=c("xid","year"), all.x=TRUE)

## test: is attrition in the COVID years (2020,2021,2022) predicted by county exposure,
## controlling for xid and year FE (so identifying off within-county-year variation is not
## possible since exposure is county-year level; instead compare xid FE + year dummies,
## i.e., testing whether HIGHER-exposure counties have MORE attrition in COVID years
## relative to their own historical attrition rate)
attr_sample <- grid[!is.na(present_prev) & present_prev==TRUE]
m_attr_covid_years <- feols(attrited ~ lncovid_mean | xid + year, attr_sample[year %in% 2020:2022], cluster=~xid)
cat("\n=== (B) Attrition ~ county-level lncovid, COVID years 2020-2022 (county+year FE) ===\n")
print(coeftable(m_attr_covid_years))

## overall attrition rate by year (descriptive)
attr_by_year <- attr_sample[, .(attrition_rate=mean(attrited), n=.N), by=year][order(year)]
cat("\nAttrition rate by year:\n"); print(attr_by_year)

## specific 2019->2020 test: does 2019 household lncovid... doesn't exist pre-covid.
## Instead: does county 2020 exposure predict whether a 2019 hh drops out in 2020?
d2019 <- dt[year==2019, .(nid, xid, ln_a_workday2_2019=ln_a_workday2)]
d2020_present <- dt[year==2020, .(nid, present_2020=TRUE)]
attr2020 <- merge(d2019, d2020_present, by="nid", all.x=TRUE)
attr2020[, present_2020 := ifelse(is.na(present_2020), FALSE, present_2020)]
attr2020[, attrited_2020 := as.integer(!present_2020)]
county_exp2020 <- dt[year==2020, .(lncovid_mean_2020=mean(lncovid,na.rm=TRUE)), by=xid]
attr2020 <- merge(attr2020, county_exp2020, by="xid", all.x=TRUE)
pid_map <- unique(dt[,.(xid,pid)])
attr2020 <- merge(attr2020, pid_map, by="xid", all.x=TRUE)
# NOTE: lncovid_mean_2020 is a county-level cross-sectional variable (single year) -- perfectly
# collinear with xid FE (each county contributes one value). Use province FE instead so
# cross-county variation within province survives; cluster SE at the county level.
m_attr2020 <- feols(attrited_2020 ~ lncovid_mean_2020 + ln_a_workday2_2019 | pid, attr2020, cluster=~xid)
cat("\n=== (B) 2019 households: P(absent in 2020) ~ county 2020 exposure + 2019 outcome level (province FE, county-clustered SE) ===\n")
print(coeftable(m_attr2020))
cat("N:", nobs(m_attr2020), " attrition rate:", mean(attr2020$attrited_2020), "\n")

## does 2019 outcome level differ between attriters and stayers? (selection on outcome)
cat("\n2019 mean ln_a_workday2: stayers =", mean(attr2020[attrited_2020==0]$ln_a_workday2_2019,na.rm=TRUE),
    " attriters =", mean(attr2020[attrited_2020==1]$ln_a_workday2_2019,na.rm=TRUE), "\n")
t_test <- t.test(ln_a_workday2_2019 ~ attrited_2020, data=attr2020)
print(t_test)

save_tab(list("Attrition (2020-22) ~ county exposure"=m_attr_covid_years),
         "tab_attrition.md","Table R-Attr. Attrition test: does county COVID exposure predict household dropout?",
         coef_map=c("lncovid_mean"="County mean ln(1+covid)"),
         notes="Note: SE clustered by county. Outcome = 1[household present in year t-1 but absent in year t]. County+year FE. A positive/significant coefficient would indicate COVID-exposure-driven selective attrition, which could bias the event-study/DiD estimates in the COVID years via differential sample composition.")

con <- file(file.path(O,"tab_attrition.md"), open="a")
writeLines(c("",
  "### 2019-cohort-specific test: P(absent in 2020 wave) ~ county 2020 exposure + 2019 outcome level",
  "",
  sprintf("County 2020 exposure (lncovid_mean_2020): b=%.4f, se=%.4f, p=%.4f",
          coeftable(m_attr2020)["lncovid_mean_2020",1], coeftable(m_attr2020)["lncovid_mean_2020",2], coeftable(m_attr2020)["lncovid_mean_2020",4]),
  sprintf("2019 outcome level (ln_a_workday2_2019): b=%.4f, se=%.4f, p=%.4f",
          coeftable(m_attr2020)["ln_a_workday2_2019",1], coeftable(m_attr2020)["ln_a_workday2_2019",2], coeftable(m_attr2020)["ln_a_workday2_2019",4]),
  sprintf("N=%d, overall 2019->2020 attrition rate=%.1f%%", nobs(m_attr2020), 100*mean(attr2020$attrited_2020)),
  "",
  sprintf("Two-sample t-test, 2019 ln(workday2) by 2020-attrition status: stayers mean=%.3f, attriters mean=%.3f, t=%.3f, p=%.4f",
          mean(attr2020[attrited_2020==0]$ln_a_workday2_2019,na.rm=TRUE),
          mean(attr2020[attrited_2020==1]$ln_a_workday2_2019,na.rm=TRUE),
          t_test$statistic, t_test$p.value),
  "",
  "### Attrition rate by year (descriptive, all households with a valid prior-year observation)",
  "",
  "| Year | Attrition rate | N (at risk) |",
  "|---|---|---|",
  sapply(1:nrow(attr_by_year), function(i) sprintf("| %d | %.1f%% | %d |", attr_by_year$year[i], 100*attr_by_year$attrition_rate[i], attr_by_year$n[i])),
  "",
  "Note: the panel has substantial rotation unrelated to COVID (e.g., 2018-2019 turnover exceeds 45%, reflecting a documented survey sample refresh), so the 2019->2020 attrition rate (27.8%) is elevated but within the range seen in non-COVID years. Two results require disclosure rather than a clean pass: (1) pooled across 2020-2022 (county+year FE), attrition is NOT significantly related to county exposure (b=0.0015, p=0.952); BUT (2) the more targeted 2019-cohort test (which households present in 2019 are absent in 2020, county 2020 exposure, province FE) finds a SIGNIFICANT NEGATIVE relationship (b=-0.107, p=0.037) -- i.e., households in HIGHER-exposure counties were somewhat LESS, not more, likely to drop out of the 2020 wave. This is the opposite of the 'COVID hit hardest households leave the sample' selection story that would inflate the estimated effect, so it does not explain away the 2020/2021 event-study coefficients; if anything it suggests the true effect may be marginally UNDERSTATED by differential retention of relatively resilient households in hard-hit counties. (3) Separately, households that attrited between 2019 and 2020 had markedly HIGHER 2019 workdays than those who stayed (4.30 vs. 2.82 log-points, t=-12.29, p<0.001) -- a real compositional shift, but one whose direction is unrelated to county exposure and therefore attributable to the general (non-COVID) sample-refresh pattern documented above rather than to the pandemic itself."
  ), con)
close(con)
cat("\nwrote tab_attrition.md\n")

########################################################################
## (C) Effect-size unit correction (replace invalid linear "100 cases -> X days" claim)
########################################################################
b <- coeftable(m_base_check <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid + ",fc_full," | tid + year")), dt0, cluster=~tid))["lncovid",1]
cat("\n=== (C) Effect-size, correct interpretation of the log-log elasticity ===\n")
cat("Baseline coefficient b =", round(b,4), "\n")
cat("Interpretation: a 1-log-point increase in ln(1+cases) is associated with a",
    sprintf("%.1f%%", 100*(exp(b)-1)), "change in workdays (semi-elasticity approx, small-b: ~", sprintf("%.1f%%",100*b),")\n")

## illustrate at representative percentiles of the ACTUAL case-count distribution (2020-2022, cases>0)
covid_pos <- dt0[year %in% 2020:2022 & covid>0]$covid
qs <- quantile(covid_pos, c(0.1,0.25,0.5,0.75,0.9), na.rm=TRUE)
cat("\nDistribution of (covid | covid>0, 2020-2022): p10=",qs[1]," p25=",qs[2]," median=",qs[3]," p75=",qs[4]," p90=",qs[5],"\n")

## Correct comparison: going from p25 to p75 case counts changes ln(1+covid) by:
delta_ln <- log(1+qs[4]) - log(1+qs[2])
pct_effect <- 100*(exp(b*delta_ln)-1)
cat(sprintf("\nGoing from the 25th to 75th percentile case count among affected county-years (%.0f -> %.0f cases) changes ln(1+cases) by %.3f log points, implying a %.1f%% change in workdays (NOT a constant days-per-100-cases slope).\n",
            qs[2], qs[4], delta_ln, pct_effect))

sink(file.path(O,"key_numbers_wage_attrition_effectsize.txt"))
cat("=== (A) Wage subsample ===\n")
cat("Full sample: b=",coeftable(m_wage_full)["lncovid",1]," p=",coeftable(m_wage_full)["lncovid",4]," N=",nobs(m_wage_full),"\n")
cat("2013-2020 subsample: b=",coeftable(m_wage_2013_2020)["lncovid",1]," p=",coeftable(m_wage_2013_2020)["lncovid",4]," N=",nobs(m_wage_2013_2020),"\n")
cat("\n=== (B) Attrition ===\n")
print(coeftable(m_attr_covid_years))
print(coeftable(m_attr2020))
cat("2019->2020 attrition rate:", 100*mean(attr2020$attrited_2020),"%\n")
cat("\n=== (C) Effect size (correct interpretation) ===\n")
cat("b=",b," semi-elasticity approx=",100*b,"% per log-point; exact=",100*(exp(b)-1),"%\n")
cat("p25->p75 case count (",qs[2],"->",qs[4],"): delta_ln=",delta_ln," implied pct effect=",pct_effect,"%\n")
sink()
cat("\nDONE 06_wage_subsample_attrition.R\n")
