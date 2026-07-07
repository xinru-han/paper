# Environmental Footprint Coefficient Library — CASM / CASM-World

An internationally-sourced, fully-cited coefficient library for carbon, water, nitrogen
and land footprints of agricultural commodities, mapped to CASM (China, 37 commodities)
and CASM-World (13 regions, 31 world commodities) codes.

**Every numeric value in this library is transcribed from a real, cited source. Cells that
could not be sourced are left blank and marked `GAP` in the notes column. Nothing is
fabricated.** Where a value is a derived aggregation rather than a verbatim published
figure, the `statistic` column says so (e.g. "area-weighted mean (derived)").

Assembled 2026-07-07 via primary-source retrieval (Poore & Nemecek 2018 SI via Our World
in Data grapher datasets; FAOSTAT Emissions-intensities bulk download; Mekonnen & Hoekstra
Value-of-Water reports; Ludemann et al. 2022; IPCC 2019 Refinement; Leach et al. 2012;
Uwizeye et al. 2020).

---

## Files

| File | Content | Unit | Primary sources |
|---|---|---|---|
| `carbon_footprint_coefficients.csv` | GHG emission intensity | kg CO2e / kg product | FAOSTAT Emissions intensities (2023), Poore & Nemecek 2018 |
| `water_footprint_coefficients.csv` | Green / blue / grey water footprint | m3 / tonne | Mekonnen & Hoekstra 2011 (crops), 2012 (animals) |
| `nitrogen_coefficients.csv` | Crop N-fertiliser rate, livestock N excretion, food-chain N | kg N/ha; kg N/(1000kg)/day; kg N/kg N | Ludemann 2022; IPCC 2019; Leach 2012; Uwizeye 2020 |
| `land_coefficients.csv` | Land occupation | m2·year / kg (also /100g protein, /1000 kcal) | Poore & Nemecek 2018 |
| `commodity_mapping.csv` | CASM ↔ CASM-World ↔ FAOSTAT ↔ P&N ↔ M&H concordance | — | — |

---

## ⚠ System-boundary warning — DO NOT MIX BOUNDARIES

The three carbon sources use **incompatible system boundaries**. They are NOT interchangeable
and must not be averaged together.

| Source | Boundary | What it includes | Typical relation |
|---|---|---|---|
| **FAOSTAT Emissions intensities** | **farm-gate (cradle-to-farm-gate)** | On-farm only: enteric fermentation, manure, rice CH4, on-farm energy, N2O from fertiliser | LOWEST for monogastrics/crops |
| **Poore & Nemecek 2018** | **cradle-to-retail LCA** | + land-use change, feed production, processing, transport, packaging, retail, losses | HIGHEST |
| **Current CASM China coefficients** | **on-farm direct only** (rice CH4 + fertiliser N2O + straw burning + enteric/manure) | China-calibrated per-ha crop factors + per-t livestock factors | Between the two, crop-side |

Concrete example — **pig meat**: FAOSTAT China farm-gate = 0.96 kg CO2e/kg, FAOSTAT world =
1.60, but Poore & Nemecek cradle-to-retail world mean = 11.9. The 12× gap is almost entirely
feed production + processing + retail, NOT a data error. Choose ONE boundary per analysis and
state it.

Water and land coefficients have their own boundary notes:
- **Mekonnen & Hoekstra water**: consumptive green+blue + grey (dilution) water at farm, period
  1996–2005. Grey is a theoretical dilution volume, not a withdrawal — report green/blue/grey
  separately.
- **Poore & Nemecek land**: m2·year of land *occupation* (arable + pasture), reference year ~2010,
  global means across ~38,700 farms. Beef "beef herd" (326 m2/kg) vs "dairy herd" (43 m2/kg)
  differ 7×; pick the herd type matching your beef supply.

---

## Comparison with the coefficients currently used in the paper

The model (`model/casm/output.py`, §4.2.8/4.3) computes emissions as:

```
crop CO2   = area(ha) × (FERTEF + BURNEF + CROPREF + RICEEF)   [tCO2e/ha]
livestock CO2 = production(t) × LVSEF                          [tCO2e/t]
```

Current China-calibrated factors (from `1parameter.xlsx`):

| Item | Current paper value | Basis | Cross-check against this library |
|---|---|---|---|
| Rice paddy CH4 (RICEEF) | 4.917 tCO2e/ha | on-farm CH4 | Consistent with IPCC 2019 rice CH4 defaults; FAOSTAT China rice EI 0.90 kg CO2e/kg-paddy ≈ 4.917/(yield t/ha) → implies ~5.5 t/ha yield, plausible |
| Rice fertiliser (FERTEF) | 0.873 tCO2e/ha | N2O + upstream | Additive to the CH4 term above |
| Wheat fertiliser | 1.068 tCO2e/ha | N2O + upstream | China wheat N rate 212 kg N/ha (Ludemann 2022) supports a high fertiliser term |
| Pig meat (LVSEF) | 0.92 tCO2e/t | on-farm | FAOSTAT China farm-gate 0.96 kg CO2e/kg = 0.96 tCO2e/t — near-identical ✓ |
| Cattle meat | 15.82 tCO2e/t | on-farm | FAOSTAT China 15.19 tCO2e/t — near-identical ✓ (P&N cradle-to-retail 99 is a different boundary) |
| Sheep/goat meat | 12.90 tCO2e/t | on-farm | FAOSTAT China sheep 11.73 / goat 11.98 tCO2e/t — close ✓ |
| Chicken meat | 0.54 tCO2e/t | on-farm | FAOSTAT China 0.44 tCO2e/t — same order ✓ |
| Eggs | 0.58 tCO2e/t | on-farm | FAOSTAT China 0.55 tCO2e/t — near-identical ✓ |
| Milk | 1.15 tCO2e/t | on-farm | FAOSTAT China 0.99 tCO2e/t — same order ✓ |

**Key finding:** the paper's current livestock factors align closely with FAOSTAT China
**farm-gate** emission intensities (2023). The library therefore *validates* the current
livestock parameters and provides the traceable international citation they previously lacked.
The current framework is a **farm-gate / on-farm** accounting — comparable to FAOSTAT, NOT to
Poore & Nemecek. Use P&N only for full-life-cycle sensitivity or consumer-footprint framing.

---

## Integration guidance

1. **Crops are per-ha; the model already multiplies by area.** To swap in an international
   *per-tonne* coefficient (FAOSTAT / P&N), convert to per-ha via crop yield:
   `tCO2e/ha = (kg CO2e/kg) × yield(t/ha)`. The model has `YCX` (yield) available at the same
   point emissions are computed, so per-t → per-ha is a one-line change.
2. **Livestock are per-tonne already** — FAOSTAT China EI values drop in directly as `LVSEF`
   replacements with citation, with essentially no change to results (see table above).
3. **Keep boundaries separate.** Recommend one column per boundary in scenario outputs
   (farm-gate vs full-LCA) rather than a blended number.
4. **Derived-product oils/meals (SOYO, RAPO, GRDO, SOYM…)** have no standalone LCA figure in
   most sources — allocate from the parent oilseed by mass or economic value at crushing.
5. **World regions (USA, E15, BRZ, …):** this library provides CHN and WLD (global mean) only.
   Region-specific carbon can be drawn from GLEAM 3.0 (livestock) and FAOSTAT EI by country
   (both keyed by the same FAOSTAT item in `commodity_mapping.csv`); those per-region cells are
   not yet populated here (see Gaps).

### Recommended main scenario + sensitivity set

- **Main (China, on-farm):** keep current CASM factors; cite FAOSTAT China Emissions-intensities
  (2023) as the external validation. This is the internally-consistent, defensible base.
- **Sensitivity S1 (full life-cycle):** apply Poore & Nemecek 2018 cradle-to-retail per-kg means
  (× yield for crops) to test consumer/diet-shift footprints — captures feed + LUC + retail.
- **Sensitivity S2 (world trade):** for CASM-World, FAOSTAT country EI + GLEAM 3.0 by region.
- **Co-footprints:** report water (M&H green+blue+grey) and land (P&N m2·yr/kg) as parallel
  indicators for diet-scenario trade-off figures; use China columns where available (all
  livestock + some crops), WLD elsewhere.

---

## Coverage & gaps (honest accounting)

**Carbon:** FAOSTAT gives China + World for all livestock + rice + aggregate cereals (2023).
P&N gives World cradle-to-retail for ~all food commodities. Gaps: sorghum (neither source);
China-specific *crop* GHG beyond rice/cereals-aggregate; GLEAM 3.0 per-kg-product region values
(dashboard-only, not machine-readable); butter GHG.

**Water:** M&H gives World for all crops and World+China for all animal products. Gaps:
China-specific *per-crop* green/blue/grey (only national aggregate published; per-crop lives in
the WaterStat DB whose download was broken at access time); aquaculture (not in M&H).

**Nitrogen:** Crop N-rates China (Ludemann 2022 as-reported) + World (derived area-weighted).
Livestock N-excretion IPCC 2019 Table 10.19 (Asia + developed regions). Food-chain VNF (Leach
2012) + livestock supply-chain N (Uwizeye 2020). Gaps: groundnut N-rate (both regions);
pure-potato China; egg VNF (not in Leach Table 2); Uwizeye per-protein & East-Asia species
breakdown (paywalled SI); per-tonne crop N (needs yield combination).

**Land:** P&N World means for ~all commodities incl. per-100g-protein and per-1000-kcal. Gaps:
vegetable oils per-kg (OWID grapher lists oils only per-1000-kcal); sorghum; butter.

---

## Full source list

- **Poore, J. & Nemecek, T. (2018).** Reducing food's environmental impacts through producers and
  consumers. *Science* 360(6392):987–992. DOI: 10.1126/science.aaq0216. (Per-kg means reproduced
  via Our World in Data grapher datasets `food-emissions-supply-chain`, `land-use-per-kg-poore`,
  `land-use-protein-poore`, `land-use-kcal-poore`.)
- **FAOSTAT Emissions intensities domain**, `Environment_Emissions_intensities_E_All_Data`,
  bulks-faostat.fao.org, accessed 2026-07-07, reference year 2023.
- **Mekonnen, M.M. & Hoekstra, A.Y. (2011).** The green, blue and grey water footprint of crops
  and derived crop products. *Hydrol. Earth Syst. Sci.* 15:1577–1600. DOI: 10.5194/hess-15-1577-2011.
  (= Value of Water Research Report No. 47, Vol. 1.)
- **Mekonnen, M.M. & Hoekstra, A.Y. (2012).** A global assessment of the water footprint of farm
  animal products. *Ecosystems* 15:401–415. DOI: 10.1007/s10021-011-9517-8. (= Value of Water
  Research Report No. 48, Vol. 1 — China + Global columns.)
- **Ludemann, C.I., Gruère, A., Heffer, P. & Dobermann, A. (2022).** Global data on fertilizer use
  by crop and by country. *Scientific Data* 9:501. DOI: 10.1038/s41597-022-01592-z. (FUBC report #9;
  Dryad 10.5061/dryad.2rbnzs7qh.)
- **IPCC (2019).** 2019 Refinement to the 2006 IPCC Guidelines for National GHG Inventories, Vol. 4
  (AFOLU), Ch. 10, Table 10.19 (livestock N excretion defaults).
- **Leach, A.M. et al. (2012).** A nitrogen footprint model to help consumers understand their role
  in nitrogen losses to the environment. *Environmental Development* 1:40–66.
  DOI: 10.1016/j.envdev.2011.12.005. (Virtual Nitrogen Factors, Table 2.)
- **Uwizeye, A. et al. (2020).** Nitrogen emissions along global livestock supply chains.
  *Nature Food* 1:437–446. DOI: 10.1038/s43016-020-0113-y.
- Context only: Adalibieke et al. 2023 *Sci Data* 10.1038/s41597-023-02526-z; Einarsson/Ludemann
  et al. 2024 *ESSD* 10.5194/essd-16-525-2024.
