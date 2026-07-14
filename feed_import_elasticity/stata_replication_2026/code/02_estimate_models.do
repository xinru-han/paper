version 17
clear all
set more off
set linesize 180

args project adodir
if `"`project'"' == "" local project "/root/data/Paper/饲料进口弹性/stata_replication_2026"
if `"`adodir'"' == "" local adodir `"`project'/ado"'
adopath ++ `"`adodir'"'

local data   `"`project'/data"'
local output `"`project'/output"'
local logs   `"`project'/logs"'
capture mkdir `"`output'"'
capture mkdir `"`logs'"'
capture log close _all
log using `"`logs'/02_estimate_models.log"', text replace name(models)

use `"`data'/feed_import_estimation.dta"', clear

local shares "w_corn w_sorghum w_cassava w_oats w_barley"
local prices "lnp_corn lnp_sorghum lnp_cassava lnp_oats lnp_barley"
local parts "part_corn part_sorghum part_cassava part_oats part_barley"
local controls "z_pork z_beef z_mutton z_poultry_meat z_eggs z_milk vhat_stata"
local common "shares(`shares') prices(`prices') expenditure(ln_expenditure)"
local common "`common' demographics(`controls') quantities(`parts') selection(sy) cluster(province_id)"

* Main estimator: nonlinear SUR with the Stata-generated control-function
* residual. This is the closest fooddem analogue to the old R FIML-CF design.
fooddem_select using `"`output'/model_selection_nlsur_cf.csv"', ///
    `common' estimator(nlsur) maxorder(3) iterate(300) tolerance(1e-6) replace

local best_model "`r(preferred_model)'"
local best_order = r(preferred_order)
local best_estimate "`r(preferred_estimate)'"
local easi_order = r(preferred_easi_order)
local easi_estimate "`r(preferred_easi_estimate)'"

foreach spec in aids quaids easi1 easi2 easi3 {
    capture estimates restore fd_`spec'
    if !_rc {
        fooddem_export using `"`output'/coefficients_nlsur_cf_`spec'.csv"', replace
        fooddem_tests using `"`output'/tests_nlsur_cf_`spec'.csv"', ///
            demographics(vhat_stata) replace
        fooddem_elasticities using `"`output'/elasticities_nlsur_cf_`spec'_latent.csv"', ///
            margin(latent) minshare(.001) replace
        fooddem_regularity using `"`output'/regularity_nlsur_cf_`spec'_latent.csv"', ///
            margin(latent) replace
        estimates save `"`output'/estimate_nlsur_cf_`spec'.ster"', replace
    }
}

* Stable aliases for all downstream comparison and reporting code.
estimates restore `best_estimate'
fooddem_export using `"`output'/preferred_coefficients_nlsur_cf.csv"', replace
fooddem_tests using `"`output'/preferred_tests_nlsur_cf.csv"', ///
    demographics(vhat_stata) replace
fooddem_elasticities using `"`output'/preferred_elasticities_nlsur_cf_latent.csv"', ///
    margin(latent) minshare(.001) replace
fooddem_elasticities using `"`output'/preferred_elasticities_nlsur_cf_unconditional.csv"', ///
    margin(unconditional) minshare(.001) replace
fooddem_regularity using `"`output'/preferred_regularity_nlsur_cf_latent.csv"', ///
    margin(latent) replace

if `"`easi_estimate'"' != "" {
    estimates restore `easi_estimate'
    fooddem_export using `"`output'/preferred_easi_coefficients_nlsur_cf.csv"', replace
    fooddem_tests using `"`output'/preferred_easi_tests_nlsur_cf.csv"', ///
        demographics(vhat_stata) replace
    fooddem_elasticities using `"`output'/preferred_easi_elasticities_nlsur_cf_latent.csv"', ///
        margin(latent) minshare(.001) replace
    fooddem_regularity using `"`output'/preferred_easi_regularity_nlsur_cf_latent.csv"', ///
        margin(latent) replace
}

file open meta using `"`output'/preferred_model.txt"', write text replace
file write meta "preferred_model=`best_model'" _n
file write meta "preferred_order=`best_order'" _n
file write meta "preferred_estimate=`best_estimate'" _n
file write meta "preferred_easi_order=`easi_order'" _n
file close meta

log close models
