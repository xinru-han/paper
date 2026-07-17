*! Point elasticities at EASI sample-average covariates, without delta method
program define ar_reference_point, rclass
    version 17
    if "`e(fooddem_model)'" != "easi" | "`e(fooddem_precommitment)'" != "" {
        di as error "ar_reference_point requires a non-precommitment EASI estimate"
        exit 301
    }
    local k = e(fooddem_goods)
    local order = e(fooddem_order)
    local demos "`e(fooddem_demographics)'"
    local cf "`e(fooddem_cf)'"
    local nd : word count `demos'
    tempname dbar cfbar estimates shares slutsky
    matrix `dbar' = J(1, `nd', 0)
    if `nd' > 0 {
        forvalues d = 1/`nd' {
            local zd : word `d' of `demos'
            quietly summarize `zd' if e(sample), meanonly
            matrix `dbar'[1, `d'] = r(mean)
        }
    }
    matrix `cfbar' = J(1, 1, 0)
    if "`cf'" != "" {
        quietly summarize `cf' if e(sample), meanonly
        matrix `cfbar'[1, 1] = r(mean)
    }
    mata: _ar_reference_point("e(b)", `k', `order', "`dbar'", "`cfbar'", ///
        ("`cf'" != ""), "`estimates'", "`shares'", "`slutsky'")
    local pos = 0
    forvalues g = 1/`k' {
        local ++pos
        return scalar exp`g' = `estimates'[1, `pos']
    }
    forvalues i = 1/`k' {
        forvalues j = 1/`k' {
            local ++pos
            if `i' == `j' return scalar mar`i' = `estimates'[1, `pos']
        }
    }
    forvalues i = 1/`k' {
        forvalues j = 1/`k' {
            local ++pos
            if `i' == `j' return scalar hic`i' = `estimates'[1, `pos']
        }
    }
    return matrix reference_shares = `shares'
    return matrix slutsky = `slutsky'
end

capture mata: mata drop _ar_reference_point()
mata:
mata set matastrict on
void _ar_reference_point(
    string scalar bname,
    real scalar k,
    real scalar hmax,
    string scalar dbarname,
    string scalar cfbarname,
    real scalar hascf,
    string scalar ename,
    string scalar wname,
    string scalar sname)
{
    real scalar neq, nd, pos, i, j, h, d, cfbar
    real rowvector dbar
    real colvector beta, avec, b1, rvec, eta, out, wref
    real matrix G, T, S

    beta = st_matrix(bname)'
    dbar = st_matrix(dbarname)
    cfbar = st_matrix(cfbarname)[1,1]
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
    st_matrix(ename, out')
    st_matrix(wname, wref')
    st_matrix(sname, S)
}
end
