version 17
clear all
set more off
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$cmroot/logs/03_corner_read_summary.log", text replace
import delimited "$cmroot/outputs/corner/price_response_all_4_families.csv", clear asdouble
keep if good==price_good
drop price_good
save "$cmroot/tmp_corner_support/own_response.dta", replace
import delimited "$cmroot/outputs/corner/fit_status.csv", clear asdouble
scalar cm_table_scale=budget_scale[1]
import delimited "$cmroot/outputs/corner/budget_response_curve_all_4_families.csv", clear asdouble
keep if abs(budget_percap_month-cm_table_scale)<1e-8
merge 1:1 type good using "$cmroot/tmp_corner_support/own_response.dta", assert(match) nogen
assert _N==32
generate str48 evaluation_state="training_mean_prices_and_full_training_median_m"
sort type good
export delimited "$cmroot/outputs/corner/own_price_and_budget_at_median_all_4_families.csv", replace
format budget_total budget_participation budget_conditional marshall_total hicks_total %9.4f
list type good budget_total budget_participation budget_conditional marshall_total hicks_total, sepby(type) noobs
summarize hicks_total marshall_total budget_total
display "CORNER_ALL_OWN_PRICE_AND_BUDGET_TABLE_READY"
log close
