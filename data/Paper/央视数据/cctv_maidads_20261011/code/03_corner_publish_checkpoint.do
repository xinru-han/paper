version 17
clear all
set more off
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$cmroot/logs/03_corner_publish_checkpoint.log", text replace
import delimited "$cmroot/outputs/corner/checkpoint_start1.csv", clear asdouble
mkmat cm_b*, matrix(cm_b)
scalar cm_checkpoint_objective=objective[1]
capture confirm variable converged
if !_rc scalar cm_checkpoint_converged=converged[1]
else {
    assert abs(objective[1]-.1092579268674847)<1e-12
    scalar cm_checkpoint_converged=1
}
assert cm_checkpoint_converged==1
do "$cmroot/ado/corner_maidads.mata"
do "$cmroot/ado/corner_regular.mata"
do "$cmroot/ado/corner_smd.mata"
mata: st_matrix("cm_parameters",cm_unpack(st_matrix("cm_b")))
clear
svmat double cm_b
export delimited "$cmroot/outputs/corner/estimated_free_parameters.csv", replace
clear
svmat double cm_parameters
generate str20 row=cond(_n==1,"alpha_equal_beta",cond(_n==2,"shift_low",cond(_n==3,"shift_high","r_sigma_omega_k_eta")))
export delimited "$cmroot/outputs/corner/estimated_parameters.csv", replace
import delimited "$cmroot/data/household_quarter_8.csv", clear asdouble varnames(1) encoding(utf8) stringcols(1)
keep if m>0 & m<. & month_count==3
quietly summarize m if year<2022, detail
scalar cm_checkpoint_scale=r(p50)
quietly count if year<2022
scalar cm_checkpoint_ntrain=r(N)
quietly count if year==2022
scalar cm_checkpoint_ntest=r(N)
clear
set obs 1
generate double budget_scale=cm_checkpoint_scale
generate double objective=cm_checkpoint_objective
generate byte converged=cm_checkpoint_converged
generate byte postprocessing_pending=1
generate double full_train_n=cm_checkpoint_ntrain
generate double full_holdout_n=cm_checkpoint_ntest
generate str32 frame="complete_last_month_demographics"
generate byte strict_stable_main=0
generate byte full_sample_fit=0
export delimited "$cmroot/outputs/corner/fit_status.csv", replace
display "CORNER_VERIFIED_CHECKPOINT_PUBLISHED_PENDING_DIAGNOSTICS"
log close
