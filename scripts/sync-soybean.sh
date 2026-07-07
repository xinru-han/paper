#!/usr/bin/env bash
# Sync soybean second-best equilibrium simulation (code + results + webapp)
# from /root/soybean_sim to the paper repo subfolder and push.
set -euo pipefail

SRC="/root/data/Paper/大豆理论文章/soybean_sim"
DEST="/root/paper/soybean_second_best"
REPO="/root/paper"
LOG="/var/log/paper-sync-soybean.log"

mkdir -p "${DEST}"

rsync -a --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude 'config/*.tmp' \
  --exclude '.git/' \
  --exclude 'nohup.out' \
  "${SRC}/" "${DEST}/"

cd "${REPO}"
if ! git diff --quiet -- soybean_second_best/ 2>/dev/null || \
   ! git diff --cached --quiet -- soybean_second_best/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard soybean_second_best/)" ]]; then
  git add soybean_second_best/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync soybean_second_best: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed soybean_second_best" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
