*! Elasticities at sample-average covariates after fooddem 1.0.0  14jul2026
program define fooddem_reference, rclass
    version 17
    syntax using/, [SAMPLE(varname numeric) REPLACE]

    if "`e(fooddem_model)'" != "easi" {
        di as error "fooddem_reference currently requires an EASI estimate"
        exit 301
    }
    if "`e(fooddem_precommitment)'" != "" {
        di as error "fooddem_reference is not available after precommitment"
        exit 198
    }

    local k = e(fooddem_goods)
    local order = e(fooddem_order)
    local demos "`e(fooddem_demographics)'"
    local cf "`e(fooddem_cf)'"
    local nd : word count `demos'
    local refif "e(sample)"
    if "`sample'" != "" local refif "`sample' != 0 & !missing(`sample')"
    tempname dbar cfbar estimates ses pvals cilow cihigh shares slutsky
    matrix `dbar' = J(1, `nd', 0)
    if `nd' > 0 {
        forvalues d = 1/`nd' {
            local zd : word `d' of `demos'
            quietly summarize `zd' if `refif', meanonly
            matrix `dbar'[1, `d'] = r(mean)
        }
    }
    matrix `cfbar' = J(1, 1, 0)
    if "`cf'" != "" {
        quietly summarize `cf' if `refif', meanonly
        matrix `cfbar'[1, 1] = r(mean)
    }

    mata: _fooddem_reference_stats("e(b)", "e(V)", `k', `order', ///
        "`dbar'", "`cfbar'", ("`cf'" != ""), "`estimates'", "`ses'", ///
        "`pvals'", "`cilow'", "`cihigh'", "`shares'", "`slutsky'")

    tempname mem
    tempfile result
    postfile `mem' str18 evaluation str14 elasticity_type int demand_good ///
        shock_good double reference_share elasticity std_error z_value ///
        p_value ci_low ci_high using `result', replace
    local pos = 0
    forvalues i = 1/`k' {
        local ++pos
        post `mem' ("sample_average") ("expenditure") (`i') (0) ///
            (`shares'[1,`i']) (`estimates'[1,`pos']) (`ses'[1,`pos']) ///
            (`estimates'[1,`pos']/`ses'[1,`pos']) (`pvals'[1,`pos']) ///
            (`cilow'[1,`pos']) (`cihigh'[1,`pos'])
    }
    foreach type in marshallian hicksian {
        forvalues i = 1/`k' {
            forvalues j = 1/`k' {
                local ++pos
                post `mem' ("sample_average") ("`type'") (`i') (`j') ///
                    (`shares'[1,`i']) (`estimates'[1,`pos']) (`ses'[1,`pos']) ///
                    (`estimates'[1,`pos']/`ses'[1,`pos']) (`pvals'[1,`pos']) ///
                    (`cilow'[1,`pos']) (`cihigh'[1,`pos'])
            }
        }
    }
    postclose `mem'
    preserve
        use `result', clear
        if regexm(lower("`using'"), "[.]dta$") {
            if "`replace'" != "" save "`using'", replace
            else save "`using'"
        }
        else {
            if "`replace'" != "" export delimited using "`using'", replace
            else export delimited using "`using'"
        }
    restore

    mata: st_numscalar("__fd_ref_maxeig", max(symeigenvalues(st_matrix("`slutsky'"))))
    return scalar slutsky_max_eigenvalue = scalar(__fd_ref_maxeig)
    return matrix reference_shares = `shares'
    return matrix slutsky = `slutsky'
end

capture mata: mata drop _fooddem_reference_vector()
capture mata: mata drop _fooddem_reference_stats()
mata:
mata set matastrict on

real colvector _fooddem_reference_vector(
    real colvector beta,
    real scalar k,
    real scalar hmax,
    real rowvector dbar,
    real scalar cfbar,
    real scalar hascf,
    real colvector wref,
    real matrix S)
{
    real scalar neq, nd, pos, i, j, h, d
    real colvector avec, b1, rvec, eta, out
    real matrix G, T

    neq = k - 1
    nd = cols(dbar)
    pos = 0
    avec = J(neq, 1, 0)
    for (i = 1; i <= neq; i++) avec[i] = beta[++pos]
    b1 = J(k, 1, 0)
    for (i = 1; i <= neq; i++) {
        for (h = 1; h <= hmax; h++) {
            pos++
            if (h == 1) b1[i] = beta[pos]
        }
    }
    b1[k] = -sum(b1[1..neq])
    G = J(k, k, 0)
    for (i = 1; i <= neq; i++) {
        for (j = i; j <= neq; j++) {
            G[i, j] = beta[++pos]
            G[j, i] = G[i, j]
        }
    }
    for (i = 1; i <= neq; i++) {
        G[i, k] = -sum(G[i, 1..neq])
        G[k, i] = G[i, k]
    }
    G[k, k] = sum(G[1..neq, 1..neq])
    T = J(neq, nd, 0)
    for (i = 1; i <= neq; i++) {
        for (d = 1; d <= nd; d++) T[i, d] = beta[++pos]
    }
    rvec = J(neq, 1, 0)
    if (hascf) {
        for (i = 1; i <= neq; i++) rvec[i] = beta[++pos]
    }
    wref = avec
    if (nd > 0) wref = wref + T * dbar'
    if (hascf) wref = wref + rvec * cfbar
    wref = wref \ (1 - sum(wref))
    eta = 1 :+ b1 :/ wref
    S = G + wref * wref' - diag(wref)

    out = J(k + 2 * k * k, 1, .)
    pos = 0
    for (i = 1; i <= k; i++) out[++pos] = eta[i]
    for (i = 1; i <= k; i++) {
        for (j = 1; j <= k; j++) {
            out[++pos] = (G[i,j] - b1[i] * wref[j]) / wref[i] - (i == j)
        }
    }
    for (i = 1; i <= k; i++) {
        for (j = 1; j <= k; j++) {
            out[++pos] = G[i,j] / wref[i] - (i == j) + wref[j]
        }
    }
    return(out)
}

void _fooddem_reference_stats(
    string scalar bname,
    string scalar Vname,
    real scalar k,
    real scalar hmax,
    string scalar dbarname,
    string scalar cfbarname,
    real scalar hascf,
    string scalar ename,
    string scalar sename,
    string scalar pname,
    string scalar loname,
    string scalar hiname,
    string scalar wname,
    string scalar Sname)
{
    real scalar p, m, j, delta, cfbar
    real rowvector dbar
    real colvector beta, bp, bm, e, wref, se, pv, lo, hi
    real matrix V, J, VE, S, Stmp

    beta = st_matrix(bname)'
    V = st_matrix(Vname)
    dbar = st_matrix(dbarname)
    cfbar = st_matrix(cfbarname)[1,1]
    e = _fooddem_reference_vector(beta, k, hmax, dbar, cfbar, hascf, wref, S)
    p = rows(beta)
    m = rows(e)
    J = J(m, p, 0)
    for (j = 1; j <= p; j++) {
        delta = 1e-6 * (1 + abs(beta[j]))
        bp = beta
        bm = beta
        bp[j] = bp[j] + delta
        bm[j] = bm[j] - delta
        J[,j] = (_fooddem_reference_vector(bp, k, hmax, dbar, cfbar,
            hascf, wref, Stmp) - _fooddem_reference_vector(bm, k, hmax,
            dbar, cfbar, hascf, wref, Stmp)) / (2 * delta)
    }
    e = _fooddem_reference_vector(beta, k, hmax, dbar, cfbar, hascf, wref, S)
    VE = J * V * J'
    se = sqrt(diagonal(VE))
    pv = 2 :* normal(-abs(e :/ se))
    lo = e :- invnormal(.975) :* se
    hi = e :+ invnormal(.975) :* se
    st_matrix(ename, e')
    st_matrix(sename, se')
    st_matrix(pname, pv')
    st_matrix(loname, lo')
    st_matrix(hiname, hi')
    st_matrix(wname, wref')
    st_matrix(Sname, S)
}
end
