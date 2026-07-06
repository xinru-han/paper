#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(jsonlite)
  library(yaml)
})

`%||%` <- function(x, y) if (is.null(x)) y else x

script_path <- tryCatch(normalizePath(sys.frame(1)$ofile), error = function(e) file.path(getwd(), "src", "20_build_high_frequency_price_and_panel.R"))
base <- normalizePath(file.path(dirname(script_path), ".."), mustWork = TRUE)
set.seed(20260626)

dir_create <- function(...) dir.create(file.path(...), recursive = TRUE, showWarnings = FALSE)
dir_create(base, "config")
dir_create(base, "data_derived")
dir_create(base, "outputs", "price_audit")
dir_create(base, "outputs", "internal_price")
dir_create(base, "outputs", "latent_price")
dir_create(base, "outputs", "validation")

raw_path <- file.path(base, "Data_merged.csv")
processed <- file.path(base, "processed")
if (!file.exists(raw_path)) stop("Missing Data_merged.csv")

groups <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉",
            "G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品","G10_坚果")
codes <- sprintf("G%02d", 1:10)
names(groups) <- codes

category_map <- data.table(
  Category = c("大米", "面粉", "挂面", "方便面", "食用油", "蔬菜", "水果", "猪肉",
               "禽类", "其他肉类", "牛肉", "羊肉", "海鲜类", "常温牛奶", "新鲜牛奶",
               "常温酸奶", "新鲜酸奶", "奶酪", "黄油", "成人奶粉", "坚果"),
  food_group10 = c("G01_主食", "G01_主食", "G01_主食", "G01_主食", "G02_食用油",
                   "G03_蔬菜", "G04_水果", "G05_猪肉", "G06_禽类及其他肉类",
                   "G06_禽类及其他肉类", "G07_牛羊肉", "G07_牛羊肉", "G08_海鲜",
                   "G09_乳制品", "G09_乳制品", "G09_乳制品", "G09_乳制品",
                   "G09_乳制品", "G09_乳制品", "G09_乳制品", "G10_坚果"),
  heterogeneity_tier = c("A","A","B","B","B","C","C","A","B","B","A","A","C","B","B","B","B","B","B","B","C")
)

family_size_mid <- c("家庭人口数1-2" = 1.5, "家庭人口数3" = 3, "家庭人口数4" = 4, "家庭人口数5+" = 5.5)
income_order <- c("<5000 RMB" = 1, "5001-7000 RMB" = 2, "7001-9000 RMB" = 3, "9001-12000 RMB" = 4, ">12000 RMB" = 5)

clean_income <- function(x) {
  x <- trimws(as.character(x))
  fifelse(x == ">12000RMB", ">12000 RMB", x)
}

mode_value <- function(x) {
  x <- as.character(x)
  x <- x[!is.na(x) & x != ""]
  if (!length(x)) return(NA_character_)
  tab <- sort(table(x), decreasing = TRUE)
  names(tab)[1]
}

weighted_mean_safe <- function(x, w) {
  ok <- is.finite(x) & is.finite(w) & w > 0
  if (!any(ok)) return(NA_real_)
  sum(x[ok] * w[ok]) / sum(w[ok])
}

safe_cor <- function(x, y) {
  ok <- is.finite(x) & is.finite(y)
  if (sum(ok) < 2) return(NA_real_)
  suppressWarnings(cor(x[ok], y[ok]))
}

message("Reading raw transactions with R/data.table...")
dt <- fread(raw_path, select = c("ID","Province","Family_Type","Family_Size","Family_Income","Date","Category","Spend","Volume","Price"),
            encoding = "UTF-8", showProgress = TRUE)
raw_rows <- nrow(dt)
dt[, ID := as.integer(ID)]
dt[, Date_chr := substr(as.character(Date), 1, 10)]
dt[, date_clean := as.IDate(gsub("/", "-", Date_chr))]
dt[, year := as.integer(format(date_clean, "%Y"))]
dt[, year_month := format(date_clean, "%Y-%m")]
dt[, Family_Income := clean_income(Family_Income)]
for (v in c("Spend","Volume","Price")) dt[, (v) := as.numeric(get(v))]
dt <- dt[year %in% 2020:2022]
dt <- merge(dt, category_map, by = "Category", all.x = TRUE)
dt <- dt[!is.na(food_group10)]
dt[, raw_uv := fifelse(is.finite(Spend) & is.finite(Volume) & Spend > 0 & Volume > 0, Spend / Volume, NA_real_)]
dt[, log_raw_uv := log(raw_uv)]
dt[, family_size_midpoint := unname(family_size_mid[Family_Size])]
dt[is.na(family_size_midpoint), family_size_midpoint := median(family_size_midpoint, na.rm = TRUE)]
dt[, spend_pos := fifelse(is.finite(Spend) & Spend > 0, Spend, 0)]

message("Writing price identity and volume audits...")
audit_sample <- dt[is.finite(Price) & is.finite(raw_uv) & raw_uv > 0 & Price > 0]
price_identity <- audit_sample[, {
  gap <- Price - raw_uv
  log_gap <- log(Price) - log(raw_uv)
  .(
    n_price_uv = .N,
    exact_match_share = mean(abs(gap) < 1e-10),
    rounded_2dp_match_share = mean(round(Price, 2) == round(raw_uv, 2)),
    median_abs_log_gap = median(abs(log_gap), na.rm = TRUE),
    p95_abs_log_gap = quantile(abs(log_gap), 0.95, na.rm = TRUE),
    median_price_to_uv_ratio = median(Price / raw_uv, na.rm = TRUE)
  )
}, by = .(Category, food_group10)]

volume_diag <- dt[, .(
  n_rows = .N,
  n_positive_spend = sum(spend_pos > 0),
  n_positive_volume = sum(is.finite(Volume) & Volume > 0),
  n_valid_uv = sum(is.finite(raw_uv) & raw_uv > 0),
  zero_volume_share_when_spend_positive = mean(spend_pos > 0 & (!is.finite(Volume) | Volume <= 0)),
  volume_p01 = quantile(Volume[is.finite(Volume) & Volume > 0], 0.01, na.rm = TRUE),
  volume_p50 = quantile(Volume[is.finite(Volume) & Volume > 0], 0.50, na.rm = TRUE),
  volume_p99 = quantile(Volume[is.finite(Volume) & Volume > 0], 0.99, na.rm = TRUE),
  log_uv_p01 = quantile(log_raw_uv[is.finite(log_raw_uv)], 0.01, na.rm = TRUE),
  log_uv_p50 = quantile(log_raw_uv[is.finite(log_raw_uv)], 0.50, na.rm = TRUE),
  log_uv_p99 = quantile(log_raw_uv[is.finite(log_raw_uv)], 0.99, na.rm = TRUE)
), by = .(Category, food_group10)]

price_tiers <- merge(category_map, price_identity, by = c("Category","food_group10"), all.x = TRUE)
price_tiers <- merge(price_tiers, volume_diag, by = c("Category","food_group10"), all.x = TRUE)
price_tiers[, price_quality_tier := fcase(
  heterogeneity_tier == "A" & n_valid_uv >= 1000 & zero_volume_share_when_spend_positive < 0.50, "A",
  heterogeneity_tier %in% c("A","B") & n_valid_uv >= 500 & zero_volume_share_when_spend_positive < 0.70, "B",
  heterogeneity_tier == "C" | zero_volume_share_when_spend_positive >= 0.70, "C",
  default = "D"
)]
price_tiers[, internal_uv_allowed_main := price_quality_tier %in% c("A","B")]

fwrite(price_identity, file.path(base, "outputs", "price_audit", "price_identity_audit_by_raw_category.csv"), bom = TRUE)
fwrite(volume_diag, file.path(base, "outputs", "price_audit", "volume_unit_diagnostics_by_raw_category.csv"), bom = TRUE)
fwrite(price_tiers[, .(Category, food_group10, price_quality_tier, heterogeneity_tier, internal_uv_allowed_main,
                       n_rows, n_valid_uv, zero_volume_share_when_spend_positive, median_abs_log_gap)],
       file.path(base, "outputs", "price_audit", "raw_category_price_eligibility.csv"), bom = TRUE)

yaml_tiers <- split(price_tiers[, .(food_group10, price_quality_tier, heterogeneity_tier, internal_uv_allowed_main)], price_tiers$Category)
write_yaml(yaml_tiers, file.path(base, "config", "category_price_tiers.yaml"))
write_yaml(list(
  positive_spend_required = TRUE,
  positive_volume_required = TRUE,
  raw_category_winsorization = list(lower_quantile = 0.005, upper_quantile = 0.995),
  min_obs_cell_month_raw_category = 80,
  min_households_for_fold_exclusion = 30,
  max_allowed_price_identity_gap_log = 0.02,
  random_seed = 20260626
), file.path(base, "config", "price_rules.yaml"))

message("Building household-month totals and folds...")
hm_spend <- dt[, .(
  total_food_spend_month = sum(spend_pos, na.rm = TRUE),
  total_food_transactions_month = .N
), by = .(ID, year_month)]
setorder(dt, ID, year_month, date_clean)
hm_attr <- dt[, .SD[.N], by = .(ID, year_month),
              .SDcols = c("Province","Family_Type","Family_Size","Family_Income","family_size_midpoint")]
hm_total <- merge(hm_spend, hm_attr, by = c("ID","year_month"), all.x = TRUE)
hm_total <- hm_total[total_food_spend_month > 0]
hm_total[, total_food_spend_pc_month := total_food_spend_month / family_size_midpoint]
hm_total[, log_total_food_spend_pc_month := log(pmax(total_food_spend_pc_month, 1e-8))]
hh_fold <- unique(hm_total[, .(ID)])
hh_fold[, fold := sample(rep(1:5, length.out = .N))]
hm_total <- merge(hm_total, hh_fold, by = "ID", all.x = TRUE)

message("Cleaning unit values and estimating internal fold-excluded prices...")
uv <- dt[is.finite(log_raw_uv) & spend_pos > 0 & Volume > 0]
uv <- merge(uv, hm_total[, .(ID, year_month, log_total_food_spend_pc_month, fold)], by = c("ID","year_month"), all.x = TRUE)
uv <- merge(uv, price_tiers[, .(Category, price_quality_tier, internal_uv_allowed_main)], by = "Category", all.x = TRUE)
uv <- uv[internal_uv_allowed_main == TRUE & !is.na(fold)]

uv[, q_low := quantile(log_raw_uv, 0.005, na.rm = TRUE), by = .(Category, Province, year)]
uv[, q_high := quantile(log_raw_uv, 0.995, na.rm = TRUE), by = .(Category, Province, year)]
uv[, log_uv_w := pmin(pmax(log_raw_uv, q_low), q_high)]

uv[, log_spend_pc_c := log_total_food_spend_pc_month - mean(log_total_food_spend_pc_month, na.rm = TRUE)]
uv[, quality_adj_log_uv := NA_real_]
uv[, spend_pc_bin := {
  r <- frank(log_total_food_spend_pc_month, ties.method = "average", na.last = "keep")
  pmax(1L, pmin(5L, as.integer(ceiling(5 * r / max(r, na.rm = TRUE)))))
}, by = Category]
uv[, cat_mean_log_uv := mean(log_uv_w, na.rm = TRUE), by = Category]
uv[, quality_cell_mean := mean(log_uv_w, na.rm = TRUE),
   by = .(Category, Family_Income, Family_Type, Family_Size, spend_pc_bin)]
uv[!is.finite(quality_cell_mean), quality_cell_mean := cat_mean_log_uv]
uv[, quality_adj_log_uv := log_uv_w - (quality_cell_mean - cat_mean_log_uv)]

cell_all <- uv[, .(
  internal_log_price_all = median(quality_adj_log_uv, na.rm = TRUE),
  n_internal_obs_all = .N,
  n_internal_households_all = uniqueN(ID),
  internal_log_price_sd_all = sd(quality_adj_log_uv, na.rm = TRUE)
), by = .(Province, year_month, Category, food_group10)]

fold_cells <- rbindlist(lapply(1:5, function(k) {
  z <- uv[fold != k, .(
    internal_log_price_cf = median(quality_adj_log_uv, na.rm = TRUE),
    n_internal_obs = .N,
    n_internal_households = uniqueN(ID),
    internal_log_price_sd = sd(quality_adj_log_uv, na.rm = TRUE)
  ), by = .(Province, year_month, Category, food_group10)]
  z[, fold := k]
  z
}), use.names = TRUE)
fold_cells <- merge(fold_cells, price_tiers[, .(Category, price_quality_tier)], by = "Category", all.x = TRUE)
fwrite(fold_cells, file.path(base, "outputs", "internal_price", "internal_price_cf_loo_month_raw_category.csv"), bom = TRUE)

message("Constructing fixed baseline category weights...")
baseline <- dt[year_month %in% c("2020-01","2020-02","2020-03") & spend_pos > 0,
               .(baseline_spend = sum(spend_pos)), by = .(food_group10, Category)]
baseline[, weight := baseline_spend / sum(baseline_spend), by = food_group10]
baseline <- merge(category_map[, .(Category, food_group10)], baseline, by = c("Category","food_group10"), all.x = TRUE)
baseline[is.na(weight), weight := 0]
baseline[, weight := { s <- sum(weight); if (is.finite(s) && s > 0) weight / s else rep(1 / .N, .N) }, by = food_group10]
fwrite(baseline, file.path(base, "outputs", "latent_price", "group_basket_weights.csv"), bom = TRUE)
write_yaml(split(baseline[, .(Category, weight)], baseline$food_group10), file.path(base, "config", "group_basket_weights.yaml"))

message("Combining internal and external prices into fold-specific latent monthly group prices...")
external_group <- fread(file.path(processed, "external_food_prices_group10_province_month_2020_2022.csv"), encoding = "UTF-8")
setnames(external_group, "province", "Province")
external_group <- external_group[, .(Province, year_month, food_group10,
                                     external_log_price = external_log_price_group10,
                                     external_price_index = external_price_index_group10_mean100,
                                     fill_levels, categories)]

fg <- merge(fold_cells, baseline[, .(Category, basket_weight = weight)], by = "Category", all.x = TRUE)
fg[, tier_weight := fcase(price_quality_tier == "A", 1.0, price_quality_tier == "B", 0.6, default = 0.0)]
internal_group <- fg[, .(
  internal_log_price_group = weighted_mean_safe(internal_log_price_cf, basket_weight * tier_weight),
  n_internal_obs_group = sum(n_internal_obs, na.rm = TRUE),
  n_internal_households_group = sum(n_internal_households, na.rm = TRUE),
  internal_log_price_sd_group = sd(internal_log_price_cf, na.rm = TRUE),
  n_internal_categories = sum(is.finite(internal_log_price_cf))
), by = .(fold, Province, year_month, food_group10)]

latent <- merge(CJ(fold = 1:5, Province = unique(external_group$Province), year_month = unique(external_group$year_month), food_group10 = unique(external_group$food_group10)),
                external_group, by = c("Province","year_month","food_group10"), all.x = TRUE)
latent <- merge(latent, internal_group, by = c("fold","Province","year_month","food_group10"), all.x = TRUE)
latent[, internal_available := is.finite(internal_log_price_group) & n_internal_households_group >= 30]
align <- latent[internal_available == TRUE & is.finite(external_log_price),
                .(align_gap = mean(external_log_price - internal_log_price_group, na.rm = TRUE)), by = food_group10]
latent <- merge(latent, align, by = "food_group10", all.x = TRUE)
latent[is.na(align_gap), align_gap := 0]
latent[, internal_log_price_aligned := internal_log_price_group + align_gap]
latent[, internal_weight := fifelse(internal_available, pmin(0.45, n_internal_households_group / (n_internal_households_group + 300)), 0)]
latent[, latent_log_price := fifelse(internal_weight > 0 & is.finite(internal_log_price_aligned), (1 - internal_weight) * external_log_price + internal_weight * internal_log_price_aligned, external_log_price)]
latent[, latent_price_se := sqrt((1 - internal_weight)^2 * 0.02^2 +
                                   internal_weight^2 * pmax((internal_log_price_sd_group / sqrt(pmax(n_internal_categories, 1)))^2, 0.01^2, na.rm = TRUE))]
latent[, price_version := "external_anchor_internal_cf_loo_r"]
fwrite(latent, file.path(base, "outputs", "latent_price", "latent_price_month_group10_fold.csv"), bom = TRUE)
fwrite(latent[, .(fold, Province, year_month, food_group10, latent_log_price, latent_price_se, internal_weight,
                  internal_available, n_internal_obs_group, n_internal_households_group, external_log_price, fill_levels, price_version)],
       file.path(base, "data_derived", "monthly_group_price_latent_r.csv"), bom = TRUE)

validation <- latent[, .(
  cells = .N,
  external_coverage = mean(is.finite(external_log_price)),
  internal_coverage = mean(internal_available),
  mean_internal_weight = mean(internal_weight, na.rm = TRUE),
  corr_internal_external = safe_cor(internal_log_price_aligned, external_log_price),
  proxy_share = mean(grepl("proxy", fill_levels %||% "", ignore.case = TRUE), na.rm = TRUE),
  price_pass = fifelse(mean(is.finite(external_log_price)) >= 0.95, "pass", "caution")
), by = food_group10]
fwrite(validation, file.path(base, "outputs", "validation", "price_validation_metrics.csv"), bom = TRUE)

message("Building household-month-group10 demand panel...")
grp <- dt[, .(
  spend_month = sum(spend_pos, na.rm = TRUE),
  volume_month = sum(fifelse(is.finite(Volume) & Volume > 0, Volume, 0), na.rm = TRUE),
  transaction_count_month = .N
), by = .(ID, year_month, food_group10)]

grid <- hm_total[, .(food_group10 = unique(category_map$food_group10)), by = .(ID, year_month, Province, Family_Type, Family_Size,
                                                                               Family_Income, family_size_midpoint,
                                                                               total_food_spend_month, total_food_transactions_month,
                                                                               total_food_spend_pc_month, log_total_food_spend_pc_month, fold)]
panel <- merge(grid, grp, by = c("ID","year_month","food_group10"), all.x = TRUE)
for (v in c("spend_month","volume_month","transaction_count_month")) panel[is.na(get(v)), (v) := 0]
panel[, positive_purchase := as.integer(spend_month > 0)]
panel[, budget_share := spend_month / total_food_spend_month]
panel <- merge(panel, latent[, .(fold, Province, year_month, food_group10, latent_log_price, latent_price_se,
                                 internal_weight, internal_available, external_log_price, fill_levels)],
               by = c("fold","Province","year_month","food_group10"), all.x = TRUE)
cov <- fread(file.path(processed, "province_month_covariates_2020_2022.csv"), encoding = "UTF-8")
setnames(cov, "province", "Province")
panel <- merge(panel, cov, by = c("Province","year_month"), all.x = TRUE)
panel[, income_group_order := unname(income_order[Family_Income])]
panel[, low_income := as.integer(income_group_order <= 2)]
panel[, elderly_household := as.integer(Family_Type == "老年家庭")]
panel[, large_family := as.integer(Family_Size %in% c("家庭人口数4","家庭人口数5+"))]
setorder(panel, ID, year_month, food_group10)
fwrite(panel, file.path(base, "data_derived", "household_month_group10_r.csv"), bom = TRUE)

sample_flow <- data.table(
  metric = c("raw_rows_2020_2022_mapped", "households", "active_household_months", "monthly_group_rows",
             "budget_share_max_abs_adding_error", "latent_price_missing_rows"),
  value = c(nrow(dt), uniqueN(dt$ID), uniqueN(panel[, paste(ID, year_month)]), nrow(panel),
            max(abs(panel[, .(s = sum(budget_share)), by = .(ID, year_month)]$s - 1), na.rm = TRUE),
            sum(!is.finite(panel$latent_log_price)))
)
fwrite(sample_flow, file.path(base, "outputs", "validation", "sample_flow_monthly_r.csv"), bom = TRUE)

report <- c(
  "# 高频价格审计与月度面板报告", "",
  sprintf("- 原始交易行数：%s", format(raw_rows, big.mark = ",")),
  sprintf("- 2020-2022 且映射到 10 组后的交易行数：%s", format(nrow(dt), big.mark = ",")),
  sprintf("- 家庭数：%s", format(uniqueN(dt$ID), big.mark = ",")),
  sprintf("- 活跃家庭-月：%s", format(uniqueN(panel[, paste(ID, year_month)]), big.mark = ",")),
  sprintf("- 家庭-月-10组面板行数：%s", format(nrow(panel), big.mark = ",")), "",
  "## 价格资格分级", "",
  capture.output(print(price_tiers[, .N, by = price_quality_tier][order(price_quality_tier)])), "",
  "## 价格认证", "",
  capture.output(print(validation)), "",
  "## 说明", "",
  "- 本 R 管线不使用家庭自身 unit value 作为需求方程价格。",
  "- 内部价格只来自同一 household fold 之外的交易记录，并由外部省月 10 组价格锚定。",
  "- 蔬菜、水果、海鲜和坚果等高异质组由外部价格主导，内部 unit value 仅提供低权重局地修正。"
)
writeLines(report, file.path(base, "outputs", "validation", "price_validation_report.md"))

message("High-frequency R price and panel build complete.")
