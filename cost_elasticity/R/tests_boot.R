# tests_boot.R — M9：省级 block bootstrap 化 LR（省内序列相关下 iid χ² 会膨胀，F-6）
#   玉米四项检验 + 小麦位似性(边界 p=0.0696) + M6 断点检验（玉米+粳稻，M6b）。
#   其余品种保留解析 p（表注"iid 假设下"）。B=200 省级整省重抽，重估无/有约束 plain。
# 产出: out/tests_boot.csv
suppressMessages({library(data.table); library(parallel)})
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/estimate.R")
SEED <- 20260703; B <- 200
ncores <- min(as.integer(Sys.getenv("BOOT_CORES","6")), detectCores()-1)

TESTS <- list(
  list(crop="corn",  name="homotheticity",  drop="^gamma_[1-4]y$",        df=4,  brk=FALSE),
  list(crop="corn",  name="hicks_neutral",  drop="^lambda_[1-4]t$",       df=4,  brk=FALSE),
  list(crop="corn",  name="no_tech_change", drop="^lambda_",              df=7,  brk=FALSE),
  list(crop="corn",  name="cobb_douglas",   drop="^gamma_[1-4]_[1-4]$",   df=10, brk=FALSE),
  list(crop="wheat", name="homotheticity",  drop="^gamma_[1-4]y$",        df=4,  brk=FALSE),
  list(crop="corn",          name="gamma_break", drop="^dgamma_",         df=10, brk=TRUE),
  list(crop="rice_japonica", name="gamma_break", drop="^dgamma_",         df=10, brk=TRUE))

one_LR <- function(pan, drop, brk, b, provs) {
  set.seed(SEED + b)
  sp <- sample(provs, length(provs), replace = TRUE)
  dl <- lapply(seq_along(sp), function(i) { x <- copy(pan[province == sp[i]]); x$province <- sprintf("bs%03d", i); x })
  d <- prep_data(rbindlist(dl))
  sys <- tl_build_system(d, 4, gamma_break = brk)
  f1 <- tryCatch(tl_itsur(sys), error = function(e) NULL)
  f0 <- tryCatch(tl_itsur(sys, drop_params = drop), error = function(e) NULL)
  if (is.null(f1) || is.null(f0) || !f1$converged || !f0$converged) return(NA_real_)
  2 * (f1$logLik - f0$logLik)
}

rows <- list()
for (tst in TESTS) {
  pan <- fread(sprintf("data/panel_%s.csv", tst$crop)); provs <- unique(pan$province)
  # 观测 LR（全样本 plain）
  d <- prep_data(pan); sys <- tl_build_system(d, 4, gamma_break = tst$brk)
  f1 <- tl_itsur(sys); f0 <- tl_itsur(sys, drop_params = tst$drop)
  LR_obs <- 2 * (f1$logLik - f0$logLik); p_an <- pchisq(LR_obs, tst$df, lower.tail = FALSE)
  crit <- qchisq(0.95, tst$df)
  bl <- unlist(mclapply(1:B, function(b) one_LR(pan, tst$drop, tst$brk, b, provs), mc.cores = ncores))
  bl <- bl[is.finite(bl)]
  # bootstrap 非拒绝率（LR 落在解析5%临界值以下的比例）作为稳健性读数
  boot_nonreject <- mean(bl < crit)
  rows[[length(rows)+1]] <- data.table(crop = tst$crop, test = tst$name, df = tst$df,
    LR_obs = round(LR_obs,2), p_analytic = signif(p_an,3), crit5 = round(crit,2),
    boot_n = length(bl), boot_LR_median = round(median(bl),1),
    boot_LR_lo = round(quantile(bl,.025),1), boot_LR_hi = round(quantile(bl,.975),1),
    boot_nonreject_rate = round(boot_nonreject,3))
  cat(sprintf("%s/%s: LR=%.1f p_an=%.3g bootLR med=%.1f [%.1f,%.1f] nonrej=%.3f\n",
      tst$crop, tst$name, LR_obs, p_an, median(bl), quantile(bl,.025), quantile(bl,.975), boot_nonreject))
}
fwrite(rbindlist(rows), "out/tests_boot.csv")
cat("\n[tests_boot] done\n")
