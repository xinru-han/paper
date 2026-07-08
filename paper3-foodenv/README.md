# Paper 3 — Rugged Roads to a Diverse Diet: Terrain, Rural Food Environments, and Nutrition in China

Evidence from a 2023–2024 eight-province rural China food & nutrition survey
(361 villages, 3,565 households, 8,565 individual 48h dietary recalls; 63 counties).

Proposal: `食物调查数据研究方案/paper3_食物环境与膳食质量_IV.md` (v1 + v2 升级包).
This folder is the full executable pipeline (R). **Household microdata under `data/`
is never pushed to GitHub** (only code + aggregate outputs).

## Design and the D1 decision (read this first)

The proposal's 2SLS design instruments the village 5km retail environment with the
**terrain detour index** `log(route-cost distance / straight-line distance)` to the
township/county seat (GEE slope-cost corridors, 1/2/5km buffer widths).

Pre-registered decision node **D1 fired**: with the honest conditioning set
(straight distances, population, elevation, water, GAEZ suitability + soil-terrain
constraint; own-village slope/TRI excluded because they are a mechanical component
of the corridor cost itself, r≈0.45), the primary combo's first-stage KP-F ≈ 6 < 10.
Best pre-registered combo (retail_pc1 ← detour_town_1km) reaches F ≈ 10.4.
Per the pre-registered rule (`outputs/reports/prereg_p3.md`):

- **PRIMARY: reduced form** — diet outcomes on the detour index directly
  (quasi-experimental terrain-isolation gradient), county FE, village-clustered.
- **SECONDARY: 2SLS** (retail_pc1 ← detour_town_1km) always with Anderson–Rubin CIs.
- MTE (v2 §15) dropped (weak-IV infeasible); replaced by a LATE mosaic across
  corridor widths. Permutation-corridor placebo (v2 §14, degraded destination/
  distance-decile version) puts the real first stage at perm p = 0.091 — **D4
  marginal**, consistent with the downgraded framing.

## Headline results

1. **A precisely estimated null within counties.** Reduced form of FGDS-10 on a 1sd
   increase in terrain isolation: −0.025 (se 0.089); OLS of retail thickness: ≈0;
   2SLS: +0.15 with AR 95% CI [−0.18, 0.63]. Null is stable across corridor widths,
   Poisson, year splits, county clustering, WCB (p=0.81), BH-FDR.
2. **The raw gradient is between-county development, not local access.** Bivariate
   detour–FGDS gradient is −0.111*** and detour Q1→Q4 means fall 2.89→2.55
   (MDD-W 17.5%→10.4%, income 5.9→4.2万), but it dies with county FE.
3. **Mechanisms agree with the null.** Purchase extensive margins are at the ceiling
   (97–100% of households buy staples/meat/vegetables); village paid prices show no
   detour gradient and no perishable×detour differential; self-sufficiency does not
   respond; FAFH extensive margin −0.7pp (p=.06) is the only marginal response.
4. **Gap accounting (v2 headline):** women's MDD-W attainment is only **13.9%**;
   the food-environment-attributable share of the 86pp shortfall is **0% (point),
   ≤8.9% (AR upper bound)** — *below* the pre-registered 10–30% band from the
   African market-access literature.
5. **Policy pricing:** at the AR upper bound the infrastructure route needs village
   investment ≲ $46–92/yr to match school-feeding cost-effectiveness — i.e. the
   nutrition case for further rural commercial-network expansion is weak in 2023–24
   China; the binding constraints are income/behavioral, not physical access.
6. Design validity: education placebo null, income/off-farm bypass null, Sargan J
   p=0.53/0.69, first stage real unconditionally (F≈20) and survives county FE +
   distance conditioning (F≈12).

## Pipeline (code/)

| script | content | outputs |
|---|---|---|
| 00_setup.R | paths, control sets, D1 constants, helpers | — |
| 01_iv_map.R | corridor column mapping + consistency checks | iv_columns_map.md, data/iv_village.csv |
| 02_build_panel.R | village treatment/IV/controls + household + person blocks | p3_*.csv, build_report.md |
| 03_first_stage.R | pre-registered grid, D1 record | t2*, prereg_p3.md |
| 04_main.R | T3 RF/OLS/2SLS + AR CI + Conley + LATE mosaic | t3, t3b, t3c |
| 05_subgroups.R | women MDD-W, children CDDS (n≈100!), elderly, DBI | t4 |
| 06_mechanisms_price.R | village×category paid prices vs detour | t5a, t5a2 |
| 07_purchase_fafh.R | purchase margins, self-sufficiency, FAFH | t5b, t5c |
| 08_moderators.R | fridge/vehicle/self-suff/income interactions | t6 |
| 09_exclusion_battery.R | placebo, bypass, overid | t7 |
| 10_robustness.R | widths, slope/TRI set, Poisson, years, WCB, FDR | t12 |
| 12_placebo_corridors.R | destination race + distance-decile permutation | t7b, t7c |
| 13_descriptives.R | T1 by detour quartile | t1, t1b |
| 14_gap_accounting.R | MDD-W shortfall attribution + MC | t8, t8b |
| 15_investment_pricing.R | county work-report intensity + pricing | t9 |
| 16_targeting_forest.R | grf forest (within-county demeaned, exploratory) | t11* |
| 17_figures.R | F2–F5, F7 | figures/ |
| 99_run_all.R | run everything in order | — |

Run: `Rscript code/99_run_all.R` (R 4.1.2, packages in `/root/data/数据/Rlibs`).

## Data notes & red lines

- Village coordinates never appear in outputs (Conley SEs computed internally only).
- Nutrient absolute quantities and gram families **sealed** per the Paper-2 Task-3
  unit audit FAIL (D1/D6 portfolio-wide); diversity indices carry the paper.
- The delivered household `food_self_suff_rate` is unit-broken (median 0.0008);
  rebuilt as consumption-weighted category rates (`food_ssr_w`, mean 0.26).
- GAEZ village file has 2 duplicated village codes (deduped); counties appear in
  a single survey year each, so county×year FE ≡ county FE.
- Children 6–59m subgroup has n≈100 — CDDS estimates are reported but uninformative.
- Person/household blocks reuse the paper2-elder reconstruction
  (`../paper2-elder/data/`), which must be built first if reproducing from scratch.

## Sync

This folder (minus `data/`, `logs/`) auto-syncs every 5 minutes to
`github.com:xinru-han/paper` subfolder `paper3-foodenv/` (cron `sync-paper3-foodenv.sh`).
