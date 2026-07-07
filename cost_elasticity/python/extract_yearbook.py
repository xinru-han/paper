#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_yearbook.py — 中国农产品成本收益汇编 省级面板提取管线
来源:
  - 年度xls文件夹 /root/data/数据/成本收益数据/{2007..2019, 2025} (数据年 2006-2018, 2024)
  - OCR长表 mineru_ocr_output/database/provincial_cost_benefit_long.csv (数据年 2004, 2005, 2019-2023)
产出:
  - data/yearbook_long.csv
  - out/coverage_matrix.csv, out/coverage_gaps.md, out/qc_violations.csv
实施依据: docs/data_audit_yearbook.md (Phase 0 审计报告)
确定性可重跑; 加密xls (2017/2018/2019卷) 用 msoffcrypto + VelvetSweatshop 解密缓存。
"""
import io
import os
import re
import sys
import glob
import hashlib

import pandas as pd
import numpy as np

DATA_ROOT = "/root/data/数据/成本收益数据"
OCR_CSV = os.path.join(DATA_ROOT, "mineru_ocr_output/database/provincial_cost_benefit_long.csv")
PROJ = "/root/paper/cost_elasticity"
SCRATCH_DECRYPT = "/tmp/claude-0/-root/35855a58-2b1b-4c73-a941-25308daf893f/scratchpad/decrypted"

OUT_LONG = os.path.join(PROJ, "data/yearbook_long.csv")
OUT_NATIONAL = os.path.join(PROJ, "data/yearbook_national_long.csv")
OUT_COVER = os.path.join(PROJ, "out/coverage_matrix.csv")
OUT_GAPS = os.path.join(PROJ, "out/coverage_gaps.md")
OUT_QC = os.path.join(PROJ, "out/qc_violations.csv")

# ---------------------------------------------------------------- crops
# crop_en -> (中文名, section)。表号不硬编码: 2007/2008卷大豆在2-9、花生2-10、油菜籽2-11,
# 2009卷起为2-7/2-8/2-9 — 统一按 -1 表标题扫描解析 (resolve_table)。
CROPS = {
    "rice_early_indica": ("早籼稻", 2),
    "rice_mid_indica":   ("中籼稻", 2),
    "rice_late_indica":  ("晚籼稻", 2),
    "rice_japonica":     ("粳稻",   2),
    "wheat":             ("小麦",   2),
    "corn":              ("玉米",   2),
    "soybean":           ("大豆",   2),
    "peanut":            ("花生",   2),
    "rapeseed":          ("油菜籽", 2),
    "cotton":            ("棉花",   3),
}
OCR_PRODUCT_MAP = {
    "玉米": "corn", "小麦": "wheat", "大豆": "soybean",
    "早籼稻": "rice_early_indica", "中籼稻": "rice_mid_indica",
    "晚籼稻": "rice_late_indica", "粳稻": "rice_japonica",
    "花生": "peanut", "油菜籽": "rapeseed",
    "棉花": "cotton", "棉花、长绒棉": "cotton",  # 长绒棉单列品种，排除
}

XLS_VOLS = list(range(2007, 2020)) + [2025]  # 卷年; 数据年 = 卷年-1

# ---------------------------------------------------------------- variables
COST_VARS_YUAN = [
    "产值合计", "主产品产值", "总成本", "生产成本", "物质与服务费用", "人工成本",
    "家庭用工折价", "雇工费用", "土地成本", "流转地租金", "自营地折租",
    "种子费", "化肥费", "农家肥费", "农药费", "农膜费", "机械作业费", "排灌费",
    "畜力费", "燃料动力费", "技术服务费", "工具材料费", "修理维护费", "其他直接费用",
    "固定资产折旧", "保险费", "管理费", "财务费", "销售费",
]
UNIT_MAP = {v: "元" for v in COST_VARS_YUAN}
UNIT_MAP.update({
    "主产品产量": "公斤", "每亩种子用量": "公斤", "每亩化肥用量": "公斤",
    "每亩化肥折纯用量": "公斤", "每亩农膜用量": "公斤",
    "家庭用工天数": "日", "雇工天数": "日", "每亩用工数量": "日",
    "劳动日工价": "元/日", "雇工工价": "元/日",
    "平均出售价格": "元/50公斤",
})
TARGET_VARS = list(UNIT_MAP)

# -1表 每亩块可取科目
K1_PER_MU = {
    "主产品产量", "产值合计", "主产品产值", "总成本", "生产成本", "物质与服务费用",
    "人工成本", "家庭用工折价", "雇工费用", "土地成本", "流转地租金", "自营地折租",
}
# -2表科目 (规范化后)
K2_VARS = {
    "种子费", "化肥费", "农家肥费", "农药费", "农膜费", "机械作业费", "排灌费",
    "畜力费", "燃料动力费", "技术服务费", "工具材料费", "修理维护费", "其他直接费用",
    "固定资产折旧", "保险费", "管理费", "财务费", "销售费",
    "家庭用工折价", "家庭用工天数", "劳动日工价", "雇工费用", "雇工天数", "雇工工价",
    "每亩种子用量", "每亩化肥用量", "每亩农膜用量",
    "物质与服务费用", "人工成本",  # 来自 一、每亩物质与服务费用 / 二、每亩人工成本
}
# 规范化后别名 -> 统一名
ALIAS = {
    "每亩物质与服务费用": "物质与服务费用",
    "每亩人工成本": "人工成本",
    "其它直接费用": "其他直接费用",
    "其它燃料动力费": None,  # 非目标
}

PROVINCES = [
    "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江", "上海", "江苏",
    "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "广西",
    "海南", "重庆", "四川", "贵州", "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆",
]
PROV_SET = set(PROVINCES)

WS_RE = re.compile(r"[\s　\xa0]+")


def norm_text(s):
    """去空白/全角空白, 全角括号转半角。"""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = WS_RE.sub("", str(s))
    s = s.replace("灿", "籼")  # 2008卷标题错别字: 早灿稻/晚灿稻
    return s.replace("（", "(").replace("）", ")").replace("：", ":").replace("，", ",")


def norm_label(s):
    """行名规范化: 去空白后剥离序号/块前缀 (一、 / (一) / 1. / 其中: )。"""
    s = norm_text(s)
    prev = None
    while s != prev:
        prev = s
        s = re.sub(r"^[一二三四五六七八九十]、", "", s)
        s = re.sub(r"^\([一二三四五六七八九十]\)", "", s)
        s = re.sub(r"^\d+[\.、．,]", "", s)
        s = re.sub(r"^其中:", "", s)
    s = s.rstrip(":：")
    if s in ALIAS:
        s = ALIAS[s]
    return s or ""


def norm_province(s):
    s = norm_text(s)
    for suf in ["维吾尔自治区", "壮族自治区", "回族自治区", "自治区", "省", "市"]:
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    return s


def is_watermark(s):
    s = norm_text(s)
    return ("数据狂" in s) or ("公众号" in s) or ("来源:《" in s)


# ---------------------------------------------------------------- xls reading
def read_xls(path):
    """读xls/xlsx; 加密则用 msoffcrypto (VelvetSweatshop) 解密到缓存后读。"""
    try:
        return pd.read_excel(path, header=None)
    except Exception:
        pass
    os.makedirs(SCRATCH_DECRYPT, exist_ok=True)
    key = hashlib.md5(path.encode()).hexdigest()[:10]
    cache = os.path.join(SCRATCH_DECRYPT, key + "_" + os.path.basename(path))
    if not os.path.exists(cache):
        import msoffcrypto
        with open(path, "rb") as fh:
            off = msoffcrypto.OfficeFile(fh)
            off.load_key(password="VelvetSweatshop")
            buf = io.BytesIO()
            off.decrypt(buf)
        with open(cache, "wb") as out:
            out.write(buf.getvalue())
    return pd.read_excel(cache, header=None)


def find_files(vol, section, table, kind):
    """按卷年命名规律返回 (含续表的) 文件列表。"""
    root = os.path.join(DATA_ROOT, str(vol))
    if vol in (2007, 2008):
        # 2007卷第3章不补零 (3-1-1.xls); 第2章补零 (2-06-1.xls)
        pats = [f"{section}-{table:02d}-{kind}*.xls", f"{section}-{table}-{kind}.xls"]
    elif vol == 2009:
        pats = [f"{section}{table:02d}0{kind}*.xls"]
    elif vol in (2010, 2011, 2012, 2013, 2014):
        pats = [f"0{section}{table:02d}0{kind}*.xls"]
    elif vol == 2015:
        pats = [f"0{section}{table:02d}-0{kind}*.xls"]
    elif vol in (2016, 2017):
        pats = [f"{section}-{table:02d}-{kind}*.xls"]
    elif vol == 2018:
        pats = [f"*/{section}-{table}-{kind} *.xls"]
    elif vol == 2019:
        pats = [f"{section}-{table}-{kind} *.xls"]
    elif vol == 2025:
        pats = [f"{section}-{table}-{kind} *.xlsx"]
    else:
        return []
    files = []
    for p in pats:
        files += glob.glob(os.path.join(root, p))
    return sorted(files)


def parse_header(df):
    """返回 (header_row_idx, [(col_idx, colname)]); colname 已规范化; 遇 长绒棉平均 截断。"""
    hdr = None
    for i in range(min(6, len(df))):
        if "项目" in norm_text(df.iloc[i, 0]):
            hdr = i
            break
    if hdr is None:
        raise ValueError("header row not found")
    cols = []
    for j in range(2, df.shape[1]):
        name = norm_text(df.iloc[hdr, j])
        if not name:
            continue
        if name == "长绒棉平均":  # 棉花合表: 之后为长绒棉块, 不取
            break
        if name == "棉花平均":  # 2019卷棉花表的平均列写作"棉花平均"
            name = "平均"
        cols.append((j, name))
    return hdr, cols


def parse_sheet(df, kind):
    """解析一张分省表, 返回 [(variable, colname, value)]。kind: 1/2/3。"""
    hdr, cols = parse_header(df)
    out = []
    block = "per_mu"  # -1表状态机
    for i in range(hdr + 1, len(df)):
        raw = df.iloc[i, 0]
        if is_watermark(raw):
            continue
        lab_raw = norm_text(raw)
        if not lab_raw:
            continue
        if kind == 1:
            if lab_raw.startswith("每50公斤"):
                block = "per50"
                continue
            if re.fullmatch(r"附[:：]?", lab_raw):
                block = "appendix"
                continue
        lab = norm_label(raw)
        var = None
        if kind == 1:
            if block == "per_mu" and lab in K1_PER_MU:
                var = lab
            elif block == "per50" and lab == "平均出售价格":
                var = "平均出售价格"
            elif block == "appendix" and lab == "每亩用工数量":
                var = "每亩用工数量"
        elif kind == 2:
            if lab in K2_VARS:
                var = lab
        elif kind == 3:
            if lab == "每亩化肥折纯用量":
                var = lab
        if var is None:
            continue
        for j, colname in cols:
            v = pd.to_numeric(df.iloc[i, j], errors="coerce")
            if pd.notna(v):
                out.append((var, colname, float(v)))
    return out


_TITLE_CACHE = {}


def table_title(vol, section, table):
    """(vol, section, table) 的 -1 主表标题 (规范化); 无文件返回 ''。"""
    key = (vol, section, table)
    if key not in _TITLE_CACHE:
        title = ""
        for f in find_files(vol, section, table, 1):
            t = norm_text(read_xls(f).iloc[0, 0])
            if "各地区" in t:  # 跳过续表 (标题无品种名)
                title = t
                break
        _TITLE_CACHE[key] = title
    return _TITLE_CACHE[key]


def resolve_table(vol, crop):
    """按 -1 表标题扫描该卷中品种的表号 (防各卷表号漂移, 如2007/08卷大豆在2-9)。"""
    cn, section = CROPS[crop]
    candidates = range(1, 4) if section == 3 else range(1, 13)
    for t in candidates:
        title = table_title(vol, section, t)
        if cn in title and "成本收益" in title:
            return t
    return None


def check_title(df, section, table, kind, cn, src):
    """防御: 表号前缀必须匹配; 主表标题必须含品种名。"""
    title = norm_text(df.iloc[0, 0])
    assert title.startswith(f"{section}-{table}-{kind}"), f"table id mismatch: {title} @ {src}"
    if "各地区" in title:
        assert cn in title, f"crop mismatch: expect {cn}, got '{title}' @ {src}"


def extract_xls():
    recs, nat = [], []
    for vol in XLS_VOLS:
        year = vol - 1
        for crop, (cn, section) in CROPS.items():
            t = resolve_table(vol, crop)
            if t is None:
                print(f"[warn] no table: vol={vol} {crop}", file=sys.stderr)
                continue
            for kind in (1, 2, 3):
                files = find_files(vol, section, t, kind)
                if not files:
                    print(f"[warn] no file: vol={vol} {crop} kind={kind}", file=sys.stderr)
                    continue
                for f in files:
                    df = read_xls(f)
                    src = f"xls:{vol}/{os.path.basename(f)}"
                    check_title(df, section, t, kind, cn, src)
                    for var, colname, val in parse_sheet(df, kind):
                        if colname == "平均":
                            nat.append((crop, "全国平均", year, var, val, src, kind))
                            continue
                        prov = norm_province(colname)
                        if prov not in PROV_SET:
                            print(f"[warn] unknown col '{colname}' in {src}", file=sys.stderr)
                            continue
                        recs.append((crop, prov, year, var, val, src, kind))
    cols = ["crop", "province", "year", "variable", "value", "source", "_kind"]
    df = pd.DataFrame(recs, columns=cols)
    dn = pd.DataFrame(nat, columns=cols)
    # 去重: -1/-2 重名科目 (物质与服务费用/人工成本/家庭用工折价/雇工费用) 优先取 -1 表
    for d in (df, dn):
        d.sort_values(["crop", "province", "year", "variable", "_kind"],
                      inplace=True, kind="mergesort")
    df = df.drop_duplicates(["crop", "province", "year", "variable"], keep="first")
    dn = dn.drop_duplicates(["crop", "province", "year", "variable"], keep="first")
    return df.drop(columns="_kind"), dn.drop(columns="_kind")


# ---------------------------------------------------------------- OCR
def extract_ocr():
    d = pd.read_csv(OCR_CSV, low_memory=False)
    d = d[d["scope"] == "provincial"]
    d = d[d["data_year"].isin([2004, 2005, 2019, 2020, 2021, 2022, 2023])]
    d = d[d["product"].isin(OCR_PRODUCT_MAP)].copy()
    d["crop"] = d["product"].map(OCR_PRODUCT_MAP)
    d["province"] = d["province_name"].map(norm_province)
    d = d[d["province"].isin(PROV_SET)]
    d["var_norm"] = d["variable"].map(norm_label)
    d = d[d["var_norm"].isin(TARGET_VARS)]
    # 科目↔表标题一致性: 防OCR跨表串页 (如2024卷棉花成本收益内容混入油菜籽化肥投入表页)
    shared = {"物质与服务费用", "人工成本", "家庭用工折价", "雇工费用"}
    k1_only = (K1_PER_MU | {"平均出售价格", "每亩用工数量"}) - shared

    def title_ok(row):
        t = str(row["source_table_title"])
        v = row["var_norm"]
        if v in shared:
            return ("成本收益" in t) or ("费用和用工" in t)
        if v in k1_only:
            return "成本收益" in t
        if v == "每亩化肥折纯用量":
            return "化肥投入" in t
        return "费用和用工" in t  # 其余均为-2表科目

    d = d[d.apply(title_ok, axis=1)]
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    d = d.dropna(subset=["value"])
    d = d[~d["raw_item"].astype(str).map(is_watermark)]

    # 消歧: 同键多行 → 每亩口径取最大值; 平均出售价格取中位数(仅每50公斤口径, 重复为OCR重表)
    keys = ["crop", "province", "data_year", "var_norm"]
    is_price = d["var_norm"] == "平均出售价格"
    agg_max = d[~is_price].groupby(keys, sort=True)["value"].max().reset_index()
    agg_med = d[is_price].groupby(keys, sort=True)["value"].median().reset_index()
    agg = pd.concat([agg_max, agg_med], ignore_index=True)
    agg = agg.rename(columns={"data_year": "year", "var_norm": "variable"})
    agg["source"] = "ocr:provincial_cost_benefit_long"
    return agg[["crop", "province", "year", "variable", "value", "source"]]


# ---------------------------------------------------------------- QC
MSF_COMPONENTS = [
    "种子费", "化肥费", "农家肥费", "农药费", "农膜费", "机械作业费", "排灌费", "畜力费",
    "燃料动力费", "技术服务费", "工具材料费", "修理维护费", "其他直接费用",
    "固定资产折旧", "保险费", "管理费", "财务费", "销售费",
]


def run_qc(long_df):
    wide = long_df.pivot_table(index=["crop", "province", "year"],
                               columns="variable", values="value", aggfunc="first")
    viol = []

    def add(idx, check, detail):
        crop, prov, yr = idx
        viol.append({"crop": crop, "province": prov, "year": yr,
                     "check": check, "detail": detail})

    n_identity = 0
    for idx, r in wide.iterrows():
        # 1) 物质与服务费用分项和 (要求≥12个分项在, 缺项按0; OCR缺口观测不参与)
        msf = r.get("物质与服务费用")
        comps = [r.get(c) for c in MSF_COMPONENTS]
        n_have = sum(pd.notna(c) for c in comps)
        if pd.notna(msf) and msf > 0 and n_have >= 12:
            n_identity += 1
            s = np.nansum([c for c in comps if pd.notna(c)])
            if abs(s - msf) / msf > 0.02:
                add(idx, "msf_sum", f"sum={s:.2f} vs 物质与服务费用={msf:.2f} (n={n_have})")
        # 2) 家庭用工折价+雇工费用 ≈ 人工成本
        lab, fam, hire = r.get("人工成本"), r.get("家庭用工折价"), r.get("雇工费用")
        if pd.notna(lab) and lab > 0 and pd.notna(fam):
            n_identity += 1
            s = fam + (hire if pd.notna(hire) else 0.0)
            if abs(s - lab) / lab > 0.02:
                add(idx, "labor_sum", f"{fam:.2f}+{0 if pd.isna(hire) else hire:.2f} vs 人工成本={lab:.2f}")
        # 3) 生产成本+土地成本 ≈ 总成本
        tc, pc, lc = r.get("总成本"), r.get("生产成本"), r.get("土地成本")
        if pd.notna(tc) and tc > 0 and pd.notna(pc) and pd.notna(lc):
            n_identity += 1
            if abs(pc + lc - tc) / tc > 0.02:
                add(idx, "total_cost", f"{pc:.2f}+{lc:.2f} vs 总成本={tc:.2f}")
        # 范围粗检
        if pd.notna(tc) and not (100 <= tc <= 4000):
            add(idx, "range_total_cost", f"总成本={tc:.2f}")
        w = r.get("劳动日工价")
        if pd.notna(w) and not (5 <= w <= 250):
            add(idx, "range_wage", f"劳动日工价={w:.2f}")
        y = r.get("主产品产量")
        if pd.notna(y):
            lo = 5 if idx[0] == "cotton" else 20
            if not (lo <= y <= 1500):
                add(idx, "range_yield", f"主产品产量={y:.2f}")

    vdf = pd.DataFrame(viol, columns=["crop", "province", "year", "check", "detail"])

    # 接缝一致性: 玉米/小麦 总成本增长率 2005(OCR)→2006(xls), 2018(xls)→2019(OCR)
    seam_rows = []
    tc = wide["总成本"].reset_index()
    for crop in ("corn", "wheat"):
        for y0, y1 in ((2005, 2006), (2018, 2019)):
            a = tc[(tc.crop == crop) & (tc.year == y0)].set_index("province")["总成本"]
            b = tc[(tc.crop == crop) & (tc.year == y1)].set_index("province")["总成本"]
            common = a.index.intersection(b.index)
            for p in common:
                g = b[p] / a[p] - 1
                seam_rows.append({"crop": crop, "province": p, "seam": f"{y0}->{y1}",
                                  "growth": round(g, 4), "flag": abs(g) > 0.60})
    seam = pd.DataFrame(seam_rows)
    for _, r in seam[seam.flag].iterrows():
        vdf = pd.concat([vdf, pd.DataFrame([{
            "crop": r.crop, "province": r.province, "year": int(r.seam.split("->")[1]),
            "check": "seam_growth", "detail": f"{r.seam} 总成本增长 {r.growth:+.1%}"}])],
            ignore_index=True)

    return vdf, seam, n_identity, wide


# ---------------------------------------------------------------- coverage
KNOWN_GAPS = {  # 审计报告§4.1 已知OCR缺口 (crop, year) -> 描述
    ("soybean", 2019): "大豆2019 OCR续表缺页(仅~6省, 真表≈13省)",
    ("soybean", 2020): "大豆2020 OCR续表缺页(仅~6省)",
    ("soybean", 2022): "大豆2022 OCR续表缺页(仅~6省)",
    ("soybean", 2023): "大豆2023 OCR续表缺页(仅~6省)",
    ("rice_japonica", 2020): "粳稻2020 OCR续表缺页(仅~6省, 应12)",
    ("rice_mid_indica", 2020): "中籼稻2020 OCR续表缺页(仅~6省)",
    ("rice_mid_indica", 2022): "中籼稻2022 OCR续表缺页(仅~6省)",
}


def coverage(long_df):
    tc = long_df[long_df.variable == "总成本"]
    rows = []
    for (crop, year), g in tc.groupby(["crop", "year"]):
        provs = sorted(g.province.unique())
        rows.append({"crop": crop, "year": year, "n_provinces": len(provs),
                     "provinces": ";".join(provs)})
    cov = pd.DataFrame(rows).sort_values(["crop", "year"])
    return cov


# ---------------------------------------------------------------- main
def main():
    os.makedirs(os.path.dirname(OUT_LONG), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_COVER), exist_ok=True)

    print("== extracting yearly xls volumes ...")
    xls_df, nat_df = extract_xls()
    print(f"   xls rows: {len(xls_df)}")
    print("== extracting OCR long table ...")
    ocr_df = extract_ocr()
    print(f"   ocr rows: {len(ocr_df)}")

    long_df = pd.concat([xls_df, ocr_df], ignore_index=True)
    long_df["unit"] = long_df["variable"].map(UNIT_MAP)
    long_df = long_df[["crop", "province", "year", "variable", "unit", "value", "source"]]
    long_df = long_df.sort_values(["crop", "year", "province", "variable"]).reset_index(drop=True)
    dup = long_df.duplicated(["crop", "province", "year", "variable"]).sum()
    assert dup == 0, f"duplicated keys: {dup}"
    long_df.to_csv(OUT_LONG, index=False)
    nat_df["unit"] = nat_df["variable"].map(UNIT_MAP)
    nat_df[["crop", "province", "year", "variable", "unit", "value", "source"]].to_csv(
        OUT_NATIONAL, index=False)
    print(f"   total rows: {len(long_df)} -> {OUT_LONG}")

    # coverage
    cov = coverage(long_df)
    cov.to_csv(OUT_COVER, index=False)
    piv = cov.pivot_table(index="crop", columns="year", values="n_provinces", aggfunc="first")
    with open(OUT_GAPS, "w") as f:
        f.write("# OCR 覆盖缺口核实（对照审计报告§4.1）\n\n")
        f.write("覆盖矩阵（crop × year, 省份数, 按`总成本`计）：\n\n```\n")
        f.write(piv.fillna(0).astype(int).to_string() + "\n```\n\n## 已知缺口核实\n\n")
        for (crop, yr), desc in sorted(KNOWN_GAPS.items()):
            row = cov[(cov.crop == crop) & (cov.year == yr)]
            n = int(row.n_provinces.iloc[0]) if len(row) else 0
            provs = row.provinces.iloc[0] if len(row) else ""
            f.write(f"- **{crop} {yr}**: 实际 {n} 省（{provs}）。审计预期: {desc}\n")
        # 有其他科目但整年缺"总成本"的 crop-year (如 棉花2023 OCR成本收益表未入库)
        have_any = long_df.groupby(["crop", "year"]).size().index
        have_tc = set(map(tuple, cov[["crop", "year"]].values))
        missing_tc = [k for k in have_any if k not in have_tc]
        if missing_tc:
            f.write("\n## 新发现缺口: 有费用/化肥科目但整年缺`总成本`(-1表未入库)\n\n")
            for crop, yr in missing_tc:
                nv = long_df[(long_df.crop == crop) & (long_df.year == yr)].variable.nunique()
                f.write(f"- {crop} {yr}: 无总成本, 其他科目 {nv} 个\n")
        f.write("\n## 其他低覆盖 (crop-year 省数 < 同crop中位数的60%)\n\n")
        for crop, g in cov.groupby("crop"):
            med = g.n_provinces.median()
            for _, r in g[g.n_provinces < 0.6 * med].iterrows():
                if (crop, r.year) not in KNOWN_GAPS:
                    f.write(f"- {crop} {r.year}: {r.n_provinces} 省 (中位数 {med:.0f})\n")
    print(f"   coverage -> {OUT_COVER}, gaps -> {OUT_GAPS}")

    # QC
    print("== QC ...")
    vdf, seam, n_identity, wide = run_qc(long_df)
    vdf.to_csv(OUT_QC, index=False)
    id_checks = vdf[vdf.check.isin(["msf_sum", "labor_sum", "total_cost"])]
    rate = len(id_checks) / max(n_identity, 1)
    print(f"   identity checks evaluated: {n_identity}, violations: {len(id_checks)} "
          f"({rate:.2%})")
    print("   violations by type:")
    print(vdf.check.value_counts().to_string())
    flagged = seam[seam.flag]
    print(f"   seam checks: {len(seam)} province-seams, flagged(|growth|>60%): {len(flagged)}")
    if len(flagged):
        print(flagged.to_string(index=False))
    assert rate <= 0.05, f"identity violation rate {rate:.2%} > 5%"
    n_range = len(vdf[vdf.check.str.startswith("range")])
    print(f"   range violations: {n_range} (written to qc_violations.csv)")
    print("QC PASSED")
    return long_df, cov, vdf, seam


if __name__ == "__main__":
    main()
