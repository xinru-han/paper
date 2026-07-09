#!/bin/bash
# Driver 2b: robustness scripts re-run ALONE (after the bootstrap) to avoid the
# out-of-memory that killed 33 when it ran concurrently with the 5-fork bootstrap.
set -uo pipefail
cd /root/data/Paper/央视数据/Paper1-EASI/model_v2_R
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
rm -f outputs/_DRIVER2_DONE outputs/_DRIVER2_FAILED
fail() { echo "$1" > outputs/_DRIVER2_FAILED; exit 1; }

Rscript src/33_robustness_v2.R          > outputs/_log_33_pcyc.txt 2>&1 || fail "33"
Rscript src/41_frequency_benchmark_v2.R > outputs/_log_41_pcyc.txt 2>&1 || fail "41"
Rscript src/42_fourweek_frequency_v2.R  > outputs/_log_42_pcyc.txt 2>&1 || fail "42"
Rscript src/40_freq_winsor_zero_v2.R    > outputs/_log_40_pcyc.txt 2>&1 || fail "40"
touch outputs/_DRIVER2_DONE
