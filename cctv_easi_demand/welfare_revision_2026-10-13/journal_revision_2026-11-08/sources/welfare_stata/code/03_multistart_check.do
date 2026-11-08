version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/welfare_revision_2026-10-13/code/00_config.do"
log using "$REV/logs/03_multistart_check.log",text replace
do "$REV/ado/cctv_exact.do"
do "$REV/ado/cctv_exact_curvature.do"
estimates use "$REV/outputs/exact/easi_curvature_full.ster"
scalar REV_reference=e(criterion)
matrix REV_reference_b=e(b)
use "$REV/data/curvature_moments.dta",clear
tempname out
postfile `out' double start_floor criterion criterion_difference max_coefficient_difference converged iterations gamma_maxeig gradient_error using "$REV/outputs/audit/multistart.dta",replace
foreach floor in .0001 .01 {
    estimates use "$BASE/outputs/exact/easi_full.ster"
    matrix XE_b=e(b)
    scalar XE_startfloor=`floor'
    mata: xec_profile_fit("$DEMOS")
    mata: st_numscalar("REV_bdiff",max(abs(st_matrix("XE_b")-st_matrix("REV_reference_b"))))
    post `out' (`floor') (XE_obj) (XE_obj-REV_reference) (REV_bdiff) (XE_conv) (XE_iters) (XE_Gamma_maxeig) (XE_graderr)
    assert XE_conv==1 & abs(XE_obj-REV_reference)<1e-8 & XE_Gamma_maxeig<1e-9 & XE_graderr<1e-6
}
postclose `out'
use "$REV/outputs/audit/multistart.dta",clear
export delimited using "$REV/outputs/audit/multistart.csv",replace
list,noobs
display "MULTISTART_VALIDATION_SUCCESS"
log close
