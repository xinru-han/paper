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


# ------------------------------------------------------------------ MD补录
# 2005/2006卷 (数据年2004/2005) 的续表内容在 mineru md 中以"同一<table>内第二个
# 表头行(项目|单位|省...)"形式存在, database构建时只用了首个表头 → 从md直接补。
MD_DIR = os.path.join(DATA_ROOT, "mineru_ocr_output")
MD_TABLES = [
    # (md卷, crop, 数据年, kind, 标题正则)
    ("2005", "soybean", 2004, 1, r"^2-9-1\s*2004年各地区大豆成本收益情况"),
    ("2005", "soybean", 2004, 2, r"^2-9-2\s*2004年各地区大豆费用和用工情况"),
    ("2005", "soybean", 2004, 3, r"^2-9-3\s*2004年各地区大豆化肥投入情况"),
    ("2005", "peanut", 2004, 1, r"^2-10-1\s*2004年各地区花生成本收益情况"),
    ("2005", "peanut", 2004, 2, r"^2-10-2\s*2004年各地区花生费用和用工情况"),
    ("2005", "peanut", 2004, 3, r"^2-10-3\s*2004年各地区花生化肥投入情况"),
    ("2006", "soybean", 2005, 1, r"^2-9-1\s*2005年各地区大豆成本收益情况"),
    ("2006", "soybean", 2005, 2, r"^2-9-2\s*2005年各地区大豆费用和用工情况"),
    ("2006", "soybean", 2005, 3, r"^2-9-3\s*2005年各地区大豆化肥投入情况"),
    ("2006", "rice_early_indica", 2005, 1, r"^2-1-1\s*2005年各地区早籼稻成本收益情况"),
    ("2006", "rice_early_indica", 2005, 2, r"^2-1-2\s*2005年各地区早籼稻费用和用工情况"),
    ("2006", "rice_early_indica", 2005, 3, r"^2-1-3\s*2005年各地区早籼稻化肥投入情况"),
    ("2006", "rice_late_indica", 2005, 1, r"^2-3-1\s*2005年各地区晚籼稻成本收益情况"),
    ("2006", "rice_late_indica", 2005, 2, r"^2-3-2\s*2005年各地区晚籼稻费用和用工情况"),
    ("2006", "rice_late_indica", 2005, 3, r"^2-3-3\s*2005年各地区晚籼稻化肥投入情况"),
    ("2006", "rice_japonica", 2005, 2, r"^2-4-2\s*2005年各地区粳稻费用和用工情况"),
    ("2006", "rice_japonica", 2005, 3, r"^2-4-3\s*2005年各地区粳稻化肥投入情况"),
]
HEADING_RE = re.compile(r"^\d-\d+-\d|^#")


def parse_md_table(vol, crop, year, kind, title_re):
    lines = open(os.path.join(MD_DIR, f"{vol}.md")).read().split("\n")
    start = None
    pat = re.compile(title_re)
    for i, l in enumerate(lines):
        if pat.match(l.strip()) and "……" not in l:
            start = i
            break
    assert start is not None, f"md heading not found: {vol} {title_re}"
    tables = []
    for l in lines[start + 1:]:
        s = l.strip()
        if HEADING_RE.match(s):
            break
        if s.startswith("<table>"):
            tables.append(s)
    out = []
    for html in tables:
        provs, block = [], "per_mu"
        for tr in re.findall(r"<tr>(.*?)</tr>", html):
            cells = [norm_text(re.sub(r"<[^>]+>", "", c))
                     for c in re.findall(r"<td[^>]*>(.*?)</td>", tr)]
            if not cells or is_watermark("".join(cells)):
                continue
            if cells[0] == "项目":  # (内嵌)表头行 → 新省份块
                provs = [(j, norm_province(c)) for j, c in enumerate(cells[2:], 2)
                         if c and norm_province(c) in PROV_SET]
                block = "per_mu"
                continue
            lab_raw = cells[0]
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
            for j, prov in provs:
                if j >= len(cells):
                    continue
                try:
                    v = float(cells[j])
                except ValueError:
                    continue
                out.append((crop, prov, year, var, v,
                            f"md_patch:{vol}.md", kind, -1))
    return out


# ------------------------------------------------------------------ 人工转录
# 2024卷 (数据年2023) 无文本层 → 从PDF页图像 (pdftoppm 200dpi) 目视抄录。
# 每块: 行内恒等式已逐省验证 (生产成本+土地成本=总成本; 物质+人工=生产成本;
# 家庭用工折价+雇工费用=人工成本; 直接分项和=直接费用; 见notes)。None=原表空白。
MANUAL = [
    dict(vol="2024", page=154, crop="soybean", year=2023, kind=1,
         provs=["江苏", "安徽", "山东", "河南", "湖北", "四川", "陕西"],
         vars={
             "主产品产量": [168.94, 157.91, 202.09, 154.66, 176.13, 122.53, 131.75],
             "产值合计": [996.10, 881.40, 1296.17, 854.09, 1073.77, 723.67, 834.86],
             "主产品产值": [982.38, 858.52, 1276.06, 841.37, 1059.84, 722.05, 813.62],
             "总成本": [1062.39, 782.72, 886.40, 827.76, 661.03, 693.00, 897.00],
             "生产成本": [782.91, 462.29, 661.87, 502.91, 560.36, 578.03, 803.84],
             "物质与服务费用": [186.77, 255.53, 242.30, 231.96, 304.99, 78.31, 218.17],
             "人工成本": [596.14, 206.76, 419.57, 270.95, 255.37, 499.72, 585.67],
             "家庭用工折价": [578.21, 202.24, 411.07, 249.06, 255.37, 497.26, 585.67],
             "雇工费用": [17.93, 4.53, 8.50, 21.89, None, 2.47, None],
             "土地成本": [279.48, 320.43, 224.53, 324.85, 100.67, 114.97, 93.16],
             "流转地租金": [49.16, 74.12, 3.50, 94.12, 8.42, 1.95, 0.56],
             "自营地折租": [230.32, 246.31, 221.03, 230.73, 92.25, 113.02, 92.60],
             "平均出售价格": [290.75, 271.84, 315.72, 272.01, 300.87, 294.64, 308.77],
             "每亩用工数量": [6.15, 2.12, 4.34, 2.77, 2.63, 5.16, 6.04],
         }),
    dict(vol="2024", page=156, crop="soybean", year=2023, kind=2,
         provs=["江苏", "安徽", "山东", "河南", "湖北", "四川", "陕西"],
         vars={
             "种子费": [64.82, 71.22, 46.98, 61.92, 111.62, 36.63, 42.09],
             "化肥费": [34.80, 24.66, 52.90, 25.12, 54.54, 8.10, 53.76],
             "农家肥费": [7.17, 13.25, 3.60, 12.47, 6.64, 0.07, 1.05],
             "农药费": [37.56, 37.32, 35.61, 47.11, 9.86, 13.10, 6.98],
             "机械作业费": [22.55, 75.94, 70.25, 75.39, 108.19, 9.21, 101.42],
             "排灌费": [3.36, 4.31, 18.33, 0.26, None, None, 5.25],
             "燃料动力费": [None, 5.19, 0.13, None, 5.93, 0.04, None],
             "工具材料费": [2.85, 2.30, 2.50, 4.43, 2.65, 3.34, 2.45],
             "修理维护费": [1.10, 1.68, 2.08, None, 1.30, 1.56, 2.49],
             "固定资产折旧": [3.82, 5.79, 3.08, None, 4.26, 2.96, 2.68],
             "保险费": [8.74, 11.71, 6.84, 5.26, None, None, None],
             "财务费": [None, 0.59, None, None, None, None, None],
             "销售费": [None, 1.57, None, None, None, 3.30, None],
             "家庭用工天数": [5.96, 2.09, 4.24, 2.57, 2.63, 5.13, 6.04],
             "劳动日工价": [96.95, 96.95, 96.95, 96.95, 96.95, 96.95, 96.95],
             "雇工天数": [0.18, 0.04, 0.10, 0.20, None, 0.03, None],
             "雇工工价": [97.45, 122.35, 89.45, 108.36, 141.34, 85.10, 117.07],
             "每亩种子用量": [5.66, 6.08, 4.60, 5.22, 6.66, 5.37, 5.69],
             "每亩化肥用量": [4.47, 3.25, 7.39, 3.32, 6.83, 0.90, 8.46],
         }),
    dict(vol="2024", page=158, crop="soybean", year=2023, kind=3,
         provs=["江苏", "安徽", "山东", "河南", "湖北", "四川", "陕西"],
         vars={"每亩化肥折纯用量": [4.47, 3.25, 7.39, 3.32, 6.83, 0.90, 8.46]}),
    dict(vol="2024", page=117, crop="rice_mid_indica", year=2023, kind=2,
         provs=["湖南", "广西", "重庆", "四川", "贵州", "云南", "陕西"],
         vars={
             "物质与服务费用": [651.88, 642.09, 484.26, 474.92, 485.06, 527.25, 445.04],
             "种子费": [72.60, 109.53, 70.30, 89.51, 71.01, 106.80, 70.65],
             "化肥费": [154.27, 199.75, 124.72, 148.43, 145.57, 132.06, 146.77],
             "农家肥费": [0.64, 27.61, 7.23, 12.11, 11.15, 8.16, 5.79],
             "农药费": [86.66, 49.10, 24.54, 22.63, 28.61, 49.42, 14.73],
             "农膜费": [0.63, 0.75, 6.98, 11.94, 6.78, 3.55, 2.32],
             "机械作业费": [276.24, 195.07, 193.29, 142.12, 149.15, 143.12, 156.38],
             "排灌费": [11.38, 1.57, 0.16, 15.63, 4.57, 16.56, 38.44],
             "畜力费": [None, 7.02, 5.07, 0.21, 12.70, 46.02, None],
             "燃料动力费": [3.42, 26.57, 13.68, 1.37, 16.52, 2.56, None],
             "工具材料费": [3.31, 8.24, 7.16, 4.01, 7.44, 9.85, 2.50],
             "修理维护费": [2.33, 5.71, 1.69, 2.27, 2.98, None, 2.43],
             "其他直接费用": [0.14, None, None, None, 0.18, 0.09, None],
             "固定资产折旧": [8.65, 11.17, 17.49, 6.87, 24.86, None, 5.03],
             "保险费": [31.52, None, 11.84, 16.17, 3.54, 8.72, None],
             "管理费": [None, None, None, 0.70, None, None, None],
             "财务费": [None, None, None, 0.15, None, None, None],
             "销售费": [0.09, None, 0.11, 0.80, None, 0.34, None],
             "人工成本": [373.28, 597.43, 690.85, 803.73, 993.82, 1041.33, 1120.25],
             "家庭用工折价": [325.46, 547.19, 683.69, 758.73, 929.94, 928.59, 1096.89],
             "家庭用工天数": [3.36, 5.64, 7.05, 7.83, 9.59, 9.58, 11.31],
             "劳动日工价": [96.95, 96.95, 96.95, 96.95, 96.95, 96.95, 96.95],
             "雇工费用": [47.82, 50.24, 7.15, 45.00, 63.87, 112.74, 23.36],
             "雇工天数": [0.27, 0.37, 0.04, 0.39, 0.53, 0.93, 0.19],
             "雇工工价": [179.77, 137.65, 188.26, 115.97, 121.43, 120.71, 121.04],
             "每亩种子用量": [1.35, 1.20, 0.59, 0.96, 0.68, 1.63, 0.85],
             "每亩化肥用量": [20.65, 24.15, 15.02, 17.64, 17.63, 16.55, 20.86],
             "每亩农膜用量": [0.04, 0.05, 0.48, 0.82, 0.46, 0.24, 0.17],
         }),
    # 棉花2023 -1表: 主表页(平均/河北/江苏/安徽/江西, 书页169)在PDF中物理缺失,
    # 仅能补 续表1(p175, 书页170) + 续表2(p176, 书页171, 长绒棉列不取)。
    dict(vol="2024", page=175, crop="cotton", year=2023, kind=1,
         provs=["山东", "河南", "湖北", "湖南"],
         vars={
             "主产品产量": [102.19, 98.85, 66.63, 75.93],
             "产值合计": [2225.67, 1993.61, 1377.48, 1720.65],
             "主产品产值": [1732.54, 1544.30, 1066.39, 1264.52],
             "总成本": [2894.91, 2670.51, 2343.47, 3032.51],
             "生产成本": [2594.70, 2279.97, 2105.81, 2834.22],
             "物质与服务费用": [550.14, 389.44, 492.22, 517.12],
             "人工成本": [2044.56, 1890.53, 1613.59, 2317.10],
             "家庭用工折价": [2013.94, 1890.53, 1552.46, 2234.60],
             "雇工费用": [30.62, None, 61.13, 82.50],
             "土地成本": [300.21, 390.54, 237.66, 198.29],
             "流转地租金": [5.13, 65.55, 28.20, 18.28],
             "自营地折租": [295.08, 324.99, 209.46, 180.01],
             "平均出售价格": [847.71, 781.13, 800.23, 832.69],
             "每亩用工数量": [21.08, 19.50, 16.49, 23.60],
         }),
    dict(vol="2024", page=176, crop="cotton", year=2023, kind=1,
         provs=["陕西", "甘肃", "新疆"],
         vars={
             "主产品产量": [64.25, 115.10, 144.46],
             "产值合计": [1338.14, 2788.11, 2943.83],
             "主产品产值": [1065.83, 2168.95, 2354.20],
             "总成本": [3317.47, 2378.37, 2492.85],
             "生产成本": [3217.47, 2166.63, 1786.94],
             "物质与服务费用": [450.90, 832.73, 1259.15],
             "人工成本": [2766.57, 1333.90, 527.79],
             "家庭用工折价": [2766.57, 1193.36, 253.91],
             "雇工费用": [None, 140.54, 273.88],
             "土地成本": [100.00, 211.74, 705.91],
             "流转地租金": [0.94, 1.92, 237.03],
             "自营地折租": [99.06, 209.82, 468.88],
             "平均出售价格": [829.44, 942.20, 814.83],
             "每亩用工数量": [28.54, 13.19, 4.55],
         }),
    # 2005卷p252 (书页239) 2-9-1续表: 大豆2004 -1表 (md中该页块缺失, 仅k2/k3有)
    dict(vol="2005", page=252, crop="soybean", year=2004, kind=1,
         provs=["安徽", "山东", "河南", "湖北", "重庆", "云南", "陕西"],
         vars={
             "主产品产量": [129.60, 152.90, 119.10, 147.10, 117.00, 129.40, 114.40],
             "产值合计": [418.27, 552.72, 383.90, 526.59, 454.03, 439.28, 355.48],
             "主产品产值": [392.23, 543.89, 373.09, 505.24, 439.11, 429.64, 349.03],
             "总成本": [205.26, 228.36, 179.59, 326.29, 286.80, 355.73, 245.53],
             "生产成本": [175.93, 188.55, 141.73, 295.18, 264.99, 314.76, 206.13],
             "物质与服务费用": [89.51, 104.25, 66.38, 154.07, 86.92, 126.91, 96.38],
             "人工成本": [86.42, 84.30, 75.35, 141.11, 178.07, 187.85, 109.75],
             "家庭用工折价": [82.75, 83.98, 75.35, 141.11, 176.87, 184.27, 103.57],
             "雇工费用": [3.67, 0.32, None, None, 1.20, 3.58, 6.18],
             "土地成本": [29.33, 39.81, 37.86, 31.11, 21.81, 40.97, 39.40],
             "流转地租金": [1.20, None, 3.17, 2.18, 2.39, 4.00, 4.61],
             "自营地折租": [28.13, 39.81, 34.69, 28.93, 19.42, 36.97, 34.79],
             "平均出售价格": [151.32, 177.86, 156.63, 171.73, 187.65, 166.01, 152.55],
             "每亩用工数量": [6.22, 6.15, 5.50, 10.30, 12.95, 13.76, 7.93],
         }),
    # 2006卷p216 (书页203) 2-4-2续表1: 粳稻2005 -2表 (md缺此页块)
    dict(vol="2006", page=216, crop="rice_japonica", year=2005, kind=2,
         provs=["吉林", "黑龙江", "上海", "江苏", "浙江", "安徽"],
         vars={
             "物质与服务费用": [250.06, 281.88, 323.72, 379.30, 324.87, 263.49],
             "种子费": [18.60, 14.87, 18.03, 19.41, 12.62, 19.83],
             "化肥费": [77.19, 71.84, 90.43, 131.24, 95.30, 97.03],
             "农家肥费": [9.21, 0.17, 0.08, 6.19, 4.35, 5.56],
             "农药费": [14.03, 12.09, 79.01, 85.20, 86.35, 43.21],
             "农膜费": [15.59, 11.44, None, 1.31, None, 4.05],
             "机械作业费": [43.58, 63.91, 103.52, 83.17, 95.75, 29.55],
             "排灌费": [46.23, 38.90, 30.21, 38.27, 14.12, 17.32],
             "畜力费": [10.74, 0.27, None, 0.68, 1.18, 23.20],
             "燃料动力费": [None, 0.02, None, 0.54, 0.56, 0.17],
             "技术服务费": [0.17, 0.70, None, None, 0.15, None],
             "工具材料费": [2.03, 2.40, 0.46, 2.94, 1.11, 8.15],
             "修理维护费": [1.02, 4.06, None, 1.54, 1.87, 5.19],
             "其他直接费用": [0.91, 9.89, 1.45, 2.02, 1.67, 3.10],
             "固定资产折旧": [5.40, 8.57, None, 5.22, 6.83, 5.84],
             "保险费": [None, 9.10, None, 0.12, None, None],
             "管理费": [0.75, 18.65, None, 0.12, 2.27, 0.41],
             "财务费": [1.35, 10.89, None, 0.01, 0.03, None],
             "销售费": [3.26, 4.11, 0.53, 1.32, 0.71, 0.88],
             "人工成本": [138.93, 140.37, 100.67, 141.81, 110.74, 171.58],
             "家庭用工折价": [100.52, 75.12, 100.67, 126.68, 86.60, 165.24],
             "家庭用工天数": [6.57, 4.91, 6.58, 8.28, 5.66, 10.80],
             "劳动日工价": [15.30, 15.30, 15.30, 15.30, 15.30, 15.30],
             "雇工费用": [38.41, 65.25, None, 15.13, 24.14, 6.34],
             "雇工天数": [1.56, 1.93, None, 0.45, 0.62, 0.21],
             "雇工工价": [24.62, 33.81, 31.84, 33.62, 38.94, 30.19],
             "每亩种子用量": [3.70, 4.62, 5.87, 4.13, 3.65, 5.28],
             "每亩化肥用量": [15.08, 15.26, 22.65, 31.69, 22.67, 22.62],
             "每亩农膜用量": [1.30, 1.16, None, 0.12, None, 0.43],
         }),
]


def manual_records():
    recs = []
    for blk in MANUAL:
        for var, vals in blk["vars"].items():
            assert len(vals) == len(blk["provs"]), \
                f"manual length mismatch {blk['vol']} p{blk['page']} {var}"
            for prov, val in zip(blk["provs"], vals):
                if val is None:
                    continue
                recs.append((blk["crop"], prov, blk["year"], var, float(val),
                             f"pdf_patch:{blk['vol']}.pdf", blk["kind"], blk["page"]))
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
    for vol, crop, year, kind, tre in MD_TABLES:
        got = parse_md_table(vol, crop, year, kind, tre)
        provs = sorted({r[1] for r in got})
        print(f"{vol}.md {crop} {year} k{kind}: {len(got)} 值, 省: {'/'.join(provs)}")
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
