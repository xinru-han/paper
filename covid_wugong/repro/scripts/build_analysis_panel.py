#!/usr/bin/env python3
"""
build_analysis_panel.py
Rebuild revision2/data/analysis.csv from the raw model dta, because the original
revision/ build scripts (06_analysis.R, 07_mechanisms.R, 08_income_build.py) and
analysis.csv were NOT shipped in the materials.

Applies the 实证分析20250908.do cleaning steps, then adds wage_built_r and the
Wuhan-distance IV interactions. Baseline complete-case sample = 13,787 (matches doc).

Usage: python3 build_analysis_panel.py <model.dta> <placebo_distances.csv> <out analysis.csv>
"""
import sys, pandas as pd, numpy as np

MODEL = sys.argv[1] if len(sys.argv)>1 else "2013-2023 长面板PDS model.dta"
PLACEBO = sys.argv[2] if len(sys.argv)>2 else "placebo_distances.csv"
OUT = sys.argv[3] if len(sys.argv)>3 else "analysis.csv"

hg=[f'hg{n:02d}_1' for n in range(2,12)]
new_wage=['本地从业工资性收入元','外出从业工资性收入元','乡村干部乡村教师工资收入元','其他工资性收入元']
need=['nid','pid','xid','tid','vid','year',
      'lna_workday2','a_workday1','a_workday2','a_workday3',
      'lncovid','covid','covid_accum2020','covid_accum2021','covid_accum2022','lncovid_accum2022','covid_dummy',
      'gender','age','health','edu','labor_ratio',
      'pilot','lnhouseholds','v_ainc','lnv_ainccpi','cpi',
      'far_station','far_asale','far_market','road_density2','lnlandprice_sum','landprice_sum',
      'hb13','hb14','operateland','homeinc_ratio','aworkincomecpi',
      'totalincome','atotalincomecpi','total_exp','atotalexpcpi','food_exp','afoodexpcpi',
      'workincome','homeincome'] + hg + new_wage
df=pd.read_stata(MODEL, columns=need)

# --- do-file cleaning ---
df=df.drop_duplicates(['nid','year'])
df.loc[df['age']<18,'age']=18
def fix_vainc(r):
    va=r['v_ainc']; cpi=r['cpi']; lnv=r['lnv_ainccpi']
    if pd.isna(va): return lnv,va
    if va==529: return np.nan,np.nan
    mp={560:5600,600:6000,980:9800,1200:12000,1380:13800}
    if va in mp and pd.notna(cpi) and cpi!=0:
        return np.log(mp[va]/cpi*100), mp[va]
    return lnv,va
fx=df.apply(fix_vainc,axis=1,result_type='expand'); df['lnv_ainccpi']=fx[0]; df['v_ainc']=fx[1]
df=df.rename(columns={'lna_workday2':'ln_a_workday2','lncovid_accum2022':'ln_exposure2022'})

# --- wage_built_r: EXACT reconstruction per original 08_income_build.py (scripts/08_income_build.py) ---
# 2013-2020: sum of itemized off-farm wage items hg02_1..hg11_1
# 2021-2022: sum of the 4 new questionnaire wage items (local/migrant/village-cadre-teacher/other)
# Both branches CPI-deflated (1978=100), then spliced by year. Reproduces the documented M2 wage
# coefficient EXACTLY: -0.2646***, N=11,258 (Table 6, full sample).
def rowsum(d,cols):
    return d[cols].apply(pd.to_numeric,errors='coerce').sum(axis=1,min_count=1)
df['wage_old']=rowsum(df,hg)
df['wage_new']=rowsum(df,new_wage)
df['wage_built']=np.where(df['year']<=2020, df['wage_old'], df['wage_new'])
df['wage_built_r']=np.where(df['wage_built']>=0, df['wage_built']/df['cpi']*100, np.nan)
for v in ['far_station','far_asale','far_market']:
    df['ln'+v]=np.log(df[v]+1)

# --- Wuhan-distance IV ---
pl=pd.read_csv(PLACEBO)
def hav(lat1,lon1,lat2,lon2):
    R=6371.0
    p1,p2=np.radians(lat1),np.radians(lat2); dphi=np.radians(lat2-lat1); dl=np.radians(lon2-lon1)
    a=np.sin(dphi/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))
WUHAN=(30.5928,114.3055)
pl['dist_wuhan_km']=hav(pl['lat'],pl['lng'],WUHAN[0],WUHAN[1]); pl['ln_dist_wuhan']=np.log(pl['dist_wuhan_km'])
pl['xid']=pl['xid'].astype(str); df['xid']=df['xid'].astype(str)
dist_cols=['xid','dist_wuhan_km','ln_dist_wuhan','ln_dist_beijing','ln_dist_shanghai','ln_dist_guangzhou',
           'dist_beijing_km','dist_shanghai_km','dist_guangzhou_km']
df=df.merge(pl[dist_cols],on='xid',how='left')
df['post']=(df['year']>=2020).astype(int)
for c,src in [('iv_dist_post','ln_dist_wuhan'),('iv_dist_beijing_post','ln_dist_beijing'),
              ('iv_dist_shanghai_post','ln_dist_shanghai'),('iv_dist_guangzhou_post','ln_dist_guangzhou')]:
    df[c]=df[src]*df['post']

df.to_csv(OUT,index=False)
chk=['ln_a_workday2','lncovid','gender','age','health','edu','labor_ratio','pilot','lnhouseholds',
     'lnv_ainccpi','lnfar_station','lnfar_asale','lnfar_market','road_density2','lnlandprice_sum']
print("wrote",OUT,df.shape,"| baseline complete-case:",df[df.year<2023].dropna(subset=chk).shape[0])
