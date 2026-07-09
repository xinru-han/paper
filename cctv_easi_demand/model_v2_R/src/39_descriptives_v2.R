#!/usr/bin/env Rscript
# v2 step 39: descriptive statistics for the paper (Table 1 inputs).
suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "descriptives")
dir.create(odir, recursive = TRUE, showWarnings = FALSE)

panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
wide <- make_wide(panel, price_col = "lp_ext")

# group-level: budget share, purchase rate, share conditional on purchase
grp <- rbindlist(lapply(seq_along(CODES9), function(g) {
  cc <- CODES9[g]
  w <- wide[[paste0("w_", cc)]]; pos <- wide[[paste0("pos_", cc)]]
  data.table(food_group10 = GROUPS9[g],
             mean_budget_share = mean(w),
             purchase_rate = mean(pos),
             mean_share_if_purchase = mean(w[pos == 1]),
             sd_budget_share = sd(w))
}))
fwrite(grp, file.path(odir, "group_descriptives_v2.csv"), bom = TRUE)

# household-month level
hh <- unique(wide, by = "ID")
hm <- data.table(
  statistic = c("households", "household_months", "provinces", "months",
                "mean_monthly_food_spend", "median_monthly_food_spend",
                "mean_monthly_food_spend_pc", "mean_family_size",
                "share_low_income", "share_elderly", "share_large_family"),
  value = c(uniqueN(wide$ID), nrow(wide), uniqueN(wide$Province), uniqueN(wide$year_month),
            mean(wide$total_food_spend_month), median(wide$total_food_spend_month),
            mean(wide$total_food_spend_pc_month), mean(hh$family_size_midpoint),
            mean(hh$low_income), mean(hh$elderly_household), mean(hh$large_family)))
fwrite(hm, file.path(odir, "sample_descriptives_v2.csv"), bom = TRUE)

# by income group
inc <- wide[, .(households = uniqueN(ID), mean_food_spend = mean(total_food_spend_month),
                mean_food_spend_pc = mean(total_food_spend_pc_month)),
            by = income_group_order][order(income_group_order)]
fwrite(inc, file.path(odir, "income_group_descriptives_v2.csv"), bom = TRUE)

# external price index series for the figure (already in group_prices, national mean)
gp <- fread(file.path(base, "data_derived", "group_prices_v2.csv"), encoding = "UTF-8")
nat <- gp[, .(lp_ext_mean = mean(lp_ext), lp_ext_p10 = quantile(lp_ext, .1),
              lp_ext_p90 = quantile(lp_ext, .9)), by = .(food_group10, year_month)]
fwrite(nat, file.path(odir, "national_price_series_v2.csv"), bom = TRUE)
message("[39] Done.")
