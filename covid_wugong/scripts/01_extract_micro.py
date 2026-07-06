#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 01: extract needed columns from the 581MB IAED panel dta,
construct outcome / covid / control / mechanism variables, save compact parquet.
Author: revision pipeline (COVID x migrant labor)."""
import pyreadstat, glob, os, numpy as np, pandas as pd

BASE = "/opt/data/research/Paper/新冠对务工的影响"
OUT  = os.path.join(BASE, "revision", "data")
SRC  = glob.glob(os.path.join(BASE, "*.dta"))[0]

ids   = ["pid","xid","tid","vid","nid","year","省名","县名","乡镇名"]
ylist = ["a_workday1","a_workday2","a_workday3"]
covid = ["covid","lncovid","covid_accum2020","covid_accum2021","covid_accum2022",
         "lncovid_accum2022","covid_dummy","covid_pop"]
light = ["light","light_pc","lnlight_pc"]
ctrl  = ["gender","age","health","edu","labor_ratio","pilot","households",
         "lnhouseholds","v_ainc","lnv_ainccpi","far_station","far_asale","far_market",
         "road_density2","landprice_sum","lnlandprice_sum","operateland"]
mech  = ["totalincome","atotalincomecpi","lnatotalincomecpi",
         "total_exp","atotalexpcpi","lnatotalexpcpi","food_exp","afoodexpcpi",
         "workincome","homeincome","cpi",
         "hb13","hb14","hb15","hb16","hb17","hb18"]

want = ids+ylist+covid+light+ctrl+mech
df, meta = pyreadstat.read_dta(SRC, metadataonly=True)
have = [c for c in want if c in meta.column_names]
missing = [c for c in want if c not in meta.column_names]
print("MISSING:", missing)

df, meta = pyreadstat.read_dta(SRC, usecols=have)
print("loaded", df.shape)

# ---- clean ids ----
for c in ["pid","xid","tid","vid","nid","year"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["nid","year"]).copy()
df = df.drop_duplicates(subset=["nid","year"])
df["age"] = df["age"].clip(lower=18)

# ---- mechanism constructs (deflate by cpi, base 1978=100) ----
def dfl(x):
    return df[x]/df["cpi"]*100 if x in df else np.nan
# liquid precautionary savings = deposits + cash
for c in ["hb13","hb14","hb15","hb16","hb17","hb18"]:
    if c in df: df[c] = pd.to_numeric(df[c], errors="coerce")
df["savings_liq"]   = df.get("hb13",np.nan).fillna(0) + df.get("hb14",np.nan).fillna(0)
df["savings_liq_r"] = df["savings_liq"]/df["cpi"]*100
df["net_lending"]   = (df.get("hb16",np.nan).fillna(0) + df.get("hb17",np.nan).fillna(0)
                       - df.get("hb18",np.nan).fillna(0))
# savings rate = (income - consumption)/income  (cpi-real levels cancel)
inc = df.get("atotalincomecpi"); exp = df.get("atotalexpcpi")
df["saving_rate"] = np.where((inc.notna())&(inc>0), 1 - exp/inc, np.nan)
df["saving_rate"] = df["saving_rate"].clip(-2,1)
# logs (add 1)
for v in ["savings_liq_r","atotalexpcpi","afoodexpcpi"]:
    if v in df: df["ln_"+v] = np.log(df[v].clip(lower=0)+1)

# ---- event-study exposure: time-invariant cumulative-by-2022 intensity ----
expo = (df[df.year==2022].groupby("xid")["covid_accum2022"].max())
df["exposure2022"] = df["xid"].map(expo)
df["ln_exposure2022"] = np.log(df["exposure2022"].fillna(0)+1)

# pre-covid household off-farm participation dummy (2019 baseline)
w19 = df[df.year==2019].set_index("nid")["a_workday2"]
df["work19"] = df["nid"].map(w19)
df["work_dum"] = (df["work19"]>0).astype(float)

# outcome logs
for v in ["a_workday1","a_workday2","a_workday3"]:
    df["ln_"+v] = np.log(df[v].clip(lower=0)+1)

# availability of savings vars by year (diagnostic)
diag = df.groupby("year")[["hb13","savings_liq_r","saving_rate","atotalexpcpi"]].apply(
    lambda g: g.notna().mean())
print(diag)

keep = [c for c in df.columns]
df.to_parquet(os.path.join(OUT,"micro_analysis.parquet"), index=False)
print("saved", os.path.join(OUT,"micro_analysis.parquet"), df.shape)
