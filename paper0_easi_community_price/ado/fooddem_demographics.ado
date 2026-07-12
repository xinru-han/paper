*! Demographic share elasticities/discrete effects after fooddem 1.0.0  12jul2026
program define fooddem_demographics, rclass
    version 17
    syntax using/, [STEP(real 0.001) REPLACE]
    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    local zvars "`e(fooddem_demographics)'"
    if "`zvars'" == "" {
        di as error "the fitted model contains no demographic variables"
        exit 198
    }
    local k = e(fooddem_goods)
    local h = ln(1 + `step')
    tempname mem
    tempfile results
    postfile `mem' str32 demographic str20 effect_type int good double effect n_valid using `results', replace
    local base ""
    forvalues i = 1/`k' {
        tempvar b`i'
        local base "`base' `b`i''"
    }
    fooddem_p `base'
    foreach z of local zvars {
        quietly summarize `z' if e(sample), meanonly
        local binary = r(min) >= 0 & r(max) <= 1 & floor(r(min)) == r(min) & floor(r(max)) == r(max)
        tempvar zbak
        gen double `zbak' = `z'
        if `binary' {
            replace `z' = 0 if e(sample)
            local low ""
            forvalues i = 1/`k' {
                tempvar lo`i'
                local low "`low' `lo`i''"
            }
            fooddem_p `low'
            replace `z' = 1 if e(sample)
            local high ""
            forvalues i = 1/`k' {
                tempvar hi`i'
                local high "`high' `hi`i''"
            }
            fooddem_p `high'
            replace `z' = `zbak'
            forvalues i = 1/`k' {
                local lo : word `i' of `low'
                local hi : word `i' of `high'
                tempvar de
                gen double `de' = (`hi' - `lo') / `lo' if e(sample) & `lo' > 0
                quietly summarize `de', meanonly
                post `mem' ("`z'") ("0-to-1 discrete") (`i') (r(mean)) (r(N))
            }
        }
        else {
            replace `z' = `z' * (1 + `step') if e(sample)
            local new ""
            forvalues i = 1/`k' {
                tempvar n`i'
                local new "`new' `n`i''"
            }
            fooddem_p `new'
            replace `z' = `zbak'
            forvalues i = 1/`k' {
                local bi : word `i' of `base'
                local ni : word `i' of `new'
                tempvar ze
                gen double `ze' = (`ni' - `bi') / (`h' * `bi') if e(sample) & `bi' > 0
                quietly summarize `ze', meanonly
                post `mem' ("`z'") ("elasticity") (`i') (r(mean)) (r(N))
            }
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
