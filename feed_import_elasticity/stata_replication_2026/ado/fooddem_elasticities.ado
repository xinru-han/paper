*! Numerical demand elasticities after fooddem 1.2.0  13jul2026
program define fooddem_elasticities, rclass
    version 17
    syntax using/, [STEP(real 0.001) MARGIN(string) MINShare(real 0) ///
        SAMPLE(varname numeric) REPLACE]
    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    if `step' <= 0 | `step' > .1 {
        di as error "step() must be in (0,.1]"
        exit 198
    }
    if `minshare' < 0 | `minshare' >= 1 {
        di as error "minshare() must be in [0,1)"
        exit 198
    }
    local margin = lower("`margin'")
    if "`margin'" == "" local margin "unconditional"
    if !inlist("`margin'", "unconditional", "intensive", "latent") {
        di as error "margin() must be unconditional, intensive, or latent"
        exit 198
    }
    local predopt ""
    if "`margin'" == "intensive" local predopt ", holdselection"
    if "`margin'" == "latent" local predopt ", latent"
    local k = e(fooddem_goods)
    local shares "`e(fooddem_shares)'"
    local prices "`e(fooddem_prices)'"
    local expvar "`e(fooddem_expenditure)'"
    local h = ln(1 + `step')
    tempname mem
    tempfile results
    postfile `mem' str14 margin str24 elasticity_type int demand_good int shock_good ///
        double elasticity aggregate_elasticity trimmed_aggregate trimmed_mean std_dev p10 p50 p90 ///
        negative_rate near_zero_rate min max n_valid support_rate min_share_floor ///
        using `results', replace

    local base ""
    forvalues i = 1/`k' {
        tempvar b`i'
        local base "`base' `b`i''"
    }
    if "`margin'" == "latent" {
        fooddem_p `base', latent
    }
    else {
        fooddem_p `base'
    }

    * A demand-system elasticity is defined only on one common interior support.
    * Equation-specific deletion would compare goods on different households and
    * can manufacture asymmetry when another fitted share is nonpositive.
    tempvar support
    gen byte `support' = e(sample)
    forvalues i = 1/`k' {
        local bi : word `i' of `base'
        replace `support' = 0 if missing(`bi') | `bi' <= `minshare'
    }
    if "`sample'" != "" {
        replace `support' = 0 if missing(`sample') | `sample' == 0
    }
    quietly summarize `support' if e(sample), meanonly
    local support_rate = r(mean)

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
    fooddem_p `xnew' `predopt'
    replace `expvar' = `xbak' - `h' if e(sample)
    fooddem_p `xlow' `predopt'
    replace `expvar' = `xbak'
    local explist ""
    forvalues i = 1/`k' {
        local bi : word `i' of `base'
        local ni : word `i' of `xnew'
        local li : word `i' of `xlow'
        tempvar ex`i'
        gen double `ex`i'' = 1 + (`ni' - `li') / (2 * `h' * `bi') ///
            if e(sample) & `support'
        tempvar qw trimok neg near
        local pi : word `i' of `prices'
        gen double `qw' = `bi' * exp(`expvar' - `pi') if e(sample) & `support'
        quietly summarize `ex`i'', detail
        local emean = r(mean)
        local esd = r(sd)
        local ep1 = r(p1)
        local ep10 = r(p10)
        local ep50 = r(p50)
        local ep90 = r(p90)
        local ep99 = r(p99)
        local emin = r(min)
        local emax = r(max)
        local en = r(N)
        gen byte `trimok' = inrange(`ex`i'', `ep1', `ep99') if !missing(`ex`i'')
        quietly summarize `ex`i'' if `trimok'
        local etrim = r(mean)
        quietly summarize `ex`i'' [aw=`qw'] if `trimok' & `qw' > 0
        local eaggtrim = r(mean)
        quietly summarize `ex`i'' [aw=`qw'] if `qw' > 0
        local eagg = r(mean)
        gen byte `neg' = `ex`i'' < 0 if !missing(`ex`i'')
        quietly summarize `neg'
        local eneg = r(mean)
        gen byte `near' = abs(`ex`i'') < .05 if !missing(`ex`i'')
        quietly summarize `near'
        local enear = r(mean)
        post `mem' ("`margin'") ("expenditure") (`i') (0) (`emean') (`eagg') ///
            (`eaggtrim') (`etrim') ///
            (`esd') (`ep10') (`ep50') (`ep90') (`eneg') (`enear') ///
            (`emin') (`emax') (`en') (`support_rate') (`minshare')
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
        fooddem_p `pnew' `predopt'
        replace `pj' = `pbak' - `h' if e(sample)
        fooddem_p `plow' `predopt'
        replace `pj' = `pbak'
        forvalues i = 1/`k' {
            local bi : word `i' of `base'
            local ni : word `i' of `pnew'
            local li : word `i' of `plow'
            local ei : word `i' of `explist'
            local bj : word `j' of `base'
            tempvar em eh qw trimok neg near
            gen double `em' = (`ni' - `li') / (2 * `h' * `bi') - (`i' == `j') ///
                if e(sample) & `support'
            gen double `eh' = `em' + `ei' * `bj' if e(sample) & `support'
            local pi : word `i' of `prices'
            gen double `qw' = `bi' * exp(`expvar' - `pi') if e(sample) & `support'
            quietly summarize `em', detail
            local emean = r(mean)
            local esd = r(sd)
            local ep1 = r(p1)
            local ep10 = r(p10)
            local ep50 = r(p50)
            local ep90 = r(p90)
            local ep99 = r(p99)
            local emin = r(min)
            local emax = r(max)
            local en = r(N)
            gen byte `trimok' = inrange(`em', `ep1', `ep99') if !missing(`em')
            quietly summarize `em' if `trimok'
            local etrim = r(mean)
            quietly summarize `em' [aw=`qw'] if `trimok' & `qw' > 0
            local eaggtrim = r(mean)
            quietly summarize `em' [aw=`qw'] if `qw' > 0
            local eagg = r(mean)
            gen byte `neg' = `em' < 0 if !missing(`em')
            quietly summarize `neg'
            local eneg = r(mean)
            gen byte `near' = abs(`em') < .05 if !missing(`em')
            quietly summarize `near'
            local enear = r(mean)
            post `mem' ("`margin'") ("marshallian") (`i') (`j') (`emean') (`eagg') ///
                (`eaggtrim') (`etrim') ///
                (`esd') (`ep10') (`ep50') (`ep90') (`eneg') (`enear') ///
                (`emin') (`emax') (`en') (`support_rate') (`minshare')
            drop `trimok' `neg' `near'
            quietly summarize `eh', detail
            local emean = r(mean)
            local esd = r(sd)
            local ep1 = r(p1)
            local ep10 = r(p10)
            local ep50 = r(p50)
            local ep90 = r(p90)
            local ep99 = r(p99)
            local emin = r(min)
            local emax = r(max)
            local en = r(N)
            gen byte `trimok' = inrange(`eh', `ep1', `ep99') if !missing(`eh')
            quietly summarize `eh' if `trimok'
            local etrim = r(mean)
            quietly summarize `eh' [aw=`qw'] if `trimok' & `qw' > 0
            local eaggtrim = r(mean)
            quietly summarize `eh' [aw=`qw'] if `qw' > 0
            local eagg = r(mean)
            gen byte `neg' = `eh' < 0 if !missing(`eh')
            quietly summarize `neg'
            local eneg = r(mean)
            gen byte `near' = abs(`eh') < .05 if !missing(`eh')
            quietly summarize `near'
            local enear = r(mean)
            post `mem' ("`margin'") ("hicksian") (`i') (`j') (`emean') (`eagg') ///
                (`eaggtrim') (`etrim') ///
                (`esd') (`ep10') (`ep50') (`ep90') (`eneg') (`enear') ///
                (`emin') (`emax') (`en') (`support_rate') (`minshare')
        }
    }
    * The final finite-difference call was evaluated at a lower price. Restore
    * centered model variables and active SY probabilities at the baseline data.
    local reset ""
    forvalues i = 1/`k' {
        tempvar reset`i'
        local reset "`reset' `reset`i''"
    }
    quietly fooddem_p `reset' `predopt'
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
