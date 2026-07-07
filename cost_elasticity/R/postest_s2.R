# postest_s2.R — S2 general-index 规格（份额方程年哑变量）+ 诱致性创新两阶段（plan §1.8）
# 用法: Rscript R/postest_s2.R <crop1> <crop2> ...   （最后自动跑跨品种第二阶段）
# 产出: out/bias_path_{crop}.csv（累计技术偏向 delta_n_tau）、out/induced_innovation.csv
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R"); source("R/estimate.R")

FN <- c("labor", "mach", "fert", "seed", "other")

s2_crop <- function(cr) {
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  d <- prep_data(pan)
  yrs <- sort(unique(d$year))
  sys <- tl_build_system(d, 4, share_time = "gindex", year_dummies = as.character(yrs))
  fit <- tl_itsur(sys, tol = 1e-9)
  stopifnot(fit$converged)
  # delta_n_tau：非numeraire 4要素直接读，other 由 sum_n delta=0 恢复
  rows <- list()
  for (y in yrs[-1]) {
    dl <- sapply(1:4, function(n) fit$theta[sprintf("delta%d_%s", n, y)])
    rows[[as.character(y)]] <- data.table(crop = cr, year = y,
      factor = FN, delta = c(dl, -sum(dl)))
  }
  path <- rbindlist(rows)
  base <- data.table(crop = cr, year = yrs[1], factor = FN, delta = 0)
  path <- rbind(base, path)[order(factor, year)]
  fwrite(path, sprintf("out/bias_path_%s.csv", cr))
  path
}

# ---- 第二阶段：sb_n,tau^c = theta^c + sum_k psi_k dln(w_n/wbar)_{tau-k}^c + e ----
stage2 <- function(paths, panels) {
  # 品种层面 Törnqvist 全要素价格指数（分省按产量加权到品种）
  idx_rows <- list()
  for (cr in names(panels)) {
    p <- panels[[cr]]
    p[, wgt := q_output / sum(q_output), by = year]
    agg <- p[, c(lapply(.SD, function(x) sum(x * wgt)),
                 .(S_labor = sum(S_labor * wgt), S_mach = sum(S_mach * wgt),
                   S_fert = sum(S_fert * wgt), S_seed = sum(S_seed * wgt),
                   S_other = sum(S_other * wgt))),
             by = year, .SDcols = paste0("w_", FN)]
    setorder(agg, year)
    # Törnqvist: dln wbar = sum_n 0.5(S_t+S_t-1) dln w_n
    for (n in FN) agg[[paste0("dlw_", n)]] <- c(NA, diff(log(agg[[paste0("w_", n)]])))
    for (n in FN) agg[[paste0("sb_", n)]] <-
      (agg[[paste0("S_", n)]] + shift(agg[[paste0("S_", n)]])) / 2
    agg[, dln_wbar := Reduce(`+`, lapply(FN, function(n) get(paste0("sb_", n)) * get(paste0("dlw_", n))))]
    for (n in c("labor", "mach"))
      agg[[paste0("dlnrel_", n)]] <- agg[[paste0("dlw_", n)]] - agg$dln_wbar
    idx_rows[[cr]] <- agg[, .(crop = cr, year, dlnrel_labor, dlnrel_mach)]
  }
  relp <- rbindlist(idx_rows)
  # 年度节约偏向 sb_n = -(delta_n,tau - delta_n,tau-1)
  bias <- rbindlist(paths)[factor %in% c("labor", "mach")]
  setorder(bias, crop, factor, year)
  bias[, sb := -(delta - shift(delta)), by = .(crop, factor)]
  reg <- merge(bias[!is.na(sb)], relp, by = c("crop", "year"))
  out <- list()
  for (n in c("labor", "mach")) {
    rv <- paste0("dlnrel_", n)
    dd <- reg[factor == n]
    setorder(dd, crop, year)
    for (k in 1:3) dd[[paste0("L", k)]] <- dd[, shift(get(rv), k), by = crop]$V1
    for (k in 1:2) dd[[paste0("F", k)]] <- dd[, shift(get(rv), -k), by = crop]$V1
    dd <- dd[complete.cases(dd[, .(L1, L2, L3)])]
    f_main <- lm(sb ~ factor(crop) + L1 + L2 + L3, dd)
    dd2 <- dd[complete.cases(dd[, .(F1, F2)])]
    f_plac <- lm(sb ~ factor(crop) + L1 + L2 + L3 + F1 + F2, dd2)
    cs <- function(f, nm) if (nm %in% names(coef(f))) coef(summary(f))[nm, ] else rep(NA, 4)
    sumpsi <- sum(coef(f_main)[c("L1", "L2", "L3")])
    # 简单HC推断 + 累计响应Wald（Driscoll–Kraay留待品种数扩充后）
    V <- sandwich::vcovHC(f_main, type = "HC1")
    l <- names(coef(f_main)) %in% c("L1", "L2", "L3")
    se_sum <- sqrt(sum(V[l, l]))
    out[[n]] <- data.table(factor = n, n_obs = nrow(dd),
      psi1 = coef(f_main)["L1"], psi2 = coef(f_main)["L2"], psi3 = coef(f_main)["L3"],
      sum_psi = sumpsi, se_sum = se_sum, t_sum = sumpsi / se_sum,
      placebo_F1 = cs(f_plac, "F1")[1], placebo_F1_t = cs(f_plac, "F1")[3],
      placebo_F2 = cs(f_plac, "F2")[1], placebo_F2_t = cs(f_plac, "F2")[3])
  }
  rbindlist(out)
}

crops <- commandArgs(trailingOnly = TRUE)
if (!length(crops)) crops <- c("corn", "wheat", "soybean", "rice_japonica", "rice_mid_indica")
paths <- list(); panels <- list()
for (cr in crops) {
  cat("S2:", cr, "\n")
  paths[[cr]] <- s2_crop(cr)
  panels[[cr]] <- fread(sprintf("data/panel_%s.csv", cr))
}
ii <- stage2(paths, panels)
fwrite(ii, "out/induced_innovation.csv")
print(ii[, .(factor, n_obs, sum_psi = round(sum_psi, 3), t_sum = round(t_sum, 2),
             placebo_F1_t = round(placebo_F1_t, 2), placebo_F2_t = round(placebo_F2_t, 2))])
