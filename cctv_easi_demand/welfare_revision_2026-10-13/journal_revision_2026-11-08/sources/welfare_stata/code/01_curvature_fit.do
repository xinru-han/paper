version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/welfare_revision_2026-10-13/code/00_config.do"
log using "$REV/logs/01_curvature_fit.log",text replace
do "$REV/ado/cctv_exact.do"
do "$REV/ado/cctv_exact_curvature.do"
use "$BASE/data/analysis_monthly.dta",clear
local demos $DEMOS
foreach v of local demos {
    capture confirm variable `v'
    if _rc {
        if substr("`v'",1,2)=="m_" gen byte `v'=month==real(substr("`v'",3,.))
        else if substr("`v'",1,3)=="yr_" gen byte `v'=year==real(substr("`v'",4,.))
    }
}
estimates use "$BASE/outputs/exact/easi_full.ster"
matrix XE_b=e(b)
scalar XE_unconstrained_obj=e(criterion)
scalar XE_xmean=e(xmean)
gen double ex=lnx-XE_xmean
forvalues j=1/8 {
    scalar XE_pmean`j'=e(pmean`j')
    gen double ep`j'=lp`j'-XE_pmean`j'
}
gen double uobs=ex
forvalues j=1/8 {
    replace uobs=uobs-w`j'*ep`j'
}
save "$REV/data/curvature_micro.dta",replace
gen double nn=1
gen double x1=ex
gen double x2=ex^2
gen double x3=ex^3
gen double x4=ex^4
gen double u1=uobs
gen double u2=u1^2
gen double u3=u1^3
gen double u4=u1^4
gen double u1x=u1*ex
gen double u1x2=u1*ex^2
gen double u2x=u2*ex
gen double u2x2=u2*ex^2
local sums nn x1 x2 x3 x4 u1 u2 u3 u4 u1x u1x2 u2x u2x2
forvalues j=1/7 {
    gen double w0`j'=w`j'
    gen double w1`j'=w`j'*ex
    gen double w2`j'=w`j'*ex^2
    gen double wt1`j'=w`j'*u1
    gen double wt2`j'=w`j'*u2
    local sums `sums' w0`j' w1`j' w2`j' wt1`j' wt2`j'
}
local controls `demos'
local indicators low_income elderly_household large_family
local controls : list controls - indicators
collapse (sum) `sums' (firstnm) ep1 ep2 ep3 ep4 ep5 ep6 ep7 ep8 `controls',by(province ym low_income elderly_household large_family)
save "$REV/data/curvature_moments.dta",replace
timer clear 1
timer on 1
mata: xec_profile_fit("`demos'")
timer off 1
quietly timer list 1
scalar XE_runtime=r(t1)
assert XE_conv==1 & XE_N==583668 & XE_Gamma_maxeig<1e-9 & XE_graderr<1e-6
local names
forvalues j=1/7 {
    local names `names' a`j'
    local d=0
    foreach c of local demos {
        local ++d
        local names `names' t`j'_`d'
    }
}
forvalues j=1/7 {
    local names `names' b`j'
}
forvalues j=1/7 {
    local names `names' l`j'
}
forvalues j=1/7 {
    forvalues k=`j'/7 {
        local names `names' g`j'_`k'
    }
}
matrix colnames XE_b=`names'
matrix colnames XE_V=`names'
matrix rownames XE_V=`names'
* Compute stationarity in the native symmetric Gamma parameterization.
mata:
void revision_boundary()
{
    struct xe_state scalar S
    real rowvector b,gr,ev
    real matrix H,M,G,L,GL
    real scalar val,i,j,pos
    S=xe_load("easi",st_global("DEMOS"));b=st_matrix("XE_b")
    xe_eval(1,b,S,val,gr,H)
    M=J(7,7,0);pos=cols(b)-28
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) M[i,j]=M[j,i]=gr[++pos]/(1+(i!=j))
    G=xe_gamma(b,22,"easi")
    st_matrix("REV_BOUNDARY",(max(abs(gr[1..175])),max(symeigenvalues(M)),max(abs(G*M)),max(symeigenvalues(G))))
    st_matrix("REV_GAMMA_EIG",symeigenvalues(G))
}
revision_boundary()
end
matrix list REV_BOUNDARY
use "$REV/data/curvature_micro.dta",clear
gen byte xe_positive=0
mata: xe_check_moments("easi","`demos'")
mata: xe_elasticities("easi","`demos'")
assert XE_compressionerr<1e-8
capture program drop revision_post
program define revision_post,eclass
    tempvar touse
    gen byte `touse'=1
    ereturn post XE_b XE_V,esample(`touse')
    ereturn local cmd "cctv_exact"
    ereturn local model "easi"
    ereturn local demographics "$DEMOS"
    ereturn local estimator "one-step profiled GMM; Gamma_7=-LL'"
    ereturn local inference "boundary constraint; saved covariance is diagnostic, no ordinary Wald claim"
    ereturn scalar N=XE_N
    ereturn scalar converged=XE_conv
    ereturn scalar iterations=XE_iters
    ereturn scalar criterion=XE_obj
    ereturn scalar xmean=XE_xmean
    forvalues j=1/8 {
        ereturn scalar pmean`j'=XE_pmean`j'
    }
end
revision_post
estimates save "$REV/outputs/exact/easi_curvature_full.ster",replace
keep hh_id ym xe_positive
save "$REV/data/curvature_support.dta",replace
clear
set obs 1
gen double N=XE_N
gen double cells=XE_cells
gen double converged=XE_conv
gen double iterations=XE_iters
gen double criterion=XE_obj
gen double unconstrained_criterion=XE_unconstrained_obj
gen double criterion_increment=XE_obj-XE_unconstrained_obj
gen double derivative_rank=XE_rank
gen double gamma_maxeig=XE_Gamma_maxeig
gen double gradient_error=XE_graderr
gen double moment_error=XE_compressionerr
gen double runtime=XE_runtime
gen double support_rate=XE_positive_support
gen double root_failures=XE_rootfail
gen double nuisance_gradient=REV_BOUNDARY[1,1]
gen double kkt_cone_maxeig=REV_BOUNDARY[1,2]
gen double kkt_complementarity=REV_BOUNDARY[1,3]
gen double slutsky_asymmetry=XE_reg[1,2]
gen double slutsky_maxeig=XE_reg[1,3]
export delimited using "$REV/outputs/exact/curvature_fit.csv",replace
save "$REV/outputs/exact/curvature_fit.dta",replace
clear
svmat double XE_elasticity
rename XE_elasticity1 expenditure
rename XE_elasticity2 marshallian_own
rename XE_elasticity3 hicksian_own
rename XE_elasticity4 fitted_share
gen byte good=_n
export delimited using "$REV/outputs/exact/curvature_elasticities.csv",replace
save "$REV/outputs/exact/curvature_elasticities.dta",replace
display "EIGHT_CURVATURE_FIT_SUCCESS"
log close
