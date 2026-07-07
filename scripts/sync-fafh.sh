#!/usr/bin/env bash
# Sync FAFH adjustment-factor paper (Food Policy submission)
# code + results + manuscript to the git repo and push.
set -euo pipefail

SRC="/root/data/Paper/fafh"
DEST="/root/paper/fafh"
REPO="/root/paper"
LOG="/var/log/paper-sync-fafh.log"

mkdir -p "${DEST}"

rsync -a --delete \
  --exclude 'lit/' \
  --exclude 'archive/' \
  --exclude 'data/data.csv' \
  --exclude 'data/imputed_ratios_best.csv' \
  --exclude 'data/data2012.csv.backup' \
  --exclude 'code/checkpoints/' \
  --exclude '__pycache__/' \
  --exclude 'catboost_info/' \
  --exclude '._*' \
  --exclude '.DS_Store' \
  --exclude '*.docx' \
  --exclude '*.zip' \
  --exclude '.git/' \
  --exclude '.cursor/' \
  "${SRC}/" "${DEST}/"

cd "${REPO}"
if ! git diff --quiet -- fafh/ 2>/dev/null || \
   ! git diff --cached --quiet -- fafh/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard fafh/)" ]]; then
  git add fafh/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync fafh: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed fafh" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
