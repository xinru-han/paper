version 17
clear all
set more off
set linesize 180

args project
if `"`project'"' == "" local project "/root/data/Paper/饲料进口弹性/stata_aids_baseline_2026"
local data   `"`project'/data"'
local output `"`project'/output"'
local logs   `"`project'/logs"'
do `"`project'/code/nlsur_demand_extended.ado"'
capture log close _all
log using `"`logs'/05_estimate_extended_models.log"', text replace

use `"`data'/aids_estimation_panel.dta"', clear
local goods "corn sorghum cassava oats barley"
local zvars "c_lnx c_lnp_corn c_lnp_sorghum c_lnp_cassava c_lnp_oats c_lnp_barley"

tempname selmem srefmem table
tempfile selection selection_ref
postfile `selmem' str10 product str18 variable double estimate std_error z_value p_value ci_low ci_high using `selection', replace
postfile `srefmem' str10 product double participation_rate intercept phi_ref pdf_ref ///
    bx bp_corn bp_sorghum bp_cassava bp_oats bp_barley using `selection_ref', replace

forvalues i = 1/5 {
    local g : word `i' of `goods'
    gen byte part_`g' = w_`g' > 0
    quietly summarize part_`g', meanonly
    local rate = r(mean)
    quietly probit part_`g' `zvars', vce(cluster province_id) iterate(200)
    predict double sy_xb`i' if e(sample), xb
    gen double sy_Phi`i' = normal(sy_xb`i')
    gen double sy_pdf`i' = normalden(sy_xb`i')
    foreach z in _cons `zvars' {
        local bhat = _b[`z']
        local seh = _se[`z']
        local zh = `bhat' / `seh'
        local ph = 2*normal(-abs(`zh'))
        local loh = `bhat' - invnormal(.975)*`seh'
        local hih = `bhat' + invnormal(.975)*`seh'
        post `selmem' ("`g'") ("`z'") (`bhat') (`seh') (`zh') (`ph') (`loh') (`hih')
    }
    local c = _b[_cons]
    local phiref = normal(`c')
    local pdfref = normalden(`c')
    post `srefmem' ("`g'") (`rate') (`c') (`phiref') (`pdfref') ///
        (_b[c_lnx]) (_b[c_lnp_corn]) (_b[c_lnp_sorghum]) ///
        (_b[c_lnp_cassava]) (_b[c_lnp_oats]) (_b[c_lnp_barley])
}
postclose `selmem'
postclose `srefmem'
preserve
    use `selection', clear
    export delimited using `"`output'/sy_selection_parameters.csv"', replace
restore
preserve
    use `selection_ref', clear
    export delimited using `"`output'/sy_selection_reference.csv"', replace
restore
save `"`data'/extended_estimation_panel.dta"', replace

local aids_p "a1 a2 a3 a4 b1 b2 b3 b4 g11 g12 g13 g14 g22 g23 g24 g33 g34 g44"
local quaids_p "a1 a2 a3 a4 b1 b2 b3 b4 l1 l2 l3 l4 g11 g12 g13 g14 g22 g23 g24 g33 g34 g44"
local sy_aids_p "`aids_p' d1 d2 d3 d4 d5"
local sy_quaids_p "`quaids_p' d1 d2 d3 d4 d5"

estimates use `"`output'/basic_aids.ster"'
local aids_init ""
foreach p of local aids_p {
    local v = _b[`p':_cons]
    local aids_init "`aids_init' `p' `v'"
}
local quaids_init ""
foreach p in a1 a2 a3 a4 b1 b2 b3 b4 {
    local v = _b[`p':_cons]
    local quaids_init "`quaids_init' `p' `v'"
}
foreach p in l1 l2 l3 l4 {
    local quaids_init "`quaids_init' `p' 0"
}
foreach p in g11 g12 g13 g14 g22 g23 g24 g33 g34 g44 {
    local v = _b[`p':_cons]
    local quaids_init "`quaids_init' `p' `v'"
}

nlsur quaids_ext @ w_corn w_sorghum w_cassava w_oats ///
    c_lnp_corn c_lnp_sorghum c_lnp_cassava c_lnp_oats c_lnp_barley c_lnx, ///
    parameters(`quaids_p') nequations(4) initial(`quaids_init') ///
    vce(cluster province_id) iterate(500)
estimates save `"`output'/quaids.ster"', replace

local sy_aids_init "`aids_init' d1 0 d2 0 d3 0 d4 0 d5 0"
nlsur sy_aids_ext @ w_corn w_sorghum w_cassava w_oats w_barley ///
    c_lnp_corn c_lnp_sorghum c_lnp_cassava c_lnp_oats c_lnp_barley c_lnx ///
    sy_Phi1 sy_Phi2 sy_Phi3 sy_Phi4 sy_Phi5 ///
    sy_pdf1 sy_pdf2 sy_pdf3 sy_pdf4 sy_pdf5, ///
    parameters(`sy_aids_p') nequations(5) initial(`sy_aids_init') ///
    vce(cluster province_id) iterate(500)
estimates save `"`output'/sy_aids.ster"', replace

estimates use `"`output'/quaids.ster"'
local sy_quaids_init ""
foreach p of local quaids_p {
    local v = _b[`p':_cons]
    local sy_quaids_init "`sy_quaids_init' `p' `v'"
}
local sy_quaids_init "`sy_quaids_init' d1 0 d2 0 d3 0 d4 0 d5 0"
nlsur sy_quaids_ext @ w_corn w_sorghum w_cassava w_oats w_barley ///
    c_lnp_corn c_lnp_sorghum c_lnp_cassava c_lnp_oats c_lnp_barley c_lnx ///
    sy_Phi1 sy_Phi2 sy_Phi3 sy_Phi4 sy_Phi5 ///
    sy_pdf1 sy_pdf2 sy_pdf3 sy_pdf4 sy_pdf5, ///
    parameters(`sy_quaids_p') nequations(5) initial(`sy_quaids_init') ///
    vce(cluster province_id) iterate(500)
estimates save `"`output'/sy_quaids.ster"', replace

tempname pmem dmem tmem
tempfile pars diagnostics tests
postfile `pmem' str12 model str8 parameter double estimate std_error z_value p_value ci_low ci_high str3 significance using `pars', replace
postfile `dmem' str12 model int N n_clusters n_parameters byte converged double ll aic bic using `diagnostics', replace
postfile `tmem' str12 model str30 test double chi2 df p_value using `tests', replace

foreach model in quaids sy_aids sy_quaids {
    estimates use `"`output'/`model'.ster"'
    local pnames "`quaids_p'"
    if "`model'" == "sy_aids" local pnames "`sy_aids_p'"
    if "`model'" == "sy_quaids" local pnames "`sy_quaids_p'"
    local k : word count `pnames'
    local N = e(N)
    local nc = e(N_clust)
    local conv = e(converged)
    local ll = e(ll)
    local aic = -2*`ll' + 2*`k'
    local bic = -2*`ll' + ln(`N')*`k'
    post `dmem' ("`model'") (`N') (`nc') (`k') (`conv') (`ll') (`aic') (`bic')
    foreach p of local pnames {
        quietly nlcom (value: _b[`p':_cons])
        matrix `table' = r(table)
        local pv = `table'[4,1]
        local stars = cond(`pv' < .01, "***", cond(`pv' < .05, "**", cond(`pv' < .10, "*", "")))
        post `pmem' ("`model'") ("`p'") (`table'[1,1]) (`table'[2,1]) ///
            (`table'[3,1]) (`pv') (`table'[5,1]) (`table'[6,1]) ("`stars'")
    }
    quietly test [g11]_cons [g12]_cons [g13]_cons [g14]_cons [g22]_cons ///
        [g23]_cons [g24]_cons [g33]_cons [g34]_cons [g44]_cons
    post `tmem' ("`model'") ("all_price_terms_zero") (r(chi2)) (r(df)) (r(p))
    if inlist("`model'", "quaids", "sy_quaids") {
        quietly test [l1]_cons [l2]_cons [l3]_cons [l4]_cons
        post `tmem' ("`model'") ("all_quadratic_terms_zero") (r(chi2)) (r(df)) (r(p))
    }
    if inlist("`model'", "sy_aids", "sy_quaids") {
        quietly test [d1]_cons [d2]_cons [d3]_cons [d4]_cons [d5]_cons
        post `tmem' ("`model'") ("all_SY_density_terms_zero") (r(chi2)) (r(df)) (r(p))
    }
}
postclose `pmem'
postclose `dmem'
postclose `tmem'
preserve
    use `pars', clear
    export delimited using `"`output'/extended_model_parameters.csv"', replace
restore
preserve
    use `diagnostics', clear
    export delimited using `"`output'/extended_model_diagnostics.csv"', replace
restore
preserve
    use `tests', clear
    export delimited using `"`output'/extended_model_joint_tests.csv"', replace
restore

log close
