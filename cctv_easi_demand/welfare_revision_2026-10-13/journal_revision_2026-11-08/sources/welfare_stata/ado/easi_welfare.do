* Exact conditional cost-function post-estimation; eight goods, Stata/Mata only.
mata:
mata set matastrict on
struct rev_welfare {
    real rowvector b,beta,lambda
    real matrix P,D,W,A,G,F0
    real colvector X,B,u0,D0,baseok
}
RW=rev_welfare()
void rw_load(string scalar demos)
{
    external struct rev_welfare scalar RW
    real matrix FF,G7
    real scalar pos,n
    RW.b=st_matrix("XE_b");RW.P=st_data(.,tokens("ep1 ep2 ep3 ep4 ep5 ep6 ep7 ep8"))
    RW.X=st_data(.,"ex");RW.D=J(st_nobs(),1,1),st_data(.,tokens(demos))
    RW.W=st_data(.,tokens("w1 w2 w3 w4 w5 w6 w7 w8"))
    RW.B=st_data(.,"total_food_spend_pc_month");n=rows(RW.X)
    FF=xe_predict(RW.b,"easi",RW.P,RW.X,RW.D,RW.W)
    RW.F0=FF[,1..8];RW.u0=FF[,9];pos=7*cols(RW.D)
    RW.A=RW.D*rowshape(RW.b[1..pos],7)'
    RW.A=RW.A,1:-rowsum(RW.A)
    RW.beta=RW.b[pos+1..pos+7];RW.beta=RW.beta,-sum(RW.beta)
    RW.lambda=RW.b[pos+8..pos+14];RW.lambda=RW.lambda,-sum(RW.lambda)
    G7=xe_gamma(RW.b,cols(RW.D)-1,"easi")
    RW.G=(G7,-rowsum(G7))\(-colsum(G7),sum(G7))
    RW.D0=1:+RW.P*RW.beta'+2*RW.u0:*(RW.P*RW.lambda')
    for(pos=1;pos<=8;pos++) st_store(.,"wf_q0"+strofreal(pos),RW.B:*RW.F0[,pos]:/exp(st_data(.,"lp"+strofreal(pos))))
    RW.baseok=(rowmin(RW.F0):>1e-8):&(rowmissing(RW.F0):==0):&(RW.D0:>1e-8):&(RW.D0:<.)
    st_store(.,"wf_baseok",RW.baseok)
    st_store(.,"wf_u0",RW.u0)
    st_matrix("WF_GAMMA",RW.G)
    st_numscalar("WF_base_cost_error",max(abs(rw_logc(RW.P,RW.u0)-RW.X)))
}
real colvector rw_logc(real matrix P,real colvector u)
{
    external struct rev_welfare scalar RW
    return(u+rowsum(P:*RW.A)+.5*rowsum((P*RW.G):*P)+u:*(P*RW.beta')+(u:^2):*(P*RW.lambda'))
}
void rw_scenario()
{
    external struct rev_welfare scalar RW
    real matrix Delta,P1,FH1,FM1,back,Q,FF,minF
    real colvector u1,d0a,d1a,d0b,d1b,ok,lo,hi,vertex,base,recalc,cv,ev,fb,ob,err
    real scalar i,j,n,h,baseline_error,cv_error,ev_error,curv,asym
    real matrix SP
    real rowvector frow
    Delta=st_data(.,tokens("wd1 wd2 wd3 wd4 wd5 wd6 wd7 wd8"));P1=RW.P+Delta
    FH1=RW.F0+Delta*RW.G
    FF=xe_predict(RW.b,"easi",P1,RW.X,RW.D,RW.W)
    FM1=FF[,1..8];u1=FF[,9]
    back=RW.A+RW.P*RW.G+u1*RW.beta+(u1:^2)*RW.lambda
    d0a=RW.D0;d1a=1:+P1*RW.beta'+2*RW.u0:*(P1*RW.lambda')
    d0b=1:+RW.P*RW.beta'+2*u1:*(RW.P*RW.lambda')
    d1b=1:+P1*RW.beta'+2*u1:*(P1*RW.lambda')
    ok=RW.baseok:&(rowmin(FH1):>1e-8):&(rowmissing(FH1):==0):&(rowmin(FM1):>1e-8):&(rowmissing(FM1):==0):&(rowmin(back):>1e-8):&(rowmissing(back):==0)
    ok=ok:&(d1a:>1e-8):&(d1a:<.):&(d0b:>1e-8):&(d0b:<.):&(d1b:>1e-8):&(d1b:<.)
    // Validate the entire rectangle of prices P0+t Delta and utilities between u0/u1.
    // Shares are linear in t and quadratic in u. Check endpoint values and any
    // interior quadratic minima. Cost monotonicity is bilinear and its four
    // corner checks above imply monotonicity throughout that rectangle.
    lo=rowmin((RW.u0,u1));hi=rowmax((RW.u0,u1))
    for(j=1;j<=8;j++) if(RW.lambda[j]>0) {
        h=-RW.beta[j]/(2*RW.lambda[j]);vertex=J(rows(lo),1,h)
        minF=RW.A+RW.P*RW.G+vertex*RW.beta+(vertex:^2)*RW.lambda
        base=(minF[,j]:>1e-8):&((minF+Delta*RW.G)[,j]:>1e-8)
        ok=ok:&((h:<lo):|(h:>hi):|base)
    }
    cv=exp(rowsum(Delta:*RW.F0)+.5*rowsum((Delta*RW.G):*Delta)):-1
    ev=1:-exp(rw_logc(RW.P,u1)-RW.X)
    fb=rowsum((exp(Delta):-1):*RW.F0);ob=rowsum((exp(Delta):-1):*RW.W)
    st_store(.,"wf_ok",ok);st_store(.,"wf_cv",cv);st_store(.,"wf_ev",ev)
    st_store(.,"wf_fitted_basket",fb);st_store(.,"wf_observed_basket",ob)
    for(j=1;j<=8;j++) {
        st_store(.,"wf_qm"+strofreal(j),FM1[,j]:/RW.F0[,j]:*exp(-Delta[,j]):-1)
        st_store(.,"wf_qh"+strofreal(j),FH1[,j]:/RW.F0[,j]:*exp(log(1:+cv)-Delta[,j]):-1)
    }
    err=rw_logc(P1,RW.u0)-rw_logc(RW.P,RW.u0)-log(1:+cv)
    cv_error=max(abs(select(err,ok)))
    err=rw_logc(P1,u1)-RW.X;ev_error=max(abs(select(err,ok)))
    st_numscalar("WF_cv_cost_error",cv_error);st_numscalar("WF_ev_root_error",ev_error)
    st_numscalar("WF_laspeyres_violations",sum(ok:&(cv:>fb:+1e-9)))
    st_numscalar("WF_baseline_support",sum(RW.baseok))
    // Independently inspect complete Slutsky matrices at representative supported
    // rows and eleven points on the same price/utility rectangle diagonal.
    lo=selectindex(ok);curv=-1;asym=0
    for(i=1;i<=min((rows(lo),101));i++) {
        n=lo[ceil(i*rows(lo)/min((rows(lo),101)))];
        for(j=0;j<=10;j++) {
            h=j/10;frow=RW.A[n,]+(RW.P[n,]+h*Delta[n,])*RW.G+(RW.u0[n]+h*(u1[n]-RW.u0[n]))*RW.beta+(RW.u0[n]+h*(u1[n]-RW.u0[n]))^2*RW.lambda
            SP=RW.G+frow'*frow-diag(frow)
            curv=max((curv,max(symeigenvalues((SP+SP')/2))))
            asym=max((asym,max(abs(SP-SP'))))
        }
    }
    st_numscalar("WF_path_maxeig",curv);st_numscalar("WF_path_asymmetry",asym)
}
end
