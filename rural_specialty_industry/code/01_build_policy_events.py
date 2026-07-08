#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_build_policy_events.py
把 /root/data/乡村特色产业数据/ 下的各政策名单统一为长表：
  policy_events_long.csv  (policy, status, batch_year, province, county, unit, product, holder, raw)
  superstar_outcomes.csv  (亿元村/十亿元镇 进入名单，含期次年份)
  province_year_counts.csv (省×年×政策 计数面板)
  summary_stats.md        (核对用汇总)
"""
import re
import warnings
import pandas as pd

warnings.filterwarnings("ignore")
DATA = "/root/data/乡村特色产业数据"
OUT = "/root/paper/rural_specialty_industry/output"

rows = []


def add(policy, status, year, province, county=None, unit=None, product=None,
        holder=None, raw=None):
    rows.append(dict(policy=policy, status=status, batch_year=year,
                     province=province, county=county, unit=unit,
                     product=product, holder=holder, raw=raw))


def clean(x):
    if pd.isna(x):
        return None
    s = str(x).replace("\xa0", "").strip()
    return s or None


# ---------- 1. 地理标志 AGI ----------
gi = pd.read_excel(f"{DATA}/1_地理标志农产品数据集（2008-2022）.xlsx")
for _, r in gi.iterrows():
    add("地理标志", "登记", int(r["登记年份"]), clean(r["省（区市）"]),
        product=clean(r["产品名称"]), holder=clean(r["证书持有人名称"]),
        raw=clean(r["产品类别"]))

# ---------- 2. 名特优新 ----------
my = pd.read_excel(f"{DATA}/全国名优特产品目录.xls")
for _, r in my.iterrows():
    code = clean(r["编号"]) or ""
    m = re.search(r"(20\d{2})", code)
    add("名特优新", "登录", int(m.group(1)) if m else None, clean(r["省份"]),
        county=clean(r["县区"]), product=clean(r["产品"]),
        holder=clean(r["获证单位"]), raw=code)

# ---------- 3. 产业强镇：批准建设 ----------
qz = pd.read_excel(f"{DATA}/产业报告/产业强镇申报-无认定-2024.xlsx")
qz.columns = ["year", "province", "county", "full"]
for _, r in qz.iterrows():
    if pd.isna(r["year"]):
        continue
    add("产业强镇", "批准建设", int(r["year"]), clean(r["province"]),
        county=clean(r["county"]), unit=clean(r["full"]), raw=clean(r["full"]))

# ---------- 4. 产业强镇：通过认定 ----------
rd = pd.ExcelFile(f"{DATA}/产业报告/产业强镇申报-认定-共2批.xlsx")
for s in rd.sheet_names:
    df = rd.parse(s)
    year = int(s) if s.isdigit() else None          # “第二批认定”无年份，2022-2023合并认定
    status = "通过认定" if year else "通过认定(第二批合并)"
    for _, r in df.iterrows():
        add("产业强镇", status, year, clean(r.get("省级")),
            county=clean(r.get("地区")), unit=clean(r.get("乡镇")),
            product=clean(r.get("品种")))

# ---------- 5. 现代农业产业园：创建 / 认定 ----------
py = pd.ExcelFile(f"{DATA}/产业报告/现代产业园申报-认定-2024.xlsx")
cj = py.parse("创建")
for _, r in cj.iterrows():
    if pd.isna(r["年份"]):
        continue
    add("现代产业园", "批准创建", int(r["年份"]), clean(r["省级行政区划名称"]),
        county=clean(r["行政区划名称"]), unit=clean(r["地级行政区划名称"]),
        raw=clean(r["原始信息"]))
rdg = py.parse("认定")
for _, r in rdg.iterrows():
    t = clean(r["时间"])
    m = re.search(r"(20\d{2})", t or "")
    add("现代产业园", "通过认定", int(m.group(1)) if m else None,
        clean(r["省份"]), county=clean(r["区"]), unit=clean(r["地方（市/县）"]),
        raw=clean(r["名称"]))

# ---------- 6. 特色农产品优势区（4批，区段式表） ----------
ty = pd.read_excel(f"{DATA}/产业报告/特色农产品优势区名单-共4批.xlsx", sheet_name="Sheet1")
ty.columns = ["raw", "province", "county", "product"]
batch_year = 2017                                   # 第一批表头在列名里
for _, r in ty.iterrows():
    if pd.isna(r["province"]):
        h = clean(r["raw"]) or ""
        m = re.search(r"(20\d{2})年", h)
        if m:
            batch_year = int(m.group(1))
        continue
    add("特优区", "认定", batch_year, clean(r["province"]),
        county=clean(r["county"]), product=clean(r["product"]),
        raw=clean(r["raw"]))

# ---------- 7. 优势特色产业集群 ----------
jq = pd.read_excel(f"{DATA}/产业报告/优势特色产业集群名单-2024.xlsx", sheet_name="SheetJS")
for _, r in jq.iterrows():
    if pd.isna(r["公布年份"]):
        continue
    add("产业集群", "批准建设", int(r["公布年份"]), clean(r["公布年份省级行政区划名称"]),
        product=clean(r["特色产业与产品"]), raw=clean(r["原始信息"]))

# ---------- 8. 中国农业品牌目录（三期，版式各异） ----------
bp = pd.ExcelFile(f"{DATA}/中国农业品牌目录-应该是两年一评定.xlsx")
df = bp.parse("2019")
for _, r in df.iterrows():
    if clean(r["省级单位"]) is None:
        continue
    add("品牌目录", "发布", 2019, clean(r["省级单位"]), county=clean(r["地区"]),
        product=clean(r["Unnamed: 2"]), holder=clean(r["Unnamed: 1"]))
df = bp.parse("2020-2021")
for _, r in df.iterrows():
    seq, prov = clean(r.iloc[0]), clean(r.iloc[1])
    if seq is None or not str(seq).isdigit() or prov is None:
        continue
    add("品牌目录", "发布", 2021, prov, county=clean(r.iloc[4]),
        product=clean(r.iloc[3]), holder=clean(r.iloc[2]))
df = bp.parse("2022-2023")
for _, r in df.iterrows():
    seq = clean(r.iloc[0])
    if seq is None or not str(seq).isdigit():
        continue
    add("品牌目录", "发布", 2023, clean(r.iloc[3]), county=clean(r.iloc[4]),
        product=clean(r.iloc[2]), holder=clean(r.iloc[1]))

events = pd.DataFrame(rows)
events.to_csv(f"{OUT}/policy_events_long.csv", index=False, encoding="utf-8-sig")

# ---------- 9. 亿元村 / 十亿元镇（结果变量） ----------
out_rows = []
ys = pd.ExcelFile(f"{DATA}/亿元村和十亿元镇.xlsx")
for sheet, kind in [("亿元村", "亿元村"), ("十亿元镇", "十亿元镇")]:
    df = ys.parse(sheet)
    year = None
    for _, r in df.iterrows():
        first = clean(r.iloc[0])
        if first and re.match(r"^20\d{2}年", first):
            year = int(first[:4])
            continue
        if first is None or pd.isna(r.iloc[1]):
            continue
        out_rows.append(dict(kind=kind, list_year=year, province=first,
                             city_county=clean(r.iloc[1]), town=clean(r.iloc[2]),
                             village=clean(r.iloc[3]) if kind == "亿元村" else None))
outcomes = pd.DataFrame(out_rows)
outcomes.to_csv(f"{OUT}/superstar_outcomes.csv", index=False, encoding="utf-8-sig")

# ---------- 10. 省×年×政策 计数面板 ----------
pyc = (events.dropna(subset=["batch_year"])
       .groupby(["province", "policy", "status", "batch_year"])
       .size().rename("n").reset_index())
pyc.to_csv(f"{OUT}/province_year_counts.csv", index=False, encoding="utf-8-sig")

# ---------- 汇总核对 ----------
with open(f"{OUT}/summary_stats.md", "w") as f:
    f.write("# 政策事件长表核对汇总\n\n## 各政策×状态 事件数\n\n")
    f.write(events.groupby(["policy", "status"]).size().to_markdown())
    f.write("\n\n## 各政策 年份覆盖\n\n")
    yr = events.dropna(subset=["batch_year"]).groupby("policy")["batch_year"] \
        .agg(["min", "max", "count"])
    f.write(yr.to_markdown())
    f.write("\n\n## 超级明星名单\n\n")
    f.write(outcomes.groupby(["kind", "list_year"]).size().to_markdown())
    f.write("\n")

print("events:", len(events), " outcomes:", len(outcomes))
print(events.groupby(["policy", "status"]).size())
print(outcomes.groupby(["kind", "list_year"]).size())
