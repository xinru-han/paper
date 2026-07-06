source("code/00_setup.R")

input_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
if (!file.exists(input_file)) {
  input_file <- path("data", "cleaned", "paper1_household_category_long.csv")
}

data <- read_csv(
  input_file,
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)

required_categories <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
data <- data[data$food_category %in% required_categories, ]
data <- prepare_revised_data(data)

revised_file <- path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv")
write_csv(data, revised_file)

sample_summary <- data.frame(
  item = c(
    "rows", "households", "food_categories", "villages_clusters",
    "provinces", "counties", "duplicate_household_category_keys"
  ),
  value = c(
    nrow(data),
    length(unique(data$nhCode)),
    length(unique(data$food_category)),
    length(unique(data$xzc12_for_merge_final)),
    length(unique(data$provn_std)),
    length(unique(data$countyn_std)),
    sum(duplicated(paste(data$nhCode, data$food_category)))
  ),
  stringsAsFactors = FALSE
)

by_year <- as.data.frame(table(data$data_year), stringsAsFactors = FALSE)
names(by_year) <- c("data_year", "n_rows")
by_cat <- as.data.frame(table(data$food_category), stringsAsFactors = FALSE)
names(by_cat) <- c("food_category", "n_rows")
by_cat <- merge(
  by_cat,
  unique(data[, c("food_category", "food_category_label")]),
  by = "food_category",
  all.x = TRUE,
  sort = FALSE
)

core_vars <- c(
  "production_participation", "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate",
  "household_size_reconstructed", "child_share", "elderly_share", "female_share",
  "market_friction_survey", "poi_market_friction_lag1", "combined_market_friction",
  "price_hedonic_imputed_w99_yuan_per_jin", "price_preferred_household_recalc_w99_yuan_per_jin",
  "village_price_category_median", "gaez_overall_si_10km", "gaez_staple_si_10km",
  "gaez_soil_terrain_constraint_10km", "risk_salience_z_5yr_sum",
  "governance_capacity_z_5yr_sum", "trust_signal_z_5yr_sum", "attention_z_5yr_sum"
)
missingness <- data.frame(
  module = c(
    rep("outcome", 4), rep("household_composition", 4), rep("market", 3),
    rep("price", 3), rep("gaez", 3), rep("text", 4)
  )[seq_along(core_vars)],
  variable = core_vars,
  n_rows = nrow(data),
  n_missing = sapply(core_vars, function(v) if (v %in% names(data)) sum(is.na(data[[v]])) else NA_integer_),
  missing_share = sapply(core_vars, function(v) if (v %in% names(data)) mean(is.na(data[[v]])) else NA_real_),
  stringsAsFactors = FALSE
)

category_summary <- aggregate(
  cbind(production_participation, cons_monthly_jin, selfprod_monthly_total, self_suff_rate) ~ food_category + food_category_label,
  data = data,
  FUN = function(x) mean(x, na.rm = TRUE)
)
names(category_summary)[names(category_summary) == "production_participation"] <- "participation_rate"
names(category_summary)[names(category_summary) == "cons_monthly_jin"] <- "mean_cons_monthly_jin"
names(category_summary)[names(category_summary) == "selfprod_monthly_total"] <- "mean_selfprod_monthly_total"
names(category_summary)[names(category_summary) == "self_suff_rate"] <- "mean_self_suff_rate"

desc_vars <- c(
  "production_participation", "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate",
  hh_terms_main,
  "dependency_ratio", "num_children", "num_elderly", "num_adult_male", "num_adult_female",
  "log1p_total_income_w_w99", "log1p_agri_business_income_w99", "log1p_annual_expense_total_w99",
  "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
  "market_friction_survey", "poi_market_friction_lag1", "combined_market_friction",
  "price_hedonic_imputed_w99_yuan_per_jin"
)
desc <- summarise_numeric(data, desc_vars, "revised_analysis")

write_csv(sample_summary, path("outputs", "tables", "table1_sample_summary_revised.csv"))
write_csv(by_year, path("outputs", "tables", "table1_observations_by_year_revised.csv"))
write_csv(by_cat, path("outputs", "tables", "table1_observations_by_category_revised.csv"))
write_csv(missingness, path("outputs", "tables", "table1_missingness_revised.csv"))
write_csv(category_summary, path("outputs", "tables", "table1_category_participation_revised.csv"))
write_csv(desc, path("outputs", "tables", "table1_descriptive_statistics_revised.csv"))

commercial_vars <- grep("commercial|sale|sell|出售|销售|商品", names(data), ignore.case = TRUE, value = TRUE)
commercial_log <- c(
  "# Commercialization Rate Audit",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Finding",
  "",
  "- `commercialization_rate` is not present in the current analysis-ready household-category file.",
  "- Current analysis-ready columns only contain self-provisioning participation, self-production amount, consumption, self-sufficiency, and price variables.",
  "- Raw labels indicate sales and self-use quantities exist for some production modules, but denominators differ by module and category.",
  "- A clean commercialization rate therefore requires a separate denominator audit before inclusion.",
  "",
  "## Matching variables found in analysis-ready data",
  "",
  if (length(commercial_vars) == 0) "- None." else paste0("- `", commercial_vars, "`"),
  "",
  "## Decision",
  "",
  "- Do not construct `commercialization_rate` in the revised main rerun.",
  "- Record as HUMAN REVIEW REQUIRED: denominator unclear."
)
writeLines(commercial_log, path("outputs", "logs", "commercialization_rate_audit.md"), useBytes = TRUE)

issue_lines <- c(
  "# Revised Variable Issues",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "- `commercialization_rate` is unavailable in the current analysis-ready data and is not constructed without denominator review.",
  "- `roulei` split and `youzhi` definition require category-definition audit outputs.",
  "- Main code variable remains `production_participation`; prose label should be self-provisioning participation."
)
writeLines(issue_lines, path("outputs", "logs", "revised_variable_issues.md"), useBytes = TRUE)

merge_log <- c(
  "# Revised Data Merge Log",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  paste0("- Input file: `", input_file, "`."),
  paste0("- Output file: `", revised_file, "`."),
  "- The revised analysis file inherits the cleaned geography, POI-year rule, hedonic price imputation, GAEZ, terrain, early NTL, county text, and household resource controls from the previously rebuilt analysis-ready long file.",
  "- Food categories are restricted to the eight revised categories; condiments, sugar, and tea are excluded.",
  "",
  "## Sample summary",
  "",
  paste0("- Rows: ", nrow(data)),
  paste0("- Households: ", length(unique(data$nhCode))),
  paste0("- Food categories: ", length(unique(data$food_category))),
  paste0("- Villages/clusters: ", length(unique(data$xzc12_for_merge_final))),
  paste0("- Provinces: ", length(unique(data$provn_std))),
  paste0("- Counties: ", length(unique(data$countyn_std)))
)
writeLines(merge_log, path("outputs", "logs", "revised_data_merge_log.md"), useBytes = TRUE)

message("Revised analysis data rebuilt.")