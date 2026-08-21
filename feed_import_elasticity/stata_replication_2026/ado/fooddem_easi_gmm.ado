*! Exact constrained EASI/GEASI nonlinear GMM solver 1.1.0  14jul2026
program define fooddem_easi_gmm, eclass sortpreserve
    version 17
    syntax [if] [in], SHARES(varlist numeric min=3) LNP(varlist numeric min=3) ///
        EXPenditure(varname numeric) ORDER(integer) INSTruments(varlist numeric) ///
        PNAMES(string asis) INITIAL(name) [DEMographics(varlist numeric) ///
        CF(varname numeric) PHI(varlist numeric) PDF(varlist numeric) ///
        SYACTIVE(numlist integer) CLuster(varname numeric) STEPS(integer 1) ///
        ITERate(integer 200) TOLerance(real 1e-6) RAWLNP(varlist numeric) ///
        RAWEXP(varname numeric) CSCALES(numlist) XMEAN(real 0) ///
        CURVature(string)]

    local curvature = lower("`curvature'")
    if "`curvature'" == "" local curvature "none"
    if !inlist("`curvature'", "none", "local", "global") {
        di as error "curvature() must be none, local, or global"
        exit 198
    }
    if "`curvature'" != "none" & "`rawlnp'" != "" {
        di as error "curvature() is not available for GEASI precommitments"
        exit 198
    }
    local curvemode = 0
    if "`curvature'" == "local" local curvemode = 1
    if "`curvature'" == "global" local curvemode = 2

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
        `curvemode', ///
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
    ereturn local curvature "`curvature'"
    ereturn local cmd "fooddem_easi_gmm"
end

capture mata: mata drop _fooddem_easi_nl_predict()
capture mata: mata drop _fooddem_easi_nl_moments()
capture mata: mata drop _fooddem_easi_nl_errors()
capture mata: mata drop _fooddem_easi_nl_jacobian()
capture mata: mata drop _fooddem_easi_nl_optimize()
capture mata: mata drop _fooddem_easi_nl_clusterS()
capture mata: mata drop _fooddem_helmert()
capture mata: mata drop _fd_softplus()
capture mata: mata drop _fd_invsoftplus()
capture mata: mata drop _fooddem_curve_wref()
capture mata: mata drop _fooddem_curve_to_theta()
capture mata: mata drop _fooddem_curve_to_beta()
capture mata: mata drop _fd_curve_transform_J()
capture mata: mata drop _fooddem_easi_gmm_fit()
mata:
mata set matastrict on

__fooddem_geasi_rawP = J(0, 0, .)
__fooddem_geasi_rawx = J(0, 1, .)
__fooddem_geasi_cscales = J(1, 0, .)
__fooddem_geasi_xmean = 0
__fooddem_curve_mode = 0

real scalar _fd_softplus(real scalar x)
{
    if (x > 30) return(x)
    if (x < -30) return(exp(x))
    return(ln(1 + exp(x)))
}

real scalar _fd_invsoftplus(real scalar x)
{
    x = max((x, 1e-10))
    if (x > 30) return(x)
    return(ln(exp(x) - 1))
}

real matrix _fooddem_helmert(real scalar k)
{
    real matrix Q
    real scalar j

    Q = J(k, k - 1, 0)
    for (j = 1; j <= k - 1; j++) {
        Q[1..j, j] = J(j, 1, 1 / sqrt(j * (j + 1)))
        Q[j + 1, j] = -j / sqrt(j * (j + 1))
    }
    return(Q)
}

real colvector _fooddem_curve_wref(
    real colvector beta,
    real scalar k,
    real scalar hmax,
    real matrix D,
    real matrix CF)
{
    real scalar neq, nd, pos, i, d
    real colvector wref, rvec
    real matrix T

    neq = k - 1
    nd = cols(D)
    wref = beta[1..neq]
    pos = neq + neq * hmax + neq * (neq + 1) / 2
    T = J(neq, nd, 0)
    for (i = 1; i <= neq; i++) {
        for (d = 1; d <= nd; d++) T[i, d] = beta[++pos]
    }
    if (nd > 0) wref = wref + T * mean(D)'
    rvec = J(neq, 1, 0)
    if (cols(CF) > 0) {
        for (i = 1; i <= neq; i++) rvec[i] = beta[++pos]
        wref = wref + rvec * mean(CF)
    }
    return(wref \ (1 - sum(wref)))
}

real colvector _fooddem_curve_to_theta(
    real colvector beta,
    real scalar k,
    real scalar hmax,
    real matrix D,
    real matrix CF,
    real scalar curvemode)
{
    real scalar neq, pos, a, bb
    real colvector theta, wref, eval
    real matrix G, S, Q, M, U, L

    neq = k - 1
    theta = beta
    wref = _fooddem_curve_wref(beta, k, hmax, D, CF)
    G = J(k, k, 0)
    pos = neq + neq * hmax
    for (a = 1; a <= neq; a++) {
        for (bb = a; bb <= neq; bb++) {
            G[a, bb] = beta[++pos]
            G[bb, a] = G[a, bb]
        }
    }
    for (a = 1; a <= neq; a++) {
        G[a, k] = -sum(G[a, 1..neq])
        G[k, a] = G[a, k]
    }
    G[k, k] = sum(G[1..neq, 1..neq])
    Q = _fooddem_helmert(k)
    if (curvemode == 1) S = G + wref * wref' - diag(wref)
    else S = G
    M = -(Q' * ((S + S') / 2) * Q)
    symeigensystem((M + M') / 2, U, eval)
    eval = (eval :> 1e-8) :* eval + (eval :<= 1e-8) :* 1e-8
    M = U' * diag(eval) * U
    L = cholesky((M + M') / 2)
    pos = neq + neq * hmax
    for (a = 1; a <= neq; a++) {
        for (bb = a; bb <= neq; bb++) {
            pos++
            if (curvemode == 2 & bb == a) theta[pos] = _fd_invsoftplus(L[bb,a])
            else theta[pos] = L[bb,a]
        }
    }
    return(theta)
}

real colvector _fooddem_curve_to_beta(
    real colvector theta,
    real scalar k,
    real scalar hmax,
    real matrix D,
    real matrix CF,
    real scalar curvemode)
{
    real scalar neq, pos, a, bb
    real colvector beta, wref
    real matrix G, Q, L

    neq = k - 1
    beta = theta
    wref = _fooddem_curve_wref(theta, k, hmax, D, CF)
    L = J(neq, neq, 0)
    pos = neq + neq * hmax
    for (a = 1; a <= neq; a++) {
        for (bb = a; bb <= neq; bb++) {
            pos++
            if (curvemode == 2 & bb == a) L[bb,a] = _fd_softplus(theta[pos])
            else L[bb,a] = theta[pos]
        }
    }
    Q = _fooddem_helmert(k)
    if (curvemode == 1) G = diag(wref) - wref * wref' - Q * L * L' * Q'
    else G = -Q * L * L' * Q'
    pos = neq + neq * hmax
    for (a = 1; a <= neq; a++) {
        for (bb = a; bb <= neq; bb++) beta[++pos] = G[a, bb]
    }
    return(beta)
}

real matrix _fd_curve_transform_J(
    real colvector theta,
    real scalar k,
    real scalar hmax,
    real matrix D,
    real matrix CF,
    real scalar curvemode)
{
    real scalar p, j, delta
    real colvector tp, tm
    real matrix Jt

    p = rows(theta)
    Jt = J(p, p, 0)
    for (j = 1; j <= p; j++) {
        delta = 1e-6 * (1 + abs(theta[j]))
        tp = theta
        tm = theta
        tp[j] = tp[j] + delta
        tm[j] = tm[j] - delta
        Jt[, j] = (_fooddem_curve_to_beta(tp, k, hmax, D, CF, curvemode) -
            _fooddem_curve_to_beta(tm, k, hmax, D, CF, curvemode)) / (2 * delta)
    }
    return(Jt)
}

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
    external real scalar __fooddem_curve_mode
    real scalar n, k, neq, nd, pos, i, j, h, d, a, bb
    real colvector avec, rvec, dvec, cvec, xlevel, totalcommit
    real colvector discretionary, y, pAp, base, wref
    real matrix B, G, L, Q, T, commit, pred

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
    L = J(neq, neq, 0)
    for (a = 1; a <= neq; a++) {
        for (bb = a; bb <= neq; bb++) {
            if (__fooddem_curve_mode) {
                pos++
                if (__fooddem_curve_mode == 2 & bb == a) {
                    L[bb,a] = _fd_softplus(beta[pos])
                }
                else L[bb,a] = beta[pos]
            }
            else {
                G[a, bb] = beta[++pos]
                G[bb, a] = G[a, bb]
            }
        }
    }
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

    if (__fooddem_curve_mode) {
        wref = avec
        if (nd > 0) wref = wref + T * mean(D)'
        if (cols(CF) > 0) wref = wref + rvec * mean(CF)
        wref = wref \ (1 - sum(wref))
        Q = _fooddem_helmert(k)
        if (__fooddem_curve_mode == 1) {
            G = diag(wref) - wref * wref' - Q * L * L' * Q'
        }
        else G = -Q * L * L' * Q'
    }
    else {
        for (i = 1; i <= neq; i++) {
            G[i, k] = -sum(G[i, 1..neq])
            G[k, i] = G[i, k]
        }
        G[k, k] = sum(G[1..neq, 1..neq])
    }

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
    real scalar curvemode,
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
    external real scalar __fooddem_curve_mode
    real colvector idx, x, cl, beta0, beta1, beta, gbar
    real matrix Sall, P, D, CF, Phi, Pdf, Z, W, Omega, OmegaV
    real matrix E1, E, J, bread, V, Jt
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
    __fooddem_curve_mode = curvemode
    if (strtrim(rawpricevars) != "") {
        __fooddem_geasi_rawP = st_data(idx, tokens(rawpricevars))
        __fooddem_geasi_rawx = st_data(idx, rawexpvar)
        __fooddem_geasi_cscales = strtoreal(tokens(cscales))
    }
    beta0 = st_matrix(initname)'
    if (rows(beta0) != p) _error(3200)
    if (curvemode) beta0 = _fooddem_curve_to_theta(beta0, k, hmax, D, CF, curvemode)

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

    if (curvemode) {
        Jt = _fd_curve_transform_J(beta, k, hmax, D, CF, curvemode)
        V = Jt * V * Jt'
        beta = _fooddem_curve_to_beta(beta, k, hmax, D, CF, curvemode)
    }

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
