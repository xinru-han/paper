version 17
clear all
set more off
set type double
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_coarse_cells.log",text replace

use "$run/data/household_quarter_8.dta",clear
keep if m>0
local qlist
local plist
local slist
local wlist
forvalues j=1/8 {
    local qlist `qlist' q`j'
    local plist `plist' p`j'
    local slist `slist' spend`j'
    local wlist `wlist' w`j'
    bysort province time: assert p`j'==p`j'[1]
}
gen long __one=1
gen double complete_n=complete_window
collapse (mean) m `qlist' `slist' nut_spend month_count size_proxy ///
    (min) min_household_m=m (p50) median_household_m=m (max) max_household_m=m ///
    (firstnm) `plist' family_type (sum) nobs=__one complete_n, ///
    by(province province_name time tq year quarter type income_band)
gen long n_households=nobs
forvalues j=1/8 {
    gen double w`j'=p`j'*q`j'/m
    assert q`j'>=0 & q`j'<.
}
egen double __wsum=rowtotal(`wlist')
assert abs(__wsum-1)<1e-10
drop __wsum
isid province time type income_band
save "$run/data/cells_quarter_8_coarse.dta",replace
export delimited using "$run/data/cells_quarter_8_coarse.csv",replace nolabel

tempname result
postfile `result' str48 metric double value using "$run/outputs/data_audit/coarse_cells_summary.dta",replace
quietly count
post `result' ("coarse_cells") (r(N))
quietly summarize nobs,detail
foreach stat in sum mean min p1 p25 p50 p75 p99 max {
    post `result' ("nobs_`stat'") (r(`stat'))
}
quietly count if nobs==1
post `result' ("one_household_cells_kept") (r(N))
quietly count if min_household_m<=0
assert r(N)==0
quietly summarize min_household_m,meanonly
post `result' ("minimum_individual_budget") (r(min))
forvalues j=1/8 {
    quietly count if q`j'==0
    post `result' ("zero_quantity_cells_good`j'") (r(N))
}
postclose `result'
use "$run/outputs/data_audit/coarse_cells_summary.dta",clear
export delimited using "$run/outputs/data_audit/coarse_cells_summary.csv",replace
list,noobs
log close
