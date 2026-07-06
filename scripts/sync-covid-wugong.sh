#!/usr/bin/env bash
# Sync COVID migrant-work paper code/results from working dir to git repo and push.
set -euo pipefail

SRC="/root/data/Paper/covid"
DEST="/root/paper/covid_wugong"
REPO="/root/paper"
LOG="/var/log/paper-sync-covid.log"

mkdir -p "${DEST}"

rsync -a --delete \
  --exclude '_extract/' \
  --exclude '新冠对务工的影响_数据+code/' \
  --exclude '*.zip' \
  --exclude '*.dta' \
  --exclude '*.docx' \
  --exclude '.git/' \
  "${SRC}/" "${DEST}/"

# Preserve repo-only README (not in source working dir)
install -m 644 "${REPO}/scripts/covid_wugong.README.md" "${DEST}/README.md"

cd "${REPO}"

if ! git diff --quiet -- covid_wugong/ 2>/dev/null || \
   ! git diff --cached --quiet -- covid_wugong/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard covid_wugong/)" ]]; then
  git add covid_wugong/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync covid_wugong: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed covid_wugong" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
