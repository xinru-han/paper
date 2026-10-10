version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_config.do"
use "$AR_DATA/total_anomaly_analysis.dta", clear

local goods "staples beans meat oil vegetables fruit"
tempname mem
tempfile stats
postfile `mem' str16 sample str28 variable long n double mean sd p1 p50 p95 ///
    p99 min max using `stats', replace
foreach smp in full physical main strict45 lenient60 p99 {
    local condition "1"
    if "`smp'" == "physical" local condition "sample_physical"
    if "`smp'" == "main" local condition "sample_main"
    if "`smp'" == "strict45" local condition "sample_strict45"
    if "`smp'" == "lenient60" local condition "sample_lenient60"
    if "`smp'" == "p99" local condition "sample_p99"
    foreach v in qt1_pc qt2_pc qt3_pc qt4_pc qt5_pc qt6_pc ///
        qb1_pc qb2_pc qb3_pc qb4_pc qb5_pc qb6_pc ///
        qs1_pc qs2_pc qs3_pc qs4_pc qs5_pc qs6_pc ///
        qg1_pc qg2_pc qg3_pc qg4_pc qg5_pc qg6_pc ///
        p1 p2 p3 p4 p5 p6 s1 s2 s3 s4 s5 s6 food_exp ///
        food_exp_pc food_to_total_exp income_annual hhsize {
        quietly summarize `v' if `condition', detail
        post `mem' ("`smp'") ("`v'") (r(N)) (r(mean)) (r(sd)) ///
            (r(p1)) (r(p50)) (r(p95)) (r(p99)) (r(min)) (r(max))
    }
}
postclose `mem'
preserve
    use `stats', clear
    export delimited using "$AR_OUT/descriptive_statistics.csv", replace
restore

tempname zmem
tempfile zeros
postfile `zmem' int group str16 food long n consuming zero double ///
    participation self_participation purchase_participation gift_participation ///
    using `zeros', replace
forvalues g = 1/6 {
    local food : word `g' of `goods'
    quietly count if sample_main
    local n = r(N)
    quietly count if sample_main & qt`g' > 0
    local nc = r(N)
    quietly count if sample_main & qs`g' > 0
    local ns = r(N)
    quietly count if sample_main & qb`g' > 0
    local nb = r(N)
    quietly count if sample_main & qg`g' > 0
    local ng = r(N)
    post `zmem' (`g') ("`food'") (`n') (`nc') (`n' - `nc') ///
        (`nc'/`n') (`ns'/`n') (`nb'/`n') (`ng'/`n')
}
postclose `zmem'
preserve
    use `zeros', clear
    export delimited using "$AR_OUT/zero_and_source_participation.csv", replace
restore

* Village-level price variation and imputation source, avoiding household
* replication in the diagnostic counts.
preserve
    keep village_id data_year p1-p6 p1_source-p6_source
    duplicates drop
    tempname pmem
    tempfile pstats
    postfile `pmem' int group long villages unique_values double mean sd cv ///
        p1 p50 p99 min max direct_share using `pstats', replace
    forvalues g = 1/6 {
        quietly levelsof p`g', local(levels)
        local nu : word count `levels'
        quietly summarize p`g', detail
        local n = r(N)
        local mn = r(mean)
        local sd = r(sd)
        local lo = r(p1)
        local md = r(p50)
        local hi = r(p99)
        local min = r(min)
        local max = r(max)
        quietly count if inrange(p`g'_source, 1, 2)
        post `pmem' (`g') (`n') (`nu') (`mn') (`sd') (`sd'/`mn') ///
            (`lo') (`md') (`hi') (`min') (`max') (r(N)/`n')
    }
    postclose `pmem'
    use `pstats', clear
    export delimited using "$AR_OUT/price_variation.csv", replace
restore

* Low-price tail diagnostics distinguish genuine concentration from repeated
* geographic donor values and record which raw quotes failed the weak-support
* screen. The final-price table is one row per village-year.
preserve
    use "$AR_DATA/village_community_prices.dta", clear
    forvalues g = 1/6 {
        rename p`g'_village p`g'
    }
    keep village_id data_year p1-p6 p1_source-p6_source ///
        p*_outlet_count p*_weak_low_flag p*_local_corroborated ///
        p*_lower_mad_protected p*_five_mad_flag
    tempname lmem
    tempfile lowtail
    postfile `lmem' int group long villages double min p005 p01 p025 p05 ///
        p10 p50 long min_count bottom5_count bottom5_unique ///
        weak_low_removed lower_mad_protected using `lowtail', replace
    forvalues g = 1/6 {
        quietly summarize p`g', meanonly
        local n = r(N)
        local min = r(min)
        quietly _pctile p`g', p(.5 1 2.5 5 10 50)
        local p005 = r(r1)
        local p01 = r(r2)
        local p025 = r(r3)
        local p05 = r(r4)
        local p10 = r(r5)
        local p50 = r(r6)
        quietly count if p`g' == `min'
        local nmin = r(N)
        quietly count if p`g' <= `p05'
        local nbottom = r(N)
        quietly levelsof p`g' if p`g' <= `p05', local(lowlevels)
        local nlevels : word count `lowlevels'
        quietly count if p`g'_weak_low_flag == 1
        local nweak = r(N)
        quietly count if p`g'_lower_mad_protected == 1
        local nprotected = r(N)
        post `lmem' (`g') (`n') (`min') (`p005') (`p01') (`p025') ///
            (`p05') (`p10') (`p50') (`nmin') (`nbottom') (`nlevels') ///
            (`nweak') (`nprotected')
    }
    postclose `lmem'
    use `lowtail', clear
    gen double min_share = min_count / villages
    gen double bottom5_average_multiplicity = bottom5_count / bottom5_unique
    export delimited using "$AR_OUT/price_low_tail_audit.csv", replace
restore

preserve
    use "$AR_DATA/village_community_prices.dta", clear
    forvalues g = 1/6 {
        rename p`g'_village p`g'
    }
    keep village_id data_year p1-p6 p1_source-p6_source ///
        p*_outlet_count p*_weak_low_flag p*_local_corroborated
    tempfile villageprices
    save `villageprices'
    tempname smem
    tempfile lowsources
    postfile `smem' int group source long villages double share ///
        using `lowsources', replace
    forvalues g = 1/6 {
        quietly _pctile p`g', p(10)
        local p10 = r(r1)
        quietly count if p`g' <= `p10'
        local ntail = r(N)
        quietly levelsof p`g'_source if p`g' <= `p10', local(sources)
        foreach s of local sources {
            quietly count if p`g' <= `p10' & p`g'_source == `s'
            post `smem' (`g') (`s') (r(N)) (r(N) / `ntail')
        }
    }
    postclose `smem'
    use `lowsources', clear
    export delimited using "$AR_OUT/price_low_tail_sources.csv", replace
restore

tempname vmem
tempfile validation
postfile `vmem' int group long n double median_uv_price_ratio p1_ratio ///
    p99_ratio extreme_share log_correlation using `validation', replace
forvalues g = 1/6 {
    tempvar luv lp
    gen double `luv' = ln(uv`g') if uv`g' > 0
    gen double `lp' = ln(p`g')
    quietly correlate `luv' `lp' if sample_main & uv`g' > 0
    matrix C = r(C)
    local corr = C[1,2]
    quietly summarize uv_ratio`g' if sample_main & uv_ratio`g' > 0, detail
    local n = r(N)
    local med = r(p50)
    local p1 = r(p1)
    local p99 = r(p99)
    quietly count if sample_main & uv_ratio_extreme`g'
    post `vmem' (`g') (`n') (`med') (`p1') (`p99') (r(N)/`n') (`corr')
}
postclose `vmem'
preserve
    use `validation', clear
    export delimited using "$AR_OUT/unit_value_price_validation.csv", replace
restore
