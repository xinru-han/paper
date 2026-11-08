*! CCTV approximate SY-EASI reproduction. Stata/Mata only, 10oct2026
program define cctv_fit, eclass
    version 17
    syntax [if] [in], [ORDER(integer 2) OMIT(integer 3) AZ YSQUARE NOSY NOPCYC EXTRAS(varlist numeric) FAST REUSE PRECOMPUTED]
    if "`reuse'"!="" {
        tempname oldfs
        matrix `oldfs'=e(firststage_stats)
        forvalues i=1/8 {
            matrix cv_syb`i'=e(syb`i')
            local oldz`i' "`e(syvars`i')'"
        }
    }
    marksample touse
    local eq ""
    local rel ""
    local mn ""
    forvalues i=1/8 {
        capture drop _cv_r`i' _cv_mn`i'
        gen double _cv_r`i'=lp`i'-lp`omit'
        bysort hh_id: egen double _cv_mn`i'=mean(_cv_r`i')
        if `i'!=`omit' {
            local eq "`eq' `i'"
            local rel "`rel' _cv_r`i'"
            local mn "`mn' _cv_mn`i'"
        }
    }
    capture drop _cv_const
    gen byte _cv_const=1
    local powers "y"
    if `order'>1 {
        forvalues h=2/`order' {
            capture drop _cv_y`h'
            gen double _cv_y`h'=y^`h'
            local powers "`powers' _cv_y`h'"
        }
    }
    local controls "$DEMO $MACRO $TIME mean_y_hh `mn' `extras'"
    local base "_cv_const `powers' `controls'"
    local pbase "y `rel' $DEMO $MACRO $TIME mean_y_hh `mn'"
    tempname fs
    matrix `fs'=J(8,8,.)
    if "`precomputed'"!="" matrix `fs'=CV_FS
    if "`reuse'"!="" matrix `fs'=`oldfs'
    forvalues i=1/8 {
        if "`reuse'`precomputed'"=="" capture drop _cv_Phi`i' _cv_pdf`i' _cv_xb`i'
        if "`precomputed'"!="" {
            local zvars`i' "`pbase' pcyc_bought_lag1_`i' pcyc_recency_`i' pcyc_nohist_`i' _cv_const"
        }
        else if "`reuse'"!="" {
            local zvars`i' "`oldz`i''"
        }
        else if "`nosy'"!="" {
            gen double _cv_Phi`i'=1
            gen double _cv_pdf`i'=0
            gen double _cv_xb`i'=0
        }
        else {
            local pc ""
            if "`nopcyc'"=="" local pc "pcyc_bought_lag1_`i' pcyc_recency_`i' pcyc_nohist_`i'"
            quietly probit pos`i' `pbase' `pc' if `touse', iterate(100)
            if !e(converged) error 430
            matrix cv_syb`i'=e(b)
            local zvars`i' "`pbase' `pc' _cv_const"
            predict double _cv_xb`i' if `touse', xb
            gen double _cv_Phi`i'=normal(_cv_xb`i') if `touse'
            gen double _cv_pdf`i'=normalden(_cv_xb`i') if `touse'
            quietly summarize pos`i' if `touse'
            matrix `fs'[`i',1]=r(mean)
            quietly summarize _cv_Phi`i' if `touse'
            matrix `fs'[`i',2]=r(mean)
            tempvar bri
            gen double `bri'=(pos`i'-_cv_Phi`i')^2 if `touse'
            quietly summarize `bri' if `touse'
            matrix `fs'[`i',3]=r(mean)
            matrix `fs'[`i',4]=e(r2_p)
            matrix `fs'[`i',5]=e(converged)
            matrix `fs'[`i',6]=e(N)
            matrix `fs'[`i',7]=e(ll)
            matrix `fs'[`i',8]=e(ll_0)
            drop `bri'
        }
        local zlist`i' "`zvars`i''"
    }
    local useaz=("`az'"!="")
    local usey2p=("`ysquare'"!="")
    local usesy=("`nosy'"=="")
    local usefast=("`fast'"!="")
    local nb: word count `base'
    local np=28
    local p=`nb'*7+56+84*`useaz'+7*`usesy'
    local pnames ""
    foreach i of local eq {
        foreach v of local base {
            local vn=subinstr("`v'","_cv_","",.)
            local pnames "`pnames' q`i'_`vn'"
        }
    }
    foreach prefix in A C {
        forvalues a=1/7 {
            forvalues b=`a'/7 {
                local i: word `a' of `eq'
                local j: word `b' of `eq'
                local pnames "`pnames' `prefix'`i'_`j'"
            }
        }
    }
    if `useaz' {
        forvalues d=1/3 {
            forvalues a=1/7 {
                forvalues b=`a'/7 {
                    local i: word `a' of `eq'
                    local j: word `b' of `eq'
                    local pnames "`pnames' Z`d'_`i'_`j'"
                }
            }
        }
    }
    if `usesy' {
        foreach i of local eq {
            local pnames "`pnames' sigma`i'"
        }
    }
    tempname b V Vhh Vnaive Sigma scores
    forvalues i=1/8 {
        global CV_Z`i' "`zlist`i''"
    }
    mata: cv_estimate("`touse'","`eq'","`base'","`rel'",`order',`useaz',`usey2p',`usesy',`usefast',"`b'","`V'","`Vhh'","`Vnaive'","`Sigma'","`scores'")
    matrix colnames `b'=`pnames'
    foreach m in V Vhh Vnaive {
        matrix colnames ``m''=`pnames'
        matrix rownames ``m''=`pnames'
    }
    ereturn post `b' `V', esample(`touse')
    ereturn matrix V_hh=`Vhh'
    ereturn matrix V_naive=`Vnaive'
    ereturn matrix Sigma=`Sigma'
    ereturn matrix influence_province=`scores'
    ereturn matrix firststage_stats=`fs'
    ereturn local eq "`eq'"
    ereturn local base "`base'"
    ereturn local rel "`rel'"
    ereturn local controls "`controls'"
    ereturn local pbase "`pbase'"
    ereturn local extras "`extras'"
    ereturn scalar order=`order'
    ereturn scalar omit=`omit'
    ereturn scalar az=`useaz'
    ereturn scalar y2p=`usey2p'
    ereturn scalar sy=`usesy'
    ereturn scalar N=cv_N
    ereturn scalar N_clust=cv_G
    ereturn scalar N_hh=cv_H
    ereturn scalar k=`p'
    ereturn scalar rank=cv_rank
    ereturn scalar adjusted_two_step=(`usesy' & !`usefast')
    forvalues i=1/8 {
        if `usesy' {
            ereturn matrix syb`i'=cv_syb`i', copy
            ereturn local syvars`i' "`zlist`i''"
        }
    }
    ereturn local title "Approximate monthly SY-EASI FGLS"
    ereturn local cmd "cctv_fit"
end

mata:
struct cv_eq {
    real matrix X
    real matrix R
    real rowvector map
}
struct cv_state {
    struct cv_eq vector e
    struct cv_eq vector fs
    real matrix base, rel, Y, Phi, pdf, xb, S, Ainv, beta, E, Gp, Gh
    real colvector idx, prov, hh, y
    real rowvector goods
    real scalar nb, az, y2p, sy, ord, p
}
CV=cv_state()

real matrix cv_groups(real matrix X, real colvector g) {
    real colvector o
    o=order(g,1)
    return(panelsum(X[o,],panelsetup(g[o],1)))
}

void cv_estimate(string scalar sample, string scalar eq, string scalar bases,
string scalar rels, real scalar ord, real scalar az, real scalar y2p,
real scalar sy, real scalar fast, string scalar bn, string scalar vn,
string scalar vhn, string scalar vnn, string scalar sn, string scalar gn) {
    external struct cv_state scalar CV
    real scalar n, nb, p, i, j, a, b, d, it, off, s, k, g, rankA
    real matrix pair, W, T, Q, A, Ai, rhs, c, beta, E, U, sc, GP, GH, PN, HN, Z, H, D, DZ, block, core, PS, PG, HG
    real colvector t, z, v, q, infl, dev, info, prob, den
    real rowvector map, mi, mj
    struct cv_eq vector CP
    string rowvector wv, pv, dv, xv
    CV.idx=selectindex(st_data(.,sample):==1)
    CV.goods=strtoreal(tokens(eq)); n=rows(CV.idx)
    CV.base=st_data(CV.idx,tokens(bases)); CV.rel=st_data(CV.idx,tokens(rels))
    CV.y=st_data(CV.idx,"y"); CV.prov=st_data(CV.idx,"province"); CV.hh=st_data(CV.idx,"hh_id")
    nb=cols(CV.base); p=7*nb+56+84*az+7*sy
    CV.nb=nb; CV.p=p; CV.az=az; CV.y2p=y2p; CV.sy=sy; CV.ord=ord
    CV.e=cv_eq(7); CV.fs=cv_eq(7)
    CV.Y=J(n,7,0); CV.Phi=CV.pdf=CV.xb=J(n,7,0)
    pair=J(7,7,0); k=0
    for(a=1;a<=7;a++) for(b=a;b<=7;b++) {k++;pair[a,b]=pair[b,a]=k;}
    for(i=1;i<=7;i++) {
        g=CV.goods[i]
        CV.Y[,i]=st_data(CV.idx,"w"+strofreal(g))
        CV.Phi[,i]=st_data(CV.idx,"_cv_Phi"+strofreal(g))
        CV.pdf[,i]=st_data(CV.idx,"_cv_pdf"+strofreal(g))
        CV.xb[,i]=st_data(CV.idx,"_cv_xb"+strofreal(g))
        t=CV.y; if(y2p) t=t:^2
        Q=(CV.base,CV.rel,CV.rel:*t)
        map=((i-1)*nb:+(1..nb),7*nb:+pair[i,],7*nb+28:+pair[i,])
        if(az) {
            Z=st_data(CV.idx,tokens(st_global("DEMO")))
            for(d=1;d<=3;d++) {
                Q=(Q,CV.rel:*Z[,d]);map=(map,7*nb+56+(d-1)*28:+pair[i,])
            }
        }
        CV.e[i].X=Q:*CV.Phi[,i]
        if(sy) {CV.e[i].X=(CV.e[i].X,CV.pdf[,i]);map=(map,7*nb+56+84*az+i);}
        CV.e[i].map=map
    }
    // Double-precision cross-products, validated against quadcross, are calculated once; every FGLS update uses sufficient statistics.
    CP=cv_eq(49)
    for(i=1;i<=7;i++) {
        CV.e[i].R=cross(CV.e[i].X,CV.Y)
        for(j=i;j<=7;j++) {
            CP[(i-1)*7+j].X=cross(CV.e[i].X,CV.e[j].X)
            if(j!=i) CP[(j-1)*7+i].X=CP[(i-1)*7+j].X'
        }
    }
    W=I(7); beta=J(p,1,0)
    for(it=0;it<=2;it++) {
        A=J(p,p,0); rhs=J(p,1,0)
        for(i=1;i<=7;i++) for(j=1;j<=7;j++) {
            mi=CV.e[i].map; mj=CV.e[j].map
            if(abs(W[i,j])>1e-15) {
                A[mi,mj]=A[mi,mj]+W[i,j]*CP[(i-1)*7+j].X
                rhs[mi]=rhs[mi]+W[i,j]*CV.e[i].R[,j]
            }
        }
        // Scale before inversion; no numerical ridge alters the model.
        den=sqrt(diagonal(A)); Ai=invsym(A:/(den*den')):/(den*den')
        beta=Ai*rhs
        E=J(n,7,0)
        for(i=1;i<=7;i++) E[,i]=CV.Y[,i]-CV.e[i].X*beta[CV.e[i].map]
        CV.S=cross(E,E)/n
        if(it<2) W=invsym(CV.S)
    }
    rankA=rank(A:/(den*den')); if(rankA<p) {errprintf("Design rank %g < %g\n",rankA,p);_error(481);}
    CV.beta=beta;CV.Ainv=Ai;CV.E=E
    U=E*W
    GP=J(rows(uniqrows(sort(CV.prov,1))),p,0)
    GH=J(rows(uniqrows(sort(CV.hh,1))),p,0)
    for(i=1;i<=7;i++) {
        mi=CV.e[i].map
        sc=CV.e[i].X:*U[,i]
        GP[,mi]=GP[,mi]+cv_groups(sc,CV.prov)
        GH[,mi]=GH[,mi]+cv_groups(sc,CV.hh)
    }
    PN=GP*Ai;HN=GH*Ai
    if(sy & !fast) {
        printf("Computing generated-probit adjustment for province and household inference\n")
        for(i=1;i<=7;i++) {
            g=CV.goods[i];mi=CV.e[i].map
            Z=st_data(CV.idx,tokens(st_global("CV_Z"+strofreal(g))))
            prob=CV.Phi[,i];den=prob:*(1:-prob)
            den=rowmax((den,J(n,1,1e-12)))
            H=cross(Z,(CV.pdf[,i]:^2:/den),Z)
            PS=Z:*(CV.pdf[,i]:*(st_data(CV.idx,"pos"+strofreal(g)):-prob):/den)
            PG=cv_groups(PS,CV.prov);HG=cv_groups(PS,CV.hh)
            CV.fs[i].X=PG*invsym(H);CV.fs[i].R=HG*invsym(H)
            D=J(p,cols(Z),0)
            core=CV.e[i].X[,1..cols(CV.e[i].X)-1]:/prob
            D[mi[1..cols(mi)-1],]=cross(core,(CV.pdf[,i]:*U[,i]),Z)
            D[mi[cols(mi)],]=cross((-CV.xb[,i]:*CV.pdf[,i]:*U[,i]),Z)
            infl=core*beta[mi[1..cols(mi)-1]]-CV.xb[,i]*beta[mi[cols(mi)]]
            infl=infl:*CV.pdf[,i]
            for(j=1;j<=7;j++) {
                mj=CV.e[j].map
                D[mj,]=D[mj,]-W[j,i]*cross(CV.e[j].X,infl,Z)
            }
            block=invsym(H)*D'
            GP=GP+PG*block;GH=GH+HG*block
        }
    }
    CV.Gp=GP*Ai; CV.Gh=GH*Ai
    s=rows(GP)/(rows(GP)-1)
    st_matrix(bn,beta');st_matrix(vn,s*cross(CV.Gp,CV.Gp))
    st_matrix(vhn,rows(GH)/(rows(GH)-1)*cross(CV.Gh,CV.Gh))
    st_matrix(vnn,s*cross(PN,PN));st_matrix(sn,CV.S);st_matrix(gn,CV.Gp)
    st_numscalar("cv_N",n);st_numscalar("cv_G",rows(GP));st_numscalar("cv_H",rows(GH));st_numscalar("cv_rank",rankA)
}
end
