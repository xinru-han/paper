version 17
clear all
set more off
set matsize 800
global rebuild "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
cap log close _all
log using "$rebuild/logs/04h_exact_derivative_audit.log",text replace
do "$rebuild/ado/cctv_exact.do"
estimates use "$rebuild/outputs/exact/aids_full.ster"
local demos `e(demographics)'
scalar XE_xmean=e(xmean)
forvalues j=1/8 {
    scalar XE_pmean`j'=e(pmean`j')
}
use "$rebuild/data/analysis_monthly.dta",clear
gen double ex=lnx-XE_xmean
forvalues j=1/8 {
    gen double ep`j'=lp`j'-XE_pmean`j'
}
foreach model in aids quaids easi {
    merge 1:1 hh_id ym using "$rebuild/data/exact_support_`model'_full.dta",assert(match) nogen
}
keep if support_aids & support_quaids & support_easi
scalar XE_audit_N=_N
collapse (mean) ep1 ep2 ep3 ep4 ep5 ep6 ep7 ep8 ex w1 w2 w3 w4 w5 w6 w7 w8 `demos'
gen byte xe_positive=0
mata:
real scalar xeda_cost(real rowvector b,string scalar model,real rowvector P,
    real rowvector D,real scalar u)
{
    real rowvector R,be,la,A
    real matrix G
    real scalar nd,pos,lnap,bp,lam
    nd=cols(D)-1; pos=7*(nd+1)
    G=xe_gamma(b,nd,model); R=P[1..7]:-P[8]
    A=D*rowshape(b[1..pos],7)'; be=b[pos+1..pos+7]
    la=J(1,7,0); if(model!="aids") la=b[pos+8..pos+14]
    lnap=P[8]+sum(A:*R)+.5*R*G*R'
    if(model=="easi") return(u+lnap+(R*be')*u+(R*la')*u^2)
    bp=exp(R*be'); lam=R*la'
    return(lnap+bp*u/(1-lam*u))
}
void xeda_check(string scalar model,string scalar demos)
{
    real rowvector b,P,D,W,F,Fp,Fm,PP,PM,EMnum,EHnum,eta
    real matrix Mnum,Hnum,M,H
    real scalar X,u,t,bp,lam,h,j,pos,i
    b=st_matrix("XE_b"); P=st_data(.,tokens("ep1 ep2 ep3 ep4 ep5 ep6 ep7 ep8"))
    D=1,st_data(.,tokens(demos)); X=st_data(.,"ex")
    W=st_data(.,tokens("w1 w2 w3 w4 w5 w6 w7 w8"))
    F=xe_predict(b,model,P,X,D,W); t=F[9]; F=F[1..8]
    u=t
    if(model!="easi") {
        pos=7*cols(D); bp=exp((P[1..7]:-P[8])*b[pos+1..pos+7]')
        lam=0; if(model=="quaids") lam=(P[1..7]:-P[8])*b[pos+8..pos+14]'
        u=t/(bp+lam*t)
    }
    h=1e-5; Mnum=Hnum=J(8,8,0)
    Fp=xe_predict(b,model,P,X+h,D,W); Fm=xe_predict(b,model,P,X-h,D,W)
    eta=(ln(Fp[1..8])-ln(Fm[1..8]))/(2*h):+1
    for(j=1;j<=8;j++) {
        PP=PM=P; PP[j]=PP[j]+h; PM[j]=PM[j]-h
        Fp=xe_predict(b,model,PP,X,D,W); Fm=xe_predict(b,model,PM,X,D,W)
        Mnum[,j]=((ln(Fp[1..8])-ln(Fm[1..8]))/(2*h))'
        Mnum[j,j]=Mnum[j,j]-1
        Fp=xe_predict(b,model,PP,xeda_cost(b,model,PP,D,u),D,W)
        Fm=xe_predict(b,model,PM,xeda_cost(b,model,PM,D,u),D,W)
        Hnum[,j]=((ln(Fp[1..8])-ln(Fm[1..8]))/(2*h):+
            (xeda_cost(b,model,PP,D,u)-xeda_cost(b,model,PM,D,u))/(2*h))'
        Hnum[j,j]=Hnum[j,j]-1
    }
    M=st_matrix("XE_rep_mar"); H=st_matrix("XE_rep_hick")
    st_matrix("XE_derivative_check",(max(abs(eta'-st_matrix("XE_rep_elasticity")[,1])),max(abs(Mnum-M)),max(abs(Hnum-H)),abs(xeda_cost(b,model,P,D,u)-X)))
}
end
tempname out
postfile `out' str24 model double common_N double finite_difference_step double expenditure_max_error double marshallian_max_error double hicksian_max_error double cost_baseline_error using "$rebuild/outputs/exact/analytic_derivative_audit.dta",replace
foreach model in aids quaids easi {
    estimates use "$rebuild/outputs/exact/`model'_full.ster"
    matrix XE_b=e(b)
    local formula "`model'"
    if "`model'"=="easi_curvature" local formula "easi"
    mata: xe_elasticities("`formula'","`demos'")
    mata: xeda_check("`formula'","`demos'")
    display "Derivative audit: `model'"
    matrix list XE_derivative_check
    post `out' ("`model'") (XE_audit_N) (1e-5) (XE_derivative_check[1,1]) (XE_derivative_check[1,2]) (XE_derivative_check[1,3]) (XE_derivative_check[1,4])
    assert XE_derivative_check[1,1]<1e-6
    assert XE_derivative_check[1,2]<1e-6
    assert XE_derivative_check[1,3]<1e-6
    assert XE_derivative_check[1,4]<1e-8
}
postclose `out'
use "$rebuild/outputs/exact/analytic_derivative_audit.dta",clear
export delimited using "$rebuild/outputs/exact/analytic_derivative_audit.csv",replace
list,noobs
display "MEAT_MERGE_DERIVATIVE_SUCCESS"
log close
