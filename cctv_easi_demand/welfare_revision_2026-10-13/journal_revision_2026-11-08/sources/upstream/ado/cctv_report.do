// Analytic derivatives of raw SY predictions. No clipping or renormalization.
mata:
CV_CACHE_BETA=J(0,1,.)
CV_CACHE_L=CV_CACHE_LY=CV_CACHE_CR=J(0,0,.)
real scalar cv_open(string scalar file) {
    unlink(file)
    return(fopen(file,"w"))
}
struct cv_pred {
    real matrix W, dx, dp
    real matrix L, Ly
    real matrix bprobit
    real matrix pair
}

struct cv_pred scalar cv_pred_all(string scalar margin, real scalar shock) {
    external struct cv_state scalar CV
    external real matrix CV_CACHE_BETA, CV_CACHE_L, CV_CACHE_LY, CV_CACHE_CR
    struct cv_pred scalar R
    real scalar n, i, j, h, d, g, k, nb, off, omit
    real matrix core, lycore, Z, pair
    real rowvector b, map
    real colvector y, t, dt, pj, etax, etap, Ly, Lp, L, sw, syx
    n=rows(CV.idx); nb=CV.nb; y=CV.y;t=y;dt=J(n,1,1)
    if(CV.y2p) {t=y:^2;dt=2*y;}
    R.W=R.dx=R.dp=R.L=R.Ly=J(n,8,0)
    pair=J(7,7,0);k=0
    for(i=1;i<=7;i++) for(j=i;j<=7;j++) {k++;pair[i,j]=pair[j,i]=k;}
    R.pair=pair
    omit=strtoreal(st_global("CV_OMIT"))
    if(rows(CV_CACHE_L)!=n | rows(CV_CACHE_BETA)!=rows(CV.beta)) CV_CACHE_BETA=J(rows(CV.beta),1,.)
    if(any(CV_CACHE_BETA:!=CV.beta)) {
        CV_CACHE_L=CV_CACHE_LY=CV_CACHE_CR=J(n,8,0)
        for(i=1;i<=7;i++) {
            g=CV.goods[i];map=CV.e[i].map
            core=CV.e[i].X[,1..nb+14+21*CV.az]:/CV.Phi[,i]
            CV_CACHE_L[,g]=core*CV.beta[map[1..cols(core)]]
            Ly=J(n,1,0)
            for(h=1;h<=CV.ord;h++) Ly=Ly+h*y:^(h-1)*CV.beta[map[1+h]]
            CV_CACHE_CR[,g]=CV.rel*CV.beta[map[nb+8..nb+14]]
            CV_CACHE_LY[,g]=Ly+CV_CACHE_CR[,g]:*dt
        }
        CV_CACHE_L[,omit]=1:-rowsum(CV_CACHE_L)
        CV_CACHE_LY[,omit]=-rowsum(CV_CACHE_LY)
        CV_CACHE_BETA=CV.beta
    }
    if(shock>0) sw=st_data(CV.idx,"sw"+strofreal(shock))
    for(i=1;i<=7;i++) {
        g=CV.goods[i];map=CV.e[i].map
        L=CV_CACHE_L[,g];Ly=CV_CACHE_LY[,g]
        syx=J(n,1,0);etax=etap=J(n,1,0)
        if(CV.sy) {
            b=st_matrix("cv_syb"+strofreal(g))
            syx=CV.xb[,i]*CV.beta[map[cols(map)]]
            etax=J(n,1,b[1])
        }
        Lp=J(n,1,0)
        if(shock>0) {
            for(j=1;j<=7;j++) {
                pj=J(n,1,(shock==CV.goods[j])-(shock==omit))
                Lp=Lp+pj:*(J(n,1,CV.beta[map[nb+j]])+t*CV.beta[map[nb+7+j]])
                if(CV.az) {
                    Z=st_data(CV.idx,tokens(st_global("DEMO")))
                    for(d=1;d<=3;d++) Lp=Lp+pj:*Z[,d]*CV.beta[map[nb+14+(d-1)*7+j]]
                }
                if(CV.sy) etap=etap+pj*b[1+j]
            }
            Lp=Lp-sw:*Ly
            etap=etap-sw:*etax
        }
        R.L[,g]=L;R.Ly[,g]=Ly
        if(margin=="latent" | !CV.sy) {
            R.W[,g]=L;R.dx[,g]=Ly;R.dp[,g]=Lp
        }
        else {
            R.W[,g]=CV.Phi[,i]:*L+CV.pdf[,i]*CV.beta[map[cols(map)]]
            R.dx[,g]=CV.Phi[,i]:*Ly;R.dp[,g]=CV.Phi[,i]:*Lp
            if(margin=="unconditional") {
                R.dx[,g]=R.dx[,g]+CV.pdf[,i]:*etax:*(L-syx)
                R.dp[,g]=R.dp[,g]+CV.pdf[,i]:*etap:*(L-syx)
            }
        }
    }
    R.W[,omit]=1:-rowsum(R.W)
    R.dx[,omit]=-rowsum(R.dx);R.dp[,omit]=-rowsum(R.dp)
    R.L[,omit]=1:-rowsum(R.L);R.Ly[,omit]=-rowsum(R.Ly)
    return(R)
}

// Delta derivative of aggregate elasticity, with common support held at baseline.
// Aggregate Jacobian without allocating dense zero derivative designs.
real rowvector cv_el_jac(struct cv_pred scalar R, real scalar demand, real scalar shock, real colvector keep) {
    external struct cv_state scalar CV
    real scalar n,i,g,j,h,d,omit,fsoff,r,p,sign,nb,delta,N,den,sigma,da,dc
    real matrix core,Z,Zd
    real rowvector map,b,DD,DN,dh,nh,dcore,deta,dw,dv
    real colvector a,t,dt,sw,dy,eta,ph,pp,L,Ld,tmp,wt,q
    n=rows(CV.idx);nb=CV.nb;p=CV.p;omit=strtoreal(st_global("CV_OMIT"))
    r=0;if(CV.sy) for(i=1;i<=7;i++) r=r+cols(CV.fs[i].X)
    DD=DN=J(1,p+r,0)
    a=exp(st_data(CV.idx,"lnx")-st_data(CV.idx,"lp"+strofreal(demand))):*keep
    den=cross(a,R.W[,demand])
    if(shock==0) {N=cross(a,R.dx[,demand]);dy=J(n,1,1);sw=J(n,1,0);}
    else {N=cross(a,R.dp[,demand]);sw=st_data(CV.idx,"sw"+strofreal(shock));dy=-sw;}
    t=CV.y;dt=J(n,1,1);if(CV.y2p) {t=t:^2;dt=2*CV.y;}
    fsoff=p
    for(i=1;i<=7;i++) {
        g=CV.goods[i];map=CV.e[i].map;sign=(g==demand)-(demand==omit)
        r=0;if(CV.sy) r=cols(CV.fs[i].X)
        if(sign==0) {fsoff=fsoff+r;continue;}
        core=CV.e[i].X[,1..cols(CV.e[i].X)-CV.sy]:/CV.Phi[,i]
        pp=CV.Phi[,i];ph=CV.pdf[,i];eta=CV.xb[,i]
        wt=a;if(CV.sy) wt=a:*pp
        dcore=J(1,cols(core),0)
        for(h=1;h<=CV.ord;h++) dcore[1+h]=cross(wt,h*CV.y:^(h-1):*dy)
        da=dc=0
        if(CV.az) Zd=st_data(CV.idx,tokens(st_global("DEMO")))
        for(j=1;j<=7;j++) {
            delta=0;if(shock>0) delta=(shock==CV.goods[j])-(shock==omit)
            dcore[nb+j]=delta*sum(wt)
            dcore[nb+7+j]=cross(wt,t*delta+CV.rel[,j]:*dt:*dy)
            da=da+delta*CV.beta[map[nb+j]];dc=dc+delta*CV.beta[map[nb+7+j]]
            if(CV.az) for(d=1;d<=3;d++) dcore[nb+14+(d-1)*7+j]=delta*cross(wt,Zd[,d])
        }
        Ld=R.Ly[,g]:*dy
        if(shock>0) {
            Ld=(Ld:+da)+t*dc
            if(CV.az) for(j=1;j<=7;j++) {
                delta=(shock==CV.goods[j])-(shock==omit)
                for(d=1;d<=3;d++) Ld=Ld+delta*Zd[,d]*CV.beta[map[nb+14+(d-1)*7+j]]
            }
        }
        if(CV.sy) {
            b=st_matrix("cv_syb"+strofreal(g));sigma=CV.beta[map[cols(map)]]
            tmp=dy*b[1]
            for(j=1;j<=7;j++) {
                delta=0;if(shock>0) delta=(shock==CV.goods[j])-(shock==omit)
                tmp=tmp:+delta*b[j+1]
            }
            dw=(cross(wt,core),cross(a,ph))
            dv=(dcore+cross(a:*ph:*tmp,core),cross(a,-eta:*ph:*tmp))
            L=R.L[,g];Z=st_data(CV.idx,tokens(st_global("CV_Z"+strofreal(g))))
            q=a:*ph:*(L-sigma*eta)
            dh=cross(q,Z)
            nh=cross(a:*ph:*(-eta:*tmp:*(L-sigma*eta)-sigma*tmp+Ld),Z)
            deta=J(1,cols(Z),0);deta[1]=cross(q,dy)
            for(j=1;j<=7;j++) {
                delta=0;if(shock>0) delta=(shock==CV.goods[j])-(shock==omit)
                deta[1+j]=delta*sum(q)
            }
            nh=nh+deta
            DD[fsoff:+(1..r)]=DD[fsoff:+(1..r)]+sign*dh
            DN[fsoff:+(1..r)]=DN[fsoff:+(1..r)]+sign*nh
        }
        else {dw=cross(a,core);dv=dcore;}
        DD[map]=DD[map]+sign*dw;DN[map]=DN[map]+sign*dv
        fsoff=fsoff+r
    }
    return((DN*den-N*DD)/(den^2))
}

void cv_report(string scalar outdir, string scalar tag, real scalar B, | real scalar points_only) {
    external struct cv_state scalar CV
    struct cv_pred scalar R, P
    real scalar n, i, j, s, f, fd, fi, fr, N, den, val, ex, mar, hi, sr, G, b, crit, stat, pv, k, t, grp
    real matrix W, DX, JAC, IP, IH, se, webb, boots, ts, ci, obs, summ, coeffI, DPRICE
    real colvector keep, support, a, sw, mask, flags, crits, qt, eigen
    real rowvector evec, mvec, hvec, vals, rawNs
    string rowvector margins, samples, subs
    string scalar margin, sample, sub, line
    n=rows(CV.idx);st_global("CV_OMIT",strofreal(st_numscalar("e(omit)")))
    margins=("unconditional","intensive","latent");samples=("raw_all","common_positive")
    if(!CV.sy) margins=("latent")
    obs=st_data(CV.idx,tokens("w1 w2 w3 w4 w5 w6 w7 w8"))
    fd=cv_open(outdir+"/demand/elasticities_"+tag+".csv")
    fr=cv_open(outdir+"/regularity/prediction_support_"+tag+".csv")
    fput(fd,"model,margin,sample,subgroup,good,shock,type,elasticity,n,support_rate")
    fput(fr,"model,margin,good,mean_share,min_share,max_share,negative_rate,above_one_rate,common_positive_rate")
    subs=("all","low_income","non_low_income","elderly","non_elderly","large_family","small_family","inc1","inc2","inc3","inc4","inc5","xq1","xq2","xq3","xq4","xq5")
    for(f=1;f<=cols(margins);f++) {
        margin=margins[f];R=cv_pred_all(margin,0);rawNs=J(1,cols(subs),.)
        DPRICE=J(n,64,0)
        for(j=1;j<=8;j++) {
            P=cv_pred_all(margin,j)
            DPRICE[,(j-1)*8:+(1..8)]=P.dp
        }
        support=rowmin(R.W):>1e-8;sr=mean(support)
        for(i=1;i<=8;i++) {
            vals=(mean(R.W[,i]),min(R.W[,i]),max(R.W[,i]),mean(R.W[,i]:<=0),mean(R.W[,i]:>1),sr)
            fput(fr,tag+","+margin+","+strofreal(i)+","+invtokens(strofreal(vals,"%20.12g"),","))
        }
        for(s=1;s<=cols(samples);s++) {
            sample=samples[s];keep=J(n,1,1);if(s==2) keep=support
            for(grp=1;grp<=cols(subs);grp++) {
                sub=subs[grp];mask=keep
                if(sub=="low_income") mask=keep:*(st_data(CV.idx,"low_income"):==1)
                if(sub=="non_low_income") mask=keep:*(st_data(CV.idx,"low_income"):==0)
                if(sub=="elderly") mask=keep:*(st_data(CV.idx,"elderly_household"):==1)
                if(sub=="non_elderly") mask=keep:*(st_data(CV.idx,"elderly_household"):==0)
                if(sub=="large_family") mask=keep:*(st_data(CV.idx,"large_family"):==1)
                if(sub=="small_family") mask=keep:*(st_data(CV.idx,"large_family"):==0)
                if(substr(sub,1,3)=="inc") mask=keep:*(st_data(CV.idx,"income_group_order"):==strtoreal(substr(sub,4,.)))
                if(substr(sub,1,2)=="xq") mask=keep:*(st_data(CV.idx,"xquintile"):==strtoreal(substr(sub,3,.)))
                N=sum(mask);if(N==0) continue
                if(s==1) {rawNs[grp]=N;sr=cross(mask,support)/N;}
                else sr=N/rawNs[grp]
                for(i=1;i<=8;i++) {
                    a=exp(st_data(CV.idx,"lnx")-st_data(CV.idx,"lp"+strofreal(i))):*mask
                    den=cross(a,R.W[,i]);ex=1+cross(a,R.dx[,i])/den
                    fput(fd,tag+","+margin+","+sample+","+sub+","+strofreal(i)+",0,expenditure,"+strofreal(ex,"%20.12g")+","+strofreal(N)+","+strofreal(sr))
                }
                if(sub!="all") {
                    // Subgroup own-price results only; full matrices are reported for the whole sample.
                    for(j=1;j<=8;j++) {
                        i=j
                        a=exp(st_data(CV.idx,"lnx")-st_data(CV.idx,"lp"+strofreal(i))):*mask
                        den=cross(a,R.W[,i]);mar=-1+cross(a,DPRICE[,(j-1)*8+i])/den
                        fput(fd,tag+","+margin+","+sample+","+sub+","+strofreal(i)+","+strofreal(j)+",marshallian,"+strofreal(mar,"%20.12g")+","+strofreal(N)+","+strofreal(sr))
                    }
                    continue
                }
                for(j=1;j<=8;j++) {
                    for(i=1;i<=8;i++) {
                        a=exp(st_data(CV.idx,"lnx")-st_data(CV.idx,"lp"+strofreal(i))):*mask
                        den=cross(a,R.W[,i]);ex=1+cross(a,R.dx[,i])/den
                        mar=-(i==j)+cross(a,DPRICE[,(j-1)*8+i])/den
                        hi=mar+ex*cross(mask,obs[,j])/N
                        fput(fd,tag+","+margin+","+sample+",all,"+strofreal(i)+","+strofreal(j)+",marshallian,"+strofreal(mar,"%20.12g")+","+strofreal(N)+","+strofreal(sr))
                        fput(fd,tag+","+margin+","+sample+",all,"+strofreal(i)+","+strofreal(j)+",formal_slutsky,"+strofreal(hi,"%20.12g")+","+strofreal(N)+","+strofreal(sr))
                    }
                }
            }
        }
    }
    fclose(fd);fclose(fr)
    if(args()==4) if(points_only) return
    cv_infer(outdir,tag,B)
}

void cv_infer(string scalar outdir, string scalar tag, real scalar B) {
    external struct cv_state scalar CV
    struct cv_pred scalar R, P
    real scalar n, i, s, fi, den, G, b, crit, stat, pv, k
    real matrix JAC, IP, IH, se, webb, boots, ts, summ
    real colvector keep, a, flags, qt
    real rowvector evec, mvec, vals
    string rowvector samples
    string scalar line
    n=rows(CV.idx)
    samples=("raw_all","common_positive")
    st_global("CV_OMIT",strofreal(st_numscalar("e(omit)")))
    if(CV.sy & cols(CV.fs[1].X)==0) return
    printf("Computing two-step delta and province Webb score-multiplier inference\n")
    IP=CV.Gp;IH=CV.Gh
    if(CV.sy) for(i=1;i<=7;i++) {IP=(IP,CV.fs[i].X);IH=(IH,CV.fs[i].R);}
    fi=cv_open(outdir+"/inference/elasticity_inference_"+tag+".csv")
    fput(fi,"model,sample,good,type,estimate,se_province_two_step,se_household_two_step,score_p,ci_lower,ci_upper,simultaneous_lower,simultaneous_upper,B,clusters")
    for(s=1;s<=2;s++) {
        R=cv_pred_all("unconditional",0);keep=J(n,1,1)
        if(s==2) keep=rowmin(R.W):>1e-8
        JAC=J(16,cols(IP),0);evec=mvec=J(1,8,0)
        for(i=1;i<=8;i++) {
            a=exp(st_data(CV.idx,"lnx")-st_data(CV.idx,"lp"+strofreal(i))):*keep
            den=cross(a,R.W[,i]);evec[i]=1+cross(a,R.dx[,i])/den
            JAC[i,]=cv_el_jac(R,i,0,keep)
            P=cv_pred_all("unconditional",i)
            mvec[i]=-1+cross(a,P.dp[,i])/den
            JAC[8+i,]=cv_el_jac(P,i,i,keep)
        }
        boots=IP*JAC';summ=IH*JAC';G=rows(boots)
        se=sqrt(colsum(boots:^2)*G/(G-1));vals=(evec,mvec)
        webb=(-sqrt(1.5),-1,-sqrt(.5),sqrt(.5),1,sqrt(1.5))
        ts=J(B,16,0)
        rseed(20261010)
        for(b=1;b<=B;b++) {
            flags=webb[ceil(runiform(G,1)*6)]'
            if(rows(flags)!=G) flags=flags'
            ts[b,]=colsum(boots:*flags):/sqrt(colsum(boots:^2:*(flags:^2))*G/(G-1))
        }
        qt=sort(rowmax(abs(ts)),1);crit=qt[ceil(.95*B)]
        for(i=1;i<=16;i++) {
            qt=sort(abs(ts[,i]),1);stat=abs(vals[i]/se[i]);pv=(1+sum(abs(ts[,i]):>=stat))/(B+1)
            k=i;if(i>8) k=i-8
            line=tag+","+samples[s]+","+strofreal(k)+","+(i<=8?"expenditure":"own_price")+","+strofreal(vals[i],"%20.12g")+","+strofreal(se[i],"%20.12g")+","+strofreal(sqrt(cross(summ[,i],summ[,i])*rows(summ)/(rows(summ)-1)),"%20.12g")+","+strofreal(pv)+","+strofreal(vals[i]-qt[ceil(.95*B)]*se[i],"%20.12g")+","+strofreal(vals[i]+qt[ceil(.95*B)]*se[i],"%20.12g")+","+strofreal(vals[i]-crit*se[i],"%20.12g")+","+strofreal(vals[i]+crit*se[i],"%20.12g")+","+strofreal(B)+","+strofreal(G)
            fput(fi,line)
        }
    }
    fclose(fi)
}
end
