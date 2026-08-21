version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"
use "$EASI_DATA/easi_analysis_ready.dta", clear

isid household_id
assert abs(share_sum - 1) < 1e-8
forvalues g = 1/6 {
    bysort village_id data_year: assert p`g' == p`g'[1]
    assert p`g' > 0 & q`g' >= 0 & inrange(s`g', 0, 1)
}

* Full-sample descriptive statistics, with tails needed to detect remaining
* data problems rather than reporting only means and standard deviations.
tempname mem
tempfile stats
postfile `mem' str36 variable long n double mean sd p1 p50 p99 min max using `stats', replace
foreach v in q1 q2 q3 q4 q5 q6 q1_pc q2_pc q3_pc q4_pc q5_pc q6_pc ///
    p1 p2 p3 p4 p5 p6 uv1 uv2 uv3 uv4 uv5 uv6 ///
    purchase_value1 purchase_value2 purchase_value3 purchase_value4 purchase_value5 purchase_value6 ///
    s1 s2 s3 s4 s5 s6 food_exp income_annual total_exp_monthly ///
    hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education {
    quietly summarize `v', detail
    post `mem' ("`v'") (r(N)) (r(mean)) (r(sd)) (r(p1)) (r(p50)) (r(p99)) (r(min)) (r(max))
}
postclose `mem'
preserve
    use `stats', clear
    export delimited using "$EASI_OUT/table_descriptives.csv", replace
restore

* Province-wave support identifies why separate province and wave effects cannot
* enter the structural system together in this repeated cross-section.
preserve
    gen byte province_group = 1
    forvalues j = 2/8 {
        replace province_group = `j' if province_`j' == 1
    }
    contract province_group data_year
    rename _freq households
    bysort province_group: gen byte province_observed_in_both_waves = _N > 1
    export delimited using "$EASI_OUT/table_province_year_support.csv", replace
restore

* Purchase-value coverage is reported because third-stage quality/sourcing
* equations use household purchase values, whereas main demand shares use all
* consumption valued at community prices.
tempname bmem
tempfile buying
postfile `bmem' int group long sample_n consuming_n positive_purchase_value_n ///
    unit_value_observed_n double purchase_value_coverage using `buying', replace
forvalues g = 1/6 {
    quietly count
    local n = r(N)
    quietly count if q`g' > 0
    local nq = r(N)
    quietly count if purchase_value`g' > 0 & !missing(purchase_value`g')
    local nv = r(N)
    quietly count if uv`g' > 0 & !missing(uv`g')
    local nuv = r(N)
    post `bmem' (`g') (`n') (`nq') (`nv') (`nuv') (`nv' / `nq')
}
postclose `bmem'
preserve
    use `buying', clear
    export delimited using "$EASI_OUT/table_purchase_coverage.csv", replace
restore

tempname ymem
tempfile ystats
postfile `ymem' int year str24 variable long n double mean sd p50 p99 using `ystats', replace
foreach y in 2023 2024 {
    foreach v in q1_pc q2_pc q3_pc q4_pc q5_pc q6_pc p1 p2 p3 p4 p5 p6 ///
        s1 s2 s3 s4 s5 s6 food_exp income_annual {
        quietly summarize `v' if data_year == `y', detail
        post `ymem' (`y') ("`v'") (r(N)) (r(mean)) (r(sd)) (r(p50)) (r(p99))
    }
}
postclose `ymem'
preserve
    use `ystats', clear
    export delimited using "$EASI_OUT/table_descriptives_by_year.csv", replace
restore

* Zero-consumption diagnostics determine whether an SY selection equation is
* estimable. Near-universal consumption is explicitly classified as bypassed;
* no unidentified inverse-Mills parameter is added in that case.
tempname zmem
tempfile zeros
postfile `zmem' int group long sample_n n_consuming n_zero double share_consuming ///
    str28 sy_action using `zeros', replace
forvalues g = 1/6 {
    quietly count if q`g' > 0
    local nc = r(N)
    local nz = _N - `nc'
    local rate = `nc' / _N
    local action "estimate probit correction"
    if `rate' >= .98 local action "bypass: almost universal"
    if `rate' <= .02 local action "not estimable: too sparse"
    post `zmem' (`g') (_N) (`nc') (`nz') (`rate') ("`action'")
}
postclose `zmem'
preserve
    use `zeros', clear
    export delimited using "$EASI_OUT/table_zero_consumption.csv", replace
restore

* Household-weighted price-source counts.
preserve
    keep p1_source p2_source p3_source p4_source p5_source p6_source
    forvalues g = 1/6 {
        rename p`g'_source source`g'
    }
    gen long household_n = _n
    reshape long source, i(household_n) j(group)
    contract group source
    rename source price_source
    rename _freq households
    export delimited using "$EASI_OUT/table_price_sources.csv", replace
restore

* Price variation and pairwise log-price correlations expose weak price
* variation or nearly collinear group prices before system estimation.
tempname pmem cmem
tempfile pstats pcorr
postfile `pmem' int group long villages unique_values double mean sd cv min max using `pstats', replace
egen byte village_tag = tag(village_id data_year)
forvalues g = 1/6 {
    quietly summarize p`g' if village_tag
    local mn = r(mean)
    local sd = sqrt(r(Var))
    local pmin = r(min)
    local pmax = r(max)
    quietly levelsof p`g' if village_tag, local(levels)
    local nu : word count `levels'
    quietly count if village_tag
    post `pmem' (`g') (r(N)) (`nu') (`mn') (`sd') (`sd' / `mn') (`pmin') (`pmax')
}
postclose `pmem'
preserve
    use `pstats', clear
    export delimited using "$EASI_OUT/table_price_variation.csv", replace
restore
postfile `cmem' int price_i price_j double correlation using `pcorr', replace
forvalues i = 1/6 {
    forvalues j = `i'/6 {
        quietly correlate lnp`i' lnp`j' if village_tag
        matrix C = r(C)
        post `cmem' (`i') (`j') (C[1,2])
    }
}
postclose `cmem'
preserve
    use `pcorr', clear
    export delimited using "$EASI_OUT/table_logprice_correlations.csv", replace
restore

* Unit-value validation following the paper's equations (6)-(8): remove
* within-market quantity and demographic effects, recover a common market
* component, and fill only for this robustness series. These prices do not
* replace the directly observed village-questionnaire prices.
fooddem_uvprice, unitvalues(uv1 uv2 uv3 uv4 uv5 uv6) ///
    quantities(q1 q2 q3 q4 q5 q6) market(village_id data_year) ///
    demographics(hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education) ///
    generate(uvp) source(uvps) method(deaton) mincell(3) trim(1) ///
    fallback1(town_id data_year) fallback2(county_id data_year) ///
    fallback3(province_id data_year) allowoverall complete ///
    audit("$EASI_OUT/unit_value_recovery_audit.csv") replace

tempname vmem
tempfile validation
postfile `vmem' int group str30 comparison long n double log_correlation median_ratio using `validation', replace
forvalues g = 1/6 {
    tempvar lp luvp luv ratio
    gen double `lp' = ln(p`g')
    gen double `luvp' = ln(uvp`g')
    quietly correlate `lp' `luvp' if village_tag
    matrix C = r(C)
    local corr = C[1,2]
    gen double `ratio' = uvp`g' / p`g' if village_tag
    quietly summarize `ratio' if village_tag, detail
    post `vmem' (`g') ("community vs corrected UV") (r(N)) (`corr') (r(p50))

    gen double `luv' = ln(uv`g') if uv`g' > 0
    quietly correlate `lp' `luv'
    matrix C = r(C)
    local corr = C[1,2]
    replace `ratio' = uv`g' / p`g' if uv`g' > 0
    quietly summarize `ratio' if uv`g' > 0, detail
    post `vmem' (`g') ("community vs raw unit value") (r(N)) (`corr') (r(p50))
}
postclose `vmem'
preserve
    use `validation', clear
    export delimited using "$EASI_OUT/table_price_validation.csv", replace
restore
preserve
    keep household_id village_id data_year uvp1 uvp2 uvp3 uvp4 uvp5 uvp6 ///
        uvps1 uvps2 uvps3 uvps4 uvps5 uvps6
    save "$EASI_DATA/unit_value_prices_validation.dta", replace
restore
