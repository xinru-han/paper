#!/usr/bin/env bash
set -euo pipefail

PROJECT="${1:-/root/data/Paper/饲料进口弹性/stata_replication_2026}"
ADO_DIR="${2:-$PROJECT/ado}"
PYTHON="${PYTHON:-/root/.claude-science/conda/envs/python/bin/python}"
STATA="${STATA:-/usr/local/stata17/stata-se}"

mkdir -p "$PROJECT/logs" "$PROJECT/output" "$PROJECT/data" "$PROJECT/input"
"$PYTHON" "$PROJECT/code/00_export_input.py" | tee "$PROJECT/logs/00_export_input.log"
"$STATA" -b do "$PROJECT/code/01_prepare_data.do" "$PROJECT"
mv -f 01_prepare_data.log "$PROJECT/logs/01_prepare_data.log" 2>/dev/null || true
"$STATA" -b do "$PROJECT/code/02_estimate_models.do" "$PROJECT" "$ADO_DIR"
"$STATA" -b do "$PROJECT/code/04_postprocess_reference.do" "$PROJECT" "$ADO_DIR"
"$STATA" -b do "$PROJECT/code/05_estimate_no_sy.do" "$PROJECT" "$ADO_DIR"
"$STATA" -b do "$PROJECT/code/06_postprocess_no_sy_reference.do" "$PROJECT" "$ADO_DIR"
"$PYTHON" "$PROJECT/code/07_build_report.py"

echo "Stata replication completed: $PROJECT"
