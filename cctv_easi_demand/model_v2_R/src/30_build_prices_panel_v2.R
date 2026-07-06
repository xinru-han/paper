#!/usr/bin/env Rscript
# ============================================================================
# v2 pipeline, step 30: external fixed-weight group prices + 9-group panel
#
# Key design changes vs the v1 pipeline (src/20):
#  - Demand system covers 9 food groups (G01..G09). Nuts (G10) are excluded:
#    no genuine external price source exists for nuts (the v1 external series
#    for nuts was an exact copy of the edible-oil series), and nut unit values
#    are Tier-C quality. Average nut budget share ~3.5%; the system is
#    conditional on food-at-home expenditure over the 9 included groups.
#  - Main-specification prices are PURE EXTERNAL provincial monthly market
#    prices: fixed-weight (2021 expenditure weights) log-price indices over
#    externally OBSERVED categories only. No proxy-filled categories enter,
#    no unit-value contamination, no composition drift, no fold dependence.
#  - Internal fold-excluded quality-adjusted unit values are still built, but
#    only for (i) the price certification table and (ii) a hybrid-price
#    robustness specification for groups passing certification.
#  - Certification thresholds (pre-registered): level corr >= 0.5 pass,
#    0.3-0.5 caution, < 0.3 fail; delta corr >= 0.15.
# ============================================================================

suppressPackageStartupMessages({
  library(data.table)
  library(yaml)
})

base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
raw_path <- "/root/data/数据/央视数据/Data_merged.csv"
processed <- "/root/data/Paper/央视数据/Paper1-EASI/processed"
set.seed(20260707)

for (d in c("config", "data_derived", "outputs/price", "outputs/validation")) {
  dir.create(file.path(base, d), recursive = TRUE, showWarnings = FALSE)
}

groups9 <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉",
             "G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品")
codes9 <- sprintf("G%02d", 1:9)
names(groups9) <- codes9

category_map <- data.table(
  Category = c("大米","面粉","挂面","方便面","食用油","蔬菜","水果","猪肉",
               "禽类","其他肉类","牛肉","羊肉","海鲜类","常温牛奶","新鲜牛奶",
               "常温酸奶","新鲜酸奶","奶酪","黄油","成人奶粉","坚果"),
  food_group10 = c("G01_主食","G01_主食","G01_主食","G01_主食","G02_食用油",
                   "G03_蔬菜","G04_水果","G05_猪肉","G06_禽类及其他肉类",
                   "G06_禽类及其他肉类","G07_牛羊肉","G07_牛羊肉","G08_海鲜",
                   "G09_乳制品","G09_乳制品","G09_乳制品","G09_乳制品",
                   "G09_乳制品","G09_乳制品","G09_乳制品","G10_坚果"),
  heterogeneity_tier = c("A","A","B","B","B","C","C","A","B","B","A","A","C",
                         "B","B","B","B","B","B","B","C")
)

# Categories whose external price is genuinely observed at province-month level
observed_external <- c("大米","面粉","方便面","食用油","蔬菜","水果","猪肉",
                       "禽类","其他肉类","牛肉","羊肉","海鲜类",
                       "常温牛奶","新鲜牛奶","成人奶粉")

family_size_mid <- c("家庭人口数1-2" = 1.5, "家庭人口数3" = 3,
                     "家庭人口数4" = 4, "家庭人口数5+" = 5.5)
# OECD-modified equivalence scale approximation by family size band
family_size_oecd <- c("家庭人口数1-2" = 1.25, "家庭人口数3" = 2.0,
                      "家庭人口数4" = 2.5, "家庭人口数5+" = 3.05)
income_order <- c("<5000 RMB" = 1, "5001-7000 RMB" = 2, "7001-9000 RMB" = 3,
                  "9001-12000 RMB" = 4, ">12000 RMB" = 5)
clean_income <- function(x) {
  x <- trimws(as.character(x))
  fifelse(x == ">12000RMB", ">12000 RMB", x)
}
safe_cor <- function(x, y) {
  ok <- is.finite(x) & is.finite(y)
  if (sum(ok) < 10) return(NA_real_)
  suppressWarnings(cor(x[ok], y[ok]))
}

message("[30] Reading raw transactions ...")
dt <- fread(raw_path,
            select = c("ID","Province","Family_Type","Family_Size","Family_Income",
                       "Date","Category","Spend","Volume"),
            encoding = "UTF-8", showProgress = TRUE)
dt[, ID := as.integer(ID)]
dt[, date_clean := as.IDate(gsub("/", "-", substr(as.character(Date), 1, 10)))]
dt[, year := as.integer(format(date_clean, "%Y"))]
dt[, year_month := format(date_clean, "%Y-%m")]
dt[, Family_Income := clean_income(Family_Income)]
for (v in c("Spend","Volume")) dt[, (v) := as.numeric(get(v))]
dt <- dt[year %in% 2020:2022]
dt <- merge(dt, category_map, by = "Category", all.x = TRUE)
dt <- dt[!is.na(food_group10)]
dt[, spend_pos := fifelse(is.finite(Spend) & Spend > 0, Spend, 0)]
raw_mapped_rows <- nrow(dt)

# ---------------------------------------------------------------------------
# 1. Fixed 2021 basket weights over externally observed categories
# ---------------------------------------------------------------------------
message("[30] Fixed 2021 basket weights over observed external categories ...")
bw <- dt[year == 2021 & spend_pos > 0 & Category %in% observed_external,
         .(spend_2021 = sum(spend_pos)), by = .(food_group10, Category)]
bw <- bw[food_group10 %in% groups9]
bw[, weight0 := spend_2021 / sum(spend_2021), by = food_group10]
fwrite(bw, file.path(base, "outputs", "price", "basket_weights_2021_observed_external.csv"), bom = TRUE)

# ---------------------------------------------------------------------------
# 2. External group log-price index, fixed weights, observed categories only
# ---------------------------------------------------------------------------
message("[30] Building external fixed-weight group price index ...")
ext <- fread(file.path(processed, "external_food_prices_category_province_month_2020_2022.csv"),
             encoding = "UTF-8")
setnames(ext, "province", "Province")
ext <- ext[Category %in% observed_external & price_fill_level == "observed_province_month",
           .(Province, year_month, Category, external_log_price)]
stopifnot(!anyNA(ext$external_log_price))
ext <- merge(ext, bw[, .(Category, food_group10, weight0)], by = "Category")
# every (Province, year_month, group) must contain the full fixed basket
chk <- ext[, .(n_cat = uniqueN(Category), wsum = sum(weight0)), by = .(Province, year_month, food_group10)]
full_basket <- bw[, .(n_full = .N), by = food_group10]
chk <- merge(chk, full_basket, by = "food_group10")
stopifnot(all(chk$n_cat == chk$n_full))
ext_group <- ext[, .(lp_ext = sum(weight0 * external_log_price)), by = .(Province, year_month, food_group10)]
stopifnot(nrow(ext_group) == 24 * 36 * 9)

# ---------------------------------------------------------------------------
# 3. Internal fold-excluded quality-adjusted unit values (certification only)
# ---------------------------------------------------------------------------
message("[30] Internal CF-LOO unit values for certification ...")
dt[, raw_uv := fifelse(is.finite(Spend) & is.finite(Volume) & Spend > 0 & Volume > 0,
                       Spend / Volume, NA_real_)]
dt[, log_raw_uv := log(raw_uv)]
dt[, family_size_midpoint := unname(family_size_mid[Family_Size])]
dt[is.na(family_size_midpoint), family_size_midpoint := 3]

# Household-month totals over the 9 included groups
hm9 <- dt[food_group10 %in% groups9,
          .(total_food_spend_month = sum(spend_pos),
            total_food_transactions_month = .N),
          by = .(ID, year_month)]
hm_nut <- dt[food_group10 == "G10_坚果", .(nut_spend_month = sum(spend_pos)), by = .(ID, year_month)]
setorder(dt, ID, year_month, date_clean)
hm_attr <- dt[, .SD[.N], by = .(ID, year_month),
              .SDcols = c("Province","Family_Type","Family_Size","Family_Income","family_size_midpoint")]
hm_total <- merge(hm9, hm_attr, by = c("ID","year_month"), all.x = TRUE)
hm_total <- merge(hm_total, hm_nut, by = c("ID","year_month"), all.x = TRUE)
hm_total[is.na(nut_spend_month), nut_spend_month := 0]
hm_total <- hm_total[total_food_spend_month > 0]
hm_total[, family_size_oecd := unname(family_size_oecd[Family_Size])]
hm_total[is.na(family_size_oecd), family_size_oecd := 2.0]
hm_total[, total_food_spend_pc_month := total_food_spend_month / family_size_midpoint]
hm_total[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]

hh_fold <- unique(hm_total[, .(ID)])
hh_fold[, fold := sample(rep(1:5, length.out = .N))]
hm_total <- merge(hm_total, hh_fold, by = "ID", all.x = TRUE)

uv <- dt[is.finite(log_raw_uv) & spend_pos > 0 & food_group10 %in% groups9]
uv <- merge(uv, hm_total[, .(ID, year_month, log_total_food_spend_pc_month, fold)],
            by = c("ID","year_month"))
uv <- merge(uv, category_map[, .(Category, heterogeneity_tier)], by = "Category")
uv <- uv[heterogeneity_tier %in% c("A","B")]
uv[, q_low := quantile(log_raw_uv, 0.005, na.rm = TRUE), by = .(Category, Province, year)]
uv[, q_high := quantile(log_raw_uv, 0.995, na.rm = TRUE), by = .(Category, Province, year)]
uv[, log_uv_w := pmin(pmax(log_raw_uv, q_low), q_high)]
uv[, spend_pc_bin := {
  r <- frank(log_total_food_spend_pc_month, ties.method = "average", na.last = "keep")
  pmax(1L, pmin(5L, as.integer(ceiling(5 * r / max(r, na.rm = TRUE)))))
}, by = Category]
uv[, cat_mean := mean(log_uv_w), by = Category]
uv[, cell_mean := mean(log_uv_w), by = .(Category, Family_Income, Family_Type, Family_Size, spend_pc_bin)]
uv[!is.finite(cell_mean), cell_mean := cat_mean]
uv[, qadj := log_uv_w - (cell_mean - cat_mean)]

fold_cells <- rbindlist(lapply(1:5, function(k) {
  z <- uv[fold != k, .(int_lp = median(qadj), n_hh = uniqueN(ID)),
          by = .(Province, year_month, Category, food_group10)]
  z[, fold := k]
  z
}))
# category-level internal, averaged over folds, only well-populated cells
int_cat <- fold_cells[n_hh >= 30, .(int_lp = mean(int_lp)), by = .(Province, year_month, Category, food_group10)]

# internal group index with the same fixed weights (only cells with FULL basket)
int_w <- merge(int_cat, bw[, .(Category, weight0)], by = "Category")
int_group <- int_w[, .(lp_int = sum(weight0 * int_lp), n_cat = .N), by = .(Province, year_month, food_group10)]
int_group <- merge(int_group, full_basket, by = "food_group10")
int_group <- int_group[n_cat == n_full]     # full fixed basket only: no composition drift

# ---------------------------------------------------------------------------
# 4. Price certification table
# ---------------------------------------------------------------------------
message("[30] Price certification ...")
cert_dt <- merge(ext_group, int_group[, .(Province, year_month, food_group10, lp_int)],
                 by = c("Province","year_month","food_group10"), all.x = TRUE)
setorder(cert_dt, food_group10, Province, year_month)
cert_dt[, d_ext := lp_ext - shift(lp_ext), by = .(food_group10, Province)]
cert_dt[, d_int := lp_int - shift(lp_int), by = .(food_group10, Province)]
cert <- cert_dt[, .(
  cells = .N,
  internal_coverage = mean(is.finite(lp_int)),
  corr_level = safe_cor(lp_int, lp_ext),
  corr_delta = safe_cor(d_int, d_ext)
), by = food_group10]
cert[, cert_level := fcase(
  !is.finite(corr_level), "no_internal_signal",
  corr_level >= 0.5 & corr_delta >= 0.15, "pass",
  corr_level >= 0.3, "caution",
  default = "fail"
)]
cert[, internal_admissible_robustness := cert_level %in% c("pass","caution")]
fwrite(cert, file.path(base, "outputs", "price", "price_certification_v2.csv"), bom = TRUE)

# hybrid price for robustness: admissible groups get bounded internal weight
lam <- 0.25
hyb <- copy(cert_dt)
hyb <- merge(hyb, cert[, .(food_group10, internal_admissible_robustness)], by = "food_group10")
hyb[, gap_p := mean(lp_ext - lp_int, na.rm = TRUE), by = .(food_group10, Province)]
hyb[, lp_int_aligned := lp_int + gap_p]
hyb[, lp_hybrid := fifelse(internal_admissible_robustness & is.finite(lp_int_aligned),
                           (1 - lam) * lp_ext + lam * lp_int_aligned, lp_ext)]
fwrite(hyb[, .(Province, year_month, food_group10, lp_ext, lp_int, lp_int_aligned, lp_hybrid)],
       file.path(base, "data_derived", "group_prices_v2.csv"), bom = TRUE)

# price variance decomposition: how much variation survives the FE structure
vd_rows <- list()
for (g in groups9) {
  z <- cert_dt[food_group10 == g]
  z[, month := substr(year_month, 6, 7)]
  z[, yr := substr(year_month, 1, 4)]
  v0 <- var(z$lp_ext)
  r1 <- resid(lm(lp_ext ~ factor(Province), z))
  r2 <- resid(lm(lp_ext ~ factor(Province) + factor(month) + factor(yr), z))
  r3 <- resid(lm(lp_ext ~ factor(Province) + factor(year_month), z))
  vd_rows[[g]] <- data.table(food_group10 = g, var_total = v0,
                             share_after_prov = var(r1)/v0,
                             share_after_prov_month_year = var(r2)/v0,
                             share_after_prov_x_time = var(r3)/v0)
}
fwrite(rbindlist(vd_rows), file.path(base, "outputs", "price", "price_variance_decomposition_v2.csv"), bom = TRUE)

# ---------------------------------------------------------------------------
# 5. Household-month-group panel (9 groups)
# ---------------------------------------------------------------------------
message("[30] Building 9-group household-month panel ...")
grp <- dt[food_group10 %in% groups9,
          .(spend_month = sum(spend_pos), transaction_count_month = .N),
          by = .(ID, year_month, food_group10)]
grid <- hm_total[, .(food_group10 = groups9), by = .(ID, year_month, Province, Family_Type,
                                                     Family_Size, Family_Income,
                                                     family_size_midpoint, family_size_oecd,
                                                     total_food_spend_month, total_food_transactions_month,
                                                     total_food_spend_pc_month, log_total_food_spend_pc_month,
                                                     nut_spend_month, fold)]
panel <- merge(grid, grp, by = c("ID","year_month","food_group10"), all.x = TRUE)
for (v in c("spend_month","transaction_count_month")) panel[is.na(get(v)), (v) := 0]
panel[, positive_purchase := as.integer(spend_month > 0)]
panel[, budget_share := spend_month / total_food_spend_month]
panel <- merge(panel, hyb[, .(Province, year_month, food_group10, lp_ext, lp_hybrid)],
               by = c("Province","year_month","food_group10"), all.x = TRUE)
stopifnot(!anyNA(panel$lp_ext))
cov <- fread(file.path(processed, "province_month_covariates_2020_2022.csv"), encoding = "UTF-8")
setnames(cov, "province", "Province")
panel <- merge(panel, cov, by = c("Province","year_month"), all.x = TRUE)
panel[, income_group_order := unname(income_order[Family_Income])]
panel[, low_income := as.integer(income_group_order <= 2)]
panel[, elderly_household := as.integer(Family_Type == "老年家庭")]
panel[, large_family := as.integer(Family_Size %in% c("家庭人口数4","家庭人口数5+"))]
setorder(panel, ID, year_month, food_group10)
fwrite(panel, file.path(base, "data_derived", "household_month_group9_v2.csv"), bom = TRUE)

adding_err <- panel[, .(s = sum(budget_share)), by = .(ID, year_month)][, max(abs(s - 1))]
sample_flow <- data.table(
  metric = c("raw_rows_2020_2022_mapped_10groups", "raw_rows_9groups", "households",
             "active_household_months_9group", "panel_rows",
             "budget_share_max_abs_adding_error", "mean_nut_share_of_food10",
             "external_price_missing_rows"),
  value = c(raw_mapped_rows, dt[food_group10 %in% groups9, .N], uniqueN(hm_total$ID),
            nrow(hm_total), nrow(panel), adding_err,
            hm_total[, mean(nut_spend_month / (nut_spend_month + total_food_spend_month))],
            sum(!is.finite(panel$lp_ext)))
)
fwrite(sample_flow, file.path(base, "outputs", "validation", "sample_flow_v2.csv"), bom = TRUE)
print(sample_flow)
message("[30] Done.")
