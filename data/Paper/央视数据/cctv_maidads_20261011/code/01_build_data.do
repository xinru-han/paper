version 17.0
clear all
set more off
set type double
capture set processors 4
args reuse_audit
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
global source "/root/data/Paper/央视数据/Paper1-EASI"
capture mkdir "$run/outputs/data_audit"
capture log close _all
log using "$run/logs/01_build_data.log", text replace
tempfile raw attrs tiers basket8 basket9 price8m price9m base9
tempname flow
postfile `flow' str64 metric double value using "$run/outputs/data_audit/sample_flow.dta", replace

* Reimport all ten original columns, including the original unit-value Price.
import delimited using "/root/data/数据/央视数据/Data_merged.csv", clear varnames(1) encoding("utf-8") stringcols(1/7) asdouble
rename id hh_id
rename province province_name
replace hh_id=strtrim(hh_id)
replace family_income=strtrim(family_income)
replace family_income=">12000 RMB" if family_income==">12000RMB"
gen long source_row=_n
gen long date_clean=daily(subinstr(substr(date,1,10),"/","-",.),"YMD")
assert !missing(date_clean)
format date_clean %td
gen double timestamp=clock(subinstr(date,"/","-",.),"YMDhms")
replace timestamp=cofd(date_clean) if missing(timestamp)
format timestamp %tc
gen int ym=mofd(date_clean)
format ym %tm
gen int year=year(date_clean)
gen byte month=month(date_clean)
gen byte quarter=quarter(date_clean)
gen int tq=qofd(date_clean)
format tq %tq
count
post `flow' ("raw_rows") (r(N))
keep if inrange(year,2020,2022)
gen byte cat=.
local categories 大米 面粉 挂面 方便面 食用油 蔬菜 水果 猪肉 禽类 其他肉类 牛肉 羊肉 海鲜类 常温牛奶 新鲜牛奶 常温酸奶 新鲜酸奶 奶酪 黄油 成人奶粉 坚果
local j=0
foreach c of local categories {
    local ++j
    replace cat=`j' if category=="`c'"
}
assert !missing(cat)
gen byte g9=cond(cat<=4,1,cond(cat==5,2,cond(cat==6,3,cond(cat==7,4,cond(cat==8,5,cond(cat<=10,6,cond(cat<=12,7,cond(cat==13,8,cond(cat<=20,9,10)))))))))
gen byte g8=cond(g9<=5,g9,cond(inlist(g9,6,7),6,cond(g9==8,7,cond(g9==9,8,9))))
gen byte priced=inlist(cat,1,2,4,5,6,7,8,9,10) | inlist(cat,11,12,13,14,15,20)
gen double spend_pos=cond(spend>0 & !missing(spend),spend,0)
gen double unit_value=spend/volume if spend>0 & volume>0 & !missing(spend,volume)
gen byte type=cond(family_type=="年轻家庭",1,cond(family_type=="成年家庭",2,cond(family_type=="老年家庭",3,cond(family_type=="青少年家庭",4,.))))
gen byte income_band=cond(family_income=="<5000 RMB",1,cond(family_income=="5001-7000 RMB",2,cond(family_income=="7001-9000 RMB",3,cond(family_income=="9001-12000 RMB",4,cond(family_income==">12000 RMB",5,.)))))
gen byte size_band=cond(family_size=="家庭人口数1-2",1,cond(family_size=="家庭人口数3",2,cond(family_size=="家庭人口数4",3,cond(family_size=="家庭人口数5+",4,.))))
assert !missing(type,income_band,size_band)
gen double size_proxy=cond(size_band==1,1.5,cond(size_band==2,3,cond(size_band==3,4,5.5)))
compress
duplicates tag hh_id province_name family_type family_size family_income date category spend volume price, gen(exact_duplicate)
quietly count if exact_duplicate>0
post `flow' ("rows_in_exact_duplicate_groups_kept") (r(N))
quietly count if volume==0
post `flow' ("rows_volume_zero") (r(N))
quietly count if spend>0 & volume==0
post `flow' ("positive_spend_zero_volume") (r(N))
quietly count if missing(price)
post `flow' ("rows_price_missing") (r(N))
quietly count if price>0 & !missing(price,unit_value) & abs(price-unit_value)>1e-6*max(1,unit_value)
post `flow' ("positive_price_unitvalue_disagreement") (r(N))
quietly count if spend<=0 | missing(spend)
post `flow' ("nonpositive_or_missing_spend_rows") (r(N))

* Descriptives retain extreme values and distinguish absence from recorded zero.
capture confirm file "$run/outputs/data_audit/item_transaction_descriptives.csv"
local have_audit=_rc==0
if "`reuse_audit'"!="1" | !`have_audit' {
tempname desc
postfile `desc' byte cat str32 category str16 variable long n long missing_n long zero_n long negative_n double mean double sd double min double p1 double p5 double p25 double p50 double p75 double p95 double p99 double max using "$run/outputs/data_audit/item_transaction_descriptives.dta", replace
forvalues j=1/21 {
    preserve
    keep if cat==`j'
    local c: word `j' of `categories'
    foreach v in spend volume price unit_value {
        quietly count if missing(`v')
        local miss=r(N)
        quietly count if `v'==0
        local zero=r(N)
        quietly count if `v'<0
        local neg=r(N)
        quietly summarize `v', detail
        post `desc' (`j') ("`c'") ("`v'") (r(N)) (`miss') (`zero') (`neg') (r(mean)) (r(sd)) (r(min)) (r(p1)) (r(p5)) (r(p25)) (r(p50)) (r(p75)) (r(p95)) (r(p99)) (r(max))
    }
    restore
}
postclose `desc'
preserve
use "$run/outputs/data_audit/item_transaction_descriptives.dta", clear
export delimited using "$run/outputs/data_audit/item_transaction_descriptives.csv", replace
restore
}
else display "Reusing already executed 21-item audit from unchanged original CSV; first-run log retained."
preserve
collapse (sum) spend=spend_pos (count) n_transactions=source_row (sum) duplicate_multiplicity_sum=exact_duplicate, by(province_name year cat category g8 g9 priced)
export delimited using "$run/outputs/data_audit/category_province_year_spending.csv", replace
restore
save `raw', replace
save "$run/data/transactions_audit_cache.dta", replace

* Raw last-observation household attributes; within-period changes are audited.
sort hh_id ym timestamp source_row
foreach v in type income_band size_band {
    by hh_id ym: egen byte min_`v'=min(`v')
    by hh_id ym: egen byte max_`v'=max(`v')
    gen byte changed_`v'=min_`v'!=max_`v'
}
by hh_id ym: keep if _n==_N
keep hh_id ym province_name family_type family_size family_income type income_band size_band size_proxy changed_*
encode province_name, gen(province)
foreach v in type income_band size_band {
    quietly count if changed_`v'
    post `flow' ("household_months_changed_`v'") (r(N))
}
isid hh_id ym
save `attrs', replace
import excel using "/root/data/数据/央视数据/补充样本城市级别--20260610.xlsx", sheet("样本城市级别") firstrow clear
tostring ID, gen(hh_id) format(%12.0f)
replace hh_id=strtrim(hh_id)
rename CityTier citytier
keep hh_id citytier
isid hh_id
save `tiers', replace

* National fixed weights estimated ONLY in 2020-2021, excluding held-out 2022.
foreach k in 8 9 {
    use `raw', clear
    keep if year<=2021 & priced & g`k'<=`k'
    collapse (sum) spend_training=spend_pos, by(g`k' cat category)
    rename g`k' g
    bysort g: egen double group_spend=total(spend_training)
    gen double weight=spend_training/group_spend
    bysort g: gen byte n_full=_N
    drop group_spend
    isid category
    save `basket`k'', replace
    save "$run/data/basket_weights_training_`k'.dta", replace
    export delimited using "$run/outputs/data_audit/basket_weights_training_`k'.csv", replace
    use `raw', clear
    keep if year==2021 & priced & g`k'<=`k'
    collapse (sum) spend_2021=spend_pos, by(g`k' cat category)
    rename g`k' g
    bysort g: egen double group_spend=total(spend_2021)
    gen double weight=spend_2021/group_spend
    drop group_spend
    export delimited using "$run/outputs/data_audit/basket_weights_2021_`k'.csv", replace
    use `raw', clear
    keep if g`k'<=`k'
    gen double priced_spend=spend_pos*priced
    collapse (sum) spend=spend_pos priced_spend, by(g`k')
    gen double priced_share=priced_spend/spend
    export delimited using "$run/outputs/data_audit/group_price_coverage_`k'.csv", replace
}

import delimited using "$source/processed/external_food_prices_category_province_month_2020_2022.csv", clear varnames(1) encoding("utf-8") asdouble
rename province province_name
gen int ym=monthly(year_month,"YM")
format ym %tm
gen int year=year(dofm(ym))
gen byte quarter=quarter(dofm(ym))
gen int tq=qofd(dofm(ym))
format tq %tq
isid province_name ym category
export delimited using "$run/outputs/data_audit/category_external_prices_all_sources.csv", replace
save "$run/data/category_external_prices_all_sources.dta", replace
keep if price_fill_level=="observed_province_month"
assert !missing(external_log_price)
assert external_price_mean>0 & !missing(external_price_mean)
export delimited using "$run/outputs/data_audit/category_external_prices_observed.csv", replace
save "$run/data/category_external_prices_observed.dta", replace
foreach k in 8 9 {
    use "$run/data/category_external_prices_observed.dta", clear
    merge m:1 category using `basket`k'', keep(match) nogen
    gen double wlp=weight*external_log_price
    collapse (sum) lp=wlp weight_sum=weight (count) n_category=external_log_price (firstnm) n_full, by(province_name ym year quarter tq g)
    assert n_category==n_full
    assert abs(weight_sum-1)<1e-10
    assert _N==24*36*`k'
    isid province_name ym g
    preserve
    keep if year<=2021
    collapse (mean) lp_reference=lp, by(g)
    tempfile ref`k'
    save `ref`k'', replace
    restore
    merge m:1 g using `ref`k'', assert(match) nogen
    gen double p=exp(lp-lp_reference)
    export delimited using "$run/outputs/data_audit/group_price_month_`k'.csv", replace
    preserve
    collapse (mean) lp lp_reference (count) n_calendar_months=ym, by(province_name tq year quarter g)
    assert n_calendar_months==3
    gen double p=exp(lp-lp_reference)
    keep province_name tq p g
    reshape wide p, i(province_name tq) j(g)
    save "$run/data/prices_quarter_`k'.dta", replace
    restore
    preserve
    collapse (mean) lp lp_reference (count) n_calendar_months=ym, by(province_name year g)
    assert n_calendar_months==12
    gen double p=exp(lp-lp_reference)
    keep province_name year p g
    reshape wide p, i(province_name year) j(g)
    save "$run/data/prices_year_`k'.dta", replace
    restore
    keep province_name ym p g
    reshape wide p, i(province_name ym) j(g)
    save "$run/data/prices_month_`k'.dta", replace
}

* Full active universe includes nut-only household-months and zero-budget records.
use `raw', clear
collapse (sum) spend=spend_pos (count) transaction_count=source_row, by(hh_id ym g9)
reshape wide spend transaction_count, i(hh_id ym) j(g9)
forvalues j=1/10 {
    replace spend`j'=0 if missing(spend`j')
    replace transaction_count`j'=0 if missing(transaction_count`j')
}
rename spend10 nut_spend
merge 1:1 hh_id ym using `attrs', assert(match) nogen
merge m:1 hh_id using `tiers'
quietly count if _merge==1
post `flow' ("household_months_citytier_unmatched") (r(N))
drop if _merge==2
drop _merge
gen int year=year(dofm(ym))
gen byte quarter=quarter(dofm(ym))
gen int tq=qofd(dofm(ym))
format tq %tq
egen double covered_spend=rowtotal(spend1 spend2 spend3 spend4 spend5 spend6 spend7 spend8 spend9)
gen double food10_spend=covered_spend+nut_spend
gen byte active_month=food10_spend>0
gen byte covered_active=covered_spend>0
gen byte nut_only=covered_spend==0 & nut_spend>0
quietly count
post `flow' ("household_months_any_transaction") (r(N))
quietly count if active_month
post `flow' ("household_months_active_21items") (r(N))
quietly count if nut_only
post `flow' ("household_months_positive_nut_only") (r(N))
quietly count if covered_active
post `flow' ("household_months_positive_covered_budget") (r(N))
egen byte hh_tag=tag(hh_id)
quietly count if hh_tag
post `flow' ("households_any_transactions") (r(N))
drop hh_tag
compress
save "$run/data/household_month_active_universe.dta", replace
keep if active_month
save `base9', replace

* Household windows use only genuinely active recorded months, never fill gaps.
foreach k in 8 9 {
    local slist
    local qlist
    local plist
    local wlist
    forvalues j=1/`k' {
        local slist `slist' spend`j'
        local qlist `qlist' q`j'
        local plist `plist' p`j'
        local wlist `wlist' w`j'
    }
    use `base9', clear
    if `k'==8 {
        replace spend6=spend6+spend7
        drop spend7
        rename spend8 spend7
        rename spend9 spend8
    }
    keep hh_id province province_name ym tq year quarter family_type type income_band size_band size_proxy citytier `slist' nut_spend active_month covered_spend
    gen byte month_count=1
    merge m:1 province_name ym using "$run/data/prices_month_`k'.dta", assert(match using) keep(match) nogen
    gen int time=ym
    gen double m=covered_spend/size_proxy
    label var m "Active-month covered purchases divided by the last recorded monthly population proxy"
    forvalues j=1/`k' {
        gen double w`j'=spend`j'/covered_spend if covered_spend>0
        gen double q`j'=m*w`j'/p`j' if m>0
    }
    isid hh_id ym
    save "$run/data/household_month_`k'.dta", replace
    export delimited using "$run/data/household_month_`k'.csv", replace nolabel
    foreach frequency in quarter year {
        use "$run/data/household_month_`k'.dta", clear
        if "`frequency'"=="quarter" {
            local period tq
            local fullmonths=3
        }
        else {
            local period year
            local fullmonths=12
        }
        sort hh_id `period' ym
        by hh_id `period': gen byte lastrow=_n==_N
        foreach v in province type income_band size_band {
            by hh_id `period': egen double lo_`v'=min(`v')
            by hh_id `period': egen double hi_`v'=max(`v')
            gen byte changed_`v'=lo_`v'!=hi_`v'
        }
        tempfile window_attrs
        preserve
        keep if lastrow
        keep hh_id `period' province province_name family_type type income_band size_band size_proxy citytier year quarter changed_*
        save `window_attrs', replace
        restore
        collapse (sum) `slist' nut_spend month_count covered_spend, by(hh_id `period')
        merge 1:1 hh_id `period' using `window_attrs', assert(match) nogen
        merge m:1 province_name `period' using "$run/data/prices_`frequency'_`k'.dta", assert(match using) keep(match) nogen
        gen int time=`period'
        gen byte complete_window=month_count==`fullmonths'
        gen double m=covered_spend/(size_proxy*month_count)
        label var m "Monthly-equivalent covered purchases divided by the last recorded window population proxy"
        forvalues j=1/`k' {
            gen double w`j'=spend`j'/covered_spend if covered_spend>0
            gen double q`j'=m*w`j'/p`j' if m>0
        }
        isid hh_id `period'
        save "$run/data/household_`frequency'_`k'.dta", replace
        export delimited using "$run/data/household_`frequency'_`k'.csv", replace nolabel
        quietly count if m==0
        post `flow' ("`frequency'_`k'_zero_covered_budget") (r(N))
        quietly count if m>0
        post `flow' ("`frequency'_`k'_positive_covered_budget") (r(N))
        quietly count if complete_window & m>0
        post `flow' ("`frequency'_`k'_positive_complete_window") (r(N))
        preserve
        keep if complete_window
        save "$run/data/household_`frequency'_`k'_complete.dta", replace
        restore
        preserve
        keep if m>0
        gen long obs_count=1
        gen double complete_n=complete_window
        if "`frequency'"=="quarter" local cellby province province_name tq year type income_band size_band
        else local cellby province province_name year type income_band size_band
        collapse (mean) m `qlist' `slist' nut_spend month_count size_proxy (firstnm) `plist' family_type (sum) nobs=obs_count complete_n, by(`cellby')
        gen long n_households=nobs
        gen int time=`period'
        if "`frequency'"=="quarter" gen byte quarter=quarter(dofq(tq))
        forvalues j=1/`k' {
            gen double w`j'=p`j'*q`j'/m
        }
        egen double wsum=rowtotal(`wlist')
        assert abs(wsum-1)<1e-10
        drop wsum
        assert m>0 & !missing(m)
        forvalues j=1/`k' {
            assert p`j'>0 & !missing(p`j')
        }
        isid province `period' type income_band size_band
        save "$run/data/cells_`frequency'_`k'.dta", replace
        export delimited using "$run/data/cells_`frequency'_`k'.csv", replace nolabel
        summarize nobs, detail
        post `flow' ("`frequency'_`k'_cells") (r(N))
        post `flow' ("`frequency'_`k'_median_cell_n") (r(p50))
        quietly count if nobs==1
        post `flow' ("`frequency'_`k'_cells_n_one_retained") (r(N))
        restore
    }
}

* Monthly item-level household coverage, including explicit zeros in active months.
use `raw', clear
collapse (sum) spend=spend_pos, by(hh_id ym cat category)
tempfile item_month
save `item_month', replace
use `base9', clear
keep hh_id ym
expand 21
bysort hh_id ym: gen byte cat=_n
merge 1:1 hh_id ym cat using `item_month', keep(match master) nogen
replace spend=0 if missing(spend)
gen byte purchased=spend>0
collapse (mean) mean_spend=spend purchase_rate=purchased (p50) median_spend=spend (p95) p95_spend=spend (p99) p99_spend=spend (max) max_spend=spend (count) active_household_months=spend, by(cat)
gen str32 category=""
forvalues j=1/21 {
    local c: word `j' of `categories'
    replace category="`c'" if cat==`j'
}
export delimited using "$run/outputs/data_audit/item_active_month_descriptives.csv", replace

* Common coverage and zero-pattern diagnostics across genuine windows.
tempname freq
postfile `freq' byte k str12 frequency byte good double n_windows double purchase_rate double mean_share double mean_m double all_positive_rate using "$run/outputs/data_audit/frequency_diagnostics.dta", replace
foreach k in 8 9 {
    foreach frequency in month quarter year {
        use "$run/data/household_`frequency'_`k'.dta", clear
        keep if m>0
        gen byte all_positive=1
        forvalues j=1/`k' {
            replace all_positive=0 if spend`j'==0
        }
        quietly summarize all_positive, meanonly
        local allpos=r(mean)
        quietly summarize m, meanonly
        local meanm=r(mean)
        local nn=_N
        forvalues j=1/`k' {
            quietly count if spend`j'>0
            local rate=r(N)/`nn'
            quietly summarize w`j', meanonly
            post `freq' (`k') ("`frequency'") (`j') (`nn') (`rate') (r(mean)) (`meanm') (`allpos')
        }
    }
}
postclose `freq'
use "$run/outputs/data_audit/frequency_diagnostics.dta", clear
export delimited using "$run/outputs/data_audit/frequency_diagnostics.csv", replace
postclose `flow'
use "$run/outputs/data_audit/sample_flow.dta", clear
export delimited using "$run/outputs/data_audit/sample_flow.csv", replace
log close
