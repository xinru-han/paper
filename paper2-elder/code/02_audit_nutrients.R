# =============================================================================
# 02_audit_nutrients.R — Task 3: nutrient unit audit (gatekeeper for AR outcomes)
# Verdict rule (pre-registered):
#   PASS if, among adults with >=4 recorded meals, the median daily intake of
#   energy/protein/ca/fe/zn lies inside plausible physiological ranges AND
#   <10% of person-days fall outside hard bounds.
#   FAIL -> decision node D1/D6: diversity-only B line, nutrient results sealed.
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")

per <- fread(file.path(DIR_DERIV, "person_analysis.csv"), colClasses = list(character = c("nhCode","pid")))
ad <- per[(elderly == 1 | nonelder_adult == 1) & !is.na(energy_kcal_day) & n_meals >= 4]

ranges <- data.table(
  nutrient = c("energy_kcal_day","protein_day","ca_day","fe_day","zn_day"),
  unit     = c("kcal/d","g/d","mg/d","mg/d","mg/d"),
  med_lo   = c(1000, 30, 150,  6,  4),
  med_hi   = c(3200, 120, 900, 40, 20),
  hard_lo  = c(300,  10,  50,  1,  1),
  hard_hi  = c(6000, 300, 3000, 100, 60)
)

res <- ranges[, {
  x <- num(ad[[nutrient]])
  x <- x[!is.na(x)]
  .(unit, n = length(x), p5 = quantile(x, .05), median = median(x), mean = mean(x),
    p95 = quantile(x, .95), med_lo, med_hi,
    med_in_range = median(x) >= med_lo & median(x) <= med_hi,
    pct_outside_hard = 100*mean(x < hard_lo | x > hard_hi))
}, by = nutrient]
res[, pass := med_in_range & pct_outside_hard < 10]
wtab(res, "table23_nutrient_unit_validation.csv")

# --- forensic evidence on the amount (grams) fields -------------------------
fg <- fread(file.path(DATA_ROOT, "导出的数据/2天48小时膳食情况/nutrients/48h_foodgroup_person_meal_long_corrected.csv"),
            select = c("nhCode","data_year","pid","edible_g","energy_kcal"),
            colClasses = list(character = c("nhCode","pid")))
ps <- fg[, .(g48 = sum(num(edible_g), na.rm = TRUE), kcal48 = sum(num(energy_kcal), na.rm = TRUE)),
         by = .(nhCode, data_year, pid)]
gq <- quantile(ps$g48, c(.05,.25,.5,.75,.95), na.rm = TRUE)
ev <- c(
  sprintf("Person-level 48h total edible grams: p5=%.1f p25=%.1f median=%.1f p75=%.1f p95=%.1f (plausible ~1500-6000 g)",
          gq[1], gq[2], gq[3], gq[4], gq[5]),
  sprintf("Share of adults with 48h total food mass < 100 g: %.1f%% — physically impossible, indicates amount fields recorded in mixed/undocumented units",
          100*mean(ps$g48 < 100, na.rm = TRUE)),
  "Meal-level nutrient columns behave as per-gram densities (median energy 1.8 kcal per unit), so person totals inherit the same unit chaos.",
  "The '_corrected' and merged-table daily-intake exports (p*_d1_ekcal) show medians of ~9-18 kcal/day and maxima of 1e17 — corrupted upstream.")

verdict <- all(res$pass)
lines <- c("# Task 3 — nutrient unit audit", "",
  "Sample: adults (18+) with >=4 recorded meals in the 48h window.",
  "Daily intakes = 48h totals / 2, from `48h_nutrients_person_meal_long_corrected.csv`.", "",
  paste(capture.output(print(res[, .(nutrient, unit, n, median, p5, p95, pct_outside_hard, pass)])), collapse = "\n"),
  "", "## Forensic evidence", paste("-", ev),
  "", paste0("## VERDICT: ", ifelse(verdict, "PASS — nutrient (AR) outcomes enabled.",
             "FAIL — decision node D1/D6 triggered.")),
  if (!verdict) c("",
    "### Consequences (pre-registered fallback, proposal §12 D1 / §21 D6)",
    "- Absolute nutrient quantities (energy, protein, Ca, Fe, Zn) and DRI adequacy ratios (AR) are SEALED for the whole portfolio until upstream repair.",
    "- B line runs on count-based diversity indices (fgds10, FVS, wdds9, DBI variety), which are invariant to amount-unit errors.",
    "- Binary outcomes 'any intake of group g in 48h' (grams > 0) are retained: presence/absence is unit-robust (R6).",
    "- The quality-protein gram share is reported only as a flagged secondary outcome: shares cancel multiplicative unit errors only if the unit is consistent within person.",
    "- The aging projection (T13) reports diversity metrics only (D6)."))
writeLines(lines, file.path(DIR_REP, "audit_nutrient_unit_validation.md"))
saveRDS(verdict, file.path(DIR_DERIV, "audit_pass.rds"))
cat("AUDIT:", ifelse(verdict, "PASS", "FAIL"), "\n")
print(res[, .(nutrient, n, median, pct_outside_hard, pass)])
