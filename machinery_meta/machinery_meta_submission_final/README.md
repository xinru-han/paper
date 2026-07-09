# Machinery Meta Submission Archive: final

This folder contains the reproducible code, checked meta-analysis inputs, CASM scenario inputs, and generated results for the machinery-meta paper after excluding `E_22` and `E_24`.

## Scope

- Final meta sample: 54 records from the manually checked 56-record dataset, excluding `E_22` and `E_24`.
- CASM scenario mapping: `S1=MCI`, `S2=AMS`, `S3=AML`.
- CASM shock target: `CGRN(RICE,WHEA,MAIZ,SOYS,BARL,OTGR,SORG)`.
- CASM shock years: 2026-2030.
- CASM implementation: external CASM-Python at `/root/data/CASM/casm_python`; the CASM source code is intentionally not included in this archive.

## Reproduction

Run from any working directory on the same machine:

```bash
python3 code/01_reproduce_meta_final.py
python3 code/02_build_casm_scenarios_final.py
CASM_PYTHON_DIR=/root/data/CASM/casm_python python3 code/03_run_casm_python_final.py
```

The CASM runner copies the necessary input workbooks from `/root/data/Paper/农机Meta/CASM20260410MACHINE2` into `results/casm/casm_inputs_used/` for run documentation, then imports the external CASM-Python package.

## Key Files

- `code/01_reproduce_meta_final.py`: reproduces meta-analysis and first-draft comparisons.
- `code/02_build_casm_scenarios_final.py`: builds the 3-path x 3-speed CASM shifter plan from verified meta evidence.
- `code/03_run_casm_python_final.py`: runs BASE plus nine machinery scenarios using CASM-Python.
- `data/literature_list_meta_final.csv`: final included literature/effect list for the meta-analysis.
- `data/literature_list_meta_with_exclusion_flag.csv`: full manually checked list with `E_22` and `E_24` flagged.
- `results/meta/final_all_estimates_vs_v1.xlsx`: meta-analysis results compared with the first draft.
- `results/casm/casm_scenario_plan_final.xlsx`: CASM shifter design and path elasticities.
- `results/casm/casm_scenario_shifter_vs_v1_final.xlsx`: shifter comparison against the first draft.
- `results/casm/casm_simulation_outputs_final.xlsx`: CASM simulation outputs, including 2030 grain and food-security summaries.
- `results/casm/casm_results_long_final.csv`: long-form CASM outputs by scenario, year, crop, and core variable.
- `results/casm/casm_summary_final.md`: compact human-readable CASM summary.

## Main CASM Results

All 10 CASM-Python runs converged: `BASE`, `S1-Low`, `S1-Medium`, `S1-High`, `S2-Low`, `S2-Medium`, `S2-High`, `S3-Low`, `S3-Medium`, and `S3-High`.

In 2030, grain production changes relative to BASE are:

- `S1-Low/Medium/High`: `+1.2267% / +2.1532% / +3.1238%`
- `S2-Low/Medium/High`: `+1.7445% / +2.7804% / +3.8668%`
- `S3-Low/Medium/High`: `+0.1275% / +1.1008% / +2.3935%`
