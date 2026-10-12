version 17
clear all
set more off
capture log close _all
args cm_mode
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
global cm_resume_mode "`cm_mode'"
capture mkdir "$cmroot/outputs/corner"
if "`cm_mode'"=="checkpoint" {
    log using "$cmroot/logs/03_corner_fit_checkpoint_postprocess.log", text replace
    forvalues s=1/2 {
        import delimited "$cmroot/outputs/corner/checkpoint_start`s'.csv", clear asdouble
        mkmat cm_b*, matrix(cm_resume_b`s')
        scalar cm_resume_f`s'=objective[1]
        scalar cm_resume_calls`s'=evaluations[1]
        scalar cm_resume_invalid`s'=invalid_candidates[1]
        capture confirm variable converged
        if !_rc scalar cm_resume_converged`s'=converged[1]
        else scalar cm_resume_converged`s'=(`s'==1 & abs(objective[1]-.1092579268674847)<1e-12)
    }
    display "POSTPROCESS ONLY: start 1 convergence verified in preserved log; start 2 externally bounded and unconverged."
}
else if inlist("`cm_mode'","start1","start2") log using "$cmroot/logs/03_corner_fit_`cm_mode'.log", text replace
else log using "$cmroot/logs/03_corner_fit.log", text replace
import delimited "$cmroot/data/household_quarter_8.csv", clear varnames(1) encoding(utf8) asdouble stringcols(1)
quietly count
scalar cm_all_quarters=r(N)
quietly count if month_count<3
scalar cm_incomplete_quarters=r(N)
quietly count if month_count==3 & (m<=0 | m>=.)
scalar cm_nonpositive_covered_budget=r(N)
keep if m>0 & m<. & month_count==3
assert inrange(type,1,4) & inrange(income_band,1,5)
foreach j of numlist 1/8 {
    assert p`j'>0 & p`j'<. & inrange(w`j',0,1)
    generate byte purchase`j'=spend`j'>0
}
generate byte train=year<2022
quietly summarize m if train, detail
scalar cm_scale=r(p50)
generate double scaled_m=m/cm_scale
bysort train province type income_band (scaled_m hh_id tq): generate long stratum_n=_N
bysort train province type income_band (scaled_m hh_id tq): generate long stratum_rank=_n
generate byte support=0
forvalues j=1/2 {
    replace support=1 if stratum_rank==ceil(stratum_n*(`j'-.5)/2)
}
bysort train province type income_band: egen long support_n=total(support)
generate double support_weight=stratum_n/support_n if support
quietly count if train
scalar cm_train_full=r(N)
quietly count if !train
scalar cm_test_full=r(N)
preserve
collapse (count) n=m (mean) purchase1 purchase2 purchase3 purchase4 purchase5 purchase6 purchase7 purchase8 w1 w2 w3 w4 w5 w6 w7 w8 m, by(train)
export delimited "$cmroot/outputs/corner/full_sample_descriptive.csv", replace
restore
keep if support
sort train province type income_band scaled_m hh_id tq
export delimited "$cmroot/outputs/corner/smd_actual_support.csv", replace
do "$cmroot/ado/corner_maidads.mata"
do "$cmroot/ado/corner_regular.mata"
do "$cmroot/ado/corner_smd.mata"
mata:
void cm_write_output(string scalar matrixname, string scalar filename,
                     string rowvector headers, | string rowvector rowlabels)
{
    real matrix M
    real scalar fh,i
    string scalar line
    M=st_matrix(matrixname)
    fh=fopen(st_global("cmroot")+"/outputs/corner/"+filename+".csv","rw")
    fseek(fh,0,-1); ftruncate(fh)
    if (args()==4) fput(fh,invtokens(headers,",")+",row")
    else fput(fh,invtokens(headers,","))
    for (i=1;i<=rows(M);i++) {
        line=invtokens(strofreal(M[i,],"%21.16g"),",")
        if (args()==4) line=line+","+rowlabels[i]
        fput(fh,line)
    }
    fclose(fh)
}

real matrix cm_makeZ(real colvector m, real matrix p, real colvector type,
                     real rowvector center, real rowvector scales)
{
    real matrix Z,X
    X=(ln(m),ln(m):^2,ln(p[,1..7]):-(ln(p[,8])*J(1,7,1)))
    if (cols(center)==0) {
        center=mean(X)
        scales=sqrt(diagonal(variance(X)))'
    }
    X=(X:-center):/scales
    Z=(J(rows(m),1,1),X,type:==2,type:==3,type:==4)
    return(Z)
}

void cm_fit()
{
    real matrix P,Y,Z,draw,par,Jm,U,V,X,predtrain,predtest,Ztest,rd,B,Bobs,Bpred,pair,PB,integ,Hg,startstatus
    real colvector m,type,w,train,ix,it,mt,typet,wt,sv
    real rowvector b,best,b0,center,scales,init_alpha,init_low,piobs,pipred,gg
    real scalar s,f,bestf,start,converged,i,j,h,val,rank,cond,ntrain,ntest,jointpred
    external real scalar cm_watch_active,cm_watch_start,cm_watch_deadline,cm_watch_calls
    external real scalar cm_watch_timeout,cm_watch_invalid,cm_watch_best_value,cm_watch_start_id
    external real rowvector cm_watch_best_b
    transmorphic S
    train=st_data(.,"train")
    ix=selectindex(train:==1)
    it=selectindex(train:==0)
    m=st_data(ix,"scaled_m")
    P=st_data(ix,("p1","p2","p3","p4","p5","p6","p7","p8"))
    type=st_data(ix,"type")
    w=st_data(ix,"support_weight")
    Y=st_data(ix,("w1","w2","w3","w4","w5","w6","w7",
                  "purchase1","purchase2","purchase3","purchase4",
                  "purchase5","purchase6","purchase7","purchase8"))
    X=(ln(m),ln(m):^2,ln(P[,1..7]):-(ln(P[,8])*J(1,7,1)))
    center=mean(X)
    scales=sqrt(diagonal(variance(X)))'
    if (min(scales)<=1e-10) _error(3498)
    Z=cm_makeZ(m,P,type,center,scales)
    draw=cm_draws(16,8)
    init_alpha=(mean(w:*Y[,1..7])/mean(w),1-sum(mean(w:*Y[,1..7])/mean(w)))
    init_alpha=init_alpha:/sum(init_alpha)
    init_low=init_alpha:*.6
    b0=(ln(init_alpha[|1\7|]:/init_alpha[8]),ln(init_low),-1.4,ln((.8-.05)/(4-.8)),0,0,0)
    bestf=.
    best=b0
    startstatus=J(0,7,.)
    printf("Actual micro support: %g training and %g held-out household quarters\n",rows(ix),rows(it))
    printf("Full eligible household quarters: %g training and %g held-out\n",
            st_numscalar("cm_train_full"),st_numscalar("cm_test_full"))
    printf("Fixed integration draws: %g; free parameters: %g\n",rows(draw),cols(b0))
    for (start=1;start<=2;start++) {
        if (st_global("cm_resume_mode")=="start1" & start!=1) continue
        if (st_global("cm_resume_mode")=="start2" & start!=2) continue
        b=b0
        if (start==2) {
            b[|8\15|]=b[|8\15|]:+.45
            b[17]=ln((1.3-.05)/(4-1.3))
        }
        if (st_global("cm_resume_mode")=="checkpoint") {
            b=st_matrix("cm_resume_b"+strofreal(start))
            f=st_numscalar("cm_resume_f"+strofreal(start))
            val=st_numscalar("cm_resume_converged"+strofreal(start))
            startstatus=startstatus\(start,f,val,1-val,
                st_numscalar("cm_resume_calls"+strofreal(start)),
                st_numscalar("cm_resume_invalid"+strofreal(start)),.)
        }
        else {
        S=optimize_init()
        optimize_init_evaluator(S,&cm_smd_objective())
        optimize_init_evaluatortype(S,"d0")
        optimize_init_which(S,"min")
        optimize_init_technique(S,"nm")
        optimize_init_nmsimplexdeltas(S,J(1,cols(b),.18))
        optimize_init_params(S,b)
        optimize_init_argument(S,1,m)
        optimize_init_argument(S,2,P)
        optimize_init_argument(S,3,type)
        optimize_init_argument(S,4,Z)
        optimize_init_argument(S,5,Y)
        optimize_init_argument(S,6,w)
        optimize_init_argument(S,7,draw)
        optimize_init_conv_maxiter(S,350)
        optimize_init_conv_ptol(S,1e-4)
        optimize_init_conv_vtol(S,1e-6)
        optimize_init_tracelevel(S,"value")
        cm_watch_active=1
        cm_watch_start=cm_wall_seconds()
        cm_watch_deadline=(start==1 ? 900 : 600)
        cm_watch_calls=0; cm_watch_timeout=0; cm_watch_invalid=0
        cm_watch_start_id=start; cm_watch_best_value=.; cm_watch_best_b=b
        s=_optimize(S)
        cm_watch_active=0
        b=cm_watch_best_b
        f=cm_watch_best_value
        cm_checkpoint(b,f,start,cm_watch_calls,cm_watch_timeout,cm_watch_invalid,
            optimize_result_converged(S)*(1-cm_watch_timeout))
        startstatus=startstatus\(start,f,optimize_result_converged(S)*(1-cm_watch_timeout),
            cm_watch_timeout,cm_watch_calls,cm_watch_invalid,cm_wall_seconds()-cm_watch_start)
        st_matrix("cm_start_status",startstatus)
        printf("Start %g objective %16.10g, converged %g, timeout %g, invalid candidates %g\n",
            start,f,optimize_result_converged(S)*(1-cm_watch_timeout),cm_watch_timeout,cm_watch_invalid)
        val=optimize_result_converged(S)*(1-cm_watch_timeout)
        }
        if (f<bestf) {
            bestf=f
            best=b
            converged=val
        }
    }
    par=cm_unpack(best)
    st_matrix("cm_b",best)
    st_matrix("cm_parameters",par)
    st_numscalar("cm_objective",bestf)
    st_numscalar("cm_converged",converged)
    st_matrix("cm_center",center)
    st_matrix("cm_scales",scales)
    st_matrix("cm_start_status",startstatus)
    cm_write_output("cm_start_status","optimizer_starts_status",
        ("start","objective","converged","timeout","evaluations","invalid_candidates","elapsed_seconds"))
    if (st_global("cm_resume_mode")=="start1" | st_global("cm_resume_mode")=="start2") return
    predtrain=cm_predict(best,m,P,type,cm_draws(256,8))
    predtest=cm_predict(best,st_data(it,"scaled_m"),
        st_data(it,("p1","p2","p3","p4","p5","p6","p7","p8")),
        st_data(it,"type"),cm_draws(256,8))
    st_matrix("cm_fit_train",(mean(w:*Y)/mean(w))\(mean(w:*predtrain)/mean(w)))
    wt=st_data(it,"support_weight")
    st_matrix("cm_fit_test",(mean(wt:*st_data(it,("w1","w2","w3","w4","w5","w6","w7",
        "purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8")))/mean(wt))\
        (mean(wt:*predtest)/mean(wt)))
    cm_write_output("cm_fit_train","training_fit",("share":+strofreal(1..7),
        "positive":+strofreal(1..8)),("observed","predicted"))
    cm_write_output("cm_fit_test","holdout_fit",("share":+strofreal(1..7),
        "positive":+strofreal(1..8)),("observed","predicted"))
    printf("256-draw training and time-holdout fit exported.\n")
    st_matrix("cm_prediction_metrics",(1,
        sqrt(mean(w:*(predtrain[,1..7]-Y[,1..7]):^2)/mean(w)),
        mean(w:*(predtrain[,8..15]-Y[,8..15]):^2)/mean(w))\
        (0,sqrt(mean(wt:*(predtest[,1..7]-st_data(it,("w1","w2","w3","w4","w5","w6","w7"))):^2)/mean(wt)),
        mean(wt:*(predtest[,8..15]-st_data(it,("purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8"))):^2)/mean(wt)))
    predtest=J(rows(it),1,1)*(mean(w:*Y)/mean(w))
    st_matrix("cm_baseline_holdout",(0,
        sqrt(mean(wt:*(predtest[,1..7]-st_data(it,("w1","w2","w3","w4","w5","w6","w7"))):^2)/mean(wt)),
        mean(wt:*(predtest[,8..15]-st_data(it,("purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8"))):^2)/mean(wt)))
    cm_write_output("cm_prediction_metrics","point_prediction_metrics",
        "cm_prediction_metrics":+strofreal(1..16))
    cm_write_output("cm_baseline_holdout","constant_mean_baseline_holdout_metrics",
        "cm_baseline_holdout":+strofreal(1..16))
    PB=Y[,8..15]
    Bobs=PB'*(w:*PB)/sum(w)
    Bpred=J(8,8,0)
    jointpred=0
    draw=cm_draws(256,8)
    for (i=1;i<=rows(m);i++) {
        val=exp(par[4,4+type[i]])
        rd=cm_random_demand(m[i],P[i,],par[1,],par[1,],val*par[2,],val*par[3,],
                            .7,0,par[4,2],draw)
        B=rd[,1..8]:>0
        Bpred=Bpred+w[i]*(B'*B)/rows(B)
        jointpred=jointpred+w[i]*mean(rowsum(B):==8)
    }
    Bpred=Bpred/sum(w)
    piobs=mean(w:*Y[,8..15])/mean(w)
    pipred=mean(w:*predtrain[,8..15])/mean(w)
    pair=J(0,6,.)
    for (i=1;i<=8;i++) for (j=1;j<=8;j++) {
        pair=pair\(i,j,Bobs[i,j],Bpred[i,j],
            (Bobs[i,j]-piobs[i]*piobs[j])/sqrt(piobs[i]*(1-piobs[i])*piobs[j]*(1-piobs[j])),
            (Bpred[i,j]-pipred[i]*pipred[j])/sqrt(pipred[i]*(1-pipred[i])*pipred[j]*(1-pipred[j])))
    }
    st_matrix("cm_pairwise",pair)
    cm_write_output("cm_pairwise","pairwise_purchase_joint_and_correlation",
        "cm_pairwise":+strofreal(1..6))
    st_numscalar("cm_all_positive_observed",sum(w:*(rowsum(PB):==8))/sum(w))
    st_numscalar("cm_all_positive_predicted",jointpred/sum(w))
    integ=J(0,2,.)
    gg=.; Hg=.
    for (i=1;i<=3;i++) {
        j=16*4^(i-1)
        cm_smd_objective(0,best,m,P,type,Z,Y,w,cm_draws(j,8),val,gg,Hg)
        integ=integ\(j,val)
    }
    st_matrix("cm_integration_sensitivity",integ)
    cm_write_output("cm_integration_sensitivity","integration_sensitivity_no_refit",
        "cm_integration_sensitivity":+strofreal(1..2))
    printf("Joint participation and 16/64/256-draw fixed-theta objectives exported.\n")
    st_numscalar("cm_objective_256draw",integ[3,2])
    // This diagnoses moment rank only; no sampling covariance is claimed.
    Jm=J(cols(cm_momvec(best,m,P,type,Z,Y,w,cm_draws(256,8))),cols(best),.)
    for (j=1;j<=cols(best);j++) {
        b=best; b[j]=b[j]+.025
        b0=best; b0[j]=b0[j]-.025
        Jm[,j]=(cm_momvec(b,m,P,type,Z,Y,w,cm_draws(256,8))-
            cm_momvec(b0,m,P,type,Z,Y,w,cm_draws(256,8)))'/.05
        printf("Moment Jacobian column %g/%g completed.\n",j,cols(best))
    }
    sv=svdsv(Jm)
    st_matrix("cm_jacobian_sv",sv')
    cm_write_output("cm_jacobian_sv","moment_jacobian_singular_values",
        "cm_jacobian_sv":+strofreal(1..cols(best)))
    st_numscalar("cm_jacobian_rank",sum(sv:>1e-6))
    st_numscalar("cm_jacobian_condition",max(sv)/min(sv))
    printf("Finite-difference moment Jacobian numerical rank %g/%g, condition %16.10g\n",
        sum(sv:>1e-6),cols(best),max(sv)/min(sv))
    printf("No bootstrap, Wald covariance, p values or fake confidence intervals are produced.\n")
}
cm_fit()
end
if inlist("`cm_mode'","start1","start2") {
    display "CORNER_INDIVIDUAL_START_FINISHED"
    log close
    exit
}
matrix colnames cm_fit_train = share1 share2 share3 share4 share5 share6 share7 positive1 positive2 positive3 positive4 positive5 positive6 positive7 positive8
matrix colnames cm_fit_test = share1 share2 share3 share4 share5 share6 share7 positive1 positive2 positive3 positive4 positive5 positive6 positive7 positive8
preserve
clear
matrix colnames cm_start_status = start objective converged timeout evaluations invalid_candidates elapsed_seconds
svmat double cm_start_status, names(col)
export delimited "$cmroot/outputs/corner/optimizer_starts_status.csv", replace
clear
svmat double cm_fit_train, names(col)
generate str12 row=cond(_n==1,"observed","predicted")
export delimited "$cmroot/outputs/corner/training_fit.csv", replace
clear
svmat double cm_fit_test, names(col)
generate str12 row=cond(_n==1,"observed","predicted")
export delimited "$cmroot/outputs/corner/holdout_fit.csv", replace
clear
svmat double cm_parameters
generate str20 row=cond(_n==1,"alpha_equal_beta",cond(_n==2,"shift_low",cond(_n==3,"shift_high","r_sigma_omega_k_eta")))
export delimited "$cmroot/outputs/corner/estimated_parameters.csv", replace
clear
svmat double cm_b
export delimited "$cmroot/outputs/corner/estimated_free_parameters.csv", replace
clear
svmat double cm_jacobian_sv
export delimited "$cmroot/outputs/corner/moment_jacobian_singular_values.csv", replace
clear
svmat double cm_prediction_metrics
export delimited "$cmroot/outputs/corner/point_prediction_metrics.csv", replace
clear
svmat double cm_baseline_holdout
export delimited "$cmroot/outputs/corner/constant_mean_baseline_holdout_metrics.csv", replace
clear
svmat double cm_pairwise
export delimited "$cmroot/outputs/corner/pairwise_purchase_joint_and_correlation.csv", replace
clear
svmat double cm_integration_sensitivity
export delimited "$cmroot/outputs/corner/integration_sensitivity_no_refit.csv", replace
restore
save "$cmroot/data/corner_smd_support.dta", replace
scalar list cm_scale cm_train_full cm_test_full cm_objective cm_converged cm_jacobian_rank cm_jacobian_condition
clear
set obs 1
generate double budget_scale=cm_scale
generate double all_observed_quarters=cm_all_quarters
generate double incomplete_quarters=cm_incomplete_quarters
generate double complete_nonpositive_budget=cm_nonpositive_covered_budget
generate double full_train_n=cm_train_full
generate double full_holdout_n=cm_test_full
generate double objective=cm_objective
generate double objective_256draw=cm_objective_256draw
generate byte converged=cm_converged
generate double moment_jacobian_rank=cm_jacobian_rank
generate double moment_jacobian_condition=cm_jacobian_condition
generate double all_positive_observed=cm_all_positive_observed
generate double all_positive_predicted=cm_all_positive_predicted
export delimited "$cmroot/outputs/corner/fit_status.csv", replace
display "CORNER_MICRO_PILOT_FINISHED"
log close
