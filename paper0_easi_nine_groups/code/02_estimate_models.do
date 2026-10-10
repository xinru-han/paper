version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_nine_groups/code/00_config.do"
use "$NINE_DATA/nine_group_analysis.dta", clear
isid household_id data_year

local shares "s1 s2 s3 s4 s5 s6 s7 s8 s9"
local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6 lnp7 lnp8 lnp9"
local quantities "qt1 qt2 qt3 qt4 qt5 qt6 qt7 qt8 qt9"
local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
ds province_*, has(type numeric)
local geography "`r(varlist)'"
local demos "`core' `geography'"
local instruments "ln_income inv_income"

quietly count if sample_model
assert r(N) > 1000
assert abs(share_sum - 1) < 1e-8 if sample_model

* Exact AIDS/QUAIDS GMM with numerical derivatives is prohibitively slow in
* this nine-good specification. Use the package's NLSUR control-function path
* for a same-estimator model comparison, then fit the selected EASI order by
* GMM-IV below.
fooddem_select using "$NINE_OUT/model_selection.csv" if sample_model, ///
    shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(nlsur) ///
    maxorder(3) demographics(`demos') quantities(`quantities') selection(sy) ///
    endogeneity(cf) instruments(`instruments') cluster(village_cluster) ///
    iterate(120) tolerance(1e-5) replace

local preferred_model "`r(preferred_model)'"
local preferred_order = r(preferred_order)
local easi_order = r(preferred_easi_order)
if missing(`easi_order') local easi_order = 1

tempname statusmem
tempfile status
postfile `statusmem' str16 model str16 estimator int order gmm_steps ///
    return_code long N double J J_df J_p firststage_F firststage_p ///
    firststage_r2 converged using `status', replace

* AIDS, NLSUR with expenditure control function.
estimates restore fd_aids
estimates store nine_aids
estimates save "$NINE_OUT/aids_nlsur_cf.ster", replace
post `statusmem' ("aids") ("nlsur_cf") (1) (0) (0) (e(N)) (.) (.) (.) ///
    (e(fooddem_firststage_F)) (e(fooddem_firststage_p)) ///
    (e(fooddem_firststage_r2)) (e(converged))
fooddem_export using "$NINE_OUT/aids_parameters.csv", label("Nine-group AIDS NLSUR-CF") replace
fooddem_tests using "$NINE_OUT/aids_tests.csv", demographics(`core') replace
fooddem_elasticities using "$NINE_OUT/aids_elasticities.csv", margin(latent) replace
fooddem_regularity using "$NINE_OUT/aids_regularity.csv", margin(latent) replace

* QUAIDS, NLSUR with expenditure control function.
estimates restore fd_quaids
estimates store nine_quaids
estimates save "$NINE_OUT/quaids_nlsur_cf.ster", replace
post `statusmem' ("quaids") ("nlsur_cf") (2) (0) (0) (e(N)) (.) (.) (.) ///
    (e(fooddem_firststage_F)) (e(fooddem_firststage_p)) ///
    (e(fooddem_firststage_r2)) (e(converged))
fooddem_export using "$NINE_OUT/quaids_parameters.csv", label("Nine-group QUAIDS NLSUR-CF") replace
fooddem_tests using "$NINE_OUT/quaids_tests.csv", demographics(`core') replace
fooddem_elasticities using "$NINE_OUT/quaids_elasticities.csv", margin(latent) replace
fooddem_regularity using "$NINE_OUT/quaids_regularity.csv", margin(latent) replace

* Preferred EASI order under the same NLSUR-CF comparison.
estimates restore fd_easi`easi_order'
matrix START_EASI = e(b)
estimates store nine_easi_nlsur
estimates save "$NINE_OUT/easi_nlsur_cf.ster", replace
post `statusmem' ("easi_nlsur") ("nlsur_cf") (`easi_order') (0) (0) ///
    (e(N)) (.) (.) (.) (e(fooddem_firststage_F)) ///
    (e(fooddem_firststage_p)) (e(fooddem_firststage_r2)) (e(converged))
fooddem_export using "$NINE_OUT/easi_nlsur_parameters.csv", label("Nine-group EASI NLSUR-CF") replace
fooddem_tests using "$NINE_OUT/easi_nlsur_tests.csv", demographics(`core') replace
fooddem_elasticities using "$NINE_OUT/easi_nlsur_elasticities.csv", margin(latent) replace
fooddem_regularity using "$NINE_OUT/easi_nlsur_regularity.csv", margin(latent) replace
fooddem_reference using "$NINE_OUT/easi_nlsur_reference_analytic.csv", replace

* EASI GMM-IV. If the selected order is rank deficient, step down by one
* Engel order rather than adding unvalidated instruments merely to fill rank.
local gmm_order = `easi_order'
local rc1 = .
capture noisily fooddem if sample_model, model(easi) order(`gmm_order') ///
    shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
    demographics(`demos') quantities(`quantities') selection(sy) ///
    endogeneity(iv) instruments(`instruments') cluster(village_cluster) ///
    gmmsteps(2) from(START_EASI) iterate(150) tolerance(1e-6)
local rc2 = _rc
local steps = 2
if `rc2' {
    capture noisily fooddem if sample_model, model(easi) order(`gmm_order') ///
        shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
        demographics(`demos') quantities(`quantities') selection(sy) ///
        endogeneity(iv) instruments(`instruments') cluster(village_cluster) ///
        gmmsteps(1) from(START_EASI) iterate(150) tolerance(1e-6)
    local rc1 = _rc
    local steps = 1
}
if `rc2' & `rc1' & `gmm_order' > 1 {
    local gmm_order = `gmm_order' - 1
    di as text "Selected EASI order is not GMM-identified; retrying order `gmm_order'"
    capture noisily fooddem if sample_model, model(easi) order(`gmm_order') ///
        shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
        demographics(`demos') quantities(`quantities') selection(sy) ///
        endogeneity(iv) instruments(`instruments') cluster(village_cluster) ///
        gmmsteps(2) from(START_EASI) iterate(150) tolerance(1e-6)
    local rc2 = _rc
    local steps = 2
    if `rc2' {
        capture noisily fooddem if sample_model, model(easi) order(`gmm_order') ///
            shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
            demographics(`demos') quantities(`quantities') selection(sy) ///
            endogeneity(iv) instruments(`instruments') cluster(village_cluster) ///
            gmmsteps(1) from(START_EASI) iterate(150) tolerance(1e-6)
        local rc1 = _rc
        local steps = 1
    }
    else local rc1 = 0
}
if `rc2' & `rc1' {
    di as error "Both two-step and one-step EASI GMM failed at the identified fallback order"
    exit `rc1'
}
estimates store nine_easi_gmm
estimates save "$NINE_OUT/easi_gmm.ster", replace
local jp = cond(`steps' == 2 & e(J_df) > 0, chi2tail(e(J_df), e(J)), .)
post `statusmem' ("easi_gmm") ("gmm_iv") (`gmm_order') (`steps') (`rc2') ///
    (e(N)) (e(J)) (e(J_df)) (`jp') (e(fooddem_firststage_F)) ///
    (e(fooddem_firststage_p)) (e(fooddem_firststage_r2)) (e(converged))
fooddem_export using "$NINE_OUT/easi_parameters.csv", label("Nine-group EASI GMM-IV") replace
fooddem_tests using "$NINE_OUT/easi_tests.csv", demographics(`core') replace
fooddem_elasticities using "$NINE_OUT/easi_elasticities.csv", margin(latent) replace
fooddem_regularity using "$NINE_OUT/easi_regularity.csv", margin(latent) replace
fooddem_reference using "$NINE_OUT/easi_reference_analytic.csv", replace

postclose `statusmem'
preserve
    use `status', clear
    gen str12 selected_model = "`preferred_model'"
    gen int selected_order = `preferred_order'
    gen int selected_easi_order = `easi_order'
    export delimited using "$NINE_OUT/estimation_status.csv", replace
restore
