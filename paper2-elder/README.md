# Paper 2 — Intergenerational Co-residence, Household Food Provisioning, and What Older Adults Actually Eat

Evidence from a 2023–2024 eight-province rural China food & nutrition survey
(3,565 households; 8,565 individual 48h dietary recalls; 62 counties, ~360 villages).

Proposal: `食物调查数据研究方案/paper2_修订方案_代际同住_供食组织与老年膳食.md`（含 ★v2 升级包）.
This folder contains the full executable pipeline (R) and all results.
**Household microdata under `data/` is never pushed to GitHub** (only code + aggregate outputs).

## Design

- **A line (household)**: living arrangement → household dietary diversity (HDDS-12, 48h),
  FE sequence (year → province×year → county×year → village×year), IPW / entropy balancing /
  NN matching / AIPW, permutation inference, Oster bounds, leave-one-province.
- **B line (within household, identification core)**: elder vs non-elder-adult intake gap under
  household fixed effects in 557 mixed households (1,596 adults), interaction with
  three-generation living; Romano–Wolf stepdown over the outcome family.
- **B3 decomposition**: elder-level arrangement differences = pass-through (φ1 × ΔHDDS)
  + allocation residual; leakage rate with village-block-bootstrap CIs.
- **Post-estimation**: 2035 aging/solo-living accounting projection (provisioning-anchored);
  county government work-report text (elder-feeding policy diffusion + exploratory moderation);
  honest causal-forest heterogeneity (appendix).

## Pipeline (code/)

| script | content | key outputs |
|---|---|---|
| 00_setup.R | paths, conventions, helpers | — |
| 01_build_data.R | roster→living arrangements, village environment, interview dates, B-line sample | data/*, build_report.md |
| 02_audit_nutrients.R | Task 3 unit audit (gatekeeper) | table23, audit report — **FAIL → D1/D6** |
| 03_descriptives.R | Table 1 household/person, figs 1–2 | table1*, fig1–2 |
| 04_aline_main.R | FE sequence, shares, scale-vs-composition (D5), children dose | table2–6 |
| 05_aline_robust.R | balance/overlap, 5 estimators, permutation, Oster, LOP | table7–9, fig3–6 |
| 06_bline_gap.R | B1 household-FE gap + Romano–Wolf + R6 | table10*, fig7 |
| 07_bline_passthrough.R | B2 pass-through φ1 by arrangement | table11* |
| 08_decomposition_leakage.R | B3 + leakage + heterogeneity + bootstrap | table12–13, fig8 |
| 09_mechanisms.R | roles (Task 5), self-provisioning (Task 6), binaries (Task 8) | table14–16 |
| 10_aging_projection.R | 2035 scenarios S0/S1/S2, k∈{4,6,8}, λ∈{25,50,75}% | table17, fig10 |
| 11_county_policy_text.R | county report keywords, diffusion, moderation + placebo | table18, fig9, county panel |
| 12_grf_heterogeneity.R | appendix causal forest (honest, village-clustered) | table19*, fig11 |
| 14_wild_bootstrap.R | few-cluster wild cluster bootstrap-t (A-line + B-line) | table20 |
| 15_threshold_sensitivity.R | elder 60-vs-65, child cutoff, 2023/2024 split | table21 |
| 16_mnar_bounds.R | proxy-under-recording (MNAR) bounds on the elder gap | table22 |
| 18_bline_identification.R | generation-ladder placebo + health strata (allocation vs physiology) | table24*, table25 |
| 99_run_all.R | run everything in order | — |

**Post-review revisions (methodological audit).** After the first full run the pipeline
was re-audited by four adversarial reviewers. Fixed a cluster-bootstrap bug (AIPW SE),
the permutation p-value, and a weak privacy assertion; relabelled A-line estimators as
selection-on-observables (not causal ATT) and phi1 as a cross-sectional slope (not
pass-through); split the leakage measure into gap-to-household (59%, mostly ordinary
pass-through) vs allocation-specific (~5%, CI spans zero); added a generation-ladder
placebo (child deficit ~4x the elder deficit), MNAR bounds (the elder gap flips under
re-imputation), wild cluster bootstrap, 60-vs-65 and year-split sensitivity, a
negative-control outcome, BH-FDR on the share family, a strict three-gen flag, and a
Monte-Carlo band on the 2035 projection. Net effect: **headline #1 (leakage) and the
"inequality against elders" framing are substantially qualified; the A-line HDDS effect
and its robustness are unchanged.** See the "Post-review revisions" block in `RESULTS.md`.

Run: `Rscript code/99_run_all.R` (R ≥ 4.1, packages in `/root/Rlibs`:
data.table, fixest, WeightIt, cobalt, ggplot2, grf, readxl, stringr).

## Key facts & decisions (pre-registered decision nodes)

- Elder households: **1,234** (of 3,565). Living arrangements: with-non-elder-adults 429 /
  elder-only-multi 354 / three-generation 289 / alone 69 / elder+child 50 / other 43.
- B-line mixed households: **557** (≥400 → D2 not triggered).
- **Task 3 audit: FAIL** — 48h amount fields are unit-corrupted upstream (median adult 48h
  food mass ≈ 5 g; nutrient exports show 1e17 maxima). Nutrient absolute quantities and DRI
  adequacy ratios are sealed portfolio-wide (D1/D6); diversity indices and presence/absence
  binaries (unit-robust) carry the B line. See `outputs/reports/audit_nutrient_unit_validation.md`.
- **D5 triggered**: household-size dummies absorb 54.6% of the three-generation HDDS
  coefficient → mechanism narrative = meal-scale economies first, composition second.
- **θ (elder-gap × three-gen) imprecise** (+0.18, p=.19 on FGDS-10; significant narrowing only
  on DBI variety) → neither D3 nor D4 cleanly; reported honestly.

## Results summary

See `RESULTS.md` and `outputs/reports/`.
