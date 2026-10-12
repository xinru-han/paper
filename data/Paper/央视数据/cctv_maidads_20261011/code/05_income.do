version 17
clear all
set more off
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "$ROOT/outputs/income"
capture log close _all
log using "$ROOT/logs/05_income.log",text replace
use "$ROOT/data/household_quarter_8.dta",clear
gen long __one=1
assert inrange(income_band,1,5)
assert inrange(size_band,1,4)
gen double ln_lower=.
gen double ln_upper=.
replace ln_upper=ln(5000) if income_band==1
replace ln_lower=ln(5000) if income_band==2
replace ln_upper=ln(7000) if income_band==2
replace ln_lower=ln(7000) if income_band==3
replace ln_upper=ln(9000) if income_band==3
replace ln_lower=ln(9000) if income_band==4
replace ln_upper=ln(12000) if income_band==4
replace ln_lower=ln(12000) if income_band==5
* Reported monetary bands are interval observations, not exact monthly income.
quietly intreg ln_lower ln_upper i.type i.size_band i.province i.year
estimates save "$ROOT/outputs/income/interval_lognormal.ster",replace
scalar income_sigma=e(sigma)
predict double income_mu, xb
gen double income_sigma=scalar(income_sigma)
gen double za=(ln_lower-income_mu)/income_sigma
gen double zb=(ln_upper-income_mu)/income_sigma
gen double pa=cond(missing(ln_lower),0,normal(za))
gen double pb=cond(missing(ln_upper),1,normal(zb))
gen double phia=cond(missing(ln_lower),0,normalden(za))
gen double phib=cond(missing(ln_upper),0,normalden(zb))
gen double prob_band=pb-pa
assert prob_band>1e-12 & prob_band<.
gen double tz=(phia-phib)/prob_band
gen double tz2=1+(cond(missing(ln_lower),0,za*phia)-cond(missing(ln_upper),0,zb*phib))/prob_band
gen double lnypc_mean=income_mu+income_sigma*tz-ln(size_proxy)
gen double lnypc_second=(income_mu-ln(size_proxy))^2+2*(income_mu-ln(size_proxy))*income_sigma*tz+income_sigma^2*tz2
gen double income_pc_mean=exp(income_mu+income_sigma^2/2)/size_proxy * ///
    (cond(missing(ln_upper),1,normal(zb-income_sigma))-cond(missing(ln_lower),0,normal(za-income_sigma)))/prob_band
gen double income_pc_geomean=exp(lnypc_mean)
quietly summarize lnypc_mean,meanonly
scalar income_center=r(mean)
gen double inc1=lnypc_mean-scalar(income_center)
gen double inc2=lnypc_second-2*scalar(income_center)*lnypc_mean+scalar(income_center)^2
gen double log_m=ln(m) if m>0 & m<.
forvalues j=1/7 {
    gen double rp`j'=ln(p`j'/p8)
}
quietly regress log_m c.inc1 c.inc2 i.type c.inc1#i.type c.inc2#i.type ///
    i.size_band i.province i.time rp1-rp7
estimates save "$ROOT/outputs/income/food_budget_interval_projection.ster",replace
scalar budget_n=e(N)
scalar budget_r2=e(r2)
gen double budget_linear=_b[inc1]
gen double budget_quadratic=_b[inc2]
forvalues t=2/4 {
    replace budget_linear=budget_linear+_b[`t'.type#c.inc1] if type==`t'
    replace budget_quadratic=budget_quadratic+_b[`t'.type#c.inc2] if type==`t'
}
gen double food_budget_income_elasticity=budget_linear+2*budget_quadratic*inc1
predict double log_budget_fitted,xb
gen double budget_geometric_fitted=exp(log_budget_fitted)
gen double income_center=scalar(income_center)
label var income_pc_mean "Conditional mean reported income per proxy person; reporting period unknown"
label var food_budget_income_elasticity "Derivative of projected mean log food budget under proportional latent income growth"
save "$ROOT/data/household_quarter_income_8.dta",replace
preserve
collapse (count) observations=__one (mean) income_pc_mean income_pc_geomean m food_budget_income_elasticity budget_linear budget_quadratic (first) income_center income_sigma,by(type income_band)
export delimited using "$ROOT/outputs/income/family_income_band_summary.csv",replace
restore
preserve
keep if year==2022
bysort hh_id (time): keep if _n==_N
rename type income_type
rename income_band income_band_used
rename size_band income_size_band
keep hh_id year income_type income_band_used income_size_band income_pc_mean income_pc_geomean lnypc_mean lnypc_second inc1 inc2 food_budget_income_elasticity budget_linear budget_quadratic income_center
tempfile income_link
save `income_link'
use "$ROOT/data/household_year_8.dta",clear
keep if year==2022 & m>0
merge 1:1 hh_id year using `income_link',keep(master match)
assert _merge==3
assert type==income_type & income_band==income_band_used & size_band==income_size_band
drop _merge income_type income_band_used income_size_band
gen long __one=1
save "$ROOT/data/household_year_income_8.dta",replace
local qpvars
forvalues j=1/8 {
    local qpvars `qpvars' q`j' w`j' p`j'
}
collapse (count) nobs=__one (sum) msum=m q1sum=q1 q2sum=q2 q3sum=q3 q4sum=q4 q5sum=q5 q6sum=q6 q7sum=q7 q8sum=q8 ///
    (mean) m `qpvars' income_pc_mean income_pc_geomean lnypc_mean lnypc_second inc1 inc2 food_budget_income_elasticity budget_linear budget_quadratic income_center, ///
    by(province province_name time year type income_band size_band)
gen double hh_income_pc_mean=income_pc_mean
save "$ROOT/data/scenario_income_cells_8.dta",replace
export delimited using "$ROOT/data/scenario_income_cells_8.csv",replace
restore
preserve
use "$ROOT/data/household_year_income_8.dta",clear
gen double base_m=m
expand 5
bysort hh_id time: gen byte scenario_order=_n
gen double growth_factor=cond(scenario_order==1,1,cond(scenario_order==2,1.1,cond(scenario_order==3,1.25,cond(scenario_order==4,1.5,2))))
gen double d=ln(growth_factor)
gen double budget_factor=exp(budget_linear*d+budget_quadratic*(2*inc1*d+d^2))
gen double income_budget=m*budget_factor
gen double income_elasticity_new=budget_linear+2*budget_quadratic*(inc1+d)
gen double income_budget_response=income_budget*income_elasticity_new
collapse (count) observations=__one (sum) income_budget_response budget_sum=income_budget ///
    (mean) base_m income_budget budget_factor income_elasticity_new income_pc_mean,by(type growth_factor)
gen double aggregate_budget_income_eta=income_budget_response/budget_sum
label var income_elasticity_new "Unweighted mean household log-budget income slope"
label var aggregate_budget_income_eta "Budget-weighted elasticity of aggregate covered-food budget"
export delimited using "$ROOT/outputs/income/food_budget_income_scenarios.csv",replace
restore
preserve
clear
set obs 1
gen str80 income_model="Interval lognormal; income reporting period unverified"
gen double income_sigma=scalar(income_sigma)
gen double income_center=scalar(income_center)
gen double budget_observations=scalar(budget_n)
gen double budget_r_squared=scalar(budget_r2)
gen str120 scope="Projection of conditional mean log covered-food budget; not causal income identification"
gen str80 uncertainty="Point estimates only; no bootstrap or joint sampling inference"
export delimited using "$ROOT/outputs/income/model_scope.csv",replace
restore
log close
