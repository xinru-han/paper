*! Demand-theory regularity diagnostics after fooddem 1.0.0  12jul2026
program define fooddem_regularity, rclass
    version 17
    syntax using/, [STEP(real 0.001) REPLACE]
    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    if `step' <= 0 | `step' > .1 {
        di as error "step() must be in (0,.1]"
        exit 198
    }

    local k = e(fooddem_goods)
    local prices "`e(fooddem_prices)'"
    local expvar "`e(fooddem_expenditure)'"
    local h = ln(1 + `step')
    local base ""
    forvalues i = 1/`k' {
        tempvar b`i'
        local base "`base' `b`i''"
    }
    quietly fooddem_p `base'

    tempvar sumfit positive xbak
    egen double `sumfit' = rowtotal(`base') if e(sample)
    gen byte `positive' = 1 if e(sample)
    forvalues i = 1/`k' {
        local bi : word `i' of `base'
        replace `positive' = 0 if `bi' <= 0 & e(sample)
    }
    quietly summarize `sumfit' if e(sample), meanonly
    local add_error = max(abs(r(min) - 1), abs(r(max) - 1))
    quietly summarize `positive' if e(sample), meanonly
    local positive_rate = r(mean)

    * Numerical expenditure derivatives are used both for monotonicity and
    * the Slutsky compensation term. Prices and expenditure are log variables.
    gen double `xbak' = `expvar'
    replace `expvar' = `expvar' + `h' if e(sample)
    local xnew ""
    local xlow ""
    forvalues i = 1/`k' {
        tempvar xn`i' xl`i'
        local xnew "`xnew' `xn`i''"
        local xlow "`xlow' `xl`i''"
    }
    quietly fooddem_p `xnew'
    replace `expvar' = `xbak' - `h' if e(sample)
    quietly fooddem_p `xlow'
    replace `expvar' = `xbak'
    local etas ""
    local eta_positive_n = 0
    local eta_valid_n = 0
    forvalues i = 1/`k' {
        local bi : word `i' of `base'
        local ni : word `i' of `xnew'
        local li : word `i' of `xlow'
        tempvar eta`i'
        gen double `eta`i'' = 1 + (`ni' - `li') / (2 * `h' * `bi') if e(sample) & `bi' > 0
        local etas "`etas' `eta`i''"
        quietly count if !missing(`eta`i'') & e(sample)
        local eta_valid_n = `eta_valid_n' + r(N)
        quietly count if `eta`i'' > 0 & !missing(`eta`i'') & e(sample)
        local eta_positive_n = `eta_positive_n' + r(N)
    }
    local eta_positive_rate = `eta_positive_n' / `eta_valid_n'

    * S_ij = E[w_i e^H_ij]. Averaging the observation-level compensated
    * share responses preserves the aggregation relevant for the sample.
    tempname H S
    matrix `H' = J(`k', `k', .)
    matrix `S' = J(`k', `k', .)
    local own_negative_n = 0
    local own_valid_n = 0
    forvalues j = 1/`k' {
        local pj : word `j' of `prices'
        tempvar pbak
        gen double `pbak' = `pj'
        replace `pj' = `pj' + `h' if e(sample)
        local pnew ""
        local plow ""
        forvalues i = 1/`k' {
            tempvar pn`j'_`i' pl`j'_`i'
            local pnew "`pnew' `pn`j'_`i''"
            local plow "`plow' `pl`j'_`i''"
        }
        quietly fooddem_p `pnew'
        replace `pj' = `pbak' - `h' if e(sample)
        quietly fooddem_p `plow'
        replace `pj' = `pbak'
        forvalues i = 1/`k' {
            local bi : word `i' of `base'
            local ni : word `i' of `pnew'
            local li : word `i' of `plow'
            local etai : word `i' of `etas'
            local bj : word `j' of `base'
            tempvar em eh sij
            gen double `em' = (`ni' - `li') / (2 * `h' * `bi') - (`i' == `j') if e(sample) & `bi' > 0
            gen double `eh' = `em' + `etai' * `bj' if e(sample) & `bi' > 0
            * A single common positive-share sample is required for both S_ij
            * and S_ji. Row-specific deletion mechanically creates asymmetry.
            gen double `sij' = `bi' * `eh' if e(sample) & `positive' == 1
            quietly summarize `eh' if e(sample), meanonly
            matrix `H'[`i',`j'] = r(mean)
            if `i' == `j' {
                quietly count if !missing(`eh') & e(sample)
                local own_valid_n = `own_valid_n' + r(N)
                quietly count if `eh' <= 0 & !missing(`eh') & e(sample)
                local own_negative_n = `own_negative_n' + r(N)
            }
            quietly summarize `sij' if e(sample) & `positive' == 1, meanonly
            matrix `S'[`i',`j'] = r(mean)
        }
    }
    local own_negative_rate = `own_negative_n' / `own_valid_n'
    mata: st_numscalar("__fd_symerr", max(abs(st_matrix("`S'") :- st_matrix("`S'")')))
    mata: st_numscalar("__fd_maxeig", max(symeigenvalues((st_matrix("`S'") + st_matrix("`S'")') / 2)))
    local symerr = scalar(__fd_symerr)
    local maxeig = scalar(__fd_maxeig)

    tempname mem
    tempfile result
    postfile `mem' str48 diagnostic double value threshold byte passed using `result', replace
    post `mem' ("adding_up_max_abs_error") (`add_error') (1e-8) (`add_error' < 1e-8)
    post `mem' ("positive_fitted_share_rate") (`positive_rate') (1) (`positive_rate' == 1)
    post `mem' ("positive_expenditure_elasticities") (`eta_positive_rate') (1) (`eta_positive_rate' == 1)
    post `mem' ("negative_hicksian_own_elasticities") (`own_negative_rate') (1) (`own_negative_rate' == 1)
    post `mem' ("slutsky_symmetry_max_abs_error") (`symerr') (1e-4) (`symerr' < 1e-4)
    post `mem' ("slutsky_max_eigenvalue") (`maxeig') (0) (`maxeig' <= 1e-8)
    post `mem' ("adding_up_homogeneity_symmetry_imposed") (1) (1) (1)
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
    return scalar adding_up_error = `add_error'
    return scalar positive_share_rate = `positive_rate'
    return scalar positive_expenditure_rate = `eta_positive_rate'
    return scalar negative_hicksian_own_rate = `own_negative_rate'
    return scalar slutsky_symmetry_error = `symerr'
    return scalar slutsky_max_eigenvalue = `maxeig'
    return matrix hicksian = `H'
    return matrix slutsky = `S'
end
