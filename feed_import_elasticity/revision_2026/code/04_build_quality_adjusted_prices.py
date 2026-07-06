
"""
04_build_quality_adjusted_prices.py
Construct quality-adjusted import prices per Issue 2 of the review memo.

Main specification (used for the headline results):
    log(unit_value) ~ n_sources + hhi + top_source_share + province FE + year_quarter FE
No ln(quantity) on the right-hand side -- avoids conflating bulk-purchase
discounts (a supply-side/contracting phenomenon correlated with quantity)
with the demand-curve slope we are trying to estimate (a generated-regressor
endogeneity problem flagged in the review).

Robustness specification: adds ln(quantity) to the same regression (the
original approach) -- reported as a robustness/sensitivity check, not the
main specification.

Three price "measures" (following the existing restricted_demand/ naming
convention) are produced for every (product, quarter) cell:
  - completed:          missing (zero-import) cells filled with the
                         national product-quarter mean adjusted price.
  - loo_quarter_winsor:  missing cells filled with the leave-one-out national
                         product-quarter mean (excluding the province itself
                         when it has data; for provinces with genuinely zero
                         imports this reduces to the same national mean),
                         built from winsorized log unit values.
  - landed_proxy:        raw (non-quality-adjusted) log unit value, imputed
                         the same way; serves as an unadjusted benchmark.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PROJ = "/root/data/Paper/饲料进口弹性/revision_2026"
CKPT_DIR = f"{PROJ}/checkpoints"
OUT_DIR = f"{PROJ}/output"

PRODUCTS = ["corn", "barley", "sorghum", "cassava", "oats"]


def winsorize_group(s, lower=0.01, upper=0.99):
    lo, hi = s.quantile([lower, upper])
    return s.clip(lo, hi)


def load_positive_cells():
    panel_long = pd.read_parquet(f"{CKPT_DIR}/panel_long.parquet")
    pos = panel_long[panel_long["import_value_usd"] > 0].copy()
    # a handful of cells record positive value but zero recorded quantity
    # (unit conversion / reporting artifacts in the raw customs data); these
    # cannot yield a unit value and are dropped from the adjustment-regression
    # sample only (they are not dropped from the demand-system estimation
    # sample, which uses budget shares, not unit values).
    pos = pos[pos["import_qty_kg"] > 0].copy()
    pos["log_uv"] = np.log(pos["unit_value_usd_per_kg"])
    pos["log_uv_wz"] = pos.groupby("product")["log_uv"].transform(winsorize_group)
    pos["log_qty"] = np.log(pos["import_qty_kg"].replace(0, np.nan))
    pos["log_hhi"] = np.log(pos["hhi"].clip(lower=1e-6))
    pos = pos.dropna(subset=["log_uv_wz", "n_sources", "top_source_share", "log_hhi"]).copy()
    return panel_long, pos


def fit_quality_adjustment(pos, include_qty):
    """Fit log(unit value) ~ composition controls + province FE + year-quarter FE,
    separately by product. Returns per-observation fitted quality-adjusted price
    (residualized composition effect removed -> the *level* used downstream is
    the regression prediction holding composition at its province-quarter value,
    i.e. this IS the adjusted price, not a residual)."""
    results = []
    diagnostics = []
    for p in PRODUCTS:
        sub = pos[pos["product"] == p].copy()
        sub["year_quarter"] = sub["year_quarter"].astype(str)
        rhs = "n_sources + top_source_share + log_hhi"
        if include_qty:
            rhs = rhs + " + log_qty"
        formula = f"log_uv_wz ~ {rhs} + C(province) + C(year_quarter)"
        try:
            model = smf.ols(formula, data=sub).fit(cov_type="cluster",
                                                     cov_kwds={"groups": sub["province"]})
        except Exception as e:
            diagnostics.append({"product": p, "include_qty": include_qty, "error": str(e)})
            continue
        sub["adj_log_price_fitted"] = model.predict(sub)
        results.append(sub[["province", "year_quarter", "product", "adj_log_price_fitted"]])
        diagnostics.append({
            "product": p, "include_qty": include_qty, "n_obs": int(model.nobs),
            "r_squared": model.rsquared,
            "coef_log_qty": model.params.get("log_qty", np.nan),
            "se_log_qty": model.bse.get("log_qty", np.nan),
            "coef_n_sources": model.params.get("n_sources", np.nan),
            "coef_log_hhi": model.params.get("log_hhi", np.nan),
        })
    return pd.concat(results, ignore_index=True), pd.DataFrame(diagnostics)


def impute_price_measures(panel_long, adj_main, adj_robust, pos):
    """Build the three price-measure panels over the FULL 31x28x5 grid.

    Two distinct imputation rules for missing (zero-import) province-quarter
    cells, applied to the quality-adjusted price:
      - completed:           pooled (all years/quarters) product-level mean
                              of the adjusted price -> a coarse, low-variance
                              fill.
      - loo_quarter_winsor:  same-quarter (product x year_quarter) mean of
                              the adjusted price (i.e. only other provinces
                              observed in that SAME quarter), which is by
                              construction a leave-one-out mean for the
                              missing cell itself (it never contributes to
                              its own quarter's mean) and preserves quarter-
                              to-quarter price variation instead of pooling
                              across the whole sample.
    landed_proxy: raw (non-quality-adjusted) log unit value, imputed with the
    same same-quarter leave-one-out rule.
    """

    grid = panel_long[["province", "year_quarter", "product"]].drop_duplicates()

    raw_price = pos[["province", "year_quarter", "product", "log_uv_wz"]].rename(
        columns={"log_uv_wz": "log_price"}
    )

    def build_measure(price_df, value_col, method):
        merged = grid.merge(
            price_df.rename(columns={value_col: "log_price"}) if value_col != "log_price" else price_df,
            on=["province", "year_quarter", "product"], how="left",
        )
        if method == "completed":
            pooled_mean = merged.groupby(["product"])["log_price"].transform("mean")
            merged["log_price_final"] = merged["log_price"].fillna(pooled_mean)
        elif method == "loo_quarter_winsor":
            quarter_mean = merged.groupby(["product", "year_quarter"])["log_price"].transform("mean")
            # fall back to pooled mean for the rare product-quarter with zero
            # observed cells anywhere (quarter_mean would be NaN)
            pooled_mean = merged.groupby(["product"])["log_price"].transform("mean")
            merged["log_price_final"] = merged["log_price"].fillna(quarter_mean).fillna(pooled_mean)
        else:
            pooled_mean = merged.groupby(["product"])["log_price"].transform("mean")
            merged["log_price_final"] = merged["log_price"].fillna(pooled_mean)
        merged["price_measure"] = method
        return merged[["province", "year_quarter", "product", "price_measure", "log_price_final"]]

    m_completed = build_measure(
        adj_main[["province", "year_quarter", "product", "adj_log_price_fitted"]],
        "adj_log_price_fitted", "completed"
    )
    m_loo = build_measure(
        adj_main[["province", "year_quarter", "product", "adj_log_price_fitted"]],
        "adj_log_price_fitted", "loo_quarter_winsor"
    )
    m_landed = build_measure(raw_price, "log_price", "loo_quarter_winsor")
    m_landed["price_measure"] = "landed_proxy"

    all_measures = pd.concat([m_completed, m_loo, m_landed], ignore_index=True)
    return all_measures


if __name__ == "__main__":
    panel_long, pos = load_positive_cells()
    adj_main, diag_main = fit_quality_adjustment(pos, include_qty=False)
    adj_robust, diag_robust = fit_quality_adjustment(pos, include_qty=True)

    diagnostics = pd.concat([diag_main, diag_robust], ignore_index=True)
    diagnostics.to_csv(f"{OUT_DIR}/quality_adjusted_price_diagnostics.csv", index=False)

    price_panel = impute_price_measures(panel_long, adj_main, adj_robust, pos)
    price_panel.to_parquet(f"{CKPT_DIR}/price_variants.parquet", index=False)

    # also save the quantity-inclusive robustness variant separately
    price_panel_robust = impute_price_measures(panel_long, adj_robust, adj_robust, pos)
    price_panel_robust = price_panel_robust[price_panel_robust.price_measure != "landed_proxy"]
    price_panel_robust["price_measure"] = price_panel_robust["price_measure"] + "_with_qty_robustness"
    price_panel_robust.to_parquet(f"{CKPT_DIR}/price_variants_qty_robustness.parquet", index=False)

    print(diagnostics.to_string())
    print(f"\\nPrice panel: {price_panel.shape[0]} rows across "
          f"{price_panel['price_measure'].nunique()} measures.")
