version 17
clear all
set more off
set type double
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_final_corner_review.log",text replace
tempname result integration
postfile `result' str16 level str64 metric double value using "$run/outputs/data_audit/final_corner_review.dta",replace

use "$run/data/corner_household_scenarios_32.dta",clear
confirm string variable hh_id
isid hh_id year scenario_order
assert nobs==1 & total_weight==1 & year==2022
bysort hh_id: assert _N==14
assert full_sample_fit==0 & qualified_forecast==0
quietly count if scenario_order==1
local households=r(N)
post `result' ("micro") ("unique_2022_households") (`households')
quietly count if prediction_valid==0
post `result' ("micro") ("invalid_household_scenarios") (r(N))
gen double __dabudget=0
gen double __dadbudget=0
forvalues j=1/8 {
    assert cr_q`j'>=-1e-10 & cr_dqdm`j'>=-1e-10 if prediction_valid
    assert inrange(cr_pi`j',0,1) if prediction_valid
    assert abs(cr_pi`j'*32-round(cr_pi`j'*32))<1e-10 if prediction_valid
    assert cr_dqdm`j'==0 & cr_pi`j'==0 if prediction_valid & cr_q`j'==0
    replace __dabudget=__dabudget+p`j'*cr_q`j'
    replace __dadbudget=__dadbudget+p`j'*cr_dqdm`j'
}
assert abs(__dabudget/m_new-1)<1e-8 if prediction_valid
assert abs(__dadbudget-1)<1e-8 if prediction_valid
post `result' ("micro") ("quantity_and_derivative_budget_closure_pass") (1)
tempfile source expected d64
save `source',replace

foreach level in province family {
    use `source',clear
    if "`level'"=="province" local groups province province_name scenario_order horizon growth_rate growth_factor
    else local groups type scenario_order horizon growth_rate growth_factor
    local averages
    forvalues j=1/8 {
        gen double avgfitq`j'=cr_q`j'
        gen double avgv`j'=p`j'*cr_q`j'
        gen double avgpi`j'=cr_pi`j'
        gen double avgbq`j'=cr_dqdm`j'*m_new
        gen double avgiq`j'=cr_dqdm`j'*m_new*eta_budget_income_new
        local averages `averages' avgfitq`j' avgv`j' avgpi`j' avgbq`j' avgiq`j'
    }
    gen long __daone=1
    gen long __dainvalid=prediction_valid==0
    collapse (mean) avg_budget=m_new `averages' (sum) check_households=__daone check_invalid=__dainvalid,by(`groups')
    save `expected',replace
    use "$run/outputs/corner_scenarios/`level'_income_growth_32.dta",clear
    merge 1:1 `groups' using `expected',assert(match) nogen
    assert total_weight==check_households & invalid_weight==check_invalid
    assert complete_coverage==(check_invalid==0)
    assert full_sample_fit==0 & qualified_forecast==0
    bysort scenario_order: egen double __households=sum(total_weight)
    assert __households==`households'
    gen double __share_sum=0
    gen double __eta_add=0
    forvalues j=1/8 {
        assert abs(quantity`j'-avgfitq`j')<1e-10*max(1,avgfitq`j') if complete_coverage
        assert abs(share`j'-avgv`j'/avg_budget)<1e-10 if complete_coverage
        assert abs(purchase_prob`j'-avgpi`j')<1e-10 if complete_coverage
        assert abs(budget_elasticity`j'-avgbq`j'/avgfitq`j')<1e-10*max(1,abs(budget_elasticity`j')) if complete_coverage & avgfitq`j'>0
        assert abs(income_elasticity`j'-avgiq`j'/avgfitq`j')<1e-10*max(1,abs(income_elasticity`j')) if complete_coverage & avgfitq`j'>0
        assert missing(budget_elasticity`j') & missing(income_elasticity`j') if complete_coverage & avgfitq`j'==0
        foreach statistic in quantity share purchase_prob budget_elasticity income_elasticity {
            assert missing(`statistic'`j') if !complete_coverage
        }
        replace __share_sum=__share_sum+share`j'
        replace __eta_add=__eta_add+cond(share`j'==0,0,share`j'*budget_elasticity`j')
    }
    assert abs(__share_sum-1)<1e-10 if complete_coverage
    if "`level'"=="province" assert abs(__eta_add-1)<1e-8 if complete_coverage
    quietly count
    post `result' ("`level'") ("aggregate_scenario_groups") (r(N))
    quietly count if complete_coverage
    post `result' ("`level'") ("groups_with_complete_prediction_coverage") (r(N))
    post `result' ("`level'") ("household_weights_shares_and_aggregate_derivatives_pass") (1)
    if "`level'"=="family" {
        gen double __heterogeneous_price_gap=abs(__eta_add-1)
        quietly summarize __heterogeneous_price_gap if complete_coverage,meanonly
        post `result' ("`level'") ("quantity_elasticity_share_add_gap_heterogeneous_prices") (r(max))
    }
}
postclose `result'
use "$run/outputs/data_audit/final_corner_review.dta",clear
export delimited using "$run/outputs/data_audit/final_corner_review.csv",replace
list,noobs abbreviate(64)

* Deterministic nested integration comparison, not sampling inference.
use "$run/data/corner_scenario_sensitivity_64.dta",clear
confirm string variable hh_id
isid hh_id scenario_order
foreach v of varlist prediction_valid cr_q* cr_dqdm* cr_pi* {
    rename `v' d64_`v'
}
save `d64',replace
use `source',clear
merge 1:1 hh_id scenario_order using `d64',keep(match) assert(master match) nogen
assert inlist(scenario_order,1,4)
assert prediction_valid==1 & d64_prediction_valid==1
postfile `integration' byte good double household_scenarios double mean_normalized_quantity_gap ///
    double max_normalized_quantity_gap double mean_abs_budget_derivative_gap double max_abs_budget_derivative_gap ///
    double mean_abs_participation_gap double max_abs_participation_gap double extra_positive_at_64 ///
    using "$run/outputs/data_audit/corner_integration_review.dta",replace
forvalues j=1/8 {
    gen double __dq=abs(d64_cr_q`j'-cr_q`j')/max(1,cr_q`j',d64_cr_q`j')
    gen double __dd=abs(d64_cr_dqdm`j'-cr_dqdm`j')
    gen double __dp=abs(d64_cr_pi`j'-cr_pi`j')
    quietly summarize __dq,meanonly
    scalar DAqmean=r(mean)
    scalar DAqmax=r(max)
    quietly summarize __dd,meanonly
    scalar DAdmean=r(mean)
    scalar DAdmax=r(max)
    quietly summarize __dp,meanonly
    scalar DApmean=r(mean)
    scalar DApmax=r(max)
    quietly count if cr_q`j'==0 & d64_cr_q`j'>0
    post `integration' (`j') (_N) (scalar(DAqmean)) (scalar(DAqmax)) (scalar(DAdmean)) ///
        (scalar(DAdmax)) (scalar(DApmean)) (scalar(DApmax)) (r(N))
    drop __dq __dd __dp
}
postclose `integration'
use "$run/outputs/data_audit/corner_integration_review.dta",clear
export delimited using "$run/outputs/data_audit/corner_integration_review.csv",replace
list,noobs
log close
