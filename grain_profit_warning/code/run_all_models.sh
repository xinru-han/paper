#!/bin/bash
# 顺序跑全部模型, 每步失败自动重试2次, 日志落盘
cd /root/grain_profit_warning
mkdir -p output/logs
for s in 03_baselines 05_ft_transformer 06_tabpfn; do
  for try in 1 2 3; do
    echo "[$(date +%T)] start $s try$try" >> output/logs/runner.log
    HF_ENDPOINT=https://hf-mirror.com OMP_NUM_THREADS=4 python3 -u code/$s.py > output/logs/$s.log 2>&1
    rc=$?
    echo "[$(date +%T)] $s exit=$rc" >> output/logs/runner.log
    [ $rc -eq 0 ] && break
    sleep 30
  done
done
echo "[$(date +%T)] ALL_MODELS_DONE" >> output/logs/runner.log
