# 高频家庭食品需求系统 — 全部 R 代码汇编

本文件汇总该研究项目从原始交易数据到最终弹性与诊断的全部 R 代码，按执行顺序排列。
数据根目录：`/opt/data/research/央视数据`。

## 执行顺序

1. `20_build_high_frequency_price_and_panel.R` — 构建面板与潜在价格
2. `21_estimate_high_frequency_demand_R.R` — 第一阶段购买选择 Probit（其稀疏二步因内存/规模未完成）
3. `22_estimate_high_frequency_demand_fast_R.R` — 受约束需求系统主估计（替代 21 的二步）
4. `23_finalize_demand_diagnostics.R` — 弹性复算 + 曲率诊断（本次新增）

---

## `src/20_build_high_frequency_price_and_panel.R`

阶段一：价格审计 + 月度面板与潜在价格构建

```r
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
```

---

## `src/21_estimate_high_frequency_demand_R.R`

阶段二（第一步）：CRE/Mundlak Probit 购买选择方程；含已废弃的稀疏堆叠二步估计（未完成）

```r
#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(Matrix)
  library(jsonlite)
  library(lmtest)
  library(sandwich)
})

script_path <- tryCatch(normalizePath(sys.frame(1)$ofile), error = function(e) file.path(getwd(), "src", "21_estimate_high_frequency_demand_R.R"))
base <- normalizePath(file.path(dirname(script_path), ".."), mustWork = TRUE)
dir.create(file.path(base, "outputs", "demand"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(base, "outputs", "regularity"), recursive = TRUE, showWarnings = FALSE)

codes <- sprintf("G%02d", 1:10)
groups <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉",
            "G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品","G10_坚果")
names(groups) <- codes
eq_codes <- codes[1:9]
omitted_code <- codes[10]
h <- 0.01

panel_path <- file.path(base, "data_derived", "household_month_group10_r.csv")
if (!file.exists(panel_path)) stop("Run src/20_build_high_frequency_price_and_panel.R first.")

message("Reading R monthly demand panel...")
panel <- fread(panel_path, encoding = "UTF-8", showProgress = TRUE)
panel <- panel[is.finite(latent_log_price) & is.finite(budget_share) & total_food_spend_month > 0]
panel[, group_code := substr(food_group10, 1, 3)]
panel[, year := substr(year_month, 1, 4)]
panel[, month := substr(year_month, 6, 7)]
panel[, covid_log := log1p(covid_daily_new_sum)]
panel[, precip_log := log1p(pmax(precipitation_mm_sum, 0))]

message("Casting to household-month wide format...")
id_cols <- c("ID","year_month","year","month","Province","Family_Type","Family_Size","Family_Income",
             "family_size_midpoint","total_food_spend_month","total_food_spend_pc_month",
             "log_total_food_spend_pc_month","fold","low_income","elderly_household","large_family",
             "cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log",
             "wholesale_agri_200_mean")
base_wide <- unique(panel[, ..id_cols], by = c("ID","year_month"))
cast_one <- function(value_col, prefix) {
  x <- dcast(panel, ID + year_month ~ group_code, value.var = value_col)
  setnames(x, codes, paste0(prefix, "_", codes), skip_absent = TRUE)
  x
}
wide <- Reduce(function(a, b) merge(a, b, by = c("ID","year_month"), all.x = TRUE),
               list(base_wide,
                    cast_one("budget_share", "w"),
                    cast_one("positive_purchase", "pos"),
                    cast_one("latent_log_price", "lp"),
                    cast_one("latent_price_se", "lpse")))
setorder(wide, ID, year_month)
share_cols <- paste0("w_", codes)
pos_cols <- paste0("pos_", codes)
lp_cols <- paste0("lp_", codes)
for (v in c(share_cols, pos_cols)) wide[is.na(get(v)), (v) := 0]
wide <- wide[rowSums(!is.finite(as.matrix(wide[, ..lp_cols]))) == 0]

wide[, stone_price := rowSums(as.matrix(.SD) * as.matrix(wide[, ..lp_cols])), .SDcols = share_cols]
wide[, y_easi := log_total_food_spend_pc_month - stone_price]
wide[, y_easi2 := y_easi^2]

for (code in eq_codes) wide[, paste0("r_", code) := get(paste0("lp_", code)) - get(paste0("lp_", omitted_code))]
r_cols <- paste0("r_", eq_codes)

scale_cols <- c("cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
for (v in scale_cols) {
  m <- mean(wide[[v]], na.rm = TRUE); s <- sd(wide[[v]], na.rm = TRUE)
  if (!is.finite(s) || s == 0) s <- 1
  wide[, paste0("z_", v) := (get(v) - m) / s]
}
z_cols <- paste0("z_", scale_cols)

message("Estimating CRE/Mundlak probit selection equations...")
wide[, mean_y_easi_hh := mean(y_easi, na.rm = TRUE), by = ID]
first_pred <- wide[, .(ID, year_month)]
first_coef <- list()
first_stats <- list()

selection_formula <- as.formula(paste(
  "y ~ y_easi +", paste(r_cols, collapse = " + "),
  "+ low_income + elderly_household + large_family + mean_y_easi_hh +",
  paste(z_cols, collapse = " + "),
  "+ factor(month) + factor(year)"
))

for (code in codes) {
  y <- wide[[paste0("pos_", code)]]
  df <- cbind(data.frame(y = y), as.data.frame(wide[, c("y_easi", r_cols, "low_income", "elderly_household", "large_family", "mean_y_easi_hh", z_cols, "month", "year"), with = FALSE]))
  fit <- glm(selection_formula, data = df, family = binomial(link = "probit"), control = glm.control(maxit = 80))
  xb <- as.numeric(predict(fit, type = "link"))
  Phi <- pmin(pmax(pnorm(xb), 1e-6), 1 - 1e-6)
  phi <- dnorm(xb)
  first_pred[, paste0("Phi_", code) := Phi]
  first_pred[, paste0("phi_", code) := phi]
  llf <- sum(y * log(Phi) + (1 - y) * log(1 - Phi))
  p0 <- mean(y)
  llnull <- sum(y * log(p0) + (1 - y) * log(1 - p0))
  brier <- mean((y - Phi)^2)
  first_coef[[code]] <- data.table(food_group10 = groups[[code]], term = names(coef(fit)), estimate = as.numeric(coef(fit)))
  first_stats[[code]] <- data.table(food_group10 = groups[[code]], nobs = length(y), positive_rate = mean(y),
                                    mean_predicted_probability = mean(Phi), brier = brier,
                                    pseudo_r2_mcfadden = 1 - llf / llnull)
}
fwrite(first_pred, file.path(base, "outputs", "demand", "selection_cre_probit_predictions_r.csv"), bom = TRUE)
fwrite(rbindlist(first_coef), file.path(base, "outputs", "demand", "selection_cre_probit_coefficients_r.csv"), bom = TRUE)
fwrite(rbindlist(first_stats), file.path(base, "outputs", "demand", "selection_cre_probit_fit_stats_r.csv"), bom = TRUE)
wide <- merge(wide, first_pred, by = c("ID","year_month"), all.x = TRUE)

message("Building constrained stacked SY-EASI design...")
demo_cols <- c("low_income","elderly_household","large_family", z_cols)
base_terms <- c("const","y_easi","y_easi2", demo_cols)
n <- nrow(wide)
Gm1 <- length(eq_codes)

upper_pairs <- which(upper.tri(matrix(0, Gm1, Gm1), diag = TRUE), arr.ind = TRUE)
pair_names <- paste0("p_", upper_pairs[,1], "_", upper_pairs[,2])

make_design <- function(dt, sy = TRUE, quaids = FALSE) {
  nr <- nrow(dt) * Gm1
  p_base <- length(eq_codes) * length(base_terms)
  p_price <- nrow(upper_pairs)
  p_yp <- nrow(upper_pairs)
  p_sigma <- if (sy) length(eq_codes) else 0
  X <- Matrix(0, nrow = nr, ncol = p_base + p_price + p_yp + p_sigma, sparse = TRUE)
  coln <- c(as.vector(outer(eq_codes, base_terms, paste, sep = "__")),
            paste0("sym_price__", pair_names),
            paste0(if (quaids) "sym_y2_price__" else "sym_y_price__", pair_names),
            if (sy) paste0("sigma__", eq_codes) else NULL)
  colnames(X) <- coln
  y <- numeric(nr)
  row_group <- character(nr)
  offset <- 0L
  for (g in seq_along(eq_codes)) {
    code <- eq_codes[g]
    rows <- offset + seq_len(nrow(dt))
    offset <- offset + nrow(dt)
    y[rows] <- dt[[paste0("w_", code)]]
    row_group[rows] <- code
    mult <- if (sy) dt[[paste0("Phi_", code)]] else rep(1, nrow(dt))
    base_mat <- cbind(const = 1, y_easi = dt$y_easi, y_easi2 = dt$y_easi2, as.matrix(dt[, ..demo_cols]))
    for (b in seq_along(base_terms)) {
      X[rows, paste0(code, "__", base_terms[b])] <- mult * base_mat[, b]
    }
    rmat <- as.matrix(dt[, ..r_cols])
    ymult <- if (quaids) dt$y_easi2 else dt$y_easi
    for (k in seq_len(nrow(upper_pairs))) {
      a <- upper_pairs[k, 1]; b <- upper_pairs[k, 2]
      val <- if (g == a) rmat[, b] else if (g == b) rmat[, a] else 0
      if (a == b && g == a) val <- rmat[, a]
      X[rows, paste0("sym_price__", pair_names[k])] <- mult * val
      X[rows, paste0(if (quaids) "sym_y2_price__" else "sym_y_price__", pair_names[k])] <- mult * ymult * val
    }
    if (sy) X[rows, paste0("sigma__", code)] <- dt[[paste0("phi_", code)]]
  }
  list(X = X, y = y, row_group = row_group)
}

fit_sparse_lm <- function(design, ridge = 1e-8) {
  xtx <- as.matrix(crossprod(design$X))
  diag(xtx) <- diag(xtx) + ridge
  xty <- as.numeric(crossprod(design$X, design$y))
  fit <- as.numeric(solve(xtx, xty))
  names(fit) <- colnames(design$X)
  pred <- as.numeric(design$X %*% fit)
  list(coef = fit, pred = pred, resid = design$y - pred)
}

des_sy <- make_design(wide, sy = TRUE, quaids = FALSE)
fit_sy <- fit_sparse_lm(des_sy)
des_q <- make_design(wide, sy = TRUE, quaids = TRUE)
fit_q <- fit_sparse_lm(des_q)
des_nosy <- make_design(wide, sy = FALSE, quaids = FALSE)
fit_nosy <- fit_sparse_lm(des_nosy)

saveRDS(list(metadata = list(codes = codes, groups = groups, eq_codes = eq_codes, omitted_code = omitted_code,
                             base_terms = base_terms, r_cols = r_cols, demo_cols = demo_cols,
                             upper_pairs = upper_pairs),
             sy_easi = fit_sy$coef, sy_quaids = fit_q$coef, no_sy_easi = fit_nosy$coef),
        file.path(base, "outputs", "demand", "constrained_high_frequency_models_r.rds"))

coef_dt <- rbindlist(list(
  data.table(model = "constrained_sy_easi", term = names(fit_sy$coef), estimate = fit_sy$coef),
  data.table(model = "constrained_sy_quaids", term = names(fit_q$coef), estimate = fit_q$coef),
  data.table(model = "constrained_no_sy_easi", term = names(fit_nosy$coef), estimate = fit_nosy$coef)
))
fwrite(coef_dt, file.path(base, "outputs", "demand", "constrained_model_coefficients_r.csv"), bom = TRUE)

predict_model <- function(dt, coef, sy = TRUE, quaids = FALSE) {
  des <- make_design(dt, sy = sy, quaids = quaids)
  pred9 <- matrix(as.numeric(des$X %*% coef), nrow = nrow(dt), ncol = Gm1, byrow = FALSE)
  colnames(pred9) <- eq_codes
  pred <- cbind(pred9, G10 = 1 - rowSums(pred9))
  colnames(pred) <- codes
  pred[pred < 1e-8] <- 1e-8
  pred / rowSums(pred)
}

base_sh <- predict_model(wide, fit_sy$coef, sy = TRUE, quaids = FALSE)
pred_dt <- data.table(ID = wide$ID, year_month = wide$year_month, base_sh)
setnames(pred_dt, codes, paste0("pred_w_", codes))
fwrite(pred_dt, file.path(base, "outputs", "demand", "predicted_shares_constrained_sy_easi_r.csv"), bom = TRUE)

quantity_matrix <- function(dt, shares) {
  prices <- exp(as.matrix(dt[, ..lp_cols]))
  shares * dt$total_food_spend_pc_month / prices
}
perturb_exp <- function(dt) {
  out <- copy(dt)
  out[, total_food_spend_pc_month := total_food_spend_pc_month * (1 + h)]
  out[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]
  out[, stone_price := rowSums(as.matrix(.SD) * as.matrix(out[, ..lp_cols])), .SDcols = share_cols]
  out[, y_easi := log_total_food_spend_pc_month - stone_price]
  out[, y_easi2 := y_easi^2]
  out
}
perturb_price <- function(dt, code) {
  out <- copy(dt)
  out[[paste0("lp_", code)]] <- out[[paste0("lp_", code)]] + log(1 + h)
  out[, stone_price := rowSums(as.matrix(.SD) * as.matrix(out[, ..lp_cols])), .SDcols = share_cols]
  out[, y_easi := log_total_food_spend_pc_month - stone_price]
  out[, y_easi2 := y_easi^2]
  for (cc in eq_codes) out[, paste0("r_", cc) := get(paste0("lp_", cc)) - get(paste0("lp_", omitted_code))]
  out
}
agg_elas <- function(q0, q1, idx) ((colMeans(q1[idx,,drop=FALSE]) - colMeans(q0[idx,,drop=FALSE])) / colMeans(q0[idx,,drop=FALSE])) / h

message("Computing numerical monthly elasticities...")
q0 <- quantity_matrix(wide, base_sh)
q_exp <- quantity_matrix(perturb_exp(wide), predict_model(perturb_exp(wide), fit_sy$coef, sy = TRUE, quaids = FALSE))
all_idx <- rep(TRUE, nrow(wide))
exp_vec <- agg_elas(q0, q_exp, all_idx)
mar <- matrix(NA_real_, 10, 10, dimnames = list(groups, groups))
price_q <- vector("list", 10); names(price_q) <- codes
for (code in codes) {
  wp <- perturb_price(wide, code)
  qp <- quantity_matrix(wp, predict_model(wp, fit_sy$coef, sy = TRUE, quaids = FALSE))
  price_q[[code]] <- qp
  mar[, groups[[code]]] <- agg_elas(q0, qp, all_idx)
}
avg_share <- colMeans(as.matrix(wide[, ..share_cols]))
hick <- mar + exp_vec %o% avg_share

fwrite(data.table(food_group10 = groups, food_expenditure_elasticity = as.numeric(exp_vec)),
       file.path(base, "outputs", "demand", "food_expenditure_elasticity_monthly_r.csv"), bom = TRUE)
fwrite(data.table(demand_group = rownames(mar), mar), file.path(base, "outputs", "demand", "marshallian_elasticity_monthly_r.csv"), bom = TRUE)
fwrite(data.table(demand_group = rownames(hick), hick), file.path(base, "outputs", "demand", "hicksian_elasticity_monthly_r.csv"), bom = TRUE)

message("Writing heterogeneity elasticities...")
hetero_rows <- list()
hetero_specs <- c(low_income = "low_income", elderly_household = "elderly_household", large_family = "large_family")
for (hn in names(hetero_specs)) {
  col <- hetero_specs[[hn]]
  for (lev in sort(unique(wide[[col]]))) {
    idx <- wide[[col]] == lev
    if (sum(idx) < 100) next
    ev <- agg_elas(q0, q_exp, idx)
    for (k in seq_along(codes)) hetero_rows[[length(hetero_rows)+1]] <- data.table(heterogeneity = hn, level = lev, elasticity_type = "food_expenditure", demand_group = groups[k], shock_group = "food_expenditure", elasticity = ev[k], n = sum(idx))
    for (code in codes) {
      pv <- agg_elas(q0, price_q[[code]], idx)
      for (k in seq_along(codes)) hetero_rows[[length(hetero_rows)+1]] <- data.table(heterogeneity = hn, level = lev, elasticity_type = "marshallian_price", demand_group = groups[k], shock_group = groups[[code]], elasticity = pv[k], n = sum(idx))
    }
  }
}
fwrite(rbindlist(hetero_rows), file.path(base, "outputs", "demand", "elasticities_by_prespecified_heterogeneity_r.csv"), bom = TRUE)

message("Writing theory and regularity diagnostics...")
adding <- data.table(metric = c("n_household_months", "max_abs_predicted_share_sum_error", "mean_abs_predicted_share_sum_error", "min_predicted_share", "max_predicted_share"),
                     value = c(nrow(wide), max(abs(rowSums(base_sh) - 1)), mean(abs(rowSums(base_sh) - 1)), min(base_sh), max(base_sh)))
sym_terms <- grep("^sym_price__", names(fit_sy$coef), value = TRUE)
sym_diag <- data.table(model = "constrained_sy_easi", restriction = c("adding_up", "homogeneity_relative_prices", "slutsky_symmetry_price_coefficients"),
                       status = c("by_construction_predicted_10th_share", "by_construction_relative_prices", "by_construction_symmetric_parameterization"),
                       max_abs_error = c(max(abs(rowSums(base_sh)-1)), 0, 0))
own <- data.table(food_group10 = groups, own_price_elasticity = diag(mar), is_negative = diag(mar) < 0)
fwrite(adding, file.path(base, "outputs", "regularity", "adding_up_diagnostics_r.csv"), bom = TRUE)
fwrite(sym_diag, file.path(base, "outputs", "regularity", "theory_constraint_checks.csv"), bom = TRUE)
fwrite(own, file.path(base, "outputs", "regularity", "own_price_sign_diagnostics_r.csv"), bom = TRUE)

report <- c(
  "# R 高频月度需求模型报告", "",
  sprintf("- 家庭-月观测：%s", format(nrow(wide), big.mark = ",")),
  sprintf("- 家庭数：%s", format(uniqueN(wide$ID), big.mark = ",")),
  sprintf("- 月份：%s 至 %s", min(wide$year_month), max(wide$year_month)), "",
  "## 第一阶段 CRE/Mundlak Probit", "",
  capture.output(print(rbindlist(first_stats))), "",
  "## 理论约束", "",
  capture.output(print(sym_diag)), "",
  "## 自价格弹性", "",
  capture.output(print(own)), "",
  "## 解释边界", "",
  "- 弹性为 monthly food-expenditure elasticity 与 measured market-price variation 下的条件需求响应。",
  "- 本脚本不把 food-expenditure elasticity 写作 income elasticity。",
  "- 当前 R 版为可复现主规格；全流程 bootstrap 可在该脚本基础上按家庭重抽样扩展。"
)
writeLines(report, file.path(base, "outputs", "demand", "high_frequency_demand_model_report_r.md"))

message("High-frequency R demand models complete.")
```

---

## `src/22_estimate_high_frequency_demand_fast_R.R`

阶段三：快速正规方程版受约束 SY-EASI / SY-QUAIDS 主估计（当前主模型）

```r
#!/usr/bin/env Rscript
suppressPackageStartupMessages({ library(data.table); library(jsonlite) })
script_path <- tryCatch(normalizePath(sys.frame(1)$ofile), error=function(e) file.path(getwd(), "src", "22_estimate_high_frequency_demand_fast_R.R"))
base <- normalizePath(file.path(dirname(script_path), ".."), mustWork=TRUE)
dir.create(file.path(base, "outputs", "demand"), recursive=TRUE, showWarnings=FALSE)
dir.create(file.path(base, "outputs", "regularity"), recursive=TRUE, showWarnings=FALSE)

codes <- sprintf("G%02d", 1:10)
groups <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉","G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品","G10_坚果")
names(groups) <- codes
eq_codes <- codes[1:9]
omitted_code <- codes[10]
h <- 0.01

message("Reading panel and casting wide...")
panel <- fread(file.path(base, "data_derived", "household_month_group10_r.csv"), encoding="UTF-8", showProgress=TRUE)
panel <- panel[is.finite(latent_log_price) & is.finite(budget_share) & total_food_spend_month > 0]
panel[, group_code := substr(food_group10, 1, 3)]
panel[, year := substr(year_month, 1, 4)]
panel[, month := substr(year_month, 6, 7)]
panel[, covid_log := log1p(covid_daily_new_sum)]
panel[, precip_log := log1p(pmax(precipitation_mm_sum, 0))]

id_cols <- c("ID","year_month","year","month","Province","Family_Type","Family_Size","Family_Income",
             "family_size_midpoint","total_food_spend_month","total_food_spend_pc_month",
             "log_total_food_spend_pc_month","fold","low_income","elderly_household","large_family",
             "cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
base_wide <- unique(panel[, ..id_cols], by=c("ID","year_month"))
cast_one <- function(value_col, prefix) {
  x <- dcast(panel, ID + year_month ~ group_code, value.var=value_col)
  setnames(x, codes, paste0(prefix, "_", codes), skip_absent=TRUE)
  x
}
wide <- Reduce(function(a,b) merge(a,b,by=c("ID","year_month"),all.x=TRUE),
               list(base_wide, cast_one("budget_share","w"), cast_one("positive_purchase","pos"), cast_one("latent_log_price","lp")))
setorder(wide, ID, year_month)
share_cols <- paste0("w_", codes); pos_cols <- paste0("pos_", codes); lp_cols <- paste0("lp_", codes)
for (v in c(share_cols,pos_cols)) wide[is.na(get(v)), (v) := 0]
wide <- wide[rowSums(!is.finite(as.matrix(wide[, ..lp_cols]))) == 0]
wide[, stone_price := rowSums(as.matrix(.SD) * as.matrix(wide[, ..lp_cols])), .SDcols=share_cols]
wide[, y_easi := log_total_food_spend_pc_month - stone_price]
wide[, y_easi2 := y_easi^2]
for (code in eq_codes) wide[, paste0("r_", code) := get(paste0("lp_", code)) - get(paste0("lp_", omitted_code))]
r_cols <- paste0("r_", eq_codes)
scale_cols <- c("cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
for (v in scale_cols) {
  m <- mean(wide[[v]], na.rm=TRUE); s <- sd(wide[[v]], na.rm=TRUE)
  if (!is.finite(s) || s == 0) s <- 1
  wide[, paste0("z_", v) := (get(v)-m)/s]
}
z_cols <- paste0("z_", scale_cols)
demo_cols <- c("low_income","elderly_household","large_family", z_cols)

pred_path <- file.path(base, "outputs", "demand", "selection_cre_probit_predictions_r.csv")
if (!file.exists(pred_path)) stop("Missing selection predictions. Run src/21_estimate_high_frequency_demand_R.R until first stage completes.")
first_pred <- fread(pred_path)
wide <- merge(wide, first_pred, by=c("ID","year_month"), all.x=TRUE)

base_terms <- c("const","y_easi","y_easi2", demo_cols)
upper_pairs <- which(upper.tri(matrix(0,9,9), diag=TRUE), arr.ind=TRUE)
pair_names <- paste0("p_", upper_pairs[,1], "_", upper_pairs[,2])
term_names <- c(as.vector(outer(eq_codes, base_terms, paste, sep="__")),
                paste0("sym_price__", pair_names), paste0("sym_y_price__", pair_names), paste0("sigma__", eq_codes))
idx_base <- matrix(seq_len(length(eq_codes)*length(base_terms)), nrow=length(eq_codes), byrow=TRUE)
offset_price <- length(eq_codes)*length(base_terms)
offset_yp <- offset_price + nrow(upper_pairs)
offset_sigma <- offset_yp + nrow(upper_pairs)
pair_index <- matrix(NA_integer_,9,9)
for (k in seq_len(nrow(upper_pairs))) {
  a <- upper_pairs[k,1]; b <- upper_pairs[k,2]
  pair_index[a,b] <- k; pair_index[b,a] <- k
}

build_active <- function(dt, g, quaids=FALSE) {
  code <- eq_codes[g]
  mult <- dt[[paste0("Phi_", code)]]
  base_mat <- cbind(const=1, y_easi=dt$y_easi, y_easi2=dt$y_easi2, as.matrix(dt[, ..demo_cols]))
  rmat <- as.matrix(dt[, ..r_cols])
  ym <- if (quaids) dt$y_easi2 else dt$y_easi
  A <- cbind(mult*base_mat, mult*rmat, mult*(ym*rmat), dt[[paste0("phi_", code)]])
  cols <- c(idx_base[g,], offset_price + pair_index[g, seq_len(9)], offset_yp + pair_index[g, seq_len(9)], offset_sigma + g)
  list(A=A, cols=cols, y=dt[[paste0("w_", code)]])
}
fit_cp <- function(dt, quaids=FALSE, ridge=1e-8) {
  p <- length(term_names); xtx <- matrix(0, p, p); xty <- numeric(p)
  for (g in seq_along(eq_codes)) {
    z <- build_active(dt,g,quaids)
    xtx[z$cols,z$cols] <- xtx[z$cols,z$cols] + crossprod(z$A)
    xty[z$cols] <- xty[z$cols] + as.numeric(crossprod(z$A,z$y))
  }
  diag(xtx) <- diag(xtx) + ridge
  b <- as.numeric(solve(xtx, xty)); names(b) <- term_names; b
}
predict_cp <- function(dt, b, quaids=FALSE) {
  pred <- matrix(0, nrow(dt), 10); colnames(pred) <- codes
  for (g in seq_along(eq_codes)) {
    z <- build_active(dt,g,quaids)
    pred[,g] <- as.numeric(z$A %*% b[z$cols])
  }
  pred[,10] <- 1 - rowSums(pred[,1:9,drop=FALSE])
  pred[pred < 1e-8] <- 1e-8
  pred / rowSums(pred)
}

message("Estimating fast constrained SY-EASI...")
b_sy <- fit_cp(wide, quaids=FALSE)
message("Estimating fast constrained SY-QUAIDS...")
b_q <- fit_cp(wide, quaids=TRUE)
saveRDS(list(sy_easi=b_sy, sy_quaids=b_q, term_names=term_names, eq_codes=eq_codes, codes=codes, groups=groups),
        file.path(base, "outputs", "demand", "constrained_high_frequency_models_fast_r.rds"))
fwrite(rbindlist(list(
  data.table(model="constrained_sy_easi_fast", term=names(b_sy), estimate=b_sy),
  data.table(model="constrained_sy_quaids_fast", term=names(b_q), estimate=b_q)
)), file.path(base, "outputs", "demand", "constrained_model_coefficients_fast_r.csv"), bom=TRUE)

message("Computing elasticities...")
base_sh <- predict_cp(wide, b_sy, quaids=FALSE)
quantity_matrix <- function(dt, shares) {
  prices <- exp(as.matrix(dt[, ..lp_cols])); shares * dt$total_food_spend_pc_month / prices
}
refresh <- function(out) {
  out[, stone_price := rowSums(as.matrix(.SD)*as.matrix(out[, ..lp_cols])), .SDcols=share_cols]
  out[, y_easi := log_total_food_spend_pc_month - stone_price]
  out[, y_easi2 := y_easi^2]
  for (cc in eq_codes) out[, paste0("r_", cc) := get(paste0("lp_", cc)) - get(paste0("lp_", omitted_code))]
  out
}
q0 <- quantity_matrix(wide, base_sh)
we <- copy(wide); we[, total_food_spend_pc_month := total_food_spend_pc_month*(1+h)]
we[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]; we <- refresh(we)
q_exp <- quantity_matrix(we, predict_cp(we,b_sy,FALSE))
agg_elas <- function(q0,q1,idx) ((colMeans(q1[idx,,drop=FALSE])-colMeans(q0[idx,,drop=FALSE]))/colMeans(q0[idx,,drop=FALSE]))/h
all_idx <- rep(TRUE,nrow(wide)); exp_vec <- agg_elas(q0,q_exp,all_idx)
mar <- matrix(NA_real_,10,10,dimnames=list(groups,groups)); price_q <- list()
for (code in codes) {
  wp <- copy(wide); wp[[paste0("lp_",code)]] <- wp[[paste0("lp_",code)]] + log(1+h); wp <- refresh(wp)
  qp <- quantity_matrix(wp, predict_cp(wp,b_sy,FALSE)); price_q[[code]] <- qp
  mar[,groups[[code]]] <- agg_elas(q0,qp,all_idx)
}
avg_share <- colMeans(as.matrix(wide[, ..share_cols])); hick <- mar + exp_vec %o% avg_share
fwrite(data.table(food_group10=groups, food_expenditure_elasticity=as.numeric(exp_vec)), file.path(base, "outputs", "demand", "food_expenditure_elasticity_monthly_fast_r.csv"), bom=TRUE)
fwrite(data.table(demand_group=rownames(mar), mar), file.path(base, "outputs", "demand", "marshallian_elasticity_monthly_fast_r.csv"), bom=TRUE)
fwrite(data.table(demand_group=rownames(hick), hick), file.path(base, "outputs", "demand", "hicksian_elasticity_monthly_fast_r.csv"), bom=TRUE)

hetero_rows <- list(); specs <- c(low_income="low_income", elderly_household="elderly_household", large_family="large_family")
for (hn in names(specs)) for (lev in sort(unique(wide[[specs[[hn]]]]))) {
  idx <- wide[[specs[[hn]]]] == lev
  if (sum(idx) < 100) next
  ev <- agg_elas(q0,q_exp,idx)
  for (k in seq_along(codes)) hetero_rows[[length(hetero_rows)+1]] <- data.table(heterogeneity=hn, level=lev, elasticity_type="food_expenditure", demand_group=groups[k], shock_group="food_expenditure", elasticity=ev[k], n=sum(idx))
  for (code in codes) {
    pv <- agg_elas(q0,price_q[[code]],idx)
    for (k in seq_along(codes)) hetero_rows[[length(hetero_rows)+1]] <- data.table(heterogeneity=hn, level=lev, elasticity_type="marshallian_price", demand_group=groups[k], shock_group=groups[[code]], elasticity=pv[k], n=sum(idx))
  }
}
fwrite(rbindlist(hetero_rows), file.path(base, "outputs", "demand", "elasticities_by_prespecified_heterogeneity_fast_r.csv"), bom=TRUE)

adding <- data.table(metric=c("n_household_months","max_abs_predicted_share_sum_error","mean_abs_predicted_share_sum_error","min_predicted_share","max_predicted_share"),
                     value=c(nrow(wide), max(abs(rowSums(base_sh)-1)), mean(abs(rowSums(base_sh)-1)), min(base_sh), max(base_sh)))
theory <- data.table(model="constrained_sy_easi_fast", restriction=c("adding_up","homogeneity_relative_prices","slutsky_symmetry_price_coefficients"),
                     status=c("by_construction_predicted_10th_share","by_construction_relative_prices","by_construction_symmetric_parameterization"),
                     max_abs_error=c(max(abs(rowSums(base_sh)-1)),0,0))
own <- data.table(food_group10=groups, own_price_elasticity=diag(mar), is_negative=diag(mar)<0)
fwrite(adding, file.path(base, "outputs", "regularity", "adding_up_diagnostics_fast_r.csv"), bom=TRUE)
fwrite(theory, file.path(base, "outputs", "regularity", "theory_constraint_checks_fast_r.csv"), bom=TRUE)
fwrite(own, file.path(base, "outputs", "regularity", "own_price_sign_diagnostics_fast_r.csv"), bom=TRUE)

report <- c("# R 高频月度需求模型报告（快速正规方程版）", "",
            sprintf("- 家庭-月观测：%s", format(nrow(wide), big.mark=",")),
            sprintf("- 家庭数：%s", format(uniqueN(wide$ID), big.mark=",")),
            sprintf("- 月份：%s 至 %s", min(wide$year_month), max(wide$year_month)), "",
            "## 自价格弹性", "", capture.output(print(own)), "",
            "## 约束", "", capture.output(print(theory)), "",
            "说明：该 R 版使用外部锚定、fold-excluded 内部价格信号和受约束 SY-EASI；结果解释为 monthly food-expenditure elasticity 和 measured market-price variation 下的条件需求响应。")
writeLines(report, file.path(base, "outputs", "demand", "high_frequency_demand_model_report_fast_r.md"))
message("Fast high-frequency R demand model complete.")
```

---

## `final_demand_model_R/23_finalize_demand_diagnostics.R`

阶段四（本次新增）：复用系数计算两模型弹性 + 曲率/负定性诊断 + 残差组标注

```r
#!/usr/bin/env Rscript
# 23_finalize_demand_diagnostics.R
# 目的：在不重估的前提下，复用 src/22 已保存的受约束系数，对
#   (1) SY-EASI 与 (2) SY-QUAIDS 两个主模型分别计算月度弹性；
#   (3) 补齐方案要求但此前缺失的“曲率/负定性诊断”（Slutsky 替代矩阵特征值）；
#   (4) 明确标注被省略的第 10 组（坚果）为残差组、其弹性不可直接解释。
# 输入：央视数据/data_derived/household_month_group10_r.csv
#       央视数据/outputs/demand/selection_cre_probit_predictions_r.csv
#       央视数据/outputs/demand/constrained_high_frequency_models_fast_r.rds
# 输出：央视数据/final_demand_model_R/outputs/*

suppressPackageStartupMessages({ library(data.table) })

base <- "/opt/data/research/央视数据"
outdir <- file.path(base, "final_demand_model_R", "outputs")
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

codes <- sprintf("G%02d", 1:10)
groups <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉",
            "G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品","G10_坚果")
names(groups) <- codes
eq_codes <- codes[1:9]
omitted_code <- codes[10]
h <- 0.01

models <- readRDS(file.path(base, "outputs", "demand", "constrained_high_frequency_models_fast_r.rds"))
term_names <- models$term_names

message("Reading panel and casting wide...")
panel <- fread(file.path(base, "data_derived", "household_month_group10_r.csv"), encoding = "UTF-8", showProgress = TRUE)
panel <- panel[is.finite(latent_log_price) & is.finite(budget_share) & total_food_spend_month > 0]
panel[, group_code := substr(food_group10, 1, 3)]
panel[, covid_log := log1p(covid_daily_new_sum)]
panel[, precip_log := log1p(pmax(precipitation_mm_sum, 0))]

id_cols <- c("ID","year_month","Province","Family_Type","Family_Size","Family_Income",
             "family_size_midpoint","total_food_spend_month","total_food_spend_pc_month",
             "log_total_food_spend_pc_month","fold","low_income","elderly_household","large_family",
             "cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
base_wide <- unique(panel[, ..id_cols], by = c("ID","year_month"))
cast_one <- function(value_col, prefix) {
  x <- dcast(panel, ID + year_month ~ group_code, value.var = value_col)
  setnames(x, codes, paste0(prefix, "_", codes), skip_absent = TRUE)
  x
}
wide <- Reduce(function(a, b) merge(a, b, by = c("ID","year_month"), all.x = TRUE),
               list(base_wide, cast_one("budget_share","w"), cast_one("positive_purchase","pos"), cast_one("latent_log_price","lp")))
setorder(wide, ID, year_month)
share_cols <- paste0("w_", codes); pos_cols <- paste0("pos_", codes); lp_cols <- paste0("lp_", codes)
for (v in c(share_cols, pos_cols)) wide[is.na(get(v)), (v) := 0]
wide <- wide[rowSums(!is.finite(as.matrix(wide[, ..lp_cols]))) == 0]
wide[, stone_price := rowSums(as.matrix(.SD) * as.matrix(wide[, ..lp_cols])), .SDcols = share_cols]
wide[, y_easi := log_total_food_spend_pc_month - stone_price]
wide[, y_easi2 := y_easi^2]
for (code in eq_codes) wide[, paste0("r_", code) := get(paste0("lp_", code)) - get(paste0("lp_", omitted_code))]
r_cols <- paste0("r_", eq_codes)
scale_cols <- c("cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
for (v in scale_cols) {
  m <- mean(wide[[v]], na.rm = TRUE); s <- sd(wide[[v]], na.rm = TRUE)
  if (!is.finite(s) || s == 0) s <- 1
  wide[, paste0("z_", v) := (get(v) - m) / s]
}
z_cols <- paste0("z_", scale_cols)
demo_cols <- c("low_income","elderly_household","large_family", z_cols)

pred <- fread(file.path(base, "outputs", "demand", "selection_cre_probit_predictions_r.csv"))
wide <- merge(wide, pred, by = c("ID","year_month"), all.x = TRUE)

# ---- design indexing identical to src/22 ----
base_terms <- c("const","y_easi","y_easi2", demo_cols)
upper_pairs <- which(upper.tri(matrix(0,9,9), diag = TRUE), arr.ind = TRUE)
idx_base <- matrix(seq_len(length(eq_codes)*length(base_terms)), nrow = length(eq_codes), byrow = TRUE)
offset_price <- length(eq_codes)*length(base_terms)
offset_yp <- offset_price + nrow(upper_pairs)
offset_sigma <- offset_yp + nrow(upper_pairs)
pair_index <- matrix(NA_integer_, 9, 9)
for (k in seq_len(nrow(upper_pairs))) { a<-upper_pairs[k,1]; b<-upper_pairs[k,2]; pair_index[a,b]<-k; pair_index[b,a]<-k }

build_active <- function(dt, g, quaids = FALSE) {
  code <- eq_codes[g]
  mult <- dt[[paste0("Phi_", code)]]
  base_mat <- cbind(const=1, y_easi=dt$y_easi, y_easi2=dt$y_easi2, as.matrix(dt[, ..demo_cols]))
  rmat <- as.matrix(dt[, ..r_cols])
  ym <- if (quaids) dt$y_easi2 else dt$y_easi
  A <- cbind(mult*base_mat, mult*rmat, mult*(ym*rmat), dt[[paste0("phi_", code)]])
  cols <- c(idx_base[g,], offset_price + pair_index[g, seq_len(9)], offset_yp + pair_index[g, seq_len(9)], offset_sigma + g)
  list(A=A, cols=cols)
}
predict_cp <- function(dt, b, quaids = FALSE) {
  pr <- matrix(0, nrow(dt), 10); colnames(pr) <- codes
  for (g in seq_along(eq_codes)) { z <- build_active(dt,g,quaids); pr[,g] <- as.numeric(z$A %*% b[z$cols]) }
  pr[,10] <- 1 - rowSums(pr[,1:9,drop=FALSE]); pr[pr<1e-8] <- 1e-8; pr/rowSums(pr)
}
quantity_matrix <- function(dt, shares) { prices <- exp(as.matrix(dt[, ..lp_cols])); shares*dt$total_food_spend_pc_month/prices }
refresh <- function(out) {
  out[, stone_price := rowSums(as.matrix(.SD)*as.matrix(out[, ..lp_cols])), .SDcols=share_cols]
  out[, y_easi := log_total_food_spend_pc_month - stone_price]; out[, y_easi2 := y_easi^2]
  for (cc in eq_codes) out[, paste0("r_", cc) := get(paste0("lp_", cc)) - get(paste0("lp_", omitted_code))]; out
}
agg_elas <- function(q0,q1) ((colMeans(q1)-colMeans(q0))/colMeans(q0))/h

avg_share <- colMeans(as.matrix(wide[, ..share_cols]))

compute_set <- function(b, quaids, tag) {
  message("Computing elasticities for ", tag, " ...")
  base_sh <- predict_cp(wide, b, quaids)
  q0 <- quantity_matrix(wide, base_sh)
  we <- copy(wide); we[, total_food_spend_pc_month := total_food_spend_pc_month*(1+h)]
  we[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]; we <- refresh(we)
  q_exp <- quantity_matrix(we, predict_cp(we, b, quaids)); exp_vec <- agg_elas(q0, q_exp)
  mar <- matrix(NA_real_, 10, 10, dimnames = list(groups, groups))
  for (code in codes) {
    wp <- copy(wide); wp[[paste0("lp_",code)]] <- wp[[paste0("lp_",code)]] + log(1+h); wp <- refresh(wp)
    qp <- quantity_matrix(wp, predict_cp(wp, b, quaids)); mar[, groups[[code]]] <- agg_elas(q0, qp)
  }
  hick <- mar + exp_vec %o% avg_share
  # 曲率/负定性诊断：份额加权 Slutsky 替代矩阵 S_ij = w_i * e^h_ij，对称化后求特征值
  S <- diag(avg_share) %*% hick
  Ssym <- (S + t(S)) / 2
  ev <- sort(eigen(Ssym, symmetric = TRUE, only.values = TRUE)$values, decreasing = TRUE)
  list(exp_vec=exp_vec, mar=mar, hick=hick, eig=ev,
       own=data.table(food_group10=groups, own_price_elasticity=diag(mar),
                      is_negative=diag(mar)<0,
                      is_omitted_residual_group = codes==omitted_code))
}

res_easi <- compute_set(models$sy_easi, FALSE, "SY-EASI")
res_quaids <- compute_set(models$sy_quaids, TRUE, "SY-QUAIDS")

write_set <- function(res, suf) {
  fwrite(data.table(food_group10=groups, food_expenditure_elasticity=as.numeric(res$exp_vec)),
         file.path(outdir, paste0("food_expenditure_elasticity_", suf, ".csv")), bom=TRUE)
  fwrite(data.table(demand_group=rownames(res$mar), res$mar),
         file.path(outdir, paste0("marshallian_elasticity_", suf, ".csv")), bom=TRUE)
  fwrite(data.table(demand_group=rownames(res$hick), res$hick),
         file.path(outdir, paste0("hicksian_elasticity_", suf, ".csv")), bom=TRUE)
  fwrite(res$own, file.path(outdir, paste0("own_price_sign_", suf, ".csv")), bom=TRUE)
}
write_set(res_easi, "sy_easi")
write_set(res_quaids, "sy_quaids")

# 曲率诊断汇总（含/不含残差组）
curv <- function(res, tag) {
  ev <- res$eig
  data.table(model=tag,
             n_nonpositive_eig = sum(ev <= 1e-8),
             max_eig = max(ev), min_eig = min(ev),
             negative_semidefinite_full = all(ev <= 1e-8),
             eigenvalues = paste(sprintf("%.4f", ev), collapse="; "))
}
curv_dt <- rbindlist(list(curv(res_easi, "constrained_sy_easi"), curv(res_quaids, "constrained_sy_quaids")))
fwrite(curv_dt, file.path(outdir, "curvature_negativity_diagnostics.csv"), bom=TRUE)

# 自价格符号汇总（两模型并排，标注残差组）
sign_cmp <- data.table(food_group10=groups,
                       sy_easi_own = diag(res_easi$mar),
                       sy_quaids_own = diag(res_quaids$mar),
                       omitted_residual_group = codes==omitted_code,
                       sy_easi_negative = diag(res_easi$mar)<0,
                       sy_quaids_negative = diag(res_quaids$mar)<0)
fwrite(sign_cmp, file.path(outdir, "own_price_sign_comparison.csv"), bom=TRUE)

saveRDS(list(easi=res_easi, quaids=res_quaids, avg_share=avg_share,
             n_hh_months=nrow(wide), n_households=uniqueN(wide$ID)),
        file.path(outdir, "finalize_diagnostics.rds"))
fwrite(data.table(metric=c("n_household_months","n_households","year_month_min","year_month_max"),
                  value=c(nrow(wide), uniqueN(wide$ID), min(wide$year_month), max(wide$year_month))),
       file.path(outdir, "sample_summary.csv"), bom=TRUE)
message("Done. Outputs in ", outdir)
```

---
