version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$ROOT/logs/06_review_simplex_delivery.log",text replace
tempname checks
postfile `checks' str24 scenario_mode str12 aggregation double target_groups complete_groups max_budget_gap max_income_derivative_gap max_budget_derivative_gap using "$ROOT/tmp/simplex_delivery_checks.dta",replace
foreach mode in pooled_micro elderly_micro cohort_mean {
    use "$ROOT/outputs/scenarios_simplex/`mode'/predictions.dta",clear
    assert nobs>0 & nobs<.
    assert prediction_valid==0 | prediction_valid==1
    forvalues j=1/8 {
        assert fitq`j'>0 & fitq`j'<. if prediction_valid
    }
    tempfile predictions
    save `predictions'
    foreach agg in province family {
        use `predictions',clear
        if "`agg'"=="province" local by province scenario_order
        else local by type scenario_order
        gen double invalid=nobs*(prediction_valid==0)
        gen double checked_budget=m_new*nobs
        local sumvars nobs invalid checked_budget
        forvalues j=1/8 {
            gen double value`j'=p`j'*fitq`j'*nobs
            gen double deriv_b`j'=p`j'*fitq`j'*nobs*eta`j'
            gen double deriv_y`j'=fitq`j'*nobs*eta`j'*eta_budget_income_new
            gen double quant`j'=fitq`j'*nobs
            local sumvars `sumvars' value`j' deriv_b`j' deriv_y`j' quant`j'
        }
        collapse (sum) `sumvars',by(`by')
        tempfile check
        save `check'
        import delimited using "$ROOT/outputs/scenarios_simplex/`mode'/`agg'_income_growth.csv",clear asdouble
        merge 1:1 `by' using `check',assert(3) nogen
        assert total_weight==nobs
        assert invalid_weight==invalid
        assert complete_coverage==(invalid==0)
        assert qualified_forecast==0
        gen double budget_check=0
        gen double budget_derivative_check=0
        gen double income_derivative_check=0
        forvalues j=1/8 {
            assert missing(quantity`j') & missing(income_elasticity`j') & missing(budget_elasticity`j') if invalid>0
            assert abs(quantity`j'-quant`j'/nobs)<1e-9 if invalid==0
            replace budget_check=budget_check+value`j'
            replace budget_derivative_check=budget_derivative_check+deriv_b`j'
            replace income_derivative_check=max(income_derivative_check,abs(income_elasticity`j'-deriv_y`j'/quant`j')) if invalid==0
        }
        replace budget_check=abs(budget_check/checked_budget-1) if invalid==0
        replace budget_derivative_check=abs(budget_derivative_check/checked_budget-1) if invalid==0
        assert budget_check<1e-10 & budget_derivative_check<1e-10 & income_derivative_check<1e-10 if invalid==0
        local target=_N
        quietly count if invalid==0
        local complete=r(N)
        quietly summarize budget_check if invalid==0,meanonly
        local gap=r(max)
        quietly summarize income_derivative_check if invalid==0,meanonly
        local igap=r(max)
        quietly summarize budget_derivative_check if invalid==0,meanonly
        post `checks' ("`mode'") ("`agg'") (`target') (`complete') (`gap') (`igap') (r(max))
    }
}
postclose `checks'
use "$ROOT/tmp/simplex_delivery_checks.dta",clear
export delimited using "$ROOT/outputs/data_audit/simplex_delivery_checks.csv",replace

local model "$ROOT/outputs/estimation/maidads_8_coarse_simplex_multistart"
import delimited using "`model'/parameters.csv",clear asdouble
sort good
mkmat alpha beta delta tau,matrix(__natural)
matrix MF_par=__natural'
import delimited using "`model'/model_summary.csv",clear asdouble
scalar MF_omega=omega[1]
scalar MF_kappa=kappa[1]
import delimited using "`model'/representative_inputs.csv",clear asdouble
sort good
mkmat price,matrix(__price)
scalar MF_budget=mean_budget[1]
do "$ROOT/ado/maidads_simplex_core.mata"
mata:
    par=st_matrix("MF_par");p=st_matrix("__price")'
    omega=st_numscalar("MF_omega");kappa=st_numscalar("MF_kappa")
    m=st_numscalar("MF_budget")
    u=MD_roots(p,m,par,omega,kappa)
    phi=MD_sigmoid(-u)*par[1,]+MD_sigmoid(u)*par[2,]
    ga=MD_sigmoid(-omega*u)*par[3,]+MD_sigmoid(omega*u)*par[4,]
    excess_budget=m-rowsum(p:*ga)
    qeq=ga+phi:*excess_budget:/p
    committed=ga:/qeq;discretionary=1:-committed
    h=-(1:-phi):*discretionary
    st_matrix("__components",((1..8)',phi',committed',discretionary',h'))
end
clear
svmat double __components,names(col)
rename (c1 c2 c3 c4 c5) (good marginal_share committed_quantity_fraction discretionary_quantity_fraction hicksian_own_decomposed)
tempfile components
save `components'
import delimited using "`model'/representative_budget_elasticities.csv",clear asdouble
merge 1:1 good using `components',assert(3) nogen
assert abs(hicksian_own-hicksian_own_decomposed)<1e-10
assert abs(committed_quantity_fraction+discretionary_quantity_fraction-1)<1e-14
export delimited using "$ROOT/outputs/data_audit/simplex_own_price_components.csv",replace
log close
