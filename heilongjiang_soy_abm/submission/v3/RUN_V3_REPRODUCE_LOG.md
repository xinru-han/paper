# v3 Reproduction Log

Run date: 2026-07-11

Working directory:

`/root/data/Paper/黑龙江大豆文章/submission/v3`

Command executed:

```bash
python3 code/01_build_panel.py
python3 code/02_build_deltapi.py
python3 code/05_identification.py
python3 code/03_estimate.py
python3 code/04_simulate_static.py
python3 code/04_simulate.py
python3 code/06_checks.py
```

Status: completed without Python exceptions.

Generated/verified outputs:

- `output/panel_hh.csv`: 884 rows, 48 columns
- `output/panel_analysis.csv`: 884 rows, 79 columns
- `output/tables/reg_logit_main.csv`: 15 rows, 5 columns
- `output/scenarios_static/static_scenarios_main.csv`: 6 rows, 13 columns
- `output/scenarios_static/static_validation_2024.csv`: 1 row, 10 columns
- `output/scenarios/terminal_2030.csv`: 6 rows, 9 columns
- Total files under `output/`: 77

Notes:

- `code/04_simulate_static.py` is the v3 static ABM reproduction script for the revised submission results.
- `code/04_simulate.py` was also run because the request was to run all code. It regenerates legacy dynamic 2030 outputs under `output/scenarios/`; these should not be used as the revised static ABM main results unless explicitly needed for archival comparison.
- Matplotlib emitted font glyph warnings for Chinese labels on figures. These warnings did not stop execution or affect CSV outputs.
