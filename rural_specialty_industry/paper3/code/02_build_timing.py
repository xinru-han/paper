#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper 3 时序数据：培育 vs 追认。
对每个镇输出强镇建设批次年(全批次2018-2024)与十亿元镇/亿元村进入年，
计算事件时间 gap = 强镇建设年 - 进入年。
  gap<0：政策先于进入（培育）；gap>=0：进入先于/同期政策（追认）。
产出 paper3/output/timing_qz_vs_entry.csv
"""
import sys
import pandas as pd
sys.path.insert(0, "/root/paper/rural_specialty_industry/common/code")
from admin_match import AdminMatcher

E = "/root/paper/rural_specialty_industry/output"
CO = "/root/paper/rural_specialty_industry/common/output"
OUT = "/root/paper/rural_specialty_industry/paper3/output"
M = AdminMatcher()

county_ref = pd.read_csv(f"{CO}/name2code_county.csv", dtype=str)
code2cty = dict(zip(county_ref["区县代码"], county_ref["county_std"]))

# 强镇全批次 → 镇代码（首次建设年）
e = pd.read_csv(f"{E}/policy_events_long.csv")
qz = e[(e.policy == "产业强镇") & (e.status == "批准建设")].copy()
qz["town_code"] = [M.town_code_from_addr(r.province, r.unit) for r in qz.itertuples()]
qz_year = (qz.dropna(subset=["town_code"]).groupby("town_code")["batch_year"]
           .min().rename("qz_year"))

# 十亿元镇/亿元村进入年
o = pd.read_csv(f"{E}/superstar_outcomes.csv")


def tcode(r):
    cc = M.county_code(r["province"], r["city_county"])
    t = None
    if cc is not None:
        t = M.town_code(r["province"], code2cty.get(str(cc), ""), r["town"])
    return t or M.town_code(r["province"], "", r["town"])


o["town_code"] = [tcode(r) for _, r in o.iterrows()]
ten = (o[o.kind == "十亿元镇"].dropna(subset=["town_code"])
       .groupby("town_code")["list_year"].min().rename("ten_year"))
yi = (o[o.kind == "亿元村"].dropna(subset=["town_code"])
      .groupby("town_code")["list_year"].min().rename("yi_year"))

df = pd.concat([qz_year, ten, yi], axis=1).reset_index()
df["gap_ten"] = df["qz_year"] - df["ten_year"]      # <0 培育, >=0 追认
df["gap_yi"] = df["qz_year"] - df["yi_year"]
df.to_csv(f"{OUT}/timing_qz_vs_entry.csv", index=False, encoding="utf-8-sig")

both = df.dropna(subset=["qz_year", "ten_year"])
print(f"强镇∩十亿元镇 镇数={len(both)}")
print("gap_ten 分布(强镇年-进入年):")
print(both["gap_ten"].value_counts().sort_index())
print(f"培育(gap<0)占比={ (both.gap_ten<0).mean():.3f} "
      f"追认(gap>=0)占比={ (both.gap_ten>=0).mean():.3f}")
