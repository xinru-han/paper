*! Local curvature projection after fooddem 1.2.0  13jul2026
program define fooddem_curvature, rclass
    version 17
    syntax using/, [REPLACE]
    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    local k = e(fooddem_goods)

    * Demand-theory regularity applies to the latent structural system. The
    * Shonkwiler-Yen observed-share transformation is intentionally excluded.
    tempfile regbase
    quietly fooddem_regularity using "`regbase'.dta", margin(latent) replace
    tempname S W E0 EP SP
    matrix `S' = r(slutsky)

    local base ""
    forvalues i = 1/`k' {
        tempvar b`i'
        local base "`base' `b`i''"
    }
    quietly fooddem_p `base', latent
    tempvar positive
    gen byte `positive' = e(sample)
    forvalues i = 1/`k' {
        local bi : word `i' of `base'
        replace `positive' = 0 if (missing(`bi') | `bi' <= 0) & e(sample)
    }
    quietly count if `positive'
    if r(N) == 0 {
        di as error "no observation has all latent fitted shares positive"
        exit 2000
    }
    matrix `W' = J(1, `k', .)
    forvalues i = 1/`k' {
        local bi : word `i' of `base'
        quietly summarize `bi' if `positive', meanonly
        matrix `W'[1,`i'] = r(mean)
    }

    mata: _fooddem_curvature_project("`S'", "`W'", "`E0'", "`EP'", "`SP'")
    local maxeig0 = scalar(__fd_curve_eig0)
    local maxeigp = scalar(__fd_curve_eigp)
    local fnorm = scalar(__fd_curve_fnorm)

    tempname mem
    tempfile result
    postfile `mem' int demand_good shock_good double original_hicksian ///
        projected_hicksian adjustment original_max_eigenvalue ///
        projected_max_eigenvalue frobenius_adjustment using `result', replace
    forvalues i = 1/`k' {
        forvalues j = 1/`k' {
            post `mem' (`i') (`j') (`E0'[`i',`j']) (`EP'[`i',`j']) ///
                (`EP'[`i',`j'] - `E0'[`i',`j']) (`maxeig0') (`maxeigp') (`fnorm')
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
    return scalar original_max_eigenvalue = `maxeig0'
    return scalar projected_max_eigenvalue = `maxeigp'
    return scalar frobenius_adjustment = `fnorm'
    return matrix original_hicksian = `E0'
    return matrix projected_hicksian = `EP'
    return matrix projected_slutsky = `SP'
end

capture mata: mata drop _fooddem_curvature_project()
mata:
mata set matastrict on

void _fooddem_curvature_project(
    string scalar sname,
    string scalar wname,
    string scalar e0name,
    string scalar epname,
    string scalar spname)
{
    real matrix S, P, S0, Q, SP, E0, EP
    real colvector w
    real rowvector eval, evalp
    real scalar k

    S = st_matrix(sname)
    w = st_matrix(wname)'
    k = rows(S)
    P = I(k) - J(k, k, 1 / k)
    S0 = P * ((S + S') / 2) * P
    symeigensystem(S0, Q, eval)
    evalp = eval
    evalp = evalp :* (evalp :< 0)
    SP = Q' * diag(evalp) * Q
    SP = P * ((SP + SP') / 2) * P
    E0 = diag(1 :/ w) * S0
    EP = diag(1 :/ w) * SP

    st_matrix(e0name, E0)
    st_matrix(epname, EP)
    st_matrix(spname, SP)
    st_numscalar("__fd_curve_eig0", max(symeigenvalues(S0)))
    st_numscalar("__fd_curve_eigp", max(symeigenvalues(SP)))
    st_numscalar("__fd_curve_fnorm", sqrt(sum((SP - S0) :^ 2)))
}
end
