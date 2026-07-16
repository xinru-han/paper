version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_config.do"

* The village questionnaire reports all six modules in yuan per jin. Prices
* below are built only from those market quotes; household unit values are
* reserved for validation and never enter the main demand-system prices.
use "$AR_RAW/村表数据_已清洗.dta", clear
rename xzcCode_clean village_id
replace village_id = strtrim(village_id)
assert strlen(village_id) == 12
isid village_id data_year
gen str9 town_id = substr(village_id, 1, 9)
gen str6 county_id = substr(village_id, 1, 6)
gen str2 province_id = substr(village_id, 1, 2)

local g1 "chaoshi01 zhd01 zysc01"
local g2 "chaoshi02 zhd02 zysc02"
local g3 "chaoshi03 zhd03 zysc03 meat01"
local g4 "chaoshi06 zhd06 zysc06"
local g5 "chaoshi07 zhd07 zysc07"
local g6 "chaoshi08 zhd08 zysc08"

tempname amem
tempfile quoteaudit
postfile `amem' int group str40 statistic double value using `quoteaudit', replace

forvalues g = 1/6 {
    local representative ""
    local midranges ""
    local outlet = 0
    local invalid_rep = 0
    local invalid_range = 0
    local reversed = 0
    foreach stem of local g`g' {
        local ++outlet

        * Comparable representative products are explicitly requested by the
        * questionnaire (rice/flour, tofu/soybean, pork, rapeseed oil,
        * greens/cabbage, and apple/orange). Exclude the seed/nut mp3 field.
        quietly ds `stem'_*mp*, has(type numeric)
        local allmp "`r(varlist)'"
        local mpvars ""
        foreach v of local allmp {
            if regexm("`v'", "_(mp|mp1|mp2)$") local mpvars "`mpvars' `v'"
        }
        foreach v of local mpvars {
            quietly count if !missing(`v') & (`v' <= 0 | `v' > 200)
            local invalid_rep = `invalid_rep' + r(N)
            replace `v' = . if `v' <= 0 | `v' > 200
        }
        egen double rep`g'_`outlet' = rowmedian(`mpvars')
        local representative "`representative' rep`g'_`outlet'"

        * Secondary quote: the midpoint between the outlet's median high and
        * low category quotes. It is used only when representative products
        * are unavailable, after calibration to their common price level.
        quietly ds `stem'_*_hp, has(type numeric)
        local hpvars "`r(varlist)'"
        quietly ds `stem'_*_lp, has(type numeric)
        local lpvars "`r(varlist)'"
        if `g' == 6 {
            local freshhp ""
            local freshlp ""
            foreach v of local hpvars {
                if regexm("`v'", "^`stem'_0[1-4]_") local freshhp "`freshhp' `v'"
            }
            foreach v of local lpvars {
                if regexm("`v'", "^`stem'_0[1-4]_") local freshlp "`freshlp' `v'"
            }
            local hpvars "`freshhp'"
            local lpvars "`freshlp'"
        }
        foreach v of local hpvars {
            quietly count if !missing(`v') & (`v' <= 0 | `v' > 200)
            local invalid_range = `invalid_range' + r(N)
            replace `v' = . if `v' <= 0 | `v' > 200
        }
        foreach v of local lpvars {
            quietly count if !missing(`v') & (`v' <= 0 | `v' > 200)
            local invalid_range = `invalid_range' + r(N)
            replace `v' = . if `v' <= 0 | `v' > 200
        }
        egen double hp`g'_`outlet' = rowmedian(`hpvars')
        egen double lp`g'_`outlet' = rowmedian(`lpvars')
        quietly count if hp`g'_`outlet' < lp`g'_`outlet' & !missing(hp`g'_`outlet', lp`g'_`outlet')
        local reversed = `reversed' + r(N)
        tempvar lower upper
        gen double `lower' = min(hp`g'_`outlet', lp`g'_`outlet')
        gen double `upper' = max(hp`g'_`outlet', lp`g'_`outlet')
        replace hp`g'_`outlet' = `upper' if !missing(`upper')
        replace lp`g'_`outlet' = `lower' if !missing(`lower')
        gen byte wide`g'_`outlet' = hp`g'_`outlet' / lp`g'_`outlet' > 4 ///
            if hp`g'_`outlet' > 0 & lp`g'_`outlet' > 0
        quietly count if wide`g'_`outlet' == 1
        post `amem' (`g') ("outlet_`outlet'_range_ratio_above_four") (r(N))
        * High and low are prices of different quality items, not confidence
        * bounds. Their spread is audited but is not itself a deletion rule.
        gen double mid`g'_`outlet' = (hp`g'_`outlet' + lp`g'_`outlet') / 2
        replace mid`g'_`outlet' = hp`g'_`outlet' if missing(lp`g'_`outlet')
        replace mid`g'_`outlet' = lp`g'_`outlet' if missing(hp`g'_`outlet')
        local midranges "`midranges' mid`g'_`outlet'"
    }

    egen double rep`g'_raw = rowmedian(`representative')
    egen double range`g'_raw = rowmedian(`midranges')
    egen double rep`g'_min = rowmin(`representative')
    egen double rep`g'_max = rowmax(`representative')
    gen byte rep`g'_outlet_dispersion = rep`g'_max / rep`g'_min > 4 ///
        if rep`g'_min > 0 & rep`g'_max < .
    quietly count if rep`g'_outlet_dispersion == 1
    post `amem' (`g') ("representative_outlet_ratio_above_four") (r(N))

    * Remove isolated data-entry errors separately within survey year. The
    * five-MAD rule acts on logs and therefore treats proportional deviations
    * symmetrically without imposing a category-specific market-price cap.
    foreach kind in rep range {
        gen double ln_`kind'`g' = ln(`kind'`g'_raw) if `kind'`g'_raw > 0
        bysort province_id data_year: egen double med_`kind'`g' = median(ln_`kind'`g')
        gen double ad_`kind'`g' = abs(ln_`kind'`g' - med_`kind'`g')
        bysort province_id data_year: egen double mad_`kind'`g' = median(ad_`kind'`g')
        gen byte out_`kind'`g' = ad_`kind'`g' > 5 * 1.4826 * mad_`kind'`g' ///
            if !missing(ad_`kind'`g') & mad_`kind'`g' > 0
        quietly count if out_`kind'`g' == 1
        post `amem' (`g') ("`kind'_five_MAD_outliers") (r(N))
        replace `kind'`g'_raw = . if out_`kind'`g' == 1
    }

    * Calibrate the broad-category midpoint to the representative basket in
    * overlapping villages, separately by year. This prevents a method switch
    * from creating a spurious price-level shift.
    gen double lnratio`g' = ln(rep`g'_raw / range`g'_raw) if rep`g'_raw > 0 & range`g'_raw > 0
    bysort data_year: egen double adj`g' = median(lnratio`g')
    quietly summarize lnratio`g', detail
    local overall_adj = r(p50)
    replace adj`g' = `overall_adj' if missing(adj`g')
    gen double range`g'_cal = range`g'_raw * exp(adj`g')
    gen double p`g'_direct = rep`g'_raw
    gen byte p`g'_direct_method = 1 if !missing(rep`g'_raw)

    * The main donor pool contains comparable representative products only.
    * Broad high/low category midpoints remain an audit series: for oil in
    * particular, their cross-quality spread is not a retail price for one
    * comparable good and can contaminate spatial donors.
    gen double ln_direct`g' = ln(p`g'_direct) if p`g'_direct > 0
    bysort province_id data_year: egen double med_direct`g' = median(ln_direct`g')
    gen double ad_direct`g' = abs(ln_direct`g' - med_direct`g')
    bysort province_id data_year: egen double mad_direct`g' = median(ad_direct`g')
    gen byte out_direct`g' = ad_direct`g' > 5 * 1.4826 * mad_direct`g' ///
        if !missing(ad_direct`g') & mad_direct`g' > 0
    quietly count if out_direct`g' == 1
    post `amem' (`g') ("combined_direct_five_MAD_outliers") (r(N))
    replace p`g'_direct = . if out_direct`g' == 1
    replace p`g'_direct_method = . if out_direct`g' == 1

    quietly count if p`g'_direct_method == 1
    post `amem' (`g') ("representative_direct_villages") (r(N))
    quietly count if range`g'_cal > 0 & range`g'_cal < .
    post `amem' (`g') ("calibrated_midrange_audit_villages") (r(N))
    quietly count if missing(p`g'_direct)
    post `amem' (`g') ("villages_without_direct_quote") (r(N))
    post `amem' (`g') ("invalid_representative_quotes") (`invalid_rep')
    post `amem' (`g') ("invalid_high_low_quotes") (`invalid_range')
    post `amem' (`g') ("outlets_high_below_low") (`reversed')
    post `amem' (`g') ("midrange_log_calibration") (`overall_adj')
}
postclose `amem'
preserve
    use `quoteaudit', clear
    export delimited using "$AR_OUT/price_quote_audit.csv", replace
restore

preserve
    keep village_id data_year province_id ///
        rep1_raw rep2_raw rep3_raw rep4_raw rep5_raw rep6_raw ///
        range1_cal range2_cal range3_cal range4_cal range5_cal range6_cal ///
        p1_direct p2_direct p3_direct p4_direct p5_direct p6_direct
    export delimited using "$AR_OUT/representative_vs_midrange_prices.csv", replace
restore

keep village_id data_year town_id county_id province_id vilLat vilLon ///
    p*_direct p*_direct_method
tempfile donor hhkeys town county province nearest target
save `donor'

* Geographic fallback tables are always computed from direct village quotes,
* never from previously imputed prices. This avoids recursive donor weighting.
preserve
    collapse (median) p1_direct p2_direct p3_direct p4_direct p5_direct p6_direct, by(town_id data_year)
    rename p1_direct town_p1
    rename p2_direct town_p2
    rename p3_direct town_p3
    rename p4_direct town_p4
    rename p5_direct town_p5
    rename p6_direct town_p6
    save `town'
restore
preserve
    collapse (median) p1_direct p2_direct p3_direct p4_direct p5_direct p6_direct, by(county_id data_year)
    rename p1_direct county_p1
    rename p2_direct county_p2
    rename p3_direct county_p3
    rename p4_direct county_p4
    rename p5_direct county_p5
    rename p6_direct county_p6
    save `county'
restore
preserve
    collapse (median) p1_direct p2_direct p3_direct p4_direct p5_direct p6_direct, by(province_id data_year)
    rename p1_direct province_p1
    rename p2_direct province_p2
    rename p3_direct province_p3
    rename p4_direct province_p4
    rename p5_direct province_p5
    rename p6_direct province_p6
    save `province'
restore

* Build the target universe from household keys. This also incorporates the
* two household village-year keys absent from the village questionnaire.
use "$AR_RAW/户表数据_已清洗.dta", clear
keep nhCode data_year vilLat vilLon
gen str12 village_id = substr(strtrim(nhCode), 1, 12)
drop nhCode
collapse (median) vilLat vilLon, by(village_id data_year)
gen str9 town_id = substr(village_id, 1, 9)
gen str6 county_id = substr(village_id, 1, 6)
gen str2 province_id = substr(village_id, 1, 2)
merge 1:1 village_id data_year using `donor', ///
    keep(master match) keepusing(p1_direct p2_direct p3_direct p4_direct p5_direct p6_direct ///
    p1_direct_method p2_direct_method p3_direct_method p4_direct_method ///
    p5_direct_method p6_direct_method) gen(village_merge)
gen byte village_questionnaire_missing = village_merge == 1
drop village_merge
isid village_id data_year

forvalues g = 1/6 {
    gen double p`g'_village = p`g'_direct
    gen byte p`g'_source = p`g'_direct_method
}
merge m:1 town_id data_year using `town', keep(master match) nogen
forvalues g = 1/6 {
    replace p`g'_village = town_p`g' if missing(p`g'_village) & town_p`g' > 0
    replace p`g'_source = 3 if missing(p`g'_source) & !missing(p`g'_village)
}
drop town_p1 town_p2 town_p3 town_p4 town_p5 town_p6
save `target'

* Next fallback: nearest directly reporting village in the same county-year.
preserve
    use `donor', clear
    keep village_id data_year county_id vilLat vilLon p1_direct p2_direct ///
        p3_direct p4_direct p5_direct p6_direct
    rename village_id donor_id
    rename vilLat donor_lat
    rename vilLon donor_lon
    forvalues g = 1/6 {
        rename p`g'_direct donor_p`g'
    }
    save `nearest'
restore
keep village_id data_year county_id vilLat vilLon
joinby county_id data_year using `nearest'
drop if village_id == donor_id
gen double km = 6371 * acos(min(1, max(-1, ///
    sin(vilLat * _pi / 180) * sin(donor_lat * _pi / 180) + ///
    cos(vilLat * _pi / 180) * cos(donor_lat * _pi / 180) * ///
    cos((donor_lon - vilLon) * _pi / 180))))
forvalues g = 1/6 {
    bysort village_id data_year: egen double min_km`g' = min(cond(donor_p`g' > 0, km, .))
    bysort village_id data_year: egen double near_p`g' = mean(cond(km == min_km`g' & donor_p`g' > 0, donor_p`g', .))
}
keep village_id data_year near_p1 near_p2 near_p3 near_p4 near_p5 near_p6
duplicates drop
isid village_id data_year
save `nearest', replace

use `target', clear
merge 1:1 village_id data_year using `nearest', nogen
forvalues g = 1/6 {
    replace p`g'_village = near_p`g' if missing(p`g'_village) & near_p`g' > 0
    replace p`g'_source = 4 if missing(p`g'_source) & !missing(p`g'_village)
}
drop near_p1 near_p2 near_p3 near_p4 near_p5 near_p6

* Coarser medians remain based on the direct donor pool.
merge m:1 county_id data_year using `county', keep(master match) nogen
forvalues g = 1/6 {
    replace p`g'_village = county_p`g' if missing(p`g'_village) & county_p`g' > 0
    replace p`g'_source = 5 if missing(p`g'_source) & !missing(p`g'_village)
}
drop county_p1 county_p2 county_p3 county_p4 county_p5 county_p6
merge m:1 province_id data_year using `province', keep(master match) nogen
forvalues g = 1/6 {
    replace p`g'_village = province_p`g' if missing(p`g'_village) & province_p`g' > 0
    replace p`g'_source = 6 if missing(p`g'_source) & !missing(p`g'_village)
    assert p`g'_village > 0 & p`g'_village < .
}
drop province_p1 province_p2 province_p3 province_p4 province_p5 province_p6 ///
    p1_direct p2_direct p3_direct p4_direct p5_direct p6_direct ///
    p1_direct_method p2_direct_method p3_direct_method p4_direct_method ///
    p5_direct_method p6_direct_method

label define price_source 1 "own village: representative products" ///
    3 "same-town representative median" ///
    4 "nearest direct village in county" 5 "county direct median" ///
    6 "province direct median"
forvalues g = 1/6 {
    label values p`g'_source price_source
}
isid village_id data_year
compress
save "$AR_DATA/village_community_prices.dta", replace
export delimited using "$AR_OUT/village_community_prices.csv", replace
