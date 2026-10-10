# Micro MAIDADS: 8 and 10 Food Groups

This project estimates a two-stage household food-demand system using the rural survey and community prices. The 10-good system separates pork from other livestock meat and nuts from fruit. Both classifications use the same positive-food-budget sample, preserve food-category zeros, and use household per-capita income rather than provincial GDP.

Stata estimates the food-budget GLM and participation probits. Python implements the general conditional MAIDADS equations, the common-factor correlated participation extension, exact nonempty-pattern integration, elasticities, income-growth scenarios, diagnostics, and reports. The provincial reference project also estimates MAIDADS in Python; this project does not claim that MAIDADS is a native Stata estimator.

## Reproduction

The installed environment is Stata/SE 17, Python 3.10.12, NumPy 1.26.4, pandas 2.3.3, SciPy 1.15.3, matplotlib 3.10.9, and tabulate 0.10.0. Use one numerical thread to keep memory use and runtimes predictable:

```bash
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /usr/local/stata17/stata-se -b do \
  /root/data/Paper/食物消费数据/paper0-EASI/micro_maidads_20261010/code/00_run_all.do
```

This executes data construction, the Stata first stage, its prediction checks, independent-participation diagnostics, correlated-participation fitting, 8/10-good AIDADS and MAIDADS estimation (`--starts 2 --maxiter 1500`), expanded-parameter-guard sensitivity, explicit finalization of accepted interior expanded-guard solutions, working-domain checks, a Stata quadratic-versus-loglinear food-budget diagnostic, result derivation (`--batch 24`), structural tests, and the report. It runs synchronously and stops on a failed child command, missing/stale output, failed numerical check, or a source-code change during the run. Finalization preserves the earlier primary fit as `standard_guard_maidads_fit.json`, records the accepted sensitivity-file SHA-256 identity, rejects failed or still-boundary solutions, and occurs before all elasticity/scenario calculations.

The executed 8-good numerical-guard expansion changed some sample elasticities by more than 0.01, so it was not guard-stable at the original bounds. The accepted expanded solution was adopted and predictions were recomputed. Long-run MAIDADS commitment parameters (notably tau/kappa) remain weakly identified on a flat ridge: in-sample fit and twofold-income forecasts do not establish the infinite-income endpoints. The expanded continuation is not an independent new global multistart search.

For source syntax, dependencies, input paths, and command-plan checks without rerunning the scientific stages:

```bash
/usr/local/stata17/stata-se -b do \
  /root/data/Paper/食物消费数据/paper0-EASI/micro_maidads_20261010/code/00_run_all.do \
  /root/data/Paper/食物消费数据/paper0-EASI/micro_maidads_20261010 check
```

The equivalent direct entry is `python3 code/run_pipeline.py` from the project folder, or `python3 code/run_pipeline.py --check` for the check-only mode. The runner sets single-thread numerical environments for child processes.

## Required Inputs

The upstream survey files are read from `/root/data/数据/食物消费调查数据/处理后的data/`: `户表数据_已清洗.dta`, `村表数据_已清洗.dta`, and `村表数据_已清洗_变量标签.csv`. Item-level inputs are read from `/root/data/Paper/食物消费数据/paper0-EASI/item_level_food_descriptives/outputs/`: `household_item_long.dta`, `household_community_price_mapping.csv`, and `item_catalog.csv`. These confidential household inputs are not distributed in the code/results repository. A relocated project retains its own `code/`, `data/`, `outputs/`, and `documentation/` structure; upstream paths in `01_build_data.py` and the runner's input check must be updated together when relocating the underlying data.

## Completion And Outputs

`outputs/RUN_ALL_MANIFEST.json` records command lines, input/source SHA-256 identities, package versions, elapsed times, child exit codes, and hashes of newly written expected outputs. Historical per-run manifests and stage logs remain under `logs/`. `outputs/RUN_ALL_COMPLETE.json` is written only after a successful full run. Check-only mode has separate `PIPELINE_CHECK_MANIFEST.json` and `PIPELINE_CHECK_COMPLETE.json` files and does not certify scientific-stage execution. Both entry points remove their old success marker before beginning, because Stata `shell` alone does not reliably propagate a child failure.

Principal deliverables are `outputs/完整主要结果.txt`, `documentation/RESULTS_SUMMARY.md`, the `outputs/maidads_8/` and `outputs/maidads_10/` elasticity/scenario tables, and the `outputs/stata_stage1_K/` participation and first-stage diagnostics. Separate `outputs/budget_shape_K/` files contain the same-sample cluster-Wald quadratic test, Gamma working-likelihood AIC/BIC comparison, loglinear sensitivity coefficients, and household predictions. This diagnostic does not overwrite the primary first stage or constrain income slopes to be positive. `outputs/FIRST_STAGE_ACTUAL_FUNCTIONS.txt` describes the executed Stata module. Household-level files remain local and should not be published.

The reported Stata p-values concern the first-stage coefficients or income slopes. Final staged elasticities have no claimed bootstrap standard errors or p-values. Correlated participation is a working model of positive latent dependence, and its independence from the conditional demand disturbance is an assumption. Conditional Hicksian elasticities and the full price response with changing food budget and participation are distinct quantities. Predicted quantities use fixed reference-basket equivalents, not literal future kilograms. No feed-pressure projection is produced.
