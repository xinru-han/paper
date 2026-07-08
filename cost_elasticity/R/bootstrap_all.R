# bootstrap_all.R — M1 全品种跨品种联合省级 block bootstrap（cc）
# 用法: Rscript R/bootstrap_all.R <B> <suffix: ""|_hw>
#   每个 draw 从 9 品种省份并集有放回抽一份"全国省名单"，各品种取该名单与自身省集
#   的交（含重复次数，重抽省作独立个体各自FE）后估 cc → 共享省份的跨品种相关性得以保留。
#   逐 draw 记 status ∈ {ok, fit_fail, prep_fail}；ok 率分母=全部尝试数。热启动加速。
# 产出: out/bootstrap_draws_all{suffix}_cc.csv, out/bootstrap_status{suffix}.csv,
#        out/crosscrop_Mml_ci{suffix}.csv, out/bootstrap_manifest{suffix}.csv
suppressMessages({library(data.table); library(parallel)})
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R"); source("R/estimate.R")

args <- commandArgs(trailingOnly = TRUE)
B_req <- if (length(args) >= 1) as.integer(args[1]) else 500
suffix <- if (length(args) >= 2) args[2] else ""
SEED <- 20260703
CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica",
           "rice_early_indica","rice_late_indica","peanut","rapeseed")
DRY <- c("corn","wheat","soybean","peanut","rapeseed")
RICE <- c("rice_japonica","rice_mid_indica","rice_early_indica","rice_late_indica")
FN <- c("labor","mach","fert","seed","other")
PB <- list(`2004-2008`=2004:2008,`2009-2014`=2009:2014,`2015-2019`=2015:2019,`2020-2024`=2020:2024)
ncores <- min(as.integer(Sys.getenv("BOOT_CORES","6")), detectCores()-1)

panels <- lapply(CROPS, function(cr) fread(sprintf("data/panel_%s%s.csv", cr, suffix)))
names(panels) <- CROPS
provs_union <- sort(unique(unlist(lapply(panels, function(p) unique(p$province)))))

# 全样本 cc 的凹性块 a（热启动种子）
a_full <- list()
for (cr in CROPS) {
  d <- prep_data(panels[[cr]]); sys <- tl_build_system(d, 4)
  So <- as.matrix(as.data.frame(d)[, paste0("S_", FN[1:4])]); So <- cbind(So, 1 - rowSums(So))
  a_full[[cr]] <- tl_itsur_c1(sys, 4, colMeans(So), S_obs = So, kappa = 1e6)$a
}

crop_boot <- function(pan_bs, cr, b) {
  d <- prep_data(pan_bs); sys <- tl_build_system(d, 4)
  So <- as.matrix(as.data.frame(d)[, paste0("S_", FN[1:4])]); So <- cbind(So, 1 - rowSums(So))
  fit <- tryCatch(tl_itsur_c1(sys, 4, colMeans(So), S_obs = So, kappa = 1e6, a_init = a_full[[cr]]),
                  error = function(e) NULL)
  if (is.null(fit) || !fit$converged) return(data.table(draw = b, crop = cr, period = "all", status = "fit_fail"))
  G <- fit$Gamma_full; th <- fit$theta
  lam <- { l <- th[sprintf("lambda_%dt",1:4)]; c(l, -sum(l)) }
  Shat <- tl_fitted_shares(fit, sys, 4)
  lnw <- as.matrix(d[, sprintf("lnw_%d",1:4), with = FALSE])
  tauC_obs <- th["lambda_t"] + th["lambda_tt"]*d$tt +
    as.numeric(lnw %*% th[sprintf("lambda_%dt",1:4)]) + th["lambda_yt"]*d$lny   # M4 对偶技术率
  rows <- list()
  for (pn in c("all", names(PB))) {
    idx <- if (pn == "all") seq_len(nrow(d)) else which(d$year %in% PB[[pn]]); if (!length(idx)) next
    Sb <- colMeans(Shat[idx, , drop = FALSE]); el <- tl_elasticities(G, Sb)
    rows[[pn]] <- data.table(draw = b, crop = cr, period = pn, status = "ok",
      eps_ll = el$eps[1,1], eps_mm = el$eps[2,2], eps_ff = el$eps[3,3],
      M_ml = el$morishima[2,1], M_lm = el$morishima[1,2],
      B_labor = lam[1]/Sb[1], B_mach = lam[2]/Sb[2], tauC = mean(tauC_obs[idx]))
  }
  rbindlist(rows, fill = TRUE)
}

set.seed(SEED)
draw_provs <- lapply(1:B_req, function(b) sample(provs_union, length(provs_union), replace = TRUE))

one_draw <- function(b) {
  sp <- draw_provs[[b]]; out <- list()
  for (cr in CROPS) {
    own <- unique(panels[[cr]]$province)
    keep <- sp[sp %in% own]                       # 含重复次数
    if (length(unique(keep)) < 4) { out[[cr]] <- data.table(draw = b, crop = cr, period = "all", status = "prep_fail"); next }
    dl <- lapply(seq_along(keep), function(i) { x <- copy(panels[[cr]][province == keep[i]]); x$province <- sprintf("bs%03d", i); x })
    out[[cr]] <- crop_boot(rbindlist(dl), cr, b)
  }
  rbindlist(out, fill = TRUE)
}

# 运行时守门：先测 1 draw，投影总时长；>24h 则按比例降 B（下限 250）
t1 <- system.time(d1 <- one_draw(1))["elapsed"]
proj_h <- B_req * t1 / ncores / 3600
B <- B_req
if (proj_h > 24) { B <- max(250L, as.integer(24 * ncores * 3600 / t1)); cat(sprintf("[guard] proj %.1fh>24h → B %d→%d\n", proj_h, B_req, B)) }
cat(sprintf("[manifest] per-draw=%.1fs cores=%d B=%d proj=%.2fh\n", t1, ncores, B, B * t1 / ncores / 3600))

res <- mclapply(1:B, one_draw, mc.cores = ncores)
dt <- rbindlist(Filter(is.data.table, res), fill = TRUE)
fwrite(dt, sprintf("out/bootstrap_draws_all%s_cc.csv", suffix))

# 状态汇总（分母=全部尝试 = B×9）
st <- dt[period == "all" | status != "ok", .(n = uniqueN(draw)), by = .(crop, status)]
status <- dcast(st, crop ~ status, value.var = "n", fill = 0)
status[, attempts := B]
status[, ok_rate := round(get("ok") / B, 3)]
fwrite(status, sprintf("out/bootstrap_status%s.csv", suffix))

# 每品种 period=all 的 percentile CI
okall <- dt[status == "ok" & period == "all"]
ci <- okall[, .(eps_ll = sprintf("%.3f [%.3f, %.3f]", median(eps_ll), quantile(eps_ll,.025), quantile(eps_ll,.975)),
                eps_mm = sprintf("%.3f [%.3f, %.3f]", median(eps_mm), quantile(eps_mm,.025), quantile(eps_mm,.975)),
                M_ml   = sprintf("%.3f [%.3f, %.3f]", median(M_ml),   quantile(M_ml,.025),   quantile(M_ml,.975)),
                B_labor= sprintf("%.4f [%.4f, %.4f]", median(B_labor),quantile(B_labor,.025),quantile(B_labor,.975))),
             by = crop]
fwrite(ci, sprintf("out/bootstrap_ci%s_cc.csv", suffix))

# 跨品种 M_ml 差异 CI（同 draw 配对）+ 旱作组均值−稻作组均值
wide <- dcast(okall, draw ~ crop, value.var = "M_ml")
pair_rows <- list()
for (i in 1:(length(CROPS)-1)) for (j in (i+1):length(CROPS)) {
  a <- CROPS[i]; bb <- CROPS[j]; dd <- wide[[a]] - wide[[bb]]; dd <- dd[is.finite(dd)]
  pair_rows[[length(pair_rows)+1]] <- data.table(a = a, b = bb, med = median(dd),
    lo = quantile(dd,.025), hi = quantile(dd,.975), excl0 = (quantile(dd,.025) > 0 | quantile(dd,.975) < 0))
}
dry_mean <- rowMeans(wide[, ..DRY], na.rm = TRUE); rice_mean <- rowMeans(wide[, ..RICE], na.rm = TRUE)
gd <- dry_mean - rice_mean; gd <- gd[is.finite(gd)]
grp <- data.table(a = "DRY_mean", b = "RICE_mean", med = median(gd), lo = quantile(gd,.025), hi = quantile(gd,.975),
                  excl0 = (quantile(gd,.025) > 0 | quantile(gd,.975) < 0))
fwrite(rbind(rbindlist(pair_rows), grp), sprintf("out/crosscrop_Mml_ci%s.csv", suffix))

fwrite(data.table(suffix = suffix, B_req = B_req, B_used = B, per_draw_s = round(t1,1),
                  cores = ncores, seed = SEED, provs_union = length(provs_union)),
       sprintf("out/bootstrap_manifest%s.csv", suffix))

cat(sprintf("\n[bootstrap_all%s] done: B=%d\n", suffix, B))
print(status); cat("\n"); print(ci)
cat("\n旱作−稻作 M_ml 差异:", sprintf("%.3f [%.3f, %.3f] excl0=%s", grp$med, grp$lo, grp$hi, grp$excl0), "\n")
