# -*- coding: utf-8 -*-
"""多效应量Meta分析统计核心。

方法依据：
  - Hedges, Tipton & Johnson (2010, RSM)：相关效应(correlated effects)
    稳健方差估计(RVE)，robumeta同款权重 w_ij = 1/(k_j*(v_bar_j+tau2))；
  - Tipton (2015)：小样本校正的自由度（此处用保守的 m-1 与 Satterthwaite 近似）；
  - IFPRI DP02361：两层随机截距 + 1/sqrt(N) 精度项；
  - Tan et al. (2026, JAE)：逆方差加权 + Egger / Begg 检验。
"""
import numpy as np
import pandas as pd
from scipy import stats


def _study_blocks(study):
    study = np.asarray(study)
    return [np.where(study == s)[0] for s in pd.unique(study)]


def tau2_ht(y, v, study, rho=0.8):
    """Hedges-Tipton 矩估计 tau^2（相关效应工作模型）。"""
    y, v = np.asarray(y, float), np.asarray(v, float)
    blocks = _study_blocks(study)
    m = len(blocks)
    # study-level means & preliminary weights 1/(k_j*vbar_j)
    w = np.zeros(len(y))
    for b in blocks:
        w[b] = 1.0 / (len(b) * v[b].mean())
    mu = np.sum(w * y) / np.sum(w)
    Q = np.sum(w * (y - mu) ** 2)
    # trace terms (HTJ 2010 eq. 7, simplified for balanced correlation rho)
    W = np.sum(w)
    sum_w2 = 0.0
    trace_term = 0.0
    for b in blocks:
        wj = w[b].sum()
        vj = v[b].mean()
        kj = len(b)
        sum_w2 += wj**2
        trace_term += wj * vj * (1 + (kj - 1) * rho)
    denom = W - sum_w2 / W
    num = Q - (trace_term - sum_w2 / W * np.mean([v[b].mean() for b in blocks]))
    tau2 = max(num / denom, 0.0) if denom > 0 else 0.0
    return tau2, Q, m


def rve_pool(y, v, study, rho=0.8):
    """相关效应RVE合并：返回 dict(mu, se, ci, pval, df, tau2, I2, k, m, pi)。"""
    y, v = np.asarray(y, float), np.asarray(v, float)
    tau2, Q, m = tau2_ht(y, v, study, rho)
    blocks = _study_blocks(study)
    w = np.zeros(len(y))
    for b in blocks:
        w[b] = 1.0 / (len(b) * (v[b].mean() + tau2))
    W = np.sum(w)
    mu = np.sum(w * y) / W
    # 稳健方差（study层面聚类）
    vr = sum((np.sum(w[b] * (y[b] - mu))) ** 2 for b in blocks) / W**2
    se = np.sqrt(vr)
    dfree = m - 1
    tcrit = stats.t.ppf(0.975, dfree)
    pval = 2 * stats.t.sf(abs(mu / se), dfree) if se > 0 else np.nan
    k = len(y)
    I2 = np.nan
    if k > 1:
        wf = 1.0 / v
        muf = np.sum(wf * y) / np.sum(wf)
        Qf = np.sum(wf * (y - muf) ** 2)
        I2 = max(0.0, (Qf - (k - 1)) / Qf) * 100 if Qf > 0 else 0.0
    if m > 2:
        pi_se = np.sqrt(tau2 + vr)
        tpi = stats.t.ppf(0.975, m - 2)
        pi = (mu - tpi * pi_se, mu + tpi * pi_se)
    else:
        pi = (np.nan, np.nan)
    return dict(mu=mu, se=se, ci=(mu - tcrit * se, mu + tcrit * se),
                pval=pval, df=dfree, tau2=tau2, I2=I2, k=k, m=m, pi=pi)


def rve_wls(y, X, v, study, rho=0.8):
    """RVE加权最小二乘Meta回归（相关效应权重+聚类稳健SE）。

    X: DataFrame（含const）。返回 DataFrame(coef, se, t, p, df)。"""
    y = np.asarray(y, float)
    Xm = np.asarray(X, float)
    v = np.asarray(v, float)
    tau2, _, m = tau2_ht(y, v, study, rho)
    blocks = _study_blocks(study)
    w = np.zeros(len(y))
    for b in blocks:
        w[b] = 1.0 / (len(b) * (v[b].mean() + tau2))
    Wsq = np.sqrt(w)
    Xw = Xm * Wsq[:, None]
    yw = y * Wsq
    XtX = Xw.T @ Xw
    XtX_inv = np.linalg.pinv(XtX)
    beta = XtX_inv @ (Xw.T @ yw)
    resid = y - Xm @ beta
    # cluster-robust meat
    meat = np.zeros((Xm.shape[1], Xm.shape[1]))
    for b in blocks:
        g = (Xm[b] * (w[b] * resid[b])[:, None]).sum(axis=0)
        meat += np.outer(g, g)
    V = XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.diag(V))
    dfree = m - Xm.shape[1]
    dfree = max(dfree, 2)
    tvals = beta / se
    pvals = 2 * stats.t.sf(np.abs(tvals), dfree)
    return pd.DataFrame(dict(coef=beta, se=se, t=tvals, p=pvals),
                        index=X.columns), tau2, m


def egger_begg(y, se_, study=None):
    """Egger回归检验 + Begg秩相关检验（发表偏倚）。"""
    y, se_ = np.asarray(y, float), np.asarray(se_, float)
    z = y / se_
    prec = 1.0 / se_
    sl, ic, r, p_eg, _ = stats.linregress(prec, z)
    # Begg: Kendall tau between standardized effects and variances
    wf = 1.0 / se_**2
    mu = np.sum(wf * y) / np.sum(wf)
    vstar = se_**2 - 1.0 / np.sum(wf)
    vstar[vstar <= 0] = se_[vstar <= 0] ** 2
    ystar = (y - mu) / np.sqrt(vstar)
    tau_k, p_bg = stats.kendalltau(ystar, se_**2)
    return dict(egger_intercept=ic, egger_p=p_eg, begg_tau=tau_k, begg_p=p_bg)


def star(p):
    if not np.isfinite(p):
        return ""
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
