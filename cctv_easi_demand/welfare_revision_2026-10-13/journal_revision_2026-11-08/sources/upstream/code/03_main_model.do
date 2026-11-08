version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/00_config.do"
set type double
args mode
local tag main
if "`mode'"=="pilot" local tag mainpilot
log using "$ROOT/logs/03_`tag'.log",text replace
if "`mode'"=="pilot" use "$ROOT/data/pilot.dta",clear
else use "$ROOT/data/analysis_monthly.dta",clear
do "$ROOT/ado/cctv_fit.ado"
cctv_fit
assert e(N)==_N
assert e(rank)==e(k)
estimates save "$ROOT/outputs/models/`tag'.ster",replace
matrix B=e(b)
matrix V=e(V)
local terms: colnames B
tempname coefs
postfile `coefs' str32 parameter double estimate double se_province_two_step using "$ROOT/outputs/demand/coefficients_`tag'.dta",replace
local j=0
foreach term of local terms {
    local ++j
    post `coefs' ("`term'") (B[1,`j']) (sqrt(V[`j',`j']))
}
postclose `coefs'
preserve
use "$ROOT/outputs/demand/coefficients_`tag'.dta",clear
export delimited using "$ROOT/outputs/demand/coefficients_`tag'.csv",replace
restore
matrix FS=e(firststage_stats)
assert FS[1,5]==1 & FS[2,5]==1 & FS[3,5]==1 & FS[4,5]==1 & FS[5,5]==1 & FS[6,5]==1 & FS[7,5]==1 & FS[8,5]==1
preserve
clear
svmat double FS
gen byte good=_n
rename FS1 observed_positive_rate
rename FS2 mean_predicted_probability
rename FS3 brier
rename FS4 pseudo_r2
rename FS5 converged
rename FS6 N
rename FS7 log_likelihood
rename FS8 null_log_likelihood
export delimited using "$ROOT/outputs/demand/probit_fit_`tag'.csv",replace
restore
save "$ROOT/data/fitted_`tag'.dta",replace
forvalues i=1/8 {
    matrix cv_syb`i'=e(syb`i')
}
mata: CV_ARCH_P=CV.Gp; CV_ARCH_H=CV.Gh
mata: CV_ARCH_FP1=CV.fs[1].X; CV_ARCH_FH1=CV.fs[1].R
mata: CV_ARCH_FP2=CV.fs[2].X; CV_ARCH_FH2=CV.fs[2].R
mata: CV_ARCH_FP3=CV.fs[3].X; CV_ARCH_FH3=CV.fs[3].R
mata: CV_ARCH_FP4=CV.fs[4].X; CV_ARCH_FH4=CV.fs[4].R
mata: CV_ARCH_FP5=CV.fs[5].X; CV_ARCH_FH5=CV.fs[5].R
mata: CV_ARCH_FP6=CV.fs[6].X; CV_ARCH_FH6=CV.fs[6].R
mata: CV_ARCH_FP7=CV.fs[7].X; CV_ARCH_FH7=CV.fs[7].R
mata: mata matsave "$ROOT/outputs/models/`tag'_influence.mmat" CV_ARCH_P CV_ARCH_H CV_ARCH_FP1 CV_ARCH_FH1 CV_ARCH_FP2 CV_ARCH_FH2 CV_ARCH_FP3 CV_ARCH_FH3 CV_ARCH_FP4 CV_ARCH_FH4 CV_ARCH_FP5 CV_ARCH_FH5 CV_ARCH_FP6 CV_ARCH_FH6 CV_ARCH_FP7 CV_ARCH_FH7,replace
do "$ROOT/ado/cctv_report.do"
mata: cv_report("$ROOT/outputs","`tag'",999,1)
* Report delta/province uncertainty only after verifying adapted derivatives.
display "MEAT_MERGE_MAIN_SUCCESS"
log close
