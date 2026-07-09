# CASM final simulation summary

All CASM-Python runs converged for BASE plus nine machinery scenarios. Shocks are applied to CGRN crops in 2026-2030 as additions to AYGR0/AAGR0 growth rates.

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

## Shifter comparison against first draft
| scenario   | Target   |   old_v1_shifter_pct |   new_shifter_pct |   diff_pct_point | Path   | speed   |
|:-----------|:---------|---------------------:|-----------------------------:|-----------------:|:-------|:--------|
| S1-Low     | Yield    |                0.25  |                     0.246198 |        -0.003802 | MCI    | Low     |
| S1-Low     | Area     |                0     |                     0        |         0        | MCI    | Low     |
| S1-Medium  | Yield    |                0.434 |                     0.430578 |        -0.003422 | MCI    | Medium  |
| S1-Medium  | Area     |                0     |                     0        |         0        | MCI    | Medium  |
| S1-High    | Yield    |                0.626 |                     0.622302 |        -0.003698 | MCI    | High    |
| S1-High    | Area     |                0     |                     0        |         0        | MCI    | High    |
| S2-Low     | Yield    |                0.278 |                     0.305087 |         0.027087 | AMS    | Low     |
| S2-Low     | Area     |                0.046 |                     0.04385  |        -0.00215  | AMS    | Low     |
| S2-Medium  | Yield    |                0.438 |                     0.484165 |         0.046165 | AMS    | Medium  |
| S2-Medium  | Area     |                0.072 |                     0.069589 |        -0.002411 | AMS    | Medium  |
| S2-High    | Yield    |                0.606 |                     0.670347 |         0.064347 | AMS    | High    |
| S2-High    | Area     |                0.098 |                     0.09635  |        -0.00165  | AMS    | High    |
| S3-Low     | Yield    |                0.024 |                     0.023729 |        -0.000271 | AML    | Low     |
| S3-Low     | Area     |                0.002 |                     0.001956 |        -4.4e-05  | AML    | Low     |
| S3-Medium  | Yield    |                0.208 |                     0.204068 |        -0.003932 | AML    | Medium  |
| S3-Medium  | Area     |                0.016 |                     0.016819 |         0.000819 | AML    | Medium  |
| S3-High    | Yield    |                0.448 |                     0.441356 |        -0.006644 | AML    | High    |
| S3-High    | Area     |                0.036 |                     0.036375 |         0.000375 | AML    | High    |