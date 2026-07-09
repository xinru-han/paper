#!/bin/bash
set -uo pipefail
cd /root/data/Paper/央视数据/Paper1-EASI/model_v2_R
export OPENBLAS_NUM_THREADS=1
rm -f outputs/_AUDITFIX_DONE outputs/_AUDITFIX_FAILED
SMOKE_V2=1 Rscript src/33_robustness_v2.R > outputs/_log_33_fix_smoke.txt 2>&1 || { echo 33smoke > outputs/_AUDITFIX_FAILED; exit 1; }
Rscript src/33_robustness_v2.R > outputs/_log_33_fix_full.txt 2>&1 || { echo 33full > outputs/_AUDITFIX_FAILED; exit 1; }
touch outputs/_AUDITFIX_DONE
