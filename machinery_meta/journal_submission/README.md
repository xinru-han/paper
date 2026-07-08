# Journal submission — data, code and results

Minimal package for journal upload. Contains only the final study list, the CSV
inputs used by the models, the analysis code, and the result tables/figures.
(The CASM model source code and the raw literature-extraction sheets are not
included here.)

```
data/
  study_list.csv        List of the 56 included studies (systematic-review name list):
                        id, author-year, language, journal tier, region, data years,
                        crop, model, outcome dimension, mechanisation path.
  meta_dataset.csv      Meta-analysis model input: one effect size per study —
                        PCC, SE(PCC), elasticity, sample size N, log(N), Target, Path.
  scenario_design.csv   CASM model input: the 9 policy scenarios with the annual
                        yield/area technology shifters (Eq. 25).

code/
  meta_analysis.py      Reproduces Tables 1-5 and the forest/funnel figures from
                        data/meta_dataset.csv.
  scenario_design.py    Rebuilds data/scenario_design.csv from data/meta_dataset.csv
                        (path-dimension elasticity medians x proxy growth rates).

results/
  Table1_overall.csv           Overall pooled effects (random effects)
  Table2_subgroup.csv          Subgroup pooled effects by mechanisation path
  Table3_meta_regression.csv   WLS meta-regression (clustered robust SE)
  Table4_fat_pet_peese.csv     Publication-bias diagnostics
  Table5_robustness.csv        Robustness (IQR / simple mean / N-weighted)
  Table8_grain.csv             CASM: grain totals, 2030 (output / net-trade / SSR)
  Table9_cereal_staple.csv     CASM: cereal and staple-grain security, 2030
  forest_*.png, funnel_*.png   Forest and funnel plots
```

## Reproduce (meta-analysis)

```bash
cd code
python meta_analysis.py      # -> ../results/  (Tables 1-5 + figures)
python scenario_design.py    # -> ../data/scenario_design.csv (CASM shifters)
```

Dependencies: Python 3, numpy, pandas, scipy, statsmodels, matplotlib.

The CASM simulation outputs (Tables 8-9) are provided in `results/`; the CASM
partial-equilibrium model code and its input workbooks are available on request.

## Method

Effect size = partial correlation coefficient (PCC). Pooling by DerSimonian-Laird
random effects (a Knapp-Hartung t-interval is reported alongside as a robustness
column). WLS meta-regression with study-clustered robust SE and inverse-variance
weights. Publication bias via FAT-PET-PEESE. Path-dimension elasticity medians map
the meta evidence to CASM yield/area technology shifters; the CASM model then
solves a baseline plus nine mechanisation scenarios for 2026-2030.
