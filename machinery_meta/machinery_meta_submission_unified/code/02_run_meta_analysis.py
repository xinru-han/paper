# -*- coding: utf-8 -*-
"""Run the first-draft meta model on the unified strict-path dataset.

Methods are unchanged from the first-draft framework: DerSimonian-Laird random
effects, the original IQR/elasticity filtering rule, inverse-variance WLS with
study-clustered robust standard errors, and FAT/PET/PEESE with HC3 errors.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "results" / "meta"
INPUT = DATA / "analysis_dataset_strict.csv"
TARGETS = ["Yield", "Area", "Efficiency"]
PATHS = ["MCI", "AMS", "AML"]
COLORS = {"MCI": "#2468a2", "AMS": "#b33b32", "AML": "#2f7d4a"}

available_fonts = {font.name for font in font_manager.fontManager.ttflist}
for preferred_font in ["Noto Sans CJK JP", "Noto Sans CJK SC", "AR PL SungtiL GB", "SimHei"]:
    if preferred_font in available_fonts:
        plt.rcParams["font.sans-serif"] = [preferred_font, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False


def significance(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def dl_meta(frame):
    d = frame.dropna(subset=["PCC", "SE_PCC"]).copy()
    d = d[d["SE_PCC"] > 0]
    k = len(d)
    empty = dict(k=0, PCC=np.nan, SE=np.nan, z=np.nan, p=np.nan,
                 significance="", CI_low=np.nan, CI_high=np.nan,
                 Q=np.nan, Q_p=np.nan, I2=np.nan, tau2=np.nan,
                 elasticity_N_weighted=np.nan)
    if k == 0:
        return empty

    w_fixed = 1 / d["SE_PCC"].pow(2)
    fixed = (w_fixed * d["PCC"]).sum() / w_fixed.sum()
    q = (w_fixed * (d["PCC"] - fixed).pow(2)).sum()
    df_q = k - 1
    c_value = w_fixed.sum() - w_fixed.pow(2).sum() / w_fixed.sum()
    tau2 = max(0, (q - df_q) / c_value) if c_value > 0 else 0
    w_random = 1 / (d["SE_PCC"].pow(2) + tau2)
    pooled = (w_random * d["PCC"]).sum() / w_random.sum()
    pooled_se = np.sqrt(1 / w_random.sum())
    z_value = pooled / pooled_se if pooled_se > 0 else np.nan
    p_value = 2 * stats.norm.sf(abs(z_value)) if pd.notna(z_value) else np.nan

    elastic = d.dropna(subset=["elasticity", "N"])
    if len(elastic) and elastic["N"].sum() > 0:
        elasticity = np.average(elastic["elasticity"], weights=elastic["N"])
    elif len(elastic):
        elasticity = elastic["elasticity"].mean()
    else:
        elasticity = np.nan

    return dict(
        k=k,
        PCC=pooled,
        SE=pooled_se,
        z=z_value,
        p=p_value,
        significance=significance(p_value),
        CI_low=pooled - 1.96 * pooled_se,
        CI_high=pooled + 1.96 * pooled_se,
        Q=q,
        Q_p=stats.chi2.sf(q, df_q) if df_q > 0 else np.nan,
        I2=max(0, (q - df_q) / q) * 100 if q > 0 and df_q > 0 else 0,
        tau2=tau2,
        elasticity_N_weighted=elasticity,
    )


def filter_outliers(frame):
    d = frame.copy()
    if len(d) < 3:
        return d, []
    q1, q3 = d["PCC"].quantile(0.25), d["PCC"].quantile(0.75)
    iqr = q3 - q1
    valid = (
        d["PCC"].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
        & (d["elasticity"].isna() | d["elasticity"].between(-0.99, 0.99))
    )
    return d[valid].copy(), sorted(d.loc[~valid, "编号"].tolist())


def build_meta_results(df):
    rows = []
    drop_rows = []
    for target in TARGETS:
        target_data = df[df["Target"] == target].copy()
        result = dl_meta(target_data)
        result.update(stage="overall_full", Target=target, Path="ALL", dropped_ids="")
        rows.append(result)

        filtered, dropped = filter_outliers(target_data)
        result = dl_meta(filtered)
        result.update(stage="overall_filtered", Target=target, Path="ALL",
                      dropped_ids=";".join(dropped))
        rows.append(result)
        drop_rows.append({"Target": target, "n_dropped": len(dropped),
                          "dropped_ids": ";".join(dropped)})

        for path in PATHS:
            result = dl_meta(target_data[target_data["Path"] == path])
            note = ("Single-record subgroup; p-value is based on the record-level SE "
                    "and is not pooled path evidence") if result["k"] == 1 else ""
            result.update(stage="path_subgroup", Target=target, Path=path,
                          dropped_ids="", interpretation_note=note)
            rows.append(result)
    return pd.DataFrame(rows), pd.DataFrame(drop_rows)


def fit_wls(y, x, weights, clusters):
    design = sm.add_constant(x.astype(float), has_constant="add")
    model = sm.WLS(y.astype(float), design, weights=weights.astype(float))
    if pd.Series(clusters).nunique() > 1:
        return model.fit(cov_type="cluster", cov_kwds={"groups": clusters})
    return model.fit(cov_type="HC3")


def add_wls_rows(rows, result, model, target, baseline, n, cluster_n):
    for term in result.params.index:
        p_value = result.pvalues.get(term, np.nan)
        rows.append({
            "model": model,
            "Target": target,
            "baseline_path": baseline,
            "term": term,
            "coefficient": result.params[term],
            "SE": result.bse.get(term, np.nan),
            "z": result.tvalues.get(term, np.nan),
            "p": p_value,
            "significance": significance(p_value),
            "n": n,
            "clusters": cluster_n,
        })


def path_design(frame, baseline):
    design = pd.DataFrame(index=frame.index)
    for path in PATHS:
        if path != baseline and path in set(frame["Path"]):
            design[f"{path}_vs_{baseline}"] = (frame["Path"] == path).astype(float)
    return design


def build_wls_results(df):
    rows = []
    notes = []

    overall = df.copy()
    x = path_design(overall, "MCI")
    clusters = overall["作者_年份"].astype("category").cat.codes
    result = fit_wls(overall["PCC"], x, 1 / overall["SE_PCC"].pow(2), clusters)
    add_wls_rows(rows, result, "all_sample_PCC_on_Path", "ALL", "MCI",
                 len(overall), pd.Series(clusters).nunique())

    for target in TARGETS:
        d = df[df["Target"] == target].copy()
        present = [path for path in PATHS if path in set(d["Path"])]
        baseline = "MCI" if "MCI" in present else present[0]
        x = path_design(d, baseline)
        x["LogN"] = np.log1p(d["N"].fillna(d["N"].median()))
        clusters = d["作者_年份"].astype("category").cat.codes
        result = fit_wls(d["PCC"], x, 1 / d["SE_PCC"].pow(2), clusters)
        add_wls_rows(rows, result, "by_target_PCC_on_Path_LogN", target,
                     baseline, len(d), pd.Series(clusters).nunique())
        note_parts = ["MCI unavailable; AMS is the estimable reference group"] \
            if baseline != "MCI" else ["MCI reference group"]
        if len(d) < 10:
            note_parts.append("Small-sample path regression; coefficient p-values are exploratory")
        notes.append({"Target": target, "n": len(d), "paths_present": ";".join(present),
                      "baseline_path": baseline, "note": "; ".join(note_parts)})
    return pd.DataFrame(rows), pd.DataFrame(notes)


def simple_wls(frame, predictor):
    x = sm.add_constant(frame[[predictor]], has_constant="add")
    return sm.WLS(frame["PCC"].astype(float), x.astype(float),
                  weights=(1 / frame["SE_PCC"].pow(2)).astype(float)).fit(cov_type="HC3")


def build_fat_results(df):
    rows = []
    for scope in ["ALL", *TARGETS]:
        d = df.copy() if scope == "ALL" else df[df["Target"] == scope].copy()
        d = d.dropna(subset=["PCC", "SE_PCC"])
        d = d[d["SE_PCC"] > 0].copy()
        d["Variance"] = d["SE_PCC"].pow(2)
        pet = simple_wls(d, "SE_PCC")
        peese = simple_wls(d, "Variance")
        specifications = [
            ("FAT_slope_SE", pet, "SE_PCC"),
            ("PET_intercept_true_effect", pet, "const"),
            ("PEESE_intercept_true_effect", peese, "const"),
            ("PEESE_slope_variance", peese, "Variance"),
        ]
        for test, result, term in specifications:
            p_value = result.pvalues.get(term, np.nan)
            rows.append({
                "scope": scope,
                "test": test,
                "estimate": result.params.get(term, np.nan),
                "SE": result.bse.get(term, np.nan),
                "z": result.tvalues.get(term, np.nan),
                "p": p_value,
                "significance": significance(p_value),
                "n": len(d),
            })
    return pd.DataFrame(rows)


def draw_plots(df, meta):
    for target in TARGETS:
        d = df[df["Target"] == target].sort_values(["Path", "作者_年份"]).reset_index(drop=True)
        pooled = meta[(meta["stage"] == "overall_full") & (meta["Target"] == target)].iloc[0]
        y_pos = np.arange(len(d), 0, -1)
        fig, ax = plt.subplots(figsize=(9, max(4.5, len(d) * 0.38)))
        for path in PATHS:
            mask = d["Path"] == path
            if mask.any():
                ax.errorbar(d.loc[mask, "PCC"], y_pos[mask.to_numpy()],
                            xerr=1.96 * d.loc[mask, "SE_PCC"], fmt="o",
                            color=COLORS[path], ecolor="#777777", capsize=2,
                            markersize=4.5, label=path)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.axvline(pooled["PCC"], color="#a51c30", linestyle="--", linewidth=1.2,
                   label=f"DL pooled PCC={pooled['PCC']:.3f}")
        ax.axvspan(pooled["CI_low"], pooled["CI_high"], color="#a51c30", alpha=0.10)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(d["作者_年份"], fontsize=8)
        ax.set_xlabel("Partial correlation coefficient (PCC)")
        ax.set_title(f"Strict-path meta-analysis: {target}")
        ax.grid(axis="x", linestyle=":", alpha=0.45)
        ax.legend(fontsize=8, loc="best")
        fig.tight_layout()
        fig.savefig(OUT / f"forest_{target}.png", dpi=300)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.scatter(d["PCC"], d["SE_PCC"], c=d["Path"].map(COLORS), s=30,
                   edgecolors="black", linewidths=0.35)
        ax.axvline(pooled["PCC"], color="#a51c30", linestyle="--", linewidth=1)
        ax.invert_yaxis()
        ax.set_xlabel("PCC")
        ax.set_ylabel("SE(PCC)")
        ax.set_title(f"Funnel plot: {target}")
        ax.grid(alpha=0.35)
        fig.tight_layout()
        fig.savefig(OUT / f"funnel_{target}.png", dpi=300)
        plt.close(fig)


def write_summary(df, meta, wls, fat):
    counts = pd.crosstab(df["Target"], df["Path"], margins=True)
    overall = meta[(meta["stage"] == "overall_full") & (meta["Path"] == "ALL")]
    lines = [
        "# Unified strict-path meta-analysis",
        "",
        "The analysis uses only manually verified MCI/AMS/AML records. "
        "Capital/Rate labels and OTH records are not analysed.",
        "",
        "## Sample counts",
        "",
        counts.to_markdown(),
        "",
        "## DerSimonian-Laird overall effects",
        "",
        overall[["Target", "k", "PCC", "SE", "p", "significance", "CI_low", "CI_high", "I2"]]
        .to_markdown(index=False),
        "",
        "Full numerical results, including subgroup p-values, WLS and FAT/PET/PEESE, "
        "are in `meta_analysis_results.xlsx`.",
        "",
        f"WLS coefficient rows: {len(wls)}; FAT/PET/PEESE rows: {len(fat)}.",
    ]
    (OUT / "meta_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT, encoding="utf-8-sig")
    for column in ["N", "PCC", "SE_PCC", "elasticity"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if not set(df["Path"]).issubset(set(PATHS)):
        raise ValueError("The strict analysis dataset contains a non-analysis path")

    meta, drops = build_meta_results(df)
    wls, wls_notes = build_wls_results(df)
    fat = build_fat_results(df)
    sample_counts = pd.crosstab(df["Target"], df["Path"], margins=True) \
        .rename_axis("Target").reset_index()

    meta.to_csv(OUT / "meta_random_effects.csv", index=False, encoding="utf-8-sig")
    wls.to_csv(OUT / "wls_meta_regression.csv", index=False, encoding="utf-8-sig")
    fat.to_csv(OUT / "fat_pet_peese.csv", index=False, encoding="utf-8-sig")
    drops.to_csv(OUT / "outlier_filter_log.csv", index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(OUT / "meta_analysis_results.xlsx", engine="openpyxl") as writer:
        sample_counts.to_excel(writer, index=False, sheet_name="sample_counts")
        meta.to_excel(writer, index=False, sheet_name="random_effects")
        wls.to_excel(writer, index=False, sheet_name="wls_meta_regression")
        wls_notes.to_excel(writer, index=False, sheet_name="wls_model_notes")
        fat.to_excel(writer, index=False, sheet_name="fat_pet_peese")
        drops.to_excel(writer, index=False, sheet_name="outlier_filter_log")
        df.to_excel(writer, index=False, sheet_name="analysis_sample")

    draw_plots(df, meta)
    write_summary(df, meta, wls, fat)
    print(meta[["stage", "Target", "Path", "k", "PCC", "p", "significance"]].to_string(index=False))
    print(f"Wrote {OUT / 'meta_analysis_results.xlsx'}")


if __name__ == "__main__":
    main()
