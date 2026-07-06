#!/usr/bin/env bash
# Sync Separability / food self-provisioning paper (Paper1-Seperability)
# code + results to the git repo and push.
set -euo pipefail

SRC="/root/data/Paper/食物消费数据/Paper1-Seperability"
DEST="/root/paper/separability_selfprovisioning"
REPO="/root/paper"
LOG="/var/log/paper-sync-separability.log"

mkdir -p "${DEST}"

rsync -a --delete \
  --exclude 'data/analysis_ready/' \
  --exclude 'data/cleaned/' \
  --exclude 'data/backups/' \
  --exclude '_extracted_code/' \
  --exclude '__pycache__/' \
  --exclude '._*' \
  --exclude '.DS_Store' \
  --exclude '*.docx' \
  --exclude '.git/' \
  "${SRC}/" "${DEST}/"

# Keep only the small self-contained reproduction inputs (zipped snapshots).
mkdir -p "${DEST}/data/repro_inputs"
rsync -a --delete "${SRC}/data/repro_inputs/" "${DEST}/data/repro_inputs/"

install -m 644 "${REPO}/scripts/separability_selfprovisioning.README.md" "${DEST}/README.md"

cd "${REPO}"
if ! git diff --quiet -- separability_selfprovisioning/ 2>/dev/null || \
   ! git diff --cached --quiet -- separability_selfprovisioning/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard separability_selfprovisioning/)" ]]; then
  git add separability_selfprovisioning/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync separability_selfprovisioning: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed separability_selfprovisioning" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
