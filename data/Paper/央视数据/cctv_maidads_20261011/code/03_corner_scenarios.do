version 17
clear all
set more off
set type double
args draws sensitivity
if "`draws'"=="" local draws 32
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "$ROOT/outputs/corner_scenarios"
capture log close _all
log using "$ROOT/logs/03_corner_scenarios_`draws'.log",text replace
import delimited using "$ROOT/outputs/corner/estimated_free_parameters.csv",clear asdouble
mkmat cm_b*,matrix(CS_b)
import delimited using "$ROOT/outputs/corner/fit_status.csv",clear asdouble
scalar CS_scale=budget_scale[1]
use "$ROOT/data/scenario_inputs_8.dta",clear
if "`sensitivity'"=="sensitivity" {
    keep if inlist(scenario_order,1,4)
    sort hh_id scenario_order
    egen long __hh=group(hh_id)
    keep if mod(__hh,100)==0
}
do "$ROOT/ado/corner_maidads.mata"
do "$ROOT/ado/corner_regular.mata"
do "$ROOT/ado/corner_smd.mata"
do "$ROOT/ado/corner_forecast.mata"
mata: cs_predict(st_matrix("CS_b"),st_numscalar("CS_scale"),`draws')
gen double budget_error=0
forvalues j=1/8 {
    replace budget_error=budget_error+p`j'*cr_q`j'
}
replace budget_error=abs(budget_error-m_new)/m_new
assert budget_error<1e-8 if prediction_valid
gen double invalid_weight=1-prediction_valid
gen double total_weight=1
gen byte full_sample_fit=0
gen byte qualified_forecast=0
gen str120 result_status="Restricted corner pilot diagnostic; full-household prediction, not full-sample fit"
gen str120 participation_scope="Quarter-kernel conditional probability at annual monthly-equivalent budget; not annual purchase incidence"
gen double integration_draws=`draws'
gen double beyond_income_proxy_support=beyond_proxy_support
gen double beyond_income_central_support=beyond_central_support
gen double negative_budget_income_weight=negative_budget_income
if "`sensitivity'"=="sensitivity" {
    gen double draws=`draws'
    local keepvars hh_id scenario_order draws prediction_valid
    forvalues j=1/8 {
        local keepvars `keepvars' cr_q`j' cr_dqdm`j' cr_pi`j'
    }
    keep `keepvars'
    save "$ROOT/data/corner_scenario_sensitivity_`draws'.dta",replace
    log close
    exit
}
save "$ROOT/data/corner_household_scenarios_`draws'.dta",replace
foreach aggregation in province family {
    preserve
    if "`aggregation'"=="province" local by province province_name scenario_order horizon growth_rate growth_factor
    else local by type scenario_order horizon growth_rate growth_factor
    local sums total_weight invalid_weight beyond_income_proxy_support beyond_income_central_support negative_budget_income_weight
    forvalues j=1/8 {
        gen double qsum`j'=cr_q`j'
        gen double vsum`j'=p`j'*cr_q`j'
        gen double psum`j'=cr_pi`j'
        gen double bsum`j'=cr_dqdm`j'*m_new
        gen double isum`j'=bsum`j'*eta_budget_income_new
        local sums `sums' qsum`j' vsum`j' psum`j' bsum`j' isum`j'
    }
    gen double budget_sum=m_new
    local sums `sums' budget_sum
    collapse (sum) `sums' (max) budget_error (first) full_sample_fit qualified_forecast result_status participation_scope integration_draws,by(`by')
    gen byte complete_coverage=invalid_weight==0
    forvalues j=1/8 {
        gen double quantity`j'=qsum`j'/total_weight if complete_coverage
        gen double purchase_prob`j'=psum`j'/total_weight if complete_coverage
        gen double share`j'=vsum`j'/budget_sum if complete_coverage
        gen double budget_elasticity`j'=bsum`j'/qsum`j' if complete_coverage & qsum`j'>0
        gen double income_elasticity`j'=isum`j'/qsum`j' if complete_coverage & qsum`j'>0
        if "`aggregation'"=="province" bysort province: egen double baseline_quantity`j'=max(cond(scenario_order==1,quantity`j',.))
        else bysort type: egen double baseline_quantity`j'=max(cond(scenario_order==1,quantity`j',.))
        gen double quantity_index`j'=100*quantity`j'/baseline_quantity`j' if complete_coverage
    }
    save "$ROOT/outputs/corner_scenarios/`aggregation'_income_growth_`draws'.dta",replace
    export delimited using "$ROOT/outputs/corner_scenarios/`aggregation'_income_growth_`draws'.csv",replace nolabel
    restore
}
log close
