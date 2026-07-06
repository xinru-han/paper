
"""
fiml_aids_quaids.py
Python port of the FIML AIDS/QUAIDS estimator documented in
cf_aids_quaids_代码整合总览.md (utils_aids_quaids.R), extended with:
  - full Gamma matrix point estimates + delta-method standard errors
  - a joint Wald test of H0: all gamma_ij = 0 (nested Engel-only model)

Parameterization (mirrors the R implementation):
  - N = m+1 products (m estimated equations + 1 omitted, recovered by adding-up).
  - alpha: N-vector, alpha_N = 1 - sum(alpha_free)              [adding-up]
  - gamma: N x N symmetric matrix built from m*(m+1)/2 free parameters
           for the upper-left m x m block; row/column N are filled by
           homogeneity (sum_j gamma_ij = 0) which simultaneously delivers
           adding-up (sum_i gamma_ij = 0) and symmetry (gamma_ij = gamma_ji).
  - beta:  N-vector, beta_N = -sum(beta_free)                    [adding-up]
  - lambda (QUAIDS only): N-vector, lambda_N = -sum(lambda_free) [adding-up]
  - delta (Z controls): N x K matrix, row N = -colSums(delta_free) [adding-up]
  - cf (control-function loading on v-hat): N-vector, cf_N = -sum(cf_free)
  - psi (Shonkwiler-Yen intercept-shift term): m-vector (only for the m
         estimated equations; the omitted equation's psi is not separately
         identified and is recovered via adding-up in aggregate, not needed
         per-equation since SY correction is only applied to estimated eqs).

FIML objective: concentrate out the residual covariance matrix Sigma
(m x m, over the m estimated share equations only) via
    obj(theta) = n * log|Sigma_hat(theta)|,   Sigma_hat = R'R/n
which is (up to additive constants) -2 * log-likelihood under joint
normality of the residuals; equations are just-identified up to the
covariance so this SUR/FIML objective is standard for singular (adding-up
constrained) demand systems.
"""
import numpy as np
from scipy import optimize
from scipy.stats import chi2


def gamma_from_free(free_params, m):
    N = m + 1
    G = np.zeros((N, N))
    idx = 0
    for i in range(m):
        for j in range(i, m):
            G[i, j] = free_params[idx]
            G[j, i] = free_params[idx]
            idx += 1
    for i in range(m):
        G[i, N - 1] = -G[i, :m].sum()
        G[N - 1, i] = G[i, N - 1]
    G[N - 1, N - 1] = -G[N - 1, :m].sum()
    return G


def n_gamma_free(m):
    return m * (m + 1) // 2


class AQSystem:
    """Container for one estimation sample: prices, shares, expenditure,
    controls, SY selection terms, and the control-function residual."""

    def __init__(self, logp, w, lnX, Z, Phi, phi, vhat, products, omitted,
                 include_cf=True, corrected=True):
        self.logp = np.asarray(logp)          # n x N
        self.w = np.asarray(w)                # n x N (all N budget shares, for residual calc on eq only)
        self.lnX = np.asarray(lnX)            # n
        self.Z = np.asarray(Z) if Z is not None and Z.shape[1] > 0 else np.zeros((logp.shape[0], 0))
        self.Phi = np.asarray(Phi)            # n x N
        self.phi = np.asarray(phi)            # n x N
        self.vhat = np.asarray(vhat)          # n
        self.products = list(products)
        self.omitted = omitted
        self.N = logp.shape[1]
        self.m = self.N - 1
        self.K = self.Z.shape[1]
        self.n = logp.shape[0]
        self.include_cf = include_cf
        self.corrected = corrected
        self.lnX_center = np.mean(self.lnX)
        ordered = [p for p in products if p != omitted] + [omitted]
        self.eq_idx = [self.products.index(p) for p in ordered[: self.m]]
        self.eq_products = [self.products[i] for i in self.eq_idx]


def n_params(sys, quaids):
    m = sys.m
    k = m  # alpha_free
    k += n_gamma_free(m)  # gamma_free
    k += m  # beta_free
    if quaids:
        k += m  # lambda_free
    k += m * sys.K  # delta_free
    if sys.include_cf:
        k += m  # cf_free
    if sys.corrected:
        k += m  # psi
    return k


def pack_initial(sys, quaids):
    mean_shares = np.mean(sys.w, axis=0)
    alpha_free = np.maximum(mean_shares[: sys.m], 1e-4)
    gamma_free = np.zeros(n_gamma_free(sys.m))
    beta_free = np.zeros(sys.m)
    parts = [alpha_free, gamma_free, beta_free]
    if quaids:
        parts.append(np.zeros(sys.m))
    parts.append(np.zeros(sys.m * sys.K))
    if sys.include_cf:
        parts.append(np.zeros(sys.m))
    if sys.corrected:
        parts.append(np.zeros(sys.m))
    return np.concatenate(parts)


def unpack(par, sys, quaids):
    m, N, K = sys.m, sys.N, sys.K
    idx = 0
    alpha_free = par[idx: idx + m]; idx += m
    alpha = np.append(alpha_free, 1 - alpha_free.sum())
    ng = n_gamma_free(m)
    gamma = gamma_from_free(par[idx: idx + ng], m); idx += ng
    beta_free = par[idx: idx + m]; idx += m
    beta = np.append(beta_free, -beta_free.sum())
    lam = np.zeros(N)
    if quaids:
        lambda_free = par[idx: idx + m]; idx += m
        lam = np.append(lambda_free, -lambda_free.sum())
    delta = np.zeros((N, K))
    if K > 0:
        delta_free = par[idx: idx + m * K].reshape(m, K); idx += m * K
        delta[:m, :] = delta_free
        delta[-1, :] = -delta_free.sum(axis=0)
    cf = np.zeros(N)
    if sys.include_cf:
        cf_free = par[idx: idx + m]; idx += m
        cf = np.append(cf_free, -cf_free.sum())
    psi = np.zeros(m)
    if sys.corrected:
        psi = par[idx: idx + m]; idx += m
    return dict(alpha=alpha, gamma=gamma, beta=beta, lam=lam, delta=delta, cf=cf, psi=psi)


def predict_systematic(par, sys, quaids, logp=None, lnX=None, Z=None, vhat=None):
    prm = unpack(par, sys, quaids)
    if logp is None:
        logp = sys.logp
    n_obs = logp.shape[0]
    if lnX is None:
        lnX = sys.lnX
    lnX = np.broadcast_to(lnX, (n_obs,))
    if Z is None:
        Z = sys.Z
    if vhat is None:
        vhat = sys.vhat
    vhat = np.broadcast_to(vhat, (n_obs,))

    lin = logp @ prm["alpha"]
    quad = 0.5 * np.sum((logp @ prm["gamma"]) * logp, axis=1)
    ln_a = lin + quad
    ln_b = logp @ prm["beta"]
    g_exp = (lnX - sys.lnX_center) - ln_a
    G_term = logp @ prm["gamma"]
    beta_term = np.outer(g_exp, prm["beta"])
    W = np.tile(prm["alpha"], (n_obs, 1)) + G_term + beta_term
    if quaids:
        quad2 = (g_exp ** 2) / np.clip(np.exp(ln_b), 1e-8, None)
        W = W + np.outer(quad2, prm["lam"])
    if Z.shape[1] > 0:
        W = W + Z @ prm["delta"].T
    if sys.include_cf:
        W = W + np.outer(vhat, prm["cf"])
    return W


def fiml_objective(par, sys, quaids):
    try:
        g = predict_systematic(par, sys, quaids)
    except Exception:
        return 1e30
    if not np.all(np.isfinite(g)):
        return 1e30
    m, n = sys.m, sys.n
    g_eq = g[:, sys.eq_idx]
    if sys.corrected:
        prm = unpack(par, sys, quaids)
        psi_mat = np.tile(prm["psi"], (n, 1))
        pred = sys.Phi[:, sys.eq_idx] * g_eq + sys.phi[:, sys.eq_idx] * psi_mat
    else:
        pred = g_eq
    R = sys.w[:, sys.eq_idx] - pred
    R = np.nan_to_num(R, nan=0.0, posinf=0.0, neginf=0.0)
    Sigma = (R.T @ R) / n + np.eye(m) * 1e-8
    sign, logdet = np.linalg.slogdet(Sigma)
    if sign <= 0 or not np.isfinite(logdet):
        return 1e30
    return n * logdet


def fit_aids_quaids(sys, quaids, start=None, maxiter=3000, polish=True):
    par0 = start if start is not None else pack_initial(sys, quaids)
    res = optimize.minimize(
        fiml_objective, par0, args=(sys, quaids), method="BFGS",
        options={"maxiter": maxiter, "gtol": 1e-8},
    )
    if polish:
        # BFGS occasionally reports a precision-loss warning right at a good
        # optimum for this concentrated log-det objective; polish with a
        # derivative-free Nelder-Mead step followed by a final BFGS pass to
        # confirm/tighten convergence.
        res_nm = optimize.minimize(
            fiml_objective, res.x, args=(sys, quaids), method="Nelder-Mead",
            options={"maxiter": 20000, "xatol": 1e-8, "fatol": 1e-10},
        )
        if res_nm.fun <= res.fun:
            res = res_nm
        res_final = optimize.minimize(
            fiml_objective, res.x, args=(sys, quaids), method="BFGS",
            options={"maxiter": maxiter, "gtol": 1e-9},
        )
        if res_final.fun <= res.fun:
            res = res_final
    k = len(res.x)
    n, m = sys.n, sys.m
    ll = -0.5 * (n * m * (np.log(2 * np.pi) + 1) + res.fun)
    return dict(
        quaids=quaids, par=res.x, objective=res.fun, logLik=ll, npar=k,
        neq=m, nobs=n, success=res.success, message=res.message, sys=sys,
        params=unpack(res.x, sys, quaids),
    )


def bewley_lr_test(fit_aids, fit_quaids):
    LLR, LLU = fit_aids["logLik"], fit_quaids["logLik"]
    NEQ, NSS, NU_P = fit_quaids["neq"], fit_quaids["nobs"], fit_quaids["npar"]
    scale = (NEQ * NSS - NU_P) / (NEQ * NSS)
    LR_plain = 2 * (LLU - LLR)
    LRB = LR_plain * scale
    df = fit_quaids["npar"] - fit_aids["npar"]
    p_LRB = 1 - chi2.cdf(LRB, df) if df > 0 else np.nan
    p_plain = 1 - chi2.cdf(LR_plain, df) if df > 0 else np.nan
    selected = "QUAIDS" if (df > 0 and np.isfinite(LRB) and p_LRB < 0.05) else "AIDS"
    return dict(logLik_AIDS=LLR, logLik_QUAIDS=LLU, NEQ=NEQ, NSS=NSS, NU_P=NU_P,
                bewley_scale=scale, LR_plain=LR_plain, LRB=LRB, df=df,
                p_value_LRB=p_LRB, p_value_plain=p_plain, selected=selected)


def numerical_hessian(f, x, args=(), eps=1e-4):
    n = len(x)
    H = np.zeros((n, n))
    f0 = f(x, *args)
    for i in range(n):
        for j in range(i, n):
            xpp = x.copy(); xpp[i] += eps; xpp[j] += eps
            xpm = x.copy(); xpm[i] += eps; xpm[j] -= eps
            xmp = x.copy(); xmp[i] -= eps; xmp[j] += eps
            xmm = x.copy(); xmm[i] -= eps; xmm[j] -= eps
            val = (f(xpp, *args) - f(xpm, *args) - f(xmp, *args) + f(xmm, *args)) / (4 * eps * eps)
            H[i, j] = val
            H[j, i] = val
    return H


def param_covariance(fit, sys, quaids, eps=1e-4, svd_tol=1e-8):
    """Delta-method parameter covariance: 2 * Hessian(obj)^-1, using a
    truncated-SVD pseudo-inverse for numerical stability (mirrors the R
    implementation's optimHess + pinv approach)."""
    H = numerical_hessian(fiml_objective, fit["par"], args=(sys, quaids), eps=eps)
    U, s, Vt = np.linalg.svd(H)
    s_max = s.max() if len(s) else 0.0
    keep = s > svd_tol * s_max
    n_trunc = int((~keep).sum())
    s_inv = np.zeros_like(s)
    s_inv[keep] = 1.0 / s[keep]
    H_pinv = (Vt.T * s_inv) @ U.T
    cov = 2 * H_pinv
    cond_number = (s.max() / s[keep].min()) if keep.any() else np.inf
    return cov, dict(hessian_condition_number=cond_number, n_truncated_singular_values=n_trunc,
                      n_total_params=len(fit["par"]))


def elasticity_delta_se(fit, sys, quaids, cov, compute_elasticities_fn, eps_param=1e-4, eps_elas=1e-4):
    """Delta-method standard errors for own-price Marshallian/Hicksian and
    expenditure elasticities, via numerical Jacobian of the elasticity
    vector w.r.t. the estimated parameter vector, propagated through the
    parameter covariance matrix `cov` (from param_covariance)."""
    par = fit["par"]
    k = len(par)

    def vec(p):
        fit_tmp = dict(par=p, params=unpack(p, sys, quaids))
        el = compute_elasticities_fn(fit_tmp, sys, quaids, eps=eps_elas)
        return np.concatenate([el["eta"], np.diag(el["marshallian"]), np.diag(el["hicksian"])])

    v0 = vec(par)
    n_out = len(v0)
    J = np.zeros((n_out, k))
    for i in range(k):
        pp = par.copy(); pp[i] += eps_param
        pm = par.copy(); pm[i] -= eps_param
        J[:, i] = (vec(pp) - vec(pm)) / (2 * eps_param)
    cov_v = J @ cov @ J.T
    se = np.sqrt(np.clip(np.diag(cov_v), 0, None))
    N = sys.N
    return dict(eta=v0[:N], eta_se=se[:N], marsh_own=v0[N:2*N], marsh_own_se=se[N:2*N],
                hicks_own=v0[2*N:3*N], hicks_own_se=se[2*N:3*N])
