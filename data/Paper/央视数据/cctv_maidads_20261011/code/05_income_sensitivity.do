version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$ROOT/logs/05_income_sensitivity.log",text replace
tempname results
postfile `results' str24 specification byte type double observations double mean_slope double min_slope double max_slope double factor_10 double factor_50 double factor_100 using "$ROOT/outputs/income/sensitivity.dta",replace
foreach spec in posterior_linear midpoint_top15000 midpoint_top20000 midpoint_top25000 size_low size_high {
    use "$ROOT/data/household_quarter_income_8.dta",clear
    keep if m>0 & m<.
    gen double lny=lnypc_mean
    gen double outcome=ln(m)
    if strpos("`spec'","midpoint") {
        local top=real(substr("`spec'",13,.))
        gen double income_point=cond(income_band==1,2500,cond(income_band==2,6000,cond(income_band==3,8000,cond(income_band==4,10500,`top'))))
        replace lny=ln(income_point/size_proxy)
    }
    if inlist("`spec'","size_low","size_high") {
        gen double size_alt=cond(size_band==1,cond("`spec'"=="size_low",1,2),cond(size_band==2,3,cond(size_band==3,4,cond("`spec'"=="size_low",5,6))))
        replace lny=lnypc_mean+ln(size_proxy/size_alt)
        replace outcome=ln(m*size_proxy/size_alt)
    }
    quietly summarize lny,meanonly
    replace lny=lny-r(mean)
    quietly regress outcome c.lny i.type c.lny#i.type i.size_band i.province i.time rp1-rp7
    scalar NS=e(N)
    gen double slope=_b[lny]
    forvalues t=2/4 {
        replace slope=slope+_b[`t'.type#c.lny] if type==`t'
    }
    forvalues t=1/4 {
        quietly summarize slope if type==`t',meanonly
        post `results' ("`spec'") (`t') (scalar(NS)) (r(mean)) (r(min)) (r(max)) (1.1^r(mean)) (1.5^r(mean)) (2^r(mean))
    }
}
postclose `results'
use "$ROOT/outputs/income/sensitivity.dta",clear
export delimited using "$ROOT/outputs/income/sensitivity.csv",replace
use "$ROOT/data/household_quarter_income_8.dta",clear
keep if m>0 & m<.
gen double outcome=ln(m)
quietly regress outcome i.income_band##i.type i.size_band i.province i.time rp1-rp7
estimates save "$ROOT/outputs/income/discrete_band_projection.ster",replace
quietly margins type#income_band
matrix DB=r(table)'
clear
svmat double DB,names(col)
gen byte type=ceil(_n/5)
gen byte income_band=mod(_n-1,5)+1
gen double adjusted_geometric_budget=exp(b)
keep type income_band b adjusted_geometric_budget
export delimited using "$ROOT/outputs/income/discrete_band_adjusted_budget.csv",replace
use "$ROOT/data/household_quarter_income_8.dta",clear
keep if year==2022 & m>0
collapse (min) min_lny=lnypc_mean (p1) p1_lny=lnypc_mean (p99) p99_lny=lnypc_mean (max) max_lny=lnypc_mean,by(type)
save "$ROOT/data/income_support_8.dta",replace
export delimited using "$ROOT/outputs/income/observed_proxy_support.csv",replace
log close
