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

    * Count genuinely distinct outlet observations. The questionnaire repeats
    * each representative-product field across category rows, so the raw
    * column count is not independent price support.
    egen int rep`g'_outlet_count = rownonmiss(`representative')
    egen double rep`g'_raw = rowmedian(`representative')
    egen double range`g'_raw = rowmedian(`midranges')
    gen double rep`g'_before_screen = rep`g'_raw
    egen double rep`g'_min = rowmin(`representative')
    egen double rep`g'_max = rowmax(`representative')
    gen byte rep`g'_outlet_dispersion = rep`g'_max / rep`g'_min > 4 ///
        if rep`g'_min > 0 & rep`g'_max < .
    quietly count if rep`g'_outlet_dispersion == 1
    post `amem' (`g') ("representative_outlet_ratio_above_four") (r(N))

    * A low quote repeated across nearby villages is market information, not
    * an isolated tail error. Protect a representative price when at least two
    * villages in the same town-year report prices within a 25 percent log
    * band around their town median. This protection applies only to the lower
    * tail; implausibly high values remain subject to the symmetric screen.
    gen double ln_local_rep`g' = ln(rep`g'_raw) if rep`g'_raw > 0
    bysort town_id data_year: egen double town_med_ln_rep`g' = median(ln_local_rep`g')
    bysort town_id data_year: egen int town_n_rep`g' = count(ln_local_rep`g')
    gen byte rep`g'_local_corroborated = town_n_rep`g' >= 2 & ///
        abs(ln_local_rep`g' - town_med_ln_rep`g') <= ln(1.25) ///
        if !missing(ln_local_rep`g')

    * Remove isolated data-entry errors separately within survey year. The
    * five-MAD rule acts on logs and therefore treats proportional deviations
    * symmetrically without imposing a category-specific market-price cap.
    foreach kind in rep range {
        gen double ln_`kind'`g' = ln(`kind'`g'_raw) if `kind'`g'_raw > 0
        bysort province_id data_year: egen double med_`kind'`g' = median(ln_`kind'`g')
        gen double ad_`kind'`g' = abs(ln_`kind'`g' - med_`kind'`g')
        bysort province_id data_year: egen double mad_`kind'`g' = median(ad_`kind'`g')
        local local_protection ""
        if "`kind'" == "rep" {
            local local_protection "& !(ln_rep`g' < med_rep`g' & rep`g'_local_corroborated == 1)"
        }
        gen byte out_`kind'`g' = ad_`kind'`g' > 5 * 1.4826 * mad_`kind'`g' ///
            `local_protection' if !missing(ad_`kind'`g') & mad_`kind'`g' > 0
        quietly count if out_`kind'`g' == 1
        post `amem' (`g') ("`kind'_five_MAD_outliers") (r(N))
        replace `kind'`g'_raw = . if out_`kind'`g' == 1
    }

    * Store the robust lower-tail score before calibrating the independent
    * broad-category audit price below.
    gen double rep`g'_weak_low_z = ///
        (ln_rep`g' - med_rep`g') / (1.4826 * mad_rep`g') ///
        if mad_rep`g' > 0 & !missing(ln_rep`g')
    gen byte rep`g'_lower_mad_protected = ///
        ad_rep`g' > 5 * 1.4826 * mad_rep`g' & ///
        ln_rep`g' < med_rep`g' & rep`g'_local_corroborated == 1 ///
        if !missing(ad_rep`g') & mad_rep`g' > 0

    * Calibrate the broad-category midpoint to the representative basket in
    * overlapping villages, separately by year. This prevents a method switch
    * from creating a spurious price-level shift.
    gen double lnratio`g' = ln(rep`g'_raw / range`g'_raw) if rep`g'_raw > 0 & range`g'_raw > 0
    bysort data_year: egen double adj`g' = median(lnratio`g')
    quietly summarize lnratio`g', detail
    local overall_adj = r(p50)
    replace adj`g' = `overall_adj' if missing(adj`g')
    gen double range`g'_cal = range`g'_raw * exp(adj`g')

    * A single-outlet lower-tail quote receives a stricter one-sided check.
    * It is removed only when neither nearby villages nor the independently
    * reported broad-category price corroborates it within a 25 percent log
    * band. This targets weak measurement support without imposing a minimum.
    gen byte rep`g'_range_corroborated = range`g'_cal > 0 & rep`g'_raw > 0 & ///
        abs(ln(rep`g'_raw / range`g'_cal)) <= ln(1.25)
    gen byte out_rep`g'_weak_low = rep`g'_outlet_count == 1 & ///
        rep`g'_weak_low_z < -3 & rep`g'_local_corroborated != 1 & ///
        rep`g'_range_corroborated != 1 if !missing(rep`g'_weak_low_z)
    quietly count if out_rep`g'_weak_low == 1
    post `amem' (`g') ("single_outlet_uncorroborated_lower_tail") (r(N))
    quietly count if rep`g'_lower_mad_protected == 1
    post `amem' (`g') ("locally_corroborated_lower_tail_retained") (r(N))
    quietly count if rep`g'_range_corroborated == 1
    post `amem' (`g') ("broad_category_price_corroborated") (r(N))
    replace rep`g'_raw = . if out_rep`g'_weak_low == 1

    gen double p`g'_direct = rep`g'_raw
    gen byte p`g'_direct_method = 1 if !missing(rep`g'_raw)
    gen int p`g'_outlet_count = rep`g'_outlet_count
    gen byte p`g'_weak_low_flag = out_rep`g'_weak_low
    gen byte p`g'_local_corroborated = rep`g'_local_corroborated
    gen byte p`g'_range_corroborated = rep`g'_range_corroborated
    gen byte p`g'_lower_mad_protected = rep`g'_lower_mad_protected
    gen byte p`g'_five_mad_flag = out_rep`g'

    * The main donor pool contains comparable representative products only.
    * Broad high/low category midpoints remain an audit series: for oil in
    * particular, their cross-quality spread is not a retail price for one
    * comparable good and can contaminate spatial donors.
    gen double ln_direct`g' = ln(p`g'_direct) if p`g'_direct > 0
    bysort province_id data_year: egen double med_direct`g' = median(ln_direct`g')
    gen double ad_direct`g' = abs(ln_direct`g' - med_direct`g')
    bysort province_id data_year: egen double mad_direct`g' = median(ad_direct`g')
    gen byte out_direct`g' = ad_direct`g' > 5 * 1.4826 * mad_direct`g' ///
        & !(ln_direct`g' < med_direct`g' & p`g'_local_corroborated == 1) ///
        if !missing(ad_direct`g') & mad_direct`g' > 0
    quietly count if out_direct`g' == 1
    post `amem' (`g') ("combined_direct_five_MAD_outliers") (r(N))
    replace p`g'_direct = . if out_direct`g' == 1
    replace p`g'_direct_method = . if out_direct`g' == 1
    replace p`g'_five_mad_flag = 1 if out_direct`g' == 1

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

    * The raw village file is close to Stata/BE's 2,048-variable limit. Once a
    * food group has been reduced to its retained price and audit fields, drop
    * its repeated questionnaire columns and construction-only intermediates.
    capture drop `representative' `midranges'
    forvalues o = 1/`outlet' {
        capture drop hp`g'_`o' lp`g'_`o' wide`g'_`o'
    }
    capture drop rep`g'_min rep`g'_max rep`g'_outlet_dispersion ///
        ln_local_rep`g' town_med_ln_rep`g' town_n_rep`g' ///
        ln_rep`g' med_rep`g' ad_rep`g' mad_rep`g' out_rep`g' ///
        ln_range`g' med_range`g' ad_range`g' mad_range`g' out_range`g' ///
        range`g'_raw lnratio`g' adj`g' ln_direct`g' med_direct`g' ///
        ad_direct`g' mad_direct`g' out_direct`g'
    foreach stem of local g`g' {
        capture drop `stem'_*
    }
}
postclose `amem'
preserve
    use `quoteaudit', clear
    export delimited using "$AR_OUT/price_quote_audit.csv", replace
restore

preserve
    keep village_id data_year province_id ///
        rep1_before_screen rep2_before_screen rep3_before_screen ///
        rep4_before_screen rep5_before_screen rep6_before_screen ///
        rep1_raw rep2_raw rep3_raw rep4_raw rep5_raw rep6_raw ///
        rep1_outlet_count rep2_outlet_count rep3_outlet_count ///
        rep4_outlet_count rep5_outlet_count rep6_outlet_count ///
        rep1_weak_low_z rep2_weak_low_z rep3_weak_low_z ///
        rep4_weak_low_z rep5_weak_low_z rep6_weak_low_z ///
        out_rep1_weak_low out_rep2_weak_low out_rep3_weak_low ///
        out_rep4_weak_low out_rep5_weak_low out_rep6_weak_low ///
        rep1_local_corroborated rep2_local_corroborated ///
        rep3_local_corroborated rep4_local_corroborated ///
        rep5_local_corroborated rep6_local_corroborated ///
        rep1_range_corroborated rep2_range_corroborated ///
        rep3_range_corroborated rep4_range_corroborated ///
        rep5_range_corroborated rep6_range_corroborated ///
        rep1_lower_mad_protected rep2_lower_mad_protected ///
        rep3_lower_mad_protected rep4_lower_mad_protected ///
        rep5_lower_mad_protected rep6_lower_mad_protected ///
        range1_cal range2_cal range3_cal range4_cal range5_cal range6_cal ///
        p1_direct p2_direct p3_direct p4_direct p5_direct p6_direct
    export delimited using "$AR_OUT/representative_vs_midrange_prices.csv", replace
restore

keep village_id data_year town_id county_id province_id vilLat vilLon ///
    p*_direct p*_direct_method p*_outlet_count p*_weak_low_flag ///
    p*_local_corroborated p*_range_corroborated ///
    p*_lower_mad_protected p*_five_mad_flag
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
use "$AR_DATA/household_core.dta", clear
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
    p5_direct_method p6_direct_method p1_outlet_count p2_outlet_count ///
    p3_outlet_count p4_outlet_count p5_outlet_count p6_outlet_count ///
    p1_weak_low_flag p2_weak_low_flag p3_weak_low_flag p4_weak_low_flag ///
    p5_weak_low_flag p6_weak_low_flag p1_local_corroborated ///
    p2_local_corroborated p3_local_corroborated p4_local_corroborated ///
    p5_local_corroborated p6_local_corroborated p1_lower_mad_protected ///
    p1_range_corroborated p2_range_corroborated p3_range_corroborated ///
    p4_range_corroborated p5_range_corroborated p6_range_corroborated ///
    p2_lower_mad_protected p3_lower_mad_protected p4_lower_mad_protected ///
    p5_lower_mad_protected p6_lower_mad_protected p1_five_mad_flag ///
    p2_five_mad_flag p3_five_mad_flag p4_five_mad_flag ///
    p5_five_mad_flag p6_five_mad_flag) gen(village_merge)
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
