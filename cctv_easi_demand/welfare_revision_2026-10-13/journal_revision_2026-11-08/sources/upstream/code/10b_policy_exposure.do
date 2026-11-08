version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/00_config.do"
capture log close _all
log using "$ROOT/logs/08_policy_exposure.log", text replace
use "$ROOT/data/analysis_monthly.dta", clear
tempname results
postfile `results' str30 scenario str25 subgroup double N double mean_cost_yuan_pc double median_cost_yuan_pc double mean_food_budget_pct double p10_food_budget_pct double p90_food_budget_pct using "$ROOT/outputs/welfare/policy_exposure.dta", replace
foreach scenario in all_food_10 meat_10 dairy_10 staple_oil_10 {
    gen double exposure=0
    if "`scenario'"=="all_food_10" replace exposure=.10
    if "`scenario'"=="meat_10" replace exposure=.10*(w5+w6)
    if "`scenario'"=="dairy_10" replace exposure=.10*w8
    if "`scenario'"=="staple_oil_10" replace exposure=.10*(w1+w2)
    gen double yuan_pc=exposure*total_food_spend_pc_month
    gen double pct=100*exposure
    foreach subgroup in all low_income non_low_income elderly non_elderly large_family small_family inc1 inc2 inc3 inc4 inc5 {
        local cond "1"
        if "`subgroup'"=="low_income" local cond "low_income==1"
        if "`subgroup'"=="non_low_income" local cond "low_income==0"
        if "`subgroup'"=="elderly" local cond "elderly_household==1"
        if "`subgroup'"=="non_elderly" local cond "elderly_household==0"
        if "`subgroup'"=="large_family" local cond "large_family==1"
        if "`subgroup'"=="small_family" local cond "large_family==0"
        if substr("`subgroup'",1,3)=="inc" local cond = "income_group_order=="+substr("`subgroup'",4,.)
        quietly summarize yuan_pc if `cond', detail
        local N=r(N)
        local mean=r(mean)
        local median=r(p50)
        quietly summarize pct if `cond', detail
        post `results' ("`scenario'") ("`subgroup'") (`N') (`mean') (`median') (r(mean)) (r(p10)) (r(p90))
    }
    drop exposure yuan_pc pct
}
postclose `results'
use "$ROOT/outputs/welfare/policy_exposure.dta", clear
export delimited using "$ROOT/outputs/welfare/policy_exposure.csv", replace
keep if inlist(subgroup,"inc1","inc2","inc3","inc4","inc5") & scenario!="all_food_10"
gen byte income_bracket=real(substr(subgroup,4,.))
label define scenario 1 "Meat" 2 "Dairy" 3 "Staples and oils"
gen byte shock=cond(scenario=="meat_10",1,cond(scenario=="dairy_10",2,3))
label values shock scenario
twoway (connected mean_food_budget_pct income_bracket if shock==1, msymbol(O)) (connected mean_food_budget_pct income_bracket if shock==2, msymbol(D)) (connected mean_food_budget_pct income_bracket if shock==3, msymbol(T)), xlabel(1(1)5) xtitle("Reported income bracket") ytitle("Fixed-basket cost, % of food budget") legend(order(1 "Meat +10%" 2 "Dairy +10%" 3 "Staples and oils +10%")) graphregion(color(white)) name(exposure, replace)
graph export "$ROOT/outputs/figures/policy_exposure.png", width(2200) replace
graph export "$ROOT/outputs/figures/policy_exposure.pdf", replace
display "EIGHT_POLICY_SUCCESS"
log close
