#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_process_firm_registration.py  <YEAR>
逐年处理工商注册明细（每个 <YEAR>.dta 约18GB，当年成立企业全量）：
分块读取 -> 解析注册资本 -> 标记涉农/合作社 -> 输出三张聚合/子集表，然后由调用方删除原始 .dta。

产出（写入 output/firm_reg/）：
  county_industry_YYYY.csv   省份×城市×区县×二级行业分类 -> n_firms, cap_wan, n_coop
  agri_county3_YYYY.csv      涉农子集 省份×城市×区县×三级行业分类 -> n_firms, cap_wan, n_coop
  agri_firms_geo_YYYY.parquet 涉农企业级子集(含经纬度/地址/资本/成立日期) 供日后落乡镇
  qc_YYYY.txt                质量核对

口径说明：地区用 省份/城市/区县（地址/信用代码口径，可靠）；经纬度/县代码为名称地理编码
产物(~1.5%错配)，仅在 agri 子集中保留原样供后续空间校验。
"""
import re
import sys
import os
import pandas as pd

YEAR = sys.argv[1]
SRC = f"/root/data/数据/乡村产业数据/工商注册数据/_tmp_extract/{YEAR}.dta"
OUTD = "/root/paper/rural_specialty_industry/output/firm_reg"
os.makedirs(OUTD, exist_ok=True)

AGRI_L1 = {"农、林、牧、渔业"}
AGRI_MANU_L2 = {"农副食品加工业", "食品制造业", "酒、饮料和精制茶制造业"}

USECOLS = ["省份", "城市", "区县", "企业类型", "注册资本", "成立日期",
           "一级行业分类", "二级行业分类", "三级行业分类",
           "注册地址", "经度", "纬度", "县代码"]

_num = re.compile(r"([0-9]+\.?[0-9]*)")


def parse_capital_wan(s):
    """把 '330万人民币' / '1亿人民币' / '500万' 解析为万元(人民币近似)。非RMB或缺失->NaN。"""
    if not isinstance(s, str) or not s.strip():
        return None
    if any(u in s for u in ("美元", "港元", "欧元", "英镑", "日元")):
        return None                       # 外币，先不折算
    m = _num.search(s)
    if not m:
        return None
    v = float(m.group(1))
    if "亿" in s:
        return v * 10000.0
    return v                              # 默认单位“万”


def is_agri(l1, l2):
    return (l1 in AGRI_L1) or (l2 in AGRI_MANU_L2)


ci_parts, a3_parts, geo_parts = [], [], []
tot = agri_tot = coop_tot = 0

it = pd.read_stata(SRC, columns=USECOLS, iterator=True, chunksize=500000)
for ch in it:
    ch["cap_wan"] = ch["注册资本"].map(parse_capital_wan)
    ch["is_coop"] = (ch["企业类型"].astype(str) == "农民专业合作社").astype(int)
    ch["agri"] = [is_agri(a, b) for a, b in
                  zip(ch["一级行业分类"], ch["二级行业分类"])]
    tot += len(ch)
    coop_tot += int(ch["is_coop"].sum())

    # A) 全行业 county×二级
    g = ch.groupby(["省份", "城市", "区县", "二级行业分类"], dropna=False).agg(
        n_firms=("agri", "size"), cap_wan=("cap_wan", "sum"),
        n_coop=("is_coop", "sum")).reset_index()
    ci_parts.append(g)

    # B) 涉农子集
    sub = ch[ch["agri"]]
    agri_tot += len(sub)
    if len(sub):
        g3 = sub.groupby(["省份", "城市", "区县", "三级行业分类"], dropna=False).agg(
            n_firms=("agri", "size"), cap_wan=("cap_wan", "sum"),
            n_coop=("is_coop", "sum")).reset_index()
        a3_parts.append(g3)
        geo_parts.append(sub[["省份", "城市", "区县", "三级行业分类", "企业类型",
                              "cap_wan", "成立日期", "注册地址",
                              "经度", "纬度", "县代码"]])


def combine_sum(parts, keys):
    df = pd.concat(parts, ignore_index=True)
    return df.groupby(keys, dropna=False).agg(
        n_firms=("n_firms", "sum"), cap_wan=("cap_wan", "sum"),
        n_coop=("n_coop", "sum")).reset_index()


ci = combine_sum(ci_parts, ["省份", "城市", "区县", "二级行业分类"])
ci["year"] = int(YEAR)
ci.to_csv(f"{OUTD}/county_industry_{YEAR}.csv", index=False, encoding="utf-8-sig")

if a3_parts:
    a3 = combine_sum(a3_parts, ["省份", "城市", "区县", "三级行业分类"])
    a3["year"] = int(YEAR)
    a3.to_csv(f"{OUTD}/agri_county3_{YEAR}.csv", index=False, encoding="utf-8-sig")
    geo = pd.concat(geo_parts, ignore_index=True)
    geo["year"] = int(YEAR)
    geo.to_pickle(f"{OUTD}/agri_firms_geo_{YEAR}.pkl.gz", compression="gzip")

with open(f"{OUTD}/qc_{YEAR}.txt", "w") as f:
    f.write(f"YEAR={YEAR}\n总企业={tot}\n涉农企业={agri_tot}"
            f"({agri_tot/tot:.3%})\n合作社={coop_tot}({coop_tot/tot:.3%})\n"
            f"county_industry行数={len(ci)}\n")
print(f"[{YEAR}] total={tot} agri={agri_tot} coop={coop_tot} -> done")
