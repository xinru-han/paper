# Recommended run order (reproducible outputs)

This project produces (i) **baseline point estimates**, (ii) **robustness/no-imputation** outputs, (iii) **bootstrap uncertainty intervals**, and (iv) **publication-quality figures** (panel plots and choropleth maps).

## 0) One-time prerequisites (check before running)

- Run all commands from the **project root** (the directory that contains `predict_tabpfn.py`, `run_bootstrap.py`, `data/`, etc.).
- Confirm required input data exist under `data/` (e.g., `data.csv`, `data2012.csv`, `data_production*.csv`, `procince_pop.csv`).
- If you use TabPFN (baseline), confirm the checkpoint file exists at:
  - `tabpfn-v2.5-regressor-v2.5_default.ckpt`

## 1) Baseline (TabPFN) point estimates (main specification)

```bash
python predict_tabpfn.py
```

**Expected outputs**
- `predictions_tabpfn.csv` (baseline point estimates)
- `predictions_tabpfn_robust.csv` (no-imputation robustness; produced by the same script)

## 2) Bootstrap 95% uncertainty intervals (baseline)

```bash
python run_bootstrap.py tabpfn 30
```

Notes:
- Replace `30` with your desired number of bootstrap runs (larger = more stable but slower).
- The updated `run_bootstrap.py` performs light winsorization in the bootstrap aggregation step to prevent rare numerical explosions from dominating the intervals.

**Expected output**
- `predictions_tabpfn_bootstrap.csv` (columns like `q_*_Mean`, `q_*_Lower`, `q_*_Upper`)

## 3) Choropleth maps (spatial heterogeneity figure)

You must provide a China-province boundary file (GeoJSON or Shapefile) whose province code field matches GB/T 2260 (e.g., 11, 12, ..., 65).

```bash
python plot_choropleth_maps.py \
  --geo <path/to/china_provinces.geojson_or_shp> \
  --pred predictions_tabpfn.csv \
  --year 2024
```

**Expected output**
- `figures/map_rice_pork_2024.pdf`

The LaTeX draft (`paper_draft/paper_final_full.tex`) will automatically include this PDF if it exists; otherwise it shows a placeholder box.

## Optional) Alternative models as robustness checks (recommended for figures/tables)

### A) LightGBM

```bash
python predict_lightgbm.py
python run_bootstrap.py lightgbm 30
```

**Outputs**
- `predictions_lightgbm.csv`
- `predictions_lightgbm_robust.csv`
- `predictions_lightgbm_bootstrap.csv`

### B) FT-Transformer

```bash
python predict_fttransformer.py
python run_bootstrap.py fttransformer 30
```

**Outputs**
- `predictions_fttransformer.csv`
- `predictions_fttransformer_robust.csv`
- `predictions_fttransformer_bootstrap.csv`

## Separate track) ε-sensitivity (`sensitivity_eps.py`) — **not** part of TabPFN prediction

`sensitivity_eps.py` does **not** use `predict_tabpfn.py`. It reads a **detail CSV** of out-of-sample predictions from the **unified bounded benchmark** (`unified_bounded_fast_detail.csv`, one row per model/category/fold/observation).

If you run `python sensitivity_eps.py` **without** that file, it will raise `FileNotFoundError`.

**Fix (pick one)**

1. **Generate the benchmark output first** (when you have `unified_bounded_model_benchmark_fast.py`): run it so it writes  
   `final/unified_bounded_fast_detail.csv` (see the docstring at the top of `sensitivity_eps.py`).

2. **Copy** an existing `unified_bounded_fast_detail.csv` into `fafh/final/` or the repo root under that exact name.

3. **Point to any compatible CSV**:

```bash
python sensitivity_eps.py --input /path/to/your_detail.csv
```

**Outputs** (under `final/`): `tableA6_eps_sensitivity.csv`, `tableA6_eps_by_category.csv`, `tidy_eps_sensitivity.csv`, and optionally `figures/figA6_eps_sensitivity.pdf`.

