# -*- coding: utf-8 -*-
"""Meta-analysis of agricultural mechanisation and grain production capacity.

Reproduces manuscript Section 4 (Tables 1-5 and forest/funnel figures):
  Table 1  Overall pooled effects (DerSimonian-Laird random effects)
  Table 2  Subgroup pooled effects by mechanisation path
  Table 3  WLS meta-regression (path premia; study-clustered robust SE)
  Table 4  Publication-bias diagnostics (FAT-PET-PEESE)
  Table 5  Robustness (IQR trimming / simple mean / sample-size weighting)

Effect size = partial correlation coefficient (PCC). Random-effects pooling
uses DerSimonian-Laird tau^2 with normal inference (manuscript convention);
a Knapp-Hartung (KH) t-interval is reported alongside as a robustness column.

Run:  python meta_analysis.py
Deps: numpy, pandas, scipy, statsmodels, matplotlib
"""
import os

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(HERE, ".mpl"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

for _f in ["Noto Sans CJK SC", "Noto Serif CJK SC", "AR PL SungtiL GB",
           "WenQuanYi Zen Hei", "SimHei"]:
    if _f in {f.name for f in font_manager.fontManager.ttflist}:
        plt.rcParams["font.sans-serif"] = [_f, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False

log = []


def out(m=""):
    print(m)
    log.append(str(m))


def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


df = pd.read_csv(os.path.join(HERE, "data", "meta_dataset.csv"),
                 encoding="utf-8-sig").dropna(subset=["PCC", "SE_PCC"])
TARGETS = ["Yield", "Area", "Efficiency"]
PATHS = ["MCI", "AMS", "AML"]
TNAME = {"Yield": "Grain yield", "Area": "Sown area",
         "Efficiency": "Production efficiency"}
PNAME = {"MCI": "Machinery capital input (MCI)",
         "AMS": "Machinery services (AMS)",
         "AML": "Comprehensive mechanisation (AML)"}


def pool_dl(y, v):
    """DerSimonian-Laird random-effects pooling (normal inference) + KH CI."""
    k = len(y)
    w = 1.0 / v
    mu_f = np.sum(w * y) / np.sum(w)
    Q = np.sum(w * (y - mu_f) ** 2)
    C = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max((Q - (k - 1)) / C, 0.0) if C > 0 and k > 1 else 0.0
    wr = 1.0 / (v + tau2)
    mu = np.sum(wr * y) / np.sum(wr)
    se = np.sqrt(1.0 / np.sum(wr))
    p = 2 * stats.norm.sf(abs(mu / se)) if se > 0 else np.nan
    I2 = max(0.0, (Q - (k - 1)) / Q) * 100 if Q > 0 and k > 1 else 0.0
    if k > 1:
        s2 = np.sum(wr * (y - mu) ** 2) / ((k - 1) * np.sum(wr))
        se_kh = np.sqrt(max(s2, se ** 2))
        tc = stats.t.ppf(0.975, k - 1)
        kh = (mu - tc * se_kh, mu + tc * se_kh)
        p_kh = 2 * stats.t.sf(abs(mu / se_kh), k - 1)
    else:
        kh, p_kh = (np.nan, np.nan), np.nan
    return dict(k=k, mu=mu, se=se, ci=(mu - 1.96 * se, mu + 1.96 * se),
                p=p, Q=Q, I2=I2, tau2=tau2, kh=kh, p_kh=p_kh)


# ---------------------------------------------------------------- Table 1
out("=" * 74)
out("Table 1  Overall pooled effects (DerSimonian-Laird random effects)")
out("=" * 74)
rows = []
for tg in TARGETS:
    d = df[df["Target"] == tg]
    r = pool_dl(d["PCC"].values, d["SE_PCC"].values ** 2)
    out(f"{TNAME[tg]:22s} k={r['k']:>2d} PCC={r['mu']:.3f}{stars(r['p']):<3s} "
        f"[{r['ci'][0]:.3f}, {r['ci'][1]:.3f}]  I2={r['I2']:.1f}%  Q={r['Q']:.2f}"
        f"  | KH [{r['kh'][0]:.3f}, {r['kh'][1]:.3f}] p={r['p_kh']:.3f}")
    rows.append(dict(dimension=TNAME[tg], k=r["k"], pooled_PCC=round(r["mu"], 3),
                     sig=stars(r["p"]), CI_low=round(r["ci"][0], 3),
                     CI_high=round(r["ci"][1], 3), p=round(r["p"], 4),
                     I2=round(r["I2"], 1), Q=round(r["Q"], 2),
                     KH_CI_low=round(r["kh"][0], 3),
                     KH_CI_high=round(r["kh"][1], 3), KH_p=round(r["p_kh"], 4)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "Table1_overall.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- Table 2
out("\n" + "=" * 74)
out("Table 2  Subgroup pooled effects by mechanisation path")
out("=" * 74)
rows = []
for tg in TARGETS:
    for p in ["ALL"] + PATHS:
        d = df[df["Target"] == tg] if p == "ALL" else \
            df[(df["Target"] == tg) & (df["Path"] == p)]
        if len(d) == 0:
            continue
        r = pool_dl(d["PCC"].values, d["SE_PCC"].values ** 2)
        nm = "All studies" if p == "ALL" else PNAME[p]
        out(f"{TNAME[tg]:22s} {nm:34s} k={r['k']:>2d} "
            f"PCC={r['mu']:+.3f}{stars(r['p']):<3s} "
            f"[{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]  I2={r['I2']:.1f}%")
        rows.append(dict(dimension=TNAME[tg], path=nm, k=r["k"],
                         pooled_PCC=round(r["mu"], 3), sig=stars(r["p"]),
                         CI_low=round(r["ci"][0], 3),
                         CI_high=round(r["ci"][1], 3), I2=round(r["I2"], 1)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "Table2_subgroup.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- Table 3
out("\n" + "=" * 74)
out("Table 3  WLS meta-regression (baseline = MCI; study-clustered robust SE)")
out("=" * 74)
rows = []
LAB = {"const": "Constant", "AMS": "AMS (vs MCI)", "AML": "AML (vs MCI)",
       "LogN": "log(N)"}
for tg in TARGETS:
    d = df[df["Target"] == tg].copy()
    d["AMS"] = (d["Path"] == "AMS").astype(float)
    d["AML"] = (d["Path"] == "AML").astype(float)
    w = 1.0 / d["SE_PCC"].values ** 2   # inverse-variance (Stanley-Doucouliagos)
    cols = ["AMS", "AML"] if tg == "Area" else ["AMS", "AML", "LogN"]
    cols = [c for c in cols if d[c].std() > 0]
    X = sm.add_constant(d[cols].astype(float))
    g = d["author_year"].astype("category").cat.codes
    res = sm.WLS(d["PCC"].astype(float), X, weights=w).fit(
        cov_type="cluster", cov_kwds={"groups": g})
    out(f"\n[{TNAME[tg]}] k={len(d)}")
    for nm in res.params.index:
        b, s, pv = res.params[nm], res.bse[nm], res.pvalues[nm]
        out(f"  {LAB.get(nm, nm):14s} {b:+.3f}{stars(pv):<3s} ({s:.3f})")
        rows.append(dict(dimension=TNAME[tg], variable=LAB.get(nm, nm),
                         coef=round(b, 3), se=round(s, 3), p=round(pv, 4),
                         sig=stars(pv), N=len(d)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "Table3_meta_regression.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- Table 4
out("\n" + "=" * 74)
out("Table 4  Publication bias (FAT-PET-PEESE; 1/v weights, clustered SE)")
out("=" * 74)
rows = []
for tg in TARGETS:
    d = df[df["Target"] == tg]
    y, se = d["PCC"].astype(float), d["SE_PCC"].astype(float)
    w = 1.0 / se ** 2
    g = d["author_year"].astype("category").cat.codes
    pet = sm.WLS(y, sm.add_constant(se.rename("SE")), weights=w).fit(
        cov_type="cluster", cov_kwds={"groups": g})
    fb, fp = pet.params["SE"], pet.pvalues["SE"]
    pb, pp = pet.params["const"], pet.pvalues["const"]
    out(f"\n[{TNAME[tg]}] k={len(d)}")
    out(f"  FAT slope = {fb:+.3f}{stars(fp)} (p={fp:.4f})   "
        f"PET intercept = {pb:+.3f}{stars(pp)} (p={pp:.4f})")
    rows += [dict(dimension=TNAME[tg], test="FAT", coef=round(fb, 3),
                  p=round(fp, 4), sig=stars(fp)),
             dict(dimension=TNAME[tg], test="PET", coef=round(pb, 3),
                  p=round(pp, 4), sig=stars(pp))]
    if pp < 0.05:
        pe = sm.WLS(y, sm.add_constant((se ** 2).rename("Var")),
                    weights=w).fit(cov_type="cluster", cov_kwds={"groups": g})
        out(f"  PEESE = {pe.params['const']:+.3f}"
            f"{stars(pe.pvalues['const'])} (p={pe.pvalues['const']:.4f})")
        rows.append(dict(dimension=TNAME[tg], test="PEESE",
                         coef=round(pe.params["const"], 3),
                         p=round(pe.pvalues["const"], 4),
                         sig=stars(pe.pvalues["const"])))
    # funnel plot
    plt.figure(figsize=(5.5, 4.5))
    mu = np.average(y, weights=w)
    plt.scatter(y, se, s=26, alpha=0.75, edgecolors="k", linewidths=0.4)
    ys = np.linspace(0, se.max() * 1.1, 40)
    plt.plot([mu, mu], [0, se.max() * 1.1], "r--", lw=1, label=f"mean={mu:.3f}")
    plt.plot(mu - 1.96 * ys, ys, "k:", lw=0.8)
    plt.plot(mu + 1.96 * ys, ys, "k:", lw=0.8, label="pseudo-95% CI")
    plt.gca().invert_yaxis()
    plt.xlabel("PCC"); plt.ylabel("SE(PCC)")
    plt.title(f"Funnel plot: {TNAME[tg]} (k={len(d)})")
    plt.legend(fontsize=8); plt.grid(alpha=0.4); plt.tight_layout()
    plt.savefig(os.path.join(OUT, f"funnel_{tg}.png"), dpi=300)
    plt.close()
pd.DataFrame(rows).to_csv(os.path.join(OUT, "Table4_fat_pet_peese.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- Table 5
out("\n" + "=" * 74)
out("Table 5  Robustness (IQR trimming / simple mean / sample-size weighting)")
out("=" * 74)
rows = []
for tg in TARGETS:
    d = df[df["Target"] == tg]
    y, v = d["PCC"].values, d["SE_PCC"].values ** 2
    base = pool_dl(y, v)
    q1, q3 = np.percentile(y, [25, 75])
    iqr = q3 - q1
    keep = (y >= q1 - 1.5 * iqr) & (y <= q3 + 1.5 * iqr)
    trim = pool_dl(y[keep], v[keep]) if keep.sum() > 1 else base
    dropped = d.loc[~keep, "study_id"].tolist()
    nw = np.nansum(d["N"].values * y) / np.nansum(d["N"].values)
    out(f"{TNAME[tg]:22s} RE={base['mu']:.3f}  "
        f"IQR-trim={trim['mu']:.3f}(k={int(keep.sum())}, drop:"
        f"{','.join(dropped) or '-'})  mean={y.mean():.3f}  Nwt={nw:.3f}")
    for lab, val, kk in [("Random effects (base)", base["mu"], len(y)),
                         ("IQR-trimmed", trim["mu"], int(keep.sum())),
                         ("Simple mean", y.mean(), len(y)),
                         ("Sample-size weighted", nw, len(y))]:
        rows.append(dict(dimension=TNAME[tg], weighting=lab,
                         pooled_PCC=round(val, 3), k=kk))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "Table5_robustness.csv"),
                          index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- forest plots
for tg in TARGETS:
    d = df[df["Target"] == tg].sort_values(["Path", "author_year"]).reset_index(drop=True)
    r = pool_dl(d["PCC"].values, d["SE_PCC"].values ** 2)
    k = len(d)
    colors = {"MCI": "#1f77b4", "AMS": "#d62728", "AML": "#2ca02c"}
    plt.figure(figsize=(8, max(3.5, 0.36 * k)))
    yp = np.arange(k, 0, -1)
    for p in PATHS:
        m = (d["Path"] == p).values
        if m.sum():
            plt.errorbar(d["PCC"][m], yp[m], xerr=1.96 * d["SE_PCC"][m],
                         fmt="o", ms=4, color=colors[p], ecolor="gray",
                         capsize=2, label=p)
    plt.axvline(0, color="black", lw=1)
    plt.axvline(r["mu"], color="red", ls="--",
                label=f"Pooled = {r['mu']:.3f}{stars(r['p'])}")
    plt.axvspan(r["ci"][0], r["ci"][1], color="red", alpha=0.12)
    plt.yticks(yp, d["author_year"], fontsize=7)
    plt.xlabel("Partial correlation coefficient (PCC)")
    plt.title(f"Forest plot: {TNAME[tg]} (k={k})")
    plt.legend(loc="lower right", fontsize=8)
    plt.grid(axis="x", ls=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, f"forest_{tg}.png"), dpi=300)
    plt.close()

with open(os.path.join(OUT, "meta_analysis_log.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(log) + "\n")
out("\nDone. Tables and figures written to results/")
