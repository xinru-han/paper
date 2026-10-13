version 17
clear all
set more off
capture log close _all
args modeldir
global cfroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
if "`modeldir'"=="" local modeldir "$cfroot/outputs/corner_freephi"
global cfout "`modeldir'"
log using "$cfout/full_holdout.log", text replace
import delimited "$cfout/estimated_free_parameters.csv", clear asdouble
mkmat b*, matrix(cf_holdout_b)
import delimited "$cfout/fit_status.csv", clear asdouble
scalar cf_holdout_scale=budget_scale[1]
scalar cf_holdout_converged=converged[1]
import delimited "$cfout/regularity_domain.csv", clear asdouble
mkmat maximum_scaled_quantity, matrix(cf_holdout_qmax_col)
import delimited "$cfroot/data/household_quarter_8.csv", clear asdouble stringcols(1)
keep if month_count==3 & m>0 & m<.
generate byte train=year<2022
generate double scaled_m=m/cf_holdout_scale
forvalues j=1/8 {
    generate double purchase`j'=spend`j'>0
}
capture confirm numeric variable tq
if !_rc generate byte calendar_quarter=quarter(dofq(tq))
else generate byte calendar_quarter=quarter(dofq(quarterly(tq,"YQ")))
tempfile historical
preserve
keep if train
generate double historical_n=1
collapse (sum) historical_n (mean) w1 w2 w3 w4 w5 w6 w7 purchase1 purchase2 purchase3 purchase4 purchase5 purchase6 purchase7 purchase8, by(province calendar_quarter)
foreach v in w1 w2 w3 w4 w5 w6 w7 purchase1 purchase2 purchase3 purchase4 purchase5 purchase6 purchase7 purchase8 {
    rename `v' historical_`v'
}
save `historical'
restore
merge m:1 province calendar_quarter using `historical', keep(master match) nogen
generate byte historical_unseen=missing(historical_n)
preserve
collapse (count) n=m (mean) m scaled_m purchase1 purchase2 purchase3 purchase4 purchase5 purchase6 purchase7 purchase8 w1 w2 w3 w4 w5 w6 w7 w8, by(train)
export delimited "$cfout/full_eligible_sample_moments.csv", replace
restore
do "$cfroot/ado/corner_maidads.mata"
do "$cfroot/ado/corner_freephi.mata"
mata:
void cf_holdout_csv(real matrix M, string scalar filename, string rowvector header)
{
    real scalar fh,i
    fh=fopen(st_global("cfout")+"/"+filename+".csv","rw")
    fseek(fh,0,-1); ftruncate(fh)
    fput(fh,invtokens(header,","))
    for (i=1;i<=rows(M);i++) fput(fh,invtokens(strofreal(M[i,],"%21.16g"),","))
    fclose(fh)
}
void cf_full_holdout()
{
    real rowvector b,qmax,trainmean,fitmean,obsmean,fitss,basess,histss
    real colvector train,ix,it,m,type
    real matrix P,Y,pred,baseline,histbase,fit
    real scalar offset,last,n,covered,first,nchunk,unseen
    b=st_matrix("cf_holdout_b"); qmax=st_matrix("cf_holdout_qmax_col")'
    train=st_data(.,"train"); ix=selectindex(train:==1); it=selectindex(train:==0)
    trainmean=colsum(st_data(ix,("w1","w2","w3","w4","w5","w6","w7",
        "purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8")))/rows(ix)
    fitmean=J(1,15,0); obsmean=fitmean; fitss=fitmean; basess=fitmean; histss=fitmean
    unseen=sum(st_data(it,"historical_unseen"))
    covered=0; n=rows(it)
    for (offset=1;offset<=n;offset=offset+4096) {
        last=min((n,offset+4095)); nchunk=last-offset+1
        m=st_data(it[|offset\last|],"scaled_m")
        P=st_data(it[|offset\last|],("p1","p2","p3","p4","p5","p6","p7","p8"))
        type=st_data(it[|offset\last|],"type")
        Y=st_data(it[|offset\last|],("w1","w2","w3","w4","w5","w6","w7",
            "purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8"))
        pred=cf_predict_vector(b,m,P,type,cm_draws(256,8),qmax)
        if (hasmissing(pred)) _error(3498)
        baseline=J(nchunk,1,1)*trainmean
        histbase=st_data(it[|offset\last|],("historical_w1","historical_w2","historical_w3","historical_w4","historical_w5","historical_w6","historical_w7",
            "historical_purchase1","historical_purchase2","historical_purchase3","historical_purchase4","historical_purchase5","historical_purchase6","historical_purchase7","historical_purchase8"))
        for (first=1;first<=rows(histbase);first++) if (hasmissing(histbase[first,])) histbase[first,]=trainmean
        covered=covered+nchunk
        fitmean=fitmean+colsum(pred); obsmean=obsmean+colsum(Y)
        fitss=fitss+colsum((pred-Y):^2); basess=basess+colsum((baseline-Y):^2)
        histss=histss+colsum((histbase-Y):^2)
        printf("Full held-out household quarters predicted: %g/%g\n",covered,n)
    }
    fitmean=fitmean/n; obsmean=obsmean/n; fitss=fitss/n; basess=basess/n; histss=histss/n
    cf_holdout_csv((obsmean\fitmean\trainmean),"full_holdout_fit",
        ("share":+strofreal(1..7),"positive":+strofreal(1..8)))
    fit=(0,n,covered,st_numscalar("cf_holdout_converged"),0,
        sqrt(fitss[1..7]),fitss[8..15])\(-1,n,covered,1,0,sqrt(basess[1..7]),basess[8..15])\
        (-2,n,covered,1,unseen,sqrt(histss[1..7]),histss[8..15])
    cf_holdout_csv(fit,"full_holdout_prediction_metrics",
        ("model_code","household_quarters","covered_household_quarters","estimate_converged","historical_fallback_quarters",
        "share_rmse":+strofreal(1..7),"participation_brier":+strofreal(1..8)))
}
cf_full_holdout()
end
display "FREEPHI_FULL_HOLDOUT_FINISHED"
log close
