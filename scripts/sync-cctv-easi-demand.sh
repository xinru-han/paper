#!/usr/bin/env bash
# Sync CCTV Paper1-EASI food demand code/results to git repo and push.
set -euo pipefail

SRC="/root/data/Paper/央视数据/Paper1-EASI"
DEST="/root/paper/cctv_easi_demand"
REPO="/root/paper"
LOG="/var/log/paper-sync-cctv.log"

mkdir -p "${DEST}"

rsync -a --delete \
  --exclude 'processed/' \
  --exclude 'repro_run/data_derived/' \
  --exclude 'repro_run/processed/' \
  --exclude 'repro_run/processed' \
  --exclude 'repro_run/Data_merged.csv' \
  --exclude 'repro_run/outputs/demand/selection_cre_probit_predictions_r.csv' \
  --exclude '__pycache__/' \
  --exclude '._*' \
  --exclude '.git/' \
  "${SRC}/" "${DEST}/"

install -m 644 "${REPO}/scripts/cctv_easi_demand.README.md" "${DEST}/README.md"

cd "${REPO}"

if ! git diff --quiet -- cctv_easi_demand/ 2>/dev/null || \
   ! git diff --cached --quiet -- cctv_easi_demand/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard cctv_easi_demand/)" ]]; then
  git add cctv_easi_demand/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync cctv_easi_demand: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed cctv_easi_demand" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
