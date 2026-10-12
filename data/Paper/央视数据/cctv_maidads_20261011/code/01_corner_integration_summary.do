version 17
clear all
set more off
set type double
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_corner_integration_summary.log",text replace
tempfile keys anchor reference
use "$run/data/corner_scenario_sensitivity_64.dta",clear
confirm string variable hh_id
keep hh_id scenario_order
isid hh_id scenario_order
local expected=_N
assert `expected'==454
save `keys',replace
use "$run/data/scenario_inputs_8.dta",clear
keep if inlist(scenario_order,1,4)
local inputs hh_id scenario_order m_new eta_budget_income_new growth_factor
forvalues j=1/8 {
    local inputs `inputs' p`j'
}
keep `inputs'
isid hh_id scenario_order
save `anchor',replace

tempname result
postfile `result' int draws byte good byte scenario_order long households double mean_quantity ///
    double budget_elasticity double income_elasticity double mean_participation double spending_share ///
    double mean_budget using "$run/outputs/data_audit/corner_integration_summary.dta",replace
foreach draws in 32 64 128 256 {
    if `draws'==32 use "$run/data/corner_household_scenarios_32.dta",clear
    else use "$run/data/corner_scenario_sensitivity_`draws'.dta",clear
    local responses hh_id scenario_order prediction_valid
    forvalues j=1/8 {
        local responses `responses' cr_q`j' cr_dqdm`j' cr_pi`j'
    }
    keep `responses'
    merge 1:1 hh_id scenario_order using `keys',keep(match) assert(master match) nogen
    assert _N==`expected' & prediction_valid==1
    merge 1:1 hh_id scenario_order using `anchor',keep(match) assert(using match) nogen
    assert _N==`expected'
    bysort hh_id: assert _N==2
    gen double __budget=0
    gen double __dbudget=0
    forvalues j=1/8 {
        replace __budget=__budget+p`j'*cr_q`j'
        replace __dbudget=__dbudget+p`j'*cr_dqdm`j'
    }
    assert abs(__budget/m_new-1)<1e-8
    assert abs(__dbudget-1)<1e-8
    foreach scenario in 1 4 {
        quietly count if scenario_order==`scenario'
        local nn=r(N)
        assert `nn'==227
        quietly summarize m_new if scenario_order==`scenario',meanonly
        local meanbudget=r(mean)
        local budgetsum=r(sum)
        forvalues j=1/8 {
            quietly summarize cr_q`j' if scenario_order==`scenario',meanonly
            scalar DA_qmean=r(mean)
            scalar DA_qsum=r(sum)
            assert scalar(DA_qsum)>0
            quietly summarize cr_pi`j' if scenario_order==`scenario',meanonly
            scalar DA_pmean=r(mean)
            gen double __b=cr_dqdm`j'*m_new
            gen double __i=__b*eta_budget_income_new
            gen double __v=p`j'*cr_q`j'
            quietly summarize __b if scenario_order==`scenario',meanonly
            scalar DA_beta=r(sum)/scalar(DA_qsum)
            quietly summarize __i if scenario_order==`scenario',meanonly
            scalar DA_income=r(sum)/scalar(DA_qsum)
            quietly summarize __v if scenario_order==`scenario',meanonly
            scalar DA_share=r(sum)/`budgetsum'
            post `result' (`draws') (`j') (`scenario') (`nn') (scalar(DA_qmean)) (scalar(DA_beta)) ///
                (scalar(DA_income)) (scalar(DA_pmean)) (scalar(DA_share)) (`meanbudget')
            drop __b __i __v
        }
    }
}
postclose `result'
use "$run/outputs/data_audit/corner_integration_summary.dta",clear
bysort draws good: egen double baseline_quantity=max(cond(scenario_order==1,mean_quantity,.))
gen double quantity_index=100*mean_quantity/baseline_quantity
bysort draws scenario_order: egen double __share_sum=sum(spending_share)
assert abs(__share_sum-1)<1e-10
drop __share_sum
preserve
keep if draws==32
keep good scenario_order mean_quantity quantity_index income_elasticity mean_participation
foreach v in mean_quantity quantity_index income_elasticity mean_participation {
    rename `v' d32_`v'
}
save `reference',replace
restore
merge m:1 good scenario_order using `reference',assert(match) nogen
gen double quantity_relative_gap_vs32=mean_quantity/d32_mean_quantity-1
gen double quantity_index_gap_vs32=quantity_index-d32_quantity_index
gen double income_elasticity_gap_vs32=income_elasticity-d32_income_elasticity
gen double participation_gap_vs32=mean_participation-d32_mean_participation
bysort good scenario_order (draws): gen double quantity_relative_gap_previous=mean_quantity/mean_quantity[_n-1]-1
bysort good scenario_order (draws): gen double quantity_index_gap_previous=quantity_index-quantity_index[_n-1]
bysort good scenario_order (draws): gen double income_elasticity_gap_previous=income_elasticity-income_elasticity[_n-1]
sort scenario_order good draws
save "$run/outputs/data_audit/corner_integration_summary.dta",replace
export delimited using "$run/outputs/data_audit/corner_integration_summary.csv",replace
foreach table in baseline_quantity growth50_quantity_index growth50_income_elasticity {
    preserve
    if "`table'"=="baseline_quantity" {
        keep if scenario_order==1
        local field mean_quantity
    }
    else {
        keep if scenario_order==4
        if "`table'"=="growth50_quantity_index" local field quantity_index
        else local field income_elasticity
    }
    keep good draws `field'
    reshape wide `field',i(good) j(draws)
    export delimited using "$run/outputs/data_audit/corner_integration_`table'.csv",replace
    restore
}
list draws good mean_quantity quantity_index income_elasticity quantity_relative_gap_previous quantity_index_gap_previous income_elasticity_gap_previous if scenario_order==4,noobs
preserve
gen double abs_quantity_gap=abs(quantity_relative_gap_previous)
gen double abs_index_gap=abs(quantity_index_gap_previous)
gen double abs_income_gap=abs(income_elasticity_gap_previous)
collapse (mean) mean_abs_quantity_gap=abs_quantity_gap mean_abs_index_gap=abs_index_gap mean_abs_income_gap=abs_income_gap ///
    (max) max_abs_quantity_gap=abs_quantity_gap max_abs_index_gap=abs_index_gap max_abs_income_gap=abs_income_gap,by(draws scenario_order)
export delimited using "$run/outputs/data_audit/corner_integration_step_summary.csv",replace
list,noobs
restore
log close
