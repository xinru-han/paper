mata:
// Counterfactual shares using exact polynomial/price increments, avoiding a
// repeated n-by-regressor design allocation. Controls and Mundlak means stay fixed.
real matrix cv_counter(real scalar shock, real scalar step, string scalar margin) {
    external struct cv_state scalar CV
    external real matrix CV_CACHE_L, CV_CACHE_CR
    struct cv_pred scalar R
    real scalar n,i,j,h,d,g,omit,sigma,delta,da,dc,nb
    real matrix W,Z
    real rowvector map,b
    real colvector y,t,t0,dy,eta,L
    R=cv_pred_all("latent",0)
    n=rows(CV.idx);omit=strtoreal(st_global("CV_OMIT"));nb=CV.nb
    dy=J(n,1,1)
    if(shock>0) dy=-st_data(CV.idx,"sw"+strofreal(shock))
    y=CV.y+step*dy;t=y;t0=CV.y
    if(CV.y2p) {t=t:^2;t0=t0:^2;}
    W=J(n,8,0)
    if(CV.az) Z=st_data(CV.idx,tokens(st_global("DEMO")))
    for(i=1;i<=7;i++) {
        g=CV.goods[i];map=CV.e[i].map;L=CV_CACHE_L[,g]
        for(h=1;h<=CV.ord;h++) L=L+(y:^h-CV.y:^h)*CV.beta[map[1+h]]
        L=L+(t-t0):*CV_CACHE_CR[,g]
        if(shock>0) {
            da=dc=0
            for(j=1;j<=7;j++) {
                delta=(shock==CV.goods[j])-(shock==omit)
                da=da+delta*CV.beta[map[nb+j]];dc=dc+delta*CV.beta[map[nb+7+j]]
                if(CV.az) for(d=1;d<=3;d++) L=L+step*delta*Z[,d]*CV.beta[map[nb+14+(d-1)*7+j]]
            }
            L=(L:+step*da)+step*t*dc
        }
        if(!CV.sy | margin=="latent") W[,g]=L
        else {
            eta=CV.xb[,i]
            if(margin=="unconditional") {
                b=st_matrix("cv_syb"+strofreal(g));eta=eta+step*dy*b[1]
                if(shock>0) for(j=1;j<=7;j++) eta=eta:+step*b[j+1]*((shock==CV.goods[j])-(shock==omit))
            }
            sigma=CV.beta[map[cols(map)]]
            W[,g]=normal(eta):*L+normalden(eta)*sigma
        }
    }
    W[,omit]=1:-rowsum(W)
    return(W)
}

void cv_audit(string scalar outdir,string scalar tag) {
    external struct cv_state scalar CV
    struct cv_pred scalar R,P
    real scalar i,j,h,f,n,fd,fr,step,maxerr,rmse,N,k,b,G,stat,pv,rankv
    real matrix M1,M2,D,SP,S,E,boots,ts,webb,IF, W
    real colvector keep,flags,eig,se,vec
    real rowvector inds,ev
    string rowvector names,terms,margins
    string scalar line
    st_global("CV_OMIT",strofreal(st_numscalar("e(omit)")))
    fd=cv_open(outdir+"/regularity/derivative_validation_"+tag+".csv")
    fput(fd,"model,margin,shock,step,max_abs_derivative_error,rms_derivative_error")
    margins=("unconditional","intensive","latent")
    for(f=1;f<=3;f++) for(j=0;j<=8;j++) {
        R=cv_pred_all(margins[f],j)
        D=R.dp;if(j==0) D=R.dx
        for(h=1;h<=2;h++) {
            step=.001/(10^(h-1))
            M1=cv_counter(j,step,margins[f]);M2=cv_counter(j,-step,margins[f])
            E=(M1-M2)/(2*step)-D
            ev=(max(abs(E)),sqrt(mean(vec(E):^2)))
            fput(fd,tag+","+margins[f]+","+strofreal(j)+","+strofreal(step)+","+invtokens(strofreal(ev,"%20.12g"),","))
        }
    }
    fclose(fd)
    fr=cv_open(outdir+"/regularity/slutsky_diagnostics_"+tag+".csv")
    fput(fr,"model,margin,n,common_positive_rate,mean_matrix_asymmetry,max_eigenvalue_symmetric_part,number_positive_eigenvalues")
    for(f=1;f<=3;f++) {
        R=cv_pred_all(margins[f],0);keep=rowmin(R.W):>1e-8;N=sum(keep)
        S=J(8,8,0)
        for(j=1;j<=8;j++) {
            P=cv_pred_all(margins[f],j)
            for(i=1;i<=8;i++) {
                vec=P.dp[,i]+(R.W[,i]+R.dx[,i]):*R.W[,j]-(i==j)*R.W[,i]
                S[i,j]=quadcross(keep,vec)/N
            }
        }
        symeigensystem((S+S')/2,W,ev)
        fput(fr,tag+","+margins[f]+","+strofreal(N)+","+strofreal(N/rows(keep))+","+strofreal(max(abs(S-S')),"%20.12g")+","+strofreal(max(ev),"%20.12g")+","+strofreal(sum(ev:>1e-8)))
    }
    fclose(fr)
    if(rows(CV.Gp)==0) return
    terms=st_matrixcolstripe("e(b)")[,2]'
    names=("quadratic_Engel","demographic_shifters","CRE_Mundlak","SY_correction","price_A","price_yC","all_price_terms")
    fd=cv_open(outdir+"/inference/specification_tests_"+tag+".csv")
    fput(fd,"model,test,restrictions,province_clusters,vcov_rank,max_t_statistic,score_multiplier_p,B")
    webb=(-sqrt(1.5),-1,-sqrt(.5),sqrt(.5),1,sqrt(1.5));G=rows(CV.Gp);rseed(20261011)
    for(f=1;f<=cols(names);f++) {
        inds=J(1,0,.)
        for(i=1;i<=cols(terms);i++) {
            k=0
            if(names[f]=="quadratic_Engel") k=(substr(terms[i],strlen(terms[i])-2,.)=="_y2")
            if(names[f]=="demographic_shifters") k=(strpos(terms[i],"low_income")>0 | strpos(terms[i],"elderly_household")>0 | strpos(terms[i],"large_family")>0)
            if(names[f]=="CRE_Mundlak") k=(strpos(terms[i],"mean_y_hh")>0 | strpos(terms[i],"_mn")>0)
            if(names[f]=="SY_correction") k=(substr(terms[i],1,5)=="sigma")
            if(names[f]=="price_A") k=(substr(terms[i],1,1)=="A")
            if(names[f]=="price_yC") k=(substr(terms[i],1,1)=="C")
            if(names[f]=="all_price_terms") k=(substr(terms[i],1,1)=="A" | substr(terms[i],1,1)=="C")
            if(k) inds=(inds,i)
        }
        IF=CV.Gp[,inds];se=sqrt(colsum(IF:^2)'*G/(G-1))
        stat=max(abs(CV.beta[inds]:/se));boots=J(999,1,0)
        for(b=1;b<=999;b++) {
            flags=webb[ceil(runiform(G,1)*6)]';if(rows(flags)!=G) flags=flags'
            boots[b]=max(abs(colsum(IF:*flags):/sqrt(colsum(IF:^2:*(flags:^2))*G/(G-1))))
        }
        pv=(1+sum(boots:>=stat))/1000
        rankv=rank(quadcross(IF,IF))
        fput(fd,tag+","+names[f]+","+strofreal(cols(inds))+","+strofreal(G)+","+strofreal(rankv)+","+strofreal(stat,"%20.12g")+","+strofreal(pv)+",999")
    }
    fclose(fd)
}

void cv_own(string scalar file,string scalar tag,real scalar append) {
    external struct cv_state scalar CV
    struct cv_pred scalar R,P
    real scalar fd,i,s,N,den,ex,mar
    real colvector keep,a
    string rowvector samples
    st_global("CV_OMIT",strofreal(st_numscalar("e(omit)")))
    samples=("raw_all","common_positive")
    if(append) fd=fopen(file,"a")
    else fd=cv_open(file)
    if(!append) fput(fd,"variant,sample,good,expenditure,own_price,n,support_rate")
    R=cv_pred_all("unconditional",0)
    for(s=1;s<=2;s++) {
        keep=J(rows(CV.idx),1,1);if(s==2) keep=rowmin(R.W):>1e-8
        N=sum(keep)
        for(i=1;i<=8;i++) {
            a=exp(st_data(CV.idx,"lnx")-st_data(CV.idx,"lp"+strofreal(i))):*keep
            den=quadcross(a,R.W[,i]);ex=1+quadcross(a,R.dx[,i])/den
            P=cv_pred_all("unconditional",i);mar=-1+quadcross(a,P.dp[,i])/den
            fput(fd,tag+","+samples[s]+","+strofreal(i)+","+strofreal(ex,"%20.12g")+","+strofreal(mar,"%20.12g")+","+strofreal(N)+","+strofreal(N/rows(keep),"%20.12g"))
        }
    }
    fclose(fd)
}

void cv_extension_test(string scalar file,string scalar tag,real scalar append) {
    external struct cv_state scalar CV
    real scalar i,b,G,stat,pv,fd,k
    real rowvector inds,webb
    real matrix IF,boots
    real colvector se,flags
    string rowvector terms
    terms=st_matrixcolstripe("e(b)")[,2]';inds=J(1,0,.)
    for(i=1;i<=cols(terms);i++) {
        k=0
        if(tag=="az") k=(substr(terms[i],1,1)=="Z")
        if(tag=="y2p") k=(substr(terms[i],1,1)=="C")
        if(substr(tag,1,5)=="order") k=(strpos(terms[i],"_y"+strofreal(CV.ord))>0)
        if(tag=="cf") k=(strpos(terms[i],"_cf_y")>0)
        if(k) inds=(inds,i)
    }
    IF=CV.Gp[,inds];G=rows(IF);se=sqrt(colsum(IF:^2)'*G/(G-1))
    stat=max(abs(CV.beta[inds]:/se));boots=J(999,1,0)
    webb=(-sqrt(1.5),-1,-sqrt(.5),sqrt(.5),1,sqrt(1.5));rseed(20261012)
    for(b=1;b<=999;b++) {
        flags=webb[ceil(runiform(G,1)*6)]';if(rows(flags)!=G) flags=flags'
        boots[b]=max(abs(colsum(IF:*flags):/sqrt(colsum(IF:^2:*(flags:^2))*G/(G-1))))
    }
    pv=(1+sum(boots:>=stat))/1000
    if(append) fd=fopen(file,"a")
    else fd=cv_open(file)
    if(!append) fput(fd,"variant,restrictions,vcov_rank,max_t_statistic,score_multiplier_p,B,inference_scope")
    fput(fd,tag+","+strofreal(cols(inds))+","+strofreal(rank(quadcross(IF,IF)))+","+strofreal(stat,"%20.12g")+","+strofreal(pv)+",999,conditional generated first-stage controls except main-probit adjustment in CF")
    fclose(fd)
}
end
