version 17
clear all
set more off
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
import delimited "$cmroot/outputs/corner/smd_actual_support.csv", clear varnames(1) encoding(utf8) asdouble stringcols(1)
assert _N==1914
assert m>0 & scaled_m>0 & support_weight>0
forvalues j=1/8 {
    assert abs(q`j'*p`j'-m*w`j')<1e-8*max(1,m)
    assert purchase`j'==(spend`j'>0)
}
save "$cmroot/data/corner_smd_support.dta", replace
display "CORNER_REAL_SUPPORT_CHECKPOINT_PUBLISHED"
