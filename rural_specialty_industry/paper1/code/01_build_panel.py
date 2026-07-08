#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper 1 面板：产业强镇交错DID。
单元=镇，年=2010-2024。结果=镇级夜间灯光(sum/mean)、淘宝村数、人口。
处理=产业强镇"批准建设"首年G(2018-2024，全批次)；控制=尚未/从未建设镇。
产出 paper1/output/town_year_panel.csv
"""
import sys
import pandas as pd
sys.path.insert(0, "/root/paper/rural_specialty_industry/common/code")
from admin_match import AdminMatcher, strip_prov, norm

E = "/root/paper/rural_specialty_industry/output"
CO = "/root/paper/rural_specialty_industry/common/output"
OUT = "/root/paper/rural_specialty_industry/paper1/output"
M = AdminMatcher()
Y0, Y1 = 2010, 2024

# ---------- 1. 强镇处理时点 G（全批次首年） ----------
e = pd.read_csv(f"{E}/policy_events_long.csv")
qz = e[(e.policy == "产业强镇") & (e.status == "批准建设")].copy()
qz["town_code"] = [M.town_code_from_addr(r.province, r.unit) for r in qz.itertuples()]
G = (qz.dropna(subset=["town_code"]).groupby("town_code")["batch_year"]
     .min().astype(int).rename("G"))
print("强镇处理镇(去重匹配):", len(G), " 批次分布:", G.value_counts().sort_index().to_dict())

# 认定时点（用于设计B：认定增量）
rd = e[(e.policy == "产业强镇") & (e.status.str.contains("认定", na=False))].copy()
# 认定名单为 省/地区/乡镇 结构
rd["town_code"] = [M.town_code(r.province, r.county if pd.notna(r.county) else "", r.unit)
                   for r in rd.itertuples()]
RD = set(rd.dropna(subset=["town_code"])["town_code"].astype(str))

# ---------- 2. 灯光面板（镇×年） ----------
lights = pd.read_stata("/root/data/数据/乡村产业数据/1986～2024年中国各省市区县、乡镇夜间灯光面板数据/"
                       "1986～2024年中国各省市区县、乡镇夜间灯光面板数据（田一禾版本）/"
                       "1986～2024年中国各乡镇夜间灯光面板数据.dta")
lights["town_code"] = lights["乡镇代码"].astype("Int64").astype(str).str[:9]
lights["year"] = lights["年份"].astype(int)
L = lights[(lights.year >= Y0) & (lights.year <= Y1)][
    ["town_code", "year", "mean", "sum"]].rename(
    columns={"mean": "light_mean", "sum": "light_sum"})
L = L.groupby(["town_code", "year"], as_index=False).agg(
    light_mean=("light_mean", "mean"), light_sum=("light_sum", "sum"))

# ---------- 3. 人口面板（镇×年，Landscan） ----------
pop = pd.read_stata("/root/data/数据/乡村产业数据/2000~2024年各省市区县、乡镇人口密度与人口数量面板数据/"
                    "2000~2024年各省市区县、乡镇人口密度与人口数量面板数据（Landscan 来源）/"
                    "2000~2024年各乡镇人口密度与人口数量数据(landscan来源).dta")
pop["town_code"] = pop["乡镇代码"].astype("Int64").astype(str).str[:9]
pop["year"] = pop["年份"].astype(int)
P = pop[(pop.year >= Y0) & (pop.year <= Y1)][["town_code", "year", "估算总人口_人"]].rename(
    columns={"估算总人口_人": "pop"})
P = P.groupby(["town_code", "year"], as_index=False)["pop"].sum()

# ---------- 4. 淘宝村数（镇×年） ----------
tb_path = ("/root/data/数据/乡村产业数据/全国淘宝村DID数据（2008-2024）/淘宝村DID.csv")
tb_rows = []
for ch in pd.read_csv(tb_path, usecols=["镇代码", "年份", "DID"], dtype=str, chunksize=1_000_000):
    ch["DID"] = pd.to_numeric(ch["DID"], errors="coerce").fillna(0)
    g = ch.groupby(["镇代码", "年份"], as_index=False)["DID"].sum()
    tb_rows.append(g)
TB = pd.concat(tb_rows).groupby(["镇代码", "年份"], as_index=False)["DID"].sum()
TB = TB.rename(columns={"镇代码": "town_code", "年份": "year", "DID": "n_taobao_village"})
TB["year"] = TB["year"].astype(int)
TB = TB[(TB.year >= Y0) & (TB.year <= Y1)]

# ---------- 5. 组装 ----------
base = L.merge(P, on=["town_code", "year"], how="left") \
        .merge(TB, on=["town_code", "year"], how="left")
base["n_taobao_village"] = base["n_taobao_village"].fillna(0)
base = base.merge(G, left_on="town_code", right_index=True, how="left")
base["treated"] = base["G"].notna().astype(int)
base["certified"] = base["town_code"].astype(str).isin(RD).astype(int)
# 事件时间（未处理设为极小，sunab用NA/Inf处理）
base["evt"] = base["year"] - base["G"]

base.to_csv(f"{OUT}/town_year_panel.csv", index=False, encoding="utf-8-sig")
print("面板行数:", len(base), " 处理镇:", base.loc[base.treated == 1, "town_code"].nunique(),
      " 认定镇:", base.loc[base.certified == 1, "town_code"].nunique(),
      " 灯光镇总数:", base.town_code.nunique())
