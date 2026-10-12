version 17
clear all
set more off
capture log close _all
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "$cmroot/outputs/corner"
log using "$cmroot/logs/03_corner_validation.log", text replace
do "$cmroot/ado/corner_maidads.mata"
mata:
void cm_validate()
{
    real rowvector alpha,beta,low,high,p,x,h,pp,pm,q,phi,a,gap,qmax
    real matrix prices,checks,H,draws,rd,result,summary
    real scalar k,c,j,t,m,u,err,Fumax,rootcount,fu,kap,om,step,eigmax
    real scalar fh,fl,scale,buderr,kkt,monerr,symerr,homerr,costerr,zero,rate
    real scalar exact,curvature,participation,convexerror,ncase,convexmax
    checks=J(0,14,.)
    for (k=2;k<=3;k++) {
        if (k==2) {
            alpha=(.6,.4); beta=(.45,.55)
            low=(1.2,.8); high=(.12,.08)
        }
        else {
            alpha=(.55,.3,.15); beta=(.40,.35,.25)
            low=(1.2,.8,.6); high=(.12,.08,.06)
        }
        om=.7; kap=0; step=1e-5
        prices=J(0,k,.)
        for (c=1;c<=9;c++) {
            p=J(1,k,1)
            for (j=1;j<=k;j++) p[j]=exp(.55*sin(c*j))
            prices=prices\p
        }
        for (c=1;c<=rows(prices);c++) for (t=1;t<=12;t++) {
            p=prices[c,]; m=exp(-3+5*(t-1)/11)
            x=cm_demand(m,p,alpha,beta,low,high,om,kap)
            q=x[|1\k|]; u=x[k+1]
            phi=cm_phi(u,alpha,beta); a=cm_shift(u,low,high,om)
            gap=phi:/(p:*(q+a))
            exact=max(select(gap,q:>1e-9))
            kkt=0
            for (j=1;j<=k;j++) {
                if (q[j]>1e-9) kkt=max((kkt,abs(gap[j]-exact)))
                else kkt=max((kkt,max((gap[j]-exact,0))))
            }
            buderr=abs(sum(p:*q)-m)/(1+m)
            h=cm_hicks(u,p,alpha,beta,low,high,om,kap)
            costerr=abs(h[k+1]-m)/(1+m)
            H=J(k,k,.)
            for (j=1;j<=k;j++) {
                pp=p; pm=p; pp[j]=p[j]+step; pm[j]=p[j]-step
                H[,j]=(cm_hicks(u,pp,alpha,beta,low,high,om,kap)[|1\k|]-
                        cm_hicks(u,pm,alpha,beta,low,high,om,kap)[|1\k|])'/(2*step)
            }
            symerr=max(abs(H-H'))
            curvature=max(symeigenvalues((H+H')/2))
            homerr=max(abs(cm_demand(3*m,3*p,alpha,beta,low,high,om,kap)[|1\k|]-q))
            rootcount=0
            fl=cm_F(cm_q_given_u(-20,m,p,alpha,beta,low,high,om),
                    -20,alpha,beta,low,high,om,kap)
            for (scale=-19.75;scale<=20;scale=scale+.25) {
                fh=cm_F(cm_q_given_u(scale,m,p,alpha,beta,low,high,om),
                        scale,alpha,beta,low,high,om,kap)
                if (fl*fh<0) rootcount++
                fl=fh
            }
            checks=checks\(k,c,m,min(q),abs(x[k+2]),x[k+3],buderr,kkt,
                            costerr,symerr,curvature,homerr,rootcount,sum(q:==0))
        }
        qmax=J(1,k,20)
        Fumax=-1e99
        for (scale=-20;scale<=20;scale=scale+.05) {
            Fumax=max((Fumax,cm_Fu_boxmax(scale,qmax,alpha,beta,low,high,om)))
        }
        printf("K=%g exact fixed-u rectangular-domain F_u maximum: %16.10g\n",k,Fumax)
        if (Fumax>=0) _error(3498)
        // At a common u, convex upper contour sets have F(midpoint,u)>=0.
        convexmax=0
        for (c=1;c<=9;c++) for (t=1;t<=8;t++) {
            m=exp(-2+4*(t-1)/7); p=prices[c,]
            x=cm_demand(m,p,alpha,beta,low,high,om,kap)
            u=x[k+1]
            q=x[|1\k|]
            h=cm_hicks(u,prices[mod(c,9)+1,],alpha,beta,low,high,om,kap)
            convexerror=max((0,-cm_F(.37*q+.63*h[|1\k|],u,
                alpha,beta,low,high,om,kap)))
            convexmax=max((convexmax,convexerror))
        }
        printf("K=%g upper-contour midpoint violation: %16.10g\n",k,convexmax)
        if (convexmax>1e-8) _error(3498)
        draws=cm_draws(1024,k)
        rd=cm_random_demand(.2,J(1,k,1),alpha,beta,low,high,om,kap,.85,draws)
        printf("K=%g random-preference zero purchase proportions: ",k)
        mean(rd[,1..k]:==0)
        if (min(mean(rd[,1..k]:==0))<=0) _error(3498)
        if (max(mean(rd[,1..k]:==0))>=1) _error(3498)
        st_matrix("cm_random_k"+strofreal(k),mean(rd[,1..k]:==0))
    }
    st_matrix("cm_checks",checks)
    printf("Cases: %g. All checks use actual budget and KKT-selected sets.\n",rows(checks))
    if (max(checks[,5])>1e-8 | max(checks[,7])>1e-8 |
        max(checks[,8])>1e-8 | max(checks[,9])>1e-8 |
        max(checks[,10])>1e-5 | max(checks[,11])>1e-5 |
        max(checks[,12])>1e-8 | min(checks[,13])!=1 |
        max(checks[,13])!=1 | min(checks[,6])>=0) _error(3498)
}
cm_validate()
end
matrix colnames cm_checks = k price_case budget min_q root_error Fu budget_error kkt_error expenditure_error symmetry_error largest_slutsky_eigen homogeneity_error utility_roots zero_goods
clear
svmat double cm_checks, names(col)
export delimited using "$cmroot/outputs/corner/synthetic_validation.csv", replace
summarize root_error Fu budget_error kkt_error expenditure_error symmetry_error largest_slutsky_eigen homogeneity_error utility_roots
count
assert root_error<1e-8 & Fu<0 & budget_error<1e-8 & kkt_error<1e-8
assert expenditure_error<1e-8 & symmetry_error<1e-5
assert largest_slutsky_eigen<1e-5 & homogeneity_error<1e-8 & utility_roots==1
display "PASS: 216 deterministic demand cases plus upper-contour and stochastic zero-mass tests."
log close
