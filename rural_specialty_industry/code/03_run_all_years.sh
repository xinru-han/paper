#!/usr/bin/env bash
# 逐年：解压 -> 处理 -> 删除解压出的原始 .dta（保留 zip）。
# 用法: bash 03_run_all_years.sh 2011 2012 ... (缺省则2010-2023全部)
set -uo pipefail

ZIPDIR="/root/data/数据/乡村产业数据/工商注册数据"
TMP="${ZIPDIR}/_tmp_extract"
CODE="/root/paper/rural_specialty_industry/code/02_process_firm_registration.py"
OUTD="/root/paper/rural_specialty_industry/output/firm_reg"
mkdir -p "$TMP" "$OUTD"

YEARS=("$@")
if [ ${#YEARS[@]} -eq 0 ]; then
  YEARS=(2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023)
fi

for y in "${YEARS[@]}"; do
  echo "==== $y $(date -Iseconds) ===="
  if [ -f "${OUTD}/county_industry_${y}.csv" ] && [ -f "${OUTD}/qc_${y}.txt" ]; then
    echo "[$y] 已完成，跳过"; rm -f "${TMP}/${y}.dta"; continue
  fi
  if [ ! -f "${TMP}/${y}.dta" ]; then
    echo "[$y] 解压..."; unzip -o "${ZIPDIR}/${y}.dta.zip" -d "$TMP" >/dev/null || { echo "[$y] 解压失败"; continue; }
  fi
  echo "[$y] 处理..."
  if /usr/bin/python3 "$CODE" "$y" >> "${OUTD}/run_${y}.log" 2>&1; then
    echo "[$y] 成功，删除解压 .dta"; rm -f "${TMP}/${y}.dta"
  else
    echo "[$y] 处理失败，保留 .dta 供排查"; tail -5 "${OUTD}/run_${y}.log"
  fi
done
echo "==== ALL DONE $(date -Iseconds) ===="
