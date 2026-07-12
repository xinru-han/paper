*! Two/three-stage income and quality elasticities after fooddem 1.0.0  12jul2026
program define fooddem_income, rclass
    version 17
    syntax using/, INCOME(varname numeric) [VALUES(varlist numeric) ///
        CONTROLS(varlist numeric) ID(varname) STEP(real 0.001) ///
        VALUEmethod(string) CLuster(varname) REPLACE]
    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    local k = e(fooddem_goods)
    if "`values'" != "" {
        local kv : word count `values'
        if `kv' != `k' {
            di as error "values() must contain one commodity expenditure per good"
            exit 198
        }
    }
    if "`valuemethod'" == "" local valuemethod "ppml"
    local valuemethod = lower("`valuemethod'")
    if !inlist("`valuemethod'", "ppml", "logols") {
        di as error "valuemethod() must be ppml or logols"
        exit 198
    }
    if `step' <= 0 | `step' > .1 {
        di as error "step() must be in (0,.1]"
        exit 198
    }
    local h = ln(1 + `step')
    tempvar sample obsid lni invi xbak
    gen byte `sample' = e(sample)
    markout `sample' `income' `controls'
    if "`cluster'" != "" markout `sample' `cluster', strok
    replace `sample' = 0 if `income' <= 0
    local vceopt "vce(robust)"
    if "`cluster'" != "" local vceopt "vce(cluster `cluster')"
    if "`id'" != "" {
        tempvar id_sample_n
        bysort `id': egen long `id_sample_n' = total(`sample')
        quietly count if `sample' & (missing(`id') | `id_sample_n' > 1)
        if r(N) > 0 {
            di as error "id() must uniquely identify the reduced-form estimation sample"
            exit 459
        }
    }
    gen long `obsid' = _n
    gen double `lni' = ln(`income') if `income' > 0
    gen double `invi' = 1 / `income' if `income' > 0

    local base ""
    local xnew ""
    local xlow ""
    forvalues i = 1/`k' {
        tempvar b`i' n`i' l`i'
        local base "`base' `b`i''"
        local xnew "`xnew' `n`i''"
        local xlow "`xlow' `l`i''"
    }
    fooddem_p `base'
    local expvar "`e(fooddem_expenditure)'"
    gen double `xbak' = `expvar'
    replace `expvar' = `expvar' + `h' if `sample'
    fooddem_p `xnew'
    replace `expvar' = `xbak' - `h' if `sample'
    fooddem_p `xlow'
    replace `expvar' = `xbak'
    forvalues i = 1/`k' {
        local bi : word `i' of `base'
        local ni : word `i' of `xnew'
        local li : word `i' of `xlow'
        gen double eta_exp_`i' = 1 + (`ni' - `li') / (2 * `h' * `bi') if `sample' & `bi' > 0
    }

    quietly regress `expvar' `lni' `invi' `controls' if `sample', `vceopt'
    gen double eta_totalexp_income = _b[`lni'] - _b[`invi'] / `income' if e(sample)
    forvalues i = 1/`k' {
        gen double eta_qty_`i' = eta_exp_`i' * eta_totalexp_income if `sample'
        gen double eta_value_`i' = .
        gen double eta_quality_`i' = .
        if "`values'" != "" {
            local vi : word `i' of `values'
            assert `vi' >= 0 if `sample' & !missing(`vi')
            if "`valuemethod'" == "ppml" {
                quietly glm `vi' `lni' `invi' `controls' if `sample' & ///
                    !missing(`vi'), family(poisson) link(log) ///
                    `vceopt' iterate(100)
            }
            else {
                tempvar lnvi
                gen double `lnvi' = ln(`vi') if `vi' > 0
                quietly regress `lnvi' `lni' `invi' `controls' if `sample' & ///
                    `vi' > 0, `vceopt'
            }
            replace eta_value_`i' = _b[`lni'] - _b[`invi'] / `income' if `sample' & `income' > 0
            replace eta_quality_`i' = eta_value_`i' - eta_qty_`i' if `sample' & `income' > 0
        }
    }

    preserve
        if "`id'" == "" {
            gen long fooddem_id = `obsid'
            local id "fooddem_id"
        }
        keep if `sample'
        keep `id' `income' `controls' eta_totalexp_income eta_exp_* eta_qty_* eta_value_* eta_quality_*
        reshape long eta_exp_ eta_qty_ eta_value_ eta_quality_, i(`id') j(good)
        rename eta_exp_ expenditure_elasticity
        rename eta_qty_ income_quantity_elasticity
        rename eta_value_ income_value_elasticity
        rename eta_quality_ income_quality_elasticity
        gen str8 value_method = "`valuemethod'"
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
