version 17
mata:
mata clear
mata set matalnum off
mata set mataoptimize on
MD_P=MD_W=MD_H=MD_QFIT=MD_WFIT=MD_ETA=J(0,0,.)
MD_M=MD_WEIGHT=MD_U=J(0,1,.)
MD_SCALE=MD_BEST=MD_LO=MD_HI=J(1,0,.)
MD_K=MD_N=MD_MAI=MD_BESTVAL=MD_BESTSCORE=MD_OK=.
MD_CBASE=MD_CFREE=MD_CLOG=J(1,0,.)
MS_AIDX=MS_BIDX=J(1,0,.)
MD_CAPTURE=0
MD_JAC=J(0,0,.)

void MD_opt_eval(real scalar todo, real rowvector x, real scalar value, real rowvector gradient, real matrix Hessian)
{
    external real rowvector MD_CBASE,MD_CFREE,MD_CLOG,MS_AIDX,MS_BIDX
    external real scalar MD_K
    real rowvector raw,g,a,b,ga,gb
    real scalar j,na,nb,pos
    raw=MD_CBASE
    if(max(abs(x))>50) {
        value=1e10+sum(x:^2)
        gradient=2*x
        return
    }
    na=length(MS_AIDX);nb=length(MS_BIDX);pos=na+nb-2
    a=b=J(1,MD_K,0)
    a[MS_AIDX]=MD_softmax(na>1 ? x[1..na-1] : J(1,0,.))
    b[MS_BIDX]=MD_softmax(nb>1 ? x[na..pos] : J(1,0,.))
    raw[1..MD_K-1]=a[1..MD_K-1];raw[MD_K..2*MD_K-2]=b[1..MD_K-1]
    for(j=1;j<=length(MD_CFREE);j++) raw[MD_CFREE[j]]=MD_CLOG[j] ? exp(x[pos+j]) : x[pos+j]
    MD_eval(raw,value,g)
    ga=(g[1..MD_K-1],0);gb=(g[MD_K..2*MD_K-2],0)
    gradient=J(1,cols(x),0)
    for(j=1;j<na;j++) gradient[j]=a[MS_AIDX[j]]*(ga[MS_AIDX[j]]-sum(a:*ga))
    for(j=1;j<nb;j++) gradient[na-1+j]=b[MS_BIDX[j]]*(gb[MS_BIDX[j]]-sum(b:*gb))
    for(j=1;j<=length(MD_CFREE);j++) gradient[pos+j]=g[MD_CFREE[j]]*(MD_CLOG[j] ? raw[MD_CFREE[j]] : 1)
    if(value>=1e9) {
        value=value+sum(x:^2)
        gradient=2*x
    }
}

void MD_polish(real rowvector b, real scalar maxiter, real scalar f, real rowvector g, real scalar iterations)
{
    external real rowvector MD_CBASE,MD_CFREE,MD_CLOG,MD_LO,MD_HI,MS_AIDX,MS_BIDX
    external real scalar MD_K,MD_MAI
    transmorphic O
    real rowvector x,ans,newg,a,beta
    real scalar j,L,rc,logthis,newf,na,nb,pos
    L=cols(b);MD_CBASE=b;MD_CFREE=MD_CLOG=x=J(1,0,.)
    MD_eval(b,f,g)
    a=MD_natural(b[1..MD_K-1]);beta=MD_natural(b[MD_K..2*MD_K-2])
    MS_AIDX=selectindex(a:>1e-12);MS_BIDX=selectindex(beta:>1e-12)
    na=length(MS_AIDX);nb=length(MS_BIDX);pos=na+nb-2
    if(na>1) x=(x,ln(a[MS_AIDX[1..na-1]]:/a[MS_AIDX[na]]))
    if(nb>1) x=(x,ln(beta[MS_BIDX[1..nb-1]]:/beta[MS_BIDX[nb]]))
    for(j=2*MD_K-1;j<=L;j++) {
        logthis=(j>=2*MD_K-1 & j<L)
        if(logthis & b[j]<=1e-8 & g[j]>0) continue
        MD_CFREE=(MD_CFREE,j);MD_CLOG=(MD_CLOG,logthis)
        x=(x,(logthis ? ln(max((1e-6,b[j]))) : b[j]))
    }
    O=optimize_init()
    optimize_init_evaluator(O,&MD_opt_eval())
    optimize_init_evaluatortype(O,"d1")
    optimize_init_which(O,"min")
    optimize_init_params(O,x)
    optimize_init_technique(O,"bfgs")
    optimize_init_conv_maxiter(O,maxiter)
    optimize_init_conv_ptol(O,1e-10)
    optimize_init_conv_vtol(O,1e-12)
    optimize_init_conv_nrtol(O,1e-8)
    optimize_init_tracelevel(O,"none")
    rc=_optimize(O)
    ans=optimize_result_params(O)
    a=beta=J(1,MD_K,0)
    a[MS_AIDX]=MD_softmax(na>1 ? ans[1..na-1] : J(1,0,.))
    beta[MS_BIDX]=MD_softmax(nb>1 ? ans[na..pos] : J(1,0,.))
    MD_CBASE[1..MD_K-1]=a[1..MD_K-1];MD_CBASE[MD_K..2*MD_K-2]=beta[1..MD_K-1]
    for(j=1;j<=length(MD_CFREE);j++) MD_CBASE[MD_CFREE[j]]=MD_CLOG[j] ? exp(ans[pos+j]) : ans[pos+j]
    MD_CBASE=MD_project(MD_CBASE)
    MD_eval(MD_CBASE,newf,newg)
    if(newf<f) {
        b=MD_CBASE
        f=newf
        g=newg
    }
    iterations=optimize_result_iterations(O)
    printf("  Active-face BFGS polish rc=%g iterations=%g natural_KKT=%9.4g\n",rc,iterations,MD_scorenorm(b,g))
}

void MD_preference_start(real rowvector b, real scalar maxiter)
{
    external real rowvector MD_LO,MD_HI
    external real scalar MD_K
    real rowvector lo,hi,g,out
    real scalar j,L,f,it,ok
    lo=MD_LO;hi=MD_HI;L=cols(b)
    for(j=2*MD_K-1;j<L;j++) MD_LO[j]=MD_HI[j]=b[j]
    MD_solver(b,min((100,maxiter)),out,f,g,it,ok)
    b=out;MD_LO=lo;MD_HI=hi
}

real matrix MD_sigmoid(real matrix x)
{
    real colvector z,v,idx,ez
    z=vec(x);v=J(rows(z),1,.)
    idx=selectindex(z:>=0)
    if(length(idx)) v[idx]=1:/(1:+exp(-z[idx]))
    idx=selectindex(z:<0)
    if(length(idx)) {
        ez=exp(z[idx]);v[idx]=ez:/(1:+ez)
    }
    return(colshape(v,cols(x)))
}

real rowvector MD_softmax(real rowvector x)
{
    real rowvector z
    z=(x,0)
    z=exp(z:-max(z))
    return(z:/sum(z))
}

real rowvector MD_natural(real rowvector x)
{
    real rowvector z
    z=(x,1-sum(x))
    if(abs(z[cols(z)])<1e-14) z[cols(z)]=0
    return(z)
}

real rowvector MS_project_simplex(real rowvector x)
{
    real colvector sorted
    real scalar j,theta,sumx,rho
    if(min(x)>=0 & abs(sum(x)-1)<1e-14) return(x:/sum(x))
    sorted=sort(x',-1);sumx=0;rho=1
    for(j=1;j<=rows(sorted);j++) {
        sumx=sumx+sorted[j]
        if(sorted[j]-(sumx-1)/j>0) rho=j
    }
    theta=(sum(sorted[1..rho])-1)/rho
    return(colmax((J(1,cols(x),0)\(x:-theta))))
}

void MS_refine_natural(real rowvector b, real scalar f, real rowvector g, real scalar iterations)
{
    external real matrix MD_P,MD_W,MD_H,MD_JAC
    external real colvector MD_M,MD_WEIGHT
    external real scalar MD_K,MD_MAI,MD_CAPTURE
    real matrix T,q,w,eta,ownm,ownh,R,V,C,Jwhite,Jface,Hgn
    real colvector u
    real rowvector direction,trial,newg
    real scalar j,rate,ls,newf,oldscore,attempt
    iterations=0
    for(attempt=1;attempt<=8;attempt++) {
        oldscore=MD_scorenorm(b,g)
        if(oldscore<1e-5) break
        MD_CAPTURE=1;MD_eval(b,f,g);MD_CAPTURE=0
        T=MS_facebasis(b)
        if(!cols(T)) break
        MD_predict(b,MD_MAI,MD_P,MD_M,q,w,u,eta,ownm,ownh)
        R=(MD_W-w)*MD_H
        V=quadcross(R,MD_WEIGHT,R)
        // This profile-QML metric whitens residuals, not Slutsky curvature.
        C=cholesky(invsym(V))
        Jface=MD_JAC*T;Jwhite=J(rows(Jface),cols(Jface),.)
        for(j=1;j<=cols(Jface);j++) Jwhite[,j]=vec(colshape(Jface[,j],MD_K-1)*C)
        Hgn=quadcross(Jwhite,Jwhite)
        direction=(-g*T*invsym(Hgn))*T'
        if(hasmissing(direction) | sum(g:*direction)>=0) break
        rate=MS_probe_step(b,direction,1)
        for(ls=1;ls<=15;ls++) {
            trial=b+rate*direction
            MD_eval(trial,newf,newg)
            if(newf<1e9 & newf<=f+1e-12 & MD_scorenorm(trial,newg)<oldscore) break
            rate=rate/2
        }
        if(ls>15) break
        b=trial;f=newf;g=newg
        iterations=iterations+1
    }
    printf("  Natural-face score refinement accepted_steps=%g KKT=%9.4g\n",iterations,MD_scorenorm(b,g))
}

void MD_load(string scalar mv, string scalar pv, string scalar wv, string scalar weight)
{
    external real matrix MD_P,MD_W,MD_H
    external real colvector MD_M,MD_WEIGHT
    external real rowvector MD_SCALE
    external real scalar MD_K,MD_N
    real scalar j
    MD_P=st_data(.,tokens(pv)); MD_W=st_data(.,tokens(wv)); MD_M=st_data(.,mv)
    MD_N=rows(MD_P); MD_K=cols(MD_P)
    if(MD_N==0) _error(3498)
    MD_WEIGHT=weight=="" ? J(MD_N,1,1) : st_data(.,weight)
    if(hasmissing(MD_WEIGHT) | min(MD_WEIGHT)<=0 | sum(MD_WEIGHT)<=0) _error(3498)
    MD_WEIGHT=MD_WEIGHT:/sum(MD_WEIGHT)
    if (hasmissing(MD_P) | hasmissing(MD_W) | hasmissing(MD_M) | min(MD_P)<=0 | min(MD_M)<=0 | min(MD_W)<0 | max(abs(rowsum(MD_W):-1))>1e-7) _error(3498)
    MD_SCALE=colsum((MD_M*J(1,MD_K,1)):*MD_W:/MD_P):/MD_N
    if(min(MD_SCALE)<=0 | hasmissing(MD_SCALE)) {
        errprintf("Each modeled food must have positive expenditure in at least one retained cell.\n")
        _error(3498)
    }
    MD_H=J(MD_K,MD_K-1,0)
    for(j=1;j<MD_K;j++) {
        MD_H[1..j,j]=J(j,1,1/sqrt(j*(j+1)))
        MD_H[j+1,j]=-j/sqrt(j*(j+1))
    }
}

real matrix MD_unpack(real rowvector raw, real scalar mai)
{
    external real scalar MD_K
    external real rowvector MD_SCALE
    real scalar k
    real rowvector a,b,d,t
    k=MD_K
    a=MD_natural(raw[1..k-1]); b=MD_natural(raw[k..2*k-2])
    d=raw[2*k-1..3*k-2]:*MD_SCALE
    t=mai ? raw[3*k-1..4*k-2]:*MD_SCALE : d
    return(a\b\d\t)
}

real matrix MD_terms(real colvector u, real matrix p, real matrix par, real scalar omega, real scalar kappa)
{
    real colvector s,lag,t,tlag,Q,Eu
    real matrix phi,phiu,gamma,gammau
    if(rows(par)!=4 | cols(par)!=cols(p) | min(par[1..2,])<0 | min(par[1,]+par[2,])<=0) {
        errprintf("Both endpoint marginal shares cannot be zero for a modeled food.\n")
        _error(3498)
    }
    s=MD_sigmoid(u);lag=MD_sigmoid(-u)
    t=MD_sigmoid(omega:*u);tlag=MD_sigmoid(-omega:*u)
    phi=lag*par[1,]+s*par[2,]
    phiu=(s:*lag)*(par[2,]-par[1,])
    gamma=tlag*par[3,]+t*par[4,]
    gammau=(omega:*t:*tlag)*(par[4,]-par[3,])
    Q=exp(u:+kappa:-rowsum(phi:*ln(phi:/p)))
    Eu=rowsum(p:*gammau)+Q:*(1:-rowsum(phiu:*ln(phi:/p)))
    return((rowsum(p:*gamma)+Q),Eu,Q,s,t)
}

real colvector MD_roots(real matrix p, real colvector m, real matrix par, real scalar omega, real scalar kappa)
{
    real colvector lo,hi,u,f,eu,proposal,scanlast,idx,cd,ct,mm,z,active,bad,indices
    real rowvector phiavg
    real matrix tt,previous,current,pp
    real scalar n,it,v
    n=rows(p); lo=J(n,1,-50);hi=J(n,1,50)
    cd=p*par[3,]';ct=p*par[4,]'
    if(any(m:<=rowmin((cd,ct)))) return(J(n,1,.))
    previous=MD_terms(lo,p,par,omega,kappa)
    if(any(previous[,1]:>=m)) {
        idx=selectindex(previous[,1]:>=m)
        pp=p[idx,];mm=m[idx];previous=previous[idx,]
        scanlast=J(rows(idx),1,.)
        for(v=-49;v<=50;v++) {
            current=MD_terms(J(rows(idx),1,v),pp,par,omega,kappa)
            z=selectindex(previous[,1]:<=mm :& current[,1]:>=mm)
            if(length(z)) scanlast[z]=J(length(z),1,v-1)
            previous=current
        }
        if(hasmissing(scanlast)) return(J(n,1,.))
        lo[idx]=scanlast;hi[idx]=scanlast:+1
    }
    phiavg=(par[1,]+par[2,]):/2
    u=ln(m)
    u=u:+sum(phiavg:*ln(phiavg))
    u=u:-kappa
    u=u-ln(p)*phiavg'
    z=selectindex(u:<=lo :| u:>=hi)
    if(length(z)) u[z]=(lo[z]+hi[z]):/2
    active=(1..n)'
    for(it=1;it<=80;it++) {
        tt=MD_terms(u[active],p[active,],par,omega,kappa)
        f=tt[,1]-m[active];eu=tt[,2]
        bad=selectindex(abs(f:/m[active]):>=1e-14)
        if(!length(bad)) break
        indices=active[bad];f=f[bad];eu=eu[bad]
        z=selectindex(f:<0)
        if(length(z)) lo[indices[z]]=u[indices[z]]
        z=selectindex(f:>=0)
        if(length(z)) hi[indices[z]]=u[indices[z]]
        proposal=u[indices]-f:/eu
        z=selectindex(proposal:<=lo[indices] :| proposal:>=hi[indices] :| eu:<=0 :| missing(proposal))
        if(length(z)) proposal[z]=(lo[indices[z]]+hi[indices[z]]):/2
        u[indices]=proposal
        active=indices
    }
    tt=MD_terms(u,p,par,omega,kappa)
    if(max(abs((tt[,1]-m):/m))>1e-10) return(J(n,1,.))
    return(u)
}

void MD_eval(real rowvector raw, real scalar value, real rowvector gradient)
{
    external real matrix MD_P,MD_W,MD_H
    external real colvector MD_M,MD_WEIGHT
    external real rowvector MD_SCALE
    external real scalar MD_K,MD_N,MD_MAI,MD_CAPTURE
    external real matrix MD_JAC
    real scalar k,L,j,omega,kappa,ld
    real matrix par,phi,phiu,gamma,gammau,qfit,wfit,R,V,Vinv,G,xu,dphi,dgamma,dq,Da,Db
    real colvector u,s,lag,t,tlag,Q,Qu,Eu,dQ,dE,domega
    real rowvector direction
    k=MD_K;L=cols(raw);gradient=J(1,L,0);value=1e10
    par=MD_unpack(raw,MD_MAI);omega=MD_MAI ? raw[L-1] : 0;kappa=raw[L]
    if(min(par[1..2,])<0 | min(par[1,]+par[2,])<=0 | abs(sum(par[1,])-1)>1e-10 | abs(sum(par[2,])-1)>1e-10) return
    u=MD_roots(MD_P,MD_M,par,omega,kappa)
    if(hasmissing(u)) return
    s=MD_sigmoid(u);lag=MD_sigmoid(-u)
    t=MD_sigmoid(omega:*u);tlag=MD_sigmoid(-omega:*u)
    phi=lag*par[1,]+s*par[2,];phiu=(s:*lag)*(par[2,]-par[1,])
    gamma=tlag*par[3,]+t*par[4,];gammau=(omega:*t:*tlag)*(par[4,]-par[3,])
    Q=exp(u:+kappa:-rowsum(phi:*ln(phi:/MD_P)))
    Qu=Q:*(1:-rowsum(phiu:*ln(phi:/MD_P)))
    Eu=rowsum(MD_P:*gammau)+Qu
    if(min(Q)<=0 | min(Eu:/Q)<=1e-7) return
    qfit=gamma+phi:*(Q*J(1,k,1)):/MD_P
    wfit=MD_P:*qfit:/(MD_M*J(1,k,1))
    R=(MD_W-wfit)*MD_H
    V=quadcross(R,MD_WEIGHT,R)
    ld=ln(det(V))
    if(missing(ld) | det(V)<=0) return
    Vinv=invsym(V)
    value=.5*((k-1)*(1+ln(2*pi()))+ld)
    G=-(R*Vinv*MD_H'):*(MD_WEIGHT*J(1,k,1))
    xu=gammau+(phiu:*(Q*J(1,k,1))+phi:*(Qu*J(1,k,1))):/MD_P
    Da=Db=(I(k-1)\J(1,k-1,-1))
    if(MD_CAPTURE) MD_JAC=J(MD_N*(k-1),L,.)
    for(j=1;j<=L;j++) {
        dphi=J(MD_N,k,0);dgamma=J(MD_N,k,0);dQ=J(MD_N,1,0)
        if(j<=k-1) dphi=lag*Da[,j]'
        else if(j<=2*k-2) dphi=s*Db[,j-k+1]'
        else if(j<=3*k-2) {
            if(MD_MAI) dgamma[,j-2*k+2]=tlag:*MD_SCALE[j-2*k+2]
            else dgamma[,j-2*k+2]=J(MD_N,1,MD_SCALE[j-2*k+2])
        }
        else if(MD_MAI & j<=4*k-2) dgamma[,j-3*k+2]=t:*MD_SCALE[j-3*k+2]
        else if(MD_MAI & j==L-1) dgamma=(u:*t:*tlag)*(par[4,]-par[3,])
        if(j==L) dQ=Q
        else dQ=-Q:*rowsum(dphi:*ln(phi:/MD_P))
        dE=rowsum(MD_P:*dgamma)+dQ
        dq=dgamma+(dphi:*(Q*J(1,k,1))+phi:*(dQ*J(1,k,1))):/MD_P-xu:*((dE:/Eu)*J(1,k,1))
        gradient[j]=sum(G:*(MD_P:*dq:/(MD_M*J(1,k,1))))
        if(MD_CAPTURE) MD_JAC[,j]=vec(((MD_P:*dq:/(MD_M*J(1,k,1)))*MD_H):*(sqrt(MD_WEIGHT)*J(1,k-1,1)))
    }
}

real rowvector MD_project(real rowvector b)
{
    external real rowvector MD_LO,MD_HI
    external real scalar MD_K
    real rowvector a,beta,out
    out=colmin((MD_HI\colmax((MD_LO\b))))
    a=MS_project_simplex(MD_natural(b[1..MD_K-1]))
    beta=MS_project_simplex(MD_natural(b[MD_K..2*MD_K-2]))
    out[1..MD_K-1]=a[1..MD_K-1];out[MD_K..2*MD_K-2]=beta[1..MD_K-1]
    return(out)
}

real rowvector MD_score(real rowvector b, real rowvector g)
{
    external real rowvector MD_LO,MD_HI
    external real scalar MD_K
    real rowvector pg,a,beta,ga,gb
    real scalar j
    pg=g
    a=MD_natural(b[1..MD_K-1]);beta=MD_natural(b[MD_K..2*MD_K-2])
    ga=(g[1..MD_K-1],0);gb=(g[MD_K..2*MD_K-2],0)
    a=a-MS_project_simplex(a-ga);beta=beta-MS_project_simplex(beta-gb)
    pg[1..MD_K-1]=a[1..MD_K-1];pg[MD_K..2*MD_K-2]=beta[1..MD_K-1]
    for(j=2*MD_K-1;j<=cols(b);j++) pg[j]=b[j]-min((MD_HI[j],max((MD_LO[j],b[j]-g[j]))))
    return(pg)
}

real scalar MD_scorenorm(real rowvector b,real rowvector g)
{
    external real scalar MD_K
    real rowvector pg
    pg=MD_score(b,g)
    return(max((max(abs(pg)),abs(sum(pg[1..MD_K-1])),abs(sum(pg[MD_K..2*MD_K-2])))))
}

void MD_solver(real rowvector initial, real scalar maxiter, real rowvector b, real scalar f, real rowvector g, real scalar iterations, real scalar ok)
{
    real matrix H,I
    real rowvector pg,d,trial,newg,step,y
    real scalar L,ls,rate,newf,sy
    b=MD_project(initial);MD_eval(b,f,g);L=cols(b);H=I(L);I=I(L);ok=0
    for(iterations=1;iterations<=maxiter;iterations++) {
        pg=MD_score(b,g)
        if(MD_scorenorm(b,g)<1e-5) {
            ok=1
            break
        }
        d=-pg*H
        for(ls=1;ls<=L;ls++) if(pg[ls]==0) d[ls]=0
        if(sum(d:*g)>=-1e-12) {
            H=I
            d=-pg
        }
        if(max(abs(d))>3) d=d:/max(abs(d)):*3
        rate=1
        for(ls=1;ls<=30;ls++) {
            trial=MD_project(b+rate*d);step=trial-b
            MD_eval(trial,newf,newg)
            if(newf<1e9 & newf<=f+1e-4*sum(g:*step)) break
            rate=rate/2
        }
        if(ls>30) {
            H=I
            if(MD_scorenorm(b,g)<1e-4) ok=1
            break
        }
        y=newg-g;sy=sum(step:*y)
        if(sy>1e-10*sqrt(sum(step:^2)*sum(y:^2))) H=(I-step'*y:/sy)*H*(I-y'*step:/sy)+step'*step:/sy
        else H=I
        b=trial;f=newf;g=newg
        if(mod(iterations,50)==0) printf("  iteration %g mean_nll %12.8f natural_KKT %9.4g\n",iterations,f,MD_scorenorm(b,g))
    }
}

void MD_predict(real rowvector raw, real scalar mai, real matrix p, real colvector m, real matrix q, real matrix w, real colvector u, real matrix eta, real matrix ownM, real matrix ownH)
{
    real matrix par,phi,phiu,gamma,gammau,xu
    real colvector s,lag,t,tlag,Q,Qu,Eu
    real scalar k,L,omega,kappa,j
    k=cols(p);L=cols(raw);par=MD_unpack(raw,mai);omega=mai ? raw[L-1] : 0;kappa=raw[L]
    if(min(par[1..2,])<0 | min(par[1,]+par[2,])<=0) {
        errprintf("Each modeled food requires support at at least one marginal-share endpoint.\n")
        _error(3498)
    }
    u=MD_roots(p,m,par,omega,kappa)
    s=MD_sigmoid(u);lag=MD_sigmoid(-u)
    t=MD_sigmoid(omega:*u);tlag=MD_sigmoid(-omega:*u)
    phi=lag*par[1,]+s*par[2,];phiu=(s:*lag)*(par[2,]-par[1,])
    gamma=tlag*par[3,]+t*par[4,];gammau=(omega:*t:*tlag)*(par[4,]-par[3,])
    Q=exp(u:+kappa:-rowsum(phi:*ln(phi:/p)));Qu=Q:*(1:-rowsum(phiu:*ln(phi:/p)));Eu=rowsum(p:*gammau)+Qu
    q=gamma+phi:*(Q*J(1,k,1)):/p;w=p:*q:/(m*J(1,k,1))
    xu=gammau+(phiu:*(Q*J(1,k,1))+phi:*(Qu*J(1,k,1))):/p
    eta=(xu:/(Eu*J(1,k,1))):*(m*J(1,k,1)):/q
    ownH=-phi:*(1:-phi):*(Q*J(1,k,1)):/p:/q
    ownM=ownH-eta:*w
}

void MD_csv(string scalar path, string scalar header, real matrix x)
{
    real scalar fh,i,j
    string scalar line
    unlink(path)
    fh=fopen(path,"w");fput(fh,header)
    for(i=1;i<=rows(x);i++) {
        line=""
        for(j=1;j<=cols(x);j++) line=line+(j>1 ? "," : "")+strofreal(x[i,j],"%21.14g")
        fput(fh,line)
    }
    fclose(fh)
}

real matrix MS_facebasis(real rowvector raw)
{
    external real scalar MD_K
    external real rowvector MD_LO,MD_HI
    real matrix T
    real rowvector a,idx,d
    real scalar block,j,i,anchor,L
    L=cols(raw);T=J(L,0,.)
    for(block=0;block<=1;block++) {
        a=MD_natural(raw[(block*(MD_K-1)+1)..((block+1)*(MD_K-1))])
        idx=selectindex(a:>0);anchor=idx[length(idx)]
        for(j=1;j<length(idx);j++) {
            d=J(1,L,0);i=idx[j]
            if(i<MD_K) d[block*(MD_K-1)+i]=1
            if(anchor<MD_K) d[block*(MD_K-1)+anchor]=-1
            T=(T,d')
        }
    }
    for(j=2*MD_K-1;j<=L;j++) if(raw[j]>MD_LO[j]+1e-8 & raw[j]<MD_HI[j]-1e-8) {
        d=J(1,L,0);d[j]=1;T=(T,d')
    }
    return(T)
}

real scalar MS_probe_step(real rowvector raw,real rowvector direction,real scalar requested)
{
    external real scalar MD_K
    external real rowvector MD_LO,MD_HI
    real rowvector a,da
    real scalar h,block,j
    h=requested
    for(block=0;block<=1;block++) {
        a=MD_natural(raw[(block*(MD_K-1)+1)..((block+1)*(MD_K-1))])
        da=(direction[(block*(MD_K-1)+1)..((block+1)*(MD_K-1))],-sum(direction[(block*(MD_K-1)+1)..((block+1)*(MD_K-1))]))
        for(j=1;j<=MD_K;j++) if(abs(da[j])>0) h=min((h,.2*a[j]/abs(da[j])))
    }
    for(j=2*MD_K-1;j<=cols(raw);j++) if(direction[j]!=0) h=min((h,.2*min((raw[j]-MD_LO[j],MD_HI[j]-raw[j]))/abs(direction[j])))
    return(h)
}

void MD_audit(string scalar out, real rowvector raw, real matrix par, real scalar mai)
{
    external real matrix MD_P,MD_W,MD_H,MD_QFIT,MD_WFIT,MD_ETA
    external real colvector MD_M,MD_U
    external real scalar MD_K,MD_N,MD_OK,MD_CAPTURE
    external real matrix MD_JAC
    external real rowvector MD_LO,MD_HI
    real matrix q,w,eta,hm,hh,par0,cur,prev,roots,slopes,M,H,S,eigvec,g,dq,w0,e0,h0
    real colvector u,pavg,sign0,ct,down,euval,ur,m0,sorted,singular,cidx,clo,chi,cmid,cvalue,leftslope,zcrit,prevzero,curzero,zeroplateau,critzero
    real matrix critterms,T
    real rowvector pbar,mbar,qr,wr,er,om,oh,eigenvals,phi0,pp
    real matrix rowsout,summary
    real scalar L,omega,kappa,v,j,l,h,f,fdmax,fh,unique,negcount,rootgap,addgap,homgap,symgap,eigmax,step,Q0,rankj,condj,fullrank,fullcondition,utilitygap,minbranch,refinements,itercrit,fp,fm,parameter_gradient_gap,inadmissible_probes,onesidedgap,onesidedcount,block,anchor,unsupported
    real rowvector freeidx,score,probe,probegradient,direction,a,idx
    string scalar line
    L=cols(raw);omega=mai ? raw[L-1] : 0;kappa=raw[L]
    MD_predict(raw,mai,MD_P,MD_M,q,w,u,eta,hm,hh)
    MD_QFIT=q;MD_WFIT=w;MD_U=u;MD_ETA=eta
    prev=MD_terms(J(MD_N,1,-50),MD_P,par,omega,kappa);refinements=0
    prevzero=abs((prev[,1]-MD_M):/MD_M):<1e-13
    roots=prevzero;zeroplateau=J(MD_N,1,0)
    for(v=-49.75;v<=50;v=v+.25) {
        cur=MD_terms(J(MD_N,1,v),MD_P,par,omega,kappa)
        curzero=abs((cur[,1]-MD_M):/MD_M):<1e-13
        roots=roots:+((prev[,1]-MD_M):*(cur[,1]-MD_M):<0):*(!prevzero):*(!curzero):+(curzero:*(!prevzero))
        zeroplateau=zeroplateau:|(prevzero:*curzero)
        cidx=selectindex(prev[,2]:*cur[,2]:<0)
        if(length(cidx)) {
            refinements=refinements+length(cidx)
            clo=J(length(cidx),1,v-.25);chi=J(length(cidx),1,v)
            leftslope=prev[cidx,2]
            for(itercrit=1;itercrit<=36;itercrit++) {
                cmid=(clo+chi):/2
                critterms=MD_terms(cmid,MD_P[cidx,],par,omega,kappa)
                zcrit=selectindex(critterms[,2]:*leftslope:>0)
                if(length(zcrit)) clo[zcrit]=cmid[zcrit]
                zcrit=selectindex(critterms[,2]:*leftslope:<=0)
                if(length(zcrit)) chi[zcrit]=cmid[zcrit]
            }
            cvalue=critterms[,1]-MD_M[cidx]
            critzero=abs(cvalue:/MD_M[cidx]):<1e-13
            roots[cidx]=roots[cidx]+((prev[cidx,1]-MD_M[cidx]):*cvalue:<0):*(!prevzero[cidx]):*(!critzero)+(cvalue:*(cur[cidx,1]-MD_M[cidx]):<0):*(!curzero[cidx]):*(!critzero)-((prev[cidx,1]-MD_M[cidx]):*(cur[cidx,1]-MD_M[cidx]):<0):*(!prevzero[cidx]):*(!curzero[cidx])+critzero:*(!prevzero[cidx]):*(!curzero[cidx])
        }
        prev=cur
        prevzero=curzero
    }
    unique=sum(roots:==1);rootgap=max(abs(rowsum(MD_P:*q):-MD_M):/MD_M);addgap=max(abs(rowsum(w):-1))
    cur=MD_terms(u,MD_P,par,omega,kappa)
    utilitygap=max(abs((cur[,1]-MD_M):/MD_M))
    minbranch=min(cur[,2]:/cur[,3])
    if(unique<MD_N | rootgap>1e-8 | addgap>1e-8 | sum(zeroplateau)>0) MD_OK=0
    MD_CAPTURE=1
    MD_eval(raw,f,score)
    MD_CAPTURE=0
    T=MS_facebasis(raw)
    singular=svdsv(MD_JAC)
    fullrank=sum(singular:>max(singular)*1e-6)
    fullcondition=max(singular)/min(singular)
    singular=svdsv(MD_JAC*T)
    rankj=sum(singular:>max(singular)*1e-6)
    condj=max(singular)/min(singular)
    parameter_gradient_gap=0;inadmissible_probes=0
    for(j=1;j<=cols(T);j++) {
        direction=T[,j]';h=MS_probe_step(raw,direction,1e-6)
        probe=raw+h*direction;MD_eval(probe,fp,probegradient)
        probe=raw-h*direction;MD_eval(probe,fm,probegradient)
        if(h>0 & fp<1e9 & fm<1e9) parameter_gradient_gap=max((parameter_gradient_gap,abs((fp-fm)/(2*h)-sum(score:*direction))))
        else inadmissible_probes=inadmissible_probes+1
    }
    onesidedgap=0;onesidedcount=0
    for(block=0;block<=1;block++) {
        a=MD_natural(raw[(block*(MD_K-1)+1)..((block+1)*(MD_K-1))])
        idx=selectindex(a:>0);anchor=idx[1]
        for(j=1;j<=MD_K;j++) if(a[j]==0) {
            direction=J(1,L,0)
            if(j<MD_K) direction[block*(MD_K-1)+j]=1
            if(anchor<MD_K) direction[block*(MD_K-1)+anchor]=-1
            h=min((1e-7,.1*a[anchor]));onesidedcount=onesidedcount+1
            probe=raw+h*direction;MD_eval(probe,fp,probegradient)
            probe=raw+2*h*direction;MD_eval(probe,fm,probegradient)
            if(fp<1e9 & fm<1e9) onesidedgap=max((onesidedgap,abs((-3*f+4*fp-fm)/(2*h)-sum(score:*direction))))
            else inadmissible_probes=inadmissible_probes+1
        }
    }
    for(j=2*MD_K-1;j<=L;j++) if(raw[j]<=MD_LO[j]+1e-12) {
        direction=J(1,L,0);direction[j]=1;h=1e-7;onesidedcount=onesidedcount+1
        probe=raw+h*direction;MD_eval(probe,fp,probegradient)
        probe=raw+2*h*direction;MD_eval(probe,fm,probegradient)
        if(fp<1e9 & fm<1e9) onesidedgap=max((onesidedgap,abs((-3*f+4*fp-fm)/(2*h)-score[j])))
        else inadmissible_probes=inadmissible_probes+1
    }
    pbar=exp(colsum(ln(MD_P)):/MD_N);mbar=mean(MD_M)
    MD_predict(raw,mai,pbar,mbar,qr,wr,ur,er,om,oh)
    par0=MD_unpack(raw,mai)
    phi0=MD_sigmoid(-ur)*par0[1,]+MD_sigmoid(ur)*par0[2,]
    Q0=exp(ur+kappa-sum(phi0:*ln(phi0:/pbar)))
    H=J(MD_K,MD_K,.);M=H;S=H
    for(j=1;j<=MD_K;j++) for(l=1;l<=MD_K;l++) {
        S[j,l]=Q0*phi0[j]*phi0[l]/(pbar[j]*pbar[l])-(j==l ? Q0*phi0[j]/pbar[j]^2 : 0)
        H[j,l]=S[j,l]*pbar[l]/qr[j]
        M[j,l]=H[j,l]-er[j]*wr[l]
    }
    symeigensystem((S+S')/2,eigvec,eigenvals);eigmax=max(eigenvals)
    symgap=max(abs(S-S'));homgap=max(abs(rowsum(M):+er'))
    fdmax=0;step=1e-5
    MD_predict(raw,mai,pbar,mbar*exp(step),dq,w0,m0,e0,h0,g)
    fdmax=max(abs((ln(dq):-ln(qr)):/step-er))
    for(l=1;l<=MD_K;l++) {
        pp=pbar;pp[l]=pp[l]*exp(step)
        MD_predict(raw,mai,pp,mbar,dq,w0,m0,e0,h0,g)
        fdmax=max((fdmax,max(abs((ln(dq):-ln(qr)):/step-M[,l]'))))
    }
    MD_csv(out+"/representative_budget_elasticities.csv","good,share,quantity_equivalent,budget_elasticity,marshallian_own,hicksian_own",((1..MD_K)',wr',qr',er',diagonal(M),diagonal(H)))
    rowsout=J(MD_K^2,4,.)
    for(j=1;j<=MD_K;j++) for(l=1;l<=MD_K;l++) rowsout[(j-1)*MD_K+l,]=(j,l,M[j,l],H[j,l])
    MD_csv(out+"/representative_price_elasticities.csv","good,price_good,marshallian,hicksian",rowsout)
    summary=J(MD_K,11,.)
    for(j=1;j<=MD_K;j++) {
        sorted=sort(eta[,j],1)
        summary[j,]=(j,mean(w[,j]),mean(eta[,j]),min(eta[,j]),max(eta[,j]),sorted[max((1,ceil(MD_N*.10)))],sorted[max((1,ceil(MD_N*.50)))],sorted[max((1,ceil(MD_N*.90)))],mean(hm[,j]),mean(hh[,j]),sum(eta[,j]:<0))
    }
    MD_csv(out+"/elasticity_distribution.csv","good,mean_share,mean_budget,min_budget,max_budget,p10_budget,p50_budget,p90_budget,mean_marshallian_own,mean_hicksian_own,negative_budget_cells",summary)
    MD_csv(out+"/representative_inputs.csv","good,price,mean_budget",((1..MD_K)',pbar',J(MD_K,1,mbar)))
    unlink(out+"/audit.csv")
    fh=fopen(out+"/audit.csv","w");fput(fh,"test,value,criterion")
    fput(fh,"unique_root_cells,"+strofreal(unique)+",N")
    fput(fh,"root_grid_step,.25,finite_grid_not_uniqueness_proof")
    fput(fh,"derivative_bracketed_critical_points,"+strofreal(refinements)+",inserted_between_grid_nodes")
    fput(fh,"nearzero_grid_plateau_cells,"+strofreal(sum(zeroplateau))+",must_be_zero_for_clear_root_audit")
    fput(fh,"root_zero_relative_tolerance,1e-13,node_roots_and_critical_tangencies_counted")
    fput(fh,"root_grid_lower,-50,numerical_search")
    fput(fh,"root_grid_upper,50,numerical_search")
    fput(fh,"free_tangent_parameters,"+strofreal(cols(T))+",positive_simplex_face_and_inactive_box_bounds")
    fput(fh,"full_natural_coordinate_parameters,"+strofreal(L)+",inward_simplex_and_box_directions_included")
    fput(fh,"full_natural_jacobian_rank_relative_1e-6,"+strofreal(fullrank)+",diagnostic_not_identification_proof")
    fput(fh,"full_natural_jacobian_condition_number,"+strofreal(fullcondition)+",reported")
    fput(fh,"jacobian_rank_relative_1e-6,"+strofreal(rankj)+",diagnostic_not_identification_proof")
    fput(fh,"jacobian_condition_number,"+strofreal(condj)+",reported")
    fput(fh,"final_natural_full_simplex_KKT_score,"+strofreal(MD_scorenorm(raw,score))+",lt_1e-4")
    fput(fh,"final_analytic_gradient_central_difference_gap,"+strofreal(parameter_gradient_gap)+",lt_1e-3_on_inactive_bounds")
    fput(fh,"central_difference_requested_step,1e-6,further_reduced_to_stay_on_simplex_face")
    fput(fh,"inadmissible_central_difference_coordinate_probes,"+strofreal(inadmissible_probes)+",must_be_zero_for_verified_gradient")
    fput(fh,"one_sided_inward_boundary_probes,"+strofreal(onesidedcount)+",natural_simplex_or_box_boundary")
    fput(fh,"one_sided_inward_gradient_maxgap,"+strofreal(onesidedgap)+",lt_1e-3")
    unsupported=sum((par[1,]+par[2,]):<=0)
    fput(fh,"unsupported_both_end_zero_foods,"+strofreal(unsupported)+",must_be_zero")
    fput(fh,"exact_zero_alpha,"+strofreal(sum(par[1,]:==0))+",economic_simplex_boundaries")
    fput(fh,"exact_zero_beta,"+strofreal(sum(par[2,]:==0))+",economic_simplex_boundaries")
    if(parameter_gradient_gap>1e-3 | missing(parameter_gradient_gap) | inadmissible_probes>0 | onesidedgap>1e-3 | unsupported>0) MD_OK=0
    if(rankj<cols(T) | fullrank<L | MD_scorenorm(raw,score)>=1e-4) MD_OK=0
    fput(fh,"N,"+strofreal(MD_N)+",observed")
    fput(fh,"relative_budget_gap,"+strofreal(rootgap)+",lt_1e-8")
    fput(fh,"relative_utility_equation_gap,"+strofreal(utilitygap)+",lt_1e-10")
    fput(fh,"min_Eu_over_Q,"+strofreal(minbranch)+",gt_1e-7")
    fput(fh,"minimum_observed_budget,"+strofreal(min(MD_M))+",reported_not_trimmed")
    fput(fh,"minimum_relative_delta_cost_slack,"+strofreal(min((MD_M-MD_P*par[3,]'):/MD_M))+",endpoint_domain_diagnostic")
    fput(fh,"minimum_relative_tau_cost_slack,"+strofreal(min((MD_M-MD_P*par[4,]'):/MD_M))+",endpoint_domain_diagnostic")
    fput(fh,"minimum_supernumerary_budget_share,"+strofreal(min(cur[,3]:/MD_M))+",positive_actual_branch")
    fput(fh,"share_addingup_gap,"+strofreal(addgap)+",lt_1e-8")
    fput(fh,"homogeneity_gap_representative,"+strofreal(homgap)+",lt_1e-8")
    fput(fh,"slutsky_symmetry_gap_representative,"+strofreal(symgap)+",lt_1e-8")
    fput(fh,"slutsky_max_eigenvalue_representative,"+strofreal(eigmax)+",le_1e-8")
    fput(fh,"finite_difference_elasticity_maxgap,"+strofreal(fdmax)+",lt_1e-3")
    if(fdmax>1e-3 | utilitygap>1e-10 | minbranch<=1e-7) MD_OK=0
    fput(fh,"min_budget_elasticity,"+strofreal(min(eta))+",reported_not_selection")
    fput(fh,"positive_marshallian_own_cells,"+strofreal(sum(hm:>0))+",reported_not_selection")
    fput(fh,"positive_hicksian_own_cells,"+strofreal(sum(hh:>1e-9))+",reported_not_selection")
    fclose(fh)
}

void MD_fit(string scalar model, string scalar out, real scalar starts, real scalar maxiter, real scalar warm)
{
    external real matrix MD_P,MD_W
    external real colvector MD_M
    external real rowvector MD_SCALE,MD_BEST,MD_LO,MD_HI
    external real scalar MD_K,MD_N,MD_MAI,MD_BESTVAL,MD_BESTSCORE,MD_OK
    real rowvector avg,initial,b,g,start,d,grad,pg
    real matrix par,ledger,warmpar,warmsummary
    real scalar L,j,r,f,it,ok,kappa,omega,ratio,fh,fd,delta,checkerr,fp,fm,guards,qualified,bestqualified,covpars,totalpars,polishit,finalit,refineit
    MD_MAI=model=="maidads";L=MD_MAI ? 4*MD_K : 3*MD_K-1
    MD_LO=(J(1,2*MD_K-2,0),J(1,MD_MAI ? 2*MD_K : MD_K,0),(MD_MAI ? .005 : J(1,0,.)),-25)
    MD_HI=(J(1,2*MD_K-2,1),J(1,MD_MAI ? 2*MD_K : MD_K,12),(MD_MAI ? 20 : J(1,0,.)),25)
    avg=colsum(MD_W):/MD_N;avg=avg:+1e-5;avg=avg:/sum(avg)
    initial=J(1,L,0);initial[1..MD_K-1]=avg[1..MD_K-1];initial[MD_K..2*MD_K-2]=initial[1..MD_K-1]
    delta=.03;ratio=min(MD_M:/(MD_P*(MD_SCALE:*delta)'));delta=delta*min((1,.2*ratio))
    initial[2*MD_K-1..3*MD_K-2]=J(1,MD_K,0)
    if(MD_MAI) {
        initial[3*MD_K-1..4*MD_K-2]=J(1,MD_K,0)
        initial[L-1]=1.5
    }
    initial[L]=mean(ln(MD_M)) + sum(avg:*ln(avg)) - mean(ln(MD_P)*avg')
    if(warm) {
        warmpar=st_matrix("MS_warmpar");warmsummary=st_matrix("MS_warmsummary")
        if(rows(warmpar)!=MD_K | cols(warmpar)!=4 | hasmissing(warmpar)) _error(3498)
        initial[1..MD_K-1]=warmpar[1..MD_K-1,1]'
        initial[MD_K..2*MD_K-2]=warmpar[1..MD_K-1,2]'
        initial[2*MD_K-1..3*MD_K-2]=warmpar[,3]':/MD_SCALE
        if(MD_MAI) {
            initial[3*MD_K-1..4*MD_K-2]=warmpar[,4]':/MD_SCALE
            initial[L-1]=warmsummary[1,1]
        }
        initial[L]=warmsummary[1,2]
        initial=MD_project(initial)
    }
    else MD_preference_start(initial,maxiter)
    MD_csv(out+"/initialization_raw.csv","index,value,lower,upper",((1..L)',initial',MD_LO',MD_HI'))
    MD_eval(initial,f,g);checkerr=0
    for(j=2*MD_K-1;j<=L;j++) {
        start=initial;start[j]=start[j]+1e-6;MD_eval(start,fp,grad)
        if(initial[j]<=MD_LO[j]+1e-8) checkerr=max((checkerr,abs((fp-f)/1e-6-g[j])))
        else {
            start=initial;start[j]=start[j]-1e-6;MD_eval(start,fm,grad)
            checkerr=max((checkerr,abs((fp-fm)/2e-6-g[j])))
        }
    }
    printf("Analytic objective gradient check: %9.4g\n",checkerr)
    MD_csv(out+"/initialization.csv","mean_nll,natural_full_simplex_KKT,initial_box_gradient_check",(f,MD_scorenorm(initial,g),checkerr))
    ledger=J(starts,12,.);MD_BESTVAL=.;MD_BEST=initial;MD_BESTSCORE=.;MD_OK=0;bestqualified=0
    rseed(20261011)
    for(r=1;r<=starts;r++) {
        start=initial
        if(r>1) {
            start[1..2*MD_K-2]=start[1..2*MD_K-2]+rnormal(1,2*MD_K-2,0,.01)
            if(MD_MAI & !warm) {
                start[L-1]=r==2 ? 2.5 : .75
                start[3*MD_K-1..4*MD_K-2]=J(1,MD_K,r==2 ? .02 : 4*delta)
            }
            if(!warm & (r>=3 | !MD_MAI)) start[2*MD_K-1..3*MD_K-2]=J(1,MD_K,delta)
            start[L]=start[L]+(r-2)*.15
        }
        printf("Start %g of %g: %s K=%g N=%g\n",r,starts,model,MD_K,MD_N)
        MD_solver(start,min((100,maxiter)),b,f,g,it,ok)
        if(MD_scorenorm(b,g)>=1e-4) {
            MD_polish(b,maxiter,f,g,polishit)
            refineit=0
            if(MD_scorenorm(b,g)>=1e-4) MS_refine_natural(b,f,g,refineit)
            finalit=0
            if(MD_scorenorm(b,g)>=1e-4) MD_solver(b,min((100,maxiter)),b,f,g,finalit,ok)
            else ok=1
            it=it+polishit+refineit+finalit
        }
        pg=MD_score(b,g)
        guards=sum(b[2*MD_K-1..L]:>=MD_HI[2*MD_K-1..L]:-1e-7)+(b[L]<=MD_LO[L]+1e-7)
        if(MD_MAI) guards=guards+(b[L-1]<=MD_LO[L-1]+1e-7)
        par=MD_unpack(b,MD_MAI)
        qualified=f<1e9 & !missing(f) & MD_scorenorm(b,g)<1e-4 & guards==0 & min(par[1,]+par[2,])>0
        ledger[r,]=(r,f,MD_scorenorm(b,g),it,ok,sum(b:<=MD_LO:+1e-8),sum(b:>=MD_HI:-1e-8),checkerr,guards,qualified,sum(par[1,]:==0),sum(par[2,]:==0))
        MD_csv(out+"/candidate_raw_"+strofreal(r)+".csv","index,value,lower,upper",((1..L)',b',MD_LO',MD_HI'))
        MD_csv(out+"/candidates.csv","start,mean_nll,natural_simplex_KKT,iterations,solver_converged,active_lower,active_upper,initial_box_gradient_check,numerical_guard_coordinates,stationary_without_guard,zero_alpha,zero_beta",ledger[1..r,])
        printf("Start complete mean_nll=%12.8f natural_KKT=%9.4g convergence=%g\n",f,MD_scorenorm(b,g),ok)
        if((qualified & !bestqualified) | (qualified==bestqualified & f<MD_BESTVAL)) {
            MD_BESTVAL=f
            MD_BEST=b
            MD_BESTSCORE=MD_scorenorm(b,g)
            MD_OK=qualified
            bestqualified=qualified
        }
    }
    MD_csv(out+"/candidates.csv","start,mean_nll,natural_simplex_KKT,iterations,solver_converged,active_lower,active_upper,initial_box_gradient_check,numerical_guard_coordinates,stationary_without_guard,zero_alpha,zero_beta",ledger)
    MD_csv(out+"/raw_parameters.csv","index,value,lower,upper",((1..L)',MD_BEST',MD_LO',MD_HI'))
    par=MD_unpack(MD_BEST,MD_MAI)
    MD_csv(out+"/scale.csv","good,training_quantity_equivalent_scale",((1..MD_K)',MD_SCALE'))
    MD_csv(out+"/parameters.csv","good,alpha,beta,delta,tau",((1..MD_K)',par'))
    covpars=MD_K*(MD_K-1)/2;totalpars=L+covpars
    MD_audit(out,MD_BEST,par,MD_MAI)
    MD_csv(out+"/model_summary.csv","N,K,mean_nll,nll,structural_parameter_count,covariance_parameter_count,total_parameter_count,AIC,BIC,projected_gradient,converged,omega,kappa",(MD_N,MD_K,MD_BESTVAL,MD_N*MD_BESTVAL,L,covpars,totalpars,2*MD_N*MD_BESTVAL+2*totalpars,2*MD_N*MD_BESTVAL+ln(MD_N)*totalpars,MD_BESTSCORE,MD_OK,(MD_MAI ? MD_BEST[L-1] : 0),MD_BEST[L]))
    st_numscalar("MD_bestvalue",MD_BESTVAL);st_numscalar("MD_bestscore",MD_BESTSCORE);st_numscalar("MD_converged",MD_OK)
    st_matrix("MD_b",MD_BEST)
    st_matrix("MD_alpha",par[1,]);st_matrix("MD_beta",par[2,])
    st_matrix("MD_delta",par[3,]);st_matrix("MD_tau",par[4,]);st_matrix("MD_scale",MD_SCALE)
}

void MD_store()
{
    external real matrix MD_QFIT,MD_WFIT,MD_ETA
    external real colvector MD_U
    real scalar j
    for(j=1;j<=cols(MD_QFIT);j++) {
        st_store(.,"fitq"+strofreal(j),MD_QFIT[,j]);st_store(.,"fitw"+strofreal(j),MD_WFIT[,j]);st_store(.,"eta"+strofreal(j),MD_ETA[,j])
    }
    st_store(.,"fitutility",MD_U)
}
end
