# =============================================================================
# run_reproduction.R
# -----------------------------------------------------------------------------
# Master reproduction driver for
#   "Farming for the Family Table: Household Composition and Food
#    Self-Provisioning in Rural China" (paper1_manuscript_v4.docx)
#
# The original code/ directory was lost; every script here was recovered
# verbatim from paper1_all_code_integrated.md and re-verified against the
# shipped results (paper1_all_results_integrated.md) and the manuscript.
#
# This driver reproduces ALL numerical results in the manuscript from the
# analysis-ready data. It deliberately does NOT re-run the raw-data
# construction scripts (04_export_*, 05_hedonic_*, 06_construct_market_*,
# 18_*, 19_*, 01_rebuild_*): those require the raw survey files and rebuild
# the analysis-ready panel, which already exists as two authoritative
# snapshots (see below). Running them is documented in REPRODUCTION_README.md.
#
# Two analysis-ready snapshots are used, matching the two samples the
# manuscript reports:
#   (A) MAIN sample  (28,520 rows -> 27,568 common M3): Tables 1-6, category
#       heterogeneity, within-village, robustness, appendix A1-A3.
#       -> data/repro_inputs/main_analysis_ready_28520.csv.zip
#   (B) kg-cleaned sample (post pipeline update): §5.6 post-estimation
#       (omnibus, Mundlak, RIF quantiles, category meta, external validity).
#       -> data/repro_inputs/kgclean_analysis_ready_28208.csv.zip
#
# Usage:  Rscript run_reproduction.R      (run from the project root)
# =============================================================================

options(warn = 1)
root <- getwd()
ar   <- function(...) file.path(root, "data", "analysis_ready", ...)
bk   <- function(...) file.path(root, "data", "backups", ...)
cl   <- function(...) file.path(root, "data", "cleaned", ...)

ri <- function(...) file.path(root, "data", "repro_inputs", ...)

# Unzip the two self-contained analysis-ready snapshots on first use.
unzip_if_needed <- function(zip, csv) {
  if (!file.exists(csv)) utils::unzip(zip, exdir = dirname(csv))
  csv
}
MAIN_SNAPSHOT    <- unzip_if_needed(ri("main_analysis_ready_28520.csv.zip"),
                                    ri("main_analysis_ready_28520.csv"))
KGCLEAN_SNAPSHOT <- unzip_if_needed(ri("kgclean_analysis_ready_28208.csv.zip"),
                                    ri("kgclean_analysis_ready_28208.csv"))
REVISED_TARGET   <- ar("paper1_revised_analysis_ready_long.csv")
CANONICAL_TARGET <- cl("paper1_household_category_long.csv")
dir.create(dirname(REVISED_TARGET),   recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(CANONICAL_TARGET), recursive = TRUE, showWarnings = FALSE)

run <- function(script) {
  message("\n===== RUN ", script, " =====")
  source(file.path("code", script), local = new.env(parent = globalenv()))
}

# -----------------------------------------------------------------------------
# Stage 1: MAIN results on the 27,568 common-M3 sample
# -----------------------------------------------------------------------------
stopifnot(file.exists(MAIN_SNAPSHOT))
file.copy(MAIN_SNAPSHOT, REVISED_TARGET, overwrite = TRUE)

main_scripts <- c(
  "02_common_sample_baseline.R",          # Table 3 (M0-M3 exclusion tests)
  "03_baseline_coefficients_margins.R",   # Table 4 (M3 composition coefficients) + Fig 4
  "04_category_specific_nsi.R",           # Table 5 (category NSI) + Fig 5
  "05_two_part_model.R",                  # Two-part model (H1 vs H2 entry/intensity)
  "06_price_robustness.R",                # Table 6 price-construction robustness
  "07_category_definition_audits.R",      # Category-definition audit (needs raw_data/ label file)
  "08_robustness_checks.R",               # Table 6 (composition defs, leave-one-province, placebo)
  "09_appendix_market_friction_interactions.R", # Appendix A1 interactions
  "10_appendix_iv_diagnostics.R",         # Appendix A2 IV first-stage diagnostics
  "11_compile_revised_results_report.R",  # Compiles the revised results report
  "14_editor_revision_analyses.R"         # Within-village (Table 3 bottom), Table A3, editor tables
)
for (s in main_scripts) run(s)

# -----------------------------------------------------------------------------
# Stage 2: §5.6 POST-ESTIMATION on the kg-cleaned sample
# -----------------------------------------------------------------------------
stopifnot(file.exists(KGCLEAN_SNAPSHOT))
file.copy(KGCLEAN_SNAPSHOT, REVISED_TARGET,   overwrite = TRUE)
file.copy(KGCLEAN_SNAPSHOT, CANONICAL_TARGET, overwrite = TRUE)

run("09_category_specific_tests.R")  # legacy: table3_category_specific_tests.csv (feeds A4)
message("\n===== RUN 20_post_estimation_plan.R =====")
source("20_post_estimation_plan.R", local = new.env(parent = globalenv()))

# Restore the MAIN snapshot as the default analysis-ready file so that a
# re-run of any individual main script reproduces the headline sample.
file.copy(MAIN_SNAPSHOT, REVISED_TARGET, overwrite = TRUE)

message("\nReproduction complete. See outputs/ and outputs/post_estimation_plan/.")
