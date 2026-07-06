#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 08: self-aggregate WAGE income (工资性收入) for every year from raw
component items (two questionnaire generations), since the pre-built
`totalincome` is empty before 2021. Farm/business net income and detailed
expenditure components for 2013-2020 are NOT in this dta (they live in the
IAED production/consumption sub-tables), so only wage income is buildable
consistently across all years. Output merged into analysis.csv as `wage_built`.
"""
import pyreadstat, glob, os, numpy as np, pandas as pd
BASE="/opt/data/research/Paper/新冠对务工的影响"; D=os.path.join(BASE,"revision","data")
SRC=glob.glob(os.path.join(BASE,"*.dta"))[0]

hg_wage=['hg02_1','hg03_1','hg04_1','hg05_1','hg06_1','hg07_1','hg08_1','hg09_1','hg10_1','hg11_1']  # 县内外各业打工(2013-2020)
new_wage=['本地从业工资性收入元','外出从业工资性收入元','乡村干部乡村教师工资收入元','其他工资性收入元']      # 2021-2022
use=['nid','year','cpi']+hg_wage+new_wage
df,_=pyreadstat.read_dta(SRC,usecols=use)
df=df.dropna(subset=['nid','year']).drop_duplicates(['nid','year'])

def rowsum(d,cols):
    return d[cols].apply(pd.to_numeric,errors='coerce').sum(axis=1,min_count=1)  # >=1 non-missing
df['wage_old']=rowsum(df,hg_wage)
df['wage_new']=rowsum(df,new_wage)
df['wage_built']=np.where(df.year<=2020, df['wage_old'], df['wage_new'])         # generation split by year
# real (CPI 1978=100); negatives->NA
df['wage_built_r']=np.where(df['wage_built']>=0, df['wage_built']/df['cpi']*100, np.nan)

out=df[['nid','year','wage_built','wage_built_r']].copy()
out.to_parquet(os.path.join(D,"income_built.parquet"),index=False)

# merge into analysis.csv
a=pd.read_csv(os.path.join(D,"analysis.csv"))
a=a.drop(columns=[c for c in ['wage_built','wage_built_r'] if c in a.columns],errors='ignore')
a=a.merge(out,on=['nid','year'],how='left')
a.to_csv(os.path.join(D,"analysis.csv"),index=False)
print("merged wage_built into analysis.csv; coverage by year:")
print(a[a.year<2023].groupby('year')['wage_built'].apply(lambda x:x.notna().sum()).to_string())
