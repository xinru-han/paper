*! Export fooddem coefficient table 1.0.0  12jul2026
program define fooddem_export, rclass
    version 17
    syntax using/, [LABel(string asis) REPLACE]
    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    if `"`label'"' == "" local label "`e(fooddem_model)'"

    tempname b V mem
    tempfile results
    matrix `b' = e(b)
    matrix `V' = e(V)
    local eqs : coleq `b'
    local cols : colnames `b'
    local npar = colsof(`b')
    local converged = cond(missing(e(converged)), 1, e(converged))
    postfile `mem' str40 specification str8 model str8 estimator int order ///
        byte gmm_steps converged str48 parameter double coefficient std_error ///
        statistic p_value ci_low ci_high using `results', replace
    forvalues h = 1/`npar' {
        local eq : word `h' of `eqs'
        local col : word `h' of `cols'
        local pname "`eq'"
        if "`col'" != "_cons" local pname "`eq':`col'"
        local coef = `b'[1,`h']
        local se = sqrt(`V'[`h',`h'])
        local z = `coef' / `se'
        local p = 2 * normal(-abs(`z'))
        local lo = `coef' - invnormal(.975) * `se'
        local hi = `coef' + invnormal(.975) * `se'
        post `mem' (`"`label'"') ("`e(fooddem_model)'") ///
            ("`e(fooddem_estimator)'") (e(fooddem_order)) ///
            (e(fooddem_gmmsteps)) (`converged') ("`pname'") (`coef') (`se') ///
            (`z') (`p') (`lo') (`hi')
    }
    postclose `mem'
    preserve
        use `results', clear
        if regexm(lower("`using'"), "[.]dta$") {
            if "`replace'" != "" save "`using'", replace
            else save "`using'"
        }
        else {
            if "`replace'" != "" export delimited using "`using'", replace
            else export delimited using "`using'"
        }
    restore
    return scalar rows = `npar'
end
