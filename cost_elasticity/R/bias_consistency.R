# bias_consistency.R — M7：技术偏向一致性筛查表（跨规格）
#  品种×要素：S1 λ_nt 符号 + M1 CI 是否排除零 | S2 累计 δ_n,2024 符号 | hw 符号 | 6f 符号
#  → consistent = 四者同向且 S1 CI 排除零。结论只允许引用 consistent=TRUE 的单元。
#  另：机械偏向不一致机制诊断——去趋势 δ_mach 与 lnw_mach 相对价格的相关。
# 产出: out/bias_consistency.csv, out/bias_mach_mechanism.csv
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica",
           "rice_early_indica","rice_late_indica","peanut","rapeseed")

# M1 draws → B_labor/B_mach percentile CI（排除零？）
dr <- fread("out/bootstrap_draws_all_cc.csv")[status == "ok" & period == "all"]
ci <- dr[, .(B_labor_lo = quantile(B_labor,.025), B_labor_hi = quantile(B_labor,.975),
             B_mach_lo = quantile(B_mach,.025),  B_mach_hi = quantile(B_mach,.975)), by = crop]

rows <- list(); mech <- list()
for (cr in CROPS) {
  s1 <- fread(sprintf("out/bias_%s_cc.csv", cr))          # factor, lambda_nt, S_mean, B
  hw <- tryCatch(fread(sprintf("out/bias_%s_hw_cc.csv", cr)), error = function(e) NULL)
  s6 <- tryCatch(fread(sprintf("out/bias6f_%s.csv", cr)), error = function(e) NULL)
  bp <- fread(sprintf("out/bias_path_%s.csv", cr))        # crop, year, factor, delta
  cci <- ci[crop == cr]
  for (fac in c("labor","mach")) {
    s1B <- s1[factor == fac]$B
    lo <- if (fac == "labor") cci$B_labor_lo else cci$B_mach_lo
    hi <- if (fac == "labor") cci$B_labor_hi else cci$B_mach_hi
    ci_excl0 <- (lo > 0 & hi > 0) | (lo < 0 & hi < 0)
    d2024 <- bp[factor == fac & year == max(year)]$delta
    hwB <- if (!is.null(hw)) hw[factor == fac]$B else NA_real_
    s6B <- if (!is.null(s6)) s6[factor == fac]$B else NA_real_
    sgn <- function(x) ifelse(is.na(x), NA, sign(x))
    # S2 偏向方向：δ_n,2024>0 表示 n 份额被技术上移 = n 使用型；与 S1 的 B(=λ/S)同号比较
    signs <- c(sgn(s1B), sgn(d2024), sgn(hwB), sgn(s6B))
    consistent <- !any(is.na(signs)) && length(unique(signs)) == 1 && ci_excl0
    rows[[length(rows)+1]] <- data.table(crop = cr, factor = fac,
      S1_B = round(s1B,4), S1_sign = sgn(s1B), M1_CI = sprintf("[%.4f,%.4f]", lo, hi), CI_excl0 = ci_excl0,
      S2_delta2024 = round(d2024,4), S2_sign = sgn(d2024),
      hw_B = round(hwB,4), hw_sign = sgn(hwB), sixf_B = round(s6B,4), sixf_sign = sgn(s6B),
      consistent = consistent)
  }
  # 机制诊断：去趋势 δ_mach 与 lnw_mach 相对价格（品种内按产量聚合）
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  lw <- pan[, .(lnw_mach = log(weighted.mean(w_mach, q_output)) - log(weighted.mean(w_other, q_output))), by = year][order(year)]
  dm <- bp[factor == "mach"][order(year)]
  m <- merge(dm, lw, by = "year")
  m[, delta_dt := residuals(lm(delta ~ year))]; m[, lnw_dt := residuals(lm(lnw_mach ~ year))]
  mech[[cr]] <- data.table(crop = cr, corr_detrended = round(cor(m$delta_dt, m$lnw_dt), 3),
                           corr_raw = round(cor(m$delta, m$lnw_mach), 3))
}
bc <- rbindlist(rows); fwrite(bc, "out/bias_consistency.csv")
mc <- rbindlist(mech); fwrite(mc, "out/bias_mach_mechanism.csv")
cat("===== M7 偏向一致性 =====\n"); print(bc[, .(crop, factor, S1_sign, CI_excl0, S2_sign, hw_sign, sixf_sign, consistent)])
cat("\n可引用(consistent=TRUE)单元:\n"); print(bc[consistent == TRUE, .(crop, factor, S1_B)])
cat("\n===== 机械偏向机制（去趋势 δ_mach vs lnw_mach 相关）=====\n"); print(mc)
