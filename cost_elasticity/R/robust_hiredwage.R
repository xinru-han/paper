# robust_hiredwage.R — 稳健性：w_labor 改用雇工工价（有省际变异的市场工价）
# 基线劳动日工价为全国统一记账值（零截面变异，识别只剩时间维度）；
# 本规格 w_labor=w_labor_hired，其余同 cc 基线。
# 产出: data/panel_{crop}_hw.csv、out/*_{crop}_hw_cc.csv、out/robust_hw_compare.csv
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R"); source("R/estimate.R")

crops <- commandArgs(trailingOnly = TRUE)
if (!length(crops)) crops <- c("corn", "wheat", "soybean", "rice_japonica", "rice_mid_indica",
                               "rice_early_indica", "rice_late_indica", "peanut", "rapeseed")
cmp <- list()
for (cr in crops) {
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  pan[, w_labor := w_labor_hired]
  fwrite(pan, sprintf("data/panel_%s_hw.csv", cr))
  cat(sprintf("\n===== %s [hired-wage cc] =====\n", cr))
  r <- tryCatch(fit_crop(paste0(cr, "_hw"), method = "cc"),
                error = function(e) { cat("!!", conditionMessage(e), "\n"); NULL })
  if (is.null(r)) next
  b5 <- fread(sprintf("out/elasticities_%s_cc.csv", cr))[period == "all"]
  el <- r$el[period == "all"]
  cmp[[cr]] <- data.table(crop = cr, conc_hw = r$conc_rate,
    eps_ll_base = round(b5[f_n == "labor" & f_m == "labor", eps], 3),
    eps_ll_hw = round(el[f_n == "labor" & f_m == "labor", eps], 3),
    M_ml_base = round(b5[f_n == "mach" & f_m == "labor", morishima], 3),
    M_ml_hw = round(el[f_n == "mach" & f_m == "labor", morishima], 3),
    B_labor_hw = round(r$bias[factor == "labor", B], 4))
  print(cmp[[cr]])
}
fwrite(rbindlist(cmp), "out/robust_hw_compare.csv")
cat("\n== baseline vs hired-wage ==\n"); print(rbindlist(cmp))
