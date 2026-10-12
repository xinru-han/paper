version 17
clear all
set more off
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_window_attribute_checks.log", text replace
tempname result
postfile `result' str12 frequency str64 metric double value using "$run/outputs/data_audit/attribute_stability_summary.dta",replace
foreach frequency in quarter year {
    use "$run/data/household_month_active_universe.dta", clear
    keep if active_month
    if "`frequency'"=="quarter" local period tq
    else local period year
    rename changed_type raw_changed_type
    rename changed_income_band raw_changed_income_band
    rename changed_size_band raw_changed_size_band
    collapse (max) raw_changed_type raw_changed_income_band raw_changed_size_band,by(hh_id `period')
    tempfile rawflags
    save `rawflags',replace
    use "$run/data/household_`frequency'_8.dta",clear
    merge 1:1 hh_id `period' using `rawflags',assert(match) nogen
    keep if complete_window & m>0
    post `result' ("`frequency'") ("complete_positive_windows") (_N)
    foreach v in province type income_band size_band {
        quietly count if changed_`v'
        post `result' ("`frequency'") ("complete_changed_monthend_`v'") (r(N))
    }
    foreach v in type income_band size_band {
        quietly count if raw_changed_`v'
        post `result' ("`frequency'") ("complete_within_month_transaction_change_`v'") (r(N))
    }
    gen byte stable=changed_province==0 & changed_type==0 & changed_income_band==0 & changed_size_band==0 & raw_changed_type==0 & raw_changed_income_band==0 & raw_changed_size_band==0
    quietly count if stable
    post `result' ("`frequency'") ("complete_stable_all_transactions") (r(N))
    foreach k in 8 9 {
        preserve
        use "$run/data/household_`frequency'_`k'_complete_stable.dta",clear
        export delimited using "$run/data/household_`frequency'_`k'_complete_stable.csv",replace nolabel
        restore
    }
}
postclose `result'
use "$run/outputs/data_audit/attribute_stability_summary.dta",clear
export delimited using "$run/outputs/data_audit/attribute_stability_summary.csv",replace
list,noobs abbreviate(64)
log close
