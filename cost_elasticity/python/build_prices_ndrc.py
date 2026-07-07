# -*- coding: utf-8 -*-
"""
build_prices_ndrc.py — 发改委价格监测数据 -> 省×年 农资价格面板
================================================================
可重跑的确定性脚本。从 /root/data/数据/发改委价格数据/ 原始 zip/csv 出发，
解压到 scratchpad 临时目录，按 docs/data_audit_ndrc.md §4 的清洗规则产出：

  data/prices_ndrc_annual.csv      province, year, item, unit, price, n_periods
  data/price_construction_log.csv  每个 item 的来源/口径/合并规则/覆盖/缺口

数据源（代号见审计报告）：
  A  农业生产资料价格200304-2010.xls          真xls，实际 2003.04–2006.07，县级
  B  农业生产资料20060701-20101231.csv        UTF-8-BOM CSV，监测点级（百草枯行错位需修复）
  C  农机用油----饲料及仔猪---20060701-20101231.zip  HTML伪xls，柴油/仔猪/豆粕/麦麸
  D  农业生产资料价格20110105-20231115.xls    GB18030 TSV 伪xls，县级，2011–2023.11
  E  202311-202312真xls + 旬报任务2024-2025 zip(HTML伪xls)，监测点级
  G  农村居民服务价格2003–2024.3 月报          机耕费/机收费（元/亩）

清洗规则要点：
  - 品种×规格 -> 统一 item（磷酸二铵两代命名合并；过钙16%/硫基复合肥不并入基准序列）
  - 县->省映射：由 B/E 完整路径构建 + 33 条手工补充（2003–06 已停报监测县）
  - 剔除 采报价单位名称=="总平均"、价格<=0/缺失
  - 异常值：item×期 全国截面 log 价格 MAD 稳健 z(|z|>5) 剔除 + 硬边界（尿素/柴油）
  - 聚合：期(旬/周/月)×县 采价点中位数 -> 期×省 县中位数 -> 年 = 各期简单平均
  - 单位：元/千克==元/公斤；仔猪 元/500克 ×2 -> 元/公斤；机械服务 元/亩
"""

import csv
import glob
import io
import os
import re
import subprocess

import numpy as np
import pandas as pd

RAW = "/root/data/数据/发改委价格数据"
WORK = "/tmp/claude-0/-root/35855a58-2b1b-4c73-a941-25308daf893f/scratchpad/ndrc_build"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")

ZIP_MAIN = os.path.join(RAW, "00000000-中国农业科学院农业经济与发展研究所(2).zip")
ZIP_NJYY = os.path.join(RAW, "农机用油----饲料及仔猪---20060701-20101231.zip")
ZIP_XB24 = os.path.join(RAW, "农业生产资料价格旬报监测任务20240101-20251231.zip")
CSV_B = os.path.join(RAW, "农业生产资料20060701-20101231.csv")

MAD_Z = 5.0
HARD_BOUNDS = {  # item -> (min, max) in output unit
    "urea": (0.8, 4.0),      # 元/公斤
    "diesel": (1.0, 15.0),   # 元/公斤
}

# ---------------------------------------------------------------- item map
# (品种, 规格前缀匹配) -> item ；规格为 None 表示不区分规格
ITEM_RULES = [
    ("尿素", "含氮46% 国产", "urea", "元/公斤"),
    ("碳酸氢铵", None, "abc", "元/公斤"),            # 含氮17%（,国产）两代写法合并
    ("过磷酸钙", "含磷12%", "ssp", "元/公斤"),        # 12% 基准；16% 不并入
    ("磷酸二铵", "含氮磷总量64%", "dap", "元/公斤"),   # 两代命名"...64%"/"...64%,国产"合并
    ("三元复合肥", "氯基", "npk_cl", "元/公斤"),      # 硫基(2013+)不并入
    ("地膜", None, "mulch_film", "元/公斤"),
    ("棚膜", None, "greenhouse_film", "元/公斤"),
    ("毒死蜱", None, "chlorpyrifos", "元/500克"),     # 480克/升乳油瓶装，全期一致口径
    ("农用柴油", None, "diesel", "元/公斤"),          # 仅 2006–2010
    ("氯化钾", "含氧化钾 60%", "kcl", "元/公斤"),     # 国产+进口合并，仅 2006–2010
    ("仔猪", None, "piglet", "元/公斤"),             # 原始 元/500克 ×2
    ("豆粕", None, "soymeal", "元/公斤"),
    ("麦麸", None, "wheat_bran", "元/公斤"),         # 原始 元/500克 ×2
]

# 县->省 手工补充（2003–2006 已停报或路径缺失的监测县；由地名归属确定）
HAND_MAP = {
    "临川市": "江西", "伊犁州": "新疆", "兴平市": "陕西", "吴忠市": "宁夏",
    "宁波市": "浙江", "安庆市": "安徽", "官渡区": "云南", "宣城市宣州区": "安徽",
    "宿州市埇桥区": "安徽", "平凉市": "甘肃", "彭泽县": "江西", "昌吉州": "新疆",
    "曲江区": "广东", "望城县": "湖南", "樟树市": "江西", "永城市": "河南",
    "汉寿县": "湖南", "湛江市": "广东", "滁州市": "安徽", "潜山县": "安徽",
    "石嘴山市": "宁夏", "绍兴市": "浙江", "苏家屯区": "辽宁", "蚌埠市": "安徽",
    "通辽市": "内蒙古", "都昌县": "江西", "鄂尔多斯市": "内蒙古", "酒泉市": "甘肃",
    "金华市": "浙江", "韶关市": "广东", "高安市": "江西",
    "南昌县": "江西", "衡阳市": "湖南",
}


def log(msg):
    print(f"[build_prices_ndrc] {msg}", flush=True)


def norm_prov(s):
    return re.sub(r"(回族|壮族|维吾尔)?(自治区|省)$", "",
                  str(s).strip()).replace("重庆市", "重庆")


def norm_txt(x):
    return re.sub(r"[\s　\"]+", " ", str(x)).strip().strip('"').strip()


def extract_zips():
    os.makedirs(WORK, exist_ok=True)
    for zp, sub in [(ZIP_MAIN, "main"), (ZIP_NJYY, "njyy"), (ZIP_XB24, "xb24")]:
        dst = os.path.join(WORK, sub)
        if not os.path.isdir(dst):
            log(f"extracting {os.path.basename(zp)} -> {sub}/")
            # 系统 unzip 能正确处理 GBK 文件名（zipfile 会得到 cp437 乱码）
            subprocess.run(["unzip", "-o", "-q", zp, "-d", dst], check=True)
    return {s: glob.glob(os.path.join(WORK, s, "*", ""))[0]
            for s in ("main", "njyy", "xb24")}


# ---------------------------------------------------------------- sources
def read_A(main_dir):
    """2003.04–2006.07 真xls，县级。丢弃与 B 重叠的 20060705。"""
    df = pd.read_excel(os.path.join(main_dir, "农业生产资料价格200304-2010.xls"),
                       dtype={"   期号   ": str})
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"机构": "county_raw", "零售价格": "price"})
    df["date"] = df["期号"].astype(float).astype(int).astype(str)
    df = df[df["date"] != "20060705"]
    for c in ("county_raw", "品种", "规格", "单位"):
        df[c] = df[c].map(norm_txt)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["point"] = ""
    df["prov"] = np.nan
    return df[["date", "prov", "county_raw", "point", "品种", "规格", "单位", "price"]], "A"


def read_B():
    """2006.07–2010 监测点级 CSV（utf-8-sig；百草枯品种名含逗号导致错位，按规则重排）。"""
    rows = []
    with open(CSV_B, encoding="utf-8-sig", newline="") as f:
        for r in csv.reader(f):
            if len(r) != 7:
                continue
            if not r[0][:8].isdigit():  # scrambled row: 期号在第5列
                r = [r[4], r[1], r[2] + "," + r[0], "", r[3], r[5], r[6]]
            rows.append(r)
    df = pd.DataFrame(rows, columns=["date", "region", "品种", "规格", "单位", "point", "price"])
    parts = df["region"].str.split("-")
    df["prov"] = parts.str[1].map(norm_prov)
    df["county_raw"] = parts.str[-1].map(norm_txt)
    for c in ("品种", "规格", "单位", "point"):
        df[c] = df[c].map(norm_txt)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    return df[["date", "prov", "county_raw", "point", "品种", "规格", "单位", "price"]], "B"


def _read_task_html(path):
    return pd.read_html(path)[0]


def read_C(njyy_dir):
    """2006–2010 农机用油/饲料/仔猪，HTML伪xls，监测点级。"""
    frames = []
    for f in sorted(glob.glob(os.path.join(njyy_dir, "*.xls"))):
        frames.append(_read_task_html(f))
    df = pd.concat(frames, ignore_index=True)
    return _from_task_schema(df), "C"


def read_D(main_dir):
    """2011.01–2023.11 GB18030 TSV 伪xls，县级。"""
    raw = open(os.path.join(main_dir, "农业生产资料价格20110105-20231115.xls"), "rb").read()
    df = pd.read_csv(io.StringIO(raw.decode("gb18030")), sep="\t", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"机构": "county_raw", "零售价格": "price", "期号": "date",
                            "采价点": "point"})
    for c in ("county_raw", "品种", "规格", "单位", "point", "date"):
        df[c] = df[c].map(norm_txt)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["date"].str.fullmatch(r"\d{8}")]  # 去掉行数统计等脚注行
    df["prov"] = np.nan
    return df[["date", "prov", "county_raw", "point", "品种", "规格", "单位", "price"]], "D"


def _from_task_schema(df):
    """任务/期号/监测点/品种/规格/品种单位/(采报价单位名称)/价格 格式 -> 标准列。"""
    df = df.rename(columns={"品种单位": "单位", "期号": "date", "价格": "price"})
    if "采报价单位名称" in df.columns:
        df = df[df["采报价单位名称"].astype(str).str.strip() != "总平均"]
        df["point"] = df["采报价单位名称"].map(norm_txt)
    else:
        df["point"] = ""
    parts = df["监测点"].astype(str).str.split("-")
    df["prov"] = parts.str[1].map(norm_prov)
    df["county_raw"] = parts.str[-1].map(norm_txt)
    for c in ("品种", "规格", "单位"):
        df[c] = df[c].fillna("").map(norm_txt)
    df["date"] = df["date"].astype(str).str.strip()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    return df[["date", "prov", "county_raw", "point", "品种", "规格", "单位", "price"]]


def read_E(main_dir, xb24_dir):
    """2023.11–2025 尾段：真xls(2023.11-12) + 2024–2025 HTML 伪xls 旬/周报。"""
    frames = [pd.read_excel(os.path.join(main_dir, "农业生产资料价格202311-202312.xls"))]
    for f in sorted(glob.glob(os.path.join(xb24_dir, "*.xls"))):
        frames.append(_read_task_html(f))
    df = pd.concat(frames, ignore_index=True)
    return _from_task_schema(df), "E"


# ---------------------------------------------------------------- services (G)
def read_G(main_dir):
    """农村居民服务价格月报 -> 机耕费/机收费（元/亩），县级月度。
    三种历史 schema；2012 文件列名为 GBK 被误读 latin1 的乱码，需重解码。"""
    recs = []
    for f in sorted(glob.glob(os.path.join(main_dir, "农村居民服务价格*"))):
        try:
            d = pd.read_excel(f)
        except Exception:
            try:
                d = pd.read_html(f)[0]
            except Exception as e:  # pragma: no cover
                log(f"  G skip {os.path.basename(f)}: {e}")
                continue
        # 修复 latin1<-gbk 乱码列名/值（2012 文件）
        if not any(("品种" in str(c)) or ("商品名称" in str(c)) for c in d.columns):
            def refix(x):
                try:
                    return str(x).encode("latin1").decode("gbk")
                except Exception:
                    return str(x)
            d.columns = [refix(c) for c in d.columns]
            for c in d.columns:
                if d[c].dtype == object:
                    d[c] = d[c].map(refix)
        icol = "品种" if "品种" in d.columns else ("商品名称" if "商品名称" in d.columns else None)
        if icol is None:
            continue
        it = d[icol].astype(str).map(norm_txt)
        sel = it.str.contains("农机作业费|农业作业费")
        if not sel.any():
            continue
        d = d[sel].copy()
        d["item_cn"] = it[sel]
        scol = "规格" if "规格" in d.columns else "规格等级"
        d["spec"] = d[scol].astype(str).map(norm_txt)
        dcol = next(c for c in ("期号", "报告期", "报告时间") if c in d.columns)
        d["date"] = d[dcol].astype(str).str.replace(r"\.0$", "", regex=True).str[:8]
        if "监测点" in d.columns:
            parts = d["监测点"].astype(str).str.split("-")
            d["prov"] = np.where(parts.str.len() > 1, parts.str[1].map(norm_prov), np.nan)
            d["county_raw"] = parts.str[-1].map(norm_txt)
        else:  # 地区 = 县名
            d["prov"] = np.nan
            d["county_raw"] = d["地区"].astype(str).map(norm_txt)
        d["point"] = d["采价点"].map(norm_txt) if "采价点" in d.columns else ""
        d["price"] = pd.to_numeric(d["价格"], errors="coerce")
        recs.append(d[["date", "prov", "county_raw", "point", "item_cn", "spec", "price"]])
    g = pd.concat(recs, ignore_index=True)
    g["item"] = np.where(g["spec"].str.contains("机耕"), "machine_tillage",
                np.where(g["spec"].str.contains("机收"), "machine_harvest", None))
    g = g[g["item"].notna() & (g["price"] > 0)]
    g["unit"] = "元/亩"
    return g


# ---------------------------------------------------------------- pipeline
def map_items(df):
    out = []
    for pz, spec, item, unit in ITEM_RULES:
        m = df["品种"] == pz
        if spec is not None:
            m &= df["规格"].str.startswith(spec)
        sub = df[m].copy()
        if sub.empty:
            continue
        sub["item"] = item
        sub["unit"] = unit
        # 单位换算：元/500克 -> 元/公斤（仔猪、麦麸；毒死蜱保留原口径单位）
        conv = sub["单位"].str.contains("500克") & sub["item"].isin(["piglet", "wheat_bran"])
        sub.loc[conv, "price"] *= 2.0
        out.append(sub)
    return pd.concat(out, ignore_index=True)


def drop_outliers(df):
    """item×期 全国截面 log 价格 MAD 稳健 z 剔除 + 硬边界。"""
    df = df[df["price"] > 0].copy()
    for item, (lo, hi) in HARD_BOUNDS.items():
        m = df["item"] == item
        df = df[~m | (df["price"].between(lo, hi))]
    lp = np.log(df["price"])
    med = lp.groupby([df["item"], df["date"]]).transform("median")
    mad = (lp - med).abs().groupby([df["item"], df["date"]]).transform("median")
    z = 0.6745 * (lp - med) / mad.replace(0, np.nan)
    keep = z.abs().fillna(0) <= MAD_Z
    log(f"  MAD outliers dropped: {(~keep).sum()} of {len(df)}")
    return df[keep]


def aggregate(df):
    """期×县 采价点中位数 -> 期×省 县中位数 -> 年 = 各期均值。"""
    cnty = (df.groupby(["item", "unit", "prov", "county_raw", "date"], as_index=False)
              ["price"].median())
    provp = (cnty.groupby(["item", "unit", "prov", "date"], as_index=False)
                 ["price"].median())
    provp["year"] = provp["date"].str[:4].astype(int)
    ann = (provp.groupby(["item", "unit", "prov", "year"])
                .agg(price=("price", "mean"), n_periods=("price", "size"))
                .reset_index())
    return ann


def main():
    dirs = extract_zips()
    main_dir, njyy_dir, xb24_dir = dirs["main"], dirs["njyy"], dirs["xb24"]

    frames = []
    for fn, args in [(read_A, (main_dir,)), (read_B, ()), (read_C, (njyy_dir,)),
                     (read_D, (main_dir,)), (read_E, (main_dir, xb24_dir))]:
        df, tag = fn(*args)
        log(f"source {tag}: {len(df):,} rows, {df['date'].min()}–{df['date'].max()}")
        df["src"] = tag
        frames.append(df)
    full = pd.concat(frames, ignore_index=True)

    # 县->省映射：完整路径来源(B/C/E) + 手工补充
    cmap = (full[full["prov"].notna()][["county_raw", "prov"]]
            .drop_duplicates().dropna())
    cmap = dict(zip(cmap["county_raw"], cmap["prov"]))
    cmap.update(HAND_MAP)
    miss = full["prov"].isna()
    full.loc[miss, "prov"] = full.loc[miss, "county_raw"].map(cmap)
    unmapped = full[full["prov"].isna() & (full["county_raw"] != "")]
    if len(unmapped):
        log(f"  unmapped county rows dropped: {len(unmapped)} "
            f"({sorted(unmapped['county_raw'].unique())[:10]})")
    full = full[full["prov"].notna() & (full["prov"] != "") & (full["prov"] != "nan")]

    goods = map_items(full)
    goods = goods[goods["price"].notna()]
    goods = drop_outliers(goods)
    ann_goods = aggregate(goods)

    # 机械服务（G）：机耕/机收，元/亩；2022+ 分作物 -> 县×月 三作物中位数
    g = read_G(main_dir)
    for c in ("county_raw",):
        m2 = g["prov"].isna()
        g.loc[m2, "prov"] = g.loc[m2, c].map(cmap)
    g = g[g["prov"].notna()]
    lp = np.log(g["price"])
    med = lp.groupby([g["item"], g["date"]]).transform("median")
    mad = (lp - med).abs().groupby([g["item"], g["date"]]).transform("median")
    z = 0.6745 * (lp - med) / mad.replace(0, np.nan)
    g = g[z.abs().fillna(0) <= MAD_Z]
    # 采价点 -> 县(含跨作物) 中位数 -> 省中位数 -> 年均
    ann_serv = aggregate(g.assign(date=g["date"].str[:6]))  # 月度

    ann = pd.concat([ann_goods, ann_serv], ignore_index=True)
    ann = ann.rename(columns={"prov": "province"})
    ann["price"] = ann["price"].round(4)
    ann = ann[["province", "year", "item", "unit", "price", "n_periods"]]
    ann = ann.sort_values(["item", "province", "year"]).reset_index(drop=True)

    os.makedirs(OUT, exist_ok=True)
    out_csv = os.path.join(OUT, "prices_ndrc_annual.csv")
    ann.to_csv(out_csv, index=False, encoding="utf-8-sig")
    log(f"wrote {out_csv}: {len(ann):,} rows, "
        f"{ann['province'].nunique()} provinces, items={ann['item'].nunique()}")

    write_log(ann, os.path.join(OUT, "price_construction_log.csv"))
    return ann


def write_log(ann, path):
    cov = ann.groupby("item")["year"].agg(["min", "max"])
    meta = {
        "urea": ("A/B/D/E", "尿素 含氮46% 国产", "元/公斤", "单一规格贯穿；进口规格弃用", "无"),
        "abc": ("A/B/D/E", "碳酸氢铵 含氮17%(,国产)", "元/公斤", "两代规格写法合并", "无"),
        "ssp": ("A/B/D/E", "过磷酸钙 含磷12% 国产/进口", "元/公斤",
                "12%基准；2013+新增16%规格为不同产品，未并入", "无"),
        "dap": ("A/B/D/E", "磷酸二铵 含氮磷总量64%(,国产)+进口", "元/公斤",
                "两代命名与进口规格合并取中位", "四川2007+、广东全期缺；江西/浙江/海南断续"),
        "npk_cl": ("A/B/D/E", "三元复合肥 氯基15-15-15 国产+进口(06-10)", "元/公斤",
                   "氯基基准；2013+硫基系统性偏贵未并入", "甘肃2006-2013缺"),
        "mulch_film": ("A/B/D/E", "地膜 当地主销", "元/公斤", "单一口径", "无"),
        "greenhouse_film": ("A/B/D/E", "棚膜 当地主销", "元/公斤", "单一口径", "无"),
        "chlorpyrifos": ("A/B/D/E", "毒死蜱 480克/升乳油瓶装", "元/500克",
                         "唯一全期口径一致的农药；其余农药06-10散装与11+包装口径不可比", "无"),
        "diesel": ("B/C", "农用柴油", "元/公斤",
                   "B/C两源合并取中位；如需元/升 ×0.84", "仅2006-2010，2011+监测项目取消"),
        "kcl": ("B", "氯化钾 含氧化钾60% 国产+进口", "元/公斤", "国产/进口合并取中位",
                "仅2006-2010"),
        "piglet": ("C", "仔猪 10公斤左右", "元/公斤", "原始元/500克×2", "仅2006-2010"),
        "soymeal": ("C", "豆粕 二等", "元/公斤", "单一口径", "仅2006-2010"),
        "wheat_bran": ("C", "麦麸 二级", "元/公斤", "原始元/500克×2", "仅2006-2010"),
        "machine_tillage": ("G 农村居民服务价格月报", "农业作业费/农机作业费·机耕费", "元/亩",
                            "2022+分作物(小麦/水稻/玉米)取县×月三作物中位数",
                            "2011与2013缺失(留空NA；'2013'月报文件实际存的是2012年数据，"
                            "以行内报告时间为准)；2024仅1-3月"),
        "machine_harvest": ("G 农村居民服务价格月报", "农机作业费·机收费", "元/亩",
                            "2022+分作物取县×月三作物中位数",
                            "机收费2012年始；2011与2013缺失；2024仅1-3月"),
    }
    rows = []
    for item, (src, spec, unit, rule, gaps) in meta.items():
        y0, y1 = (cov.loc[item, "min"], cov.loc[item, "max"]) if item in cov.index else ("", "")
        rows.append({"item": item, "source_files": src, "definition_spec": spec,
                     "unit": unit, "merge_rule": rule,
                     "years_covered": f"{y0}-{y1}", "gaps_and_treatment": gaps})
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    log(f"wrote {path}")


if __name__ == "__main__":
    ann = main()
    # 抽查
    chk = ann[(ann["province"].isin(["黑龙江", "河南", "山东"]))
              & (ann["item"].isin(["urea", "diesel", "machine_tillage"]))
              & (ann["year"].isin([2006, 2015, 2023]))]
    log("spot check:\n" + chk.to_string(index=False))
