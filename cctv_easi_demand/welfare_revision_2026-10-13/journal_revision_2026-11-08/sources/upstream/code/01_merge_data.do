version 17
clear all
set more off
set type double
set varabbrev off
set matsize 800
global ROOT "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
global OLD "/root/data/Paper/央视数据/Paper1-EASI/stata_rebuild_2026-10-10"
global SOURCE "/root/data/Paper/央视数据/Paper1-EASI"
log using "$ROOT/logs/01_merge_data.log",text replace
use "$OLD/data/basket_weights_2021.dta",clear
quietly summarize spend_2021 if g==6,meanonly
scalar spend6=r(sum)
quietly summarize spend_2021 if g==7,meanonly
scalar spend7=r(sum)
scalar poultry_weight=spend6/(spend6+spend7)
replace g=6 if g==7
replace g=g-1 if g>7
capture drop weight0 n_full
bysort g: egen double group_spend_2021=total(spend_2021)
gen double weight0=spend_2021/group_spend_2021
bysort g: gen byte n_full=_N
save "$ROOT/data/basket_weights_2021.dta",replace
export delimited using "$ROOT/outputs/audit/basket_weights_2021.csv",replace
list category spend_2021 weight0 if g==6,noobs
import delimited using "$SOURCE/processed/external_food_prices_category_province_month_2020_2022.csv",clear varnames(1) encoding("utf-8")
rename province province_name
keep if price_fill_level=="observed_province_month"
merge m:1 category using "$ROOT/data/basket_weights_2021.dta",keep(match) nogen
assert !missing(external_log_price)
gen int ym=monthly(year_month,"YM")
format ym %tm
gen double weighted_lp=weight0*external_log_price
collapse (sum) lp_ext=weighted_lp weight_sum=weight0 (count) n_cat=external_log_price (firstnm) n_full,by(province_name ym year_month g)
assert n_cat==n_full
assert abs(weight_sum-1)<1e-10
assert _N==24*36*8
isid province_name ym g
save "$ROOT/data/group_prices_external_long.dta",replace
export delimited using "$ROOT/outputs/audit/group_prices_external.csv",replace
keep province_name ym lp_ext g
reshape wide lp_ext,i(province_name ym) j(g)
forvalues j=1/8 {
    rename lp_ext`j' new_lp`j'
    quietly summarize new_lp`j',meanonly
    gen double new_p`j'=new_lp`j'-r(mean)
    gen double new_price`j'=exp(new_p`j')
}
tempfile prices
save `prices',replace
use "$OLD/data/analysis_monthly.dta",clear
assert _N==583668
isid hh_id ym
merge m:1 province_name ym using `prices',assert(match) nogen
assert abs(new_lp6-(poultry_weight*lp6+(1-poultry_weight)*lp7))<1e-10
forvalues j=1/5 {
    assert abs(new_lp`j'-lp`j')<1e-10
}
assert abs(new_lp7-lp8)<1e-10
assert abs(new_lp8-lp9)<1e-10
gen double old_share_total=w1+w2+w3+w4+w5+w6+w7+w8+w9
gen double old_spend_total=spend1+spend2+spend3+spend4+spend5+spend6+spend7+spend8+spend9
replace w6=w6+w7
replace spend6=spend6+spend7
replace pos6=spend6>0
forvalues j=7/8 {
    local k=`j'+1
    replace w`j'=w`k'
    replace spend`j'=spend`k'
    replace pos`j'=pos`k'
}
drop w9 spend9 pos9
assert abs(w1+w2+w3+w4+w5+w6+w7+w8-old_share_total)<1e-10
assert abs(spend1+spend2+spend3+spend4+spend5+spend6+spend7+spend8-old_spend_total)<1e-7
assert abs(old_spend_total-total_food_spend_month)<1e-7
drop old_share_total old_spend_total
forvalues j=1/9 {
    drop lp`j' p`j' price`j' sw`j' r`j' mn_r`j' yp`j'
    drop pcyc_bought_lag1_`j' pcyc_recency_`j' pcyc_nohist_`j'
}
drop stone_idx y y2 y_easi y_easi2 mean_y_hh
forvalues j=1/8 {
    rename new_lp`j' lp`j'
    rename new_p`j' p`j'
    rename new_price`j' price`j'
    label variable w`j' "Eight-group budget share G`j'"
    label variable spend`j' "Eight-group monthly expenditure G`j'"
    label variable pos`j' "Eight-group purchase indicator G`j'"
    label variable lp`j' "Eight-group fixed 2021 basket external log price G`j'"
}
label variable w6 "其他肉类：禽类、其他肉类、牛肉和羊肉"
label variable spend6 "其他肉类：禽类、其他肉类、牛肉和羊肉"
gen double stone_idx=0
forvalues j=1/8 {
    bysort province ym: egen double sw`j'=mean(w`j')
    replace stone_idx=stone_idx+sw`j'*lp`j'
}
gen double y=lnx-stone_idx
gen double y2=y^2
gen double y_easi=y
gen double y_easi2=y2
bysort hh_id: egen double mean_y_hh=mean(y)
forvalues j=1/8 {
    gen double r`j'=lp`j'-lp3
    bysort hh_id: egen double mn_r`j'=mean(r`j')
    gen double yp`j'=y*r`j'
}
sort hh_id ym
forvalues j=1/8 {
    by hh_id: gen byte pcyc_bought_lag1_`j'=(_n>1 & ym==ym[_n-1]+1 & pos`j'[_n-1]==1)
    by hh_id: gen int last_buy`j'=.
    by hh_id: replace last_buy`j'=cond(pos`j'[_n-1]==1,ym[_n-1],last_buy`j'[_n-1]) if _n>1
    gen byte pcyc_nohist_`j'=missing(last_buy`j')
    gen double pcyc_recency_`j'=cond(missing(last_buy`j'),0,1/(1+max(0,ym-last_buy`j')))
    drop last_buy`j'
}
capture confirm variable xquintile
if _rc xtile xquintile=total_food_spend_pc_month,nq(5)
assert abs(w1+w2+w3+w4+w5+w6+w7+w8-1)<1e-10
assert !missing(lp1,lp2,lp3,lp4,lp5,lp6,lp7,lp8)
compress
save "$ROOT/data/analysis_monthly.dta",replace
preserve
keep if pilot_hh
save "$ROOT/data/pilot.dta",replace
restore
tempname desc
postfile `desc' byte good double mean_share double purchase_rate double mean_spend using "$ROOT/outputs/audit/descriptives.dta",replace
forvalues j=1/8 {
    quietly summarize w`j',meanonly
    local wm=r(mean)
    quietly summarize pos`j',meanonly
    local pr=r(mean)
    quietly summarize spend`j',meanonly
    post `desc' (`j') (`wm') (`pr') (r(mean))
}
postclose `desc'
use "$ROOT/outputs/audit/descriptives.dta",clear
export delimited using "$ROOT/outputs/audit/descriptives.csv",replace
list,noobs
scalar list poultry_weight
file open done using "$ROOT/outputs/audit/data_success.txt",write replace
file write done "Data assertions passed; original sample and food expenditure unchanged." _n
file close done
display "MEAT_MERGE_DATA_SUCCESS"
log close
