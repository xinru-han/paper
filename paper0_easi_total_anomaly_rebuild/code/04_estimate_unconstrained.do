version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_config.do"
use "$AR_DATA/total_anomaly_analysis.dta", clear
isid household_id data_year

local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
local shares "s1 s2 s3 s4 s5 s6"
local quantities "qt1 qt2 qt3 qt4 qt5 qt6"
local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
ds province_*, has(type numeric)
local geo "`r(varlist)'"
local demos "`core' `geo'"
local excluded "ln_income inv_income"

* Candidate models are estimated on exactly the same preferred sample. GEASI
* and every curvature option are deliberately excluded.
fooddem_select using "$AR_OUT/model_selection.csv" if sample_model, ///
    shares(`shares') prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
    maxorder(3) demographics(`demos') quantities(`quantities') selection(sy) ///
    endogeneity(iv) instruments(`excluded') cluster(village_cluster) ///
    gmmsteps(1) iterate(80) tolerance(1e-5) replace
local preferred_model "`r(preferred_model)'"
local preferred_order = r(preferred_order)
local easi_order = r(preferred_easi_order)
if missing(`easi_order') local easi_order = 1

* AIDS
estimates restore fd_aids
matrix AR_AIDS_START = e(b)
fooddem if sample_model, model(aids) order(1) shares(`shares') prices(`prices') ///
    expenditure(ln_foodexp) estimator(gmm) demographics(`demos') ///
    quantities(`quantities') selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(AR_AIDS_START) iterate(100) tolerance(1e-6)
estimates store ar_aids
estimates save "$AR_OUT/aids_gmm.ster", replace
fooddem_export using "$AR_OUT/aids_parameters.csv", label("AIDS unrestricted") replace
fooddem_tests using "$AR_OUT/aids_tests.csv", demographics(`core') replace
fooddem_elasticities using "$AR_OUT/aids_elasticities.csv", margin(latent) replace
fooddem_elasticities using "$AR_OUT/aids_elasticities_support005.csv", ///
    margin(latent) minshare(.005) replace
fooddem_regularity using "$AR_OUT/aids_regularity.csv", margin(latent) replace

* QUAIDS
estimates restore fd_quaids
matrix AR_QUAIDS_START = e(b)
fooddem if sample_model, model(quaids) order(2) shares(`shares') prices(`prices') ///
    expenditure(ln_foodexp) estimator(gmm) demographics(`demos') ///
    quantities(`quantities') selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(AR_QUAIDS_START) iterate(100) tolerance(1e-6)
estimates store ar_quaids
estimates save "$AR_OUT/quaids_gmm.ster", replace
fooddem_export using "$AR_OUT/quaids_parameters.csv", label("QUAIDS unrestricted") replace
fooddem_tests using "$AR_OUT/quaids_tests.csv", demographics(`core') replace
fooddem_elasticities using "$AR_OUT/quaids_elasticities.csv", margin(latent) replace
fooddem_elasticities using "$AR_OUT/quaids_elasticities_support005.csv", ///
    margin(latent) minshare(.005) replace
fooddem_regularity using "$AR_OUT/quaids_regularity.csv", margin(latent) replace

* Preferred EASI order within the EASI family.
estimates restore fd_easi`easi_order'
matrix AR_EASI_START = e(b)
fooddem if sample_model, model(easi) order(`easi_order') shares(`shares') ///
    prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
    demographics(`demos') quantities(`quantities') selection(sy) ///
    endogeneity(iv) instruments(`excluded') cluster(village_cluster) ///
    gmmsteps(2) from(AR_EASI_START) iterate(100) tolerance(1e-6)
estimates store ar_easi
estimates save "$AR_OUT/easi_gmm.ster", replace
fooddem_export using "$AR_OUT/easi_parameters.csv", ///
    label("EASI order `easi_order' unrestricted") replace
fooddem_tests using "$AR_OUT/easi_tests.csv", demographics(`core') replace
fooddem_elasticities using "$AR_OUT/easi_elasticities.csv", margin(latent) replace
fooddem_elasticities using "$AR_OUT/easi_elasticities_support005.csv", ///
    margin(latent) minshare(.005) replace
fooddem_regularity using "$AR_OUT/easi_regularity.csv", margin(latent) replace
fooddem_reference using "$AR_OUT/easi_reference_analytic.csv", replace

tempname smem
tempfile sensitivity
postfile `smem' str20 sample int return_code order long n double hansen_p ///
    firststage_p converged using `sensitivity', replace
post `smem' ("main") (0) (`easi_order') (e(N)) ///
    (chi2tail(e(J_df), e(J))) (e(firststage_p)) (e(converged))
matrix AR_EASI_MAIN = e(b)

* These estimates identify whether elasticity signs move because of raw-data
* screens. Every model remains unrestricted; the only change is the sample.
foreach spec in physical total5 allcomponents strict45 lenient60 p99 localprice {
    local condition "sample_physical"
    if "`spec'" == "total5" local condition "sample_total5"
    if "`spec'" == "allcomponents" local condition "sample_allcomponents"
    if "`spec'" == "strict45" local condition "sample_strict45"
    if "`spec'" == "lenient60" local condition "sample_lenient60"
    if "`spec'" == "p99" local condition "sample_p99"
    if "`spec'" == "localprice" local condition "sample_main_localprice"
    capture noisily fooddem if `condition' & !missing(ln_income, inv_income), ///
        model(easi) order(`easi_order') shares(`shares') prices(`prices') ///
        expenditure(ln_foodexp) estimator(gmm) demographics(`demos') ///
        quantities(`quantities') selection(sy) endogeneity(iv) ///
        instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
        from(AR_EASI_MAIN) iterate(100) tolerance(1e-6)
    local rc = _rc
    if `rc' {
        post `smem' ("`spec'") (`rc') (`easi_order') (.) (.) (.) (0)
    }
    else {
        estimates save "$AR_OUT/easi_`spec'_gmm.ster", replace
        fooddem_reference using "$AR_OUT/easi_`spec'_reference_analytic.csv", replace
        fooddem_elasticities using "$AR_OUT/easi_`spec'_elasticities.csv", ///
            margin(latent) replace
        fooddem_tests using "$AR_OUT/easi_`spec'_tests.csv", ///
            demographics(`core') replace
        local hp = chi2tail(e(J_df), e(J))
        post `smem' ("`spec'") (0) (`easi_order') (e(N)) (`hp') ///
            (e(firststage_p)) (e(converged))
    }
}
postclose `smem'
preserve
    use `sensitivity', clear
    gen str12 preferred_model = "`preferred_model'"
    gen int preferred_order = `preferred_order'
    export delimited using "$AR_OUT/easi_sample_sensitivity_status.csv", replace
restore

estimates restore ar_easi
