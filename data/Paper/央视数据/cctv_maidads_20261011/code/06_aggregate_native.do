version 17
clear all
set more off
set type double
args input out modelscope
capture mkdir "`out'"
capture log close _all
log using "`out'/aggregate.log",text replace
use "`input'",clear
gen str200 model_scope="`modelscope'"
gen double invalid_weight=nobs*(prediction_valid==0)
gen double total_weight=nobs
gen double income_support_weight=nobs*beyond_proxy_support
gen double central_income_support_weight=nobs*beyond_central_support
gen double fitted_budget_support_weight=nobs*beyond_fitted_budget_support
gen double negative_income_budget_weight=nobs*negative_budget_income
forvalues j=1/8 {
    gen double eta_income`j'=eta`j'*eta_budget_income_new
}
foreach aggregation in province family {
    preserve
    if "`aggregation'"=="province" local by province province_name scenario_order horizon growth_rate growth_factor
    else local by type scenario_order horizon growth_rate growth_factor
    local sums invalid_weight total_weight income_support_weight central_income_support_weight fitted_budget_support_weight negative_income_budget_weight
    forvalues j=1/8 {
        gen double qsum`j'=fitq`j'*nobs
        gen double vsum`j'=p`j'*fitq`j'*nobs
        gen double bsum`j'=eta`j'*fitq`j'*nobs
        gen double isum`j'=eta_income`j'*fitq`j'*nobs
        local sums `sums' qsum`j' vsum`j' bsum`j' isum`j'
    }
    gen double budget_sum=m_new*nobs
    collapse (sum) `sums' budget_sum (max) budget_error utility_equation_error ///
        (first) estimate_stationary estimate_qualified estimate_score evaluation_kernel model_scope,by(`by')
    gen byte complete_coverage=invalid_weight==0
    gen byte point_model_qualified=estimate_stationary & estimate_qualified
    gen byte numeric_scenario_qualified=complete_coverage & point_model_qualified
    gen byte qualified_forecast=0
    gen str120 result_status="Conditional point-model sensitivity; predictive validation and individual-unit interpretation not established"
    gen double income_out_of_support_share=income_support_weight/total_weight
    gen double budget_out_of_support_share=fitted_budget_support_weight/total_weight
    forvalues j=1/8 {
        gen double quantity`j'=qsum`j'/total_weight if complete_coverage
        gen double share`j'=vsum`j'/budget_sum if complete_coverage
        gen double budget_elasticity`j'=bsum`j'/qsum`j' if complete_coverage & qsum`j'>0
        gen double income_elasticity`j'=isum`j'/qsum`j' if complete_coverage & qsum`j'>0
        if "`aggregation'"=="province" bysort province: egen double baseline_quantity`j'=max(cond(scenario_order==1,quantity`j',.))
        else bysort type: egen double baseline_quantity`j'=max(cond(scenario_order==1,quantity`j',.))
        gen double quantity_index`j'=100*quantity`j'/baseline_quantity`j' if complete_coverage & baseline_quantity`j'>0
    }
    save "`out'/`aggregation'_income_growth.dta",replace
    export delimited using "`out'/`aggregation'_income_growth.csv",replace nolabel
    restore
}
log close
