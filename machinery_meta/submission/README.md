# Replication package

**Agricultural mechanisation and grain production capacity in China:
a meta-analysis and CASM scenario simulation**

This package reproduces every table and figure in the manuscript. It has two
self-contained parts plus the manuscript-revision script.

```
1_meta_analysis/          Meta-analysis (Sections 3-4, Tables 1-5, forest/funnel figures)
  data/
    raw/                    verified extraction sheets (effect sizes, descriptors, sample sizes)
    build_dataset.py        assembles the analysis dataset from raw sheets
    meta_dataset.csv        56 effect sizes (one per study) — the analysis input
  meta_analysis.py          Tables 1-5 + forest/funnel plots
  results/                  generated tables (.csv) and figures (.png)

2_casm_simulation/        CASM policy simulation (Section 5, Tables 6-9)
  scenario_design.py        builds the 3x3 scenario matrix (Table 6-7)
  data/scenario_design.csv  9 scenarios with yield/area technology shifters
  run_casm.py               baseline + 9 scenarios; writes Tables 8-9
  casm/                     CASM China Agricultural Sector Model (Python port)
  casm_inputs/              model input workbooks
  results/                  Table8_grain.csv, Table9_cereal_staple.csv, long results

CORRECTIONS.md            errors fixed vs the original draft and the resulting number updates
```

## Reproduce

```bash
# Part 1 — meta-analysis (Tables 1-5)
cd 1_meta_analysis/data && python build_dataset.py     # -> meta_dataset.csv
cd .. && python meta_analysis.py                        # -> results/

# Part 2 — CASM simulation (Tables 6-9); ~7 min
cd ../2_casm_simulation && python scenario_design.py    # -> data/scenario_design.csv
python run_casm.py                                      # -> results/
```

Dependencies: Python 3, numpy, pandas, scipy, statsmodels, matplotlib,
openpyxl. No GAMS required — CASM runs from the bundled Python port.

## Method summary

- Effect size = partial correlation coefficient (PCC); pooling by
  DerSimonian-Laird random effects (Table 1-2). A Knapp-Hartung t-interval is
  reported alongside as a robustness column.
- WLS meta-regression with study-clustered robust standard errors and
  inverse-variance weights (Table 3).
- Publication bias via FAT-PET-PEESE (Table 4); robustness via IQR trimming,
  simple mean and sample-size weighting (Table 5).
- Elasticity medians per path x dimension map Meta evidence to CASM yield/area
  technology shifters (Eq. 25); the CASM partial-equilibrium model then solves
  baseline + 9 mechanisation scenarios for 2026-2030 (Tables 6-9).

See `manuscript/CORRECTIONS.md` for the list of errors fixed relative to the
original draft and the resulting number updates.
