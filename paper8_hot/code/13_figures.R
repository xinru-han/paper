# Paper 8 script 13: figures
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")
library(ggplot2)
theme_set(theme_minimal(base_size = 11))
BINS <- setdiff(TBIN_LABELS, TBIN_REF)
binlab <- c(le0 = "<=0", b0_6 = "0-6", b6_12 = "6-12", b12_18 = "12-18",
            ref18_24 = "18-24 (ref)", b24_30 = "24-30", gt30 = ">30")
ordbin <- function(x) factor(binlab[x], levels = binlab)

## Fig 1: temperature response curves (trip + daily spend)
main <- fread(file.path(DIR_TAB, "t1_main_coefs.csv"))
d1 <- main[outcome %in% c("trip_any","spend_day") & model == "lpm" & grepl("^tbin", term)]
d1[, bin := sub("tbin", "", term)]
ref <- data.table(term = "ref", est = 0, se = 0, model = "lpm",
                  outcome = unique(d1$outcome), bin = "ref18_24")
d1 <- rbind(d1, ref, fill = TRUE)
d1 <- unique(d1, by = c("outcome","bin"))
d1[, binf := ordbin(bin)]
g1 <- ggplot(d1, aes(binf, est, group = outcome)) +
  geom_hline(yintercept = 0, linetype = 2, colour = "grey50") +
  geom_pointrange(aes(ymin = est - 1.96*se, ymax = est + 1.96*se), colour = "#B2182B") +
  geom_line(colour = "#B2182B") +
  facet_wrap(~ outcome, scales = "free_y",
             labeller = as_labeller(c(trip_any = "P(any purchase today)", spend_day = "Daily food spend (yuan)"))) +
  labs(x = "Daily mean temperature bin (deg C)", y = "Effect vs 18-24 deg C")
ggsave(file.path(DIR_FIG, "fig1_response_curves.png"), g1, width = 8, height = 3.6, dpi = 300)

## Fig 2: channel decomposition on hot days
dec <- fread(file.path(DIR_TAB, "t4_channel_decomposition.csv"))
d2 <- melt(dec[bin == "gt30", .(group, price_channel, demand_channel)], id.vars = "group")
d2[, glab := sub("^G[0-9]+_", "", group)]
g2 <- ggplot(d2, aes(glab, value, fill = variable)) +
  geom_col(position = "stack") + coord_flip() +
  scale_fill_manual(values = c(price_channel = "#2166AC", demand_channel = "#B2182B"),
                    labels = c("price channel", "demand channel")) +
  labs(x = NULL, y = "d ln spend on a >30C day", fill = NULL)
ggsave(file.path(DIR_FIG, "fig2_channel_decomposition.png"), g2, width = 7, height = 4.2, dpi = 300)

## Fig 3: acclimatization within season
ad <- fread(file.path(DIR_TAB, "t7_adaptation.csv"))
d3 <- ad[model == "acclimatization" & grepl("hot_phase", term)]
d3[, phase := factor(sub(".*hot_phase", "", term), levels = c("hot_1_5","hot_6_15","hot_16p"),
                     labels = c("1st-5th", "6th-15th", "16th+"))]
g3 <- ggplot(d3, aes(phase, est)) +
  geom_hline(yintercept = 0, linetype = 2, colour = "grey50") +
  geom_pointrange(aes(ymin = est - 1.96*se, ymax = est + 1.96*se), colour = "#B2182B") +
  labs(x = "k-th >30C day of the year", y = "ln per-capita spend effect")
ggsave(file.path(DIR_FIG, "fig3_acclimatization.png"), g3, width = 5, height = 3.5, dpi = 300)

## Fig 4: cumulative displacement by perishability
dl <- fread(file.path(DIR_TAB, "t8_displacement_lags.csv"))
fresh <- c("G03_蔬菜","G04_水果","G05_猪肉","G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜")
d4 <- dl[grepl("^hot_l", term)]
d4[, k := as.integer(sub("hot_l", "", term))]
d4[, cls := fifelse(group %in% fresh, "perishable", "storable")]
d4 <- d4[order(cls, group, k)][, .(cum = cumsum(est), k = k), by = .(cls, group)]
d4m <- d4[, .(cum = mean(cum)), by = .(cls, k)]
g4 <- ggplot(d4m, aes(k, cum, colour = cls)) +
  geom_hline(yintercept = 0, linetype = 2, colour = "grey50") +
  geom_line(linewidth = 1) + geom_point() +
  scale_colour_manual(values = c(perishable = "#B2182B", storable = "#2166AC")) +
  labs(x = "Days since >30C day", y = "Cumulative per-capita spend effect (yuan)", colour = NULL)
ggsave(file.path(DIR_FIG, "fig4_displacement.png"), g4, width = 6, height = 3.8, dpi = 300)

## Fig 5: projected protein change by province, +3C
pj <- fread(file.path(DIR_TAB, "t12_projection_province.csv"), encoding = "UTF-8")
d5 <- pj[scen == "d30" & adaptation %in% c("none","adapted")]
ord <- d5[adaptation == "none"][order(prot_pct_yr), province]
d5[, prov := factor(province, levels = ord)]
g5 <- ggplot(d5, aes(prov, prot_pct_yr, fill = adaptation)) +
  geom_col(position = "dodge") + coord_flip() +
  scale_fill_manual(values = c(none = "#B2182B", adapted = "#F4A582")) +
  labs(x = NULL, y = "Projected change in annual purchased protein (%), +3C", fill = "adaptation")
ggsave(file.path(DIR_FIG, "fig5_projection_protein.png"), g5, width = 7, height = 6, dpi = 300)
logmsg("13: figures written")
