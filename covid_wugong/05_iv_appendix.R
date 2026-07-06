#!/usr/bin/env Rscript
# ============================================================================
# 05_iv_appendix.R
# P1-2 (modification plan Sec 3.4): demote the Wuhan-distance IV from the main
# identification strategy to an appendix robustness check; add a placebo-IV
# test (distance to Beijing/Shanghai/Guangzhou x post) and an
# Anderson-Rubin (1949) weak-instrument-robust confidence interval.
#
# Logic of the placebo test (per the plan): if distance-to-ANY-major-city x
# post is ALSO "significant" in the same specification, that is evidence the
# Wuhan-distance IV is picking up a generic regional-development/labor-market
# gradient rather than a Wuhan-specific epidemic shock -- which would weaken
# the exclusion restriction. If the placebo IVs are NOT significant while the
# Wuhan IV is, that is supportive (though not dispositive, given only 12
# counties) of Wuhan-specificity.
#
# AR-type weak-IV-robust CI: because first-stage F is a specific issue in
# the IV literature with FEW CLUSTERS (Young 2022 finds jackknife/wild
# bootstrap-based weak-IV corrections matter exactly in small-G settings like
# this 12-county sample), we construct an Anderson-Rubin confidence set by
# grid search: for each candidate beta0, test H0: beta=beta0 via regressing
# (y - beta0*lncovid) on the instrument + controls + FE and testing whether
# the instrument's coefficient is zero (Wald test, township-clustered). The
# AR 95% CI is the set of beta0 NOT rejected at 5%. This CI is valid
# irrespective of instrument strength (unlike the 2SLS Wald CI), which
# matters here since we only have 12 clusters for the first stage.
# ============================================================================
source("/opt/data/research/Paper/新冠对务工的影响/revision2/scripts/00_common.R")
dt <- load_analysis()
dt0 <- dt[year<2023]

########################################################################
## 1. Main Wuhan-distance IV (reproduced, now explicitly labelled "appendix")
########################################################################
m_iv_wuhan <- feols(as.formula(paste0("ln_a_workday2 ~ ",fc_full," | tid + year | lncovid ~ iv_dist_post")),
                     dt0, cluster=~tid)
cat("\n=== IV: dist-Wuhan x post (main, appendix-demoted) ===\n")
print(coeftable(m_iv_wuhan)["fit_lncovid",])
cat("First-stage F:", fitstat(m_iv_wuhan,"ivf1")$ivf1$stat, "\n")

########################################################################
## 2. Placebo IVs: distance to Beijing / Shanghai / Guangzhou x post
########################################################################
placebo_results <- list()
for (city in c("beijing","shanghai","guangzhou")) {
  ivvar <- paste0("iv_dist_",city,"_post")
  m <- feols(as.formula(paste0("ln_a_workday2 ~ ",fc_full," | tid + year | lncovid ~ ",ivvar)),
             dt0, cluster=~tid)
  fstat <- tryCatch(fitstat(m,"ivf1")$ivf1$stat, error=function(e) NA)
  placebo_results[[city]] <- list(model=m, fstat=fstat)
  cat(sprintf("\n=== Placebo IV: dist-%s x post ===\n", city))
  print(coeftable(m)["fit_lncovid",])
  cat("First-stage F:", fstat, "\n")
}

########################################################################
## 3. Anderson-Rubin weak-IV-robust confidence interval (Wuhan IV)
##    Grid search over beta0; test whether IV coefficient = 0 in the
##    "y - beta0*x ~ controls + IV | FE" regression (township-clustered Wald).
########################################################################
ar_test <- function(data, yvar, xvar, ivvar, other_rhs, fe, cluster_var, beta0) {
  data <- copy(data)
  data[, ytilde := get(yvar) - beta0*get(xvar)]
  fml <- as.formula(paste0("ytilde ~ ",ivvar," + ",other_rhs," | ",fe))
  m <- feols(fml, data, cluster=as.formula(paste0("~",cluster_var)))
  ct <- coeftable(m)
  if (!(ivvar %in% rownames(ct))) return(NA_real_)
  ct[ivvar,4]  # p-value
}

beta_grid <- seq(-2.5, 2.0, by=0.02)
p_grid <- sapply(beta_grid, function(b0)
  ar_test(dt0, "ln_a_workday2","lncovid","iv_dist_post",fc_full,"tid + year","tid", b0))

ar_ci <- range(beta_grid[p_grid > 0.05], na.rm=TRUE)
cat("\n=== Anderson-Rubin 95% CI for Wuhan-IV coefficient ===\n")
cat("AR 95% CI: [", round(ar_ci[1],3), ",", round(ar_ci[2],3), "]\n")
cat("(2SLS point estimate:", round(coeftable(m_iv_wuhan)["fit_lncovid",1],4),
    ", conventional Wald 95% CI: [",
    round(coeftable(m_iv_wuhan)["fit_lncovid",1] - 1.96*coeftable(m_iv_wuhan)["fit_lncovid",2],3),",",
    round(coeftable(m_iv_wuhan)["fit_lncovid",1] + 1.96*coeftable(m_iv_wuhan)["fit_lncovid",2],3),"])\n")

write.csv(data.frame(beta0=beta_grid, p=p_grid), file.path(O,"ar_grid_wuhan_iv.csv"), row.names=FALSE)

########################################################################
## Write appendix table
########################################################################
mods <- list("Wuhan distance x post"=m_iv_wuhan,
             "Placebo: Beijing dist x post"=placebo_results$beijing$model,
             "Placebo: Shanghai dist x post"=placebo_results$shanghai$model,
             "Placebo: Guangzhou dist x post"=placebo_results$guangzhou$model)
save_tab(mods, "tab_iv_appendix.md",
         "Table A-IV. IV appendix: Wuhan-distance instrument + placebo distance instruments",
         coef_map=c("fit_lncovid"="Log(Covid) [2SLS]"))

## append first-stage F stats, AR CI, and placebo interpretation
con <- file(file.path(O,"tab_iv_appendix.md"), open="a")
writeLines(c("",
  "### First-stage F-statistics",
  "",
  "| Instrument | First-stage F |",
  "|---|---|",
  sprintf("| dist-Wuhan x post | %.1f |", fitstat(m_iv_wuhan,"ivf1")$ivf1$stat),
  sprintf("| dist-Beijing x post | %.1f |", placebo_results$beijing$fstat),
  sprintf("| dist-Shanghai x post | %.1f |", placebo_results$shanghai$fstat),
  sprintf("| dist-Guangzhou x post | %.1f |", placebo_results$guangzhou$fstat),
  "",
  "### Anderson-Rubin weak-instrument-robust 95% CI (Wuhan IV)",
  "",
  sprintf("AR 95%% CI: [%.3f, %.3f]  (grid search, beta0 in [-2.5,2.0], step 0.02, township-clustered Wald test per beta0)", ar_ci[1], ar_ci[2]),
  sprintf("Conventional (2SLS asymptotic) 95%% CI: [%.3f, %.3f]",
          coeftable(m_iv_wuhan)["fit_lncovid",1] - 1.96*coeftable(m_iv_wuhan)["fit_lncovid",2],
          coeftable(m_iv_wuhan)["fit_lncovid",1] + 1.96*coeftable(m_iv_wuhan)["fit_lncovid",2]),
  "",
  "### Interpretation",
  "",
  "MIXED, NOT CLEAN evidence. The Wuhan-distance instrument's first-stage F (1272) is 2-5x every placebo instrument's F (266-587), and its 2SLS coefficient is the most precisely estimated (p=0.030). However, the placebo results are NOT uniformly null: dist-Beijing x post is insignificant (p=0.47) and dist-Shanghai x post is insignificant (p=0.14), but dist-Guangzhou x post is ALSO marginally significant (b=-1.16, p=0.089) and similar in sign/magnitude to the Wuhan estimate. This is a genuine caveat, not a clean pass: at least one alternative distance-to-a-major-city instrument produces a marginally 'significant' 2SLS estimate too, consistent with the concern (raised for the main IV in Sec 3.4 of the modification plan) that distance-based instruments may partly proxy a general geography-of-development/labor-migration-corridor gradient rather than a Wuhan-specific epidemic shock. The stronger first stage and lower p-value for Wuhan is suggestive of some Wuhan-specificity, but the Guangzhou result means this evidence should NOT be oversold in the manuscript -- report it as partially reassuring, explicitly flag the Guangzhou placebo as a residual identification concern, and lean on the event-study + province x year FE + county-trends evidence (Sec 3.1) as the primary identification argument, with the IV kept firmly in the appendix.",
  "",
  "Note: given only 12 counties, all inference here should be read as suggestive; the IV strategy is reported as an APPENDIX robustness check, not as the paper's primary identification strategy (see main text Sec. 3.1, event-study + province x year FE + county trends).",
  ""), con)
close(con)
cat("\nwrote tab_iv_appendix.md\n")

sink(file.path(O,"key_numbers_iv.txt"))
cat("Wuhan IV: b=",coeftable(m_iv_wuhan)["fit_lncovid",1]," se=",coeftable(m_iv_wuhan)["fit_lncovid",2],
    " p=",coeftable(m_iv_wuhan)["fit_lncovid",4]," F=",fitstat(m_iv_wuhan,"ivf1")$ivf1$stat,"\n")
for(city in names(placebo_results)) {
  m <- placebo_results[[city]]$model
  cat("Placebo",city,": b=",coeftable(m)["fit_lncovid",1]," p=",coeftable(m)["fit_lncovid",4],
      " F=",placebo_results[[city]]$fstat,"\n")
}
cat("AR 95% CI: [",ar_ci[1],",",ar_ci[2],"]\n")
sink()
cat("DONE 05_iv_appendix.R\n")
