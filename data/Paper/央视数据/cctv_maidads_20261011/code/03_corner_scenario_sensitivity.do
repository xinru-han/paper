version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$ROOT/logs/03_corner_scenario_sensitivity.log",text replace
use "$ROOT/data/corner_household_scenarios_32.dta",clear
keep if inlist(scenario_order,1,4)
egen long __hh=group(hh_id)
keep if mod(__hh,100)==0
local keepvars hh_id scenario_order prediction_valid
forvalues j=1/8 {
    local keepvars `keepvars' cr_q`j' cr_dqdm`j' cr_pi`j'
}
keep `keepvars'
rename prediction_valid valid32
forvalues j=1/8 {
    rename cr_q`j' q32_`j'
    rename cr_dqdm`j' dq32_`j'
    rename cr_pi`j' pi32_`j'
}
merge 1:1 hh_id scenario_order using "$ROOT/data/corner_scenario_sensitivity_64.dta",assert(match) nogen
assert prediction_valid==1 & valid32==1
tempname result
postfile `result' byte good double cases double zero_quantity_either_draws ///
    double mean_abs_relative_quantity_gap double max_abs_relative_quantity_gap ///
    double mean_abs_participation_gap double max_abs_participation_gap ///
    double mean_abs_budget_derivative_gap double max_abs_budget_derivative_gap ///
    using "$ROOT/tmp/corner_scenario_integration.dta",replace
forvalues j=1/8 {
    gen double qgap=abs(q32_`j'-cr_q`j')/cr_q`j' if cr_q`j'>1e-12 & q32_`j'>1e-12
    gen double pgap=abs(pi32_`j'-cr_pi`j')
    gen double dgap=abs(dq32_`j'-cr_dqdm`j')
    quietly count if q32_`j'<=1e-12 | cr_q`j'<=1e-12
    local zeros=r(N)
    quietly summarize qgap,meanonly
    local qm=r(mean)
    local qx=r(max)
    quietly summarize pgap,meanonly
    local pm=r(mean)
    local px=r(max)
    quietly summarize dgap,meanonly
    post `result' (`j') (_N) (`zeros') (`qm') (`qx') (`pm') (`px') (r(mean)) (r(max))
    drop qgap pgap dgap
}
postclose `result'
use "$ROOT/tmp/corner_scenario_integration.dta",clear
gen str150 scope="Every 100th sorted 2022 household, baseline and income+50%; same fitted theta; integration sensitivity, not sampling CI"
export delimited using "$ROOT/outputs/corner_scenarios/integration_sensitivity_32_64.csv",replace
log close
