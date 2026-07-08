# gamma_break.R — M6 H1 正面检验：Γ 结构断点（2004–13 vs 2014–24）+ 决策门 G3
#  (b) LR 检验 H0: Δγ=0（df=10，plain），全品种；(c) 分半样本独立 cc 在共同评估点比 M_ML；
#  (d) 附加 Δλ_nt 断点（分半 λ_nt/份额偏向是否 2014 后加速）。
#  注：玉米+粳稻的省级 block bootstrap 化 LR p 值在 M9 tests_boot（R4）产出。
# 产出：out/gamma_break_test.csv, out/elasticities_split_{crop}.csv, out/gamma_break_G3.csv
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R"); source("R/estimate.R")

CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica",
           "rice_early_indica","rice_late_indica","peanut","rapeseed")
FN <- c("labor","mach","fert","seed","other")
BREAK <- 2014

cc_fit <- function(pan) {
  d <- prep_data(pan); sys <- tl_build_system(d, 4)
  So <- as.matrix(as.data.frame(d)[, paste0("S_", FN[1:4])]); So <- cbind(So, 1 - rowSums(So))
  fit <- tl_itsur_c1(sys, 4, colMeans(So), S_obs = So, kappa = 1e6)
  lam <- { l <- fit$theta[sprintf("lambda_%dt",1:4)]; c(l, -sum(l)) }
  Shat <- tl_fitted_shares(fit, sys, 4)
  list(fit = fit, G = fit$Gamma_full, lam = lam, Shat = Shat, d = d, converged = fit$converged)
}

test_rows <- list(); g3_rows <- list()
for (cr in CROPS) {
  cat("gamma_break:", cr, "\n")
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  d <- prep_data(pan)
  # (b) plain 断点 LR
  sysB <- tl_build_system(d, 4, gamma_break = TRUE)
  fB <- tl_itsur(sysB); f0 <- tl_itsur(sysB, drop_params = "^dgamma_")
  LR <- 2 * (fB$logLik - f0$logLik); p_an <- pchisq(LR, 10, lower.tail = FALSE)

  # (c) 分半样本独立 cc；共同评估点 = 全样本 cc 拟合份额均值
  full <- cc_fit(pan)
  Sbar_common <- colMeans(full$Shat)
  pre  <- cc_fit(pan[year <  BREAK]); post <- cc_fit(pan[year >= BREAK])
  mml_pre  <- tl_elasticities(pre$G,  Sbar_common)$morishima[2,1]
  mml_post <- tl_elasticities(post$G, Sbar_common)$morishima[2,1]
  ell_pre  <- tl_elasticities(pre$G,  Sbar_common)$eps[1,1]
  ell_post <- tl_elasticities(post$G, Sbar_common)$eps[1,1]
  # (d) Δλ：分半偏向 B_labor（λ_labor/份额），是否 2014 后加速（更负）
  Bl_pre  <- pre$lam[1]  / mean(pre$Shat[,1])
  Bl_post <- post$lam[1] / mean(post$Shat[,1])

  # 分半弹性落盘
  esp <- rbindlist(list(
    data.table(crop=cr, seg="2004-2013", eps_ll=ell_pre,  M_ml=mml_pre,  B_labor=Bl_pre,  n=nrow(pan[year<BREAK])),
    data.table(crop=cr, seg="2014-2024", eps_ll=ell_post, M_ml=mml_post, B_labor=Bl_post, n=nrow(pan[year>=BREAK]))))
  fwrite(esp, sprintf("out/elasticities_split_%s.csv", cr))

  test_rows[[cr]] <- data.table(crop = cr, LR = round(LR,2), df = 10, p_analytic = signif(p_an,3),
    reject_5pct = p_an < 0.05, mml_pre = round(mml_pre,3), mml_post = round(mml_post,3),
    dmml = round(mml_post - mml_pre,3), Bl_pre = round(Bl_pre,4), Bl_post = round(Bl_post,4),
    dBl = round(Bl_post - Bl_pre,4))

  # G3 归类
  verdict <- if (p_an >= 0.05) "not_reject_stability(稳定性是发现)" else
             if (mml_post > mml_pre) "reject_higher_post(H1部分复活)" else "reject_lower_post(方向相反-报作者)"
  g3_rows[[cr]] <- data.table(crop = cr, p_analytic = signif(p_an,3), dmml = round(mml_post-mml_pre,3), G3_verdict = verdict)
}
tt <- rbindlist(test_rows); fwrite(tt, "out/gamma_break_test.csv")
g3 <- rbindlist(g3_rows); fwrite(g3, "out/gamma_break_G3.csv")
cat("\n===== M6 Γ 断点 LR + 分半 M_ML =====\n"); print(tt[, .(crop, LR, p_analytic, reject_5pct, mml_pre, mml_post, dmml)])
cat("\n===== Δλ_nt（分半劳动偏向，是否2014后更负=加速）=====\n"); print(tt[, .(crop, Bl_pre, Bl_post, dBl)])
cat("\n===== G3 归类 =====\n"); print(g3)
if (any(grepl("方向相反", g3$G3_verdict))) cat("\n*** G3 存在方向相反品种，需报作者 ***\n")
cat("\n[gamma_break] done\n")
