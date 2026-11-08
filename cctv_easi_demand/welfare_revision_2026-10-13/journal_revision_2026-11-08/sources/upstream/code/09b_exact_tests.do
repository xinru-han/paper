version 17
clear all
set more off
set matsize 800
global rebuild "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
cap log close _all
log using "$rebuild/logs/04d_exact_tests.log",text replace
tempname out
postfile `out' str12 model str48 hypothesis byte restrictions byte covariance_rank double Wald double F_reference double df_num double df_den double p_chi2 double p_F_reference using "$rebuild/outputs/exact/engel_nested_tests.dta",replace
foreach model in quaids easi {
    estimates use "$rebuild/outputs/exact/`model'_full.ster"
    matrix XE_b=e(b)
    matrix XE_V=e(V)
    local first=colnumb(XE_b,"l1")
    local last=colnumb(XE_b,"l7")
    assert `last'-`first'==6
    mata: bv=st_matrix("XE_b")[1,`first'..`last']; VV=st_matrix("XE_V")[`first'..`last',`first'..`last']; st_numscalar("XE_lrank",rank(VV)); st_numscalar("XE_lwald",bv*invsym(VV)*bv')
    local W=XE_lwald
    local rank=XE_lrank
    local pc=cond(`rank'==7,chi2tail(7,`W'),.)
    local pf=cond(`rank'==7,Ftail(7,23,`W'/7),.)
    local hypothesis "highest_Engel_order_zero"
    if "`model'"=="quaids" local hypothesis "QUAIDS_lambda_zero_AIDS_nested"
    post `out' ("`model'") ("`hypothesis'") (7) (`rank') (`W') (`W'/7) (7) (23) (`pc') (`pf')
}
postclose `out'
use "$rebuild/outputs/exact/engel_nested_tests.dta",clear
export delimited using "$rebuild/outputs/exact/engel_nested_tests.csv",replace
list,abbreviate(25) noobs
display "EIGHT_ENGEL_TESTS_SUCCESS"
log close
