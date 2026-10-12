mata:
mata set matastrict on
mata set matalnum on

struct ct_state {
    real matrix W, LP, R
    real colvector X
    real scalar k, quadratic, mref
}

real matrix ct_contrast(real scalar k)
{
    real matrix A
    real scalar j
    A=J(k,k-1,0)
    for(j=1;j<k;j++) {
        A[1..j,j]=J(j,1,1/sqrt(j*(j+1)))
        A[j+1,j]=-j/sqrt(j*(j+1))
    }
    return(A)
}

real matrix ct_gamma(real rowvector b, real scalar k, real scalar quadratic)
{
    real matrix G
    real scalar i,j,h,pos
    h=k-1; G=J(h,h,0); pos=2*h+quadratic*h
    for(i=1;i<=h;i++) for(j=i;j<=h;j++) {
        pos++; G[i,j]=G[j,i]=b[pos]
    }
    return(G)
}

real matrix ct_predict(real rowvector b, struct ct_state scalar S)
{
    real rowvector a,be,la
    real colvector t,bp
    real matrix G,F
    real scalar h
    h=S.k-1; a=b[1..h]; be=b[h+1..2*h]; la=J(1,h,0)
    if(S.quadratic) la=b[2*h+1..3*h]
    G=ct_gamma(b,S.k,S.quadratic)
    t=S.X-S.LP[,S.k]-S.R*a'-.5*rowsum((S.R*G):*S.R)
    bp=exp(S.R*be')
    F=J(rows(S.W),1,1)*a+S.R*G+t*be+(t:^2:/bp)*la
    return((F,1:-rowsum(F),t,bp))
}

void ct_eval(real scalar todo, real rowvector b, struct ct_state scalar S,
    real scalar val, real rowvector grad, real matrix Hess)
{
    real matrix F,E,C,T,L,G,A,TF
    real rowvector be,la,ev
    real colvector t,bp,r
    real scalar n,h,i,j,pos,ld
    n=rows(S.W); h=S.k-1
    F=ct_predict(b,S)
    if(hasmissing(F)) {
        val=1e20
        if(todo) grad=J(1,cols(b),0)
        return
    }
    A=ct_contrast(S.k)
    E=(F[,1..S.k]-S.W)*A; C=quadcross(E,E)/n
    ev=symeigenvalues(C)
    if(min(ev)<=1e-15 | hasmissing(ev)) {
        val=1e20
        if(todo) grad=J(1,cols(b),0)
        return
    }
    val=sum(ln(ev))
    if(!todo) return
    TF=E*invsym(C)*A'*2/n
    T=TF[,1..h]:-TF[,S.k]
    t=F[,S.k+1]; bp=F[,S.k+2]
    be=b[h+1..2*h]; la=J(1,h,0)
    if(S.quadratic) la=b[2*h+1..3*h]
    L=J(n,1,1)*be+2*(t:/bp)*la
    grad=colsum(T)-colsum(S.R:*rowsum(T:*L))
    grad=grad,colsum(T:*t)-colsum(S.R:*rowsum(T:*((t:^2:/bp)*la)))
    if(S.quadratic) grad=grad,colsum(T:*(t:^2:/bp))
    pos=cols(grad)
    grad=grad,J(1,h*(h+1)/2,0)
    for(i=1;i<=h;i++) for(j=i;j<=h;j++) {
        pos++; r=S.R[,i]:*S.R[,j]*(1-.5*(i==j))
        grad[pos]=sum(T[,i]:*S.R[,j]-rowsum(T:*L):*r)
        if(i!=j) grad[pos]=grad[pos]+sum(T[,j]:*S.R[,i])
    }
}

real rowvector ct_start(struct ct_state scalar S)
{
    real matrix D,B,G
    real colvector y
    real rowvector b
    real scalar h,i,j
    h=S.k-1; y=S.X-rowsum(S.W:*S.LP)
    D=J(rows(y),1,1),S.R,y
    if(S.quadratic) D=D,y:^2
    B=qrsolve(D,S.W[,1..h])
    b=B[1,],B[h+2,]
    if(S.quadratic) b=b,B[h+3,]
    G=(B[2..h+1,]+B[2..h+1,]')/2
    for(i=1;i<=h;i++) for(j=i;j<=h;j++) b=b,G[i,j]
    return(b)
}

void ct_fit(string scalar model, real scalar k, real scalar starts)
{
    struct ct_state scalar S
    transmorphic scalar O
    real rowvector b0,b,best,gg,gn,ev
    real matrix HH,ledger,PP
    real scalar j,v,bv,rc,conv,hstep,vp,vm,ge,qualified,bestqualified
    string rowvector wnames,pnames
    wnames=pnames=J(1,k,"")
    for(j=1;j<=k;j++) {
        wnames[j]="w"+strofreal(j)
        pnames[j]="p"+strofreal(j)
    }
    S.W=st_data(.,wnames); S.LP=ln(st_data(.,pnames)); S.k=k
    S.R=S.LP[,1..k-1]:-S.LP[,k]; S.mref=exp(mean(ln(st_data(.,"m"))))
    S.X=ln(st_data(.,"m")/S.mref); S.quadratic=(model=="quaids")
    b0=ct_start(S); bv=.; best=b0; ledger=J(starts,7,.); bestqualified=0
    for(j=1;j<=starts;j++) {
        b=b0
        if(j>1) b=b+rnormal(1,cols(b),0,.01)
        O=optimize_init(); optimize_init_evaluator(O,&ct_eval())
        optimize_init_evaluatortype(O,"d1"); optimize_init_which(O,"min")
        optimize_init_argument(O,1,S); optimize_init_params(O,b)
        optimize_init_technique(O,"bfgs"); optimize_init_conv_maxiter(O,1000)
        optimize_init_conv_ptol(O,1e-12); optimize_init_conv_vtol(O,1e-14)
        optimize_init_tracelevel(O,"none"); rc=_optimize(O)
        b=optimize_result_params(O); ct_eval(1,b,S,v,gg,HH)
        conv=optimize_result_converged(O)
        if(v<1e19 & max(abs(gg))>=1e-4) {
            O=optimize_init(); optimize_init_evaluator(O,&ct_eval())
            optimize_init_evaluatortype(O,"d1"); optimize_init_which(O,"min")
            optimize_init_argument(O,1,S); optimize_init_params(O,b)
            optimize_init_technique(O,"nr"); optimize_init_conv_maxiter(O,100)
            optimize_init_conv_ptol(O,1e-12); optimize_init_conv_vtol(O,1e-14)
            optimize_init_tracelevel(O,"none"); rc=_optimize(O)
            b=optimize_result_params(O); ct_eval(1,b,S,v,gg,HH)
            conv=optimize_result_converged(O)
        }
        qualified=(v<1e19 & max(abs(gg))<1e-4)
        ledger[j,]=(j,rc,conv,optimize_result_iterations(O),v,max(abs(gg)),qualified)
        printf("%s start %g objective %g score %g converged %g\n",model,j,v,max(abs(gg)),conv)
        if(v<1e19 & (qualified>bestqualified | (qualified==bestqualified & v<bv))) {
            bv=v
            best=b
            bestqualified=qualified
        }
    }
    ct_eval(1,best,S,v,gg,HH); gn=J(1,cols(best),.)
    for(j=1;j<=cols(best);j++) {
        hstep=1e-6*max((1,abs(best[j])))
        b=best; b[j]=b[j]+hstep; ct_eval(0,b,S,vp,ev,HH)
        b=best; b[j]=b[j]-hstep; ct_eval(0,b,S,vm,ev,HH)
        gn[j]=(vp-vm)/(2*hstep)
    }
    ge=max(abs(gn-gg):/(1:+abs(gg)))
    PP=ct_predict(best,S)
    st_matrix("CT_b",best); st_matrix("CT_ledger",ledger)
    st_numscalar("CT_mref",S.mref); st_numscalar("CT_objective",bv)
    st_numscalar("CT_score",max(abs(gg))); st_numscalar("CT_gradient_error",ge)
    st_numscalar("CT_stationary",bestqualified)
    st_numscalar("CT_n",rows(S.W)); st_numscalar("CT_parameters",cols(best))
    st_numscalar("CT_cov_parameters",k*(k-1)/2)
    ct_export(best,S)
}

void ct_export(real rowvector b, struct ct_state scalar S)
{
    real matrix F,G,Gfull,H,M,SS,OUT
    real rowvector a,be,la,ww,eta,ap,l,ev
    real scalar n,k,h,i,j,r,valid,pos
    F=ct_predict(b,S); n=rows(F); k=S.k; h=k-1
    a=b[1..h],1-sum(b[1..h]); be=b[h+1..2*h],-sum(b[h+1..2*h])
    la=J(1,k,0)
    if(S.quadratic) la=b[2*h+1..3*h],-sum(b[2*h+1..3*h])
    G=ct_gamma(b,k,S.quadratic)
    Gfull=(G,-rowsum(G))\(-colsum(G),sum(G))
    OUT=J(n,k*4+4,.)
    for(r=1;r<=n;r++) {
        ww=F[r,1..k]; l=be+2*F[r,k+1]/F[r,k+2]*la
        valid=min(ww)>0 & !hasmissing(ww)
        eta=1:+l:/ww; ap=a+S.LP[r,]*Gfull
        M=Gfull-l'*ap-(la'*be)*F[r,k+1]^2/F[r,k+2]
        M=M:/ww'-I(k); H=M+eta'*ww
        SS=diag(ww)*H
        ev=symeigenvalues((SS+SS')/2)
        OUT[r,]=(ww,eta,diagonal(M)',diagonal(H)',valid,max(ev),max(abs(SS-SS')),abs(sum(ww)-1))
    }
    for(j=1;j<=k;j++) {
        st_addvar("double","fit_w"+strofreal(j)); st_store(.,"fit_w"+strofreal(j),OUT[,j])
        st_addvar("double","eta_m"+strofreal(j)); st_store(.,"eta_m"+strofreal(j),OUT[,k+j])
        st_addvar("double","own_m"+strofreal(j)); st_store(.,"own_m"+strofreal(j),OUT[,2*k+j])
        st_addvar("double","own_h"+strofreal(j)); st_store(.,"own_h"+strofreal(j),OUT[,3*k+j])
    }
    st_addvar("byte","positive_support"); st_store(.,"positive_support",OUT[,4*k+1])
    st_addvar("double","slutsky_max_eig"); st_store(.,"slutsky_max_eig",OUT[,4*k+2])
    st_addvar("double","slutsky_symmetry_error"); st_store(.,"slutsky_symmetry_error",OUT[,4*k+3])
    st_addvar("double","budget_error"); st_store(.,"budget_error",OUT[,4*k+4])
    ct_representative(b,S)
}

void ct_representative(real rowvector b, struct ct_state scalar S)
{
    struct ct_state scalar T
    real matrix F,G,Gfull,M,H
    real rowvector a,be,la,w,eta,ap,l
    real scalar k,h
    k=S.k; h=k-1; T=S
    T.W=mean(S.W); T.LP=mean(S.LP); T.R=T.LP[,1..h]:-T.LP[,k]
    T.X=ln(mean(st_data(.,"m"))/S.mref)
    F=ct_predict(b,T); w=F[1,1..k]
    a=b[1..h],1-sum(b[1..h]); be=b[h+1..2*h],-sum(b[h+1..2*h])
    la=J(1,k,0); if(S.quadratic) la=b[2*h+1..3*h],-sum(b[2*h+1..3*h])
    G=ct_gamma(b,k,S.quadratic); Gfull=(G,-rowsum(G))\(-colsum(G),sum(G))
    l=be+2*F[1,k+1]/F[1,k+2]*la; eta=1:+l:/w
    ap=a+T.LP*Gfull; M=Gfull-l'*ap-(la'*be)*F[1,k+1]^2/F[1,k+2]
    M=M:/w'-I(k); H=M+eta'*w
    st_matrix("CT_representative",((1..k)',w',eta',diagonal(M),diagonal(H)))
    st_matrix("CT_marshallian",M); st_matrix("CT_hicksian",H)
}
end
