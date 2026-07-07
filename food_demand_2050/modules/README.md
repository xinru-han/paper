# Environmental Footprint Module (`footprints.py`)

Carbon / water / nitrogen / land footprint accounting for the Food-Demand-2050
project, applied to **all 19 China CASM scenarios** (BS, A1-A6, B1-B6, C1-C6,
2023-2050) and **all 4 CASM-World scenarios** (BS, PTS, HDS, MTS; 13 regions;
2024-2050).

- Code: `modules/footprints.py` (pure standard-library Python; `python3 modules/footprints.py`)
- Coefficients: `modules/coefficients/*.csv` (fully cited — read
  `coefficients/README.md` first; **the system-boundary warning there governs
  everything below**).
- Outputs: `results/footprints/` (four CSVs + `footprints_report.md`).

---

## 1. What is computed

| Indicator (China) | Boundary | Formula | Unit |
|---|---|---|---|
| `co2_faostat_prod` | FAOSTAT farm-gate, **production** | production × FAOSTAT China EI | Mt CO2e |
| `co2_faostat_cons` | FAOSTAT farm-gate, **trade-adjusted consumption** (QXXADJ) | QXXADJ × FAOSTAT China EI | Mt CO2e |
| `co2_pn_lca` | Poore & Nemecek **cradle-to-retail**, consumption | QXXADJ × P&N world LCA | Mt CO2e |
| `water_green/blue/grey` | M&H, **consumption** | QXXADJ × M&H (CHN livestock / WLD crops) | km3 |
| `water_*_prod` | M&H, **production** | production × M&H | km3 |
| `nitrogen_total` | reactive N, **consumption** | QXXADJ × per-t N | Mt N |
| `nitrogen_prod` | reactive N, **production** | production × per-t N | Mt N |
| `land_diet` | P&N land occupation, **consumption** | QXXADJ × P&N m²·yr/kg | Mha·yr |

| Indicator (World) | Formula | Unit |
|---|---|---|
| `co2_faostat` | regional PRD × FAOSTAT EI (CHN for China, else WLD) | Mt CO2e |
| `water_green/blue/grey` | regional PRD × M&H | km3 |
| `nitrogen_total` | regional PRD × per-t N | Mt N |
| `land_prod` | regional PRD × P&N m²·yr/kg (occupation incl. pasture) | Mha·yr |
| `land_harvested` | model AHV (harvested area) summed | Mha |

The China `long` file also emits zero-valued `co2_faostat_gap` rows that
**flag** every commodity for which FAOSTAT publishes no farm-gate value (see §4).

### Trade-adjusted consumption (QXXADJ)
Replicates the original CASM carbon accounting exactly
(`model/casm/output.py` §4.3): `QXXADJ = production + (net_import − net_import₂₀₂₃)`,
i.e. domestic apparent consumption anchored so that the 2023 trade balance is
treated as the structural baseline. This is why `co2_faostat_cons` for BS 2050
(**652 Mt**) reproduces the paper's published `co2_total` (**654 Mt**) to <0.5 %.

### Commodity coverage (primary commodities only)
To avoid double-counting, only **primary** commodities enter the footprints —
oilseeds (SOYS, RAPS, GRDS) not their crushed oils/meals; SUGC+SUGB not the
SUGA aggregate. China set: 15 crops + 7 livestock/fish. World set: 10 crops +
6 livestock (world codes).

---

## 2. Unit handling (verified against known totals)

China results are in **万吨 = 10⁴ t** (production, food demand, net trade),
**万ha = 10⁴ ha** (area), t/ha (yield). World results are in **Mt = 10⁶ t**.
Conversions to headline units:

```
carbon   kgCO2e/kg = tCO2e/t : 万吨×coef/100 → MtCO2e ;  Mt×coef → MtCO2e
water    m³/t              : 万吨×coef/1e5 → km³ ;      Mt×coef/1e3 → km³
nitrogen kgN/t             : 万吨×coef×1e4/1e9 → MtN ;   Mt×coef/1e3 → MtN
land     m²·yr/kg          : 万吨×coef×1e7/1e10 → Mha ;  Mt×coef×1e9/1e10 → Mha
```

Sanity anchors (BS 2050): FAOSTAT consumption carbon 652 Mt (≈paper 654),
farm-gate production carbon 622 Mt, blue water 338 km³, reactive N 46 Mt,
diet land 1206 Mha; world farm-gate carbon 5.3 Gt, blue water 1244 km³, N 144 Mt.
All within the expected order of magnitude.

---

## 3. Boundary choice and the dual-boundary carbon sensitivity

Three carbon boundaries are reported **side by side, never blended** (the
coefficient README forbids averaging boundaries):

1. **FAOSTAT farm-gate** (`co2_faostat_*`) — on-farm only. This is the internally
   consistent main scenario and the one comparable to the paper's `co2_total`.
2. **Poore & Nemecek cradle-to-retail** (`co2_pn_lca`) — adds feed, land-use
   change, processing, transport, packaging, retail and losses. BS 2050 = **7607
   Mt**, i.e. ~11× the farm-gate number. This is the *consumer/diet* footprint
   and is deliberately an upper bound; it is not comparable to the farm-gate line.
3. **Original CASM China library** (`co2_total` in `results_long.csv`) — the
   paper's own on-farm factors. Pulled directly for comparison, not recomputed.

The farm-gate (1) and the P&N (2) differ by boundary, not by data quality. The
12× pig-meat gap flagged in the coefficient README is exactly this.

---

## 4. Gap handling (honest accounting)

- **FAOSTAT crop gaps.** FAOSTAT Emissions-intensities publishes farm-gate EI
  only for rice and the *cereals-excl-rice* aggregate (applied to WHEA, MAIZ,
  OTGR, SORG, BARL) plus all livestock **except aquaculture**. It has **no**
  farm-gate value for potato, oilseeds, sugar crops, cotton, fruit, vegetables
  or fish. Rather than boundary-mix a cradle-to-retail P&N number into the
  farm-gate total (which inflated it to 3.9 Gt in testing, driven mostly by
  farmed-fish LCA), those commodities contribute **zero** to `co2_faostat_*`
  and are flagged as `co2_faostat_gap` rows. Their full-life-cycle emissions are
  instead captured in the separate `co2_pn_lca` indicator. Consequently the
  farm-gate China total (~0.62–0.65 Gt) is a clean lower bound reflecting rice
  CH₄, cereal N₂O and livestock; the diet LCA (~7.6 Gt) is the upper bound.
- **Water:** M&H China columns used for all livestock; WLD used for crops
  (no per-crop China cells published). Grey water reported separately (dilution
  volume, not a withdrawal). Aquaculture absent from M&H → FISH has no water
  footprint here.
- **Nitrogen crop:** per-tonne N = Ludemann 2022 China N-rate (kg N/ha) ÷ model
  yield (t/ha), so the same coefficient serves both boundaries. Groundnut N-rate
  is a genuine gap (folded into "other oil crops" in FUBC9) → GRDS omitted from N.
- **Nitrogen livestock:** reactive-N surplus = product-N content (protein%/6.25)
  × Uwizeye 2020 surplus ratio (feed-N/product-N − 1: beef 4, sheep/goat 4,
  pork 2, poultry 1, eggs 2.5, milk 3, fish 1). This is a documented
  **approximation** (no live-weight/turnover data in the results) — it captures
  the diet-composition signal, not an inventory-grade manure-N estimate.
- **Land:** P&N global-mean occupation (arable + pasture). CATM uses the
  **beef-herd** row (326 m²·yr/kg), the dominant Chinese beef supply, so
  `land_diet`/`land_prod` are large and pasture-dominated. For a physical
  cropland metric the world module additionally reports `land_harvested`
  straight from the model's harvested-area variable (AHV).

---

## 5. Key methodological finding — why the scenario spread differs from the paper

**China production is scenario-invariant** in the results set (BS…C6 have
identical production paths); all diet-scenario differences flow through
**trade** (`net_import`). Therefore:

- Production-boundary footprints (`*_prod`) are identical across all 19
  scenarios — they describe what happens on Chinese soil, which the scenarios
  do not move.
- Consumption-boundary footprints (`co2_faostat_cons`, `water_*`,
  `nitrogen_total`, `land_diet`) vary with diet, but only by **±10 %**, because
  they hold coefficients fixed at 2023 international values and move only with
  quantities/trade.

The paper's own `co2_total` varies far more (BS 654 → B1 451 Mt, −31 %). Since
production is invariant, that larger spread **cannot** come from quantities — it
comes from **scenario-specific emission factors** (the `FERTEF0/RICEEF0/LVSEF0`
SIM blocks in `1parameter.xlsx`), i.e. supply-side mitigation/technology built
into each scenario. Concretely, B1 livestock CO₂ falls to 225 Mt vs 348 Mt at
fixed factors — a pure technology effect.

**The two accountings answer different questions and are both correct:**
the paper measures *total* emissions including per-scenario supply-side
technology; the footprint module isolates the *diet-composition + trade*
footprint at fixed coefficients. The report tabulates both.

---

## 6. Reproducing

```bash
cd food_demand_2050
python3 modules/footprints.py          # writes results/footprints/*.csv
```
No third-party dependencies. Runtime ≈ a few seconds. Re-run is idempotent.
