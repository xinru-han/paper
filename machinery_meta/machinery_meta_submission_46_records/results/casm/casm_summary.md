# Revised 46-record strict-path CASM results

BASE and all nine scenarios completed without a solver exception. The shocks use the same strict MCI/AMS/AML dataset as the meta-analysis.

## Path elasticities

| Path   | Target   |   k_elasticity |   elasticity_used | record_ids                                        |
|:-------|:---------|---------------:|------------------:|:--------------------------------------------------|
| MCI    | Yield    |             10 |            0.163  | P_01;P_09;P_22;P_29;E_08;E_11;E_16;E_19;E_25;E_26 |
| MCI    | Area     |              0 |            0      | nan                                               |
| AMS    | Yield    |              6 |            0.1635 | P_11;P_15;E_02;E_04;E_05;E_17                     |
| AMS    | Area     |              3 |            0.0235 | P_08;P_12;P_31                                    |
| AML    | Yield    |              3 |            0.194  | P_02;P_03;E_24                                    |
| AML    | Area     |              1 |            0.015  | P_19                                              |

## Scenario shocks

| scenario   | Path   |   yield_shifter_pct_per_year |   area_shifter_pct_per_year |
|:-----------|:-------|-----------------------------:|----------------------------:|
| S1-Low     | MCI    |                     0.23468  |                    0        |
| S1-Medium  | MCI    |                     0.410434 |                    0        |
| S1-High    | MCI    |                     0.593189 |                    0        |
| S2-Low     | AMS    |                     0.305087 |                    0.04385  |
| S2-Medium  | AMS    |                     0.484165 |                    0.069589 |
| S2-High    | AMS    |                     0.670347 |                    0.09635  |
| S3-Low     | AML    |                     0.025293 |                    0.001956 |
| S3-Medium  | AML    |                     0.217523 |                    0.016819 |
| S3-High    | AML    |                     0.470456 |                    0.036375 |

## 2030 grain results

| scenario   |   production_10kt |   production_change_pct |   net_import_10kt |   self_sufficiency_pct |   area_million_mu |   yield_change_pct |
|:-----------|------------------:|------------------------:|------------------:|-----------------------:|------------------:|-------------------:|
| BASE       |           72530.4 |                0        |           14304.6 |                83.5267 |           17.9977 |           0        |
| S1-Low     |           73378.3 |                1.16902  |           13536.4 |                84.4256 |           17.9977 |           1.16902  |
| S1-Medium  |           74018.5 |                2.05165  |           12956.5 |                85.1032 |           17.9977 |           2.05165  |
| S1-High    |           74688.9 |                2.97596  |           12349.1 |                85.8118 |           17.9977 |           2.97596  |
| S2-Low     |           73795.7 |                1.74449  |           13160.8 |                84.8651 |           18.0372 |           1.5221   |
| S2-Medium  |           74547   |                2.78037  |           12481.6 |                85.6581 |           18.0603 |           2.42412  |
| S2-High    |           75335   |                3.86678  |           11769.2 |                86.4884 |           18.0845 |           3.36872  |
| S3-Low     |           72628.5 |                0.135256 |           14215.8 |                83.6307 |           17.9995 |           0.125481 |
| S3-Medium  |           73377.7 |                1.16816  |           13538   |                84.424  |           18.0129 |           1.08327  |
| S3-High    |           74373.2 |                2.54064  |           12637.2 |                85.4762 |           18.0304 |           2.35468  |

Completed CASM runs: 10 (BASE plus nine scenarios).
