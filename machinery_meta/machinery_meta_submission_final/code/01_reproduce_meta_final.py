# -*- coding: utf-8 -*-
"""Reproduce the final meta-analysis comparison against the first draft.

Inputs are kept outside this archive so the script can be rerun after moving the
archive inside the same project tree. The statistical definitions follow the
first-draft scripts: DerSimonian-Laird random effects, the same outlier rule,
cluster-robust WLS meta-regression, and FAT/PET/PEESE tests.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


PROJECT = Path("/root/data/Paper/农机Meta")
ARCHIVE = PROJECT / "machinery_meta_submission_final"
OUT = ARCHIVE / "results" / "meta"
DATA_OUT = ARCHIVE / "data"
REMOVE_IDS = {"E_22", "E_24"}


def sig(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def dl_meta(df_sub):
    d = df_sub.dropna(subset=["PCC", "SE_PCC"]).copy()
    d = d[d["SE_PCC"] > 0]
    k = len(d)
    if k == 0:
        return dict(k=0, PCC=np.nan, SE=np.nan, z=np.nan, p=np.nan, sig="",
                    CI_L=np.nan, CI_U=np.nan, Q=np.nan, Q_p=np.nan,
                    I2=np.nan, tau2=np.nan, Elasticity=np.nan)
    w = 1 / (d["SE_PCC"] ** 2)
    p_fixed = (w * d["PCC"]).sum() / w.sum()
    Q = (w * (d["PCC"] - p_fixed) ** 2).sum()
    dfq = k - 1
    q_p = stats.chi2.sf(Q, dfq) if dfq > 0 else np.nan
    c = w.sum() - (w.pow(2).sum() / w.sum())
    tau2 = max(0, (Q - dfq) / c) if c > 0 else 0
    wr = 1 / (d["SE_PCC"] ** 2 + tau2)
    pcc = (wr * d["PCC"]).sum() / wr.sum()
    se = np.sqrt(1 / wr.sum())
    z = pcc / se if se > 0 else np.nan
    p = 2 * stats.norm.sf(abs(z)) if pd.notna(z) else np.nan
    de = d.dropna(subset=["弹性"])
    if len(de) and de["样本量"].fillna(0).sum() > 0:
        elas = np.average(de["弹性"], weights=de["样本量"].fillna(0))
    elif len(de):
        elas = de["弹性"].mean()
    else:
        elas = np.nan
    return dict(k=k, PCC=pcc, SE=se, z=z, p=p, sig=sig(p),
                CI_L=pcc - 1.96 * se, CI_U=pcc + 1.96 * se,
                Q=Q, Q_p=q_p, I2=max(0, (Q - dfq) / Q) * 100 if Q > 0 and dfq > 0 else 0,
                tau2=tau2, Elasticity=elas)


def filter_outliers(df_sub):
    d = df_sub.copy()
    if len(d) < 3:
        return d, []
    q1, q3 = d["PCC"].quantile(0.25), d["PCC"].quantile(0.75)
    iqr = q3 - q1
    valid = (
        (d["PCC"] >= q1 - 1.5 * iqr)
        & (d["PCC"] <= q3 + 1.5 * iqr)
        & (d["弹性"].isna() | ((d["弹性"] >= -0.99) & (d["弹性"] <= 0.99)))
    )
    clean = d[valid].copy()
    return clean, sorted(set(d["编号"]) - set(clean["编号"]))


def meta_results(df, label):
    rows, drops = [], []
    for target in ["Yield", "Area", "Efficiency"]:
        d = df[df["Target"] == target].copy()
        r = dl_meta(d)
        r.update(dataset=label, stage="全样本", Target=target, Indicator_Type="ALL", dropped="")
        rows.append(r)
        clean, drop = filter_outliers(d)
        drops.append(dict(dataset=label, Target=target, dropped=", ".join(drop), n_dropped=len(drop)))
        r = dl_meta(clean)
        r.update(dataset=label, stage="提纯后", Target=target, Indicator_Type="ALL", dropped=", ".join(drop))
        rows.append(r)
        for ind in sorted(d["Indicator_Type"].dropna().unique()):
            r = dl_meta(d[d["Indicator_Type"] == ind])
            r.update(dataset=label, stage="分路径", Target=target, Indicator_Type=ind, dropped="")
            rows.append(r)
    return pd.DataFrame(rows), pd.DataFrame(drops)


def fit_wls(y, x, weights, clusters=None):
    x = sm.add_constant(x, has_constant="add")
    model = sm.WLS(y.astype(float), x.astype(float), weights=weights.astype(float))
    if clusters is not None and len(set(clusters)) > 1:
        return model.fit(cov_type="cluster", cov_kwds={"groups": clusters})
    return model.fit(cov_type="HC3")


def add_result_rows(rows, label, model_name, target, res, n):
    for term in res.params.index:
        p = res.pvalues.get(term, np.nan)
        rows.append(dict(dataset=label, model=model_name, Target=target, term=term,
                         coef=res.params[term], se=res.bse.get(term, np.nan),
                         z=res.tvalues.get(term, np.nan), p=p, sig=sig(p), n=n))


def wls_results(df, label):
    rows = []
    d = df.dropna(subset=["PCC", "SE_PCC", "Indicator_Type", "作者_年份"]).copy()
    d = d[d["SE_PCC"] > 0]
    x = pd.get_dummies(d["Indicator_Type"], prefix="Indicator_Type", drop_first=True, dtype=float)
    res = fit_wls(d["PCC"], x, 1 / (d["SE_PCC"] ** 2), d["作者_年份"].astype("category").cat.codes)
    add_result_rows(rows, label, "actual_all_sample_PCC_on_Indicator", "ALL", res, len(d))
    for target in ["Yield", "Area", "Efficiency"]:
        g = d[d["Target"] == target].copy()
        if len(g) < 3:
            continue
        x = pd.get_dummies(g["Indicator_Type"], drop_first=True, dtype=float)
        x["LogN"] = np.log1p(g["样本量"].fillna(g["样本量"].median()))
        res = fit_wls(g["PCC"], x, 1 / (g["SE_PCC"] ** 2), g["作者_年份"].astype("category").cat.codes)
        add_result_rows(rows, label, "by_target_PCC_on_Path_LogN", target, res, len(g))
    return pd.DataFrame(rows)


def simple_wls(d, xcol):
    x = sm.add_constant(d[[xcol]], has_constant="add")
    return sm.WLS(d["PCC"].astype(float), x.astype(float),
                  weights=(1 / (d["SE_PCC"] ** 2)).astype(float)).fit(cov_type="HC3")


def fat_results(df, label):
    rows = []
    for scope in ["ALL", "Yield", "Area", "Efficiency"]:
        d = df.copy() if scope == "ALL" else df[df["Target"] == scope].copy()
        d = d.dropna(subset=["PCC", "SE_PCC"])
        d = d[d["SE_PCC"] > 0].copy()
        if len(d) < 3:
            continue
        d["Variance"] = d["SE_PCC"] ** 2
        pet = simple_wls(d, "SE_PCC")
        peese = simple_wls(d, "Variance")
        for test, res, term in [
            ("FAT_slope_SE", pet, "SE_PCC"),
            ("PET_intercept_true_effect", pet, "const"),
            ("PEESE_intercept_true_effect", peese, "const"),
            ("PEESE_slope_variance", peese, "Variance"),
        ]:
            p = res.pvalues.get(term, np.nan)
            rows.append(dict(dataset=label, scope=scope, test=test,
                             estimate=res.params.get(term, np.nan), se=res.bse.get(term, np.nan),
                             z=res.tvalues.get(term, np.nan), p=p, sig=sig(p), n=len(d)))
    return pd.DataFrame(rows)


def compare(left, right, keys, suffix):
    out = left.merge(right, on=keys, how="outer", suffixes=("_v1", suffix))
    for col in ["k", "PCC", "SE", "z", "p", "CI_L", "CI_U", "Q", "Q_p", "I2", "tau2", "Elasticity",
                "coef", "estimate", "n"]:
        a, b = f"{col}_v1", f"{col}{suffix}"
        if a in out.columns and b in out.columns:
            out[f"delta_{col}"] = out[b] - out[a]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    v1 = pd.read_csv(PROJECT / "code_data_v1" / "meta_analysis_ready_data.csv")
    manual_all = pd.read_csv(PROJECT / "manual_first_model_ready_data.csv")
    manual = manual_all[~manual_all["编号"].isin(REMOVE_IDS)].copy()
    for df in (v1, manual, manual_all):
        for c in ["PCC", "SE_PCC", "弹性", "样本量"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    manual.to_csv(DATA_OUT / "manual_first_model_ready_data_final.csv",
                  index=False, encoding="utf-8-sig")

    meta_v1, drops_v1 = meta_results(v1, "v1第一版")
    meta_m, drops_m = meta_results(manual, "人工核实_final_sample")
    wls_v1, wls_m = wls_results(v1, "v1第一版"), wls_results(manual, "人工核实_final_sample")
    fat_v1, fat_m = fat_results(v1, "v1第一版"), fat_results(manual, "人工核实_final_sample")

    out_xlsx = OUT / "final_all_estimates_vs_v1.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        pd.concat([meta_v1, meta_m], ignore_index=True).to_excel(writer, index=False, sheet_name="meta_all_results")
        compare(meta_v1, meta_m, ["stage", "Target", "Indicator_Type"], "_final").to_excel(
            writer, index=False, sheet_name="meta_compare_vs_v1")
        pd.concat([wls_v1, wls_m], ignore_index=True).to_excel(writer, index=False, sheet_name="wls_reg_all_results")
        compare(wls_v1, wls_m, ["model", "Target", "term"], "_final").to_excel(
            writer, index=False, sheet_name="wls_reg_compare_vs_v1")
        pd.concat([fat_v1, fat_m], ignore_index=True).to_excel(writer, index=False, sheet_name="fat_pet_peese_all")
        compare(fat_v1, fat_m, ["scope", "test"], "_final").to_excel(
            writer, index=False, sheet_name="fat_pet_peese_compare_vs_v1")
        pd.concat([drops_v1, drops_m], ignore_index=True).to_excel(writer, index=False, sheet_name="outlier_drops")
        manual_all[manual_all["编号"].isin(REMOVE_IDS)].to_excel(writer, index=False, sheet_name="excluded_records")
    print(f"wrote {out_xlsx}")


if __name__ == "__main__":
    main()
