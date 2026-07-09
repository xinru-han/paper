#!/usr/bin/env Rscript
# ============================================================================
# v2 step 40: E-list robustness bundle — frequency aggregation, winsorization,
# basket-completeness screens, and the zero-consumption dual mechanism.
# Motivation: the monthly *purchase* elasticity of storable staples (rice/flour)
# overstates the *consumption* elasticity because purchases are lumpy (stock up
# when cheap). Aggregating to quarterly / annual frequency, and screening out
# thin-recording household-months, should pull the staple own-price elasticity
# toward the inelastic range a necessity implies.
#   F1_quarterly     : household-quarter aggregation
#   F2_annual        : household-year aggregation (consumption benchmark)
#   S1_minTx3/5/8    : keep hh-months with >= 3/5/8 recorded food transactions
#   W1_winsor_sh_1/2p5 : winsorize group budget shares at 1% / 2.5% per group
#   W2_winsor_exp_1/2p5: winsorize log real per-capita expenditure at 1% / 2.5%
#   Z1_ever_consumer : zero-consumption dual mechanism (Cragg double hurdle) —
#                      first hurdle = household is an in-sample consumer of the
#                      group; second hurdle = SY purchase-incidence probit among
#                      consumers. Structural-zero households enter with Phi = 0.
# All variants rerun the full two-step pipeline and report expenditure/own-price
# elasticities and Slutsky curvature next to the monthly main spec.
# ============================================================================

suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "robustness")
dir.create(odir, recursive = TRUE, showWarnings = FALSE)
SMOKE <- nzchar(Sys.getenv("SMOKE_V2"))
set.seed(20260709)

message("[40] Loading panel ...")
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
if (SMOKE) { keep <- sample(unique(panel$ID), 4000); panel <- panel[ID %in% keep] }

cov_cols <- c("cpi_yoy_prev_year_100","covid_daily_new_sum","holiday_days",
              "temp_avg_c_mean","precipitation_mm_sum","wholesale_agri_200_mean")

# ---- pipeline runner (same as 33) ------------------------------------------
run_pipeline <- function(wide, omit = "G03") {
  wt <- rep(1, nrow(wide))
  sw <- compute_stone_weights(wide, wt)
  wide <- derive_vars(wide, sw, omit = omit)
  wide <- add_mundlak(wide, omit = omit)
  fs <- fit_probits(wide, wt, omit = omit)
  pp <- predict_probits(wide, fs$betas, omit = omit)
  lay <- system_layout(omit = omit, az = FALSE, y2p = FALSE)
  fit <- fit_system(wide, lay, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2)
  el <- compute_elasticities(wide, lay, fit$beta, fs$betas, sw, wt)
  list(el = el$all, n_rows = nrow(wide), n_hh = uniqueN(wide$ID),
       pr2_g01 = fs$stats[code=="G01", pseudo_r2], pr2_g09 = fs$stats[code=="G09", pseudo_r2])
}
variant_row <- function(tag, res) {
  eig <- res$el$eigenvalues
  data.table(variant = tag, food_group10 = GROUPS9,
             expenditure = res$el$exp, own_price = diag(res$el$mar),
             own_negative = diag(res$el$mar) < 0,
             eig_max = max(eig), curvature_ok = res$el$curvature_ok,
             probit_r2_g01 = res$pr2_g01, probit_r2_g09 = res$pr2_g09,
             n_rows = res$n_rows, n_households = res$n_hh)
}

# ---- period aggregation (quarter / year) -----------------------------------
build_period_panel <- function(panel, period_col) {
  grp <- panel[, .(spend_month = sum(spend_month),
                   transaction_count_month = sum(transaction_count_month),
                   positive_purchase = as.integer(sum(spend_month) > 0),
                   lp_ext = mean(lp_ext), lp_hybrid = mean(lp_hybrid)),
               by = c("ID","Province", period_col, "food_group10","Family_Type",
                      "Family_Size","Family_Income","family_size_midpoint","family_size_oecd",
                      "income_group_order","low_income","elderly_household","large_family")]
  hmt <- panel[, lapply(.SD, mean), by = c("ID", period_col), .SDcols = cov_cols]
  tot <- grp[, .(total_food_spend_month = sum(spend_month),
                 total_food_transactions_month = sum(transaction_count_month)),
             by = c("ID", period_col)]
  grp <- merge(merge(grp, tot, by = c("ID", period_col)), hmt, by = c("ID", period_col))
  grp[, budget_share := spend_month / total_food_spend_month]
  grp[, total_food_spend_pc_month := total_food_spend_month / family_size_midpoint]
  grp[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]
  grp[, nut_spend_month := 0]
  setnames(grp, period_col, "year_month")
  hf <- unique(grp[, .(ID)]); hf[, fold := sample(rep(1:5, length.out = .N))]
  grp <- merge(grp, hf, by = "ID")
  grp[total_food_spend_month > 0]
}
panel[, yr := substr(year_month, 1, 4)]
panel[, mo := as.integer(substr(year_month, 6, 7))]
panel[, qtr := paste0(yr, "-Q", ((mo - 1) %/% 3) + 1)]

results <- list()

message("[40] Main monthly reference ...")
results[["M0_monthly_main"]] <- variant_row("M0_monthly_main",
    run_pipeline(make_wide(copy(panel), price_col = "lp_ext")))

message("[40] F1 quarterly ...")
results[["F1_quarterly"]] <- variant_row("F1_quarterly",
    run_pipeline(make_wide(build_period_panel(panel, "qtr"), price_col = "lp_ext")))

message("[40] F2 annual ...")
results[["F2_annual"]] <- variant_row("F2_annual",
    run_pipeline(make_wide(build_period_panel(panel, "yr"), price_col = "lp_ext")))

for (k in c(3L, 5L, 8L)) {
  message(sprintf("[40] S1 min transactions >= %d ...", k))
  results[[paste0("S1_minTx", k)]] <- variant_row(paste0("S1_minTx", k),
      run_pipeline(make_wide(panel[total_food_transactions_month >= k], price_col = "lp_ext")))
}

# ---- winsorization variants ------------------------------------------------
winsor_share_panel <- function(panel, q) {
  p2 <- copy(panel)
  p2[, budget_share := {
        lo <- quantile(budget_share, q, na.rm = TRUE)
        hi <- quantile(budget_share, 1 - q, na.rm = TRUE)
        pmin(pmax(budget_share, lo), hi)
      }, by = food_group10]
  # renormalize shares to sum to 1 within hh-month (winsor breaks adding-up)
  p2[, budget_share := budget_share / sum(budget_share), by = .(ID, year_month)]
  p2
}
for (q in c(0.01, 0.025)) {
  tag <- paste0("W1_winsor_sh_", sub("\\.", "p", as.character(q*100)))
  message(sprintf("[40] %s ...", tag))
  results[[tag]] <- variant_row(tag,
      run_pipeline(make_wide(winsor_share_panel(panel, q), price_col = "lp_ext")))
}
for (q in c(0.01, 0.025)) {
  tag <- paste0("W2_winsor_exp_", sub("\\.", "p", as.character(q*100)))
  message(sprintf("[40] %s ...", tag))
  p2 <- copy(panel)
  lo <- quantile(p2$log_total_food_spend_pc_month, q, na.rm = TRUE)
  hi <- quantile(p2$log_total_food_spend_pc_month, 1 - q, na.rm = TRUE)
  p2[, log_total_food_spend_pc_month := pmin(pmax(log_total_food_spend_pc_month, lo), hi)]
  p2[, total_food_spend_pc_month := exp(log_total_food_spend_pc_month)]
  results[[tag]] <- variant_row(tag, run_pipeline(make_wide(p2, price_col = "lp_ext")))
  rm(p2); gc(FALSE)
}

# ---- Z1 zero-consumption dual mechanism (Cragg double hurdle) --------------
# First hurdle: household is an in-sample consumer of the group (buys >=1 time).
# Second hurdle: SY purchase-incidence probit among consumer household-months.
# Structural-zero households (never buy g) get Phi_g = 0, phi_g = 0 in the
# system, so their zero share is a genuine corner, not a censored positive.
message("[40] Z1 zero-consumption dual mechanism (double hurdle) ...")
{
  p2 <- copy(panel)
  p2[, ever_buyer := as.integer(sum(positive_purchase) > 0), by = .(ID, food_group10)]
  wide <- make_wide(p2, price_col = "lp_ext")
  # cast ever_buyer to wide (one indicator per group)
  p2[, group_code := substr(food_group10, 1, 3)]
  eb <- dcast(p2, ID + year_month ~ group_code, value.var = "ever_buyer")
  setnames(eb, CODES9, paste0("eb_", CODES9), skip_absent = TRUE)
  wide <- merge(wide, eb, by = c("ID","year_month"), all.x = TRUE)
  for (cc in CODES9) wide[is.na(get(paste0("eb_",cc))), (paste0("eb_",cc)) := 0L]
  res <- local({
    omit <- "G03"; wt <- rep(1, nrow(wide))
    sw <- compute_stone_weights(wide, wt)
    wide <- derive_vars(wide, sw, omit = omit); wide <- add_mundlak(wide, omit = omit)
    fs <- fit_probits(wide, wt, omit = omit)
    pp <- predict_probits(wide, fs$betas, omit = omit)
    # apply first hurdle: zero out participation for structural non-consumers
    for (g in seq_along(CODES9)) {
      cc <- CODES9[g]; eb <- wide[[paste0("eb_", cc)]]
      pp$Phi[, cc] <- pp$Phi[, cc] * eb
      pp$phi[, cc] <- pp$phi[, cc] * eb
    }
    lay <- system_layout(omit = omit, az = FALSE, y2p = FALSE)
    fit <- fit_system(wide, lay, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2)
    el <- compute_elasticities(wide, lay, fit$beta, fs$betas, sw, wt)
    list(el = el$all, n_rows = nrow(wide), n_hh = uniqueN(wide$ID),
         pr2_g01 = fs$stats[code=="G01", pseudo_r2], pr2_g09 = fs$stats[code=="G09", pseudo_r2])
  })
  results[["Z1_dual_hurdle"]] <- variant_row("Z1_dual_hurdle", res)
  rm(p2, wide); gc(FALSE)
}

out <- rbindlist(results)
fwrite(out, file.path(odir, "robustness_freq_winsor_zero_v2.csv"), bom = TRUE)
cat("\n=== own-price elasticities by variant ===\n")
print(dcast(out, food_group10 ~ variant, value.var = "own_price"))
cat("\n=== staple (G01) own-price + probit R2 across variants ===\n")
print(out[food_group10 == "G01_主食", .(variant, own_price = round(own_price,3),
          probit_r2_g01 = round(probit_r2_g01,3), n_rows)])
message("[40] Done.")
