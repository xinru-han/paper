version 17
clear all
set more off
set type double
args project
if `"`project'"' == "" local project "/root/data/Paper/央视数据/Paper1-EASI/welfare_revision_2026-10-13"
do "`project'/code/00_config.do"
local out "$REV/journal_revision_2026-11-08"
capture mkdir "`out'/outputs"
capture mkdir "`out'/logs"
capture log close _all
log using "`out'/logs/06_price_offset_check.log", text replace

* Use the archived fixed-basket definition, not the separate curvature/welfare fit.
use "$BASE/data/analysis_monthly.dta", clear
assert _N==583668
preserve
keep province ym lp1 lp2 lp3 lp4 lp5 lp6 lp7 lp8
bysort province ym: keep if _n==1
collapse (mean) lp1 lp2 lp3 lp4 lp5 lp6 lp7 lp8, by(ym)
reshape long lp, i(ym) j(good)
bysort good (ym): gen double price_index=100*exp(lp-lp[1])
label define food 1 "Staples" 2 "Oils" 3 "Vegetables" 4 "Fruit" ///
    5 "Pork" 6 "Other meat" 7 "Seafood" 8 "Dairy"
label values good food
export delimited using "`out'/outputs/price_paths.csv", replace
twoway line price_index ym, ///
    by(good, cols(2) yrescale compact note("") graphregion(color(white))) ///
    xlabel(720 "2020" 732 "2021" 744 "2022",labsize(small)) ///
    ylabel(#3,angle(horizontal) labsize(small) format(%4.0f)) ///
    ytitle("") xtitle("") graphregion(color(white)) ///
    lcolor("52 110 100") name(price_paths,replace)
graph export "`out'/outputs/price_paths.png", width(2400) replace
graph export "`out'/outputs/price_paths.pdf", replace
restore
preserve
keep province ym year lp1 lp2 lp3 lp4 lp5 lp6 lp7 lp8
bysort province ym: keep if _n==1
keep if inlist(year,2020,2022)
collapse (mean) lp1 lp2 lp3 lp4 lp5 lp6 lp7 lp8 (count) months=ym, by(province year)
assert months==12
reshape wide lp1 lp2 lp3 lp4 lp5 lp6 lp7 lp8 months, i(province) j(year)
forvalues j=1/8 {
    gen double delta`j'=exp(lp`j'2022-lp`j'2020)-1
}
tempfile shocks
save `shocks'
restore
keep if year==2020
merge m:1 province using `shocks', assert(match using) keep(match) nogen
assert _N==182676
egen double share_sum=rowtotal(w1 w2 w3 w4 w5 w6 w7 w8)
assert abs(share_sum-1)<1e-12
gen double cost_pct=0
forvalues j=1/8 {
    gen double component`j'=100*w`j'*delta`j'
    replace cost_pct=cost_pct+component`j'
}
gen double cost_yuan=cost_pct/100*total_food_spend_pc_month
gen double meat_pct=component5+component6
gen double nonmeat_pct=cost_pct-meat_pct
quietly summarize cost_pct, detail
scalar historical_mean=r(mean)
scalar historical_p10=r(p10)
scalar historical_p90=r(p90)
assert abs(historical_mean-2.973402578372977)<1e-9
quietly summarize cost_yuan, meanonly
scalar historical_yuan=r(mean)
assert abs(historical_yuan-4.427046612142189)<1e-9
quietly summarize meat_pct, meanonly
scalar meat_mean=r(mean)
quietly summarize nonmeat_pct, meanonly
scalar nonmeat_mean=r(mean)
assert meat_mean<0 & nonmeat_mean>0
assert abs(historical_mean-meat_mean-nonmeat_mean)<1e-10
scalar offset_pct=-100*meat_mean/nonmeat_mean
quietly summarize component5, meanonly
scalar pork_mean=r(mean)
quietly summarize component6, meanonly
scalar other_meat_mean=r(mean)
quietly count if cost_pct>0
scalar rising_share=r(N)/_N

tempname summary
postfile `summary' str32 statistic double value using "`out'/outputs/price_offset_summary.dta", replace
post `summary' ("baseline_household_months") (_N)
foreach s in historical_mean historical_yuan historical_p10 historical_p90 meat_mean nonmeat_mean pork_mean other_meat_mean offset_pct rising_share {
    post `summary' ("`s'") (`s')
}
postclose `summary'

tempname components
postfile `components' byte good double contribution_pp using "`out'/outputs/historical_components.dta", replace
forvalues j=1/8 {
    quietly summarize component`j', meanonly
    post `components' (`j') (r(mean))
}
postclose `components'
use "`out'/outputs/historical_components.dta", clear
isid good
quietly summarize contribution_pp, meanonly
assert abs(r(sum)-historical_mean)<1e-10
export delimited using "`out'/outputs/historical_components.csv", replace

use "`out'/outputs/price_offset_summary.dta", clear
isid statistic
export delimited using "`out'/outputs/price_offset_summary.csv", replace
list, noobs
clear
set obs 4
gen byte group=_n
gen double contribution_pp=.
replace contribution_pp=nonmeat_mean in 1
replace contribution_pp=pork_mean in 2
replace contribution_pp=other_meat_mean in 3
replace contribution_pp=historical_mean in 4
label define group 1 "Non-meat foods" 2 "Pork" 3 "Other meat" 4 "Net basket cost"
label values group group
twoway (bar contribution_pp group if group==1, color("52 132 112") barwidth(.7)) ///
    (bar contribution_pp group if group==2, color("186 78 86") barwidth(.7)) ///
    (bar contribution_pp group if group==3, color("142 155 90") barwidth(.7)) ///
    (bar contribution_pp group if group==4, color("74 86 100") barwidth(.7)) ///
    (scatter contribution_pp group, msymbol(none) mlabel(contribution_pp) ///
        mlabformat(%5.2f) mlabposition(12) mlabcolor(black) mlabsize(medium)), ///
    xlabel(1 "Non-meat foods" 2 "Pork" 3 "Other meat" 4 "Net basket cost",labsize(small)) ///
    ylabel(-4(2)8,angle(horizontal) labsize(small)) ///
    ytitle("Contribution (percentage points)",size(small)) xtitle("") ///
    yline(0,lcolor(gs8)) legend(off) graphregion(color(white)) ///
    xsize(7) ysize(4) name(price_offset,replace)
graph export "`out'/outputs/price_offset.png", width(2200) replace
graph export "`out'/outputs/price_offset.pdf", replace
display "PRICE_OFFSET_CHECK_SUCCESS"
log close
