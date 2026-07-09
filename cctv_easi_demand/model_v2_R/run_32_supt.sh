#!/bin/bash
set -uo pipefail
cd /root/data/Paper/央视数据/Paper1-EASI/model_v2_R
export OPENBLAS_NUM_THREADS=1
rm -f outputs/_32SUPT_DONE outputs/_32SUPT_FAILED
SMOKE_V2=1 Rscript src/32_estimate_main_v2.R > outputs/_log_32_supt_smoke.txt 2>&1 || { echo 32smoke > outputs/_32SUPT_FAILED; exit 1; }
Rscript src/32_estimate_main_v2.R > outputs/_log_32_supt_full.txt 2>&1 || { echo 32full > outputs/_32SUPT_FAILED; exit 1; }
touch outputs/_32SUPT_DONE
