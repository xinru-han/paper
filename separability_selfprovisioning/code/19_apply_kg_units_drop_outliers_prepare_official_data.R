options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "analysis_ready"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "data", "cleaned"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "data", "backups"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
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

fmt <- function(x, digits = 3) {
  ifelse(is.na(x), "", formatC(x, format = "f", digits = digits, big.mark = ","))
}

md_table <- function(df, digits = 3) {
  if (is.null(df) || nrow(df) == 0) return("")
  out <- df
  for (nm in names(out)) {
    if (is.numeric(out[[nm]])) out[[nm]] <- fmt(out[[nm]], digits)
  }
  cols <- names(out)
  lines <- c(
    paste0("| ", paste(cols, collapse = " | "), " |"),
    paste0("|", paste(rep("---", length(cols)), collapse = "|"), "|")
  )
  for (i in seq_len(nrow(out))) {
    vals <- vapply(out[i, , drop = FALSE], function(x) as.character(x[1]), character(1))
    vals <- gsub("\\|", "\\\\|", vals)
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

get_original <- function(data, var, original_var = NULL) {
  if (is.null(original_var)) original_var <- paste0(var, "_original")
  if (original_var %in% names(data)) return(to_num(data[[original_var]]))
  to_num(data[[var]])
}

safe_quantile <- function(x, p, min_positive = 30) {
  x <- to_num(x)
  x <- x[is.finite(x)]
  if (sum(x > 0, na.rm = TRUE) < min_positive) return(NA_real_)
  as.numeric(quantile(x, p, na.rm = TRUE, names = FALSE))
}

threshold_by_category <- function(data, var, p = 0.995, min_positive = 30) {
  rows <- lapply(split(data, data$food_category), function(d) {
    x <- to_num(d[[var]])
    q <- safe_quantile(x, p, min_positive = min_positive)
    data.frame(
      food_category = d$food_category[1],
      food_category_label = d$food_category_label[1],
      variable = var,
      threshold_quantile = p,
      n_nonmissing = sum(!is.na(x)),
      n_positive = sum(x > 0, na.rm = TRUE),
      threshold = q,
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, rows)
}

flag_gt_threshold <- function(data, var, thresholds) {
  out <- rep(FALSE, nrow(data))
  if (!var %in% names(data)) return(out)
  for (i in seq_len(nrow(thresholds))) {
    cat <- thresholds$food_category[i]
    thr <- thresholds$threshold[i]
    if (!is.finite(thr)) next
    idx <- data$food_category == cat
    x <- to_num(data[[var]])
    out[idx] <- !is.na(x[idx]) & x[idx] > thr
  }
  out
}

summarise_numeric <- function(data, vars, module = "") {
  rows <- lapply(vars[vars %in% names(data)], function(v) {
    x <- to_num(data[[v]])
    ok <- !is.na(x) & is.finite(x)
    qs <- if (any(ok)) as.numeric(quantile(x[ok], c(.01, .05, .25, .5, .75, .95, .99), names = FALSE)) else rep(NA_real_, 7)
    data.frame(
      module = module,
      variable = v,
      n = sum(ok),
      missing = sum(!ok),
      missing_share = mean(!ok),
      mean = if (any(ok)) mean(x[ok]) else NA_real_,
      sd = if (sum(ok) > 1) sd(x[ok]) else NA_real_,
      min = if (any(ok)) min(x[ok]) else NA_real_,
      p01 = qs[1],
      p05 = qs[2],
      p25 = qs[3],
      median = qs[4],
      p75 = qs[5],
      p95 = qs[6],
      p99 = qs[7],
      max = if (any(ok)) max(x[ok]) else NA_real_,
      stringsAsFactors = FALSE
    )
  })
  out <- do.call(rbind, rows)
  rownames(out) <- NULL
  out
}

top_extremes <- function(data, vars, n_top = 10) {
  rows <- list()
  for (v in vars[vars %in% names(data)]) {
    x <- to_num(data[[v]])
    idx <- which(!is.na(x) & is.finite(x))
    if (length(idx) == 0) next
    idx <- idx[order(x[idx], decreasing = TRUE)]
    idx <- idx[seq_len(min(length(idx), n_top))]
    rows[[length(rows) + 1]] <- data.frame(
      variable = v,
      rank = seq_along(idx),
      value = x[idx],
      nhCode = data$nhCode[idx],
      data_year = data$data_year[idx],
      provn = data$provn[idx],
      countyn = data$countyn[idx],
      townn_std = data$townn_std[idx],
      viln_std = data$viln_std[idx],
      food_category = data$food_category[idx],
      food_category_label = data$food_category_label[idx],
      stringsAsFactors = FALSE
    )
  }
  out <- do.call(rbind, rows)
  rownames(out) <- NULL
  out
}

analysis_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
revised_file <- path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv")
canonical_file <- path("data", "cleaned", "paper1_household_category_long.csv")
kg_clean_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long_kg_month_outlier_cleaned.csv")

timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
for (f in c(analysis_file, revised_file, canonical_file)) {
  if (file.exists(f)) {
    backup <- path("data", "backups", paste0(timestamp, "_", basename(f)))
    file.copy(f, backup, overwrite = FALSE)
  }
}

data <- read_csv(
  analysis_file,
  colClasses = c(
    nhCode = "character",
    xzc12 = "character",
    xzc12_for_merge_final = "character",
    xzc12_for_merge = "character"
  )
)

required_categories <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
data <- data[data$food_category %in% required_categories, ]

data$cons_monthly_jin_original_jin <- get_original(data, "cons_monthly_jin", "cons_monthly_jin_original_jin")
data$selfprod_monthly_total_original_jin <- get_original(data, "selfprod_monthly_total", "selfprod_monthly_total_original_jin")
if ("purchase_qty_sum_jin" %in% names(data)) {
  data$purchase_qty_sum_jin_original_jin <- get_original(data, "purchase_qty_sum_jin", "purchase_qty_sum_jin_original_jin")
}

data$cons_kg_month <- data$cons_monthly_jin_original_jin * 0.5
data$selfprod_kg_month <- data$selfprod_monthly_total_original_jin * 0.5
if ("purchase_qty_sum_jin" %in% names(data)) data$purchase_qty_kg_month <- data$purchase_qty_sum_jin_original_jin * 0.5

price_suffix_vars <- grep("yuan_per_jin$", names(data), value = TRUE)
for (v in price_suffix_vars) {
  original_v <- paste0(v, "_original_yuan_per_jin")
  data[[original_v]] <- get_original(data, v, original_v)
  kg_v <- sub("yuan_per_jin$", "yuan_per_kg", v)
  data[[kg_v]] <- data[[original_v]] * 2
  data[[v]] <- data[[kg_v]]
}

price_extra_vars <- c(
  "price_recalc_spend_sum_over_purchase_qty_sum",
  "village_price_category_median",
  "price_mean_detail_total_spend_over_qty",
  "price_mean_detail_avg_each_purchase",
  "price_mean_raw_pjxfl"
)
for (v in intersect(price_extra_vars, names(data))) {
  original_v <- paste0(v, "_original_yuan_per_jin")
  data[[original_v]] <- get_original(data, v, original_v)
  kg_v <- paste0(v, "_yuan_per_kg")
  data[[kg_v]] <- data[[original_v]] * 2
  data[[v]] <- data[[kg_v]]
}

data$production_participation <- as.integer(!is.na(data$selfprod_kg_month) & data$selfprod_kg_month > 0)
data$log_selfprod_amount_original_jin_scale <- data$log_selfprod_amount
data$ihs_selfprod_amount_original_jin_scale <- data$ihs_selfprod_amount
data$log_selfprod_amount <- log1p(pmax(data$selfprod_kg_month, 0))
data$ihs_selfprod_amount <- asinh(pmax(data$selfprod_kg_month, 0))
data$log_selfprod_amount_kg_month <- data$log_selfprod_amount
data$ihs_selfprod_amount_kg_month <- data$ihs_selfprod_amount

data$cons_monthly_jin <- data$cons_kg_month
data$selfprod_monthly_total <- data$selfprod_kg_month
if ("purchase_qty_sum_jin" %in% names(data)) data$purchase_qty_sum_jin <- data$purchase_qty_kg_month

quantity_vars <- c("cons_kg_month", "selfprod_kg_month", "purchase_qty_kg_month")
quantity_thresholds <- do.call(rbind, lapply(quantity_vars[quantity_vars %in% names(data)], function(v) {
  threshold_by_category(data, v, p = 0.995, min_positive = 30)
}))
write_csv(quantity_thresholds, path("outputs", "tables", "paper1_outlier_thresholds_quantity_kg_month.csv"))

data$outlier_cons_kg_month <- flag_gt_threshold(data, "cons_kg_month", quantity_thresholds[quantity_thresholds$variable == "cons_kg_month", ])
data$outlier_selfprod_kg_month <- flag_gt_threshold(data, "selfprod_kg_month", quantity_thresholds[quantity_thresholds$variable == "selfprod_kg_month", ])
data$outlier_purchase_qty_kg_month <- flag_gt_threshold(data, "purchase_qty_kg_month", quantity_thresholds[quantity_thresholds$variable == "purchase_qty_kg_month", ])
data$outlier_quantity_any <- data$outlier_cons_kg_month | data$outlier_selfprod_kg_month | data$outlier_purchase_qty_kg_month

price_clean_threshold_vars <- c(
  "price_preferred_household_recalc_w99_yuan_per_kg",
  "price_hedonic_imputed_w99_yuan_per_kg",
  "village_price_category_median_yuan_per_kg",
  "spend_sum_yuan"
)
price_thresholds <- do.call(rbind, lapply(price_clean_threshold_vars[price_clean_threshold_vars %in% names(data)], function(v) {
  p <- if (v == "village_price_category_median_yuan_per_kg") 0.99 else 0.995
  threshold_by_category(data, v, p = p, min_positive = 30)
}))
write_csv(price_thresholds, path("outputs", "tables", "paper1_outlier_thresholds_price_spend.csv"))

data$outlier_observed_price_any <- flag_gt_threshold(
  data,
  "price_preferred_household_recalc_w99_yuan_per_kg",
  price_thresholds[price_thresholds$variable == "price_preferred_household_recalc_w99_yuan_per_kg", ]
)
data$outlier_hedonic_price_any <- flag_gt_threshold(
  data,
  "price_hedonic_imputed_w99_yuan_per_kg",
  price_thresholds[price_thresholds$variable == "price_hedonic_imputed_w99_yuan_per_kg", ]
)
data$outlier_spend_any <- flag_gt_threshold(
  data,
  "spend_sum_yuan",
  price_thresholds[price_thresholds$variable == "spend_sum_yuan", ]
)
data$outlier_village_price_any <- flag_gt_threshold(
  data,
  "village_price_category_median_yuan_per_kg",
  price_thresholds[price_thresholds$variable == "village_price_category_median_yuan_per_kg", ]
)

## Price anomalies are removed from price variables. Row exclusion is driven
## by food quantity anomalies so participation is not mechanically changed by
## purchase-price availability.
for (v in c(
  "price_preferred_household_recalc_w99_yuan_per_kg",
  "price_preferred_household_recalc_w99_yuan_per_jin",
  "price_preferred_household_recalc_yuan_per_kg",
  "price_preferred_household_recalc_yuan_per_jin"
)) {
  if (v %in% names(data)) data[[v]][data$outlier_observed_price_any] <- NA_real_
}
for (v in c("village_price_category_median_yuan_per_kg", "village_price_category_median")) {
  if (v %in% names(data)) data[[v]][data$outlier_village_price_any] <- NA_real_
}

if ("price_hedonic_imputed_w99_yuan_per_kg" %in% names(data)) {
  data$price_hedonic_imputed_w99_yuan_per_kg_clean <- data$price_hedonic_imputed_w99_yuan_per_kg
  data$price_hedonic_imputed_w99_yuan_per_kg_clean[data$outlier_hedonic_price_any] <- NA_real_
  for (cat in unique(data$food_category)) {
    idx <- data$food_category == cat
    med <- median(data$price_hedonic_imputed_w99_yuan_per_kg_clean[idx], na.rm = TRUE)
    if (is.na(med)) med <- median(data$price_hedonic_imputed_w99_yuan_per_kg_clean, na.rm = TRUE)
    data$price_hedonic_imputed_w99_yuan_per_kg_clean[idx & is.na(data$price_hedonic_imputed_w99_yuan_per_kg_clean)] <- med
  }
  data$price_hedonic_imputed_w99_yuan_per_kg <- data$price_hedonic_imputed_w99_yuan_per_kg_clean
  data$price_hedonic_imputed_w99_yuan_per_jin <- data$price_hedonic_imputed_w99_yuan_per_kg_clean
}

data$outlier_row_excluded_from_models <- data$outlier_quantity_any
clean <- data[!data$outlier_row_excluded_from_models, ]

clean$unit_system <- "kg_month_outlier_cleaned_v1"
clean$quantity_unit_for_models <- "kg/month/household"
clean$price_unit_for_models <- "yuan/kg"
clean$compatibility_note <- "Columns ending in _jin or _yuan_per_jin are retained for older scripts but now contain kg/month or yuan/kg values."

food_order <- required_categories
clean$food_category <- factor(clean$food_category, levels = food_order)
clean <- clean[order(clean$nhCode, clean$food_category), ]
clean$food_category <- as.character(clean$food_category)

write_csv(clean, kg_clean_file)
write_csv(clean, analysis_file)
write_csv(clean, canonical_file)
write_csv(clean, revised_file)

summary_rows <- data.frame(
  metric = c(
    "rows_before_outlier_exclusion",
    "rows_after_outlier_exclusion",
    "rows_dropped_for_quantity_outlier",
    "households_before",
    "households_after",
    "food_categories",
    "observed_price_cells_set_missing",
    "hedonic_price_cells_replaced_by_category_median",
    "village_price_cells_set_missing",
    "spend_outlier_rows_flagged_not_dropped"
  ),
  value = c(
    nrow(data),
    nrow(clean),
    sum(data$outlier_row_excluded_from_models),
    length(unique(data$nhCode)),
    length(unique(clean$nhCode)),
    length(unique(clean$food_category)),
    sum(data$outlier_observed_price_any, na.rm = TRUE),
    sum(data$outlier_hedonic_price_any, na.rm = TRUE),
    sum(data$outlier_village_price_any, na.rm = TRUE),
    sum(data$outlier_spend_any, na.rm = TRUE)
  ),
  stringsAsFactors = FALSE
)
write_csv(summary_rows, path("outputs", "tables", "paper1_kg_month_outlier_cleaning_summary.csv"))

drop_counts <- aggregate(
  cbind(outlier_cons_kg_month, outlier_selfprod_kg_month, outlier_purchase_qty_kg_month, outlier_quantity_any,
        outlier_observed_price_any, outlier_hedonic_price_any, outlier_village_price_any, outlier_spend_any) ~
    food_category + food_category_label,
  data = data,
  FUN = function(x) sum(x, na.rm = TRUE)
)
drop_counts$n_before <- as.integer(table(factor(data$food_category, levels = drop_counts$food_category)))
drop_counts$n_after <- as.integer(table(factor(clean$food_category, levels = drop_counts$food_category)))
write_csv(drop_counts, path("outputs", "tables", "paper1_kg_month_outlier_counts_by_category.csv"))

desc_vars <- c(
  "production_participation", "cons_kg_month", "selfprod_kg_month", "purchase_qty_kg_month",
  "self_suff_rate", "log_selfprod_amount", "ihs_selfprod_amount",
  "price_hedonic_imputed_w99_yuan_per_kg", "price_preferred_household_recalc_w99_yuan_per_kg",
  "village_price_category_median_yuan_per_kg", "spend_sum_yuan",
  "household_size_reconstructed", "child_share", "elderly_share", "female_share",
  "agricultural_labor_days", "offfarm_labor_days", "total_sown_area"
)
desc <- summarise_numeric(clean, desc_vars, "kg_month_outlier_cleaned")
write_csv(desc, path("outputs", "tables", "paper1_descriptives_after_kg_outlier_cleaning.csv"))

category_desc <- aggregate(
  cbind(production_participation, cons_kg_month, selfprod_kg_month, self_suff_rate, price_hedonic_imputed_w99_yuan_per_kg) ~
    food_category + food_category_label,
  data = clean,
  FUN = function(x) mean(x, na.rm = TRUE)
)
names(category_desc)[names(category_desc) == "production_participation"] <- "participation_rate"
names(category_desc)[names(category_desc) == "cons_kg_month"] <- "mean_cons_kg_month"
names(category_desc)[names(category_desc) == "selfprod_kg_month"] <- "mean_selfprod_kg_month"
names(category_desc)[names(category_desc) == "self_suff_rate"] <- "mean_self_suff_rate"
names(category_desc)[names(category_desc) == "price_hedonic_imputed_w99_yuan_per_kg"] <- "mean_price_yuan_per_kg"
write_csv(category_desc, path("outputs", "tables", "paper1_category_descriptives_after_kg_outlier_cleaning.csv"))

extremes_after <- top_extremes(clean, c(
  "cons_kg_month", "selfprod_kg_month", "purchase_qty_kg_month",
  "price_hedonic_imputed_w99_yuan_per_kg", "village_price_category_median_yuan_per_kg",
  "total_sown_area"
), n_top = 10)
write_csv(extremes_after, path("outputs", "tables", "paper1_top_extreme_values_after_kg_outlier_cleaning.csv"))

report_lines <- c(
  "# Paper 1 kg/month Unit Conversion and Outlier Exclusion",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Official Analysis Files Updated",
  "",
  "- `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv`",
  "- `data/cleaned/paper1_household_category_long.csv`",
  paste0("- `", kg_clean_file, "`"),
  "",
  "## Unit Rules",
  "",
  "- Household food quantities are converted from jin/month to kg/month using `kg = jin * 0.5`.",
  "- Unit values are converted from yuan/jin to yuan/kg using `yuan/kg = yuan/jin * 2`.",
  "- `log_selfprod_amount` and `ihs_selfprod_amount` are recomputed from `selfprod_kg_month`.",
  "- The quantities are household totals, so the model unit is kg/month/household, not kg/person/month.",
  "- Legacy column names ending in `_jin` or `_yuan_per_jin` are retained for old scripts, but their values are now kg/month or yuan/kg. Clearly named kg/yuan-per-kg columns are also present.",
  "",
  "## Outlier Rules",
  "",
  "- Food quantity rows are excluded from model data when `cons_kg_month`, `selfprod_kg_month`, or `purchase_qty_kg_month` exceeds the food-category P99.5 threshold, provided the category has at least 30 positive observations for that variable.",
  "- Observed household unit-value outliers are set to missing before observed-price-only robustness models.",
  "- Village median unit-value outliers are set to missing before village-price robustness models; this removes the 30,000 yuan/kg village-price records.",
  "- Hedonic main price outliers are replaced by the category median so the main price control remains complete.",
  "- Spending outliers are flagged for audit but not used to drop rows, because spending is not a model outcome.",
  "",
  "## Cleaning Summary",
  "",
  md_table(summary_rows, 3),
  "",
  "## Outlier Counts by Category",
  "",
  md_table(drop_counts, 3),
  "",
  "## Category Descriptives After Cleaning",
  "",
  md_table(category_desc, 3),
  "",
  "## Key Descriptives After Cleaning",
  "",
  md_table(desc, 3)
)
writeLines(report_lines, path("outputs", "reports", "paper1_kg_month_outlier_cleaning_report.md"), useBytes = TRUE)

log_lines <- c(
  "# kg/month Unit Conversion and Outlier Cleaning Log",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "- Converted official analysis data to kg/month/household and yuan/kg.",
  "- Excluded quantity outlier household-category rows using category-specific P99.5 thresholds.",
  "- Cleaned price outliers before robustness and main-price use.",
  "- Backups of prior analysis files were written to `data/backups/`.",
  "",
  "## Summary",
  "",
  paste0("- Rows before: ", summary_rows$value[summary_rows$metric == "rows_before_outlier_exclusion"]),
  paste0("- Rows after: ", summary_rows$value[summary_rows$metric == "rows_after_outlier_exclusion"]),
  paste0("- Rows dropped: ", summary_rows$value[summary_rows$metric == "rows_dropped_for_quantity_outlier"]),
  paste0("- Households before: ", summary_rows$value[summary_rows$metric == "households_before"]),
  paste0("- Households after: ", summary_rows$value[summary_rows$metric == "households_after"])
)
writeLines(log_lines, path("outputs", "logs", "kg_month_outlier_cleaning.md"), useBytes = TRUE)

message("kg/month unit conversion and outlier cleaning completed.")