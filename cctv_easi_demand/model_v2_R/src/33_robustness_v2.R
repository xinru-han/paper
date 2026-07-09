#!/usr/bin/env Rscript
# ============================================================================
# v2 step 33: robustness matrix. Each variant reruns the full two-step
# pipeline (probits -> FGLS system -> elasticities incl. participation
# margin) and reports expenditure elasticities, own-price elasticities and
# Slutsky curvature next to the main specification.
#   R1_no_time_fe    : mechanism demo — drop month/year FE (expected to
#                      degrade signs; documents why FE matter)
#   R2_hybrid        : lp_hybrid price (fold-specific internal signal blended,
#                      lambda=0.25, admissible groups only; leak-free — the
#                      internal component excludes the household's own fold)
#   R4_drop_lockdown : drop 2020-02..04 and 2022-04..05 (COVID lockdowns)
#   R5_oecd_scale    : OECD equivalence scale instead of per-capita
#   R6_min_spend20   : drop household-months with total food spend < 20 yuan
#   R7_iterated_stone: one Stone iteration using fitted province-month shares
#   R8_trim1pct      : trim 1%/99% tails of log real food expenditure
#   R9_priced_subbasket: budget shares narrowed to the externally priced
#                      sub-basket (coverage-mismatch check, cf. price_coverage)
# (R3 EASI-y2p — the y^2 x price functional-form variant — is produced by 32.)
# ============================================================================

suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "robustness")
dir.create(odir, recursive = TRUE, showWarnings = FALSE)
SMOKE <- nzchar(Sys.getenv("SMOKE_V2"))

message("[33] Loading panel ...")
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
if (SMOKE) {
  set.seed(1)
  keep <- sample(unique(panel$ID), 3000)
  panel <- panel[ID %in% keep]
}

run_pipeline <- function(wide, omit = "G03", stone_from_pred = FALSE) {
  wt <- rep(1, nrow(wide))
  sw <- compute_stone_weights(wide, wt)
  wide <- derive_vars(wide, sw, omit = omit)
  wide <- add_mundlak(wide, omit = omit)
  fs <- fit_probits(wide, wt, omit = omit)
  pp <- predict_probits(wide, fs$betas, omit = omit)
  lay <- system_layout(omit = omit, az = FALSE, y2p = FALSE)
  fit <- fit_system(wide, lay, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2)
  if (stone_from_pred) {
    pred <- predict_shares(wide, lay, fit$beta, fs$betas, sw)
    tmp <- data.table(Province = wide$Province, year_month = wide$year_month, pred)
    setnames(tmp, CODES9, paste0("sw_", CODES9))
    sw <- tmp[, lapply(.SD, mean), by = .(Province, year_month),
              .SDcols = paste0("sw_", CODES9)]
    wide <- derive_vars(wide, sw, omit = omit)
    wide <- add_mundlak(wide, omit = omit)
    fs <- fit_probits(wide, wt, omit = omit, beta0_list = fs$betas)
    pp <- predict_probits(wide, fs$betas, omit = omit)
    fit <- fit_system(wide, lay, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2)
  }
  el <- compute_elasticities(wide, lay, fit$beta, fs$betas, sw, wt)
  list(el = el$all, n_rows = nrow(wide), n_hh = uniqueN(wide$ID))
}

variant_row <- function(tag, res) {
  eig <- res$el$eigenvalues
  data.table(variant = tag, food_group10 = GROUPS9,
             expenditure = res$el$exp, own_price = diag(res$el$mar),
             own_negative = diag(res$el$mar) < 0,
             eig_max = max(eig), curvature_ok = res$el$curvature_ok,
             n_rows = res$n_rows, n_households = res$n_hh)
}

results <- list()

message("[33] R1: no time FE (mechanism demo) ...")
{
  MONTH_D_SAVE <- MONTH_D; YEAR_D_SAVE <- YEAR_D
  assign("MONTH_D", character(0), envir = globalenv())
  assign("YEAR_D",  character(0), envir = globalenv())
  wide <- make_wide(copy(panel), price_col = "lp_ext")
  results[["R1_no_time_fe"]] <- variant_row("R1_no_time_fe", run_pipeline(wide))
  assign("MONTH_D", MONTH_D_SAVE, envir = globalenv())
  assign("YEAR_D",  YEAR_D_SAVE,  envir = globalenv())
  rm(wide); gc(FALSE)
}

message("[33] R2: hybrid price (lambda=0.25, admissible groups) ...")
{
  wide <- make_wide(copy(panel), price_col = "lp_hybrid")
  results[["R2_hybrid"]] <- variant_row("R2_hybrid", run_pipeline(wide))
  rm(wide); gc(FALSE)
}

message("[33] R4: drop lockdown months ...")
{
  drop_m <- c("2020-02","2020-03","2020-04","2022-04","2022-05")
  wide <- make_wide(panel[!(year_month %in% drop_m)], price_col = "lp_ext")
  results[["R4_drop_lockdown"]] <- variant_row("R4_drop_lockdown", run_pipeline(wide))
  rm(wide); gc(FALSE)
}

message("[33] R5: OECD equivalence scale ...")
{
  p2 <- copy(panel)
  p2[, total_food_spend_pc_month := total_food_spend_month / family_size_oecd]
  p2[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]
  wide <- make_wide(p2, price_col = "lp_ext")
  results[["R5_oecd_scale"]] <- variant_row("R5_oecd_scale", run_pipeline(wide))
  rm(wide, p2); gc(FALSE)
}

message("[33] R6: minimum spend 20 yuan ...")
{
  wide <- make_wide(panel[total_food_spend_month >= 20], price_col = "lp_ext")
  results[["R6_min_spend20"]] <- variant_row("R6_min_spend20", run_pipeline(wide))
  rm(wide); gc(FALSE)
}

message("[33] R7: iterated Stone deflator ...")
{
  wide <- make_wide(copy(panel), price_col = "lp_ext")
  results[["R7_iterated_stone"]] <- variant_row("R7_iterated_stone",
                                                run_pipeline(wide, stone_from_pred = TRUE))
  rm(wide); gc(FALSE)
}

message("[33] R8: trim 1%/99% expenditure tails ...")
{
  qs <- quantile(panel$log_total_food_spend_pc_month, c(0.01, 0.99), na.rm = TRUE)
  wide <- make_wide(panel[log_total_food_spend_pc_month %between% qs], price_col = "lp_ext")
  results[["R8_trim1pct"]] <- variant_row("R8_trim1pct", run_pipeline(wide))
  rm(wide); gc(FALSE)
}

message("[33] R9: budget shares narrowed to the priced sub-basket ...")
{
  # The group price index only covers externally observed categories; here the
  # dependent shares are narrowed to that same sub-basket so price and share
  # coverage coincide (addresses coverage mismatch, worst for dairy).
  p2 <- copy(panel)
  p2[is.na(spend_month_priced), spend_month_priced := 0]   # zero-purchase rows
  p2[, spend_month := spend_month_priced]
  p2[, total_food_spend_month := sum(spend_month), by = .(ID, year_month)]
  p2 <- p2[total_food_spend_month > 0]
  p2[, budget_share := spend_month / total_food_spend_month]
  p2[, positive_purchase := as.integer(spend_month > 0)]
  p2[, total_food_spend_pc_month := total_food_spend_month / family_size_midpoint]
  p2[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]
  wide <- make_wide(p2, price_col = "lp_ext")
  results[["R9_priced_subbasket"]] <- variant_row("R9_priced_subbasket", run_pipeline(wide))
  rm(wide, p2); gc(FALSE)
}

out <- rbindlist(results)
fwrite(out, file.path(odir, "robustness_matrix_v2.csv"), bom = TRUE)
print(dcast(out, food_group10 ~ variant, value.var = "own_price"))
print(unique(out[, .(variant, eig_max, curvature_ok)]))
message("[33] Done.")
