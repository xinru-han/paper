#!/bin/bash
# 全品种估计 → S2 → 分解/OOS → bootstrap(corn) → 图
set -uo pipefail
cd /root/paper/cost_elasticity
CROPS="corn wheat soybean rice_japonica rice_mid_indica rice_early_indica rice_late_indica peanut rapeseed"

echo "=== [1/5] estimate all crops (plain + cc) ==="
Rscript R/estimate.R $CROPS plain cc || echo "!! estimate FAILED"

echo "=== [2/5] S2 bias paths + induced innovation ==="
Rscript R/postest_s2.R $CROPS || echo "!! s2 FAILED"

echo "=== [3/5] decomposition + OOS ==="
for c in $CROPS; do Rscript R/postest_decomp.R $c || echo "!! decomp $c FAILED"; done

echo "=== [4/5] bootstrap corn cc B=200 ==="
Rscript R/bootstrap.R corn 200 cc || echo "!! bootstrap FAILED"

echo "=== [5/5] figures ==="
for c in $CROPS; do Rscript R/build_figs.R $c || echo "!! figs $c FAILED"; done

echo "=== pipeline done $(date) ==="
