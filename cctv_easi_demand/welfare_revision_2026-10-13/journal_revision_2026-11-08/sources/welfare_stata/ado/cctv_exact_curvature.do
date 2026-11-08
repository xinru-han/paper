* GMM re-estimation with the sufficient global EASI restriction Gamma7=-LL'.
* No sign projection is used as an estimated result; projection initializes L.
scalar XE_startfloor=1e-6
mata:
mata set matastrict on
real matrix xec_L(real rowvector theta)
{
    real scalar pos,i,j
    real matrix L
    L=J(7,7,0); pos=cols(theta)-28
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) L[j,i]=theta[++pos]
    return(L)
}
real rowvector xec_b(real rowvector theta)
{
    real rowvector b
    real matrix G,L
    real scalar pos,i,j
    b=theta; L=xec_L(theta); G=-L*L'; pos=cols(b)-28
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) b[++pos]=G[i,j]
    return(b)
}
void xec_eval(real scalar todo,real rowvector theta,struct xe_state scalar S,
    real scalar val,real rowvector grad,real matrix Hess)
{
    real rowvector b,gb
    real matrix M,L,GL
    real scalar pos,i,j
    b=xec_b(theta); gb=J(1,cols(theta),0)
    xe_eval(todo,b,S,val,gb,Hess)
    if(todo==0) return
    M=J(7,7,0); pos=cols(theta)-28
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) {
        M[i,j]=M[j,i]=gb[++pos]/(1+(i!=j))
    }
    L=xec_L(theta); GL=-2*M*L; grad=gb; pos=cols(theta)-28
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) grad[++pos]=GL[j,i]
}
void xec_fit(string scalar demos)
{
    struct xe_state scalar S
    real rowvector theta,theta0,b0,b,eval,grad,numgrad,tc
    real colvector ord,g
    real matrix G,U,L,H,Jj,W,JW,bread,F,ClSc,Sc,V,JJ,info,Btrans
    real scalar val,vp,vm,h,i,j,pos,np,nq,nc,iter,conv,grerr
    transmorphic opt
    S=xe_load("easi",demos); b0=st_matrix("XE_b")
    G=xe_gamma(b0,S.nd,"easi")
    symeigensystem((G+G')/2,U,eval)
    eval=(eval:<-st_numscalar("XE_startfloor")):*eval+(eval:>=-st_numscalar("XE_startfloor")):*(-st_numscalar("XE_startfloor"))
    G=U'*diag(eval)*U
    L=cholesky(-G); theta0=b0; pos=cols(b0)-36
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) theta0[++pos]=L[j,i]
    xec_eval(1,theta0,S,val,grad,H); numgrad=grad
    for(i=1;i<=cols(theta0);i++) {
        h=1e-6*(1+abs(theta0[i])); tc=theta0; tc[i]=tc[i]+h
        xec_eval(0,tc,S,vp,grad,H); tc[i]=tc[i]-2*h
        xec_eval(0,tc,S,vm,grad,H); numgrad[i]=(vp-vm)/(2*h)
    }
    grerr=max(abs(grad-numgrad))
    printf("Constrained EASI gradient max error: %9.3e\n",grerr)
    opt=optimize_init(); optimize_init_evaluator(opt,&xec_eval())
    optimize_init_evaluatortype(opt,"d1"); optimize_init_which(opt,"min")
    optimize_init_argument(opt,1,S); optimize_init_params(opt,theta0)
    optimize_init_technique(opt,"bfgs"); optimize_init_conv_maxiter(opt,800)
    optimize_init_conv_ptol(opt,1e-9); optimize_init_conv_vtol(opt,1e-14)
    optimize_init_conv_nrtol(opt,1e-12)
    optimize_init_tracelevel(opt,"value")
    theta=optimize(opt); b=xec_b(theta); iter=optimize_result_iterations(opt)
    conv=optimize_result_converged(opt)
    G=xe_mom(b,S); g=vec(G); np=cols(theta); nq=rows(g)
    Jj=J(nq,np,0); Btrans=J(np,np,0)
    for(i=1;i<=np;i++) {
        h=1e-5*(1+abs(theta[i])); tc=theta; tc[i]=tc[i]+h
        JJ=xe_mom(xec_b(tc),S); vp=0
        Btrans[,i]=xec_b(tc)'; tc[i]=tc[i]-2*h
        Jj[,i]=(vec(JJ)-vec(xe_mom(xec_b(tc),S)))/(2*h)
        Btrans[,i]=(Btrans[,i]-xec_b(tc)')/(2*h)
    }
    W=I(7)#S.Wz; JW=Jj'*W; bread=invsym(JW*Jj)
    F=xe_cellmom(b,S); ord=order(S.cl,1); info=panelsetup(S.cl[ord],1)
    nc=rows(info); ClSc=J(nc,nq,0)
    for(i=1;i<=7;i++) {
        Sc=S.Z:*F[,i],F[,7+i],F[,14+i]
        ClSc[,(i-1)*(cols(S.Z)+2)+1..i*(cols(S.Z)+2)]=panelsum(Sc[ord,],info)
    }
    V=bread*JW*quadcross(ClSc,ClSc)*JW'*bread*nc/(nc-1)/S.n^2
    V=Btrans*V*Btrans'
    st_matrix("XE_b",b); st_matrix("XE_V",V)
    st_matrix("XE_momfit",G); tc=b:+1e-4*sin(1..np)
    st_matrix("XE_bpert",tc); st_matrix("XE_mompert",xe_mom(tc,S))
    st_numscalar("XE_N",S.n); st_numscalar("XE_cells",rows(S.D))
    st_numscalar("XE_conv",conv); st_numscalar("XE_iters",iter)
    st_numscalar("XE_obj",sum(G:*(S.Wz*G)))
    st_numscalar("XE_graderr",grerr); st_numscalar("XE_rank",rank(Jj))
    st_numscalar("XE_clusters",nc)
    st_numscalar("XE_Gamma_maxeig",max(symeigenvalues(xe_gamma(b,S.nd,"easi"))))
}

real rowvector xec_profile_b(real rowvector lt,struct xe_state scalar S)
{
    real matrix G,L,A,coef,Ymom,Q
    real colvector cc,t1,t2
    real rowvector b
    real scalar i,j,pos
    L=xec_L(lt); G=-L*L'; cc=.5*rowsum((S.R*G):*S.R)
    Ymom=S.U1+cc:*S.U0
    A=S.Qd,(quadcross(S.Z,Ymom[,1])\sum(Ymom[,2])\sum(Ymom[,3]))/S.n
    Ymom=S.U2+2*cc:*S.U1+(cc:^2):*S.U0
    A=A,(quadcross(S.Z,Ymom[,1])\sum(Ymom[,2])\sum(Ymom[,3]))/S.n
    Q=S.Qw-S.Qr*G
    coef=invsym(A'*S.Wz*A)*(A'*S.Wz*Q)
    b=vec(coef[1..S.nd+1,])',coef[S.nd+2,],coef[S.nd+3,]
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) b=b,G[i,j]
    return(b)
}
void xec_profile_eval(real scalar todo,real rowvector lt,struct xe_state scalar S,
    real scalar val,real rowvector grad,real matrix Hess)
{
    real rowvector b,gb
    real matrix M,GL
    real scalar i,j,pos
    b=xec_profile_b(lt,S); gb=J(1,cols(b),0)
    xe_eval(todo,b,S,val,gb,Hess)
    if(todo==0) return
    M=J(7,7,0); pos=cols(b)-28
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) M[i,j]=M[j,i]=gb[++pos]/(1+(i!=j))
    GL=-2*M*xec_L(lt); grad=lt; pos=0
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) grad[++pos]=GL[j,i]
}

void xec_profile_fit(string scalar demos)
{
    struct xe_state scalar S
    real rowvector theta,lt,theta0,b0,b,eval,grad,numgrad,tc
    real colvector ord,g
    real matrix G,U,L,H,Jj,W,JW,bread,F,ClSc,Sc,V,JJ,info,Btrans
    real scalar val,vp,vm,h,i,j,pos,np,nq,nc,iter,conv,grerr
    transmorphic opt
    S=xe_load("easi",demos); b0=st_matrix("XE_b")
    G=xe_gamma(b0,S.nd,"easi")
    symeigensystem((G+G')/2,U,eval)
    eval=(eval:<-st_numscalar("XE_startfloor")):*eval+(eval:>=-st_numscalar("XE_startfloor")):*(-st_numscalar("XE_startfloor"))
    G=U'*diag(eval)*U; L=cholesky(-G); lt=J(1,28,0); pos=0
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) lt[++pos]=L[j,i]
    grad=lt; xec_profile_eval(1,lt,S,val,grad,H); numgrad=grad
    for(i=1;i<=28;i++) {
        h=1e-6*(1+abs(lt[i])); tc=lt; tc[i]=tc[i]+h
        xec_profile_eval(0,tc,S,vp,grad,H); tc[i]=tc[i]-2*h
        xec_profile_eval(0,tc,S,vm,grad,H); numgrad[i]=(vp-vm)/(2*h)
    }
    grerr=max(abs(grad-numgrad)); printf("Profiled EASI gradient max error: %9.3e\n",grerr)
    opt=optimize_init(); optimize_init_evaluator(opt,&xec_profile_eval())
    optimize_init_evaluatortype(opt,"d1"); optimize_init_which(opt,"min")
    optimize_init_argument(opt,1,S); optimize_init_params(opt,lt)
    optimize_init_technique(opt,"bfgs"); optimize_init_conv_maxiter(opt,800)
    optimize_init_conv_ptol(opt,1e-9); optimize_init_conv_vtol(opt,1e-14)
    optimize_init_conv_nrtol(opt,1e-12)
    optimize_init_tracelevel(opt,"value")
    lt=optimize(opt); b=xec_profile_b(lt,S); iter=optimize_result_iterations(opt)
    conv=optimize_result_converged(opt); np=cols(b)
    theta=b[1..np-28],lt
    G=xe_mom(b,S); g=vec(G); nq=rows(g); Jj=J(nq,np,0); Btrans=J(np,np,0)
    for(i=1;i<=np;i++) {
        h=1e-5*(1+abs(theta[i])); tc=theta; tc[i]=tc[i]+h
        JJ=xe_mom(xec_b(tc),S)
        Btrans[,i]=xec_b(tc)'; tc[i]=tc[i]-2*h
        Jj[,i]=(vec(JJ)-vec(xe_mom(xec_b(tc),S)))/(2*h)
        Btrans[,i]=(Btrans[,i]-xec_b(tc)')/(2*h)
    }
    W=I(7)#S.Wz; JW=Jj'*W; bread=invsym(JW*Jj)
    F=xe_cellmom(b,S); ord=order(S.cl,1); info=panelsetup(S.cl[ord],1)
    nc=rows(info); ClSc=J(nc,nq,0)
    for(i=1;i<=7;i++) {
        Sc=S.Z:*F[,i],F[,7+i],F[,14+i]
        ClSc[,(i-1)*(cols(S.Z)+2)+1..i*(cols(S.Z)+2)]=panelsum(Sc[ord,],info)
    }
    V=bread*JW*quadcross(ClSc,ClSc)*JW'*bread*nc/(nc-1)/S.n^2
    V=Btrans*V*Btrans'
    st_matrix("XE_b",b); st_matrix("XE_V",V)
    st_matrix("XE_momfit",G); tc=b:+1e-4*sin(1..np)
    st_matrix("XE_bpert",tc); st_matrix("XE_mompert",xe_mom(tc,S))
    st_numscalar("XE_N",S.n); st_numscalar("XE_cells",rows(S.D))
    st_numscalar("XE_conv",conv); st_numscalar("XE_iters",iter)
    st_numscalar("XE_obj",sum(G:*(S.Wz*G)))
    st_numscalar("XE_graderr",grerr); st_numscalar("XE_rank",rank(Jj))
    st_numscalar("XE_clusters",nc)
    st_numscalar("XE_Gamma_maxeig",max(symeigenvalues(xe_gamma(b,S.nd,"easi"))))
}
end
