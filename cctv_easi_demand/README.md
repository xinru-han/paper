# CCTV EASI Purchase Demand v2

This project estimates a nine-group monthly food purchase-demand system for
China using CCTV scanner data and external provincial food prices.

The current revision follows the Food Policy-oriented response to
`EASI_V2_econometric_audit_AJAE_FoodPolicy.md`:

- monthly outcomes are described as purchase demand, not literal consumption;
- invalid quarterly/annual full SY and full-sample ever-buyer double-hurdle
  outputs are removed from the robustness bundle;
- the 28-day frequency diagnostic now builds a complete zero grid;
- welfare outputs are retained as exploratory/potential-demand calculations
  rather than a strict unconditional corner-demand welfare result;
- audit diagnostics are written to `model_v2_R/outputs/audit/`;
- generated outputs are indexed in `model_v2_R/outputs/results_manifest_v2.csv`.

Raw and derived household-level data are intentionally not versioned in git.
Required local data inputs include `model_v2_R/data_derived/` and selected files
under `processed/`.

Main commands:

```bash
Rscript run_all.R
bash paper_v2/src/run_finalize.sh
```

The latest generated manuscript is:

```text
paper_v2/manuscript_food_policy_v2.docx
```
