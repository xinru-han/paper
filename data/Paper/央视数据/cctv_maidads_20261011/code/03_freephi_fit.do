version 17
clear all
set more off
capture log close _all
args mode
global cfroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
global cf_mode "`mode'"
capture mkdir "$cfroot/outputs/corner_freephi"
log using "$cfroot/logs/03_freephi_fit`mode'.log", text replace
import delimited "$cfroot/outputs/corner/estimated_free_parameters.csv", clear asdouble
mkmat cm_b*, matrix(cf_initial_b)
import delimited "$cfroot/data/household_quarter_8.csv", clear asdouble stringcols(1)
keep if month_count==3 & m>0 & m<.
generate byte train=year<2022
quietly summarize m if train, detail
scalar cf_scale=r(p50)
generate double scaled_m=m/cf_scale
quietly summarize scaled_m, meanonly
scalar cf_mmax=2*r(max)
forvalues j=1/8 {
    quietly summarize p`j', meanonly
    scalar cf_pmin`j'=.8*r(min)
    scalar cf_qmax`j'=cf_mmax/cf_pmin`j'
    generate double purchase`j'=spend`j'>0
}
do "$cfroot/ado/corner_maidads.mata"
do "$cfroot/ado/corner_freephi.mata"
do "$cfroot/ado/corner_freephi_smd.mata"
mata:
void cf_csv(real matrix M, string scalar filename, string rowvector header)
{
    real scalar fh,i
    fh=fopen(st_global("cfroot")+"/outputs/corner_freephi/"+filename+".csv","rw")
    fseek(fh,0,-1); ftruncate(fh)
    fput(fh,invtokens(header,","))
    for (i=1;i<=rows(M);i++) fput(fh,invtokens(strofreal(M[i,],"%21.16g"),","))
    fclose(fh)
}
real matrix cf_Z(real colvector m, real matrix p, real colvector type,
                 real rowvector center, real rowvector scales)
{
    real matrix X
    X=(ln(m),ln(m):^2,ln(p[,1..7]):-(ln(p[,8])*J(1,7,1)))
    return((J(rows(m),1,1),(X:-center):/scales,type:==2,type:==3,type:==4))
}
real matrix cf_metrics(real matrix pred, real matrix Y, real colvector w)
{
    return((sqrt(colsum(w:*(pred[,1..7]-Y[,1..7]):^2)/sum(w)),
        colsum(w:*(pred[,8..15]-Y[,8..15]):^2)/sum(w)))
}
end
preserve
collapse (count) n=m (mean) m scaled_m purchase1 purchase2 purchase3 purchase4 purchase5 purchase6 purchase7 purchase8 w1 w2 w3 w4 w5 w6 w7 w8, by(train)
export delimited "$cfroot/outputs/corner_freephi/full_eligible_sample_moments.csv", replace
restore
mata:
cf_fulltrain=selectindex(st_data(.,"train"):==1)
cf_fullX=(ln(st_data(cf_fulltrain,"scaled_m")),
    ln(st_data(cf_fulltrain,"scaled_m")):^2,
    ln(st_data(cf_fulltrain,("p1","p2","p3","p4","p5","p6","p7"))):-
    (ln(st_data(cf_fulltrain,"p8"))*J(1,7,1)))
st_matrix("cf_center",mean(cf_fullX))
st_matrix("cf_scales",sqrt(diagonal(variance(cf_fullX)))')
end
bysort train province type income_band (scaled_m hh_id tq): generate long stratum_n=_N
bysort train province type income_band (scaled_m hh_id tq): generate long stratum_rank=_n
generate byte support=0
forvalues j=1/8 {
    replace support=1 if stratum_rank==ceil(stratum_n*(`j'-.5)/8)
}
bysort train province type income_band: egen long support_n=total(support)
generate double support_weight=stratum_n/support_n if support
keep if support
sort train province type income_band scaled_m hh_id tq
save "$cfroot/data/corner_freephi_support.dta", replace
preserve
bysort train: egen double represented_household_quarters=total(support_weight)
collapse (count) support_rows=m (mean) represented_household_quarters m scaled_m purchase1 purchase2 purchase3 purchase4 purchase5 purchase6 purchase7 purchase8 w1 w2 w3 w4 w5 w6 w7 w8 [aw=support_weight], by(train)
export delimited "$cfroot/outputs/corner_freephi/support_sample_moments.csv", replace
restore
mata:
void cf_fit()
{
    real colvector train,ix,it,m,type,w,wt
    real matrix P,Y,Z,draw,par,pred,predtest,baseline,starts,fit,domain,probe
    real rowvector b,best,b0,center,scales,qmax,pmin,header
    real scalar s,f,bestf,start,cvg,j,val,elapsed,bench,initialf,bestcvg
    external real scalar cf_watch_active,cf_watch_start,cf_watch_deadline,cf_watch_calls
    external real scalar cf_watch_timeout,cf_watch_invalid,cf_watch_best_value
    external real scalar cf_watch_start_id,cf_watch_limit
    external real rowvector cf_watch_best_b
    transmorphic S
    train=st_data(.,"train"); ix=selectindex(train:==1); it=selectindex(train:==0)
    m=st_data(ix,"scaled_m")
    P=st_data(ix,("p1","p2","p3","p4","p5","p6","p7","p8"))
    type=st_data(ix,"type"); w=st_data(ix,"support_weight")
    wt=st_data(it,"support_weight")
    Y=st_data(ix,("w1","w2","w3","w4","w5","w6","w7",
        "purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8"))
    center=st_matrix("cf_center"); scales=st_matrix("cf_scales")
    Z=cf_Z(m,P,type,center,scales); draw=cm_draws(64,8)
    qmax=J(1,8,.); pmin=qmax
    for (j=1;j<=8;j++) {
        qmax[j]=st_numscalar("cf_qmax"+strofreal(j))
        pmin[j]=st_numscalar("cf_pmin"+strofreal(j))
    }
    domain=((1..8)',pmin',qmax',J(8,1,st_numscalar("cf_mmax")))
    cf_csv(domain,"regularity_domain",("good","minimum_price","maximum_scaled_quantity","maximum_scaled_budget"))
    b0=(st_matrix("cf_initial_b"),J(1,7,0))
    val=cm_logistic(b0[16])
    val=max((.00001,min((.99999,(val-.02)/.96))))
    b0[16]=ln(val/(1-val))
    bench=cf_seconds()
    cf_smd_objective(0,b0,m,P,type,Z,Y,w,draw,qmax,initialf,best,probe)
    bench=cf_seconds()-bench
    cf_csv((rows(ix),rows(it),rows(draw),cols(b0),bench,initialf),"initial_benchmark",
        ("training_support_rows","holdout_support_rows","draws","parameter_count","objective_seconds","initial_objective"))
    printf("8-node/64-draw objective: %g training supports, %g seconds, loss %16.9g\n",rows(ix),bench,initialf)
    if (initialf>=1000 | initialf>=.) _error(3498)
    if (st_global("cf_mode")=="benchmark") return
    best=b0; bestf=initialf; bestcvg=0
    starts=J(0,7,.)
    for (start=1;start<=2;start++) {
        if (st_global("cf_mode")=="start1" & start!=1) continue
        if (st_global("cf_mode")=="start2" & start!=2) continue
        b=b0
        if (start==2) b[|21\27|]=(.3,-.3,.2,-.2,.1,-.1,.15)
        S=optimize_init()
        optimize_init_evaluator(S,&cf_smd_objective())
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
        optimize_init_argument(S,8,qmax)
        optimize_init_conv_maxiter(S,450)
        optimize_init_conv_ptol(S,1e-4)
        optimize_init_conv_vtol(S,1e-6)
        optimize_init_tracelevel(S,"value")
        cf_watch_active=1; cf_watch_start=cf_seconds(); cf_watch_deadline=1200
        cf_watch_calls=0; cf_watch_timeout=0; cf_watch_invalid=0
        cf_watch_start_id=start; cf_watch_best_value=.; cf_watch_best_b=b
        s=_optimize(S)
        cf_watch_active=0
        b=cf_watch_best_b; f=cf_watch_best_value
        cvg=optimize_result_converged(S)*(1-cf_watch_timeout)
        cf_checkpoint(b,f,cvg)
        starts=starts\(start,f,cvg,cf_watch_timeout,cf_watch_calls,cf_watch_invalid,
            cf_seconds()-cf_watch_start)
        cf_csv(starts,"optimizer_starts_status",
            ("start","objective","converged","timeout","evaluations","invalid_candidates","elapsed_seconds"))
        printf("Freephi start %g: objective %16.9g, converged %g, timeout %g\n",start,f,cvg,cf_watch_timeout)
        if (f<bestf) {
            best=b
            bestf=f
            bestcvg=cvg
        }
    }
    par=cf_unpack(best,qmax)
    cf_csv(best,"estimated_free_parameters","b":+strofreal(1..cols(best)))
    cf_csv(par,"estimated_parameters","p":+strofreal(1..8))
    cf_csv((st_numscalar("cf_scale"),rows(ix),rows(it),rows(draw),cols(best),bestf,bestcvg,0,
        par[6,1],par[6,2],cf_ratio_span(par[1,],par[2,])),"fit_status",
        ("budget_scale","training_support_rows","holdout_support_rows","draws","parameter_count",
        "objective","converged","full_sample_fit","Hcap","domain_log_span","fitted_H"))
    pred=cf_predict_vector(best,m,P,type,cm_draws(256,8),qmax)
    predtest=cf_predict_vector(best,st_data(it,"scaled_m"),
        st_data(it,("p1","p2","p3","p4","p5","p6","p7","p8")),
        st_data(it,"type"),cm_draws(256,8),qmax)
    if (hasmissing(pred) | hasmissing(predtest)) _error(3498)
    cf_csv((colsum(w:*Y)/sum(w))\(colsum(w:*pred)/sum(w)),"training_fit",
        ("share":+strofreal(1..7),"positive":+strofreal(1..8)))
    Y=st_data(it,("w1","w2","w3","w4","w5","w6","w7",
        "purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8"))
    cf_csv((colsum(wt:*Y)/sum(wt))\(colsum(wt:*predtest)/sum(wt)),"holdout_fit",
        ("share":+strofreal(1..7),"positive":+strofreal(1..8)))
    baseline=J(rows(it),1,1)*colsum(w:*st_data(ix,("w1","w2","w3","w4","w5","w6","w7",
        "purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8")))/sum(w)
    cf_csv((1,cf_metrics(pred,st_data(ix,("w1","w2","w3","w4","w5","w6","w7",
        "purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8")),w))\
        (0,cf_metrics(predtest,Y,wt))\(-1,cf_metrics(baseline,Y,wt)),"point_prediction_metrics",
        ("sample","share_rmse":+strofreal(1..7),"participation_brier":+strofreal(1..8)))
    fit=J(0,3,.)
    for (j=1;j<=4;j++) {
        val=cf_Fu_uniform_bound(qmax,par[1,],par[2,],exp(par[5,4+j])*par[3,],par[5,1])
        fit=fit\(j,val,val<-.1)
    }
    cf_csv(fit,"regularity_certificate",("family_type","Fu_uniform_upper_bound","margin_certified"))
}
cf_fit()
end
display "FREEPHI_FIT_PROGRAM_FINISHED"
log close
