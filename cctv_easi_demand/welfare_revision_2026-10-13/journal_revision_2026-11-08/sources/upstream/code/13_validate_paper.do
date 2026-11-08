version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
log using "$ROOT/logs/13_validate_paper.log",text replace
* Validate every newly computed manuscript input; no re-estimation required.
import delimited using "$ROOT/outputs/inference/elasticity_inference_paper_main.csv",clear varnames(1)
assert _N==32
isid sample good type
assert inrange(good,1,8) & b==999 & clusters==24
assert !missing(estimate,se_province_two_step,se_household_two_step,ci_lower,ci_upper)
assert se_province_two_step>0 & se_household_two_step>0
assert ci_lower<estimate & ci_upper>estimate
assert simultaneous_lower<=ci_lower & simultaneous_upper>=ci_upper
assert estimate<0 if type=="own_price"
assert estimate>0 if type=="expenditure"
assert abs(estimate-(-1.05895722564))<1e-9 if sample=="common_positive" & good==6 & type=="own_price"
assert abs(ci_lower-(-1.64770116284))<1e-7 if sample=="common_positive" & good==6 & type=="own_price"
assert abs(ci_upper-(-.470213288447))<1e-7 if sample=="common_positive" & good==6 & type=="own_price"
assert ci_upper>0 if sample=="common_positive" & good==2 & type=="own_price"
import delimited using "$ROOT/outputs/paper/robustness_all_points.csv",clear varnames(1)
assert _N==48
isid variant good
assert inrange(good,1,8) & own_price<0 & expenditure>0
assert abs(n-583668*support_rate)<.1
import delimited using "$ROOT/outputs/paper/main_regularity.csv",clear varnames(1)
assert _N==3
isid margin
assert n==574172 if inlist(margin,"unconditional","intensive")
assert n==334603 if margin=="latent"
assert max_eigenvalue>0
import delimited using "$ROOT/outputs/exact/engel_nested_tests.csv",clear varnames(1)
assert _N==2
assert restrictions==7 & covariance_rank==7 & p_f_reference<.001
import delimited using "$ROOT/outputs/paper/main_specification_tests.csv",clear varnames(1)
assert _N==6
assert covariance_rank<=23 & clusters==24 & score_p==.001
import delimited using "$ROOT/outputs/paper/descriptives.csv",clear varnames(1)
assert _N==8
isid good
assert inrange(good,1,8) & inrange(purchase_rate,0,1)
summarize mean_share,meanonly
assert abs(r(sum)-1)<1e-12
import delimited using "$ROOT/outputs/paper/purchase_frequency.csv",clear varnames(1)
assert _N==24
isid frequency good
assert inrange(good,1,8) & inrange(purchase_rate,0,1)
import delimited using "$ROOT/outputs/paper/price_variation.csv",clear varnames(1)
assert _N==8
assert inrange(residual_prov_month_year,0,1) & inrange(residual_prov_ym,0,1)
import delimited using "$ROOT/outputs/welfare/policy_exposure.csv",clear varnames(1)
assert _N==48
isid scenario subgroup
assert n==583668 if subgroup=="all"
assert abs(mean_food_budget_pct-10)<1e-10 if scenario=="all_food_10"
import delimited using "$ROOT/outputs/welfare/policy_exposure_historical.csv",clear varnames(1)
assert _N==48
isid scenario subgroup
assert n==182676 if subgroup=="all"
assert abs(mean_food_budget_pct-2.973402578372977)<1e-10 if subgroup=="all" & scenario=="all_food_2020_2022"
assert abs(mean_cost_yuan_pc-4.427046612142189)<1e-10 if subgroup=="all" & scenario=="all_food_2020_2022"
foreach file in eight_group_paper_tables.xlsx paper_statistics_success.txt {
    confirm file "$ROOT/outputs/paper/`file'"
}
file open done using "$ROOT/outputs/paper/final_paper_validation.txt",write replace
file write done "EIGHT_GROUP_PAPER_VALIDATION_SUCCESS" _n
file write done "New eight-group inference, sensitivity, Engel tests, participation windows, price exposure and reporting inputs passed Stata assertions." _n
file close done
display "EIGHT_GROUP_PAPER_VALIDATION_SUCCESS"
log close
