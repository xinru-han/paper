#!/usr/bin/env Rscript
# Extensive vs intensive margin decomposition of own-price elasticities.
# Observed elasticity = participation margin (probit Phi responds to price) +
# intensive margin (share|purchase). The latent system (Phi==1) removes the
# participation response. If the staple own-price elasticity collapses in the
# latent system, the large observed value is a purchase-INCIDENCE (stock-up
# timing) phenomenon for a storable good, not high consumption sensitivity.
suppressPackageStartupMessages(library(data.table))
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
source(file.path(base, "src", "pcyc_lib_v2.R"))
set.seed(101)
assign("PCYC_BASE", c("pcyc_bought_lag1","pcyc_recency","pcyc_nohist"), envir = globalenv())
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
ids <- sample(unique(panel$ID), 15000)
wide <- make_wide(add_purchase_cycle_vars(panel[ID %in% ids]), price_col = "lp_ext")
wt <- rep(1, nrow(wide))
sw <- compute_stone_weights(wide, wt)
wide <- derive_vars(wide, sw, omit = "G03")
wide <- add_mundlak(wide, omit = "G03")
fs <- fit_probits(wide, wt, omit = "G03")
pp <- predict_probits(wide, fs$betas, omit = "G03")
lay <- system_layout(omit = "G03", az = FALSE, y2p = FALSE)
fit <- fit_system(wide, lay, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2)

el_obs <- compute_elasticities(wide, lay, fit$beta, fs$betas, sw, wt, latent = FALSE)
el_lat <- compute_elasticities(wide, lay, fit$beta, fs$betas, sw, wt, latent = TRUE)

dt <- data.table(group = GROUPS9,
                 own_observed = round(diag(el_obs$all$mar), 3),
                 own_intensive_latent = round(diag(el_lat$all$mar), 3))
dt[, extensive_margin := round(own_observed - own_intensive_latent, 3)]
dt[, pct_from_extensive := round(100 * extensive_margin / own_observed, 0)]
cat("=== Own-price elasticity: extensive (participation/timing) vs intensive ===\n")
print(dt)
fwrite(dt, file.path(base, "outputs", "regularity", "margin_decomposition_v2.csv"), bom = TRUE)
cat("\n=== DONE margin decomp ===\n")
