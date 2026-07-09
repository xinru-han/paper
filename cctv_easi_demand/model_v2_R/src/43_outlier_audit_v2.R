#!/usr/bin/env Rscript
# ============================================================================
# v2 step 43: dataset outlier / data-quality audit (appendix documentation).
# Documents the thin-recording household-months and lumpy-share observations
# that motivate the purchase-cycle treatment and the winsor/screen robustness,
# and confirms they do not drive the main estimates (see robustness bundle 40).
# ============================================================================
suppressPackageStartupMessages(library(data.table))
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
odir <- file.path(base, "outputs", "validation")
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8",
               select = c("ID","year_month","food_group10","total_food_spend_month",
                          "total_food_spend_pc_month","total_food_transactions_month",
                          "budget_share","positive_purchase"))
hm <- unique(panel[, .(ID, year_month, total_food_spend_month, total_food_spend_pc_month,
                       total_food_transactions_month)], by = c("ID","year_month"))

qs <- c(0, .005, .01, .05, .25, .5, .75, .95, .99, .995, 1)
qnames <- c("min","p0_5","p1","p5","p25","p50","p75","p95","p99","p99_5","max")
q_tbl <- function(x, nm) {
  v <- as.list(round(quantile(x, qs), 3)); names(v) <- qnames
  data.table(variable = nm, as.data.table(v))
}
audit_q <- rbindlist(list(
  q_tbl(hm$total_food_spend_month, "total_food_spend_month"),
  q_tbl(hm$total_food_spend_pc_month, "total_food_spend_pc_month"),
  q_tbl(hm$total_food_transactions_month, "food_transactions_month")))
fwrite(audit_q, file.path(odir, "outlier_audit_quantiles_v2.csv"), bom = TRUE)

# thin-recording flags & lumpy-share incidence
flags <- data.table(
  metric = c("hh_months_total",
             "share_pc_spend_below_20rmb", "share_lt_3_transactions",
             "share_lt_5_transactions",
             "G01_purchaser_months", "G01_share_eq_1_count", "G01_share_gt_0.6_share"),
  value = c(nrow(hm),
            round(mean(hm$total_food_spend_pc_month < 20), 4),
            round(mean(hm$total_food_transactions_month < 3), 4),
            round(mean(hm$total_food_transactions_month < 5), 4),
            panel[food_group10=="G01_主食" & positive_purchase==1, .N],
            panel[food_group10=="G01_主食" & budget_share>=0.999, .N],
            round(panel[food_group10=="G01_主食" & positive_purchase==1, mean(budget_share>0.6)], 4)))
fwrite(flags, file.path(odir, "outlier_audit_flags_v2.csv"), bom = TRUE)
cat("=== outlier audit quantiles ===\n"); print(audit_q)
cat("\n=== outlier audit flags ===\n"); print(flags)
cat("\n=== DONE outlier audit ===\n")
