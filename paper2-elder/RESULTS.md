# Paper 2 (elder diet) — Results summary
Auto-generated: 2026-07-07 21:24:46

All tables in `outputs/tables/`, figures in `outputs/figures/`, reports in `outputs/reports/`.

## Sample
- Elder households (>=1 member 60+): **1,234** of 3,565; six living arrangements (Table 1).
- Elders with 48h records: 1,683; B-line mixed households: **557** (1,596 adults; CONSORT in `table_bline_consort_flow.csv`).
- Nutrient unit audit (Task 3): **FAIL** -> D1/D6, diversity indices carry the B line (`audit_nutrient_unit_validation.md`).

## A line: living arrangement -> household provisioning (HDDS-12)
- Three-generation vs with-non-elder-adults: 0.533*** under year_FE; 0.529*** under prov_year_FE; 0.519*** under county_year_FE; 0.516*** under county_year_FE_env; 0.518*** under village_year_FE.
- Elder-only and elder-alone households provision 0.4-0.5 fewer groups (Table 2).
- **Interpretation caveat**: A-line contrasts are cross-sectional and living arrangement is self-selected. The weighting estimators below (IPW/entropy-balancing/AIPW/matching) adjust for **observed** covariates only — they identify an *adjusted association under selection-on-observables*, **not** a causal ATT. The Oster bound (below) is the key check on unobserved selection.
- Estimator agreement (three-gen adjusted contrast on HDDS, selection-on-observables): OLS_countyFE 0.532; IPW_ATT 0.581; EntropyBal_ATT 0.586; NN_match_caliper 0.567; AIPW_ATT 0.592.
- Permutation p-value (1000 within-village reshuffles): 0.001
- Oster beta* (delta=1, Rmax=1.3 R2): 0.579 (OLS long: 0.566); delta for beta=0: -44.08
- Estimator range: 0.532 to 0.592
- Matched sample: 254 pairs of 262 treated

- Construct validity: 'threegen' is an age-composition class (elder+adult+minor). Under a **strict** 3-gen flag (elder+mid-adult 25-59+minor), the HDDS effect is 0.569*** vs 0.547*** for the headline definition (table2b) — robust; only ~3 households differ.
- **Negative control** (salt+condiment share, should be unaffected): three-gen coef -0.003 (p=0.758) — near-zero, so the HDDS result is not a generic 'big households buy more of everything' artifact.
- **Threshold/year sensitivity** (table21): elder>=60 -> elder>=65 gives 0.547 vs 0.542; 2023-only 0.612, 2024-only 0.495 — the A-line effect is stable to the hard-coded age cutoff and across survey years.
- **Wild cluster bootstrap** (few-cluster robust, Rademacher, null imposed): A-line three-gen p_wcb=0.001 vs CRVE p=0.000 (304 village clusters) — significance survives.
- **Multiplicity (BH-FDR) on the food-share family** (table3): 0 of 30 share coefficients survive FDR<0.05 — the composition-shift (share) results are **not** robust to multiple testing and are demoted to secondary; the headline is HDDS diversity (T2), not the shares.
### Scale vs composition (D5 TRIGGERED)
- Household-size dummies absorb **54.6%** of the three-gen coefficient: the provisioning gain is first a **meal-scale economy**, second a composition effect. Narrative adjusted per decision node D5.

## B line: within-household elder gap (household FE, 557 mixed households)
- FGDS-10: elders eat **-0.294***** groups less than co-resident non-elder adults (se 0.087; Romano-Wolf p=0.000).
- Food variety score: -0.561***; DBI-16 variety: -0.110***.
- Three-generation interaction (theta): FGDS-10 0.215 (p=0.114, imprecise); significant narrowing only on DBI variety (0.129***, RW p=0.000). **Neither D3 nor D4 cleanly** — reported honestly.
- Presence/absence outcomes (any animal-source, any dairy/egg/bean — unit-robust) show **no elder gap**: the deficit is in variety breadth, not in being served protein foods at all.
- Meal-frequency channel (table10d): within the same household elders record **-0.301*** fewer recorded meals** (se 0.078; 48h; 31.9% of elders <3 recorded meals vs 22.9% of non-elder adults); restricting to members with >=3 recorded meals removes the FGDS gap. The gap thus operates through **fewer recorded eating occasions** — which may be genuine meal-skipping and/or proxy under-recording of elders' meals; the data carry no respondent field to separate the two, so we do not claim behavioural skipping (measurement caveat, R6).
- Power on the imprecise interaction (table10e): theta 95% CI [-0.051, 0.480], 80%-power MDE ~0.379 FGDS groups; the sample cannot rule out a moderate theta, so 'neither D3 nor D4' means **underpowered to distinguish**, not a precise zero.
- **Identification probe — generation ladder (table24, C)**: within the same households, relative to prime-age adults, elders eat -0.168*** fewer FGDS groups but **children eat -0.676*** fewer — ~4x the elder gap**. The elder deficit is therefore largely part of a broad **life-stage/recording gradient** (children fare worse), NOT an elder-specific intra-household allocation penalty. The 'inequality against elders' reading must be heavily qualified.
- **MNAR / proxy-under-recording bound (table22)**: if the 32% of elders with <3 recorded meals were actually eating like their co-resident adults (a recording artifact, not real skipping), the gap **flips to 0.174*****. A uniform under-recording of only ~0.205 FGDS groups per elder nulls the gap. The elder deficit is thus **fragile to proxy under-recording** and cannot be asserted as a behavioural/nutritional fact.

## B2: household-HDDS -> elder-FGDS cross-sectional slope (phi1)
- **phi1 is an associational cross-sectional slope, NOT a causal pass-through**: the focal elder's own 48h diet mechanically enters household HDDS, biasing phi1 up (worst where the elder is most of the household).
- phi1 by arrangement: cohabit_nonelder 0.425***; elder_only_multi 0.473***; threegen 0.320***; elder_alone 0.696***; elder_child 0.409***; other 0.406***.
- Contamination robustness (table11c): pooled slope 0.436 (all arrangements) vs 0.380 excluding the mechanically-contaminated elder-alone/elder-only households — modest attenuation, slope robust.

## B3: decomposition and leakage (revised headline #1)
- Three-generation provisioning gain: **0.519 HDDS groups**; expected elder gain (phi1 x gain): 0.226; realized elder gain (reduced form): 0.214.
- **Two leakage measures (the original single number conflated them).** (1) gap-to-household 1-bR/bA = **59%** (95% CI 19-108%) — but this is dominated by the normal <1 slope phi1 that EVERY member faces, not elder-specific loss. (2) **Allocation-specific leakage 1-realized/expected = 5%** (95% CI -91-118%) — the share the elder loses *beyond* the pass-through everyone faces. This CI spans zero widely, so **elder-specific leakage is small and statistically indistinguishable from zero**. The honest headline is (2): once you net out ordinary pass-through, three-generation elders are **not** meaningfully shortchanged.
- Heterogeneity (gap-to-household basis, SUGGESTIVE only — grf finds no significant heterogeneity): 25% when the elder is the household cook vs 84% when not; 64% (low income) vs 48% (high income). Treat as exploratory, not an established policy lever.

## Mechanisms (Tasks 5-6, 8)
- Provisioning-role mediation of three-gen HDDS effect: -0.6%
- Three-gen -> non-elder member cooks: -0.023 (p=0.508)
- Three-gen -> elder is cook: +0.039 (p=0.256)
- Three-gen -> household self-sufficiency: +0.000 (p=0.775)
- Provisioning-role variables do **not** mediate the three-gen HDDS association (~0%): consistent with the D5 reading that scale economies, not who cooks, carry the effect.

## Post-estimation: 2035 aging projection (headline #2, accounting)
- S1 (k=6pp/decade out of three-gen): mean household provisioning falls 0.058 HDDS groups; elder FGDS-10 falls 0.0253 (provisioning-anchored, phi1 pass-through).
- Per affected elder (moving three-gen -> elder-only) the provisioning loss is ~1 HDDS group x phi1 ~ 0.3-0.4 FGDS groups; the population average is modest because the shift affects ~6.6pp of elders by 2035.
- S2 community provisioning at lambda={25,50,75}% recovers the same share of the loss (accounting identity); sensitivity k in {4,8} in table17.
- Naive individual-means variant flagged: solo elders' measured individual diversity is inflated by recording concentration.
- **Monte-Carlo uncertainty (table17b)**: propagating sampling error in bA and phi1 plus a 0.5-1.5x selective-migration multiplier, the 2035 elder-FGDS change at k=6 has median -0.0248 (95% interval [-0.0426, -0.0115]); P(worse than today)=1.00. The sign is robust (interval excludes zero) but the **magnitude is small** (~0.02-0.03 FGDS groups) — headline #2 is a modest, directionally-reliable accounting signal, not a large or precise forecast. (Interval reflects bA/phi1/migration uncertainty; it does not include the structural risk that cross-sectional LA gaps mis-measure true within-elder change.)

## Post-estimation: county elder-feeding policy text
- Counties matched: 47/61; county-year reports with text: 637
- Moderation solo/elder-only x policy intensity: 0.071 (p=0.335) — imprecise — descriptive context only
- Validity: 100 keyword sentences exported for manual audit (target >=85% true elder-feeding policy content).
- Red line respected: county-level context variable only.

## Appendix: causal-forest heterogeneity
- ATT (forest): 0.536 (se 0.135)
- Calibration: mean prediction t=3.93, differential t=-1.46.
- **Heterogeneity NOT detected**: the differential-forest-prediction calibration coefficient is below 2, so the forest does **not** give statistical evidence of treatment-effect heterogeneity. Subgroup CATE differences (and the leakage-by-subgroup contrasts they motivate) are therefore **suggestive only**, not established effect modification.
- Framing: conditional-association heterogeneity; treatment non-random.

## Decision-node ledger
| node | status | consequence |
|---|---|---|
| D1/D6 nutrient audit | **TRIGGERED (FAIL)** | AR/nutrient outcomes sealed; diversity indices carry B line |
| D2 B-line N<400 | not triggered (557) | B line stays central |
| D3/D4 theta | neither (imprecise +0.18) | honest two-sided discussion; DBI variety narrows significantly |
| D5 scale attenuation>50% | **TRIGGERED (54.6%)** | meal-scale economies lead the mechanism narrative |
| D7 census trend | default k=6pp/decade with {4,8} sensitivity | documented |
| D8 policy-text sign | not triggered (imprecise +) | descriptive context only |

## Post-review revisions (methodological audit)
This pipeline was re-audited by four adversarial reviewers (identification, estimator implementation, measurement, missed tests). Changes made:
- **Fixed bugs**: AIPW cluster bootstrap used set-membership (`%in%`) instead of with-replacement village replication (SE was inflated); permutation p-value now (1+k)/(1+B); privacy assertion was case-sensitive and missed `*Phone` columns (now case-insensitive with false-positive guards).
- **Relabelled claims**: A-line weighting estimators are *adjusted associations under selection-on-observables*, not causal ATT; phi1 is a *cross-sectional slope*, not causal pass-through.
- **Corrected leakage**: the headline '59% leakage' conflated ordinary <1 pass-through (common to all members) with elder-specific loss. Allocation-specific leakage (unit-consistent) is ~5% with a CI spanning zero — **elders are not meaningfully shortchanged once ordinary pass-through is netted out**.
- **Reframed B-line**: a within-household generation ladder shows the child deficit is ~4x the elder deficit, and an MNAR bound shows the elder gap flips sign if <3-meal elders are re-imputed to adult levels. The elder deficit is real but modest, part of a life-stage/recording gradient, and fragile to proxy under-recording — NOT established elder-specific inequality.
- **Added tests**: wild cluster bootstrap (few-cluster robust), 60-vs-65 and year-split sensitivity, negative-control outcome, BH-FDR on the share family (0 survive), strict three-generation flag, 2035 projection Monte-Carlo interval, honest 'no significant heterogeneity' note for the causal forest.
- **Dropped a bad control**: `main_cook` (a mediator) removed from the B-line baseline; the elder gap grows modestly as expected.
