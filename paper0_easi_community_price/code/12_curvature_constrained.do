version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

use "$EASI_DATA/source_analysis_ready.dta", clear
isid household_id
egen long village_cluster = group(village_id data_year)

local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
local geo "province_2 province_3 province_4 province_5 province_6 province_7 province_8"
local demos "`core' `geo'"
local excluded "ln_income inv_income"
gen byte direct_all_prices = 1
forvalues g = 1/6 {
    replace direct_all_prices = 0 if !inrange(p`g'_source, 1, 2)
}
gen byte direct_price_sample = sample_total & direct_all_prices

foreach f in source_total_reference_unconstrained.csv ///
    source_total_curvature_constrained_parameters.csv ///
    source_total_curvature_constrained_tests.csv ///
    source_total_curvature_constrained_reference.csv ///
    source_total_curvature_constrained_elasticities_latent.csv ///
    source_total_curvature_constrained_regularity_latent.csv ///
    source_total_curvature_global_parameters.csv ///
    source_total_curvature_global_tests.csv ///
    source_total_curvature_global_reference.csv ///
    source_total_curvature_global_elasticities_latent.csv ///
    source_total_curvature_global_regularity_latent.csv ///
    source_total_directprice_curvature_parameters.csv ///
    source_total_directprice_reference_unconstrained.csv ///
    source_total_directprice_curvature_tests.csv ///
    source_total_directprice_curvature_reference.csv ///
    source_total_directprice_curvature_elasticities_latent.csv ///
    source_total_directprice_curvature_regularity_latent.csv ///
    source_total_curvature_estimation_comparison.csv {
    capture erase "$EASI_OUT/`f'"
}
capture erase "$EASI_OUT/source_total_curvature_constrained_gmm.ster"
capture erase "$EASI_OUT/source_total_curvature_global_gmm.ster"
capture erase "$EASI_OUT/source_total_directprice_curvature_gmm.ster"

* The unrestricted estimate is retained as the statistical benchmark. Its
* reference elasticities use the same sample-average evaluation point as the
* locally curvature-constrained model and Hovhannisyan et al. (2025).
estimates use "$EASI_OUT/source_total_gmm_twostep.ster"
tempname unrestricted_start
matrix `unrestricted_start' = e(b)
local Ju = e(J)
local dfu = e(J_df)
local Nu = e(N)
fooddem_reference using "$EASI_OUT/source_total_reference_unconstrained.csv", ///
    sample(sample_total) replace
local eig_u = r(slutsky_max_eigenvalue)

* Moschini-style local curvature is imposed by writing the reference Slutsky
* matrix as -Q*L*L'*Q', where Q spans the adding-up subspace. The EASI price
* matrix is estimated jointly as diag(w0)-w0*w0'-Q*L*L'*Q'.
fooddem if sample_total, model(easi) order(1) ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    curvature(local) from(`unrestricted_start') iterate(160) tolerance(1e-5)
estimates store fd_source_total_curvature
estimates save "$EASI_OUT/source_total_curvature_constrained_gmm.ster", replace
fooddem_export using "$EASI_OUT/source_total_curvature_constrained_parameters.csv", ///
    label("replacement_total_easi_order1_gmm_curvature_local") replace
fooddem_tests using "$EASI_OUT/source_total_curvature_constrained_tests.csv", ///
    demographics(`core') replace
fooddem_reference using "$EASI_OUT/source_total_curvature_constrained_reference.csv", ///
    sample(sample_total) replace
local eig_c = r(slutsky_max_eigenvalue)
fooddem_elasticities using ///
    "$EASI_OUT/source_total_curvature_constrained_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using ///
    "$EASI_OUT/source_total_curvature_constrained_regularity_latent.csv", ///
    margin(latent) replace

local Jl = e(J)
local dfl = e(J_df)
local Nl = e(N)
local convl = e(converged)

* A stronger, globally sufficient condition makes gamma negative semidefinite.
* Because diag(w)-w*w' is positive semidefinite for every interior share
* vector, S=gamma-[diag(w)-w*w'] is then negative semidefinite household by
* household. This is deliberately reported separately because it is more
* restrictive than the standard local condition.
fooddem if sample_total, model(easi) order(1) ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    curvature(global) from(`unrestricted_start') iterate(200) tolerance(1e-5)
estimates store fd_curve_global
estimates save "$EASI_OUT/source_total_curvature_global_gmm.ster", replace
fooddem_export using "$EASI_OUT/source_total_curvature_global_parameters.csv", ///
    label("replacement_total_easi_order1_gmm_curvature_global") replace
fooddem_tests using "$EASI_OUT/source_total_curvature_global_tests.csv", ///
    demographics(`core') replace
fooddem_reference using "$EASI_OUT/source_total_curvature_global_reference.csv", ///
    sample(sample_total) replace
local eig_g = r(slutsky_max_eigenvalue)
fooddem_elasticities using ///
    "$EASI_OUT/source_total_curvature_global_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using ///
    "$EASI_OUT/source_total_curvature_global_regularity_latent.csv", ///
    margin(latent) replace
local Jg = e(J)
local dfg = e(J_df)
local Ng = e(N)
local convg = e(converged)

* Price elasticities are also estimated on the pre-specified direct-price
* sample. This excludes town/county/province price imputations, which are the
* main empirical source of the positive aggregate own-price estimates.
estimates use "$EASI_OUT/source_total_directprice_gmm.ster"
tempname direct_start
matrix `direct_start' = e(b)
local Jdu = e(J)
local dfdu = e(J_df)
local Ndu = e(N)
fooddem_reference using ///
    "$EASI_OUT/source_total_directprice_reference_unconstrained.csv", ///
    sample(direct_price_sample) replace
local eig_du = r(slutsky_max_eigenvalue)
fooddem if sample_total & direct_all_prices, model(easi) order(1) ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    curvature(local) from(`direct_start') iterate(160) tolerance(1e-5)
estimates store fd_curve_direct
estimates save "$EASI_OUT/source_total_directprice_curvature_gmm.ster", replace
fooddem_export using "$EASI_OUT/source_total_directprice_curvature_parameters.csv", ///
    label("replacement_total_direct_prices_easi_order1_gmm_curvature_local") replace
fooddem_tests using "$EASI_OUT/source_total_directprice_curvature_tests.csv", ///
    demographics(`core') replace
fooddem_reference using "$EASI_OUT/source_total_directprice_curvature_reference.csv", ///
    sample(direct_price_sample) replace
local eig_d = r(slutsky_max_eigenvalue)
fooddem_elasticities using ///
    "$EASI_OUT/source_total_directprice_curvature_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using ///
    "$EASI_OUT/source_total_directprice_curvature_regularity_latent.csv", ///
    margin(latent) replace
local Jd = e(J)
local dfd = e(J_df)
local Nd = e(N)
local convd = e(converged)

tempname mem
tempfile comparison
postfile `mem' str20 specification double N J J_df Hansen_p ///
    reference_max_eigenvalue converged using `comparison', replace
post `mem' ("unrestricted") (`Nu') (`Ju') (`dfu') (chi2tail(`dfu',`Ju')) ///
    (`eig_u') (1)
post `mem' ("curvature_local") (`Nl') (`Jl') (`dfl') (chi2tail(`dfl',`Jl')) ///
    (`eig_c') (`convl')
post `mem' ("curvature_global") (`Ng') (`Jg') (`dfg') (chi2tail(`dfg',`Jg')) ///
    (`eig_g') (`convg')
post `mem' ("directprice_unrestr") (`Ndu') (`Jdu') (`dfdu') ///
    (chi2tail(`dfdu',`Jdu')) (`eig_du') (1)
post `mem' ("directprice_local") (`Nd') (`Jd') (`dfd') (chi2tail(`dfd',`Jd')) ///
    (`eig_d') (`convd')
postclose `mem'
preserve
    use `comparison', clear
    export delimited using "$EASI_OUT/source_total_curvature_estimation_comparison.csv", replace
restore
