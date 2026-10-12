version 17
clear all
set more off
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$ROOT/logs/03_test_corner_forecast.log",text replace
do "$ROOT/ado/corner_maidads.mata"
do "$ROOT/ado/corner_regular.mata"
do "$ROOT/ado/corner_smd.mata"
do "$ROOT/ado/corner_forecast.mata"
mata:
void cs_test()
{
    real rowvector p,a,l,x,q,qp,qm,fd
    real scalar i,m,h,gap,qgap,budgetgap,derivativebudget
    gap=qgap=budgetgap=derivativebudget=0
    p=(.8,1,1.5); a=(.2,.3,.5); l=(.7,.4,.9); h=1e-6
    for(i=1;i<=100;i++) {
        m=exp(-4+i*.08)
        x=cs_response(m,p,a,l,.2,.7)
        q=cm_regular_q(m,p,a,l,.2,.7)
        qp=cm_regular_q(m*(1+h),p,a,l,.2,.7)
        qm=cm_regular_q(m*(1-h),p,a,l,.2,.7)
        fd=(qp-qm)/(2*h*m)
        if(hasmissing((x,q,fd))) _error(3498)
        gap=max((gap,max(abs(fd-x[|4\6|]))))
        qgap=max((qgap,max(abs(q-x[|1\3|]))))
        budgetgap=max((budgetgap,abs(sum(p:*x[|1\3|])-m)/m))
        derivativebudget=max((derivativebudget,abs(sum(p:*x[|4\6|])-1)))
    }
    if(gap>1e-7 | qgap>1e-10 | budgetgap>1e-8 | derivativebudget>1e-8) _error(3498)
    st_matrix("cs_test",(100,gap,qgap,budgetgap,derivativebudget))
}
cs_test()
end
matrix colnames cs_test=cases analytic_budget_derivative_gap existing_solver_q_gap budget_gap derivative_budget_gap
clear
svmat double cs_test,names(col)
export delimited using "$ROOT/outputs/corner/forecast_numeric_validation.csv",replace
log close
