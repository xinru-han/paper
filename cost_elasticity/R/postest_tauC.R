# postest_tauC.R — M4：撤除 RTS/TFP，只保留对偶技术率 τ_C 年路径（+ M1 bootstrap CI）
#   ε_Cy 病态（除法偏误+无外生y变异），RTS=1/ε_Cy、TFP=−τ_C/ε_Cy 不可发表 → 停产。
#   scale_tfp_*.csv 改名 _deprecated 存档；新产出 out/tauC_{crop}_cc.csv（年路径+CI）。
# 用法: Rscript R/postest_tauC.R
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/estimate.R")
CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica",
           "rice_early_indica","rice_late_indica","peanut","rapeseed")
FN <- c("labor","mach","fert","seed","other")
PB <- list(`2004-2008`=2004:2008,`2009-2014`=2009:2014,`2015-2019`=2015:2019,`2020-2024`=2020:2024)

# M1 draws 的 period-level τ_C CI（若已产出）
draws_ci <- NULL
if (file.exists("out/bootstrap_draws_all_cc.csv")) {
  dr <- fread("out/bootstrap_draws_all_cc.csv")
  if ("tauC" %in% names(dr))
    draws_ci <- dr[status == "ok" & !is.na(tauC), .(tauC_lo = quantile(tauC,.025), tauC_hi = quantile(tauC,.975)),
                   by = .(crop, period)]
}

tauC_path <- function(cr) {
  th_dt <- fread(sprintf("out/params_%s_cc.csv", cr)); th <- setNames(th_dt$est, th_dt$param)
  d <- prep_data(fread(sprintf("data/panel_%s.csv", cr)))
  lnw <- as.matrix(d[, sprintf("lnw_%d",1:4), with = FALSE])
  d$tauC <- th["lambda_t"] + th["lambda_tt"]*d$tt +
    as.numeric(lnw %*% th[sprintf("lambda_%dt",1:4)]) + th["lambda_yt"]*d$lny
  yr <- d[, .(tauC = mean(tauC)), by = year][order(year)]
  # period 均值 + CI
  d[, period := NA_character_]; for (nm in names(PB)) d[year %in% PB[[nm]], period := nm]
  per <- d[, .(tauC = mean(tauC)), by = period]
  per[, crop := cr]
  if (!is.null(draws_ci)) per <- merge(per, draws_ci[crop == cr], by = c("crop","period"), all.x = TRUE)
  list(yr = data.table(crop = cr, yr), per = per)
}

allper <- list()
for (cr in CROPS) {
  r <- tauC_path(cr)
  fwrite(r$yr, sprintf("out/tauC_%s_cc.csv", cr))
  allper[[cr]] <- r$per
  # 停产 scale_tfp：改名 _deprecated（含 _cc 与 plain 版）
  for (sfx in c(sprintf("scale_tfp_%s_cc.csv", cr), sprintf("scale_tfp_%s.csv", cr),
                sprintf("scale_tfp_%s_hw_cc.csv", cr))) {
    if (file.exists(file.path("out", sfx)))
      file.rename(file.path("out", sfx), file.path("out", sub("\\.csv$", "_deprecated.csv", sfx)))
  }
}
fwrite(rbindlist(allper, fill = TRUE), "out/tauC_period_summary.csv")
cat("[postest_tauC] τ_C 年路径 + period CI 产出；scale_tfp_* 已停产改名 _deprecated\n")
print(rbindlist(allper, fill = TRUE)[, .(crop, period, tauC = round(tauC,3))])
