version 17
clear all
set more off
set type double
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_build_cv_prices.log", text replace
tempfile spending pricebase foldbasket accum foldprices
import delimited using "$run/outputs/data_audit/category_province_year_spending.csv", clear varnames(1) encoding("utf-8") asdouble
keep if year<=2021 & priced==1
save `spending', replace
use "$run/data/category_external_prices_observed.dta", clear
save `pricebase', replace
use "$run/data/household_quarter_8.dta", clear
keep province province_name
duplicates drop
isid province
gen byte cv_fold=mod(province-1,5)+1
save "$run/data/province_id_crosswalk.dta", replace
foreach k in 8 9 {
    local plist
    forvalues j=1/`k' {
        local plist `plist' p`j'
    }
    local first=1
    forvalues h=1/5 {
        use `spending', clear
        merge m:1 province_name using "$run/data/province_id_crosswalk.dta", assert(match) nogen
        keep if cv_fold!=`h' & g`k'<=`k'
        collapse (sum) spend_training=spend, by(category g`k')
        rename g`k' g
        bysort g: egen double total=total(spend_training)
        gen double weight=spend_training/total
        bysort g: gen byte n_full=_N
        drop total
        save `foldbasket', replace
        use `pricebase', clear
        merge m:1 province_name using "$run/data/province_id_crosswalk.dta", assert(match) nogen
        merge m:1 category using `foldbasket', keep(match) nogen
        gen double wlp=weight*external_log_price
        collapse (sum) lp=wlp weight_sum=weight (count) n_category=external_log_price (firstnm) n_full, by(province_name ym year quarter tq cv_fold g)
        assert n_category==n_full
        assert abs(weight_sum-1)<1e-10
        preserve
        keep if year<=2021 & cv_fold!=`h'
        collapse (mean) lp_reference=lp, by(g)
        tempfile reference
        save `reference', replace
        restore
        merge m:1 g using `reference', assert(match) nogen
        collapse (mean) lp lp_reference (count) n_calendar_months=ym, by(province_name tq year quarter g)
        assert n_calendar_months==3
        gen double p=exp(lp-lp_reference)
        keep province_name tq p g
        reshape wide p, i(province_name tq) j(g)
        gen byte heldout_fold=`h'
        save `foldprices', replace
        preserve
        use "$run/data/cells_quarter_`k'.dta", clear
        drop `plist'
        merge m:1 province_name tq using `foldprices', assert(match using) keep(match) nogen
        gen byte cv_fold=mod(province-1,5)+1
        forvalues j=1/`k' {
            replace q`j'=m*w`j'/p`j'
        }
        save "$run/data/cells_quarter_`k'_cvfold`h'.dta", replace
        export delimited using "$run/data/cells_quarter_`k'_cvfold`h'.csv", replace nolabel
        restore
        if `first' {
            save `accum', replace
            local first=0
        }
        else {
            append using `accum'
            save `accum', replace
        }
    }
    use `accum', clear
    isid heldout_fold province_name tq
    assert _N==5*24*12
    save "$run/data/prices_quarter_`k'_cv5.dta", replace
    export delimited using "$run/data/prices_quarter_`k'_cv5.csv", replace nolabel
}
log close
