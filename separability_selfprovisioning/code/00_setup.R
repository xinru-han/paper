options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "analysis_ready"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "data", "cleaned"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "figures"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "model_summaries"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "logs"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "reports"), recursive = TRUE, showWarnings = FALSE)

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
  miss <- is.na(x) | !is.finite(x)
  x[!is.finite(x)] <- NA_real_
  med <- median(x, na.rm = TRUE)
  if (is.na(med)) med <- 0
  x[miss] <- med
  data[[paste0(var, "_imp")]] <- x
  data[[paste0(var, "_missing")]] <- as.integer(miss)
  data
}

prepare_revised_data <- function(data) {
  impute_vars <- c(
    "household_head_age", "household_head_education", "household_head_gender_male",
    "household_assets_count_proxy", "log1p_total_income_w_w99",
    "log1p_agri_business_income_w99", "log1p_annual_expense_total_w99"
  )
  for (v in impute_vars[impute_vars %in% names(data)]) {
    data <- median_impute(data, v)
  }
  if ("food_category" %in% names(data)) data$food_category <- factor(data$food_category)
  if ("data_year" %in% names(data)) data$data_year <- factor(data$data_year)
  if ("provn_std" %in% names(data)) data$provn_std <- factor(data$provn_std)
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

safe_coef_stats <- function(model, vcov_mat, term) {
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

fit_lm_cluster <- function(data, outcome, rhs_terms, cluster_var = "xzc12_for_merge_final") {
  f <- as.formula(paste(outcome, "~", paste(rhs_terms, collapse = " + ")))
  vars_needed <- unique(c(all.vars(f), cluster_var))
  d <- data[complete.cases(data[, vars_needed, drop = FALSE]), ]
  if (nrow(d) < 100 || length(unique(d[[outcome]])) < 2) {
    return(list(ok = FALSE, formula = f, data = d, model = NULL, vcov = NULL))
  }
  model <- lm(f, data = d)
  vc <- cluster_vcov(model, d[[cluster_var]])
  list(ok = TRUE, formula = f, data = d, model = model, vcov = vc)
}

find_interaction_name <- function(coef_names, term, friction_var) {
  candidates <- c(paste0(term, ":", friction_var), paste0(friction_var, ":", term))
  hit <- candidates[candidates %in% coef_names]
  if (length(hit) == 0) return(NA_character_)
  hit[1]
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

write_simple_json <- function(rows, file, key = "models") {
  if (is.null(rows) || nrow(rows) == 0) {
    writeLines(c("{", paste0('  "', key, '": []'), "}"), file, useBytes = TRUE)
    return(invisible(NULL))
  }
  lines <- c("{", paste0('  "', key, '": ['))
  for (i in seq_len(nrow(rows))) {
    r <- rows[i, , drop = FALSE]
    parts <- c()
    for (nm in names(r)) {
      val <- r[[nm]][1]
      if (is.numeric(val)) {
        parts <- c(parts, paste0('"', json_escape(nm), '":', json_number(val)))
      } else {
        parts <- c(parts, paste0('"', json_escape(nm), '":"', json_escape(as.character(val)), '"'))
      }
    }
    comma <- if (i < nrow(rows)) "," else ""
    lines <- c(lines, paste0("    {", paste(parts, collapse = ","), "}", comma))
  }
  lines <- c(lines, "  ]", "}")
  writeLines(lines, file, useBytes = TRUE)
}

summarise_numeric <- function(data, vars, module = "") {
  rows <- lapply(vars[vars %in% names(data)], function(v) {
    x <- to_num(data[[v]])
    data.frame(
      module = module,
      variable = v,
      n = sum(!is.na(x)),
      missing = sum(is.na(x)),
      mean = mean(x, na.rm = TRUE),
      sd = sd(x, na.rm = TRUE),
      min = min(x, na.rm = TRUE),
      p25 = quantile(x, 0.25, na.rm = TRUE),
      median = median(x, na.rm = TRUE),
      p75 = quantile(x, 0.75, na.rm = TRUE),
      max = max(x, na.rm = TRUE),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, rows)
}

hh_terms_main <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")
resource_terms_revised <- c(
  "log1p_total_income_w_w99_imp", "log1p_total_income_w_w99_missing",
  "log1p_agri_business_income_w99_imp", "log1p_agri_business_income_w99_missing",
  "log1p_annual_expense_total_w99_imp", "log1p_annual_expense_total_w99_missing",
  "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
  "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
  "household_head_age_imp", "household_head_age_missing",
  "household_head_education_imp", "household_head_education_missing",
  "household_head_gender_male_imp", "household_head_gender_male_missing"
)
market_gaez_terms_revised <- c(
  "market_friction_survey", "poi_market_friction_lag1",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
  "factor(provn_std)"
)
price_text_terms_revised <- c(
  "price_hedonic_imputed_w99_yuan_per_jin",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_5yr_sum"
)
category_year_terms_revised <- c("factor(food_category)", "factor(data_year)")

baseline_rhs <- function(spec) {
  if (spec == "M0") return(c(hh_terms_main, category_year_terms_revised))
  if (spec == "M1") return(c(hh_terms_main, resource_terms_revised, category_year_terms_revised))
  if (spec == "M2") return(c(hh_terms_main, resource_terms_revised, market_gaez_terms_revised, category_year_terms_revised))
  if (spec == "M3") return(c(hh_terms_main, resource_terms_revised, market_gaez_terms_revised, price_text_terms_revised, category_year_terms_revised))
  stop("Unknown spec: ", spec)
}

signal_label <- function(p, nsi) {
  if (!is.na(p) && p < 0.01) return("Strong")
  if (!is.na(nsi) && nsi > 1.25) return("Strong")
  if (!is.na(p) && p < 0.05) return("Moderate")
  if (!is.na(nsi) && nsi >= 0.9 && nsi <= 1.1) return("Moderate")
  "Weak"
}

message("Revised setup loaded.")