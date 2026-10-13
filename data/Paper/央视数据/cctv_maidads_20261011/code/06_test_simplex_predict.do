version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$ROOT/logs/06_test_simplex_predict.log",text replace
do "$ROOT/ado/maidads_simplex_core.mata"
do "$ROOT/ado/cctv_prediction.mata"
clear
set obs 2
forvalues j=1/8 {
    gen double p`j'=1
}
gen double m_new=.
mata:
void mf_endpoint_test()
{
    real matrix par,p,term
    real rowvector a,b
    real colvector u
    a=J(1,8,1/7);a[6]=0
    b=J(1,8,1/7);b[7]=0
    par=(a\b\J(1,8,.1)\J(1,8,.2))
    p=st_data(.,"p":+strofreal(1..8));u=(-15\45)
    term=MD_terms(u,p,par,2,0)
    if(hasmissing(term)) _error(3498)
    st_store(.,"m_new",term[,1])
    mf_store(par,2,0)
}
mf_endpoint_test()
end
assert prediction_valid==1
assert utility_roots_finite_grid==1
assert utility_equation_error<1e-10
gen double closure=0
forvalues j=1/8 {
    replace closure=closure+p`j'*fitq`j'
    assert fitq`j'>0 & fitq`j'<.
}
gen double budget_gap=abs(closure-m_new)/m_new
assert budget_gap<1e-8
gen str100 scope="Synthetic exact alpha6/beta7 zero; utility -15/45; not CCTV estimates"
export delimited using "$ROOT/outputs/data_audit/simplex_prediction_endpoints.csv",replace
log close
