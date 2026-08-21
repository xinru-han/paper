*! Conditional linear EASI GMM initializer 1.0.0  12jul2026
program define fooddem_easi_linear, eclass sortpreserve
    version 17
    syntax [if] [in], SHARES(varlist numeric min=3) LNP(varlist numeric min=3) ///
        EXPenditure(varname numeric) ORDER(integer) INSTruments(varlist numeric) ///
        PNAMES(string asis) [DEMographics(varlist numeric) CF(varname numeric) ///
        PHI(varlist numeric) PDF(varlist numeric) SYACTIVE(numlist integer) ///
        CLuster(varname numeric) STEPS(integer 1)]

    marksample touse, novarlist
    markout `touse' `shares' `lnp' `expenditure' `instruments' ///
        `demographics' `cf' `phi' `pdf' `cluster'
    local k : word count `shares'
    local kp : word count `lnp'
    local neq = `k' - 1
    local npar : word count `pnames'
    local nd : word count `demographics'
    local nphi : word count `phi'
    local npdf : word count `pdf'
    if `kp' != `k' {
        di as error "shares() and lnp() must contain the same number of goods"
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
    quietly count if `touse'
    if r(N) <= `npar' {
        di as error "insufficient observations for the EASI parameterization"
        exit 2001
    }

    tempname b V J Jdf prank N Nclust qinst
    mata: _fooddem_easi_linear_fit("`touse'", "`shares'", "`lnp'", ///
        "`expenditure'", "`demographics'", "`cf'", "`phi'", "`pdf'", ///
        "`syactive'", "`instruments'", "`cluster'", `order', `npar', ///
        `steps', "`b'", "`V'", "`J'", "`Jdf'", "`prank'", "`N'", ///
        "`Nclust'", "`qinst'")

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
    ereturn scalar converged = 1
    ereturn scalar k_eq = `neq'
    ereturn scalar k_moments = scalar(`qinst') * `neq'
    ereturn local vcetype "Robust"
    ereturn local vce "robust"
    if "`cluster'" != "" {
        ereturn local vcetype "Robust"
        ereturn local vce "cluster"
        ereturn local clustvar "`cluster'"
    }
    ereturn local title "Linear constrained EASI GMM"
    ereturn local cmd "fooddem_easi_linear"
end

capture mata: mata drop _fooddem_easi_clusterS()
capture mata: mata drop _fooddem_easi_linear_fit()
mata:
mata set matastrict on

real matrix _fooddem_easi_clusterS(
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

void _fooddem_easi_linear_fit(
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
    real scalar hmax,
    real scalar p,
    real scalar steps,
    string scalar bname,
    string scalar Vname,
    string scalar Jname,
    string scalar Jdfname,
    string scalar prankname,
    string scalar Nname,
    string scalar Nclustname,
    string scalar qinstname)
{
    real colvector idx, y, cl, beta, beta1, c, gbar
    real matrix Sall, P, D, CF, Phi, Pdf, Z, relP, Y, X, A
    real matrix W, Omega, OmegaV, bread, V, E, E1
    real rowvector active
    real scalar n, k, neq, nd, q, pos, i, j, h, d, a, bb
    real scalar r1, r2, rankA, Jstat, Jdf, nclust, adjust
    real rowvector rr

    idx = selectindex(st_data(., tousevar) :!= 0)
    Sall = st_data(idx, tokens(sharevars))
    P = st_data(idx, tokens(pricevars))
    y = st_data(idx, expvar) - rowsum(Sall :* P)
    n = rows(Sall)
    k = cols(Sall)
    neq = k - 1
    Y = Sall[, 1..neq]

    D = J(n, 0, .)
    if (strtrim(demovars) != "") D = st_data(idx, tokens(demovars))
    nd = cols(D)
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
    relP = J(n, neq, .)
    for (j = 1; j <= neq; j++) relP[, j] = P[, j] - P[, k]

    X = J(n * neq, p, 0)
    pos = 0
    for (i = 1; i <= neq; i++) {
        rr = (i - 1) * n + 1..i * n
        pos++
        X[rr, pos] = Phi[, i]
    }
    for (i = 1; i <= neq; i++) {
        rr = (i - 1) * n + 1..i * n
        for (h = 1; h <= hmax; h++) {
            pos++
            X[rr, pos] = Phi[, i] :* (y:^h)
        }
    }
    for (a = 1; a <= neq; a++) {
        for (bb = a; bb <= neq; bb++) {
            pos++
            r1 = (a - 1) * n + 1
            r2 = a * n
            X[r1..r2, pos] = Phi[, a] :* relP[, bb]
            if (bb != a) {
                r1 = (bb - 1) * n + 1
                r2 = bb * n
                X[r1..r2, pos] = Phi[, bb] :* relP[, a]
            }
        }
    }
    for (i = 1; i <= neq; i++) {
        rr = (i - 1) * n + 1..i * n
        for (d = 1; d <= nd; d++) {
            pos++
            X[rr, pos] = Phi[, i] :* D[, d]
        }
    }
    if (cols(CF) > 0) {
        for (i = 1; i <= neq; i++) {
            rr = (i - 1) * n + 1..i * n
            pos++
            X[rr, pos] = Phi[, i] :* CF
        }
    }
    for (i = 1; i <= neq; i++) {
        if (active[i]) {
            rr = (i - 1) * n + 1..i * n
            pos++
            X[rr, pos] = Pdf[, i]
        }
    }
    if (pos != p) {
        errprintf("internal EASI parameter-map mismatch: built %g columns, expected %g\n", pos, p)
        exit(498)
    }

    A = J(q * neq, p, 0)
    c = J(q * neq, 1, 0)
    for (i = 1; i <= neq; i++) {
        r1 = (i - 1) * n + 1
        r2 = i * n
        A[(i - 1) * q + 1..i * q, ] = quadcross(Z, X[r1..r2, ]) / n
        c[(i - 1) * q + 1..i * q] = quadcross(Z, Y[, i]) / n
    }
    rankA = rank(A)
    if (rankA < p) {
        errprintf("EASI moment Jacobian has rank %g but %g parameters were requested\n", rankA, p)
        exit(481)
    }

    W = I(q * neq)
    bread = invsym(quadcross(A, W * A))
    beta1 = bread * quadcross(A, W * c)
    E1 = J(n, neq, .)
    for (i = 1; i <= neq; i++) {
        r1 = (i - 1) * n + 1
        r2 = i * n
        E1[, i] = Y[, i] - X[r1..r2, ] * beta1
    }
    if (strtrim(clustvar) == "") cl = 1::n
    else cl = st_data(idx, clustvar)
    Omega = _fooddem_easi_clusterS(Z, E1, cl)

    beta = beta1
    if (steps == 2) {
        W = invsym(Omega)
        bread = invsym(quadcross(A, W * A))
        beta = bread * quadcross(A, W * c)
    }
    E = J(n, neq, .)
    for (i = 1; i <= neq; i++) {
        r1 = (i - 1) * n + 1
        r2 = i * n
        E[, i] = Y[, i] - X[r1..r2, ] * beta
    }
    OmegaV = _fooddem_easi_clusterS(Z, E, cl)
    bread = invsym(quadcross(A, W * A))
    V = bread * quadcross(A, W * OmegaV * W * A) * bread / n
    nclust = rows(uniqrows(sort(cl, 1)))
    adjust = 1
    if (nclust > 1 & n > p) adjust = (nclust / (nclust - 1)) * ((n - 1) / (n - p))
    V = adjust * (V + V') / 2

    gbar = J(q * neq, 1, 0)
    for (i = 1; i <= neq; i++) {
        gbar[(i - 1) * q + 1..i * q] = quadcross(Z, E[, i]) / n
    }
    Jstat = n * quadcross(gbar, W * gbar)
    Jdf = q * neq - rankA

    st_matrix(bname, beta')
    st_matrix(Vname, V)
    st_numscalar(Jname, Jstat)
    st_numscalar(Jdfname, Jdf)
    st_numscalar(prankname, rankA)
    st_numscalar(Nname, n)
    st_numscalar(Nclustname, nclust)
    st_numscalar(qinstname, q)
}
end
