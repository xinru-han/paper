# bootstrap.R — 省份 block bootstrap（整省重抽，plan §3.3）
# 用法: Rscript R/bootstrap.R <crop> <B> <method: plain|c1>
# 产出: out/bootstrap_draws_{crop}[_c1].csv（每draw的弹性/偏向统计量）、draw级诊断
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R"); source("R/estimate.R")

args <- commandArgs(trailingOnly = TRUE)
cr <- ifelse(length(args) >= 1, args[1], "corn")
B <- ifelse(length(args) >= 2, as.integer(args[2]), 200)
method <- ifelse(length(args) >= 3, args[3], "plain")
set.seed(20260703)

pan <- fread(sprintf("data/panel_%s.csv", cr))
provs <- unique(pan$province)
FN <- c("labor", "mach", "fert", "seed", "other")

one_draw <- function(b) {
  ps <- sample(provs, length(provs), replace = TRUE)
  dl <- lapply(seq_along(ps), function(i) {
    x <- pan[province == ps[i]]
    x$province <- sprintf("bs%02d_%s", i, ps[i])   # 重抽省作为独立个体（各自FE）
    x
  })
  pb <- rbindlist(dl)
  d <- prep_data(pb)
  sys <- tl_build_system(d, 4)
  fit <- tryCatch({
    if (method == "c1") {
      Sb <- colMeans(as.data.frame(d)[, paste0("S_", FN[1:4])]); Sb <- c(Sb, 1 - sum(Sb))
      f <- tl_itsur_c1(sys, 4, Sb); f$Gamma <- f$Gamma_full; f
    } else {
      f <- tl_itsur(sys); f$Gamma <- tl_recover(f, 4)$Gamma; f
    }
  }, error = function(e) NULL)
  if (is.null(fit) || !fit$converged) return(data.table(draw = b, ok = FALSE))
  G <- fit$Gamma
  Shat <- tl_fitted_shares(fit, sys, 4)
  conc <- mean(vapply(seq_len(nrow(Shat)), function(i) tl_concavity(G, Shat[i, ]), logical(1)))
  lam <- fit$theta[sprintf("lambda_%dt", 1:4)]; lam <- c(lam, -sum(lam))
  rows <- list()
  for (pn in c("all", names(PERIODS))) {
    idx <- if (pn == "all") seq_len(nrow(d)) else which(d$year %in% PERIODS[[pn]])
    if (!length(idx)) next
    el <- tl_elasticities(G, colMeans(Shat[idx, , drop = FALSE]))
    rows[[pn]] <- data.table(draw = b, ok = TRUE, period = pn, conc_rate = conc,
      eps_ll = el$eps[1, 1], eps_mm = el$eps[2, 2], eps_ff = el$eps[3, 3],
      eps_ss = el$eps[4, 4], eps_oo = el$eps[5, 5],
      M_ml = el$morishima[2, 1], M_lm = el$morishima[1, 2],
      M_fl = el$morishima[3, 1], M_lf = el$morishima[1, 3],
      B_labor = lam[1] / mean(Shat[idx, 1]), B_mach = lam[2] / mean(Shat[idx, 2]),
      B_fert = lam[3] / mean(Shat[idx, 3]), B_seed = lam[4] / mean(Shat[idx, 4]),
      B_other = lam[5] / mean(Shat[idx, 5]))
  }
  rbindlist(rows, fill = TRUE)
}

res <- list()
t0 <- Sys.time()
for (b in 1:B) {
  res[[b]] <- one_draw(b)
  if (b %% 25 == 0) cat(sprintf("[boot %s %s] %d/%d (%.1f min)\n", cr, method, b, B,
                                as.numeric(difftime(Sys.time(), t0, units = "mins"))))
}
dt <- rbindlist(res, fill = TRUE)
suf <- ifelse(method == "c1", "_c1", "")
fwrite(dt, sprintf("out/bootstrap_draws_%s%s.csv", cr, suf))
okr <- dt[period == "all" | is.na(period), mean(ok)]
cat(sprintf("done: %d draws, ok rate %.3f\n", B, okr))
qs <- dt[ok == TRUE & period == "all",
         lapply(.SD, function(x) sprintf("%.3f [%.3f, %.3f]", median(x),
                quantile(x, .025), quantile(x, .975))),
         .SDcols = c("eps_ll", "eps_mm", "M_ml", "M_lm", "B_labor", "B_mach")]
print(t(qs))
