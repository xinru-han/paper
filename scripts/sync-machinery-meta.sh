#!/usr/bin/env bash
# Sync machinery_meta paper (农机Meta：Meta分析+CASM情景模拟)
# Work happens directly in /root/paper/machinery_meta — just commit + push.
set -euo pipefail

REPO="/root/paper"
LOG="/var/log/paper-sync-machinery-meta.log"

cd "${REPO}"
if ! git diff --quiet -- machinery_meta/ 2>/dev/null || \
   ! git diff --cached --quiet -- machinery_meta/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard machinery_meta/)" ]]; then
  git add machinery_meta/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync machinery_meta: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed machinery_meta" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
