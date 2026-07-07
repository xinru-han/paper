#!/usr/bin/env bash
# Auto-commit & push the food_demand_2050 subfolder (work happens directly
# in the repo, so no rsync source — just commit whatever changed).
set -euo pipefail

REPO="/root/paper"
SUB="food_demand_2050"
LOG="/var/log/paper-sync-food-demand-2050.log"

cd "${REPO}"
if ! git diff --quiet -- "${SUB}/" 2>/dev/null || \
   ! git diff --cached --quiet -- "${SUB}/" 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard "${SUB}/")" ]]; then
  git add "${SUB}/"
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync ${SUB}: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed ${SUB}" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
