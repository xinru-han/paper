version 17
clear all
set more off
set type double
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_refresh_descriptives.log", text replace
use "$run/data/transactions_audit_cache.dta", clear
describe spend volume price
foreach v in spend volume price {
    local t : type `v'
    assert "`t'"=="double"
}
local categories 大米 面粉 挂面 方便面 食用油 蔬菜 水果 猪肉 禽类 其他肉类 牛肉 羊肉 海鲜类 常温牛奶 新鲜牛奶 常温酸奶 新鲜酸奶 奶酪 黄油 成人奶粉 坚果
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
use "$run/outputs/data_audit/item_transaction_descriptives.dta", clear
export delimited using "$run/outputs/data_audit/item_transaction_descriptives.csv", replace
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
log close
