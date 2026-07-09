#!/bin/bash
# Driver 1: curvature-constrained refit + regularity + bootstrap CIs + welfare.
set -uo pipefail
cd /root/data/Paper/央视数据/Paper1-EASI/model_v2_R
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
rm -f outputs/_DRIVER1_DONE outputs/_DRIVER1_FAILED
fail() { echo "$1" > outputs/_DRIVER1_FAILED; exit 1; }

Rscript src/36_curvature_constrained_v2.R > outputs/_log_36_pcyc.txt 2>&1 || fail "36"
Rscript src/37_curvature_settings_v2.R    > outputs/_log_37_pcyc.txt 2>&1 || fail "37"
Rscript src/38_regularity_final_v2.R      > outputs/_log_38_pcyc.txt 2>&1 || fail "38"
CURV=1 BOOT_B=200 BOOT_CORES=5 Rscript src/34_bootstrap_v2.R > outputs/_log_34_pcyc.txt 2>&1 || fail "34"
CURV=1 Rscript src/35_welfare_cv_v2.R     > outputs/_log_35_pcyc.txt 2>&1 || fail "35"
touch outputs/_DRIVER1_DONE
