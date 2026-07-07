# -*- coding: utf-8 -*-
"""解析央视《成品粮零售价格》旬报(2005-2024) → 全国品种×月价格信号
粳米→rice*, 面粉→wheat, 玉米粉→corn (国家层面年内信号, 全作物类型共享)
输出: data/processed/retail_price_features.csv (crop_group×year)
"""
import glob, os, re, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
SRC = "/root/data/数据/央视数据/成品粮零售---2005年1月----2024年5月30日(2005年1月预警系统)"
OUT = "/root/grain_profit_warning/data/processed"

VAR_MAP = {"粳米": "rice", "面粉": "wheat", "玉米粉": "corn", "籼米": "rice"}

def norm(df):
    df = df.rename(columns=lambda c: str(c).strip())
    cols = {c: c for c in df.columns}
    need_num = [c for c in df.columns if "零售价格" in c or c == "价格"]
    if "期号" not in df.columns or "品种" not in df.columns or not need_num:
        return None
    d = df[["期号", "品种"] + need_num[:1]].copy()
    d.columns = ["period", "variety", "price"]
    d["period"] = d["period"].astype(str).str.extract(r"(\d{8})")[0]
    d = d.dropna(subset=["period"])
    d["price"] = pd.to_numeric(d["price"], errors="coerce")
    d = d.dropna(subset=["price"])
    d = d[(d["price"] > 0.5) & (d["price"] < 20)]  # 元/500克
    d["variety"] = d["variety"].astype(str).str.strip()
    d["grp"] = None
    for k, v in VAR_MAP.items():
        d.loc[d["variety"].str.contains(k, na=False), "grp"] = v
    d = d.dropna(subset=["grp"])
    d["year"] = d["period"].str[:4].astype(int)
    d["month"] = d["period"].str[4:6].astype(int)
    return d[["grp", "year", "month", "price"]]

frames = []
for f in sorted(glob.glob(os.path.join(SRC, "*"))):
    base = os.path.basename(f)
    try:
        if f.endswith(".txt"):
            raw = pd.read_csv(f, sep=r"\s+", engine="python", skiprows=[1],
                              dtype=str, on_bad_lines="skip")
            d = norm(raw)
        elif f.endswith((".xls", ".xlsx")):
            try:
                raw = pd.read_excel(f)
            except Exception:
                raw = pd.read_html(f)[0]
            d = norm(raw)
        else:
            continue
        if d is None or d.empty:
            print("SKIP", base)
            continue
        frames.append(d)
        print("OK", base, len(d))
    except Exception as e:
        print("FAIL", base, repr(e)[:80])

m = pd.concat(frames, ignore_index=True)
m = m.groupby(["grp", "year", "month"])["price"].mean().reset_index()
m.to_csv(os.path.join(OUT, "retail_price_monthly.csv"), index=False)
print("monthly:", m.shape, m.year.min(), m.year.max())

def feats(g):
    pre = g.loc[g["month"].between(1, 9), "price"].mean()   # 秋收前信号
    q1 = g.loc[g["month"].between(1, 3), "price"].mean()
    return pd.Series({"rp_pre_mean": pre, "rp_q1_mean": q1})

a = m.groupby(["grp", "year"]).apply(feats).reset_index().sort_values(["grp", "year"])
a["rp_pre_yoy"] = a.groupby("grp")["rp_pre_mean"].pct_change()
a["rp_q1_yoy"] = a.groupby("grp")["rp_q1_mean"].pct_change()
a.to_csv(os.path.join(OUT, "retail_price_features.csv"), index=False)
print("annual:", a.shape)
print(a.groupby("grp")["year"].agg(["min", "max", "count"]))
