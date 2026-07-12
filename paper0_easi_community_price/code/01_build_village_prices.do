version 17
do "$EASI_CODE/00_config.do"

* Village questionnaire prices are used exclusively. Household unit values are
* never used as demand-system prices.
use "$EASI_RAW/村表数据_已清洗.dta", clear
rename xzcCode_clean village_id
replace village_id = strtrim(village_id)
assert strlen(village_id) == 12
isid village_id data_year
gen str9 town_id = substr(village_id, 1, 9)
gen str6 county_id = substr(village_id, 1, 6)
gen str2 province_id = substr(village_id, 1, 2)

* Each group price is the median of valid product-level market quotes from all
* available outlets. For an item with both endpoints, hp/lp are both included;
* the within-group median prevents a single high-priced variety driving price.
local g1 "chaoshi01 zhd01 zysc01"
local g2 "chaoshi02 zhd02 zysc02"
local g3 "chaoshi03 zhd03 zysc03 meat01"
local g4 "chaoshi06 zhd06 zysc06"
local g5 "chaoshi07 zhd07 zysc07"
local g6 "chaoshi08 zhd08 zysc08"

forvalues g = 1/6 {
    local quotes ""
    foreach stem of local g`g' {
        ds `stem'_*_hp `stem'_*_lp, has(type numeric)
        local quotes "`quotes' `r(varlist)'"
    }
    foreach v of local quotes {
        replace `v' = . if `v' <= 0 | `v' > 200
    }
    egen p`g'_village = rowmedian(`quotes')
    gen byte p`g'_source = cond(!missing(p`g'_village), 1, .)
}

keep village_id data_year town_id county_id province_id vilLat vilLon p*_village p*_source
tempfile village base town county province nearest
save `village'

* First fallback: the median price among villages in the same township-year.
preserve
    collapse (median) p1_village p2_village p3_village p4_village p5_village p6_village, by(town_id data_year)
    rename p1_village t1
    rename p2_village t2
    rename p3_village t3
    rename p4_village t4
    rename p5_village t5
    rename p6_village t6
    save `town'
restore
merge m:1 town_id data_year using `town', nogen
forvalues g = 1/6 {
    replace p`g'_village = t`g' if missing(p`g'_village) & !missing(t`g')
    replace p`g'_source = 2 if missing(p`g'_source) & !missing(t`g')
}
drop t1-t6
save `base'

* Second fallback: geographically nearest reporting village in the same county-year.
* This uses straight-line great-circle distance and is only applied after the
* same-township median; no household-level prices enter the donor pool.
preserve
    keep village_id data_year county_id vilLat vilLon p1_village-p6_village
    rename village_id donor_id
    rename vilLat donor_lat
    rename vilLon donor_lon
    forvalues g = 1/6 {
        rename p`g'_village donor_p`g'
    }
    save `nearest'
restore
keep village_id data_year county_id vilLat vilLon p1_village-p6_village p1_source-p6_source
joinby county_id data_year using `nearest'
drop if village_id == donor_id
gen double km = 6371 * acos(min(1, max(-1, sin(vilLat*_pi/180)*sin(donor_lat*_pi/180) + cos(vilLat*_pi/180)*cos(donor_lat*_pi/180)*cos((donor_lon-vilLon)*_pi/180))))
forvalues g = 1/6 {
    bysort village_id data_year: egen double min_km`g' = min(cond(missing(p`g'_village) & donor_p`g' > 0, km, .))
    bysort village_id data_year: egen double near_p`g' = max(cond(km == min_km`g' & donor_p`g' > 0, donor_p`g', .))
}
keep village_id data_year near_p1-near_p6
duplicates drop
isid village_id data_year
save `nearest'

use `base', clear
merge 1:1 village_id data_year using `nearest', nogen
forvalues g = 1/6 {
    replace p`g'_village = near_p`g' if missing(p`g'_village) & near_p`g' > 0
    replace p`g'_source = 3 if missing(p`g'_source) & near_p`g' > 0
}
drop near_p1-near_p6

* Final deterministic fallbacks: county-year then province-year median.
preserve
    collapse (median) p1_village p2_village p3_village p4_village p5_village p6_village, by(county_id data_year)
    rename p1_village c1
    rename p2_village c2
    rename p3_village c3
    rename p4_village c4
    rename p5_village c5
    rename p6_village c6
    save `county'
restore
merge m:1 county_id data_year using `county', nogen
forvalues g = 1/6 {
    replace p`g'_village = c`g' if missing(p`g'_village) & c`g' > 0
    replace p`g'_source = 4 if missing(p`g'_source) & c`g' > 0
}
drop c1-c6
preserve
    collapse (median) p1_village p2_village p3_village p4_village p5_village p6_village, by(province_id data_year)
    rename p1_village r1
    rename p2_village r2
    rename p3_village r3
    rename p4_village r4
    rename p5_village r5
    rename p6_village r6
    save `province'
restore
merge m:1 province_id data_year using `province', nogen
forvalues g = 1/6 {
    replace p`g'_village = r`g' if missing(p`g'_village) & r`g' > 0
    replace p`g'_source = 5 if missing(p`g'_source) & r`g' > 0
    assert p`g'_village > 0 if !missing(p`g'_village)
}
drop r1-r6
label define price_source 1 "own village" 2 "town median" 3 "nearest county village" 4 "county median" 5 "province median"
forvalues g = 1/6 {
    label values p`g'_source price_source
}

* The household roster contains two village-year keys absent from the village
* questionnaire. Retain them in the analysis universe and assign prices only
* from the documented geographic fallback hierarchy; do not discard them.
tempfile completed hhkeys
save `completed'
use "$EASI_RAW/户表数据_已清洗.dta", clear
keep nhCode data_year vilLat vilLon
gen str12 village_id = substr(strtrim(nhCode), 1, 12)
drop nhCode
collapse (median) vilLat vilLon, by(village_id data_year)
gen str9 town_id = substr(village_id, 1, 9)
gen str6 county_id = substr(village_id, 1, 6)
gen str2 province_id = substr(village_id, 1, 2)
save `hhkeys'
use `hhkeys', clear
merge 1:1 village_id data_year using `completed', keep(master match) ///
    keepusing(p1_village-p6_village p1_source-p6_source) nogen
forvalues g = 1/6 {
    bysort town_id data_year: egen double hh_town`g' = median(p`g'_village)
    replace p`g'_village = hh_town`g' if missing(p`g'_village) & hh_town`g' > 0
    replace p`g'_source = 6 if missing(p`g'_source) & hh_town`g' > 0
    drop hh_town`g'
    bysort county_id data_year: egen double hh_county`g' = median(p`g'_village)
    replace p`g'_village = hh_county`g' if missing(p`g'_village) & hh_county`g' > 0
    replace p`g'_source = 7 if missing(p`g'_source) & hh_county`g' > 0
    drop hh_county`g'
    bysort province_id data_year: egen double hh_province`g' = median(p`g'_village)
    replace p`g'_village = hh_province`g' if missing(p`g'_village) & hh_province`g' > 0
    replace p`g'_source = 8 if missing(p`g'_source) & hh_province`g' > 0
    drop hh_province`g'
    assert p`g'_village > 0 & p`g'_village < .
}
label define price_source 6 "missing village: town median" 7 "missing village: county median" 8 "missing village: province median", add
forvalues g = 1/6 {
    label values p`g'_source price_source
}
isid village_id data_year
compress
save "$EASI_DATA/village_community_prices.dta", replace
export delimited using "$EASI_OUT/village_community_prices.csv", replace
