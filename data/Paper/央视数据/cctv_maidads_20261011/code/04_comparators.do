version 17
clear all
set more off
set type double
set seed 20261011
args input out model k starts filter
if "`model'"=="" local model aids
if "`k'"=="" local k 8
if "`starts'"=="" local starts 3
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "`out'"
capture log close _all
log using "`out'/run.log",text replace
import delimited using "`input'",clear varnames(1) encoding("utf-8") asdouble
if "`filter'"!="" keep if `filter'
assert m>0 & m<.
local sharelist
forvalues j=1/`k' {
    local sharelist `sharelist' w`j'
}
egen double __ws=rowtotal(`sharelist')
assert abs(__ws-1)<1e-8
forvalues j=1/`k' {
    assert p`j'>0 & p`j'<.
    assert w`j'>=0 & w`j'<.
}
drop __ws
do "$ROOT/ado/cctv_comparators.mata"
mata: ct_fit("`model'",`k',`starts')
matrix colnames CT_ledger=start rc converged iterations objective max_score stationary
preserve
clear
svmat double CT_ledger,names(col)
export delimited using "`out'/candidates.csv",replace
restore
preserve
clear
svmat double CT_b
export delimited using "`out'/raw_parameters.csv",replace
restore
preserve
clear
svmat double CT_representative
rename (CT_representative1 CT_representative2 CT_representative3 CT_representative4 CT_representative5) (good share expenditure_elasticity marshallian_own hicksian_own)
export delimited using "`out'/representative_elasticities.csv",replace
restore
foreach typ in marshallian hicksian {
    preserve
    clear
    svmat double CT_`typ'
    gen byte good=_n
    export delimited using "`out'/`typ'_matrix.csv",replace
    restore
}
gen str12 model="`model'"
gen double objective=scalar(CT_objective)
gen double m_reference=scalar(CT_mref)
gen double max_score=scalar(CT_score)
gen byte stationary=scalar(CT_stationary)
gen double gradient_error=scalar(CT_gradient_error)
gen int structural_parameters=scalar(CT_parameters)
gen int covariance_parameters=scalar(CT_cov_parameters)
gen double qml_aic=_N*(scalar(CT_objective)+(`k'-1)*(1+ln(2*c(pi))))+2*(scalar(CT_parameters)+scalar(CT_cov_parameters))
gen double qml_bic=_N*(scalar(CT_objective)+(`k'-1)*(1+ln(2*c(pi))))+ln(_N)*(scalar(CT_parameters)+scalar(CT_cov_parameters))
save "`out'/predictions.dta",replace
export delimited using "`out'/predictions.csv",replace
preserve
gen long __one=1
collapse (count) observations=__one (first) objective m_reference max_score stationary gradient_error structural_parameters covariance_parameters qml_aic qml_bic (mean) positive_support (max) budget_error slutsky_symmetry_error slutsky_max_eig,by(model)
export delimited using "`out'/fit_summary.csv",replace
restore
log close
