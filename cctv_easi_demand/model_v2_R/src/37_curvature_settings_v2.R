#!/usr/bin/env Rscript
# ============================================================================
# v2 step 37: compare curvature-imposition settings on the full sample.
# For each setting, report the numerical Slutsky eigenvalue range and own-
# price elasticities for BOTH the unconditional (participation-adjusted) and
# the latent (uncensored) system. Theory requires negativity of the LATENT
# Slutsky matrix; the unconditional SY expectation need not satisfy it.
# Settings: unconstrained | B only | single point at mean y | two-point 5/95
#           | two-point 1/99.
# ============================================================================

suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
rdir <- file.path(base, "outputs", "regularity")

message("[37] Loading panel and main fit ...")
main <- readRDS(file.path(base, "outputs", "demand", "main_fit_v2.rds"))
lay <- main$lay
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
wide <- make_wide(panel, price_col = "lp_ext")
rm(panel); gc(FALSE)
wt <- rep(1, nrow(wide))
stone_w <- compute_stone_weights(wide, wt)
wide <- derive_vars(wide, stone_w, omit = lay$omit)
wide <- add_mundlak(wide, omit = lay$omit)
pp <- predict_probits(wide, main$probit_betas, omit = lay$omit)

message("[37] One GLS solve with fixed Sigma (keeping normal equations) ...")
fit <- fit_system(wide, lay, pp$Phi, pp$phi, wt, Sigma = main$Sigma, keep_xtx_inv = TRUE)

yq <- quantile(wide$y_easi, c(0.01, 0.05, 0.95, 0.99))
ybar <- weighted.mean(wide$y_easi, wt)
message(sprintf("    y quantiles: 1%%=%.2f 5%%=%.2f mean=%.2f 95%%=%.2f 99%%=%.2f",
                yq[1], yq[2], ybar, yq[3], yq[4]))

settings <- list(
  unconstrained = NULL,
  B_only        = list(),
  mean_point    = list(y_lo = ybar - 1e-6, y_hi = ybar + 1e-6),
  two_point_5_95 = list(y_lo = yq[2], y_hi = yq[3]),
  two_point_1_99 = list(y_lo = yq[1], y_hi = yq[4])
)

xq <- cut(wide$total_food_spend_pc_month,
          quantile(wide$total_food_spend_pc_month, seq(0, 1, 0.2)), include.lowest = TRUE, labels = FALSE)
subg <- list(xq1 = xq == 1, xq5 = xq == 5)

rows <- list(); own_rows <- list()
for (nm in names(settings)) {
  s <- settings[[nm]]
  beta_s <- if (is.null(s)) fit$beta
            else if (length(s) == 0) impose_curvature(fit, lay)$beta
            else impose_curvature(fit, lay, y_lo = s$y_lo, y_hi = s$y_hi)$beta
  for (lat in c(FALSE, TRUE)) {
    el <- compute_elasticities(wide, lay, beta_s, main$probit_betas, stone_w, wt,
                               latent = lat, subgroups = subg)
    tag <- paste0(nm, if (lat) "_latent" else "_uncond")
    rows[[tag]] <- data.table(setting = nm, system = if (lat) "latent" else "unconditional",
                              point = c("aggregate","xq1","xq5"),
                              eig_max = c(max(el$all$eigenvalues),
                                          max(el$sub$xq1$eigenvalues),
                                          max(el$sub$xq5$eigenvalues)),
                              eig_min = c(min(el$all$eigenvalues),
                                          min(el$sub$xq1$eigenvalues),
                                          min(el$sub$xq5$eigenvalues)),
                              curvature_ok = c(el$all$curvature_ok,
                                               el$sub$xq1$curvature_ok,
                                               el$sub$xq5$curvature_ok))
    own_rows[[tag]] <- data.table(setting = nm, system = if (lat) "latent" else "unconditional",
                                  food_group10 = GROUPS9,
                                  own_price = diag(el$all$mar),
                                  expenditure = el$all$exp)
    message(sprintf("  %-28s eig_max(agg) = %8.4f  curv_ok = %s",
                    tag, max(el$all$eigenvalues), el$all$curvature_ok))
  }
}
res <- rbindlist(rows); own <- rbindlist(own_rows)
fwrite(res, file.path(rdir, "curvature_settings_comparison_v2.csv"), bom = TRUE)
fwrite(own, file.path(rdir, "curvature_settings_own_price_v2.csv"), bom = TRUE)
print(res)
print(dcast(own[system == "unconditional"], food_group10 ~ setting, value.var = "own_price"))
message("[37] Done.")
