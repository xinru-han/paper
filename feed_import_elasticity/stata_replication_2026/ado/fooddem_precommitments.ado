*! GEASI transformed precommitment quantities 1.0.0  12jul2026
program define fooddem_precommitments, rclass
    version 17
    syntax using/, [REPLACE]
    if "`e(fooddem_precommitment)'" == "" {
        di as error "the active fooddem estimate has no GEASI precommitments"
        exit 301
    }
    local k = e(fooddem_goods)
    local scales "`e(fooddem_cscales)'"
    tempname b V mem
    tempfile results
    matrix `b' = e(b)
    matrix `V' = e(V)
    local first = colsof(`b') - `k' + 1
    postfile `mem' int good double scale latent_parameter latent_std_error ///
        precommitted_quantity std_error statistic p_value using `results', replace
    forvalues i = 1/`k' {
        local h = `first' + `i' - 1
        local scale : word `i' of `scales'
        local theta = `b'[1,`h']
        local setheta = sqrt(`V'[`h',`h'])
        local quantity = `scale' * tanh(`theta')
        local derivative = `scale' * (1 - tanh(`theta')^2)
        local sequantity = abs(`derivative') * `setheta'
        local z = `quantity' / `sequantity'
        local p = 2 * normal(-abs(`z'))
        post `mem' (`i') (`scale') (`theta') (`setheta') (`quantity') ///
            (`sequantity') (`z') (`p')
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
    return scalar goods = `k'
end
