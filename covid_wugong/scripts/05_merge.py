#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 05: merge micro panel + GWR word freq + Wuhan distance + county fiscal panel
into a single analysis CSV for the R econometrics."""
import pandas as pd, numpy as np, os

BASE="/opt/data/research/Paper/新冠对务工的影响"; D=os.path.join(BASE,"revision","data")
m=pd.read_parquet(os.path.join(D,"micro_analysis.parquet"))
gwr=pd.read_parquet(os.path.join(D,"gwr_wugong.parquet"))[["xid","year","wugong"]]
wd=pd.read_parquet(os.path.join(D,"wuhan_distance.parquet"))[["xid","dist_wuhan_km","ln_dist_wuhan"]]
pol=pd.read_parquet(os.path.join(D,"county_policy.parquet"))[["xid","year",
     "fiscal_expenditure_general_budget"]]

m["xid"]=m["xid"].astype(int); m["year"]=m["year"].astype(int)
for df in (gwr,pol): df["xid"]=df["xid"].astype(int); df["year"]=df["year"].astype(int)

df=m.merge(gwr,on=["xid","year"],how="left").merge(wd,on="xid",how="left")\
    .merge(pol,on=["xid","year"],how="left")

# post indicator & instrument interaction
df["post"]=(df["year"]>=2020).astype(int)
df["iv_dist_post"]=df["ln_dist_wuhan"]*df["post"]

# GWR proxy: pre-2020 mean per county (predetermined -> avoids reverse causality)
pre=df[df.year<2020].groupby("xid")["wugong"].mean()
df["wugong_pre"]=df["xid"].map(pre).fillna(0)
df["wugong"]=df["wugong"].fillna(0)

# objective fiscal moderator: within-county log, and pre-2020 mean (predetermined capacity)
df["ln_fiscal"]=np.log(df["fiscal_expenditure_general_budget"].clip(lower=1))
fpre=df[df.year<2020].groupby("xid")["ln_fiscal"].mean()
df["ln_fiscal_pre"]=df["xid"].map(fpre)

# centered interactions (mirror original 'center' approach)
for v in ["lncovid","wugong","wugong_pre","ln_fiscal","ln_fiscal_pre"]:
    df["c_"+v]=df[v]-df[v].mean(skipna=True)
df["covid_x_wugong"]     = df["c_lncovid"]*df["c_wugong"]
df["covid_x_wugongpre"]  = df["c_lncovid"]*df["c_wugong_pre"]
df["covid_x_fiscal"]     = df["c_lncovid"]*df["c_ln_fiscal"]
df["covid_x_fiscalpre"]  = df["c_lncovid"]*df["c_ln_fiscal_pre"]

# event-study relative-year interaction handled in R via i(year, ln_exposure2022)
out=os.path.join(D,"analysis.csv")
df.to_csv(out,index=False)
print("saved",out,df.shape)
print("nonmissing key vars:")
for v in ["ln_a_workday2","lncovid","ln_exposure2022","ln_dist_wuhan","saving_rate",
          "ln_atotalexpcpi","light_pc","wugong_pre","ln_fiscal"]:
    print(f"  {v}: {df[v].notna().sum()}")
