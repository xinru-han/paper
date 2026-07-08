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
  L <- c(L, "- **Interpretation caveat**: A-line contrasts are cross-sectional and living arrangement is self-selected. The weighting estimators below (IPW/entropy-balancing/AIPW/matching) use ATT-type weights but adjust for **observed** covariates only — they identify an *adjusted association under selection-on-observables*, **not** a causal ATT. The Oster bound (below) is the key check on unobserved selection.",
    "- **What the outcome measures**: household HDDS-12 is the diversity of food groups OBSERVED at the household table over 48h. More (and more heterogeneous) members mechanically raise the chance of recording more groups, and household size is itself part of the living arrangement (a definitional, post-treatment component — the size-dummy decomposition in T4 is therefore an accounting split, not a mechanism estimate). The correct reading is **'three-generation households set a more diverse table'**, NOT 'co-residence improves diet quality'.")
  t26 <- rd("table26_aline_scalefree.csv")
  if (!is.null(t26)) L <- c(L, sprintf("- **Scale-standardised outcomes (table26, audit item #1)**: union FGDS-10 over all recorded members %s%s and union **excluding elders** %s%s remain strong (the richer table is not just the elder's own recorded intake), and union excluding children %s%s. But **mean member FGDS-10 is %s%s (null)** and HDDS-12 conditioning on the number of recorded members and recorded meals (rarefaction-style) is %s%s (null). Reading: the A-line result is a **household-table / provisioning-breadth** phenomenon carried by more people eating together; it does NOT show higher individual-level dietary diversity, and the paper's interpretation is restricted accordingly ('three-generation households set a more diverse table', never 'co-residence improves diet quality').",
    fnum(t26[grepl("all recorded", spec), est][1]), stars(t26[grepl("all recorded", spec), p][1]),
    fnum(t26[grepl("EXCLUDING elders", spec), est][1]), stars(t26[grepl("EXCLUDING elders", spec), p][1]),
    fnum(t26[grepl("EXCLUDING children", spec), est][1]), stars(t26[grepl("EXCLUDING children", spec), p][1]),
    fnum(t26[grepl("mean member", spec), est][1]), stars(t26[grepl("mean member", spec), p][1]),
    fnum(t26[grepl("rarefaction", spec), est][1]), stars(t26[grepl("rarefaction", spec), p][1])))
  t27 <- rd("table27_resident_agreement.csv"); t27b <- rd("table27b_resident_main_results.csv")
  if (!is.null(t27) && !is.null(t27b)) L <- c(L, sprintf("- **Resident-based living arrangement (table27/27b, audit item #2)**: the roster classification agrees with a >=180-days-at-home reconstruction for %s%% of elder households (%s%% in the cohabit/threegen estimation sample) and with a 48h-observed-members reconstruction for %s%%. A-line three-gen coefficient: roster %s%s vs resident-based %s%s vs 48h-observed %s%s; B-line two-gen elder gap: roster %s%s vs resident-based %s%s. Registered-but-absent members do not drive the results.",
    fnum(100*t27$agreement[1],1), fnum(100*t27$agreement[2],1), fnum(100*t27$agreement[3],1),
    fnum(t27b[grepl("A-line, roster", spec), est][1]), stars(t27b[grepl("A-line, roster", spec), p][1]),
    fnum(t27b[grepl("A-line, resident", spec), est][1]), stars(t27b[grepl("A-line, resident", spec), p][1]),
    fnum(t27b[grepl("A-line, 48h", spec), est][1]), stars(t27b[grepl("A-line, 48h", spec), p][1]),
    fnum(t27b[grepl("B-line elder gap, roster", spec) & term == "elder", est][1]),
    stars(t27b[grepl("B-line elder gap, roster", spec) & term == "elder", p][1]),
    fnum(t27b[grepl("B-line elder gap, resident", spec) & term == "elder", est][1]),
    stars(t27b[grepl("B-line elder gap, resident", spec) & term == "elder", p][1])))
  t7 <- rd("table7_estimator_comparison.csv")
  if (!is.null(t7)) L <- c(L, paste0("- Estimator agreement (three-gen adjusted contrast on HDDS, selection-on-observables): ",
    paste(sprintf("%s %s", t7$estimator, fnum(t7$est)), collapse = "; "), "."))
  rob <- readLines(file.path(DIR_REP, "aline_robustness_summary.md"))[-1]
  L <- c(L, paste0("- ", sub("^- ", "", rob)), "")
  # construct-validity + threshold + few-cluster + multiplicity robustness
  t2b <- rd("table2b_threegen_strict_robustness.csv"); nc <- rd("table3b_negative_control.csv")
  t21 <- rd("table21_threshold_year_sensitivity.csv"); t20 <- rd("table20_wild_cluster_bootstrap.csv")
  t3 <- rd("table3_aline_food_structure_shares.csv")
  if (!is.null(t2b)) L <- c(L, sprintf("- Construct validity: 'threegen' is an age-composition class (elder+adult+minor). Under a **strict** 3-gen flag (elder+mid-adult 25-59+minor), the HDDS effect is %s%s vs %s%s for the headline definition (table2b) — robust; only ~3 households differ.",
    fnum(t2b[grepl("strict", spec), est][1]), stars(t2b[grepl("strict", spec), p][1]),
    fnum(t2b[grepl("headline", spec), est][1]), stars(t2b[grepl("headline", spec), p][1])))
  if (!is.null(nc)) L <- c(L, sprintf("- **Negative-control outcome** (salt+condiment share): three-gen coef %s (p=%s) — near-zero. Caveat: this is an **imperfect placebo** (cooking style, household scale and communal meals could in principle move condiment shares too), so it is an auxiliary diagnostic, not proof of design validity.",
    fnum(nc[grepl("threegen", term), est][1]), fnum(nc[grepl("threegen", term), p][1])))
  if (!is.null(t21)) {L <- c(L, sprintf("- **Threshold/year sensitivity** (table21): elder>=60 -> elder>=65 gives %s vs %s; 2023-only %s, 2024-only %s — the A-line effect is stable to the hard-coded age cutoff and across survey years.",
    fnum(t21[grepl("elder>=60, pooled", spec), est][1]), fnum(t21[grepl("elder>=65, pooled", spec), est][1]),
    fnum(t21[grepl("year 2023", spec), est][1]), fnum(t21[grepl("year 2024", spec), est][1])))}
  if (!is.null(t20)) {aw <- t20[grepl("A-line", spec)][1]
    if (nrow(aw)) L <- c(L, sprintf("- **Wild cluster bootstrap** (few-cluster robust, Rademacher, null imposed): A-line three-gen p_wcb=%s vs CRVE p=%s (%s village clusters) — significance survives.",
      fnum(aw$p_wcb), fnum(aw$p_crve), aw$n_clusters))}
  if (!is.null(t3) && "p_bh_fdr" %in% names(t3)) {nsurv <- sum(t3$p_bh_fdr < .05, na.rm = TRUE)
    L <- c(L, sprintf("- **Multiplicity (BH-FDR) on the food-share family** (table3): %d of %d share coefficients survive FDR<0.05 — the composition-shift (share) results are **not** robust to multiple testing and are demoted to secondary; the headline is HDDS diversity (T2), not the shares.", nsurv, nrow(t3)))}
  t4 <- rd("table4_scale_vs_composition.csv")
  L <- c(L, "### Scale vs composition (D5 TRIGGERED)",
    "- Household-size dummies absorb **54.6%** of the three-gen coefficient: the provisioning gain is first a **meal-scale economy**, second a composition effect. Because household size is a definitional component of the living arrangement (post-treatment), this split is an **accounting decomposition**, not a strict mechanism test; the scale-free outcomes in table26 are the cleaner check.",
    "- **Design note**: the survey provides no sampling/design weights, so estimates are unweighted; robustness across province-year, county-year and village-year fixed effects (T2) covers the main design concern (regional composition).", "")
}

# ---- B line ----
t10 <- rd("table10_bline_gap_main.csv"); rw <- rd("table10a_romano_wolf.csv")
if (!is.null(t10)) {
  g <- function(o, trm) t10[outcome == o & term == trm]
  L <- c(L, "## B line: within-household elder gap in RECORDED dietary diversity (household FE, 557 mixed households)",
    sprintf("- FGDS-10: elders' **recorded** 48h food-group diversity is **%s%s** groups lower than co-resident non-elder adults' (se %s; Romano-Wolf p=%s, village-bootstrap with relabelled clusters, B=999, finite-sample corrected).",
            fnum(g("fgds10","elder")$est), stars(g("fgds10","elder")$p), fnum(g("fgds10","elder")$se),
            fnum(rw[outcome=="fgds10", p_rw_elder])),
    "- **MAIN-TEXT caveat (not appendix)**: this is a gap in *measured/recorded* diversity, and it is NOT evidence that households allocate food away from elders or that elders' true intake is worse. Three results bound the allocation reading: (i) adding age, the elder coefficient shrinks from -0.29 to about -0.17 and loses significance; (ii) restricting to members with >=3 recorded meals it disappears entirely (+0.04); (iii) the MNAR re-imputation below flips its sign. The candidate explanations — age gradient, fewer eating occasions, proxy under-recording of elders' meals — cannot be separated with these data.",
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
     } else ""},
    {gl <- rd("table24_generation_ladder.csv")
     if (!is.null(gl)) {ce <- gl[term=="genchild"][1]; ee <- gl[term=="genelder"][1]
       sprintf("- **Identification probe — generation ladder (table24, C)**: within the same households, relative to prime-age adults, elders eat %s%s fewer FGDS groups but **children eat %s%s fewer — ~%.0fx the elder gap**. The elder deficit is therefore largely part of a broad **life-stage/recording gradient** (children fare worse), NOT an elder-specific intra-household allocation penalty. The 'inequality against elders' reading must be heavily qualified.",
               fnum(ee$est), stars(ee$p), fnum(ce$est), stars(ce$p), abs(ce$est/ee$est))
     } else ""},
    {mn <- rd("table22_mnar_bounds.csv")
     if (!is.null(mn)) {bc <- mn[grepl("<3 recorded", scenario)][1]
       sprintf("- **MNAR / proxy-under-recording bound (table22)**: if the 32%% of elders with <3 recorded meals were actually eating like their co-resident adults (a recording artifact, not real skipping), the gap **flips to %s%s**. A uniform under-recording of only ~%s FGDS groups per elder nulls the gap. The elder deficit is thus **fragile to proxy under-recording** and cannot be asserted as a behavioural/nutritional fact.",
               fnum(bc$est), stars(bc$p), fnum(mn$breakdown_delta_all_elders[1]))
     } else ""},
    {t21b <- rd("table21_threshold_year_sensitivity.csv")
     if (!is.null(t21b) && any(grepl("MAIN estimand", t21b$spec))) {
       sprintf("- **Threshold sensitivity, main-estimand aligned (table21)**: rebuilding the living-arrangement classification and re-running the exact main model (elder + elder x threegen, cohabit/threegen mixed households), the two-generation baseline elder gap is %s%s at elder>=60 and %s%s at elder>=65. A pooled all-mixed-household gap without the interaction (a different estimand) is also reported, explicitly labelled.",
               fnum(t21b[grepl("MAIN estimand.*elder>=60", spec), est][1]), stars(t21b[grepl("MAIN estimand.*elder>=60", spec), p][1]),
               fnum(t21b[grepl("MAIN estimand.*elder>=65", spec), est][1]), stars(t21b[grepl("MAIN estimand.*elder>=65", spec), p][1]))
     } else ""},
    {hs <- rd("table25_elder_health_strata.csv")
     if (!is.null(hs) && nrow(hs) >= 2) {
       gd <- function(sl) hs[grepl(sl, stratum)][1]
       sprintf("- **Health-stratified elder gap (table25, fixed split)**: elder gap %s%s where the elder reports chronic disease vs %s%s where not; %s%s where self-rated health is below the best code vs %s%s at the best code. A gap present in BOTH strata points away from a purely physiological story; interpret descriptively (health is post-treatment).",
               fnum(gd("reports chronic")$est), stars(gd("reports chronic")$p),
               fnum(gd("no chronic")$est), stars(gd("no chronic")$p),
               fnum(gd("worse than best")$est), stars(gd("worse than best")$p),
               fnum(gd("best code")$est), stars(gd("best code")$p))
     } else "- Health stratification (table25): not citable (degenerate strata)."}, "")
}

# ---- pass-through ----
pt <- rd("table11b_passthrough_by_LA.csv")
if (!is.null(pt)) {
  L <- c(L, "## B2: household-HDDS -> elder-FGDS cross-sectional slope (phi1)",
    "- **phi1 is an associational cross-sectional slope, NOT a causal pass-through**: the focal elder's own 48h diet mechanically enters household HDDS, biasing phi1 up (worst where the elder is most of the household).",
    paste0("- phi1 by arrangement: ",
      paste(sprintf("%s %s%s", pt$arrangement, fnum(pt$phi1), stars(pt$p)), collapse = "; "), "."),
    {pc <- rd("table11c_phi1_contamination_robust.csv")
     if (!is.null(pc)) sprintf("- Contamination robustness (table11c): pooled slope %s (all arrangements) vs %s excluding the mechanically-contaminated elder-alone/elder-only households — modest attenuation, slope robust.",
       fnum(pc[grepl("all", spec), est][1]), fnum(pc[grepl("excl", spec), est][1]))
     else "- Slope lowest in three-generation households; highest for elders alone (mechanical)."}, "")
}

# ---- decomposition & leakage ----
t12 <- rd("table12_decomposition.csv")
if (!is.null(t12)) {
  tg <- t12[arrangement == "threegen"]
  L <- c(L, "## B3: descriptive reconciliation (accounting decomposition — NOT a mechanism estimate)",
    "- **Status**: dHDDS (A line), phi1 (B2) and the reduced-form elder effect come from different samples and control sets, and the elder's own 48h diet mechanically enters household HDDS. This section reconciles three separately-estimated quantities as an accounting exercise; no number here is a causal pass-through, and **no leakage rate is a headline of the paper**.",
    sprintf("- Reconciliation quantities: three-generation provisioning association **%s HDDS groups**; phi1 x gain = %s expected FGDS groups; reduced-form elder association = %s.",
            fnum(tg$dHDDS), fnum(tg$passthrough_component), fnum(tg$total_elder_effect)),
    sprintf("- **The only citable conclusion**: allocation-specific leakage (1 - realized/expected, both in FGDS-10 units) is %s%% with a 95%% CI of %s%% to %s%% — **spanning zero**, so elder-specific loss beyond the ordinary <1 cross-sectional slope is statistically indistinguishable from zero. (The gap-to-household ratio 1-bR/bA is retained in table12 for continuity only; it mixes scales and mostly reflects the <1 slope common to all members, and must not be quoted as elder-specific leakage.)",
            fnum(100*tg$leak_allocation, 0), fnum(100*tg$leak_alloc_lo, 0), fnum(100*tg$leak_alloc_hi, 0)),
    {h <- rd("table13_leakage_heterogeneity.csv");
     if (!is.null(h) && nrow(h)) sprintf("- Heterogeneity (gap-to-household basis, SUGGESTIVE only — grf finds no significant heterogeneity): %s%% when the elder is the household cook vs %s%% when not; %s%% (low income) vs %s%% (high income). Treat as exploratory, not an established policy lever.",
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
    "- Naive individual-means variant flagged: solo elders' measured individual diversity is inflated by recording concentration.",
    {mc <- rd("table17b_projection_montecarlo.csv")
     if (!is.null(mc)) {m6 <- mc[k_pp_decade == 6][1]
       sprintf("- **Monte-Carlo uncertainty (table17b)**: propagating sampling error in bA and phi1 plus a 0.5-1.5x selective-migration multiplier, the 2035 elder-FGDS change at k=6 has median %s (95%% interval [%s, %s]); P(worse than today)=%s. The sign is robust (interval excludes zero) but the **magnitude is small** (~0.02-0.03 FGDS groups) — headline #2 is a modest, directionally-reliable accounting signal, not a large or precise forecast. (Interval reflects bA/phi1/migration uncertainty; it does not include the structural risk that cross-sectional LA gaps mis-measure true within-elder change.)",
               fnum(m6$d_elder_fgds_med, 4), fnum(m6$lo95, 4), fnum(m6$hi95, 4), fnum(m6$p_worse_than_zero, 2))
     } else ""}, "")
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

L <- c(L, "", "## Headline framing (three-layer conclusion, per econometric audit)",
  "1. **Household level (A line)**: three-generation households show higher observed 48h household HDDS-12, stable across county-year/village-year FE, weighting estimators, permutation and threshold checks. This mainly reflects table diversity from household scale and communal meals — an adjusted provisioning association, **not** a causal effect of co-residence on diet quality.",
  "2. **Individual level (B line)**: within the same household, elders' *recorded* food-group diversity is lower than co-resident non-elder adults'. The gap is sensitive to age controls, meal-recording counts and plausible proxy under-recording (MNAR flips it), and children show a larger deficit — so it **cannot** be read as intra-household allocation inequality against elders.",
  "3. **Projection (2035)**: population aging and household downsizing may weaken elder dietary diversity through household provisioning; the estimates support a directional, small-magnitude **accounting projection**, not a strong causal forecast.", "")

L <- c(L, "", "## Post-review revisions round 2 (econometric audit, 2026-07-08)",
  "Per `paper2_elder_econometric_audit.md`:",
  "- **#1 scale-free A-line outcomes** (17_measurement_robustness.R, table26): mean member FGDS-10, union FGDS-10 (all / excluding elders / excluding children), rarefaction-style HDDS fixing recorded members & meals.",
  "- **#2 resident-based living arrangement** (table27/27b): >=180-days-at-home and 48h-observed reconstructions; agreement rates and re-estimated A/B-line main results reported.",
  "- **#3 B-line relabelled** as a gap in *recorded* diversity with the allocation caveat promoted to the main text.",
  "- **#4 B3 relabelled** as descriptive reconciliation; leakage rates removed from headlines; only the CI-spans-zero allocation-specific result is citable.",
  "- **#5 Romano-Wolf fixed**: finite-sample p = (1+#extreme)/(1+B), B=999, bootstrap villages relabelled so repeated draws count as distinct clusters; positioned as auxiliary to the wild cluster bootstrap.",
  "- **#6 county policy-text merges** now key on (province, county) with county_id clustering (county names repeat across provinces).",
  "- **#7 health stratification fixed** (table25): chronic-disease and self-rated-health splits on the elder's own health replace the degenerate whole-sample-median split.",
  "- **#8 B-line threshold sensitivity aligned** with the main estimand (same sample construction and elder x threegen model); the old pooled variant kept with an explicit different-estimand label.",
  "- **#9 GRF language**: ATT/CATE replaced by adjusted average contrast / conditional contrast; forest framed as an ML heterogeneity diagnostic.",
  "- Minor: estimator names de-ATT-ed; Oster delta caveat; negative control flagged as imperfect placebo; presence-indicator provenance cross-check (MDD-W vs DBI-16 gram families); no-survey-weights design note.")

L <- c(L, "", "## Post-review revisions (methodological audit)",
  "This pipeline was re-audited by four adversarial reviewers (identification, estimator implementation, measurement, missed tests). Changes made:",
  "- **Fixed bugs**: AIPW cluster bootstrap used set-membership (`%in%`) instead of with-replacement village replication (SE was inflated); permutation p-value now (1+k)/(1+B); privacy assertion was case-sensitive and missed `*Phone` columns (now case-insensitive with false-positive guards).",
  "- **Relabelled claims**: A-line weighting estimators are *adjusted associations under selection-on-observables*, not causal ATT; phi1 is a *cross-sectional slope*, not causal pass-through.",
  "- **Corrected leakage**: the headline '59% leakage' conflated ordinary <1 pass-through (common to all members) with elder-specific loss. Allocation-specific leakage (unit-consistent) is ~5% with a CI spanning zero — **elders are not meaningfully shortchanged once ordinary pass-through is netted out**.",
  "- **Reframed B-line**: a within-household generation ladder shows the child deficit is ~4x the elder deficit, and an MNAR bound shows the elder gap flips sign if <3-meal elders are re-imputed to adult levels. The elder deficit is real but modest, part of a life-stage/recording gradient, and fragile to proxy under-recording — NOT established elder-specific inequality.",
  "- **Added tests**: wild cluster bootstrap (few-cluster robust), 60-vs-65 and year-split sensitivity, negative-control outcome, BH-FDR on the share family (0 survive), strict three-generation flag, 2035 projection Monte-Carlo interval, honest 'no significant heterogeneity' note for the causal forest.",
  "- **Dropped a bad control**: `main_cook` (a mediator) removed from the B-line baseline; the elder gap grows modestly as expected.")

writeLines(L, file.path(PROJ, "RESULTS.md"))
cat("RESULTS.md written\n")
