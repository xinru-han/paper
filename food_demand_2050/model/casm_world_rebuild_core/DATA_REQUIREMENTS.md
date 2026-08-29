# Processed-data requirements

The Git repository contains the CASM-World source, configuration, tests and
study outputs. It does not duplicate the full processed benchmark layer,
which is approximately 243 MB and includes a 173 MB climate-yield path file.

The complete executable copy is available in the study archive:

`/root/data/Paper/食物预测2050/casm_world_rebuild_diet_study_20260829/model_run/`

Key processed inputs used by the run are listed below. Paths are relative to
that model root.

| File | SHA-256 |
|---|---|
| `data/processed/benchmark_equilibrium_2023.csv` | `ab7acf0c4039c982bcdda6c571c449b54252ac92f307b7db195c305774ab11e3` |
| `data/processed/casm_world_parameters_v2_2023.csv` | `8b9d53bbfd9ce6662cbafdd1599fa86f76d4c74d42476cd4debbd95f9b90d698` |
| `data/processed/ssp_drivers_2023_2050.csv` | `75d0d4fe8018e08e275214791376f783e468680598961723f9dd1a2b08f93656` |
| `data/processed/tfp_paths_2023_2050.csv` | `37ce2173801ebd6c06cad835b9e79f6ae3922531ac5d8c0b9dc39a7d4dbdddf1` |
| `data/processed/climate_yield_paths_2023_2050.csv` | `dd6cff858a9a8b177f7440ccf1110f8be7eb1c0bda03afed21ce3dc1f5660398` |
| `data/processed/real_exchange_rate_paths_2023_2050.csv` | `75d7f8917cf320ed328e10df1ee135cad83712ca6c9462248b986d997a197fd6` |
| `data/processed/tariff_paths_2023_2050.csv` | `2a7c4e1fbfed0dae47a410e82f1d84f8108032b40a24ca68abd459cad45bb3d5` |
| `data/processed/ghg_emission_factors_2023.csv` | `bd607be6d6a2a813c785b6bba38aec7050e1306516be61db11a78ae502474ff5` |
| `data/processed/nutrition_coefficients_2023.csv` | `d824694c8fabab51cdc05be590988c9eb8e293a324f2676ce7fe8042e8f38588` |
| `data/processed/reporting_model_account_membership_2023.csv` | `601aeb80493f82202a2e4a6a09d3290bba6e8e8a3b135783e3d27e809335e601` |
| `data/processed/reporting_source_allocation_weights_2023.csv` | `14c7f628227467abaac8bdc52de8b6bdc0f4b28c07764fbfad63028a715df950` |
| `data/processed/reporting_source_group_membership_2023.csv` | `d4b9e42940e088c144c5260b45dd76d0ab1d3ddc5771c6f4090770706f180ed7` |

The counterfactual run report records the hashes of the study configuration,
mapped diet paths, simulation configuration and V2 parameter table. Derived
output hashes are recorded in the same report.

