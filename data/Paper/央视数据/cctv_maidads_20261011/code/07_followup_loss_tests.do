version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
global FOLLOW "$ROOT/outputs/followup_20261013"
capture log close _all
log using "$FOLLOW/loss_tests.log",text replace
tempname results
postfile `results' str24 model str12 benchmark str32 status double cells household_quarters province_clusters mean_loss_difference standard_error t_statistic df p_value ci_lower ci_upper byte numeric_pair_qualified using "$ROOT/tmp/followup_loss_tests.dta",replace
foreach model in quaids aids aidads maidads maidads_prior {
    if "`model'"=="maidads_prior" local source "$ROOT/outputs/validation_simplex/temporal_maidads/metrics/cell_errors.dta"
    else local source "$FOLLOW/temporal_`model'/metrics/cell_errors.dta"
    capture confirm file "`source'"
    if _rc {
        foreach benchmark in history quaids {
            if "`model'"=="quaids" & "`benchmark'"=="quaids" continue
            post `results' ("`model'") ("`benchmark'") ("no_completed_validation") (.) (.) (.) (.) (.) (.) (.) (.) (.) (.) (0)
        }
        continue
    }
    foreach benchmark in history quaids {
        if "`model'"=="quaids" & "`benchmark'"=="quaids" continue
        use "`source'",clear
        isid province time type income_band
        assert year==2022
        assert nobs>0 & nobs<.
        capture confirm variable estimate_qualified
        if _rc generate byte estimate_qualified=estimate_stationary
        quietly summarize estimate_qualified,meanonly
        local qualified=r(min)==1
        if "`benchmark'"=="history" {
            generate double comparator_loss=all_history_share_sse/8
            generate byte comparator_valid=historical_available
            generate byte comparator_qualified=1
        }
        else {
            tempfile source
            save `source'
            use "$FOLLOW/temporal_quaids/metrics/cell_errors.dta",clear
            capture confirm variable estimate_qualified
            if _rc generate byte estimate_qualified=estimate_stationary
            keep province time type income_band all_share_sse prediction_valid estimate_qualified
            rename all_share_sse comparator_loss
            replace comparator_loss=comparator_loss/8
            rename prediction_valid comparator_valid
            rename estimate_qualified comparator_qualified
            merge 1:1 province time type income_band using `source',assert(3) nogen
        }
        generate double loss_difference=all_share_sse/8-comparator_loss
        quietly count if prediction_valid!=1 | comparator_valid!=1 | missing(loss_difference)
        if r(N)>0 {
            local cells=_N
            quietly summarize nobs,meanonly
            post `results' ("`model'") ("`benchmark'") ("incomplete_coverage_no_test") (`cells') (r(sum)) (.) (.) (.) (.) (.) (.) (.) (.) (0)
            continue
        }
        quietly summarize comparator_qualified,meanonly
        local qualified=`qualified' & r(min)==1
        quietly summarize nobs,meanonly
        local households=r(sum)
        quietly regress loss_difference [aw=nobs],vce(cluster province)
        local delta=_b[_cons]
        local se=_se[_cons]
        local t=`delta'/`se'
        local df=e(df_r)
        local p=2*ttail(`df',abs(`t'))
        local critical=invttail(`df',.025)
        local status="conditional_loss_comparison"
        if !`qualified' local status="unqualified_model_diagnostic"
        post `results' ("`model'") ("`benchmark'") ("`status'") (e(N)) (`households') (e(N_clust)) (`delta') (`se') (`t') (`df') (`p') (`delta'-`critical'*`se') (`delta'+`critical'*`se') (`qualified')
    }
}
postclose `results'
use "$ROOT/tmp/followup_loss_tests.dta",clear
quietly count if p_value<.
local hypotheses=r(N)
sort p_value
generate double p_holm=min(1,(`hypotheses'-_n+1)*p_value) if p_value<.
forvalues j=2/`hypotheses' {
    replace p_holm=max(p_holm,p_holm[`j'-1]) in `j'
}
generate str80 interpretation="positive difference means model has greater held-out squared share loss"
generate byte first_stage_and_training_uncertainty_included=0
sort model benchmark
export delimited "$FOLLOW/conditional_loss_tests.csv",replace
list model benchmark status mean_loss_difference p_value p_holm,nolabel noobs
log close
