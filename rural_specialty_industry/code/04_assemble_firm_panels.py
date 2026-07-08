#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_assemble_firm_panels.py
把逐年产出合并为三张最终面板（供三篇论文直接用）：
  county_industry_panel_2010_2023.csv  省份×城市×区县×二级行业×year
  agri_county3_panel_2010_2023.csv     涉农 省份×城市×区县×三级行业×year
  agri_total_county_year.csv           涉农合计 省份×城市×区县×year（含合作社数、资本）
  firm_reg_qc_summary.csv              各年总量核对
仅合并轻量CSV；企业级 pkl.gz 保留本地，日后落乡镇时用。
"""
import glob
import os
import re
import pandas as pd

OUTD = "/root/paper/rural_specialty_industry/output/firm_reg"
FIN = "/root/paper/rural_specialty_industry/output"


def concat(pattern):
    fs = sorted(glob.glob(f"{OUTD}/{pattern}"))
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else None


ci = concat("county_industry_*.csv")
if ci is not None:
    ci.to_csv(f"{FIN}/county_industry_panel_2010_2023.csv",
              index=False, encoding="utf-8-sig")

a3 = concat("agri_county3_*.csv")
if a3 is not None:
    a3.to_csv(f"{FIN}/agri_county3_panel_2010_2023.csv",
              index=False, encoding="utf-8-sig")
    at = a3.groupby(["省份", "城市", "区县", "year"], dropna=False).agg(
        n_agri_firms=("n_firms", "sum"), agri_cap_wan=("cap_wan", "sum"),
        n_coop=("n_coop", "sum")).reset_index()
    at.to_csv(f"{FIN}/agri_total_county_year.csv",
              index=False, encoding="utf-8-sig")

# QC 汇总
rows = []
for f in sorted(glob.glob(f"{OUTD}/qc_*.txt")):
    d = dict(re.findall(r"(\w+)=([^\n(]+)", open(f).read()))
    rows.append(d)
if rows:
    pd.DataFrame(rows).to_csv(f"{FIN}/firm_reg_qc_summary.csv",
                              index=False, encoding="utf-8-sig")
print("assembled:", "ci" if ci is not None else "-",
      "a3" if a3 is not None else "-")
