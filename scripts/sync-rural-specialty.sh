#!/usr/bin/env bash
# Sync rural specialty industry paper portfolio (3-paper plan)
# docs from /root/data/Paper/乡村特色产业 + in-repo code/output, then push.
set -euo pipefail

SRC="/root/data/Paper/乡村特色产业"
DEST="/root/paper/rural_specialty_industry"
REPO="/root/paper"
LOG="/var/log/paper-sync-rural-specialty.log"

mkdir -p "${DEST}/docs"

rsync -a --delete \
  --include '*/' \
  --include '*.md' \
  --include '*.py' \
  --include '*.R' \
  --include '*.do' \
  --exclude '*' \
  "${SRC}/" "${DEST}/docs/"

cd "${REPO}"
if ! git diff --quiet -- rural_specialty_industry/ 2>/dev/null || \
   ! git diff --cached --quiet -- rural_specialty_industry/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard rural_specialty_industry/)" ]]; then
  git add rural_specialty_industry/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync rural_specialty_industry: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed rural_specialty_industry" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
