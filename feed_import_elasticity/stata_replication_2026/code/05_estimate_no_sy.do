version 17
clear all
set more off
set linesize 180

args project adodir
if `"`project'"' == "" local project "/root/data/Paper/饲料进口弹性/stata_replication_2026"
if `"`adodir'"' == "" local adodir `"`project'/ado"'
adopath ++ `"`adodir'"'
local output `"`project'/output"'
capture log close _all
log using `"`project'/logs/05_estimate_no_sy.log"', text replace name(nosy)
use `"`project'/data/feed_import_estimation.dta"', clear

local shares "w_corn w_sorghum w_cassava w_oats w_barley"
local prices "lnp_corn lnp_sorghum lnp_cassava lnp_oats lnp_barley"
local controls "z_pork z_beef z_mutton z_poultry_meat z_eggs z_milk vhat_stata"
local common "shares(`shares') prices(`prices') expenditure(ln_expenditure)"
local common "`common' demographics(`controls') cluster(province_id)"

fooddem_select using `"`output'/model_selection_nlsur_cf_no_sy.csv"', ///
    `common' estimator(nlsur) maxorder(3) iterate(300) tolerance(1e-6) replace
local best_model "`r(preferred_model)'"
local best_order = r(preferred_order)
local best_estimate "`r(preferred_estimate)'"

foreach spec in aids quaids easi1 easi2 easi3 {
    capture estimates restore fd_`spec'
    if !_rc {
        fooddem_export using `"`output'/coefficients_nlsur_cf_no_sy_`spec'.csv"', replace
        fooddem_tests using `"`output'/tests_nlsur_cf_no_sy_`spec'.csv"', ///
            demographics(vhat_stata) replace
        fooddem_elasticities using `"`output'/elasticities_nlsur_cf_no_sy_`spec'_latent.csv"', ///
            margin(latent) minshare(.001) replace
        fooddem_regularity using `"`output'/regularity_nlsur_cf_no_sy_`spec'_latent.csv"', ///
            margin(latent) replace
        estimates save `"`output'/estimate_nlsur_cf_no_sy_`spec'.ster"', replace
    }
}

estimates restore `best_estimate'
fooddem_elasticities using `"`output'/preferred_elasticities_nlsur_cf_no_sy_latent.csv"', ///
    margin(latent) minshare(.001) replace
fooddem_regularity using `"`output'/preferred_regularity_nlsur_cf_no_sy_latent.csv"', ///
    margin(latent) replace
file open meta using `"`output'/preferred_model_no_sy.txt"', write text replace
file write meta "preferred_model=`best_model'" _n
file write meta "preferred_order=`best_order'" _n
file write meta "preferred_estimate=`best_estimate'" _n
file close meta
log close nosy
