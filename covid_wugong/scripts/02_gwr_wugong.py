#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 02: count '务工' mentions in county government work reports (GWR) for the
12 sample counties, 2013-2022; also extract each county's prefecture (city) code/name."""
import pandas as pd, numpy as np, os

BASE="/opt/data/research/Paper/新冠对务工的影响"; OUT=os.path.join(BASE,"revision","data")
GWR="/opt/data/research/文本分析/政府工作报告/政府工作报告.csv"

codes = [130131,130224,130430,220421,220822,222403,350426,350629,350724,530425,532527,532627]
codes_s = set(str(c) for c in codes)

g = pd.read_csv(GWR, dtype=str, low_memory=False)
g["区县代码"]=g["区县代码"].str.strip()
sub = g[g["区县代码"].isin(codes_s)].copy()
sub["年份"]=pd.to_numeric(sub["年份"],errors="coerce")
sub=sub[(sub["年份"]>=2013)&(sub["年份"]<=2022)]
sub["内容"]=sub["内容"].fillna("")
sub["wugong"]=sub["内容"].str.count("务工")

# collapse to county-year (a report may be split across rows)
rep = sub.groupby(["区县代码","县名","市名","市代码","省名","年份"],as_index=False).agg(
        wugong=("wugong","sum"))
# some county-years have multiple report rows -> already summed; report count:
rep["xid"]=rep["区县代码"].astype(int)
rep=rep.rename(columns={"年份":"year","市代码":"city_code","市名":"city_name"})
print(rep[["xid","县名","city_name","city_code","year","wugong"]].to_string())
print("county-year rows:",len(rep),"counties:",rep.xid.nunique(),
      "years:",sorted(rep.year.unique()))

rep.to_parquet(os.path.join(OUT,"gwr_wugong.parquet"),index=False)

# city crosswalk (county -> prefecture)
cw = rep.drop_duplicates("xid")[["xid","县名","省名","city_name","city_code"]]
cw.to_parquet(os.path.join(OUT,"county_city_xwalk.parquet"),index=False)
print("\ncity crosswalk:\n",cw.to_string())
