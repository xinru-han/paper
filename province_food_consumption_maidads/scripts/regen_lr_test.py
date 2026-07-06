"""Regenerate the authoritative LR test CSV from the province-block LR bootstrap
draws, using the CORRECTED optimum's observed LR (466.54). The previous top-level
file reported the void-basin LR (191.9); the Diagnostics/ copy reported 441.3.
Both are stale. This script is the single source of truth for the LR CSV.
Run from scripts/ with PYTHONPATH=scripts."""
import pandas as pd, numpy as np, json
from pathlib import Path
RES=Path(__file__).resolve().parents[1]/"Results"

# corrected optimum (see OPTIMUM_CORRECTION_NOTE.md)
NLL_A=-4248.285092302137
NLL_M=-4481.554472  # authoritative global optimum (omega=0.705, kappa=4.91)
OBS_LR=2*(abs(NLL_M)-abs(NLL_A))  # 466.54

draws=pd.read_csv(RES/"lr_bootstrap_draws.csv")
lr=draws["lr_stat"].dropna(); lr=lr[(lr>0)&np.isfinite(lr)]
n=len(lr)
tail=float((lr>=OBS_LR).mean())
row=dict(test="MAIDADS_vs_AIDADS",
         observed_lr=round(OBS_LR,4),
         bootstrap_reps=int(draws.shape[0]),
         completed_reps=int(draws["success"].notna().sum()),
         successful_reps=int(n),
         convergence_rate=round(n/draws.shape[0],3),
         cluster_bootstrap_tail_probability=round(tail,4),
         lr_bootstrap_median=round(float(np.median(lr)),4),
         lr_bootstrap_q95=round(float(np.percentile(lr,95)),4),
         lr_bootstrap_q99=round(float(np.percentile(lr,99)),4),
         chi2_p_value_status="invalid_not_reported",
         note=("Cluster bootstrap with province-block resampling; MAIDADS speed "
               "parameter unidentified under the AIDADS null, so chi-square p not used. "
               "Observed LR from the CORRECTED global optimum (nll_M=-4481.554)."),
         inference_scale="formal")
out=pd.DataFrame([row])
out.to_csv(RES/"lr_test_chi2_and_bootstrap.csv",index=False)
# keep Diagnostics/ copy in sync
(RES/"Diagnostics").mkdir(exist_ok=True)
out.to_csv(RES/"Diagnostics"/"lr_test_chi2_and_bootstrap.csv",index=False)
print(json.dumps(row,indent=1,ensure_ascii=False))
