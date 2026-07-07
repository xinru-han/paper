#!/usr/bin/env bash
# Paper 9 driver: run the chain with memory gates (machine shared with another
# project's bootstrap). Logs to logs/pipeline.log.
cd /root/data/Paper/央视数据/paper9-easiq
PLOG=logs/pipeline.log
say() { echo "[$(date +%H:%M:%S)] $*" >> "$PLOG"; }
wait_mem() { until [ "$(free -g | awk 'NR==2{print $7}')" -ge "$1" ]; do sleep 60; done; }
run_r() {
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
[ -f data/interim/uv_hh_month_cat.csv.gz ] || run_r 90a_uv_build.R 6 5
[ -f data/interim/quality_panel.rds ]      || run_r 90b_price_panel.R 4 5
[ -f data/lookups/quality_ladder.csv ]     || run_r 90c_ladder.R 2 3
[ -f outputs/tables/t2a_income_link.csv ]  || run_r 90d_income_link.R 4 5
[ -f data/interim/stageA.rds ]             || run_r 91_stageA_easi.R 8 8
[ -f outputs/tables/t3_theta.csv ]         || run_r 92_stageB_quality.R 6 6
[ -f outputs/tables/t4_two_margin_elasticities.csv ] || run_r 93_elasticities.R 5 5
run_r 94_psi_matrix.R 2 3
run_r 95_mckelvey.R 5 5
run_r 96_shocks.R 6 5
run_r 97_qcpi.R 2 3
run_r 98_welfare_voucher.R 4 3
run_r 99_robustness.R 5 5
run_r 9f_figures.R 4 3
say "=== main chain done; launching bootstrap ==="
run_r 9x_bootstrap.R 6 3
say "=== pipeline done ==="
