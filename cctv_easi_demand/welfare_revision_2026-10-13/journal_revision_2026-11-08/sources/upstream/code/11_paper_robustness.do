version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/00_config.do"
args variant
local variants "order1 order3 nosy nopcyc"
if "`variant'"!="" local variants "`variant'"
log using "$ROOT/logs/11_paper_robustness`variant'.log",text replace
do "$ROOT/ado/cctv_fit.ado"
do "$ROOT/ado/cctv_report.do"
do "$ROOT/ado/cctv_audit.do"
foreach v of local variants {
    use "$ROOT/data/fitted_main.dta",clear
    estimates use "$ROOT/outputs/models/main.ster"
    if "`v'"=="order1" cctv_fit,order(1) reuse fast
    if "`v'"=="order3" cctv_fit,order(3) reuse fast
    if "`v'"=="nosy" cctv_fit,nosy fast
    if "`v'"=="nopcyc" cctv_fit,nopcyc fast
    if "`v'"=="omit5" cctv_fit,omit(5) fast
    assert e(N)==583668 & e(rank)==e(k)
    estimates save "$ROOT/outputs/robustness/`v'.ster",replace
    forvalues i=1/8 {
        if e(sy) matrix cv_syb`i'=e(syb`i')
    }
    mata: CV_CACHE_BETA=J(0,1,.)
    mata: cv_own("$ROOT/outputs/robustness/points_`v'.csv","`v'",0)
    display "EIGHT_ROBUST_VARIANT_SUCCESS: `v'"
}
display "EIGHT_PAPER_ROBUSTNESS_SUCCESS"
log close
