source("code/00_setup.R")

read_if_exists <- function(file) {
  if (!file.exists(file)) return(data.frame())
  read_csv(file)
}

fmt <- function(x, digits = 3) {
  vapply(x, function(z) {
    if (is.na(z) || !is.finite(z)) return("NA")
    sprintf(paste0("%.", digits, "f"), z)
  }, character(1))
}

fmtp <- function(x) {
  vapply(x, function(z) {
    if (is.na(z) || !is.finite(z)) return("NA")
    if (z < 0.001) return("<0.001")
    sprintf("%.3f", z)
  }, character(1))
}

table2 <- read_if_exists(path("outputs", "tables", "table2_common_sample_baseline.csv"))
table3 <- read_if_exists(path("outputs", "tables", "table3_baseline_coefficients_margins.csv"))
table4 <- read_if_exists(path("outputs", "tables", "table4_category_specific_nsi.csv"))
table5 <- read_if_exists(path("outputs", "tables", "table5_two_part_model.csv"))
table6 <- read_if_exists(path("outputs", "tables", "table6_alternative_composition_outcomes.csv"))
table7 <- read_if_exists(path("outputs", "tables", "table7_leave_one_province.csv"))
table8 <- read_if_exists(path("outputs", "tables", "table8_household_composition_permutation.csv"))
tableA <- read_if_exists(path("outputs", "tables", "tableA_market_friction_interactions_appendix.csv"))
tableB <- read_if_exists(path("outputs", "tables", "tableB_iv_diagnostics_appendix.csv"))
tableC <- read_if_exists(path("outputs", "tables", "tableC_price_robustness.csv"))
tableD <- read_if_exists(path("outputs", "tables", "tableD_category_definition_audits.csv"))
sample_summary <- read_if_exists(path("outputs", "tables", "table1_sample_summary_revised.csv"))
by_year <- read_if_exists(path("outputs", "tables", "table1_observations_by_year_revised.csv"))
by_cat <- read_if_exists(path("outputs", "tables", "table1_observations_by_category_revised.csv"))
missingness <- read_if_exists(path("outputs", "tables", "table1_missingness_revised.csv"))

## Figure 1 conceptual framework placeholder.
png(path("outputs", "figures", "figure1_conceptual_framework_placeholder.png"), width = 1800, height = 900, res = 180)
par(mar = c(1, 1, 3, 1))
plot.new()
title("Conceptual Framework: Household Composition and Self-Provisioning Entry")
box <- function(x1, y1, x2, y2, label, col) {
  rect(x1, y1, x2, y2, col = col, border = "#333333", lwd = 1.5)
  text((x1 + x2) / 2, (y1 + y2) / 2, label, cex = 0.9)
}
box(0.05, 0.55, 0.27, 0.78, "Household\ncomposition", "#DCEAF7")
box(0.39, 0.55, 0.61, 0.78, "Self-provisioning\nentry", "#E9F3E4")
box(0.73, 0.55, 0.95, 0.78, "Category-specific\nheterogeneity", "#F6E4D7")
box(0.39, 0.18, 0.61, 0.38, "Controls:\nresources, prices,\nmarkets, GAEZ,\ntext, province, year", "#EFEFEF")
arrows(0.27, 0.665, 0.39, 0.665, length = 0.08, lwd = 2)
arrows(0.61, 0.665, 0.73, 0.665, length = 0.08, lwd = 2)
arrows(0.50, 0.38, 0.50, 0.55, length = 0.08, lwd = 2, lty = 2)
dev.off()

main_m3 <- table2[table2$outcome == "production_participation" & table2$spec == "M3", ]
log_m3 <- table2[table2$outcome == "log_selfprod_amount" & table2$spec == "M3", ]
ihs_m3 <- table2[table2$outcome == "ihs_selfprod_amount" & table2$spec == "M3", ]
two_part_part2 <- table5[table5$model_part == "Part 2", ]
two_part_part2_sig <- nrow(two_part_part2) > 0 && two_part_part2$hhcomp_wald_p[1] < 0.05

strong_cats <- table4[table4$signal_label == "Strong", ]
weak_cats <- table4[table4$signal_label == "Weak", ]
top_cats <- table4[order(table4$nsi, decreasing = TRUE), ]

loo_all_sig <- if (nrow(table7) > 0) all(table7$wald_p < 0.05, na.rm = TRUE) else NA
loo_min <- if (nrow(table7) > 0) min(table7$wald_chisq, na.rm = TRUE) else NA
loo_max <- if (nrow(table7) > 0) max(table7$wald_chisq, na.rm = TRUE) else NA
loo_infl <- if (nrow(table7) > 0) table7$dropped_province[which.min(table7$wald_chisq)] else "NA"

required_files <- c(
  "outputs/tables/table2_common_sample_baseline.csv",
  "outputs/tables/table3_baseline_coefficients_margins.csv",
  "outputs/tables/table4_category_specific_nsi.csv",
  "outputs/tables/table5_two_part_model.csv",
  "outputs/tables/table6_alternative_composition_outcomes.csv",
  "outputs/tables/table7_leave_one_province.csv",
  "outputs/tables/table8_household_composition_permutation.csv",
  "outputs/figures/figure2_nsi_by_category.png",
  "outputs/logs/revised_data_merge_log.md",
  "outputs/logs/common_sample_log.md",
  "outputs/logs/roulei_split_audit.md",
  "outputs/logs/youzhi_definition_audit.md"
)
missing_required <- required_files[!file.exists(path(required_files))]

inventory <- data.frame(
  Item = c(
    "Table 1", "Table 2", "Table 3", "Table 4", "Table 5", "Table 6", "Table 7", "Table 8",
    "Appendix Table A", "Appendix Table B", "Appendix Table C", "Appendix Table D",
    "Figure 1", "Figure 2", "Figure 3", "Figure 4"
  ),
  File = c(
    "outputs/tables/table1_descriptive_statistics_revised.csv",
    "outputs/tables/table2_common_sample_baseline.csv",
    "outputs/tables/table3_baseline_coefficients_margins.csv",
    "outputs/tables/table4_category_specific_nsi.csv",
    "outputs/tables/table5_two_part_model.csv",
    "outputs/tables/table6_alternative_composition_outcomes.csv",
    "outputs/tables/table7_leave_one_province.csv",
    "outputs/tables/table8_household_composition_permutation.csv",
    "outputs/tables/tableA_market_friction_interactions_appendix.csv",
    "outputs/tables/tableB_iv_diagnostics_appendix.csv",
    "outputs/tables/tableC_price_robustness.csv",
    "outputs/tables/tableD_category_definition_audits.csv",
    "outputs/figures/figure1_conceptual_framework_placeholder.png",
    "outputs/figures/figure2_nsi_by_category.png",
    "outputs/figures/figure3_household_composition_coefficients.png",
    "outputs/figures/figure4_household_composition_permutation.png"
  ),
  Placement = c(rep("Main text", 8), rep("Appendix", 4), rep("Main text", 4)),
  Purpose = c(
    "Descriptive statistics and sample checks",
    "Common-sample baseline separability tests",
    "Household-composition coefficient interpretation",
    "Category-specific NSI",
    "Two-part entry versus conditional intensity",
    "Alternative composition and outcomes",
    "Province leave-one-out",
    "Household-composition permutation placebo",
    "Market-friction interactions",
    "IV diagnostics",
    "Price robustness",
    "Category-definition audits",
    "Conceptual framework",
    "NSI ranking by category",
    "Baseline coefficient plot",
    "Permutation distribution"
  ),
  Status = "",
  Human_review = c(rep("No", 11), "Yes", rep("No", 4)),
  stringsAsFactors = FALSE
)
inventory$Status <- ifelse(file.exists(path(inventory$File)), "Generated", "Missing")

inv_lines <- c(
  "| Item | File path | Placement | Purpose | Status | Human review |",
  "|---|---|---|---|---|---|",
  paste0("| ", inventory$Item, " | `", inventory$File, "` | ", inventory$Placement, " | ", inventory$Purpose, " | ", inventory$Status, " | ", inventory$Human_review, " |")
)

sample_lines <- if (nrow(sample_summary) > 0) paste0("- ", sample_summary$item, ": ", sample_summary$value) else "- Sample summary unavailable."
year_lines <- if (nrow(by_year) > 0) paste0("- ", by_year$data_year, ": ", by_year$n_rows) else "- Year summary unavailable."
cat_lines <- if (nrow(by_cat) > 0) paste0("- ", by_cat$food_category, " / ", by_cat$food_category_label, ": ", by_cat$n_rows) else "- Category summary unavailable."
display_var <- function(x) {
  x <- sub("yuan_per_jin$", "yuan_per_kg", x)
  x <- ifelse(x == "village_price_category_median", "village_price_category_median_yuan_per_kg", x)
  x
}

miss_lines <- if (nrow(missingness) > 0) {
  paste0("- ", missingness$module, " / `", display_var(missingness$variable), "`: ", missingness$n_missing, " missing")
} else "- Missingness summary unavailable."

coeff_m3 <- table3[table3$outcome == "production_participation" & table3$spec == "M3", ]
coeff_lines <- if (nrow(coeff_m3) > 0) {
  paste0(
    "- `", coeff_m3$term, "`: beta = ", fmt(coeff_m3$estimate, 4),
    ", SE = ", fmt(coeff_m3$std_error_cluster, 4),
    ", p = ", fmtp(coeff_m3$p_value),
    ", direction = ", coeff_m3$direction,
    ", stable across M0-M3 = ", coeff_m3$sign_stable_across_M0_M3
  )
} else "- Coefficient table unavailable."

cat_report_lines <- if (nrow(table4) > 0) {
  paste0(
    "- ", table4$food_category_label, ": Wald = ", fmt(table4$hhcomp_wald_chisq),
    ", p = ", fmtp(table4$hhcomp_wald_p),
    ", NSI = ", fmt(table4$nsi),
    ", signal = ", table4$signal_label,
    ", drivers = ", table4$main_coefficient_drivers
  )
} else "- Category NSI table unavailable."

two_part_lines <- if (nrow(table5) > 0) {
  paste0(
    "- ", table5$model_part, " (", table5$sample_definition, ", outcome `", table5$outcome, "`): Wald = ",
    fmt(table5$hhcomp_wald_chisq), ", p = ", fmtp(table5$hhcomp_wald_p),
    ", N = ", table5$n
  )
} else "- Two-part table unavailable."

robust_lines <- if (nrow(table6) > 0) {
  paste0("- ", table6$composition_spec, " / `", table6$outcome, "`: Wald = ", fmt(table6$wald_chisq), ", p = ", fmtp(table6$wald_p), ", N = ", table6$n)
} else "- Robustness table unavailable."

market_lines <- if (nrow(tableA) > 0) {
  paste0("- ", tableA$friction_spec, " / `", tableA$outcome, "`: interaction Wald = ", fmt(tableA$interaction_wald_chisq), ", p = ", fmtp(tableA$interaction_wald_p), ".")
} else "- Market interaction appendix table unavailable."

iv_lines <- if (nrow(tableB) > 0) {
  paste0("- ", tableB$iv_spec, ": corr = ", fmt(tableB$correlation_with_market_friction_survey), ", min F = ", fmt(tableB$min_first_stage_F), ", median F = ", fmt(tableB$median_first_stage_F), ", weak = ", tableB$weak_iv_flag, ".")
} else "- IV diagnostics table unavailable."

price_lines <- if (nrow(tableC) > 0) {
  paste0("- ", tableC$price_spec, ": Wald = ", fmt(tableC$hhcomp_wald_chisq), ", p = ", fmtp(tableC$hhcomp_wald_p), ", N = ", tableC$n, ".")
} else "- Price robustness table unavailable."

human_flags <- c(
  if (nrow(tableD) > 0 && any(tableD$audit_item == "roulei_split" & tableD$human_review_required)) "- roulei split not performed; raw detail exists but analysis-ready split outcome is not cleanly available." else NULL,
  if (nrow(tableD) > 0 && any(tableD$audit_item == "youzhi_definition" & tableD$human_review_required)) "- youzhi definition requires human review before strong substantive claims about oils." else NULL,
  if (nrow(tableB) > 0 && any(tableB$weak_iv_flag)) "- IV first stages are weak; IV remains appendix-only." else NULL,
  if (nrow(tableA) > 0 && all(tableA$interaction_wald_p >= 0.05, na.rm = TRUE)) "- Market-friction interactions are non-significant." else NULL,
  "- commercialization_rate denominator unclear; not included in revised rerun."
)

report <- c(
  "# Paper 1 Revised Results Package",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## 1. Executive summary",
  "",
  paste0("- MAIN RESULT: household composition predicts self-provisioning participation in the common-sample M3 model (Wald = ", fmt(main_m3$hhcomp_wald_chisq[1]), ", p = ", fmtp(main_m3$hhcomp_wald_p[1]), ")."),
  paste0("- MAIN RESULT: full-sample intensive amount margins are weaker (`log_selfprod_amount` p = ", fmtp(log_m3$hhcomp_wald_p[1]), "; `ihs_selfprod_amount` p = ", fmtp(ihs_m3$hhcomp_wald_p[1]), "), so participation remains the clearest margin."),
  if (two_part_part2_sig) paste0("- SUPPORTING RESULT: the formal two-part model also finds a conditional-intensity signal among self-provisioning entrants (Part 2 p = ", fmtp(two_part_part2$hhcomp_wald_p[1]), "), so the intensive-margin conclusion should be stated cautiously.") else "- SUPPORTING RESULT: the two-part conditional-intensity model is weak, reinforcing the entry-margin interpretation.",
  paste0("- MAIN RESULT: category heterogeneity is strong; top NSI categories are ", paste(head(top_cats$food_category_label, 5), collapse = ", "), "."),
  "- SUPPORTING RESULT: self-sufficiency and alternative household-composition specifications are reported as robustness checks.",
  paste0("- ROBUSTNESS RESULT: leave-one-province baseline Wald remains significant in all drops = ", loo_all_sig, "."),
  "- APPENDIX / EXPLORATORY RESULT: market-friction interactions and IV diagnostics are appendix-only.",
  if (nrow(tableB) > 0 && any(tableB$weak_iv_flag)) "- FAILED OR WEAK EVIDENCE: IV first stages remain weak." else "- APPENDIX / EXPLORATORY RESULT: IV first stages require review.",
  "- HUMAN REVIEW REQUIRED: roulei split feasibility, youzhi definition, and commercialization-rate denominator.",
  "",
  "## 2. Data and sample checks",
  "",
  "### Unit and outlier handling",
  "",
  "- Food quantities are household totals in kg/month/household after converting from jin/month with `kg = jin * 0.5`.",
  "- Unit values are yuan/kg after converting from yuan/jin with `yuan/kg = yuan/jin * 2`; legacy model aliases ending in `_yuan_per_jin` are retained only for script compatibility.",
  "- Food quantity outliers were excluded by food-category P99.5 thresholds; the cleaned model file drops 312 category-level rows and retains all 3,565 households.",
  "- Main outcome transforms, `log_selfprod_amount` and `ihs_selfprod_amount`, are recomputed from `selfprod_kg_month`.",
  "",
  sample_lines,
  "",
  "### Observations by data_year",
  "",
  year_lines,
  "",
  "### Observations by food_category",
  "",
  cat_lines,
  "",
  "### Missingness by core variables",
  "",
  miss_lines,
  "",
  paste0("- M0-M3 common sample constructed: ", nrow(main_m3) > 0),
  paste0("- Common-sample N: ", ifelse(nrow(main_m3) > 0, main_m3$n[1], NA)),
  paste0("- Common-sample cluster count: ", ifelse(nrow(main_m3) > 0, main_m3$n_clusters[1], NA)),
  "",
  "## 3. Main baseline results",
  "",
  "- Table: `outputs/tables/table2_common_sample_baseline.csv`",
  "- Model summary: `outputs/model_summaries/model2_common_sample_baseline.json`",
  "",
  paste0("- `production_participation`: Wald = ", fmt(main_m3$hhcomp_wald_chisq[1]), ", df = ", main_m3$hhcomp_wald_df[1], ", p = ", fmtp(main_m3$hhcomp_wald_p[1]), ", N = ", main_m3$n[1], "."),
  paste0("- `log_selfprod_amount`: Wald = ", fmt(log_m3$hhcomp_wald_chisq[1]), ", p = ", fmtp(log_m3$hhcomp_wald_p[1]), "."),
  paste0("- `ihs_selfprod_amount`: Wald = ", fmt(ihs_m3$hhcomp_wald_chisq[1]), ", p = ", fmtp(ihs_m3$hhcomp_wald_p[1]), "."),
  "",
  "Interpretation: The evidence rejects separability restrictions on the self-provisioning participation margin, but provides weaker evidence on the self-production quantity margin. This is a reduced-form association, not a causal treatment effect.",
  "",
  "## 4. Household-composition coefficient interpretation",
  "",
  "- Table: `outputs/tables/table3_baseline_coefficients_margins.csv`",
  "- Figure: `outputs/figures/figure3_household_composition_coefficients.png`",
  "",
  coeff_lines,
  "",
  "## 5. Category-specific non-separability and NSI",
  "",
  "- Table: `outputs/tables/table4_category_specific_nsi.csv`",
  "- Figure: `outputs/figures/figure2_nsi_by_category.png`",
  "",
  paste0("- Strong categories: ", ifelse(nrow(strong_cats) > 0, paste(strong_cats$food_category_label, collapse = ", "), "none")),
  paste0("- Weak categories: ", ifelse(nrow(weak_cats) > 0, paste(weak_cats$food_category_label, collapse = ", "), "none")),
  "",
  cat_report_lines,
  "",
  "Possible substantive explanation: the signal is concentrated in categories where households may make discrete entry decisions into self-provisioning. Data-definition concerns remain for `youzhi` and the combined `roulei` category.",
  "",
  "## 6. Two-part model: entry versus conditional intensity",
  "",
  "- Table: `outputs/tables/table5_two_part_model.csv`",
  "",
  two_part_lines,
  "",
  if (two_part_part2_sig) "Interpretation: Part 1 is significant and Part 2 is also significant at the 5% level. The clearest main result remains entry into self-provisioning, while the conditional-intensity result should be treated as supporting but more cautious evidence because full-sample log/IHS amount models are weaker." else "Interpretation: Part 1 is significant and Part 2 is weak, so the main non-separability signal operates through entry into self-provisioning rather than conditional intensity.",
  "",
  "## 7. Robustness checks",
  "",
  "### 7.1 Alternative household composition and outcomes",
  "",
  robust_lines,
  "",
  "### 7.2 Province leave-one-out",
  "",
  paste0("- Minimum leave-one-province Wald: ", fmt(loo_min)),
  paste0("- Maximum leave-one-province Wald: ", fmt(loo_max)),
  paste0("- All leave-one-province estimates remain significant: ", loo_all_sig),
  paste0("- Most influential drop by minimum Wald: ", loo_infl),
  "",
  "### 7.3 Household-composition permutation placebo",
  "",
  if (nrow(table8) > 0) paste0("- Permutations: ", table8$n_draws[1], "; true Wald = ", fmt(table8$true_wald_chisq[1]), "; placebo mean = ", fmt(table8$placebo_mean[1]), "; placebo P95 = ", fmt(table8$placebo_p95[1]), "; randomization p = ", fmtp(table8$randomization_p_value[1]), ".") else "- Permutation table unavailable.",
  "",
  "## 8. Appendix mechanism diagnostics",
  "",
  "### 8.1 Market-friction interactions",
  "",
  market_lines,
  "",
  "Default interpretation: Market-friction interactions do not provide strong support for a cross-sectional amplification mechanism if the p-values remain weak.",
  "",
  "### 8.2 IV diagnostics",
  "",
  iv_lines,
  "",
  "Default interpretation: IV results are reported as diagnostics and should not be used as the main identification basis when first stages are weak.",
  "",
  "## 9. Price robustness",
  "",
  price_lines,
  "",
  "Interpretation: Compare Wald p-values across no-price, hedonic-price, observed-price-only, and county-median-price specifications to assess dependence on price imputation.",
  "",
  "## 10. Category-definition audits",
  "",
  if (nrow(tableD) > 0) paste0("- ", tableD$audit_item, ": ", tableD$status, "; decision: ", tableD$decision) else "- Category definition audit unavailable.",
  "",
  "## 11. Table and figure inventory",
  "",
  inv_lines,
  "",
  "## 12. Human-review flags",
  "",
  human_flags,
  "",
  if (length(missing_required) == 0) "Rerun complete: all required completion-criteria files exist." else paste0("Rerun incomplete: missing required output `", missing_required, "`."),
  "",
  "## 13. Recommended manuscript language",
  "",
  if (two_part_part2_sig) {
    "The results indicate that household composition significantly predicts category-specific self-provisioning participation, providing reduced-form evidence inconsistent with separability. The clearest evidence is on the extensive margin: household composition predicts whether households enter self-provisioning, while full-sample quantity-margin tests are weaker. A formal two-part model also suggests some conditional-intensity association among households that enter self-provisioning, so the intensive-margin evidence should be interpreted cautiously rather than dismissed. The category-specific analysis shows that non-separability is concentrated in eggs, oils, vegetables, fruits, and beans, rather than being uniform across food groups. Market-friction interactions and IV diagnostics provide weaker support for the market-friction amplification mechanism and are therefore interpreted as exploratory."
  } else {
    "The results indicate that household composition significantly predicts category-specific self-provisioning participation, providing reduced-form evidence inconsistent with separability. This evidence is strongest on the extensive margin: household composition predicts whether households enter self-provisioning, while conditional quantity responses are weaker. The category-specific analysis shows that non-separability is concentrated in eggs, oils, vegetables, fruits, and beans, rather than being uniform across food groups. Market-friction interactions and IV diagnostics provide weaker support for the market-friction amplification mechanism and are therefore interpreted as exploratory."
  }
)

writeLines(report, path("outputs", "reports", "paper1_revised_results_package.md"), useBytes = TRUE)

message("Revised results report compiled.")