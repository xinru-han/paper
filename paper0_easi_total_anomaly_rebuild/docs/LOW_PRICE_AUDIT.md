# Low-price tail audit

No category-specific minimum, percentile floor, curvature constraint, or elasticity-sign rule is used.

A raw representative price exits the direct donor pool only when it is supported by one outlet, is more than three scaled MADs below its province-year median, and is corroborated by neither same-town prices nor the calibrated broad-category quote within a 25 percent log band.

## Final lower tail

| Food | Min | p1 | p5 | Villages at min | Bottom-5% unique values | Weak lows removed | Lower MAD values locally retained |
|---|---:|---:|---:|---:|---:|---:|---:|
| Staples | 1.9000 | 1.9800 | 2.1150 | 1 | 9 | 2 | 0 |
| Beans | 2.0000 | 2.0000 | 2.4800 | 5 | 6 | 1 | 0 |
| Meat | 8.0000 | 8.9900 | 9.0000 | 3 | 3 | 1 | 0 |
| Edible oil | 4.0000 | 4.5900 | 5.7000 | 1 | 9 | 0 | 0 |
| Vegetables | 0.6800 | 0.9800 | 1.2000 | 2 | 9 | 3 | 0 |
| Fruit | 1.6000 | 1.6000 | 3.0000 | 4 | 5 | 1 | 6 |

## Removed weak lower-tail quotes

| Food | Village | Year | Raw price | Outlet support | Robust z | Calibrated broad price |
|---|---|---:|---:|---:|---:|---:|
| Staples | 350426109201 | 2024 | 1.5000 | 1 | -3.63 | 3.5932 |
| Staples | 532529103204 | 2024 | 1.6000 | 1 | -4.59 | 2.5388 |
| Beans | 371324103243 | 2023 | 1.4800 | 1 | -3.30 | 3.0993 |
| Meat | 530624101203 | 2024 | 3.0000 | 1 | -7.59 | 19.0069 |
| Vegetables | 422828200204 | 2024 | 1.2000 | 1 | -13.72 | 2.7518 |
| Vegetables | 532529102201 | 2024 | 1.5000 | 1 | -5.28 | 2.6753 |
| Vegetables | 530628201202 | 2024 | 1.0000 | 1 | -12.72 | NA |
| Fruit | 420683107005 | 2024 | 4.0000 | 1 | -36.81 | NA |

## Interpretation

- Staples 1.50 and 1.60 yuan/jin and beans 1.48 yuan/jin were single-outlet observations contradicted by both local and broad price evidence; they were replaced through the pre-specified geographic hierarchy.
- Vegetables 0.68 yuan/jin remains because two direct villages in the same town report it and a third nearby direct quote is close.
- Fruit 1.60 yuan/jin remains because two direct villages report it, the calibrated broad quote is about 1.59, and household unit values in those villages are compatible. Two additional villages inherit it through town/nearest-village imputation.
- Meat 9.00 yuan/jin is heaped because direct questionnaire prices are rounded and geographic imputation repeats donor medians. The concentration is visible in the audit but is not an isolated raw minimum or a basis for imposing a price floor.

The detailed village rows and source codes are in `outputs/village_community_prices.csv`; bottom-decile source shares are in `outputs/price_low_tail_sources.csv`.
