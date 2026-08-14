# Machinery Meta-analysis: Unified MCI/AMS/AML Package

This archive contains the manually verified analysis data, reproducible code,
meta-analysis outputs, CASM shock construction and CASM simulation outputs.
The meta-analysis and simulation use one common strict path definition:

- `MCI`: machinery capital input;
- `AMS`: agricultural machinery services;
- `AML`: comprehensive mechanisation level.

The broad `Capital/AMS/Rate` classification is not used. Records whose core
explanatory variable is not mechanisation (`OTH`) are excluded from analysis.

## Analysis sample

The source contains 56 manually checked records. The documented final-sample
decisions are applied first, followed by the strict path restriction. The final
analysis contains 40 records:

| Target | MCI | AMS | AML | Total |
|---|---:|---:|---:|---:|
| Yield | 9 | 7 | 1 | 17 |
| Area | 0 | 3 | 2 | 5 |
| Efficiency | 2 | 15 | 1 | 18 |
| Total | 11 | 25 | 4 | 40 |

`data/analysis_dataset_all_classified.csv` retains the full classification and
exclusion audit trail. `data/analysis_dataset_strict.csv` is the only dataset
used by both the meta-analysis and CASM scenario builder.

## Statistical methods

To isolate the classification correction, the statistical framework remains
the first-draft framework:

- manually verified PCC, SE(PCC), elasticity and sample size;
- DerSimonian-Laird random-effects pooling with normal 95% confidence intervals;
- the original 1.5-IQR and `|elasticity| <= 0.99` filtered result;
- inverse-variance WLS meta-regression with study-clustered robust SE;
- FAT/PET/PEESE weighted regressions with HC3 robust SE.

All estimates, standard errors, p-values, confidence intervals, heterogeneity
statistics and model notes are in `results/meta/meta_analysis_results.xlsx`.
Area has no MCI observation in the strict sample, so its estimable WLS reference
group is AMS; this is recorded explicitly in the workbook.

## CASM simulation

The scenario structure is `S1=MCI`, `S2=AMS`, `S3=AML`, each with Low, Medium
and High speeds. Shocks are additions to `AYGR0` and `AAGR0` for CGRN crops in
2026-2030. Path-specific elasticity medians are calculated from the same strict
analysis dataset after excluding `|elasticity| >= 0.99`.

CASM-Python source code is not included. The runner calls the external source at
`/root/data/CASM/casm_python` by default. Set `CASM_PYTHON_DIR` and
`CASM_TEMPLATE_DIR` to use other locations.

## Reproduction

Required Python packages include `pandas`, `numpy`, `scipy`, `statsmodels`,
`matplotlib`, `openpyxl` and `tabulate`.

Run the complete workflow from this directory:

```bash
python3 code/00_run_all.py
```

The CASM input workbooks actually used are copied to
`results/casm/casm_inputs_used/`. No CASM source file is copied into this
archive.
