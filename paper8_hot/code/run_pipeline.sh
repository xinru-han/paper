#!/usr/bin/env bash
# Paper 8 driver: run remaining scripts in order, with memory gates for the
# heavy household-level steps (the machine is shared with another project's
# bootstrap). Logs to logs/pipeline.log; per-script logs alongside.
cd /root/data/Paper/央视数据/paper8-hot
PLOG=logs/pipeline.log
say() { echo "[$(date +%H:%M:%S)] $*" >> "$PLOG"; }

wait_mem() {  # $1 = GB available required
  until [ "$(free -g | awk 'NR==2{print $7}')" -ge "$1" ]; do sleep 60; done
}

run_r() {  # $1 script, $2 required GB (0 = none), $3 retries
  local script=$1 gb=${2:-0} tries=${3:-1} rc
  for t in $(seq 1 "$tries"); do
    [ "$gb" -gt 0 ] && wait_mem "$gb"
    say "start $script (try $t, $(free -g | awk 'NR==2{print $7}')G free)"
    Rscript "code/$script" >> "logs/${script%.R}.log" 2>&1
    rc=$?
    say "end $script rc=$rc"
    [ $rc -eq 0 ] && return 0
    sleep 120
  done
  return 1
}

say "=== pipeline start ==="
[ -f outputs/tables/t1b_group_coefs.csv ]  || run_r 05b_group_regs.R 4 5
[ -f outputs/tables/t2_inference_triple.csv ] || run_r 05c_unit_inference.R 2 3
[ -f outputs/tables/t1a_grid_coefs.csv ]   || run_r 05a_grid_regs.R 8 8
run_r 06_channel.R 2 3
run_r 07_margins.R 8 8
run_r 10_nutrition.R 5 5
run_r 11_projection.R 2 3
run_r 12_robustness.R 2 3
run_r 13_figures.R 2 3
say "=== pipeline done ==="
