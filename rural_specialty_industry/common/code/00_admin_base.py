#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_admin_base.py — 三篇共用行政区划编码底座
从淘宝村DID（全国村庄×年份全集，含省市县镇村五级代码）提取：
  town_universe.csv    镇宇宙：省代码/省/城市代码/城市/区县代码/区县名称/镇代码/镇  (去重)
  county_universe.csv  县宇宙：省/城市/区县 及 区县代码  (去重)
  name2code_town.csv   (省,县,镇)标准名 -> 镇代码  匹配键（供政策名单落码）
  name2code_county.csv (省,市,县)标准名 -> 区县代码
另附常用清洗函数库 admin_utils（被下游import）。
"""
import re
import pandas as pd

TAOBAO = ("/root/data/数据/乡村产业数据/全国淘宝村DID数据（2008-2024）/淘宝村DID.csv")
OUT = "/root/paper/rural_specialty_industry/common/output"

USE = ["省代码", "省", "城市代码", "城市", "区县代码", "区县名称",
       "镇代码", "镇", "村", "村代码"]

# 只读一届年份即可拿到全集（村宇宙每年重复）——用2020年切片
rows = []
for ch in pd.read_csv(TAOBAO, usecols=USE + ["年份"], dtype=str, chunksize=1_000_000):
    ch = ch[ch["年份"] == "2020"]
    if len(ch):
        rows.append(ch[USE])
uni = pd.concat(rows, ignore_index=True).drop_duplicates()
print("村级记录(2020切片):", len(uni))

town = (uni[["省代码", "省", "城市代码", "城市", "区县代码", "区县名称", "镇代码", "镇"]]
        .drop_duplicates().reset_index(drop=True))
county = (uni[["省代码", "省", "城市代码", "城市", "区县代码", "区县名称"]]
          .drop_duplicates().reset_index(drop=True))
town.to_csv(f"{OUT}/town_universe.csv", index=False, encoding="utf-8-sig")
county.to_csv(f"{OUT}/county_universe.csv", index=False, encoding="utf-8-sig")
uni[["村代码", "村", "镇代码", "镇", "区县代码", "区县名称", "省"]].to_csv(
    f"{OUT}/village_universe.csv", index=False, encoding="utf-8-sig")
print("镇宇宙:", len(town), " 县宇宙:", len(county), " 村宇宙:", len(uni))


# --------- 名称标准化：去后缀便于跨源匹配 ---------
def norm(s):
    if pd.isna(s):
        return ""
    s = re.sub(r"\s+", "", str(s))
    return s


def strip_prov(s):
    s = norm(s)
    return re.sub(r"(省|市|自治区|特别行政区|维吾尔|壮族|回族|)$", "", s)


town["province_std"] = town["省"].map(strip_prov)
town["county_std"] = town["区县名称"].map(norm)
town["town_std"] = town["镇"].map(norm)
town[["province_std", "county_std", "town_std", "镇代码", "区县代码", "省", "区县名称", "镇"]] \
    .to_csv(f"{OUT}/name2code_town.csv", index=False, encoding="utf-8-sig")

county["province_std"] = county["省"].map(strip_prov)
county["city_std"] = county["城市"].map(norm)
county["county_std"] = county["区县名称"].map(norm)
county[["province_std", "city_std", "county_std", "区县代码", "省", "城市", "区县名称"]] \
    .to_csv(f"{OUT}/name2code_county.csv", index=False, encoding="utf-8-sig")
print("已写 name2code 键表")
