version 17
clear all
set more off
capture log close _all
global cfroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
log using "$cfroot/logs/03_freephi_identification.log", text replace
import delimited "$cfroot/outputs/corner_freephi/estimated_free_parameters.csv", clear asdouble
mkmat b*, matrix(cf_id_b)
import delimited "$cfroot/outputs/corner_freephi/fit_status.csv", clear asdouble
scalar cf_id_scale=budget_scale[1]
import delimited "$cfroot/outputs/corner_freephi/regularity_domain.csv", clear asdouble
mkmat maximum_scaled_quantity, matrix(cf_id_qmax_col)
import delimited "$cfroot/data/household_quarter_8.csv", clear asdouble stringcols(1)
keep if month_count==3 & m>0 & m<. & year<2022
generate double scaled_m=m/cf_id_scale
mata:
cf_id_m=st_data(.,"scaled_m")
cf_id_P=st_data(.,("p1","p2","p3","p4","p5","p6","p7","p8"))
cf_id_X=(ln(cf_id_m),ln(cf_id_m):^2,ln(cf_id_P[,1..7]):-(ln(cf_id_P[,8])*J(1,7,1)))
st_matrix("cf_id_center",mean(cf_id_X))
st_matrix("cf_id_scales",sqrt(diagonal(variance(cf_id_X)))')
end
use "$cfroot/data/corner_freephi_support.dta", clear
keep if train
do "$cfroot/ado/corner_maidads.mata"
do "$cfroot/ado/corner_freephi.mata"
mata:
real rowvector cf_id_mom(real rowvector b, real colvector m, real matrix p,
                        real colvector type, real matrix Z, real matrix Y,
                        real colvector w, real rowvector qmax)
{
    real matrix pred,mom
    pred=cf_predict_vector(b,m,p,type,cm_draws(64,8),qmax)
    if (hasmissing(pred)) _error(3498)
    mom=Z'*(w:*(pred-Y))/sum(w)
    mom[,1..7]=2*mom[,1..7]
    return(vec(mom)')
}
void cf_identification()
{
    real rowvector b,bp,bm,qmax,center,scales
    real colvector m,type,w,sv
    real matrix P,Y,X,Z,Jm
    real scalar j,h
    b=st_matrix("cf_id_b"); qmax=st_matrix("cf_id_qmax_col")'
    center=st_matrix("cf_id_center"); scales=st_matrix("cf_id_scales")
    m=st_data(.,"scaled_m"); type=st_data(.,"type"); w=st_data(.,"support_weight")
    P=st_data(.,("p1","p2","p3","p4","p5","p6","p7","p8"))
    Y=st_data(.,("w1","w2","w3","w4","w5","w6","w7",
        "purchase1","purchase2","purchase3","purchase4","purchase5","purchase6","purchase7","purchase8"))
    X=(ln(m),ln(m):^2,ln(P[,1..7]):-(ln(P[,8])*J(1,7,1)))
    Z=(J(rows(m),1,1),(X:-center):/scales,type:==2,type:==3,type:==4)
    h=.025; Jm=J(195,27,.)
    for (j=1;j<=27;j++) {
        bp=b; bm=b; bp[j]=bp[j]+h; bm[j]=bm[j]-h
        Jm[,j]=(cf_id_mom(bp,m,P,type,Z,Y,w,qmax)-cf_id_mom(bm,m,P,type,Z,Y,w,qmax))'/(2*h)
        printf("Freephi 64-draw moment Jacobian column %g/27 done\n",j)
    }
    sv=svdsv(Jm)
    st_matrix("cf_id_sv",((1::27),sv))
    st_matrix("cf_id_summary",(64,h,sum(sv:>1e-6),min(sv),max(sv)/min(sv),27,195))
}
cf_identification()
end
clear
matrix colnames cf_id_sv = singular_value_index singular_value
svmat double cf_id_sv, names(col)
export delimited "$cfroot/outputs/corner_freephi/moment_jacobian_singular_values.csv", replace
clear
matrix colnames cf_id_summary = integration_draws finite_difference_step numerical_rank minimum_singular_value condition_number parameter_count moment_count
svmat double cf_id_summary, names(col)
export delimited "$cfroot/outputs/corner_freephi/moment_rank_diagnostic.csv", replace
display "FREEPHI_MOMENT_RANK_DIAGNOSTIC_FINISHED"
log close
