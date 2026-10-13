version 17
mata:

real scalar cf_TV(real rowvector alpha, real rowvector beta)
{
    return(sum(abs(beta-alpha))/2)
}

real scalar cf_ratio_span(real rowvector alpha, real rowvector beta)
{
    real rowvector z
    z=ln(beta:/alpha)
    return(max(z)-min(z))
}

real scalar cf_tv_span_bound(real scalar H)
{
    return((1-exp(-H/2))/(1+exp(-H/2)))
}

real scalar cf_log_range(real rowvector qmax, real rowvector low, real scalar ratio)
{
    return(max(ln(qmax:/ratio+low))-min(ln(low)))
}

real scalar cf_Fu_signed_bound(real rowvector qmax, real rowvector alpha,
                              real rowvector beta, real rowvector low,
                              real scalar ratio)
{
    real rowvector delta
    real scalar A
    delta=beta-alpha
    A=sum(delta:*(delta:>0):*ln(qmax:/ratio+low))+
        sum(delta:*(delta:<0):*ln(low))
    return(max((0,A))/4-1)
}

real scalar cf_Fu_uniform_bound(real rowvector qmax, real rowvector alpha,
                               real rowvector beta, real rowvector low,
                               real scalar ratio)
{
    return(cf_tv_span_bound(cf_ratio_span(alpha,beta))*
            cf_log_range(qmax,low,ratio)/4-1)
}

// Common positive taste multipliers preserve the endpoint log-ratio span.
real rowvector cf_softmax(real rowvector x)
{
    x=exp(x:-max(x))
    return(x:/sum(x))
}

real matrix cf_unpack(real rowvector b, real rowvector qmax)
{
    real rowvector alpha,beta,low,eta,d
    real scalar ratio,sigma,R,j,mult,tmax,Hcap
    alpha=cf_softmax((b[|1\7|],0))
    low=exp(b[|8\15|])
    ratio=.02+.96*cm_logistic(b[16])
    sigma=.05+3.95*cm_logistic(b[17])
    eta=(0,b[|18\20|])
    R=0
    for (j=1;j<=4;j++) {
        mult=exp(eta[j])
        R=max((R,cf_log_range(qmax,mult*low,ratio)))
    }
    tmax=min((.95,3.6/R))
    Hcap=.99*2*ln((1+tmax)/(1-tmax))
    d=J(1,8,0)
    for (j=1;j<=7;j++) d[j]=2*cm_logistic(b[20+j])-1
    beta=cf_softmax(ln(alpha)+Hcap*d/2)
    return(alpha\beta\low\ratio*low\
        (ratio,sigma,.7,0,eta)\(Hcap,R,J(1,6,0)))
}

// Fixed-budget scalar root with the exact common-shift envelope derivative.
real rowvector cf_q(real scalar m, real rowvector p, real rowvector alpha,
                    real rowvector beta, real rowvector low, real scalar ratio,
                    real scalar omega)
{
    real rowvector pa,phi,dphi,A,next,q,logqa
    real scalar u,l,r,s,t,C,Cd,nu,aa,pp,F,Fu,candidate,iter,j,fl,fr
    if (hasmissing((m,p,alpha,beta,low,ratio,omega)) | m<=0 | min(p)<=0 |
        min(alpha)<=0 | min(beta)<=0 | min(low)<=0 | ratio<=0 | ratio>=1 |
        omega<=0) return(J(1,cols(p),.))
    pa=p:*low
    u=ln(m+sum(pa))+sum(alpha:*ln(alpha:/p))
    l=-40; r=40
    fl=cm_F(cm_q_given_u(l,m,p,alpha,beta,low,ratio*low,omega),
             l,alpha,beta,low,ratio*low,omega,0)
    fr=cm_F(cm_q_given_u(r,m,p,alpha,beta,low,ratio*low,omega),
             r,alpha,beta,low,ratio*low,omega,0)
    if (hasmissing((fl,fr)) | fl<=0 | fr>=0) return(J(1,cols(p),.))
    u=max((l+.01,min((r-.01,u))))
    for (iter=1;iter<=80;iter++) {
        s=cm_logistic(u); t=cm_logistic(omega*u)
        phi=alpha*(1-s)+beta*s
        dphi=(beta-alpha)*s*(1-s)
        C=1-(1-ratio)*t
        Cd=-(1-ratio)*omega*t*(1-t)
        A=J(1,cols(p),1)
        for (j=1;j<=cols(p)+1;j++) {
            aa=sum(phi:*A); pp=sum(pa:*A)
            nu=aa/(m+C*pp)
            next=(phi:/(pa*C):>nu)
            if (sum(next)==0 | nu<=0 | nu>=.) return(J(1,cols(p),.))
            if (all(next:==A)) break
            A=next
        }
        if (j>cols(p)+1) return(J(1,cols(p),.))
        q=(phi:/(nu*p)-C*low):*A
        if (hasmissing(q) | min(q)<-1e-10) return(J(1,cols(p),.))
        logqa=ln(q+C*low)
        F=sum(phi:*logqa)-u
        Fu=sum(dphi:*logqa)+Cd*(nu*pp+(1-aa)/C)-1
        if (hasmissing((F,Fu)) | Fu>=0) return(J(1,cols(p),.))
        if (abs(F)<1e-11) break
        if (F>0) l=u
        else r=u
        candidate=u-F/Fu
        if (candidate<=l | candidate>=r | candidate>=.) candidate=(l+r)/2
        u=candidate
    }
    if (iter>80 | abs(sum(p:*q)-m)>1e-8*max((1,m)))
        return(J(1,cols(p),.))
    return(q)
}

real matrix cf_predict(real rowvector b, real colvector m, real matrix p,
                        real colvector type, real matrix draws,
                        real rowvector qmax)
{
    real matrix par,out,aa,bb
    real rowvector low,q
    real scalar i,r,nd,mult,sigma
    par=cf_unpack(b,qmax)
    low=par[3,]; sigma=par[5,2]; nd=rows(draws)
    aa=J(nd,8,.); bb=aa
    for (r=1;r<=nd;r++) {
        aa[r,]=cm_reweight(par[1,],draws[r,],sigma)
        bb[r,]=cm_reweight(par[2,],draws[r,],sigma)
    }
    out=J(rows(m),15,0)
    for (i=1;i<=rows(m);i++) {
        if (max(m[i]:/p[i,]:/qmax)>1+1e-12)
            return(J(rows(m),15,.))
        mult=exp(par[5,4+type[i]])
        for (r=1;r<=nd;r++) {
            q=cf_q(m[i],p[i,],aa[r,],bb[r,],mult*low,par[5,1],.7)
            if (hasmissing(q)) return(J(rows(m),15,.))
            out[i,1..7]=out[i,1..7]+p[i,1..7]:*q[|1\7|]/m[i]/nd
            out[i,8..15]=out[i,8..15]+(q:>0)/nd
        }
    }
    return(out)
}

// All rows are independent budget problems; no row is discarded on failure.
real matrix cf_batch_given_u(real colvector u, real colvector m, real matrix p,
                            real matrix alpha, real matrix beta, real matrix low,
                            real scalar ratio, real scalar omega)
{
    real colvector s,t,C,Cd,aa,pp,nu,F,Fu
    real matrix phi,phid,pa,A,next,q,logqa
    real scalar j,k
    k=cols(p)
    s=1:/(1:+exp(-u)); t=1:/(1:+exp(-omega*u))
    C=1:-(1-ratio)*t; Cd=-(1-ratio)*omega*t:*(1:-t)
    phi=alpha:*(1:-s)+beta:*s
    phid=(beta-alpha):*(s:*(1:-s))
    pa=p:*low
    A=J(rows(p),k,1)
    for (j=1;j<=k+1;j++) {
        aa=rowsum(phi:*A); pp=rowsum(pa:*A)
        nu=aa:/(m+C:*pp)
        next=(phi:/(pa:*C):>nu)
        if (min(rowsum(next))==0 | min(nu)<=0 | hasmissing(nu))
            return(J(rows(p),k+2,.))
        if (all(next:==A)) break
        A=next
    }
    if (j>k+1) return(J(rows(p),k+2,.))
    q=(phi:/(p:*nu)-low:*C):*A
    if (hasmissing(q) | min(q)<-1e-10) return(J(rows(p),k+2,.))
    logqa=ln(q+low:*C)
    F=rowsum(phi:*logqa)-u
    Fu=rowsum(phid:*logqa)+Cd:*(nu:*pp+(1:-aa):/C):-1
    return((q,F,Fu))
}

real matrix cf_batch_solution(real colvector m, real matrix p, real matrix alpha,
                              real matrix beta, real matrix low, real scalar ratio,
                              real scalar omega)
{
    real colvector u,l,r,F,Fu,candidate,unfinished,bad
    real matrix sol
    real scalar n,k,iter
    n=rows(m); k=cols(p)
    if (hasmissing((m,p,alpha,beta,low)) | min(m)<=0 | min(p)<=0 |
        min(alpha)<=0 | min(beta)<=0 | min(low)<=0 | ratio<=0 | ratio>=1)
        return(J(n,k+3,.))
    l=J(n,1,-40); r=J(n,1,40)
    sol=cf_batch_given_u(l,m,p,alpha,beta,low,ratio,omega)
    if (hasmissing(sol) | min(sol[,k+1])<=0) return(J(n,k+3,.))
    sol=cf_batch_given_u(r,m,p,alpha,beta,low,ratio,omega)
    if (hasmissing(sol) | max(sol[,k+1])>=0) return(J(n,k+3,.))
    u=ln(m+rowsum(p:*low))+rowsum(alpha:*ln(alpha:/p))
    u=rowmax((l:+.01,rowmin((r:-.01,u))))
    for (iter=1;iter<=80;iter++) {
        sol=cf_batch_given_u(u,m,p,alpha,beta,low,ratio,omega)
        if (hasmissing(sol)) return(J(n,k+3,.))
        F=sol[,k+1]; Fu=sol[,k+2]
        if (max(Fu)>=0) return(J(n,k+3,.))
        unfinished=(abs(F):>=1e-11)
        if (sum(unfinished)==0) break
        l=l:*(1:-(unfinished:&(F:>0)))+u:*(unfinished:&(F:>0))
        r=r:*(1:-(unfinished:&(F:<=0)))+u:*(unfinished:&(F:<=0))
        candidate=u-F:/Fu
        bad=(candidate:<=l):|(candidate:>=r):|(candidate:>=.)
        candidate=candidate:*(1:-bad)+(l+r):/2:*bad
        u=u:*(1:-unfinished)+candidate:*unfinished
    }
    if (iter>80 | max(abs(rowsum(p:*sol[,1..k])-m):/rowmax((J(n,1,1),m)))>1e-8)
        return(J(n,k+3,.))
    return((sol[,1..k],u,sol[,k+1..k+2]))
}

real matrix cf_batch_q(real colvector m, real matrix p, real matrix alpha,
                       real matrix beta, real matrix low, real scalar ratio,
                       real scalar omega)
{
    return(cf_batch_solution(m,p,alpha,beta,low,ratio,omega)[,1..cols(p)])
}

real matrix cf_batch_hicks(real colvector u, real matrix p, real matrix alpha,
                           real matrix beta, real matrix low, real scalar ratio,
                           real scalar omega)
{
    real colvector s,t,C,aa,lognu,nu
    real matrix phi,a,A,next,q
    real scalar j,k
    k=cols(p)
    s=1:/(1:+exp(-u)); t=1:/(1:+exp(-omega*u)); C=1:-(1-ratio)*t
    phi=alpha:*(1:-s)+beta:*s; a=low:*C
    if (hasmissing((u,p,phi,a)) | min(p)<=0 | min(phi)<=0 | min(a)<=0)
        return(J(rows(p),k+1,.))
    A=J(rows(p),k,1)
    for (j=1;j<=k+1;j++) {
        aa=rowsum(phi:*A)
        if (min(aa)<=0) return(J(rows(p),k+1,.))
        lognu=(rowsum(A:*phi:*ln(phi:/p))+
            rowsum((1:-A):*phi:*ln(a))-u):/aa
        nu=exp(lognu)
        next=(phi:/(p:*a):>nu)
        if (hasmissing(nu) | min(nu)<=0 | min(rowsum(next))==0)
            return(J(rows(p),k+1,.))
        if (all(next:==A)) break
        A=next
    }
    if (j>k+1) return(J(rows(p),k+1,.))
    q=(phi:/(p:*nu)-a):*A
    if (hasmissing(q) | min(q)<-1e-10 |
        max(abs(rowsum(phi:*ln(q+a))-u))>1e-9)
        return(J(rows(p),k+1,.))
    return((q,rowsum(p:*q)))
}

real matrix cf_predict_vector(real rowvector b, real colvector m, real matrix p,
                             real colvector type, real matrix draws,
                             real rowvector qmax)
{
    real matrix par,out,aa,bb,P,Q,LO,W,B
    real colvector hi,di,mm,mult
    real rowvector low
    real scalar i,j,r,nd,last,nblock,offset,sigma
    par=cf_unpack(b,qmax)
    low=par[3,]; sigma=par[5,2]; nd=rows(draws)
    aa=J(nd,8,.); bb=aa
    for (r=1;r<=nd;r++) {
        aa[r,]=cm_reweight(par[1,],draws[r,],sigma)
        bb[r,]=cm_reweight(par[2,],draws[r,],sigma)
    }
    out=J(rows(m),15,0)
    if (max((m*J(1,8,1)):/p:/(J(rows(m),1,1)*qmax))>1+1e-12)
        return(J(rows(m),15,.))
    for (offset=1;offset<=rows(m);offset=offset+256) {
        last=min((rows(m),offset+255)); nblock=last-offset+1
        hi=ceil((1::nblock*nd):/nd):+offset:-1
        di=mod((1::nblock*nd):-1,nd):+1
        P=p[hi,]; mm=vec(m[hi])
        mult=exp(par[5,4:+type[hi]])'
        LO=mult*low
        Q=cf_batch_q(mm,P,aa[di,],bb[di,],LO,par[5,1],.7)
        if (hasmissing(Q)) return(J(rows(m),15,.))
        W=P[,1..7]:*Q[,1..7]:/mm
        B=Q:>0
        for (i=1;i<=nblock;i++) {
            j=(i-1)*nd+1
            out[offset+i-1,1..7]=colsum(W[|j,1\j+nd-1,7|])/nd
            out[offset+i-1,8..15]=colsum(B[|j,1\j+nd-1,8|])/nd
        }
    }
    return(out)
}

end
