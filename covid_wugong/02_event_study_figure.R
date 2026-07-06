#!/usr/bin/env Rscript
# ============================================================================
# 02_event_study_figure.R
# Publication-quality event-study plot, 2013-2023, extending the original
# 2013-2022 figure with the recovered 2023 outcome year (modification plan
# Sec 3.1 / Sec 3.5b: "图3 事件研究图（2013–2022/23，含联合检验p值）").
# ============================================================================
suppressMessages({library(ggplot2); library(data.table)})
BASE <- "/opt/data/research/Paper/新冠对务工的影响"
O    <- file.path(BASE,"revision2","output")
FIG  <- file.path(BASE,"revision2","figures")

pd <- fread(file.path(O,"event_study_coefs.csv"))
pd[, sig := ifelse(year==2019, "ref", ifelse(lo>0 | hi<0, "sig","ns"))]

pretrend_p <- 0.362  # Wald F=1.132, df1=6, df2=40 (see tab_2023_persistence.md)

ymin <- min(pd$lo); ymax <- max(pd$hi)
pad  <- 0.08*(ymax-ymin)

p <- ggplot(pd, aes(x=year, y=est)) +
  geom_hline(yintercept=0, linetype="dashed", color="grey40", linewidth=0.4) +
  geom_vline(xintercept=2019.5, linetype="dotted", color="grey60", linewidth=0.4) +
  geom_line(color="grey50", linewidth=0.5, alpha=0.6) +
  geom_errorbar(aes(ymin=lo, ymax=hi, color=sig), width=0.18, linewidth=0.7) +
  geom_point(aes(color=sig), size=2.8) +
  scale_color_manual(values=c("sig"="#C44E52","ns"="#4C72B0","ref"="grey30"), guide="none") +
  annotate("text", x=2019.55, y=ymax+pad*0.55, label="COVID-19 onset",
           angle=90, vjust=-0.4, hjust=1, size=2.9, color="grey40") +
  annotate("text", x=2013, y=ymin-pad*0.35,
           label=paste0("Pre-trend joint test (2013-2018): p = ", sprintf("%.2f", pretrend_p)),
           hjust=0, size=3.0, color="grey20") +
  scale_x_continuous(breaks=2013:2023) +
  scale_y_continuous(limits=c(ymin-pad*0.7, ymax+pad*1.3)) +
  labs(
    title="COVID exposure effect on off-farm workdays concentrates in 2020-2021,\nfades by 2022, and shows no rebound through 2023",
    x="Year", y="Coef. on ln(1+cum. cases thru 2022) x year\n(ref. 2019)"
  ) +
  theme_minimal(base_size=11) +
  theme(
    plot.title = element_text(size=10.5, face="plain", hjust=0, margin=margin(b=10), lineheight=1.15),
    panel.grid.minor = element_blank(),
    axis.title = element_text(size=9.5),
    axis.text = element_text(size=9),
    plot.margin = margin(14,16,10,10)
  )

ggsave(file.path(FIG,"fig_event_study.png"), plot=p, width=7.4, height=4.9, dpi=300)
cat("saved fig_event_study.png\n")
