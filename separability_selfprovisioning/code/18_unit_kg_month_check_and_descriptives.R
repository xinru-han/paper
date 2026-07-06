options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "analysis_ready"), recursive = TRUE, showWarnings = FALSE)
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
  if (nrow(df) == 0) return("")
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

summarise_numeric <- function(data, vars, labels, units, module = "") {
  rows <- lapply(vars[vars %in% names(data)], function(v) {
    x <- to_num(data[[v]])
    ok <- !is.na(x) & is.finite(x)
    qs <- if (any(ok)) {
      as.numeric(quantile(x[ok], probs = c(.01, .05, .25, .5, .75, .95, .99), names = FALSE))
    } else {
      rep(NA_real_, 7)
    }
    data.frame(
      module = module,
      variable = v,
      label = labels[[v]],
      unit = units[[v]],
      n = sum(ok),
      missing = sum(!ok),
      missing_share = mean(!ok),
      zero = sum(x == 0, na.rm = TRUE),
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
      max_to_p99 = if (any(ok) && !is.na(qs[7]) && qs[7] != 0) max(x[ok]) / qs[7] else NA_real_,
      stringsAsFactors = FALSE
    )
  })
  out <- do.call(rbind, rows)
  rownames(out) <- NULL
  out
}

category_summary <- function(data) {
  cats <- unique(data[, c("food_category", "food_category_label")])
  cats <- cats[order(match(cats$food_category, c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo"))), ]
  rows <- lapply(seq_len(nrow(cats)), function(i) {
    d <- data[data$food_category == cats$food_category[i], ]
    q <- function(v, p) as.numeric(quantile(to_num(d[[v]]), p, na.rm = TRUE, names = FALSE))
    mn <- function(v) mean(to_num(d[[v]]), na.rm = TRUE)
    mx <- function(v) max(to_num(d[[v]]), na.rm = TRUE)
    data.frame(
      food_category = cats$food_category[i],
      food_category_label = cats$food_category_label[i],
      n = nrow(d),
      participation_rate = mn("production_participation"),
      mean_cons_kg_month = mn("cons_kg_month"),
      p99_cons_kg_month = q("cons_kg_month", .99),
      max_cons_kg_month = mx("cons_kg_month"),
      mean_selfprod_kg_month = mn("selfprod_kg_month"),
      p99_selfprod_kg_month = q("selfprod_kg_month", .99),
      max_selfprod_kg_month = mx("selfprod_kg_month"),
      mean_purchase_qty_kg_month = mn("purchase_qty_kg_month"),
      p99_purchase_qty_kg_month = q("purchase_qty_kg_month", .99),
      max_purchase_qty_kg_month = mx("purchase_qty_kg_month"),
      mean_price_hedonic_w99_yuan_per_kg = mn("price_hedonic_imputed_w99_yuan_per_kg"),
      p99_price_hedonic_w99_yuan_per_kg = q("price_hedonic_imputed_w99_yuan_per_kg", .99),
      max_price_hedonic_w99_yuan_per_kg = mx("price_hedonic_imputed_w99_yuan_per_kg"),
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

input_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
data <- read_csv(
  input_file,
  colClasses = c(
    nhCode = "character",
    xzc12 = "character",
    xzc12_for_merge_final = "character",
    xzc12_for_merge = "character"
  )
)

required_categories <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
unexpected_categories <- setdiff(unique(data$food_category), required_categories)

conversion_rows <- list()

add_quantity_kg <- function(data, from, to, label) {
  if (!from %in% names(data)) return(data)
  data[[to]] <- to_num(data[[from]]) * 0.5
  conversion_rows[[length(conversion_rows) + 1]] <<- data.frame(
    variable_original = from,
    variable_converted = to,
    original_unit = "jin/month",
    converted_unit = "kg/month",
    operation = "converted = original * 0.5",
    n = sum(!is.na(to_num(data[[from]]))),
    max_abs_check_error = max(abs(data[[to]] - to_num(data[[from]]) * 0.5), na.rm = TRUE),
    note = label,
    stringsAsFactors = FALSE
  )
  data
}

add_price_kg <- function(data, from, to = NULL, label = "") {
  if (!from %in% names(data)) return(data)
  if (is.null(to)) to <- sub("yuan_per_jin", "yuan_per_kg", from, fixed = TRUE)
  if (identical(to, from)) to <- paste0(from, "_yuan_per_kg")
  data[[to]] <- to_num(data[[from]]) * 2
  conversion_rows[[length(conversion_rows) + 1]] <<- data.frame(
    variable_original = from,
    variable_converted = to,
    original_unit = "yuan/jin",
    converted_unit = "yuan/kg",
    operation = "converted = original * 2",
    n = sum(!is.na(to_num(data[[from]]))),
    max_abs_check_error = max(abs(data[[to]] - to_num(data[[from]]) * 2), na.rm = TRUE),
    note = label,
    stringsAsFactors = FALSE
  )
  data
}

data <- add_quantity_kg(data, "cons_monthly_jin", "cons_kg_month", "monthly consumption quantity")
data <- add_quantity_kg(data, "selfprod_monthly_total", "selfprod_kg_month", "monthly self-produced/self-consumed quantity")
data <- add_quantity_kg(data, "purchase_qty_sum_jin", "purchase_qty_kg_month", "monthly purchased quantity")

data$log_selfprod_amount_original_jin_scale <- data$log_selfprod_amount
data$ihs_selfprod_amount_original_jin_scale <- data$ihs_selfprod_amount
data$log_selfprod_amount_kg_month <- log1p(pmax(to_num(data$selfprod_kg_month), 0))
data$ihs_selfprod_amount_kg_month <- asinh(pmax(to_num(data$selfprod_kg_month), 0))

price_vars_suffix <- grep("yuan_per_jin$", names(data), value = TRUE)
for (v in price_vars_suffix) {
  data <- add_price_kg(data, v)
}

price_vars_extra <- c(
  "price_recalc_spend_sum_over_purchase_qty_sum",
  "village_price_category_median",
  "price_mean_detail_total_spend_over_qty",
  "price_mean_detail_avg_each_purchase",
  "price_mean_raw_pjxfl"
)
for (v in price_vars_extra) {
  data <- add_price_kg(data, v, paste0(v, "_yuan_per_kg"))
}

kg_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long_kg_month.csv")
write_csv(data, kg_file)

conversion_audit <- do.call(rbind, conversion_rows)
conversion_audit$max_abs_check_error[is.infinite(conversion_audit$max_abs_check_error)] <- NA_real_
write_csv(conversion_audit, path("outputs", "tables", "paper1_unit_conversion_audit_kg_month.csv"))

labels <- c(
  production_participation = "Self-provisioning participation",
  cons_kg_month = "Monthly consumption",
  selfprod_kg_month = "Monthly self-produced consumption",
  purchase_qty_kg_month = "Monthly purchased quantity",
  self_suff_rate = "Self-sufficiency rate",
  log_selfprod_amount_kg_month = "log(1 + selfprod kg/month)",
  ihs_selfprod_amount_kg_month = "asinh(selfprod kg/month)",
  price_hedonic_imputed_w99_yuan_per_kg = "Main hedonic/winsorized unit value",
  price_preferred_household_recalc_w99_yuan_per_kg = "Observed household recalculated unit value, w99",
  village_price_category_median_yuan_per_kg = "Village category median unit value",
  spend_sum_yuan = "Monthly purchase spending",
  household_size_reconstructed = "Household size",
  num_children = "Number of children",
  num_elderly = "Number of elderly members",
  adult_members = "Adult members",
  child_share = "Child share",
  elderly_share = "Elderly share",
  female_share = "Female share",
  dependency_ratio = "Dependency ratio",
  agricultural_labor_days = "Agricultural labor days, household sum",
  offfarm_labor_days = "Off-farm labor days, household sum",
  total_labor_days = "Total labor days, household sum",
  agricultural_labor_days_per_adult = "Agricultural labor days per adult",
  offfarm_labor_days_per_adult = "Off-farm labor days per adult",
  total_labor_days_per_adult = "Total labor days per adult",
  agricultural_labor_days_working_age_16_64 = "Agricultural labor days, age 16-64 sum",
  offfarm_labor_days_working_age_16_64 = "Off-farm labor days, age 16-64 sum",
  total_labor_days_working_age_16_64 = "Total labor days, age 16-64 sum",
  agricultural_labor_days_head = "Agricultural labor days, household head",
  offfarm_labor_days_head = "Off-farm labor days, household head",
  total_labor_days_head = "Total labor days, household head",
  total_sown_area = "Total sown area, cleaned",
  total_sown_area_raw = "Total sown area, raw",
  total_sown_area_nonnegative = "Total sown area, nonnegative",
  total_sown_area_component_cap500 = "Total sown area after component cap",
  area_any_component_outlier = "Any crop-area component outlier",
  area_total_winsorized_flag = "Total area winsorized flag",
  log1p_total_income_w_w99 = "Log total income, winsorized",
  log1p_agri_business_income_w99 = "Log agricultural business income, winsorized",
  log1p_annual_expense_total_w99 = "Log annual expense, winsorized",
  market_friction_survey = "Survey market friction",
  poi_market_friction_lag1 = "POI market friction",
  combined_market_friction = "Combined market friction",
  poi_market_capacity_5km = "POI market capacity within 5km",
  poi_fresh_market_capacity_5km = "Fresh-market POI capacity within 5km",
  gaez_overall_si_10km = "GAEZ overall suitability",
  gaez_staple_si_10km = "GAEZ staple suitability",
  gaez_soil_terrain_constraint_10km = "GAEZ soil/terrain constraint",
  risk_salience_z_5yr_sum = "County food-safety risk salience",
  governance_capacity_z_5yr_sum = "County governance capacity signal",
  trust_signal_z_5yr_sum = "County trust signal",
  attention_z_5yr_sum = "County attention signal"
)
units <- c(
  production_participation = "0/1",
  cons_kg_month = "kg/month",
  selfprod_kg_month = "kg/month",
  purchase_qty_kg_month = "kg/month",
  self_suff_rate = "0-1",
  log_selfprod_amount_kg_month = "log kg/month",
  ihs_selfprod_amount_kg_month = "IHS kg/month",
  price_hedonic_imputed_w99_yuan_per_kg = "yuan/kg",
  price_preferred_household_recalc_w99_yuan_per_kg = "yuan/kg",
  village_price_category_median_yuan_per_kg = "yuan/kg",
  spend_sum_yuan = "yuan/month",
  household_size_reconstructed = "persons",
  num_children = "persons",
  num_elderly = "persons",
  adult_members = "persons",
  child_share = "share",
  elderly_share = "share",
  female_share = "share",
  dependency_ratio = "ratio",
  agricultural_labor_days = "days/year, household sum",
  offfarm_labor_days = "days/year, household sum",
  total_labor_days = "days/year, household sum",
  agricultural_labor_days_per_adult = "days/year/adult",
  offfarm_labor_days_per_adult = "days/year/adult",
  total_labor_days_per_adult = "days/year/adult",
  agricultural_labor_days_working_age_16_64 = "days/year, age 16-64 sum",
  offfarm_labor_days_working_age_16_64 = "days/year, age 16-64 sum",
  total_labor_days_working_age_16_64 = "days/year, age 16-64 sum",
  agricultural_labor_days_head = "days/year, household head",
  offfarm_labor_days_head = "days/year, household head",
  total_labor_days_head = "days/year, household head",
  total_sown_area = "mu",
  total_sown_area_raw = "mu",
  total_sown_area_nonnegative = "mu",
  total_sown_area_component_cap500 = "mu",
  area_any_component_outlier = "0/1",
  area_total_winsorized_flag = "0/1",
  log1p_total_income_w_w99 = "log yuan/year",
  log1p_agri_business_income_w99 = "log yuan/year",
  log1p_annual_expense_total_w99 = "log yuan/year",
  market_friction_survey = "z-score",
  poi_market_friction_lag1 = "z-score",
  combined_market_friction = "z-score",
  poi_market_capacity_5km = "count",
  poi_fresh_market_capacity_5km = "count",
  gaez_overall_si_10km = "index",
  gaez_staple_si_10km = "index",
  gaez_soil_terrain_constraint_10km = "index",
  risk_salience_z_5yr_sum = "z-score",
  governance_capacity_z_5yr_sum = "z-score",
  trust_signal_z_5yr_sum = "z-score",
  attention_z_5yr_sum = "z-score"
)

desc_vars <- names(labels)
desc <- summarise_numeric(data, desc_vars, labels, units, "kg_month_unit_checked")
desc$outlier_attention <- ifelse(
  !is.na(desc$max_to_p99) & desc$max_to_p99 >= 5,
  "max >= 5*p99; inspect top cases",
  ""
)
write_csv(desc, path("outputs", "tables", "paper1_key_variable_descriptives_kg_month.csv"))

cat_desc <- category_summary(data)
write_csv(cat_desc, path("outputs", "tables", "paper1_category_outcome_descriptives_kg_month.csv"))

extreme_vars <- c(
  "cons_kg_month",
  "selfprod_kg_month",
  "purchase_qty_kg_month",
  "price_hedonic_imputed_w99_yuan_per_kg",
  "price_preferred_household_recalc_w99_yuan_per_kg",
  "village_price_category_median_yuan_per_kg",
  "spend_sum_yuan",
  "total_sown_area",
  "total_labor_days",
  "total_labor_days_per_adult"
)
extremes <- top_extremes(data, extreme_vars, 10)
write_csv(extremes, path("outputs", "tables", "paper1_top_extreme_values_kg_month.csv"))

unit_checks <- data.frame(
  check = c(
    "unexpected food categories outside eight-category analysis set",
    "quantity kg/month conversion records",
    "price yuan/kg conversion records",
    "rows with missing main hedonic price yuan/kg",
    "rows with old jin-based log retained for audit",
    "rows with kg-based log/IHS recomputed"
  ),
  value = c(
    if (length(unexpected_categories) == 0) "none" else paste(unexpected_categories, collapse = "; "),
    sum(conversion_audit$converted_unit == "kg/month"),
    sum(conversion_audit$converted_unit == "yuan/kg"),
    sum(is.na(data$price_hedonic_imputed_w99_yuan_per_kg)),
    sum(!is.na(data$log_selfprod_amount_original_jin_scale)),
    sum(!is.na(data$log_selfprod_amount_kg_month) & !is.na(data$ihs_selfprod_amount_kg_month))
  ),
  stringsAsFactors = FALSE
)
write_csv(unit_checks, path("outputs", "tables", "paper1_unit_checks_kg_month.csv"))

report_lines <- c(
  "# Paper 1 Unit Conversion and Descriptive Check",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Files",
  "",
  paste0("- Unit-checked data: `", kg_file, "`"),
  "- Conversion audit: `outputs/tables/paper1_unit_conversion_audit_kg_month.csv`",
  "- Key variable descriptives: `outputs/tables/paper1_key_variable_descriptives_kg_month.csv`",
  "- Category outcome descriptives: `outputs/tables/paper1_category_outcome_descriptives_kg_month.csv`",
  "- Top extreme values: `outputs/tables/paper1_top_extreme_values_kg_month.csv`",
  "",
  "## Unit Rule",
  "",
  "- Quantities originally labelled jin/month are converted to kg/month using kg = jin * 0.5.",
  "- Unit values originally labelled yuan/jin are converted to yuan/kg using yuan/kg = yuan/jin * 2.",
  "- `log_selfprod_amount_kg_month` and `ihs_selfprod_amount_kg_month` are recomputed from `selfprod_kg_month`.",
  "- Original jin-scale log/IHS columns are retained as `*_original_jin_scale` for audit.",
  "",
  "## Unit Checks",
  "",
  md_table(unit_checks, 3),
  "",
  "## Category-Level Food Outcome Descriptives",
  "",
  md_table(cat_desc, 3),
  "",
  "## Key Variable Descriptives",
  "",
  md_table(desc, 3),
  "",
  "## Variables Flagged by Max-to-P99 Ratio",
  "",
  md_table(desc[desc$outlier_attention != "", c("variable", "unit", "n", "p99", "max", "max_to_p99", "outlier_attention")], 3)
)
writeLines(report_lines, path("outputs", "reports", "paper1_unit_kg_month_descriptive_check.md"), useBytes = TRUE)

log_lines <- c(
  "# Unit kg/month Check",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  paste0("- Input: `", input_file, "`."),
  paste0("- Output: `", kg_file, "`."),
  "- Quantities converted from jin/month to kg/month.",
  "- Unit values converted from yuan/jin to yuan/kg.",
  "- Descriptive tables and top-extreme table were written for human review."
)
writeLines(log_lines, path("outputs", "logs", "unit_kg_month_check.md"), useBytes = TRUE)

message("Unit conversion and descriptive check completed.")