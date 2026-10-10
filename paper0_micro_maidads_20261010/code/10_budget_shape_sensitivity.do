version 17
clear all
set more off
set linesize 160
args project_root
if `"`project_root'"'=="" local project_root "/root/data/Paper/食物消费数据/paper0-EASI/micro_maidads_20261010"
capture log close budget_shape
log using "`project_root'/logs/10_budget_shape_sensitivity.log", name(budget_shape) text replace

capture program drop mmshape_export
program define mmshape_export
    version 17
    syntax, MODEL(string) COEFHANDLE(name) VHANDLE(name) COMPHANDLE(name)
    tempname b V
    matrix `b'=e(b)
    matrix `V'=e(V)
    local terms : colnames `b'
    local nterms : word count `terms'
    forvalues j=1/`nterms' {
        local term : word `j' of `terms'
        local estimate=`b'[1,`j']
        local se=sqrt(max(0,`V'[`j',`j']))
        local p=cond(`se'>0,2*normal(-abs(`estimate'/`se')),.)
        post `coefhandle' ("`model'") ("`term'") (`estimate') (`se') (`p') ///
            (`estimate'-invnormal(.975)*`se') (`estimate'+invnormal(.975)*`se') (`se'==0)
        forvalues h=1/`nterms' {
            local other : word `h' of `terms'
            post `vhandle' ("`model'") ("`term'") ("`other'") (`V'[`j',`h'])
        }
    }
    post `comphandle' ("`model'") (e(N)) (e(rank)) (e(N_clust)) ///
        (e(converged)) (e(ll)) (-2*e(ll)+2*e(rank)) ///
        (-2*e(ll)+ln(e(N))*e(rank)) (e(aic)) (e(phi))
end

foreach k in 10 8 {
    use "`project_root'/data/analysis_`k'_firststage.dta", clear
    local out "`project_root'/outputs/budget_shape_`k'"
    capture mkdir "`out'"
    preserve
        import delimited using "`project_root'/outputs/stata_stage1_`k'/model_metadata.csv", ///
            clear varnames(1) stringcols(_all)
        local full_rhs=budget_rhs[1]
        local family_base=real(family_base[1])
        local income_center=real(income_log_center[1])
        local family_levels=family_levels[1]
    restore
    local linear_rhs ""
    local quadratic_terms ""
    foreach term of local full_rhs {
        if regexm("`term'","lninc2$") local quadratic_terms "`quadratic_terms' `term'"
        else local linear_rhs "`linear_rhs' `term'"
    }
    tempname coefficients covariances comparisons tests
    tempfile coeff_file covariance_file comparison_file test_file
    postfile `coefficients' str40 model str40 term double coefficient std_error p_value ///
        ci_low ci_high byte zero_variance using `coeff_file', replace
    postfile `covariances' str40 model str40 row_term str40 column_term double covariance ///
        using `covariance_file', replace
    postfile `comparisons' str40 model long N int parameter_rank long clusters byte converged ///
        double log_likelihood AIC_total BIC_total Stata_AIC_per_observation ///
        dispersion_phi using `comparison_file', replace
    postfile `tests' str40 model str50 test_name int family_type long degrees_freedom ///
        double chi_squared elasticity std_error p_value ci_low ci_high ///
        using `test_file', replace

    estimates use "`project_root'/outputs/stata_stage1_`k'/food_budget_main.ster"
    assert e(N)==3145
    mmshape_export, model(food_budget_main_quadratic) coefhandle(`coefficients') ///
        vhandle(`covariances') comphandle(`comparisons')
    noisily test `quadratic_terms'
    post `tests' ("food_budget_main_quadratic") ("all_quadratic_income_terms_zero") ///
        (.) (r(df)) (r(chi2)) (.) (.) (r(p)) (.) (.)

    glm food_budget_pc_month `linear_rhs' if fs_sample_main, family(gamma) link(log) ///
        vce(cluster village_cluster) nolog iterate(100)
    assert e(converged)==1
    assert e(N)==3145
    mmshape_export, model(food_budget_loglinear) coefhandle(`coefficients') ///
        vhandle(`covariances') comphandle(`comparisons')
    estimates save "`out'/food_budget_loglinear.ster", replace
    predict double food_budget_hat_loglinear if fs_valid, mu
    generate double food_income_elast_loglinear=_b[fs_lninc]
    foreach f of local family_levels {
        local expression "fs_lninc"
        if `f'!=`family_base' {
            replace food_income_elast_loglinear=food_income_elast_loglinear+ ///
                fs_family_`f'*_b[fs_family_`f'_lninc]
            local expression "fs_lninc+fs_family_`f'_lninc"
        }
        quietly lincom `expression'
        post `tests' ("food_budget_loglinear") ("family_income_elasticity_zero") ///
            (`f') (.) (.) (r(estimate)) (r(se)) (r(p)) (r(lb)) (r(ub))
    }
    postclose `coefficients'
    postclose `covariances'
    postclose `comparisons'
    postclose `tests'
    export delimited using "`out'/household_predictions.csv", nolabel replace
    preserve
        use `coeff_file', clear
        generate int variant=`k'
        generate str40 param=term
        export delimited using "`out'/coefficients.csv", replace
        use `covariance_file', clear
        export delimited using "`out'/covariance.csv", replace
        use `comparison_file', clear
        generate strL comparison_scope="same-sample Gamma GLM working likelihood; cluster Wald is the primary quadratic-shape test"
        export delimited using "`out'/modelcomparison.csv", replace
        use `test_file', clear
        export delimited using "`out'/tests.csv", replace
        clear
        set obs 1
        generate double income_log_center=`income_center'
        generate int family_base=`family_base'
        generate strL family_levels="`family_levels'"
        generate strL budget_rhs="`linear_rhs'"
        generate strL quadratic_terms="`quadratic_terms'"
        generate strL income_unit="nominal yuan per person per month"
        generate strL covariance_scope="first-stage village-year cluster sandwich only; no propagated final-elasticity inference"
        generate strL selection_scope="shape diagnostic; no imposed positive income slope and no automatic change of primary model"
        export delimited using "`out'/model_metadata.csv", replace
    restore
}
log close budget_shape
exit, clear
