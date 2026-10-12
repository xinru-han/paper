version 17
clear all
set more off
capture log close _all
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
log using "$cmroot/logs/03_corner_scopeaudit.log", text replace
import delimited "$cmroot/outputs/data_audit/attribute_stability_summary.csv", clear asdouble
keep if frequency=="quarter"
quietly summarize value if metric=="complete_changed_monthend_type"
scalar sc_type=r(mean)
quietly summarize value if metric=="complete_changed_monthend_income_band"
scalar sc_income=r(mean)
quietly summarize value if metric=="complete_changed_monthend_size_band"
scalar sc_size=r(mean)
quietly summarize value if metric=="complete_within_month_transaction_change_type"
scalar sc_within_type=r(mean)
quietly summarize value if metric=="complete_within_month_transaction_change_income_band"
scalar sc_within_income=r(mean)
quietly summarize value if metric=="complete_within_month_transaction_change_size_band"
scalar sc_within_size=r(mean)
quietly summarize value if metric=="complete_stable_all_transactions"
scalar sc_stable=r(mean)
export delimited "$cmroot/outputs/corner/attribute_stability_scope.csv", replace
import delimited "$cmroot/outputs/corner/fit_status.csv", clear asdouble
generate double changed_type_quarters=sc_type
generate double changed_income_quarters=sc_income
generate double changed_size_quarters=sc_size
generate double within_month_type_conflicts=sc_within_type
generate double within_month_income_conflicts=sc_within_income
generate double within_month_size_conflicts=sc_within_size
generate double complete_stable_quarters=sc_stable
generate str32 frame="complete_last_month_demographics"
generate byte strict_stable_main=0
generate byte full_sample_fit=0
export delimited "$cmroot/outputs/corner/fit_status.csv", replace
display "CORNER_SCOPE_METADATA_FINISHED"
log close
