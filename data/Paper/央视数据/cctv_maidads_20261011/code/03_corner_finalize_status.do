version 17
clear all
set more off
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$cmroot/logs/03_corner_finalize_status.log", text replace
import delimited "$cmroot/outputs/corner/estimated_free_parameters.csv", clear asdouble
mkmat cm_b*, matrix(cm_status_b)
import delimited "$cmroot/outputs/corner/moment_jacobian_singular_values.csv", clear asdouble
mkmat cm_jacobian_sv*, matrix(cm_status_sv)
mata: st_numscalar("cs_rank",sum(st_matrix("cm_status_sv"):>1e-6))
mata: st_numscalar("cs_condition",max(st_matrix("cm_status_sv"))/min(st_matrix("cm_status_sv")))
import delimited "$cmroot/outputs/corner/integration_sensitivity_no_refit.csv", clear asdouble
capture confirm variable objective
if _rc rename cm_integration_sensitivity2 objective
scalar cs_obj16=objective[1]
scalar cs_obj256=objective[3]
import delimited "$cmroot/outputs/corner/optimizer_starts_status.csv", clear asdouble
sort objective
scalar cs_conv=converged[1]
assert abs(objective[1]-cs_obj16)<1e-12
import delimited "$cmroot/data/household_quarter_8.csv", clear asdouble varnames(1) encoding(utf8) stringcols(1)
quietly count
scalar cs_all=r(N)
quietly count if month_count<3
scalar cs_incomplete=r(N)
quietly count if month_count==3 & (m<=0 | m>=.)
scalar cs_nonpositive=r(N)
keep if m>0 & m<. & month_count==3
quietly summarize m if year<2022, detail
scalar cs_scale=r(p50)
quietly count if year<2022
scalar cs_ntrain=r(N)
quietly count if year==2022
scalar cs_ntest=r(N)
generate byte all_positive=spend1>0 & spend2>0 & spend3>0 & spend4>0 & spend5>0 & spend6>0 & spend7>0 & spend8>0
quietly summarize all_positive if year<2022
scalar cs_full_allpositive_train=r(mean)
quietly summarize all_positive if year==2022
scalar cs_full_allpositive_holdout=r(mean)
use "$cmroot/data/corner_smd_support.dta", clear
keep if train
generate byte all_positive=purchase1 & purchase2 & purchase3 & purchase4 & purchase5 & purchase6 & purchase7 & purchase8
quietly summarize all_positive [aw=support_weight]
scalar cs_allpositive_obs=r(mean)
do "$cmroot/ado/corner_maidads.mata"
do "$cmroot/ado/corner_regular.mata"
do "$cmroot/ado/corner_smd.mata"
mata:
void cm_recover_joint()
{
    real matrix par,draw
    real rowvector p,a,low,q
    real colvector m,w,type
    real scalar i,r,mult,prob,total
    par=cm_unpack(st_matrix("cm_status_b")); draw=cm_draws(256,8)
    m=st_data(.,"scaled_m"); w=st_data(.,"support_weight"); type=st_data(.,"type")
    total=0
    for (i=1;i<=rows(m);i++) {
        p=st_data(i,("p1","p2","p3","p4","p5","p6","p7","p8"))
        mult=exp(par[4,4+type[i]]); low=mult*par[2,]; prob=0
        for (r=1;r<=rows(draw);r++) {
            a=cm_reweight(par[1,],draw[r,],par[4,2])
            q=cm_regular_q(m[i],p,a,low,par[4,1],.7)
            if (hasmissing(q)) _error(3498)
            prob=prob+all(q:>0)/rows(draw)
        }
        total=total+w[i]*prob
    }
    st_numscalar("cs_allpositive_pred",total/sum(w))
}
cm_recover_joint()
end
clear
set obs 1
generate double budget_scale=cs_scale
generate double all_observed_quarters=cs_all
generate double incomplete_quarters=cs_incomplete
generate double complete_nonpositive_budget=cs_nonpositive
generate double full_train_n=cs_ntrain
generate double full_holdout_n=cs_ntest
generate double objective=cs_obj16
generate double objective_256draw=cs_obj256
generate byte converged=cs_conv
generate double moment_jacobian_rank=cs_rank
generate double moment_jacobian_condition=cs_condition
generate double all_positive_observed=cs_allpositive_obs
generate double all_positive_predicted=cs_allpositive_pred
generate double full_allpositive_train=cs_full_allpositive_train
generate double full_allpositive_holdout=cs_full_allpositive_holdout
generate byte postprocessing_pending=0
export delimited "$cmroot/outputs/corner/fit_status.csv", replace
display "CORNER_FINAL_STATUS_COMPLETE"
log close
