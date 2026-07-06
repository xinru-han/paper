options(warn = 1)

root <- getwd()
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

assert_unique <- function(data, keys, name) {
  dup <- duplicated(data[, keys, drop = FALSE])
  if (any(dup)) {
    stop(sprintf("%s has duplicated keys: %s", name, paste(keys, collapse = "+")))
  }
}

food_category_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")

hh_der <- read_csv(
  path("data", "cleaned", "household_derived_analysis_variables.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character")
)
food_long <- read_csv(
  path("data", "cleaned", "paper1_household_category_variable_audit_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character")
)
price_long <- read_csv(
  path("data", "cleaned", "household_category_price_reconstruction_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character")
)
hh_geo <- read_csv(
  path("data", "cleaned", "household_geography_clean.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge = "character")
)
poi <- read_csv(
  path("data", "cleaned", "poi_5km_village_counts_filled.csv"),
  colClasses = c(xzc12 = "character")
)
village_price <- read_csv(
  path("data", "cleaned", "village_category_price_candidates.csv"),
  colClasses = c(xzc12 = "character")
)

food_long <- food_long[food_long$food_category %in% food_category_order, ]
food_long$food_category <- factor(food_long$food_category, levels = food_category_order)
food_long <- food_long[order(food_long$nhCode, food_long$food_category), ]
food_long$food_category <- as.character(food_long$food_category)

assert_unique(hh_der, "nhCode", "household_derived_analysis_variables")
assert_unique(food_long, c("nhCode", "food_category"), "paper1_household_category_variable_audit_long")
assert_unique(price_long, c("nhCode", "food_category"), "household_category_price_reconstruction_long")
assert_unique(hh_geo, "nhCode", "household_geography_clean")
assert_unique(poi, "xzc12", "poi_5km_village_counts_filled")

price_keep <- c(
  "nhCode", "food_category",
  "price_recalc_spend_sum_over_purchase_qty_sum",
  "price_mean_detail_total_spend_over_qty",
  "price_mean_detail_avg_each_purchase",
  "price_mean_raw_pjxfl",
  "spend_sum_yuan",
  "purchase_qty_sum_jin"
)
analysis <- merge(
  food_long,
  price_long[, intersect(price_keep, names(price_long)), drop = FALSE],
  by = c("nhCode", "food_category"),
  all.x = TRUE,
  sort = FALSE
)

hh_keep <- setdiff(names(hh_der), c("data_year", "provn", "countyn", "xzc12"))
analysis <- merge(
  analysis,
  hh_der[, hh_keep, drop = FALSE],
  by = "nhCode",
  all.x = TRUE,
  sort = FALSE
)

geo_keep <- c("nhCode", "provn_std", "countyn_std", "townn_std", "viln_std", "xzc12_for_merge", "match_status", "fallback_reason", "fallback_distance_km")
analysis <- merge(
  analysis,
  hh_geo[, intersect(geo_keep, names(hh_geo)), drop = FALSE],
  by = "nhCode",
  all.x = TRUE,
  sort = FALSE
)
analysis$xzc12_for_merge_final <- ifelse(
  is.na(analysis$xzc12_for_merge) | analysis$xzc12_for_merge == "",
  analysis$xzc12,
  analysis$xzc12_for_merge
)

poi_keep <- c("xzc12", grep("^poi_", names(poi), value = TRUE))
poi_for_merge <- poi[, intersect(poi_keep, names(poi)), drop = FALSE]
names(poi_for_merge)[names(poi_for_merge) == "xzc12"] <- "xzc12_for_merge_final"
analysis <- merge(
  analysis,
  poi_for_merge,
  by = "xzc12_for_merge_final",
  all.x = TRUE,
  sort = FALSE
)

village_price_rows <- do.call(rbind, lapply(food_category_order, function(cat) {
  v <- paste0("village_price_", cat, "_median")
  if (!v %in% names(village_price)) return(data.frame())
  data.frame(
    xzc12_for_merge_final = village_price$xzc12,
    data_year = village_price$data_year,
    food_category = cat,
    village_price_category_median = village_price[[v]],
    stringsAsFactors = FALSE
  )
}))
assert_unique(village_price_rows, c("xzc12_for_merge_final", "data_year", "food_category"), "village_category_price_candidates_long")
analysis <- merge(
  analysis,
  village_price_rows,
  by = c("xzc12_for_merge_final", "data_year", "food_category"),
  all.x = TRUE,
  sort = FALSE
)

analysis$price_preferred_household_recalc_yuan_per_jin <- analysis$price_recalc_spend_sum_over_purchase_qty_sum
analysis$price_preferred_household_recalc_w99_yuan_per_jin <- analysis$price_preferred_household_recalc_yuan_per_jin
for (cat in food_category_order) {
  idx <- analysis$food_category == cat
  x <- analysis$price_preferred_household_recalc_yuan_per_jin[idx]
  if (any(!is.na(x))) {
    cutoff <- as.numeric(quantile(x, 0.99, na.rm = TRUE, names = FALSE))
    analysis$price_preferred_household_recalc_w99_yuan_per_jin[idx] <- pmin(x, cutoff)
  }
}
analysis$price_source_preferred <- ifelse(
  !is.na(analysis$price_preferred_household_recalc_yuan_per_jin),
  "household_recalc_spend_over_qty",
  ifelse(!is.na(analysis$village_price_category_median), "village_category_median", NA_character_)
)

analysis$food_category <- factor(analysis$food_category, levels = food_category_order)
analysis <- analysis[order(analysis$nhCode, analysis$food_category), ]
analysis$food_category <- as.character(analysis$food_category)

front_cols <- c(
  "nhCode", "data_year", "provn", "countyn", "xzc12", "xzc12_for_merge_final",
  "provn_std", "countyn_std", "townn_std", "viln_std", "match_status",
  "food_category", "food_category_label",
  "cons_monthly_jin", "selfprod_monthly_total", "production_participation",
  "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate",
  "price_recalc_spend_sum_over_purchase_qty_sum",
  "price_preferred_household_recalc_w99_yuan_per_jin",
  "price_wavg_yuan_per_jin", "price_wavg_yuan_per_jin_w99",
  "village_price_category_median", "price_source_preferred"
)
analysis <- analysis[, c(intersect(front_cols, names(analysis)), setdiff(names(analysis), front_cols)), drop = FALSE]

out_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
write_csv(analysis, out_file)

summary <- data.frame(
  metric = c(
    "n_rows",
    "n_households",
    "n_food_categories",
    "n_duplicate_household_category_rows",
    "contains_tiaoliao_tang_cha",
    "n_missing_household_recalc_price",
    "n_missing_village_category_price",
    "n_missing_poi_market_capacity"
  ),
  value = c(
    nrow(analysis),
    length(unique(analysis$nhCode)),
    length(unique(analysis$food_category)),
    sum(duplicated(analysis[, c("nhCode", "food_category")])),
    any(analysis$food_category %in% c("tiaoliao", "tang", "cha")),
    sum(is.na(analysis$price_recalc_spend_sum_over_purchase_qty_sum)),
    sum(is.na(analysis$village_price_category_median)),
    if ("poi_market_capacity_5km" %in% names(analysis)) sum(is.na(analysis$poi_market_capacity_5km)) else NA_integer_
  ),
  stringsAsFactors = FALSE
)
write_csv(summary, path("outputs", "tables", "paper1_reprocessed_analysis_ready_export_summary.csv"))

report <- c(
  "# Paper 1 Reprocessed Analysis-Ready Export",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Output",
  "",
  "- `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv`",
  "",
  "## Unit of Observation",
  "",
  "- Household by food category.",
  "- Food categories retained: zhushi, doulei, roulei, danlei, nailei, youzhi, shucai, shuiguo.",
  "",
  "## Included Reprocessed Variables",
  "",
  "- Household composition and labor variables without household-level 365-day capping.",
  "- Cleaned total sown area and area anomaly flags.",
  "- Food-category outcomes for the 8 retained categories.",
  "- Existing positive prices and reconstructed household prices using detail spend divided by purchase quantity.",
  "- Village category price candidates and POI 5km market-access variables."
)
writeLines(report, path("outputs", "logs", "paper1_reprocessed_analysis_ready_export.md"), useBytes = TRUE)

message("Export completed: ", out_file)