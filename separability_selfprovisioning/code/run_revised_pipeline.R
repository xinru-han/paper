options(warn = 1)

root <- getwd()
if (!file.exists(file.path(root, "code", "00_setup.R"))) {
  stop("Run this script from the paper project root: ", root)
}

scripts <- c(
  "code/19_apply_kg_units_drop_outliers_prepare_official_data.R",
  "code/01_rebuild_revised_analysis_data.R",
  "code/02_common_sample_baseline.R",
  "code/03_baseline_coefficients_margins.R",
  "code/04_category_specific_nsi.R",
  "code/05_two_part_model.R",
  "code/06_price_robustness.R",
  "code/07_category_definition_audits.R",
  "code/08_robustness_checks.R",
  "code/09_appendix_market_friction_interactions.R",
  "code/10_appendix_iv_diagnostics.R",
  "code/11_compile_revised_results_report.R",
  "code/14_editor_revision_analyses.R",
  "code/13_compile_all_integrated_markdowns.R"
)

for (script in scripts) {
  message("===== RUN ", script, " =====")
  source(script, local = new.env(parent = globalenv()))
}

message("Revised Paper 1 pipeline completed.")