version 17
clear all
set more off
set linesize 160

args project_root
if `"`project_root'"' == "" local project_root "/root/data/Paper/食物消费数据/paper0-EASI/micro_maidads_20261010"
capture mkdir "`project_root'/outputs"
capture mkdir "`project_root'/logs"
capture log close mma_stage1
log using "`project_root'/logs/02_first_stage.log", name(mma_stage1) text replace

capture program drop mma_post_estimate
program define mma_post_estimate
    version 17
    syntax, MODEL(string) METHOD(string) SAMPLE(string) COEFHANDLE(name) ///
        VHANDLE(name) STATUSHANDLE(name) [FALLBACK(string)]
    tempname b V
    matrix `b' = e(b)
    matrix `V' = e(V)
    local terms : colnames `b'
    local nterms : word count `terms'
    forvalues j = 1/`nterms' {
        local term : word `j' of `terms'
        local estimate = `b'[1,`j']
        local se = sqrt(max(0, `V'[`j',`j']))
        local p = cond(`se'>0, 2*normal(-abs(`estimate'/`se')), .)
        local ci_lo = `estimate' - invnormal(.975)*`se'
        local ci_hi = `estimate' + invnormal(.975)*`se'
        post `coefhandle' ("`model'") ("`method'") ("`term'") ///
            (`estimate') (`se') (`p') (`ci_lo') (`ci_hi') (`se'==0)
        forvalues h = 1/`nterms' {
            local other : word `h' of `terms'
            post `vhandle' ("`model'") ("`term'") ("`other'") (`V'[`j',`h'])
        }
    }
    local N = e(N)
    local rank = e(rank)
    local converged = e(converged)
    local clusters = e(N_clust)
    local ll = e(ll)
    post `statushandle' ("`model'") ("`method'") ("`sample'") ///
        ("`fallback'") (0) (`N') (`rank') (`converged') (`clusters') (`ll')
end

foreach k in 8 10 {
    use "`project_root'/data/analysis_`k'.dta", clear
    capture mkdir "`project_root'/outputs/stata_stage1_`k'"
    local out "`project_root'/outputs/stata_stage1_`k'"
    assert income_pc_month > 0 if sample_model
    assert food_budget_pc_month > 0 if sample_model
    assert food_price_index > 0 if sample_model
    assert hhsize > 0 if sample_model

    generate double fs_log_income_nominal = ln(income_pc_month) if income_pc_month>0
    generate double fs_log_income_fooddeflated = ln(income_pc_month/food_price_index) ///
        if income_pc_month>0 & food_price_index>0
    generate double fs_ln_hhsize = ln(hhsize) if hhsize>0
    generate double fs_ln_foodprice = ln(food_price_index) if food_price_index>0
    generate byte fs_valid = !missing(fs_log_income_nominal,fs_ln_hhsize, ///
        fs_ln_foodprice,child_ratio,elderly_ratio,family_type,village_cluster) ///
        & family_type>=0 & village_cluster>0 & food_budget_pc_month>=0 ///
        & food_budget_pc_month<. & !missing(province_id)
    forvalues j = 1/`k' {
        replace fs_valid = 0 if missing(p`j',q`j') | p`j'<=0 | q`j'<0
    }
    generate byte fs_sample_raw = fs_valid & food_budget_pc_month>0
    generate byte fs_sample_main = fs_sample_raw & sample_model==1
    quietly count if fs_sample_main
    assert r(N)>500
    quietly centile income_pc_month if fs_sample_main, centile(1 99)
    local income_p01 = r(c_1)
    local income_p99 = r(c_2)
    generate byte fs_income_supported = inrange(income_pc_month,`income_p01',`income_p99') ///
        if !missing(income_pc_month)
    generate byte fs_sample_income_trim = fs_sample_main & fs_income_supported==1
    capture confirm variable income_percentile_tail
    if !_rc replace fs_income_supported = income_percentile_tail==0 if income_pc_month<.
    capture confirm variable sample_income_supported
    if !_rc replace fs_sample_income_trim = fs_sample_main & sample_income_supported==1
    quietly summarize fs_log_income_nominal if fs_sample_main, meanonly
    local income_center = r(mean)
    quietly summarize fs_log_income_fooddeflated if fs_sample_main, meanonly
    local real_center = r(mean)
    generate double fs_lninc = fs_log_income_nominal - `income_center'
    generate double fs_lninc2 = fs_lninc^2
    generate double fr_lninc = fs_log_income_fooddeflated - `real_center'
    generate double fr_lninc2 = fr_lninc^2
    quietly levelsof family_type if fs_sample_main, local(ftypes)
    local family_base : word 1 of `ftypes'
    foreach f of local ftypes {
        if `f'==1 local family_base = 1
    }
    local family_rhs ""
    local family_real_rhs ""
    foreach f of local ftypes {
        if `f' != `family_base' {
            generate byte fs_family_`f' = family_type==`f' if family_type<.
            generate double fs_family_`f'_lninc = fs_family_`f'*fs_lninc
            generate double fs_family_`f'_lninc2 = fs_family_`f'*fs_lninc2
            generate double fr_family_`f'_lninc = fs_family_`f'*fr_lninc
            generate double fr_family_`f'_lninc2 = fs_family_`f'*fr_lninc2
            local family_rhs "`family_rhs' fs_family_`f' fs_family_`f'_lninc fs_family_`f'_lninc2"
            local family_real_rhs "`family_real_rhs' fs_family_`f' fr_family_`f'_lninc fr_family_`f'_lninc2"
        }
    }
    egen long fs_province = group(province_id)
    quietly levelsof fs_province if fs_sample_main, local(provinces)
    local province_base : word 1 of `provinces'
    local province_rhs ""
    foreach p of local provinces {
        if `p' != `province_base' {
            generate byte fs_prov_`p' = fs_province==`p' if fs_province<.
            local province_rhs "`province_rhs' fs_prov_`p'"
        }
    }
    local relative_prices ""
    local last = `k'-1
    forvalues j = 1/`last' {
        generate double fs_relp_`j' = ln(p`j'/p`k') if p`j'>0 & p`k'>0
        local relative_prices "`relative_prices' fs_relp_`j'"
    }
    local controls "fs_ln_hhsize child_ratio elderly_ratio fs_ln_foodprice `province_rhs'"
    local budget_rhs "fs_lninc fs_lninc2 `family_rhs' `controls'"
    local real_rhs "fr_lninc fr_lninc2 `family_real_rhs' `controls'"
    local participation_rhs "`budget_rhs' `relative_prices'"
    generate byte fs_constant = 1

    tempname coeffmem vmem statusmem tests
    tempfile coefficients covariance status income_tests
    postfile `coeffmem' str40 model str20 method str40 term double coefficient ///
        std_error p_value ci_low ci_high byte zero_variance using `coefficients', replace
    postfile `vmem' str40 model str40 row_term str40 column_term double covariance ///
        using `covariance', replace
    postfile `statusmem' str40 model str20 method str32 sample str100 fallback ///
        int return_code long N int rank byte converged long clusters double log_likelihood ///
        using `status', replace
    postfile `tests' str40 model int family_type double evaluation_income_pc_month ///
        elasticity std_error p_value ci_low ci_high using `income_tests', replace

    foreach specification in main raw fooddeflated income_trim {
        local rhs "`budget_rhs'"
        local sample "fs_sample_main"
        if "`specification'" == "raw" local sample "fs_sample_raw"
        if "`specification'" == "income_trim" local sample "fs_sample_income_trim"
        if "`specification'" == "fooddeflated" local rhs "`real_rhs'"
        noisily display "Food-budget first stage: `k' goods / `specification'"
        capture noisily glm food_budget_pc_month `rhs' if `sample', ///
            family(gamma) link(log) vce(cluster village_cluster) nolog iterate(100)
        local rc = _rc
        if `rc' {
            post `statusmem' ("food_budget_`specification'") ("gamma_log") ///
                ("`sample'") ("estimation_failed") (`rc') (.) (.) (0) (.) (.)
            if "`specification'" == "main" exit `rc'
            continue
        }
        mma_post_estimate, model(food_budget_`specification') method(gamma_log) ///
            sample(`sample') coefhandle(`coeffmem') vhandle(`vmem') statushandle(`statusmem')
        estimates save "`out'/food_budget_`specification'.ster", replace
        predict double food_budget_hat_`specification' if fs_valid, mu
        local income_term "fs_lninc"
        local square_term "fs_lninc2"
        local prefix "fs"
        local center = `income_center'
        if "`specification'" == "fooddeflated" {
            local income_term "fr_lninc"
            local square_term "fr_lninc2"
            local prefix "fr"
            local center = `real_center'
        }
        generate double food_income_elast_`specification' = ///
            _b[`income_term']+2*_b[`square_term']*`income_term'
        foreach f of local ftypes {
            if `f' != `family_base' {
                replace food_income_elast_`specification' = food_income_elast_`specification' + ///
                    fs_family_`f'*(_b[`prefix'_family_`f'_lninc] + ///
                    2*_b[`prefix'_family_`f'_lninc2]*`income_term')
            }
        }
        foreach f of local ftypes {
            quietly summarize income_pc_month if `sample' & family_type==`f', meanonly
            local income_mean = r(mean)
            local x = ln(`income_mean')-`center'
            if "`specification'" == "fooddeflated" {
                quietly summarize fs_ln_foodprice if `sample' & family_type==`f', meanonly
                local x = `x'-r(mean)
            }
            local expression "`income_term' + `=2*`x''*`square_term'"
            if `f' != `family_base' local expression "`expression' + `prefix'_family_`f'_lninc + `=2*`x''*`prefix'_family_`f'_lninc2"
            quietly lincom `expression'
            post `tests' ("food_budget_`specification'") (`f') (`income_mean') ///
                (r(estimate)) (r(se)) (r(p)) (r(lb)) (r(ub))
        }
        if "`specification'" == "main" {
            generate double food_income_elasticity = food_income_elast_main
        }
    }

    * The probit correction is an observed participation component. It does
    * not replace the latent MAIDADS expenditure function or its Slutsky matrix.
    forvalues j = 1/`k' {
        generate byte positive_q`j' = q`j'>0 if !missing(q`j')
        quietly count if fs_sample_main
        local expected_N = r(N)
        quietly count if fs_sample_main & positive_q`j'==1
        local positive_N = r(N)
        generate double participation_p`j' = .
        generate double participation_xb`j' = .
        if inlist(`positive_N',0,`expected_N') {
            replace participation_p`j' = (`positive_N'>0) if fs_valid
            post `statusmem' ("participation_g`j'") ("constant_probability") ///
                ("fs_sample_main") ("no_outcome_variation") (0) (`expected_N') ///
                (0) (1) (.) (.)
            continue
        }
        noisily display "Participation first stage: `k' goods / group `j'"
        capture noisily probit positive_q`j' `participation_rhs' if fs_sample_main, ///
            vce(cluster village_cluster) nolog iterate(100)
        local rc = _rc
        local fallback ""
        if !`rc' {
            if e(converged)!=1 | e(N)!=`expected_N' local rc = 430
        }
        if `rc' {
            local fallback "intercept_only_after_separation_nonconvergence_or_sample_loss"
            noisily display as text "Group `j': `fallback'"
            capture noisily probit positive_q`j' if fs_sample_main, ///
                vce(cluster village_cluster) nolog iterate(100)
            local rc = _rc
        }
        if `rc' {
            replace participation_p`j' = `positive_N'/`expected_N' if fs_valid
            replace participation_xb`j' = invnormal(participation_p`j') if fs_valid
            post `statusmem' ("participation_g`j'") ("sample_probability") ///
                ("fs_sample_main") ("probit_failed_empirical_prevalence") (`rc') ///
                (`expected_N') (0) (0) (.) (.)
            continue
        }
        mma_post_estimate, model(participation_g`j') method(probit) sample(fs_sample_main) ///
            coefhandle(`coeffmem') vhandle(`vmem') statushandle(`statusmem') fallback("`fallback'")
        estimates save "`out'/participation_g`j'.ster", replace
        tempvar pr xb
        predict double `pr' if fs_valid, pr
        predict double `xb' if fs_valid, xb
        replace participation_p`j' = `pr' if fs_valid
        replace participation_xb`j' = `xb' if fs_valid
        drop `pr' `xb'
        assert inrange(participation_p`j',0,1) if fs_valid
    }
    postclose `coeffmem'
    postclose `vmem'
    postclose `statusmem'
    postclose `tests'
    save "`project_root'/data/analysis_`k'_firststage.dta", replace
    export delimited using "`out'/household_predictions.csv", nolabel replace
    preserve
        use `coefficients', clear
        generate int variant = `k'
        generate int good = 0
        replace good = real(subinstr(model,"participation_g","",.)) ///
            if strpos(model,"participation_g")==1
        generate str40 param = term
        export delimited using "`out'/coefficients.csv", replace
        use `covariance', clear
        export delimited using "`out'/covariance.csv", replace
        use `status', clear
        export delimited using "`out'/estimation_status.csv", replace
        use `income_tests', clear
        export delimited using "`out'/income_elasticity_tests.csv", replace
        clear
        set obs 1
        generate int number_food_groups = `k'
        generate double income_log_center = `income_center'
        generate double fooddeflated_income_log_center = `real_center'
        generate double empirical_income_p01 = `income_p01'
        generate double empirical_income_p99 = `income_p99'
        generate int family_base = `family_base'
        generate int province_base = `province_base'
        generate strL family_levels = "`ftypes'"
        generate strL province_levels = "`provinces'"
        generate strL budget_rhs = "`budget_rhs'"
        generate strL fooddeflated_budget_rhs = "`real_rhs'"
        generate strL participation_rhs = "`participation_rhs'"
        generate strL baseline_income_unit = "nominal yuan per person per month"
        generate strL relative_price_definition = "fs_relp_j=log(p_j/p_K), raw community basket price levels"
        generate strL family_zero_definition = "ambiguous or incomplete roster; retained as an unknown-type dummy"
        generate strL price_sensitivity = "common food-price deflation is purchasing-power sensitivity, not a comprehensive CPI"
        generate strL cluster_definition = "village by survey year"
        generate strL covariance_scope = "first-stage sandwich only; not propagated MAIDADS or two-stage uncertainty"
        generate strL income_trim_definition = "sample_income_supported from the data builder when available; otherwise Stata percentile interpolation"
        export delimited using "`out'/model_metadata.csv", replace
    restore
}

log close mma_stage1
exit, clear
