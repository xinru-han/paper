version 17
mata:
// Restricted corner demand and its analytic within-draw budget derivative.
real rowvector cs_response(real scalar m, real rowvector p, real rowvector alpha,
    real rowvector low, real scalar ratio, real scalar omega)
{
    real rowvector pa,threshold,logalpha,loglow,A,next,q,dq,a,ad
    real scalar u,l,r,s,C,Cd,nu,aa,pp,F,Fu,candidate,iter,j,du
    if(hasmissing((m,p,alpha,low,ratio,omega)) | m<=0 | min(p)<=0 |
       min(alpha)<=0 | min(low)<=0 | ratio<=0 | ratio>=1 | omega<=0)
        return(J(1,2*cols(p),.))
    pa=p:*low; threshold=alpha:/pa
    logalpha=alpha:*ln(alpha:/p); loglow=alpha:*ln(low)
    u=ln(m+sum(pa))+sum(logalpha)
    l=-40; r=40; u=max((l+.01,min((r-.01,u))))
    for(iter=1;iter<=40;iter++) {
        s=cm_logistic(omega*u)
        C=1-(1-ratio)*s; Cd=-(1-ratio)*omega*s*(1-s)
        A=J(1,cols(p),1)
        for(j=1;j<=cols(p)+1;j++) {
            aa=sum(alpha:*A); pp=sum(pa:*A)
            nu=aa/(m+C*pp)
            next=(threshold:>nu*C)
            if(sum(next)==0 | nu<=0 | nu>=.) return(J(1,2*cols(p),.))
            if(all(next:==A)) break
            A=next
        }
        F=sum(A:*logalpha)-aa*ln(nu)+sum((1:-A):*loglow)+(1-aa)*ln(C)-u
        Fu=Cd*(nu*pp+(1-aa)/C)-1
        if(F>=. | Fu>=0 | Fu>=.) return(J(1,2*cols(p),.))
        if(abs(F)<1e-11) break
        if(F>0) l=u
        else r=u
        candidate=u-F/Fu
        if(candidate<=l | candidate>=r | candidate>=.) candidate=(l+r)/2
        u=candidate
    }
    q=(alpha:/(nu*p)-C*low):*A
    if(iter>40 | hasmissing(q) | min(q)<-1e-10 |
       abs(sum(p:*q)-m)>1e-8*max((1,m))) return(J(1,2*cols(p),.))
    a=C*low; ad=Cd*low
    Fu=sum(alpha:*ad:/(q+a))-1
    du=-nu/Fu
    dq=(alpha:*A):/(aa*p)
    dq=dq+(Cd*du)*((pp*(alpha:*A)):/(aa*p)-(low:*A))
    if(hasmissing(dq) | min(dq)<-1e-10 | abs(sum(p:*dq)-1)>1e-8)
        return(J(1,2*cols(p),.))
    return((q,dq))
}

void cs_predict(real rowvector b, real scalar scale, real scalar draws_n)
{
    real matrix par,draw,alpha,P,Q,DQ,PI
    real rowvector low,response,qs,ds,pis
    real colvector m,typ,valid
    real scalar n,k,i,r,j,v,mult
    string rowvector pn
    par=cm_unpack(b); k=cols(par)
    draw=cm_draws(draws_n,k); alpha=J(draws_n,k,.)
    for(r=1;r<=draws_n;r++) alpha[r,]=cm_reweight(par[1,],draw[r,],par[4,2])
    pn="p":+strofreal(1..k)
    P=st_data(.,pn); m=st_data(.,"m_new")/scale; typ=st_data(.,"type")
    n=rows(m); Q=DQ=PI=J(n,k,.)
    valid=J(n,1,1)
    for(i=1;i<=n;i++) {
        mult=exp(par[4,4+typ[i]]); low=mult*par[2,]
        qs=ds=pis=J(1,k,0)
        for(r=1;r<=draws_n;r++) {
            response=cs_response(m[i],P[i,],alpha[r,],low,par[4,1],.7)
            if(hasmissing(response)) {
                valid[i]=0
                break
            }
            qs=qs+response[|1\k|]
            ds=ds+response[|k+1\2*k|]
            pis=pis+(response[|1\k|]:>0)
        }
        if(valid[i]) {
            Q[i,]=scale*qs/draws_n
            DQ[i,]=ds/draws_n
            PI[i,]=pis/draws_n
        }
        if(mod(i,20000)==0) printf("Restricted corner forecast rows %g/%g\n",i,n)
    }
    for(j=1;j<=k;j++) {
        v=st_addvar("double","cr_q"+strofreal(j)); st_store(.,v,Q[,j])
        v=st_addvar("double","cr_dqdm"+strofreal(j)); st_store(.,v,DQ[,j])
        v=st_addvar("double","cr_pi"+strofreal(j)); st_store(.,v,PI[,j])
    }
    v=st_addvar("byte","prediction_valid"); st_store(.,v,valid)
}
end
