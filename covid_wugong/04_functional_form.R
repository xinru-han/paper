#!/usr/bin/env Rscript
# ============================================================================
# 04_functional_form.R
# P1-1 (modification plan Sec 3.3): log(x+1) zero-value robustness triad.
# lncovid = ln(1+cases) has 84% zeros overall (29% even restricted to 2020-22),
# so the log(x+1) transform's scale-dependence (Chen & Roth 2024, QJE) is a
# reviewer-obvious concern. Three alternative specifications for the exposure
# variable, holding the outcome/sample/controls/FE fixed at the baseline:
#   (a) PPML on workday LEVELS (fixest::fepois) -- avoids taking any log of
#       the outcome; exposure stays as lncovid for comparability, coefficient
#       interpreted as semi-elasticity on the count outcome.
#   (b) asinh(covid) instead of ln(1+covid) as the exposure regressor --
#       asinh is scale-invariant near zero and behaves like log for large x.
#   (c) 1[covid>0] (own-year extensive margin of exposure) instead of the
#       continuous log/asinh measure.
#       NOTE: the pre-built `covid_dummy` variable in the source data is
#       actually a POST(>=2020) indicator, not a real case-based dummy (it is
#       1 for 100% of obs in 2020/2021/2022 alike) -- it is PERFECTLY
#       COLLINEAR with year FE and cannot be used. We construct our OWN
#       extensive-margin dummy `own_covid_dummy = 1[covid>0]` directly from
#       the case COUNT. Because every county has covid=0 in 2013-2019 and
#       covid>0 in 2020 & 2022 (100% of counties each of those years), the
#       ONLY within-year cross-sectional variation this dummy has is in 2021
#       (25.6% of counties report zero new cases that year) -- so this
#       specification is a weak/narrow test by construction, reported with
#       that caveat rather than presented as equivalent-power to (a)/(b).
# If direction and significance agree across (a)-(b) and the baseline, the
# main result is robust to the functional form of the exposure variable; (c)
# is included for completeness but under-powered.
# ============================================================================
source("/opt/data/research/Paper/新冠对务工的影响/revision2/scripts/00_common.R")
dt <- load_analysis()
dt0 <- dt[year<2023]

## zero-share diagnostics (for the write-up)
zero_share_all   <- mean(dt0$covid==0, na.rm=TRUE)
zero_share_20_22 <- mean(dt0[year>=2020 & year<=2022]$covid==0, na.rm=TRUE)
zero_share_2021  <- mean(dt0[year==2021]$covid==0, na.rm=TRUE)
cat(sprintf("Zero share of `covid`: all years = %.1f%%, 2020-2022 only = %.1f%%, 2021 only = %.1f%%\n",
            100*zero_share_all, 100*zero_share_20_22, 100*zero_share_2021))

## baseline (log(1+x), for reference)
m_base <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid + ",fc_full," | tid + year")),
                 dt0, cluster=~tid)

## (a) PPML on LEVELS
m_ppml <- fepois(as.formula(paste0("a_workday2 ~ lncovid + ",fc_full," | tid + year")),
                  dt0, cluster=~tid)

## (b) asinh(covid) exposure
dt0[, asinh_covid := asinh(covid)]
m_asinh <- feols(as.formula(paste0("ln_a_workday2 ~ asinh_covid + ",fc_full," | tid + year")),
                  dt0, cluster=~tid)

## (c) own-year extensive-margin dummy (see header note: weak, 2021-concentrated identification)
dt0[, own_covid_dummy := as.integer(covid>0)]
m_dummy <- feols(as.formula(paste0("ln_a_workday2 ~ own_covid_dummy + ",fc_full," | tid + year")),
                  dt0, cluster=~tid)

cat("\n=== Baseline (log(1+covid)) ===\n"); print(coeftable(m_base)["lncovid",c(1,2,4)])
cat("\n=== (a) PPML, levels outcome ===\n"); print(coeftable(m_ppml)["lncovid",c(1,2,4)])
cat("\n=== (b) asinh(covid) exposure ===\n"); print(coeftable(m_asinh)["asinh_covid",c(1,2,4)])
cat("\n=== (c) 1[covid>0] (own-year extensive margin, weak/2021-concentrated) ===\n")
print(coeftable(m_dummy)["own_covid_dummy",c(1,2,4)])

save_tab(list("Baseline: log(1+covid)"=m_base, "(a) PPML, levels"=m_ppml,
              "(b) asinh(covid)"=m_asinh, "(c) 1[covid>0], own-year"=m_dummy),
         "tab_functional_form.md",
         "Table R-FF. Functional-form robustness of the exposure variable (log(x+1) zero-value critique)",
         coef_map=c("lncovid"="Log(1+Covid)",
                    "asinh_covid"="asinh(Covid)","own_covid_dummy"="1[Covid>0] (extensive margin)"),
         notes=paste0("Note: SE clustered by township. * p<0.10, ** p<0.05, *** p<0.01. ",
                       "Zero share of `covid`: ", sprintf("%.1f%%",100*zero_share_all)," (all years), ",
                       sprintf("%.1f%%",100*zero_share_20_22)," (2020-2022). ",
                       "(a) PPML = Poisson pseudo-maximum-likelihood on workday LEVELS (fixest::fepois), coefficient is a semi-elasticity, same lncovid exposure as baseline. ",
                       "(b) keeps ln(workday) outcome, replaces the exposure transform lncovid -> asinh(covid). ",
                       "(c) 1[covid>0] is constructed directly from the case COUNT (NOT the pre-built `covid_dummy`, which is actually a post-2020 indicator collinear with year FE and unusable). Every county has covid=0 in 2013-2019 and covid>0 in ALL of 2020 and 2022, so column (c) is identified ONLY from within-2021 cross-sectional variation (",
                       sprintf("%.1f%%",100*zero_share_2021)," of counties report zero cases that year) -- a much weaker/narrower test than (a)/(b), reported for completeness rather than as an equal-power robustness check. ",
                       "Sample and controls identical to the baseline (year<2023, N as reported)."))

sink(file.path(O,"key_numbers_functional_form.txt"))
cat("Zero share (all years):",100*zero_share_all,"%\n")
cat("Zero share (2020-2022):",100*zero_share_20_22,"%\n")
cat("Zero share (2021 only):",100*zero_share_2021,"%\n\n")
cat("Baseline log(1+covid): "); print(coeftable(m_base)["lncovid",c(1,2,4)])
cat("PPML levels: "); print(coeftable(m_ppml)["lncovid",c(1,2,4)])
cat("asinh(covid): "); print(coeftable(m_asinh)["asinh_covid",c(1,2,4)])
cat("1[covid>0] (own-year, weak): "); print(coeftable(m_dummy)["own_covid_dummy",c(1,2,4)])
sink()
cat("\nDONE 04_functional_form.R\n")
