version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$ROOT/logs/05_income_tests.log",text replace
use "$ROOT/data/household_quarter_income_8.dta",clear
egen long household_cluster=group(hh_id)
quietly regress log_m c.inc1 c.inc2 i.type c.inc1#i.type c.inc2#i.type ///
    i.size_band i.province i.time rp1-rp7,vce(cluster household_cluster)
estimates save "$ROOT/outputs/income/food_budget_cluster_conditional.ster",replace
local nn=e(N)
local nc=e(N_clust)
tempname tests slopes
postfile `tests' str70 test double statistic double df double df_residual ///
    double p_value double observations double clusters ///
    using "$ROOT/tmp/income_tests.dta",replace
foreach which in nonlinear family_curve income_response {
    if "`which'"=="nonlinear" quietly test inc2 2.type#c.inc2 3.type#c.inc2 4.type#c.inc2
    if "`which'"=="family_curve" quietly test 2.type#c.inc1 3.type#c.inc1 4.type#c.inc1 ///
        2.type#c.inc2 3.type#c.inc2 4.type#c.inc2
    if "`which'"=="income_response" quietly test inc1 inc2 2.type#c.inc1 3.type#c.inc1 ///
        4.type#c.inc1 2.type#c.inc2 3.type#c.inc2 4.type#c.inc2
    post `tests' ("`which'") (r(F)) (r(df)) (r(df_r)) (r(p)) (`nn') (`nc')
}
postclose `tests'
postfile `slopes' byte type double growth_factor double mean_inc1 double estimate ///
    double conditional_se double conditional_p double ci_lower double ci_upper ///
    using "$ROOT/tmp/income_slopes.dta",replace
use "$ROOT/data/household_year_income_8.dta",clear
forvalues t=1/4 {
    quietly summarize inc1 if type==`t',meanonly
    local center=r(mean)
    local linear "inc1"
    local quadratic "inc2"
    if `t'>1 {
        local linear "inc1+`t'.type#c.inc1"
        local quadratic "inc2+`t'.type#c.inc2"
    }
    foreach growth in 1 1.5 2 {
        local z=2*(`center'+ln(`growth'))
        quietly lincom (`linear')+`z'*(`quadratic')
        post `slopes' (`t') (`growth') (`center') (r(estimate)) (r(se)) (r(p)) (r(lb)) (r(ub))
    }
}
postclose `slopes'
use "$ROOT/tmp/income_tests.dta",clear
gen str160 inference_scope="Household-cluster Wald; treats estimated interval-income moments as fixed; not joint food-elasticity inference"
export delimited using "$ROOT/outputs/income/conditional_wald_tests.csv",replace
use "$ROOT/tmp/income_slopes.dta",clear
gen str160 inference_scope="2022 once-per-household mean log-budget slope; income distribution and forecast anchor treated as fixed"
export delimited using "$ROOT/outputs/income/conditional_slope_inference.csv",replace
log close
