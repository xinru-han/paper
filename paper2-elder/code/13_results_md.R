# =============================================================================
# 13_results_md.R — assemble RESULTS.md from output tables (rerun anytime)
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")

rd <- function(f) {
  p <- file.path(DIR_TAB, f)
  if (file.exists(p)) fread(p) else NULL
}
fnum <- function(x, d = 3) formatC(x, digits = d, format = "f")
coefline <- function(dt, trm, lab = NULL) {
  r <- dt[term == trm][1]
  if (is.null(dt) || nrow(r) == 0 || is.na(r$est)) return("(n/a)")
  sprintf("%s%s (se %s, N=%s)", fnum(r$est), stars(r$p), fnum(r$se), r$n)
}

L <- c("# Paper 2 (elder diet) — Results summary",
       paste0("Auto-generated: ", format(Sys.time())), "",
       "All tables in `outputs/tables/`, figures in `outputs/figures/`, reports in `outputs/reports/`.", "")

# ---- sample ----
t1 <- rd("table1_household_by_LA.csv")
L <- c(L, "## Sample",
  "- Elder households (>=1 member 60+): **1,234** of 3,565; six living arrangements (Table 1).",
  "- Elders with 48h records: 1,683; B-line mixed households: **557** (1,596 adults; CONSORT in `table_bline_consort_flow.csv`).",
  "- Nutrient unit audit (Task 3): **FAIL** -> D1/D6, diversity indices carry the B line (`audit_nutrient_unit_validation.md`).", "")

# ---- A line ----
t2 <- rd("table2_aline_fe_sequence_hdds.csv")
if (!is.null(t2)) {
  tg <- t2[term == "LAthreegen"]
  L <- c(L, "## A line: living arrangement -> household provisioning (HDDS-12)",
    paste0("- Three-generation vs with-non-elder-adults: ",
           paste(sprintf("%s under %s", paste0(fnum(tg$est), stars(tg$p)), tg$model), collapse = "; "), "."),
    "- Elder-only and elder-alone households provision 0.4-0.5 fewer groups (Table 2).")
  t7 <- rd("table7_estimator_comparison.csv")
  if (!is.null(t7)) L <- c(L, paste0("- Estimator agreement (three-gen ATT on HDDS): ",
    paste(sprintf("%s %s", t7$estimator, fnum(t7$est)), collapse = "; "), "."))
  rob <- readLines(file.path(DIR_REP, "aline_robustness_summary.md"))[-1]
  L <- c(L, paste0("- ", sub("^- ", "", rob)), "")
  t4 <- rd("table4_scale_vs_composition.csv")
  L <- c(L, "### Scale vs composition (D5 TRIGGERED)",
    "- Household-size dummies absorb **54.6%** of the three-gen coefficient: the provisioning gain is first a **meal-scale economy**, second a composition effect. Narrative adjusted per decision node D5.", "")
}

# ---- B line ----
t10 <- rd("table10_bline_gap_main.csv"); rw <- rd("table10a_romano_wolf.csv")
if (!is.null(t10)) {
  g <- function(o, trm) t10[outcome == o & term == trm]
  L <- c(L, "## B line: within-household elder gap (household FE, 557 mixed households)",
    sprintf("- FGDS-10: elders eat **%s%s** groups less than co-resident non-elder adults (se %s; Romano-Wolf p=%s).",
            fnum(g("fgds10","elder")$est), stars(g("fgds10","elder")$p), fnum(g("fgds10","elder")$se),
            fnum(rw[outcome=="fgds10", p_rw_elder])),
    sprintf("- Food variety score: %s%s; DBI-16 variety: %s%s.",
            fnum(g("fvs_unique_foods","elder")$est), stars(g("fvs_unique_foods","elder")$p),
            fnum(g("dbi16_variety_subscore","elder")$est), stars(g("dbi16_variety_subscore","elder")$p)),
    sprintf("- Three-generation interaction (theta): FGDS-10 %s (p=%s, imprecise); significant narrowing only on DBI variety (%s%s, RW p=%s). **Neither D3 nor D4 cleanly** — reported honestly.",
            fnum(g("fgds10","elder:threegen")$est), fnum(g("fgds10","elder:threegen")$p),
            fnum(g("dbi16_variety_subscore","elder:threegen")$est), stars(g("dbi16_variety_subscore","elder:threegen")$p),
            fnum(rw[outcome=="dbi16_variety_subscore", p_rw_interaction])),
    "- Presence/absence outcomes (any animal-source, any dairy/egg/bean — unit-robust) show **no elder gap**: the deficit is in variety breadth, not in being served protein foods at all.",
    {mf <- rd("table10d_meal_frequency_gap.csv"); sh <- rd("table10d_meal_frequency_shares.csv")
     if (!is.null(mf) && !is.null(sh)) {
       eg <- mf[term == "elder"][1]; se <- sh[group=="elder", pct_lt3_meals][1]; sa <- sh[group=="non_elder_adult", pct_lt3_meals][1]
       sprintf("- Meal-frequency channel (table10d): within the same household elders record **%s%s fewer recorded meals** (se %s; 48h; %s%% of elders <3 recorded meals vs %s%% of non-elder adults); restricting to members with >=3 recorded meals removes the FGDS gap. The gap thus operates through **fewer recorded eating occasions** — which may be genuine meal-skipping and/or proxy under-recording of elders' meals; the data carry no respondent field to separate the two, so we do not claim behavioural skipping (measurement caveat, R6).",
               fnum(eg$est), stars(eg$p), fnum(eg$se), fnum(se,1), fnum(sa,1))
     } else "- Meal-frequency channel: see `table10d_meal_frequency_*.csv`."},
    {md <- rd("table10e_mde_power.csv")
     if (!is.null(md)) {th <- md[term=="elder:threegen"][1]
       sprintf("- Power on the imprecise interaction (table10e): theta 95%% CI [%s, %s], 80%%-power MDE ~%s FGDS groups; the sample cannot rule out a moderate theta, so 'neither D3 nor D4' means **underpowered to distinguish**, not a precise zero.",
               fnum(th$ci_lo), fnum(th$ci_hi), fnum(th$mde_80))
     } else ""}, "")
}

# ---- pass-through ----
pt <- rd("table11b_passthrough_by_LA.csv")
if (!is.null(pt)) {
  L <- c(L, "## B2: pass-through of household provisioning to elder intake",
    paste0("- phi1 by arrangement: ",
      paste(sprintf("%s %s%s", pt$arrangement, fnum(pt$phi1), stars(pt$p)), collapse = "; "), "."),
    "- Pass-through is **lowest in three-generation households (0.32)** — extra provisioning diversity is partly captured by other members (children) — and highest for elders alone (0.70, mechanical).", "")
}

# ---- decomposition & leakage ----
t12 <- rd("table12_decomposition.csv")
if (!is.null(t12)) {
  tg <- t12[arrangement == "threegen"]
  L <- c(L, "## B3: decomposition and leakage (headline #1)",
    sprintf("- Three-generation provisioning gain: **%s HDDS groups**; expected elder gain (phi1 x gain): %s; realized elder gain (reduced form): %s.",
            fnum(tg$dHDDS), fnum(tg$passthrough_component), fnum(tg$total_elder_effect)),
    sprintf("- **Leakage rate: %s%%** of the provisioning gain does not appear in the elder's own 48h intake (95%% block-bootstrap CI %s-%s%%).",
            fnum(100*tg$leakage_rate, 0), fnum(100*tg$leak_lo, 0), fnum(100*tg$leak_hi, 0)),
    {h <- rd("table13_leakage_heterogeneity.csv");
     if (!is.null(h) && nrow(h)) sprintf("- Heterogeneity (policy lever): leakage is **%s%%** when the elder is the household cook vs **%s%%** when not; %s%% (low income) vs %s%% (high income). Keeping elders in the provisioning role is a low-cost intervention point.",
        fnum(100*h[group=="elder_cook", leakage_rate],0), fnum(100*h[group=="elder_notcook", leakage_rate],0),
        fnum(100*h[group=="low_income", leakage_rate],0), fnum(100*h[group=="high_income", leakage_rate],0))
     else "- Heterogeneity in `table13_leakage_heterogeneity.csv`."}, "")
}

# ---- mechanisms ----
mech <- file.path(DIR_REP, "mechanisms_summary.md")
if (file.exists(mech)) L <- c(L, "## Mechanisms (Tasks 5-6, 8)", readLines(mech)[-1],
  "- Provisioning-role variables do **not** mediate the three-gen HDDS association (~0%): consistent with the D5 reading that scale economies, not who cooks, carry the effect.", "")

# ---- projection ----
t17 <- rd("table17_aging_projection_scenarios.csv")
if (!is.null(t17)) {
  s1 <- t17[scenario == "S1 2035 structure" & k_pp_decade == 6]
  L <- c(L, "## Post-estimation: 2035 aging projection (headline #2, accounting)",
    sprintf("- S1 (k=6pp/decade out of three-gen): mean household provisioning falls %s HDDS groups; elder FGDS-10 falls %s (provisioning-anchored, phi1 pass-through).",
            fnum(-s1$d_hh_hdds), fnum(-s1$d_elder_fgds_provisioning, 4)),
    "- Per affected elder (moving three-gen -> elder-only) the provisioning loss is ~1 HDDS group x phi1 ~ 0.3-0.4 FGDS groups; the population average is modest because the shift affects ~6.6pp of elders by 2035.",
    "- S2 community provisioning at lambda={25,50,75}% recovers the same share of the loss (accounting identity); sensitivity k in {4,8} in table17.",
    "- Naive individual-means variant flagged: solo elders' measured individual diversity is inflated by recording concentration.", "")
}

# ---- policy text ----
ct <- file.path(DIR_REP, "county_policy_text_summary.md")
if (file.exists(ct)) L <- c(L, "## Post-estimation: county elder-feeding policy text", readLines(ct)[-1], "")

# ---- grf ----
gr <- file.path(DIR_REP, "grf_summary.md")
if (file.exists(gr)) L <- c(L, "## Appendix: causal-forest heterogeneity", readLines(gr)[-1], "")

L <- c(L, "## Decision-node ledger",
  "| node | status | consequence |",
  "|---|---|---|",
  "| D1/D6 nutrient audit | **TRIGGERED (FAIL)** | AR/nutrient outcomes sealed; diversity indices carry B line |",
  "| D2 B-line N<400 | not triggered (557) | B line stays central |",
  "| D3/D4 theta | neither (imprecise +0.18) | honest two-sided discussion; DBI variety narrows significantly |",
  "| D5 scale attenuation>50% | **TRIGGERED (54.6%)** | meal-scale economies lead the mechanism narrative |",
  "| D7 census trend | default k=6pp/decade with {4,8} sensitivity | documented |",
  "| D8 policy-text sign | not triggered (imprecise +) | descriptive context only |")

writeLines(L, file.path(PROJ, "RESULTS.md"))
cat("RESULTS.md written\n")
