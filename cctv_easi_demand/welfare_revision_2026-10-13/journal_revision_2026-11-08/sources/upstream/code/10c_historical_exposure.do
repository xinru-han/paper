version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/00_config.do"
capture log close _all
log using "$ROOT/logs/08b_historical_exposure.log", text replace
use "$ROOT/data/analysis_monthly.dta", clear
preserve
keep province ym year lp1 lp2 lp3 lp4 lp5 lp6 lp7 lp8
bysort province ym: keep if _n==1
keep if inlist(year,2020,2022)
collapse (mean) lp1 lp2 lp3 lp4 lp5 lp6 lp7 lp8 (count) months=ym, by(province year)
assert months==12
reshape wide lp1 lp2 lp3 lp4 lp5 lp6 lp7 lp8 months, i(province) j(year)
forvalues i=1/8 {
    gen double delta`i'=exp(lp`i'2022-lp`i'2020)-1
}
save "$ROOT/data/historical_price_shocks.dta", replace
export delimited using "$ROOT/outputs/welfare/price_shocks_2020_2022.csv", replace
restore
keep if year==2020
merge m:1 province using "$ROOT/data/historical_price_shocks.dta", assert(match using) keep(match) nogen
tempname results
postfile `results' str30 scenario str25 subgroup double N double mean_cost_yuan_pc double median_cost_yuan_pc double mean_food_budget_pct double p10_food_budget_pct double p90_food_budget_pct using "$ROOT/outputs/welfare/policy_exposure_historical.dta", replace
foreach scenario in all_food_2020_2022 meat_2020_2022 dairy_2020_2022 staple_oil_2020_2022 {
    gen double exposure=0
    if "`scenario'"=="all_food_2020_2022" {
        forvalues i=1/8 {
            replace exposure=exposure+w`i'*delta`i'
        }
    }
    if "`scenario'"=="meat_2020_2022" replace exposure=w5*delta5+w6*delta6
    if "`scenario'"=="dairy_2020_2022" replace exposure=w8*delta8
    if "`scenario'"=="staple_oil_2020_2022" replace exposure=w1*delta1+w2*delta2
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
use "$ROOT/outputs/welfare/policy_exposure_historical.dta", clear
export delimited using "$ROOT/outputs/welfare/policy_exposure_historical.csv", replace
display "EIGHT_POLICY_SUCCESS"
log close
