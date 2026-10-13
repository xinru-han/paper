mata:
mata set matastrict on

real colvector mf_logistic(real colvector z)
{
    real colvector out,ix,ez
    out=J(rows(z),1,.)
    ix=selectindex((z:>=0):&(z:<.))
    if(length(ix)) out[ix]=1:/(1:+exp(-z[ix]))
    ix=selectindex(z:<0)
    if(length(ix)) {
        ez=exp(z[ix]);out[ix]=ez:/(1:+ez)
    }
    return(out)
}

real colvector mf_safe_roots(real matrix p, real colvector m, real matrix par,
    real scalar omega, real scalar kappa)
{
    real colvector u,ix,z,batch
    real scalar first,last,r
    u=J(rows(m),1,.)
    ix=selectindex((m:>rowmin((p*par[3,]',p*par[4,]'))):&(m:<.))
    for(first=1;first<=length(ix);first=first+1024) {
        last=min((first+1023,length(ix)))
        z=ix[|first\last|]
        batch=MD_roots(p[z,],m[z],par,omega,kappa)
        if(hasmissing(batch)) {
            for(r=1;r<=length(z);r++) batch[r]=MD_roots(p[z[r],],m[z[r]],par,omega,kappa)
        }
        u[z]=batch
    }
    return(u)
}

void mf_responses(real matrix par, real scalar omega, real scalar kappa,
    real matrix p, real colvector m, real matrix q, real matrix w,
    real matrix eta, real matrix om, real matrix oh, real colvector valid)
{
    real matrix phi,phiu,ga,gau,xu,tt
    real colvector u,s,t,lag,lag_t,Q,Qu,Eu,ix
    real scalar n,k,j,r
    n=rows(p); k=cols(p)
    q=w=eta=om=oh=J(n,k,.)
    valid=J(n,1,0)
    ix=selectindex((m:>rowmin((p*par[3,]',p*par[4,]'))):&(m:<.))
    if(!rows(ix)) return
    u=mf_safe_roots(p[ix,],m[ix],par,omega,kappa)
    if(min(par[1..2,])==0) {
        s=mf_logistic(u);lag=mf_logistic(-u)
        t=mf_logistic(omega:*u);lag_t=mf_logistic(-omega:*u)
        phi=lag*par[1,]+s*par[2,]
        phiu=(s:*lag)*(par[2,]-par[1,])
        ga=lag_t*par[3,]+t*par[4,]
        gau=(omega:*t:*lag_t)*(par[4,]-par[3,])
    }
    else {
        s=1:/(1:+exp(-u)); t=1:/(1:+exp(-omega:*u))
        phi=(1:-s)*par[1,]+s*par[2,]
        phiu=(s:*(1:-s))*(par[2,]-par[1,])
        ga=(1:-t)*par[3,]+t*par[4,]
        gau=(omega:*t:*(1:-t))*(par[4,]-par[3,])
    }
    Q=m[ix]-rowsum(p[ix,]:*ga)
    Qu=Q:*(1:-rowsum(phiu:*ln(phi:/p[ix,])))
    Eu=rowsum(p[ix,]:*gau)+Qu
    q[ix,]=ga+phi:*Q:/p[ix,]
    w[ix,]=p[ix,]:*q[ix,]:/m[ix]
    xu=gau+(phiu:*Q+phi:*Qu):/p[ix,]
    eta[ix,]=xu:/Eu:*m[ix]:/q[ix,]
    oh[ix,]=-phi:*(1:-phi):*Q:/p[ix,]:/q[ix,]
    om[ix,]=oh[ix,]-eta[ix,]:*w[ix,]
    valid[ix]=(Q:>0):&(Eu:/Q:>1e-7):&(rowmin(q[ix,]):>0):&(rowmax(q[ix,]):<.)
}

real colvector mf_grid_count(real matrix p, real colvector m, real matrix par,
    real scalar omega, real scalar kappa)
{
    real matrix unique_p,prev,cur,crit
    real colvector count,ord,mark,starts,group,ix,left,right,mid,leftslope,z,cv,nearprev,nearcur,nearcrit,critical_E
    real scalar step,it,n
    n=rows(p)
    if(!n) return(J(0,1,.))
    ord=order(p,1..cols(p))
    mark=J(n,1,1)
    if(n>1) mark[|2\n|]=rowsum(p[ord[|2\n|],]:!=p[ord[|1\n-1|],]):>0
    starts=selectindex(mark)
    group=J(n,1,.)
    group[ord]=runningsum(mark)
    unique_p=p[ord[starts],]
    count=J(rows(m),1,0)
    // Expenditure and its utility derivative depend on prices, not observed m.
    prev=MD_terms(J(rows(unique_p),1,-50),unique_p,par,omega,kappa)
    nearprev=abs((prev[group,1]-m):/m):<1e-13
    count=count:+nearprev
    for(step=-49.75;step<=50;step=step+.25) {
        cur=MD_terms(J(rows(unique_p),1,step),unique_p,par,omega,kappa)
        nearcur=abs((cur[group,1]-m):/m):<1e-13
        count=count:+((prev[group,1]-m):*(cur[group,1]-m):<0):*(!nearprev):*(!nearcur)
        count=count:+nearcur:*(!nearprev)
        ix=selectindex(prev[,2]:*cur[,2]:<0)
        if(length(ix)) {
            left=J(length(ix),1,step-.25); right=J(length(ix),1,step)
            leftslope=prev[ix,2]
            for(it=1;it<=36;it++) {
                mid=(left+right)/2
                crit=MD_terms(mid,unique_p[ix,],par,omega,kappa)
                z=selectindex(crit[,2]:*leftslope:>0)
                if(length(z)) left[z]=mid[z]
                z=selectindex(crit[,2]:*leftslope:<=0)
                if(length(z)) right[z]=mid[z]
            }
            critical_E=J(rows(unique_p),1,.)
            critical_E[ix]=crit[,1]
            ix=selectindex(critical_E[group,1]:<.)
            cv=critical_E[group[ix,1],1]-m[ix]
            nearcrit=abs(cv:/m[ix]):<1e-13
            count[ix]=count[ix]+((prev[group[ix],1]-m[ix]):*cv:<0):*(!nearprev[ix]):*(!nearcrit)+(cv:*(cur[group[ix],1]-m[ix]):<0):*(!nearcur[ix]):*(!nearcrit)-((prev[group[ix],1]-m[ix]):*(cur[group[ix],1]-m[ix]):<0):*(!nearprev[ix]):*(!nearcur[ix])
            count[ix]=count[ix]+nearcrit:*(!nearprev[ix]):*(!nearcur[ix])
        }
        prev=cur
        nearprev=nearcur
    }
    return(count)
}

void mf_store(real matrix par, real scalar omega, real scalar kappa)
{
    real matrix p,q,w,eta,om,oh,terms
    real colvector m,valid,count,u,ugap
    real scalar k,j,v
    string rowvector pn
    k=cols(par); pn="p":+strofreal(1..k)
    p=st_data(.,pn); m=st_data(.,"m_new")
    mf_responses(par,omega,kappa,p,m,q,w,eta,om,oh,valid)
    u=mf_safe_roots(p,m,par,omega,kappa)
    terms=MD_terms(u,p,par,omega,kappa)
    ugap=abs((terms[,1]-m):/m)
    count=mf_grid_count(p,m,par,omega,kappa)
    valid=valid:*(count:==1):*(ugap:<1e-10)
    for(j=1;j<=k;j++) {
        v=st_addvar("double","fitq"+strofreal(j)); st_store(.,v,q[,j])
        v=st_addvar("double","fitw"+strofreal(j)); st_store(.,v,w[,j])
        v=st_addvar("double","eta"+strofreal(j)); st_store(.,v,eta[,j])
        v=st_addvar("double","own_m"+strofreal(j)); st_store(.,v,om[,j])
        v=st_addvar("double","own_h"+strofreal(j)); st_store(.,v,oh[,j])
    }
    v=st_addvar("byte","prediction_valid"); st_store(.,v,valid)
    v=st_addvar("int","utility_roots_finite_grid"); st_store(.,v,count)
    v=st_addvar("double","utility_equation_error"); st_store(.,v,ugap)
}
end
