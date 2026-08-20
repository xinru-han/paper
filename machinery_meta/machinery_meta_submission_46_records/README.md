# Machinery Meta-analysis: Revised 46-record MCI/AMS/AML Package

This archive contains the manually verified analysis data, reproducible code,
meta-analysis outputs, CASM shock construction and CASM simulation outputs.
The meta-analysis and simulation use one common strict path definition:

- `MCI`: machinery capital input;
- `AMS`: agricultural machinery services;
- `AML`: comprehensive mechanisation level.

Only the strict `MCI/AMS/AML` classification is used. Records whose core
explanatory variable is not mechanisation (`OTH`) are excluded from analysis.

## Analysis sample

The source contains 56 records. A coding review found six records whose direct
mechanisation coefficients in the first-draft coding reference had been
replaced by coefficients for other explanatory variables in the later table.
Their full coded rows are restored transparently through
`data/record_reinstatement_map.csv` and
`data/first_draft_parameter_reference.csv`. The final strict analysis contains
46 records:

| Target | MCI | AMS | AML | Total |
|---|---:|---:|---:|---:|
| Yield | 12 | 7 | 3 | 22 |
| Area | 0 | 3 | 2 | 5 |
| Efficiency | 2 | 16 | 1 | 19 |
| Total | 14 | 26 | 6 | 46 |

The restored records are `E_03` (AMS), `E_16` (MCI), `E_19` (MCI), `E_24`
(AML), `P_01` (MCI) and `P_03` (AML).

`data/analysis_dataset_all_classified.csv` retains the full classification,
parameter-source and exclusion audit trail. `data/analysis_dataset_strict.csv`
is the only dataset used by both the meta-analysis and CASM scenario builder.

## Statistical methods

To isolate the classification correction, the statistical framework remains
the first-draft framework:

- manually verified parameters, with the six documented coding restorations;
- DerSimonian-Laird random-effects pooling with normal 95% confidence intervals;
- the original 1.5-IQR and `|elasticity| <= 0.99` filtered result;
- inverse-variance WLS meta-regression with study-clustered robust SE;
- FAT/PET/PEESE weighted regressions with HC3 robust SE.

All estimates, standard errors, p-values, confidence intervals, heterogeneity
statistics and model notes are in `results/meta/meta_analysis_results.xlsx`.
Area has no MCI observation in the strict sample, so its estimable WLS reference
group is AMS; this is recorded explicitly in the workbook. Efficiency-AML has
one record and is marked as single-record evidence.

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
