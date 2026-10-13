version 17
clear all
set more off
set type double
args mode
global cfroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
global cfout "$cfroot/outputs/corner_freephi_refined"
capture mkdir "$cfout"
capture log close _all
log using "$cfout/refine`mode'.log", text replace
import delimited "$cfroot/outputs/corner_freephi/estimated_free_parameters.csv", clear asdouble
mkmat b*, matrix(cf_refine_initial)
import delimited "$cfroot/outputs/corner_freephi/fit_status.csv", clear asdouble
scalar cf_old_scale=budget_scale[1]
import delimited "$cfroot/data/household_quarter_8.csv", clear asdouble stringcols(1)
keep if month_count==3 & m>0 & m<.
generate byte train=year<2022
quietly summarize m if train, detail
scalar cf_scale=r(p50)
assert abs(cf_scale-cf_old_scale)<1e-10
generate double scaled_m=m/cf_scale
quietly summarize scaled_m if train, meanonly
scalar cf_mmax=2*r(max)
forvalues j=1/8 {
    quietly summarize p`j' if train, meanonly
    scalar cf_pmin`j'=.8*r(min)
    scalar cf_qmax`j'=cf_mmax/cf_pmin`j'
    generate double purchase`j'=spend`j'>0
    generate byte domain_violation`j'=scaled_m/p`j'>cf_qmax`j'
}
egen byte domain_violation=rowmax(domain_violation1-domain_violation8)
preserve
collapse (count) rows=m (sum) domain_violations=domain_violation, by(train)
export delimited "$cfout/domain_coverage.csv", replace
restore
mata:
rf_ix=selectindex(st_data(.,"train"):==1)
rf_X=(ln(st_data(rf_ix,"scaled_m")),ln(st_data(rf_ix,"scaled_m")):^2,
    ln(st_data(rf_ix,("p1","p2","p3","p4","p5","p6","p7"))):-
    ln(st_data(rf_ix,"p8"))*J(1,7,1))
st_matrix("rf_center",mean(rf_X))
st_matrix("rf_scales",sqrt(diagonal(variance(rf_X)))')
end
use "$cfroot/data/corner_freephi_support.dta", clear
keep if train
assert year<=2021
do "$cfroot/ado/corner_maidads.mata"
do "$cfroot/ado/corner_freephi.mata"
do "$cfroot/ado/corner_freephi_smd.mata"
mata:
void rf_csv(real matrix M,string scalar name,string rowvector header)
{
    real scalar fh,i
    fh=fopen(st_global("cfout")+"/"+name+".csv","rw")
    fseek(fh,0,-1);ftruncate(fh);fput(fh,invtokens(header,","))
    for(i=1;i<=rows(M);i++) fput(fh,invtokens(strofreal(M[i,],"%21.16g"),","))
    fclose(fh)
}
void rf_refine()
{
    external real scalar cf_watch_active,cf_watch_start,cf_watch_deadline,cf_watch_calls
    external real scalar cf_watch_timeout,cf_watch_invalid,cf_watch_best_value
    external real scalar cf_watch_start_id,cf_watch_limit
    external real rowvector cf_watch_best_b
    real colvector m,type,w
    real matrix p,Y,X,Z,draw,par,ledger,probe,pred,mom
    real rowvector b,trial,qmax,pmin,center,scales,g
    real scalar f,ft,h,j,sgn,sweep,initial,elapsed,accepted,old,calls,nd
    b=st_matrix("cf_refine_initial");qmax=J(1,8,.);pmin=qmax
    for(j=1;j<=8;j++) {
        qmax[j]=st_numscalar("cf_qmax"+strofreal(j))
        pmin[j]=st_numscalar("cf_pmin"+strofreal(j))
    }
    rf_csv(((1..8)',pmin',qmax',J(8,1,st_numscalar("cf_mmax"))),
        "regularity_domain",("good","minimum_price","maximum_scaled_quantity","maximum_scaled_budget"))
    m=st_data(.,"scaled_m");type=st_data(.,"type");w=st_data(.,"support_weight")
    p=st_data(.,("p1","p2","p3","p4","p5","p6","p7","p8"))
    Y=st_data(.,("w1","w2","w3","w4","w5","w6","w7",
        "purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8"))
    center=st_matrix("rf_center");scales=st_matrix("rf_scales")
    X=(ln(m),ln(m):^2,ln(p[,1..7]):-(ln(p[,8])*J(1,7,1)))
    Z=(J(rows(m),1,1),(X:-center):/scales,type:==2,type:==3,type:==4)
    draw=cm_draws(64,8)
    cf_watch_active=0
    cf_smd_objective(0,b,m,p,type,Z,Y,w,draw,qmax,f,g,probe)
    initial=f
    if(f>=1000 | f>=.) _error(3498)
    cf_watch_start=cf_seconds();cf_watch_deadline=900;cf_watch_calls=0
    cf_watch_limit=250;cf_watch_timeout=0;cf_watch_invalid=0;cf_watch_start_id=3
    cf_watch_best_value=f;cf_watch_best_b=b;cf_watch_active=1
    ledger=J(0,7,.)
    for(sweep=1;sweep<=2;sweep++) {
        h=sweep==1 ? .1 : .025
        accepted=0;old=f
        for(j=1;j<=cols(b);j++) {
            for(sgn=-1;sgn<=1;sgn=sgn+2) {
                trial=b;trial[j]=trial[j]+sgn*h
                cf_smd_objective(0,trial,m,p,type,Z,Y,w,draw,qmax,ft,g,probe)
                if(cf_watch_timeout) break
                if(ft<f-1e-10) {
                    b=trial
                    f=ft
                    accepted++
                }
            }
            if(cf_watch_timeout) break
        }
        ledger=ledger\(sweep,h,old,f,accepted,cf_watch_calls,cf_seconds()-cf_watch_start)
        rf_csv(ledger,"coordinate_refinement",("sweep","step","initial_objective",
            "final_objective","accepted_moves","evaluations","elapsed_seconds"))
        printf("Refinement sweep %g: loss %g -> %g, moves %g\n",sweep,old,f,accepted)
        if(cf_watch_timeout) break
    }
    cf_watch_active=0;b=cf_watch_best_b;f=cf_watch_best_value
    cf_checkpoint(b,f,0)
    par=cf_unpack(b,qmax)
    rf_csv(b,"estimated_free_parameters","b":+strofreal(1..cols(b)))
    rf_csv(par,"estimated_parameters","p":+strofreal(1..8))
    rf_csv((st_numscalar("cf_scale"),rows(m),rows(draw),cols(b),initial,f,0,
        cf_watch_timeout,cf_watch_calls,cf_seconds()-cf_watch_start,1,0),"fit_status",
        ("budget_scale","training_support_rows","draws","parameter_count","initial_objective",
        "objective","converged","timeout","evaluations","elapsed_seconds",
        "domain_from_training_only","full_sample_fit"))
    // A finite coordinate search is progress, not a stationarity certificate.
    pred=cf_predict_vector(b,m,p,type,cm_draws(256,8),qmax)
    if(hasmissing(pred)) _error(3498)
    rf_csv((colsum(w:*Y)/sum(w))\(colsum(w:*pred)/sum(w)),"training_fit",
        ("share":+strofreal(1..7),"positive":+strofreal(1..8)))
    ledger=J(0,3,.)
    for(j=1;j<=4;j++) {
        f=cf_Fu_uniform_bound(qmax,par[1,],par[2,],exp(par[5,4+j])*par[3,],par[5,1])
        ledger=ledger\(j,f,f<-.1)
    }
    rf_csv(ledger,"regularity_certificate",("family_type","Fu_uniform_upper_bound","margin_certified"))
    ledger=J(0,2,.)
    for(nd=16;nd<=256;nd=nd*4) {
        cf_smd_objective(0,b,m,p,type,Z,Y,w,cm_draws(nd,8),qmax,f,g,probe)
        ledger=ledger\(nd,f)
    }
    rf_csv(ledger,"integration_objective_sensitivity",("draws","objective_same_parameters"))
}
end
mata: rf_refine()
display "FREEPHI_TRAINING_ONLY_REFINEMENT_FINISHED"
log close
