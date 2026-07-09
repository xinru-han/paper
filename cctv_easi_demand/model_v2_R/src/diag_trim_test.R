#!/usr/bin/env Rscript
# Decisive test: does trimming thin/degenerate household-months tame the staple
# own-price elasticity? Fixed household subsample, estimate with vs without trim.
suppressPackageStartupMessages(library(data.table))
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
set.seed(101)

panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
# extra hh-month attributes we need for trimming (pc spend already lives in wide)
attr_cols <- unique(panel[, .(ID, year_month, total_food_transactions_month)],
                    by = c("ID","year_month"))
pc_all <- unique(panel[, .(ID, year_month, total_food_spend_pc_month)],
                 by = c("ID","year_month"))$total_food_spend_pc_month

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
  own <- diag(el$all$mar)
  cat(sprintf("\n[%s] n_hhmonth=%d\n", tag, nrow(wide)))
  print(round(setNames(own, GROUPS9), 3))
  print(round(setNames(el$all$exp, GROUPS9), 3))
  cat(sprintf("[%s] probit pseudoR2 G01=%.3f G09=%.3f | curvature_ok=%s\n",
              tag, fs$stats[code=="G01",pseudo_r2], fs$stats[code=="G09",pseudo_r2],
              el$all$curvature_ok))
  invisible(own)
}

# fixed household subsample for a clean comparison
ids <- sample(unique(panel$ID), 12000)
sub <- panel[ID %in% ids]
wide_full <- make_wide(sub, price_col = "lp_ext")
wide_full <- merge(wide_full, attr_cols, by = c("ID","year_month"), all.x = TRUE)

cat("################ BASELINE (no trim) ################\n")
estimate_own(copy(wide_full), "baseline")

# Trim A: drop thin months (< 5 transactions) — degenerate baskets
wa <- wide_full[total_food_transactions_month >= 5]
cat("\n################ TRIM A: >=5 transactions/month ################\n")
estimate_own(copy(wa), "trim>=5tx")

# Trim B: drop extreme pc spend tails (0.5%/99.5%) computed on full sample
lo <- quantile(pc_all, 0.005)
hi <- quantile(pc_all, 0.995)
wb <- wide_full[total_food_spend_pc_month > lo & total_food_spend_pc_month < hi]
cat(sprintf("\n################ TRIM B: pc spend in (%.1f, %.1f) ################\n", lo, hi))
estimate_own(copy(wb), "trimPC")

# Trim C: both
wc <- wide_full[total_food_transactions_month >= 5 &
                total_food_spend_pc_month > lo & total_food_spend_pc_month < hi]
cat("\n################ TRIM C: >=5 tx AND pc-trim ################\n")
estimate_own(copy(wc), "trimBoth")

cat("\n=== DONE trim test ===\n")
