version 17
clear all
set more off
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$ROOT/logs/01_review_prediction.log", text replace
do "$ROOT/ado/maidads_core.mata"
do "$ROOT/ado/cctv_prediction.mata"
mata:
void DA_numeric_test(real scalar testcase)
{
    real matrix par,p,terms
    real colvector u,m
    par=(J(2,8,1/8)\J(2,8,0))
    p=st_data(.,"p":+strofreal(1..8))
    u=(.123\.654)
    if(testcase==2) u[1]=0
    if(testcase==4) u[1]=1e-14
    if(testcase==5 | testcase==7) par[3,]=J(1,8,2)
    terms=MD_terms(u,p,par,1,0)
    m=terms[,1]
    if(testcase==3) m[2]=-1
    if(testcase==5 | testcase==7) m[1]=15.5
    st_store(.,"m_new",m)
    mf_store(par,1,0)
}
end
forvalues testcase=1/7 {
    clear
    set obs 2
    forvalues j=1/8 {
        gen double p`j'=1
        if inlist(`testcase',6,7) replace p`j'=2 if _n==2
    }
    gen double m_new=.
    mata: DA_numeric_test(`testcase')
    gen byte testcase=`testcase'
    if inlist(`testcase',1,2,4,6) {
        assert prediction_valid==1
        assert utility_roots_finite_grid==1
    }
    if `testcase'==3 {
        assert prediction_valid==1 & utility_roots_finite_grid==1 if _n==1
        assert prediction_valid==0 & utility_roots_finite_grid==0 if _n==2
    }
    if inlist(`testcase',5,7) {
        assert prediction_valid==0 & utility_roots_finite_grid==2 if _n==1
        assert prediction_valid==1 & utility_roots_finite_grid==1 if _n==2
    }
    assert utility_equation_error<1e-10 if prediction_valid==1
    list testcase m_new fitq1 prediction_valid utility_roots_finite_grid utility_equation_error,noobs
    export delimited using "$ROOT/outputs/data_audit/prediction_numeric_test`testcase'.csv",replace
}
log close
