#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(Matrix)
  library(jsonlite)
  library(lmtest)
  library(sandwich)
})

script_path <- tryCatch(normalizePath(sys.frame(1)$ofile), error = function(e) file.path(getwd(), "src", "21_estimate_high_frequency_demand_R.R"))
base <- normalizePath(file.path(dirname(script_path), ".."), mustWork = TRUE)
dir.create(file.path(base, "outputs", "demand"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(base, "outputs", "regularity"), recursive = TRUE, showWarnings = FALSE)

codes <- sprintf("G%02d", 1:10)
groups <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉",
            "G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品","G10_坚果")
names(groups) <- codes
eq_codes <- codes[1:9]
omitted_code <- codes[10]
h <- 0.01

panel_path <- file.path(base, "data_derived", "household_month_group10_r.csv")
if (!file.exists(panel_path)) stop("Run src/20_build_high_frequency_price_and_panel.R first.")

message("Reading R monthly demand panel...")
panel <- fread(panel_path, encoding = "UTF-8", showProgress = TRUE)
panel <- panel[is.finite(latent_log_price) & is.finite(budget_share) & total_food_spend_month > 0]
panel[, group_code := substr(food_group10, 1, 3)]
panel[, year := substr(year_month, 1, 4)]
panel[, month := substr(year_month, 6, 7)]
panel[, covid_log := log1p(covid_daily_new_sum)]
panel[, precip_log := log1p(pmax(precipitation_mm_sum, 0))]

message("Casting to household-month wide format...")
id_cols <- c("ID","year_month","year","month","Province","Family_Type","Family_Size","Family_Income",
             "family_size_midpoint","total_food_spend_month","total_food_spend_pc_month",
             "log_total_food_spend_pc_month","fold","low_income","elderly_household","large_family",
             "cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log",
             "wholesale_agri_200_mean")
base_wide <- unique(panel[, ..id_cols], by = c("ID","year_month"))
cast_one <- function(value_col, prefix) {
  x <- dcast(panel, ID + year_month ~ group_code, value.var = value_col)
  setnames(x, codes, paste0(prefix, "_", codes), skip_absent = TRUE)
  x
}
wide <- Reduce(function(a, b) merge(a, b, by = c("ID","year_month"), all.x = TRUE),
               list(base_wide,
                    cast_one("budget_share", "w"),
                    cast_one("positive_purchase", "pos"),
                    cast_one("latent_log_price", "lp"),
                    cast_one("latent_price_se", "lpse")))
setorder(wide, ID, year_month)
share_cols <- paste0("w_", codes)
pos_cols <- paste0("pos_", codes)
lp_cols <- paste0("lp_", codes)
for (v in c(share_cols, pos_cols)) wide[is.na(get(v)), (v) := 0]
wide <- wide[rowSums(!is.finite(as.matrix(wide[, ..lp_cols]))) == 0]

wide[, stone_price := rowSums(as.matrix(.SD) * as.matrix(wide[, ..lp_cols])), .SDcols = share_cols]
wide[, y_easi := log_total_food_spend_pc_month - stone_price]
wide[, y_easi2 := y_easi^2]

for (code in eq_codes) wide[, paste0("r_", code) := get(paste0("lp_", code)) - get(paste0("lp_", omitted_code))]
r_cols <- paste0("r_", eq_codes)

scale_cols <- c("cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
for (v in scale_cols) {
  m <- mean(wide[[v]], na.rm = TRUE); s <- sd(wide[[v]], na.rm = TRUE)
  if (!is.finite(s) || s == 0) s <- 1
  wide[, paste0("z_", v) := (get(v) - m) / s]
}
z_cols <- paste0("z_", scale_cols)

message("Estimating CRE/Mundlak probit selection equations...")
wide[, mean_y_easi_hh := mean(y_easi, na.rm = TRUE), by = ID]
first_pred <- wide[, .(ID, year_month)]
first_coef <- list()
first_stats <- list()

selection_formula <- as.formula(paste(
  "y ~ y_easi +", paste(r_cols, collapse = " + "),
  "+ low_income + elderly_household + large_family + mean_y_easi_hh +",
  paste(z_cols, collapse = " + "),
  "+ factor(month) + factor(year)"
))

for (code in codes) {
  y <- wide[[paste0("pos_", code)]]
  df <- cbind(data.frame(y = y), as.data.frame(wide[, c("y_easi", r_cols, "low_income", "elderly_household", "large_family", "mean_y_easi_hh", z_cols, "month", "year"), with = FALSE]))
  fit <- glm(selection_formula, data = df, family = binomial(link = "probit"), control = glm.control(maxit = 80))
  xb <- as.numeric(predict(fit, type = "link"))
  Phi <- pmin(pmax(pnorm(xb), 1e-6), 1 - 1e-6)
  phi <- dnorm(xb)
  first_pred[, paste0("Phi_", code) := Phi]
  first_pred[, paste0("phi_", code) := phi]
  llf <- sum(y * log(Phi) + (1 - y) * log(1 - Phi))
  p0 <- mean(y)
  llnull <- sum(y * log(p0) + (1 - y) * log(1 - p0))
  brier <- mean((y - Phi)^2)
  first_coef[[code]] <- data.table(food_group10 = groups[[code]], term = names(coef(fit)), estimate = as.numeric(coef(fit)))
  first_stats[[code]] <- data.table(food_group10 = groups[[code]], nobs = length(y), positive_rate = mean(y),
                                    mean_predicted_probability = mean(Phi), brier = brier,
                                    pseudo_r2_mcfadden = 1 - llf / llnull)
}
fwrite(first_pred, file.path(base, "outputs", "demand", "selection_cre_probit_predictions_r.csv"), bom = TRUE)
fwrite(rbindlist(first_coef), file.path(base, "outputs", "demand", "selection_cre_probit_coefficients_r.csv"), bom = TRUE)
fwrite(rbindlist(first_stats), file.path(base, "outputs", "demand", "selection_cre_probit_fit_stats_r.csv"), bom = TRUE)
wide <- merge(wide, first_pred, by = c("ID","year_month"), all.x = TRUE)

message("Building constrained stacked SY-EASI design...")
demo_cols <- c("low_income","elderly_household","large_family", z_cols)
base_terms <- c("const","y_easi","y_easi2", demo_cols)
n <- nrow(wide)
Gm1 <- length(eq_codes)

upper_pairs <- which(upper.tri(matrix(0, Gm1, Gm1), diag = TRUE), arr.ind = TRUE)
pair_names <- paste0("p_", upper_pairs[,1], "_", upper_pairs[,2])

make_design <- function(dt, sy = TRUE, quaids = FALSE) {
  nr <- nrow(dt) * Gm1
  p_base <- length(eq_codes) * length(base_terms)
  p_price <- nrow(upper_pairs)
  p_yp <- nrow(upper_pairs)
  p_sigma <- if (sy) length(eq_codes) else 0
  X <- Matrix(0, nrow = nr, ncol = p_base + p_price + p_yp + p_sigma, sparse = TRUE)
  coln <- c(as.vector(outer(eq_codes, base_terms, paste, sep = "__")),
            paste0("sym_price__", pair_names),
            paste0(if (quaids) "sym_y2_price__" else "sym_y_price__", pair_names),
            if (sy) paste0("sigma__", eq_codes) else NULL)
  colnames(X) <- coln
  y <- numeric(nr)
  row_group <- character(nr)
  offset <- 0L
  for (g in seq_along(eq_codes)) {
    code <- eq_codes[g]
    rows <- offset + seq_len(nrow(dt))
    offset <- offset + nrow(dt)
    y[rows] <- dt[[paste0("w_", code)]]
    row_group[rows] <- code
    mult <- if (sy) dt[[paste0("Phi_", code)]] else rep(1, nrow(dt))
    base_mat <- cbind(const = 1, y_easi = dt$y_easi, y_easi2 = dt$y_easi2, as.matrix(dt[, ..demo_cols]))
    for (b in seq_along(base_terms)) {
      X[rows, paste0(code, "__", base_terms[b])] <- mult * base_mat[, b]
    }
    rmat <- as.matrix(dt[, ..r_cols])
    ymult <- if (quaids) dt$y_easi2 else dt$y_easi
    for (k in seq_len(nrow(upper_pairs))) {
      a <- upper_pairs[k, 1]; b <- upper_pairs[k, 2]
      val <- if (g == a) rmat[, b] else if (g == b) rmat[, a] else 0
      if (a == b && g == a) val <- rmat[, a]
      X[rows, paste0("sym_price__", pair_names[k])] <- mult * val
      X[rows, paste0(if (quaids) "sym_y2_price__" else "sym_y_price__", pair_names[k])] <- mult * ymult * val
    }
    if (sy) X[rows, paste0("sigma__", code)] <- dt[[paste0("phi_", code)]]
  }
  list(X = X, y = y, row_group = row_group)
}

fit_sparse_lm <- function(design, ridge = 1e-8) {
  xtx <- as.matrix(crossprod(design$X))
  diag(xtx) <- diag(xtx) + ridge
  xty <- as.numeric(crossprod(design$X, design$y))
  fit <- as.numeric(solve(xtx, xty))
  names(fit) <- colnames(design$X)
  pred <- as.numeric(design$X %*% fit)
  list(coef = fit, pred = pred, resid = design$y - pred)
}

des_sy <- make_design(wide, sy = TRUE, quaids = FALSE)
fit_sy <- fit_sparse_lm(des_sy)
des_q <- make_design(wide, sy = TRUE, quaids = TRUE)
fit_q <- fit_sparse_lm(des_q)
des_nosy <- make_design(wide, sy = FALSE, quaids = FALSE)
fit_nosy <- fit_sparse_lm(des_nosy)

saveRDS(list(metadata = list(codes = codes, groups = groups, eq_codes = eq_codes, omitted_code = omitted_code,
                             base_terms = base_terms, r_cols = r_cols, demo_cols = demo_cols,
                             upper_pairs = upper_pairs),
             sy_easi = fit_sy$coef, sy_quaids = fit_q$coef, no_sy_easi = fit_nosy$coef),
        file.path(base, "outputs", "demand", "constrained_high_frequency_models_r.rds"))

coef_dt <- rbindlist(list(
  data.table(model = "constrained_sy_easi", term = names(fit_sy$coef), estimate = fit_sy$coef),
  data.table(model = "constrained_sy_quaids", term = names(fit_q$coef), estimate = fit_q$coef),
  data.table(model = "constrained_no_sy_easi", term = names(fit_nosy$coef), estimate = fit_nosy$coef)
))
fwrite(coef_dt, file.path(base, "outputs", "demand", "constrained_model_coefficients_r.csv"), bom = TRUE)

predict_model <- function(dt, coef, sy = TRUE, quaids = FALSE) {
  des <- make_design(dt, sy = sy, quaids = quaids)
  pred9 <- matrix(as.numeric(des$X %*% coef), nrow = nrow(dt), ncol = Gm1, byrow = FALSE)
  colnames(pred9) <- eq_codes
  pred <- cbind(pred9, G10 = 1 - rowSums(pred9))
  colnames(pred) <- codes
  pred[pred < 1e-8] <- 1e-8
  pred / rowSums(pred)
}

base_sh <- predict_model(wide, fit_sy$coef, sy = TRUE, quaids = FALSE)
pred_dt <- data.table(ID = wide$ID, year_month = wide$year_month, base_sh)
setnames(pred_dt, codes, paste0("pred_w_", codes))
fwrite(pred_dt, file.path(base, "outputs", "demand", "predicted_shares_constrained_sy_easi_r.csv"), bom = TRUE)

quantity_matrix <- function(dt, shares) {
  prices <- exp(as.matrix(dt[, ..lp_cols]))
  shares * dt$total_food_spend_pc_month / prices
}
perturb_exp <- function(dt) {
  out <- copy(dt)
  out[, total_food_spend_pc_month := total_food_spend_pc_month * (1 + h)]
  out[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]
  out[, stone_price := rowSums(as.matrix(.SD) * as.matrix(out[, ..lp_cols])), .SDcols = share_cols]
  out[, y_easi := log_total_food_spend_pc_month - stone_price]
  out[, y_easi2 := y_easi^2]
  out
}
perturb_price <- function(dt, code) {
  out <- copy(dt)
  out[[paste0("lp_", code)]] <- out[[paste0("lp_", code)]] + log(1 + h)
  out[, stone_price := rowSums(as.matrix(.SD) * as.matrix(out[, ..lp_cols])), .SDcols = share_cols]
  out[, y_easi := log_total_food_spend_pc_month - stone_price]
  out[, y_easi2 := y_easi^2]
  for (cc in eq_codes) out[, paste0("r_", cc) := get(paste0("lp_", cc)) - get(paste0("lp_", omitted_code))]
  out
}
agg_elas <- function(q0, q1, idx) ((colMeans(q1[idx,,drop=FALSE]) - colMeans(q0[idx,,drop=FALSE])) / colMeans(q0[idx,,drop=FALSE])) / h

message("Computing numerical monthly elasticities...")
q0 <- quantity_matrix(wide, base_sh)
q_exp <- quantity_matrix(perturb_exp(wide), predict_model(perturb_exp(wide), fit_sy$coef, sy = TRUE, quaids = FALSE))
all_idx <- rep(TRUE, nrow(wide))
exp_vec <- agg_elas(q0, q_exp, all_idx)
mar <- matrix(NA_real_, 10, 10, dimnames = list(groups, groups))
price_q <- vector("list", 10); names(price_q) <- codes
for (code in codes) {
  wp <- perturb_price(wide, code)
  qp <- quantity_matrix(wp, predict_model(wp, fit_sy$coef, sy = TRUE, quaids = FALSE))
  price_q[[code]] <- qp
  mar[, groups[[code]]] <- agg_elas(q0, qp, all_idx)
}
avg_share <- colMeans(as.matrix(wide[, ..share_cols]))
hick <- mar + exp_vec %o% avg_share

fwrite(data.table(food_group10 = groups, food_expenditure_elasticity = as.numeric(exp_vec)),
       file.path(base, "outputs", "demand", "food_expenditure_elasticity_monthly_r.csv"), bom = TRUE)
fwrite(data.table(demand_group = rownames(mar), mar), file.path(base, "outputs", "demand", "marshallian_elasticity_monthly_r.csv"), bom = TRUE)
fwrite(data.table(demand_group = rownames(hick), hick), file.path(base, "outputs", "demand", "hicksian_elasticity_monthly_r.csv"), bom = TRUE)

message("Writing heterogeneity elasticities...")
hetero_rows <- list()
hetero_specs <- c(low_income = "low_income", elderly_household = "elderly_household", large_family = "large_family")
for (hn in names(hetero_specs)) {
  col <- hetero_specs[[hn]]
  for (lev in sort(unique(wide[[col]]))) {
    idx <- wide[[col]] == lev
    if (sum(idx) < 100) next
    ev <- agg_elas(q0, q_exp, idx)
    for (k in seq_along(codes)) hetero_rows[[length(hetero_rows)+1]] <- data.table(heterogeneity = hn, level = lev, elasticity_type = "food_expenditure", demand_group = groups[k], shock_group = "food_expenditure", elasticity = ev[k], n = sum(idx))
    for (code in codes) {
      pv <- agg_elas(q0, price_q[[code]], idx)
      for (k in seq_along(codes)) hetero_rows[[length(hetero_rows)+1]] <- data.table(heterogeneity = hn, level = lev, elasticity_type = "marshallian_price", demand_group = groups[k], shock_group = groups[[code]], elasticity = pv[k], n = sum(idx))
    }
  }
}
fwrite(rbindlist(hetero_rows), file.path(base, "outputs", "demand", "elasticities_by_prespecified_heterogeneity_r.csv"), bom = TRUE)

message("Writing theory and regularity diagnostics...")
adding <- data.table(metric = c("n_household_months", "max_abs_predicted_share_sum_error", "mean_abs_predicted_share_sum_error", "min_predicted_share", "max_predicted_share"),
                     value = c(nrow(wide), max(abs(rowSums(base_sh) - 1)), mean(abs(rowSums(base_sh) - 1)), min(base_sh), max(base_sh)))
sym_terms <- grep("^sym_price__", names(fit_sy$coef), value = TRUE)
sym_diag <- data.table(model = "constrained_sy_easi", restriction = c("adding_up", "homogeneity_relative_prices", "slutsky_symmetry_price_coefficients"),
                       status = c("by_construction_predicted_10th_share", "by_construction_relative_prices", "by_construction_symmetric_parameterization"),
                       max_abs_error = c(max(abs(rowSums(base_sh)-1)), 0, 0))
own <- data.table(food_group10 = groups, own_price_elasticity = diag(mar), is_negative = diag(mar) < 0)
fwrite(adding, file.path(base, "outputs", "regularity", "adding_up_diagnostics_r.csv"), bom = TRUE)
fwrite(sym_diag, file.path(base, "outputs", "regularity", "theory_constraint_checks.csv"), bom = TRUE)
fwrite(own, file.path(base, "outputs", "regularity", "own_price_sign_diagnostics_r.csv"), bom = TRUE)

report <- c(
  "# R 高频月度需求模型报告", "",
  sprintf("- 家庭-月观测：%s", format(nrow(wide), big.mark = ",")),
  sprintf("- 家庭数：%s", format(uniqueN(wide$ID), big.mark = ",")),
  sprintf("- 月份：%s 至 %s", min(wide$year_month), max(wide$year_month)), "",
  "## 第一阶段 CRE/Mundlak Probit", "",
  capture.output(print(rbindlist(first_stats))), "",
  "## 理论约束", "",
  capture.output(print(sym_diag)), "",
  "## 自价格弹性", "",
  capture.output(print(own)), "",
  "## 解释边界", "",
  "- 弹性为 monthly food-expenditure elasticity 与 measured market-price variation 下的条件需求响应。",
  "- 本脚本不把 food-expenditure elasticity 写作 income elasticity。",
  "- 当前 R 版为可复现主规格；全流程 bootstrap 可在该脚本基础上按家庭重抽样扩展。"
)
writeLines(report, file.path(base, "outputs", "demand", "high_frequency_demand_model_report_r.md"))

message("High-frequency R demand models complete.")
