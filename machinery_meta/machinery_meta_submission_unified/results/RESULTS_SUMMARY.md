# Unified MCI/AMS/AML results

## Strict analysis sample

| Target     |   AML |   AMS |   MCI |   All |
|:-----------|------:|------:|------:|------:|
| Area       |     2 |     3 |     0 |     5 |
| Efficiency |     1 |    15 |     2 |    18 |
| Yield      |     1 |     7 |     9 |    17 |
| All        |     4 |    25 |    11 |    40 |

## Overall DL random-effects results

| Target     |   k |       PCC |        SE |           p | significance   |    CI_low |   CI_high |      I2 |
|:-----------|----:|----------:|----------:|------------:|:---------------|----------:|----------:|--------:|
| Yield      |  17 | 0.149594  | 0.0365281 | 4.21598e-05 | ***            | 0.0779989 |  0.221189 | 95.7542 |
| Area       |   5 | 0.0999424 | 0.0373995 | 0.00753345  | ***            | 0.0266394 |  0.173245 | 97.5982 |
| Efficiency |  18 | 0.175839  | 0.0240781 | 2.81744e-13 | ***            | 0.128645  |  0.223032 | 92.3367 |

## Path subgroup results

| Target     | Path   |   k |         PCC |             p | significance   | interpretation_note                                                                             |
|:-----------|:-------|----:|------------:|--------------:|:---------------|:------------------------------------------------------------------------------------------------|
| Yield      | MCI    |   9 |   0.14086   |   0.0354775   | **             | nan                                                                                             |
| Yield      | AMS    |   7 |   0.130632  |   5.0935e-06  | ***            | nan                                                                                             |
| Yield      | AML    |   1 |   0.362     |   1.79961e-26 | ***            | Single-record subgroup; p-value is based on the record-level SE and is not pooled path evidence |
| Area       | MCI    |   0 | nan         | nan           | nan            | nan                                                                                             |
| Area       | AMS    |   3 |   0.0773912 |   0.0843314   | *              | nan                                                                                             |
| Area       | AML    |   2 |   0.137538  |   2.2322e-05  | ***            | nan                                                                                             |
| Efficiency | MCI    |   2 |   0.263622  |   2.02938e-08 | ***            | nan                                                                                             |
| Efficiency | AMS    |  15 |   0.168735  |   6.08398e-11 | ***            | nan                                                                                             |
| Efficiency | AML    |   1 |   0.123     |   0.0203001   | **             | Single-record subgroup; p-value is based on the record-level SE and is not pooled path evidence |

Yield-AML and Efficiency-AML each contain one record. Area contains no MCI record; its WLS path comparison therefore uses AMS as the estimable baseline and should be interpreted as exploratory.

## CASM shocks

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

## CASM 2030 grain results

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

All ten CASM runs completed without an exception: True.
