source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

base_no_price <- c(
  hh_terms_main, resource_terms_revised, market_gaez_terms_revised,
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
  category_year_terms_revised
)

specs <- list(
  no_price_control = list(price_var = NA_character_, rhs = base_no_price, subset = rep(TRUE, nrow(data))),
  hedonic_price_main = list(price_var = "price_hedonic_imputed_w99_yuan_per_jin", rhs = c(base_no_price, "price_hedonic_imputed_w99_yuan_per_jin"), subset = rep(TRUE, nrow(data))),
  observed_price_only = list(price_var = "price_preferred_household_recalc_w99_yuan_per_jin", rhs = c(base_no_price, "price_preferred_household_recalc_w99_yuan_per_jin"), subset = !is.na(data$price_preferred_household_recalc_w99_yuan_per_jin)),
  county_category_median_price = list(price_var = "village_price_category_median", rhs = c(base_no_price, "village_price_category_median"), subset = !is.na(data$village_price_category_median))
)

rows <- list()
issues <- c()
for (nm in names(specs)) {
  sp <- specs[[nm]]
  d <- data[sp$subset, ]
  if (nrow(d) < 100) {
    issues <- c(issues, paste0("- Skipped ", nm, ": fewer than 100 rows after price restriction."))
    next
  }
  fit <- fit_lm_cluster(d, "production_participation", sp$rhs)
  if (!fit$ok) {
    issues <- c(issues, paste0("- Skipped ", nm, ": model could not be estimated."))
    next
  }
  w <- wald_test(fit$model, fit$vcov, hh_terms_main)
  price_var_display <- ifelse(is.na(sp$price_var), "none", sp$price_var)
  price_var_display <- sub("yuan_per_jin$", "yuan_per_kg", price_var_display)
  price_var_display <- ifelse(
    price_var_display == "village_price_category_median",
    "village_price_category_median_yuan_per_kg",
    price_var_display
  )
  rows[[length(rows) + 1]] <- data.frame(
    price_spec = nm,
    model_compatibility_variable = ifelse(is.na(sp$price_var), "none", sp$price_var),
    price_variable = price_var_display,
    price_unit = ifelse(is.na(sp$price_var), "none", "yuan/kg"),
    outcome = "production_participation",
    conceptual_outcome = "self_provisioning_participation",
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
    r_squared = summary(fit$model)$r.squared,
    hhcomp_wald_chisq = w$stat,
    hhcomp_wald_df = w$df,
    hhcomp_wald_p = w$p,
    price_observed_share = ifelse(
      "price_hedonic_source" %in% names(fit$data),
      mean(fit$data$price_hedonic_source == "observed_household_recalc", na.rm = TRUE),
      NA_real_
    ),
    stringsAsFactors = FALSE
  )
}

tableC <- do.call(rbind, rows)
write_csv(tableC, path("outputs", "tables", "tableC_price_robustness.csv"))
write_simple_json(tableC, path("outputs", "model_summaries", "modelC_price_robustness.json"), key = "price_robustness")

if (length(issues) == 0) issues <- "- None. All requested price robustness variants were generated."
log_lines <- c(
  "# Price Robustness Issues",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Notes",
  "",
  "- Price variables are interpreted as yuan/kg in the cleaned analysis data.",
  "- Main price variable: `price_hedonic_imputed_w99_yuan_per_kg`.",
  "- Observed-price-only uses `price_preferred_household_recalc_w99_yuan_per_kg` and drops rows with missing observed recalculated price.",
  "- County-category median price uses `village_price_category_median_yuan_per_kg` and drops rows with missing median price.",
  "- The model still reads legacy compatibility aliases ending in `_yuan_per_jin`; those alias values were overwritten to yuan/kg by `code/19_apply_kg_units_drop_outliers_prepare_official_data.R`.",
  "",
  "## Issues",
  "",
  issues
)
writeLines(log_lines, path("outputs", "logs", "price_robustness_issues.md"), useBytes = TRUE)

message("Price robustness completed.")