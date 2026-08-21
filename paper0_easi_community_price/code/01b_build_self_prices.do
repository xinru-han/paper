version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

* Opportunity-cost prices for own-produced food come from question 08
* ("if sold, yuan/jin"). No household report is used as a household-specific
* price. An own-village median requires at least three reporting producers;
* every fallback is built only from independently eligible village medians,
* never from an imputed price or an ineligible target-village report.
use "$EASI_DATA/household_unit_values.dta", clear
gen str12 village_id = substr(strtrim(household_id), 1, 12)
merge m:1 village_id data_year using "$EASI_DATA/village_community_prices.dta", ///
    keep(match) keepusing(town_id county_id province_id vilLat vilLon p1_village ///
    p2_village p3_village p4_village p5_village p6_village) nogen

tempname amem
tempfile reports direct town towndonors county pratio yratio nearest targets audit
postfile `amem' int group str42 statistic double value using `audit', replace

forvalues g = 1/6 {
    gen double self_price_coverage`g' = self_price_covered_quantity`g' / ///
        self_consumed_quantity`g' if self_consumed_quantity`g' > 0 & ///
        self_consumed_quantity`g' < .
    gen double ln_selfuv`g' = ln(self_unit_value`g') ///
        if self_unit_value`g' > 0 & self_unit_value`g' < . & ///
        self_consumed_quantity`g' > 0 & self_consumed_quantity`g' < . & ///
        inrange(self_price_coverage`g', .5, 1)
    gen double ln_ratio`g' = ln(self_unit_value`g' / p`g'_village) ///
        if !missing(ln_selfuv`g') & p`g'_village > 0

    bysort province_id data_year: egen double med_uv`g' = median(ln_selfuv`g')
    gen double ad_uv`g' = abs(ln_selfuv`g' - med_uv`g')
    bysort province_id data_year: egen double mad_uv`g' = median(ad_uv`g')
    bysort data_year: egen double ymed_uv`g' = median(ln_selfuv`g')
    gen double yad_uv`g' = abs(ln_selfuv`g' - ymed_uv`g')
    bysort data_year: egen double ymad_uv`g' = median(yad_uv`g')

    bysort province_id data_year: egen double med_lr`g' = median(ln_ratio`g')
    gen double ad_lr`g' = abs(ln_ratio`g' - med_lr`g')
    bysort province_id data_year: egen double mad_lr`g' = median(ad_lr`g')
    bysort data_year: egen double ymed_lr`g' = median(ln_ratio`g')
    gen double yad_lr`g' = abs(ln_ratio`g' - ymed_lr`g')
    bysort data_year: egen double ymad_lr`g' = median(yad_lr`g')

    gen byte self_price_outlier`g' = 0 if !missing(ln_selfuv`g')
    replace self_price_outlier`g' = 1 if ///
        ad_uv`g' > 4.5 * 1.4826 * mad_uv`g' & mad_uv`g' > 0 & !missing(ad_uv`g')
    replace self_price_outlier`g' = 1 if ///
        mad_uv`g' <= 0 & yad_uv`g' > 4.5 * 1.4826 * ymad_uv`g' & ///
        ymad_uv`g' > 0 & !missing(yad_uv`g')
    replace self_price_outlier`g' = 1 if ///
        ad_lr`g' > 4.5 * 1.4826 * mad_lr`g' & mad_lr`g' > 0 & !missing(ad_lr`g')
    replace self_price_outlier`g' = 1 if ///
        mad_lr`g' <= 0 & yad_lr`g' > 4.5 * 1.4826 * ymad_lr`g' & ///
        ymad_lr`g' > 0 & !missing(yad_lr`g')
    gen double selfuv_clean`g' = self_unit_value`g' if ///
        self_price_outlier`g' == 0 & self_unit_value`g' > 0 & self_unit_value`g' < .
    gen double lratio_clean`g' = ln(selfuv_clean`g' / p`g'_village) ///
        if selfuv_clean`g' > 0 & p`g'_village > 0

    quietly count if self_consumed_quantity`g' > 0 & self_consumed_quantity`g' < .
    post `amem' (`g') ("households with own consumption") (r(N))
    quietly count if self_unit_value`g' > 0 & self_unit_value`g' < .
    post `amem' (`g') ("households with reported own price") (r(N))
    quietly count if !missing(ln_selfuv`g')
    post `amem' (`g') ("reports covering at least half quantity") (r(N))
    quietly count if self_price_outlier`g' == 1
    post `amem' (`g') ("robust price outliers removed") (r(N))
    quietly count if selfuv_clean`g' > 0 & selfuv_clean`g' < .
    post `amem' (`g') ("clean household opportunity prices") (r(N))
}
postclose `amem'
save `reports', replace

preserve
    collapse (count) nself1=selfuv_clean1 nself2=selfuv_clean2 ///
        nself3=selfuv_clean3 nself4=selfuv_clean4 nself5=selfuv_clean5 ///
        nself6=selfuv_clean6 (median) pself_direct1=selfuv_clean1 ///
        pself_direct2=selfuv_clean2 pself_direct3=selfuv_clean3 ///
        pself_direct4=selfuv_clean4 pself_direct5=selfuv_clean5 ///
        pself_direct6=selfuv_clean6 ///
        (median) retail1=p1_village retail2=p2_village ///
        retail3=p3_village retail4=p4_village retail5=p5_village ///
        retail6=p6_village vilLat vilLon, ///
        by(village_id town_id county_id province_id data_year)
    forvalues g = 1/6 {
        replace pself_direct`g' = . if nself`g' < 3
    }
    save `direct', replace
restore

preserve
    use "$EASI_DATA/village_community_prices.dta", clear
    keep village_id data_year town_id county_id province_id vilLat vilLon p*_village
    save `targets', replace
restore

* Same-town fallback excludes the target village and uses only village medians
* that already meet the three-producer direct-price rule.
preserve
    use `direct', clear
    keep village_id town_id data_year pself_direct1-pself_direct6
    rename village_id donor_id
    forvalues g = 1/6 {
        rename pself_direct`g' donor_pself`g'
    }
    save `towndonors', replace
    use `targets', clear
    keep village_id town_id data_year
    joinby town_id data_year using `towndonors'
    drop if village_id == donor_id
    collapse (count) ntown1=donor_pself1 ntown2=donor_pself2 ///
        ntown3=donor_pself3 ntown4=donor_pself4 ntown5=donor_pself5 ///
        ntown6=donor_pself6 (median) pself_town1=donor_pself1 ///
        pself_town2=donor_pself2 pself_town3=donor_pself3 ///
        pself_town4=donor_pself4 pself_town5=donor_pself5 ///
        pself_town6=donor_pself6, by(village_id data_year)
    save `town', replace
restore

* County medians likewise aggregate independently eligible village medians,
* rather than pooling target-village household reports.
preserve
    use `direct', clear
    collapse (count) ncounty1=pself_direct1 ncounty2=pself_direct2 ///
        ncounty3=pself_direct3 ncounty4=pself_direct4 ///
        ncounty5=pself_direct5 ncounty6=pself_direct6 ///
        (median) pself_county1=pself_direct1 pself_county2=pself_direct2 ///
        pself_county3=pself_direct3 pself_county4=pself_direct4 ///
        pself_county5=pself_direct5 pself_county6=pself_direct6, ///
        by(county_id data_year)
    save `county', replace
restore

* Producer/retail wedges give equal weight to eligible village medians. A
* province-year wedge requires at least three eligible villages.
preserve
    use `direct', clear
    forvalues g = 1/6 {
        gen double village_lratio`g' = ln(pself_direct`g' / retail`g') ///
            if pself_direct`g' > 0 & retail`g' > 0
    }
    collapse (count) nratio1=village_lratio1 nratio2=village_lratio2 ///
        nratio3=village_lratio3 nratio4=village_lratio4 ///
        nratio5=village_lratio5 nratio6=village_lratio6 ///
        (median) lratio_prov1=village_lratio1 lratio_prov2=village_lratio2 ///
        lratio_prov3=village_lratio3 lratio_prov4=village_lratio4 ///
        lratio_prov5=village_lratio5 lratio_prov6=village_lratio6, ///
        by(province_id data_year)
    forvalues g = 1/6 {
        replace lratio_prov`g' = . if nratio`g' < 3
    }
    save `pratio', replace
restore

preserve
    use `direct', clear
    forvalues g = 1/6 {
        gen double village_lratio`g' = ln(pself_direct`g' / retail`g') ///
            if pself_direct`g' > 0 & retail`g' > 0
    }
    collapse (median) lratio_year1=village_lratio1 ///
        lratio_year2=village_lratio2 lratio_year3=village_lratio3 ///
        lratio_year4=village_lratio4 lratio_year5=village_lratio5 ///
        lratio_year6=village_lratio6, by(data_year)
    save `yratio', replace
restore

* Nearest donor is an independently eligible village price, not an imputed
* price. Compute all six categories in a single county-year geographic join.
use `targets', clear
preserve
    use `direct', clear
    keep village_id data_year county_id vilLat vilLon pself_direct1-pself_direct6
    rename village_id donor_id
    rename vilLat donor_lat
    rename vilLon donor_lon
    forvalues g = 1/6 {
        rename pself_direct`g' donor_pself`g'
    }
    save `nearest', replace
restore

keep village_id data_year county_id vilLat vilLon
joinby county_id data_year using `nearest'
drop if village_id == donor_id
gen double km = 6371 * acos(min(1, max(-1, ///
    sin(vilLat * _pi / 180) * sin(donor_lat * _pi / 180) + ///
    cos(vilLat * _pi / 180) * cos(donor_lat * _pi / 180) * ///
    cos((donor_lon - vilLon) * _pi / 180))))
forvalues g = 1/6 {
    bysort village_id data_year: egen double min_km`g' = ///
        min(cond(donor_pself`g' > 0 & donor_pself`g' < ., km, .))
    bysort village_id data_year: egen double near_pself`g' = ///
        mean(cond(km == min_km`g' & donor_pself`g' > 0 & donor_pself`g' < ., ///
        donor_pself`g', .))
}
keep village_id data_year near_pself1-near_pself6
duplicates drop
isid village_id data_year
save `nearest', replace

use `targets', clear
merge 1:1 village_id data_year using `direct', ///
    keep(master match) keepusing(nself1-nself6 pself_direct1-pself_direct6) nogen
merge 1:1 village_id data_year using `town', keep(master match) nogen
merge 1:1 village_id data_year using `nearest', keep(master match) nogen
merge m:1 county_id data_year using `county', keep(master match) nogen
merge m:1 province_id data_year using `pratio', keep(master match) nogen
merge m:1 data_year using `yratio', keep(master match) nogen

forvalues g = 1/6 {
    gen double pself`g' = pself_direct`g'
    gen byte pself`g'_source = 1 if pself`g' > 0 & pself`g' < .
    replace pself`g' = pself_town`g' if missing(pself`g') & ///
        pself_town`g' > 0 & pself_town`g' < .
    replace pself`g'_source = 2 if missing(pself`g'_source) & ///
        pself`g' > 0 & pself`g' < .
    replace pself`g' = near_pself`g' if missing(pself`g') & ///
        near_pself`g' > 0 & near_pself`g' < .
    replace pself`g'_source = 3 if missing(pself`g'_source) & ///
        pself`g' > 0 & pself`g' < .
    replace pself`g' = pself_county`g' if missing(pself`g') & ///
        pself_county`g' > 0 & pself_county`g' < .
    replace pself`g'_source = 4 if missing(pself`g'_source) & ///
        pself`g' > 0 & pself`g' < .
    replace pself`g' = p`g'_village * exp(lratio_prov`g') ///
        if missing(pself`g') & !missing(lratio_prov`g')
    replace pself`g'_source = 5 if missing(pself`g'_source) & ///
        pself`g' > 0 & pself`g' < .
    replace pself`g' = p`g'_village * exp(lratio_year`g') ///
        if missing(pself`g') & !missing(lratio_year`g')
    replace pself`g'_source = 6 if missing(pself`g'_source) & ///
        pself`g' > 0 & pself`g' < .
    assert pself`g' > 0 & pself`g' < .
}

label define self_price_source 1 "own village median: at least 3 producers" ///
    2 "same-town other eligible-village median" ///
    3 "nearest eligible producer village in county" ///
    4 "county eligible-village median" ///
    5 "retail times province median eligible-village wedge" ///
    6 "retail times survey-year median eligible-village wedge"
forvalues g = 1/6 {
    label values pself`g'_source self_price_source
}

preserve
    keep pself1_source-pself6_source
    gen long village_n = _n
    reshape long pself@_source, i(village_n) j(group)
    rename pself_source source
    contract group source
    rename _freq villages
    export delimited using "$EASI_OUT/self_price_source_audit.csv", replace
restore
preserve
    use `audit', clear
    export delimited using "$EASI_OUT/self_price_report_audit.csv", replace
restore

keep village_id data_year pself1-pself6 pself1_source-pself6_source ///
    nself1-nself6
isid village_id data_year
compress
save "$EASI_DATA/village_self_prices.dta", replace
export delimited using "$EASI_OUT/village_self_prices.csv", replace
