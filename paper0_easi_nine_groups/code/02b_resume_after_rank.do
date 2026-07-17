version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_nine_groups/code/00_config.do"
use "$NINE_DATA/nine_group_analysis.dta", clear

local shares "s1 s2 s3 s4 s5 s6 s7 s8 s9"
local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6 lnp7 lnp8 lnp9"
local quantities "qt1 qt2 qt3 qt4 qt5 qt6 qt7 qt8 qt9"
local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
ds province_*, has(type numeric)
local demos "`core' `r(varlist)'"
local instruments "ln_income inv_income"

* The original rank failure came from exact collinearity between year_2024 and
* province fixed effects. With year_2024 excluded, selected order three is
* identified by the original income instrument functions.
local selected_model "easi"
local selected_order = 3
local selected_easi_order = 3
local gmm_order = 3

estimates use "$NINE_OUT/easi_nlsur_cf.ster"
matrix START_EASI = e(b)
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
    if `rc1' exit `rc1'
}
estimates store nine_easi_gmm
estimates save "$NINE_OUT/easi_gmm.ster", replace
fooddem_export using "$NINE_OUT/easi_parameters.csv", label("Nine-group EASI GMM-IV order 2") replace
fooddem_tests using "$NINE_OUT/easi_tests.csv", demographics(`core') replace
fooddem_elasticities using "$NINE_OUT/easi_elasticities.csv", margin(latent) replace
fooddem_regularity using "$NINE_OUT/easi_regularity.csv", margin(latent) replace
fooddem_reference using "$NINE_OUT/easi_reference_analytic.csv", replace

tempname statusmem
tempfile status
postfile `statusmem' str16 model str16 estimator int order gmm_steps ///
    return_code long N double J J_df J_p firststage_F firststage_p ///
    firststage_r2 converged using `status', replace
foreach spec in aids quaids easi_nlsur {
    local ster = cond("`spec'" == "aids", "aids_nlsur_cf.ster", ///
        cond("`spec'" == "quaids", "quaids_nlsur_cf.ster", "easi_nlsur_cf.ster"))
    estimates use "$NINE_OUT/`ster'"
    post `statusmem' ("`spec'") ("nlsur_cf") (e(fooddem_order)) (0) (0) ///
        (e(N)) (.) (.) (.) (e(fooddem_firststage_F)) ///
        (e(fooddem_firststage_p)) (e(fooddem_firststage_r2)) (e(converged))
}
estimates restore nine_easi_gmm
local jp = cond(`steps' == 2 & e(J_df) > 0, chi2tail(e(J_df), e(J)), .)
post `statusmem' ("easi_gmm") ("gmm_iv") (`gmm_order') (`steps') (`rc2') ///
    (e(N)) (e(J)) (e(J_df)) (`jp') (e(fooddem_firststage_F)) ///
    (e(fooddem_firststage_p)) (e(fooddem_firststage_r2)) (e(converged))
postclose `statusmem'

use `status', clear
gen str12 selected_model = "`selected_model'"
gen int selected_order = `selected_order'
gen int selected_easi_order = `selected_easi_order'
export delimited using "$NINE_OUT/estimation_status.csv", replace
