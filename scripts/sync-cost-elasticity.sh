#!/usr/bin/env bash
# Sync cost_elasticity paper (translog cost function, Lewis narrative)
# Work happens directly in /root/paper/cost_elasticity — just commit + push.
set -euo pipefail

REPO="/root/paper"
LOG="/var/log/paper-sync-cost-elasticity.log"

cd "${REPO}"
if ! git diff --quiet -- cost_elasticity/ 2>/dev/null || \
   ! git diff --cached --quiet -- cost_elasticity/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard cost_elasticity/)" ]]; then
  git add cost_elasticity/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync cost_elasticity: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed cost_elasticity" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
