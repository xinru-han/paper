# build_figs.R — 论文图（300dpi，serif），全部从 data/ 与 out/ 的CSV生成
# 用法: Rscript R/build_figs.R <crop>   缺省 corn
suppressMessages({library(data.table); library(ggplot2)})
setwd("/root/paper/cost_elasticity")
dir.create("figs", showWarnings = FALSE)

cr <- {a <- commandArgs(trailingOnly = TRUE); if (length(a)) a[1] else "corn"}
FN <- c("labor", "mach", "fert", "seed", "other")
th <- theme_bw(base_size = 11, base_family = "serif") +
  theme(panel.grid.minor = element_blank(), legend.position = "bottom")
gsave <- function(p, f, w = 7, h = 4.5) ggsave(file.path("figs", f), p, width = w, height = h, dpi = 300)

pan <- fread(sprintf("data/panel_%s.csv", cr))

# ---- F1 动机四联图：日工价、机械服务价、亩用工天数、机械费份额 --------------
nat <- pan[, .(w_labor = mean(w_labor), w_mach = mean(w_mach),
               labor_days = mean(labor_days), S_mach = mean(S_mach),
               S_labor = mean(S_labor)), by = year][order(year)]
f1d <- rbindlist(list(
  data.table(year = nat$year, v = nat$w_labor, panel = "A. Labor day wage (yuan/day)"),
  data.table(year = nat$year, v = nat$w_mach, panel = "B. Machinery service price (yuan/mu)"),
  data.table(year = nat$year, v = nat$labor_days, panel = "C. Labor input (days/mu)"),
  data.table(year = nat$year, v = 100 * nat$S_mach, panel = "D. Machinery cost share (%)")))
p1 <- ggplot(f1d, aes(year, v)) + geom_line(linewidth = .7) + geom_point(size = 1) +
  facet_wrap(~panel, scales = "free_y") + labs(x = NULL, y = NULL) + th
gsave(p1, sprintf("F1_motivation_%s.png", cr), 7.5, 5)

# ---- F2 拟合优度：fitted vs observed 份额 -----------------------------------
fs <- fread(sprintf("out/fitted_shares_%s_cc.csv", cr))
f2 <- rbindlist(lapply(FN[1:4], function(n)
  data.table(factor = n, obs = fs[[paste0("Sobs_", n)]], fit = fs[[paste0("Shat_", n)]])))
p2 <- ggplot(f2, aes(obs, fit)) + geom_point(alpha = .35, size = .8) +
  geom_abline(linetype = 2, color = "red") + facet_wrap(~factor, scales = "free") +
  labs(x = "Observed share", y = "Fitted share") + th
gsave(p2, sprintf("F2_fit_%s.png", cr), 7, 5.5)

# ---- F3 M_ML 演化：逐年评估点 + bootstrap 带 --------------------------------
source("R/itsur.R")
G <- as.matrix(fread(sprintf("out/gamma_%s_cc.csv", cr))[, -1])
years <- sort(unique(fs$year))
mml <- rbindlist(lapply(years, function(y) {
  S <- colMeans(fs[year == y, paste0("Shat_", FN), with = FALSE])
  el <- tl_elasticities(G, unlist(S))
  data.table(year = y, M_ml = el$morishima[2, 1], M_lm = el$morishima[1, 2],
             w_labor = mean(pan[year == y, w_labor]))
}))
bootf <- sprintf("out/bootstrap_draws_%s_cc.csv", cr)
if (file.exists(bootf)) {
  bt <- fread(bootf)[ok == TRUE & period != "all"]
  per_mid <- c(`2004-2008` = 2006, `2009-2014` = 2011.5, `2015-2019` = 2017, `2020-2024` = 2022)
  bb <- bt[, .(lo = quantile(M_ml, .025), hi = quantile(M_ml, .975), md = median(M_ml)),
           by = period]
  bb[, year := per_mid[period]]
  p3 <- ggplot(mml, aes(year, M_ml)) +
    geom_ribbon(data = bb, aes(x = year, ymin = lo, ymax = hi), inherit.aes = FALSE,
                alpha = .15, fill = "steelblue") +
    geom_line(linewidth = .8, color = "steelblue4") + geom_point(size = 1.2, color = "steelblue4") +
    geom_hline(yintercept = 1, linetype = 3) +
    labs(x = NULL, y = expression(M[ML]~"(labor"%->%"machinery substitution as wage rises)")) + th
} else {
  p3 <- ggplot(mml, aes(year, M_ml)) + geom_line(linewidth = .8) + geom_point() +
    geom_hline(yintercept = 1, linetype = 3) + labs(x = NULL, y = "M_ML") + th
}
gsave(p3, sprintf("F3_morishima_path_%s.png", cr))

# ---- F4 S2 累计偏向路径 ------------------------------------------------------
bp <- sprintf("out/bias_path_%s.csv", cr)
if (file.exists(bp)) {
  b <- fread(bp)
  p4 <- ggplot(b, aes(year, delta, color = factor)) + geom_line(linewidth = .7) +
    geom_hline(yintercept = 0, linetype = 3) +
    labs(x = NULL, y = expression(delta[n*tau]~"(cumulative technical shift in cost share)"),
         color = NULL) + th
  gsave(p4, sprintf("F4_bias_path_%s.png", cr))
}

# ---- F5 成本分解堆叠柱 -------------------------------------------------------
dc <- sprintf("out/decomp_%s.csv", cr)
if (file.exists(dc)) {
  d <- fread(dc)[province == "NATIONAL"]
  dl <- melt(d[, .(seg, labor = price_labor, mach = price_mach, fert = price_fert,
                   seed = price_seed, other = price_other, yield, tech, residual)],
             id.vars = "seg")
  p5 <- ggplot(dl, aes(seg, 100 * value, fill = variable)) +
    geom_col(position = "stack") +
    geom_point(data = d, aes(seg, 100 * dlnC), inherit.aes = FALSE, shape = 18, size = 3) +
    labs(x = NULL, y = "Contribution to Δln(cost per mu) × 100", fill = NULL,
         caption = "Diamond = total log cost growth (nominal)") + th
  gsave(p5, sprintf("F5_decomp_%s.png", cr))
}
cat("figs written for", cr, "\n")
