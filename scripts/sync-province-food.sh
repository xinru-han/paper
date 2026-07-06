#!/usr/bin/env bash
# Sync province food consumption MAIDADS code/results from working dir to git repo and push.
set -euo pipefail

SRC="/root/data/Paper/省级食物消费/ProvinceMAIDADS"
DEST="/root/paper/province_food_consumption_maidads"
REPO="/root/paper"
LOG="/var/log/paper-sync-province-food.log"

mkdir -p "${DEST}"

rsync -a --delete \
  --exclude '.paper_work/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.ipynb_checkpoints/' \
  --exclude 'ProvinceData/' \
  "${SRC}/" "${DEST}/"

# Preserve repo-only README (not in source working dir)
install -m 644 "${REPO}/scripts/province_food.README.md" "${DEST}/README.md" 2>/dev/null || true

cd "${REPO}"

if ! git diff --quiet -- province_food_consumption_maidads/ 2>/dev/null || \
   ! git diff --cached --quiet -- province_food_consumption_maidads/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard province_food_consumption_maidads/)" ]]; then
  git add province_food_consumption_maidads/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync province_food_consumption_maidads: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed province_food_consumption_maidads" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
