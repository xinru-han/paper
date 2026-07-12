version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"
use "$EASI_DATA/easi_analysis_ready.dta", clear

isid household_id
egen long village_cluster = group(village_id data_year)

local shares "s1 s2 s3 s4 s5 s6"
local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
local quantities "q1 q2 q3 q4 q5 q6"
local purchasevalues "purchase_value1 purchase_value2 purchase_value3 purchase_value4 purchase_value5 purchase_value6"
local core_demos "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
* Survey wave is exactly determined by the province groups in this repeated
* cross-section, so province fixed effects and year_2 cannot both be identified.
local geography "province_2 province_3 province_4 province_5 province_6 province_7 province_8"
local demos "`core_demos' `geography'"
local excluded "ln_income inv_income"

* These files are deleted first so a failed run cannot be mistaken for fresh
* output from the current analysis data.
foreach f in model_selection_gmm_onestep.csv selected_model_parameters_gmm_onestep.csv ///
    selected_model_parameters_gmm_twostep.csv selected_model_summary.csv ///
    selected_model_tests.csv selected_model_elasticities.csv ///
    selected_model_regularity.csv selected_model_demographic_effects.csv ///
    fitted_share_diagnostics.csv income_elasticity_summary.csv ///
    income_elasticity_by_decile.csv income_elasticity_by_demographics.csv ///
    geasi_robustness_status.csv geasi_parameters.csv geasi_precommitments.csv geasi_tests.csv ///
    model_selection_nlsur_cf.csv selected_nlsur_parameters.csv ///
    selected_nlsur_tests.csv selected_nlsur_elasticities.csv ///
    selected_nlsur_regularity.csv {
    capture erase "$EASI_OUT/`f'"
}
foreach f in selected_gmm_twostep.ster geasi_robustness.ster easi_sy3sls.ster ///
    selected_nlsur_cf.ster income_elasticity_distribution.dta {
    capture erase "$EASI_OUT/`f'"
}

* Functional-form selection uses the same complete sample, household
* demographics, community prices, income instruments, and village clustering
* for every candidate. Identity-weight one-step GMM is used for selection;
* the preferred specification is re-estimated efficiently below.
fooddem_select using "$EASI_OUT/model_selection_gmm_onestep.csv", ///
    shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
    maxorder(3) demographics(`demos') quantities(`quantities') selection(sy) ///
    endogeneity(iv) instruments(`excluded') ///
    cluster(village_cluster) gmmsteps(1) iterate(60) tolerance(1e-5) replace

local best_model "`r(preferred_model)'"
local best_order = r(preferred_order)
local best_estimate "`r(preferred_estimate)'"
local best_easi_order = r(preferred_easi_order)
local best_easi_estimate "`r(preferred_easi_estimate)'"

estimates restore `best_easi_estimate'
estimates store fd_easi_gmm_for_geasi
estimates restore `best_estimate'
estimates store fd_selected_gmm1
fooddem_export using "$EASI_OUT/selected_model_parameters_gmm_onestep.csv", ///
    label("`best_model'_order`best_order'_gmm_onestep") replace

* Warm-start the efficient two-step estimator at the converged one-step
* solution. This preserves the model-selection sample and restrictions.
tempname gmmwarm
matrix `gmmwarm' = e(b)
fooddem, model(`best_model') order(`best_order') shares(`shares') ///
    prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
    demographics(`demos') quantities(`quantities') selection(sy) ///
    endogeneity(iv) instruments(`excluded') ///
    cluster(village_cluster) gmmsteps(2) from(`gmmwarm') ///
    iterate(80) tolerance(1e-6)
estimates store fd_selected_gmm2
estimates save "$EASI_OUT/selected_gmm_twostep.ster", replace

fooddem_export using "$EASI_OUT/selected_model_parameters_gmm_twostep.csv", ///
    label("`best_model'_order`best_order'_gmm_twostep") replace

tempname smem
tempfile selectedsummary
postfile `smem' str12 model int order byte gmm_steps converged double N parameters ///
    J J_df J_p firststage_F firststage_p firststage_r2 using `selectedsummary', replace
local selected_converged = cond(missing(e(converged)), 1, e(converged))
post `smem' ("`best_model'") (`best_order') (e(fooddem_gmmsteps)) ///
    (`selected_converged') (e(N)) (e(fooddem_npar)) (e(J)) (e(J_df)) ///
    (chi2tail(e(J_df), e(J))) (e(fooddem_firststage_F)) ///
    (e(fooddem_firststage_p)) (e(fooddem_firststage_r2))
postclose `smem'
preserve
    use `selectedsummary', clear
    export delimited using "$EASI_OUT/selected_model_summary.csv", replace
restore

fooddem_tests using "$EASI_OUT/selected_model_tests.csv", ///
    demographics(`core_demos') replace
fooddem_elasticities using "$EASI_OUT/selected_model_elasticities.csv", replace
fooddem_regularity using "$EASI_OUT/selected_model_regularity.csv", replace
fooddem_demographics using "$EASI_OUT/selected_model_demographic_effects.csv", replace

* Fitted-share diagnostics are aggregate only; household identifiers are not
* written to the version-controlled results directory.
fooddem_p shat1 shat2 shat3 shat4 shat5 shat6
tempname fmem
tempfile fitstats
postfile `fmem' int good long N double observed_mean fitted_mean rmse mae correlation ///
    negative_fitted_rate using `fitstats', replace
forvalues g = 1/6 {
    tempvar sq ae neg
    gen double `sq' = (s`g' - shat`g')^2 if e(sample)
    gen double `ae' = abs(s`g' - shat`g') if e(sample)
    gen byte `neg' = shat`g' < 0 if e(sample)
    quietly summarize s`g' if e(sample), meanonly
    local om = r(mean)
    local n = r(N)
    quietly summarize shat`g' if e(sample), meanonly
    local fm = r(mean)
    quietly summarize `sq' if e(sample), meanonly
    local rmse = sqrt(r(mean))
    quietly summarize `ae' if e(sample), meanonly
    local mae = r(mean)
    quietly correlate s`g' shat`g' if e(sample)
    matrix FC = r(C)
    local corr = FC[1,2]
    quietly summarize `neg' if e(sample), meanonly
    post `fmem' (`g') (`n') (`om') (`fm') (`rmse') (`mae') (`corr') (r(mean))
}
postclose `fmem'
preserve
    use `fitstats', clear
    export delimited using "$EASI_OUT/fitted_share_diagnostics.csv", replace
restore

* Two-stage budgeting and third-stage quality decomposition. Commodity-value
* equations use PPML so the few zero quantities remain in the sample.
fooddem_income using "$EASI_OUT/income_elasticity_distribution.dta", ///
    income(income_annual) values(`purchasevalues') controls(`demos') ///
    id(household_id) valuemethod(ppml) cluster(village_cluster) replace
estimates restore fd_selected_gmm2

preserve
    use "$EASI_OUT/income_elasticity_distribution.dta", clear
    tempname imem
    tempfile istats
    postfile `imem' int good str36 elasticity long N double mean sd p10 p50 p90 ///
        using `istats', replace
    foreach y in eta_totalexp_income expenditure_elasticity ///
        income_quantity_elasticity income_value_elasticity income_quality_elasticity {
        forvalues g = 1/6 {
            quietly summarize `y' if good == `g', detail
            post `imem' (`g') ("`y'") (r(N)) (r(mean)) (r(sd)) ///
                (r(p10)) (r(p50)) (r(p90))
        }
    }
    postclose `imem'
    use `istats', clear
    export delimited using "$EASI_OUT/income_elasticity_summary.csv", replace
restore

preserve
    use "$EASI_OUT/income_elasticity_distribution.dta", clear
    xtile income_decile = income_annual, nq(10)
    collapse (count) N=income_annual (mean) eta_totalexp_income ///
        expenditure_elasticity income_quantity_elasticity ///
        income_value_elasticity income_quality_elasticity, by(good income_decile)
    export delimited using "$EASI_OUT/income_elasticity_by_decile.csv", replace
restore

preserve
    use "$EASI_OUT/income_elasticity_distribution.dta", clear
    gen str16 head_sex_group = cond(female_head_missing, "missing", ///
        cond(female_head, "female", "male"))
    gen str16 education_group = cond(education_missing, "missing", ///
        cond(head_no_education, "none", cond(head_primary_education, ///
        "primary", "secondary_plus")))
    gen str16 child_group = cond(age_missing, "missing", ///
        cond(child_ratio > 0, "child_present", "no_child"))
    gen str16 elderly_group = cond(age_missing, "missing", ///
        cond(elderly_ratio > 0, "elderly_present", "no_elderly"))
    tempname dmem
    tempfile dstats
    postfile `dmem' str24 dimension str20 category int good long N double ///
        eta_totalexp_income expenditure_elasticity income_quantity_elasticity ///
        income_value_elasticity income_quality_elasticity using `dstats', replace
    foreach dim in head_sex_group education_group child_group elderly_group {
        quietly levelsof `dim', local(levels)
        foreach level of local levels {
            forvalues g = 1/6 {
                quietly count if good == `g' & `dim' == "`level'"
                local n = r(N)
                local means ""
                foreach y in eta_totalexp_income expenditure_elasticity ///
                    income_quantity_elasticity income_value_elasticity income_quality_elasticity {
                    quietly summarize `y' if good == `g' & `dim' == "`level'", meanonly
                    local means "`means' (`=r(mean)')"
                }
                post `dmem' ("`dim'") ("`level'") (`g') (`n') `means'
            }
        }
    }
    postclose `dmem'
    use `dstats', clear
    export delimited using "$EASI_OUT/income_elasticity_by_demographics.csv", replace
restore

* GEASI is a nested robustness check at the preferred EASI order. It does not
* enter the AIDS/QUAIDS/EASI BIC choice if numerical convergence fails.
estimates restore fd_easi_gmm_for_geasi
tempname easiwarm cstart geasiwarm gsmem
matrix `easiwarm' = e(b)
matrix `cstart' = J(1, 6, 0)
matrix colnames `cstart' = c1 c2 c3 c4 c5 c6
matrix `geasiwarm' = `easiwarm', `cstart'
tempfile gs
postfile `gsmem' int easi_order return_code byte converged double N parameters ///
    J J_df J_p using `gs', replace
capture noisily fooddem, model(easi) order(`best_easi_order') precommitment ///
    shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
    demographics(`demos') quantities(`quantities') selection(sy) ///
    endogeneity(iv) instruments(`excluded') ///
    cluster(village_cluster) gmmsteps(1) from(`geasiwarm') ///
    iterate(100) tolerance(1e-5)
local geasi_rc = _rc
if `geasi_rc' {
    post `gsmem' (`best_easi_order') (`geasi_rc') (0) (.) (.) (.) (.) (.)
}
else {
    local geasi_converged = cond(missing(e(converged)), 1, e(converged))
    post `gsmem' (`best_easi_order') (0) (`geasi_converged') (e(N)) ///
        (e(fooddem_npar)) (e(J)) (e(J_df)) (.)
    estimates save "$EASI_OUT/geasi_robustness.ster", replace
    fooddem_export using "$EASI_OUT/geasi_parameters.csv", ///
        label("geasi_order`best_easi_order'_gmm_onestep") replace
    fooddem_precommitments using "$EASI_OUT/geasi_precommitments.csv", replace
    fooddem_tests using "$EASI_OUT/geasi_tests.csv", demographics(`core_demos') replace
}
postclose `gsmem'
preserve
    use `gs', clear
    export delimited using "$EASI_OUT/geasi_robustness_status.csv", replace
restore

* NLSUR with a control-function residual provides an estimator and expenditure
* exogeneity robustness check independent of the IV-GMM weighting choice.
fooddem_select using "$EASI_OUT/model_selection_nlsur_cf.csv", ///
    shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(nlsur) ///
    maxorder(3) demographics(`demos') quantities(`quantities') selection(sy) ///
    endogeneity(cf) instruments(`excluded') ///
    cluster(village_cluster) gmmsteps(1) iterate(100) tolerance(1e-6) replace
local nlsur_best_model "`r(preferred_model)'"
local nlsur_best_order = r(preferred_order)
local nlsur_best_estimate "`r(preferred_estimate)'"
estimates restore `nlsur_best_estimate'
estimates store fd_selected_nlsur
estimates save "$EASI_OUT/selected_nlsur_cf.ster", replace
fooddem_export using "$EASI_OUT/selected_nlsur_parameters.csv", ///
    label("`nlsur_best_model'_order`nlsur_best_order'_nlsur_cf") replace
fooddem_tests using "$EASI_OUT/selected_nlsur_tests.csv", demographics(`core_demos') replace
fooddem_elasticities using "$EASI_OUT/selected_nlsur_elasticities.csv", replace
fooddem_regularity using "$EASI_OUT/selected_nlsur_regularity.csv", replace

estimates restore fd_selected_gmm2
