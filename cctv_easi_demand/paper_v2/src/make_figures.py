#!/usr/bin/env python3
"""Publication figures for the Food Policy manuscript.

Reads model_v2_R outputs; skips gracefully anything not yet produced.
All figures saved as 300-dpi PNG + PDF into paper_v2/figures/.
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = "/root/data/Paper/央视数据/Paper1-EASI"
OUT = os.path.join(BASE, "model_v2_R", "outputs")
FIG = os.path.join(BASE, "paper_v2", "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False,
})

EN = {  # English group labels for the manuscript
    "G01_主食": "Staples", "G02_食用油": "Edible oils", "G03_蔬菜": "Vegetables",
    "G04_水果": "Fruits", "G05_猪肉": "Pork", "G06_禽类及其他肉类": "Poultry & other meat",
    "G07_牛羊肉": "Beef & mutton", "G08_海鲜": "Seafood", "G09_乳制品": "Dairy",
}
ORDER = list(EN.values())


def _read(path):
    p = os.path.join(OUT, path)
    if not os.path.exists(p):
        print(f"  [skip] missing {path}")
        return None
    return pd.read_csv(p)


def fig1_price_series():
    d = _read("descriptives/national_price_series_v2.csv")
    if d is None:
        return
    d["label"] = d["food_group10"].map(EN)
    d["t"] = pd.to_datetime(d["year_month"])
    fig, axes = plt.subplots(3, 3, figsize=(7.5, 5.6), sharex=True)
    for ax, lab in zip(axes.flat, ORDER):
        g = d[d["label"] == lab].sort_values("t")
        ax.fill_between(g["t"], g["lp_ext_p10"], g["lp_ext_p90"], alpha=0.25, lw=0)
        ax.plot(g["t"], g["lp_ext_mean"], lw=1.2)
        ax.axhline(0, color="grey", lw=0.5, ls=":")
        ax.set_title(lab)
        ax.tick_params(axis="x", rotation=45)
    fig.supylabel("Log price index (fixed 2021 basket, external prices)")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig1_price_series.{ext}"))
    plt.close(fig)
    print("  fig1 done")


def fig2_own_price_ci():
    d = _read("inference/marshallian_ci_v2.csv")
    if d is None:
        return
    own = d[d["demand_group"] == d["price_group"]].copy()
    own["label"] = own["demand_group"].map(EN)
    own = own.set_index("label").loc[ORDER[::-1]].reset_index()
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    y = np.arange(len(own))
    ax.errorbar(own["estimate"], y,
                xerr=np.maximum(0, [own["estimate"] - own["ci_lo"], own["ci_hi"] - own["estimate"]]),
                fmt="o", ms=4, capsize=2.5, lw=1, color="#1f4e79")
    ax.axvline(0, color="grey", lw=0.7, ls=":")
    ax.set_yticks(y)
    ax.set_yticklabels(own["label"])
    ax.set_xlabel("Marshallian own-price elasticity (95% cluster-bootstrap CI)")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig2_own_price_ci.{ext}"))
    plt.close(fig)
    print("  fig2 done")


def _fig3_panel(inc, value, lo, hi, ylab, color, marker, fname, title):
    """One elasticity type (expenditure OR own-price) across income groups,
    a 2x3 small-multiple over the six focus groups."""
    show = ["Staples", "Vegetables", "Pork", "Beef & mutton", "Seafood", "Dairy"]
    fig, axes = plt.subplots(2, 3, figsize=(7.5, 4.4), sharex=True)
    for ax, lab in zip(axes.flat, show):
        g = inc[inc["label"] == lab].sort_values("q")
        ax.errorbar(g["q"], g[value],
                    yerr=np.maximum(0, [g[value] - g[lo], g[hi] - g[value]]),
                    fmt=marker, ms=3.5, capsize=2, lw=1, color=color)
        ax.axhline(0, color="grey", lw=0.5, ls=":")
        ax.set_title(lab)
        ax.set_xticks(range(1, 6))
    fig.supxlabel("Household income group (1 = lowest)")
    fig.supylabel(ylab)
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"{fname}.{ext}"))
    plt.close(fig)


def fig3_heterogeneity():
    d = _read("inference/subgroup_elasticity_ci_v2.csv")
    if d is None:
        return
    d["label"] = d["food_group10"].map(EN)
    inc = d[d["subgroup"].str.match(r"inc[1-5]")].copy()
    inc["q"] = inc["subgroup"].str[3].astype(int)
    # Split into two separate figures (expenditure vs own-price) per request.
    _fig3_panel(inc, "expenditure", "exp_lo", "exp_hi",
                "Expenditure elasticity", "#1f4e79", "-o",
                "fig3a_expenditure_by_income",
                "Expenditure elasticities by income group")
    _fig3_panel(inc, "own_price", "own_lo", "own_hi",
                "Own-price elasticity", "#c00000", "-s",
                "fig3b_ownprice_by_income",
                "Own-price elasticities by income group")
    print("  fig3a/fig3b done")


def fig4_welfare():
    d = _read("welfare/cv_national_by_income_v2.csv")
    if d is None:
        return
    d["q"] = d["income_group"].str[3].astype(int)
    d = d.sort_values("q")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
    ax = axes[0]
    ax.bar(d["q"] - 0.2, 100 * d["first_order"], width=0.4,
           label="First-order (no substitution)", color="#9dc3e6")
    ax.bar(d["q"] + 0.2, 100 * d["cv_share"], width=0.4,
           label="CV (with substitution)", color="#1f4e79")
    if "ci_lo" in d.columns:
        ax.errorbar(d["q"] + 0.2, 100 * d["cv_share"],
                    yerr=np.maximum(0, [100 * (d["cv_share"] - d["ci_lo"]), 100 * (d["ci_hi"] - d["cv_share"])]),
                    fmt="none", ecolor="black", capsize=2, lw=0.9)
    ax.set_xlabel("Income group (1 = lowest)")
    ax.set_ylabel("Welfare loss, % of food budget")
    ax.legend(frameon=False)
    ax2 = axes[1]
    ax2.bar(d["q"], d["cv_yuan_per_year"], color="#1f4e79", width=0.55)
    ax2.set_xlabel("Income group (1 = lowest)")
    ax2.set_ylabel("CV, yuan per household per year")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig4_welfare.{ext}"))
    plt.close(fig)
    print("  fig4 done")


def fig5_regularity():
    eg = _read("regularity/curvature_representative_points_v2.csv")
    if eg is None:
        return
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    y = np.arange(len(eg))
    ax.scatter(eg["eig_max_unconstrained"], y, marker="x", color="#c00000",
               label="Unconstrained", s=25)
    ax.scatter(eg["eig_max_constrained"], y, marker="o", color="#1f4e79",
               label="Curvature-constrained", s=22)
    ax.axvline(0, color="grey", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(eg["point"])
    ax.set_xlabel("Largest eigenvalue of the Slutsky matrix at evaluation point")
    ax.legend(frameon=False, loc="center right")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig5_regularity.{ext}"))
    plt.close(fig)
    print("  fig5 done")


if __name__ == "__main__":
    print("[figures]")
    fig1_price_series()
    fig2_own_price_ci()
    fig3_heterogeneity()
    fig4_welfare()
    fig5_regularity()
    print("[figures] done")
