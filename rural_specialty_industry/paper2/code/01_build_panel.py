#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper 2 面板：认证叠加(certification stacking)。
单元 = 县 × 品类 × 年(2010-2023)。
认证：地理标志/名特优新/品牌目录/特优区（各映射到品类，落县代码）。
结果：涉农新增企业数（agri_county3 三级行业→品类聚合）。
产出 paper2/output/county_cat_panel.csv, cert_events.csv
"""
import re
import sys
import pandas as pd
sys.path.insert(0, "/root/paper/rural_specialty_industry/common/code")
from admin_match import AdminMatcher, strip_prov, norm

E = "/root/paper/rural_specialty_industry/output"
CO = "/root/paper/rural_specialty_industry/common/output"
OUT = "/root/paper/rural_specialty_industry/paper2/output"
M = AdminMatcher()

# ---------- 品类映射（关键词优先级从上到下） ----------
CAT_RULES = [
    ("茶", ["茶"]),
    ("水产", ["鱼", "虾", "蟹", "水产", "海参", "贝", "鲍", "螺", "蚌", "鳖", "鳝", "蚝", "牡蛎", "海带", "紫菜"]),
    ("畜禽", ["猪", "牛", "羊", "鸡", "鸭", "鹅", "禽", "畜", "蛋", "奶", "乳", "蜂", "驴", "兔", "鸽", "肉"]),
    ("水果", ["苹果", "梨", "桃", "柑", "橘", "橙", "柚", "枣", "葡萄", "果", "杧果", "芒果", "荔枝", "龙眼",
             "枇杷", "杨梅", "猕猴桃", "石榴", "柿", "樱桃", "西瓜", "甜瓜", "香蕉", "菠萝", "莓"]),
    ("蔬菜食用菌", ["菜", "菌", "菇", "耳", "姜", "蒜", "葱", "椒", "藕", "笋", "萝卜", "土豆", "马铃薯",
                 "山药", "芋", "豆角", "番茄", "西红柿", "黄瓜", "茄", "园艺"]),
    ("粮油", ["稻", "米", "麦", "玉米", "谷", "粮", "豆", "薯", "油", "花生", "芝麻", "菜籽", "杂粮", "高粱", "荞"]),
    ("中药材", ["药", "参", "枸杞", "黄芪", "当归", "党参", "三七", "天麻", "陈皮", "菊", "花椒", "桂", "茯苓"]),
    ("加工食品", ["加工", "制品", "制造", "食品", "酒", "醋", "酱", "糖", "饮料", "面", "粉", "干", "腌", "腊"]),
]
IND_RULES = [
    ("茶", ["茶"]),
    ("水产", ["水产", "渔", "捕捞", "养殖"]),   # 养殖含水产/畜牧，后接畜禽细分
    ("畜禽", ["牲畜", "家禽", "畜牧", "猪", "牛", "羊", "禽", "饲养", "屠宰", "蛋", "奶", "乳"]),
    ("水果", ["水果", "园林水果", "水果种植"]),
    ("蔬菜食用菌", ["蔬菜", "食用菌", "园艺", "花卉"]),
    ("粮油", ["谷物", "豆", "薯", "油料", "棉", "糖料", "粮食"]),
    ("中药材", ["中药材", "药材"]),
    ("加工食品", ["农副食品加工", "食品制造", "酒", "饮料", "精制茶"]),
    ("农业服务", ["农业专业", "辅助性", "管护", "改培", "经营"]),
]


def map_cat(text, rules):
    t = norm(text)
    for cat, kws in rules:
        if any(k in t for k in kws):
            return cat
    return None


# ---------- 认证事件 → (县代码, 品类, 年) ----------
e = pd.read_csv(f"{E}/policy_events_long.csv")
cert = []


def add_cert(policy, county_code, cat, year):
    if county_code and cat and pd.notna(year):
        cert.append((policy, str(county_code), cat, int(year)))


# GI：holder扫县 + product定品类
for r in e[e.policy == "地理标志"].itertuples():
    p = strip_prov(r.province)
    text = norm(r.holder) + norm(r.product)
    ccode = None
    for cn in sorted(M.county_names.get(p, ()), key=len, reverse=True):
        if cn and len(cn) >= 2 and cn in text:
            ccode = M.pc2code.get((p, cn)); break
    add_cert("GI", ccode, map_cat(r.product, CAT_RULES), r.batch_year)

# 名特优新：有县区 + product
for r in e[e.policy == "名特优新"].itertuples():
    if pd.isna(r.county):
        continue
    codes = M.county_codes_flex(r.province, r.county)
    for c in codes:
        add_cert("名特优新", c, map_cat(r.product, CAT_RULES), r.batch_year)

# 特优区：county + product
for r in e[e.policy == "特优区"].itertuples():
    if pd.isna(r.county):
        continue
    for c in M.county_codes_flex(r.province, r.county):
        add_cert("特优区", c, map_cat(r.product, CAT_RULES), r.batch_year)

# 品牌目录：地区(county) + product
for r in e[e.policy == "品牌目录"].itertuples():
    if pd.isna(r.county):
        continue
    for c in M.county_codes_flex(r.province, r.county):
        add_cert("品牌目录", c, map_cat(r.product, CAT_RULES), r.batch_year)

cert = pd.DataFrame(cert, columns=["policy", "county_code", "cat", "year"])
cert = cert.dropna(subset=["cat"])
cert.to_csv(f"{OUT}/cert_events.csv", index=False, encoding="utf-8-sig")
print("认证事件(落县×品类):", len(cert))
print(cert.groupby("policy").size().to_dict())
print("品类分布:", cert.cat.value_counts().to_dict())

# ---------- 结果：涉农企业 三级行业→品类 ----------
a3 = pd.read_csv(f"{E}/agri_county3_panel_2010_2023.csv")
a3["cat"] = a3["三级行业分类"].map(lambda s: map_cat(s, IND_RULES))
a3["county_code"] = [M.pc2code.get((strip_prov(p), norm(c)))
                     for p, c in zip(a3["省份"], a3["区县"])]
a3 = a3.dropna(subset=["cat", "county_code"])
a3["county_code"] = a3["county_code"].astype(str)
firms = (a3.groupby(["county_code", "cat", "year"], as_index=False)
         .agg(n_firms=("n_firms", "sum"), cap_wan=("cap_wan", "sum"),
              n_coop=("n_coop", "sum")))
print("企业面板行:", len(firms), " 品类:", firms.cat.unique().tolist())

# ---------- 组装 县×品类×年 面板 ----------
# 完整网格：出现过的县×品类 × 2010-2023
keys = firms[["county_code", "cat"]].drop_duplicates()
years = pd.DataFrame({"year": range(2010, 2024)})
grid = keys.merge(years, how="cross")
panel = grid.merge(firms, on=["county_code", "cat", "year"], how="left")
for c in ["n_firms", "cap_wan", "n_coop"]:
    panel[c] = panel[c].fillna(0)

# 各认证首次年 → 品类内累计层数
for pol in ["GI", "名特优新", "特优区", "品牌目录"]:
    first = (cert[cert.policy == pol].groupby(["county_code", "cat"])["year"]
             .min().rename(f"{pol}_year").reset_index())
    panel = panel.merge(first, on=["county_code", "cat"], how="left")

# 时点层数：截至t已获得的认证数
def layers_at(row):
    n = 0
    for pol in ["GI", "名特优新", "特优区", "品牌目录"]:
        y = row.get(f"{pol}_year")
        if pd.notna(y) and row["year"] >= y:
            n += 1
    return n


panel["cert_layers"] = panel.apply(layers_at, axis=1)
panel["any_cert"] = (panel["cert_layers"] > 0).astype(int)
# 首次认证事件时间（相对第一块牌）
panel["first_cert_year"] = panel[[f"{p}_year" for p in ["GI", "名特优新", "特优区", "品牌目录"]]].min(axis=1)
panel["evt_first"] = panel["year"] - panel["first_cert_year"]

panel.to_csv(f"{OUT}/county_cat_panel.csv", index=False, encoding="utf-8-sig")
print("面板:", panel.shape, " 有认证县品类:", (panel.groupby(['county_code','cat'])['any_cert'].max()>0).sum())
print("层数分布(2023):")
print(panel[panel.year == 2023].cert_layers.value_counts().sort_index().to_dict())
