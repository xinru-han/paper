#!/usr/bin/env bash
set -euo pipefail

PROJECT="${1:-/root/data/Paper/饲料进口弹性/stata_aids_baseline_2026}"
RAW="${2:-/root/data/Paper/饲料进口弹性/data}"
STATA="${STATA:-/usr/local/stata17/stata-se}"

mkdir -p "$PROJECT/data" "$PROJECT/output" "$PROJECT/logs"
"$STATA" -q -b do "$PROJECT/code/01_describe_and_build.do" "$PROJECT" "$RAW"
"$STATA" -q -b do "$PROJECT/code/02_estimate_aids.do" "$PROJECT"
"$STATA" -q -b do "$PROJECT/code/03_elasticities.do" "$PROJECT"
python3 "$PROJECT/code/04_build_report.py" "$PROJECT"
