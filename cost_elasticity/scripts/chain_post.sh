#!/bin/bash
# 等 R2 全部 R 作业结束（robust_matrix/gamma_break/estimate），再启动 run_post_R2
cd /root/paper/cost_elasticity
while ps -C R -o args 2>/dev/null | grep -qE "robust_matrix\.R|gamma_break\.R|estimate\.R"; do sleep 30; done
echo "=== R2 all R jobs finished $(date); launching post-R2 ===" >> out/_post_logs/chain.log 2>/dev/null || { mkdir -p out/_post_logs; echo "=== R2 done $(date) ===" >> out/_post_logs/chain.log; }
bash scripts/run_post_R2.sh >> out/_post_logs/run_post_R2.log 2>&1
echo "=== post-R2 pipeline finished $(date) ===" >> out/_post_logs/chain.log
