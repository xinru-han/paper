
"""
06_fit_fiml_aids_quaids.py
Step 4 of the revision pipeline: fit AIDS and QUAIDS by FIML (Shonkwiler-Yen
corrected, Bartik control-function augmented) for each of the three price
measures (completed, loo_quarter_winsor, landed_proxy), then:
  - run the Bewley (1986) small-sample LR test for AIDS vs QUAIDS
  - compute delta-method parameter covariances (2 * Hessian(obj)^-1) and
    report the Hessian condition number / number of truncated singular
    values as an identification-strength diagnostic (review Issue 4)
  - report the full Gamma matrix with standard errors, plus a joint Wald
    test of H0: all gamma_ij = 0 (review Issue 1, remedy 1)
  - fit a curvature-constrained (Slutsky negative-semi-definite) version of
    the preferred (QUAIDS) model via SLSQP with a max-eigenvalue inequality
    constraint, and compare its objective value / elasticities to the
    unconstrained fit
  - compute Marshallian/Hicksian/Morishima elasticities (Green-Alston
    convention: numerical derivatives of the systematic share function,
    NOT multiplied by Phi-hat -- see review Issue 3) at the sample mean,
    for both the unconstrained and curvature-constrained fits
  - compute the "mechanical benchmark" elasticities obtained by zeroing out
    all estimated gamma parameters while holding alpha/beta/lambda fixed,
    and report the Full-minus-Mechanical decomposition (review Issue 1)
"""
import numpy as np
import pandas as pd
from scipy.optimize import NonlinearConstraint, minimize
from scipy.stats import chi2 as chi2_dist

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
PRICE_MEASURES = ["completed", "loo_quarter_winsor", "landed_proxy"]


def load_inputs():
    panel_long = pd.read_parquet(f"{CKPT_DIR}/panel_long.parquet")
    price_variants = pd.read_parquet(f"{CKPT_DIR}/price_variants.parquet")
    sy_selection = pd.read_parquet(f"{CKPT_DIR}/sy_selection.parquet")
    vhat_df = pd.read_parquet(f"{CKPT_DIR}/expenditure_vhat.parquet")
    panel_wide = pd.read_parquet(f"{CKPT_DIR}/panel_wide.parquet")
    return panel_long, price_variants, sy_selection, vhat_df, panel_wide


def build_shares(panel_long):
    shares = panel_long[panel_long.positive_budget_flag == 1].pivot_table(
        index=["province", "year_quarter"], columns="product", values="budget_share"
    ).reset_index()
    return shares[["province", "year_quarter"] + PRODUCTS]


def assemble_estimation_data(price_measure, shares, price_variants, sy_selection, vhat_df, panel_wide, panel_long):
    pm = price_variants[price_variants.price_measure == price_measure].pivot_table(
        index=["province", "year_quarter"], columns="product", values="log_price_final"
    ).reset_index()
    pm = pm[["province", "year_quarter"] + PRODUCTS]
    pm.columns = ["province", "year_quarter"] + [f"logp__{p}" for p in PRODUCTS]

    phi_wide = sy_selection.pivot_table(index=["province", "year_quarter"], columns="product",
                                          values="selection_Phi").reset_index()
    phi_wide = phi_wide[["province", "year_quarter"] + PRODUCTS]
    phi_wide.columns = ["province", "year_quarter"] + [f"Phi__{p}" for p in PRODUCTS]

    phi_pdf_wide = sy_selection.pivot_table(index=["province", "year_quarter"], columns="product",
                                              values="selection_phi").reset_index()
    phi_pdf_wide = phi_pdf_wide[["province", "year_quarter"] + PRODUCTS]
    phi_pdf_wide.columns = ["province", "year_quarter"] + [f"phi__{p}" for p in PRODUCTS]

    budget_flag = panel_long[["province", "year_quarter", "positive_budget_flag",
                                "total_import_expenditure_usd"]].drop_duplicates()
    pos_pq = budget_flag[budget_flag.positive_budget_flag == 1][
        ["province", "year_quarter", "total_import_expenditure_usd"]
    ]

    df = shares.merge(pm, on=["province", "year_quarter"]).merge(
        phi_wide, on=["province", "year_quarter"]).merge(
        phi_pdf_wide, on=["province", "year_quarter"])
    df = df.merge(pos_pq, on=["province", "year_quarter"])
    df = df.merge(vhat_df[["province", "year_quarter", "v_hat"]], on=["province", "year_quarter"], how="left")
    df = df.merge(panel_wide[["province", "year_quarter"] + CONTROLS], on=["province", "year_quarter"], how="left")
    df["ln_X"] = np.log(df["total_import_expenditure_usd"])
    return df


def build_sys(df, products=PRODUCTS, omitted=OMITTED, controls=CONTROLS, include_cf=True, corrected=True):
    ordered = [p for p in products if p != omitted] + [omitted]
    logp = df[[f"logp__{p}" for p in ordered]].values
    w = df[ordered].values
    lnX = df["ln_X"].values
    Phi = df[[f"Phi__{p}" for p in ordered]].values
    phi = df[[f"phi__{p}" for p in ordered]].values
    vhat = df["v_hat"].values
    Z = df[list(controls)].values.astype(float)
    Zmean = Z.mean(axis=0)
    Zstd = Z.std(axis=0)
    Zstd[Zstd == 0] = 1
    Zs = (Z - Zmean) / Zstd
    return fq.AQSystem(logp, w, lnX, Zs, Phi, phi, vhat, ordered, omitted,
                        include_cf=include_cf, corrected=corrected)


def compute_elasticities(fit, sys, quaids, eps=1e-4):
    par = fit["par"]
    ordered = sys.eq_products + [sys.omitted]
    N = sys.N
    logp_mean = sys.logp.mean(axis=0, keepdims=True)
    lnX_mean = np.array([sys.lnX.mean()])
    Z_mean = sys.Z.mean(axis=0, keepdims=True) if sys.K > 0 else np.zeros((1, 0))
    vhat_mean = np.array([sys.vhat.mean()])

    g0 = fq.predict_systematic(par, sys, quaids, logp=logp_mean, lnX=lnX_mean, Z=Z_mean, vhat=vhat_mean)[0]
    w_mean = g0

    lnX_p = lnX_mean + eps
    lnX_m = lnX_mean - eps
    gp = fq.predict_systematic(par, sys, quaids, logp=logp_mean, lnX=lnX_p, Z=Z_mean, vhat=vhat_mean)[0]
    gm = fq.predict_systematic(par, sys, quaids, logp=logp_mean, lnX=lnX_m, Z=Z_mean, vhat=vhat_mean)[0]
    dw_dlnX = (gp - gm) / (2 * eps)
    eta = 1 + dw_dlnX / w_mean

    dw_dlnp = np.zeros((N, N))
    for j in range(N):
        logp_p = logp_mean.copy(); logp_p[0, j] += eps
        logp_m = logp_mean.copy(); logp_m[0, j] -= eps
        gp = fq.predict_systematic(par, sys, quaids, logp=logp_p, lnX=lnX_mean, Z=Z_mean, vhat=vhat_mean)[0]
        gm = fq.predict_systematic(par, sys, quaids, logp=logp_m, lnX=lnX_mean, Z=Z_mean, vhat=vhat_mean)[0]
        dw_dlnp[:, j] = (gp - gm) / (2 * eps)

    marsh = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            marsh[i, j] = -(1 if i == j else 0) + dw_dlnp[i, j] / w_mean[i]
    hicks = marsh + np.outer(eta, w_mean)
    return dict(products=ordered, w_mean=w_mean, eta=eta, marshallian=marsh, hicksian=hicks)



def compute_elasticities_observed(fit, sys, quaids, eps=1e-4):
    """
    'Observed/censored' elasticity variant (review Issue 3, remedy b):
    dw_i/dz = Phi_i * dg_i/dz, i.e. the observed-budget-share derivative,
    treating the participation probability Phi-hat as locally constant.
    This differs from the paper's headline "conditional (intensive-margin)"
    elasticities -- derivatives of the LATENT systematic share g, not
    multiplied by Phi-hat -- by a factor of Phi-hat, since the actual
    observed share is w_i = Phi_i * g_i + phi_i * psi_i. Reported as a
    contrast/robustness table, not the headline specification.
    """
    par = fit["par"]
    ordered = sys.eq_products + [sys.omitted]
    N = sys.N
    logp_mean = sys.logp.mean(axis=0, keepdims=True)
    lnX_mean = np.array([sys.lnX.mean()])
    Z_mean = sys.Z.mean(axis=0, keepdims=True) if sys.K > 0 else np.zeros((1, 0))
    vhat_mean = np.array([sys.vhat.mean()])
    Phi_mean_ordered = sys.Phi.mean(axis=0)

    g0 = fq.predict_systematic(par, sys, quaids, logp=logp_mean, lnX=lnX_mean, Z=Z_mean, vhat=vhat_mean)[0]
    w_obs_mean = Phi_mean_ordered * g0

    lnX_p = lnX_mean + eps; lnX_m = lnX_mean - eps
    gp = fq.predict_systematic(par, sys, quaids, logp=logp_mean, lnX=lnX_p, Z=Z_mean, vhat=vhat_mean)[0]
    gm = fq.predict_systematic(par, sys, quaids, logp=logp_mean, lnX=lnX_m, Z=Z_mean, vhat=vhat_mean)[0]
    dw_dlnX_obs = Phi_mean_ordered * (gp - gm) / (2 * eps)
    eta_obs = 1 + dw_dlnX_obs / w_obs_mean

    dw_dlnp_obs = np.zeros((N, N))
    for j in range(N):
        logp_p = logp_mean.copy(); logp_p[0, j] += eps
        logp_m = logp_mean.copy(); logp_m[0, j] -= eps
        gp = fq.predict_systematic(par, sys, quaids, logp=logp_p, lnX=lnX_mean, Z=Z_mean, vhat=vhat_mean)[0]
        gm = fq.predict_systematic(par, sys, quaids, logp=logp_m, lnX=lnX_mean, Z=Z_mean, vhat=vhat_mean)[0]
        dw_dlnp_obs[:, j] = Phi_mean_ordered * (gp - gm) / (2 * eps)

    marsh_obs = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            marsh_obs[i, j] = -(1 if i == j else 0) + dw_dlnp_obs[i, j] / w_obs_mean[i]
    hicks_obs = marsh_obs + np.outer(eta_obs, w_obs_mean)
    return dict(products=ordered, w_mean=w_obs_mean, eta=eta_obs, marshallian=marsh_obs, hicksian=hicks_obs)


def morishima_matrix(marsh, eta, w_mean):
    N = len(w_mean)
    M = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            if i == j:
                M[i, j] = np.nan
            else:
                M[i, j] = marsh[i, j] / w_mean[j] - marsh[j, j] / w_mean[j]
    return M


def mechanical_benchmark(fit, sys, quaids, eps=1e-4):
    par_mech = fit["par"].copy()
    m = sys.m
    n_gamma = fq.n_gamma_free(m)
    par_mech[m: m + n_gamma] = 0.0
    fit_mech = dict(fit)
    fit_mech["par"] = par_mech
    return compute_elasticities(fit_mech, sys, quaids, eps=eps)


def slutsky_matrix(hicks, w_mean):
    N = len(w_mean)
    S = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            S[i, j] = hicks[i, j] * w_mean[i]
    return S


def slutsky_max_eigenvalue(par, sys, quaids):
    fit_tmp = dict(par=par, params=fq.unpack(par, sys, quaids))
    el = compute_elasticities(fit_tmp, sys, quaids, eps=1e-4)
    S = slutsky_matrix(el["hicksian"], el["w_mean"])
    S_sym = (S + S.T) / 2
    return np.linalg.eigvalsh(S_sym).max()


def fit_curvature_constrained(sys, quaids, start, maxiter=300):
    con = NonlinearConstraint(lambda p: slutsky_max_eigenvalue(p, sys, quaids), -np.inf, 1e-8)
    res = minimize(fq.fiml_objective, start, args=(sys, quaids), method="SLSQP",
                    constraints=[con], options={"maxiter": maxiter, "ftol": 1e-8})
    return res


def joint_wald_gamma_zero(fit, sys, cov):
    m = sys.m
    n_gamma = fq.n_gamma_free(m)
    gamma_free_est = fit["par"][m: m + n_gamma]
    cov_sub = cov[m: m + n_gamma, m: m + n_gamma]
    try:
        cov_sub_inv = np.linalg.inv(cov_sub)
    except np.linalg.LinAlgError:
        cov_sub_inv = np.linalg.pinv(cov_sub)
    wald_stat = float(gamma_free_est @ cov_sub_inv @ gamma_free_est)
    df = n_gamma
    p_value = 1 - chi2_dist.cdf(wald_stat, df)
    return dict(wald_stat=wald_stat, df=df, p_value=p_value,
                gamma_free_est=gamma_free_est, gamma_free_se=np.sqrt(np.diag(cov_sub)))


def run_for_measure(price_measure, shares, price_variants, sy_selection, vhat_df, panel_wide, panel_long):
    df = assemble_estimation_data(price_measure, shares, price_variants, sy_selection, vhat_df, panel_wide, panel_long)
    sys_obj = build_sys(df)
    m = sys_obj.m
    n_ag = m + fq.n_gamma_free(m) + m

    fit_aids = fq.fit_aids_quaids(sys_obj, quaids=False, maxiter=3000)
    start_q = fq.pack_initial(sys_obj, quaids=True)
    start_q[:n_ag] = fit_aids["par"][:n_ag]
    fit_quaids = fq.fit_aids_quaids(sys_obj, quaids=True, start=start_q, maxiter=3000)
    bewley = fq.bewley_lr_test(fit_aids, fit_quaids)

    preferred_family = bewley["selected"]
    preferred_fit = fit_quaids if preferred_family == "QUAIDS" else fit_aids
    preferred_quaids = preferred_family == "QUAIDS"

    cov, hess_diag = fq.param_covariance(preferred_fit, sys_obj, preferred_quaids, eps=1e-4)
    wald = joint_wald_gamma_zero(preferred_fit, sys_obj, cov)

    se_result = fq.elasticity_delta_se(preferred_fit, sys_obj, preferred_quaids, cov, compute_elasticities)

    res_curv = fit_curvature_constrained(sys_obj, preferred_quaids, preferred_fit["par"])
    fit_curv = dict(preferred_fit)
    fit_curv["par"] = res_curv.x
    fit_curv["params"] = fq.unpack(res_curv.x, sys_obj, preferred_quaids)
    fit_curv["objective"] = res_curv.fun
    max_eig_curv = slutsky_max_eigenvalue(res_curv.x, sys_obj, preferred_quaids)
    max_eig_uncon = slutsky_max_eigenvalue(preferred_fit["par"], sys_obj, preferred_quaids)

    elas_uncon = compute_elasticities(preferred_fit, sys_obj, preferred_quaids)
    elas_curv = compute_elasticities(fit_curv, sys_obj, preferred_quaids)
    elas_mech = mechanical_benchmark(preferred_fit, sys_obj, preferred_quaids)

    morishima_uncon = morishima_matrix(elas_uncon["marshallian"], elas_uncon["eta"], elas_uncon["w_mean"])
    elas_observed = compute_elasticities_observed(preferred_fit, sys_obj, preferred_quaids)

    return dict(
        price_measure=price_measure, sys=sys_obj, fit_aids=fit_aids, fit_quaids=fit_quaids,
        bewley=bewley, preferred_family=preferred_family, cov=cov, hess_diag=hess_diag, wald=wald,
        fit_curv=fit_curv, max_eig_curv=max_eig_curv, max_eig_uncon=max_eig_uncon,
        elas_uncon=elas_uncon, elas_curv=elas_curv, elas_mech=elas_mech, morishima_uncon=morishima_uncon,
        se_result=se_result, elas_observed=elas_observed,
    )


if __name__ == "__main__":
    panel_long, price_variants, sy_selection, vhat_df, panel_wide = load_inputs()
    shares = build_shares(panel_long)

    all_results = {}
    bewley_rows = []
    wald_rows = []
    param_rows = []
    elas_rows = []
    mech_decomp_rows = []

    for pm_name in PRICE_MEASURES:
        print(f"=== Fitting price measure: {pm_name} ===")
        res = run_for_measure(pm_name, shares, price_variants, sy_selection, vhat_df, panel_wide, panel_long)
        all_results[pm_name] = res

        b = dict(res["bewley"]); b["price_measure"] = pm_name
        bewley_rows.append(b)

        w = res["wald"]
        wald_rows.append(dict(
            price_measure=pm_name, preferred_family=res["preferred_family"],
            wald_stat=w["wald_stat"], df=w["df"], p_value=w["p_value"],
            hessian_condition_number=res["hess_diag"]["hessian_condition_number"],
            n_truncated_singular_values=res["hess_diag"]["n_truncated_singular_values"],
            max_eig_slutsky_unconstrained=res["max_eig_uncon"],
            max_eig_slutsky_curvature_constrained=res["max_eig_curv"],
            objective_unconstrained=res["fit_quaids"]["objective"] if res["preferred_family"] == "QUAIDS"
                else res["fit_aids"]["objective"],
            objective_curvature_constrained=res["fit_curv"]["objective"],
        ))

        sys_obj = res["sys"]
        prods_ord = sys_obj.eq_products + [sys_obj.omitted]
        prm = res["fit_quaids"]["params"] if res["preferred_family"] == "QUAIDS" else res["fit_aids"]["params"]
        gamma_df = pd.DataFrame(prm["gamma"], index=prods_ord, columns=prods_ord)
        for i_prod in prods_ord:
            for j_prod in prods_ord:
                param_rows.append(dict(price_measure=pm_name, term="gamma", product_i=i_prod, product_j=j_prod,
                                        coef=gamma_df.loc[i_prod, j_prod]))
        for k, prod in enumerate(prods_ord):
            param_rows.append(dict(price_measure=pm_name, term="alpha", product_i=prod, product_j=None,
                                    coef=prm["alpha"][k]))
            param_rows.append(dict(price_measure=pm_name, term="beta", product_i=prod, product_j=None,
                                    coef=prm["beta"][k]))
            if res["preferred_family"] == "QUAIDS":
                param_rows.append(dict(price_measure=pm_name, term="lambda", product_i=prod, product_j=None,
                                        coef=prm["lam"][k]))

        for label, el in [("unconstrained", res["elas_uncon"]), ("curvature_constrained", res["elas_curv"]),
                           ("mechanical_benchmark", res["elas_mech"])]:
            for i_idx, i_prod in enumerate(prods_ord):
                elas_rows.append(dict(price_measure=pm_name, spec=label, product=i_prod, elasticity_type="expenditure",
                                       price_product=None, value=el["eta"][i_idx]))
                for j_idx, j_prod in enumerate(prods_ord):
                    elas_rows.append(dict(price_measure=pm_name, spec=label, product=i_prod,
                                           elasticity_type="marshallian", price_product=j_prod,
                                           value=el["marshallian"][i_idx, j_idx]))
                    elas_rows.append(dict(price_measure=pm_name, spec=label, product=i_prod,
                                           elasticity_type="hicksian", price_product=j_prod,
                                           value=el["hicksian"][i_idx, j_idx]))

        obs_el = res["elas_observed"]
        for i_idx, i_prod in enumerate(prods_ord):
            elas_rows.append(dict(price_measure=pm_name, spec="observed_censored_PhiScaled", product=i_prod,
                                   elasticity_type="expenditure", price_product=None, value=obs_el["eta"][i_idx]))
            elas_rows.append(dict(price_measure=pm_name, spec="observed_censored_PhiScaled", product=i_prod,
                                   elasticity_type="marshallian_own", price_product=i_prod,
                                   value=obs_el["marshallian"][i_idx, i_idx]))
            elas_rows.append(dict(price_measure=pm_name, spec="observed_censored_PhiScaled", product=i_prod,
                                   elasticity_type="hicksian_own", price_product=i_prod,
                                   value=obs_el["hicksian"][i_idx, i_idx]))

        se_res = res["se_result"]
        for i_idx, i_prod in enumerate(prods_ord):
            elas_rows.append(dict(price_measure=pm_name, spec="unconstrained_with_SE", product=i_prod,
                                   elasticity_type="expenditure", price_product=None,
                                   value=se_res["eta"][i_idx], se=se_res["eta_se"][i_idx]))
            elas_rows.append(dict(price_measure=pm_name, spec="unconstrained_with_SE", product=i_prod,
                                   elasticity_type="marshallian_own", price_product=i_prod,
                                   value=se_res["marsh_own"][i_idx], se=se_res["marsh_own_se"][i_idx]))
            elas_rows.append(dict(price_measure=pm_name, spec="unconstrained_with_SE", product=i_prod,
                                   elasticity_type="hicksian_own", price_product=i_prod,
                                   value=se_res["hicks_own"][i_idx], se=se_res["hicks_own_se"][i_idx]))

        full_hicks = res["elas_uncon"]["hicksian"]
        mech_hicks = res["elas_mech"]["hicksian"]
        diff = full_hicks - mech_hicks
        for i_idx, i_prod in enumerate(prods_ord):
            for j_idx, j_prod in enumerate(prods_ord):
                mech_decomp_rows.append(dict(
                    price_measure=pm_name, product_i=i_prod, product_j=j_prod,
                    hicksian_full=full_hicks[i_idx, j_idx], hicksian_mechanical=mech_hicks[i_idx, j_idx],
                    gamma_contribution=diff[i_idx, j_idx],
                ))

        print(f"  Bewley: LRB={res['bewley']['LRB']:.2f}, p={res['bewley']['p_value_LRB']:.2e}, "
              f"selected={res['bewley']['selected']}")
        print(f"  Joint Wald H0:Gamma=0 -> stat={w['wald_stat']:.2f}, df={w['df']}, p={w['p_value']:.2e}")
        print(f"  Max Slutsky eigenvalue: unconstrained={res['max_eig_uncon']:.2e}, "
              f"curvature-constrained={res['max_eig_curv']:.2e}")

    pd.DataFrame(bewley_rows).to_csv(f"{OUT_DIR}/bewley_model_selection.csv", index=False)
    pd.DataFrame(wald_rows).to_csv(f"{OUT_DIR}/gamma_joint_wald_test.csv", index=False)
    pd.DataFrame(param_rows).to_csv(f"{OUT_DIR}/fiml_structural_parameters.csv", index=False)
    pd.DataFrame(elas_rows).to_csv(f"{OUT_DIR}/fiml_elasticities_full.csv", index=False)
    pd.DataFrame(mech_decomp_rows).to_csv(f"{OUT_DIR}/mechanical_benchmark_decomposition.csv", index=False)

    print("\\nAll outputs saved to", OUT_DIR)
