version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

use "$EASI_DATA/source_analysis_ready.dta", clear
isid household_id
egen long village_cluster = group(village_id data_year)

local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
local selfprices "lnps1 lnps2 lnps3 lnps4 lnps5 lnps6"
local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
local geo "province_2 province_3 province_4 province_5 province_6 province_7 province_8"
local demos "`core' `geo'"
local excluded "ln_income inv_income"

foreach f in source_model_selection_total.csv source_total_parameters.csv ///
    source_total_tests.csv source_total_elasticities_unconditional.csv ///
    source_total_elasticities_intensive.csv source_total_elasticities_latent.csv ///
    source_total_regularity_unconditional.csv source_total_regularity_intensive.csv ///
    source_total_regularity_latent.csv source_total_curvature_projection.csv ///
    source_total_trim99_elasticities_unconditional.csv ///
    source_total_trim99_elasticities_latent.csv source_total_trim99_regularity_latent.csv ///
    source_total_trim99_tests.csv source_total_directprice_elasticities_latent.csv ///
    source_total_directprice_regularity_latent.csv source_total_directprice_tests.csv ///
    source_buy_parameters.csv source_buy_tests.csv ///
    source_buy_elasticities_unconditional.csv source_buy_elasticities_latent.csv ///
    source_buy_regularity_latent.csv source_omitself_parameters.csv ///
    source_omitself_tests.csv source_omitself_elasticities_unconditional.csv ///
    source_omitself_elasticities_latent.csv source_omitself_regularity_latent.csv ///
    source_self_parameters.csv source_self_tests.csv ///
    source_self_elasticities_unconditional.csv source_self_elasticities_latent.csv ///
    source_self_regularity_latent.csv {
    capture erase "$EASI_OUT/`f'"
}
foreach f in source_total_gmm_twostep.ster source_total_trim99_gmm.ster ///
    source_total_directprice_gmm.ster source_buy_gmm_twostep.ster ///
    source_omitself_gmm_twostep.ster source_self_gmm_twostep.ster ///
    source_total_income_distribution.dta source_buy_income_distribution.dta ///
    source_omitself_income_distribution.dta source_self_income_distribution.dta {
    capture erase "$EASI_OUT/`f'"
}

* Replacement-cost total demand is the primary welfare system: every consumed
* unit is valued at its village retail replacement price. Functional form is
* selected on one common sample before efficient two-step GMM estimation.
fooddem_select using "$EASI_OUT/source_model_selection_total.csv" if sample_total, ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) maxorder(3) ///
    demographics(`demos') quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) ///
    endogeneity(iv) instruments(`excluded') cluster(village_cluster) ///
    gmmsteps(1) iterate(60) tolerance(1e-5) replace
local model "`r(preferred_model)'"
local order = r(preferred_order)
local selected "`r(preferred_estimate)'"
estimates restore `selected'
tempname totalwarm
matrix `totalwarm' = e(b)
fooddem if sample_total, model(`model') order(`order') ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(`totalwarm') iterate(80) tolerance(1e-6)
estimates store fd_source_total
estimates save "$EASI_OUT/source_total_gmm_twostep.ster", replace
fooddem_export using "$EASI_OUT/source_total_parameters.csv", ///
    label("replacement_total_`model'_order`order'_gmm") replace
fooddem_tests using "$EASI_OUT/source_total_tests.csv", demographics(`core') replace
foreach margin in unconditional intensive latent {
    fooddem_elasticities using "$EASI_OUT/source_total_elasticities_`margin'.csv", ///
        margin(`margin') replace
    fooddem_regularity using "$EASI_OUT/source_total_regularity_`margin'.csv", ///
        margin(`margin') replace
}
fooddem_curvature using "$EASI_OUT/source_total_curvature_projection.csv", replace
fooddem_income using "$EASI_OUT/source_total_income_distribution.dta", ///
    income(income_annual) values(vt1 vt2 vt3 vt4 vt5 vt6) controls(`demos') ///
    id(household_id) valuemethod(ppml) cluster(village_cluster) replace

* Sensitivity 1 removes year-category positive-quantity tails above p99.
estimates restore fd_source_total
matrix `totalwarm' = e(b)
fooddem if sample_total & sample_trim99, model(`model') order(`order') ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(`totalwarm') iterate(80) tolerance(1e-6)
estimates save "$EASI_OUT/source_total_trim99_gmm.ster", replace
fooddem_elasticities using "$EASI_OUT/source_total_trim99_elasticities_unconditional.csv", ///
    margin(unconditional) replace
fooddem_elasticities using "$EASI_OUT/source_total_trim99_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using "$EASI_OUT/source_total_trim99_regularity_latent.csv", ///
    margin(latent) replace
fooddem_tests using "$EASI_OUT/source_total_trim99_tests.csv", demographics(`core') replace

* Sensitivity 2 requires all six retail prices to come from the household's
* own village/current year or an exact direct village quote, excluding every
* town/county/province imputation tier.
gen byte direct_all_prices = 1
forvalues g = 1/6 {
    replace direct_all_prices = 0 if !inrange(p`g'_source, 1, 2)
}
estimates restore fd_source_total
matrix `totalwarm' = e(b)
fooddem if sample_total & direct_all_prices, model(`model') order(`order') ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(`totalwarm') iterate(80) tolerance(1e-6)
estimates save "$EASI_OUT/source_total_directprice_gmm.ster", replace
fooddem_elasticities using "$EASI_OUT/source_total_directprice_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using "$EASI_OUT/source_total_directprice_regularity_latent.csv", ///
    margin(latent) replace
fooddem_tests using "$EASI_OUT/source_total_directprice_tests.csv", ///
    demographics(`core') replace

* Purchase demand holds the total-demand functional form fixed. Its prices and
* expenditure therefore describe the market-purchase margin, not all food use.
fooddem if sample_buy, model(`model') order(`order') ///
    shares(sb1 sb2 sb3 sb4 sb5 sb6) prices(`prices') ///
    expenditure(ln_foodexp_buy) estimator(gmm) demographics(`demos') ///
    quantities(qb1 qb2 qb3 qb4 qb5 qb6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(1) ///
    iterate(60) tolerance(1e-5)
tempname buywarm
matrix `buywarm' = e(b)
fooddem if sample_buy, model(`model') order(`order') ///
    shares(sb1 sb2 sb3 sb4 sb5 sb6) prices(`prices') ///
    expenditure(ln_foodexp_buy) estimator(gmm) demographics(`demos') ///
    quantities(qb1 qb2 qb3 qb4 qb5 qb6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(`buywarm') iterate(80) tolerance(1e-6)
estimates save "$EASI_OUT/source_buy_gmm_twostep.ster", replace
fooddem_export using "$EASI_OUT/source_buy_parameters.csv", ///
    label("purchase_`model'_order`order'_gmm") replace
fooddem_tests using "$EASI_OUT/source_buy_tests.csv", demographics(`core') replace
foreach margin in unconditional latent {
    fooddem_elasticities using "$EASI_OUT/source_buy_elasticities_`margin'.csv", ///
        margin(`margin') replace
}
fooddem_regularity using "$EASI_OUT/source_buy_regularity_latent.csv", ///
    margin(latent) replace
fooddem_income using "$EASI_OUT/source_buy_income_distribution.dta", ///
    income(income_annual) values(vb1 vb2 vb3 vb4 vb5 vb6) controls(`demos') ///
    id(household_id) valuemethod(ppml) cluster(village_cluster) replace

* Buy-plus-gift demand removes own production but retains other received food.
* Comparing it with total demand isolates omission of own consumption, unlike
* purchase-only demand, which also removes gifts.
fooddem if sample_omitself, model(`model') order(`order') ///
    shares(so1 so2 so3 so4 so5 so6) prices(`prices') ///
    expenditure(ln_foodexp_omitself) estimator(gmm) demographics(`demos') ///
    quantities(qo1 qo2 qo3 qo4 qo5 qo6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(1) ///
    iterate(60) tolerance(1e-5)
tempname omitwarm
matrix `omitwarm' = e(b)
fooddem if sample_omitself, model(`model') order(`order') ///
    shares(so1 so2 so3 so4 so5 so6) prices(`prices') ///
    expenditure(ln_foodexp_omitself) estimator(gmm) demographics(`demos') ///
    quantities(qo1 qo2 qo3 qo4 qo5 qo6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(`omitwarm') iterate(80) tolerance(1e-6)
estimates save "$EASI_OUT/source_omitself_gmm_twostep.ster", replace
fooddem_export using "$EASI_OUT/source_omitself_parameters.csv", ///
    label("buy_plus_gift_`model'_order`order'_gmm") replace
fooddem_tests using "$EASI_OUT/source_omitself_tests.csv", demographics(`core') replace
foreach margin in unconditional latent {
    fooddem_elasticities using "$EASI_OUT/source_omitself_elasticities_`margin'.csv", ///
        margin(`margin') replace
}
fooddem_regularity using "$EASI_OUT/source_omitself_regularity_latent.csv", ///
    margin(latent) replace
fooddem_income using "$EASI_OUT/source_omitself_income_distribution.dta", ///
    income(income_annual) values(vo1 vo2 vo3 vo4 vo5 vo6) controls(`demos') ///
    id(household_id) valuemethod(ppml) cluster(village_cluster) replace

* This separate own-consumption system is retained as a falsification/diagnostic
* fit only. Farmgate opportunity prices are endogenous to production choice;
* weak-instrument, Hansen, and fitted-share diagnostics determine validity.
fooddem if sample_self, model(`model') order(`order') ///
    shares(ss1 ss2 ss3 ss4 ss5 ss6) prices(`selfprices') ///
    expenditure(ln_foodexp_self) estimator(gmm) demographics(`demos') ///
    quantities(qs1 qs2 qs3 qs4 qs5 qs6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(1) ///
    iterate(60) tolerance(1e-5)
tempname selfwarm
matrix `selfwarm' = e(b)
fooddem if sample_self, model(`model') order(`order') ///
    shares(ss1 ss2 ss3 ss4 ss5 ss6) prices(`selfprices') ///
    expenditure(ln_foodexp_self) estimator(gmm) demographics(`demos') ///
    quantities(qs1 qs2 qs3 qs4 qs5 qs6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(`selfwarm') iterate(80) tolerance(1e-6)
estimates save "$EASI_OUT/source_self_gmm_twostep.ster", replace
fooddem_export using "$EASI_OUT/source_self_parameters.csv", ///
    label("own_consumption_diagnostic_`model'_order`order'_gmm") replace
fooddem_tests using "$EASI_OUT/source_self_tests.csv", demographics(`core') replace
foreach margin in unconditional latent {
    fooddem_elasticities using "$EASI_OUT/source_self_elasticities_`margin'.csv", ///
        margin(`margin') replace
}
fooddem_regularity using "$EASI_OUT/source_self_regularity_latent.csv", ///
    margin(latent) replace
fooddem_income using "$EASI_OUT/source_self_income_distribution.dta", ///
    income(income_annual) values(vs1 vs2 vs3 vs4 vs5 vs6) controls(`demos') ///
    id(household_id) valuemethod(ppml) cluster(village_cluster) replace
