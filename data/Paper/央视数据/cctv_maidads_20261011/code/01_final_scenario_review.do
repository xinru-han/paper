version 17
clear all
set more off
set type double
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_final_scenario_review.log",text replace
tempname result
postfile `result' str16 level str56 metric double value using "$run/outputs/data_audit/final_scenario_review.dta",replace

use "$run/outputs/scenarios/cell_scenarios.dta",clear
confirm string variable hh_id
isid hh_id year scenario_order
assert nobs==1 & year==2022
bysort hh_id: assert _N==14
quietly count if scenario_order==1
local households=r(N)
post `result' ("micro") ("unique_2022_households") (`households')
quietly count if prediction_valid==0
post `result' ("micro") ("invalid_household_scenarios") (r(N))
quietly count if estimate_stationary==0 | estimate_qualified==0
post `result' ("micro") ("unqualified_parameter_household_scenarios") (r(N))
quietly summarize estimate_score,meanonly
post `result' ("micro") ("candidate_projected_gradient") (r(mean))
tempfile source expected
save `source',replace

foreach level in province family {
    use `source',clear
    if "`level'"=="province" local groups province province_name scenario_order horizon growth_rate growth_factor
    else local groups type scenario_order horizon growth_rate growth_factor
    local averages
    forvalues j=1/8 {
        gen double avgfitq`j'=fitq`j'
        gen double avgv`j'=p`j'*fitq`j'
        gen double avgeq`j'=eta`j'*fitq`j'
        gen double avgeiq`j'=eta`j'*eta_budget_income_new*fitq`j'
        local averages `averages' avgfitq`j' avgv`j' avgeq`j' avgeiq`j'
    }
    gen long __daone=1
    gen long __dainvalid=prediction_valid==0
    collapse (mean) avg_budget=m_new `averages' (sum) check_households=__daone check_invalid=__dainvalid,by(`groups')
    save `expected',replace
    use "$run/outputs/scenarios/`level'_income_growth.dta",clear
    merge 1:1 `groups' using `expected',assert(match) nogen
    assert total_weight==check_households & invalid_weight==check_invalid
    assert complete_coverage==(check_invalid==0)
    assert qualified_forecast==(complete_coverage & estimate_stationary & estimate_qualified)
    bysort scenario_order: egen double __households=sum(total_weight)
    assert __households==`households'
    forvalues j=1/8 {
        assert abs(quantity`j'-avgfitq`j')<1e-10*max(1,avgfitq`j') if complete_coverage
        assert abs(share`j'-avgv`j'/avg_budget)<1e-10 if complete_coverage
        assert abs(budget_elasticity`j'-avgeq`j'/avgfitq`j')<1e-10*max(1,abs(budget_elasticity`j')) if complete_coverage
        assert abs(income_elasticity`j'-avgeiq`j'/avgfitq`j')<1e-10*max(1,abs(income_elasticity`j')) if complete_coverage
        foreach statistic in quantity share budget_elasticity income_elasticity {
            assert missing(`statistic'`j') if !complete_coverage
        }
        assert missing(formal_quantity`j') if !qualified_forecast
        assert missing(formal_income_elasticity`j') if !qualified_forecast
        assert abs(quantity_index`j'-100)<1e-10 if scenario_order==1 & complete_coverage
    }
    quietly count
    post `result' ("`level'") ("aggregate_scenario_groups") (r(N))
    quietly count if complete_coverage
    post `result' ("`level'") ("groups_with_complete_prediction_coverage") (r(N))
    quietly count if qualified_forecast
    post `result' ("`level'") ("qualified_formal_forecast_groups") (r(N))
    post `result' ("`level'") ("unique_household_weight_and_aggregate_derivatives_pass") (1)
}
postclose `result'
use "$run/outputs/data_audit/final_scenario_review.dta",clear
export delimited using "$run/outputs/data_audit/final_scenario_review.csv",replace
list,noobs abbreviate(56)
log close
