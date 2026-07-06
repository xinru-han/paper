options(warn = 1)

root <- getwd()
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "model_summaries"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "logs"), recursive = TRUE, showWarnings = FALSE)

path <- function(...) file.path(root, ...)

read_csv <- function(file, colClasses = NULL) {
  args <- list(
    file = file,
    stringsAsFactors = FALSE,
    check.names = FALSE,
    fileEncoding = "UTF-8"
  )
  if (!is.null(colClasses)) args$colClasses <- colClasses
  out <- do.call(read.csv, args)
  names(out) <- gsub("\ufeff", "", names(out), fixed = TRUE)
  out
}

write_csv <- function(x, file) {
  write.csv(x, file, row.names = FALSE, fileEncoding = "UTF-8")
}

to_num <- function(x) {
  if (is.numeric(x)) return(x)
  suppressWarnings(as.numeric(x))
}

median_impute <- function(data, var) {
  x <- to_num(data[[var]])
  miss <- is.na(x)
  med <- median(x, na.rm = TRUE)
  if (is.na(med)) med <- 0
  x[miss] <- med
  data[[paste0(var, "_imp")]] <- x
  data[[paste0(var, "_missing")]] <- as.integer(miss)
  data
}

cluster_vcov <- function(model, cluster) {
  sandwich::vcovCL(model, cluster = cluster, type = "HC1")
}

wald_test <- function(model, vcov_mat, terms) {
  coefs <- coef(model)
  terms <- intersect(terms, names(coefs))
  terms <- terms[!is.na(coefs[terms])]
  if (length(terms) == 0) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_))
  }
  b <- coefs[terms]
  V <- vcov_mat[terms, terms, drop = FALSE]
  keep <- is.finite(b) & apply(V, 1, function(x) all(is.finite(x)))
  b <- b[keep]
  V <- V[keep, keep, drop = FALSE]
  if (length(b) == 0) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_))
  }
  invV <- tryCatch(solve(V), error = function(e) MASS::ginv(V))
  stat <- as.numeric(t(b) %*% invV %*% b)
  df <- length(b)
  list(stat = stat, df = df, p = 1 - pchisq(stat, df))
}

safe_lm_coef_row <- function(model, vcov_mat, term) {
  coefs <- coef(model)
  ses <- sqrt(diag(vcov_mat))
  if (!term %in% names(coefs) || is.na(coefs[term])) {
    return(c(estimate = NA_real_, std_error_cluster = NA_real_, t_stat = NA_real_, p_value = NA_real_))
  }
  est <- as.numeric(coefs[term])
  se <- as.numeric(ses[term])
  tval <- est / se
  c(
    estimate = est,
    std_error_cluster = se,
    t_stat = tval,
    p_value = 2 * pnorm(abs(tval), lower.tail = FALSE)
  )
}

full_rank_matrix <- function(M, tol = 1e-10) {
  M <- as.matrix(M)
  q <- qr(M, tol = tol)
  keep <- sort(q$pivot[seq_len(q$rank)])
  M[, keep, drop = FALSE]
}

iv_2sls <- function(y, X, Z, cluster) {
  X <- full_rank_matrix(X)
  Z <- full_rank_matrix(Z)
  y <- as.numeric(y)
  n <- nrow(X)
  k <- ncol(X)
  G <- length(unique(cluster))

  ZTZ_inv <- MASS::ginv(crossprod(Z))
  XZ <- crossprod(X, Z)
  ZX <- t(XZ)
  A <- XZ %*% ZTZ_inv %*% ZX
  A_inv <- MASS::ginv(A)
  beta <- A_inv %*% XZ %*% ZTZ_inv %*% crossprod(Z, y)
  beta <- as.numeric(beta)
  names(beta) <- colnames(X)

  resid <- y - as.numeric(X %*% beta)
  S <- matrix(0, ncol(Z), ncol(Z))
  for (g in unique(cluster)) {
    idx <- cluster == g
    Zg <- Z[idx, , drop = FALSE]
    ug <- resid[idx]
    S <- S + crossprod(Zg, ug %*% t(ug) %*% Zg)
  }
  V <- A_inv %*% XZ %*% ZTZ_inv %*% S %*% ZTZ_inv %*% ZX %*% A_inv
  if (G > 1 && n > k) {
    V <- V * (G / (G - 1)) * ((n - 1) / (n - k))
  }
  rownames(V) <- colnames(V) <- colnames(X)
  r2 <- 1 - sum(resid^2) / sum((y - mean(y))^2)
  list(beta = beta, vcov = V, n = n, k = k, n_clusters = G, r_squared = r2)
}

json_escape <- function(x) {
  x <- gsub("\\\\", "\\\\\\\\", x)
  x <- gsub('"', '\\"', x)
  x <- gsub("\n", "\\\\n", x)
  x
}

json_number <- function(x) {
  if (is.na(x) || !is.finite(x)) return("null")
  as.character(signif(x, 8))
}

write_model_json <- function(meta, file) {
  lines <- c("{", '  "models": [')
  for (i in seq_len(nrow(meta))) {
    r <- meta[i, ]
    comma <- if (i < nrow(meta)) "," else ""
    lines <- c(lines, paste0(
      "    {",
      '"outcome":"', json_escape(r$outcome), '",',
      '"iv_spec":"', json_escape(r$iv_spec), '",',
      '"estimator":"', json_escape(r$estimator), '",',
      '"n":', r$n, ",",
      '"n_clusters":', r$n_clusters, ",",
      '"r_squared":', json_number(r$r_squared), ",",
      '"first_stage_min_F":', json_number(r$first_stage_min_F), ",",
      '"first_stage_median_F":', json_number(r$first_stage_median_F),
      "}", comma
    ))
  }
  lines <- c(lines, "  ]", "}")
  writeLines(lines, file, useBytes = TRUE)
}

data <- read_csv(
  path("data", "cleaned", "paper1_household_category_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)

impute_vars <- c(
  "household_head_age", "household_head_education", "household_head_gender_male",
  "household_assets_count_proxy", "log1p_total_income_w_w99",
  "log1p_agri_business_income_w99", "log1p_annual_expense_total_w99"
)
for (v in impute_vars[impute_vars %in% names(data)]) {
  data <- median_impute(data, v)
}

data$food_category <- factor(data$food_category)
data$data_year <- factor(data$data_year)
data$provn_std <- factor(data$provn_std)

outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
hh_main <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")
endog_vars <- c("market_friction_survey", "child_market", "elderly_market", "female_market")
iv_interaction_terms <- c("iv_main", "child_iv", "elderly_iv", "female_iv")

resource_terms <- c(
  "log1p_total_income_w_w99_imp", "log1p_total_income_w_w99_missing",
  "log1p_agri_business_income_w99_imp", "log1p_agri_business_income_w99_missing",
  "log1p_annual_expense_total_w99_imp", "log1p_annual_expense_total_w99_missing",
  "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
  "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
  "household_head_age_imp", "household_head_age_missing",
  "household_head_education_imp", "household_head_education_missing",
  "household_head_gender_male_imp", "household_head_gender_male_missing"
)

other_controls <- c(
  "poi_market_friction_lag1",
  "price_hedonic_imputed_w99_yuan_per_jin",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
  "factor(food_category)", "factor(provn_std)", "factor(data_year)"
)

exog_terms <- c(hh_main, resource_terms, other_controls)

iv_specs <- list(
  terrain_town_2km = "iv_terrain_barrier_town_gee_2km",
  terrain_town_1km = "iv_terrain_barrier_town_gee_1km",
  terrain_town_5km = "iv_terrain_barrier_town_gee_5km",
  terrain_county_2km = "iv_terrain_barrier_county_gee_2km",
  early_ntl_9294 = "iv_early_ntl_peak_dist_9294"
)

## Correlation diagnostics use one row per household to avoid multiplying
## correlations by the eight food-category rows.
hh_once <- data[!duplicated(data$nhCode), ]
cor_targets <- c(
  "market_friction_survey", "poi_market_friction_lag1", "combined_market_friction",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
  "log1p_total_income_w_w99", "log1p_agri_business_income_w99",
  "log1p_annual_expense_total_w99", "total_sown_area"
)
cor_rows <- list()
for (iv_name in names(iv_specs)) {
  iv_var <- iv_specs[[iv_name]]
  if (!iv_var %in% names(hh_once)) next
  for (target in cor_targets[cor_targets %in% names(hh_once)]) {
    x <- to_num(hh_once[[iv_var]])
    y <- to_num(hh_once[[target]])
    ok <- is.finite(x) & is.finite(y)
    cor_rows[[length(cor_rows) + 1]] <- data.frame(
      iv_spec = iv_name,
      iv_variable = iv_var,
      target_variable = target,
      n = sum(ok),
      pearson_cor = if (sum(ok) >= 3) cor(x[ok], y[ok]) else NA_real_,
      stringsAsFactors = FALSE
    )
  }
}
cor_table <- do.call(rbind, cor_rows)
write_csv(cor_table, path("outputs", "tables", "table5_iv_correlations.csv"))

coef_rows <- list()
first_stage_rows <- list()
meta_rows <- list()
issues <- c()

for (iv_name in names(iv_specs)) {
  iv_var <- iv_specs[[iv_name]]
  if (!iv_var %in% names(data)) {
    issues <- c(issues, paste0("- Skipped IV spec ", iv_name, ": missing variable ", iv_var, "."))
    next
  }

  d0 <- data
  d0$iv_main <- to_num(d0[[iv_var]])
  d0$child_market <- d0$child_share * d0$market_friction_survey
  d0$elderly_market <- d0$elderly_share * d0$market_friction_survey
  d0$female_market <- d0$female_share * d0$market_friction_survey
  d0$child_iv <- d0$child_share * d0$iv_main
  d0$elderly_iv <- d0$elderly_share * d0$iv_main
  d0$female_iv <- d0$female_share * d0$iv_main

  for (outcome in outcomes) {
    all_terms <- unique(c(outcome, exog_terms, endog_vars, iv_interaction_terms, "xzc12_for_merge_final"))
    vars_needed <- unique(all.vars(as.formula(paste("~", paste(all_terms, collapse = " + ")))))
    missing_vars <- setdiff(vars_needed, names(d0))
    if (length(missing_vars) > 0) {
      issues <- c(issues, paste0(
        "- Skipped ", outcome, " / ", iv_name,
        ": missing variables: ", paste(missing_vars, collapse = ", ")
      ))
      next
    }
    d <- d0[complete.cases(d0[, vars_needed, drop = FALSE]), ]
    if (nrow(d) < 100) {
      issues <- c(issues, paste0("- Skipped ", outcome, " / ", iv_name, ": fewer than 100 complete rows."))
      next
    }

    ## First-stage diagnostics.
    fs_stats <- data.frame()
    for (endog in endog_vars) {
      fs_formula <- as.formula(paste(endog, "~", paste(c(exog_terms, iv_interaction_terms), collapse = " + ")))
      fs_model <- lm(fs_formula, data = d)
      fs_vc <- cluster_vcov(fs_model, d$xzc12_for_merge_final)
      fs_wald <- wald_test(fs_model, fs_vc, iv_interaction_terms)
      fs_F <- fs_wald$stat / fs_wald$df
      fs_stats <- rbind(fs_stats, data.frame(
        endogenous_variable = endog,
        first_stage_wald_chisq = fs_wald$stat,
        first_stage_df = fs_wald$df,
        first_stage_F = fs_F,
        first_stage_p = fs_wald$p,
        stringsAsFactors = FALSE
      ))
      for (zterm in iv_interaction_terms) {
        stats <- safe_lm_coef_row(fs_model, fs_vc, zterm)
        first_stage_rows[[length(first_stage_rows) + 1]] <- data.frame(
          outcome = outcome,
          iv_spec = iv_name,
          iv_variable = iv_var,
          endogenous_variable = endog,
          excluded_instrument = zterm,
          estimate = stats["estimate"],
          std_error_cluster = stats["std_error_cluster"],
          t_stat = stats["t_stat"],
          p_value = stats["p_value"],
          first_stage_wald_chisq = fs_wald$stat,
          first_stage_df = fs_wald$df,
          first_stage_F = fs_F,
          first_stage_p = fs_wald$p,
          n = nrow(d),
          n_clusters = length(unique(d$xzc12_for_merge_final)),
          stringsAsFactors = FALSE
        )
      }
    }
    fs_min_F <- min(fs_stats$first_stage_F, na.rm = TRUE)
    fs_median_F <- median(fs_stats$first_stage_F, na.rm = TRUE)

    ## Same-sample OLS comparison.
    ols_formula <- as.formula(paste(outcome, "~", paste(c(exog_terms, endog_vars), collapse = " + ")))
    ols_model <- lm(ols_formula, data = d)
    ols_vc <- cluster_vcov(ols_model, d$xzc12_for_merge_final)
    ols_r2 <- summary(ols_model)$r.squared
    for (term in endog_vars) {
      stats <- safe_lm_coef_row(ols_model, ols_vc, term)
      coef_rows[[length(coef_rows) + 1]] <- data.frame(
        outcome = outcome,
        iv_spec = iv_name,
        iv_variable = iv_var,
        estimator = "OLS_same_sample",
        term = term,
        estimate = stats["estimate"],
        std_error_cluster = stats["std_error_cluster"],
        t_stat = stats["t_stat"],
        p_value = stats["p_value"],
        n = nrow(d),
        n_clusters = length(unique(d$xzc12_for_merge_final)),
        r_squared = ols_r2,
        first_stage_min_F = fs_min_F,
        first_stage_median_F = fs_median_F,
        stringsAsFactors = FALSE
      )
    }
    meta_rows[[length(meta_rows) + 1]] <- data.frame(
      outcome = outcome,
      iv_spec = iv_name,
      estimator = "OLS_same_sample",
      n = nrow(d),
      n_clusters = length(unique(d$xzc12_for_merge_final)),
      r_squared = ols_r2,
      first_stage_min_F = fs_min_F,
      first_stage_median_F = fs_median_F,
      stringsAsFactors = FALSE
    )

    ## Manual 2SLS with clustered IV sandwich standard errors.
    X_exog <- model.matrix(as.formula(paste("~", paste(exog_terms, collapse = " + "))), data = d)
    X <- cbind(X_exog, as.matrix(d[, endog_vars, drop = FALSE]))
    Z <- cbind(X_exog, as.matrix(d[, iv_interaction_terms, drop = FALSE]))
    iv_fit <- iv_2sls(d[[outcome]], X, Z, d$xzc12_for_merge_final)
    beta <- iv_fit$beta
    ses <- sqrt(diag(iv_fit$vcov))
    for (term in endog_vars) {
      if (!term %in% names(beta)) {
        issues <- c(issues, paste0("- IV term dropped by rank check: ", outcome, " / ", iv_name, " / ", term, "."))
        next
      }
      tval <- beta[term] / ses[term]
      coef_rows[[length(coef_rows) + 1]] <- data.frame(
        outcome = outcome,
        iv_spec = iv_name,
        iv_variable = iv_var,
        estimator = "IV_2SLS",
        term = term,
        estimate = beta[term],
        std_error_cluster = ses[term],
        t_stat = tval,
        p_value = 2 * pnorm(abs(tval), lower.tail = FALSE),
        n = iv_fit$n,
        n_clusters = iv_fit$n_clusters,
        r_squared = iv_fit$r_squared,
        first_stage_min_F = fs_min_F,
        first_stage_median_F = fs_median_F,
        stringsAsFactors = FALSE
      )
    }
    meta_rows[[length(meta_rows) + 1]] <- data.frame(
      outcome = outcome,
      iv_spec = iv_name,
      estimator = "IV_2SLS",
      n = iv_fit$n,
      n_clusters = iv_fit$n_clusters,
      r_squared = iv_fit$r_squared,
      first_stage_min_F = fs_min_F,
      first_stage_median_F = fs_median_F,
      stringsAsFactors = FALSE
    )
  }
}

iv_results <- do.call(rbind, coef_rows)
first_stage_table <- do.call(rbind, first_stage_rows)
model_meta <- do.call(rbind, meta_rows)

write_csv(iv_results, path("outputs", "tables", "table5_iv_results.csv"))
write_csv(first_stage_table, path("outputs", "tables", "table5_iv_first_stage.csv"))
write_model_json(model_meta, path("outputs", "model_summaries", "model5_iv_results.json"))

weak_rows <- unique(model_meta[, c("outcome", "iv_spec", "first_stage_min_F", "first_stage_median_F")])
weak_flags <- weak_rows[weak_rows$first_stage_min_F < 10 | is.na(weak_rows$first_stage_min_F), ]
weak_lines <- if (nrow(weak_flags) == 0) {
  "- No first-stage minimum F-statistic is below 10."
} else {
  paste0(
    "- ", weak_flags$outcome, " / ", weak_flags$iv_spec,
    ": minimum first-stage F = ", sprintf("%.3f", weak_flags$first_stage_min_F),
    ", median F = ", sprintf("%.3f", weak_flags$first_stage_median_F), "."
  )
}

log_lines <- c(
  "# IV Diagnostics and Market-Friction 2SLS Models",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Estimation Notes",
  "",
  "- IV is used as mechanism-support evidence for market friction, not as the paper's main identification strategy.",
  "- Endogenous variables: `market_friction_survey`, `child_share × market_friction_survey`, `elderly_share × market_friction_survey`, and `female_share × market_friction_survey`.",
  "- Excluded instruments: one terrain/early-market IV plus its interactions with child, elderly, and female shares.",
  "- Exogenous controls follow the M3 controls plus household composition main effects and lagged POI market friction.",
  "- Standard errors are clustered by `xzc12_for_merge_final`.",
  "- The reported 2SLS standard errors are manually computed clustered IV sandwich standard errors; no household, village, village-year, DID, or panel fixed effects are used.",
  "- Each IV specification is exactly identified, so overidentification tests are not reported.",
  "",
  "## Weak-IV Flags",
  "",
  weak_lines,
  "",
  "## Outputs",
  "",
  "- `outputs/tables/table5_iv_results.csv`",
  "- `outputs/tables/table5_iv_first_stage.csv`",
  "- `outputs/tables/table5_iv_correlations.csv`",
  "- `outputs/model_summaries/model5_iv_results.json`",
  "",
  "## Issues",
  "",
  if (length(issues) == 0) "- None." else issues
)
writeLines(log_lines, path("outputs", "logs", "iv_diagnostics.md"), useBytes = TRUE)

message("IV diagnostics and 2SLS models completed.")