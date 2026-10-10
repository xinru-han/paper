version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_nine_groups/code/00_config.do"
use "$NINE_DATA/nine_group_analysis.dta", clear

local shares "s1 s2 s3 s4 s5 s6 s7 s8 s9"
local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6 lnp7 lnp8 lnp9"
local quantities "qt1 qt2 qt3 qt4 qt5 qt6 qt7 qt8 qt9"
local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
ds province_*, has(type numeric)
local demos "`core' `r(varlist)'"

estimates use "$NINE_OUT/easi_nlsur_cf.ster"
local easi_order = e(fooddem_order)
matrix START_EASI = e(b)
fooddem if sample_model, model(easi) order(`easi_order') shares(`shares') ///
    prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
    demographics(`demos') quantities(`quantities') selection(sy) ///
    endogeneity(iv) instruments(ln_income inv_income) ///
    cluster(village_cluster) gmmsteps(1) from(START_EASI) ///
    iterate(150) tolerance(1e-6)
estimates save "$NINE_OUT/easi_gmm_onestep.ster", replace
fooddem_export using "$NINE_OUT/easi_gmm1_parameters.csv", label("Nine-group EASI one-step GMM-IV") replace
fooddem_tests using "$NINE_OUT/easi_gmm1_tests.csv", demographics(`core') replace
fooddem_elasticities using "$NINE_OUT/easi_gmm1_elasticities.csv", margin(latent) replace
fooddem_regularity using "$NINE_OUT/easi_gmm1_regularity.csv", margin(latent) replace
fooddem_reference using "$NINE_OUT/easi_gmm1_reference_analytic.csv", replace
