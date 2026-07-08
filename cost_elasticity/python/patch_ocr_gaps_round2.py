#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_ocr_gaps_round2.py — 第二轮补录/修正 (2026-07-07, 见 notes §7)

任务:
1. 玉米2005 -2表(2-6-2): 2006.md 主<table>内嵌第二表头块
   [辽宁,吉林,黑龙江,江苏,安徽,山东] → 追加 data/yearbook_patch_ocr_gaps.csv。
2. 小麦2005 -2表(2-5-2): 2006.md 续表2 <table>内嵌第二表头块
   [陕西,甘肃,青海,宁夏,新疆] → 同上。
3. 油菜籽2023 (2024卷 2-9-2 续表1, pdf物理页169=书页162, 无文本层, 目视转录):
   mineru md 在该页把真实"种子费"行拆成无行名行, 导致 种子费/化肥费/农家肥费
   三行整体上移一行(农药费真值丢失) → 河南/湖北/湖南/重庆/四川 5省:
   修正 种子费/化肥费/农家肥费 (写 data/yearbook_fix_rapeseed2023.csv +
   追加 out/base_conflicts.csv, build_panel.R 自动应用), 补录库中缺失的 农药费
   (追加 data/yearbook_patch_ocr_gaps.csv)。每亩种子用量 经PDF核对为真值, 不改。

附带发现与处理 (同 notes §4 机制, 库值=max(主块省真值, 内嵌块省值)):
- 玉米/小麦2005 -2表 及 -3表 主块省份库值污染 → 以md解析真值追加
  out/base_conflicts.csv (ref_source=md_patch:2006.md, 全省MSF恒等式精确成立);
- -3表(每亩化肥折纯用量) 缺省份一并补录: 玉米[辽宁,吉林,黑龙江,江苏,安徽,山东],
  小麦[黑龙江,上海,江苏,安徽,山东,河南]+[陕西,甘肃,青海,宁夏,新疆]
  (后5省表头行OCR损毁, 值以人工核对块给出, 与 -2表每亩化肥用量逐值一致——
   2005年表制两者同值)。

QC: 与 patch_qc.csv 相同的恒等式 (MSF=分项和±2%, 含2005年税金;
    生产成本+土地成本=总成本±2%; 另加 折纯用量=化肥用量 一致性)
    → out/patch_qc_round2.csv。
幂等: 追加前按键去重, 可重复运行。
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patch_ocr_gaps import parse_md_table  # noqa: E402
from extract_yearbook import UNIT_MAP, MSF_COMPONENTS  # noqa: E402

PROJ = "/root/paper/cost_elasticity"
BASE_CSV = os.path.join(PROJ, "data/yearbook_long.csv")
PATCH_CSV = os.path.join(PROJ, "data/yearbook_patch_ocr_gaps.csv")
FIX_CSV = os.path.join(PROJ, "data/yearbook_fix_rapeseed2023.csv")
CONFLICT_CSV = os.path.join(PROJ, "out/base_conflicts.csv")
QC_CSV = os.path.join(PROJ, "out/patch_qc_round2.csv")

# ---- 任务1/2: 2006.md 内嵌续表块 (kind=2) ----------------------------------
MD_TABLES_R2 = [
    # 玉米 2-6-2: 主<table>含 [平均..内蒙古] + 内嵌 [辽宁..山东]
    ("2006", "corn", 2005, 2, r"^2-6-2\s*2005年各地区玉米费用和用工情况"),
    # 玉米 2-6-2续表2: [河南..贵州] + [云南..新疆] (均已在库, 仅供审计/QC)
    ("2006", "corn", 2005, 2, r"^2-6-2续表2"),
    # 小麦 2-5-2 主表/续表1 (已在库, 仅供审计/QC)
    ("2006", "wheat", 2005, 2, r"^2-5-2\s*2005年各地区小麦费用和用工情况"),
    ("2006", "wheat", 2005, 2, r"^2-5-2续表1"),
    # 小麦 2-5-2续表2: [湖北..云南] + 内嵌 [陕西,甘肃,青海,宁夏,新疆]
    ("2006", "wheat", 2005, 2, r"^2-5-2续表2"),
    # -3表 (每亩化肥折纯用量): 主<table>同样含内嵌第二表头块
    ("2006", "corn", 2005, 3, r"^2-6-3\s*2005年各地区玉米化肥投入情况"),
    ("2006", "corn", 2005, 3, r"^2-6-3续表2"),
    ("2006", "corn", 2005, 3, r"^2-6-3续表3"),
    ("2006", "wheat", 2005, 3, r"^2-5-3\s*2005年各地区小麦化肥投入情况"),
    # 小麦 2-5-3续表2: 首块[湖北..云南]正常; 内嵌块[陕西..新疆]表头行OCR损毁
    # ('2.混配肥项目'等合并单元格), parse_md_table 不会切换省份表头, 其第二个
    # "二、每亩化肥折纯用量"行会被误配到首块省份 —— 依赖 drop_duplicates
    # keep="first" 保留首块正确值; 损毁块以下方人工核对值补录。
    ("2006", "wheat", 2005, 3, r"^2-5-3续表2"),
]

# 小麦2005 -3续表2 内嵌块 (表头行损毁, 人工核对; 与 -2表每亩化肥用量逐值一致)
MANUAL_R2 = [
    ("wheat", p, 2005, "每亩化肥折纯用量", v, "md_patch:2006.md", 3, -1)
    for p, v in [("陕西", 29.05), ("甘肃", 18.43), ("青海", 10.99),
                 ("宁夏", 26.68), ("新疆", 21.15)]
]

# ---- 任务3: 油菜籽2023 续表1 目视转录真值 (2024.pdf p169, 书页162) ----------
# 行内恒等式逐省验证: 直接费用=分项和, 物质与服务费用=直接+间接, 均精确成立。
RAPE_PROVS = ["河南", "湖北", "湖南", "重庆", "四川"]
RAPE_TRUE = {  # variable -> [5省真值]
    "种子费":   [29.64, 36.48, 25.72, 15.74, 26.63],
    "化肥费":   [146.93, 139.66, 122.53, 66.18, 127.83],
    "农家肥费": [1.49, 8.60, 6.57, 14.84, 10.04],
    "农药费":   [15.35, 25.76, 24.68, 6.41, 17.30],  # 库中缺失(md错移为农家肥费)
}
RAPE_SRC = "pdf_patch:2024.pdf"


def main():
    base = pd.read_csv(BASE_CSV)
    patch_old = pd.read_csv(PATCH_CSV)
    key_cols = ["crop", "province", "year", "variable"]
    have = set(map(tuple, base[key_cols].itertuples(index=False, name=None)))
    have |= set(map(tuple, patch_old[key_cols].itertuples(index=False, name=None)))

    # ---------------- 任务1/2: 解析 md ----------------
    recs = []
    for vol, crop, year, kind, tre in MD_TABLES_R2:
        got = parse_md_table(vol, crop, year, kind, tre)
        provs = sorted({r[1] for r in got})
        print(f"{vol}.md {crop} {year} k{kind} [{tre}]: {len(got)} 值, "
              f"省: {'/'.join(provs)}")
        recs += got
    recs += MANUAL_R2
    df = pd.DataFrame(recs, columns=key_cols[:2] + ["year", "variable",
                      "value", "source", "_kind", "_page"])
    df = df.drop_duplicates(key_cols, keep="first")

    # 审计: 已有库键的值对照 (含税金则跳过—库中无税金)
    m = base.merge(df[key_cols + ["value", "source"]], on=key_cols,
                   suffixes=("_base", "_md"))
    rel = (m["value_base"] - m["value_md"]).abs() / m["value_md"].abs().clip(lower=0.01)
    audit = m[rel > 0.005].copy()
    print(f"\n[审计] 玉米/小麦2005 -2/-3表: 复核 {len(m)} 条库值, "
          f"不一致 {len(audit)} 条 (机制同 notes §4, 追加 base_conflicts.csv)")
    audit_conf = audit.rename(columns={"value_md": "value_pdf",
                                       "source_md": "ref_source"})[
        key_cols + ["value_base", "value_pdf", "ref_source"]]

    # --- 真空白污染: 库有值而md原表该格为空白 —— 值实为同列位内嵌块省份之值
    #     (max机制), 真值=空白(0)。逐条要求与"伙伴省"md值精确一致后方置0。
    PARTNER = {  # 主块省 -> 同<table>内嵌块同列位省
        ("corn", 2): {"北京": "吉林", "天津": "黑龙江", "河北": "江苏",
                      "山西": "安徽", "内蒙古": "山东"},
        ("corn", 3): {"北京": "吉林", "天津": "黑龙江", "河北": "江苏",
                      "山西": "安徽", "内蒙古": "山东"},
        ("wheat", 2): {"湖北": "陕西", "重庆": "甘肃", "四川": "青海",
                       "贵州": "宁夏", "云南": "新疆"},
        ("wheat", 3): {"北京": "上海", "天津": "江苏", "河北": "安徽",
                       "山西": "山东", "内蒙古": "河南"},
    }
    var_kind = df.groupby("variable")["_kind"].first().to_dict()
    mdv = df.set_index(key_cols)["value"].to_dict()
    mdkeys = set(mdv)
    tab_provs = {c: set(df[df.crop == c].province) for c in ("corn", "wheat")}
    tab_vars = set(df.variable) - {"税金"}
    cand = base[(base.year == 2005) & base.crop.isin(["corn", "wheat"])
                & base.variable.isin(tab_vars)]
    zero_rows, n_skip = [], 0
    for r in cand.itertuples(index=False):
        if r.province not in tab_provs[r.crop] or \
                (r.crop, r.province, r.year, r.variable) in mdkeys:
            continue
        partner = PARTNER.get((r.crop, var_kind[r.variable]), {}).get(r.province)
        pv = mdv.get((r.crop, partner, 2005, r.variable)) if partner else None
        if pv is not None and abs(r.value - pv) <= 0.005 * max(abs(pv), 0.01):
            zero_rows.append((r.crop, r.province, 2005, r.variable, r.value,
                              0.0, "md_patch:2006.md(blank)"))
        else:
            n_skip += 1
            print(f"[warn] 疑似真空白但与伙伴省不符, 不处理: {r.crop} {r.province} "
                  f"{r.variable} base={r.value} partner={partner}:{pv}")
    zero_conf = pd.DataFrame(zero_rows, columns=list(audit_conf.columns))
    print(f"[审计] 真空白污染置0: {len(zero_conf)} 条 (跳过 {n_skip})")
    audit_conf = pd.concat([audit_conf, zero_conf], ignore_index=True)

    # 新键 (不在库也不在既有补丁中), 税金仅供QC不入CSV
    mask = [t not in have for t in df[key_cols].itertuples(index=False, name=None)]
    new = df[mask].copy()
    new_qc = new.copy()  # 含税金, 供QC
    new = new[new.variable != "税金"]
    new["unit"] = new["variable"].map(UNIT_MAP)
    new = new[["crop", "province", "year", "variable", "unit", "value", "source"]]
    print("\n任务1/2 新增行:")
    print(new.groupby(["crop", "year"])["province"]
          .agg(lambda s: f"{len(s)}行/" + ",".join(sorted(s.unique()))).to_string())

    # ---------------- 任务3: 油菜籽2023 ----------------
    fix_rows, conf_rows, rape_patch = [], [], []
    for var, vals in RAPE_TRUE.items():
        for prov, v in zip(RAPE_PROVS, vals):
            k = ("rapeseed", prov, 2023, var)
            old = base.loc[(base.crop == "rapeseed") & (base.province == prov)
                           & (base.year == 2023) & (base.variable == var), "value"]
            if len(old):  # 库中已有 → 修正 (fix csv + base_conflicts)
                vo = float(old.iloc[0])
                fix_rows.append(("rapeseed", prov, 2023, var, UNIT_MAP[var],
                                 v, RAPE_SRC, vo))
                if abs(vo - v) > 1e-9:
                    conf_rows.append(("rapeseed", prov, 2023, var, vo, v, RAPE_SRC))
            else:  # 库中缺失 → 补录
                fix_rows.append(("rapeseed", prov, 2023, var, UNIT_MAP[var],
                                 v, RAPE_SRC, None))
                if k not in have:
                    rape_patch.append(("rapeseed", prov, 2023, var, UNIT_MAP[var],
                                       v, RAPE_SRC))
    fix = pd.DataFrame(fix_rows, columns=["crop", "province", "year", "variable",
                                          "unit", "value", "source", "value_old"])
    fix.to_csv(FIX_CSV, index=False)
    print(f"\n任务3: {FIX_CSV} 写入 {len(fix)} 行 "
          f"(修正 {len(conf_rows)}, 库缺补录 {len(rape_patch)})")

    conf = pd.DataFrame(conf_rows, columns=["crop", "province", "year", "variable",
                                            "value_base", "value_pdf", "ref_source"])
    conf = pd.concat([audit_conf, conf], ignore_index=True)
    bc = pd.read_csv(CONFLICT_CSV)
    n0 = len(bc)
    bc = pd.concat([bc, conf], ignore_index=True)
    bc = bc.drop_duplicates(key_cols, keep="last")
    bc.to_csv(CONFLICT_CSV, index=False)
    print(f"base_conflicts.csv: {n0} → {len(bc)} 行 (+{len(bc)-n0})")

    rp = pd.DataFrame(rape_patch, columns=new.columns)
    add = pd.concat([new, rp], ignore_index=True)
    add = add.sort_values(["crop", "year", "province", "variable"])
    n0 = len(patch_old)
    out = pd.concat([patch_old, add], ignore_index=True)
    out = out.drop_duplicates(key_cols, keep="first")
    out.to_csv(PATCH_CSV, index=False)
    print(f"yearbook_patch_ocr_gaps.csv: {n0} → {len(out)} 行 (+{len(out)-n0})")

    # ---------------- QC: 恒等式 (同 patch_qc) ----------------
    # 数据状态 = base + base_conflicts修正 + 全部补丁 + (QC专用)税金
    yb = base.set_index(key_cols)["value"].to_dict()
    for r in bc.itertuples(index=False):
        yb[(r.crop, r.province, r.year, r.variable)] = r.value_pdf
    for r in out.itertuples(index=False):
        yb.setdefault((r.crop, r.province, r.year, r.variable), r.value)
    for r in new_qc[new_qc.variable == "税金"].itertuples(index=False):
        yb[(r.crop, r.province, r.year, r.variable)] = r.value
    # 本轮涉及键
    touched = sorted({(r.crop, r.province, r.year) for r in add.itertuples(index=False)}
                     | {(r.crop, r.province, r.year) for r in conf.itertuples(index=False)}
                     | {("rapeseed", p, 2023) for p in RAPE_PROVS})
    qc = []
    for crop, prov, yr in touched:
        g = lambda v: yb.get((crop, prov, yr, v))
        tc, pc, lc = g("总成本"), g("生产成本"), g("土地成本")
        if tc and pc and lc:
            rel = abs(pc + lc - tc) / tc
            qc.append((crop, prov, yr, "total_cost", round(rel, 4),
                       f"生产{pc}+土地{lc} vs 总{tc}", "FAIL" if rel > .02 else "ok"))
        msf = g("物质与服务费用")
        comps = [g(c) for c in MSF_COMPONENTS + ["税金"]]
        have_c = [c for c in comps if c is not None]
        if msf and have_c:
            rel = abs(sum(have_c) - msf) / msf
            qc.append((crop, prov, yr, "msf_sum", round(rel, 4),
                       f"分项和{sum(have_c):.2f} vs {msf} (n={len(have_c)})",
                       "FAIL" if rel > .02 else "ok"))
        # 2005年表制: -3折纯用量 与 -2化肥用量 同值 (交叉校验)
        fp, fq = g("每亩化肥折纯用量"), g("每亩化肥用量")
        if yr == 2005 and fp and fq:
            rel = abs(fp - fq) / fq
            qc.append((crop, prov, yr, "fert_purity_eq", round(rel, 4),
                       f"折纯{fp} vs 化肥用量{fq}", "FAIL" if rel > .02 else "ok"))
    qcdf = pd.DataFrame(qc, columns=["crop", "province", "year", "check",
                                     "rel", "detail", "status"])
    qcdf.to_csv(QC_CSV, index=False)
    nfail = (qcdf.status == "FAIL").sum()
    print(f"\nQC: {len(qcdf)} 项恒等式检查, FAIL {nfail} → {QC_CSV}")
    if nfail:
        print(qcdf[qcdf.status == "FAIL"].to_string(index=False))


if __name__ == "__main__":
    main()
