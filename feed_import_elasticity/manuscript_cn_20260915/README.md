# Supplementary Stata Audit, 2026-09-15

These files supplement `../stata_aids_baseline_2026/`. They do not replace the original sample, model estimates, or elasticities. The associated unpublished Chinese manuscript and its text-generating template are retained locally and are not included in this public directory.

## New Checks

- Actual zero expenditure shares are counted separately from missing local prices. Oats have 341 zero shares and 344 imputed prices; barley has 207 zero shares and 208 imputed prices, each out of 634 observations.
- At the centered reference point, the latent curvature matrix `C = Gamma + alpha*alpha' - diag(alpha)` is numerically negative semidefinite in all four specifications. This is only a pointwise diagnostic. SY-AIDS still has a negative barley share and is not economically admissible at that point.
- Predicted observed shares in the five-equation SY systems do not necessarily sum to one. Reference sums are approximately 1.087497 for SY-AIDS and 1.023633 for SY-QUAIDS.
- Existing elasticity estimates are supplied in CSV/Excel, with standard errors, p-values and confidence intervals. SY uncertainty is conditional on first-stage fitted regressors; no full-process bootstrap has been performed.

## Reproduce the Audit

From this directory:

```bash
/usr/local/stata17/stata-se -b do code/01_manuscript_audit.do "../stata_aids_baseline_2026" "."
```

The Stata program reads the existing sample and `.ster` files. It only writes supplementary diagnostics under `tables/` and `logs/`. The complete underlying model scripts remain in `../stata_aids_baseline_2026/code/`.
