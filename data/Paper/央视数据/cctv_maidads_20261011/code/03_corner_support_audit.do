version 17
clear all
set more off
capture log close _all
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
log using "$cmroot/logs/03_corner_support_audit.log", text replace
import delimited "$cmroot/data/household_quarter_8.csv", clear asdouble stringcols(1) encoding(utf8)
keep if month_count==3 & m>0 & m<.
generate byte train=year<2022
forvalues j=1/8 {
    generate double purchase`j'=spend`j'>0
}
bysort train province type income_band (m hh_id tq): generate long stratum_n=_N
bysort train province type income_band (m hh_id tq): generate long stratum_rank=_n
local outcomes "purchase1 purchase2 purchase3 purchase4 purchase5 purchase6 purchase7 purchase8 w1 w2 w3 w4 w5 w6 w7 w8 m"
preserve
collapse (mean) `outcomes' (count) support_n=m, by(train)
generate str20 source="full_eligible"
generate points_per_stratum=0
tempfile full
save `full'
restore
tempfile all
preserve
use `full', clear
save `all'
restore
foreach points of numlist 1 2 4 8 {
    preserve
    generate byte selected=0
    forvalues j=1/`points' {
        replace selected=1 if stratum_rank==ceil(stratum_n*(`j'-.5)/`points')
    }
    bysort train province type income_band: egen long actual_support=total(selected)
    generate double support_weight=stratum_n/actual_support
    keep if selected
    quietly count if train
    scalar ctrain=r(N)
    quietly count if !train
    scalar ctest=r(N)
    collapse (mean) `outcomes' [aw=support_weight], by(train)
    generate double support_n=cond(train,ctrain,ctest)
    generate str20 source="weighted_support"
    generate points_per_stratum=`points'
    append using `all'
    save `all', replace
    restore
}
use `all', clear
sort train points_per_stratum
export delimited "$cmroot/outputs/corner/support_moment_sensitivity_no_refit.csv", replace
list train source points_per_stratum support_n m purchase1 purchase2 purchase8, noobs
display "CORNER_SUPPORT_AUDIT_FINISHED"
log close
