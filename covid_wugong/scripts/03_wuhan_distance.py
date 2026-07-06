#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 03: geocode the 12 sample counties via Baidu, compute great-circle
distance to Wuhan (initial COVID epicentre) as an instrument for exposure."""
import requests, os, time, math, pandas as pd, numpy as np

BASE="/opt/data/research/Paper/新冠对务工的影响"; OUT=os.path.join(BASE,"revision","data")
AK="7mDHDde2n5iwohEC92U5XS6EG0ib5phG"

counties = {
 130131:("河北省","平山县"),130224:("河北省","滦南县"),130430:("河北省","邱县"),
 220421:("吉林省","东丰县"),220822:("吉林省","通榆县"),222403:("吉林省","敦化市"),
 350426:("福建省","尤溪县"),350629:("福建省","华安县"),350724:("福建省","松溪县"),
 530425:("云南省","易门县"),532527:("云南省","泸西县"),532627:("云南省","广南县"),
}

def geocode(addr):
    r=requests.get("https://api.map.baidu.com/geocoding/v3/",
        params={"address":addr,"output":"json","ak":AK},timeout=15).json()
    if r.get("status")==0:
        loc=r["result"]["location"]; return loc["lng"],loc["lat"]
    return None,None

def haversine(lo1,la1,lo2,la2):
    R=6371.0; p=math.pi/180
    dlo=(lo2-lo1)*p; dla=(la2-la1)*p
    a=math.sin(dla/2)**2+math.cos(la1*p)*math.cos(la2*p)*math.sin(dlo/2)**2
    return 2*R*math.asin(math.sqrt(a))

wlng,wlat=geocode("湖北省武汉市")
rows=[]
for code,(prov,name) in counties.items():
    lng,lat=geocode(prov+name); time.sleep(0.3)
    d=haversine(wlng,wlat,lng,lat) if lng else np.nan
    rows.append(dict(xid=code,省名=prov,县名=name,lng=lng,lat=lat,dist_wuhan_km=d))
    print(code,name,round(d,1) if d==d else "NA")

df=pd.DataFrame(rows)
df["ln_dist_wuhan"]=np.log(df["dist_wuhan_km"])
df.to_parquet(os.path.join(OUT,"wuhan_distance.parquet"),index=False)
print("\nWuhan @",round(wlng,4),round(wlat,4))
print(df[["xid","县名","dist_wuhan_km"]].to_string())
