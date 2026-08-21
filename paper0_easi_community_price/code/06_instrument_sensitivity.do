version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"
use "$EASI_DATA/easi_analysis_ready.dta", clear

isid household_id
egen long village_cluster = group(village_id data_year)
local shares "s1 s2 s3 s4 s5 s6"
local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
local quantities "q1 q2 q3 q4 q5 q6"
local core_demos "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
local geography "province_2 province_3 province_4 province_5 province_6 province_7 province_8"
local demos "`core_demos' `geography'"

foreach f in instrument_firststage_diagnostics.csv instrument_sensitivity_summary.csv ///
    instrument_sensitivity_elasticities.csv instrument_sensitivity_regularity.csv {
    capture erase "$EASI_OUT/`f'"
}

* Reuse the converged main estimate only as a common numerical start. Every
* sensitivity specification below is re-estimated on the identical IV sample.
estimates use "$EASI_OUT/selected_gmm_twostep.ster"
tempname warm saved smem
matrix `warm' = e(b)
matrix `saved' = e(b)
tempfile summary allel allreg
postfile `smem' str28 specification str28 excluded_instruments double N ///
    parameters converged J J_df J_p firststage_F firststage_p firststage_R2 ///
    max_abs_b_diff_main using `summary', replace

local specifications "income_log_and_inverse income_log_only income_inverse_only expenditure_exogenous"
local first = 1
local firstreg = 1
foreach spec of local specifications {
    local endogopt "endogeneity(iv)"
    local instopt "instruments(ln_income inv_income)"
    local instlabel "ln_income inv_income"
    if "`spec'" == "income_log_only" {
        local instopt "instruments(ln_income)"
        local instlabel "ln_income"
    }
    if "`spec'" == "income_inverse_only" {
        local instopt "instruments(inv_income)"
        local instlabel "inv_income"
    }
    if "`spec'" == "expenditure_exogenous" {
        local endogopt "endogeneity(none)"
        local instopt ""
        local instlabel "none"
    }

    fooddem if !missing(ln_income, inv_income), model(easi) order(1) ///
        shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
        demographics(`demos') quantities(`quantities') selection(sy) ///
        `endogopt' `instopt' cluster(village_cluster) gmmsteps(2) ///
        from(`warm') iterate(80) tolerance(1e-6)

    local conv = cond(missing(e(converged)), 1, e(converged))
    local jp = cond(e(J_df) > 0, chi2tail(e(J_df), e(J)), .)
    local bdiff = .
    if "`spec'" == "income_log_and_inverse" {
        tempname current
        matrix `current' = e(b)
        mata: st_numscalar("__fd_sensitivity_bdiff", ///
            max(abs(st_matrix("`current'") :- st_matrix("`saved'"))))
        local bdiff = scalar(__fd_sensitivity_bdiff)
        fooddem_firststage using "$EASI_OUT/instrument_firststage_diagnostics.csv", replace
    }
    post `smem' ("`spec'") ("`instlabel'") (e(N)) (e(fooddem_npar)) (`conv') ///
        (e(J)) (e(J_df)) (`jp') (e(fooddem_firststage_F)) ///
        (e(fooddem_firststage_p)) (e(fooddem_firststage_r2)) (`bdiff')

    tempfile oneel
    local oneeldta "`oneel'.dta"
    fooddem_elasticities using "`oneeldta'", replace
    preserve
        use "`oneeldta'", clear
        gen str28 specification = "`spec'"
        order specification
        if `first' save `allel', replace
        else {
            append using `allel'
            save `allel', replace
        }
    restore
    local first = 0

    tempfile onereg
    local oneregdta "`onereg'.dta"
    fooddem_regularity using "`oneregdta'", replace
    preserve
        use "`oneregdta'", clear
        gen str28 specification = "`spec'"
        order specification
        if `firstreg' save `allreg', replace
        else {
            append using `allreg'
            save `allreg', replace
        }
    restore
    local firstreg = 0
}
postclose `smem'

preserve
    use `summary', clear
    export delimited using "$EASI_OUT/instrument_sensitivity_summary.csv", replace
restore
preserve
    use `allel', clear
    sort specification elasticity_type demand_good shock_good
    export delimited using "$EASI_OUT/instrument_sensitivity_elasticities.csv", replace
restore
preserve
    use `allreg', clear
    sort specification diagnostic
    export delimited using "$EASI_OUT/instrument_sensitivity_regularity.csv", replace
restore
