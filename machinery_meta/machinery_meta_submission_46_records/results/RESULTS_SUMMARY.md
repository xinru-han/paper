# Revised 46-record MCI/AMS/AML results

## Strict analysis sample

| Target     |   AML |   AMS |   MCI |   All |
|:-----------|------:|------:|------:|------:|
| Area       |     2 |     3 |     0 |     5 |
| Efficiency |     1 |    16 |     2 |    19 |
| Yield      |     3 |     7 |    12 |    22 |
| All        |     6 |    26 |    14 |    46 |

## Overall DL random-effects results

| Target     |   k |       PCC |        SE |           p | significance   |    CI_low |   CI_high |      I2 |
|:-----------|----:|----------:|----------:|------------:|:---------------|----------:|----------:|--------:|
| Yield      |  22 | 0.153642  | 0.0311612 | 8.19903e-07 | ***            | 0.0925665 |  0.214718 | 95.4247 |
| Area       |   5 | 0.0999424 | 0.0373995 | 0.00753345  | ***            | 0.0266394 |  0.173245 | 97.5982 |
| Efficiency |  19 | 0.168763  | 0.0191247 | 1.10064e-18 | ***            | 0.131279  |  0.206248 | 92.635  |

## Path subgroup results

| Target     | Path   |   k |       PCC |           p | significance   | interpretation_note                                                                             |
|:-----------|:-------|----:|----------:|------------:|:---------------|:------------------------------------------------------------------------------------------------|
| Yield      | MCI    |  12 | 0.124939  | 0.0063914   | ***            |                                                                                                 |
| Yield      | AMS    |   7 | 0.130632  | 5.0935e-06  | ***            |                                                                                                 |
| Yield      | AML    |   3 | 0.317687  | 0.000357803 | ***            |                                                                                                 |
| Area       | MCI    |   0 |           |             |                |                                                                                                 |
| Area       | AMS    |   3 | 0.0773912 | 0.0843314   | *              |                                                                                                 |
| Area       | AML    |   2 | 0.137538  | 2.2322e-05  | ***            |                                                                                                 |
| Efficiency | MCI    |   2 | 0.263622  | 2.02938e-08 | ***            |                                                                                                 |
| Efficiency | AMS    |  16 | 0.161367  | 1.09182e-15 | ***            |                                                                                                 |
| Efficiency | AML    |   1 | 0.123     | 0.0203001   | **             | Single-record subgroup; p-value is based on the record-level SE and is not pooled path evidence |

Efficiency-AML contains one record. Area contains no MCI record; its WLS path comparison therefore uses AMS as the estimable baseline and should be interpreted as exploratory.

## CASM shocks

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

## CASM 2030 grain results

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

All ten CASM runs completed without an exception: True.
