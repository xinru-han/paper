version 17
mata:

real scalar cm_logistic(real scalar x)
{
    if (x>=0) return(1/(1+exp(-x)))
    return(exp(x)/(1+exp(x)))
}

real rowvector cm_phi(real scalar u, real rowvector alpha, real rowvector beta)
{
    real scalar s
    s=cm_logistic(u)
    return(alpha*(1-s)+beta*s)
}

real rowvector cm_shift(real scalar u, real rowvector low, real rowvector high,
                       real scalar omega)
{
    real scalar s
    s=cm_logistic(omega*u)
    return(low*(1-s)+high*s)
}

// The budget water-filling solution drops inactive goods until KKT closes.
real rowvector cm_q_given_u(real scalar u, real scalar m, real rowvector p,
                           real rowvector alpha, real rowvector beta,
                           real rowvector low, real rowvector high,
                           real scalar omega)
{
    real rowvector phi, a, active, next, q
    real scalar nu, j
    phi=cm_phi(u,alpha,beta)
    a=cm_shift(u,low,high,omega)
    if (hasmissing((m,p,phi,a)) | m<=0 | min(p)<=0 | min(phi)<=0 |
        max(phi)>=. | min(a)<=0 | max(a)>=.) return(J(1,cols(p),.))
    active=J(1,cols(p),1)
    for (j=1;j<=cols(p)+1;j++) {
        nu=sum(phi:*active)/(m+sum(p:*a:*active))
        next=(phi:/(p:*a):>nu)
        if (sum(next)==0 | nu<=0 | nu>=.) return(J(1,cols(p),.))
        if (all(next:==active)) break
        active=next
    }
    q=(phi:/(nu*p)-a):*active
    if (j>cols(p)+1 | hasmissing(q) | min(q)<-1e-10 |
        abs(sum(p:*q)-m)>1e-8*max((1,m))) return(J(1,cols(p),.))
    return(q)
}

real scalar cm_F(real rowvector q, real scalar u, real rowvector alpha,
                 real rowvector beta, real rowvector low, real rowvector high,
                 real scalar omega, real scalar kappa)
{
    return(sum(cm_phi(u,alpha,beta):*ln(q+cm_shift(u,low,high,omega)))-u-kappa)
}

real scalar cm_Fu(real rowvector q, real scalar u, real rowvector alpha,
                  real rowvector beta, real rowvector low, real rowvector high,
                  real scalar omega)
{
    real scalar s, t
    real rowvector phi, a, phid, ad
    s=cm_logistic(u)
    t=cm_logistic(omega*u)
    phi=alpha*(1-s)+beta*s
    a=low*(1-t)+high*t
    phid=(beta-alpha)*s*(1-s)
    ad=(high-low)*omega*t*(1-t)
    return(sum(phid:*ln(q+a)+phi:*ad:/(q+a))-1)
}

// The envelope derivative is F_u because the budget is fixed along q(u).
real rowvector cm_demand(real scalar m, real rowvector p, real rowvector alpha,
                        real rowvector beta, real rowvector low, real rowvector high,
                        real scalar omega, real scalar kappa)
{
    real scalar l, r, u, f, fu, candidate, iter, fl, fr
    real rowvector q
    if (hasmissing((m,p,alpha,beta,low,high,omega,kappa)) | m<=0 | min(p)<=0 | min(low)<=0 |
        max(low)>=. | min(high)<=0 | max(high)>=.) {
        return(J(1,cols(p)+3,.))
    }
    l=-40
    r=40
    fl=cm_F(cm_q_given_u(l,m,p,alpha,beta,low,high,omega),
            l,alpha,beta,low,high,omega,kappa)
    fr=cm_F(cm_q_given_u(r,m,p,alpha,beta,low,high,omega),
            r,alpha,beta,low,high,omega,kappa)
    if (fl<=0 | fr>=0 | fl>=. | fr>=.) return(J(1,cols(p)+3,.))
    u=ln(m+sum(p:*low))-kappa
    u=max((l+.01,min((r-.01,u))))
    for (iter=1;iter<=80;iter++) {
        q=cm_q_given_u(u,m,p,alpha,beta,low,high,omega)
        f=cm_F(q,u,alpha,beta,low,high,omega,kappa)
        fu=cm_Fu(q,u,alpha,beta,low,high,omega)
        if (f>=. | fu>=.) return(J(1,cols(p)+3,.))
        if (abs(f)<1e-11) break
        if (f>0) l=u
        else r=u
        candidate=u-f/fu
        if (candidate<=l | candidate>=r | fu>=0 | candidate>=.) {
            candidate=(l+r)/2
        }
        u=candidate
    }
    q=cm_q_given_u(u,m,p,alpha,beta,low,high,omega)
    if (iter>80 | hasmissing(q)) return(J(1,cols(p)+3,.))
    return((q,u,cm_F(q,u,alpha,beta,low,high,omega,kappa),
             cm_Fu(q,u,alpha,beta,low,high,omega)))
}

// Fixed-u Hicksian demand enumerates nested active sets in threshold order.
real rowvector cm_hicks(real scalar u, real rowvector p, real rowvector alpha,
                       real rowvector beta, real rowvector low, real rowvector high,
                       real scalar omega, real scalar kappa)
{
    real rowvector phi, a, active, q, ratio
    real colvector ix
    real scalar k, j, nu, lognu, target
    k=cols(p)
    phi=cm_phi(u,alpha,beta)
    a=cm_shift(u,low,high,omega)
    if (hasmissing((u,p,phi,a)) | min(p)<=0 | min(phi)<=0 | max(phi)>=. |
        min(a)<=0 | max(a)>=.) return(J(1,k+1,.))
    ratio=phi:/(p:*a)
    ix=order(ratio',-1)
    target=u+kappa
    for (j=1;j<=k;j++) {
        active=J(1,k,0)
        active[ix[|1\j|]']=J(1,j,1)
        lognu=(sum(active:*phi:*ln(phi:/p))+
                  sum((1:-active):*phi:*ln(a))-target)/sum(active:*phi)
        nu=exp(lognu)
        if (nu<=0 | nu>=.) continue
        if (all((ratio:>nu):==active)) {
            q=(phi:/(nu*p)-a):*active
            if (hasmissing(q) | min(q)<-1e-10) continue
            return((q,sum(p:*q)))
        }
    }
    return(J(1,k+1,.))
}

real rowvector cm_reweight(real rowvector weights, real rowvector epsilon,
                          real scalar sigma)
{
    real rowvector x
    x=ln(weights)+sigma*epsilon
    x=exp(x:-max(x))
    return(x:/sum(x))
}

real scalar cm_radical_inverse(real scalar n, real scalar base)
{
    real scalar f, r, iter
    if (n<0 | n>=. | base<2 | base>=.) _error(3300)
    f=1/base
    r=0
    for (iter=1;iter<=64 & n>0;iter++) {
        r=r+f*mod(n,base)
        n=floor(n/base)
        f=f/base
    }
    if (n>0) _error(3498)
    return(r)
}

real matrix cm_draws(real scalar n, real scalar k)
{
    real rowvector prime
    real matrix d
    real scalar i,j
    prime=(2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53)
    if (k>cols(prime)) _error(3300)
    d=J(n,k,.)
    for (i=1;i<=n;i++) for (j=1;j<=k;j++) {
        d[i,j]=invnormal(cm_radical_inverse(i+31,prime[j]))
    }
    return(d)
}

real matrix cm_random_demand(real scalar m, real rowvector p,
                             real rowvector alpha, real rowvector beta,
                             real rowvector low, real rowvector high,
                             real scalar omega, real scalar kappa,
                             real scalar sigma, real matrix draws)
{
    real scalar r
    real matrix out
    out=J(rows(draws),cols(p)+3,.)
    for (r=1;r<=rows(draws);r++) {
        out[r,]=cm_demand(m,p,cm_reweight(alpha,draws[r,],sigma),
            cm_reweight(beta,draws[r,],sigma),low,high,omega,kappa)
    }
    return(out)
}

// Exact maximum of F_u over a rectangular quantity domain at fixed u.
real scalar cm_Fu_boxmax(real scalar u, real rowvector qmax,
                        real rowvector alpha, real rowvector beta,
                        real rowvector low, real rowvector high, real scalar omega)
{
    real scalar s,t,i,z,ans,tc,value
    real rowvector a,phi,phid,ad
    s=cm_logistic(u)
    t=cm_logistic(omega*u)
    a=low*(1-t)+high*t
    phi=alpha*(1-s)+beta*s
    phid=(beta-alpha)*s*(1-s)
    ad=(high-low)*omega*t*(1-t)
    ans=-1
    for (i=1;i<=cols(qmax);i++) {
        z=max((phid[i]*ln(a[i])+phi[i]*ad[i]/a[i],
                phid[i]*ln(a[i]+qmax[i])+phi[i]*ad[i]/(a[i]+qmax[i])))
        if (phid[i]!=0) {
            tc=phi[i]*ad[i]/phid[i]
            if (tc>a[i] & tc<a[i]+qmax[i]) {
                value=phid[i]*ln(tc)+phi[i]*ad[i]/tc
                z=max((z,value))
            }
        }
        ans=ans+z
    }
    return(ans)
}

end
