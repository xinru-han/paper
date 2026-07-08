# robust_matrix.R — R2 稳健性重估矩阵（cc 基线规格的多重扰动）
# 覆盖：M3a plain/cc 对照、M3b κ 网格、M10 w_mach 构造年剔除、M11 仅原生xls年、
#       M12c 发改委三肥 Törnqvist 替代 w_fert、M13a 价格变异诊断、
#       M13b 区域×时期可积FE、M13c 剔除疫情年。
# 产出：out/{plaincc_compare,kappa_sensitivity,robust_wmach_years,robust_xlsonly,
#            robust_dropcovid,robust_regionperiod,robust_fertndrc,price_variation_diag,
#            robust_matrix}.csv
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R"); source("R/estimate.R")

CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica",
           "rice_early_indica","rice_late_indica","peanut","rapeseed")
FN <- c("labor","mach","fert","seed","other")
PB <- list(`2004-2008`=2004:2008,`2009-2014`=2009:2014,`2015-2019`=2015:2019,`2020-2024`=2020:2024)

# ---- 通用核心统计（给定 panel 与规格，返回核心弹性/偏向/凹性）--------------
core_stats <- function(pan, kappa = 1e6, extra_fe = NULL, method = "cc", a_init = NULL) {
  d <- prep_data(pan)
  sys <- tl_build_system(d, 4, extra_fe = extra_fe)
  So <- as.matrix(as.data.frame(d)[, paste0("S_", FN[1:4])]); So <- cbind(So, 1 - rowSums(So))
  if (method == "cc") {
    fit <- tl_itsur_c1(sys, 4, colMeans(So), S_obs = So, kappa = kappa, a_init = a_init)
    if (!fit$converged) return(NULL)
    G <- fit$Gamma_full
    lam <- { l <- fit$theta[sprintf("lambda_%dt", 1:4)]; c(l, -sum(l)) }
  } else {
    fit <- tl_itsur(sys); if (!fit$converged) return(NULL)
    rec <- tl_recover(fit, 4); G <- rec$Gamma; lam <- rec$lambda_nt
  }
  Shat <- tl_fitted_shares(fit, sys, 4); Sbar <- colMeans(Shat)
  el <- tl_elasticities(G, Sbar)
  concf <- mean(vapply(seq_len(nrow(Shat)), function(i) tl_concavity(G, Shat[i, ]), logical(1)))
  conco <- mean(vapply(seq_len(nrow(So)),   function(i) tl_concavity(G, So[i, ]),   logical(1)))
  mml_p <- sapply(PB, function(yy) { idx <- which(d$year %in% yy)
    if (!length(idx)) NA_real_ else tl_elasticities(G, colMeans(Shat[idx, , drop = FALSE]))$morishima[2, 1] })
  list(n = nrow(d), conc = concf, conc_obs = conco,
       eps_ll = el$eps[1, 1], eps_mm = el$eps[2, 2], eps_ff = el$eps[3, 3],
       M_ml = el$morishima[2, 1], M_lm = el$morishima[1, 2],
       B_labor = lam[1] / Sbar[1], B_mach = lam[2] / Sbar[2],
       mml_2024 = unname(mml_p["2020-2024"]), G = G, Sbar = Sbar,
       a = if (method == "cc") fit$a else NULL)
}

# 区域×时期 extra_fe（基期2004-08设NA，避免与省FE共线）
mk_regperiod <- function(pan) {
  perlab <- rep(NA_character_, nrow(pan))
  for (nm in names(PB)) perlab[pan$year %in% PB[[nm]]] <- nm
  ifelse(perlab == names(PB)[1], NA_character_, paste0(pan$region, "_", perlab))
}

# ---- M12c 发改委三肥 Törnqvist 化肥价格（尿素/二铵/氯基复合肥，等权=几何均值）--
build_fert_ndrc <- function() {
  nd <- fread("data/prices_ndrc_annual.csv", encoding = "UTF-8")
  ft <- dcast(nd[item %in% c("urea", "dap", "npk_cl")], province + year ~ item, value.var = "price")
  fill_series <- function(x, yr) { if (sum(!is.na(x)) >= 3) x <- exp(approx(yr[!is.na(x)], log(x[!is.na(x)]), xout = yr, rule = 2)$y); x }
  ft <- ft[order(province, year)]
  for (v in c("urea", "dap", "npk_cl")) ft[, (v) := fill_series(get(v), year), by = province]
  for (v in c("urea", "dap", "npk_cl")) { med <- ft[!is.na(get(v)), .(m = median(get(v))), by = year]
    ft <- merge(ft, med, by = "year", all.x = TRUE); ft[is.na(get(v)), (v) := m]; ft[, m := NULL] }
  ft[, w_fert_ndrc := (urea * dap * npk_cl)^(1/3)]   # 等权 Törnqvist=几何均值（子结构不可得）
  ft[, .(province, year, w_fert_ndrc)]
}

log_rows <- list(); add <- function(...) log_rows[[length(log_rows)+1]] <<- data.table(...)
row_of <- function(cr, variant, s) if (is.null(s)) NULL else data.table(crop=cr, variant=variant,
  n=s$n, conc=round(s$conc,3), conc_obs=round(s$conc_obs,3),
  eps_ll=round(s$eps_ll,3), eps_mm=round(s$eps_mm,3), M_ml=round(s$M_ml,3),
  M_lm=round(s$M_lm,3), B_labor=round(s$B_labor,4), mml_2024=round(s$mml_2024,3))

fert_ndrc <- build_fert_ndrc()
master <- list(); plaincc <- list(); kappa_rows <- list(); diag_rows <- list()

for (cr in CROPS) {
  cat("== robust_matrix:", cr, "==\n")
  pan <- fread(sprintf("data/panel_%s.csv", cr))

  # 基线（其凹性块 a 作后续所有 cc 变体的热启动种子，大幅提速）
  base <- core_stats(pan); master[[length(master)+1]] <- row_of(cr, "baseline_cc", base)
  a0 <- base$a

  # M3a plain vs cc：plain 凹性违反率（在拟合份额处）、约束触发观测数、点估计位移
  pl <- core_stats(pan, method = "plain")
  if (!is.null(pl) && !is.null(base)) {
    d <- prep_data(pan)
    # plain 在观测份额处的凹性违反数（cc 惩罚实际触发的观测）
    So <- as.matrix(as.data.frame(d)[, paste0("S_", FN[1:4])]); So <- cbind(So, 1 - rowSums(So))
    viol <- sum(!vapply(seq_len(nrow(So)), function(i) tl_concavity(pl$G, So[i, ]), logical(1)))
    plaincc[[length(plaincc)+1]] <- data.table(crop = cr, n = base$n,
      plain_conc_viol_rate = round(1 - pl$conc_obs, 3), n_constraint_trigger = viol,
      eps_ll_plain = round(pl$eps_ll, 3), eps_ll_cc = round(base$eps_ll, 3),
      d_eps_ll = round(base$eps_ll - pl$eps_ll, 3),
      eps_mm_plain = round(pl$eps_mm, 3), eps_mm_cc = round(base$eps_mm, 3),
      d_eps_mm = round(base$eps_mm - pl$eps_mm, 3),
      M_ml_plain = round(pl$M_ml, 3), M_ml_cc = round(base$M_ml, 3),
      d_M_ml = round(base$M_ml - pl$M_ml, 3))
  }

  # M3b κ 网格（1e6 复用基线；其余热启动）
  for (kp in c(1e4, 1e5, 1e6, 1e7)) {
    s <- if (kp == 1e6) base else core_stats(pan, kappa = kp, a_init = a0)
    if (!is.null(s)) kappa_rows[[length(kappa_rows)+1]] <- data.table(crop = cr, kappa = kp,
      conc = round(s$conc, 3), eps_ll = round(s$eps_ll, 3), eps_mm = round(s$eps_mm, 3),
      M_ml = round(s$M_ml, 3), B_labor = round(s$B_labor, 4))
  }

  # M10 剔 w_mach 构造年
  master[[length(master)+1]] <- row_of(cr, "wmach_years", core_stats(pan[!year %in% c(2004,2005,2011,2013,2024)], a_init = a0))
  # M11 仅原生 xls 年
  master[[length(master)+1]] <- row_of(cr, "xlsonly", core_stats(pan[year %in% c(2006:2018, 2024)], a_init = a0))
  # M13c 剔疫情
  master[[length(master)+1]] <- row_of(cr, "dropcovid", core_stats(pan[!year %in% 2020:2022], a_init = a0))
  # M13b 区域×时期可积FE
  master[[length(master)+1]] <- row_of(cr, "regionperiod", core_stats(pan, extra_fe = mk_regperiod(pan), a_init = a0))
  # M12c 发改委三肥替代 w_fert
  panf <- merge(pan, fert_ndrc, by = c("province","year"), all.x = TRUE)
  panf[!is.na(w_fert_ndrc), w_fert := w_fert_ndrc]
  master[[length(master)+1]] <- row_of(cr, "fert_ndrc", core_stats(panf, a_init = a0))

  # M13a 价格变异诊断：各 ln(w_m/w_other) 对年份哑变量 R² + 省内SD（daywage 与 hired）
  d <- prep_data(pan)
  for (m in 1:4) {
    lw <- log(pan[[paste0("w_", FN[m])]] / pan$w_other)
    r2 <- summary(lm(lw ~ factor(pan$year)))$r.squared
    within_sd <- mean(tapply(lw, pan$province, sd, na.rm = TRUE), na.rm = TRUE)
    diag_rows[[length(diag_rows)+1]] <- data.table(crop = cr, factor = FN[m], wage_def = "daywage",
      R2_year = round(r2, 3), within_prov_sd = round(within_sd, 3))
  }
  lwh <- log(pan$w_labor_hired / pan$w_other)
  diag_rows[[length(diag_rows)+1]] <- data.table(crop = cr, factor = "labor", wage_def = "hired",
    R2_year = round(summary(lm(lwh ~ factor(pan$year)))$r.squared, 3),
    within_prov_sd = round(mean(tapply(lwh, pan$province, sd, na.rm = TRUE), na.rm = TRUE), 3))
}

mst <- rbindlist(master, fill = TRUE)
fwrite(mst, "out/robust_matrix.csv")
fwrite(rbindlist(plaincc), "out/plaincc_compare.csv")
fwrite(rbindlist(kappa_rows), "out/kappa_sensitivity.csv")
fwrite(rbindlist(diag_rows), "out/price_variation_diag.csv")
# 拆分单变量对照（含基线列供比对）；指令文件名映射
bl <- mst[variant == "baseline_cc", .(crop, eps_ll_base = eps_ll, eps_mm_base = eps_mm, M_ml_base = M_ml, mml24_base = mml_2024)]
outname <- c(wmach_years="robust_wmach_years", xlsonly="robust_xlsonly", dropcovid="robust_dropcovid",
             regionperiod="robust_regionperiod", fert_ndrc="robust_fertndrc")
for (vn in names(outname)) {
  cmp <- merge(bl, mst[variant == vn], by = "crop")
  fwrite(cmp, sprintf("out/%s.csv", outname[vn]))
}

cat("\n== κ=1e6 vs 1e7 M_ml 收敛检查（应<0.02）==\n")
kd <- dcast(rbindlist(kappa_rows), crop ~ kappa, value.var = "M_ml")
kd[, d_67 := abs(get("1e+07") - get("1e+06"))]
print(kd[, .(crop, M_ml_1e6 = get("1e+06"), M_ml_1e7 = get("1e+07"), d_67 = round(d_67, 4))])
cat("max |ΔM_ml(1e6→1e7)| =", round(max(kd$d_67), 4), "\n")
cat("\n== plain/cc M_ml 位移 ==\n"); print(rbindlist(plaincc)[, .(crop, d_M_ml, n_constraint_trigger, plain_conc_viol_rate)])
cat("\n[robust_matrix] done\n")
