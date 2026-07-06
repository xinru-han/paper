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

find_interaction_name <- function(coef_names, term, friction_var) {
  candidates <- c(
    paste0(term, ":", friction_var),
    paste0(friction_var, ":", term)
  )
  hit <- candidates[candidates %in% coef_names]
  if (length(hit) == 0) return(NA_character_)
  hit[1]
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

write_model_json <- function(models_meta, file) {
  lines <- c("{", '  "models": [')
  for (i in seq_len(nrow(models_meta))) {
    r <- models_meta[i, ]
    comma <- if (i < nrow(models_meta)) "," else ""
    lines <- c(lines, paste0(
      "    {",
      '"outcome":"', json_escape(r$outcome), '",',
      '"friction_spec":"', json_escape(r$friction_spec), '",',
      '"friction_variable":"', json_escape(r$friction_variable), '",',
      '"n":', r$n, ",",
      '"n_clusters":', r$n_clusters, ",",
      '"r_squared":', json_number(r$r_squared), ",",
      '"interaction_wald_chisq":', json_number(r$interaction_wald_chisq), ",",
      '"interaction_wald_df":', r$interaction_wald_df, ",",
      '"interaction_wald_p":', json_number(r$interaction_wald_p),
      "}", comma
    ))
  }
  lines <- c(lines, "  ]", "}")
  writeLines(lines, file, useBytes = TRUE)
}

safe_term_stats <- function(coefs, ses, term, out_prefix) {
  if (is.na(term) || !term %in% names(coefs) || is.na(coefs[term])) {
    out <- rep(NA_real_, 3)
  } else {
    tval <- coefs[term] / ses[term]
    out <- c(coefs[term], ses[term], 2 * pnorm(abs(tval), lower.tail = FALSE))
  }
  names(out) <- paste0(out_prefix, c("_coef", "_se", "_p"))
  out
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
hh_terms <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")
hh_labels <- c(
  household_size_reconstructed = "household_size",
  child_share = "child_share",
  elderly_share = "elderly_share",
  female_share = "female_share"
)

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

base_controls <- paste(
  c(
    resources,
    "price_hedonic_imputed_w99_yuan_per_jin",
    "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
    "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
    "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
    "factor(food_category)", "factor(provn_std)", "factor(data_year)"
  ),
  collapse = " + "
)

friction_specs <- list(
  survey_market_friction = list(
    friction_var = "market_friction_survey",
    friction_label = "Survey market friction",
    extra_controls = c("poi_market_friction_lag1")
  ),
  poi_market_friction = list(
    friction_var = "poi_market_friction_lag1",
    friction_label = "Lagged POI market friction",
    extra_controls = c("market_friction_survey")
  ),
  combined_market_friction = list(
    friction_var = "combined_market_friction",
    friction_label = "Combined survey/POI market friction",
    extra_controls = character(0)
  )
)

model_rows <- list()
coef_rows <- list()
issues <- c()
main_margin_model <- NULL
main_margin_vcov <- NULL
main_margin_data <- NULL

for (spec_name in names(friction_specs)) {
  spec <- friction_specs[[spec_name]]
  friction_var <- spec$friction_var
  interaction_part <- paste0("(", paste(hh_terms, collapse = " + "), ") * ", friction_var)
  controls <- paste(c(base_controls, spec$extra_controls), collapse = " + ")

  for (outcome in outcomes) {
    f <- as.formula(paste(outcome, "~", interaction_part, "+", controls))
    vars_needed <- unique(c(all.vars(f), "xzc12_for_merge_final"))
    missing_vars <- setdiff(vars_needed, names(data))
    if (length(missing_vars) > 0) {
      issues <- c(issues, paste0(
        "- Skipped ", outcome, " / ", spec_name,
        ": missing variables: ", paste(missing_vars, collapse = ", ")
      ))
      next
    }
    d <- data[complete.cases(data[, vars_needed, drop = FALSE]), ]
    if (nrow(d) < 100) {
      issues <- c(issues, paste0("- Skipped ", outcome, " / ", spec_name, ": fewer than 100 complete rows."))
      next
    }
    if (length(unique(d[[outcome]])) < 2) {
      issues <- c(issues, paste0("- Skipped ", outcome, " / ", spec_name, ": outcome has fewer than 2 unique values."))
      next
    }

    model <- lm(f, data = d)
    vc <- cluster_vcov(model, d$xzc12_for_merge_final)
    coefs <- coef(model)
    ses <- sqrt(diag(vc))
    interaction_coef_names <- vapply(
      hh_terms,
      function(term) find_interaction_name(names(coefs), term, friction_var),
      character(1)
    )
    wald <- wald_test(model, vc, interaction_coef_names)
    cluster_n <- length(unique(d$xzc12_for_merge_final))
    r2 <- summary(model)$r.squared

    main_term_stats <- unlist(lapply(hh_terms, function(term) {
      safe_term_stats(coefs, ses, term, hh_labels[term])
    }))
    interaction_stats <- unlist(lapply(hh_terms, function(term) {
      safe_term_stats(
        coefs,
        ses,
        interaction_coef_names[term],
        paste0(hh_labels[term], "_x_friction")
      )
    }))
    friction_stats <- safe_term_stats(coefs, ses, friction_var, "friction_main")

    model_rows[[length(model_rows) + 1]] <- data.frame(
      friction_spec = spec_name,
      friction_label = spec$friction_label,
      friction_variable = friction_var,
      outcome = outcome,
      n = nrow(d),
      n_clusters = cluster_n,
      outcome_mean = mean(d[[outcome]], na.rm = TRUE),
      friction_mean = mean(d[[friction_var]], na.rm = TRUE),
      friction_sd = sd(d[[friction_var]], na.rm = TRUE),
      r_squared = r2,
      interaction_wald_chisq = wald$stat,
      interaction_wald_df = wald$df,
      interaction_wald_p = wald$p,
      t(c(friction_stats, main_term_stats, interaction_stats)),
      stringsAsFactors = FALSE
    )

    for (term in hh_terms) {
      interaction_name <- interaction_coef_names[term]
      if (is.na(interaction_name) || !interaction_name %in% names(coefs) || is.na(coefs[interaction_name])) next
      tval <- coefs[interaction_name] / ses[interaction_name]
      coef_rows[[length(coef_rows) + 1]] <- data.frame(
        friction_spec = spec_name,
        friction_label = spec$friction_label,
        friction_variable = friction_var,
        outcome = outcome,
        term = term,
        coefficient_name = interaction_name,
        estimate = coefs[interaction_name],
        std_error_cluster = ses[interaction_name],
        t_stat = tval,
        p_value = 2 * pnorm(abs(tval), lower.tail = FALSE),
        n = nrow(d),
        n_clusters = cluster_n,
        r_squared = r2,
        interaction_wald_chisq = wald$stat,
        interaction_wald_df = wald$df,
        interaction_wald_p = wald$p,
        stringsAsFactors = FALSE
      )
    }

    if (spec_name == "survey_market_friction" && outcome == "production_participation") {
      main_margin_model <- model
      main_margin_vcov <- vc
      main_margin_data <- d
    }
  }
}

table4 <- do.call(rbind, model_rows)
coef_table <- do.call(rbind, coef_rows)

write_csv(table4, path("outputs", "tables", "table4_market_friction_interactions.csv"))
write_csv(coef_table, path("outputs", "tables", "table4_market_friction_interaction_coefficients.csv"))
write_model_json(table4, path("outputs", "model_summaries", "model4_market_interactions.json"))

## Figure: marginal effects over survey-based market friction for the main
## production-participation model.
if (!is.null(main_margin_model)) {
  coefs <- coef(main_margin_model)
  vc <- main_margin_vcov
  friction_var <- "market_friction_survey"
  x_grid <- seq(
    quantile(main_margin_data[[friction_var]], 0.05, na.rm = TRUE),
    quantile(main_margin_data[[friction_var]], 0.95, na.rm = TRUE),
    length.out = 100
  )
  plot_terms <- hh_terms
  plot_labels <- c("Household size", "Child share", "Elderly share", "Female share")

  png(path("outputs", "figures", "figure3_market_friction_margins.png"), width = 1800, height = 1300, res = 180)
  par(mfrow = c(2, 2), mar = c(4.5, 4.5, 3, 1.2))
  for (i in seq_along(plot_terms)) {
    term <- plot_terms[i]
    inter <- find_interaction_name(names(coefs), term, friction_var)
    if (is.na(inter)) {
      plot.new()
      title(plot_labels[i])
      next
    }
    b0 <- coefs[term]
    b1 <- coefs[inter]
    effect <- b0 + b1 * x_grid
    var_effect <- vc[term, term] + x_grid^2 * vc[inter, inter] + 2 * x_grid * vc[term, inter]
    se_effect <- sqrt(pmax(var_effect, 0))
    upper <- effect + 1.96 * se_effect
    lower <- effect - 1.96 * se_effect
    ylim <- range(c(lower, upper, 0), na.rm = TRUE)
    plot(
      x_grid, effect,
      type = "l",
      lwd = 2,
      col = "#2F6B9A",
      xlab = "Survey market friction",
      ylab = "Marginal effect",
      main = plot_labels[i],
      ylim = ylim
    )
    polygon(
      c(x_grid, rev(x_grid)),
      c(upper, rev(lower)),
      col = adjustcolor("#2F6B9A", alpha.f = 0.18),
      border = NA
    )
    lines(x_grid, effect, lwd = 2, col = "#2F6B9A")
    abline(h = 0, lty = 2, col = "#777777")
  }
  dev.off()
}

log_lines <- c(
  "# Market-Friction Interaction Models",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Estimation Notes",
  "",
  "- Models are pooled cross-sectional OLS/LPM specifications estimated with base R.",
  "- Standard errors are clustered by `xzc12_for_merge_final` using `sandwich::vcovCL`.",
  "- No household, village, village-year, DID, or panel fixed effects are used.",
  "- Each model includes household composition, the selected market-friction variable, and the four household-composition × market-friction interactions.",
  "- The control set follows the complete baseline M3 structure: household resources, land, labor, assets, household-head controls, hedonic food price, GAEZ controls, county text indicators, food-category indicators, province indicators, and survey-year indicators.",
  "- Survey-friction models additionally control for lagged POI friction; POI-friction models additionally control for survey friction; combined-friction models do not add the component indices separately.",
  "",
  "## Outputs",
  "",
  "- `outputs/tables/table4_market_friction_interactions.csv`",
  "- `outputs/tables/table4_market_friction_interaction_coefficients.csv`",
  "- `outputs/figures/figure3_market_friction_margins.png`",
  "- `outputs/model_summaries/model4_market_interactions.json`",
  "",
  "## Issues",
  "",
  if (length(issues) == 0) "- None." else issues
)
writeLines(log_lines, path("outputs", "logs", "market_friction_interactions.md"), useBytes = TRUE)

message("Market-friction interaction models completed.")