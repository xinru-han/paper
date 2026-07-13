*! Excluded-instrument relevance diagnostics after fooddem 1.0.0  13jul2026
program define fooddem_firststage, rclass
    version 17
    syntax using/, [REPLACE]

    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    local excluded "`e(fooddem_instruments)'"
    if "`excluded'" == "" {
        di as error "the active fooddem estimate has no excluded instruments"
        exit 198
    }
    local depvar "`e(fooddem_expenditure)'"
    local included "`e(fooddem_prices)' `e(fooddem_demographics)' `e(fooddem_selectvars)'"
    local included : list uniq included
    local cluster "`e(fooddem_cluster)'"
    local vceopt "vce(robust)"
    if "`cluster'" != "" local vceopt "vce(cluster `cluster')"

    tempvar touse
    gen byte `touse' = e(sample)
    markout `touse' `depvar' `included' `excluded'
    if "`cluster'" != "" markout `touse' `cluster', strok

    tempname held mem
    tempfile diagnostics
    estimates store `held'
    quietly regress `depvar' `included' `excluded' if `touse', `vceopt'
    local unrestricted_ssr = e(rss)
    local first_r2 = e(r2)
    local first_n = e(N)
    quietly test `excluded'
    local joint_f = r(F)
    local joint_p = r(p)
    local joint_df = r(df)
    local joint_dfr = r(df_r)

    quietly regress `depvar' `included' if `touse'
    local restricted_ssr = e(rss)
    local joint_partial = max(0, (`restricted_ssr' - `unrestricted_ssr') / `restricted_ssr')

    postfile `mem' str28 test str32 instrument double F df_num df_den p_value ///
        partial_R2 firststage_R2 N using `diagnostics', replace
    post `mem' ("excluded_instruments_joint") ("`excluded'") (`joint_f') ///
        (`joint_df') (`joint_dfr') (`joint_p') (`joint_partial') (`first_r2') (`first_n')

    foreach z of local excluded {
        quietly regress `depvar' `included' `excluded' if `touse', `vceopt'
        quietly test `z'
        local cond_f = r(F)
        local cond_p = r(p)
        local cond_df = r(df)
        local cond_dfr = r(df_r)
        local other : list excluded - z
        quietly regress `depvar' `included' `other' if `touse'
        local restricted_ssr = e(rss)
        local partial = max(0, (`restricted_ssr' - `unrestricted_ssr') / `restricted_ssr')
        post `mem' ("instrument_conditional") ("`z'") (`cond_f') (`cond_df') ///
            (`cond_dfr') (`cond_p') (`partial') (`first_r2') (`first_n')
    }
    postclose `mem'

    preserve
        use `diagnostics', clear
        if regexm(lower("`using'"), "[.]dta$") {
            if "`replace'" != "" save "`using'", replace
            else save "`using'"
        }
        else {
            if "`replace'" != "" export delimited using "`using'", replace
            else export delimited using "`using'"
        }
    restore
    estimates restore `held'
    estimates drop `held'

    return scalar joint_F = `joint_f'
    return scalar joint_df = `joint_df'
    return scalar joint_df_r = `joint_dfr'
    return scalar joint_p = `joint_p'
    return scalar joint_partial_R2 = `joint_partial'
    return scalar firststage_R2 = `first_r2'
    return scalar N = `first_n'
end
