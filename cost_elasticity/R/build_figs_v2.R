# build_figs_v2.R — R6 图 v2：新增 Γ 断点两段 M_ML、bootstrap CI 森林图、区域诱致系数
#  （F3 分期两段线+CI；F5 实际口径待 INPUT，暂沿用名义版 F5）
suppressMessages({library(data.table); library(ggplot2)})
setwd("/root/paper/cost_elasticity"); dir.create("figs", showWarnings = FALSE)
th <- theme_bw(base_size = 11) + theme(panel.grid.minor = element_blank())
gs <- function(p, f, w=7.5, h=4.8) ggsave(file.path("figs", f), p, width=w, height=h, dpi=300)
CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica","rice_early_indica","rice_late_indica","peanut","rapeseed")

# F3v2：Γ 断点两段 M_ML（pre 2004-13 vs post 2014-24，共同评估点）
bk <- fread("out/gamma_break_test.csv")
d1 <- melt(bk[, .(crop, `2004–2013` = mml_pre, `2014–2024` = mml_post)], id.vars = "crop",
           variable.name = "segment", value.name = "M_ML")
d1[, crop := factor(crop, levels = bk[order(mml_post)]$crop)]
pB <- ggplot(d1, aes(M_ML, crop, color = segment)) +
  geom_line(aes(group = crop), color = "grey60", arrow = arrow(length = unit(0.12,"cm"), ends="last")) +
  geom_point(size = 2.6) + geom_vline(xintercept = 1, linetype = 3) +
  scale_color_manual(values = c("2004–2013" = "#377eb8", "2014–2024" = "#e41a1c")) +
  labs(x = expression(M[ML]~"(工资"%->%"机械替代劳动，共同评估点)"), y = NULL, color = NULL,
       title = "Γ 结构断点：M_ML 在 2014 年后一律上升（9 品种全部拒绝 Γ 稳定）") + th +
  theme(legend.position = "top")
gs(pB, "F3v2_break_Mml.png")

# F6：M_ML bootstrap 95% CI 森林图（cc 基线，B=500）
dr <- fread("out/bootstrap_draws_all_cc.csv")[status=="ok" & period=="all"]
ci <- dr[, .(med = median(M_ml), lo = quantile(M_ml,.025), hi = quantile(M_ml,.975)), by = crop]
ci[, crop := factor(crop, levels = ci[order(med)]$crop)]
ci[, grp := ifelse(crop %in% c("corn","wheat","soybean","peanut","rapeseed"), "旱作", "稻作")]
pC <- ggplot(ci, aes(med, crop, color = grp)) +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0.25) + geom_point(size = 2.4) +
  geom_vline(xintercept = 1, linetype = 3) + geom_vline(xintercept = 0, color = "grey40") +
  scale_color_manual(values = c("旱作"="#d95f02","稻作"="#1b9e77")) +
  labs(x = expression(M[ML]~"[95% 省级 block bootstrap CI]"), y = NULL, color = NULL,
       title = "M_ML 全品种 95% CI 下界均 >0（替代稳健）；旱作−稻作差 0.33 [0.14, 0.48]") + th +
  theme(legend.position = "top")
gs(pC, "F6_Mml_bootstrap_ci.png")

# F7：区域×品种诱致性 劳动 Σψ（DK CI），两滞后规格
ir <- fread("out/induced_regional.csv")[factor=="labor"]
ir[, ci_lo := sum_psi - 1.96*se_dk][, ci_hi := sum_psi + 1.96*se_dk]
pD <- ggplot(ir, aes(sum_psi, spec)) +
  geom_errorbarh(aes(xmin = ci_lo, xmax = ci_hi), height = 0.15, color = "#377eb8") +
  geom_point(size = 3, color = "#377eb8") + geom_vline(xintercept = 0, linetype = 2) +
  labs(x = expression(Sigma*psi~"(劳动节约偏向对滞后区域相对雇工工价; DK 95% CI)"), y = "滞后规格",
       title = "M8 区域×品种：劳动诱致系数转正显著（Hicks 方向）；k1–5 placebo 干净") + th
gs(pD, "F7_induced_regional_labor.png")

cat("[build_figs_v2] F3v2/F6/F7 written\n")
