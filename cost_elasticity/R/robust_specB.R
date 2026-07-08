# robust_specB.R — M2 Spec B（预期产量 lny_e）全品种重估 + 决策门 G2
# lny 由实际亩产 log(q_output) 换为 log(q_output_e)（省内前3年移动平均，样本顺延2006）。
# 产出：out/params_{crop}_specB_cc.csv, out/elasticities_{crop}_specB_cc.csv, out/specB_compare.csv
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R"); source("R/estimate.R")

CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica",
           "rice_early_indica","rice_late_indica","peanut","rapeseed")
FN <- c("labor","mach","fert","seed","other")

fit_core <- function(pan) {
  d <- prep_data(pan); sys <- tl_build_system(d, 4)
  So <- as.matrix(as.data.frame(d)[, paste0("S_", FN[1:4])]); So <- cbind(So, 1 - rowSums(So))
  fit <- tl_itsur_c1(sys, 4, colMeans(So), S_obs = So, kappa = 1e6); stopifnot(fit$converged)
  G <- fit$Gamma_full; lam <- { l <- fit$theta[sprintf("lambda_%dt",1:4)]; c(l, -sum(l)) }
  Shat <- tl_fitted_shares(fit, sys, 4); Sbar <- colMeans(Shat)
  el <- tl_elasticities(G, Sbar)
  th <- fit$theta
  lnw <- as.matrix(d[, sprintf("lnw_%d",1:4), with = FALSE])
  eCy <- th["alpha_y"] + th["gamma_yy"]*d$lny + as.numeric(lnw %*% th[sprintf("gamma_%dy",1:4)]) + th["lambda_yt"]*d$tt
  list(fit = fit, n = nrow(d),
       eps_ll = el$eps[1,1], eps_mm = el$eps[2,2], M_ml = el$morishima[2,1],
       B_labor = lam[1]/Sbar[1],
       eCy_mean = mean(eCy), eCy_min = min(eCy), eCy_max = max(eCy),
       eCy_neg_rate = mean(eCy < 0), el = el, G = G, Sbar = Sbar)
}

rows <- list()
for (cr in CROPS) {
  cat("specB:", cr, "\n")
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  base <- fit_core(pan)
  panB <- pan[!is.na(q_output_e)]; panB[, q_output := q_output_e]
  sb <- fit_core(panB)
  # 落盘 specB 参数与弹性（cc 无解析 vcov，推断走 bootstrap）
  th <- sb$fit$theta
  fwrite(data.table(param = names(th), est = th), sprintf("out/params_%s_specB_cc.csv", cr))
  eldt <- rbindlist(lapply(1:5, function(n) rbindlist(lapply(1:5, function(m) data.table(
    crop = cr, f_n = FN[n], f_m = FN[m], eps = sb$el$eps[n,m], morishima = sb$el$morishima[n,m])))))
  fwrite(eldt, sprintf("out/elasticities_%s_specB_cc.csv", cr))
  rows[[cr]] <- data.table(crop = cr, n_base = base$n, n_specB = sb$n,
    eps_ll_base = round(base$eps_ll,3), eps_ll_specB = round(sb$eps_ll,3),
    eps_mm_base = round(base$eps_mm,3), eps_mm_specB = round(sb$eps_mm,3),
    M_ml_base = round(base$M_ml,3), M_ml_specB = round(sb$M_ml,3),
    dM_ml = round(sb$M_ml - base$M_ml,3),
    B_labor_base = round(base$B_labor,4), B_labor_specB = round(sb$B_labor,4),
    eCy_base_mean = round(base$eCy_mean,3), eCy_base_negrate = round(base$eCy_neg_rate,3),
    eCy_specB_mean = round(sb$eCy_mean,3), eCy_specB_negrate = round(sb$eCy_neg_rate,3),
    eCy_specB_range = sprintf("[%.2f,%.2f]", sb$eCy_min, sb$eCy_max))
}
cmp <- rbindlist(rows)
fwrite(cmp, "out/specB_compare.csv")

# 决策门 G2：任一 |ΔM_ml|>0.15 或核心弹性变号 → 停下报作者
cmp[, sign_flip := (sign(eps_ll_base) != sign(eps_ll_specB)) | (sign(eps_mm_base) != sign(eps_mm_specB)) | (sign(M_ml_base) != sign(M_ml_specB))]
cmp[, big_move := abs(dM_ml) > 0.15]
cat("\n===== M2 Spec B 对照 =====\n"); print(cmp[, .(crop, M_ml_base, M_ml_specB, dM_ml, eps_ll_base, eps_ll_specB, big_move, sign_flip)])
cat("\n===== ε_Cy（预期产量是否回到合理(0,1)区间）=====\n"); print(cmp[, .(crop, eCy_base_negrate, eCy_specB_mean, eCy_specB_negrate, eCy_specB_range)])
g2_trip <- cmp[big_move | sign_flip]
if (nrow(g2_trip)) {
  cat("\n*** G2 触发：以下品种 |ΔM_ml|>0.15 或变号，需作者定基线归属 ***\n"); print(g2_trip[, .(crop, dM_ml, big_move, sign_flip)])
} else cat("\n>>> G2 未触发：Spec B 进稳健性、基线不动 <<<\n")
fwrite(g2_trip, "out/specB_G2_flags.csv")
cat("\n[robust_specB] done\n")
