version 17
clear all
set more off
args input output model k filter
if "`filter'"=="" local filter 1
capture log close _all
log using "`output'/audit_refresh.log", text replace
import delimited using "`output'/raw_parameters.csv", clear varnames(1) asdouble
mkmat value lower upper, matrix(MS_existing)
import delimited using "`output'/model_summary.csv", clear varnames(1) asdouble
scalar MS_previous_qualification=converged[1]
import delimited using "`input'", clear varnames(1) encoding(utf8) asdouble
keep if `filter'
local prices
local shares
forvalues j=1/`k' {
    local prices `prices' p`j'
    local shares `shares' w`j'
}
do "/root/data/Paper/央视数据/cctv_maidads_20261011/ado/maidads_simplex_core.mata"
mata:
MD_load("m",st_local("prices"),st_local("shares"),"")
MD_MAI=st_local("model")=="maidads"
MD_BEST=st_matrix("MS_existing")[,1]'
MD_LO=st_matrix("MS_existing")[,2]'
MD_HI=st_matrix("MS_existing")[,3]'
MD_OK=st_numscalar("MS_previous_qualification")
par=MD_unpack(MD_BEST,MD_MAI)
MD_audit(st_local("output"),MD_BEST,par,MD_MAI)
if(MD_OK!=st_numscalar("MS_previous_qualification")) _error(3498)
st_numscalar("MS_refreshed_qualification",MD_OK)
end
display "SIMPLEX AUDIT REFRESH PASSED WITHOUT REFITTING"
log close
