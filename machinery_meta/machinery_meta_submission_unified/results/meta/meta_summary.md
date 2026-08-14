# Unified strict-path meta-analysis

The analysis uses only manually verified MCI/AMS/AML records. Capital/Rate labels and OTH records are not analysed.

## Sample counts

| Target     |   AML |   AMS |   MCI |   All |
|:-----------|------:|------:|------:|------:|
| Area       |     2 |     3 |     0 |     5 |
| Efficiency |     1 |    15 |     2 |    18 |
| Yield      |     1 |     7 |     9 |    17 |
| All        |     4 |    25 |    11 |    40 |

## DerSimonian-Laird overall effects

| Target     |   k |       PCC |        SE |           p | significance   |    CI_low |   CI_high |      I2 |
|:-----------|----:|----------:|----------:|------------:|:---------------|----------:|----------:|--------:|
| Yield      |  17 | 0.149594  | 0.0365281 | 4.21598e-05 | ***            | 0.0779989 |  0.221189 | 95.7542 |
| Area       |   5 | 0.0999424 | 0.0373995 | 0.00753345  | ***            | 0.0266394 |  0.173245 | 97.5982 |
| Efficiency |  18 | 0.175839  | 0.0240781 | 2.81744e-13 | ***            | 0.128645  |  0.223032 | 92.3367 |

Full numerical results, including subgroup p-values, WLS and FAT/PET/PEESE, are in `meta_analysis_results.xlsx`.

WLS coefficient rows: 14; FAT/PET/PEESE rows: 16.
