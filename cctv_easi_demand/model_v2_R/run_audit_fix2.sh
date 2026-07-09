#!/bin/bash
# Audit-fix rerun: 30 (fold-specific hybrid, coverage, cert col) ->
# 32 (studentized score boot, CR1, fold-clean OOF, y2p rename) -> 33 (+R9)
set -uo pipefail
cd /root/data/Paper/央视数据/Paper1-EASI/model_v2_R
export OPENBLAS_NUM_THREADS=1
rm -f outputs/_AUDITFIX_DONE outputs/_AUDITFIX_FAILED

fail() { echo "$1" > outputs/_AUDITFIX_FAILED; exit 1; }

# 30 already done
SMOKE_V2=1 Rscript src/32_estimate_main_v2.R > outputs/_log_32_fix_smoke.txt 2>&1 || fail "32smoke"
Rscript src/32_estimate_main_v2.R > outputs/_log_32_fix_full.txt 2>&1 || fail "32full"
SMOKE_V2=1 Rscript src/33_robustness_v2.R > outputs/_log_33_fix_smoke.txt 2>&1 || fail "33smoke"
Rscript src/33_robustness_v2.R > outputs/_log_33_fix_full.txt 2>&1 || fail "33full"

touch outputs/_AUDITFIX_DONE
echo done
