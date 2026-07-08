#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper 3 面板构建：亿元村/十亿元镇"超级明星"进入 vs 先期政策认定。
产出（paper3/output/）：
  town_panel.csv   镇×年(2018-2022) 离散时间风险面板（十亿元镇进入 / 是否有亿元村）
  county_year_covar.csv  县级协变量（涉农企业、产粮大县、政策存量）
  match_report.txt 匹配率诊断
设计：
  - 单元=镇（town_universe 41k）。风险期 2020/2021/2022，事件=首次进入十亿元镇名单。
  - 解释变量取 ≤2019 各类政策（镇级：强镇建设；县级：产业园/特优区/品牌/GI/名特优新）。
  - 协变量：镇级基期灯光/人口、县级涉农企业存量、产粮大县标识。
"""
import sys
import pandas as pd
sys.path.insert(0, "/root/paper/rural_specialty_industry/common/code")
from admin_match import AdminMatcher, strip_prov, norm

OUT = "/root/paper/rural_specialty_industry/paper3/output"
CO = "/root/paper/rural_specialty_industry/common/output"
E = "/root/paper/rural_specialty_industry/output"
M = AdminMatcher()
rep = []

# 县代码->标准县名（供先县后镇匹配）
county_ref = pd.read_csv(f"{CO}/name2code_county.csv", dtype=str)
code2cty = dict(zip(county_ref["区县代码"], county_ref["county_std"]))
code2prov = dict(zip(county_ref["区县代码"], county_ref["province_std"]))

# ---------- 1. 结果：超级明星 → 代码 ----------
o = pd.read_csv(f"{E}/superstar_outcomes.csv")


def resolve(r):
    ccode = M.county_code(r["province"], r["city_county"])
    tcode = None
    if ccode is not None:
        cty = code2cty.get(str(ccode), "")
        tcode = M.town_code(r["province"], cty, r["town"])
    if tcode is None:
        tcode = M.town_code(r["province"], "", r["town"])
    return pd.Series({"county_code": ccode, "town_code": tcode})


o = o.join(o.apply(resolve, axis=1))
ten = o[o.kind == "十亿元镇"]
yi = o[o.kind == "亿元村"]
rep.append(f"十亿元镇 county匹配率={ten.county_code.notna().mean():.3f} "
           f"town匹配率={ten.town_code.notna().mean():.3f} (n={len(ten)})")
rep.append(f"亿元村 county匹配率={yi.county_code.notna().mean():.3f} "
           f"town匹配率={yi.town_code.notna().mean():.3f} (n={len(yi)})")

# 镇级首次进入年
ten_entry = (ten.dropna(subset=["town_code"])
             .groupby("town_code")["list_year"].min().rename("ten_entry_year"))
# 镇内是否出现亿元村（首年）
yi_town = (yi.dropna(subset=["town_code"])
           .groupby("town_code")["list_year"].min().rename("yi_entry_year"))

# ---------- 2. 政策 → 代码 ----------
e = pd.read_csv(f"{E}/policy_events_long.csv")

# 2a 强镇建设（镇级，≤2019）
qz = e[(e.policy == "产业强镇") & (e.status == "批准建设") & (e.batch_year <= 2019)].copy()
qz["town_code"] = [M.town_code_from_addr(r.province, r.unit) for r in qz.itertuples()]
rep.append(f"强镇建设<=2019 town匹配率={qz.town_code.notna().mean():.3f} (n={len(qz)})")
qz_town = set(qz.dropna(subset=["town_code"])["town_code"])

# 2b 县级政策存量（≤2019）：产业园/特优区/品牌/名特优新
def county_flags(policy, statuses, yr=2019):
    sub = e[(e.policy == policy) & (e.batch_year <= yr)]
    if statuses:
        sub = sub[sub.status.isin(statuses)]
    codes = set()
    for r in sub.itertuples():
        if pd.notna(r.county):
            codes |= M.county_codes_flex(r.province, r.county)
    return codes


park = county_flags("现代产业园", None)
tqz = county_flags("特优区", None)
brand = county_flags("品牌目录", None)
mte = county_flags("名特优新", None)

# GI：无county字段，从证书持有人名/产品名扫县名（province内匹配）
gi_ev = e[(e.policy == "地理标志") & (e.batch_year <= 2019)]
gi = set()
for r in gi_ev.itertuples():
    p = strip_prov(r.province)
    text = norm(r.holder) + norm(r.product)
    for cn in sorted(M.county_names.get(p, ()), key=len, reverse=True):
        if cn and len(cn) >= 2 and cn in text:
            code = M.pc2code.get((p, cn))
            if code:
                gi.add(code)
            break
rep.append(f"县级政策覆盖县数: 产业园={len(park)} 特优区={len(tqz)} "
           f"品牌={len(brand)} 名特优新={len(mte)} GI(县)={len(gi)}")

# ---------- 3. 镇级协变量：基期灯光/人口 ----------
lights = pd.read_stata("/root/data/数据/乡村产业数据/1986～2024年中国各省市区县、乡镇夜间灯光面板数据/"
                       "1986～2024年中国各省市区县、乡镇夜间灯光面板数据（田一禾版本）/"
                       "1986～2024年中国各乡镇夜间灯光面板数据.dta")
lights["town_code"] = lights["乡镇代码"].astype("Int64").astype(str).str[:9]
l19 = lights[lights["年份"] == 2019][["town_code", "mean", "sum"]].rename(
    columns={"mean": "light_mean_2019", "sum": "light_sum_2019"}).drop_duplicates("town_code")
l15 = lights[lights["年份"] == 2015][["town_code", "sum"]].rename(
    columns={"sum": "light_sum_2015"}).drop_duplicates("town_code")

# ---------- 4. 县级涉农企业存量（2010-2019累计） ----------
agri = pd.read_csv(f"{E}/agri_total_county_year.csv")
agri["ckey"] = agri["省份"].map(strip_prov) + agri["区县"].map(norm)
# county code via pc2code
agri["county_code"] = [M.pc2code.get((strip_prov(p), norm(c)))
                       for p, c in zip(agri["省份"], agri["区县"])]
agri_pre = (agri[agri.year <= 2019].dropna(subset=["county_code"])
            .groupby("county_code").agg(agri_firms_pre=("n_agri_firms", "sum"),
                                        coop_pre=("n_coop", "sum")).reset_index())

# ---------- 5. 产粮大县 ----------
g800 = pd.read_csv("/root/data/数据/县域统计数据/mineru_ocr_output/grain_county_800_2009.csv",
                   dtype=str)["county_code_standard"].dropna().tolist()
g720 = pd.read_csv("/root/data/数据/县域统计数据/mineru_ocr_output/grain_capacity_720_2024.csv",
                   dtype=str)["county_code_standard"].dropna().tolist()
grain800 = set(g800)
grain720 = set(g720)

# ---------- 6. 组装镇宇宙面板 ----------
town = pd.read_csv(f"{CO}/town_universe.csv", dtype=str)
town = town.rename(columns={"镇代码": "town_code", "区县代码": "county_code"})
town["town_code"] = town["town_code"].astype(str)
town["county_code"] = town["county_code"].astype(str)

# 镇级标识
town["qz_pre2020"] = town["town_code"].isin({str(x) for x in qz_town}).astype(int)
town["ten_entry_year"] = town["town_code"].map(ten_entry)
town["yi_entry_year"] = town["town_code"].map(yi_town)
# 县级标识
town["park_pre"] = town["county_code"].isin({str(x) for x in park}).astype(int)
town["tqz_pre"] = town["county_code"].isin({str(x) for x in tqz}).astype(int)
town["brand_pre"] = town["county_code"].isin({str(x) for x in brand}).astype(int)
town["mte_pre"] = town["county_code"].isin({str(x) for x in mte}).astype(int)
town["gi_pre"] = town["county_code"].isin({str(x) for x in gi}).astype(int)
town["grain800"] = town["county_code"].isin(grain800).astype(int)
town["grain720"] = town["county_code"].isin(grain720).astype(int)
# 灯光/企业
town = town.merge(l19, on="town_code", how="left").merge(l15, on="town_code", how="left")
town = town.merge(agri_pre, on="county_code", how="left")
town["agri_firms_pre"] = town["agri_firms_pre"].fillna(0)
town["coop_pre"] = town["coop_pre"].fillna(0)

# ---------- 7. 展开为离散时间面板 2020-2022 ----------
panel = []
for y in (2020, 2021, 2022):
    d = town.copy()
    d["year"] = y
    d["entered_before"] = (d["ten_entry_year"] < y).astype(int)
    d["ten_enter"] = (d["ten_entry_year"] == y).astype(int)
    d["yi_enter"] = (d["yi_entry_year"] == y).astype(int)
    d["has_yi_by"] = (d["yi_entry_year"] <= y).astype(int)
    panel.append(d)
panel = pd.concat(panel, ignore_index=True)
# 风险集：已进入十亿元镇的镇在其后年份剔除
panel_risk = panel[panel["entered_before"] == 0].copy()

keep = ["town_code", "county_code", "省", "区县名称", "镇", "year",
        "ten_enter", "yi_enter", "has_yi_by", "qz_pre2020",
        "park_pre", "tqz_pre", "brand_pre", "mte_pre", "gi_pre", "grain800", "grain720",
        "light_mean_2019", "light_sum_2019", "light_sum_2015",
        "agri_firms_pre", "coop_pre"]
panel_risk[keep].to_csv(f"{OUT}/town_panel.csv", index=False, encoding="utf-8-sig")

# 政策梯度层级（村→镇→县）计数
town["policy_layers"] = town[["qz_pre2020", "park_pre", "tqz_pre",
                              "brand_pre", "mte_pre", "gi_pre"]].sum(axis=1)
town[["town_code", "county_code", "省", "区县名称", "镇", "policy_layers",
      "ten_entry_year", "yi_entry_year"]].to_csv(
    f"{OUT}/town_master.csv", index=False, encoding="utf-8-sig")

rep.append(f"镇面板行数={len(panel_risk)} 十亿元镇进入事件={int(panel_risk.ten_enter.sum())} "
           f"亿元村镇进入={int(panel_risk.yi_enter.sum())}")
rep.append(f"镇宇宙={len(town)} 强镇pre2020镇={town.qz_pre2020.sum()} "
           f"灯光匹配率={town.light_sum_2019.notna().mean():.3f}")
open(f"{OUT}/match_report.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
