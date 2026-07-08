# price_crossvalid.R — M12b：单位值价格 × 独立价格 交叉验证（MP4）
#  w_fert 单位值 vs 发改委尿素/二铵/氯基复合肥 省×年 相关系数；
#  w_seed 单位值逐品种与全国趋势的相关。
# 产出: out/price_crossvalid.csv
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica",
           "rice_early_indica","rice_late_indica","peanut","rapeseed")

nd <- fread("data/prices_ndrc_annual.csv", encoding = "UTF-8")
fert <- dcast(nd[item %in% c("urea","dap","npk_cl")], province + year ~ item, value.var = "price")

rows <- list()
for (cr in CROPS) {
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  m <- merge(pan[, .(province, year, w_fert, w_seed)], fert, by = c("province","year"), all.x = TRUE)
  cor_s <- function(a, b) { ok <- is.finite(a) & is.finite(b); if (sum(ok) < 10) NA else cor(a[ok], b[ok]) }
  # w_fert 与三肥（省×年 within，去年份均值以看截面+时序共同变异）
  rows[[length(rows)+1]] <- data.table(crop = cr,
    cor_wfert_urea   = round(cor_s(log(m$w_fert), log(m$urea)), 3),
    cor_wfert_dap    = round(cor_s(log(m$w_fert), log(m$dap)), 3),
    cor_wfert_npkcl  = round(cor_s(log(m$w_fert), log(m$npk_cl)), 3),
    cor_wfert_gm3    = round(cor_s(log(m$w_fert), log((m$urea*m$dap*m$npk_cl)^(1/3))), 3),
    # w_seed 与全国当年趋势（品种内全国均值）
    cor_wseed_nattrend = {
      nat <- pan[, .(ws_nat = mean(w_seed, na.rm = TRUE)), by = year]
      mm <- merge(pan[, .(province, year, w_seed)], nat, by = "year")
      round(cor_s(log(mm$w_seed), log(mm$ws_nat)), 3) })
}
out <- rbindlist(rows); fwrite(out, "out/price_crossvalid.csv")
cat("===== M12b 价格交叉验证 =====\n"); print(out)
