#!/usr/bin/env Rscript
# ============================================================================
# v2 step 42: 4-week (28-day) frequency robustness.
# Calendar months have unequal length and arbitrary boundaries; a common
# alternative for continuous scanner panels is a fixed 28-day period. We rebin
# the raw transactions into 28-day windows (anchored at the first sample date),
# rebuild household-period group spends/shares, assign each window the external
# provincial price of the calendar month containing its midpoint, and report
# the reduced-form own-price benchmark (purchase rate + among-purchaser
# intensive own-price elasticity) next to the calendar-month version. Stable
# results indicate the monthly binning is not driving the elasticities.
# ============================================================================
suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
raw_path <- "/root/data/数据/央视数据/Data_merged.csv"
processed <- "/root/data/Paper/央视数据/Paper1-EASI/processed"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "robustness")

category_map <- data.table(
  Category = c("大米","面粉","挂面","方便面","食用油","蔬菜","水果","猪肉",
               "禽类","其他肉类","牛肉","羊肉","海鲜类","常温牛奶","新鲜牛奶",
               "常温酸奶","新鲜酸奶","奶酪","黄油","成人奶粉","坚果"),
  food_group10 = c("G01_主食","G01_主食","G01_主食","G01_主食","G02_食用油",
                   "G03_蔬菜","G04_水果","G05_猪肉","G06_禽类及其他肉类",
                   "G06_禽类及其他肉类","G07_牛羊肉","G07_牛羊肉","G08_海鲜",
                   "G09_乳制品","G09_乳制品","G09_乳制品","G09_乳制品",
                   "G09_乳制品","G09_乳制品","G09_乳制品","G10_坚果"))
observed_external <- c("大米","面粉","方便面","食用油","蔬菜","水果","猪肉",
                       "禽类","其他肉类","牛肉","羊肉","海鲜类",
                       "常温牛奶","新鲜牛奶","成人奶粉")
family_size_mid <- c("家庭人口数1-2" = 1.5, "家庭人口数3" = 3, "家庭人口数4" = 4, "家庭人口数5+" = 5.5)

message("[42] Reading raw transactions ...")
dt <- fread(raw_path, select = c("ID","Province","Family_Size","Date","Category","Spend"),
            encoding = "UTF-8")
dt[, date_clean := as.IDate(gsub("/", "-", substr(as.character(Date), 1, 10)))]
dt <- dt[!is.na(date_clean)]
dt[, year := year(date_clean)]
dt <- dt[year %in% 2020:2022]
dt <- merge(dt, category_map, by = "Category", all.x = TRUE)
dt <- dt[!is.na(food_group10) & food_group10 %in% GROUPS9]
dt[, Spend := as.numeric(Spend)]
dt[, spend_pos := fifelse(is.finite(Spend) & Spend > 0, Spend, 0)]

anchor <- min(dt$date_clean)
dt[, p28 := as.integer(as.integer(date_clean - anchor) %/% 28L)]      # 28-day period index
dt[, mid_month := format(anchor + as.integer(p28) * 28L + 14L, "%Y-%m")]  # month of window midpoint
dt[, family_size_midpoint := unname(family_size_mid[Family_Size])]
dt[is.na(family_size_midpoint), family_size_midpoint := 3]

# external prices by category-province-month (observed)
ext <- fread(file.path(processed, "external_food_prices_category_province_month_2020_2022.csv"),
             encoding = "UTF-8")
setnames(ext, "province", "Province")
ext <- ext[Category %in% observed_external & price_fill_level == "observed_province_month",
           .(Province, year_month, Category, external_log_price)]
bw <- dt[year == 2021 & spend_pos > 0 & Category %in% observed_external,
         .(spend_2021 = sum(spend_pos)), by = .(food_group10, Category)]
bw[, weight0 := spend_2021 / sum(spend_2021), by = food_group10]
full_basket <- bw[, .(n_full = .N), by = food_group10]
ext <- merge(ext, bw[, .(Category, food_group10, weight0)], by = "Category")
ext_group <- ext[, .(lp_ext = sum(weight0 * external_log_price), n_cat = .N),
                 by = .(Province, year_month, food_group10)]
ext_group <- merge(ext_group, full_basket, by = "food_group10")[n_cat == n_full]

# household-28day-group spends
grp <- dt[, .(spend = sum(spend_pos), fsz = family_size_midpoint[1]),
          by = .(ID, Province, p28, mid_month, food_group10)]
tot <- grp[, .(tot_spend = sum(spend)), by = .(ID, p28)]
grp <- merge(grp, tot, by = c("ID","p28"))[tot_spend > 0]
grp <- merge(grp, ext_group[, .(Province, mid_month = year_month, food_group10, lp_ext)],
             by = c("Province","mid_month","food_group10"))
grp[, pos := as.integer(spend > 0)]
grp[, log_x_pc := log(tot_spend / fsz)]
grp[, q_pc := spend / exp(lp_ext) / fsz]

cat("=== 4-week (28-day) purchase rate & intensive own-price elasticity ===\n")
rows <- list()
for (g in GROUPS9) {
  z <- grp[food_group10 == g]
  pr <- mean(z$pos)
  zp <- z[pos == 1 & is.finite(q_pc) & q_pc > 0]
  zp[, prov := factor(Province)]; zp[, per := factor(p28)]
  m <- tryCatch(lm(log(q_pc) ~ lp_ext + log_x_pc + prov + per, data = zp), error = function(e) NULL)
  b <- if (!is.null(m)) unname(coef(m)["lp_ext"]) else NA_real_
  rows[[g]] <- data.table(food_group10 = g, purchase_rate_28d = pr,
                          own_price_intensive_28d = b, n_purchasers = nrow(zp))
}
out <- rbindlist(rows)
fwrite(out, file.path(odir, "fourweek_frequency_v2.csv"), bom = TRUE)
print(out)
cat("\n=== DONE 4-week frequency ===\n")
