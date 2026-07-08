# make_hw_panels.R — M12a：从当前 panel_{crop}.csv 生成雇工工价并列基线面板
# w_labor := w_labor_hired（有真实省际变异的市场工价）；其余列不变（含 q_output_e）。
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica",
           "rice_early_indica","rice_late_indica","peanut","rapeseed")
for (cr in CROPS) {
  p <- fread(sprintf("data/panel_%s.csv", cr))
  p[, w_labor := w_labor_hired]
  fwrite(p, sprintf("data/panel_%s_hw.csv", cr))
}
cat("[make_hw_panels] regenerated", length(CROPS), "hw panels\n")
