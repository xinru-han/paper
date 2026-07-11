# prereg_p3.md — pre-registered first-stage grid and D1 decision
Generated: 2026-07-11 17:37:42

## Grid (all combinations evaluated, none selected ex post beyond the rule below)
- treatments: retail_pc1 (PCA), retail_lnfresh, access_dist
- IVs: detour_{town,county}_{1,2,5}km
- conditioning: ln_dist_town + ln_dist_county + ln_vpop + elevation + water + GAEZ (si, constraint)
- own-village slope/TRI are excluded from the main conditioning set: they are a
  mechanical component of the corridor-cost instrument (r ≈ 0.45); the agriculture
  bypass is controlled directly via GAEZ suitability and soil-terrain constraint.
  Slope/TRI-augmented specs appear in the robustness battery with AR inference.

## Decision rule (proposal §12 D1)
primary spec fixed ex ante = retail_pc1 <- detour_town_5km; if its KP-F < 10,
pick the best-F combo from the grid for 2SLS and downgrade the paper's primary
framing to the reduced form in detour (quasi-experimental terrain-isolation
gradient), targeting Food Policy / World Development.

## Outcome: D1 FIRES. Primary combo F = 4.3 (<10).
Best combo: retail_pc1 <- detour_town_1km with person-level village-clustered F = 9.7.

Consequences applied throughout the pipeline:
1. PRIMARY: reduced form  y ~ detour_town_5km + Z | county FE (person level, village cluster).
2. SECONDARY: 2SLS retail_pc1 <- detour_town_1km, always accompanied by Anderson-Rubin CIs.
3. MTE (v2 §15) is dropped (D5 analogue): weak first stage cannot support LIV;
   replaced by the LATE/reduced-form mosaic across IV widths and subgroups.
4. Post-estimation (gap accounting, investment pricing) is anchored on the reduced form,
   with 2SLS-scaled versions shown as upper bounds.
