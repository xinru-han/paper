# Paper 2 (elder diet) — Results summary
Auto-generated: 2026-07-07 19:56:49

All tables in `outputs/tables/`, figures in `outputs/figures/`, reports in `outputs/reports/`.

## Sample
- Elder households (>=1 member 60+): **1,234** of 3,565; six living arrangements (Table 1).
- Elders with 48h records: 1,683; B-line mixed households: **557** (1,596 adults; CONSORT in `table_bline_consort_flow.csv`).
- Nutrient unit audit (Task 3): **FAIL** -> D1/D6, diversity indices carry the B line (`audit_nutrient_unit_validation.md`).

## A line: living arrangement -> household provisioning (HDDS-12)
- Three-generation vs with-non-elder-adults: 0.533*** under year_FE; 0.529*** under prov_year_FE; 0.519*** under county_year_FE; 0.516*** under county_year_FE_env; 0.518*** under village_year_FE.
- Elder-only and elder-alone households provision 0.4-0.5 fewer groups (Table 2).
- Estimator agreement (three-gen ATT on HDDS): OLS_countyFE 0.532; IPW_ATT 0.581; EntropyBal_ATT 0.586; NN_match_caliper 0.567; AIPW_ATT 0.592.
- Permutation p-value (1000 within-village reshuffles): 0.001
- Oster beta* (delta=1, Rmax=1.3 R2): 0.579 (OLS long: 0.566); delta for beta=0: -44.08
- Estimator range: 0.532 to 0.592
- Matched sample: 254 pairs of 262 treated

### Scale vs composition (D5 TRIGGERED)
- Household-size dummies absorb **54.6%** of the three-gen coefficient: the provisioning gain is first a **meal-scale economy**, second a composition effect. Narrative adjusted per decision node D5.

## B line: within-household elder gap (household FE, 557 mixed households)
- FGDS-10: elders eat **-0.242***** groups less than co-resident non-elder adults (se 0.086; Romano-Wolf p=0.007).
- Food variety score: -0.442***; DBI-16 variety: -0.093***.
- Three-generation interaction (theta): FGDS-10 0.178 (p=0.187, imprecise); significant narrowing only on DBI variety (0.117***, RW p=0.000). **Neither D3 nor D4 cleanly** — reported honestly.
- Presence/absence outcomes (any animal-source, any dairy/egg/bean — unit-robust) show **no elder gap**: the deficit is in variety breadth, not in being served protein foods at all.
- Meal-frequency channel (table10d): within the same household elders record **-0.301*** fewer recorded meals** (se 0.078; 48h; 31.9% of elders <3 recorded meals vs 22.9% of non-elder adults); restricting to members with >=3 recorded meals removes the FGDS gap. The gap thus operates through **fewer recorded eating occasions** — which may be genuine meal-skipping and/or proxy under-recording of elders' meals; the data carry no respondent field to separate the two, so we do not claim behavioural skipping (measurement caveat, R6).
- Power on the imprecise interaction (table10e): theta 95% CI [-0.086, 0.442], 80%-power MDE ~0.377 FGDS groups; the sample cannot rule out a moderate theta, so 'neither D3 nor D4' means **underpowered to distinguish**, not a precise zero.

## B2: pass-through of household provisioning to elder intake
- phi1 by arrangement: cohabit_nonelder 0.425***; elder_only_multi 0.473***; threegen 0.320***; elder_alone 0.696***; elder_child 0.409***; other 0.406***.
- Pass-through is **lowest in three-generation households (0.32)** — extra provisioning diversity is partly captured by other members (children) — and highest for elders alone (0.70, mechanical).

## B3: decomposition and leakage (headline #1)
- Three-generation provisioning gain: **0.519 HDDS groups**; expected elder gain (phi1 x gain): 0.226; realized elder gain (reduced form): 0.214.
- **Leakage rate: 59%** of the provisioning gain does not appear in the elder's own 48h intake (95% block-bootstrap CI 19-108%).
- Heterogeneity (policy lever): leakage is **25%** when the elder is the household cook vs **84%** when not; 64% (low income) vs 48% (high income). Keeping elders in the provisioning role is a low-cost intervention point.

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

## Post-estimation: county elder-feeding policy text
- Counties matched: 47/61; county-year reports with text: 637
- Moderation solo/elder-only x policy intensity: 0.071 (p=0.335) — imprecise — descriptive context only
- Validity: 100 keyword sentences exported for manual audit (target >=85% true elder-feeding policy content).
- Red line respected: county-level context variable only.

## Appendix: causal-forest heterogeneity
- ATT (forest): 0.536 (se 0.135)
- Calibration: mean prediction t=3.93, differential t=-1.46 (differential>2 => real heterogeneity)
- Framing: conditional-association heterogeneity; feeds S2 targeting and leakage heterogeneity.

## Decision-node ledger
| node | status | consequence |
|---|---|---|
| D1/D6 nutrient audit | **TRIGGERED (FAIL)** | AR/nutrient outcomes sealed; diversity indices carry B line |
| D2 B-line N<400 | not triggered (557) | B line stays central |
| D3/D4 theta | neither (imprecise +0.18) | honest two-sided discussion; DBI variety narrows significantly |
| D5 scale attenuation>50% | **TRIGGERED (54.6%)** | meal-scale economies lead the mechanism narrative |
| D7 census trend | default k=6pp/decade with {4,8} sensitivity | documented |
| D8 policy-text sign | not triggered (imprecise +) | descriptive context only |
