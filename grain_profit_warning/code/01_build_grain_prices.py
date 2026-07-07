# -*- coding: utf-8 -*-
"""解析发改委《主产区原粮购销价格监测旬报》(2005-2025, HTML伪xls)
输出: 省×品种×年 的收购价格特征 (data/processed/grain_price_features.csv)
特征: 全年均价、生长季(4-9月)均价、播前(1-4月)均价、同比变化、年内波动率
"""
import glob, os, re, warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

RAW_DIR = "/root/grain_profit_warning/data/raw_grain_price/主产区原粮购销价格监测旬报子任务2005-2025"
OUT = "/root/grain_profit_warning/data/processed"
os.makedirs(OUT, exist_ok=True)

# 品种 → 面板作物映射（与 yearbook_long 的 crop 对齐）
CROP_MAP = {
    "玉米": "corn",
    "白小麦": "wheat", "红小麦": "wheat", "混合麦": "wheat", "小麦": "wheat",
    "大豆": "soybean",
    "早籼稻": "rice_early_indica", "中籼稻": "rice_mid_indica",
    "晚籼稻": "rice_late_indica", "粳稻": "rice_japonica",
    "稻谷": "rice_mid_indica",
}

rows = []
files = sorted(glob.glob(os.path.join(RAW_DIR, "*.xls")))
print(f"{len(files)} files")
for f in files:
    try:
        tabs = pd.read_html(f)
    except Exception as e:
        print("FAIL", os.path.basename(f), e)
        continue
    d = tabs[0]
    need = ["期号", "监测点", "品种", "混等平均收购价格", "标准品收购价格"]
    if not all(c in d.columns for c in need):
        print("SKIP cols", os.path.basename(f), d.columns.tolist()[:8])
        continue
    d = d[need].copy()
    d["price"] = pd.to_numeric(d["混等平均收购价格"], errors="coerce")
    d["price"] = d["price"].fillna(pd.to_numeric(d["标准品收购价格"], errors="coerce"))
    d = d.dropna(subset=["price"])
    d = d[(d["price"] > 20) & (d["price"] < 600)]  # 元/50公斤 合理区间
    d["期号"] = d["期号"].astype(str).str.extract(r"(\d{8})")[0]
    d = d.dropna(subset=["期号"])
    d["year"] = d["期号"].str[:4].astype(int)
    d["month"] = d["期号"].str[4:6].astype(int)
    d["province"] = d["监测点"].astype(str).str.extract(r"全国-([^省市区-]+)")[0]
    d["crop"] = d["品种"].astype(str).str.strip().map(CROP_MAP)
    d = d.dropna(subset=["province", "crop"])
    # 先聚合到 省×crop×年×月，压缩体量
    g = d.groupby(["province", "crop", "year", "month"])["price"].mean().reset_index()
    rows.append(g)
    print("OK", os.path.basename(f), len(d))

m = pd.concat(rows, ignore_index=True)
m = m.groupby(["province", "crop", "year", "month"])["price"].mean().reset_index()
m.to_csv(os.path.join(OUT, "grain_price_monthly.csv"), index=False)
print("monthly:", m.shape)

# 年度特征
def feats(g):
    full = g["price"].mean()
    grow = g.loc[g["month"].between(4, 9), "price"].mean()
    pre = g.loc[g["month"].between(1, 4), "price"].mean()
    vol = g["price"].std() / full if full else np.nan
    return pd.Series({"gp_year_mean": full, "gp_grow_mean": grow,
                      "gp_pre_mean": pre, "gp_cv": vol})

a = m.groupby(["province", "crop", "year"]).apply(feats).reset_index()
a = a.sort_values(["province", "crop", "year"])
a["gp_yoy"] = a.groupby(["province", "crop"])["gp_year_mean"].pct_change()
a["gp_pre_yoy"] = a.groupby(["province", "crop"])["gp_pre_mean"].pct_change()
a.to_csv(os.path.join(OUT, "grain_price_features.csv"), index=False)
print("annual:", a.shape)
print(a.groupby("crop")["year"].agg(["min", "max", "count"]))
