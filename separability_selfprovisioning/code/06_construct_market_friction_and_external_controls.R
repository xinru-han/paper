options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "cleaned"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "data", "analysis_ready"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
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

trim_text <- function(x) {
  x <- as.character(x)
  x <- gsub("\ufeff", "", x, fixed = TRUE)
  x <- gsub("[[:space:]\u3000]+", "", x)
  x[x == ""] <- NA_character_
  x
}

to_num <- function(x) {
  if (is.numeric(x)) return(x)
  suppressWarnings(as.numeric(trim_text(x)))
}

zscore <- function(x) {
  x <- to_num(x)
  s <- sd(x, na.rm = TRUE)
  if (is.na(s) || s == 0) return(rep(NA_real_, length(x)))
  (x - mean(x, na.rm = TRUE)) / s
}

row_mean_min <- function(mat, min_nonmissing = 1) {
  mat <- as.matrix(mat)
  n_ok <- rowSums(!is.na(mat))
  out <- rowMeans(mat, na.rm = TRUE)
  out[n_ok < min_nonmissing] <- NA_real_
  out
}

first_nonmissing <- function(x) {
  x <- x[!is.na(x) & x != ""]
  if (length(x) == 0) NA else x[1]
}

dedupe_by_key <- function(data, key) {
  if (!any(duplicated(data[[key]]))) return(data)
  split_data <- split(data, data[[key]])
  rows <- lapply(split_data, function(d) {
    out <- d[1, , drop = FALSE]
    for (v in names(d)) {
      if (v == key) next
      x_num <- suppressWarnings(as.numeric(d[[v]]))
      if (sum(!is.na(x_num)) > 0 && sum(!is.na(x_num)) >= sum(!is.na(trim_text(d[[v]]))) * 0.8) {
        out[[v]] <- mean(x_num, na.rm = TRUE)
      } else {
        out[[v]] <- first_nonmissing(trim_text(d[[v]]))
      }
    }
    out
  })
  do.call(rbind, rows)
}

summarise_numeric <- function(data, vars, module) {
  rows <- lapply(vars[vars %in% names(data)], function(v) {
    x <- to_num(data[[v]])
    ok <- !is.na(x)
    qs <- if (any(ok)) {
      as.numeric(quantile(x, c(0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99), na.rm = TRUE, names = FALSE))
    } else {
      rep(NA_real_, 7)
    }
    data.frame(
      module = module,
      variable = v,
      n = length(x),
      missing = sum(!ok),
      missing_share = mean(!ok),
      mean = if (any(ok)) mean(x, na.rm = TRUE) else NA_real_,
      sd = if (sum(ok) > 1) sd(x, na.rm = TRUE) else NA_real_,
      min = if (any(ok)) min(x, na.rm = TRUE) else NA_real_,
      p01 = qs[1], p05 = qs[2], p25 = qs[3], p50 = qs[4],
      p75 = qs[5], p95 = qs[6], p99 = qs[7],
      max = if (any(ok)) max(x, na.rm = TRUE) else NA_real_,
      stringsAsFactors = FALSE
    )
  })
  if (length(rows) == 0) data.frame() else do.call(rbind, rows)
}

analysis_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
analysis <- read_csv(
  analysis_file,
  colClasses = c(
    nhCode = "character",
    xzc12 = "character",
    xzc12_for_merge_final = "character",
    xzc12_for_merge = "character"
  )
)

## Drop previously appended fields to make reruns idempotent.
fields_to_refresh <- c(
  "fe01_01", "fe01_02", "fe01_03", "fe01_04",
  "fe03_01", "fe03_02", "fe03_03", "fe03_04",
  "juli", "shuzi05", "shuzi06",
  "retail_thickness_survey", "market_remoteness_survey",
  "fresh_market_friction_survey", "market_friction_survey",
  "market_friction_survey_components", "retail_thickness_survey_components",
  "market_remoteness_survey_components", "fresh_market_friction_survey_components",
  "poi_market_capacity_lag1", "poi_fresh_market_capacity_lag1",
  "poi_market_friction_lag1", "poi_fresh_market_friction_lag1",
  "combined_market_friction", "combined_market_friction_components",
  "gaez_wheat_si_10km", "gaez_maize_si_10km", "gaez_rice_si_10km",
  "gaez_soybean_si_10km", "gaez_wheat_ay_10km", "gaez_maize_ay_10km",
  "gaez_rice_ay_10km", "gaez_soybean_ay_10km",
  "gaez_overall_si_10km", "gaez_staple_si_10km",
  "gaez_soil_terrain_constraint_10km",
  "iv_terrain_barrier_town_gee_2km", "iv_terrain_barrier_town_gee_1km",
  "iv_terrain_barrier_town_gee_5km", "iv_terrain_barrier_county_gee_2km",
  "town_corridor_slope_mean_gee_2km", "town_corridor_tri_mean_gee_2km",
  "town_corridor_water_occurrence_mean_gee_2km", "town_straight_dist_km_gee_2km",
  "iv_early_ntl_peak_dist_9294", "dist_to_ntl_peak_km_9294",
  "county_ntl9294_mean", "county_ntl9294_sum", "county_ntl9294_max",
  "ntl9294_mean_20km", "ntl9294_max_20km", "ntl9294_sum_20km",
  "text_group", "text_window", "text_n_years_available",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_broad_5yr_sum",
  "attention_z_strict_5yr_sum", "attention_z_5yr_sum",
  "county_text_match"
)
analysis <- analysis[, setdiff(names(analysis), fields_to_refresh), drop = FALSE]

## Village survey market indices -------------------------------------------

vl <- read_csv(
  path("raw_data", "村表数据_已清洗.csv"),
  colClasses = c(xzcCode = "character", xzcCode_clean = "character")
)
village_vars <- c(
  "xzcCode_clean", "data_year",
  "fe01_01", "fe01_02", "fe01_03", "fe01_04",
  "fe03_01", "fe03_02", "fe03_03", "fe03_04",
  "juli", "shuzi05", "shuzi06"
)
village_market <- vl[, intersect(village_vars, names(vl)), drop = FALSE]
names(village_market)[names(village_market) == "xzcCode_clean"] <- "xzc12_for_merge_final"

count_vars <- c("fe01_01", "fe01_02", "fe01_03", "fe01_04")
dist_vars <- c("fe03_01", "fe03_02", "fe03_03", "fe03_04", "juli")
for (v in intersect(c(count_vars, dist_vars, "shuzi05", "shuzi06"), names(village_market))) {
  x <- to_num(village_market[[v]])
  x[x < 0] <- NA_real_
  village_market[[v]] <- x
}

z_counts <- as.data.frame(lapply(village_market[, intersect(count_vars, names(village_market)), drop = FALSE], zscore), check.names = FALSE)
z_dists <- as.data.frame(lapply(village_market[, intersect(dist_vars, names(village_market)), drop = FALSE], zscore), check.names = FALSE)
village_market$retail_thickness_survey <- row_mean_min(z_counts, min_nonmissing = 2)
village_market$retail_thickness_survey_components <- rowSums(!is.na(z_counts))
village_market$market_remoteness_survey <- row_mean_min(z_dists, min_nonmissing = 2)
village_market$market_remoteness_survey_components <- rowSums(!is.na(z_dists))

fresh_components <- data.frame(
  fe01_03_neg = -zscore(village_market$fe01_03),
  fe01_04_neg = -zscore(village_market$fe01_04),
  fe03_03 = zscore(village_market$fe03_03),
  fe03_04 = zscore(village_market$fe03_04),
  check.names = FALSE
)
village_market$fresh_market_friction_survey <- row_mean_min(fresh_components, min_nonmissing = 2)
village_market$fresh_market_friction_survey_components <- rowSums(!is.na(fresh_components))

market_components <- cbind(-z_counts, z_dists)
village_market$market_friction_survey <- row_mean_min(market_components, min_nonmissing = 3)
village_market$market_friction_survey_components <- rowSums(!is.na(market_components))

analysis <- merge(
  analysis,
  village_market,
  by = c("xzc12_for_merge_final", "data_year"),
  all.x = TRUE,
  sort = FALSE
)

## POI friction aliases -----------------------------------------------------

analysis$poi_market_capacity_lag1 <- to_num(analysis$poi_market_capacity_5km)
analysis$poi_fresh_market_capacity_lag1 <- to_num(analysis$poi_fresh_market_capacity_5km)
analysis$poi_market_friction_lag1 <- -zscore(log1p(analysis$poi_market_capacity_lag1))
analysis$poi_fresh_market_friction_lag1 <- -zscore(log1p(analysis$poi_fresh_market_capacity_lag1))

combined_components <- data.frame(
  survey = zscore(analysis$market_friction_survey),
  poi = zscore(analysis$poi_market_friction_lag1),
  check.names = FALSE
)
analysis$combined_market_friction <- row_mean_min(combined_components, min_nonmissing = 1)
analysis$combined_market_friction_components <- rowSums(!is.na(combined_components))

## External village controls and IVs ---------------------------------------

merge_xzc12 <- function(base, external, vars) {
  external <- dedupe_by_key(external, "xzc12")
  keep <- intersect(c("xzc12", vars), names(external))
  external <- external[, keep, drop = FALSE]
  names(external)[names(external) == "xzc12"] <- "xzc12_for_merge_final"
  merge(base, external, by = "xzc12_for_merge_final", all.x = TRUE, sort = FALSE)
}

gaez <- read_csv(path("raw_data", "paper1_iv_controls", "gaez_theme4_10km_village.csv"), colClasses = c(xzc12 = "character"))
gaez_vars <- c(
  "gaez_wheat_si_10km", "gaez_maize_si_10km", "gaez_rice_si_10km", "gaez_soybean_si_10km",
  "gaez_wheat_ay_10km", "gaez_maize_ay_10km", "gaez_rice_ay_10km", "gaez_soybean_ay_10km",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km"
)
analysis <- merge_xzc12(analysis, gaez, gaez_vars)

terrain <- read_csv(path("raw_data", "paper1_iv_controls", "paper1_village_topography_iv_all_corridors.csv"), colClasses = c(xzc12 = "character"))
terrain_vars <- c(
  "iv_terrain_barrier_town_gee_2km", "iv_terrain_barrier_town_gee_1km",
  "iv_terrain_barrier_town_gee_5km", "iv_terrain_barrier_county_gee_2km",
  "town_corridor_slope_mean_gee_2km", "town_corridor_tri_mean_gee_2km",
  "town_corridor_water_occurrence_mean_gee_2km", "town_straight_dist_km_gee_2km"
)
analysis <- merge_xzc12(analysis, terrain, terrain_vars)

ntl <- read_csv(path("raw_data", "paper1_iv_controls", "paper1_village_early_ntl_peak_iv_9294.csv"), colClasses = c(xzc12 = "character"))
ntl_vars <- c(
  "iv_early_ntl_peak_dist_9294", "dist_to_ntl_peak_km_9294",
  "county_ntl9294_mean", "county_ntl9294_sum", "county_ntl9294_max",
  "ntl9294_mean_20km", "ntl9294_max_20km", "ntl9294_sum_20km"
)
analysis <- merge_xzc12(analysis, ntl, ntl_vars)

## County text indicators ---------------------------------------------------

food_safety <- read_csv(path("raw_data", "food_safety", "paper_8provinces_all_counties_5year_complete.csv"))
text_vars <- c(
  "province", "county", "group", "window", "n_years_available",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_broad_5yr_sum", "attention_z_strict_5yr_sum"
)
food_safety <- food_safety[, intersect(text_vars, names(food_safety)), drop = FALSE]
names(food_safety)[names(food_safety) == "province"] <- "provn_std"
names(food_safety)[names(food_safety) == "county"] <- "countyn_std"
names(food_safety)[names(food_safety) == "group"] <- "text_group"
names(food_safety)[names(food_safety) == "window"] <- "text_window"
names(food_safety)[names(food_safety) == "n_years_available"] <- "text_n_years_available"
food_safety$provn_std <- trim_text(food_safety$provn_std)
food_safety$countyn_std <- trim_text(food_safety$countyn_std)
food_safety <- food_safety[!duplicated(food_safety[, c("provn_std", "countyn_std")]), ]

analysis$provn_std <- trim_text(analysis$provn_std)
analysis$countyn_std <- trim_text(analysis$countyn_std)
analysis <- merge(
  analysis,
  food_safety,
  by = c("provn_std", "countyn_std"),
  all.x = TRUE,
  sort = FALSE
)
analysis$attention_z_5yr_sum <- analysis$attention_z_broad_5yr_sum
analysis$county_text_match <- as.integer(!is.na(analysis$risk_salience_z_5yr_sum))

## Ordering and output ------------------------------------------------------

food_category_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
analysis$food_category <- factor(analysis$food_category, levels = food_category_order)
analysis <- analysis[order(analysis$nhCode, analysis$food_category), ]
analysis$food_category <- as.character(analysis$food_category)

write_csv(analysis, analysis_file)
write_csv(analysis, path("data", "cleaned", "paper1_household_category_long.csv"))

## Diagnostics --------------------------------------------------------------

merge_summary <- data.frame(
  item = c(
    "rows",
    "households",
    "food_categories",
    "unique_household_category_keys",
    "duplicate_household_category_keys",
    "unique_villages_in_analysis",
    "rows_missing_village_survey_market_friction",
    "rows_missing_poi_market_friction",
    "rows_missing_combined_market_friction",
    "rows_missing_gaez_overall_si",
    "rows_missing_terrain_iv_main",
    "rows_missing_early_ntl_iv",
    "rows_missing_county_text",
    "rows_with_wrong_poi_year_rule"
  ),
  value = c(
    nrow(analysis),
    length(unique(analysis$nhCode)),
    length(unique(analysis$food_category)),
    nrow(unique(analysis[, c("nhCode", "food_category")])),
    sum(duplicated(analysis[, c("nhCode", "food_category")])),
    length(unique(analysis$xzc12_for_merge_final)),
    sum(is.na(analysis$market_friction_survey)),
    sum(is.na(analysis$poi_market_friction_lag1)),
    sum(is.na(analysis$combined_market_friction)),
    sum(is.na(analysis$gaez_overall_si_10km)),
    sum(is.na(analysis$iv_terrain_barrier_town_gee_2km)),
    sum(is.na(analysis$iv_early_ntl_peak_dist_9294)),
    sum(is.na(analysis$risk_salience_z_5yr_sum)),
    sum((analysis$data_year == 2023 & analysis$poi_year_assigned != 2022) |
          (analysis$data_year == 2024 & analysis$poi_year_assigned != 2023), na.rm = TRUE)
  ),
  stringsAsFactors = FALSE
)
write_csv(merge_summary, path("outputs", "tables", "market_external_merge_summary.csv"))

market_vars <- c(
  "retail_thickness_survey", "market_remoteness_survey",
  "fresh_market_friction_survey", "market_friction_survey",
  "poi_market_capacity_lag1", "poi_fresh_market_capacity_lag1",
  "poi_market_friction_lag1", "poi_fresh_market_friction_lag1",
  "combined_market_friction"
)
market_summary <- summarise_numeric(analysis, market_vars, "market_friction")
write_csv(market_summary, path("outputs", "tables", "market_friction_indices_summary.csv"))

table1_vars <- c(
  "production_participation", "selfprod_monthly_total", "log_selfprod_amount",
  "ihs_selfprod_amount", "self_suff_rate",
  "price_hedonic_imputed_w99_yuan_per_jin",
  "household_size_reconstructed", "child_share", "elderly_share", "female_share",
  "dependency_ratio", "num_children", "num_elderly", "num_adult_male", "num_adult_female",
  "agricultural_labor_days", "offfarm_labor_days", "total_labor_days",
  "total_sown_area", "household_assets_count_proxy", "household_head_age",
  "household_head_education", "market_friction_survey", "poi_market_friction_lag1",
  "combined_market_friction", "gaez_overall_si_10km", "gaez_staple_si_10km",
  "gaez_soil_terrain_constraint_10km", "iv_terrain_barrier_town_gee_2km",
  "iv_early_ntl_peak_dist_9294", "risk_salience_z_5yr_sum",
  "governance_capacity_z_5yr_sum", "trust_signal_z_5yr_sum", "attention_z_5yr_sum"
)
table1 <- summarise_numeric(analysis, table1_vars, "table1")
write_csv(table1, path("outputs", "tables", "table1_descriptive_statistics.csv"))

category_summary <- aggregate(
  cbind(production_participation, selfprod_monthly_total, cons_monthly_jin) ~ food_category + food_category_label,
  data = analysis,
  FUN = function(x) mean(x, na.rm = TRUE)
)
category_n <- aggregate(nhCode ~ food_category + food_category_label, data = analysis, FUN = length)
names(category_n)[3] <- "n_rows"
category_summary <- merge(category_n, category_summary, by = c("food_category", "food_category_label"), all.x = TRUE)
write_csv(category_summary, path("outputs", "tables", "category_outcome_summary_for_checks.csv"))

report <- c(
  "# Data Merge Log",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Completed Step",
  "",
  "- Constructed village-survey market-friction indices.",
  "- Constructed POI friction aliases and combined market-friction index.",
  "- Merged GAEZ controls, terrain-water IVs, early nighttime-light IVs, and county text indicators.",
  "- Wrote the updated long dataset to both analysis-ready and canonical cleaned paths.",
  "",
  "## Output Data",
  "",
  "- `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv`",
  "- `data/cleaned/paper1_household_category_long.csv`",
  "",
  "## Market-Friction Construction",
  "",
  "- `retail_thickness_survey`: row mean of standardized outlet counts, requiring at least 2 outlet-count components.",
  "- `market_remoteness_survey`: row mean of standardized distances, requiring at least 2 distance components.",
  "- `fresh_market_friction_survey`: row mean of -standardized fresh/wet/meat outlet counts and standardized fresh/wet/meat distances, requiring at least 2 components.",
  "- `market_friction_survey`: row mean of -standardized outlet counts and standardized distances, requiring at least 3 components.",
  "- `poi_market_friction_lag1`: negative standardized log(1 + POI market capacity).",
  "- `combined_market_friction`: row mean of standardized survey friction and standardized POI friction.",
  "",
  "## Notes",
  "",
  "- `attention_z_5yr_sum` is set to `attention_z_broad_5yr_sum` because the actual text file contains broad and strict variants, not a generic attention field.",
  "- No village fixed effects, village-year fixed effects, DID, or panel specifications are used."
)
writeLines(report, path("outputs", "logs", "data_merge_log.md"), useBytes = TRUE)

message("Market friction and external controls merged.")