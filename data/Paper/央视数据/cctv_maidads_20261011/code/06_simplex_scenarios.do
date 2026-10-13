version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "$ROOT/outputs/scenarios_simplex"
local coarse "$ROOT/outputs/estimation/maidads_8_coarse_simplex_multistart"
local elderly "$ROOT/outputs/estimation/maidads_family_3_simplex_multistart"
do "$ROOT/code/06_predict.do" "$ROOT/data/scenario_inputs_8.dta" "`coarse'" "$ROOT/outputs/scenarios_simplex/pooled_micro" 8
do "$ROOT/code/06_aggregate_native.do" "$ROOT/outputs/scenarios_simplex/pooled_micro/predictions.dta" "$ROOT/outputs/scenarios_simplex/pooled_micro" "Quarter coarse-cell fit evaluated on individual annual budgets; diagnostic only"
do "$ROOT/code/06_predict.do" "$ROOT/data/scenario_inputs_8.dta" "`elderly'" "$ROOT/outputs/scenarios_simplex/elderly_micro" 8 "type==3"
do "$ROOT/code/06_aggregate_native.do" "$ROOT/outputs/scenarios_simplex/elderly_micro/predictions.dta" "$ROOT/outputs/scenarios_simplex/elderly_micro" "Elderly cell fit evaluated on individual annual budgets; diagnostic only"
use "$ROOT/data/scenario_inputs_8.dta",clear
gen double budget_income_response=m_new*eta_budget_income_new
local meanvars m m_new baseline_m income_pc_new beyond_proxy_support beyond_central_support negative_budget_income
forvalues j=1/8 {
    local meanvars `meanvars' p`j' q`j'
}
* Representative province-family budgets are an explicit aggregation sensitivity.
collapse (sum) nobs budget_income_response (mean) `meanvars', ///
    by(province province_name type scenario_order horizon growth_rate growth_factor)
gen double eta_budget_income_new=budget_income_response/(nobs*m_new)
save "$ROOT/data/simplex_representative_cohort_inputs.dta",replace
do "$ROOT/code/06_predict.do" "$ROOT/data/simplex_representative_cohort_inputs.dta" "`coarse'" "$ROOT/outputs/scenarios_simplex/cohort_mean" 8
do "$ROOT/code/06_aggregate_native.do" "$ROOT/outputs/scenarios_simplex/cohort_mean/predictions.dta" "$ROOT/outputs/scenarios_simplex/cohort_mean" "Representative province-family mean budget sensitivity; q(mean budget) rather than average individual demand"
