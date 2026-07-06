
"""
05_sy_probit_bartik_first_stage.py
Step 3 of the pipeline: Shonkwiler-Yen (1999) participation (probit) stage,
and the Bartik-instrumented first-stage regression for total five-product
import expenditure (the control-function residual v-hat used later in FIML).

SY probit design (per product): only PREDETERMINED / strictly lagged
regressors are used on the right-hand side, to avoid the "current-period
source-country variables leak into the selection equation" mechanical
problem flagged in the review (Issue 4/5 area): lagged participation
indicator, expanding historical participation rate (both computed using only
information up to t-1), plus province and year fixed effects. Current-period
source-country composition variables (n_sources, hhi, top_source_share) are
NOT included, unlike in the original code overview's Phi/phi construction.

Bartik first stage: regress ln(total five-product import expenditure) on the
Bartik instrument (province exposure to non-agricultural imports x national
leave-one-out growth) plus province and year-quarter fixed effects; report
the partial F-statistic on the instrument and save the first-stage residual
v-hat as the control-function term for FIML estimation.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import norm

PROJ = "/root/data/Paper/饲料进口弹性/revision_2026"
CKPT_DIR = f"{PROJ}/checkpoints"
OUT_DIR = f"{PROJ}/output"

PRODUCTS = ["corn", "barley", "sorghum", "cassava", "oats"]


def build_participation_panel():
    panel_long = pd.read_parquet(f"{CKPT_DIR}/panel_long.parquet")
    panel_long["year"] = panel_long["year_quarter"].str[:4].astype(int)
    panel_long["quarter_num"] = panel_long["year_quarter"].str[5:].astype(int)
    panel_long["participate"] = (panel_long["import_value_usd"] > 0).astype(int)
    panel_long = panel_long.sort_values(["province", "product", "year", "quarter_num"])
    panel_long["participate_lag1"] = panel_long.groupby(["province", "product"])["participate"].shift(1)
    panel_long["hist_participation_rate"] = panel_long.groupby(["province", "product"])["participate"].transform(
        lambda s: s.shift(1).expanding().mean()
    )
    return panel_long


def fit_sy_probit(panel_long):
    """Fit probit per product; return fitted Phi (CDF) and phi (pdf) for
    every province-quarter-product cell (including the first period, using
    unconditional fills for the lag terms so no observations are dropped
    from the downstream demand system)."""
    results = []
    diagnostics = []
    for p in PRODUCTS:
        sub = panel_long[panel_long["product"] == p].copy()
        unconditional_rate = sub["participate"].mean()
        sub["participate_lag1_f"] = sub["participate_lag1"].fillna(unconditional_rate)
        sub["hist_rate_f"] = sub["hist_participation_rate"].fillna(unconditional_rate)
        # Note: province fixed effects are DELIBERATELY excluded here. With only
        # 28 quarters per province, several provinces never (or always) import a
        # given product, producing quasi-complete separation with province
        # dummies (MLE fails to converge / diverges to +-inf). The lagged
        # participation indicator and expanding historical participation rate
        # already absorb province-specific persistence without inducing
        # separation; year fixed effects absorb common aggregate shocks.
        formula = "participate ~ participate_lag1_f + hist_rate_f + C(year)"
        model = smf.probit(formula, data=sub).fit(disp=0)
        if not model.mle_retvals.get("converged", True):
            raise RuntimeError(f"Probit failed to converge for product={p}")
        xb = model.predict(sub, linear=True)
        Phi = norm.cdf(xb)
        phi = norm.pdf(xb)
        out = sub[["province", "year_quarter", "product"]].copy()
        out["selection_Phi"] = np.clip(Phi, 0.01, 0.99)
        out["selection_phi"] = phi
        results.append(out)
        diagnostics.append({
            "product": p, "n_obs": int(model.nobs), "pseudo_r2": model.prsquared,
            "coef_participate_lag1": model.params.get("participate_lag1_f", np.nan),
            "se_participate_lag1": model.bse.get("participate_lag1_f", np.nan),
            "coef_hist_rate": model.params.get("hist_rate_f", np.nan),
            "se_hist_rate": model.bse.get("hist_rate_f", np.nan),
        })
    return pd.concat(results, ignore_index=True), pd.DataFrame(diagnostics)


def bartik_first_stage():
    """First-stage regression of ln(total 5-product import expenditure) on
    the Bartik instrument, with province and year-quarter fixed effects.
    Returns the residual v-hat (control function term) and diagnostics."""
    panel_long = pd.read_parquet(f"{CKPT_DIR}/panel_long.parquet")
    bartik = pd.read_parquet(f"{CKPT_DIR}/bartik_instrument.parquet")

    budget = panel_long[["province", "year_quarter", "total_import_expenditure_usd",
                          "positive_budget_flag"]].drop_duplicates()
    budget = budget.merge(bartik, on=["province", "year_quarter"], how="left")
    budget = budget[budget["positive_budget_flag"] == 1].copy()
    budget["ln_X"] = np.log(budget["total_import_expenditure_usd"])
    budget = budget.dropna(subset=["bartik_instrument"]).copy()

    formula = "ln_X ~ bartik_instrument + C(province) + C(year_quarter)"
    model = smf.ols(formula, data=budget).fit(cov_type="cluster", cov_kwds={"groups": budget["province"]})

    # partial F-statistic on the excluded instrument only
    from statsmodels.stats.anova import anova_lm
    restricted = smf.ols("ln_X ~ C(province) + C(year_quarter)", data=budget).fit()
    f_test = model.compare_f_test(restricted)

    budget["v_hat"] = model.resid
    diag = {
        "n_obs": int(model.nobs), "r_squared": model.rsquared,
        "coef_bartik": model.params.get("bartik_instrument", np.nan),
        "se_bartik": model.bse.get("bartik_instrument", np.nan),
        "t_bartik": model.tvalues.get("bartik_instrument", np.nan),
        "partial_F": f_test[0], "partial_F_pvalue": f_test[1],
    }
    return budget[["province", "year_quarter", "v_hat", "ln_X", "bartik_instrument"]], pd.DataFrame([diag])


if __name__ == "__main__":
    panel_long = build_participation_panel()
    sy_out, sy_diag = fit_sy_probit(panel_long)
    sy_diag.to_csv(f"{OUT_DIR}/selection_stage_params.csv", index=False)
    sy_out.to_parquet(f"{CKPT_DIR}/sy_selection.parquet", index=False)

    vhat_out, fs_diag = bartik_first_stage()
    fs_diag.to_csv(f"{OUT_DIR}/expenditure_first_stage_diagnostics.csv", index=False)
    vhat_out.to_parquet(f"{CKPT_DIR}/expenditure_vhat.parquet", index=False)

    print("SY probit diagnostics:")
    print(sy_diag.to_string())
    print("\\nBartik first-stage diagnostics:")
    print(fs_diag.to_string())
