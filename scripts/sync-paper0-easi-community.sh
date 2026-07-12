#!/usr/bin/env bash
# Sync the reproducible community-price EASI pipeline without raw survey data.
set -euo pipefail

SRC="/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price"
DEST="/root/paper/paper0_easi_community_price"

mkdir -p "${DEST}"
rsync -a --delete \
  --exclude 'data/*.dta' \
  --exclude 'outputs/*.dta' \
  --exclude 'outputs/*.ster' \
  --exclude '.DS_Store' \
  --exclude '._*' \
  "${SRC}/" "${DEST}/"
