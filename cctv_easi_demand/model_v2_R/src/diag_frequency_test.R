#!/usr/bin/env Rscript
# Decisive test of the storability hypothesis: does aggregating from monthly to
# quarterly / annual frequency shrink the staple own-price elasticity toward the
# inelastic range a necessity should show? Storable staples (rice/flour) are
# bought lumpily, so monthly *purchase* elasticity overstates *consumption*
# elasticity; time aggregation averages out stock-up timing.
suppressPackageStartupMessages(library(data.table))
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
set.seed(101)

panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")

# quarter / year keys
panel[, yr := substr(year_month, 1, 4)]
panel[, mo := as.integer(substr(year_month, 6, 7))]
panel[, qtr := paste0(yr, "-Q", ((mo - 1) %/% 3) + 1)]

# covariate columns carried at province-time level (means when aggregating)
cov_cols <- c("cpi_yoy_prev_year_100","covid_daily_new_sum","holiday_days",
              "temp_avg_c_mean","precipitation_mm_sum","wholesale_agri_200_mean")

build_period_panel <- function(panel, period_col) {
  # group-level spend + purchase over the period
  grp <- panel[, .(spend_month = sum(spend_month),
                   transaction_count_month = sum(transaction_count_month),
                   positive_purchase = as.integer(sum(spend_month) > 0),
                   lp_ext = mean(lp_ext),                 # period-mean log price
                   lp_hybrid = mean(lp_hybrid)),
               by = c("ID","Province", period_col, "food_group10",
                      "Family_Type","Family_Size","Family_Income","family_size_midpoint",
                      "family_size_oecd","income_group_order","low_income",
                      "elderly_household","large_family")]
  # hh-period covariates (period means)
  hmt <- panel[, lapply(.SD, mean), by = c("ID", period_col), .SDcols = cov_cols]
  tot <- grp[, .(total_food_spend_month = sum(spend_month),
                 total_food_transactions_month = sum(transaction_count_month)),
             by = c("ID", period_col)]
  grp <- merge(grp, tot, by = c("ID", period_col))
  grp <- merge(grp, hmt, by = c("ID", period_col))
  grp[, budget_share := spend_month / total_food_spend_month]
  grp[, total_food_spend_pc_month := total_food_spend_month / family_size_midpoint]
  grp[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]
  grp[, nut_spend_month := 0]
  setnames(grp, period_col, "year_month")           # reuse make_wide machinery
  # fold by household
  hf <- unique(grp[, .(ID)]); hf[, fold := sample(rep(1:5, length.out = .N))]
  grp <- merge(grp, hf, by = "ID")
  grp <- grp[total_food_spend_month > 0]
  grp
}

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
  cat(sprintf("\n[%s] n_obs=%d  staple purchase rate=%.3f\n", tag, nrow(wide),
              mean(wide$pos_G01)))
  cat("own-price:\n"); print(round(setNames(own, GROUPS9), 3))
  cat(sprintf("[%s] probit pseudoR2 G01=%.3f G09=%.3f\n", tag,
              fs$stats[code=="G01",pseudo_r2], fs$stats[code=="G09",pseudo_r2]))
  invisible(own)
}

cat("################ MONTHLY (reference, full sample) ################\n")
wm <- make_wide(panel, price_col = "lp_ext")
estimate_own(wm, "monthly"); rm(wm); gc(FALSE)

cat("\n################ QUARTERLY aggregation ################\n")
pq <- build_period_panel(panel, "qtr")
wq <- make_wide(pq, price_col = "lp_ext")
estimate_own(wq, "quarterly"); rm(pq, wq); gc(FALSE)

cat("\n################ ANNUAL aggregation ################\n")
pa <- build_period_panel(panel, "yr")
wa <- make_wide(pa, price_col = "lp_ext")
estimate_own(wa, "annual"); rm(pa, wa); gc(FALSE)

cat("\n=== DONE frequency test ===\n")
