# Repository copy and executable archive

This directory copies the study layer used in the 29 August 2026 run. Its
scripts expect to live at `study/china_diet/` inside a complete CASM-World
rebuild root, as recorded in `config.yaml`.

The one packaging difference is
`inputs/prior_casm_results_long.csv`: in this repository it is a relative
symbolic link to the byte-identical tracked file `results/results_long.csv`
(SHA-256 `60e3a1eefbda383f5292c2b4954f640f436b0cbe591dde3c3b002a715134cf2b`).
The executable archive contains an independent regular-file copy.

The directly executable, isolated model copy is stored at:

`/root/data/Paper/食物预测2050/casm_world_rebuild_diet_study_20260829/model_run/`

That archive contains the unchanged CASM-World core, processed benchmark
inputs, environment lock files, this study layer and every generated output.
The original source at `/root/data/CASM/casm_world_rebuild_2050/` was not
modified.

Within the paper repository, generated outputs are deliberately separated
from code:

- `../../results/casm_world_rebuild/`: model and analysis results;
- `../../figures/casm_world_rebuild/`: PNG/PDF figures;
- `../../manuscript/`: manuscript, Supplementary Information and revision log.
