# Task 3 — nutrient unit audit

Sample: adults (18+) with >=4 recorded meals in the 48h window.
Daily intakes = 48h totals / 2, from `48h_nutrients_person_meal_long_corrected.csv`.

          nutrient   unit    n     median        p5        p95 pct_outside_hard
1: energy_kcal_day kcal/d 2673 7.41627031 0.9551659 561.732791         92.44295
2:     protein_day    g/d 2673 0.25517000 0.0499360  17.584000         92.63000
3:          ca_day   mg/d 2673 0.95750000 0.1928700  50.923936         95.54807
4:          fe_day   mg/d 2673 0.07862067 0.0173194   5.620719         88.73924
5:          zn_day   mg/d 2673 0.03537250 0.0077281   2.601761         91.35802
    pass
1: FALSE
2: FALSE
3: FALSE
4: FALSE
5: FALSE

## Forensic evidence
- Person-level 48h total edible grams: p5=0.6 p25=2.5 median=5.2 p75=12.3 p95=372.8 (plausible ~1500-6000 g)
- Share of adults with 48h total food mass < 100 g: 85.8% — physically impossible, indicates amount fields recorded in mixed/undocumented units
- Meal-level nutrient columns behave as per-gram densities (median energy 1.8 kcal per unit), so person totals inherit the same unit chaos.
- The '_corrected' and merged-table daily-intake exports (p*_d1_ekcal) show medians of ~9-18 kcal/day and maxima of 1e17 — corrupted upstream.

## VERDICT: FAIL — decision node D1/D6 triggered.

### Consequences (pre-registered fallback, proposal §12 D1 / §21 D6)
- Absolute nutrient quantities (energy, protein, Ca, Fe, Zn) and DRI adequacy ratios (AR) are SEALED for the whole portfolio until upstream repair.
- B line runs on count-based diversity indices (fgds10, FVS, wdds9, DBI variety), which are invariant to amount-unit errors.
- Binary outcomes 'any intake of group g in 48h' (grams > 0) are retained: presence/absence is unit-robust (R6).
- The quality-protein gram share is reported only as a flagged secondary outcome: shares cancel multiplicative unit errors only if the unit is consistent within person.
- The aging projection (T13) reports diversity metrics only (D6).
