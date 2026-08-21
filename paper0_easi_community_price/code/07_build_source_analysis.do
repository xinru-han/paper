version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

use "$EASI_DATA/easi_analysis_ready.dta", clear
merge 1:1 household_id data_year using "$EASI_DATA/household_unit_values.dta", ///
    keep(match) keepusing(purchase_consumed_quantity1-purchase_consumed_quantity6 ///
    purchase_direct_quantity1-purchase_direct_quantity6 ///
    purchase_residual_quantity1-purchase_residual_quantity6 ///
    purchase_typical_quantity1-purchase_typical_quantity6 ///
    self_consumed_quantity1-self_consumed_quantity6 ///
    gift_consumed_quantity1-gift_consumed_quantity6 ///
    source_total_quantity1-source_total_quantity6 ///
    self_unit_value1-self_unit_value6 ///
    self_price_covered_quantity1-self_price_covered_quantity6) nogen
merge m:1 village_id data_year using "$EASI_DATA/village_self_prices.dta", ///
    keep(match) keepusing(pself1-pself6 pself1_source-pself6_source nself1-nself6) nogen

tempname flowmem
tempfile flow
postfile `flowmem' int sequence str54 stage long observations using `flow', replace
post `flowmem' (1) ("legacy cleaned demand sample") (_N)

local caps "90 30 60 21 150 120"
local sourceflags ""
forvalues g = 1/6 {
    rename q`g' q_legacy`g'
    gen double qt`g' = source_total_quantity`g'
    gen double qb`g' = purchase_consumed_quantity`g'
    gen double qs`g' = self_consumed_quantity`g'
    gen double qg`g' = gift_consumed_quantity`g'
    gen double qo`g' = qb`g' + qg`g'
    assert abs(qt`g' - qb`g' - qs`g' - qg`g') < 1e-5 * max(1, qt`g')
    assert qt`g' >= 0 & qt`g' < . & qb`g' >= 0 & qb`g' < . & ///
        qs`g' >= 0 & qs`g' < . & qg`g' >= 0 & qg`g' < . & ///
        qo`g' >= 0 & qo`g' < .
    gen double qt`g'_pc = qt`g' / hhsize
    local cap : word `g' of `caps'
    gen byte source_physical`g' = qt`g'_pc > `cap' if qt`g'_pc < .
    local sourceflags "`sourceflags' source_physical`g'"
}
egen byte source_physical_any = rowmax(`sourceflags')
drop if source_physical_any == 1
post `flowmem' (2) ("source-specific physical quantity screen") (_N)

* Robust high-tail screen is reported and used for sensitivity estimation.
* It does not redefine the main sample because genuine subsistence production
* can be far above the local median while remaining physically plausible.
local qrobust ""
forvalues g = 1/6 {
    gen double lnqtpc`g' = ln(1 + qt`g'_pc)
    bysort province_id data_year: egen double med_lnqt`g' = median(lnqtpc`g')
    gen double ad_lnqt`g' = abs(lnqtpc`g' - med_lnqt`g')
    bysort province_id data_year: egen double mad_lnqt`g' = median(ad_lnqt`g')
    gen byte source_robust`g' = ad_lnqt`g' > 4.5 * 1.4826 * mad_lnqt`g' ///
        if mad_lnqt`g' > 0 & mad_lnqt`g' < .
    replace source_robust`g' = 0 if missing(source_robust`g')
    local qrobust "`qrobust' source_robust`g'"
}
egen byte source_robust_any = rowmax(`qrobust')
local p99flags ""
forvalues g = 1/6 {
    gen byte source_p99`g' = 0
    foreach y in 2023 2024 {
        quietly _pctile qt`g'_pc if data_year == `y' & qt`g'_pc > 0, p(99)
        replace source_p99`g' = 1 if data_year == `y' & qt`g'_pc > r(r1) & ///
            qt`g'_pc < .
    }
    local p99flags "`p99flags' source_p99`g'"
}
egen byte source_p99_any = rowmax(`p99flags')

forvalues g = 1/6 {
    assert p`g' > 0 & p`g' < . & pself`g' > 0 & pself`g' < .
    gen double lnps`g' = ln(pself`g')
    gen double price_wedge`g' = pself`g' / p`g'

    * Replacement-cost total demand is the consumer-welfare estimand. Purchased
    * demand uses only purchased food; own demand uses producer opportunity cost.
    gen double vt`g' = p`g' * qt`g'
    gen double vb`g' = p`g' * qb`g'
    gen double vs`g' = pself`g' * qs`g'
    gen double vo`g' = p`g' * qo`g'
    gen double vh`g' = vb`g' + p`g' * qg`g' + vs`g'
}
egen double foodexp_total = rowtotal(vt1 vt2 vt3 vt4 vt5 vt6)
egen double foodexp_buy = rowtotal(vb1 vb2 vb3 vb4 vb5 vb6)
egen double foodexp_self = rowtotal(vs1 vs2 vs3 vs4 vs5 vs6)
egen double foodexp_omitself = rowtotal(vo1 vo2 vo3 vo4 vo5 vo6)
egen double foodexp_hybrid = rowtotal(vh1 vh2 vh3 vh4 vh5 vh6)
drop if foodexp_total <= 0 | missing(foodexp_total)
post `flowmem' (3) ("positive reconstructed total food value") (_N)
postclose `flowmem'
preserve
    use `flow', clear
    gen long removed_from_previous = observations[_n-1] - observations
    replace removed_from_previous = 0 in 1
    export delimited using "$EASI_OUT/source_sample_flow.csv", replace
restore

gen double ln_foodexp_total = ln(foodexp_total)
gen double ln_foodexp_buy = ln(foodexp_buy) if foodexp_buy > 0
gen double ln_foodexp_self = ln(foodexp_self) if foodexp_self > 0
gen double ln_foodexp_omitself = ln(foodexp_omitself) if foodexp_omitself > 0
gen double ln_foodexp_hybrid = ln(foodexp_hybrid) if foodexp_hybrid > 0
gen byte sample_total = foodexp_total > 0 & foodexp_total < .
gen byte sample_buy = foodexp_buy > 0 & foodexp_buy < .
gen byte sample_self = foodexp_self > 0 & foodexp_self < .
gen byte sample_omitself = foodexp_omitself > 0 & foodexp_omitself < .
gen byte sample_common = sample_total & sample_omitself

forvalues g = 1/6 {
    gen double st`g' = vt`g' / foodexp_total
    gen double sb`g' = vb`g' / foodexp_buy if sample_buy
    gen double ss`g' = vs`g' / foodexp_self if sample_self
    gen double so`g' = vo`g' / foodexp_omitself if sample_omitself
    gen double source_share_qty`g' = qs`g' / qt`g' if qt`g' > 0
    gen double source_share_value`g' = vs`g' / vh`g' if vh`g' > 0
}
egen double st_sum = rowtotal(st1 st2 st3 st4 st5 st6)
egen double sb_sum = rowtotal(sb1 sb2 sb3 sb4 sb5 sb6) if sample_buy
egen double ss_sum = rowtotal(ss1 ss2 ss3 ss4 ss5 ss6) if sample_self
egen double so_sum = rowtotal(so1 so2 so3 so4 so5 so6) if sample_omitself
assert abs(st_sum - 1) < 1e-8
assert abs(sb_sum - 1) < 1e-8 if sample_buy
assert abs(ss_sum - 1) < 1e-8 if sample_self
assert abs(so_sum - 1) < 1e-8 if sample_omitself

* Local price-tail flag for sensitivity only. Prices are village-level, so the
* robust center is calculated on one observation per village and merged back.
tempfile priceflags
preserve
    keep village_id data_year province_id lnp1-lnp6
    duplicates drop
    forvalues g = 1/6 {
        bysort province_id data_year: egen double med_lnp`g' = median(lnp`g')
        gen double ad_lnp`g' = abs(lnp`g' - med_lnp`g')
        bysort province_id data_year: egen double mad_lnp`g' = median(ad_lnp`g')
        gen byte price_robust`g' = ad_lnp`g' > 4.5 * 1.4826 * mad_lnp`g' ///
            if mad_lnp`g' > 0 & mad_lnp`g' < .
        replace price_robust`g' = 0 if missing(price_robust`g')
    }
    egen byte price_robust_any = rowmax(price_robust1 price_robust2 ///
        price_robust3 price_robust4 price_robust5 price_robust6)
    keep village_id data_year price_robust1-price_robust6 price_robust_any
    save `priceflags'
restore
merge m:1 village_id data_year using `priceflags', assert(3) nogen
gen byte sample_robust = !source_robust_any & !price_robust_any
gen byte sample_trim99 = !source_p99_any & !price_robust_any

* Reconciliation and source composition audit.
tempname amem
tempfile audit
postfile `amem' int group str42 statistic double value using `audit', replace
forvalues g = 1/6 {
    gen double q_reconciliation`g' = qt`g' - q_legacy`g'
    gen double fallback_share`g' = (purchase_residual_quantity`g' + ///
        purchase_typical_quantity`g') / qb`g' if qb`g' > 0
    foreach v in qt`g' qb`g' qs`g' qg`g' q_reconciliation`g' ///
        fallback_share`g' price_wedge`g' source_share_qty`g' {
        quietly summarize `v', detail
        post `amem' (`g') ("`v': mean") (r(mean))
        post `amem' (`g') ("`v': p50") (r(p50))
        post `amem' (`g') ("`v': p99") (r(p99))
    }
    quietly count if qt`g' > 0
    post `amem' (`g') ("total participation rate") (r(N)/_N)
    quietly count if qb`g' > 0
    post `amem' (`g') ("purchase participation rate") (r(N)/_N)
    quietly count if qs`g' > 0
    post `amem' (`g') ("own-consumption participation rate") (r(N)/_N)
    quietly count if source_robust`g' == 1
    post `amem' (`g') ("robust quantity-tail households") (r(N))
    quietly count if source_p99`g' == 1
    post `amem' (`g') ("positive-quantity top-one-percent") (r(N))
    quietly count if price_robust`g' == 1
    post `amem' (`g') ("robust local-price-tail households") (r(N))
}
postclose `amem'
preserve
    use `audit', clear
    export delimited using "$EASI_OUT/source_quantity_price_audit.csv", replace
restore

compress
save "$EASI_DATA/source_analysis_ready.dta", replace
