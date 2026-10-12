version 17
clear all
set more off
set type double
args input modeldir out model k filter
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "`out'"
capture log close _all
log using "`out'/predict.log",text replace
import delimited using "`modeldir'/raw_parameters.csv",clear asdouble
mkmat _all,matrix(CP_b)
import delimited using "`modeldir'/fit_summary.csv",clear asdouble
scalar CP_mref=m_reference[1]
scalar CP_stationary=stationary[1]
scalar CP_score=max_score[1]
import delimited using "`input'",clear varnames(1) encoding("utf-8") asdouble
if "`filter'"!="" keep if `filter'
do "$ROOT/ado/cctv_comparators.mata"
mata:
S=ct_state()
pn="p":+strofreal(1..`k')
wn="w":+strofreal(1..`k')
S.W=st_data(.,wn); S.LP=ln(st_data(.,pn)); S.k=`k'
S.R=S.LP[,1..`k'-1]:-S.LP[,`k']; S.mref=st_numscalar("CP_mref")
S.X=ln(st_data(.,"m")/S.mref); S.quadratic=("`model'"=="quaids")
ct_export(st_matrix("CP_b"),S)
end
gen byte prediction_valid=positive_support
gen byte estimate_stationary=scalar(CP_stationary)
gen double estimate_score=scalar(CP_score)
forvalues j=1/`k' {
    gen double fitw`j'=fit_w`j'
    gen double fitq`j'=m*fitw`j'/p`j'
}
save "`out'/predictions.dta",replace
export delimited using "`out'/predictions.csv",replace
preserve
collapse (count) target_rows=m (sum) valid_rows=prediction_valid (max) budget_error (first) estimate_stationary estimate_score
gen double coverage=valid_rows/target_rows
export delimited using "`out'/coverage.csv",replace
restore
log close
