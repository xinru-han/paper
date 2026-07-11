# Validation report — Python CASM vs GAMS (3RESULTCOM)

Python port of CASM v2.2.7 (base 2024, projections 2025-2050), 19 scenarios (BS + A1-A6 + B1-B6 + C1-C6).

GAMS truth: 预测结果整理/3RESULTCOM-{normal,diet,median}.XLSX. Comparison over the reported periods TSP = 2023/2024/2035/2050.

## Per-scenario deviation summary

`n` = number of compared cells (16 variable sheets x commodities x TSP years + 10 macro rows). Relative deviation = |py - gams| / max(|gams|, 1e-9).

| scenario | group | SIM | n | median rel.dev | max rel.dev | worst cell | max rel.dev (GAMS>1) | worst cell (GAMS>1) |
|---|---|---|---|---|---|---|---|---|
| BS | PTS | BASE | 1118 | 1.38e-16 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| A1 | PTS | SIM1 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| A4 | PTS | SIM2 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| A5 | PTS | SIM3 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| A2 | PTS | SIM4 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| A3 | PTS | SIM5 | 1070 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| A6 | PTS | SIM6 | 1058 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| B1 | HDS | SIM1 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| B4 | HDS | SIM2 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| B5 | HDS | SIM3 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| B2 | HDS | SIM4 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| B3 | HDS | SIM5 | 1070 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| B6 | HDS | SIM6 | 1058 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| C1 | MTS | SIM1 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| C4 | MTS | SIM2 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| C5 | MTS | SIM3 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| C2 | MTS | SIM4 | 1076 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| C3 | MTS | SIM5 | 1070 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |
| C6 | MTS | SIM6 | 1058 | 0.00e+00 | 1.00e+00 | SEEDX/SOYO/2023 | 1.00e+00 | SEEDX/SOYO/2023 |

## Key indicators, 2050 (Python vs GAMS)

| scenario | per-capita rice demand 2050 (kg) | per-capita pork demand 2050 (kg) | per-capita dairy demand 2050 (kg) | dietary energy 2050 (kcal/cap/day) | total CO2 2050 (万吨 CO2e) |
|---|---|---|---|---|---|
| BS | 96.59 / 96.59 | 38.24 / 38.24 | 47.32 / 47.32 | 3035.84 / 3070.27 | 65402.02 / 65402.02 |
| A1 | 90.50 / 90.50 | 42.42 / 42.42 | 57.47 / 57.47 | 3091.10 / 3127.59 | 63259.49 / 63259.49 |
| A4 | 90.50 / 90.50 | 42.42 / 42.42 | 57.47 / 57.47 | 3091.10 / 3127.59 | 62346.09 / 62346.09 |
| A5 | 90.50 / 90.50 | 42.42 / 42.42 | 57.47 / 57.47 | 3091.10 / 3127.59 | 64822.47 / 64822.47 |
| A2 | 88.47 / 88.47 | 41.89 / 41.89 | 56.42 / 56.42 | 3042.81 / 3078.94 | 67890.71 / 67890.71 |
| A3 | 92.67 / 92.67 | 42.99 / 42.99 | 58.58 / 58.58 | 3142.69 / 3179.57 | 54368.96 / 54368.96 |
| A6 | 89.16 / 89.16 | 42.50 / 42.50 | 56.38 / 56.38 | 3047.17 / 3083.12 | 0.00 / n.a. |
| B1 | 65.20 / 65.20 | 10.97 / 10.97 | 102.05 / 102.05 | 2257.70 / 2257.70 | 45124.58 / 45124.58 |
| B4 | 65.20 / 65.20 | 10.97 / 10.97 | 102.05 / 102.05 | 2257.70 / 2257.70 | 46260.88 / 46260.88 |
| B5 | 65.20 / 65.20 | 10.97 / 10.97 | 102.05 / 102.05 | 2257.70 / 2257.70 | 47461.17 / 47461.17 |
| B2 | 63.74 / 63.74 | 10.83 / 10.83 | 100.20 / 100.20 | 2226.12 / 2226.12 | 49292.94 / 49292.94 |
| B3 | 66.76 / 66.76 | 11.11 / 11.11 | 104.03 / 104.03 | 2291.44 / 2291.44 | 39895.81 / 39895.81 |
| B6 | 64.49 / 64.49 | 10.98 / 10.98 | 100.62 / 100.62 | 2231.30 / 2231.30 | 0.00 / n.a. |
| C1 | 76.86 / 76.86 | 21.76 / 21.76 | 76.70 / 76.70 | 2571.50 / 2571.50 | 50222.26 / 50222.26 |
| C4 | 76.86 / 76.86 | 21.76 / 21.76 | 76.70 / 76.70 | 2571.50 / 2571.50 | 51017.63 / 51017.63 |
| C5 | 76.86 / 76.86 | 21.76 / 21.76 | 76.70 / 76.70 | 2571.50 / 2571.50 | 52422.24 / 52422.24 |
| C2 | 75.13 / 75.13 | 21.49 / 21.49 | 75.31 / 75.31 | 2532.94 / 2532.94 | 54623.48 / 54623.48 |
| C3 | 78.70 / 78.70 | 22.05 / 22.05 | 78.19 / 78.19 | 2612.70 / 2612.70 | 44085.19 / 44085.19 |
| C6 | 76.01 / 76.01 | 21.79 / 21.79 | 75.63 / 75.63 | 2542.68 / 2542.68 | 0.00 / n.a. |

(Each cell: Python / GAMS.)

## Manuscript table cross-check

| item | manuscript | python | rel.dev |
|---|---|---|---|
| T2 Rice 2024 | 111.13 | 111.13 | 1.4e-05 |
| T2 Rice BS 2035 | 103.10 | 103.10 | 3.8e-05 |
| T2 Rice BS 2050 | 96.59 | 96.59 | 4.2e-05 |
| T2 Rice PTS(A1) 2035 | 100.30 | 100.30 | 3.9e-05 |
| T2 Rice PTS(A1) 2050 | 90.50 | 90.50 | 2.4e-06 |
| T2 Rice HDS(B1) 2035 | 87.31 | 87.31 | 5.4e-05 |
| T2 Rice HDS(B1) 2050 | 65.20 | 65.20 | 2.0e-05 |
| T2 Rice MTS(C1) 2035 | 93.60 | 93.60 | 4.3e-05 |
| T2 Rice MTS(C1) 2050 | 76.86 | 76.86 | 5.3e-05 |
| T2 Wheat 2024 | 64.62 | 64.62 | 3.4e-05 |
| T2 Wheat BS 2035 | 59.84 | 59.84 | 1.3e-05 |
| T2 Wheat BS 2050 | 55.77 | 55.77 | 5.1e-05 |
| T2 Wheat PTS(A1) 2035 | 58.54 | 58.54 | 4.5e-05 |
| T2 Wheat PTS(A1) 2050 | 52.94 | 52.94 | 2.6e-05 |
| T2 Wheat HDS(B1) 2035 | 50.68 | 50.68 | 9.4e-05 |
| T2 Wheat HDS(B1) 2050 | 37.65 | 37.65 | 1.0e-04 |
| T2 Wheat MTS(C1) 2035 | 54.48 | 54.48 | 4.6e-05 |
| T2 Wheat MTS(C1) 2050 | 44.67 | 44.67 | 6.1e-05 |
| T2 Edible oils 2024 | 22.18 | 22.18 | 6.9e-05 |
| T2 Edible oils BS 2035 | 23.02 | 23.02 | 1.6e-04 |
| T2 Edible oils BS 2050 | 24.26 | 24.26 | 1.4e-04 |
| T2 Edible oils PTS(A1) 2035 | 23.53 | 23.53 | 9.1e-05 |
| T2 Edible oils PTS(A1) 2050 | 25.55 | 25.55 | 6.7e-07 |
| T2 Edible oils HDS(B1) 2035 | 17.92 | 17.92 | 3.7e-05 |
| T2 Edible oils HDS(B1) 2050 | 13.42 | 13.42 | 2.6e-04 |
| T2 Edible oils MTS(C1) 2035 | 20.55 | 20.55 | 1.5e-05 |
| T2 Edible oils MTS(C1) 2050 | 18.56 | 18.56 | 2.0e-04 |
| T2 Fruits 2024 | 116.31 | 116.31 | 1.6e-05 |
| T2 Fruits BS 2035 | 121.02 | 121.02 | 7.0e-06 |
| T2 Fruits BS 2050 | 125.14 | 125.14 | 3.1e-05 |
| T2 Fruits PTS(A1) 2035 | 123.71 | 123.71 | 1.3e-05 |
| T2 Fruits PTS(A1) 2050 | 131.82 | 131.82 | 2.5e-05 |
| T2 Fruits HDS(B1) 2035 | 115.54 | 115.54 | 3.5e-05 |
| T2 Fruits HDS(B1) 2050 | 112.17 | 112.17 | 1.8e-05 |
| T2 Fruits MTS(C1) 2035 | 119.56 | 119.56 | 2.4e-05 |
| T2 Fruits MTS(C1) 2050 | 121.61 | 121.61 | 2.9e-05 |
| T2 Vegetables 2024 | 144.97 | 144.97 | 1.5e-05 |
| T2 Vegetables BS 2035 | 147.87 | 147.87 | 2.2e-05 |
| T2 Vegetables BS 2050 | 151.41 | 151.41 | 1.7e-05 |
| T2 Vegetables PTS(A1) 2035 | 148.68 | 148.68 | 1.4e-05 |
| T2 Vegetables PTS(A1) 2050 | 153.39 | 153.39 | 2.1e-05 |
| T2 Vegetables HDS(B1) 2035 | 152.82 | 152.82 | 1.4e-06 |
| T2 Vegetables HDS(B1) 2050 | 163.68 | 163.68 | 2.2e-05 |
| T2 Vegetables MTS(C1) 2035 | 150.74 | 150.74 | 1.2e-05 |
| T2 Vegetables MTS(C1) 2050 | 158.45 | 158.45 | 2.9e-05 |
| T2 Pork 2024 | 31.56 | 31.56 | 8.1e-05 |
| T2 Pork BS 2035 | 34.46 | 34.46 | 5.5e-05 |
| T2 Pork BS 2050 | 38.24 | 38.24 | 3.9e-06 |
| T2 Pork PTS(A1) 2035 | 36.01 | 36.01 | 3.0e-05 |
| T2 Pork PTS(A1) 2050 | 42.42 | 42.42 | 5.9e-05 |
| T2 Pork HDS(B1) 2035 | 20.32 | 20.32 | 1.4e-04 |
| T2 Pork HDS(B1) 2050 | 10.97 | 10.97 | 2.0e-04 |
| T2 Pork MTS(C1) 2035 | 27.15 | 27.15 | 4.0e-05 |
| T2 Pork MTS(C1) 2050 | 21.76 | 21.76 | 4.4e-05 |
| T2 Beef 2024 | 6.78 | 6.78 | 4.4e-04 |
| T2 Beef BS 2035 | 7.84 | 7.84 | 2.1e-04 |
| T2 Beef BS 2050 | 9.15 | 9.15 | 2.5e-04 |
| T2 Beef PTS(A1) 2035 | 8.06 | 8.06 | 4.2e-04 |
| T2 Beef PTS(A1) 2050 | 9.76 | 9.76 | 1.3e-04 |
| T2 Beef HDS(B1) 2035 | 4.51 | 4.51 | 7.5e-05 |
| T2 Beef HDS(B1) 2050 | 2.48 | 2.48 | 1.0e-03 |
| T2 Beef MTS(C1) 2035 | 6.05 | 6.05 | 2.0e-04 |
| T2 Beef MTS(C1) 2050 | 4.96 | 4.96 | 4.6e-04 |
| T2 Mutton 2024 | 3.52 | 3.52 | 5.0e-04 |
| T2 Mutton BS 2035 | 4.09 | 4.09 | 1.2e-04 |
| T2 Mutton BS 2050 | 4.88 | 4.88 | 8.9e-04 |
| T2 Mutton PTS(A1) 2035 | 4.20 | 4.20 | 8.1e-04 |
| T2 Mutton PTS(A1) 2050 | 5.20 | 5.20 | 5.2e-04 |
| T2 Mutton HDS(B1) 2035 | 2.35 | 2.35 | 1.4e-03 |
| T2 Mutton HDS(B1) 2050 | 1.32 | 1.32 | 3.6e-04 |
| T2 Mutton MTS(C1) 2035 | 3.16 | 3.16 | 9.1e-04 |
| T2 Mutton MTS(C1) 2050 | 2.64 | 2.64 | 1.8e-03 |
| T2 Poultry 2024 | 17.00 | 17.00 | 8.9e-05 |
| T2 Poultry BS 2035 | 19.64 | 19.64 | 1.0e-04 |
| T2 Poultry BS 2050 | 23.33 | 23.33 | 1.3e-05 |
| T2 Poultry PTS(A1) 2035 | 20.30 | 20.30 | 2.5e-07 |
| T2 Poultry PTS(A1) 2050 | 25.22 | 25.22 | 2.7e-05 |
| T2 Poultry HDS(B1) 2035 | 22.64 | 22.64 | 3.1e-05 |
| T2 Poultry HDS(B1) 2050 | 32.64 | 32.64 | 1.0e-05 |
| T2 Poultry MTS(C1) 2035 | 21.44 | 21.44 | 6.2e-05 |
| T2 Poultry MTS(C1) 2050 | 28.70 | 28.70 | 2.1e-06 |
| T2 Eggs 2024 | 16.95 | 16.95 | 1.7e-04 |
| T2 Eggs BS 2035 | 17.55 | 17.55 | 1.4e-05 |
| T2 Eggs BS 2050 | 18.75 | 18.75 | 1.8e-04 |
| T2 Eggs PTS(A1) 2035 | 18.14 | 18.14 | 1.0e-04 |
| T2 Eggs PTS(A1) 2050 | 20.27 | 20.27 | 1.1e-04 |
| T2 Eggs HDS(B1) 2035 | 14.86 | 14.86 | 1.4e-04 |
| T2 Eggs HDS(B1) 2050 | 12.66 | 12.66 | 3.0e-05 |
| T2 Eggs MTS(C1) 2035 | 16.43 | 16.43 | 2.4e-04 |
| T2 Eggs MTS(C1) 2050 | 16.04 | 16.04 | 1.8e-04 |
| T2 Dairy products 2024 | 35.49 | 35.49 | 1.3e-04 |
| T2 Dairy products BS 2035 | 40.52 | 40.52 | 3.2e-05 |
| T2 Dairy products BS 2050 | 47.32 | 47.32 | 2.4e-05 |
| T2 Dairy products PTS(A1) 2035 | 43.99 | 43.99 | 5.7e-05 |
| T2 Dairy products PTS(A1) 2050 | 57.47 | 57.47 | 3.4e-05 |
| T2 Dairy products HDS(B1) 2035 | 56.09 | 56.09 | 1.7e-05 |
| T2 Dairy products HDS(B1) 2050 | 102.05 | 102.05 | 2.3e-05 |
| T2 Dairy products MTS(C1) 2035 | 49.71 | 49.71 | 3.8e-05 |
| T2 Dairy products MTS(C1) 2050 | 76.70 | 76.70 | 4.1e-05 |
| T2 Aquatic products 2024 | 22.75 | 22.75 | 9.1e-05 |
| T2 Aquatic products BS 2035 | 25.29 | 25.29 | 1.0e-04 |
| T2 Aquatic products BS 2050 | 28.74 | 28.74 | 1.3e-04 |
| T2 Aquatic products PTS(A1) 2035 | 26.14 | 26.14 | 4.4e-06 |
| T2 Aquatic products PTS(A1) 2050 | 31.06 | 31.06 | 1.2e-04 |
| T2 Aquatic products HDS(B1) 2035 | 34.64 | 34.64 | 3.5e-05 |
| T2 Aquatic products HDS(B1) 2050 | 60.43 | 60.43 | 5.1e-05 |
| T2 Aquatic products MTS(C1) 2035 | 30.12 | 30.12 | 7.1e-05 |
| T2 Aquatic products MTS(C1) 2050 | 43.42 | 43.42 | 5.2e-05 |
| T6 BS co2_crop | 305.90 | 305.90 | 1.4e-05 |
| T6 BS co2_livestock | 348.12 | 348.12 | 1.3e-05 |
| T6 BS co2_total | 654.02 | 654.02 | 3.8e-07 |
| T6 PTS (A1) co2_crop | 249.15 | 249.15 | 1.6e-05 |
| T6 PTS (A1) co2_livestock | 383.44 | 383.44 | 2.2e-06 |
| T6 PTS (A1) co2_total | 632.59 | 632.59 | 7.7e-06 |
| T6 HDS (B1) co2_crop | 225.96 | 225.96 | 1.1e-05 |
| T6 HDS (B1) co2_livestock | 225.29 | 225.29 | 7.9e-06 |
| T6 HDS (B1) co2_total | 451.25 | 451.25 | 9.3e-06 |
| T6 MTS (C1) co2_crop | 236.64 | 236.64 | 1.1e-05 |
| T6 MTS (C1) co2_livestock | 265.59 | 265.59 | 1.8e-05 |
| T6 MTS (C1) co2_total | 502.22 | 502.22 | 5.3e-06 |

Worst manuscript-table deviation: 1.84e-03 (manuscript values are rounded to 2 decimals).
