version 17
clear all
set more off
set type double
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/00_config.do"
cap mkdir "$ROOT/outputs/paper"
cap mkdir "$ROOT/outputs/figures"
cap mkdir "$ROOT/outputs/welfare"
log using "$ROOT/logs/10_paper_data.log",text replace
use "$ROOT/data/basket_weights_2021.dta",clear
collapse (sum) priced_spend_2021=spend_2021,by(g)
rename g good
tempfile coverage
save `coverage',replace
use "$ROOT/data/analysis_monthly.dta",clear
tempname desc audit freqs
postfile `desc' byte good double mean_share double purchase_rate double mean_share_buyers double sd_share double mean_spend double spend_2021 using "$ROOT/outputs/paper/descriptives.dta",replace
forvalues j=1/8 {
    quietly summarize w`j'
    local wm=r(mean)
    local ws=r(sd)
    quietly summarize pos`j',meanonly
    local pr=r(mean)
    quietly summarize w`j' if pos`j',meanonly
    local wb=r(mean)
    quietly summarize spend`j',meanonly
    local sm=r(mean)
    quietly summarize spend`j' if year==2021,meanonly
    post `desc' (`j') (`wm') (`pr') (`wb') (`ws') (`sm') (r(sum))
}
postclose `desc'
preserve
use "$ROOT/outputs/paper/descriptives.dta",clear
merge 1:1 good using `coverage',assert(match) nogen
gen double coverage=priced_spend_2021/spend_2021
assert coverage>0 & coverage<=1+1e-9
save "$ROOT/outputs/paper/descriptives.dta",replace
export delimited using "$ROOT/outputs/paper/descriptives.csv",replace
restore
postfile `audit' str48 statistic double value using "$ROOT/outputs/paper/sample_statistics.dta",replace
post `audit' ("active_household_months") (_N)
egen byte hh_tag=tag(hh_id)
quietly count if hh_tag
post `audit' ("households") (r(N))
quietly summarize total_food_spend_month,detail
post `audit' ("mean_monthly_food_spend") (r(mean))
post `audit' ("median_monthly_food_spend") (r(p50))
quietly summarize total_food_spend_pc_month,meanonly
post `audit' ("mean_proxy_per_capita_food_spend") (r(mean))
gen double add_error=abs(w1+w2+w3+w4+w5+w6+w7+w8-1)
quietly summarize add_error,meanonly
post `audit' ("budget_share_max_adding_error") (r(max))
post `audit' ("eight_group_household_month_cells") (8*_N)
postclose `audit'
preserve
sort income_group_order hh_id ym
by income_group_order hh_id: gen byte inc_hh=_n==1
collapse (sum) households=inc_hh (count) household_months=hh_id (mean) mean_food_spend=total_food_spend_month mean_food_spend_pc=total_food_spend_pc_month,by(income_group_order)
export delimited using "$ROOT/outputs/paper/income_descriptives.csv",replace
restore
postfile `freqs' str12 frequency byte good double active_windows double purchase_rate double mean_share double median_active_months using "$ROOT/outputs/paper/purchase_frequency.dta",replace
foreach frequency in monthly quarterly annual {
    preserve
    gen int period=ym
    if "`frequency'"=="quarterly" replace period=qofd(dofm(ym))
    if "`frequency'"=="annual" replace period=year
    collapse (sum) spend1 spend2 spend3 spend4 spend5 spend6 spend7 spend8 (count) active_months=ym,by(hh_id period)
    egen double total=rowtotal(spend1 spend2 spend3 spend4 spend5 spend6 spend7 spend8)
    assert total>0
    local nw=_N
    quietly summarize active_months,detail
    local am=r(p50)
    forvalues j=1/8 {
        gen byte buy`j'=spend`j'>0
        gen double share`j'=spend`j'/total
        quietly summarize buy`j',meanonly
        local pr=r(mean)
        quietly summarize share`j',meanonly
        post `freqs' ("`frequency'") (`j') (`nw') (`pr') (r(mean)) (`am')
    }
    restore
}
postclose `freqs'
foreach f in sample_statistics purchase_frequency {
    preserve
    use "$ROOT/outputs/paper/`f'.dta",clear
    export delimited using "$ROOT/outputs/paper/`f'.csv",replace
    restore
}
* Residual price variance uses the complete equally weighted external price grid.
use "$ROOT/data/group_prices_external_long.dta",clear
encode province_name,gen(province)
gen int year=year(dofm(ym))
gen byte month=month(dofm(ym))
tempname pv
postfile `pv' byte good double variance double residual_prov_month_year double residual_prov_ym using "$ROOT/outputs/paper/price_variation.dta",replace
forvalues j=1/8 {
    quietly summarize lp_ext if g==`j'
    local totalvar=r(Var)
    quietly regress lp_ext i.province i.month i.year if g==`j'
    predict double rr if e(sample),resid
    quietly summarize rr
    local r1=r(Var)/`totalvar'
    drop rr
    quietly regress lp_ext i.province i.ym if g==`j'
    predict double rr if e(sample),resid
    quietly summarize rr
    post `pv' (`j') (`totalvar') (`r1') (r(Var)/`totalvar')
    drop rr
}
postclose `pv'
preserve
use "$ROOT/outputs/paper/price_variation.dta",clear
export delimited using "$ROOT/outputs/paper/price_variation.csv",replace
restore
collapse (mean) lp_ext,by(g ym)
bysort g (ym): gen double price_index=100*exp(lp_ext-lp_ext[1])
label define food 1 "Staples" 2 "Oils" 3 "Vegetables" 4 "Fruit" 5 "Pork" 6 "Other meat" 7 "Seafood" 8 "Dairy"
label values g food
format ym %tmCCYY!mNN
twoway line price_index ym,by(g,cols(2) yrescale note("")) ytitle("January 2020=100") xtitle("") graphregion(color(white)) name(pricegrid,replace)
graph export "$ROOT/figures/fig1_eight_group_prices.png",width(2400) replace
use "$ROOT/outputs/paper/descriptives.dta",clear
gen double share_pct=100*mean_share
gen double no_purchase_pct=100*(1-purchase_rate)
label values good food
graph bar share_pct no_purchase_pct,over(good,label(angle(30) labsize(small))) legend(order(1 "Mean budget share" 2 "No purchase in active month")) ytitle("Percent") graphregion(color(white)) name(zeros,replace)
graph export "$ROOT/figures/fig2_eight_group_budget.png",width(2400) replace
do "$ROOT/code/09b_exact_tests.do"
do "$ROOT/code/10b_policy_exposure.do"
do "$ROOT/code/10c_historical_exposure.do"
* Each called script has its own success marker and log; all mutations stay inside ROOT.
log using "$ROOT/logs/10_paper_data_final.log",text replace
foreach file in descriptives.csv sample_statistics.csv purchase_frequency.csv price_variation.csv {
    confirm file "$ROOT/outputs/paper/`file'"
}
confirm file "$ROOT/outputs/exact/engel_nested_tests.csv"
confirm file "$ROOT/outputs/welfare/policy_exposure.csv"
confirm file "$ROOT/outputs/welfare/policy_exposure_historical.csv"
display "EIGHT_PAPER_DATA_SUCCESS"
log close
