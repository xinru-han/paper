version 17
clear all
set more off
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$cmroot/logs/03_corner_format_results.log", text replace
foreach f in training_fit holdout_fit {
    import delimited "$cmroot/outputs/corner/`f'.csv", clear asdouble
    generate double share8=1-share1-share2-share3-share4-share5-share6-share7
    assert inrange(share8,0,1)
    order row share1 share2 share3 share4 share5 share6 share7 share8
    export delimited "$cmroot/outputs/corner/`f'.csv", replace
}
foreach f in point_prediction_metrics constant_mean_baseline_holdout_metrics {
    import delimited "$cmroot/outputs/corner/`f'.csv", clear asdouble
    local prefix=cond("`f'"=="point_prediction_metrics","cm_prediction_metrics","cm_baseline_holdout")
    rename `prefix'1 train
    forvalues j=1/7 {
        local c=`j'+1
        rename `prefix'`c' share_rmse`j'
    }
    forvalues j=1/8 {
        local c=`j'+8
        rename `prefix'`c' purchase_brier`j'
    }
    export delimited "$cmroot/outputs/corner/`f'.csv", replace
}
import delimited "$cmroot/outputs/corner/pairwise_purchase_joint_and_correlation.csv", clear asdouble
rename cm_pairwise1 good_i
rename cm_pairwise2 good_j
rename cm_pairwise3 observed_joint
rename cm_pairwise4 predicted_joint
rename cm_pairwise5 observed_correlation
rename cm_pairwise6 predicted_correlation
export delimited "$cmroot/outputs/corner/pairwise_purchase_joint_and_correlation.csv", replace
import delimited "$cmroot/outputs/corner/integration_sensitivity_no_refit.csv", clear asdouble
rename cm_integration_sensitivity1 draws
rename cm_integration_sensitivity2 objective
export delimited "$cmroot/outputs/corner/integration_sensitivity_no_refit.csv", replace
import delimited "$cmroot/outputs/corner/optimizer_starts_status.csv", clear asdouble
rename evaluations evaluations_at_last_checkpoint
generate byte checkpoint_is_final=converged==1
export delimited "$cmroot/outputs/corner/optimizer_starts_status.csv", replace
display "CORNER_RESULT_LABELS_FINISHED"
log close
