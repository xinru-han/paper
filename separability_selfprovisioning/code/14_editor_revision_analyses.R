source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

outcomes_main <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
food_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")

market_terms_only <- c("market_friction_survey", "poi_market_friction_lag1")
gaez_terms_only <- c("gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km")
province_fe_only <- "factor(provn_std)"
unit_value_text_terms <- price_text_terms_revised

fixed_resource_terms <- c(
  "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
  "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
  "household_head_age_imp", "household_head_age_missing",
  "household_head_education_imp", "household_head_education_missing",
  "household_head_gender_male_imp", "household_head_gender_male_missing"
)

rbind_fill <- function(lst) {
  lst <- Filter(Negate(is.null), lst)
  if (length(lst) == 0) return(data.frame())
  cols <- unique(unlist(lapply(lst, names), use.names = FALSE))
  out <- lapply(lst, function(x) {
    miss <- setdiff(cols, names(x))
    for (m in miss) x[[m]] <- NA
    x[, cols, drop = FALSE]
  })
  do.call(rbind, out)
}

fmt_num <- function(x, digits = 3) {
  ifelse(is.na(x), "", formatC(x, format = "f", digits = digits))
}

md_table <- function(df, digits = 3, max_rows = Inf) {
  if (is.null(df) || nrow(df) == 0) return("")
  if (is.finite(max_rows)) df <- head(df, max_rows)
  df2 <- df
  for (nm in names(df2)) {
    if (is.numeric(df2[[nm]])) df2[[nm]] <- fmt_num(df2[[nm]], digits)
  }
  cols <- names(df2)
  lines <- c(
    paste0("| ", paste(cols, collapse = " | "), " |"),
    paste0("|", paste(rep("---", length(cols)), collapse = "|"), "|")
  )
  for (i in seq_len(nrow(df2))) {
    vals <- vapply(df2[i, , drop = FALSE], function(x) as.character(x[1]), character(1))
    vals <- gsub("\\|", "\\\\|", vals)
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

complete_data_for_rhs <- function(d, outcomes, rhs_terms, cluster_var = "xzc12_for_merge_final") {
  f <- as.formula(paste("~", paste(rhs_terms, collapse = " + ")))
  vars_needed <- unique(c(outcomes, all.vars(f), cluster_var))
  d[complete.cases(d[, vars_needed, drop = FALSE]), ]
}

wald_row <- function(d, outcome, rhs_terms, test_terms = hh_terms_main, label = "", cluster_var = "xzc12_for_merge_final") {
  fit <- fit_lm_cluster(d, outcome, rhs_terms, cluster_var = cluster_var)
  if (!fit$ok) {
    return(data.frame(
      label = label, outcome = outcome, n = nrow(fit$data), n_clusters = NA_integer_,
      r_squared = NA_real_, wald_chisq = NA_real_, wald_df = 0L, wald_p = NA_real_,
      stringsAsFactors = FALSE
    ))
  }
  w <- wald_test(fit$model, fit$vcov, test_terms)
  data.frame(
    label = label,
    outcome = outcome,
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data[[cluster_var]])),
    r_squared = summary(fit$model)$r.squared,
    wald_chisq = w$stat,
    wald_df = w$df,
    wald_p = w$p,
    stringsAsFactors = FALSE
  )
}

## -------------------------------------------------------------------------
## A. M1-to-M2 add-one-block diagnostics.
## -------------------------------------------------------------------------

m3_vars <- unique(c(
  outcomes_main,
  all.vars(as.formula(paste("~", paste(baseline_rhs("M3"), collapse = " + ")))),
  "xzc12_for_merge_final"
))
data_common_m3 <- data[complete.cases(data[, m3_vars, drop = FALSE]), ]

block_specs <- list(
  "B0_composition_category_year" = c(hh_terms_main, category_year_terms_revised),
  "B1_plus_household_resources" = c(hh_terms_main, resource_terms_revised, category_year_terms_revised),
  "B1a_M1_plus_market" = c(hh_terms_main, resource_terms_revised, market_terms_only, category_year_terms_revised),
  "B1b_M1_plus_GAEZ" = c(hh_terms_main, resource_terms_revised, gaez_terms_only, category_year_terms_revised),
  "B1c_M1_plus_province_FE" = c(hh_terms_main, resource_terms_revised, province_fe_only, category_year_terms_revised),
  "B1d_M1_plus_market_GAEZ" = c(hh_terms_main, resource_terms_revised, market_terms_only, gaez_terms_only, category_year_terms_revised),
  "B1e_M1_plus_market_province_FE" = c(hh_terms_main, resource_terms_revised, market_terms_only, province_fe_only, category_year_terms_revised),
  "B1f_M1_plus_GAEZ_province_FE" = c(hh_terms_main, resource_terms_revised, gaez_terms_only, province_fe_only, category_year_terms_revised),
  "B2_full_market_GAEZ_province_FE" = c(hh_terms_main, resource_terms_revised, market_terms_only, gaez_terms_only, province_fe_only, category_year_terms_revised),
  "B3_plus_unit_value_text" = c(hh_terms_main, resource_terms_revised, market_terms_only, gaez_terms_only, province_fe_only, unit_value_text_terms, category_year_terms_revised)
)

block_rows <- list()
for (outcome in outcomes_main) {
  for (nm in names(block_specs)) {
    row <- wald_row(data_common_m3, outcome, block_specs[[nm]], label = nm)
    row$diagnostic_family <- "add_one_block"
    row$common_sample <- "M3_complete_case"
    row$spec_order <- match(nm, names(block_specs))
    block_rows[[length(block_rows) + 1]] <- row
  }
}
tableE <- rbind_fill(block_rows)
tableE <- tableE[order(tableE$outcome, tableE$spec_order), ]
write_csv(tableE, path("outputs", "tables", "tableE_add_one_block_diagnostics.csv"))

## -------------------------------------------------------------------------
## B. Village fixed effects robustness.
## -------------------------------------------------------------------------

village_fe_rhs <- c(
  hh_terms_main,
  resource_terms_revised,
  "price_hedonic_imputed_w99_yuan_per_jin",
  "factor(data_year)",
  "factor(food_category)",
  "factor(xzc12_for_merge_final)"
)

village_rows <- list()
for (outcome in outcomes_main) {
  row <- wald_row(data_common_m3, outcome, village_fe_rhs, label = "village_FE_M3_like")
  row$absorbed_controls <- "province_FE_market_GAEZ_text_absorbed_or_collinear_at_village_county_level"
  row$common_sample <- "M3_complete_case"
  village_rows[[length(village_rows) + 1]] <- row
}

for (cat in food_order) {
  dcat <- data_common_m3[data_common_m3$food_category == cat, ]
  if (nrow(dcat) == 0) next
  rhs_cat <- setdiff(village_fe_rhs, "factor(food_category)")
  row <- wald_row(dcat, "production_participation", rhs_cat, label = paste0("village_FE_category_", cat))
  row$food_category <- cat
  row$food_category_label <- dcat$food_category_label[1]
  row$absorbed_controls <- "category_specific_village_FE"
  row$common_sample <- "M3_complete_case"
  village_rows[[length(village_rows) + 1]] <- row
}

tableF <- rbind_fill(village_rows)
write_csv(tableF, path("outputs", "tables", "tableF_village_fe_robustness.csv"))

## -------------------------------------------------------------------------
## C. Logit/probit robustness for participation.
## -------------------------------------------------------------------------

fit_glm_cluster <- function(d, outcome, rhs_terms, link, cluster_var = "xzc12_for_merge_final") {
  f <- as.formula(paste(outcome, "~", paste(rhs_terms, collapse = " + ")))
  vars_needed <- unique(c(all.vars(f), cluster_var))
  d0 <- d[complete.cases(d[, vars_needed, drop = FALSE]), ]
  if (nrow(d0) < 100 || length(unique(d0[[outcome]])) < 2) {
    return(list(ok = FALSE, formula = f, data = d0, model = NULL, vcov = NULL, warnings = "insufficient_outcome_variation"))
  }
  warns <- character()
  model <- tryCatch(
    withCallingHandlers(
      glm(f, data = d0, family = binomial(link = link), control = glm.control(maxit = 75)),
      warning = function(w) {
        warns <<- c(warns, conditionMessage(w))
        invokeRestart("muffleWarning")
      }
    ),
    error = function(e) e
  )
  if (inherits(model, "error")) {
    return(list(ok = FALSE, formula = f, data = d0, model = NULL, vcov = NULL, warnings = conditionMessage(model)))
  }
  vc <- tryCatch(cluster_vcov(model, d0[[cluster_var]]), error = function(e) e)
  if (inherits(vc, "error")) {
    return(list(ok = FALSE, formula = f, data = d0, model = model, vcov = NULL, warnings = conditionMessage(vc)))
  }
  list(ok = TRUE, formula = f, data = d0, model = model, vcov = vc, warnings = paste(unique(warns), collapse = " | "))
}

glm_row <- function(d, outcome, rhs_terms, link, label) {
  fit <- fit_glm_cluster(d, outcome, rhs_terms, link)
  ybar <- mean(fit$data[[outcome]], na.rm = TRUE)
  low_variation <- is.finite(ybar) && (ybar < 0.05 || ybar > 0.95)
  if (!fit$ok) {
    return(data.frame(
      model_family = link, label = label, outcome = outcome,
      n = nrow(fit$data), n_clusters = NA_integer_, outcome_mean = ybar,
      converged = FALSE, wald_chisq = NA_real_, wald_df = 0L, wald_p = NA_real_,
      low_variation_flag = low_variation,
      recommended_use = ifelse(low_variation, "do_not_interpret_low_variation_or_separation", "failed_model"),
      warnings = fit$warnings, stringsAsFactors = FALSE
    ))
  }
  w <- wald_test(fit$model, fit$vcov, hh_terms_main)
  data.frame(
    model_family = link,
    label = label,
    outcome = outcome,
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
    outcome_mean = ybar,
    converged = isTRUE(fit$model$converged),
    wald_chisq = w$stat,
    wald_df = w$df,
    wald_p = w$p,
    low_variation_flag = low_variation,
    recommended_use = ifelse(low_variation, "do_not_interpret_low_variation_or_separation", "supporting_functional_form_check"),
    warnings = fit$warnings,
    stringsAsFactors = FALSE
  )
}

glm_rows <- list()
for (link in c("logit", "probit")) {
  glm_rows[[length(glm_rows) + 1]] <- glm_row(data_common_m3, "production_participation", baseline_rhs("M3"), link, "overall_M3")
  for (cat in food_order) {
    dcat <- data[data$food_category == cat, ]
    rhs_cat <- setdiff(baseline_rhs("M3"), "factor(food_category)")
    row <- glm_row(dcat, "production_participation", rhs_cat, link, paste0("category_", cat))
    row$food_category <- cat
    row$food_category_label <- dcat$food_category_label[1]
    glm_rows[[length(glm_rows) + 1]] <- row
  }
}
tableG <- rbind_fill(glm_rows)
write_csv(tableG, path("outputs", "tables", "tableG_binary_response_robustness.csv"))

## -------------------------------------------------------------------------
## D. Multiple-testing correction and reframed category diagnostics.
## -------------------------------------------------------------------------

table4 <- read_csv(path("outputs", "tables", "table4_category_specific_nsi.csv"))
table1cat <- read_csv(path("outputs", "tables", "table1_category_participation_revised.csv"))

tableH <- table4[, c(
  "food_category", "food_category_label", "outcome_mean", "hhcomp_wald_chisq",
  "hhcomp_wald_df", "hhcomp_wald_p", "nsi", "main_coefficient_drivers"
)]
tableH$p_bonferroni <- p.adjust(tableH$hhcomp_wald_p, method = "bonferroni")
tableH$p_holm <- p.adjust(tableH$hhcomp_wald_p, method = "holm")
tableH$p_bh_fdr <- p.adjust(tableH$hhcomp_wald_p, method = "BH")
tableH$significant_raw_5pct <- tableH$hhcomp_wald_p < 0.05
tableH$significant_bh_fdr_5pct <- tableH$p_bh_fdr < 0.05
tableH$significant_bonferroni_5pct <- tableH$p_bonferroni < 0.05
write_csv(tableH, path("outputs", "tables", "tableH_category_multiple_testing.csv"))

tableI <- merge(
  tableH,
  table1cat[, c("food_category", "participation_rate", "mean_self_suff_rate", "mean_cons_monthly_jin", "mean_selfprod_monthly_total")],
  by = "food_category",
  all.x = TRUE
)
tableI$nsi_rank_detectability <- rank(-tableI$nsi, ties.method = "min")
tableI$self_suff_rank_economic_importance <- rank(-tableI$mean_self_suff_rate, ties.method = "min")
tableI$variation_flag <- ifelse(
  tableI$participation_rate < 0.05, "near_zero_variation_exclude_main",
  ifelse(tableI$participation_rate > 0.95, "near_ceiling_variation_caution",
    ifelse(tableI$participation_rate > 0.80, "high_participation_ceiling_caution", "middle_range_variation")
  )
)
tableI$main_text_status <- ifelse(
  tableI$food_category == "nailei", "exclude_from_main_category_interpretation",
  ifelse(tableI$food_category == "youzhi", "definition_pending_human_review",
    ifelse(tableI$food_category == "roulei", "aggregate_meat_aquatic_limitations",
      ifelse(tableI$variation_flag == "middle_range_variation", "main_comparable_category", "interpret_with_variation_caution")
    )
  )
)
tableI$nsi_interpretation <- "detectability_ranking_not_economic_magnitude"
tableI <- tableI[order(tableI$nsi_rank_detectability), ]
write_csv(tableI, path("outputs", "tables", "tableI_category_variation_and_nsi_reframed.csv"))

png(path("outputs", "figures", "figure2_editor_nsi_detectability.png"), width = 1900, height = 1150, res = 180)
plot_df <- tableI[order(tableI$nsi), ]
cols <- ifelse(plot_df$main_text_status == "exclude_from_main_category_interpretation", "#B8B8B8",
  ifelse(plot_df$significant_bh_fdr_5pct, "#2F6B9A", "#8BA6A9"))
par(mar = c(6, 9, 4, 2))
barplot(
  plot_df$nsi,
  names.arg = plot_df$food_category_label,
  horiz = TRUE,
  las = 1,
  col = cols,
  border = NA,
  xlab = "Relative Wald statistic (category Wald / mean category Wald)",
  main = "Category Detectability Ranking, Not Economic Magnitude"
)
abline(v = 1, lty = 2, col = "#666666")
legend("bottomright", legend = c("BH FDR < 0.05", "Not BH-significant", "Excluded/caution"), fill = c("#2F6B9A", "#8BA6A9", "#B8B8B8"), border = NA, bty = "n")
dev.off()

## -------------------------------------------------------------------------
## E. Fixed common-sample robustness for composition and price variants.
## -------------------------------------------------------------------------

fit_wald_generic <- function(d, outcome, terms, controls) {
  fit <- fit_lm_cluster(d, outcome, c(terms, controls))
  if (!fit$ok) {
    return(data.frame(n = nrow(fit$data), n_clusters = NA_integer_, r_squared = NA_real_, wald_chisq = NA_real_, wald_df = 0L, wald_p = NA_real_))
  }
  w <- wald_test(fit$model, fit$vcov, terms)
  data.frame(
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
    r_squared = summary(fit$model)$r.squared,
    wald_chisq = w$stat,
    wald_df = w$df,
    wald_p = w$p,
    stringsAsFactors = FALSE
  )
}

comp_specs <- list(
  proportion = hh_terms_main,
  dependency = c("household_size_reconstructed", "dependency_ratio", "female_share"),
  counts = c("num_children", "num_elderly", "num_adult_male", "num_adult_female")
)
controls_no_hh <- c(resource_terms_revised, market_gaez_terms_revised, price_text_terms_revised, category_year_terms_revised)
outcomes_with_selfsuff <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate")
all_comp_vars <- unique(unlist(comp_specs, use.names = FALSE))
fixed_comp_vars <- unique(c(outcomes_with_selfsuff, all_comp_vars, all.vars(as.formula(paste("~", paste(controls_no_hh, collapse = " + ")))), "xzc12_for_merge_final"))
data_fixed_comp <- data[complete.cases(data[, fixed_comp_vars, drop = FALSE]), ]

fixed_comp_rows <- list()
for (comp in names(comp_specs)) {
  terms <- comp_specs[[comp]]
  for (outcome in outcomes_with_selfsuff) {
    res <- fit_wald_generic(data_fixed_comp, outcome, terms, controls_no_hh)
    fixed_comp_rows[[length(fixed_comp_rows) + 1]] <- data.frame(
      composition_spec = comp,
      outcome = outcome,
      fixed_common_sample = TRUE,
      tested_terms = paste(terms, collapse = " + "),
      res,
      stringsAsFactors = FALSE
    )
  }
}
tableJ <- rbind_fill(fixed_comp_rows)
write_csv(tableJ, path("outputs", "tables", "tableJ_fixed_common_sample_robustness.csv"))

price_specs <- list(
  no_unit_value = setdiff(price_text_terms_revised, "price_hedonic_imputed_w99_yuan_per_jin"),
  hedonic_unit_value = price_text_terms_revised,
  observed_household_unit_value = c("price_preferred_household_recalc_w99_yuan_per_jin", setdiff(price_text_terms_revised, "price_hedonic_imputed_w99_yuan_per_jin")),
  village_median_unit_value = c("village_price_category_median", setdiff(price_text_terms_revised, "price_hedonic_imputed_w99_yuan_per_jin"))
)
price_common_vars <- unique(c(
  "production_participation", hh_terms_main, resource_terms_revised, market_gaez_terms_revised,
  unlist(price_specs, use.names = FALSE), category_year_terms_revised, "xzc12_for_merge_final"
))
data_fixed_price <- complete_data_for_rhs(
  data,
  "production_participation",
  c(hh_terms_main, resource_terms_revised, market_gaez_terms_revised, unlist(price_specs, use.names = FALSE), category_year_terms_revised)
)
fixed_price_rows <- list()
for (nm in names(price_specs)) {
  rhs <- c(hh_terms_main, resource_terms_revised, market_gaez_terms_revised, price_specs[[nm]], category_year_terms_revised)
  row <- wald_row(data_fixed_price, "production_participation", rhs, label = nm)
  row$fixed_common_sample <- TRUE
  fixed_price_rows[[length(fixed_price_rows) + 1]] <- row
}
tableJ_price <- rbind_fill(fixed_price_rows)
write_csv(tableJ_price, path("outputs", "tables", "tableJ_fixed_common_sample_price_robustness.csv"))

## -------------------------------------------------------------------------
## F. Bad-control/fixed-factor sensitivity.
## -------------------------------------------------------------------------

bad_control_specs <- list(
  full_M3_resources = baseline_rhs("M3"),
  fixed_factors_no_income_expense = c(hh_terms_main, fixed_resource_terms, market_gaez_terms_revised, price_text_terms_revised, category_year_terms_revised),
  fixed_factors_no_income_expense_land_w99 = c(hh_terms_main, setdiff(fixed_resource_terms, "total_sown_area"), "total_sown_area_w99", market_gaez_terms_revised, price_text_terms_revised, category_year_terms_revised)
)

bad_rows <- list()
for (outcome in outcomes_main) {
  rhs_all <- unique(unlist(bad_control_specs, use.names = FALSE))
  d_bad <- complete_data_for_rhs(data, outcome, rhs_all)
  for (nm in names(bad_control_specs)) {
    row <- wald_row(d_bad, outcome, bad_control_specs[[nm]], label = nm)
    row$fixed_common_sample_across_bad_control_specs <- TRUE
    bad_rows[[length(bad_rows) + 1]] <- row
  }
}
tableK <- rbind_fill(bad_rows)
write_csv(tableK, path("outputs", "tables", "tableK_fixed_factors_bad_controls_robustness.csv"))

## -------------------------------------------------------------------------
## G. Missingness and definition diagnostics.
## -------------------------------------------------------------------------

source_selfprod_missing <- sum(is.na(data$selfprod_monthly_total))
source_participation_missing <- sum(is.na(data$production_participation))
missing_table <- data.frame(
  diagnostic = c(
    "selfprod_monthly_total_missing_in_current_long_file",
    "production_participation_missing_in_current_long_file",
    "na_to_zero_robustness_status"
  ),
  value = c(
    as.character(source_selfprod_missing),
    as.character(source_participation_missing),
    "not_reconstructable_from_current_analysis_ready_or_cleaned_long_files"
  ),
  implication = c(
    "The current long files no longer preserve item-level source missingness.",
    "Participation is fully populated after prior cleaning.",
    "Report as a limitation and rerun only if raw item-level missing codes are restored."
  ),
  stringsAsFactors = FALSE
)
write_csv(missing_table, path("outputs", "tables", "tableL_participation_missingness_robustness.csv"))

hh_once <- data[!duplicated(data$nhCode), ]
hh_year_counts <- tapply(data$data_year, data$nhCode, function(x) length(unique(x)))
definition_rows <- list(
  data.frame(
    diagnostic = "pooled_repeated_cross_section",
    value = paste0("min_years_per_nhCode=", min(hh_year_counts), "; max_years_per_nhCode=", max(hh_year_counts)),
    numeric_value = max(hh_year_counts),
    decision = "No household fixed effects are feasible with current nhCode; use pooled repeated cross-section language.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "households_at_roster_cap_8",
    value = paste0(sum(hh_once$household_size_reconstructed >= 8, na.rm = TRUE), " of ", nrow(hh_once), " households"),
    numeric_value = mean(hh_once$household_size_reconstructed >= 8, na.rm = TRUE),
    decision = "Roster cap is visible but rare; disclose in data limitations.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "total_sown_area_w99_max",
    value = paste0("max=", max(hh_once$total_sown_area_w99, na.rm = TRUE), "; p99=", as.numeric(quantile(hh_once$total_sown_area_w99, 0.99, na.rm = TRUE))),
    numeric_value = max(hh_once$total_sown_area_w99, na.rm = TRUE),
    decision = "Winsorized total sown area is used as a sensitivity check; main setup still uses total_sown_area.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "sex_coding_audit",
    value = "household_head_gender_male inferred from earlier household relation cross-check, codebook confirmation still needed",
    numeric_value = NA_real_,
    decision = "Keep female_share interpretation conditional until HA2 coding is manually verified.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "youzhi_definition",
    value = "partially identified; item-code review required",
    numeric_value = NA_real_,
    decision = "Do not make strong substantive claims about oils before item-code review.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "roulei_aggregation",
    value = "meat plus aquatic plus processed products in current aggregate category",
    numeric_value = NA_real_,
    decision = "Use label meat/aquatic products and state aggregation limitation.",
    stringsAsFactors = FALSE
  )
)
tableM <- rbind_fill(definition_rows)
write_csv(tableM, path("outputs", "tables", "tableM_definition_diagnostics_editor.csv"))

## -------------------------------------------------------------------------
## H. Price-unit-value diagnostics gathered for reporting.
## -------------------------------------------------------------------------

price_source <- read_csv(path("outputs", "tables", "hedonic_price_imputation_source_summary.csv"))
price_model <- read_csv(path("outputs", "tables", "hedonic_price_model_diagnostics.csv"))
price_rob <- read_csv(path("outputs", "tables", "tableC_price_robustness.csv"))

price_diag <- data.frame(
  diagnostic = c("observed_unit_value_share", "hedonic_imputed_share", "county_hedonic_r_squared", "county_hedonic_rmse_log", "observed_only_participation_p"),
  value = c(
    price_source$share[price_source$price_hedonic_source == "observed_household_recalc"],
    price_source$share[price_source$price_hedonic_source == "hedonic_county"],
    price_model$r_squared[price_model$model == "county"],
    price_model$rmse_log_in_sample[price_model$model == "county"],
    price_rob$hhcomp_wald_p[price_rob$price_spec == "observed_price_only" & price_rob$outcome == "production_participation"]
  ),
  interpretation = c(
    "Observed variable is household purchase-side unit value, not pure exogenous price.",
    "A sizeable share is imputed and should be disclosed.",
    "Hedonic imputation explains a moderate share of log unit-value variation.",
    "RMSE implies noisy unit-value prediction.",
    "Observed-only robustness remains statistically similar for participation, but on a selected purchasing subsample."
  ),
  stringsAsFactors = FALSE
)
write_csv(price_diag, path("outputs", "tables", "tableN_price_unit_value_diagnostics.csv"))

## -------------------------------------------------------------------------
## I. Logs, JSON, and addendum report.
## -------------------------------------------------------------------------

model_summary <- rbind_fill(list(
  data.frame(output = "tableE_add_one_block_diagnostics.csv", rows = nrow(tableE), stringsAsFactors = FALSE),
  data.frame(output = "tableF_village_fe_robustness.csv", rows = nrow(tableF), stringsAsFactors = FALSE),
  data.frame(output = "tableG_binary_response_robustness.csv", rows = nrow(tableG), stringsAsFactors = FALSE),
  data.frame(output = "tableH_category_multiple_testing.csv", rows = nrow(tableH), stringsAsFactors = FALSE),
  data.frame(output = "tableI_category_variation_and_nsi_reframed.csv", rows = nrow(tableI), stringsAsFactors = FALSE),
  data.frame(output = "tableJ_fixed_common_sample_robustness.csv", rows = nrow(tableJ), stringsAsFactors = FALSE),
  data.frame(output = "tableK_fixed_factors_bad_controls_robustness.csv", rows = nrow(tableK), stringsAsFactors = FALSE),
  data.frame(output = "tableL_participation_missingness_robustness.csv", rows = nrow(missing_table), stringsAsFactors = FALSE),
  data.frame(output = "tableM_definition_diagnostics_editor.csv", rows = nrow(tableM), stringsAsFactors = FALSE),
  data.frame(output = "tableN_price_unit_value_diagnostics.csv", rows = nrow(price_diag), stringsAsFactors = FALSE)
))
write_simple_json(model_summary, path("outputs", "model_summaries", "modelE_editor_revision_analyses.json"), key = "editor_revision_outputs")

add_one_part <- tableE[tableE$outcome == "production_participation", c("label", "n", "n_clusters", "wald_chisq", "wald_p")]
add_one_log <- tableE[tableE$outcome == "log_selfprod_amount", c("label", "n", "n_clusters", "wald_chisq", "wald_p")]
village_overall <- tableF[tableF$label == "village_FE_M3_like", c("outcome", "n", "n_clusters", "wald_chisq", "wald_p")]
glm_overall <- tableG[tableG$label == "overall_M3", c("model_family", "n", "n_clusters", "outcome_mean", "converged", "wald_chisq", "wald_p")]
cat_report <- tableI[, c("food_category_label", "participation_rate", "mean_self_suff_rate", "nsi", "hhcomp_wald_p", "p_bh_fdr", "main_text_status")]
fixed_comp_report <- tableJ[tableJ$outcome == "production_participation", c("composition_spec", "n", "n_clusters", "wald_chisq", "wald_p")]
bad_report <- tableK[tableK$outcome == "production_participation", c("label", "n", "n_clusters", "wald_chisq", "wald_p")]

report_lines <- c(
  "# Paper 1 Editor-Revision Results Addendum",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "This addendum implements the additional diagnostics requested in `paper1_editor_review_and_action_plan.md`. It should be read together with `paper1_revised_results_package.md`.",
  "",
  "## 1. Revised Bottom Line / 修订后核心结论",
  "",
  "- 最稳妥的正文表述应改为：在加入省份、市场可达性、农业生态、购买侧单位值和县级文本控制后，户内人口结构能够条件性预测自产自给参与；但该结果对控制集敏感，且不能通过村庄固定效应的参与边际稳健性检验。",
  "- M1 以后数量边际整体较弱；固定共同样本下部分数量口径重新显著，说明数量结果具有样本和口径敏感性，应作为辅助描述而非主结论。",
  "- logit/probit 对总体 M3 参与边际给出相近结论，说明 M3 的参与结果不是简单 LPM 泛函形式造成的。",
  "- NSI 已重新定位为 Wald 检验统计量的相对可检测性排序，不是经济幅度指数；奶类因参与率接近 0 从主类别解释中剔除。",
  "",
  "## 2. Add-One-Block Diagnostics: Participation",
  "",
  md_table(add_one_part, digits = 4),
  "",
  "## 3. Add-One-Block Diagnostics: Log Quantity",
  "",
  md_table(add_one_log, digits = 4),
  "",
  "## 4. Village Fixed Effects Robustness",
  "",
  md_table(village_overall, digits = 4),
  "",
  "Interpretation: village fixed effects shift identification to within-village household comparisons. In this check, the participation-margin Wald test is not significant, while the log/IHS quantity margins become significant. This weakens any claim that the M3 participation result is fully robust. Village-level market, GAEZ, province, and much of county text variation are absorbed or collinear, so this is a robustness check rather than the preferred mechanism specification.",
  "",
  "## 5. Logit/Probit Participation Robustness",
  "",
  md_table(glm_overall, digits = 4),
  "",
  "Category-specific logit/probit rows are in `outputs/tables/tableG_binary_response_robustness.csv`; extreme categories, especially dairy, should be read with separation/low-variation caution.",
  "",
  "## 6. Category Multiple Testing and NSI Reframing",
  "",
  md_table(cat_report, digits = 4),
  "",
  "Interpretation: the category table now reports raw p-values and BH FDR q-values. NSI remains useful for describing where the Wald test is most detectable, but it is not an effect size. Participation and self-sufficiency are reported side by side to separate detectability from economic importance.",
  "",
  "## 7. Fixed Common-Sample Composition Robustness",
  "",
  md_table(fixed_comp_report, digits = 4),
  "",
  "The original robustness table used different samples across proportion, dependency-ratio, and count specifications. This fixed-sample table uses the intersection of all variables needed by all composition definitions and outcomes.",
  "",
  "## 8. Fixed-Factor / Bad-Control Sensitivity",
  "",
  md_table(bad_report, digits = 4),
  "",
  "The no-income/no-expense specifications respond to the concern that income and expenditure may be jointly determined with self-provisioning. These should be discussed alongside the full M3 results.",
  "",
  "## 9. Price and Unit-Value Diagnostics",
  "",
  md_table(price_diag, digits = 4),
  "",
  "Price variables should be described as purchase-side unit values. The hedonic values are imputations for missing purchase unit values, not farm-gate selling prices. This limits how strongly price controls can be interpreted in a market-separability framework.",
  "",
  "## 10. Data Definition Diagnostics",
  "",
  md_table(tableM, digits = 4),
  "",
  "## 11. Missingness Robustness Status",
  "",
  md_table(missing_table, digits = 4),
  "",
  "## 12. New Artifacts",
  "",
  md_table(model_summary, digits = 0)
)

writeLines(report_lines, path("outputs", "reports", "paper1_editor_revision_results_addendum.md"), useBytes = TRUE)

log_lines <- c(
  "# Editor Review Action Log",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "Completed with current analysis-ready data:",
  "",
  "- Add-one-block diagnostics for M0/M1/M2/M3 sensitivity and M1-to-M2 block attribution.",
  "- Village fixed-effects robustness for overall outcomes and category-specific participation.",
  "- Logit/probit participation robustness for overall and category-specific models.",
  "- Bonferroni, Holm, and BH FDR corrections for category-level Wald tests.",
  "- NSI reframing with participation/self-sufficiency and low-variation flags.",
  "- Fixed common-sample composition and price robustness checks.",
  "- Fixed-factor/no-income/no-expense sensitivity checks.",
  "- Price unit-value and hedonic imputation diagnostics.",
  "- Definition diagnostics for repeated-cross-section status, roster cap, land winsorization, sex coding, oils, and meat/aquatic aggregation.",
  "",
  "Still requires manual or raw-item-code work:",
  "",
  "- HA2 sex-codebook verification for `female_share` interpretation.",
  "- Item-code review for `youzhi` and detail-level rebuild if meat versus aquatic categories are to be split.",
  "- Raw item-level missing-code recovery before a valid NA-to-zero versus missing-exclusion participation robustness can be run.",
  "- Formal theoretical model and replacement of the placeholder conceptual framework figure."
)
writeLines(log_lines, path("outputs", "logs", "editor_review_action_log.md"), useBytes = TRUE)

message("Editor-revision analyses completed.")