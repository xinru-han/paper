# Unified strict-path CASM results

BASE and all nine scenarios completed without a solver exception. The shocks use the same strict MCI/AMS/AML dataset as the meta-analysis.

## Path elasticities

| Path   | Target   |   k_elasticity |   elasticity_used | record_ids                         |
|:-------|:---------|---------------:|------------------:|:-----------------------------------|
| MCI    | Yield    |              7 |            0.171  | P_09;P_22;P_29;E_08;E_11;E_25;E_26 |
| MCI    | Area     |              0 |            0      | nan                                |
| AMS    | Yield    |              6 |            0.1635 | P_11;P_15;E_02;E_04;E_05;E_17      |
| AMS    | Area     |              3 |            0.0235 | P_08;P_12;P_31                     |
| AML    | Yield    |              1 |            0.182  | P_02                               |
| AML    | Area     |              1 |            0.015  | P_19                               |

## Scenario shocks

| scenario   | Path   |   yield_shifter_pct_per_year |   area_shifter_pct_per_year |
|:-----------|:-------|-----------------------------:|----------------------------:|
| S1-Low     | MCI    |                     0.246198 |                    0        |
| S1-Medium  | MCI    |                     0.430578 |                    0        |
| S1-High    | MCI    |                     0.622302 |                    0        |
| S2-Low     | AMS    |                     0.305087 |                    0.04385  |
| S2-Medium  | AMS    |                     0.484165 |                    0.069589 |
| S2-High    | AMS    |                     0.670347 |                    0.09635  |
| S3-Low     | AML    |                     0.023729 |                    0.001956 |
| S3-Medium  | AML    |                     0.204068 |                    0.016819 |
| S3-High    | AML    |                     0.441356 |                    0.036375 |

## 2030 grain results

| scenario   |   production_10kt |   production_change_pct |   net_import_10kt |   self_sufficiency_pct |   area_million_mu |   yield_change_pct |
|:-----------|------------------:|------------------------:|------------------:|-----------------------:|------------------:|-------------------:|
| BASE       |           72530.4 |                0        |           14304.6 |                83.5267 |           17.9977 |           0        |
| S1-Low     |           73420.1 |                1.22667  |           13498.6 |                84.4699 |           17.9977 |           1.22667  |
| S1-Medium  |           74092.2 |                2.1532   |           12889.7 |                85.1811 |           17.9977 |           2.1532   |
| S1-High    |           74796.1 |                3.12382  |           12251.9 |                85.9251 |           17.9977 |           3.12382  |
| S2-Low     |           73795.7 |                1.74449  |           13160.8 |                84.8651 |           18.0372 |           1.5221   |
| S2-Medium  |           74547   |                2.78037  |           12481.6 |                85.6581 |           18.0603 |           2.42412  |
| S2-High    |           75335   |                3.86678  |           11769.2 |                86.4884 |           18.0845 |           3.36872  |
| S3-Low     |           72622.9 |                0.127493 |           14220.9 |                83.6247 |           17.9995 |           0.117719 |
| S3-Medium  |           73328.9 |                1.10083  |           13582.2 |                84.3723 |           18.0129 |           1.016    |
| S3-High    |           74266.4 |                2.39346  |           12733.9 |                85.3634 |           18.0304 |           2.20777  |

Completed CASM runs: 10 (BASE plus nine scenarios).
