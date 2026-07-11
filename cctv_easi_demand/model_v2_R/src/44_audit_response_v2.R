#!/usr/bin/env Rscript
# ============================================================================
# v2 step 44: audit-response diagnostics for the AJAE/Food Policy econometric
# review. These outputs make the remaining identification limits explicit and
# provide Food Policy-oriented robustness checks for monthly PURCHASE demand.
# ============================================================================

suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "audit")
dir.create(odir, recursive = TRUE, showWarnings = FALSE)
SMOKE <- nzchar(Sys.getenv("SMOKE_V2"))

message("[44] Loading panel and rebuilding main wide data ...")
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"),
               encoding = "UTF-8")
if (SMOKE) {
  set.seed(44)
  keep <- sample(unique(panel$ID), 4000)
  panel <- panel[ID %in% keep]
}
wide <- make_wide(panel, price_col = "lp_ext")
wt <- rep(1, nrow(wide))
sw <- compute_stone_weights(wide, wt)
wide <- derive_vars(wide, sw, omit = "G03")
wide <- add_mundlak(wide, omit = "G03")

price_cells <- panel[, .(n_household_month_group_rows = .N,
                         n_households = uniqueN(ID)),
                     by = .(Province, year_month, food_group10)]
fwrite(price_cells[, .(n_provinces = uniqueN(Province),
                       n_months = uniqueN(year_month),
                       n_province_month_group_cells = .N,
                       mean_households_per_cell = mean(n_households),
                       min_households_per_cell = min(n_households),
                       max_households_per_cell = max(n_households)),
                   by = food_group10],
       file.path(odir, "price_identification_cells_v2.csv"), bom = TRUE)

# ---------------------------------------------------------------------------
# A1 diagnostic: expenditure control-function sensitivity.
# Instruments are household income/size categories excluded from the share
# equation in the baseline, conditional on prices, demographics, controls,
# province and time effects. This is a sensitivity design, not a definitive IV
# solution; the manuscript labels it accordingly.
# ---------------------------------------------------------------------------
message("[44] Expenditure first stages and control-function system ...")
eq_codes <- setdiff(CODES9, "G03")
r_cols <- paste0("r_", eq_codes)
base_cols <- c(r_cols, DEMO_COLS, Z_COLS, MONTH_D, YEAR_D, "Province")
inst_cols <- c("Family_Income", "Family_Size", "income_group_order")
mk_formula <- function(y, cols, inst = FALSE) {
  rhs <- c(cols[cols != "Province"], "factor(Province)")
  if (inst) rhs <- c(rhs, "factor(Family_Income)", "factor(Family_Size)",
                    "factor(income_group_order)")
  as.formula(paste(y, "~", paste(rhs, collapse = " + ")))
}
fit_restr_y <- lm(mk_formula("y_easi", base_cols, FALSE), data = wide)
fit_full_y  <- lm(mk_formula("y_easi", base_cols, TRUE),  data = wide)
fit_restr_y2 <- lm(mk_formula("y_easi2", base_cols, FALSE), data = wide)
fit_full_y2  <- lm(mk_formula("y_easi2", base_cols, TRUE),  data = wide)
partial_r2 <- function(r, f) (sum(resid(r)^2) - sum(resid(f)^2)) / sum(resid(r)^2)
p_floor <- function(p) pmax(p, .Machine$double.xmin, na.rm = TRUE)
fa_y <- tryCatch(anova(fit_restr_y, fit_full_y), error = function(e) NULL)
fa_y2 <- tryCatch(anova(fit_restr_y2, fit_full_y2), error = function(e) NULL)
diag_iv <- rbind(
  data.table(endogenous = "y_easi", partial_r2 = partial_r2(fit_restr_y, fit_full_y),
             first_stage_F = if (!is.null(fa_y)) fa_y$F[2] else NA_real_,
             p_value = if (!is.null(fa_y)) p_floor(fa_y$`Pr(>F)`[2]) else NA_real_),
  data.table(endogenous = "y_easi2", partial_r2 = partial_r2(fit_restr_y2, fit_full_y2),
             first_stage_F = if (!is.null(fa_y2)) fa_y2$F[2] else NA_real_,
             p_value = if (!is.null(fa_y2)) p_floor(fa_y2$`Pr(>F)`[2]) else NA_real_)
)
fwrite(diag_iv, file.path(odir, "expenditure_first_stage_diagnostics_v2.csv"), bom = TRUE)

wide[, cf_y := resid(fit_full_y)]
wide[, cf_y2 := resid(fit_full_y2)]
fs <- fit_probits(wide, wt, omit = "G03")
pp <- predict_probits(wide, fs$betas, omit = "G03")
lay0 <- system_layout(omit = "G03", az = FALSE, y2p = FALSE)
fit0 <- fit_system(wide, lay0, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2,
                   keep_xtx_inv = TRUE)
el0 <- compute_elasticities(wide, lay0, fit0$beta, fs$betas, sw, wt)

assign("EXTRA_BASE_COLS", c("cf_y", "cf_y2"), envir = globalenv())
lay_cf <- system_layout(omit = "G03", az = FALSE, y2p = FALSE)
fit_cf <- fit_system(wide, lay_cf, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2,
                     keep_xtx_inv = TRUE)
el_cf <- compute_elasticities(wide, lay_cf, fit_cf$beta, fs$betas, sw, wt)
Vcf <- system_cluster_vcov(wide, lay_cf, pp$Phi, pp$phi, wt, fit_cf$beta,
                           fit_cf$Sigma, fit_cf$xtx_inv, cluster = wide$Province)
cf_idx <- grep("__(cf_y|cf_y2)$", lay_cf$term_names)
Wcf <- tryCatch(as.numeric(t(fit_cf$beta[cf_idx]) %*%
                    solve(Vcf[cf_idx, cf_idx], fit_cf$beta[cf_idx])),
                error = function(e) NA_real_)
cf_p <- if (is.finite(Wcf)) pchisq(Wcf, length(cf_idx), lower.tail = FALSE) else NA_real_
fwrite(data.table(test = "control_function_residuals_joint_zero",
                  method = "province_cluster_CR1_Wald",
                  stat = Wcf, df = length(cf_idx), p_value = cf_p),
       file.path(odir, "expenditure_control_function_dwh_v2.csv"), bom = TRUE)
fwrite(data.table(food_group10 = GROUPS9,
                  own_price_fgls = diag(el0$all$mar),
                  own_price_cf = diag(el_cf$all$mar),
                  diff_cf_minus_fgls = diag(el_cf$all$mar) - diag(el0$all$mar)),
       file.path(odir, "control_function_own_price_compare_v2.csv"), bom = TRUE)
assign("EXTRA_BASE_COLS", character(0), envir = globalenv())

# ---------------------------------------------------------------------------
# A4 exclusion checks: do purchase-cycle variables also enter the share equation?
# Per equation auxiliary OLS with the same broad controls; this is a diagnostic
# for the exclusion restriction, not the production estimator.
# ---------------------------------------------------------------------------
message("[44] Purchase-cycle exclusion diagnostics ...")
excl <- rbindlist(lapply(CODES9, function(cc) {
  pc <- paste0(PCYC_BASE, "_", cc)
  pc <- pc[pc %in% names(wide)]
  if (!length(pc)) return(data.table(code = cc, n_pc_terms = 0L,
                                     F_stat = NA_real_, p_value = NA_real_))
  y <- paste0("w_", cc)
  rhs0 <- c("y_easi", "y_easi2", r_cols, DEMO_COLS, Z_COLS, MONTH_D, YEAR_D,
            "mean_y_hh", paste0("mn_r_", eq_codes))
  rhs0 <- rhs0[rhs0 %in% names(wide)]
  f0 <- as.formula(paste(y, "~", paste(rhs0, collapse = " + ")))
  f1 <- as.formula(paste(y, "~", paste(c(rhs0, pc), collapse = " + ")))
  m0 <- lm(f0, data = wide)
  m1 <- lm(f1, data = wide)
  a <- tryCatch(anova(m0, m1), error = function(e) NULL)
  data.table(code = cc, food_group10 = GROUPS9[cc], n_pc_terms = length(pc),
             F_stat = if (!is.null(a)) a$F[2] else NA_real_,
             p_value = if (!is.null(a)) p_floor(a$`Pr(>F)`[2]) else NA_real_)
}))
fwrite(excl, file.path(odir, "purchase_cycle_exclusion_tests_v2.csv"), bom = TRUE)

# ---------------------------------------------------------------------------
# A3/B7 regularity diagnostics: raw predicted shares before clipping,
# Slutsky/Hicksian asymmetry, and finite-difference step sensitivity.
# ---------------------------------------------------------------------------
message("[44] Prediction clipping, asymmetry, and step-size diagnostics ...")
raw_pred <- matrix(0, nrow(wide), 9, dimnames = list(NULL, CODES9))
for (g in seq_len(lay0$G)) {
  z <- build_Ag(wide, g, lay0, pp$Phi, pp$phi)
  raw_pred[, lay0$eq_codes[g]] <- as.numeric(z$A %*% fit0$beta[z$cols])
}
raw_pred[, lay0$omit] <- 1 - rowSums(raw_pred[, lay0$eq_codes, drop = FALSE])
clip <- rbindlist(lapply(CODES9, function(cc) {
  x <- raw_pred[, cc]
  data.table(food_group10 = GROUPS9[cc],
             negative_share_rate = mean(x < 0),
             below_clip_rate = mean(x < 1e-8),
             min_raw_pred = min(x),
             p005_raw_pred = as.numeric(quantile(x, 0.005)),
             mean_abs_clip_change = mean(abs(pmax(x, 1e-8) - x)))
}))
fwrite(clip, file.path(odir, "predicted_share_clipping_diagnostics_v2.csv"), bom = TRUE)

S <- diag(el0$all$wbar) %*% el0$all$hick
fwrite(data.table(metric = c("max_abs_S_minus_St", "frobenius_S_minus_St",
                             "max_abs_hicksian_minus_transpose"),
                  value = c(max(abs(S - t(S))),
                            sqrt(sum((S - t(S))^2)),
                            max(abs(el0$all$hick - t(el0$all$hick))))),
       file.path(odir, "hicksian_asymmetry_diagnostics_v2.csv"), bom = TRUE)

steps <- c(0.001, 0.005, 0.01, 0.02)
step_dt <- rbindlist(lapply(steps, function(hh) {
  elh <- compute_elasticities(wide, lay0, fit0$beta, fs$betas, sw, wt, h = hh)
  data.table(h = hh, food_group10 = GROUPS9, own_price = diag(elh$all$mar))
}))
fwrite(step_dt, file.path(odir, "finite_difference_step_sensitivity_v2.csv"), bom = TRUE)

# ---------------------------------------------------------------------------
# A2 cluster sensitivity: leave-one-province-out reduced-form intensive
# own-price slopes with full year-month fixed effects.
# ---------------------------------------------------------------------------
message("[44] Leave-one-province-out reduced-form intensive slopes ...")
qty <- copy(wide)
for (cc in CODES9) {
  qty[, paste0("q_", cc) := get(paste0("w_", cc)) *
        total_food_spend_pc_month / exp(get(paste0("lp_", cc)))]
}
loo <- rbindlist(lapply(CODES9, function(cc) {
  rbindlist(lapply(sort(unique(qty$Province)), function(pr) {
    z <- qty[Province != pr & get(paste0("q_", cc)) > 0]
    z[, ym_fe := factor(year_month)]
    m <- tryCatch(lm(log(get(paste0("q_", cc))) ~ get(paste0("lp_", cc)) +
                       y_easi + ym_fe + factor(Province), data = z),
                  error = function(e) NULL)
    data.table(food_group10 = GROUPS9[cc], omitted_province = pr,
               own_price_intensive = if (!is.null(m)) unname(coef(m)[2]) else NA_real_,
               n = nrow(z))
  }))
}))
fwrite(loo, file.path(odir, "leave_one_province_out_intensive_v2.csv"), bom = TRUE)
fwrite(loo[, .(mean = mean(own_price_intensive, na.rm = TRUE),
               sd = sd(own_price_intensive, na.rm = TRUE),
               min = min(own_price_intensive, na.rm = TRUE),
               max = max(own_price_intensive, na.rm = TRUE)),
           by = food_group10],
       file.path(odir, "leave_one_province_out_intensive_summary_v2.csv"), bom = TRUE)

message("[44] Done.")
