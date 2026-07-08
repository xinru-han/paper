#!/bin/bash
# run_post_R2.sh — R2 之后：refresh(S2/6f/decomp/priceCV) → M8/M9 → bootstrap(M1) → M4/M7
set -uo pipefail
cd /root/paper/cost_elasticity
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1   # 单线程BLAS，防 mclapply thrash
export BOOT_CORES=6
LOG=out/_post_logs; mkdir -p $LOG
CROPS="corn wheat soybean rice_japonica rice_mid_indica rice_early_indica rice_late_indica peanut rapeseed"
echo "=== post-R2 start $(date) ==="

# --- Group A：独立刷新（并行，单线程各一）---
Rscript R/postest_s2.R $CROPS      > $LOG/postest_s2.log 2>&1 &
Rscript R/robust_6f.R              > $LOG/robust_6f.log 2>&1 &
Rscript R/postest_decomp.R $CROPS  > $LOG/postest_decomp.log 2>&1 &
Rscript R/price_crossvalid.R       > $LOG/price_crossvalid.log 2>&1 &
wait; echo "Group A done $(date)"

# --- Group B：自并行作业（顺序，避免嵌套并行）---
Rscript R/tests_boot.R        > $LOG/tests_boot.log 2>&1 ; echo "tests_boot done $(date)"
Rscript R/induced_regional.R  > $LOG/induced_regional.log 2>&1 ; echo "induced_regional done $(date)"

# --- Group C：主 bootstrap（M1 联合重抽，长）---
Rscript R/bootstrap_all.R 500 ""   > $LOG/bootstrap_main.log 2>&1 ; echo "bootstrap_main done $(date)"

# --- Group D：hw 子集 + 双 block ---
Rscript R/bootstrap_all.R 500 "_hw" > $LOG/bootstrap_hw.log 2>&1 ; echo "bootstrap_hw done $(date)"
Rscript R/bootstrap_doubleblock.R   > $LOG/bootstrap_doubleblock.log 2>&1 ; echo "doubleblock done $(date)"

# --- Group E：需要 draws 的后处理 ---
Rscript R/postest_tauC.R      > $LOG/postest_tauC.log 2>&1 &
Rscript R/bias_consistency.R  > $LOG/bias_consistency.log 2>&1 &
wait; echo "Group E done $(date)"
echo "=== post-R2 done $(date) ==="
