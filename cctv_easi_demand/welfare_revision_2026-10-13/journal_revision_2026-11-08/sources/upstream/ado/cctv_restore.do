* Reconstruct prediction state from an archived successful cctv_fit estimate.
* The currently loaded data must already carry the matching variant transforms.
capture program drop cctv_restore
program define cctv_restore
    version 17
    local omit=e(omit)
    local ord=e(order)
    forvalues i=1/8 {
        capture drop _cv_r`i' _cv_mn`i'
        gen double _cv_r`i'=lp`i'-lp`omit'
        bysort hh_id: egen double _cv_mn`i'=mean(_cv_r`i')
        if e(sy) matrix cv_syb`i'=e(syb`i')
    }
    capture drop _cv_const
    gen byte _cv_const=1
    if `ord'>1 {
        forvalues h=2/`ord' {
            capture drop _cv_y`h'
            gen double _cv_y`h'=y^`h'
        }
    }
    mata: cv_restore_prediction_state()
end
capture mata: mata drop cv_restore_prediction_state()
mata:
void cv_restore_prediction_state()
{
    external struct cv_state scalar CV
    real scalar n,nb,p,az,sy,i,j,k,g,d
    real matrix pair,Q,Z
    real rowvector map
    real colvector t,eta
    CV.idx=(1::st_nobs())
    CV.goods=strtoreal(tokens(st_global("e(eq)")))
    CV.base=st_data(CV.idx,tokens(st_global("e(base)")))
    CV.rel=st_data(CV.idx,tokens(st_global("e(rel)")))
    CV.y=st_data(CV.idx,"y")
    CV.hh=st_data(CV.idx,"hh_id")
    CV.prov=st_data(CV.idx,"province")
    CV.ord=st_numscalar("e(order)")
    CV.sy=st_numscalar("e(sy)")
    CV.az=st_numscalar("e(az)")
    CV.y2p=st_numscalar("e(y2p)")
    CV.beta=st_matrix("e(b)")'
    CV.S=st_matrix("e(Sigma)")
    n=rows(CV.idx);nb=cols(CV.base);az=CV.az;sy=CV.sy
    CV.nb=nb;CV.p=st_numscalar("e(k)")
    CV.e=cv_eq(7);CV.fs=cv_eq(7)
    CV.Phi=J(n,7,1);CV.pdf=CV.xb=CV.Y=J(n,7,0)
    pair=J(7,7,0);k=0
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) {k++;pair[i,j]=pair[j,i]=k;}
    t=CV.y;if(CV.y2p) t=t:^2
    for(i=1;i<=7;i++) {
        g=CV.goods[i]
        if(sy) {
            Z=st_data(CV.idx,tokens(st_global("e(syvars"+strofreal(g)+")")))
            eta=Z*st_matrix("e(syb"+strofreal(g)+")")'
            CV.xb[,i]=eta;CV.Phi[,i]=normal(eta);CV.pdf[,i]=normalden(eta)
        }
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
        CV.Y[,i]=st_data(CV.idx,"w"+strofreal(g))
    }
    st_global("CV_OMIT",strofreal(st_numscalar("e(omit)")))
}
end
