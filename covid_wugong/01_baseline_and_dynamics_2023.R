#!/usr/bin/env Rscript
# ============================================================================
# 01_baseline_and_dynamics_2023.R
# P0-1 (modification plan Sec 3.1): fix the lead-construction bug and use the
# recovered 2023 outcome year to directly test post-reopening persistence.
#
# Produces:
#   output/tab_baseline_replication.md   -- sanity check vs revision/ (unchanged sample/vars)
#   output/tab_dynamics_2023.md          -- lead effects t / t+1 / t+2, now with 2022->2023 populated
#   output/tab_2023_persistence.md       -- (a) 2022 cum. exposure -> 2023 workdays (cross-section)
#                                            (b) event study extended through 2023 (panel)
#   figures/fig_event_study.png          -- publication-quality event-study plot, 2013-2023
#   output/key_numbers_2023.txt
#
# NOTE on FE choice for the 2023-only cross-section (Sec 2a below): ln_exposure2022
# is a TIME-INVARIANT COUNTY-level variable. In the full panel it is identified via
# its interaction with year (i(year,...)) net of township+year FE. In a single
# cross-section (year==2023 only) there is no time dimension left, and it has ZERO
# within-township variation (every township belongs to exactly one county), so a
# tid FE spec drops it by collinearity. We use province (pid) FE instead -- 12
# counties nest within 4 provinces (~3 counties/province), so cross-county variation
# survives -- and cluster at the county (xid) level, the natural level of the
# regressor (a wild-bootstrap version follows in 02_inference_robustness.R since
# 12 clusters is few).
# ============================================================================
source("/opt/data/research/Paper/新冠对务工的影响/revision2/scripts/00_common.R")
dt <- load_analysis()

########################################################################
## 0. Baseline replication sanity check (year<2023, ctrl_full, matches revision/)
########################################################################
dt0 <- dt[year<2023]
m_base_check <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid + ",fc_full," | tid + year")),
                       dt0, cluster=~tid)
cat("\n=== BASELINE REPLICATION CHECK (should match revision/: b=-0.1186, se=0.0424, N=13787) ===\n")
print(coeftable(m_base_check)["lncovid",])
save_tab(list("Baseline (replication)"=m_base_check), "tab_baseline_replication.md",
         "Table R0. Baseline replication check (year<2023, identical to revision/06_analysis.R)",
         coef_map=c("lncovid"="Log(Covid)"))

########################################################################
## 1. Dynamics (lead) effects, FIXED: lead constructed pre-filter, so
##    2022 exposure -> 2023 outcome is now populated for t+1 (was NA before).
########################################################################
dt_dyn <- dt[!is.na(lncovid)]     # exposure must be defined -> excludes year==2023 as LHS-exposure row
m_l0 <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid + ",fc_full," | tid + year")), dt_dyn, cluster=~tid)
m_l1 <- feols(as.formula(paste0("lead1 ~ lncovid + ",fc_full," | tid + year")), dt_dyn, cluster=~tid)
m_l2 <- feols(as.formula(paste0("lead2 ~ lncovid + ",fc_full," | tid + year")), dt_dyn, cluster=~tid)
cat("\n=== DYNAMICS (fixed: 2022 exposure -> 2023 outcome now included in t+1) ===\n")
for(m in list(m_l0,m_l1,m_l2)) print(coeftable(m)["lncovid",c(1,2,4)])
save_tab(list("t (contemp.)"=m_l0,"t+1"=m_l1,"t+2"=m_l2),
         "tab_dynamics_2023.md","Table R2 (updated). Dynamic (lead) effects — persistence, 2022→2023 lead now populated",
         coef_map=c("lncovid"="Log(Covid)"),
         notes="Note: SE clustered by township. * p<0.10, ** p<0.05, *** p<0.01. Fixed vs. revision/06_analysis.R: leads are constructed on the FULL 2013-2023 panel before any year filter, so 2022-exposure -> 2023-outcome populates t+1 (previously discarded as NA). t+1 sample now includes 2022-exposure rows whose lead outcome is observed in 2023.")

########################################################################
## 2a. Direct persistence test: 2022 cumulative exposure -> 2023 workdays
##     (cross-section; province FE — see header note on why tid FE is invalid here)
########################################################################
d23 <- dt[year==2023]
d22exp <- dt[year==2022, .(nid, lncovid_2022=lncovid)]
d23 <- merge(d23, d22exp, by="nid", all.x=TRUE)
m_2022to2023_cum <- feols(as.formula(paste0("ln_a_workday2 ~ ln_exposure2022 + ",fc_2023," | pid")),
                           d23, cluster=~xid)
m_2022to2023_cur <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid_2022 + ",fc_2023," | pid")),
                           d23[!is.na(lncovid_2022)], cluster=~xid)
cat("\n=== 2023 PERSISTENCE: 2022-cum.exposure -> 2023 workdays (province FE, county-clustered) ===\n")
print(coeftable(m_2022to2023_cum)["ln_exposure2022",c(1,2,4)])
cat("\n=== 2023 PERSISTENCE: 2022-current-year covid -> 2023 workdays ===\n")
print(coeftable(m_2022to2023_cur)["lncovid_2022",c(1,2,4)])

########################################################################
## 2b. Event study extended through 2023 (cross-sectional exposure gradient
##     x year, ref 2019). Uses ln_exposure2022 (time-invariant, available in 2023).
##     This IS identified with tid+year FE because year variation lets the
##     interaction move within-township across years.
########################################################################
m_es_full <- feols(ln_a_workday2 ~ i(year, ln_exposure2022, ref=2019) +
                    .[ctrl_2023] | tid + year, dt, cluster=~tid)
es <- coeftable(m_es_full)
es_yr <- es[grep("year::",rownames(es)),,drop=FALSE]
cat("\n=== EVENT STUDY (exposure x year, ref 2019), extended to 2023 ===\n")
print(es_yr[,c(1,2,4)])

## pre-trend joint test: 2013-2018 coefficients jointly zero
pre_terms <- grep("year::(2013|2014|2015|2016|2017|2018):", rownames(es), value=TRUE)
wt <- wald(m_es_full, keep = pre_terms)
cat("\nJoint Wald test, pre-period (2013-2018) coefficients = 0:\n")
print(wt)

save_tab(list("Event study (2013-2023)"=m_es_full), "tab_2023_persistence.md",
         "Table R2b. Event study extended through 2023 (exposure x year interactions, ref=2019)")

## Append the direct persistence regressions & pre-trend test to the same file
con <- file(file.path(O,"tab_2023_persistence.md"), open="a")
writeLines(c("",
  "### Direct persistence test: 2022 exposure -> 2023 outcome (cross-section, province FE, county-clustered SE)",
  "",
  "| Model | Coefficient | Estimate | SE | p |",
  "|---|---|---|---|---|",
  sprintf("| 2022 cum. exposure ln(1+cases) -> 2023 ln(workday2) | ln_exposure2022 | %.4f | %.4f | %.4f |",
          coeftable(m_2022to2023_cum)["ln_exposure2022",1],
          coeftable(m_2022to2023_cum)["ln_exposure2022",2],
          coeftable(m_2022to2023_cum)["ln_exposure2022",4]),
  sprintf("| 2022 current-year lncovid -> 2023 ln(workday2) | lncovid_2022 | %.4f | %.4f | %.4f |",
          coeftable(m_2022to2023_cur)["lncovid_2022",1],
          coeftable(m_2022to2023_cur)["lncovid_2022",2],
          coeftable(m_2022to2023_cur)["lncovid_2022",4]),
  "",
  sprintf("N(2022 cum exposure model)=%d; N(2022 current covid model)=%d. FE: province (pid); SE clustered by county (xid, 11-12 clusters -- see wild-bootstrap version in tab_inference_robustness.md).",
          nobs(m_2022to2023_cum), nobs(m_2022to2023_cur)),
  "",
  "### Pre-trend joint test (2013-2018 event-study coefficients = 0)",
  "",
  sprintf("Wald F = %.3f, df1 = %d, df2 = %d, p = %.4f",
          wt$stat, wt$df1, wt$df2, wt$p),
  "",
  "Note: exposure = ln(1+cumulative confirmed cases through 2022) x year dummy, ref=2019, township+year FE, controls (ctrl_2023, road_density2 excluded because 100% missing in 2023).",
  ""), con)
close(con)

########################################################################
## 3. Publication-quality event-study figure (2013-2023), with 95% CI
########################################################################
plot_df <- data.frame(
  year = as.integer(gsub("year::(\\d+):ln_exposure2022","\\1", rownames(es_yr))),
  est  = es_yr[,1], se = es_yr[,2]
)
ref_row <- data.frame(year=2019, est=0, se=0)
plot_df <- rbind(plot_df, ref_row)
plot_df <- plot_df[order(plot_df$year),]
plot_df$lo <- plot_df$est - 1.96*plot_df$se
plot_df$hi <- plot_df$est + 1.96*plot_df$se

write.csv(plot_df, file.path(O,"event_study_coefs.csv"), row.names=FALSE)

sink(file.path(O,"key_numbers_2023.txt"))
cat("Baseline replication check (year<2023):\n"); print(coeftable(m_base_check)["lncovid",])
cat("\nDynamics (fixed, 2022->2023 populated):\n")
cat("t   :"); print(coeftable(m_l0)["lncovid",c(1,2,4)])
cat("t+1 :"); print(coeftable(m_l1)["lncovid",c(1,2,4)])
cat("t+2 :"); print(coeftable(m_l2)["lncovid",c(1,2,4)])
cat("\n2023 direct persistence (2022 cum exposure -> 2023 outcome, province FE):\n")
print(coeftable(m_2022to2023_cum)["ln_exposure2022",c(1,2,4)])
cat("N =", nobs(m_2022to2023_cum), "\n")
cat("\n2023 direct persistence (2022 current-year covid -> 2023 outcome, province FE):\n")
print(coeftable(m_2022to2023_cur)["lncovid_2022",c(1,2,4)])
cat("N =", nobs(m_2022to2023_cur), "\n")
cat("\nEvent study coefficients (ref=2019):\n"); print(plot_df)
cat("\nPre-trend (2013-2018) joint Wald test: F=",wt$stat," df1=",wt$df1," df2=",wt$df2," p=",wt$p,"\n")
sink()

cat("\nDONE 01_baseline_and_dynamics_2023.R\n")
