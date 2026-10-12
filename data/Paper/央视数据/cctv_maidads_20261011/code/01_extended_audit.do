version 17
clear all
set more off
set type double
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_extended_audit.log", text replace

* A bounds diagnostic, not an instruction to delete repeat purchases.
use "$run/data/transactions_audit_cache.dta", clear
gen byte duplicate_row=exact_duplicate>0
gen double unique_group_spend=spend_pos/(exact_duplicate+1)
gen double repeated_group_spend=spend_pos-unique_group_spend
gen byte source_price_mismatch=price>0 & !missing(price,unit_value) & abs(price-unit_value)>1e-6*max(1,unit_value)
gen double relative_price_gap=abs(price-unit_value)/unit_value if price>0 & unit_value>0 & !missing(price,unit_value)
collapse (count) n_transactions=source_row (sum) rows_in_duplicate_groups=duplicate_row original_positive_spend=spend_pos exact_unique_lower_bound_spend=unique_group_spend repeated_group_spend price_mismatch_n=source_price_mismatch (mean) mean_relative_price_gap=relative_price_gap (max) max_relative_price_gap=relative_price_gap, by(cat category g8 g9)
gen double repeated_spending_share=repeated_group_spend/original_positive_spend
export delimited using "$run/outputs/data_audit/item_duplicate_price_audit.csv", replace nolabel
save "$run/outputs/data_audit/item_duplicate_price_audit.dta", replace
quietly summarize original_positive_spend, meanonly
local orig=r(sum)
quietly summarize repeated_group_spend, meanonly
display "Upper bound spending removed if ALL exact repeats were erroneous: " r(sum)/`orig'

* Stable means all reported transactions, not just the last monthly attribute.
tempfile stability_quarter stability_year
foreach frequency in quarter year {
    use "$run/data/household_month_active_universe.dta", clear
    keep if active_month
    if "`frequency'"=="quarter" local period tq
    else local period year
    rename changed_type raw_changed_type
    rename changed_income_band raw_changed_income_band
    rename changed_size_band raw_changed_size_band
    collapse (max) raw_changed_type raw_changed_income_band raw_changed_size_band, by(hh_id `period')
    save `stability_`frequency'', replace
}

tempname summary
postfile `summary' byte k str12 frequency str48 metric double value using "$run/outputs/data_audit/window_spending_descriptives.dta", replace
foreach k in 8 9 {
    local wlist
    local qlist
    local plist
    local slist
    forvalues j=1/`k' {
        local wlist `wlist' w`j'
        local qlist `qlist' q`j'
        local plist `plist' p`j'
        local slist `slist' spend`j'
    }
    foreach frequency in month quarter year {
        use "$run/data/household_`frequency'_`k'.dta", clear
        quietly summarize m if m>0, detail
        foreach statistic in mean sd min p1 p5 p25 p50 p75 p95 p99 max {
            post `summary' (`k') ("`frequency'") ("m_`statistic'") (r(`statistic'))
        }
        if "`frequency'"=="month" continue
        if "`frequency'"=="quarter" local period tq
        else local period year
        merge 1:1 hh_id `period' using `stability_`frequency'', assert(match) nogen
        gen byte stable_attributes=changed_province==0 & changed_type==0 & changed_income_band==0 & changed_size_band==0 & raw_changed_type==0 & raw_changed_income_band==0 & raw_changed_size_band==0
        quietly count if complete_window & stable_attributes & m>0
        post `summary' (`k') ("`frequency'") ("complete_stable_positive_windows") (r(N))
        keep if complete_window & stable_attributes & m>0
        save "$run/data/household_`frequency'_`k'_complete_stable.dta", replace
        if "`frequency'"=="quarter" local cellby province province_name tq year type income_band size_band
        else local cellby province province_name year type income_band size_band
        gen long obs_count=1
        collapse (mean) m `qlist' `slist' nut_spend month_count size_proxy (firstnm) `plist' family_type (sum) nobs=obs_count, by(`cellby')
        gen long n_households=nobs
        gen double complete_n=nobs
        if "`frequency'"=="quarter" {
            gen int time=tq
            gen byte quarter=quarter(dofq(tq))
        }
        else gen int time=year
        forvalues j=1/`k' {
            gen double w`j'=p`j'*q`j'/m
        }
        egen double wsum=rowtotal(`wlist')
        assert abs(wsum-1)<1e-10
        drop wsum
        save "$run/data/cells_`frequency'_`k'_complete_stable.dta", replace
        export delimited using "$run/data/cells_`frequency'_`k'_complete_stable.csv", replace nolabel
    }
}
postclose `summary'
use "$run/outputs/data_audit/window_spending_descriptives.dta", clear
export delimited using "$run/outputs/data_audit/window_spending_descriptives.csv", replace nolabel
log close
