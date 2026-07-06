# Budget-variable (m) scale resolution

## Question
The published draft's descriptive table (Table 0) and §3.3 state the budget
variable is "real per capita GDP, m = pgdp/monetary_deflator" (median ≈¥66,734),
with per-capita expenditure (median ≈¥18k) "reported only for comparison." But
the estimation pipeline (run_maidads_pipeline.py line 533) sets
`m = expenditure_nominal / monetary_deflator` (median ≈¥18k).

## Decisive test — per-observation log-likelihood fingerprint
Docx MAIDADS (national non-food) NLL = -3999 on 279 obs = **-14.33/obs**.
Evaluating the published Table 2 parameters on the reconstructed 2015-2023 panel:
- EXPENDITURE-scale m (median ¥17,952): NLL -3515, -12.60/obs
- PGDP-scale m       (median ¥56,762): NLL -2080,  -7.46/obs
Full re-estimation (2015-2024) on EXPENDITURE m reaches -4481.55/310 = **-14.46/obs**,
matching the docx -14.33/obs. The pgdp scale (-7.5/obs) is nowhere close.

## Conclusion
The paper's ACTUAL estimation used per-capita **expenditure** as m. The
descriptive-table / §3.3 "per capita GDP" labeling is a documentation
inconsistency in the original draft. The 2024 update keeps estimation on the
expenditure scale so results are directly comparable to the published tables.

## US$ income axis
K=0.137515 (= mean gdp_2015usd/pgdp) maps the PGDP scale to US$, not the
estimation m. The defensible income→US$ mapping for the elasticity nodes is the
linear reconstruction from the paper's stated provincial US$ range
(US$4,200-23,900 ↔ expenditure ¥9,342-45,408):
  US$ = -902.4 + 0.54621 * m   (m = expenditure, 2023 yuan)
  US$15,000 -> ¥29,114 ; US$20,000 -> ¥38,268 ; US$25,000 -> ¥47,422 ; US$30,000 -> ¥56,576
At these nodes the corrected pork income elasticity is positive and declining
(+0.112 -> +0.007), matching the published Table 4 pattern (+0.191 -> +0.108).
