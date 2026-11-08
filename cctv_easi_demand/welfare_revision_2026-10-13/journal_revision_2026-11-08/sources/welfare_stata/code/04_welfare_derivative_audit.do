version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/welfare_revision_2026-10-13/code/00_config.do"
log using "$REV/logs/04_welfare_derivative_audit.log",text replace
do "$REV/ado/cctv_exact.do"
do "$REV/ado/easi_welfare.do"
estimates use "$REV/outputs/exact/easi_curvature_full.ster"
matrix XE_b=e(b)
use "$REV/data/curvature_micro.dta",clear
* Deterministic evaluation grid only; the estimated model still uses all observations.
keep if mod(_n,1139)==0
gen byte wf_baseok=0
gen double wf_u0=.
forvalues j=1/8 {
    gen double wf_q0`j'=.
}
mata: rw_load("$DEMOS")
mata:
void audit_cost_derivatives()
{
    external struct rev_welfare scalar RW
    real scalar i,j,h,firsterr,seconderr,ey,cov
    real matrix P0,P1,P2,F0,G,S
    real colvector u,C0,cp,cm,cmm,cpm,cmp,cpp,idx,num,anal
    idx=selectindex(RW.baseok);P0=RW.P[idx,];u=RW.u0[idx]
    F0=RW.F0[idx,];G=RW.G
    // Restrict the covariate cost intercept to exactly the selected audit rows.
    RW.A=RW.A[idx,]
    C0=rw_logc(P0,u)
    firsterr=0;seconderr=0;h=1e-4
    for(j=1;j<=8;j++) {
        P1=P0;P2=P0;P1[,j]=P1[,j]:+h;P2[,j]=P2[,j]:-h
        num=(rw_logc(P1,u)-rw_logc(P2,u))/(2*h)
        firsterr=max((firsterr,max(abs(num-F0[,j]))))
        for(i=1;i<=8;i++) {
            if(i==j) {
                P1=P0;P2=P0;P1[,j]=P1[,j]:+ln(1+h);P2[,j]=P2[,j]:+ln(1-h)
                num=(exp(rw_logc(P1,u)-C0):-2:+exp(rw_logc(P2,u)-C0))/(h^2)
            }
            else {
                P1=P0;P1[,i]=P1[,i]:+ln(1+h);P1[,j]=P1[,j]:+ln(1+h)
                cpp=exp(rw_logc(P1,u)-C0)
                P1=P0;P1[,i]=P1[,i]:+ln(1+h);P1[,j]=P1[,j]:+ln(1-h)
                cpm=exp(rw_logc(P1,u)-C0)
                P1=P0;P1[,i]=P1[,i]:+ln(1-h);P1[,j]=P1[,j]:+ln(1+h)
                cmp=exp(rw_logc(P1,u)-C0)
                P1=P0;P1[,i]=P1[,i]:+ln(1-h);P1[,j]=P1[,j]:+ln(1-h)
                cmm=exp(rw_logc(P1,u)-C0)
                num=(cpp-cpm-cmp+cmm)/(4*h^2)
            }
            anal=J(rows(F0),1,G[i,j])+F0[,i]:*F0[,j]-(i==j)*F0[,i]
            seconderr=max((seconderr,max(abs(num-anal))))
        }
    }
    st_matrix("WF_DERIVATIVE_AUDIT",(rows(P0),firsterr,seconderr))
}
audit_cost_derivatives()
end
matrix list WF_DERIVATIVE_AUDIT
assert WF_DERIVATIVE_AUDIT[1,2]<1e-7 & WF_DERIVATIVE_AUDIT[1,3]<1e-5
clear
svmat double WF_DERIVATIVE_AUDIT
rename WF_DERIVATIVE_AUDIT1 evaluation_points
rename WF_DERIVATIVE_AUDIT2 shephard_derivative_error
rename WF_DERIVATIVE_AUDIT3 scaled_price_hessian_error
export delimited using "$REV/outputs/audit/welfare_derivatives.csv",replace
display "WELFARE_DERIVATIVE_AUDIT_SUCCESS"
log close
