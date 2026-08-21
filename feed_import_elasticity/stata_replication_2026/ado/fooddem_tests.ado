*! Specification tests after fooddem 1.0.0  12jul2026
program define fooddem_tests, rclass
    version 17
    syntax using/, [DEMographics(varlist numeric) REPLACE]
    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    local model "`e(fooddem_model)'"
    local neq = e(fooddem_goods) - 1
    local order = e(fooddem_order)
    local alldemos "`e(fooddem_demographics)'"
    if "`demographics'" == "" local demographics "`alldemos'"

    tempname mem
    tempfile results
    postfile `mem' str40 test double statistic df p_value using `results', replace

    local tests ""
    if "`model'" == "quaids" {
        forvalues i = 1/`neq' {
            local tests "`tests' [l`i']_cons"
        }
    }
    else if "`model'" == "easi" & `order' > 1 {
        forvalues i = 1/`neq' {
            local tests "`tests' [b`i'_`order']_cons"
        }
    }
    if "`tests'" != "" {
        quietly test `tests'
        local stat = cond(missing(r(chi2)), r(F), r(chi2))
        local df = cond(missing(r(df)), r(df_r), r(df))
        post `mem' ("highest_Engel_order_joint_zero") (`stat') (`df') (r(p))
    }

    local tests ""
    foreach z of local demographics {
        local d : list posof "`z'" in alldemos
        if `d' == 0 {
            di as error "`z' was not included in demographics() at estimation"
            exit 198
        }
        forvalues i = 1/`neq' {
            local tests "`tests' [t`i'_`d']_cons"
        }
    }
    if "`tests'" != "" {
        quietly test `tests'
        local stat = cond(missing(r(chi2)), r(F), r(chi2))
        local df = cond(missing(r(df)), r(df_r), r(df))
        post `mem' ("demographics_joint_zero") (`stat') (`df') (r(p))
    }

    if "`demographics'" != "`alldemos'" & "`alldemos'" != "" {
        local tests ""
        local d = 0
        foreach z of local alldemos {
            local ++d
            forvalues i = 1/`neq' {
                local tests "`tests' [t`i'_`d']_cons"
            }
        }
        quietly test `tests'
        local stat = cond(missing(r(chi2)), r(F), r(chi2))
        local df = cond(missing(r(df)), r(df_r), r(df))
        post `mem' ("all_share_shifters_joint_zero") (`stat') (`df') (r(p))
    }

    if "`e(fooddem_cf)'" != "" {
        local tests ""
        forvalues i = 1/`neq' {
            local tests "`tests' [r`i']_cons"
        }
        quietly test `tests'
        local stat = cond(missing(r(chi2)), r(F), r(chi2))
        local df = cond(missing(r(df)), r(df_r), r(df))
        post `mem' ("expenditure_exogeneity") (`stat') (`df') (r(p))
    }

    if "`e(fooddem_selection)'" == "sy" {
        local active "`e(fooddem_syactive)'"
        local tests ""
        forvalues i = 1/`neq' {
            local ai : word `i' of `active'
            if `ai' local tests "`tests' [d`i']_cons"
        }
        if "`tests'" != "" {
            quietly test `tests'
            local stat = cond(missing(r(chi2)), r(F), r(chi2))
            local df = cond(missing(r(df)), r(df_r), r(df))
            post `mem' ("Shonkwiler_Yen_terms_joint_zero") (`stat') (`df') (r(p))
        }
    }

    if "`e(fooddem_precommitment)'" != "" {
        local tests ""
        forvalues i = 1/`=e(fooddem_goods)' {
            local tests "`tests' [c`i']_cons"
        }
        quietly test `tests'
        local stat = cond(missing(r(chi2)), r(F), r(chi2))
        local df = cond(missing(r(df)), r(df_r), r(df))
        post `mem' ("precommitments_joint_zero") (`stat') (`df') (r(p))
    }

    if "`e(fooddem_estimator)'" == "gmm" {
        local jlabel "GMM_overidentification_identity_weight"
        local jp = .
        if e(fooddem_gmmsteps) == 2 {
            local jlabel "Hansen_overidentification"
            local jp = chi2tail(e(J_df), e(J))
        }
        post `mem' ("`jlabel'") (e(J)) (e(J_df)) (`jp')
    }
    if !missing(e(fooddem_firststage_F)) {
        post `mem' ("excluded_instruments_first_stage") (e(fooddem_firststage_F)) (.) (e(fooddem_firststage_p))
    }
    post `mem' ("theory_restrictions_imposed") (1) (.) (.)
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
