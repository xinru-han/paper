#!/usr/bin/env bash
# Sync feed-grain import elasticity paper code/results to git repo and push.
set -euo pipefail

SRC="/root/data/Paper/饲料进口弹性"
DEST="/root/paper/feed_import_elasticity"
REPO="/root/paper"
LOG="/var/log/paper-sync-feed.log"

mkdir -p "${DEST}"

rsync -a --delete \
  --exclude '进口数据/' \
  --exclude '主产区原粮购销价格监测旬报子任务2005-2025/' \
  --exclude '全国邮政编码数据库/' \
  --exclude 'data/*-food.csv' \
  --exclude 'data/__pycache__/' \
  --exclude 'data/编码对照表*.xlsx' \
  --exclude '*.docx' \
  --exclude '.git/' \
  "${SRC}/" "${DEST}/"

install -m 644 "${REPO}/scripts/feed_import_elasticity.README.md" "${DEST}/README.md"

cd "${REPO}"

if ! git diff --quiet -- feed_import_elasticity/ 2>/dev/null || \
   ! git diff --cached --quiet -- feed_import_elasticity/ 2>/dev/null || \
   [[ -n "$(git ls-files --others --exclude-standard feed_import_elasticity/)" ]]; then
  git add feed_import_elasticity/
  TS="$(date -Iseconds)"
  git commit -m "Auto-sync feed_import_elasticity: ${TS}" || true
  if git push -q origin main; then
    echo "[${TS}] pushed feed_import_elasticity" >> "${LOG}"
  else
    echo "[${TS}] push failed" >> "${LOG}"
    exit 1
  fi
fi
