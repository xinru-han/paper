# =============================================================================
# 99_run_all.R — full pipeline for Paper 2 (elder diet), in dependency order
# Usage: Rscript code/99_run_all.R   (from the paper2-elder project root)
# =============================================================================
scripts <- c(
  "01_build_data.R",         # datasets (household / member / person / B-line)
  "02_audit_nutrients.R",    # Task 3 gatekeeper (currently: FAIL -> D1/D6)
  "03_descriptives.R",       # Table 1, figs 1-2
  "04_aline_main.R",         # A line FE sequence, scale-vs-composition (D5)
  "05_aline_robust.R",       # IPW/EB/matching/AIPW, permutation, Oster, LOP
  "06_bline_gap.R",          # B1 household-FE elder gap (+ Romano-Wolf)
  "07_bline_passthrough.R",  # B2 pass-through by arrangement
  "08_decomposition_leakage.R", # B3 decomposition + leakage bootstrap
  "09_mechanisms.R",         # roles / self-provisioning / binary outcomes
  "10_aging_projection.R",   # 2035 scenarios (provisioning-anchored)
  "11_county_policy_text.R", # county report text: diffusion + moderation
  "12_grf_heterogeneity.R"   # appendix causal forest
)
base <- "/root/data/Paper/食物消费数据/paper2-elder/code"
for (s in scripts) {
  cat("\n============================", s, "============================\n")
  status <- system2("Rscript", file.path(base, s))
  if (status != 0) stop("FAILED: ", s)
}
cat("\nALL SCRIPTS COMPLETED\n")
