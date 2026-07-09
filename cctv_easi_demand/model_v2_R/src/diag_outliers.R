#!/usr/bin/env Rscript
# Diagnostic: outlier audit of the v2 panel, focused on staples (G01)
suppressPackageStartupMessages(library(data.table))
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8",
               select = c("ID","year_month","Province","food_group10","family_size_midpoint",
                          "total_food_spend_month","total_food_spend_pc_month",
                          "log_total_food_spend_pc_month","spend_month","budget_share",
                          "positive_purchase","lp_ext"))

# household-month level table (one row per hh-month)
hm <- unique(panel[, .(ID, year_month, Province, family_size_midpoint,
                       total_food_spend_month, total_food_spend_pc_month,
                       log_total_food_spend_pc_month)], by = c("ID","year_month"))

qs <- c(0, .0001, .001, .005, .01, .05, .25, .5, .75, .95, .99, .995, .999, .9999, 1)
cat("=== total_food_spend_month (hh-month) ===\n")
print(round(quantile(hm$total_food_spend_month, qs), 2))
cat("\n=== total_food_spend_pc_month (hh-month) ===\n")
print(round(quantile(hm$total_food_spend_pc_month, qs), 2))
cat("\n=== log_total_food_spend_pc_month ===\n")
print(round(quantile(hm$log_total_food_spend_pc_month, qs), 3))
cat(sprintf("\nmean=%.2f sd=%.2f  |  n hh-month=%d\n",
            mean(hm$log_total_food_spend_pc_month), sd(hm$log_total_food_spend_pc_month), nrow(hm)))

# how many hh-months are extreme
cat(sprintf("\nhh-months with pc food spend > 5000/mo: %d (%.3f%%)\n",
            sum(hm$total_food_spend_pc_month > 5000), 100*mean(hm$total_food_spend_pc_month > 5000)))
cat(sprintf("hh-months with pc food spend < 20/mo:   %d (%.3f%%)\n",
            sum(hm$total_food_spend_pc_month < 20), 100*mean(hm$total_food_spend_pc_month < 20)))

# budget shares per group
cat("\n=== budget_share quantiles by group ===\n")
bs <- panel[, as.list(round(quantile(budget_share, c(.5,.9,.99,.999,1)),3)), by = food_group10]
setnames(bs, c("food_group10","p50","p90","p99","p999","max"))
print(bs)

# among purchasers, share distribution for staples
cat("\n=== G01 staple budget_share among purchasers ===\n")
g1 <- panel[food_group10=="G01_主食" & positive_purchase==1]
print(round(quantile(g1$budget_share, qs), 3))
cat(sprintf("G01 purchasers with share > 0.6: %d (%.3f%% of purchasers)\n",
            sum(g1$budget_share>0.6), 100*mean(g1$budget_share>0.6)))
cat(sprintf("G01 purchasers with share = 1.0: %d\n", sum(g1$budget_share>=0.999)))

# staple price series spread
cat("\n=== G01 lp_ext (external staple log price) ===\n")
g1p <- unique(panel[food_group10=="G01_主食", .(Province, year_month, lp_ext)])
print(round(quantile(g1p$lp_ext, qs), 4))
cat(sprintf("G01 price: distinct prov-month cells=%d, sd=%.4f, range=[%.3f,%.3f]\n",
            nrow(g1p), sd(g1p$lp_ext), min(g1p$lp_ext), max(g1p$lp_ext)))

cat("\n=== DONE diag ===\n")
