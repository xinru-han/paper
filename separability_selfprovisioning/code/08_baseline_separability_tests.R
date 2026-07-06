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
  if (length(terms) == 0) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_))
  }
  b <- coefs[terms]
  V <- vcov_mat[terms, terms, drop = FALSE]
  invV <- tryCatch(solve(V), error = function(e) MASS::ginv(V))
  stat <- as.numeric(t(b) %*% invV %*% b)
  df <- length(terms)
  list(stat = stat, df = df, p = 1 - pchisq(stat, df))
}

tidy_hh_terms <- function(model, vcov_mat, outcome, spec, n_used, cluster_n, r2, wald) {
  terms <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")
  coefs <- coef(model)
  rows <- lapply(terms, function(term) {
    if (!term %in% names(coefs)) {
      return(data.frame())
    }
    se <- sqrt(diag(vcov_mat))[term]
    tval <- coefs[term] / se
    data.frame(
      outcome = outcome,
      spec = spec,
      term = term,
      estimate = coefs[term],
      std_error_cluster = se,
      t_stat = tval,
      p_value = 2 * pnorm(abs(tval), lower.tail = FALSE),
      n = n_used,
      n_clusters = cluster_n,
      r_squared = r2,
      hhcomp_wald_chisq = wald$stat,
      hhcomp_wald_df = wald$df,
      hhcomp_wald_p = wald$p,
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, rows)
}

json_escape <- function(x) {
  x <- gsub("\\\\", "\\\\\\\\", x)
  x <- gsub('"', '\\"', x)
  x <- gsub("\n", "\\\\n", x)
  x
}

write_model_json <- function(models_meta, file) {
  lines <- c("{", '  "models": [')
  for (i in seq_len(nrow(models_meta))) {
    r <- models_meta[i, ]
    comma <- if (i < nrow(models_meta)) "," else ""
    lines <- c(lines, paste0(
      "    {",
      '"outcome":"', json_escape(r$outcome), '",',
      '"spec":"', json_escape(r$spec), '",',
      '"n":', r$n, ",",
      '"n_clusters":', r$n_clusters, ",",
      '"r_squared":', signif(r$r_squared, 8), ",",
      '"hhcomp_wald_chisq":', signif(r$hhcomp_wald_chisq, 8), ",",
      '"hhcomp_wald_df":', r$hhcomp_wald_df, ",",
      '"hhcomp_wald_p":', signif(r$hhcomp_wald_p, 8),
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

## Median-impute selected controls to avoid dropping observations solely due
## to household-head or resource-control missingness. Missingness indicators
## are included in resource/control specs.
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

hhcomp <- "household_size_reconstructed + child_share + elderly_share + female_share"
category_year <- "factor(food_category) + factor(data_year)"
resources <- paste(
  c(
    "log1p_total_income_w_w99_imp", "log1p_total_income_w_w99_missing",
    "log1p_agri_business_income_w99_imp", "log1p_agri_business_income_w99_missing",
    "log1p_annual_expense_total_w99_imp", "log1p_annual_expense_total_w99_missing",
    "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
    "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
    "household_head_age_imp", "household_head_age_missing",
    "household_head_education_imp", "household_head_education_missing",
    "household_head_gender_male_imp", "household_head_gender_male_missing"
  ),
  collapse = " + "
)
market_controls <- paste(
  c(
    "market_friction_survey", "poi_market_friction_lag1",
    "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
    "factor(provn_std)"
  ),
  collapse = " + "
)
text_price_controls <- paste(
  c(
    "price_hedonic_imputed_w99_yuan_per_jin",
    "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
    "trust_signal_z_5yr_sum", "attention_z_5yr_sum"
  ),
  collapse = " + "
)

specs <- list(
  M0_composition_category_year = paste(hhcomp, category_year, sep = " + "),
  M1_plus_household_resources = paste(hhcomp, resources, category_year, sep = " + "),
  M2_plus_market_gaez_province = paste(hhcomp, resources, market_controls, category_year, sep = " + "),
  M3_plus_price_text = paste(hhcomp, resources, market_controls, text_price_controls, category_year, sep = " + ")
)

outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
hh_terms <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")

coef_rows <- list()
meta_rows <- list()
issues <- c()

for (outcome in outcomes) {
  for (spec_name in names(specs)) {
    f <- as.formula(paste(outcome, "~", specs[[spec_name]]))
    vars_needed <- all.vars(f)
    vars_needed <- unique(c(vars_needed, "xzc12_for_merge_final"))
    d <- data[complete.cases(data[, vars_needed, drop = FALSE]), ]
    if (nrow(d) < 100) {
      issues <- c(issues, paste0("- Skipped ", outcome, " / ", spec_name, ": fewer than 100 complete rows."))
      next
    }
    model <- lm(f, data = d)
    vc <- cluster_vcov(model, d$xzc12_for_merge_final)
    wald <- wald_test(model, vc, hh_terms)
    cluster_n <- length(unique(d$xzc12_for_merge_final))
    r2 <- summary(model)$r.squared
    coef_rows[[length(coef_rows) + 1]] <- tidy_hh_terms(model, vc, outcome, spec_name, nrow(d), cluster_n, r2, wald)
    meta_rows[[length(meta_rows) + 1]] <- data.frame(
      outcome = outcome,
      spec = spec_name,
      n = nrow(d),
      n_clusters = cluster_n,
      r_squared = r2,
      hhcomp_wald_chisq = wald$stat,
      hhcomp_wald_df = wald$df,
      hhcomp_wald_p = wald$p,
      stringsAsFactors = FALSE
    )
  }
}

coef_table <- do.call(rbind, coef_rows)
model_meta <- do.call(rbind, meta_rows)

write_csv(coef_table, path("outputs", "tables", "table2_baseline_separability.csv"))
write_csv(model_meta, path("outputs", "tables", "table2_baseline_wald_summary.csv"))
write_model_json(model_meta, path("outputs", "model_summaries", "model2_baseline_separability.json"))

log_lines <- c(
  "# Baseline Separability Tests",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Estimation Notes",
  "",
  "- Models are pooled cross-sectional OLS/LPM specifications estimated with base R.",
  "- Standard errors are clustered by `xzc12_for_merge_final` using `sandwich::vcovCL`.",
  "- No household, village, village-year, DID, or panel fixed effects are used.",
  "- Household-head/resource controls are median-imputed with missingness indicators where needed.",
  "- M2 and M3 require nonmissing survey market friction, POI friction, GAEZ controls, and province indicators.",
  "",
  "## Outputs",
  "",
  "- `outputs/tables/table2_baseline_separability.csv`",
  "- `outputs/tables/table2_baseline_wald_summary.csv`",
  "- `outputs/model_summaries/model2_baseline_separability.json`",
  "",
  "## Issues",
  "",
  if (length(issues) == 0) "- None." else issues
)
writeLines(log_lines, path("outputs", "logs", "baseline_separability_tests.md"), useBytes = TRUE)

message("Baseline separability tests completed.")