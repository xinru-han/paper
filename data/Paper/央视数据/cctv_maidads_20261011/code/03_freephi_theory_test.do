version 17
clear all
set more off
capture log close _all
global cfroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "$cfroot/outputs/corner_freephi"
log using "$cfroot/logs/03_freephi_theory_test.log", text replace
do "$cfroot/ado/corner_maidads.mata"
do "$cfroot/ado/corner_regular.mata"
do "$cfroot/ado/corner_freephi.mata"
mata:
void cf_test()
{
    real rowvector alpha,beta,low,qmax,eps,q,q1,q2,b
    real matrix draw,tab,par,AA,BB,LO,QQ,P,vectorpred,scalarpred,SOL,HQ,SETS
    real rowvector A,p,phi
    real scalar n,j,u,r,fu,bound,signedb,tv,span,err,viol,solvererr,symerr,ownmax
    real scalar m,omega,h,ms,budgeterr,roots,count,C,shift,aa
    rseed(761091)
    viol=0; err=0; solvererr=0; budgeterr=0
    tab=J(0,5,.)
    for (n=1;n<=1000;n++) {
        alpha=cf_softmax(rnormal(1,8,0,1.5))
        beta=cf_softmax(rnormal(1,8,0,1.5))
        low=exp(rnormal(1,8,-2,1)); qmax=exp(rnormal(1,8,2,1))
        eps=rnormal(1,8,0,3)
        span=cf_ratio_span(alpha,beta)
        alpha=cm_reweight(alpha,eps,2)
        beta=cm_reweight(beta,eps,2)
        err=max((err,abs(span-cf_ratio_span(alpha,beta))))
        tv=cf_TV(alpha,beta)
        if (tv>cf_tv_span_bound(span)+1e-12) viol++
        r=.01+.98*runiform(1,1); omega=.1+2*runiform(1,1)
        signedb=cf_Fu_signed_bound(qmax,alpha,beta,low,r)
        bound=cf_Fu_uniform_bound(qmax,alpha,beta,low,r)
        for (j=1;j<=10;j++) {
            u=-15+30*runiform(1,1); q=qmax:*runiform(1,8)
            fu=cm_Fu(q,u,alpha,beta,low,r*low,omega)
            if (fu>signedb+1e-12 | fu>bound+1e-12) viol++
        }
    }
    tab=tab\(1,10000,viol,err,.)
    // Signed expression can be negative: the uncorrected A/4 claim fails.
    alpha=(.1,.9); beta=(.9,.1); low=(.001,10); qmax=(.001,.001)
    signedb=cf_Fu_signed_bound(qmax,alpha,beta,low,.5)
    fu=cm_Fu(J(1,2,0),-30,alpha,beta,low,.5*low,1)
    if (signedb!=-1 | fu>signedb+1e-10) viol++
    tab=tab\(2,1,signedb,fu,.)
    // Sharp likelihood-ratio TV bound at two extreme goods.
    for (j=1;j<=50;j++) {
        span=j/10
        alpha=(1/(1+exp(-span/2)),1/(1+exp(span/2)))
        beta=alpha:*(exp(-span/2),exp(span/2))
        err=max((err,abs(cf_TV(alpha,beta)-cf_tv_span_bound(span))))
    }
    tab=tab\(3,50,0,err,.)
    // Candidate cap guarantees the margin for every family and taste draw.
    qmax=J(1,8,100)
    for (n=1;n<=100;n++) {
        b=rnormal(1,27,0,1)
        b[|8\15|]=b[|8\15|]:-2
        par=cf_unpack(b,qmax)
        draw=cm_draws(64,8)
        for (j=1;j<=4;j++) {
            low=exp(par[5,4+j])*par[3,]
            bound=cf_Fu_uniform_bound(qmax,par[1,],par[2,],low,par[5,1])
            if (bound>-.1+1e-12) viol++
        }
        alpha=cm_reweight(par[1,],draw[1,],par[5,2])
        beta=cm_reweight(par[2,],draw[1,],par[5,2])
        m=.05+5*runiform(1,1)
        q=cf_q(m,J(1,8,1),alpha,beta,par[3,],par[5,1],.7)
        q1=cm_demand(m,J(1,8,1),alpha,beta,par[3,],par[4,],.7,0)
        if (hasmissing(q) | hasmissing(q1)) viol++
        else {
            solvererr=max((solvererr,max(abs(q-q1[|1\8|]))))
            budgeterr=max((budgeterr,abs(sum(q)-m)))
        }
    }
    tab=tab\(4,400,viol,solvererr,budgeterr)
    // Vector roots agree with the scalar general solver and alpha=beta fast path.
    b=J(1,27,0); b[|8\15|]=J(1,8,-2)
    b[|21\27|]=(.5,-.5,.4,-.3,.2,-.2,.1)
    par=cf_unpack(b,qmax); draw=cm_draws(64,8)
    AA=J(64,8,.); BB=AA
    for (j=1;j<=64;j++) {
        AA[j,]=cm_reweight(par[1,],draw[j,],par[5,2])
        BB[j,]=cm_reweight(par[2,],draw[j,],par[5,2])
    }
    P=exp(rnormal(64,8,0,.4)); LO=J(64,1,1)*par[3,]
    QQ=cf_batch_q(J(64,1,1),P,AA,BB,LO,par[5,1],.7)
    for (j=1;j<=64;j++) {
        q=cf_q(1,P[j,],AA[j,],BB[j,],LO[j,],par[5,1],.7)
        solvererr=max((solvererr,max(abs(q-QQ[j,]))))
    }
    vectorpred=cf_predict_vector(b,(.2\.5\1\2),J(4,8,1),(1\2\3\4),draw,qmax)
    scalarpred=cf_predict(b,(.2\.5\1\2),J(4,8,1),(1\2\3\4),draw,qmax)
    solvererr=max((solvererr,max(abs(vectorpred-scalarpred))))
    vectorpred=cf_predict_vector(b,.5,J(1,8,1),3,draw,qmax)
    scalarpred=cf_predict(b,.5,J(1,8,1),3,draw,qmax)
    solvererr=max((solvererr,max(abs(vectorpred-scalarpred))))
    SOL=cf_batch_solution(J(64,1,1),P,AA,BB,LO,par[5,1],.7)
    P[,1]=1.05*P[,1]
    HQ=cf_batch_hicks(SOL[,9],P,AA,BB,LO,par[5,1],.7)
    for (j=1;j<=64;j++) {
        q=cm_hicks(SOL[j,9],P[j,],AA[j,],BB[j,],LO[j,],par[5,1]*LO[j,],.7,0)
        solvererr=max((solvererr,max(abs(q-HQ[j,]))))
    }
    b[|21\27|]=J(1,7,0)
    par=cf_unpack(b,qmax)
    QQ=cf_batch_q(J(64,1,1),P,AA,AA,LO,par[5,1],.7)
    for (j=1;j<=64;j++) {
        q=cm_regular_q(1,P[j,],AA[j,],LO[j,],par[5,1],.7)
        solvererr=max((solvererr,max(abs(q-QQ[j,]))))
    }
    tab=tab\(5,384,viol,solvererr,.)
    // Every nonempty purchase set is an endogenous KKT solution, not supplied.
    qmax=J(1,8,10000); b=J(1,27,0)
    b[|8\15|]=J(1,8,ln(.7))
    b[|21\27|]=(1,-1,.8,-.8,.6,-.6,.4)
    par=cf_unpack(b,qmax); phi=(par[1,]+par[2,])/2
    C=(1+par[5,1])/2; SETS=J(0,4,.)
    for (n=1;n<=255;n++) {
        A=J(1,8,0)
        for (j=1;j<=8;j++) A[j]=mod(floor(n/2^(j-1)),2)
        aa=sum(A:*phi)
        shift=exp((-sum(phi:*ln(par[3,]))-(1-aa)*ln(C))/aa)-C
        q=shift*par[3,]:*A
        p=(phi:/(q+C*par[3,])):*A+(2*phi:/(C*par[3,])):*(1:-A)
        m=sum(p:*q)
        q1=cf_q(m,p,par[1,],par[2,],par[3,],par[5,1],.7)
        q2=cm_hicks(0,p,par[1,],par[2,],par[3,],par[4,],.7,0)
        if (hasmissing(q1) | hasmissing(q2) | max(q)>max(qmax) |
            any((q1:>1e-9):!=A)) _error(3498)
        solvererr=max((solvererr,max(abs(q1-q)),max(abs(q2[1..8]-q))))
        SETS=SETS\(n,sum(A),max(abs(q1-q)),abs(sum(p:*q1)-m))
    }
    tab=tab\(6,255,0,solvererr,max(SETS[,4]))
    st_matrix("cf_allsets",SETS)
    st_matrix("cf_theory_tests",tab)
    st_numscalar("cf_test_violations",viol)
    if (viol>0 | err>1e-11 | solvererr>1e-8 | budgeterr>1e-9) _error(3498)
}
cf_test()
end
clear
matrix colnames cf_theory_tests = test_id checks violations_or_bound max_gap_or_Fu budget_error
svmat double cf_theory_tests, names(col)
export delimited "$cfroot/outputs/corner_freephi/theory_tests.csv", replace
clear
matrix colnames cf_allsets = consumption_set_index positive_goods maximum_quantity_gap budget_error
svmat double cf_allsets, names(col)
export delimited "$cfroot/outputs/corner_freephi/all_255_consumption_sets.csv", replace
capture confirm file "$cfroot/data/corner_freephi_support.dta"
if !_rc {
    use "$cfroot/data/corner_freephi_support.dta", clear
    mata:
    void cf_actual_test()
    {
        real matrix P,AA,BB,LO,Q,S
        real colvector ix,m,typ
        real rowvector b,parq,q,low
        real matrix par
        real scalar j,error,budgeterr
        ix=ceil((1::320)*st_nobs()/320)
        m=st_data(ix,"scaled_m")
        P=st_data(ix,("p1","p2","p3","p4","p5","p6","p7","p8"))
        b=J(1,27,0); b[|8\15|]=J(1,8,-2)
        b[|21\27|]=(.5,-.5,.4,-.3,.2,-.2,.1)
        parq=2*max(m):/colmin(P)
        par=cf_unpack(b,parq)
        AA=J(320,1,1)*par[1,]; BB=J(320,1,1)*par[2,]
        LO=J(320,1,1)*par[3,]
        Q=cf_batch_q(m,P,AA,BB,LO,par[5,1],.7)
        error=0
        for (j=1;j<=320;j++) {
            q=cm_demand(m[j],P[j,],AA[j,],BB[j,],LO[j,],par[5,1]*LO[j,],.7,0)
            if (hasmissing(q) | hasmissing(Q[j,])) _error(3498)
            error=max((error,max(abs(Q[j,]-q[|1\8|]))))
        }
        budgeterr=max(abs(rowsum(P:*Q)-m):/rowmax((J(320,1,1),m)))
        Q=cf_batch_q(m,P,AA,AA,LO,par[5,1],.7)
        for (j=1;j<=320;j++) {
            q=cm_regular_q(m[j],P[j,],AA[j,],LO[j,],par[5,1],.7)
            if (hasmissing(q) | hasmissing(Q[j,])) _error(3498)
            error=max((error,max(abs(Q[j,]-q))))
        }
        if (error>1e-8 | budgeterr>1e-9) _error(3498)
        st_matrix("cf_actual_test",(320,error,budgeterr))
    }
    cf_actual_test()
    end
    clear
    matrix colnames cf_actual_test = actual_support_points maximum_solver_gap relative_budget_error
    svmat double cf_actual_test, names(col)
    export delimited "$cfroot/outputs/corner_freephi/actual_solver_tests.csv", replace
}
display "FREEPHI_THEORY_TEST_PASSED"
log close
