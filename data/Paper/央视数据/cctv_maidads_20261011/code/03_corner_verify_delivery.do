version 17
clear all
set more off
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$cmroot/logs/03_corner_verify_delivery.log", text replace
foreach f in training_fit holdout_fit {
    import delimited "$cmroot/outputs/corner/`f'.csv", clear asdouble
    assert _N==2
    assert abs(share1+share2+share3+share4+share5+share6+share7+share8-1)<1e-12
    forvalues j=1/8 {
        assert inrange(share`j',0,1) & inrange(positive`j',0,1)
    }
}
import delimited "$cmroot/outputs/corner/price_response_all_4_families.csv", clear asdouble
assert _N==256
isid type good price_good
assert integration_draws==16384 & perturbation==.025
assert hicks_total<=0 & marshall_total<=0 if good==price_good
assert abs(marshall_total-marshall_participation-marshall_conditional)<1e-10
assert abs(hicks_total-hicks_participation-hicks_conditional)<1e-10
import delimited "$cmroot/outputs/corner/budget_response_curve_all_4_families.csv", clear asdouble
assert _N==160
isid type good budget_percap_month
assert abs(budget_total-budget_participation-budget_conditional)<1e-10
import delimited "$cmroot/outputs/corner/fitted_solver_checks.csv", clear asdouble
assert invalid_roots==0 & invalid_budgets==0 & negative_quantities==0
assert max_root_error<1e-8 & max_slutsky_eigenvalue<1e-6
import delimited "$cmroot/outputs/corner/fit_status.csv", clear asdouble
assert _N==1 & postprocessing_pending==0 & converged==1
assert moment_jacobian_rank==20 & full_sample_fit==0 & strict_stable_main==0
assert full_train_n==117537 & full_holdout_n==68371
import delimited "$cmroot/outputs/corner/integration_sensitivity_no_refit.csv", clear asdouble
assert _N==3
assert draws[1]==16 & draws[2]==64 & draws[3]==256
display "CORNER_COMPLETE_RESULTS_VERIFIED"
log close
