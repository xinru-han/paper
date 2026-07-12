*! Numerical demand elasticities after fooddem 1.0.0  12jul2026
program define fooddem_elasticities, rclass
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
    local shares "`e(fooddem_shares)'"
    local prices "`e(fooddem_prices)'"
    local expvar "`e(fooddem_expenditure)'"
    local h = ln(1 + `step')
    tempname mem
    tempfile results
    postfile `mem' str24 elasticity_type int demand_good int shock_good ///
        double elasticity std_dev p10 p50 p90 n_valid using `results', replace

    local base ""
    forvalues i = 1/`k' {
        tempvar b`i'
        local base "`base' `b`i''"
    }
    fooddem_p `base'

    tempvar xbak
    gen double `xbak' = `expvar'
    replace `expvar' = `expvar' + `h' if e(sample)
    local xnew ""
    local xlow ""
    forvalues i = 1/`k' {
        tempvar xn`i' xl`i'
        local xnew "`xnew' `xn`i''"
        local xlow "`xlow' `xl`i''"
    }
    fooddem_p `xnew'
    replace `expvar' = `xbak' - `h' if e(sample)
    fooddem_p `xlow'
    replace `expvar' = `xbak'
    local explist ""
    forvalues i = 1/`k' {
        local bi : word `i' of `base'
        local ni : word `i' of `xnew'
        local li : word `i' of `xlow'
        tempvar ex`i'
        gen double `ex`i'' = 1 + (`ni' - `li') / (2 * `h' * `bi') if e(sample) & `bi' > 0
        quietly summarize `ex`i'', detail
        post `mem' ("expenditure") (`i') (0) (r(mean)) (r(sd)) ///
            (r(p10)) (r(p50)) (r(p90)) (r(N))
        local explist "`explist' `ex`i''"
    }

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
        fooddem_p `pnew'
        replace `pj' = `pbak' - `h' if e(sample)
        fooddem_p `plow'
        replace `pj' = `pbak'
        forvalues i = 1/`k' {
            local bi : word `i' of `base'
            local ni : word `i' of `pnew'
            local li : word `i' of `plow'
            local ei : word `i' of `explist'
            local bj : word `j' of `base'
            tempvar em eh
            gen double `em' = (`ni' - `li') / (2 * `h' * `bi') - (`i' == `j') if e(sample) & `bi' > 0
            gen double `eh' = `em' + `ei' * `bj' if e(sample) & `bi' > 0
            quietly summarize `em', detail
            post `mem' ("marshallian") (`i') (`j') (r(mean)) (r(sd)) ///
                (r(p10)) (r(p50)) (r(p90)) (r(N))
            quietly summarize `eh', detail
            post `mem' ("hicksian") (`i') (`j') (r(mean)) (r(sd)) ///
                (r(p10)) (r(p50)) (r(p90)) (r(N))
        }
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
        quietly count
        return scalar rows = r(N)
    restore
end
