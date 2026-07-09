#!/bin/bash
# Driver 1b: after the constrained regularity checks (36/37/38, now a robustness),
# run the UNCONSTRAINED bootstrap (primary CIs) and unconstrained welfare, since
# the near-regular unconstrained participation-adjusted system is the headline.
set -uo pipefail
cd /root/data/Paper/央视数据/Paper1-EASI/model_v2_R
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
rm -f outputs/_DRIVER1B_DONE outputs/_DRIVER1B_FAILED
fail() { echo "$1" > outputs/_DRIVER1B_FAILED; exit 1; }

# wait for any still-running 37 to finish
while pgrep -f "37_curvature_settings_v2.R" > /dev/null; do sleep 5; done

[ -f outputs/regularity/curvature_representative_points_v2.csv ] || \
  Rscript src/38_regularity_final_v2.R > outputs/_log_38_pcyc.txt 2>&1 || fail "38"
# ensure fresh 38 with pcyc constrained fit
Rscript src/38_regularity_final_v2.R > outputs/_log_38_pcyc.txt 2>&1 || fail "38"

# UNCONSTRAINED primary bootstrap (no CURV) -> *_ci_v2.csv (no _curv suffix)
BOOT_B=200 BOOT_CORES=5 Rscript src/34_bootstrap_v2.R > outputs/_log_34_uncon_pcyc.txt 2>&1 || fail "34"
# UNCONSTRAINED welfare (uses main_fit_v2.rds + unconstrained bootstrap draws)
Rscript src/35_welfare_cv_v2.R > outputs/_log_35_uncon_pcyc.txt 2>&1 || fail "35"
touch outputs/_DRIVER1B_DONE
