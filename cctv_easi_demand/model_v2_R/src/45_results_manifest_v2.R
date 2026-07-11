#!/usr/bin/env Rscript
# Build a lightweight results manifest for generated v2 outputs.
suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
out <- file.path(base, "outputs")
files <- list.files(out, recursive = TRUE, full.names = TRUE)
files <- files[file.info(files)$isdir == FALSE]
sha_one <- function(p) {
  z <- tryCatch(system2("sha256sum", p, stdout = TRUE, stderr = FALSE), error = function(e) NA_character_)
  if (length(z) && !is.na(z[1])) strsplit(z[1], " +")[[1]][1] else NA_character_
}
script_map <- data.table(
  pattern = c("^price/", "^demand/", "^inference/", "^welfare/", "^regularity/",
              "^robustness/robustness_matrix", "^robustness/fourweek",
              "^robustness/(intensive|purchase)", "^robustness/robustness_freq",
              "^descriptives/", "^validation/", "^audit/"),
  generating_script = c("30_build_prices_panel_v2.R", "32_estimate_main_v2.R",
                        "34_bootstrap_v2.R / 34b_bootstrap_merge_v2.R",
                        "35_welfare_cv_v2.R", "36-38 regularity scripts",
                        "33_robustness_v2.R", "42_fourweek_frequency_v2.R",
                        "41_frequency_benchmark_v2.R", "40_freq_winsor_zero_v2.R",
                        "39_descriptives_v2.R / 43_outlier_audit_v2.R",
                        "43_outlier_audit_v2.R", "44_audit_response_v2.R"))
rel <- sub(paste0("^", out, "/"), "", files)
gen <- vapply(rel, function(x) {
  hit <- script_map[grepl(pattern, x)]
  if (nrow(hit)) hit$generating_script[1] else "driver/log/manual"
}, character(1))
git_commit <- tryCatch(system2("git", c("rev-parse", "HEAD"), stdout = TRUE,
                               stderr = FALSE), error = function(e) NA_character_)
manifest <- data.table(
  path = rel,
  bytes = file.info(files)$size,
  mtime = format(file.info(files)$mtime, "%Y-%m-%d %H:%M:%S %Z"),
  sha256 = vapply(files, sha_one, character(1)),
  generating_script = gen,
  git_commit = if (length(git_commit)) git_commit[1] else NA_character_,
  manifest_built_at = format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"),
  r_version = paste(R.version$major, R.version$minor, sep = ".")
)
fwrite(manifest, file.path(out, "results_manifest_v2.csv"), bom = TRUE)
writeLines(capture.output(sessionInfo()), file.path(out, "sessionInfo.txt"))
message("[45] wrote results_manifest_v2.csv and sessionInfo.txt")
