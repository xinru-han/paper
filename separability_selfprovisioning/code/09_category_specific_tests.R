options(warn = 1)

root <- getwd()
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "figures"), recursive = TRUE, showWarnings = FALSE)
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
      '"food_category":"', json_escape(r$food_category), '",',
      '"food_category_label":"', json_escape(r$food_category_label), '",',
      '"outcome":"', json_escape(r$outcome), '",',
      '"n":', r$n, ",",
      '"n_clusters":', r$n_clusters, ",",
      '"r_squared":', signif(r$r_squared, 8), ",",
      '"hhcomp_wald_chisq":', signif(r$hhcomp_wald_chisq, 8), ",",
      '"hhcomp_wald_df":', r$hhcomp_wald_df, ",",
      '"hhcomp_wald_p":', signif(r$hhcomp_wald_p, 8), ",",
      '"nsi":', signif(r$nsi, 8),
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

data$data_year <- factor(data$data_year)
data$provn_std <- factor(data$provn_std)

food_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
hh_terms <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")

hhcomp <- "household_size_reconstructed + child_share + elderly_share + female_share"
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
controls <- paste(
  c(
    resources,
    "market_friction_survey", "poi_market_friction_lag1",
    "price_hedonic_imputed_w99_yuan_per_jin",
    "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
    "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
    "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
    "factor(provn_std)", "factor(data_year)"
  ),
  collapse = " + "
)

test_rows <- list()
coef_rows <- list()
issues <- c()

for (cat in food_order) {
  d_cat0 <- data[data$food_category == cat, ]
  cat_label <- d_cat0$food_category_label[1]
  for (outcome in outcomes) {
    f <- as.formula(paste(outcome, "~", hhcomp, "+", controls))
    vars_needed <- unique(c(all.vars(f), "xzc12_for_merge_final"))
    d <- d_cat0[complete.cases(d_cat0[, vars_needed, drop = FALSE]), ]
    if (nrow(d) < 100) {
      issues <- c(issues, paste0("- Skipped ", cat, " / ", outcome, ": fewer than 100 complete rows."))
      next
    }
    if (length(unique(d[[outcome]])) < 2) {
      issues <- c(issues, paste0("- Skipped ", cat, " / ", outcome, ": outcome has fewer than 2 unique values."))
      next
    }
    model <- lm(f, data = d)
    vc <- cluster_vcov(model, d$xzc12_for_merge_final)
    wald <- wald_test(model, vc, hh_terms)
    cluster_n <- length(unique(d$xzc12_for_merge_final))
    r2 <- summary(model)$r.squared
    coefs <- coef(model)
    ses <- sqrt(diag(vc))

    get_coef <- function(term, suffix) {
      if (!term %in% names(coefs)) return(setNames(rep(NA_real_, 3), paste0(term, c("_coef", "_se", "_p"))))
      tval <- coefs[term] / ses[term]
      out <- c(coefs[term], ses[term], 2 * pnorm(abs(tval), lower.tail = FALSE))
      names(out) <- paste0(suffix, c("_coef", "_se", "_p"))
      out
    }
    c_household <- get_coef("household_size_reconstructed", "household_size")
    c_child <- get_coef("child_share", "child_share")
    c_elderly <- get_coef("elderly_share", "elderly_share")
    c_female <- get_coef("female_share", "female_share")

    test_rows[[length(test_rows) + 1]] <- data.frame(
      food_category = cat,
      food_category_label = cat_label,
      outcome = outcome,
      n = nrow(d),
      n_clusters = cluster_n,
      outcome_mean = mean(d[[outcome]], na.rm = TRUE),
      r_squared = r2,
      hhcomp_wald_chisq = wald$stat,
      hhcomp_wald_df = wald$df,
      hhcomp_wald_p = wald$p,
      t(c(c_household, c_child, c_elderly, c_female)),
      stringsAsFactors = FALSE
    )

    for (term in hh_terms) {
      if (!term %in% names(coefs)) next
      tval <- coefs[term] / ses[term]
      coef_rows[[length(coef_rows) + 1]] <- data.frame(
        food_category = cat,
        food_category_label = cat_label,
        outcome = outcome,
        term = term,
        estimate = coefs[term],
        std_error_cluster = ses[term],
        t_stat = tval,
        p_value = 2 * pnorm(abs(tval), lower.tail = FALSE),
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
}

tests <- do.call(rbind, test_rows)
coef_table <- do.call(rbind, coef_rows)

tests$nsi <- NA_real_
for (outcome in unique(tests$outcome)) {
  idx <- tests$outcome == outcome
  avg <- mean(tests$hhcomp_wald_chisq[idx], na.rm = TRUE)
  tests$nsi[idx] <- tests$hhcomp_wald_chisq[idx] / avg
}
coef_table <- merge(
  coef_table,
  tests[, c("food_category", "outcome", "nsi")],
  by = c("food_category", "outcome"),
  all.x = TRUE,
  sort = FALSE
)

tests$food_category <- factor(tests$food_category, levels = food_order)
tests <- tests[order(tests$outcome, tests$food_category), ]
tests$food_category <- as.character(tests$food_category)

write_csv(tests, path("outputs", "tables", "table3_category_specific_tests.csv"))
write_csv(coef_table, path("outputs", "tables", "table3_category_specific_coefficients.csv"))
write_model_json(tests, path("outputs", "model_summaries", "model3_category_specific_tests.json"))

## Figure: NSI by category for the baseline participation outcome.
fig_data <- tests[tests$outcome == "production_participation", ]
fig_data <- fig_data[order(fig_data$nsi, decreasing = TRUE), ]
png(path("outputs", "figures", "figure2_nsi_by_category.png"), width = 1800, height = 1100, res = 180)
par(mar = c(8, 5, 4, 2))
cols <- ifelse(fig_data$hhcomp_wald_p < 0.05, "#2F6B9A", "#9AA7B1")
barplot(
  fig_data$nsi,
  names.arg = fig_data$food_category_label,
  las = 2,
  col = cols,
  border = NA,
  ylab = "NSI = category Wald / mean Wald",
  main = "Category-Specific Non-Separability Index",
  ylim = c(0, max(fig_data$nsi, na.rm = TRUE) * 1.18)
)
abline(h = 1, lty = 2, col = "#666666")
legend(
  "topright",
  legend = c("Wald p < 0.05", "Wald p >= 0.05"),
  fill = c("#2F6B9A", "#9AA7B1"),
  border = NA,
  bty = "n"
)
dev.off()

log_lines <- c(
  "# Category-Specific Separability Tests",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Estimation Notes",
  "",
  "- Each model is estimated separately by food category.",
  "- The control set mirrors the complete baseline M3 specification, except food-category indicators are not included within category-specific models.",
  "- Standard errors are clustered by `xzc12_for_merge_final`.",
  "- NSI is defined as category Wald chi-square divided by the mean Wald chi-square within the same outcome.",
  "",
  "## Outputs",
  "",
  "- `outputs/tables/table3_category_specific_tests.csv`",
  "- `outputs/tables/table3_category_specific_coefficients.csv`",
  "- `outputs/figures/figure2_nsi_by_category.png`",
  "- `outputs/model_summaries/model3_category_specific_tests.json`",
  "",
  "## Issues",
  "",
  if (length(issues) == 0) "- None." else issues
)
writeLines(log_lines, path("outputs", "logs", "category_specific_tests.md"), useBytes = TRUE)

message("Category-specific tests completed.")