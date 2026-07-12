version 17
do "$EASI_CODE/00_config.do"

use "$EASI_RAW/户表数据_已清洗.dta", clear
rename nhCode household_id
replace household_id = strtrim(household_id)
assert strlen(household_id) == 14 if household_id != ""
gen str12 village_id = substr(household_id, 1, 12)
isid household_id

* Six mutually exclusive demand groups, in the same physical unit (jin).
rename zhushi_cons_monthly_jin q1
rename doulei_cons_monthly_jin q2
rename roulei_cons_monthly_jin q3
rename youzhi_cons_monthly_jin q4
rename shucai_cons_monthly_jin q5
rename shuiguo_cons_monthly_jin q6
forvalues g = 1/6 {
    replace q`g' = . if q`g' < 0
}

merge m:1 village_id data_year using "$EASI_DATA/village_community_prices.dta", keep(master match) gen(price_merge)
preserve
    contract price_merge
    export delimited using "$EASI_OUT/household_village_merge_audit.csv", replace
restore
drop if price_merge != 3
drop price_merge vilLat vilLon town_id county_id province_id

forvalues g = 1/6 {
    rename p`g'_village p`g'
    assert p`g' > 0 & p`g' < .
    gen double v`g' = p`g' * q`g'
}
egen double food_exp = rowtotal(v1-v6)
egen byte q_missing = rowmiss(q1-q6)
drop if q_missing > 0 | food_exp <= 0
drop q_missing
forvalues g = 1/6 {
    gen double s`g' = v`g' / food_exp
    assert inrange(s`g', 0, 1)
    gen double lnp`g' = ln(p`g')
}
egen double share_sum = rowtotal(s1-s6)
assert abs(share_sum - 1) < 1e-10
gen double ln_foodexp = ln(food_exp)

* Demand shifters are deliberately parsimonious; province and year absorb broad
* geographic/time effects while price variation remains at the village level.
rename HA0 hhsize
replace hhsize = . if hhsize <= 0
drop if missing(hhsize)
tabulate prov, generate(province_)
tabulate data_year, generate(year_)
drop province_1 year_1
unab province_fe : province_*
unab year_fe : year_*
global EASI_Z "hhsize `province_fe' `year_fe'"

order household_id village_id data_year q1-q6 p1-p6 p1_source-p6_source v1-v6 s1-s6 food_exp ln_foodexp hhsize
label var food_exp "Six-group monthly food expenditure using village community prices"
label var p1 "Community price: staple foods"
label var p2 "Community price: beans and bean products"
label var p3 "Community price: meat"
label var p4 "Community price: edible oils"
label var p5 "Community price: vegetables"
label var p6 "Community price: fruit"
compress
save "$EASI_DATA/easi_analysis_ready.dta", replace
