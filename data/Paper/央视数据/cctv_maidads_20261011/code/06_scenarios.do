version 17
clear all
set more off
set type double
args modeldir
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
if "`modeldir'"=="" local modeldir "$ROOT/outputs/estimation/maidads_8"
confirm file "`modeldir'/model_summary.csv"
capture mkdir "$ROOT/outputs/scenarios"
capture log close _all
log using "$ROOT/logs/06_scenarios.log",text replace
use "$ROOT/data/household_year_income_8.dta",clear
gen double nobs=1
merge m:1 type using "$ROOT/data/income_support_8.dta",assert(match) nogen
gen long scenario_cell=_n
gen double baseline_m=m
expand 14
bysort scenario_cell: gen byte scenario_order=_n
gen int horizon=2022
gen double growth_rate=.
gen double growth_factor=cond(scenario_order==1,1,cond(scenario_order==2,1.1,cond(scenario_order==3,1.25,cond(scenario_order==4,1.5,2)))) if scenario_order<=5
forvalues j=6/14 {
    local h=cond(`j'<=8,2030,cond(`j'<=11,2035,2050))
    local r=(mod(`j'-6,3)+1)/100
    replace horizon=`h' if scenario_order==`j'
    replace growth_rate=`r' if scenario_order==`j'
    replace growth_factor=(1+`r')^(`h'-2022) if scenario_order==`j'
}
gen double d=ln(growth_factor)
gen double budget_factor=exp(budget_linear*d+budget_quadratic*(2*inc1*d+d^2))
gen double m_new=baseline_m*budget_factor
gen double eta_budget_income_new=budget_linear+2*budget_quadratic*(inc1+d)
gen double income_pc_new=income_pc_mean*growth_factor
gen byte beyond_proxy_support=lnypc_mean+d>max_lny | lnypc_mean+d<min_lny
gen byte beyond_central_support=lnypc_mean+d>p99_lny | lnypc_mean+d<p1_lny
gen byte negative_budget_income=eta_budget_income_new<0
gen str24 income_unit="reported unit / proxy size"
gen str24 price_scenario="fixed province 2022"
* Province annual prices are fixed across baseline and income scenarios.
forvalues j=1/8 {
    drop p`j'
}
merge m:1 province_name year using "$ROOT/data/prices_year_8.dta",keep(master match) nogen
forvalues j=1/8 {
    assert p`j'>0 & p`j'<.
}
export delimited using "$ROOT/data/scenario_inputs_8.csv",replace
save "$ROOT/data/scenario_inputs_8.dta",replace
log close
do "$ROOT/code/06_predict.do" "$ROOT/data/scenario_inputs_8.dta" "`modeldir'" "$ROOT/outputs/scenarios/pooled" 8
use "$ROOT/outputs/scenarios/pooled/predictions.dta",clear
gen str160 model_source="`modeldir'"
forvalues j=1/8 {
    gen double eta_income`j'=eta`j'*eta_budget_income_new
    gen double value`j'=p`j'*fitq`j'
}
save "$ROOT/outputs/scenarios/cell_scenarios.dta",replace
export delimited using "$ROOT/outputs/scenarios/cell_scenarios.csv",replace
* Invalid cells block a complete province summary instead of being dropped.
gen double invalid_weight=nobs*(prediction_valid==0)
gen double total_weight=nobs
gen double out_of_support_weight=nobs*beyond_proxy_support
gen double out_of_central_weight=nobs*beyond_central_support
gen double negative_budget_slope_weight=nobs*negative_budget_income
gen double beyond_fit_weight=nobs*beyond_fitted_budget_support
foreach aggregation in province family {
    preserve
    if "`aggregation'"=="province" local by province province_name scenario_order horizon growth_rate growth_factor
    else local by type scenario_order horizon growth_rate growth_factor
    local sums total_weight invalid_weight out_of_support_weight out_of_central_weight negative_budget_slope_weight beyond_fit_weight
    forvalues j=1/8 {
        gen double qsum`j'=fitq`j'*nobs
        gen double q0sum`j'=q`j'*nobs
        gen double vsum`j'=value`j'*nobs
        gen double msumn`j'=eta`j'*fitq`j'*nobs
        gen double isumn`j'=eta_income`j'*fitq`j'*nobs
        local sums `sums' qsum`j' q0sum`j' vsum`j' msumn`j' isumn`j'
    }
    gen double budget_sum=m_new*nobs
    local sums `sums' budget_sum
    collapse (sum) `sums' (max) budget_error utility_equation_error (first) estimate_stationary estimate_qualified estimate_score model_source,by(`by')
    gen byte complete_coverage=invalid_weight==0
    gen byte qualified_forecast=complete_coverage & estimate_stationary & estimate_qualified
    gen str60 result_status=cond(qualified_forecast,"qualified conditional scenario","unqualified parameter diagnostic; not formal forecast")
    gen double out_of_support_share=out_of_support_weight/total_weight
    gen double out_of_central_share=out_of_central_weight/total_weight
    gen double negative_budget_slope_share=negative_budget_slope_weight/total_weight
    gen double beyond_fitted_budget_share=beyond_fit_weight/total_weight
    forvalues j=1/8 {
        gen double quantity`j'=qsum`j'/total_weight if complete_coverage
        gen double share`j'=vsum`j'/budget_sum if complete_coverage
        gen double budget_elasticity`j'=msumn`j'/qsum`j' if complete_coverage
        gen double income_elasticity`j'=isumn`j'/qsum`j' if complete_coverage
        gen double formal_income_elasticity`j'=income_elasticity`j' if qualified_forecast
        gen double formal_quantity`j'=quantity`j' if qualified_forecast
        if "`aggregation'"=="province" {
            bysort province: egen double baseline_quantity`j'=max(cond(scenario_order==1,quantity`j',.))
        }
        else {
            bysort type: egen double baseline_quantity`j'=max(cond(scenario_order==1,quantity`j',.))
        }
        gen double quantity_index`j'=100*quantity`j'/baseline_quantity`j' if complete_coverage
    }
    save "$ROOT/outputs/scenarios/`aggregation'_income_growth.dta",replace
    export delimited using "$ROOT/outputs/scenarios/`aggregation'_income_growth.csv",replace
    restore
}
