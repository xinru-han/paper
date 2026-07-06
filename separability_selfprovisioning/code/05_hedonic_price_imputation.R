options(warn = 1)

root <- getwd()
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

to_num <- function(x) {
  if (is.numeric(x)) return(x)
  suppressWarnings(as.numeric(x))
}

positive_or_na <- function(x) {
  x <- to_num(x)
  x[is.na(x) | x <= 0] <- NA_real_
  x
}

winsor_by_group <- function(x, group, p_low = 0.01, p_high = 0.99) {
  out <- positive_or_na(x)
  for (g in unique(group)) {
    idx <- group == g
    vals <- out[idx]
    if (sum(!is.na(vals)) < 5) next
    lo <- as.numeric(quantile(vals, p_low, na.rm = TRUE, names = FALSE))
    hi <- as.numeric(quantile(vals, p_high, na.rm = TRUE, names = FALSE))
    out[idx] <- pmin(pmax(vals, lo), hi)
  }
  out
}

category_median_impute <- function(x, group) {
  out <- positive_or_na(x)
  global_med <- median(out, na.rm = TRUE)
  for (g in unique(group)) {
    idx <- group == g
    med <- median(out[idx], na.rm = TRUE)
    if (is.na(med)) med <- global_med
    out[idx & is.na(out)] <- med
  }
  out
}

prep_prediction_data <- function(data) {
  data$food_category_model <- factor(data$food_category)
  data$data_year_model <- factor(data$data_year)
  data$provn_model <- data$provn_std
  data$provn_model[is.na(data$provn_model) | data$provn_model == ""] <- data$provn[is.na(data$provn_model) | data$provn_model == ""]
  data$provn_model[is.na(data$provn_model) | data$provn_model == ""] <- "UNKNOWN_PROVINCE"
  data$countyn_model <- data$countyn_std
  data$countyn_model[is.na(data$countyn_model) | data$countyn_model == ""] <- data$countyn[is.na(data$countyn_model) | data$countyn_model == ""]
  data$countyn_model[is.na(data$countyn_model) | data$countyn_model == ""] <- "UNKNOWN_COUNTY"
  data$provn_model <- factor(data$provn_model)
  data$countyn_model <- factor(data$countyn_model)

  village_price <- positive_or_na(data$village_price_category_median)
  data$village_price_missing <- as.integer(is.na(village_price))
  village_price_w <- winsor_by_group(village_price, data$food_category, 0.01, 0.99)
  village_price_imp <- category_median_impute(village_price_w, data$food_category)
  data$log_village_price_imp <- log(village_price_imp)

  poi_vars <- c(
    "poi_market_capacity_5km", "poi_fresh_market_capacity_5km",
    "poi_supermarket_5km", "poi_wet_market_5km", "poi_fresh_food_5km",
    "poi_grocery_5km", "poi_meat_aquatic_5km"
  )
  data$poi_covariates_missing <- as.integer(!complete.cases(data[, intersect(poi_vars, names(data)), drop = FALSE]))
  for (v in intersect(poi_vars, names(data))) {
    x <- to_num(data[[v]])
    x[is.na(x) | x < 0] <- 0
    data[[paste0("log1p_", v)]] <- log1p(x)
  }
  if ("poi_has_any_5km" %in% names(data)) {
    data$poi_has_any_5km_model <- to_num(data$poi_has_any_5km)
    data$poi_has_any_5km_model[is.na(data$poi_has_any_5km_model)] <- 0
  } else {
    data$poi_has_any_5km_model <- 0
  }
  data
}

eligible_for_model <- function(model, newdata) {
  ok <- rep(TRUE, nrow(newdata))
  for (nm in names(model$xlevels)) {
    if (nm %in% names(newdata)) {
      ok <- ok & as.character(newdata[[nm]]) %in% model$xlevels[[nm]]
    }
  }
  ok
}

safe_predict_price <- function(model, newdata) {
  out <- rep(NA_real_, nrow(newdata))
  ok <- eligible_for_model(model, newdata)
  if (any(ok)) {
    pred <- predict(model, newdata = newdata[ok, , drop = FALSE])
    out[ok] <- exp(pred)
  }
  out
}

fit_lm <- function(formula, data) {
  lm(formula, data = data, na.action = na.exclude)
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

price_obs <- positive_or_na(analysis$price_recalc_spend_sum_over_purchase_qty_sum)
price_fit <- winsor_by_group(price_obs, analysis$food_category, 0.01, 0.99)
analysis$price_hedonic_observed_fit_yuan_per_jin <- price_fit

model_data <- prep_prediction_data(analysis)
model_data$log_price_fit <- log(price_fit)
train <- model_data[!is.na(model_data$log_price_fit), ]

base_covariates <- paste(
  c(
    "food_category_model",
    "data_year_model",
    "village_price_missing",
    "log_village_price_imp",
    "poi_covariates_missing",
    "poi_has_any_5km_model",
    "log1p_poi_market_capacity_5km",
    "log1p_poi_fresh_market_capacity_5km",
    "log1p_poi_supermarket_5km",
    "log1p_poi_wet_market_5km",
    "log1p_poi_fresh_food_5km",
    "log1p_poi_grocery_5km",
    "log1p_poi_meat_aquatic_5km"
  ),
  collapse = " + "
)

model_county <- fit_lm(as.formula(paste("log_price_fit ~", base_covariates, "+ countyn_model")), train)
model_province <- fit_lm(as.formula(paste("log_price_fit ~", base_covariates, "+ provn_model")), train)
model_category_year <- fit_lm(log_price_fit ~ food_category_model + data_year_model, train)

pred_county <- safe_predict_price(model_county, model_data)
pred_province <- safe_predict_price(model_province, model_data)
pred_category_year <- safe_predict_price(model_category_year, model_data)
category_median_price <- category_median_impute(price_fit, analysis$food_category)

hedonic_pred <- pred_county
pred_tier <- ifelse(!is.na(pred_county), "hedonic_county", NA_character_)
idx <- is.na(hedonic_pred) & !is.na(pred_province)
hedonic_pred[idx] <- pred_province[idx]
pred_tier[idx] <- "hedonic_province"
idx <- is.na(hedonic_pred) & !is.na(pred_category_year)
hedonic_pred[idx] <- pred_category_year[idx]
pred_tier[idx] <- "hedonic_category_year"
idx <- is.na(hedonic_pred)
hedonic_pred[idx] <- category_median_price[idx]
pred_tier[idx] <- "category_median_fallback"

analysis$price_hedonic_predicted_yuan_per_jin <- hedonic_pred
analysis$price_hedonic_prediction_tier <- pred_tier
analysis$price_hedonic_imputed_yuan_per_jin <- ifelse(!is.na(price_obs), price_obs, hedonic_pred)
analysis$price_hedonic_imputed_w99_yuan_per_jin <- winsor_by_group(
  analysis$price_hedonic_imputed_yuan_per_jin,
  analysis$food_category,
  0.01,
  0.99
)
analysis$price_hedonic_source <- ifelse(
  !is.na(price_obs),
  "observed_household_recalc",
  pred_tier
)

diagnostics <- data.frame(
  model = c("county", "province", "category_year"),
  n_train = c(nrow(model_county$model), nrow(model_province$model), nrow(model_category_year$model)),
  r_squared = c(summary(model_county)$r.squared, summary(model_province)$r.squared, summary(model_category_year)$r.squared),
  adj_r_squared = c(summary(model_county)$adj.r.squared, summary(model_province)$adj.r.squared, summary(model_category_year)$adj.r.squared),
  rmse_log_in_sample = c(
    sqrt(mean(resid(model_county)^2, na.rm = TRUE)),
    sqrt(mean(resid(model_province)^2, na.rm = TRUE)),
    sqrt(mean(resid(model_category_year)^2, na.rm = TRUE))
  ),
  stringsAsFactors = FALSE
)
write_csv(diagnostics, path("outputs", "tables", "hedonic_price_model_diagnostics.csv"))

summary_by_category <- do.call(rbind, lapply(split(analysis, analysis$food_category), function(d) {
  data.frame(
    food_category = d$food_category[1],
    food_category_label = d$food_category_label[1],
    n = nrow(d),
    n_observed_household_recalc = sum(d$price_hedonic_source == "observed_household_recalc", na.rm = TRUE),
    n_hedonic_imputed = sum(d$price_hedonic_source != "observed_household_recalc", na.rm = TRUE),
    n_county_tier = sum(d$price_hedonic_source == "hedonic_county", na.rm = TRUE),
    n_province_tier = sum(d$price_hedonic_source == "hedonic_province", na.rm = TRUE),
    n_category_year_tier = sum(d$price_hedonic_source == "hedonic_category_year", na.rm = TRUE),
    n_category_median_fallback = sum(d$price_hedonic_source == "category_median_fallback", na.rm = TRUE),
    observed_mean = mean(d$price_recalc_spend_sum_over_purchase_qty_sum, na.rm = TRUE),
    hedonic_imputed_mean = mean(d$price_hedonic_imputed_yuan_per_jin, na.rm = TRUE),
    hedonic_imputed_w99_mean = mean(d$price_hedonic_imputed_w99_yuan_per_jin, na.rm = TRUE),
    hedonic_imputed_p50 = median(d$price_hedonic_imputed_yuan_per_jin, na.rm = TRUE),
    hedonic_imputed_p99 = as.numeric(quantile(d$price_hedonic_imputed_yuan_per_jin, 0.99, na.rm = TRUE, names = FALSE)),
    hedonic_imputed_max = max(d$price_hedonic_imputed_yuan_per_jin, na.rm = TRUE),
    stringsAsFactors = FALSE
  )
}))
summary_by_category <- summary_by_category[match(unique(analysis$food_category), summary_by_category$food_category), ]
write_csv(summary_by_category, path("outputs", "tables", "hedonic_price_imputation_summary_by_category.csv"))

source_summary <- as.data.frame(table(analysis$price_hedonic_source), stringsAsFactors = FALSE)
names(source_summary) <- c("price_hedonic_source", "n_rows")
source_summary$share <- source_summary$n_rows / nrow(analysis)
write_csv(source_summary, path("outputs", "tables", "hedonic_price_imputation_source_summary.csv"))

write_csv(analysis, analysis_file)

report <- c(
  "# Hedonic Price Imputation",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Outcome",
  "",
  "- Updated `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv` in place.",
  "- Observed price is `price_recalc_spend_sum_over_purchase_qty_sum`.",
  "- Fitting price is category-level P1/P99 winsorized observed household recalc price.",
  "- Dependent variable is log fitting price.",
  "",
  "## Imputation Hierarchy",
  "",
  "1. Keep observed household-recalculated price when available.",
  "2. Use county-level hedonic prediction for missing household price.",
  "3. Use province-level hedonic prediction when county-level prediction is unavailable.",
  "4. Use category-year hedonic prediction when province-level prediction is unavailable.",
  "5. Use category median fallback if all model predictions fail.",
  "",
  "## New Columns",
  "",
  "- `price_hedonic_observed_fit_yuan_per_jin`",
  "- `price_hedonic_predicted_yuan_per_jin`",
  "- `price_hedonic_prediction_tier`",
  "- `price_hedonic_imputed_yuan_per_jin`",
  "- `price_hedonic_imputed_w99_yuan_per_jin`",
  "- `price_hedonic_source`",
  "",
  "## Outputs",
  "",
  "- `outputs/tables/hedonic_price_model_diagnostics.csv`",
  "- `outputs/tables/hedonic_price_imputation_summary_by_category.csv`",
  "- `outputs/tables/hedonic_price_imputation_source_summary.csv`"
)
writeLines(report, path("outputs", "logs", "hedonic_price_imputation.md"), useBytes = TRUE)

message("Hedonic price imputation completed and appended to: ", analysis_file)