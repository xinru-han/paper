#!/usr/bin/env Rscript
# Test: do purchase-cycle exclusion variables in the SY probit sharpen the weak
# staple/dairy participation stage and tame the staple own-price elasticity?
suppressPackageStartupMessages(library(data.table))
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
source(file.path(base, "src", "pcyc_lib_v2.R"))
set.seed(101)

panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
ids <- sample(unique(panel$ID), 12000)
sub <- panel[ID %in% ids]
sub <- add_purchase_cycle_vars(sub)

estimate_own <- function(wide, tag) {
  wt <- rep(1, nrow(wide))
  sw <- compute_stone_weights(wide, wt)
  wide <- derive_vars(wide, sw, omit = "G03")
  wide <- add_mundlak(wide, omit = "G03")
  fs <- fit_probits(wide, wt, omit = "G03")
  pp <- predict_probits(wide, fs$betas, omit = "G03")
  lay <- system_layout(omit = "G03", az = FALSE, y2p = FALSE)
  fit <- fit_system(wide, lay, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2)
  el <- compute_elasticities(wide, lay, fit$beta, fs$betas, sw, wt)
  cat(sprintf("\n[%s] n=%d\n own-price:\n", tag, nrow(wide)))
  print(round(setNames(diag(el$all$mar), GROUPS9), 3))
  cat(" probit pseudoR2:\n"); print(round(setNames(fs$stats$pseudo_r2, CODES9), 3))
  invisible(NULL)
}

cat("################ BASELINE (no pcyc) ################\n")
assign("PCYC_BASE", character(0), envir = globalenv())
estimate_own(make_wide(copy(sub), price_col = "lp_ext"), "baseline")

cat("\n################ + PURCHASE-CYCLE EXCLUSION VARS ################\n")
assign("PCYC_BASE", c("pcyc_bought_lag1","pcyc_recency","pcyc_nohist"), envir = globalenv())
estimate_own(make_wide(copy(sub), price_col = "lp_ext"), "pcyc")

cat("\n=== DONE pcyc test ===\n")
