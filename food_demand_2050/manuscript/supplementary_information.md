# Supplementary Information

**China's dietary transition to 2050 reshapes global agricultural markets and environmental footprints**

Shengnan Huang, Xinru Han\*

This Supplementary Information contains: the full 19-scenario definition matrix (Supplementary Table 1); the composite healthy-diet benchmark (Supplementary Table 2); upgraded demand, nutrition and emissions tables with percentage-change columns (Supplementary Tables 3–7); guideline-comparison diet indicators (Supplementary Table 8); the 19-scenario multi-footprint matrix (Supplementary Table 9); planetary-boundary comparison (Supplementary Table 10); the MTS realisation table (Supplementary Table 11); footprint coefficient summary (Supplementary Table 12); and the model validation summary (Supplementary Note 1). All values are reproducible from the open repository (github.com/xinru-han/paper, folder `food_demand_2050`).

---

## Supplementary Table 1 | Full scenario matrix (19 scenarios)

| Code | Group | Dietary pathway | Population | Urbanisation | Ageing |
|---|---|---|---|---|---|
| BS | Baseline | Fixed 2023 income elasticities | Medium (CASS: 1.367 bn 2035, 1.259 bn 2050) | Medium (75.4% 2035, 81.4% 2050) | No |
| A1 | PTS | Dynamic income elasticities (Gouel & Guimbard tiers) | Medium | Medium | No |
| A2 | PTS | Same as A1 | High (UN WPP 2024: 1.420 bn 2035, 1.389 bn 2050) | Medium | No |
| A3 | PTS | Same as A1 | Low (UN WPP 2024: 1.345 bn 2035, 1.200 bn 2050) | Medium | No |
| A4 | PTS | Same as A1 | Medium | High | No |
| A5 | PTS | Same as A1 | Medium | Low | No |
| A6 | PTS | Same as A1 + ageing elasticity term | Adult-equivalent (1.397 bn 2035, 1.270 bn 2050) | Medium | Yes |
| B1 | HDS | Convergence to composite healthy-diet benchmark by 2050 | Medium | Medium | No |
| B2 | HDS | Same as B1 | High | Medium | No |
| B3 | HDS | Same as B1 | Low | Medium | No |
| B4 | HDS | Same as B1 | Medium | High | No |
| B5 | HDS | Same as B1 | Medium | Low | No |
| B6 | HDS | Same as B1 + ageing elasticity term | Adult-equivalent | Medium | Yes |
| C1 | MTS | Growth rate = mean(PTS, HDS) | Medium | Medium | No |
| C2 | MTS | Same as C1 | High | Medium | No |
| C3 | MTS | Same as C1 | Low | Medium | No |
| C4 | MTS | Same as C1 | Medium | High | No |
| C5 | MTS | Same as C1 | Medium | Low | No |
| C6 | MTS | Same as C1 + ageing elasticity term | Adult-equivalent | Medium | Yes |

Ageing adjustment: population converted to adult-equivalent consumers using age–sex dietary-energy requirement weights, plus an income-elasticity adjustment of −0.0314 per percentage-point increase in the old-age share. Source files: `scenarios/scenario_definitions.csv`, `scenarios/macro_assumptions.csv`.

## Supplementary Table 2 | Composite healthy-diet benchmark

Recommended intake (g per person per day) by reference system (midpoints), the composite band, and the implied 2050 purchase target (kg per person per year, converted with edible shares).

| Food group | China 2022 | EAT-Lancet | Taiwan | Japan | Mediterranean | Composite band (min–max) | Composite mid | Edible share | Purchase target (kg/yr, composite mid) | 2023 CASM actual (kg/yr) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Cereals | 250 | 232 | 260 | 240 | 150 | 150–260 | 205 | 0.70 | 106.9 | 190.5 |
| Tubers | 100 | 50 | — | — | — | 50–100 | 75 | 0.90 | 30.4 | 41.7 |
| Legumes | 20 | 50 | 110 | — | 64 | 20–110 | 65 | 1.00 | 23.7 | 11.0 |
| Edible oils | 27.5 | 55.9 | 22.5 | — | 54 | 22.5–55.9 | 39.2 | 1.00 | 14.3 | 21.6 |
| Meat | 57.5 | 43 | 165 | — | 42 | 42–165 | 103.6 | 1.00 | 37.8 | 59.6 |
| Eggs | 45 | 12.5 | — | — | 15.7 | 12.5–45 | 28.8 | 0.88 | 11.9 | 16.9 |
| Dairy | 400 | 250 | 360 | 200 | 281 | 200–400 | 300 | 1.00 | 109.5 | 37.1 |
| Vegetables | 400 | 400 | 400 | 455 | 350 | 350–455 | 402.5 | 0.87 | 168.9 | 136.1 |
| Fruits | 275 | 200 | 300 | 200 | 250 | 200–300 | 250 | 0.82 | 111.3 | 110.9 |
| Sugar | 25 | 15.5 | — | — | — | 15.5–25 | 20.3 | 1.00 | 7.4 | 4.1 |
| Aquatic products | 57.5 | 50 | 192.5 | — | 71.4 | 50–192.5 | 121.3 | 0.59 | 75.0 | 22.2 |

The composite band is the cross-system minimum and maximum of the five systems' midpoints; the composite target is the band midpoint. A Korean guideline was excluded (servings without gram weights). Purchase target = composite mid ÷ edible share × 365/1000. HDS converges from the 2023 CASM actual to the purchase target by 2050 at a constant growth rate. Source: `scenarios/healthy_diet_benchmark.csv`.

## Supplementary Table 3 | Per-capita food demand, 2050 (kg per person per year; % change versus BS 2050 in parentheses)

| Food group | 2024 | BS 2050 | PTS (A1) 2050 | MTS (C1) 2050 | HDS (B1) 2050 |
|---|---:|---:|---:|---:|---:|
| Rice | 111.13 | 96.59 | 90.50 (−6.3%) | 76.86 (−20.4%) | 65.20 (−32.5%) |
| Wheat | 64.62 | 55.77 | 52.94 (−5.1%) | 44.67 (−19.9%) | 37.65 (−32.5%) |
| Edible oils | 22.18 | 24.26 | 25.55 (+5.3%) | 18.56 (−23.5%) | 13.42 (−44.7%) |
| Fruits | 116.31 | 125.14 | 131.82 (+5.3%) | 121.61 (−2.8%) | 112.17 (−10.4%) |
| Vegetables | 144.97 | 151.41 | 153.39 (+1.3%) | 158.45 (+4.6%) | 163.68 (+8.1%) |
| Pork | 31.56 | 38.24 | 42.42 (+10.9%) | 21.76 (−43.1%) | 10.97 (−71.3%) |
| Beef | 6.78 | 9.15 | 9.76 (+6.7%) | 4.96 (−45.8%) | 2.48 (−72.9%) |
| Mutton | 3.52 | 4.88 | 5.20 (+6.6%) | 2.64 (−45.9%) | 1.32 (−73.0%) |
| Poultry | 17.00 | 23.33 | 25.22 (+8.1%) | 28.70 (+23.0%) | 32.64 (+39.9%) |
| Eggs | 16.95 | 18.75 | 20.27 (+8.1%) | 16.04 (−14.5%) | 12.66 (−32.5%) |
| Dairy products | 35.49 | 47.32 | 57.47 (+21.4%) | 76.70 (+62.1%) | 102.05 (+115.7%) |
| Aquatic products | 22.75 | 28.74 | 31.06 (+8.1%) | 43.42 (+51.1%) | 60.43 (+110.3%) |

BS, baseline; PTS, preference-driven transition; MTS, moderate transition; HDS, healthy-diet scenario (representative medium-population, medium-urbanisation cases A1/C1/B1). 2035 values and all demographic variants: repository files `results/results_long.csv` (variable `food_demand_pc`). Upgrades manuscript Table 2 of the previous version.

## Supplementary Table 4 | Aggregate food demand, 2050 (million tonnes; % change versus BS 2050)

| Food group | 2024 | BS 2050 | PTS (A1) 2050 | MTS (C1) 2050 | HDS (B1) 2050 |
|---|---:|---:|---:|---:|---:|
| Rice | 156.5 | 121.1 | 113.5 (−6.3%) | 96.4 (−20.4%) | 81.8 (−32.5%) |
| Wheat | 91.0 | 69.9 | 66.4 (−5.0%) | 56.0 (−19.9%) | 47.2 (−32.5%) |
| Edible oils | 31.2 | 30.4 | 32.0 (+5.3%) | 23.3 (−23.4%) | 16.8 (−44.7%) |
| Fruits | 163.8 | 157.0 | 165.3 (+5.3%) | 152.5 (−2.9%) | 140.7 (−10.4%) |
| Vegetables | 204.2 | 189.9 | 192.4 (+1.3%) | 198.7 (+4.6%) | 205.3 (+8.1%) |
| Pork | 44.4 | 48.0 | 53.2 (+10.8%) | 27.3 (−43.1%) | 13.8 (−71.2%) |
| Beef | 9.5 | 11.5 | 12.2 (+6.1%) | 6.2 (−46.1%) | 3.1 (−73.0%) |
| Mutton | 5.0 | 6.1 | 6.5 (+6.6%) | 3.3 (−45.9%) | 1.7 (−72.1%) |
| Poultry | 23.9 | 29.3 | 31.6 (+7.8%) | 36.0 (+22.9%) | 40.9 (+39.6%) |
| Eggs | 23.9 | 23.5 | 25.4 (+8.1%) | 20.1 (−14.5%) | 15.9 (−32.3%) |
| Dairy products | 50.0 | 59.3 | 72.1 (+21.6%) | 96.2 (+62.2%) | 128.0 (+115.9%) |
| Aquatic products | 32.0 | 36.0 | 39.0 (+8.3%) | 54.5 (+51.4%) | 75.8 (+110.6%) |

High-/low-population variants rescale all rows by approximately ±7%; the ageing adjustment (A6/B6/C6) lowers aggregate demand by 3–7% without reordering pathways. Upgrades manuscript Table 3 of the previous version.

## Supplementary Table 5 | Nutrition outcomes, 2024 and 2050 (% change versus BS 2050)

| Indicator | Unit | 2024 | BS 2050 | PTS (A1) 2050 | MTS (C1) 2050 | HDS (B1) 2050 |
|---|---|---:|---:|---:|---:|---:|
| Dietary energy | kcal cap⁻¹ d⁻¹ | 2,957.6 | 3,035.8 | 3,091.1 (+1.8%) | 2,571.5 (−15.3%) | 2,257.7 (−25.6%) |
| Protein | g cap⁻¹ d⁻¹ | 95.4 | 104.3 | 107.8 (+3.4%) | 98.8 (−5.3%) | 98.1 (−5.9%) |
| Fat | g cap⁻¹ d⁻¹ | 117.3 | 133.8 | 143.1 (+7.0%) | 104.7 (−21.7%) | 82.7 (−38.2%) |
| Carbohydrate | g cap⁻¹ d⁻¹ | 374.2 | 345.4 | 335.5 (−2.9%) | 300.1 (−13.1%) | 271.4 (−21.4%) |
| Protein share of energy | % | 12.9 | 13.7 | 14.0 | 15.4 | 17.4 |
| Fat share of energy | % | 35.7 | 39.7 | 41.7 | 36.7 | 33.0 |
| Carbohydrate share of energy | % | 50.6 | 45.5 | 43.4 | 46.7 | 48.1 |

All values are from the internally consistent (current-coefficient) nutrition accounting of the open-source model. The previous manuscript's Table 4 mixed two coefficient vintages for BS/PTS (e.g. BS 2050 energy reported as 3,070.3 kcal from a stale legacy workbook); the consistent value is 3,035.8 kcal (Supplementary Note 1). Upgrades manuscript Table 4.

## Supplementary Table 6 | China GHG emissions under two accountings, 2050 (Mt CO₂e; % versus BS 2050)

**a. Total accounting (diet + scenario-specific supply-side technology), as in conventional single-country studies**

| Scenario | Crop | Livestock | Total | % vs BS |
|---|---:|---:|---:|---:|
| BS | 305.9 | 348.1 | 654.0 | — |
| PTS (A1) | 249.2 | 383.4 | 632.6 | −3.3% |
| MTS (C1) | 236.6 | 265.6 | 502.2 | −23.2% |
| HDS (B1) | 226.0 | 225.3 | 451.2 | −31.0% |

**b. Fixed 2023 coefficients (FAOSTAT farm-gate, consumption boundary) — pure diet-composition + trade signal**

| Scenario | Carbon (Mt CO₂e) | % vs BS | Blue water (km³) | Reactive N (Mt N) | Diet land (Mha) |
|---|---:|---:|---:|---:|---:|
| BS | 652.1 | — | 338.1 | 46.2 | 1,206 |
| PTS (A1) | 681.1 | +4.4% | 340.5 | 46.8 | 1,270 |
| MTS (C1) | 612.0 | −6.1% | 335.4 | 46.2 | 1,102 |
| HDS (B1) | 645.5 | −1.0% | 341.8 | 47.5 | 1,155 |

Comparing panels a and b decomposes the headline −31% (HDS) into supply-side technology (roughly two-thirds) and diet composition (roughly one-third). Panel b also supplies the ageing-scenario emissions absent from the legacy implementation: A6 655.0, B6 639.0, C6 606.9 Mt CO₂e. Upgrades manuscript Tables 5–6; full 19-scenario matrix in Supplementary Table 9.

## Supplementary Table 7 | World price and China net-import changes, 2050 (HDS/MTS/PTS versus BS)

| Commodity | BS world price ($/t) | PTS Δ% | MTS Δ% | HDS Δ% | China BS net imports (Mt) | HDS Δ net imports (Mt) |
|---|---:|---:|---:|---:|---:|---:|
| Rice | 2,807 | −3.3 | −23.9 | −36.7 | 24.2 | −58.3 |
| Wheat | 1,202 | −1.1 | −20.3 | −32.3 | 38.7 | −57.5 |
| Maize | 717 | +4.0 | −20.4 | −33.3 | 39.7 | −35.9 |
| Soybeans | 1,736 | +4.5 | −20.8 | −34.6 | 115.8 | −7.4 |
| Soybean oil | 7,171 | +5.4 | −28.1 | −47.8 | 5.4 | −8.7 |
| Soybean meal | 916 | +5.8 | −14.6 | −21.7 | 11.5 | −14.3 |
| Beef | 18,901 | +4.8 | −25.8 | −40.3 | 9.0 | −12.3 |
| Pork | 8,671 | +9.4 | −36.3 | −56.3 | 11.7 | −40.6 |
| Poultry | 5,778 | +5.7 | −14.7 | −24.9 | 5.8 | +3.7 |
| Butter | 16,240 | +1.7 | −5.6 | −9.3 | — | +0.4 |
| Skim milk powder | 8,123 | +7.0 | +3.0 | +5.6 | — | +0.6 |
| Whole milk powder | 10,787 | +9.8 | +11.2 | +20.4 | 1.1 | +2.0 |
| Sugar | 29,306 | +2.3 | −14.0 | −23.4 | — | — |

Net-import changes exceeding baseline net imports (rice, wheat, pork) imply a switch to net exports. Source: `results/world/world_results_long.csv`.

## Supplementary Table 8 | Diet-quality indicators versus guidelines, 2050 (edible g per capita per day)

| Indicator | Guideline range | BS | PTS | MTS | HDS |
|---|---|---:|---:|---:|---:|
| Red meat (pork+beef+mutton) | 14–28 | 143 | 157 | 80 | 40 |
| Total meat (incl. poultry) | 40–75 | 185 | 202 | 132 | 99 |
| Cereals | 200–300 | 322 | 305 | 263 | 227 |
| Vegetables | 300–500 | 415 | 420 | 434 | 448 |
| Fruits | 200–350 | 343 | 361 | 333 | 307 |
| Dairy | 300–500 | 130 | 157 | 210 | 280 |
| Aquatic products | 40–75 | 46 | 50 | 70 | 98 |
| Eggs | 40–50 | 45 | 49 | 39 | 31 |
| Added sugar | 0–50 | 13 | 13 | 13 | 13 |
| Fat energy share (%E) | 20–30 | 40 | 42 | 37 | 33 |
| Dietary energy (kcal/d) | 2,000–2,600 | 3,036 | 3,091 | 2,572 | 2,258 |

Dairy remains below the Chinese-guideline 300 g floor even under HDS — the "guideline gap" behind the counter-cyclical world milk-powder price. Source: `results/post_analysis/diet_health_proxies_2050.csv`.

## Supplementary Table 9 | 19-scenario multi-footprint matrix, China 2050 (fixed 2023 coefficients, consumption boundary)

| Scenario | FAOSTAT farm-gate carbon (Mt CO₂e) | P&N life-cycle carbon (Mt CO₂e) | Blue water (km³) | Reactive N (Mt N) | Diet land (Mha) |
|---|---:|---:|---:|---:|---:|
| BS | 652.1 | 7,607 | 338.1 | 46.21 | 1,206 |
| A1 | 681.1 | 7,834 | 340.5 | 46.81 | 1,270 |
| A2 | 676.4 | 7,814 | 339.1 | 46.69 | 1,266 |
| A3 | 681.4 | 7,815 | 341.0 | 46.80 | 1,266 |
| A4 | 717.4 | 8,134 | 349.7 | 48.00 | 1,337 |
| A5 | 649.8 | 7,562 | 334.3 | 45.87 | 1,206 |
| A6 | 655.0 | 7,609 | 335.4 | 46.06 | 1,219 |
| B1 | 645.5 | 7,939 | 341.8 | 47.49 | 1,155 |
| B2 | 643.1 | 7,946 | 341.4 | 47.47 | 1,153 |
| B3 | 646.7 | 7,911 | 341.8 | 47.43 | 1,154 |
| B4 | 655.7 | 8,098 | 345.3 | 48.08 | 1,173 |
| B5 | 635.4 | 7,781 | 338.4 | 46.89 | 1,136 |
| B6 | 639.0 | 7,841 | 339.6 | 47.12 | 1,143 |
| C1 | 612.0 | 7,518 | 335.4 | 46.18 | 1,102 |
| C2 | 610.1 | 7,522 | 335.1 | 46.15 | 1,100 |
| C3 | 612.8 | 7,496 | 335.4 | 46.13 | 1,101 |
| C4 | 620.4 | 7,652 | 338.7 | 46.73 | 1,117 |
| C5 | 604.1 | 7,388 | 332.4 | 45.67 | 1,087 |
| C6 | 606.9 | 7,437 | 333.5 | 45.86 | 1,092 |

Spread versus BS 2050: carbon −7.4% (C5) to +10.0% (A4); land −9.9% to +10.9%; blue water −1.7% to +3.4%; reactive N −1.2% to +3.9%. The MTS (C) family is the only pathway lowering every footprint. Farm-gate and life-cycle boundaries are never blended. Source: `results/footprints/china_footprints_summary.csv`.

## Supplementary Table 10 | Global net effect of China's dietary transition, 2050 (Δ versus BS; world totals and incidence)

| Indicator | World BS 2050 | HDS Δ | HDS Δ% | MTS Δ | PTS Δ | HDS: China Δ | HDS: ex-China Δ | Share outside China |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Carbon (Mt CO₂e, farm-gate) | 5,308.8 | −495.3 | −9.3% | −299.4 | +64.4 | −44.7 | −450.5 | 91% |
| Blue water (km³) | 1,244.4 | −88.8 | −7.1% | −52.8 | +3.8 | −20.7 | −68.1 | 77% |
| Reactive N (Mt N) | 144.4 | −10.4 | −7.2% | −6.1 | +0.9 | −2.4 | −8.0 | 77% |
| Land occupation (Mha, incl. pasture) | 6,315.1 | −555.7 | −8.8% | −332.6 | +81.6 | −66.1 | −489.5 | 88% |
| Harvested cropland (Mha) | 1,046.9 | −22.7 | −2.2% | −12.9 | +0.7 | −1.0 | −21.7 | 96% |

Per-capita planetary-boundary comparison (EAT-Lancet food-system boundaries at 9.7 bn people): China's farm-gate GHG per capita is 1.01× the boundary share under BS, 1.05× under PTS and 0.95× under MTS; reactive N (~4×) and land (~7×, cradle incl. pasture, not directly comparable to the cropland-only boundary) exceed boundary shares in all scenarios. Sources: `results/footprints/world_footprints_summary.csv`, `results/post_analysis/per_capita_footprints_vs_boundaries.csv`.

## Supplementary Table 11 | MTS realisation (share of the PTS→HDS change under the moderate pathway)

| Domain | Indicator | PTS | MTS | HDS | MTS realisation |
|---|---|---:|---:|---:|---:|
| China diet | Dietary energy (kcal cap⁻¹ d⁻¹) | 3,091 | 2,572 | 2,258 | 62% |
| China diet | Fat energy share (%E) | 41.7 | 36.7 | 33.0 | 58% |
| China diet | Red meat (g cap⁻¹ d⁻¹) | 157 | 80 | 40 | 66% |
| China footprint | CO₂, total accounting (Mt) | 632.6 | 502.2 | 451.2 | 72% |
| World market | Pork price (Δ% vs BS) | +9.4 | −36.3 | −56.3 | 70% |
| World market | Soybean price (Δ% vs BS) | +4.5 | −20.8 | −34.6 | 65% |
| Global net effect | Global agricultural CO₂ (Mt) | 5,373 | 5,009 | 4,814 | 65% |
| Global net effect | Ex-China harvested cropland (Mha) | 922.8 | 909.9 | 900.6 | 58% |

Median realisation across the full set of 21 indicators: 65%; most indicators lie in the 55–65% band. Realisations above 100% (fixed-coefficient consumption CO₂/land, not shown) occur where HDS's dairy/aquatic expansion partly offsets its red-meat cuts while MTS avoids that rebound. Source: `results/post_analysis/mts_efficiency.csv`.

## Supplementary Table 12 | Footprint coefficient library — sources and boundaries

| Dimension | Source | Boundary / scope | CASM mapping |
|---|---|---|---|
| Carbon (main) | FAOSTAT Emissions intensities, reference year 2023 | Cradle-to-farm-gate (on-farm) | China values for livestock, rice, cereals; world elsewhere |
| Carbon (sensitivity S1) | Poore & Nemecek (2018), Science | Cradle-to-retail LCA (≈11× farm-gate for the diet basket) | World means, ~all commodities |
| Blue water | Mekonnen & Hoekstra (2011; 2012) | Consumptive blue water at farm, 1996–2005 (upper bound for China) | China columns for animal products; world for crops |
| Reactive N | Ludemann et al. (2022); IPCC (2019) Table 10.19; Leach et al. (2012); Uwizeye et al. (2020) | Fertiliser N + livestock excretion/supply-chain N | China crop N rates as reported |
| Land | Poore & Nemecek (2018); model harvested area | Occupation (arable+pasture); physical harvested cropland | World means; model-internal cropland |

Every cell in the library carries a per-value citation; unsourced cells are flagged `GAP`, never imputed. Cross-check: the legacy China livestock factors match FAOSTAT China farm-gate intensities item-by-item (pig 0.92 vs 0.96; cattle 15.82 vs 15.19; eggs 0.58 vs 0.55 t CO₂e t⁻¹). Full library: `modules/coefficients/`.

## Supplementary Note 1 | Validation of the open-source implementation

The Python re-implementation of CASM v2.2.7 was validated cell-by-cell against the original GAMS solution workbooks across all 19 scenarios (~1,076 compared cells per scenario spanning 16 variable sheets × commodities × reporting years plus macro rows). Median relative deviation is ≤ 1.4 × 10⁻¹⁶ (machine precision); the single worst cell is a reporting artefact in the GAMS workbook (seed demand recorded for soybean oil in the pre-base year, substantively zero). Reproduction of the previous manuscript's tables achieves a worst deviation of 1.8 × 10⁻³, attributable to two-decimal rounding. Two legacy artefacts were identified and corrected: (1) one legacy result workbook reported BS/PTS nutrition from an outdated energy-coefficient table (BS 2050 energy 3,070.3 kcal instead of the internally consistent 3,035.8 kcal); this paper uses the consistent set throughout. (2) The legacy emission-factor tables did not define the ageing scenarios (A6/B6/C6), so their emissions were previously unreported; the scenario-invariant footprint module now covers all 19 scenarios. CASM-World converges in every year of every scenario with world market-clearing residuals ≤ 7 × 10⁻⁹ (mostly ~10⁻¹³). Full report: `results/validation_report.md`.
