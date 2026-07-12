*! Exact constrained EASI/GEASI nonlinear GMM solver 1.0.0  12jul2026
program define fooddem_easi_gmm, eclass sortpreserve
    version 17
    syntax [if] [in], SHARES(varlist numeric min=3) LNP(varlist numeric min=3) ///
        EXPenditure(varname numeric) ORDER(integer) INSTruments(varlist numeric) ///
        PNAMES(string asis) INITIAL(name) [DEMographics(varlist numeric) ///
        CF(varname numeric) PHI(varlist numeric) PDF(varlist numeric) ///
        SYACTIVE(numlist integer) CLuster(varname numeric) STEPS(integer 1) ///
        ITERate(integer 200) TOLerance(real 1e-6) RAWLNP(varlist numeric) ///
        RAWEXP(varname numeric) CSCALES(numlist) XMEAN(real 0)]

    marksample touse, novarlist
    markout `touse' `shares' `lnp' `expenditure' `instruments' ///
        `demographics' `cf' `phi' `pdf' `cluster' `rawlnp' `rawexp'
    local k : word count `shares'
    local kp : word count `lnp'
    local neq = `k' - 1
    local npar : word count `pnames'
    local nphi : word count `phi'
    local npdf : word count `pdf'
    if `kp' != `k' {
        di as error "shares() and lnp() must contain the same number of goods"
        exit 198
    }
    local kr : word count `rawlnp'
    local kc : word count `cscales'
    if (`kr' > 0 | "`rawexp'" != "" | `kc' > 0) & ///
        (`kr' != `k' | "`rawexp'" == "" | `kc' != `k') {
        di as error "GEASI requires one rawlnp() and cscales() value per good plus rawexp()"
        exit 198
    }
    if !inlist(`steps', 1, 2) {
        di as error "steps() must be 1 or 2"
        exit 198
    }
    if (`nphi' != 0 | `npdf' != 0) & (`nphi' != `k' | `npdf' != `k') {
        di as error "phi() and pdf() must both contain one variable per good"
        exit 198
    }
    if "`syactive'" != "" {
        local nsy : word count `syactive'
        if `nsy' != `k' {
            di as error "syactive() must contain one indicator per good"
            exit 198
        }
    }
    tempname b0
    matrix `b0' = `initial'
    if colsof(`b0') != `npar' {
        di as error "initial() does not match the EASI parameter count"
        exit 503
    }
    quietly count if `touse'
    if r(N) <= `npar' {
        di as error "insufficient observations for the EASI parameterization"
        exit 2001
    }

    tempname b V J Jdf prank N Nclust qinst conv iters criterion
    mata: _fooddem_easi_gmm_fit("`touse'", "`shares'", "`lnp'", ///
        "`expenditure'", "`demographics'", "`cf'", "`phi'", "`pdf'", ///
        "`syactive'", "`instruments'", "`cluster'", "`rawlnp'", ///
        "`rawexp'", "`cscales'", `xmean', `order', `npar', ///
        `steps', `iterate', `tolerance', "`b0'", "`b'", "`V'", "`J'", ///
        "`Jdf'", "`prank'", "`N'", "`Nclust'", "`qinst'", "`conv'", ///
        "`iters'", "`criterion'")

    local cnames ""
    foreach ph of local pnames {
        local cnames "`cnames' _cons"
    }
    matrix colnames `b' = `cnames'
    matrix coleq `b' = `pnames'
    matrix rownames `V' = `cnames'
    matrix colnames `V' = `cnames'
    matrix roweq `V' = `pnames'
    matrix coleq `V' = `pnames'
    ereturn post `b' `V', esample(`touse')
    ereturn scalar N = scalar(`N')
    ereturn scalar N_clust = scalar(`Nclust')
    ereturn scalar rank = scalar(`prank')
    ereturn scalar J = scalar(`J')
    ereturn scalar J_df = scalar(`Jdf')
    ereturn scalar converged = scalar(`conv')
    ereturn scalar ic = scalar(`iters')
    ereturn scalar criterion = scalar(`criterion')
    ereturn scalar k_eq = `neq'
    ereturn scalar k_moments = scalar(`qinst') * `neq'
    ereturn local vcetype "Robust"
    ereturn local vce "robust"
    if "`cluster'" != "" {
        ereturn local vce "cluster"
        ereturn local clustvar "`cluster'"
    }
    ereturn local title "Exact constrained EASI/GEASI GMM"
    ereturn local cmd "fooddem_easi_gmm"
end

capture mata: mata drop _fooddem_easi_nl_predict()
capture mata: mata drop _fooddem_easi_nl_moments()
capture mata: mata drop _fooddem_easi_nl_errors()
capture mata: mata drop _fooddem_easi_nl_jacobian()
capture mata: mata drop _fooddem_easi_nl_optimize()
capture mata: mata drop _fooddem_easi_nl_clusterS()
capture mata: mata drop _fooddem_easi_gmm_fit()
mata:
mata set matastrict on

__fooddem_geasi_rawP = J(0, 0, .)
__fooddem_geasi_rawx = J(0, 1, .)
__fooddem_geasi_cscales = J(1, 0, .)
__fooddem_geasi_xmean = 0

real matrix _fooddem_easi_nl_predict(
    real colvector beta,
    real matrix Sall,
    real matrix P,
    real colvector x,
    real matrix D,
    real matrix CF,
    real matrix Phi,
    real matrix Pdf,
    real rowvector active,
    real scalar hmax)
{
    external real matrix __fooddem_geasi_rawP
    external real colvector __fooddem_geasi_rawx
    external real rowvector __fooddem_geasi_cscales
    external real scalar __fooddem_geasi_xmean
    real scalar n, k, neq, nd, pos, i, j, h, d, a, bb
    real colvector avec, rvec, dvec, cvec, xlevel, totalcommit
    real colvector discretionary, y, pAp, base
    real matrix B, G, T, commit, pred

    n = rows(Sall)
    k = cols(Sall)
    neq = k - 1
    nd = cols(D)
    pos = 0
    avec = J(neq, 1, 0)
    for (i = 1; i <= neq; i++) avec[i] = beta[++pos]
    B = J(neq, hmax, 0)
    for (i = 1; i <= neq; i++) {
        for (h = 1; h <= hmax; h++) B[i, h] = beta[++pos]
    }
    G = J(k, k, 0)
    for (a = 1; a <= neq; a++) {
        for (bb = a; bb <= neq; bb++) {
            G[a, bb] = beta[++pos]
            G[bb, a] = G[a, bb]
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
    if (cols(CF) > 0) {
        for (i = 1; i <= neq; i++) rvec[i] = beta[++pos]
    }
    dvec = J(neq, 1, 0)
    for (i = 1; i <= neq; i++) {
        if (active[i]) dvec[i] = beta[++pos]
    }
    cvec = J(k, 1, 0)
    if (cols(__fooddem_geasi_rawP) > 0) {
        for (i = 1; i <= k; i++) {
            cvec[i] = __fooddem_geasi_cscales[i] * tanh(beta[++pos])
        }
    }
    if (pos != rows(beta)) _error(3200)

    pAp = rowsum((P * G) :* P)
    discretionary = x
    commit = J(n, k, 0)
    totalcommit = J(n, 1, 0)
    if (cols(__fooddem_geasi_rawP) > 0) {
        xlevel = exp(__fooddem_geasi_rawx)
        commit = exp(__fooddem_geasi_rawP) :* (J(n, 1, 1) * cvec')
        commit = commit :/ (xlevel * J(1, k, 1))
        totalcommit = rowsum(commit)
        discretionary = xlevel :* (1 :- totalcommit)
        discretionary = ln(discretionary)
        discretionary = discretionary :- __fooddem_geasi_xmean
    }
    y = discretionary - rowsum(Sall :* P) + 0.5 * pAp
    pred = J(n, neq, 0)
    for (i = 1; i <= neq; i++) {
        base = J(n, 1, avec[i]) + P * G[i, ]'
        for (h = 1; h <= hmax; h++) base = base + B[i, h] * (y:^h)
        if (nd > 0) base = base + D * T[i, ]'
        if (cols(CF) > 0) base = base + rvec[i] * CF
        if (cols(__fooddem_geasi_rawP) > 0) {
            base = commit[, i] + (1 :- totalcommit) :* base
        }
        pred[, i] = Phi[, i] :* base + dvec[i] * Pdf[, i]
    }
    return(pred)
}

real matrix _fooddem_easi_nl_errors(
    real colvector beta,
    real matrix Sall,
    real matrix P,
    real colvector x,
    real matrix D,
    real matrix CF,
    real matrix Phi,
    real matrix Pdf,
    real rowvector active,
    real scalar hmax)
{
    real scalar neq
    neq = cols(Sall) - 1
    return(Sall[, 1..neq] - _fooddem_easi_nl_predict(beta, Sall, P, x, D,
        CF, Phi, Pdf, active, hmax))
}

real colvector _fooddem_easi_nl_moments(
    real colvector beta,
    real matrix Sall,
    real matrix P,
    real colvector x,
    real matrix D,
    real matrix CF,
    real matrix Phi,
    real matrix Pdf,
    real rowvector active,
    real scalar hmax,
    real matrix Z)
{
    real matrix E
    real colvector g
    real scalar n, neq, q, i

    E = _fooddem_easi_nl_errors(beta, Sall, P, x, D, CF, Phi, Pdf,
        active, hmax)
    n = rows(E)
    neq = cols(E)
    q = cols(Z)
    g = J(q * neq, 1, 0)
    for (i = 1; i <= neq; i++) {
        g[(i - 1) * q + 1..i * q] = quadcross(Z, E[, i]) / n
    }
    return(g)
}

real matrix _fooddem_easi_nl_jacobian(
    real colvector beta,
    real matrix Sall,
    real matrix P,
    real colvector x,
    real matrix D,
    real matrix CF,
    real matrix Phi,
    real matrix Pdf,
    real rowvector active,
    real scalar hmax,
    real matrix Z)
{
    real colvector bp, bm, gp, gm
    real matrix J
    real scalar p, j, delta

    p = rows(beta)
    J = J(cols(Z) * (cols(Sall) - 1), p, 0)
    for (j = 1; j <= p; j++) {
        delta = 1e-6 * (1 + abs(beta[j]))
        bp = beta
        bm = beta
        bp[j] = bp[j] + delta
        bm[j] = bm[j] - delta
        gp = _fooddem_easi_nl_moments(bp, Sall, P, x, D, CF, Phi,
            Pdf, active, hmax, Z)
        gm = _fooddem_easi_nl_moments(bm, Sall, P, x, D, CF, Phi,
            Pdf, active, hmax, Z)
        J[, j] = (gp - gm) / (2 * delta)
    }
    return(J)
}

real colvector _fooddem_easi_nl_optimize(
    real colvector start,
    real matrix W,
    real matrix Sall,
    real matrix P,
    real colvector x,
    real matrix D,
    real matrix CF,
    real matrix Phi,
    real matrix Pdf,
    real rowvector active,
    real scalar hmax,
    real matrix Z,
    real scalar maxiter,
    real scalar tolerance,
    real scalar converged,
    real scalar iterations)
{
    real colvector beta, candidate, g, gc, step
    real matrix J, H
    real scalar objective, newobjective, alpha, ls, movement

    beta = start
    g = _fooddem_easi_nl_moments(beta, Sall, P, x, D, CF, Phi,
        Pdf, active, hmax, Z)
    objective = quadcross(g, W * g)
    converged = 0
    iterations = 0
    for (iterations = 1; iterations <= maxiter; iterations++) {
        J = _fooddem_easi_nl_jacobian(beta, Sall, P, x, D, CF, Phi,
            Pdf, active, hmax, Z)
        H = quadcross(J, W * J)
        step = -invsym(H) * quadcross(J, W * g)
        if (missing(step)) break
        alpha = 1
        newobjective = .
        for (ls = 0; ls <= 20; ls++) {
            candidate = beta + alpha * step
            gc = _fooddem_easi_nl_moments(candidate, Sall, P, x, D, CF,
                Phi, Pdf, active, hmax, Z)
            newobjective = quadcross(gc, W * gc)
            if (newobjective <= objective + 1e-14 * (1 + objective)) break
            alpha = alpha / 2
        }
        if (ls > 20) break
        movement = max(abs(alpha * step) :/ (1 :+ abs(beta)))
        beta = candidate
        g = gc
        if (movement < tolerance | abs(objective - newobjective) <
            tolerance * 1e-3 * (1 + objective)) {
            converged = 1
            break
        }
        objective = newobjective
    }
    if (iterations > maxiter) iterations = maxiter
    return(beta)
}

real matrix _fooddem_easi_nl_clusterS(
    real matrix Z,
    real matrix E,
    real colvector cl)
{
    real scalar n, neq, q, i
    real colvector ord
    real matrix info, G, ZE

    n = rows(Z)
    neq = cols(E)
    q = cols(Z)
    ord = order(cl, 1)
    info = panelsetup(cl[ord], 1)
    G = J(rows(info), q * neq, 0)
    for (i = 1; i <= neq; i++) {
        ZE = Z :* E[, i]
        G[, (i - 1) * q + 1..i * q] = panelsum(ZE[ord, ], info)
    }
    return(quadcross(G, G) / n)
}

void _fooddem_easi_gmm_fit(
    string scalar tousevar,
    string scalar sharevars,
    string scalar pricevars,
    string scalar expvar,
    string scalar demovars,
    string scalar cfvar,
    string scalar phivars,
    string scalar pdfvars,
    string scalar syactive,
    string scalar instvars,
    string scalar clustvar,
    string scalar rawpricevars,
    string scalar rawexpvar,
    string scalar cscales,
    real scalar xmean,
    real scalar hmax,
    real scalar p,
    real scalar steps,
    real scalar maxiter,
    real scalar tolerance,
    string scalar initname,
    string scalar bname,
    string scalar Vname,
    string scalar Jname,
    string scalar Jdfname,
    string scalar prankname,
    string scalar Nname,
    string scalar Nclustname,
    string scalar qinstname,
    string scalar convname,
    string scalar itername,
    string scalar critname)
{
    external real matrix __fooddem_geasi_rawP
    external real colvector __fooddem_geasi_rawx
    external real rowvector __fooddem_geasi_cscales
    external real scalar __fooddem_geasi_xmean
    real colvector idx, x, cl, beta0, beta1, beta, gbar
    real matrix Sall, P, D, CF, Phi, Pdf, Z, W, Omega, OmegaV
    real matrix E1, E, J, bread, V
    real rowvector active
    real scalar n, k, neq, q, conv1, conv2, iter1, iter2
    real scalar rankJ, Jstat, Jdf, nclust, adjust, criterion

    idx = selectindex(st_data(., tousevar) :!= 0)
    Sall = st_data(idx, tokens(sharevars))
    P = st_data(idx, tokens(pricevars))
    x = st_data(idx, expvar)
    n = rows(Sall)
    k = cols(Sall)
    neq = k - 1
    D = J(n, 0, .)
    if (strtrim(demovars) != "") D = st_data(idx, tokens(demovars))
    CF = J(n, 0, .)
    if (strtrim(cfvar) != "") CF = st_data(idx, cfvar)
    Phi = J(n, neq, 1)
    Pdf = J(n, neq, 0)
    if (strtrim(phivars) != "") {
        Phi = st_data(idx, tokens(phivars))[, 1..neq]
        Pdf = st_data(idx, tokens(pdfvars))[, 1..neq]
    }
    active = J(1, k, 0)
    if (strtrim(syactive) != "") active = strtoreal(tokens(syactive))
    Z = J(n, 1, 1), st_data(idx, tokens(instvars))
    q = cols(Z)
    if (strtrim(clustvar) == "") cl = 1::n
    else cl = st_data(idx, clustvar)
    __fooddem_geasi_rawP = J(n, 0, .)
    __fooddem_geasi_rawx = J(n, 1, .)
    __fooddem_geasi_cscales = J(1, 0, .)
    __fooddem_geasi_xmean = xmean
    if (strtrim(rawpricevars) != "") {
        __fooddem_geasi_rawP = st_data(idx, tokens(rawpricevars))
        __fooddem_geasi_rawx = st_data(idx, rawexpvar)
        __fooddem_geasi_cscales = strtoreal(tokens(cscales))
    }
    beta0 = st_matrix(initname)'
    if (rows(beta0) != p) _error(3200)

    W = I(q * neq)
    conv1 = 0
    iter1 = 0
    beta1 = _fooddem_easi_nl_optimize(beta0, W, Sall, P, x, D, CF,
        Phi, Pdf, active, hmax, Z, maxiter, tolerance, conv1, iter1)
    E1 = _fooddem_easi_nl_errors(beta1, Sall, P, x, D, CF, Phi,
        Pdf, active, hmax)
    Omega = _fooddem_easi_nl_clusterS(Z, E1, cl)
    beta = beta1
    conv2 = 1
    iter2 = 0
    if (steps == 2) {
        W = invsym(Omega)
        beta = _fooddem_easi_nl_optimize(beta1, W, Sall, P, x, D, CF,
            Phi, Pdf, active, hmax, Z, maxiter, tolerance, conv2, iter2)
    }
    E = _fooddem_easi_nl_errors(beta, Sall, P, x, D, CF, Phi,
        Pdf, active, hmax)
    OmegaV = _fooddem_easi_nl_clusterS(Z, E, cl)
    J = _fooddem_easi_nl_jacobian(beta, Sall, P, x, D, CF, Phi,
        Pdf, active, hmax, Z)
    rankJ = rank(J)
    if (rankJ < p) {
        errprintf("EASI moment Jacobian has rank %g but %g parameters were requested\n", rankJ, p)
        exit(481)
    }
    bread = invsym(quadcross(J, W * J))
    V = bread * quadcross(J, W * OmegaV * W * J) * bread / n
    nclust = rows(uniqrows(sort(cl, 1)))
    adjust = 1
    if (nclust > 1 & n > p) adjust = (nclust / (nclust - 1)) * ((n - 1) / (n - p))
    V = adjust * (V + V') / 2
    gbar = _fooddem_easi_nl_moments(beta, Sall, P, x, D, CF, Phi,
        Pdf, active, hmax, Z)
    criterion = quadcross(gbar, W * gbar)
    Jstat = n * criterion
    Jdf = q * neq - rankJ

    st_matrix(bname, beta')
    st_matrix(Vname, V)
    st_numscalar(Jname, Jstat)
    st_numscalar(Jdfname, Jdf)
    st_numscalar(prankname, rankJ)
    st_numscalar(Nname, n)
    st_numscalar(Nclustname, nclust)
    st_numscalar(qinstname, q)
    st_numscalar(convname, conv1 & conv2)
    st_numscalar(itername, iter1 + iter2)
    st_numscalar(critname, criterion)
}
end
