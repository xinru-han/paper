#!/usr/bin/env Rscript
suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
panel_path <- file.path(base, "data_derived", "household_month_group9_v2.csv")
stopifnot(file.exists(panel_path))
p <- fread(panel_path, encoding = "UTF-8")
share_sum <- p[, .(s = sum(budget_share)), by = .(ID, year_month)]
stopifnot(max(abs(share_sum$s - 1), na.rm = TRUE) < 1e-8)
stopifnot(p[, all(is.finite(lp_ext))])
stopifnot(!file.exists(file.path(base, "outputs", "_DRIVER2_FAILED")))
fwz <- file.path(base, "outputs", "robustness", "robustness_freq_winsor_zero_v2.csv")
if (file.exists(fwz)) {
  x <- fread(fwz)
  stopifnot(!any(x$variant %in% c("F1_quarterly", "F2_annual", "Z1_dual_hurdle")))
}
ff <- file.path(base, "outputs", "robustness", "fourweek_frequency_v2.csv")
if (file.exists(ff)) {
  x <- fread(ff)
  stopifnot(max(x$purchase_rate_28d, na.rm = TRUE) < 0.999)
}
stopifnot(file.exists(file.path(base, "outputs", "results_manifest_v2.csv")) ||
          !dir.exists(file.path(base, "outputs")))
message("[99] smoke tests passed")
