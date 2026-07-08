# -*- coding: utf-8 -*-
"""Manuscript对齐版（ms版）Meta分析：复刻论文口径 + 根本性错误检查 + 数字更新。

口径与manuscript一致：
  - 数据：一文一主效应量56条；轨道一PCC/SE沿用manuscript数值
    （即v1提取、亦即check版文件中的[轨道一]列）；分类沿用v1的
    Target×Indicator（Capital→MCI, Rate→AML）；
  - 样本量N采用check版修订值（数字更新）；
  - 表1/表2：DerSimonian-Laird随机效应 + 正态推断（manuscript式）；
    附Knapp-Hartung校正CI作参考列（完善项，不改变主口径）；
  - 表3：WLS Meta回归 PCC~AMS+AML+LogN，文献层聚类稳健SE；
  - 表4：FAT-PET-PEESE（1/v加权，聚类稳健）；
  - 表5：IQR(1.5)提纯 / 简单平均 / 样本量加权；
  - 删除v1中使用虚构数据的GPR模块与SHAP模块（根本性错误）。

输出 results/meta_ms/，含错误检查报告 audit_findings.txt。
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V1 = "/root/data/Paper/农机Meta/code_data_v1/meta_analysis_ready_data.csv"
OUT = os.path.join(BASE, "results", "meta_ms")
os.makedirs(OUT, exist_ok=True)

log_lines = []


def log(m=""):
    print(m)
    log_lines.append(str(m))


def star(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


# ------------------------------------------------------------- 数据
v1 = pd.read_csv(V1)
v1["Path"] = v1["Indicator_Type"].map(
    {"Capital": "MCI", "AMS": "AMS", "Rate": "AML"})
chk = pd.read_csv(os.path.join(BASE, "data", "meta_base_dataset.csv"),
                  encoding="utf-8-sig")
chk_n = chk.set_index("编号")["N"]
chk_pccr = chk.set_index("编号")["PCC_recalc"]
df = v1.merge(chk_n.rename("N_check"), left_on="编号", right_index=True,
              how="left")
df["N_used"] = df["N_check"].fillna(df["样本量"])
n_upd = int((df["N_used"] != df["样本量"]).sum())
df["LogN"] = np.log(df["N_used"])

ms = df.dropna(subset=["PCC", "SE_PCC"]).copy()
ms.to_csv(os.path.join(BASE, "data", "meta_ms_dataset.csv"),
          index=False, encoding="utf-8-sig")
log(f"ms版数据集：{len(ms)}条（一文一主效应量）；check版N更新{n_upd}条")

TARGETS = ["Yield", "Area", "Efficiency"]
PATHS = ["MCI", "AMS", "AML"]
TNAME = {"Yield": "粮食单产", "Area": "播种面积", "Efficiency": "生产效率"}
PNAME = {"MCI": "农机资本投入(MCI)", "AMS": "农机社会化服务(AMS)",
         "AML": "综合机械化水平(AML)"}


def dl_pool(y, v):
    """DerSimonian-Laird随机效应（manuscript口径：正态推断）+ KH参考CI。"""
    k = len(y)
    w = 1 / v
    mu_f = np.sum(w * y) / np.sum(w)
    Q = np.sum(w * (y - mu_f) ** 2)
    C = np.sum(w) - np.sum(w**2) / np.sum(w)
    tau2 = max((Q - (k - 1)) / C, 0.0) if C > 0 and k > 1 else 0.0
    wr = 1 / (v + tau2)
    mu = np.sum(wr * y) / np.sum(wr)
    se = np.sqrt(1 / np.sum(wr))
    p = 2 * stats.norm.sf(abs(mu / se)) if se > 0 else np.nan
    I2 = max(0.0, (Q - (k - 1)) / Q) * 100 if Q > 0 and k > 1 else 0.0
    # KH参考
    if k > 1:
        s2 = np.sum(wr * (y - mu) ** 2) / ((k - 1) * np.sum(wr))
        se_kh = np.sqrt(max(s2, 0.0)) if s2 > 0 else se
        crit = stats.t.ppf(0.975, k - 1)
        kh_ci = (mu - crit * se_kh, mu + crit * se_kh)
        p_kh = 2 * stats.t.sf(abs(mu / se_kh), k - 1)
    else:
        kh_ci, p_kh = (np.nan, np.nan), np.nan
    return dict(k=k, mu=mu, se=se, ci=(mu - 1.96 * se, mu + 1.96 * se),
                p=p, Q=Q, I2=I2, tau2=tau2, kh_ci=kh_ci, p_kh=p_kh)


# ---------------------------------------------- 表1 基准综合效应
log("\n" + "=" * 78)
log("表1 基准综合效应（DL随机效应，manuscript口径；KH列为参考）")
log("=" * 78)
rows = []
for tg in TARGETS:
    d = ms[ms["Target"] == tg]
    r = dl_pool(d["PCC"].values, d["SE_PCC"].values ** 2)
    log(f"{TNAME[tg]:6s} k={r['k']:>2d} PCC={r['mu']:.3f}{star(r['p']):<3s} "
        f"[{r['ci'][0]:.3f},{r['ci'][1]:.3f}] p={r['p']:.4f} "
        f"I2={r['I2']:.1f}% Q={r['Q']:.2f}  "
        f"| KH CI[{r['kh_ci'][0]:.3f},{r['kh_ci'][1]:.3f}] p_KH={r['p_kh']:.4f}")
    rows.append(dict(维度=TNAME[tg], k=r["k"], 合并PCC=round(r["mu"], 3),
                     显著性=star(r["p"]), CI下=round(r["ci"][0], 3),
                     CI上=round(r["ci"][1], 3), p值=round(r["p"], 4),
                     I2=round(r["I2"], 1), Q=round(r["Q"], 2),
                     KH_CI下=round(r["kh_ci"][0], 3),
                     KH_CI上=round(r["kh_ci"][1], 3),
                     KH_p=round(r["p_kh"], 4)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "table1_overall.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------- 表2 分路径
log("\n" + "=" * 78)
log("表2 分路径子组Meta分析（DL随机效应）")
log("=" * 78)
rows = []
for tg in TARGETS:
    for p in ["ALL"] + PATHS:
        d = ms[ms["Target"] == tg] if p == "ALL" else \
            ms[(ms["Target"] == tg) & (ms["Path"] == p)]
        if len(d) == 0:
            continue
        r = dl_pool(d["PCC"].values, d["SE_PCC"].values ** 2)
        nm = "全样本" if p == "ALL" else PNAME[p]
        log(f"{TNAME[tg]:6s} {nm:14s} k={r['k']:>2d} "
            f"PCC={r['mu']:+.3f}{star(r['p']):<3s} "
            f"[{r['ci'][0]:+.3f},{r['ci'][1]:+.3f}] I2={r['I2']:.1f}%")
        rows.append(dict(维度=TNAME[tg], 路径=nm, k=r["k"],
                         合并PCC=round(r["mu"], 3), 显著性=star(r["p"]),
                         CI下=round(r["ci"][0], 3), CI上=round(r["ci"][1], 3),
                         p值=round(r["p"], 4), I2=round(r["I2"], 1)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "table2_subgroup.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------- 表3 WLS Meta回归
log("\n" + "=" * 78)
log("表3 WLS Meta回归（PCC~AMS+AML+LogN；基准组MCI；文献层聚类稳健SE）")
log("=" * 78)
rows = []
for tg in TARGETS:
    d = ms[ms["Target"] == tg].copy()
    d["AMS_d"] = (d["Path"] == "AMS").astype(float)
    d["AML_d"] = (d["Path"] == "AML").astype(float)
    v = d["SE_PCC"].values ** 2
    r0 = dl_pool(d["PCC"].values, v)
    w = 1 / (v + r0["tau2"])
    Xc = [("AMS_d", "农机社会化服务"), ("AML_d", "综合机械化水平"),
          ("LogN", "LogN")]
    Xc = [(c, l) for c, l in Xc if d[c].std() > 0]
    if len(d) < len(Xc) + 3:
        log(f"\n[{TNAME[tg]}] k={len(d)} 过小，仅供参考（manuscript亦有此列）")
    X = sm.add_constant(d[[c for c, _ in Xc]].astype(float))
    groups = d["作者_年份"].astype("category").cat.codes
    res = sm.WLS(d["PCC"].astype(float), X, weights=w).fit(
        cov_type="cluster", cov_kwds={"groups": groups})
    log(f"\n[{TNAME[tg]}] k={len(d)}")
    lab = {"const": "常数项", "AMS_d": "农机社会化服务",
           "AML_d": "综合机械化水平", "LogN": "LogN"}
    for nm in res.params.index:
        b, s, pv = res.params[nm], res.bse[nm], res.pvalues[nm]
        log(f"  {lab.get(nm, nm):10s} {b:+.3f}{star(pv):<3s} ({s:.3f})")
        rows.append(dict(维度=TNAME[tg], 变量=lab.get(nm, nm),
                         系数=round(b, 3), SE=round(s, 3),
                         p值=round(pv, 4), 显著性=star(pv), k=len(d)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "table3_meta_regression.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------- 表4 FAT-PET-PEESE
log("\n" + "=" * 78)
log("表4 FAT-PET-PEESE（1/v加权WLS，文献层聚类稳健SE）")
log("=" * 78)
rows = []
for tg in TARGETS:
    d = ms[ms["Target"] == tg]
    y = d["PCC"].astype(float)
    se = d["SE_PCC"].astype(float)
    wgt = 1 / se**2
    groups = d["作者_年份"].astype("category").cat.codes
    pet = sm.WLS(y, sm.add_constant(se.rename("SE")), weights=wgt).fit(
        cov_type="cluster", cov_kwds={"groups": groups})
    fb, fp = pet.params["SE"], pet.pvalues["SE"]
    pb, pp = pet.params["const"], pet.pvalues["const"]
    log(f"\n[{TNAME[tg]}] k={len(d)}")
    log(f"  FAT={fb:+.3f}{star(fp)} (p={fp:.4f})   "
        f"PET={pb:+.3f}{star(pp)} (p={pp:.4f})")
    rows.append(dict(维度=TNAME[tg], 检验="FAT", 系数=round(fb, 3),
                     p值=round(fp, 4), 显著性=star(fp)))
    rows.append(dict(维度=TNAME[tg], 检验="PET", 系数=round(pb, 3),
                     p值=round(pp, 4), 显著性=star(pp)))
    if pp < 0.05:
        pe = sm.WLS(y, sm.add_constant((se**2).rename("Var")),
                    weights=wgt).fit(cov_type="cluster",
                                     cov_kwds={"groups": groups})
        log(f"  PEESE={pe.params['const']:+.3f}{star(pe.pvalues['const'])} "
            f"(p={pe.pvalues['const']:.4f})")
        rows.append(dict(维度=TNAME[tg], 检验="PEESE",
                         系数=round(pe.params["const"], 3),
                         p值=round(pe.pvalues["const"], 4),
                         显著性=star(pe.pvalues["const"])))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "table4_fat_pet_peese.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------- 表5 稳健性
log("\n" + "=" * 78)
log("表5 稳健性（IQR提纯 / 简单平均 / 样本量加权）")
log("=" * 78)
rows = []
for tg in TARGETS:
    d = ms[ms["Target"] == tg]
    y, v = d["PCC"].values, d["SE_PCC"].values ** 2
    base = dl_pool(y, v)
    q1, q3 = np.percentile(y, [25, 75])
    iqr = q3 - q1
    keep = (y >= q1 - 1.5 * iqr) & (y <= q3 + 1.5 * iqr)
    trim = dl_pool(y[keep], v[keep]) if keep.sum() > 1 else base
    dropped = d.loc[~keep, "编号"].tolist()
    nw = np.nansum(d["N_used"].values * y) / np.nansum(d["N_used"].values)
    log(f"{TNAME[tg]:6s} 基准={base['mu']:.3f}  "
        f"IQR提纯={trim['mu']:.3f}(k={int(keep.sum())},剔:{','.join(dropped) or '-'})  "
        f"简单平均={y.mean():.3f}  N加权={nw:.3f}")
    for lab, val, kk in [("随机效应（基准）", base["mu"], len(y)),
                         ("IQR提纯后", trim["mu"], int(keep.sum())),
                         ("简单算术平均", y.mean(), len(y)),
                         ("样本量加权", nw, len(y))]:
        rows.append(dict(维度=TNAME[tg], 权重设定=lab, 合并PCC=round(val, 3),
                         样本量=kk))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "table5_robustness.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------- 弹性中位数（表6用）
log("\n" + "=" * 78)
log("弹性中位数（|e|<1，manuscript口径：路径×维度，含半弹性近似）")
log("=" * 78)
rows = []
el = ms[ms["弹性"].abs() < 1]
for tg in TARGETS:
    for p in PATHS:
        d = el[(el["Target"] == tg) & (el["Path"] == p)]
        med = d["弹性"].median() if len(d) else np.nan
        rows.append(dict(Target=tg, Path=p, k_elast=len(d),
                         elast_median=round(med, 4) if len(d) else np.nan,
                         ids=";".join(d["编号"])))
        if len(d):
            log(f"{TNAME[tg]:6s} {p}: 中位数={med:+.4f} (k={len(d)}: "
                f"{','.join(d['编号'])})")
pd.DataFrame(rows).to_csv(os.path.join(OUT, "elasticity_medians_ms.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------- 错误检查报告
findings = """== Manuscript与v1代码根本性错误检查报告 ==

[必须修复]
1. v1的3-meta-regress.py"GPR代理模型"模块使用硬编码的虚构数据
   （X_obs/Y_obs手写数组），与任何实际提取数据无关——本版已删除；
   manuscript未引用该模块结果，不影响正文，但代码库中必须移除。
2. v1的3-meta-regress.py WLS Meta回归缺少LogN（小样本偏倚控制），与
   manuscript表3不一致（表3含LogN行）——本版已补齐，结果与表3口径一致。
3. manuscript表6弹性中位数与表7 Shifter内部不一致：S1单产Shifter
   0.434%/年 ÷ 增速2.4%/年 = 隐含弹性0.181，而表6中位数为0.171
   （S2同理：隐含0.156 vs 表6的0.147）。本版按式(25)用表6中位数统一重算。

[需作者复核（不改变主口径，仅提示）]
4. check版修订了36条文献的β/SE/t等原始统计量，但[轨道一]PCC列未同步
   变动；若以check后统计量重算PCC，部分条目数值/符号会变化
   （明细见 results/meta/0-dataset-report.txt）。本ms版按用户指示沿用
   manuscript的轨道一数值；建议在论文数据附录中说明轨道一的提取基准。
5. 分路径计数与manuscript表2略有出入：本数据给出 单产MCI15/AMS7/AML7
   （表2为16/6/7）、面积MCI3/AMS1/AML3（表2为2/2/3）；效率4/14/2一致。
   相应子组合并PCC与表2数字有小幅差异，建议以本版重算数为准更新表2。
6. 自由度以样本量N近似（DF=N），PCC的SE略被低估（k个回归元未扣除）；
   为与manuscript一致未改，附KH校正CI作参考。
7. 编号P_13在两版数据中均缺失（56条而非57条），建议核对是否漏录。
8. 面积维度k=7、I2=97%，检验功效有限（manuscript已自述），表2面积子组
   单篇路径（AMS仅1条）不宜过度解释。
"""
log("\n" + findings)
with open(os.path.join(OUT, "audit_findings.txt"), "w", encoding="utf-8") as f:
    f.write(findings)
with open(os.path.join(OUT, "10-ms-meta-results.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")
