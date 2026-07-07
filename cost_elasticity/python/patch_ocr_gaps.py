#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_ocr_gaps.py — 补录汇编OCR数据库的续表缺页 (对照 out/coverage_gaps.md)

来源: 原始PDF文本层 (pdftotext -bbox, 词级坐标)。
  - 2020/2021卷: 出版商文本层(Founder), 2020卷小数点为空词、数字全角逐字;
    2021卷为ASCII数字带小数点。
  - 2022/2023卷: OCR文本层, 数字可靠性次之 → QC重点。
  - 2024卷/2006卷: 无文本层 → 人工目视转录 (MANUAL_* 常量, 从Read PDF页图像抄录)。
产出: data/yearbook_patch_ocr_gaps.csv (schema 同 yearbook_long.csv,
      source = pdf_patch:<卷>.pdf), 只含 yearbook_long.csv 中不存在的
      (crop, province, year, variable) 组合。
QC: 恒等式(物质与服务费用分项和 2%、生产成本+土地成本≈总成本 2%)、
    相邻年份增长率>60%标记 → 打印 + out/patch_qc.csv。
"""
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_yearbook import (  # noqa: E402
    norm_text, norm_label, norm_province, is_watermark,
    PROV_SET, UNIT_MAP, K1_PER_MU, K2_VARS, MSF_COMPONENTS,
)

DATA_ROOT = "/root/data/数据/成本收益数据"
PROJ = "/root/paper/cost_elasticity"
SCRATCH = os.environ.get(
    "PATCH_SCRATCH",
    "/tmp/claude-0/-root/35855a58-2b1b-4c73-a941-25308daf893f/scratchpad/patch_bbox")
OUT_PATCH = os.path.join(PROJ, "data/yearbook_patch_ocr_gaps.csv")
OUT_QC = os.path.join(PROJ, "out/patch_qc.csv")
BASE_CSV = os.path.join(PROJ, "data/yearbook_long.csv")

# ------------------------------------------------------------------ 缺页清单
# (卷, pdf物理页, crop, 数据年, kind, 预期表号前缀)
# 页码推断: cost_benefit_tables.json 中已入库主表的 pdf_page, 续表=主表页+1;
# 均经文本层标题断言核实 (expect_id + "续表")。
PAGES = [
    # ---- 大豆 (最高优先级) ----
    ("2020", 153, "soybean", 2019, 1, "2-7-1"),
    ("2020", 155, "soybean", 2019, 2, "2-7-2"),
    ("2020", 157, "soybean", 2019, 3, "2-7-3"),
    ("2021", 152, "soybean", 2020, 1, "2-7-1"),
    ("2021", 154, "soybean", 2020, 2, "2-7-2"),
    ("2021", 156, "soybean", 2020, 3, "2-7-3"),
    ("2023", 155, "soybean", 2022, 1, "2-7-1"),
    ("2023", 157, "soybean", 2022, 2, "2-7-2"),
    ("2023", 159, "soybean", 2022, 3, "2-7-3"),
    # ---- 粳稻 2020 ----
    ("2021", 128, "rice_japonica", 2020, 1, "2-4-1"),
    ("2021", 130, "rice_japonica", 2020, 2, "2-4-2"),
    ("2021", 132, "rice_japonica", 2020, 3, "2-4-3"),
    # ---- 中籼稻 2019/2020/2022 ----
    ("2020", 117, "rice_mid_indica", 2019, 1, "2-2-1"),
    ("2020", 119, "rice_mid_indica", 2019, 2, "2-2-2"),
    ("2020", 121, "rice_mid_indica", 2019, 3, "2-2-3"),
    ("2021", 116, "rice_mid_indica", 2020, 1, "2-2-1"),
    ("2021", 118, "rice_mid_indica", 2020, 2, "2-2-2"),
    ("2021", 120, "rice_mid_indica", 2020, 3, "2-2-3"),
    ("2023", 119, "rice_mid_indica", 2022, 1, "2-2-1"),
    ("2023", 121, "rice_mid_indica", 2022, 2, "2-2-2"),
    ("2023", 123, "rice_mid_indica", 2022, 3, "2-2-3"),
    # ---- 早籼稻/晚籼稻 2019/2020, 及2022零星缺页 ----
    ("2020", 111, "rice_early_indica", 2019, 1, "2-1-1"),
    ("2020", 113, "rice_early_indica", 2019, 2, "2-1-2"),
    ("2020", 115, "rice_early_indica", 2019, 3, "2-1-3"),
    ("2020", 123, "rice_late_indica", 2019, 1, "2-3-1"),
    ("2020", 125, "rice_late_indica", 2019, 2, "2-3-2"),
    ("2020", 127, "rice_late_indica", 2019, 3, "2-3-3"),
    ("2021", 110, "rice_early_indica", 2020, 1, "2-1-1"),
    ("2021", 112, "rice_early_indica", 2020, 2, "2-1-2"),
    ("2021", 114, "rice_early_indica", 2020, 3, "2-1-3"),
    ("2021", 122, "rice_late_indica", 2020, 1, "2-3-1"),
    ("2021", 124, "rice_late_indica", 2020, 2, "2-3-2"),
    ("2021", 126, "rice_late_indica", 2020, 3, "2-3-3"),
    ("2023", 115, "rice_early_indica", 2022, 2, "2-1-2"),
    ("2023", 129, "rice_late_indica", 2022, 3, "2-3-3"),
    # ---- 玉米2019 -2续1 / 小麦2021 -2续1 / 花生2019续 ----
    ("2020", 147, "corn", 2019, 2, "2-6-2"),
    ("2022", 143, "wheat", 2021, 2, "2-5-2"),
    ("2020", 159, "peanut", 2019, 1, "2-8-1"),
    ("2020", 161, "peanut", 2019, 2, "2-8-2"),
    ("2020", 163, "peanut", 2019, 3, "2-8-3"),
]

# OCR文本层省名误识修正 (2022/2023卷)
PROV_FIX = {
    "四JII": "四川", "四JIl": "四川", "四Jll": "四川", "四JI!": "四川",
    ";可南": "河南", ";可北": "河北", "?可南": "河南", "?可北": "河北",
    "；可南": "河南", "；可北": "河北", "彳可南": "河南", "彳可北": "河北",
    "淅江": "浙江", "womenc": "", "?每南": "海南", ";每南": "海南",
}

FW = str.maketrans("０１２３４５６７８９－．", "0123456789-.")
NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


def page_words(vol, page):
    """pdftotext -bbox → [(y, x0, x1, text)]; 缓存xml。"""
    os.makedirs(SCRATCH, exist_ok=True)
    xml = os.path.join(SCRATCH, f"{vol}_p{page}.xml")
    if not os.path.exists(xml):
        subprocess.run(
            ["pdftotext", "-bbox", "-f", str(page), "-l", str(page),
             os.path.join(DATA_ROOT, f"{vol}.pdf"), xml],
            check=True, capture_output=True)
    words = []
    for m in re.finditer(
            r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" '
            r'yMax="([\d.]+)">(.*?)</word>', open(xml).read()):
        x0, y0, x1 = float(m.group(1)), float(m.group(2)), float(m.group(3))
        t = m.group(5).strip()
        # 2020卷小数点为空词或私用区字形(U+E010)
        t = re.sub(r"[-]", ".", t)
        t = "." if t == "" else t.translate(FW)
        words.append((y0, x0, x1, t))
    return words


def group_rows(words, tol=5.0):  # 2021卷行名与数值y偏移~4pt
    rows = []
    for w in sorted(words):
        if rows and abs(w[0] - rows[-1][0][0]) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w[1]) for r in rows]


NUM2_RE = re.compile(r"-?\d+\.\d{2}")


def join_cells(ws, gap=6.0):
    """按x间隙聚词成cell; 相邻列数字过宽粘连时按 两位小数 定式再切分。
    返回 [(x_center, text)]。"""
    groups = []
    for y, x0, x1, t in ws:
        if groups and x0 - groups[-1][-1][1] <= gap:
            groups[-1].append((x0, x1, t))
        else:
            groups.append([(x0, x1, t)])
    cells = []
    for g in groups:
        text = "".join(t for _, _, t in g).replace(" ", "")
        # 字符级x坐标 (词内均匀内插)
        chx = []
        for x0, x1, t in g:
            tt = t.replace(" ", "")
            n = len(tt)
            for i in range(n):
                chx.append(x0 + (x1 - x0) * (i + 0.5) / max(n, 1))
        if NUM_RE.match(text) or not re.search(r"\d", text):
            cells.append(((g[0][0] + g[-1][1]) / 2, text))
            continue
        # 粘连: 若整串恰为若干个 -?d+.dd 之连接, 则逐段拆分
        frags = NUM2_RE.findall(text)
        if "".join(frags) == text and len(frags) > 1:
            pos = 0
            for f in frags:
                xs = chx[pos:pos + len(f)]
                cells.append((float(np.mean(xs)), f))
                pos += len(f)
        else:
            cells.append(((g[0][0] + g[-1][1]) / 2, text))
    return cells


def parse_page(vol, page, crop, year, kind, expect_id):
    words = [w for w in page_words(vol, page) if not is_watermark(w[3])]
    rows = group_rows(words)
    # --- 标题断言: 表号 + 续表 (玉米/小麦-2续1为整表缺省份; 花生为主表后续页) ---
    head_txt = norm_text("".join(t for r in rows[:8] for _, _, _, t in r))
    tid = expect_id.replace("-", "")
    assert tid in head_txt.replace("-", "").replace("—", "").replace("–", ""), \
        f"table id {expect_id} not found on {vol}.pdf p{page}: {head_txt[:80]}"
    # --- 表头行: 含'单位' ---
    hdr_i, unit_x = None, None
    for i, r in enumerate(rows):
        txt = norm_text("".join(t for _, _, _, t in r))
        if "单位" in txt and ("项" in txt or "目" in txt):
            hdr_i = i
            for y, x0, x1, t in r:
                if "单位" in t:
                    unit_x = (x0 + x1) / 2
            break
    assert hdr_i is not None and unit_x is not None, f"header not found {vol} p{page}"
    val_x_min = unit_x + 18  # 值区: 单位列右侧

    # --- 数据行 → (label, [(center, numtext)]) ---
    data = []
    for r in rows[hdr_i + 1:]:
        lab = norm_text("".join(t for y, x0, x1, t in r if x1 < unit_x - 4))
        cells = join_cells([w for w in r if w[1] > val_x_min])
        cells = [(cx, t.replace(" ", "")) for cx, t in cells]
        data.append((lab, cells))

    # --- 列中心: 聚类所有数值cell ---
    centers = sorted(cx for _, cells in data for cx, t in cells if NUM_RE.match(t))
    cols = []
    for c in centers:
        if cols and c - cols[-1][-1] <= 20:
            cols[-1].append(c)
        else:
            cols.append([c])
    col_x = [float(np.mean(c)) for c in cols]

    # --- 省名: 表头行'单位'右侧词 → 就近列 ---
    hdr_cells = {}
    for y, x0, x1, t in rows[hdr_i]:
        cx = (x0 + x1) / 2
        if cx <= val_x_min - 10:
            continue
        j = int(np.argmin([abs(cx - c) for c in col_x]))
        hdr_cells.setdefault(j, []).append((x0, t))
    provs = {}
    for j, parts in hdr_cells.items():
        name = norm_text("".join(t for _, t in sorted(parts)))
        name = PROV_FIX.get(name, name)
        name = norm_province(name)
        provs[j] = name
    # 长绒棉平均及其右侧列不取; 平均列(全国)不取
    cut = min((j for j, n in provs.items() if n == "长绒棉平均"), default=None)
    keep = {}
    for j, n in provs.items():
        if cut is not None and j >= cut:
            continue
        if n in ("平均", "棉花平均"):
            continue
        if n not in PROV_SET:
            print(f"[warn] {vol} p{page}: 非省名表头列 '{n}' (col {j}) — 跳过",
                  file=sys.stderr)
            continue
        keep[j] = n
    assert keep, f"no province columns on {vol} p{page}"

    # --- 行状态机 (同 extract_yearbook.parse_sheet) ---
    out = []
    block = "per_mu"
    for lab_raw, cells in data:
        if not lab_raw:
            continue
        if kind == 1:
            if lab_raw.startswith("每50公斤"):
                block = "per50"
                continue
            if re.fullmatch(r"附[:：]?", lab_raw):
                block = "appendix"
                continue
        lab = norm_label(lab_raw)
        var = None
        if kind == 1:
            if block == "per_mu" and lab in K1_PER_MU:
                var = lab
            elif block == "per50" and lab == "平均出售价格":
                var = lab
            elif block == "appendix" and lab == "每亩用工数量":
                var = lab
        elif kind == 2 and lab in K2_VARS:
            var = lab
        elif kind == 3 and lab == "每亩化肥折纯用量":
            var = lab
        if var is None:
            continue
        for cx, t in cells:
            if not NUM_RE.match(t):
                if re.search(r"\d", t):
                    print(f"[warn] {vol} p{page} '{lab}': 非数值token '{t}'",
                          file=sys.stderr)
                continue
            j = int(np.argmin([abs(cx - c) for c in col_x]))
            if j in keep:
                out.append((crop, keep[j], year, var, float(t),
                            f"pdf_patch:{vol}.pdf", kind, page))
    return out


# ------------------------------------------------------------------ 人工转录
# 2024卷 (数据年2023) 无文本层 → 从PDF页图像目视抄录 (Read工具)。
# 格式: (crop, year, kind, page): {province: {variable: value}}
# 见 docs/patch_ocr_gaps_notes.md 转录记录。
MANUAL = {}


def manual_records():
    recs = []
    for (crop, year, kind, page, vol), provdata in MANUAL.items():
        for prov, dd in provdata.items():
            for var, val in dd.items():
                recs.append((crop, prov, year, var, float(val),
                             f"pdf_patch:{vol}.pdf", kind, page))
    return recs


# ------------------------------------------------------------------ QC
def run_qc(base, patch):
    """恒等式 + 相邻年增长率检查; 返回 DataFrame。"""
    alld = pd.concat([base, patch], ignore_index=True)
    wide = alld.pivot_table(index=["crop", "province", "year"],
                            columns="variable", values="value", aggfunc="first")
    pkeys = set(map(tuple, patch[["crop", "province", "year"]].drop_duplicates()
                    .itertuples(index=False)))
    viol = []
    for idx, row in wide.iterrows():
        if idx not in pkeys:
            continue
        crop, prov, yr = idx
        tc, pc, lc = row.get("总成本"), row.get("生产成本"), row.get("土地成本")
        if pd.notna(tc) and pd.notna(pc) and pd.notna(lc):
            rel = abs(pc + lc - tc) / tc
            if rel > 0.02:
                viol.append((crop, prov, yr, "total_cost", round(rel, 4),
                             f"生产{pc}+土地{lc} vs 总{tc}"))
        msf = row.get("物质与服务费用")
        comps = [row.get(c) for c in MSF_COMPONENTS]
        have = [c for c in comps if pd.notna(c)]
        if pd.notna(msf) and len(have) >= 10:
            rel = abs(sum(have) - msf) / msf
            if rel > 0.02:
                viol.append((crop, prov, yr, "msf_sum", round(rel, 4),
                             f"分项和{sum(have):.2f} vs {msf} (n={len(have)})"))
    # 增长率: 补录行的 总成本/主产品产量 vs 同省相邻年
    for var in ["总成本", "主产品产量", "产值合计"]:
        if var not in wide.columns:
            continue
        s = wide[var]
        for (crop, prov, yr) in pkeys:
            v = s.get((crop, prov, yr))
            if pd.isna(v):
                continue
            for dy in (-1, 1):
                v2 = s.get((crop, prov, yr + dy))
                if v2 is not None and pd.notna(v2) and v2 > 0:
                    g = v / v2 - 1
                    if abs(g) > 0.6:
                        viol.append((crop, prov, yr, f"growth_{var}", round(g, 3),
                                     f"{yr}={v} vs {yr+dy}={v2}"))
    return pd.DataFrame(viol, columns=["crop", "province", "year",
                                       "check", "value", "detail"])


def main():
    recs = []
    for vol, page, crop, year, kind, tid in PAGES:
        got = parse_page(vol, page, crop, year, kind, tid)
        provs = sorted({r[1] for r in got})
        print(f"{vol}.pdf p{page} {crop} {year} k{kind}: "
              f"{len(got)} 值, 省: {'/'.join(provs)}")
        recs += got
    recs += manual_records()
    df = pd.DataFrame(recs, columns=["crop", "province", "year", "variable",
                                     "value", "source", "_kind", "_page"])
    # -1/-2重名科目取-1
    df.sort_values(["crop", "province", "year", "variable", "_kind"],
                   inplace=True, kind="mergesort")
    df = df.drop_duplicates(["crop", "province", "year", "variable"], keep="first")
    # 与已有库去重
    base = pd.read_csv(BASE_CSV)
    have = set(map(tuple, base[["crop", "province", "year", "variable"]]
                   .itertuples(index=False)))
    mask = [t not in have for t in
            df[["crop", "province", "year", "variable"]].itertuples(index=False, name=None)]
    dropped = len(df) - sum(mask)
    df = df[mask].copy()
    df["unit"] = df["variable"].map(UNIT_MAP)
    out = df[["crop", "province", "year", "variable", "unit", "value", "source"]]
    out = out.sort_values(["crop", "year", "province", "variable"])
    out.to_csv(OUT_PATCH, index=False)
    print(f"\n补录 {len(out)} 行 → {OUT_PATCH} (与库重复剔除 {dropped} 行)")
    cov = out[out.variable == "总成本"].groupby(["crop", "year"])["province"].nunique()
    print("新增(总成本)省数:\n", cov.to_string())

    qc = run_qc(base, out)
    qc.to_csv(OUT_QC, index=False)
    npk = out[["crop", "province", "year"]].drop_duplicates().shape[0]
    print(f"\nQC: 补录 crop×省×年 组合 {npk} 个, 违规/标记 {len(qc)} 条 → {OUT_QC}")
    if len(qc):
        print(qc.to_string(index=False))


if __name__ == "__main__":
    main()
