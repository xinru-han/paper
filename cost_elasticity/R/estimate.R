# estimate.R — translog成本系统 ITSUR 估计 + post-estimation
# 用法: Rscript R/estimate.R [crop1 crop2 ...]  缺省=corn
# 产出: out/params_{crop}.csv, out/fitted_shares_{crop}.csv, out/elasticities_{crop}.csv,
#       out/tests_{crop}.csv, out/bias_{crop}.csv, out/concavity_{crop}.csv, out/scale_tfp_{crop}.csv
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R")

FACTORS <- c("labor", "mach", "fert", "seed", "other")   # other = numeraire
K <- 4; N <- 5
PERIODS <- list(`2004-2008` = 2004:2008, `2009-2014` = 2009:2014,
                `2015-2019` = 2015:2019, `2020-2024` = 2020:2024)

prep_data <- function(pan) {
  d <- as.data.table(pan)
  for (n in 1:K)
    d[[sprintf("lnw_%d", n)]] <- log(d[[paste0("w_", FACTORS[n])]] / d$w_other)
  d$lny <- log(d$q_output)
  d$lnC <- log(d$C_var / d$w_other)
  # 中心化（样本几何均值归一化）
  ctr <- c(sprintf("lnw_%d", 1:K), "lny", "lnC")
  centers <- sapply(ctr, function(v) mean(d[[v]]))
  for (v in ctr) d[[v]] <- d[[v]] - centers[v]
  d$tt <- d$year - 2014
  for (n in 1:K) d[[sprintf("S_%d", n)]] <- d[[paste0("S_", FACTORS[n])]]
  d$prov <- d$province
  attr(d, "centers") <- centers
  d
}

# method: "plain" 无约束ITSUR（LR检验、参照）；"cc" 曲率约束（惩罚κ=1e6，基线弹性）
fit_crop <- function(cr, write_out = TRUE, method = "plain", kappa = 1e6) {
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  d <- prep_data(pan)
  sys <- tl_build_system(d, K)
  if (method == "cc") {
    Sobs <- as.matrix(as.data.frame(d)[, paste0("S_", FACTORS[1:K])])
    Sobs <- cbind(Sobs, 1 - rowSums(Sobs))
    fit <- tl_itsur_c1(sys, K, colMeans(Sobs), S_obs = Sobs, kappa = kappa)
    stopifnot(fit$converged)
    rec <- list(Gamma = fit$Gamma_full,
                lambda_nt = { l <- fit$theta[sprintf("lambda_%dt", 1:K)]; c(l, -sum(l)) })
  } else {
    fit <- tl_itsur(sys)
    stopifnot(fit$converged)
    rec <- tl_recover(fit, K)
  }

  # 不变性检验（仅plain）：换 numeraire（用 seed）重估，完整Gamma应一致
  inv_err <- NA_real_
  if (method == "plain") {
    d2 <- copy(d)
    perm <- c(1, 2, 3, 5, 4)  # labor mach fert other | seed 为numeraire
    wmat <- as.matrix(pan[, paste0("w_", FACTORS), with = FALSE])
    Smat <- as.matrix(pan[, paste0("S_", FACTORS), with = FALSE])
    for (m in 1:K) {
      x <- log(wmat[, perm[m]] / wmat[, perm[N]])
      d2[[sprintf("lnw_%d", m)]] <- x - mean(x)
      d2[[sprintf("S_%d", m)]] <- Smat[, perm[m]]
    }
    x <- log(pan$C_var / wmat[, perm[N]]); d2$lnC <- x - mean(x)
    fit2 <- tl_itsur(tl_build_system(d2, K))
    G2 <- tl_recover(fit2, K)$Gamma[order(perm), order(perm)]
    inv_err <- max(abs(G2 - rec$Gamma))
    stopifnot(inv_err < 1e-4)
  }

  # 拟合份额与凹性/单调性
  Shat <- tl_fitted_shares(fit, sys, K)
  mono_ok <- rowSums(Shat > 0) == N
  conc_ok <- vapply(seq_len(nrow(Shat)), function(i) tl_concavity(rec$Gamma, Shat[i, ]), logical(1))

  # 弹性：分时期在时期均值拟合份额处评估 + 全样本
  eval_points <- c(list(all = seq_len(nrow(d))),
                   lapply(PERIODS, function(yy) which(d$year %in% yy)))
  el_rows <- list()
  for (pn in names(eval_points)) {
    idx <- eval_points[[pn]]; if (!length(idx)) next
    Sbar <- colMeans(Shat[idx, , drop = FALSE])
    el <- tl_elasticities(rec$Gamma, Sbar)
    for (n in 1:N) for (m in 1:N)
      el_rows[[length(el_rows) + 1]] <- data.table(
        crop = cr, period = pn, f_n = FACTORS[n], f_m = FACTORS[m],
        S_n = Sbar[n], eps = el$eps[n, m], allen = el$allen[n, m], morishima = el$morishima[n, m])
  }
  el_dt <- rbindlist(el_rows)

  # 技术偏向
  Sbar_all <- colMeans(Shat)
  bias <- data.table(crop = cr, factor = FACTORS, lambda_nt = rec$lambda_nt,
                     S_mean = Sbar_all, B = rec$lambda_nt / Sbar_all)

  # 规模弹性与技术变迁率（逐观测，再按年汇总）
  th <- fit$theta
  lnw <- as.matrix(d[, sprintf("lnw_%d", 1:K), with = FALSE])
  eCy <- th["alpha_y"] + th["gamma_yy"] * d$lny +
    as.numeric(lnw %*% th[sprintf("gamma_%dy", 1:K)]) + th["lambda_yt"] * d$tt
  tauC <- th["lambda_t"] + th["lambda_tt"] * d$tt +
    as.numeric(lnw %*% th[sprintf("lambda_%dt", 1:K)]) + th["lambda_yt"] * d$lny
  scale_dt <- data.table(crop = cr, year = d$year, eCy = eCy, RTS = 1 / eCy,
                         tauC = tauC, TFP = -tauC / eCy)[
    , lapply(.SD, mean), by = .(crop, year)][order(year)]

  # LR 检验（仅plain：cc为惩罚估计，非ML）
  tests <- NULL
  if (method == "plain") {
    lr <- function(drop, name, df) {
      f0 <- tl_itsur(sys, drop_params = drop)
      data.table(crop = cr, test = name, LR = 2 * (fit$logLik - f0$logLik), df = df,
                 p = pchisq(2 * (fit$logLik - f0$logLik), df, lower.tail = FALSE))
    }
    tests <- rbindlist(list(
      lr("^gamma_[1-4]y$", "homotheticity", K),
      lr("^lambda_[1-4]t$", "hicks_neutral", K),
      lr("^lambda_", "no_tech_change", K + 3),
      lr("^gamma_[1-4]_[1-4]$", "cobb_douglas", K * (K + 1) / 2)))
  }

  res <- list(crop = cr, fit = fit, rec = rec, d = d, sys = sys,
              conc_rate = mean(conc_ok), mono_rate = mean(mono_ok), inv_err = inv_err,
              el = el_dt, bias = bias, tests = tests, scale = scale_dt, Shat = Shat)
  if (write_out) {
    suf <- if (method == "cc") paste0(cr, "_cc") else cr
    G <- rec$Gamma; dimnames(G) <- list(FACTORS, FACTORS)
    se <- if (!is.null(fit$vcov)) sqrt(pmax(diag(fit$vcov), 0)) else NA_real_
    fwrite(data.table(param = names(fit$theta), est = fit$theta, se_delta = se),
           sprintf("out/params_%s.csv", suf))
    fwrite(as.data.table(G, keep.rownames = "factor"), sprintf("out/gamma_%s.csv", suf))
    fwrite(cbind(d[, .(province, year)], as.data.table(setNames(as.data.frame(Shat), paste0("Shat_", FACTORS))),
                 as.data.table(setNames(as.data.frame(cbind(d[[ "S_1"]], d$S_2, d$S_3, d$S_4)), paste0("Sobs_", FACTORS[1:4]))),
                 mono_ok = mono_ok, conc_ok = conc_ok),
           sprintf("out/fitted_shares_%s.csv", suf))
    fwrite(el_dt, sprintf("out/elasticities_%s.csv", suf))
    fwrite(bias, sprintf("out/bias_%s.csv", suf))
    if (!is.null(tests)) fwrite(tests, sprintf("out/tests_%s.csv", suf))
    fwrite(scale_dt, sprintf("out/scale_tfp_%s.csv", suf))
    fwrite(data.table(crop = cr, method = method, n_obs = nrow(d), n_prov = uniqueN(d$prov),
                      iter = fit$iter, converged = fit$converged, inv_err = inv_err,
                      concavity_rate = mean(conc_ok), monotonicity_rate = mean(mono_ok)),
           sprintf("out/concavity_%s.csv", suf))
  }
  res
}

this_file <- sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))
if (length(this_file) && basename(this_file) == "estimate.R") {
  args <- commandArgs(trailingOnly = TRUE)
  methods <- intersect(args, c("plain", "cc"))
  crops <- setdiff(args, methods)
  if (!length(crops)) crops <- "corn"
  if (!length(methods)) methods <- c("plain", "cc")
  for (cr in crops) for (mt in methods) {
    cat(sprintf("\n===== %s [%s] =====\n", cr, mt))
    r <- fit_crop(cr, method = mt)
    cat(sprintf("n=%d, iter=%d, invariance=%.2e, concavity=%.1f%%, monotonicity=%.1f%%\n",
                nrow(r$d), r$fit$iter, r$inv_err, 100 * r$conc_rate, 100 * r$mono_rate))
    cat("\n-- own-price eps --\n")
    print(r$el[period == "all" & f_n == f_m, .(f_n, S_n = round(S_n, 3), eps = round(eps, 3))])
    cat("-- Morishima (all) --\n")
    print(dcast(r$el[period == "all"], f_n ~ f_m, value.var = "morishima"), digits = 3)
    cat("-- tech bias --\n"); print(r$bias[, .(factor, lambda_nt = round(lambda_nt, 5), B = round(B, 4))])
    if (!is.null(r$tests)) { cat("-- LR tests --\n")
      print(r$tests[, .(test, LR = round(LR, 1), df, p = signif(p, 3))]) }
  }
}
