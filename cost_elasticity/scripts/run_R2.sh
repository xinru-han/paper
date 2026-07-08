#!/bin/bash
# run_R2.sh — R2 主重估矩阵：四个单线程 R 作业并行
set -uo pipefail
cd /root/paper/cost_elasticity
LOG=out/_R2_logs; mkdir -p $LOG

echo "=== R2 start $(date) ==="
# 1) 稳健性矩阵（M3/M10/M11/M12c/M13a/M13b/M13c）
Rscript R/robust_matrix.R > $LOG/robust_matrix.log 2>&1 &
P1=$!
# 2) Spec B（M2 + G2）
Rscript R/robust_specB.R > $LOG/robust_specB.log 2>&1 &
P2=$!
# 3) Γ 断点（M6 + G3）
Rscript R/gamma_break.R > $LOG/gamma_break.log 2>&1 &
P3=$!
CROPS="corn wheat soybean rice_japonica rice_mid_indica rice_early_indica rice_late_indica peanut rapeseed"
HWCROPS="corn_hw wheat_hw soybean_hw rice_japonica_hw rice_mid_indica_hw rice_early_indica_hw rice_late_indica_hw peanut_hw rapeseed_hw"
# 4) 基线重估刷新（当前面板）→ hw 面板重建 → hw 全套 postest（M12a）
( Rscript R/estimate.R $CROPS cc plain && \
  Rscript R/make_hw_panels.R && \
  Rscript R/estimate.R $HWCROPS cc plain ) \
  > $LOG/baseline_hw_postest.log 2>&1 &
P4=$!

wait $P1; echo "robust_matrix exit=$? $(date)"
wait $P2; echo "robust_specB exit=$? $(date)"
wait $P3; echo "gamma_break exit=$? $(date)"
wait $P4; echo "baseline+hw_postest exit=$? $(date)"
echo "=== R2 done $(date) ==="
