# Stata basic AIDS baseline (fresh start)

This directory is a new baseline and does not consume any previous cleaned
panel, model estimate, selection correction, control-function residual, or
elasticity output.

## Scope

- Raw source: `../data/2017-feed.csv` through `../data/2023-feed.csv`.
- Goods: corn, sorghum, cassava, oats, and barley, using the exact eight-digit
  HS mappings encoded in `code/01_describe_and_build.do`.
- Unit: province-quarter.
- Price: aggregate customs value divided by quantity for positive cells.
  A zero-import cell receives the same-product, same-quarter median log price;
  the product-wide median is only a fallback.
- Estimator: exact nonlinear AIDS with adding-up, homogeneity, and symmetry
  imposed; no SY correction, instruments, control function, controls,
  fixed effects, quality adjustment, or winsorization.
- Inference: province-clustered covariance and delta-method elasticities.

Run:

```bash
bash code/run_all.sh
```

Potential anomalies are reported, not automatically deleted or winsorized.

The same sample is also used for QUAIDS, two-step SY-AIDS, and two-step
SY-QUAIDS. Their complete latent reference elasticities and specification
diagnostics are reported in `EXTENDED_MODELS_RESULTS.md`.
