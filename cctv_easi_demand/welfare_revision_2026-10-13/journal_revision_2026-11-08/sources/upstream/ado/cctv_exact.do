* Eight food groups: old G6 and G7 merged; seven free equations.
* Exact AIDS, QUAIDS and EASI(2), fast one-step GMM using exact sufficient moments.
* No SY. Food budget is assumed exogenous; observed EASI implicit utility is
* instrumented with nominal log budget, its square, prices and observed controls.
capture mata: mata drop xe_*()
mata:
mata set matastrict on
struct xe_state {
    string scalar model
    real scalar n, nd
    real matrix D, R, P, Z, U0, U1, U2, WW0, WW1, WW2, WT1, WT2, Wz,Qd,Qw,Qr
    real colvector cl, u3, u4, x3, x4
}

real matrix xe_gamma(real rowvector b, real scalar nd, string scalar model)
{
    real scalar j,k,h,pos
    real matrix G
    h=7*(nd+1)+7+7*(model!="aids")
    G=J(7,7,0); pos=h
    for(j=1;j<=7;j++) for(k=j;k<=7;k++) {
        pos++; G[j,k]=G[k,j]=b[pos]
    }
    return(G)
}

real matrix xe_coeff(real rowvector b, struct xe_state scalar S)
{
    real matrix A,G,c0,c1,c2,K
    real rowvector be,la
    real colvector L,cc,bp
    real scalar pos
    pos=7*(S.nd+1)
    A=S.D*rowshape(b[1..pos],7)'
    be=b[pos+1..pos+7]
    la=J(1,7,0)
    if(S.model!="aids") la=b[pos+8..pos+14]
    G=xe_gamma(b,S.nd,S.model)
    cc=.5*rowsum((S.R*G):*S.R)
    if(S.model=="easi") {
        c0=A+S.R*G+cc*be+(cc:^2)*la
        c1=J(rows(A),1,1)*be+2*cc*la
        c2=J(rows(A),1,1)*la
    }
    else {
        L=S.P[,8]+rowsum(A:*S.R)+cc
        bp=exp(-S.R*be')
        K=bp*la
        c0=A+S.R*G-L*be+(L:^2):*K
        c1=J(rows(A),1,1)*be-2*L:*K
        c2=K
    }
    return(c0,c1,c2)
}

real matrix xe_cellmom(real rowvector b, struct xe_state scalar S)
{
    real matrix C,c0,c1,c2,F0,F1,F2
    C=xe_coeff(b,S); c0=C[,1..7]; c1=C[,8..14]; c2=C[,15..21]
    F0=S.U0[,1]:*c0+S.U1[,1]:*c1+S.U2[,1]:*c2-S.WW0
    F1=S.U0[,2]:*c0+S.U1[,2]:*c1+S.U2[,2]:*c2-S.WW1
    F2=S.U0[,3]:*c0+S.U1[,3]:*c1+S.U2[,3]:*c2-S.WW2
    return(F0,F1,F2)
}

real matrix xe_mom(real rowvector b, struct xe_state scalar S)
{
    real matrix F
    F=xe_cellmom(b,S)
    return((quadcross(S.Z,F[,1..7])\colsum(F[,8..14])\colsum(F[,15..21]))/S.n)
}

void xe_eval(real scalar todo, real rowvector b, struct xe_state scalar S,
    real scalar val, real rowvector grad, real matrix Hess)
{
    real scalar nc,pos,j,k
    real matrix MM,T,H0,H1,H2,A,G,K,HH,combo
    real rowvector be,la,gb,gl,gg
    real colvector L,cc,bp,QL,QQ,rr
    MM=xe_mom(b,S); T=S.Wz*MM
    val=sum(MM:*T)
    if(todo==0) return
    nc=cols(S.Z)
    HH=S.Z*T[1..nc,]
    H0=S.U0[,1]:*HH+S.U0[,2]*T[nc+1,]+S.U0[,3]*T[nc+2,]
    H1=S.U1[,1]:*HH+S.U1[,2]*T[nc+1,]+S.U1[,3]*T[nc+2,]
    H2=S.U2[,1]:*HH+S.U2[,2]*T[nc+1,]+S.U2[,3]*T[nc+2,]
    pos=7*(S.nd+1)
    A=S.D*rowshape(b[1..pos],7)'
    be=b[pos+1..pos+7]; la=J(1,7,0)
    if(S.model!="aids") la=b[pos+8..pos+14]
    G=xe_gamma(b,S.nd,S.model); cc=.5*rowsum((S.R*G):*S.R)
    if(S.model=="easi") {
        QL=H0*be'+2*cc:*(H0*la')+2*H1*la'
        grad=vec(quadcross(S.D,H0))'
        gb=colsum(H1+cc:*H0)
        gl=colsum(H2+2*cc:*H1+(cc:^2):*H0)
    }
    else {
        L=S.P[,8]+rowsum(A:*S.R)+cc
        bp=exp(-S.R*be'); K=bp*la
        QL=-H0*be'+2*L:*rowsum(K:*H0)-2*rowsum(K:*H1)
        combo=H2-2*L:*H1+(L:^2):*H0
        QQ=rowsum(K:*combo)
        grad=vec(quadcross(S.D,H0+QL:*S.R))'
        gb=colsum(H1-L:*H0-S.R:*QQ)
        gl=colsum(bp:*combo)
    }
    grad=grad,gb
    if(S.model!="aids") grad=grad,gl
    gg=J(1,28,0); pos=0
    for(j=1;j<=7;j++) for(k=j;k<=7;k++) {
        pos++; rr=S.R[,j]:*S.R[,k]*(1-.5*(j==k))
        gg[pos]=sum(H0[,j]:*S.R[,k]+QL:*rr)
        if(j!=k) gg[pos]=gg[pos]+sum(H0[,k]:*S.R[,j])
    }
    grad=2*(grad,gg)/S.n
}

real rowvector xe_start(struct xe_state scalar S)
{
    real matrix B,X,M,Q,coef,G
    real rowvector b
    real scalar j,k,nb,h,pos
    B=S.D,S.R; nb=cols(B)
    h=1+(S.model!="aids")
    if(h==1) M=(quadcross(B,S.U0[,1],B),quadcross(B,S.U1[,1]))\(quadcross(B,S.U1[,1])',sum(S.U2[,1]))
    else M=(quadcross(B,S.U0[,1],B),quadcross(B,S.U1[,1]),quadcross(B,S.U2[,1]))\(quadcross(B,S.U1[,1])',sum(S.U2[,1]),sum(S.u3))\(quadcross(B,S.U2[,1])',sum(S.u3),sum(S.u4))
    Q=quadcross(B,S.WW0)\colsum(S.WT1)
    if(h==2) Q=Q\colsum(S.WT2)
    coef=invsym(M)*Q
    b=vec(coef[1..S.nd+1,])',coef[nb+1,]
    if(h==2) b=b,coef[nb+2,]
    G=(coef[S.nd+2..S.nd+8,]+coef[S.nd+2..S.nd+8,]')/2
    for(j=1;j<=7;j++) for(k=j;k<=7;k++) b=b,G[j,k]
    return(b)
}

struct xe_state scalar xe_load(string scalar model, string scalar demos)
{
    struct xe_state scalar S
    real matrix ZZZ,WX
    real scalar nc
    S.model=model; S.D=J(st_nobs(),1,1),st_data(.,tokens(demos))
    S.nd=cols(S.D)-1
    S.P=st_data(.,tokens("ep1 ep2 ep3 ep4 ep5 ep6 ep7 ep8"))
    S.R=S.P[,1..7]:-S.P[,8]
    S.Z=S.D,S.R
    S.U0=st_data(.,tokens("nn x1 x2"))
    S.U1=st_data(.,tokens("u1 u1x u1x2"))
    S.U2=st_data(.,tokens("u2 u2x u2x2"))
    S.WW0=st_data(.,tokens("w01 w02 w03 w04 w05 w06 w07"))
    S.WW1=st_data(.,tokens("w11 w12 w13 w14 w15 w16 w17"))
    S.WW2=st_data(.,tokens("w21 w22 w23 w24 w25 w26 w27"))
    S.WT1=st_data(.,tokens("wt11 wt12 wt13 wt14 wt15 wt16 wt17"))
    S.WT2=st_data(.,tokens("wt21 wt22 wt23 wt24 wt25 wt26 wt27"))
    S.cl=st_data(.,"province")
    S.u3=st_data(.,"u3"); S.u4=st_data(.,"u4")
    S.x3=st_data(.,"x3"); S.x4=st_data(.,"x4")
    S.n=sum(S.U0[,1]); nc=cols(S.Z)
    ZZZ=quadcross(S.Z,S.U0[,1],S.Z),quadcross(S.Z,S.U0[,2..3])
    ZZZ=ZZZ\(quadcross(S.Z,S.U0[,2..3])',(sum(S.U0[,3]),sum(S.x3)\sum(S.x3),sum(S.x4)))
    S.Wz=invsym(ZZZ/S.n)
    S.Qd=(quadcross(S.Z,S.U0[,1],S.D)\colsum(S.U0[,2]:*S.D)\colsum(S.U0[,3]:*S.D))/S.n
    S.Qw=(quadcross(S.Z,S.WW0)\colsum(S.WW1)\colsum(S.WW2))/S.n
    S.Qr=(quadcross(S.Z,S.U0[,1],S.R)\colsum(S.U0[,2]:*S.R)\colsum(S.U0[,3]:*S.R))/S.n
    return(S)
}

void xe_fit(string scalar model, string scalar demos)
{
    struct xe_state scalar S
    transmorphic opt
    real rowvector b,b0,gr,numgr,bc
    real colvector g
    real matrix H,Jj,W,JW,bread,F,ClSc,Sc,V,G,JJ
    real scalar val,vp,vm,h,j,nq,np,nc,iter,conv,graderr
    real colvector ord
    real matrix info
    S=xe_load(model,demos); b0=xe_start(S)
    xe_eval(1,b0,S,val,gr,H)
    numgr=J(1,cols(b0),0)
    for(j=1;j<=cols(b0);j++) {
        h=1e-6*(1+abs(b0[j])); bc=b0; bc[j]=bc[j]+h
        xe_eval(0,bc,S,vp,gr,H); bc[j]=bc[j]-2*h
        xe_eval(0,bc,S,vm,gr,H); numgr[j]=(vp-vm)/(2*h)
    }
    graderr=max(abs(gr-numgr))
    printf("Exact %s: %g rows, %g sufficient-statistic cells; gradient error %9.3e\n",model,S.n,rows(S.D),graderr)
    opt=optimize_init(); optimize_init_evaluator(opt,&xe_eval())
    optimize_init_evaluatortype(opt,"d1"); optimize_init_which(opt,"min")
    optimize_init_argument(opt,1,S); optimize_init_params(opt,b0)
    optimize_init_technique(opt,"bfgs"); optimize_init_conv_maxiter(opt,500)
    optimize_init_conv_ptol(opt,1e-7); optimize_init_conv_vtol(opt,1e-10)
    optimize_init_tracelevel(opt,"value")
    b=optimize(opt); iter=optimize_result_iterations(opt)
    conv=optimize_result_converged(opt)
    G=xe_mom(b,S); g=vec(G); np=cols(b); nq=rows(g)
    Jj=J(nq,np,0)
    for(j=1;j<=np;j++) {
        h=1e-5*(1+abs(b[j])); bc=b; bc[j]=bc[j]+h
        JJ=xe_mom(bc,S); bc[j]=bc[j]-2*h
        Jj[,j]=(vec(JJ)-vec(xe_mom(bc,S)))/(2*h)
    }
    W=I(7)#S.Wz; JW=Jj'*W
    bread=invsym(JW*Jj)
    F=xe_cellmom(b,S); ord=order(S.cl,1); info=panelsetup(S.cl[ord],1)
    nc=rows(info); ClSc=J(nc,nq,0)
    for(j=1;j<=7;j++) {
        Sc=S.Z:*F[,j],F[,7+j],F[,14+j]
        ClSc[,(j-1)*(cols(S.Z)+2)+1..j*(cols(S.Z)+2)]=panelsum(Sc[ord,],info)
    }
    V=bread*JW*quadcross(ClSc,ClSc)*JW'*bread*nc/(nc-1)/S.n^2
    st_matrix("XE_b",b); st_matrix("XE_V",V)
    st_matrix("XE_momfit",G)
    bc=b:+1e-4*sin(1..np)
    st_matrix("XE_bpert",bc); st_matrix("XE_mompert",xe_mom(bc,S))
    st_numscalar("XE_N",S.n); st_numscalar("XE_cells",rows(S.D))
    st_numscalar("XE_conv",conv); st_numscalar("XE_iters",iter)
    st_numscalar("XE_obj",sum(G:*(S.Wz*G)))
    st_numscalar("XE_graderr",graderr); st_numscalar("XE_rank",rank(Jj))
    st_numscalar("XE_clusters",nc)
}

void xe_check_moments(string scalar model,string scalar demos)
{
    struct xe_state scalar S
    real matrix W,Z,C,F,M
    real colvector X,t
    real rowvector b
    real scalar e1,e2,j
    S.model=model; S.D=J(st_nobs(),1,1),st_data(.,tokens(demos)); S.nd=cols(S.D)-1
    S.P=st_data(.,tokens("ep1 ep2 ep3 ep4 ep5 ep6 ep7 ep8"))
    S.R=S.P[,1..7]:-S.P[,8]
    X=st_data(.,"ex"); W=st_data(.,tokens("w1 w2 w3 w4 w5 w6 w7 w8"))
    t=X
    if(model=="easi") t=t-rowsum(W:*S.P)
    Z=S.D,S.R,X,X:^2
    b=st_matrix("XE_b"); C=xe_coeff(b,S)
    F=C[,1..7]+t:*C[,8..14]+(t:^2):*C[,15..21]
    M=quadcross(Z,F-W[,1..7])/st_nobs()
    e1=max(abs(M-st_matrix("XE_momfit")))
    b=st_matrix("XE_bpert"); C=xe_coeff(b,S)
    F=C[,1..7]+t:*C[,8..14]+(t:^2):*C[,15..21]
    M=quadcross(Z,F-W[,1..7])/st_nobs()
    e2=max(abs(M-st_matrix("XE_mompert")))
    st_numscalar("XE_compressionerr",max((e1,e2)))
    printf("Compressed/full micro moment max error: %9.3e\n",max((e1,e2)))
}

real matrix xe_predict(real rowvector b, string scalar model, real matrix P,
    real colvector X, real matrix D, real matrix obsW)
{
    real matrix A,G,F
    real rowvector be,la
    real matrix R
    real colvector cc,L,y,bp,qa,qb,qc,dis,r1,r2,use,seed
    real scalar nd,pos,i,qstable
    nd=cols(D)-1; pos=7*(nd+1); bp=0
    A=D*rowshape(b[1..pos],7)'; G=xe_gamma(b,nd,model)
    R=P[,1..7]:-P[,8]; cc=.5*rowsum((R*G):*R)
    be=b[pos+1..pos+7]; la=J(1,7,0)
    if(model!="aids") la=b[pos+8..pos+14]
    if(model=="easi") {
        qa=R*la'; qb=1:+R*be'; qc=P[,8]+rowsum(A:*R)+cc-X
        dis=qb:^2-4*qa:*qc
        y=J(rows(X),1,.)
        for(i=1;i<=rows(X);i++) {
            if(abs(qa[i])<1e-12) {
                if(qb[i]>1e-8) y[i]=-qc[i]/qb[i]
            }
            else if(dis[i]>=0) {
                qstable=-.5*(qb[i]+(2*(qb[i]>=0)-1)*sqrt(dis[i]))
                r1=qstable/qa[i]
                r2=qc[i]/qstable
                seed=X[i]-sum(obsW[i,]:*P[i,])+cc[i]
                if(qb[i]+2*qa[i]*r1>1e-8) y[i]=r1
                if(qb[i]+2*qa[i]*r2>1e-8) {
                    if(missing(y[i]) | abs(r2-seed)<abs(y[i]-seed)) y[i]=r2
                }
            }
        }
        F=A+R*G+y*be+(y:^2)*la
    }
    else {
        L=P[,8]+rowsum(A:*R)+cc; y=X-L; bp=exp(-R*be')
        F=A+R*G+y*be+(y:^2):*(bp*la)
    }
    return(F,1:-rowsum(F),y)
}

void xe_elasticities(string scalar model,string scalar demos)
{
    real matrix P,D,W,F,R,G8,G9,Q,dx,eta,der,EH,EM,SS,WM
    real rowvector b,be,la,ev,own,ehown,ws,support,ag
    real colvector X,y,bp,den,ok,idx,pr,inc,tt,part
    real scalar nd,pos,j,i,n,asym,eig,sp,ng
    b=st_matrix("XE_b"); P=st_data(.,tokens("ep1 ep2 ep3 ep4 ep5 ep6 ep7 ep8"))
    X=st_data(.,"ex"); W=st_data(.,tokens("w1 w2 w3 w4 w5 w6 w7 w8"))
    D=J(st_nobs(),1,1),st_data(.,tokens(demos)); n=rows(X); nd=cols(D)-1
    F=xe_predict(b,model,P,X,D,W); y=F[,9]; F=F[,1..8]
    ok=(rowmin(F):>0):&(rowmissing(F):==0)
    if(st_varindex("xe_positive")<.) st_store(.,"xe_positive",ok)
    idx=selectindex(ok); sp=rows(idx)/n
    st_numscalar("XE_positive_support",sp)
    st_numscalar("XE_rootfail",sum(y:>=.))
    st_matrix("XE_share_audit",(colsum(F:<0)/n\colsum(F:>=.)/n\colsum(W)/n\colsum(F)/n)')
    if(rows(idx)==0) {
        st_matrix("XE_elasticity",J(8,4,.)); st_matrix("XE_reg",(sp,.,.)); return
    }
    P=P[idx,]; X=X[idx]; D=D[idx,]; W=W[idx,]; F=F[idx,]; y=y[idx]
    R=P[,1..7]:-P[,8]; pos=7*(nd+1); be=b[pos+1..pos+7]
    la=J(1,7,0); if(model!="aids") la=b[pos+8..pos+14]
    be=be,-sum(be); la=la,-sum(la)
    G8=xe_gamma(b,nd,model)
    G9=(G8,-rowsum(G8))\(-colsum(G8),sum(G8))
    if(model=="easi") {
        dx=J(rows(F),1,1)*be+2*y*la
        den=1:+rowsum(P:*dx); dx=dx:/den
        WM=F
    }
    else {
        bp=exp(-P*be')
        dx=J(rows(F),1,1)*be+2*y:*(bp*la)
        WM=D*rowshape(b[1..pos],7)'
        WM=WM,1:-rowsum(WM); WM=WM+P*G9
    }
    eta=1:+dx:/F
    Q=F:*exp(X):/exp(P)
    ev=colsum(Q:*eta):/colsum(Q)
    own=ehown=J(1,8,.); SS=EM=EH=J(8,8,.)
    for(j=1;j<=8;j++) {
        if(model=="easi") der=J(rows(F),1,1)*G9[,j]'-dx:*F[,j]
        else der=J(rows(F),1,1)*G9[,j]'-dx:*WM[,j]-(y:^2):*(bp*la)*be[j]
        for(i=1;i<=8;i++) {
            tt=der[,i]:/F[,i]:-(i==j)
            part=tt+eta[,i]:*F[,j]
            EM[i,j]=sum(Q[,i]:*tt)/sum(Q[,i])
            EH[i,j]=sum(Q[,i]:*part)/sum(Q[,i])
            SS[i,j]=mean(F[,i]:*part)
        }
        own[j]=EM[j,j]; ehown[j]=EH[j,j]
    }
    st_matrix("XE_elasticity",(ev\own\ehown\colsum(F)/rows(F))')
    st_matrix("XE_mar",EM); st_matrix("XE_hick",EH); st_matrix("XE_slutsky",SS)
    asym=max(abs(SS-SS')); eig=max(symeigenvalues((SS+SS')/2))
    st_matrix("XE_reg",(sp,asym,eig))
    xe_representative(b,model,mean(P),mean(X),mean(D),mean(W))
}

void xe_representative(real rowvector b,string scalar model,real matrix P,
    real colvector X,real matrix D,real matrix W)
{
    real matrix F,G8,G9,WM,dx,eta,M,H
    real rowvector be,la
    real scalar nd,pos,j,i,y,bp
    nd=cols(D)-1; pos=7*(nd+1); bp=0
    F=xe_predict(b,model,P,X,D,W); y=F[1,9]; F=F[,1..8]
    be=b[pos+1..pos+7]; la=J(1,7,0)
    if(model!="aids") la=b[pos+8..pos+14]
    be=be,-sum(be); la=la,-sum(la)
    G8=xe_gamma(b,nd,model); G9=(G8,-rowsum(G8))\(-colsum(G8),sum(G8))
    if(model=="easi") {
        dx=be+2*y*la; dx=dx/(1+sum(P:*dx)); WM=F
    }
    else {
        bp=exp(-P*be'); dx=be+2*y*bp*la
        WM=D*rowshape(b[1..pos],7)'; WM=WM,1-sum(WM)
        WM=WM+P*G9
    }
    eta=1:+dx:/F; M=H=J(8,8,.)
    for(i=1;i<=8;i++) for(j=1;j<=8;j++) {
        M[i,j]=(G9[i,j]-dx[i]*WM[j]-(model!="easi")*la[i]*bp*y^2*be[j])/F[i]-(i==j)
        H[i,j]=M[i,j]+eta[i]*F[j]
    }
    st_matrix("XE_rep_elasticity",(eta\diagonal(M)'\diagonal(H)'\F)')
    st_matrix("XE_rep_mar",M); st_matrix("XE_rep_hick",H)
}
end
