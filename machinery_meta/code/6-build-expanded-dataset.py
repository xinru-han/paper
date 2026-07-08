# -*- coding: utf-8 -*-
"""汇总 data/extracted_parts/*.csv（全文多效应量提取件），标准化为
可分析数据集 data/meta_effects_expanded.csv。

标准化规则（docs/extraction_protocol.md）：
  t = 报告t值，否则 beta/se；PCC = t/sqrt(t^2+df)，df 缺失用 N；
  仅保留能推导t且N可得的行；弹性 = elast_reported，或log-log模型的beta，
  或(半对数/虚拟)beta标注semi，或level模型用mean_x/mean_y换算。
"""
import glob
import os
import re

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = sorted(glob.glob(os.path.join(BASE, "data", "extracted_parts", "*.csv")))
OUT_CSV = os.path.join(BASE, "data", "meta_effects_expanded.csv")
REPORT = os.path.join(BASE, "results", "meta", "6-expanded-dataset-report.txt")

log_lines = []


def log(m=""):
    print(m)
    log_lines.append(str(m))


dfs = []
for p in PARTS:
    d = pd.read_csv(p, encoding="utf-8-sig", dtype=str)
    d["part"] = os.path.basename(p)
    dfs.append(d)
    log(f"{os.path.basename(p)}: {len(d)} 行")
df = pd.concat(dfs, ignore_index=True)
log(f"合计原始提取 {len(df)} 行，来自 {df['study_id'].nunique()} 篇文献")

NUM = re.compile(r"-?\d+\.?\d*")


def num(x):
    if pd.isna(x):
        return np.nan
    s = str(x).replace("−", "-").replace(",", "").replace("*", "").strip()
    m = NUM.search(s)
    return float(m.group(0)) if m else np.nan


for c in ["beta", "se", "t_stat", "N", "df", "mean_y", "mean_x",
          "elast_reported", "endog", "micro"]:
    df[c] = df[c].apply(num)

df = df[df["beta"].notna()].copy()

# 剔除不宜与粮食口径直接合并的行：
#  - 非粮/经济作物面积（趋粮化的镜像证据，方向相反）
#  - 空间溢出（间接效应）项
#  - 净收益/利润口径（非产量/产值）
dep = df["dep_var"].fillna("")
nts = df["notes"].fillna("")
bad = (dep.str.contains("non.?grain|非粮|棉|cotton|油料|糖料|sugar|经济作物|cash crop",
                        case=False, regex=True)
       | nts.str.contains("空间溢出")
       | dep.str.contains("net return|净收益|利润|profit", case=False)
       # 经营规模/土地流转意愿不属于粮食面积口径（协议限定粮食面积/趋粮化）
       | dep.str.contains("planting areas|transfer willingness|经营规模",
                          case=False))
log(f"剔除非粮镜像/空间溢出/净收益口径行: {int(bad.sum())}")
df = df[~bad].copy()

# 因变量为"无效率项/成本"的行：系数方向反号后并入 Efficiency（提取件notes中标注）
flip_mask = df["notes"].fillna("").str.contains("无效率|反号|inefficien", case=False)
df.loc[flip_mask, "beta"] = -df.loc[flip_mask, "beta"]
df.loc[flip_mask & df["t_stat"].notna(), "t_stat"] = \
    -df.loc[flip_mask & df["t_stat"].notna(), "t_stat"]
log(f"无效率方程反号处理: {int(flip_mask.sum())} 行")

# ------------------------------------------------- t 与 PCC
t = df["t_stat"].copy()
t_se = df["beta"] / df["se"]
t = t.fillna(t_se)
flip = t.notna() & (np.sign(t) != np.sign(df["beta"])) & (df["beta"] != 0)
t.loc[flip] = -t.loc[flip]
df["t_use"] = t
df["df_use"] = df["df"].fillna(df["N"])

before = len(df)
df = df[df["t_use"].notna() & df["df_use"].notna() & (df["df_use"] > 2)].copy()
log(f"可计算PCC的行: {len(df)} / {before}")

df["PCC"] = df["t_use"] / np.sqrt(df["t_use"] ** 2 + df["df_use"])
df["SE_PCC"] = np.sqrt((1 - df["PCC"] ** 2) / df["df_use"])

# ------------------------------------------------- 弹性
def elasticity(row):
    if np.isfinite(row["elast_reported"]):
        return row["elast_reported"], "reported"
    dep = str(row["dep_var"]).lower()
    xv = str(row["x_var"]).lower()
    dep_log = ("log" in dep) or ("ln" in dep) or ("对数" in dep)
    x_log = ("log" in xv) or ("ln" in xv) or ("对数" in xv)
    dummy = ("虚拟" in xv) or ("dummy" in xv) or ("0-1" in xv) or ("是否" in xv)
    b = row["beta"]
    if dep_log and x_log:
        return b, "full"
    if dep_log and (dummy or not x_log):
        return b, "semi"
    my, mx = row["mean_y"], row["mean_x"]
    if np.isfinite(my) and np.isfinite(mx) and my != 0:
        return b * mx / my, "converted"
    return np.nan, "none"


ee = df.apply(elasticity, axis=1)
df["elasticity"] = [x[0] for x in ee]
df["elast_type"] = [x[1] for x in ee]

# ------------------------------------------------- 清理与输出
df["Target"] = df["Target"].str.strip().str.capitalize()
df["Path"] = df["Path"].str.strip().str.upper()
df = df[df["Target"].isin(["Yield", "Area", "Efficiency"])
        & df["Path"].isin(["MCI", "AMS", "AML"])].copy()

log("\n== 效应量分布（估计值层面）==")
log(pd.crosstab(df["Target"], df["Path"], margins=True).to_string())
log("\n== 文献层面覆盖 ==")
log(pd.crosstab(df["Target"], df["Path"],
                values=df["study_id"], aggfunc="nunique").fillna(0)
    .astype(int).to_string())
log(f"\n|PCC|>0.99 异常行: {(df['PCC'].abs() > 0.99).sum()}")

df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
log(f"\n已输出 {OUT_CSV}: {len(df)} 条效应量 / {df['study_id'].nunique()} 篇文献")

os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")
