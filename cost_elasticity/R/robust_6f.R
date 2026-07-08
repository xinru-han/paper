# robust_6f.R — 6要素稳健性（含土地）：labor, mach, fert, seed, land, other(numeraire)
# w_land = 土地成本/亩（流转地租金+自营地折租；土地投入量=1亩，价格=亩租金）
# C6 = C_var + cost_land；份额按C6重算；估计用cc曲率惩罚（与基线一致）
# 用法: Rscript R/robust_6f.R [crop1 crop2 ...]  缺省=9品种
# 产出: out/robust6f_{crop}.csv（弹性）、out/robust6f_compare.csv（与5要素基线对比）
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R")

FACTORS6 <- c("labor", "mach", "fert", "seed", "land", "other")
K <- 5; N <- 6

prep6 <- function(pan) {
  d <- as.data.table(pan)
  d <- d[is.finite(cost_land) & cost_land > 0]
  d[, C6 := C_var + cost_land]
  d[, w_land := cost_land]                       # 元/亩，数量=1
  for (n in FACTORS6) d[[paste0("S6_", n)]] <-
    (if (n == "land") d$cost_land else d[[paste0("cost_", n)]]) / d$C6
  stopifnot(max(abs(rowSums(as.matrix(d[, paste0("S6_", FACTORS6), with = FALSE])) - 1)) < 1e-8)
  for (n in 1:K)
    d[[sprintf("lnw_%d", n)]] <- log(d[[paste0("w_", FACTORS6[n])]] / d$w_other)
  d$lny <- log(d$q_output)
  d$lnC <- log(d$C6 / d$w_other)
  ctr <- c(sprintf("lnw_%d", 1:K), "lny", "lnC")
  for (v in ctr) d[[v]] <- d[[v]] - mean(d[[v]])
  d$tt <- d$year - 2014
  for (n in 1:K) d[[sprintf("S_%d", n)]] <- d[[paste0("S6_", FACTORS6[n])]]
  d$prov <- d$province
  d
}

fit6 <- function(cr) {
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  d <- prep6(pan)
  sys <- tl_build_system(d, K)
  Sobs <- as.matrix(as.data.frame(d)[, paste0("S6_", FACTORS6[1:K])])
  Sobs <- cbind(Sobs, 1 - rowSums(Sobs))
  fit <- tl_itsur_c1(sys, K, colMeans(Sobs), S_obs = Sobs, kappa = 1e6)
  stopifnot(fit$converged)
  G <- fit$Gamma_full
  lam <- fit$theta[sprintf("lambda_%dt", 1:K)]; lam <- c(lam, -sum(lam))
  Shat <- tl_fitted_shares(fit, sys, K)
  conc <- mean(vapply(seq_len(nrow(Shat)), function(i) tl_concavity(G, Shat[i, ]), logical(1)))
  mono <- mean(rowSums(Shat > 0) == N)
  Sbar <- colMeans(Shat)
  el <- tl_elasticities(G, Sbar)
  rows <- rbindlist(lapply(1:N, function(n) rbindlist(lapply(1:N, function(m)
    data.table(crop = cr, f_n = FACTORS6[n], f_m = FACTORS6[m], S_n = Sbar[n],
               eps = el$eps[n, m], morishima = el$morishima[n, m])))))
  fwrite(rows, sprintf("out/robust6f_%s.csv", cr))
  fwrite(data.table(crop = cr, factor = FACTORS6, lambda_nt = lam, S_mean = Sbar, B = lam / Sbar),
         sprintf("out/bias6f_%s.csv", cr))   # M7 偏向一致性用
  list(crop = cr, n = nrow(d), n_drop_land = nrow(pan) - nrow(d),
       conc = conc, mono = mono, el = el, Sbar = Sbar, lam = lam, rows = rows)
}

main <- function(crops) {
  cmp <- list()
  for (cr in crops) {
    cat(sprintf("\n===== %s [6f cc] =====\n", cr))
    r <- tryCatch(fit6(cr), error = function(e) { cat("!!", conditionMessage(e), "\n"); NULL })
    if (is.null(r)) next
    cat(sprintf("n=%d (land-drop %d), concavity=%.1f%%, monotonicity=%.1f%%\n",
                r$n, r$n_drop_land, 100 * r$conc, 100 * r$mono))
    own6 <- r$rows[f_n == f_m, .(f_n, eps = round(eps, 3))]
    print(own6)
    b5 <- fread(sprintf("out/elasticities_%s_cc.csv", cr))[period == "all"]
    cmp[[cr]] <- data.table(
      crop = cr, n6 = r$n, conc6 = r$conc,
      eps_ll_5f = round(b5[f_n == "labor" & f_m == "labor", eps], 3),
      eps_ll_6f = round(r$el$eps[1, 1], 3),
      eps_mm_5f = round(b5[f_n == "mach" & f_m == "mach", eps], 3),
      eps_mm_6f = round(r$el$eps[2, 2], 3),
      M_ml_5f = round(b5[f_n == "mach" & f_m == "labor", morishima], 3),
      M_ml_6f = round(r$el$morishima[2, 1], 3),
      eps_land_6f = round(r$el$eps[5, 5], 3),
      S_land = round(r$Sbar[5], 3),
      B_labor_6f = round(r$lam[1] / r$Sbar[1], 4))
    cat(sprintf("M_ML: 5f=%.3f  6f=%.3f | eps_ll: 5f=%.3f 6f=%.3f | eps_land=%.3f (S_land=%.2f)\n",
                cmp[[cr]]$M_ml_5f, cmp[[cr]]$M_ml_6f, cmp[[cr]]$eps_ll_5f,
                cmp[[cr]]$eps_ll_6f, cmp[[cr]]$eps_land_6f, cmp[[cr]]$S_land))
  }
  cmpdt <- rbindlist(cmp)
  fwrite(cmpdt, "out/robust6f_compare.csv")
  cat("\n== 5f vs 6f comparison ==\n"); print(cmpdt)
}

this_file <- sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))
if (length(this_file) && basename(this_file) == "robust_6f.R") {
  a <- commandArgs(trailingOnly = TRUE)
  if (!length(a)) a <- c("corn", "wheat", "soybean", "rice_japonica", "rice_mid_indica",
                         "rice_early_indica", "rice_late_indica", "peanut", "rapeseed")
  main(a)
}
