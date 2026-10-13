version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "$ROOT/outputs/scope_audit"
capture log close _all
log using "$ROOT/logs/01_scope_box_audit.log",text replace

* Freeze the candidate domain from all eligible training households, not support nodes.
use "$ROOT/data/household_quarter_8.dta",clear
keep if inrange(year,2020,2021) & month_count==3 & m>0 & m<.
assert _N>0
scalar SB_Ntrain=_N
quietly summarize m,detail
scalar SB_Mmin=r(min)
scalar SB_Mmax=r(max)
scalar SB_Mmean=r(mean)
scalar SB_Mmedian=r(p50)
tempname boxh
tempfile box
postfile `boxh' double good double train_N double budget_min double budget_max double budget_mean double price_min double price_max double observed_quantity_max double feasible_quantity_upper using `box',replace
forvalues j=1/8 {
    assert p`j'>0 & p`j'<.
    assert q`j'>=0 & q`j'<.
    quietly summarize p`j',meanonly
    scalar SB_Pmin`j'=r(min)
    scalar SB_Pmax`j'=r(max)
    quietly summarize q`j',meanonly
    scalar SB_Qobs`j'=r(max)
    scalar SB_Qmax`j'=SB_Mmax/SB_Pmin`j'
    assert q`j'<=SB_Qmax`j'*(1+1e-12)
    post `boxh' (`j') (SB_Ntrain) (SB_Mmin) (SB_Mmax) (SB_Mmean) (SB_Pmin`j') (SB_Pmax`j') (SB_Qobs`j') (SB_Qmax`j')
}
postclose `boxh'
use `box',clear
gen str80 domain_source="2020-2021 positive purchase quarters with transactions in all three months"
gen str80 quantity_unit="reference-price purchasing quantity equivalent; not kg"
gen byte diary_coverage_provider_verified=0
gen byte income_period_provider_verified=0
gen byte train_only_domain_construction=1
gen double training_budget_median=SB_Mmedian
gen double normalized_budget_min=budget_min/training_budget_median
gen double normalized_budget_max=budget_max/training_budget_median
gen double normalized_feasible_q_upper=feasible_quantity_upper/training_budget_median
export delimited using "$ROOT/outputs/scope_audit/frozen_training_box.csv",replace
save "$ROOT/outputs/scope_audit/frozen_training_box.dta",replace

* Domain alternatives are diagnostics, not automatic replacements for the frozen box.
tempname rangeh
tempfile ranges
postfile `rangeh' str40 sample str20 period double good double N double budget_min double budget_max double budget_mean double price_min double price_max double observed_quantity_max double feasible_quantity_upper using `ranges',replace
foreach sample in quarter_complete quarter_all year_all cells_quarter cells_year cells_quarter_coarse {
    if "`sample'"=="quarter_complete" local file household_quarter_8
    if "`sample'"=="quarter_all" local file household_quarter_8
    if "`sample'"=="year_all" local file household_year_8
    if "`sample'"=="cells_quarter" local file cells_quarter_8
    if "`sample'"=="cells_year" local file cells_year_8
    if "`sample'"=="cells_quarter_coarse" local file cells_quarter_8_coarse
    foreach period in train_2020_2021 heldout_2022 {
        use "$ROOT/data/`file'.dta",clear
        if "`sample'"=="quarter_complete" keep if month_count==3
        keep if m>0 & m<.
        if "`period'"=="train_2020_2021" keep if inrange(year,2020,2021)
        else keep if year==2022
        quietly count
        local N=r(N)
        quietly summarize m,meanonly
        local mmin=r(min)
        local mmax=r(max)
        local mmean=r(mean)
        forvalues j=1/8 {
            quietly summarize p`j',meanonly
            local pmin=r(min)
            local pmax=r(max)
            quietly summarize q`j',meanonly
            post `rangeh' ("`sample'") ("`period'") (`j') (`N') (`mmin') (`mmax') (`mmean') (`pmin') (`pmax') (r(max)) (`mmax'/`pmin')
        }
    }
}
postclose `rangeh'
use `ranges',clear
export delimited using "$ROOT/outputs/scope_audit/sample_domain_ranges.csv",replace

* Three active months verify transactions, not enrollment or completed diary days.
use "$ROOT/data/household_quarter_8.dta",clear
gen double quarter_count=1
gen byte positive_budget=m>0 & m<.
collapse (sum) quarter_count (sum) positive_budget,by(year month_count)
gen byte observed_active_months=month_count
gen byte diary_coverage_verified=0
gen str100 measurement_scope="Active transaction months; enrolled days and no-purchase reporting are unavailable"
export delimited using "$ROOT/outputs/scope_audit/transaction_window_coverage.csv",replace

capture program drop _scope_flags
program define _scope_flags
    syntax varlist(min=1 max=1 numeric)
    local budget `varlist'
    assert `budget'>0 & `budget'<.
    gen byte below_train_budget=`budget'<SB_Mmin*(1-1e-12)
    gen byte above_train_budget=`budget'>SB_Mmax*(1+1e-12)
    gen byte any_price_below_train=0
    gen byte any_price_above_train=0
    gen byte any_feasible_q_upper_exceeds=0
    forvalues j=1/8 {
        assert p`j'>0 & p`j'<.
        gen byte price_below`j'=p`j'<SB_Pmin`j'*(1-1e-12)
        gen byte price_above`j'=p`j'>SB_Pmax`j'*(1+1e-12)
        gen byte feasible_q_upper_exceeds`j'=`budget'/p`j'>SB_Qmax`j'*(1+1e-12)
        replace any_price_below_train=max(any_price_below_train,price_below`j')
        replace any_price_above_train=max(any_price_above_train,price_above`j')
        replace any_feasible_q_upper_exceeds=max(any_feasible_q_upper_exceeds,feasible_q_upper_exceeds`j')
    }
    gen byte outside_price_box=any_price_below_train | any_price_above_train
    gen byte outside_budget_price_box=below_train_budget | above_train_budget | outside_price_box
    gen byte outside_zero_lower_budget_box=above_train_budget | outside_price_box
    gen double target_observations=1
end

local flagvars below_train_budget above_train_budget any_price_below_train any_price_above_train outside_price_box outside_budget_price_box outside_zero_lower_budget_box any_feasible_q_upper_exceeds
forvalues j=1/8 {
    local flagvars `flagvars' price_below`j' price_above`j' feasible_q_upper_exceeds`j'
}
use "$ROOT/data/household_quarter_8.dta",clear
keep if year==2022 & month_count==3 & m>0 & m<.
_scope_flags m
collapse (sum) target_observations (mean) `flagvars',by(type)
gen str50 target="2022 positive three-active-month quarters"
export delimited using "$ROOT/outputs/scope_audit/heldout_quarter_box_coverage_by_family.csv",replace

use "$ROOT/data/household_quarter_8.dta",clear
keep if year==2022 & month_count==3 & m>0 & m<.
_scope_flags m
collapse (sum) target_observations (mean) `flagvars'
gen str50 target="2022 positive three-active-month quarters"
export delimited using "$ROOT/outputs/scope_audit/heldout_quarter_box_coverage.csv",replace

use "$ROOT/data/scenario_inputs_8.dta",clear
isid hh_id scenario_order
assert inrange(scenario_order,1,14)
bysort hh_id: assert _N==14
assert year==2022
_scope_flags m_new
foreach aggregation in national family province {
    preserve
    local by scenario_order horizon growth_rate growth_factor
    if "`aggregation'"=="family" local by type `by'
    if "`aggregation'"=="province" local by province_name `by'
    collapse (sum) target_observations (mean) `flagvars' beyond_proxy_support beyond_central_support (min) minimum_budget=m_new (max) maximum_budget=m_new,by(`by')
    gen str80 target="2022 annual household anchors; individual income-growth scenarios"
    gen str100 quantity_bound_scope="Upper bound m_new/p, not an assertion that fitted q lies outside the quantity box"
    export delimited using "$ROOT/outputs/scope_audit/scenario_box_coverage_`aggregation'.csv",replace
    restore
}

* Quantities already generated are checked separately from the pre-fit box diagnostic.
foreach predtype in native corner32 {
    if "`predtype'"=="native" {
        local input "$ROOT/outputs/scenarios/pooled/predictions.dta"
        local stub fitq
    }
    else {
        local input "$ROOT/data/corner_household_scenarios_32.dta"
        local stub cr_q
    }
    capture confirm file "`input'"
    if _rc==0 {
        use "`input'",clear
        gen double target_observations=1
        gen byte any_fitted_quantity_exceeds=0
        gen byte any_invalid_prediction=prediction_valid!=1
        local qvars any_fitted_quantity_exceeds any_invalid_prediction
        forvalues j=1/8 {
            gen byte fitted_quantity_exceeds`j'=`stub'`j'>SB_Qmax`j'*(1+1e-12) & `stub'`j'<.
            replace any_fitted_quantity_exceeds=max(any_fitted_quantity_exceeds,fitted_quantity_exceeds`j')
            local qvars `qvars' fitted_quantity_exceeds`j'
        }
        collapse (sum) target_observations (mean) `qvars',by(scenario_order horizon growth_rate growth_factor)
        gen str20 model_predictions="`predtype'"
        gen byte model_forecast_qualified=0
        gen str100 interpretation="Existing unqualified diagnostic predictions; not accepted native or phase2 forecasts"
        export delimited using "$ROOT/outputs/scope_audit/existing_`predtype'_quantity_box_coverage.csv",replace
    }
}
clear
set obs 1
gen double completed=1
gen double training_household_quarters=SB_Ntrain
gen double training_budget_max=SB_Mmax
gen str100 disclosure="No income reporting period or diary coverage inferred from transaction presence"
export delimited using "$ROOT/outputs/scope_audit/_SCOPE_AUDIT_COMPLETED.csv",replace
log close
