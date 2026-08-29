# CASM-World China diet study run manifest

**Study ID:** `CHINA_DIET_CASM_WORLD_REBUILD_2050`  
**Run date:** 2026-08-29  
**Archive root:** `/root/data/Paper/食物预测2050/casm_world_rebuild_diet_study_20260829/`

## Where everything is

| Directory | Contents | Approximate size |
|---|---|---:|
| `model_run/` | Complete isolated CASM-World V2 copy, processed inputs, copied baseline outputs, new study code and all counterfactual outputs | 744 MB |
| `paper_worktree/` | Independent Git worktree containing the revised paper, copied code, results, figures and audits | 1.0 GB including the existing repository content |
| `inputs_from_prior_study/` | Frozen source China-CASM scenario/path inputs used to construct preference multipliers | 25 MB |

The original model at `/root/data/CASM/casm_world_rebuild_2050/` was not
modified. The run report records `core_model_files_modified: false`.

## Executable model study

Study code:

`model_run/study/china_diet/`

Complete new outputs:

`model_run/study/china_diet/outputs/`

The output directory contains:

- main country-product, world-price, processing and convergence files;
- SSP2 low/central/high response and nested-demand sensitivity files;
- country, group, GHG and model-covered nutrition post-solutions;
- eight publication tables;
- four figures in PNG and PDF;
- run, analysis and claim audits.

The copied baseline model outputs needed by the full upstream test suite are
under `model_run/outputs/`. They were copied after the first full test run
identified missing test prerequisites in the intentionally minimal copy.

## Paper deliverables

Canonical paper directory:

`paper_worktree/food_demand_2050/`

Primary files:

- `manuscript/manuscript_v3_casm_world.md`
- `manuscript/manuscript_v3_casm_world.docx`
- `manuscript/supplementary_information_v3_casm_world.md`
- `manuscript/supplementary_information_v3_casm_world.docx`
- `manuscript/cover_letter_nature_communications_draft.md`
- `manuscript/cover_letter_nature_communications_draft.docx`
- `manuscript/revision_notes_casm_world_rebuild_20260829.md`
- `results/casm_world_rebuild/`
- `figures/casm_world_rebuild/`
- `model/casm_world_rebuild_core/`
- `model/casm_world_rebuild_study/`

The prior `manuscript_v2.md` and its 13-region result chain remain in place as
an archive and are not the canonical manuscript.

## Model design

- 193 solved economy accounts and 31 products.
- Four China diet paths: BASELINE, PTS, MTS and CGS.
- China food-preference shifts for 19 world products.
- SSP2 annual 2023-2050; SSP1/3/4/5 at 2023 and 2050.
- 144 main and 16 sensitivity equilibria.
- Two-way price feedback inside CASM-World; source China-CASM targets remain a soft link.
- Net trade only, without bilateral flow allocation.
- Frozen 2023 attributed biological farm-gate GHG boundary.
- Nutrition covers only the modelled edible basket.

## Verification

- Main maximum relative market residual: `5.253e-15`.
- Sensitivity maximum relative market residual: `7.253e-15`.
- Maximum accounting residual: `1.421e-14 Mt`.
- Common 2023 benchmark error: `0`.
- Full model plus study test suite: `139 passed`.
- Manuscript-to-results audit: `32/32 passed`.
- Main manuscript, SI and cover-letter DOCX archives: integrity checks passed.

## Publication status

The counterfactual chain is computationally valid, but the underlying V2 SSP
baseline passes 18 of 20 frozen publication gates. Two 2050 price-band gates
remain failed, and a shared crop-resource/land-allocation mechanism remains
unimplemented. The accurate status is:

`computationally valid diagnostic conditional scenario, not publication baseline`

This status is stated on the manuscript's first page and in the SI and cover
letter. The current paper is framed towards *Nature Communications*, but the
cover letter is marked `HOLD` pending model promotion.

## Reproduction commands

Run from `model_run/`:

```bash
export PYTHONPATH="$PWD/src"
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python study/china_diet/prepare_diet_paths.py
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python study/china_diet/run_counterfactuals.py
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python study/china_diet/analyze_counterfactuals.py
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python study/china_diet/make_figures.py
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python -m pytest -q tests study/china_diet/tests
```

Run the manuscript audit from `paper_worktree/food_demand_2050/`:

```bash
python3 audit_manuscript_repository_consistency.py
```

## Git

Working branch: `agent/china-diet-casm-world-rebuild-20260829`  
Remote: `git@github.com:xinru-han/paper.git`

The Git commit and push status are recorded in `GIT_SYNC_STATUS.md` after the
repository operation completes.

