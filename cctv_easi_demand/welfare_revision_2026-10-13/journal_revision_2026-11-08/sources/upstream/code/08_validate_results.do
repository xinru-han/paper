version 17
clear all
set more off
global ROOT "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
log using "$ROOT/logs/08_validate_results.log",text replace
use "$ROOT/outputs/exact/model_fit_full.dta",clear
assert _N==3
isid model
assert N==583668 & cells==5163 & provinces==24
assert converged==1 & moment_jacobian_rank==n_parameters
assert n_parameters==196 if model=="aids"
assert n_parameters==203 if inlist(model,"quaids","easi")
assert analytic_gradient_check<1e-6 & compressed_moment_check<1e-8 & root_failures==0
use "$ROOT/outputs/exact/elasticities_common_full.dta",clear
assert _N==24
isid model good
assert inrange(good,1,8) & N==579066
assert !missing(expenditure,marshallian_own,hicksian_own,mean_fitted_share)
assert marshallian_own<0 if good==6
use "$ROOT/outputs/exact/cross_price_common_full.dta",clear
assert _N==3*8*8
isid model demand_good price_good
assert !missing(marshallian,hicksian,mean_slutsky)
use "$ROOT/outputs/exact/analytic_derivative_audit.dta",clear
assert _N==3
assert expenditure_max_error<1e-6 & marshallian_max_error<1e-6 & hicksian_max_error<1e-6 & cost_baseline_error<1e-8
use "$ROOT/outputs/comparison/exact_matched_sample.dta",clear
assert _N==3*(8+9)
isid grouping model good
assert N==569808
assert marshallian_own<0 if grouping=="eight" & good==6
import delimited using "$ROOT/outputs/demand/elasticities_main.csv",clear varnames(1)
assert _N==2352
isid margin sample subgroup good shock type
assert inrange(good,1,8) & inrange(shock,0,8)
assert !missing(elasticity,n,support_rate)
assert n==583668 if sample=="raw_all" & subgroup=="all"
assert n==574172 if sample=="common_positive" & subgroup=="all" & margin=="unconditional"
assert elasticity<0 if margin=="unconditional" & sample=="common_positive" & subgroup=="all" & type=="marshallian" & good==6 & shock==6
import delimited using "$ROOT/outputs/demand/probit_fit_main.csv",clear varnames(1)
assert _N==8
assert n==583668 & converged==1
import delimited using "$ROOT/outputs/audit/main_derivative_main.csv",clear varnames(1)
assert expenditure_derivative_max_error<1e-7 & price_derivative_max_error<1e-7
import delimited using "$ROOT/outputs/inference/other_meat_main.csv",clear varnames(1)
assert _N==4
assert ci_lower<estimate & estimate<ci_upper & se_province_two_step>0
use "$ROOT/outputs/comparison/own_price_all_models.dta",clear
assert _N==8
isid good
assert !missing(AIDS,QUAIDS,EASI,SY_EASI)
use "$ROOT/outputs/comparison/meat_before_after.dta",clear
assert _N==4
assert merged_other_meat<0
list model old_poultry old_beef_mutton merged_other_meat expenditure,noobs
foreach file in meat_merge_results.docx meat_merge_results.xlsx {
    confirm file "$ROOT/outputs/`file'"
}
file open done using "$ROOT/outputs/audit/final_success.txt",write replace
file write done "All data, convergence, identification, derivative, support, table and completeness checks passed in Stata." _n
file close done
display "MEAT_MERGE_VALIDATION_SUCCESS"
log close
