# =============================================================================
# 99_run_all.R — run the full Paper 3 pipeline in order.
# Prerequisite: paper2-elder data build exists (../paper2-elder/data/).
# =============================================================================
scripts <- c("01_iv_map.R", "02_build_panel.R", "03_first_stage.R", "04_main.R",
             "05_subgroups.R", "06_mechanisms_price.R", "07_purchase_fafh.R",
             "08_moderators.R", "09_exclusion_battery.R", "10_robustness.R",
             "12_placebo_corridors.R", "13_descriptives.R", "14_gap_accounting.R",
             "15_investment_pricing.R", "16_targeting_forest.R", "17_figures.R")
base <- "/root/data/Paper/食物消费数据/paper3-foodenv/code"
for (s in scripts) {
  cat("\n========", s, "========\n")
  status <- system2("Rscript", file.path(base, s))
  if (status != 0) stop("FAILED: ", s)
}
cat("\nAll Paper 3 scripts completed.\n")
