version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/00_config.do"
args mode
local tag main
if "`mode'"=="pilot" local tag mainpilot
log using "$ROOT/logs/06_`tag'_audit.log",text replace
use "$ROOT/data/fitted_`tag'.dta",clear
estimates use "$ROOT/outputs/models/`tag'.ster"
do "$ROOT/ado/cctv_fit.ado"
do "$ROOT/ado/cctv_report.do"
do "$ROOT/ado/cctv_restore.do"
cctv_restore
forvalues i=1/8 {
    global CV_Z`i' "`e(syvars`i')'"
}
mata: mata matuse "$ROOT/outputs/models/`tag'_influence.mmat",replace
mata:
real matrix mm_direct(real scalar shock,real scalar delta)
{
    external struct cv_state scalar CV
    real matrix out,core,rr
    real rowvector b,map
    real colvector dy,yy,eta,phi,pdf
    real scalar i,j,k,n,nb,g,omit
    n=rows(CV.idx); nb=CV.nb; omit=st_numscalar("e(omit)")
    dy=J(n,1,delta)
    if(shock>0) dy=-st_data(CV.idx,"sw"+strofreal(shock))*delta
    yy=CV.y+dy; rr=CV.rel
    if(shock>0) for(j=1;j<=7;j++) rr[,j]=rr[,j]:+((shock==CV.goods[j])-(shock==omit))*delta
    out=J(n,8,0)
    for(i=1;i<=7;i++) {
        g=CV.goods[i]; map=CV.e[i].map
        core=CV.e[i].X[,1..nb+14]:/CV.Phi[,i]
        for(k=1;k<=CV.ord;k++) core[,1+k]=yy:^k
        core[,nb+1..nb+7]=rr; core[,nb+8..nb+14]=rr:*yy
        b=st_matrix("cv_syb"+strofreal(g))
        eta=CV.xb[,i]+dy*b[1]
        if(shock>0) for(j=1;j<=7;j++) eta=eta:+((shock==CV.goods[j])-(shock==omit))*delta*b[j+1]
        phi=normal(eta); pdf=normalden(eta)
        out[,g]=phi:*(core*CV.beta[map[1..cols(core)]])+pdf*CV.beta[map[cols(map)]]
    }
    out[,omit]=1:-rowsum(out)
    return(out)
}
void mm_main_check()
{
    external struct cv_state scalar CV
    struct cv_pred scalar R
    real matrix fp,fm,num
    real scalar j,h,err,budgeterr
    h=1e-5; R=cv_pred_all("unconditional",0)
    fp=mm_direct(0,h); fm=mm_direct(0,-h)
    budgeterr=max(abs((fp-fm)/(2*h)-R.dx)); err=0
    for(j=1;j<=8;j++) {
        R=cv_pred_all("unconditional",j)
        fp=mm_direct(j,h); fm=mm_direct(j,-h)
        err=max((err,max(abs((fp-fm)/(2*h)-R.dp))))
    }
    st_matrix("MM_CHECK",(budgeterr,err))
}
CV.fs[1].X=CV_ARCH_FP1; CV.fs[1].R=CV_ARCH_FH1
CV.fs[2].X=CV_ARCH_FP2; CV.fs[2].R=CV_ARCH_FH2
CV.fs[3].X=CV_ARCH_FP3; CV.fs[3].R=CV_ARCH_FH3
CV.fs[4].X=CV_ARCH_FP4; CV.fs[4].R=CV_ARCH_FH4
CV.fs[5].X=CV_ARCH_FP5; CV.fs[5].R=CV_ARCH_FH5
CV.fs[6].X=CV_ARCH_FP6; CV.fs[6].R=CV_ARCH_FH6
CV.fs[7].X=CV_ARCH_FP7; CV.fs[7].R=CV_ARCH_FH7
st_global("CV_OMIT",strofreal(st_numscalar("e(omit)")))
mm_main_check()
end
matrix list MM_CHECK
assert MM_CHECK[1,1]<1e-7 & MM_CHECK[1,2]<1e-7
preserve
clear
svmat double MM_CHECK
rename MM_CHECK1 expenditure_derivative_max_error
rename MM_CHECK2 price_derivative_max_error
export delimited using "$ROOT/outputs/audit/main_derivative_`tag'.csv",replace
restore
mata:
void mm_main_ci()
{
    external real matrix CV_ARCH_P
    external struct cv_state scalar CV
    struct cv_pred scalar R,P
    real matrix IP,J,score,res
    real colvector keep,a
    real rowvector jac
    real scalar s,t,n,g,den,val,se,crit,k
    IP=CV_ARCH_P
    for(k=1;k<=7;k++) IP=(IP,CV.fs[k].X)
    g=rows(IP); n=rows(CV.idx); res=J(4,7,.)
    R=cv_pred_all("unconditional",0); P=cv_pred_all("unconditional",6)
    crit=invttail(g-1,.025)
    for(s=1;s<=2;s++) {
        keep=J(n,1,1); if(s==2) keep=rowmin(R.W):>1e-8
        a=exp(st_data(CV.idx,"lnx")-st_data(CV.idx,"lp6")):*keep
        den=cross(a,R.W[,6])
        for(t=1;t<=2;t++) {
            if(t==1) {val=1+cross(a,R.dx[,6])/den; jac=cv_el_jac(R,6,0,keep);}
            else {val=-1+cross(a,P.dp[,6])/den; jac=cv_el_jac(P,6,6,keep);}
            score=IP*jac'; se=sqrt(sum(score:^2)*g/(g-1))
            res[(s-1)*2+t,]=(s,t,sum(keep),val,se,val-crit*se,val+crit*se)
        }
    }
    st_matrix("MM_CI",res)
}
mm_main_ci()
end
clear
svmat double MM_CI
rename MM_CI1 support_code
rename MM_CI2 elasticity_code
rename MM_CI3 N
rename MM_CI4 estimate
rename MM_CI5 se_province_two_step
rename MM_CI6 ci_lower
rename MM_CI7 ci_upper
gen str20 sample=cond(support_code==1,"raw_all","common_positive")
gen str20 type=cond(elasticity_code==1,"expenditure","own_price")
export delimited using "$ROOT/outputs/inference/other_meat_`tag'.csv",replace
list sample type estimate se_province_two_step ci_lower ci_upper,noobs
display "MEAT_MERGE_MAIN_AUDIT_SUCCESS"
log close
