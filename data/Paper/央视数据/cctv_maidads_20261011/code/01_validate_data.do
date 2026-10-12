version 17
clear all
set more off
args max_k max_frequency
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_validate_data.log", text replace
tempname diagnostics
postfile `diagnostics' str64 metric double value using "$run/outputs/data_audit/validation_metrics.dta", replace
use "$run/outputs/data_audit/item_transaction_descriptives.dta", clear
assert _N==84
preserve
keep if variable=="volume"
quietly summarize n, meanonly
local nr=r(sum)
quietly summarize zero_n, meanonly
post `diagnostics' ("transaction_volume_zero_fraction") (r(sum)/`nr')
restore
keep if variable=="price"
quietly summarize n, meanonly
local nr=r(sum)
quietly summarize missing_n, meanonly
post `diagnostics' ("transaction_price_missing_fraction") (r(sum)/(`nr'+r(sum)))

foreach k in 8 9 {
    if "`max_k'"=="8" & `k'==9 continue
    local slist
    local wlist
    forvalues j=1/`k' {
        local slist `slist' spend`j'
        local wlist `wlist' w`j'
    }
    foreach frequency in month quarter year {
        if "`max_frequency'"=="quarter" & "`frequency'"=="year" continue
        capture confirm file "$run/data/household_`frequency'_`k'.dta"
        if _rc continue
        use "$run/data/household_`frequency'_`k'.dta", clear
        export delimited using "$run/data/household_`frequency'_`k'.csv", replace nolabel
        egen double ssum=rowtotal(`slist')
        assert abs(ssum-covered_spend)<1e-7
        assert abs(m-ssum/(size_proxy*month_count))<1e-7
        assert month_count>0
        local maxmonths=cond("`frequency'"=="month",1,cond("`frequency'"=="quarter",3,12))
        assert month_count<=`maxmonths'
        egen double wsum=rowtotal(`wlist')
        assert abs(wsum-1)<1e-10 if m>0
        forvalues j=1/`k' {
            assert q`j'>=0 & !missing(q`j') if m>0
            assert abs(p`j'*q`j'-m*w`j')<1e-8 if m>0
            assert w`j'==0 if spend`j'==0 & m>0
        }
        post `diagnostics' ("`frequency'_`k'_n_windows") (_N)
        quietly count if m==0
        post `diagnostics' ("`frequency'_`k'_zero_budget_windows_retained") (r(N))
        if "`frequency'"!="month" {
            quietly count if complete_window
            post `diagnostics' ("`frequency'_`k'_complete_windows") (r(N))
            foreach v in province type income_band size_band {
                quietly count if changed_`v'
                post `diagnostics' ("`frequency'_`k'_changed_`v'") (r(N))
            }
        }
        if "`frequency'"!="month" {
            use "$run/data/cells_`frequency'_`k'.dta", clear
            export delimited using "$run/data/cells_`frequency'_`k'.csv", replace nolabel
            egen double wsum=rowtotal(`wlist')
            assert abs(wsum-1)<1e-10
            forvalues j=1/`k' {
                assert q`j'>=0 & !missing(q`j')
                assert abs(p`j'*q`j'-m*w`j')<1e-8
            }
            post `diagnostics' ("`frequency'_`k'_validated_cells") (_N)
        }
    }
}
postclose `diagnostics'
use "$run/outputs/data_audit/validation_metrics.dta", clear
export delimited using "$run/outputs/data_audit/validation_metrics.csv", replace
list, noobs abbreviate(64)
capture confirm file "$run/data/category_external_prices_observed.dta"
if !_rc {
    use "$run/data/category_external_prices_observed.dta", clear
    collapse (count) n=external_price_mean (mean) mean=external_price_mean (min) min=external_price_mean (p1) p1=external_price_mean (p5) p5=external_price_mean (p50) p50=external_price_mean (p95) p95=external_price_mean (p99) p99=external_price_mean (max) max=external_price_mean, by(category units)
    export delimited using "$run/outputs/data_audit/external_price_category_descriptives.csv", replace
    list, noobs
}
log close
