
"""
07_province_cluster_bootstrap.py
Step 6 of the revision pipeline: province-clustered block bootstrap through
the FULL estimation pipeline (review Issue 4). Each bootstrap replicate:
  1. Resamples the 30 positive-budget provinces WITH REPLACEMENT (whole
     province-quarter blocks, preserving within-province serial correlation);
     repeated draws of the same province are relabeled as distinct pseudo-
     province identifiers (standard cluster-bootstrap practice, Cameron,
     Gelbach & Miller 2008) so fixed-effect regressions remain full rank.
  2. Rebuilds the quality-adjusted price regression (per product, main
     specification without ln(quantity)) on the resampled data.
  3. Refits the Shonkwiler-Yen participation probit (predetermined lags +
     year FE) on the resampled data.
  4. Refits the Bartik first-stage regression (predicted-trade instrument)
     and recovers a new v-hat control-function residual.
  5. Refits the QUAIDS system by FIML (warm-started from the full-sample
     estimate for speed) and recomputes elasticities at the bootstrap
     sample's own mean reference point.

The resulting empirical distribution of elasticities (own-price Marshallian/
Hicksian, expenditure) is compared to the delta-method (asymptotic normal)
standard errors from Step 4, for the "completed" price measure (the primary
specification). This directly implements the review's Issue 4 remedy.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import norm

import sys as _sys
CODE_DIR = "/root/data/Paper/饲料进口弹性/revision_2026/code"
_sys.path.insert(0, CODE_DIR)
import fiml_aids_quaids as fq

PROJ = "/root/data/Paper/饲料进口弹性/revision_2026"
CKPT_DIR = f"{PROJ}/checkpoints"
OUT_DIR = f"{PROJ}/output"

PRODUCTS = ["corn", "barley", "sorghum", "cassava", "oats"]
OMITTED = "barley"
CONTROLS = ["pork", "beef", "mutton", "poultry_meat", "eggs", "milk"]
PRICE_MEASURE_PRIMARY = "completed"


def winsorize_group(s, lower=0.01, upper=0.99):
    lo, hi = s.quantile(lower), s.quantile(upper)
    return s.clip(lo, hi)


def load_raw_inputs():
    panel_long = pd.read_parquet(f"{CKPT_DIR}/panel_long.parquet")
    bartik = pd.read_parquet(f"{CKPT_DIR}/bartik_instrument.parquet")
    panel_wide = pd.read_parquet(f"{CKPT_DIR}/panel_wide.parquet")
    return panel_long, bartik, panel_wide


def resample_provinces(positive_provinces, rng):
    """Draw len(positive_provinces) provinces with replacement; return a
    mapping original_province -> [list of boot pseudo-ids] (one pseudo-id
    per draw of that province)."""
    draws = rng.choice(positive_provinces, size=len(positive_provinces), replace=True)
    mapping = []  # list of (orig_province, boot_id)
    counts = {}
    for p in draws:
        counts[p] = counts.get(p, 0) + 1
        mapping.append((p, f"{p}__b{counts[p]}"))
    return mapping


def build_boot_panel(panel_long, bartik, panel_wide, mapping):
    """Expand panel_long/bartik/panel_wide rows for each (orig, boot_id) pair
    in `mapping`, relabeling province -> boot_id."""
    frames_pl, frames_bk, frames_pw = [], [], []
    for orig, boot_id in mapping:
        sub_pl = panel_long[panel_long.province == orig].copy()
        sub_pl["province"] = boot_id
        frames_pl.append(sub_pl)
        sub_bk = bartik[bartik.province == orig].copy()
        sub_bk["province"] = boot_id
        frames_bk.append(sub_bk)
        sub_pw = panel_wide[panel_wide.province == orig].copy()
        sub_pw["province"] = boot_id
        frames_pw.append(sub_pw)
    return (pd.concat(frames_pl, ignore_index=True),
            pd.concat(frames_bk, ignore_index=True),
            pd.concat(frames_pw, ignore_index=True))


def refit_prices(panel_long_b):
    pos = panel_long_b[panel_long_b["import_value_usd"] > 0].copy()
    pos = pos[pos["import_qty_kg"] > 0].copy()
    pos["log_uv"] = np.log(pos["unit_value_usd_per_kg"])
    pos["log_uv_wz"] = pos.groupby("product")["log_uv"].transform(winsorize_group)
    pos["log_hhi"] = np.log(pos["hhi"].clip(lower=1e-6))
    pos = pos.dropna(subset=["log_uv_wz", "n_sources", "top_source_share", "log_hhi"]).copy()

    fitted_rows = []
    for p in PRODUCTS:
        sub = pos[pos['product'] == p].copy()
        if sub["province"].nunique() < 3 or sub.shape[0] < 15:
            # too few effective clusters/obs this replicate for this product;
            # fall back to product mean (rare edge case, avoids a crashed replicate)
            sub_all = pos[pos['product'] == p]
            fallback_mean = sub_all["log_uv_wz"].mean() if len(sub_all) else np.nan
            fitted_rows.append((p, None, fallback_mean))
            continue
        formula = "log_uv_wz ~ n_sources + top_source_share + log_hhi + C(province) + C(year_quarter)"
        try:
            model = smf.ols(formula, data=sub).fit()
            fitted_rows.append((p, model, None))
        except Exception:
            fitted_rows.append((p, None, sub["log_uv_wz"].mean()))

    # build full grid price panel (completed measure: pooled product mean fill)
    grid = panel_long_b[["province", "year_quarter", "product"]].drop_duplicates()
    price_frames = []
    for p, model, fallback in fitted_rows:
        sub_grid = grid[grid['product'] == p].copy()
        if model is not None:
            sub_pos = pos[pos['product'] == p][["province", "year_quarter", "log_uv_wz",
                                               "n_sources", "top_source_share", "log_hhi"]]
            sub_grid = sub_grid.merge(sub_pos, on=["province", "year_quarter"], how="left")
            # fitted values for observed rows; pooled mean for missing rows
            try:
                fitted_vals = model.predict(sub_grid)
            except Exception:
                fitted_vals = pd.Series(np.nan, index=sub_grid.index)
            pooled_mean = sub_grid["log_uv_wz"].mean()
            sub_grid["log_price_final"] = fitted_vals.where(sub_grid["log_uv_wz"].notna(), pooled_mean)
            sub_grid["log_price_final"] = sub_grid["log_price_final"].fillna(pooled_mean)
        else:
            sub_grid["log_price_final"] = fallback
        price_frames.append(sub_grid[["province", "year_quarter", "product", "log_price_final"]])
    return pd.concat(price_frames, ignore_index=True)


def refit_sy_probit(panel_long_b):
    df = panel_long_b.copy()
    df["year"] = df["year_quarter"].str[:4].astype(int)
    df["quarter_num"] = df["year_quarter"].str[5:].astype(int)
    df["participate"] = (df["import_value_usd"] > 0).astype(int)
    df = df.sort_values(["province", "product", "year", "quarter_num"])
    df["participate_lag1"] = df.groupby(["province", "product"])["participate"].shift(1)
    df["hist_rate"] = df.groupby(["province", "product"])["participate"].transform(
        lambda s: s.shift(1).expanding().mean()
    )
    out = []
    for p in PRODUCTS:
        sub = df[df['product'] == p].copy()
        unc = sub["participate"].mean()
        sub["participate_lag1_f"] = sub["participate_lag1"].fillna(unc)
        sub["hist_rate_f"] = sub["hist_rate"].fillna(unc)
        try:
            m = smf.probit("participate ~ participate_lag1_f + hist_rate_f + C(year)", data=sub).fit(disp=0)
            xb = m.predict(sub, which="linear")
        except Exception:
            xb = np.full(len(sub), norm.ppf(np.clip(unc, 0.02, 0.98)))
        Phi = norm.cdf(xb)
        phi = norm.pdf(xb)
        o = sub[["province", "year_quarter", "product"]].copy()
        o["selection_Phi"] = np.clip(Phi, 0.01, 0.99)
        o["selection_phi"] = phi
        out.append(o)
    return pd.concat(out, ignore_index=True)


def refit_bartik_first_stage(panel_long_b, bartik_b):
    budget = panel_long_b[["province", "year_quarter", "total_import_expenditure_usd",
                            "positive_budget_flag"]].drop_duplicates()
    budget = budget.merge(bartik_b, on=["province", "year_quarter"], how="left")
    budget = budget[budget.positive_budget_flag == 1].copy()
    budget["ln_X"] = np.log(budget["total_import_expenditure_usd"])
    budget = budget.dropna(subset=["bartik_instrument"]).copy()
    try:
        model = smf.ols("ln_X ~ bartik_instrument + C(province) + C(year_quarter)", data=budget).fit()
        budget["v_hat"] = model.resid
    except Exception:
        budget["v_hat"] = 0.0
    return budget[["province", "year_quarter", "v_hat"]]


def build_sys_from_boot(panel_long_b, price_panel_b, sy_b, vhat_b, panel_wide_b):
    shares = panel_long_b[panel_long_b.positive_budget_flag == 1].pivot_table(
        index=["province", "year_quarter"], columns="product", values="budget_share"
    ).reset_index()
    shares = shares[["province", "year_quarter"] + PRODUCTS]
    if shares.shape[0] < 50:
        return None

    pm = price_panel_b.pivot_table(index=["province", "year_quarter"], columns="product",
                                     values="log_price_final").reset_index()
    pm = pm[["province", "year_quarter"] + PRODUCTS]
    pm.columns = ["province", "year_quarter"] + [f"logp__{p}" for p in PRODUCTS]

    phi_wide = sy_b.pivot_table(index=["province", "year_quarter"], columns="product",
                                  values="selection_Phi").reset_index()
    phi_wide = phi_wide[["province", "year_quarter"] + PRODUCTS]
    phi_wide.columns = ["province", "year_quarter"] + [f"Phi__{p}" for p in PRODUCTS]

    phi_pdf_wide = sy_b.pivot_table(index=["province", "year_quarter"], columns="product",
                                      values="selection_phi").reset_index()
    phi_pdf_wide = phi_pdf_wide[["province", "year_quarter"] + PRODUCTS]
    phi_pdf_wide.columns = ["province", "year_quarter"] + [f"phi__{p}" for p in PRODUCTS]

    budget_flag = panel_long_b[["province", "year_quarter", "positive_budget_flag",
                                  "total_import_expenditure_usd"]].drop_duplicates()
    pos_pq = budget_flag[budget_flag.positive_budget_flag == 1][
        ["province", "year_quarter", "total_import_expenditure_usd"]
    ]

    df = shares.merge(pm, on=["province", "year_quarter"], how="inner")
    df = df.merge(phi_wide, on=["province", "year_quarter"], how="inner")
    df = df.merge(phi_pdf_wide, on=["province", "year_quarter"], how="inner")
    df = df.merge(pos_pq, on=["province", "year_quarter"], how="inner")
    df = df.merge(vhat_b, on=["province", "year_quarter"], how="left")
    df["v_hat"] = df["v_hat"].fillna(0.0)
    df = df.merge(panel_wide_b[["province", "year_quarter"] + CONTROLS], on=["province", "year_quarter"], how="left")
    df = df.dropna(subset=PRODUCTS + [f"logp__{p}" for p in PRODUCTS] + CONTROLS)
    if df.shape[0] < 50:
        return None
    df["ln_X"] = np.log(df["total_import_expenditure_usd"])

    ordered = [p for p in PRODUCTS if p != OMITTED] + [OMITTED]
    logp = df[[f"logp__{p}" for p in ordered]].values
    w = df[ordered].values
    lnX = df["ln_X"].values
    Phi = df[[f"Phi__{p}" for p in ordered]].values
    phi = df[[f"phi__{p}" for p in ordered]].values
    vhat = df["v_hat"].values
    Z = df[CONTROLS].values.astype(float)
    Zmean, Zstd = Z.mean(axis=0), Z.std(axis=0)
    Zstd[Zstd == 0] = 1
    Zs = (Z - Zmean) / Zstd
    return fq.AQSystem(logp, w, lnX, Zs, Phi, phi, vhat, ordered, OMITTED, include_cf=True, corrected=True)


def compute_own_elasticities(fit, sys, quaids, eps=1e-4):
    par = fit["par"]
    N = sys.N
    logp_mean = sys.logp.mean(axis=0, keepdims=True)
    lnX_mean = np.array([sys.lnX.mean()])
    Z_mean = sys.Z.mean(axis=0, keepdims=True) if sys.K > 0 else np.zeros((1, 0))
    vhat_mean = np.array([sys.vhat.mean()])

    g0 = fq.predict_systematic(par, sys, quaids, logp=logp_mean, lnX=lnX_mean, Z=Z_mean, vhat=vhat_mean)[0]
    lnX_p, lnX_m = lnX_mean + eps, lnX_mean - eps
    gp = fq.predict_systematic(par, sys, quaids, logp=logp_mean, lnX=lnX_p, Z=Z_mean, vhat=vhat_mean)[0]
    gm = fq.predict_systematic(par, sys, quaids, logp=logp_mean, lnX=lnX_m, Z=Z_mean, vhat=vhat_mean)[0]
    eta = 1 + (gp - gm) / (2 * eps) / g0

    own_marsh = np.zeros(N)
    own_hicks = np.zeros(N)
    for i in range(N):
        logp_p = logp_mean.copy(); logp_p[0, i] += eps
        logp_m = logp_mean.copy(); logp_m[0, i] -= eps
        gp_i = fq.predict_systematic(par, sys, quaids, logp=logp_p, lnX=lnX_mean, Z=Z_mean, vhat=vhat_mean)[0]
        gm_i = fq.predict_systematic(par, sys, quaids, logp=logp_m, lnX=lnX_mean, Z=Z_mean, vhat=vhat_mean)[0]
        deriv = (gp_i[i] - gm_i[i]) / (2 * eps)
        own_marsh[i] = -1 + deriv / g0[i]
        own_hicks[i] = own_marsh[i] + eta[i] * g0[i]
    return dict(products=sys.eq_products + [sys.omitted], eta=eta, own_marsh=own_marsh, own_hicks=own_hicks)


def run_one_replicate(seed, panel_long, bartik, panel_wide, start_par):
    rng = np.random.default_rng(seed)
    positive_provinces = sorted(
        panel_long[panel_long.positive_budget_flag == 1]["province"].unique()
    )
    mapping = resample_provinces(positive_provinces, rng)
    panel_long_b, bartik_b, panel_wide_b = build_boot_panel(panel_long, bartik, panel_wide, mapping)

    price_panel_b = refit_prices(panel_long_b)
    sy_b = refit_sy_probit(panel_long_b)
    vhat_b = refit_bartik_first_stage(panel_long_b, bartik_b)
    sys_b = build_sys_from_boot(panel_long_b, price_panel_b, sy_b, vhat_b, panel_wide_b)
    if sys_b is None:
        return None
    try:
        fit_b = fq.fit_aids_quaids(sys_b, quaids=True, start=start_par, maxiter=1500, polish=False)
        if not np.all(np.isfinite(fit_b["par"])):
            return None
        el = compute_own_elasticities(fit_b, sys_b, True)
        return el
    except Exception:
        return None


if __name__ == "__main__":
    import pickle
    with open(f"{CKPT_DIR}/fiml_fit_results.pkl", "rb") as f:
        all_results = pickle.load(f)
    primary = all_results[PRICE_MEASURE_PRIMARY]
    start_par = primary["fit_quaids"]["par"]

    panel_long, bartik, panel_wide = load_raw_inputs()

    N_BOOT = 300
    records = []
    n_success = 0
    for b in range(N_BOOT):
        el = run_one_replicate(seed=1000 + b, panel_long=panel_long, bartik=bartik,
                                panel_wide=panel_wide, start_par=start_par)
        if el is None:
            continue
        n_success += 1
        for i, p in enumerate(el["products"]):
            records.append(dict(rep=b, product=p, eta=el["eta"][i],
                                 own_marsh=el["own_marsh"][i], own_hicks=el["own_hicks"][i]))
        if (b + 1) % 25 == 0:
            print(f"  ... {b+1}/{N_BOOT} replicates attempted, {n_success} succeeded")

    boot_df = pd.DataFrame(records)
    boot_df.to_parquet(f"{CKPT_DIR}/bootstrap_elasticities.parquet", index=False)
    print(f"Bootstrap complete: {n_success}/{N_BOOT} replicates succeeded, "
          f"{boot_df['rep'].nunique()} unique reps in output")
