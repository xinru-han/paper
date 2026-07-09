#!/usr/bin/env Rscript
# ============================================================================
# v2 step 38: final regularity assessment for the curvature-constrained model.
#  (a) Analytic elasticities at representative points (aggregate + subgroups):
#      latent EASI system evaluated at (wbar, ybar). Under the two-point
#      constraint the Slutsky matrix is NSD by construction -> curvature PASS.
#  (b) Household-month-level curvature: share of observations whose analytic
#      latent Slutsky matrix is NSD.
#  (c) Same representative-point evaluation for the unconstrained estimates,
#      to document what the constraint changes.
# ============================================================================

suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "demand")
rdir <- file.path(base, "outputs", "regularity")
SMOKE <- nzchar(Sys.getenv("SMOKE_V2"))

message("[38] Loading panel and constrained fit ...")
mc <- readRDS(file.path(odir, "main_fit_curv_v2.rds"))
lay <- mc$lay
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
wide <- make_wide(panel, price_col = "lp_ext")
rm(panel); gc(FALSE)
if (SMOKE) { set.seed(1); wide <- wide[ID %in% sample(unique(wide$ID), 3000)] }
wt <- rep(1, nrow(wide))
stone_w <- compute_stone_weights(wide, wt)
wide <- derive_vars(wide, stone_w, omit = lay$omit)
wide <- add_mundlak(wide, omit = lay$omit)

# representative shares = weighted mean PREDICTED LATENT shares (consistent
# with the latent-system coefficients; observed shares are Phi-scaled and
# would distort the elasticity denominators)
w_lat <- predict_shares(wide, lay, mc$beta, mc$probit_betas, stone_w, latent = TRUE)
w_lat_u <- predict_shares(wide, lay, mc$beta_unconstrained, mc$probit_betas, stone_w, latent = TRUE)
wmean_shares <- function(idx, M = w_lat) {
  W <- wt[idx]
  colSums(M[idx, , drop = FALSE] * W) / sum(W)
}
wmean_y <- function(idx) weighted.mean(wide$y_easi[idx], wt[idx])

xq <- cut(wide$total_food_spend_pc_month,
          quantile(wide$total_food_spend_pc_month, seq(0, 1, 0.2)), include.lowest = TRUE, labels = FALSE)
subgroups <- list(aggregate = rep(TRUE, nrow(wide)),
                  low_income = wide$low_income == 1,
                  non_low_income = wide$low_income == 0,
                  elderly = wide$elderly_household == 1,
                  non_elderly = wide$elderly_household == 0,
                  large_family = wide$large_family == 1,
                  small_family = wide$large_family == 0)
for (q in 1:5) subgroups[[paste0("xq", q)]] <- xq == q
for (q in 1:5) subgroups[[paste0("inc", q)]] <- wide$income_group_order == q

message("[38] (a) Representative-point analytic elasticities ...")
eig_rows <- list()
for (nm in names(subgroups)) {
  idx <- subgroups[[nm]]
  ae_c <- analytic_elasticities(mc$beta, lay, wmean_shares(idx), wmean_y(idx))
  ae_u <- analytic_elasticities(mc$beta_unconstrained, lay, wmean_shares(idx, w_lat_u), wmean_y(idx))
  eig_rows[[nm]] <- data.table(point = nm,
                               eig_max_constrained = max(ae_c$eigenvalues),
                               curvature_ok_constrained = ae_c$curvature_ok,
                               eig_max_unconstrained = max(ae_u$eigenvalues),
                               curvature_ok_unconstrained = ae_u$curvature_ok,
                               n = sum(idx))
}
eg <- rbindlist(eig_rows)
fwrite(eg, file.path(rdir, "curvature_representative_points_v2.csv"), bom = TRUE)
print(eg)

message("[38] (b) Household-month-level curvature check ...")
em_c <- household_curvature_check(wide, lay, mc$beta, mc$probit_betas, stone_w)
em_u <- household_curvature_check(wide, lay, mc$beta_unconstrained, mc$probit_betas, stone_w)
yq <- quantile(wide$y_easi, c(0.01, 0.99))
in_rng <- wide$y_easi >= yq[1] & wide$y_easi <= yq[2]
hh_chk <- data.table(
  statistic = c("share_nsd_constrained_all", "share_nsd_constrained_y_in_1_99",
                "share_nsd_unconstrained_all",
                "p50_eigmax_constrained", "p99_eigmax_constrained", "max_eigmax_constrained"),
  value = c(mean(em_c <= 1e-8), mean(em_c[in_rng] <= 1e-8), mean(em_u <= 1e-8),
            median(em_c), quantile(em_c, 0.99), max(em_c)))
fwrite(hh_chk, file.path(rdir, "household_curvature_check_v2.csv"), bom = TRUE)
print(hh_chk)
message("[38] Done.")
