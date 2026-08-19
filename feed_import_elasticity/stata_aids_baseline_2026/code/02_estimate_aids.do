version 17
clear all
set more off
set linesize 180

args project
if `"`project'"' == "" local project "/root/data/Paper/饲料进口弹性/stata_aids_baseline_2026"
local data   `"`project'/data"'
local output `"`project'/output"'
local logs   `"`project'/logs"'
adopath ++ `"`project'/code"'
do `"`project'/code/nlsur_aids_basic.ado"'
capture log close _all
log using `"`logs'/02_estimate_aids.log"', text replace

use `"`data'/aids_estimation_panel.dta"', clear

* Theory-consistent starting values from a linear Stone-index projection.
gen double y_stone = c_lnx
foreach g in corn sorghum cassava oats barley {
    replace y_stone = y_stone - w_`g' * c_lnp_`g'
}
forvalues j = 1/4 {
    local g : word `j' of corn sorghum cassava oats
    gen double relp`j' = c_lnp_`g' - c_lnp_barley
}

matrix init = J(1, 18, 0)
matrix colnames init = a1 a2 a3 a4 b1 b2 b3 b4 g11 g12 g13 g14 g22 g23 g24 g33 g34 g44
forvalues i = 1/4 {
    local g : word `i' of corn sorghum cassava oats
    quietly regress w_`g' relp1 relp2 relp3 relp4 y_stone
    matrix init[1, `i'] = _b[_cons]
    matrix init[1, `i' + 4] = _b[y_stone]
    forvalues j = 1/4 {
        local raw`i'_`j' = _b[relp`j']
    }
}
local pos = 9
forvalues i = 1/4 {
    forvalues j = `i'/4 {
        matrix init[1, `pos'] = (`raw`i'_`j'' + `raw`j'_`i'') / 2
        local ++pos
    }
}

local initlist ""
local pnames : colnames init
forvalues k = 1/18 {
    local p : word `k' of `pnames'
    local v = init[1, `k']
    local initlist "`initlist' `p' `v'"
}

nlsur basic_aids @ w_corn w_sorghum w_cassava w_oats ///
    c_lnp_corn c_lnp_sorghum c_lnp_cassava c_lnp_oats c_lnp_barley c_lnx, ///
    parameters(`pnames') nequations(4) initial(`initlist') ///
    vce(cluster province_id) iterate(500)

estimates save `"`output'/basic_aids.ster"', replace

tempname mem table
tempfile coef
postfile `mem' str8 parameter double estimate std_error z_value p_value ci_low ci_high str3 significance using `coef', replace
foreach p of local pnames {
    quietly nlcom (value: _b[`p':_cons])
    matrix `table' = r(table)
    local pv = `table'[4,1]
    local stars = cond(`pv' < .01, "***", cond(`pv' < .05, "**", cond(`pv' < .10, "*", "")))
    post `mem' ("`p'") (`table'[1,1]) (`table'[2,1]) (`table'[3,1]) (`pv') ///
        (`table'[5,1]) (`table'[6,1]) ("`stars'")
}
postclose `mem'
preserve
    use `coef', clear
    export delimited using `"`output'/basic_aids_parameters.csv"', replace
restore

quietly test [b1]_cons [b2]_cons [b3]_cons [b4]_cons
scalar chi2_exp = r(chi2)
scalar df_exp = r(df)
scalar p_exp = r(p)
quietly test [g11]_cons [g12]_cons [g13]_cons [g14]_cons [g22]_cons ///
    [g23]_cons [g24]_cons [g33]_cons [g34]_cons [g44]_cons
scalar chi2_price = r(chi2)
scalar df_price = r(df)
scalar p_price = r(p)

preserve
    clear
    set obs 2
    gen str32 test = ""
    replace test = "all_expenditure_terms_zero" in 1
    replace test = "all_price_terms_zero" in 2
    gen double chi2 = .
    gen double df = .
    gen double p_value = .
    replace chi2 = scalar(chi2_exp) in 1
    replace df = scalar(df_exp) in 1
    replace p_value = scalar(p_exp) in 1
    replace chi2 = scalar(chi2_price) in 2
    replace df = scalar(df_price) in 2
    replace p_value = scalar(p_price) in 2
    export delimited using `"`output'/basic_aids_joint_tests.csv"', replace
restore

preserve
    clear
    set obs 1
    gen int N = e(N)
    gen int n_clusters = e(N_clust)
    gen byte converged = e(converged)
    gen double rss = e(rss)
    gen double ll = e(ll)
    gen int n_parameters = 18
    gen str50 vce = "province-clustered delta-method covariance"
    export delimited using `"`output'/basic_aids_model_diagnostics.csv"', replace
restore

log close
