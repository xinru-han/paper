version 17
clear all
set more off
set type double
args input modeldir out k filter
if "`k'"=="" local k 8
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "`out'"
capture log close _all
log using "`out'/predict.log",text replace
import delimited using "`modeldir'/parameters.csv",clear asdouble
sort good
assert _N==`k'
mkmat alpha beta delta tau,matrix(__natural)
matrix MF_par=__natural'
import delimited using "`modeldir'/model_summary.csv",clear asdouble
scalar MF_omega=omega[1]
scalar MF_kappa=kappa[1]
scalar MF_estimate_converged=converged[1]
scalar MF_estimate_score=projected_gradient[1]
import delimited using "`modeldir'/predictions.csv",clear asdouble
quietly summarize m,meanonly
scalar MF_minbudget=r(min)
scalar MF_maxbudget=r(max)
if substr(lower("`input'"),-4,4)==".dta" use "`input'",clear
else import delimited using "`input'",clear encoding("utf-8") varnames(1) asdouble
if "`filter'"!="" keep if `filter'
forvalues j=1/`k' {
    foreach reserved in fitq`j' fitw`j' eta`j' own_m`j' own_h`j' {
        capture drop `reserved'
    }
}
foreach reserved in prediction_valid estimate_stationary estimate_qualified estimate_score budget_error utility_roots_finite_grid utility_equation_error {
    capture drop `reserved'
}
capture confirm variable m_new
if _rc gen double m_new=m
do "$ROOT/ado/maidads_core.mata"
do "$ROOT/ado/cctv_prediction.mata"
mata: mf_store(st_matrix("MF_par"),st_numscalar("MF_omega"),st_numscalar("MF_kappa"))
gen byte estimate_stationary=scalar(MF_estimate_score)<1e-4
gen byte estimate_qualified=scalar(MF_estimate_converged)
gen double estimate_score=scalar(MF_estimate_score)
gen byte beyond_fitted_budget_support=m_new<scalar(MF_minbudget) | m_new>scalar(MF_maxbudget)
gen double budget_error=0
forvalues j=1/`k' {
    replace budget_error=budget_error+p`j'*fitq`j'
}
replace budget_error=abs(budget_error-m_new)/m_new
save "`out'/predictions.dta",replace
export delimited using "`out'/predictions.csv",replace
preserve
collapse (count) target_rows=m_new (sum) valid_rows=prediction_valid (max) budget_error utility_equation_error (first) estimate_stationary estimate_qualified estimate_score
gen double coverage=valid_rows/target_rows
export delimited using "`out'/coverage.csv",replace
restore
log close
