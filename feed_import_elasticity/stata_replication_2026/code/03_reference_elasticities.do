* Utility do-file. Requires an active fooddem estimate and global REFOUT.
version 17
set more off

local k = e(fooddem_goods)
local prices "`e(fooddem_prices)'"
local expvar "`e(fooddem_expenditure)'"
local demos "`e(fooddem_demographics)'"
local h = ln(1.001)

preserve
    tempvar sample
    capture gen byte `sample' = e(sample)
    if _rc gen byte `sample' = 1
    quietly count if `sample'
    if r(N) == 0 replace `sample' = 1

    foreach z of local prices {
        quietly summarize `z' if `sample', meanonly
        replace `z' = r(mean) if `sample'
    }
    quietly summarize `expvar' if `sample', meanonly
    replace `expvar' = r(mean) if `sample'
    foreach z of local demos {
        quietly summarize `z' if `sample', meanonly
        replace `z' = r(mean) if `sample'
    }

    local base ""
    forvalues i = 1/`k' {
        tempvar b`i'
        local base "`base' `b`i''"
    }
    quietly fooddem_p `base', latent

    tempvar xbak
    gen double `xbak' = `expvar'
    replace `expvar' = `xbak' + `h' if `sample'
    local xhi ""
    local xlo ""
    forvalues i = 1/`k' {
        tempvar xh`i' xl`i'
        local xhi "`xhi' `xh`i''"
        local xlo "`xlo' `xl`i''"
    }
    quietly fooddem_p `xhi', latent
    replace `expvar' = `xbak' - `h' if `sample'
    quietly fooddem_p `xlo', latent
    replace `expvar' = `xbak' if `sample'

    local etas ""
    tempname mem
    tempfile result
    postfile `mem' str12 model int order str14 elasticity_type int demand_good ///
        shock_good double reference_share elasticity using `result', replace
    forvalues i = 1/`k' {
        local bi : word `i' of `base'
        local hi : word `i' of `xhi'
        local lo : word `i' of `xlo'
        tempvar eta`i'
        gen double `eta`i'' = 1 + (`hi' - `lo') / (2 * `h' * `bi') if `sample'
        local etas "`etas' `eta`i''"
        quietly summarize `bi' if `sample', meanonly
        local wi = r(mean)
        quietly summarize `eta`i'' if `sample', meanonly
        post `mem' ("`e(fooddem_model)'") (`=e(fooddem_order)') ///
            ("expenditure") (`i') (0) (`wi') (r(mean))
    }

    forvalues j = 1/`k' {
        local pj : word `j' of `prices'
        tempvar pbak
        gen double `pbak' = `pj'
        replace `pj' = `pbak' + `h' if `sample'
        local phi ""
        local plo ""
        forvalues i = 1/`k' {
            tempvar ph`j'_`i' pl`j'_`i'
            local phi "`phi' `ph`j'_`i''"
            local plo "`plo' `pl`j'_`i''"
        }
        quietly fooddem_p `phi', latent
        replace `pj' = `pbak' - `h' if `sample'
        quietly fooddem_p `plo', latent
        replace `pj' = `pbak' if `sample'
        forvalues i = 1/`k' {
            local bi : word `i' of `base'
            local bj : word `j' of `base'
            local hi : word `i' of `phi'
            local lo : word `i' of `plo'
            local etai : word `i' of `etas'
            tempvar em eh
            gen double `em' = (`hi' - `lo') / (2 * `h' * `bi') - (`i' == `j') if `sample'
            gen double `eh' = `em' + `etai' * `bj' if `sample'
            quietly summarize `bi' if `sample', meanonly
            local wi = r(mean)
            quietly summarize `em' if `sample', meanonly
            local emean = r(mean)
            quietly summarize `eh' if `sample', meanonly
            local hmean = r(mean)
            post `mem' ("`e(fooddem_model)'") (`=e(fooddem_order)') ///
                ("marshallian") (`i') (`j') (`wi') (`emean')
            post `mem' ("`e(fooddem_model)'") (`=e(fooddem_order)') ///
                ("hicksian") (`i') (`j') (`wi') (`hmean')
        }
    }
    postclose `mem'
    use `result', clear
    export delimited using "$REFOUT", replace
restore
