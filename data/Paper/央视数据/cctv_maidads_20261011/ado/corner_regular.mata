version 17
mata:
// Specialization of the proven global model; avoids repeated phi/shift creation.
real rowvector cm_regular_q(real scalar m, real rowvector p, real rowvector alpha,
                            real rowvector low, real scalar ratio,
                            real scalar omega)
{
    real rowvector pa,threshold,logalpha,loglow,A,next,q
    real scalar u,l,r,s,C,Cd,nu,aa,pp,F,Fu,candidate,iter,j
    if (hasmissing((m,p,alpha,low,ratio,omega)) | m<=0 | min(p)<=0 | min(alpha)<=0 |
        max(alpha)>=. | min(low)<=0 | max(low)>=. | ratio<=0 |
        ratio>=1 | omega<=0 | omega>=.) return(J(1,cols(p),.))
    pa=p:*low
    threshold=alpha:/pa
    logalpha=alpha:*ln(alpha:/p)
    loglow=alpha:*ln(low)
    u=ln(m+sum(pa))+sum(logalpha)
    l=-40; r=40
    u=max((l+.01,min((r-.01,u))))
    for (iter=1;iter<=40;iter++) {
        s=cm_logistic(omega*u)
        C=1-(1-ratio)*s
        Cd=-(1-ratio)*omega*s*(1-s)
        A=J(1,cols(p),1)
        for (j=1;j<=cols(p)+1;j++) {
            aa=sum(alpha:*A)
            pp=sum(pa:*A)
            nu=aa/(m+C*pp)
            next=(threshold:>nu*C)
            if (sum(next)==0 | nu<=0 | nu>=.) return(J(1,cols(p),.))
            if (all(next:==A)) break
            A=next
        }
        F=sum(A:*logalpha)-aa*ln(nu)+sum((1:-A):*loglow)+(1-aa)*ln(C)-u
        Fu=Cd*(nu*pp+(1-aa)/C)-1
        if (F>=. | Fu>=0 | Fu>=.) return(J(1,cols(p),.))
        if (abs(F)<1e-11) break
        if (F>0) l=u
        else r=u
        candidate=u-F/Fu
        if (candidate<=l | candidate>=r | candidate>=.) candidate=(l+r)/2
        u=candidate
    }
    q=(alpha:/(nu*p)-C*low):*A
    if (iter>40 | hasmissing(q) | min(q)<-1e-10 |
        abs(sum(p:*q)-m)>1e-8*max((1,m))) return(J(1,cols(p),.))
    return(q)
}
end
