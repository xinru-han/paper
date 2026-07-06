#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 04: objective county-level policy/economy panel for the 12 sample counties
(unemployment-insurance participants, general-budget fiscal expenditure, employees).
Used to (a) validate the GWR text proxy and (b) provide an objective moderator."""
import pandas as pd, numpy as np, os, glob

BASE="/opt/data/research/Paper/新冠对务工的影响"; OUT=os.path.join(BASE,"revision","data")
codes=[130131,130224,130430,220421,220822,222403,350426,350629,350724,530425,532527,532627]

# ---- social insurance (unemployment insurance participants) ----
ins=pd.read_csv("/opt/data/research/数据/县级数据/extracted/gta/各县域社会保险与福利113112528(仅供中国农业科学院农业经济与发展研究所使用)/CNT_InsuranceWelf.csv",
                dtype=str)
ins.columns=[c.strip().strip('"').replace('﻿','') for c in ins.columns]
ins["CountyCode"]=pd.to_numeric(ins["CountyCode"],errors="coerce")
ins=ins[ins["CountyCode"].isin(codes)].copy()
ins["year"]=pd.to_numeric(ins["SgnYear"],errors="coerce")
for c in ["UnemployInsuranceNum","UrbPensionInsuranceNum","UrbMedInsuranceNum"]:
    ins[c]=pd.to_numeric(ins[c],errors="coerce")
ins=ins.rename(columns={"CountyCode":"xid"})[["xid","year","UnemployInsuranceNum",
        "UrbPensionInsuranceNum","UrbMedInsuranceNum"]]

# ---- fiscal expenditure & employees from long panel ----
lp=pd.read_parquet("/opt/data/research/数据/县级数据/output/county_panel_long_analysis.parquet",
     columns=["county_code","year","std_var","chosen_value"])
lp["county_code"]=pd.to_numeric(lp["county_code"],errors="coerce")
lp=lp[lp["county_code"].isin(codes)]
keep=["fiscal_expenditure_general_budget","total_employees","urban_employees_on_duty",
      "urban_employee_wage","rural_employees"]
lp=lp[lp["std_var"].isin(keep)]
wide=lp.pivot_table(index=["county_code","year"],columns="std_var",
                    values="chosen_value",aggfunc="first").reset_index()
wide=wide.rename(columns={"county_code":"xid"})

pol=ins.merge(wide,on=["xid","year"],how="outer").sort_values(["xid","year"])
pol=pol[(pol.year>=2010)&(pol.year<=2022)]
print("policy panel rows",len(pol))
print(pol.groupby("xid").apply(lambda g:g[["UnemployInsuranceNum",
     "fiscal_expenditure_general_budget","total_employees"]].notna().sum()).to_string())
pol.to_parquet(os.path.join(OUT,"county_policy.parquet"),index=False)
print("\nsaved county_policy.parquet")
print(pol[pol.year.between(2018,2022)][["xid","year","UnemployInsuranceNum",
      "fiscal_expenditure_general_budget"]].to_string())
