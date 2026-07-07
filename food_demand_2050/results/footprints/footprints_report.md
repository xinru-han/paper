# Environmental Footprints — Core Results Report

Module: `modules/footprints.py` · Coefficients: `modules/coefficients/` (fully cited)
Scope: 19 China CASM scenarios (2023-2050) + 4 CASM-World scenarios (13 regions,
2024-2050). Headline units: **Mt CO2e, km³, Mt N, Mha**. All values 2050 unless noted.

> Boundaries are never blended. FAOSTAT = farm-gate (on-farm); Poore & Nemecek =
> cradle-to-retail LCA (consumer footprint, ~11× larger). See `modules/README.md` §3.

---

## A. China — 2050 footprints by scenario (consumption boundary, fixed 2023 coefficients)

| Scenario | Paper co2_total | **FAOSTAT cons** | P&N LCA | Blue water | Reactive N | Diet land |
|---|--:|--:|--:|--:|--:|--:|
| | Mt CO2e | Mt CO2e | Mt CO2e | km³ | Mt N | Mha |
| **BS** | 654.0 | 652.1 | 7607 | 338.1 | 46.21 | 1206 |
| A1 | 632.6 | 681.1 | 7834 | 340.5 | 46.81 | 1270 |
| A2 | 678.9 | 676.4 | 7814 | 339.1 | 46.69 | 1266 |
| A3 | 543.7 | 681.4 | 7815 | 341.0 | 46.80 | 1266 |
| A4 | 623.5 | 717.4 | 8134 | 349.7 | 48.00 | 1337 |
| A5 | 648.2 | 649.8 | 7562 | 334.3 | 45.87 | 1206 |
| A6 | n/a  | 655.0 | 7609 | 335.4 | 46.06 | 1219 |
| B1 | 451.2 | 645.5 | 7939 | 341.8 | 47.49 | 1155 |
| B2 | 492.9 | 643.1 | 7946 | 341.4 | 47.47 | 1153 |
| B3 | 399.0 | 646.7 | 7911 | 341.8 | 47.43 | 1154 |
| B4 | 462.6 | 655.7 | 8098 | 345.3 | 48.08 | 1173 |
| B5 | 474.6 | 635.4 | 7781 | 338.4 | 46.89 | 1136 |
| B6 | n/a  | 639.0 | 7841 | 339.6 | 47.12 | 1143 |
| C1 | 502.2 | 612.0 | 7518 | 335.4 | 46.18 | 1102 |
| C2 | 546.2 | 610.1 | 7522 | 335.1 | 46.15 | 1100 |
| C3 | 440.9 | 612.8 | 7496 | 335.4 | 46.13 | 1101 |
| C4 | 510.2 | 620.4 | 7652 | 338.7 | 46.73 | 1117 |
| C5 | 524.2 | 604.1 | 7388 | 332.4 | 45.67 | 1087 |
| C6 | n/a  | 606.9 | 7437 | 333.5 | 45.86 | 1092 |

Relative to BS 2050, the diet-scenario spread at fixed coefficients is modest:
FAOSTAT-consumption carbon ranges −7.4 % (C5) to +10.0 % (A4); diet land −9.9 %
(C5) to +10.9 % (A4); blue water −1.7 % to +3.4 %; reactive N −1.2 % to +3.9 %.
The **C group** (moderate-consumption / dietary-guideline scenarios)
systematically lowers every footprint; the **A4** high-animal-protein scenario
raises every footprint the most. Production-boundary footprints are identical
across all 19 scenarios (production is exogenous in the results; diet
differences flow entirely through trade) — BS production-side values: carbon
622 Mt, blue water 333 km³, reactive N 45.4 Mt.

### Comparison with the paper's carbon numbers (BS 654 / A1 632.6 / B1 451.2 / C1 502.2)

- **BS reproduces to <0.5 %:** FAOSTAT-consumption 652.1 vs paper 654.0 Mt.
  This validates both the QXXADJ trade-adjustment reconstruction and the FAOSTAT
  China livestock coefficients (which the coefficient README already showed match
  the paper's on-farm factors item-by-item).
- **The scenario spread diverges, and this is expected and informative.** The
  paper's `co2_total` falls steeply for B/C scenarios (B1 451, −31 % vs BS); the
  footprint module moves only ±10 %. Because production is identical across
  scenarios, the paper's large declines **cannot** come from quantities — they
  come from **scenario-specific emission factors** (`FERTEF0/RICEEF0/LVSEF0` SIM
  blocks = supply-side mitigation/technology built into each scenario). Example:
  B1 livestock CO₂ = 225 Mt in the paper vs 348 Mt at fixed 2023 factors — a pure
  technology effect. The footprint module deliberately holds coefficients fixed
  to isolate the **diet-composition + trade** signal; the paper measures **total**
  emissions including supply-side technology. Both are correct; they answer
  different questions.
- **Bonus:** the paper leaves A6/B6/C6 carbon at 0 (uncomputed); the footprint
  module fills them (655.0 / 639.0 / 606.9 Mt FAOSTAT-consumption).
- **Full-life-cycle (P&N) diet footprint** is ~11× the farm-gate number
  (BS 7607 Mt) — the consumer/diet-LCA upper bound, dominated by ruminant meat,
  farmed fish and dairy at cradle-to-retail boundary. Not comparable to the
  farm-gate line; reported as sensitivity S1.

---

## B. World — 2050 footprints and the global net effect of China's diet transition

Farm-gate carbon, blue water, reactive N and land, summed over the 13 CASM-World
regions, split China / rest-of-world (exCHN) / world total.

### BS 2050 baseline
| Indicator | China | rest-of-world | World |
|---|--:|--:|--:|
| Carbon (Mt CO2e) | 535.7 | 4773.2 | 5308.8 |
| Blue water (km³) | 236.1 | 1008.3 | 1244.4 |
| Reactive N (Mt N) | 27.0 | 117.3 | 144.4 |
| Land occupation (Mha, P&N) | 750.8 | 5564.3 | 6315.1 |
| Harvested cropland (Mha, model AHV) | 124.7 | 922.2 | 1046.9 |

### Change vs BS 2050 (Δ absolute, world total)
| Scenario | Carbon | Blue water | Reactive N | Land occ. | **Harvested cropland** |
|---|--:|--:|--:|--:|--:|
| | Mt CO2e | km³ | Mt N | Mha | Mha |
| **HDS** (healthy diet) | **−495.3** (−9.3%) | **−88.8** (−7.1%) | **−10.4** (−7.2%) | **−555.7** (−8.8%) | **−22.7** (−2.2%) |
| MTS (moderate transition) | −299.4 (−5.6%) | −52.8 (−4.2%) | −6.1 (−4.3%) | −332.6 (−5.3%) | −12.9 (−1.2%) |
| PTS (protein-transition) | +64.4 (+1.2%) | +3.8 (+0.3%) | +0.9 (+0.6%) | +81.6 (+1.3%) | +0.7 (+0.1%) |

### Where the HDS savings fall — China vs the rest of the world
| Indicator | China Δ | exCHN Δ | share outside China |
|---|--:|--:|--:|
| Carbon (Mt CO2e) | −44.7 | −450.5 | 91 % |
| Blue water (km³) | −20.7 | −68.1 | 77 % |
| Reactive N (Mt N) | −2.4 | −8.0 | 77 % |
| Land occupation (Mha) | −66.1 | −489.5 | 88 % |
| **Harvested cropland (Mha)** | −1.0 | **−21.7** | 96 % |

**The global net-effect story (Nature-subjournal core):** a healthy-diet
transition in China (HDS) lowers **global** farm-gate agricultural emissions by
~0.50 Gt CO2e (−9.3 %), saves ~89 km³ of blue water (−7.1 %), cuts ~10.4 Mt of
reactive nitrogen (−7.2 %), and releases ~556 Mha of land occupation — of which
**21.7 Mha is physical harvested cropland released outside China** (`land_harvested`
exCHN, matching the known 21.7 Mha figure to two significant digits). The
striking result is that **the majority of every environmental benefit accrues
outside China** (77-96 %): because China imports a large share of its feed and
animal products, moderating domestic animal-food demand propagates through trade
and relieves environmental pressure primarily on exporting regions
(Americas, Oceania, ROW). This is the net global environmental effect of China's
dietary transition — a China policy with a predominantly ex-China footprint.

The two land metrics measure different things: `land_prod` is P&N total
occupation including pasture (large, ruminant/pasture-dominated); `land_harvested`
is the model's own physical harvested cropland (the 21.7 Mha metric). Both are
reported; the cropland figure is the conservative, model-internal one.

---

## C. Self-check (magnitude & integrity)

| Check | Target | Result | OK |
|---|---|---|---|
| China ag carbon (farm-gate) | 0.6–1 Gt | 0.62–0.72 Gt | ✓ |
| China carbon vs paper BS | ≈654 | 652.1 | ✓ |
| China blue water | 100–200 km³ (see note) | ~333 km³ | ⚠ high |
| China reactive N | 20–40 Mt | 45–48 Mt | ≈ (slightly high) |
| World farm-gate carbon | 5–7 Gt | 5.3 Gt | ✓ |
| World blue water | ~1000–1800 km³ | 1244 km³ | ✓ |
| World reactive N | ~150 Mt | 144 Mt | ✓ |
| exCHN cropland release (HDS) | 21.7 Mha | 21.7 Mha | ✓ |
| NaN / blank explosion | none | none | ✓ |
| All 4 CSVs readable | yes | yes | ✓ |

**Notes on the two flags.** (i) China blue water ~333 km³ exceeds the 100–200 km³
target because Mekonnen & Hoekstra 1996–2005 coefficients predate two decades of
Chinese irrigation-efficiency gains and because M&H blue includes livestock
drinking/servicing and feed-crop irrigation; it aligns with China's ~370 km³
total agricultural water withdrawal, so it is the right order of magnitude but
should be read as an upper bound. (ii) Reactive N ~46 Mt slightly exceeds the
40 Mt upper target because the livestock-N surplus term is an approximation
(product-N × Uwizeye surplus ratio, no live-weight data); the crop-fertiliser
component (~30 Mt) is well grounded. Both are documented in `modules/README.md` §4.

---

## Files

- `china_footprints_long.csv` — 127,680 rows: scenario, indicator, coef_source,
  commodity, year, value.
- `china_footprints_summary.csv` — scenario × indicator × {2024, 2035, 2050} +
  %-vs-BS-2050.
- `world_footprints_long.csv` — 22,776 rows: scenario, indicator, coef_source,
  region, commodity, year, value.
- `world_footprints_summary.csv` — scenario × indicator × {CHN, exCHN, WLD} ×
  {2024, 2050} + Δ and %-vs-BS-2050.
