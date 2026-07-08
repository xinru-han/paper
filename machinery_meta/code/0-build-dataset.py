# -*- coding: utf-8 -*-
"""整合check后的中英文文献参数提取表，生成meta分析基础数据集。

来源（均为人工check后的修订版）：
  - data/文献参数提取与汇总.csv        中文文献check版  -> 取 P_ 行
  - data/En_文献参数提取与汇总.xlsx    英文文献check版  -> 取 E_ 行

输出：
  - data/meta_base_dataset.csv   整合后的基础数据（原始字段+解析/派生字段）
  - results/meta/0-dataset-report.txt  字段解析与PCC核验报告
"""
import os
import re
import sys

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "results", "meta")
os.makedirs(OUT, exist_ok=True)

log_lines = []


def log(msg=""):
    print(msg)
    log_lines.append(str(msg))


# ---------------------------------------------------------------- 读取
cn = pd.read_csv(os.path.join(DATA, "文献参数提取与汇总.csv"), encoding="utf-8-sig")
en = pd.read_excel(os.path.join(DATA, "En_文献参数提取与汇总.xlsx"))
cn.columns = [c.strip() for c in cn.columns]
en.columns = [c.strip() for c in en.columns]

cn_p = cn[cn["编号"].astype(str).str.startswith("P_")].copy()
en_e = en[en["编号"].astype(str).str.startswith("E_")].copy()
cn_p["来源"] = "中文check版"
en_e["来源"] = "英文check版"
log(f"中文check版取 P_ 行 {len(cn_p)} 条；英文check版取 E_ 行 {len(en_e)} 条")

df = pd.concat([cn_p, en_e], ignore_index=True, sort=False)


def col(name_part):
    hits = [c for c in df.columns if name_part in c]
    if not hits:
        raise KeyError(name_part)
    return hits[0]


C_PCC = [c for c in df.columns if "PCC" in c and "SE" not in c][0]
C_SEPCC = [c for c in df.columns if "SE" in c and "PCC" in c][0]
C_ELAS = col("CASM 对接弹性")
C_BETA = col("核心回归系数")
C_SET = col("标准误 SE 或 t")
C_N = col("样本量")
C_DF = col("自由度")
C_X = col("自变量定义")
C_Y = col("因变量定义")
C_CASM = col("CASM 软链接目标")
C_REGION = col("数据层级")
C_ENDO = col("控内生性")
C_YEARS = col("调研/数据年份")

FLOAT_RE = re.compile(r"-?\d+(?:\.\d+)?")


def first_float(s):
    m = FLOAT_RE.search(str(s).replace("−", "-"))
    return float(m.group(0)) if m else np.nan


# ------------------------------------------------- 解析 β 与 SE/t
def parse_beta(s):
    return first_float(s)


def parse_se_or_t(s):
    """返回 (se, t, p)；只解析首个主效应量的统计量。"""
    s = str(s).replace("−", "-")
    se = t = p = np.nan
    m = re.search(r"SE\s*=?\s*(-?\d+(?:\.\d+)?)", s, re.I)
    if m:
        se = float(m.group(1))
    m = re.search(r"\bt\s*=?\s*(-?\d+(?:\.\d+)?)", s)
    if m:
        t = float(m.group(1))
    m = re.search(r"\bp\s*=?\s*(0?\.\d+|0|1)", s, re.I)
    if m:
        p = float(m.group(1))
    return se, t, p


df["beta"] = df[C_BETA].apply(parse_beta)
se_t = df[C_SET].apply(parse_se_or_t)
df["se_raw"] = [x[0] for x in se_t]
df["t_raw"] = [x[1] for x in se_t]
df["p_raw"] = [x[2] for x in se_t]
df["N"] = pd.to_numeric(df[C_N], errors="coerce")
df["DF_report"] = pd.to_numeric(df[C_DF], errors="coerce")
# 英文表未报告自由度，按提取规则以样本量近似（与轨道一口径一致）
df["DF_used"] = df["DF_report"].fillna(df["N"])

# t 统计量：优先原文 t，其次 β/SE，最后由报告 p 值反推（正态近似）；符号以 β 为准
from scipy import stats as _st

t = df["t_raw"].copy()
t_from_se = df["beta"] / df["se_raw"]
t = t.fillna(t_from_se)
t_from_p = pd.Series(
    [np.sign(b) * _st.norm.ppf(1 - p / 2) if (np.isfinite(p) and 0 < p < 1
                                              and np.isfinite(b)) else np.nan
     for b, p in zip(df["beta"], df["p_raw"])], index=df.index)
t = t.fillna(t_from_p)
flip = t.notna() & df["beta"].notna() & (np.sign(t) != np.sign(df["beta"])) & (df["beta"] != 0)
t[flip] = -t[flip]
df["t_stat"] = t

# ------------------------------------------------- PCC 双轨核验
df["PCC_report"] = df[C_PCC].apply(first_float)
df["SE_PCC_report"] = df[C_SEPCC].apply(first_float)
df["PCC_recalc"] = df["t_stat"] / np.sqrt(df["t_stat"] ** 2 + df["DF_used"])
df["SE_PCC_recalc"] = np.sqrt((1 - df["PCC_recalc"] ** 2) / df["DF_used"])

# check版修订的是 β/SE/t/N/DF 等原始统计量，而表中 PCC 列沿用了修订前的旧值，
# 因此基准分析统一由check后的 t 与 df 重算 PCC（式 PCC=t/sqrt(t^2+df)）；
# 仅在统计量无法解析时回退到表中报告值。
df["PCC"] = df["PCC_recalc"].fillna(df["PCC_report"])
df["SE_PCC"] = df["SE_PCC_recalc"].fillna(df["SE_PCC_report"])
df["PCC_source"] = np.where(df["PCC_recalc"].notna(), "recalc", "report")

diff = (df["PCC_report"] - df["PCC_recalc"]).abs()
big = df[diff > 0.05][["编号", "作者_年份", "PCC_report", "PCC_recalc", "t_stat", "DF_used"]]
log("\n== PCC 核验（表中旧报告值 vs 由check后 t/df 重算值）==")
log(f"可重算 {df['PCC_recalc'].notna().sum()}/{len(df)} 条；|差异|>0.05 的 {len(big)} 条：")
if len(big):
    log(big.to_string(index=False))
log("说明：check版修订了 β/SE/t/DF 等原始统计量但未同步更新 PCC 列，"
    "故基准分析采用重算 PCC；旧报告值仅保留作对照。")

# ------------------------------------------------- 弹性轨
def parse_elasticity(s):
    s = str(s).replace("−", "-")
    m = re.search(r"半弹性\s*=?\s*(-?\d+(?:\.\d+)?)", s)
    if m:
        return "semi", float(m.group(1))
    m = re.search(r"弹性\s*=?\s*(-?\d+(?:\.\d+)?)", s)
    if m:
        return "full", float(m.group(1))
    return "none", np.nan


el = df[C_ELAS].apply(parse_elasticity)
df["elast_type"] = [x[0] for x in el]
df["elasticity"] = [x[1] for x in el]

# ------------------------------------------------- 派生分组变量
def determine_target(row):
    casm = str(row.get(C_CASM, "")).lower()
    y = str(row.get(C_Y, "")).lower()
    if "area" in casm or "面积" in y or "趋粮" in y:
        return "Area"
    if ("efficiency" in casm or "效率" in y or "tfp" in y
            or "错配" in y or "集约" in y):
        return "Efficiency"
    return "Yield"


# 机械化路径：MCI=农机资本投入, AMS=农机社会化服务, AML=综合机械化水平,
# OTH=check后核心自变量并非机械化（主分析剔除，仅作扩展参考）
MECH_RE = re.compile(r"农机|机械|机耕|机播|机收|跨区|托管|耦合")
AMS_RE = re.compile(r"服务|外包|托管|作业费|跨区|机耕|环节")
AML_RE = re.compile(r"机械化率|机械化水平|耦合")

# 个别行规则难以判别，依据原文与CASM软链接目标人工指定：
PATH_OVERRIDES = {
    "P_04": "AMS",   # 农业产业链服务：以农机作业等生产性服务环节为主
}


def determine_path(row):
    pid = str(row.get("编号", ""))
    if pid in PATH_OVERRIDES:
        return PATH_OVERRIDES[pid]
    x = str(row.get(C_X, ""))
    if not MECH_RE.search(x):
        return "OTH"
    if AMS_RE.search(x):
        return "AMS"
    if AML_RE.search(x):
        return "AML"
    return "MCI"


df["Target"] = df.apply(determine_target, axis=1)
df["Path"] = df.apply(determine_path, axis=1)
df["Mech"] = (df["Path"] != "OTH").astype(int)
df["Micro"] = df[C_REGION].astype(str).str.contains("微观").astype(int)
df["Endog"] = (df[C_ENDO].astype(str).str.strip().str.startswith("1")).astype(int)
df["PubYear"] = df["作者_年份"].astype(str).str.extract(r"(\d{4})").astype(float)


def year_mid(s):
    ys = re.findall(r"(19|20)\d{2}", str(s))
    ys = [int(m.group(0)) for m in re.finditer(r"(?:19|20)\d{2}", str(s))]
    return float(np.mean(ys)) if ys else np.nan


df["DataYear_mid"] = df[C_YEARS].apply(year_mid)
df["LogN"] = np.log(df["N"])

log("\n== 分组分布（全部56条）==")
log(pd.crosstab(df["Target"], df["Path"], margins=True).to_string())
oth = df[df["Path"] == "OTH"]
log(f"\ncheck后核心自变量非机械化（OTH，主分析剔除）共 {len(oth)} 条：")
log(oth[["编号", "作者_年份", C_X]].to_string(index=False))
mech = df[df["Mech"] == 1]
log(f"\n== 机械化主分析样本分布（{len(mech)} 条）==")
log(pd.crosstab(mech["Target"], mech["Path"], margins=True).to_string())
log("\n弹性轨： full=" + str((df["elast_type"] == "full").sum())
    + ", semi=" + str((df["elast_type"] == "semi").sum())
    + ", none=" + str((df["elast_type"] == "none").sum()))

# ------------------------------------------------- 输出
front = ["编号", "来源", "标题", "作者_年份", "期刊级别"]
front = [c for c in front if c in df.columns]
rest = [c for c in df.columns if c not in front]
df = df[front + rest]

out_csv = os.path.join(DATA, "meta_base_dataset.csv")
df.to_csv(out_csv, index=False, encoding="utf-8-sig")
log(f"\n已输出整合基础数据: {out_csv}  ({len(df)} 行 × {len(df.columns)} 列)")

miss = df[df["PCC"].isna() | df["SE_PCC"].isna()]
if len(miss):
    log("警告：以下行缺失 PCC/SE_PCC，将被后续分析剔除：" + ", ".join(miss["编号"]))

with open(os.path.join(OUT, "0-dataset-report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")
