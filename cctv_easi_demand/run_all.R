#!/usr/bin/env Rscript
# One-command driver for the v2 CCTV EASI purchase-demand outputs.
base <- "/root/data/Paper/央视数据/Paper1-EASI"
run <- function(cmd, wd = base) {
  message("[run_all] ", cmd)
  status <- system(cmd, intern = FALSE, ignore.stdout = FALSE, ignore.stderr = FALSE)
  if (!identical(status, 0L)) stop("Command failed: ", cmd, call. = FALSE)
}
setwd(file.path(base, "model_v2_R"))
Sys.setenv(OPENBLAS_NUM_THREADS = "1", OMP_NUM_THREADS = "1")
run("Rscript src/30_build_prices_panel_v2.R")
run("Rscript src/32_estimate_main_v2.R")
run("Rscript src/33_robustness_v2.R")
run("Rscript src/34_bootstrap_v2.R")
run("Rscript src/34b_bootstrap_merge_v2.R")
run("Rscript src/35_welfare_cv_v2.R")
run("Rscript src/36_curvature_constrained_v2.R")
run("Rscript src/37_curvature_settings_v2.R")
run("Rscript src/38_regularity_final_v2.R")
run("Rscript src/39_descriptives_v2.R")
run("Rscript src/40_freq_winsor_zero_v2.R")
run("Rscript src/41_frequency_benchmark_v2.R")
run("Rscript src/42_fourweek_frequency_v2.R")
run("Rscript src/43_outlier_audit_v2.R")
run("Rscript src/44_audit_response_v2.R")
run("Rscript src/45_results_manifest_v2.R")
setwd(file.path(base, "paper_v2"))
run("bash src/run_finalize.sh")
