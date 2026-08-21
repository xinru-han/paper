version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

* Source composition and price description precede every model result.
use "$EASI_DATA/source_analysis_ready.dta", clear
tempname smem
tempfile source_description
postfile `smem' int good long N double total_quantity_mean total_quantity_p50 ///
    total_quantity_p99 purchase_participation self_participation ///
    gift_participation purchase_quantity_share_mean ///
    purchase_quantity_share_p50 self_quantity_share_mean ///
    self_quantity_share_p50 gift_quantity_share_mean gift_quantity_share_p50 ///
    retail_price_p50 self_price_p50 self_retail_wedge_p50 ///
    using `source_description', replace
forvalues g = 1/6 {
    quietly summarize qt`g', detail
    local n = r(N)
    local qtmean = r(mean)
    local qtp50 = r(p50)
    local qtp99 = r(p99)
    quietly count if qb`g' > 0
    local buy_part = r(N) / `n'
    quietly count if qs`g' > 0
    local self_part = r(N) / `n'
    quietly count if qg`g' > 0
    local gift_part = r(N) / `n'
    tempvar buyshare selfshare giftshare
    gen double `buyshare' = qb`g' / qt`g' if qt`g' > 0
    gen double `selfshare' = qs`g' / qt`g' if qt`g' > 0
    gen double `giftshare' = qg`g' / qt`g' if qt`g' > 0
    quietly summarize `buyshare', detail
    local buymean = r(mean)
    local buyp50 = r(p50)
    quietly summarize `selfshare', detail
    local selfmean = r(mean)
    local selfp50 = r(p50)
    quietly summarize `giftshare', detail
    local giftmean = r(mean)
    local giftp50 = r(p50)
    quietly summarize p`g', detail
    local retailp50 = r(p50)
    quietly summarize pself`g', detail
    local selfpricep50 = r(p50)
    quietly summarize price_wedge`g', detail
    local wedgep50 = r(p50)
    post `smem' (`g') (`n') (`qtmean') (`qtp50') (`qtp99') ///
        (`buy_part') (`self_part') (`gift_part') (`buymean') (`buyp50') ///
        (`selfmean') (`selfp50') (`giftmean') (`giftp50') (`retailp50') ///
        (`selfpricep50') (`wedgep50')
}
postclose `smem'
use `source_description', clear
export delimited using "$EASI_OUT/source_composition_descriptives.csv", replace

* Compact elasticity table. Simple household means are retained for diagnosing
* denominator outliers, but aggregate and p1-p99 aggregate columns are primary.
local files "source_total_elasticities_unconditional.csv source_total_elasticities_latent.csv source_total_trim99_elasticities_latent.csv source_total_directprice_elasticities_latent.csv source_buy_elasticities_unconditional.csv source_buy_elasticities_latent.csv source_omitself_elasticities_unconditional.csv source_omitself_elasticities_latent.csv source_self_elasticities_unconditional.csv source_self_elasticities_latent.csv"
local systems "total total total total purchase purchase omitself omitself self self"
local samples "full full trim99 direct_prices full full full full full full"
local valid "1 1 1 1 1 1 1 1 0 0"
tempfile elasticities
clear
save `elasticities', emptyok replace
local nfiles : word count `files'
forvalues f = 1/`nfiles' {
    local file : word `f' of `files'
    local system : word `f' of `systems'
    local sample : word `f' of `samples'
    local isvalid : word `f' of `valid'
    import delimited using "$EASI_OUT/`file'", clear varnames(1)
    keep if elasticity_type == "expenditure" | ///
        (elasticity_type == "hicksian" & demand_good == shock_good)
    gen str12 system = "`system'"
    gen str16 analysis_sample = "`sample'"
    gen byte structural_interpretation = `isvalid'
    gen str18 interpretation = cond(elasticity_type == "expenditure", ///
        "expenditure", "hicksian_own")
    keep system analysis_sample structural_interpretation margin interpretation ///
        demand_good aggregate_elasticity trimmed_aggregate elasticity ///
        trimmed_mean std_dev p10 p50 p90 negative_rate near_zero_rate n_valid ///
        support_rate min_share_floor
    append using `elasticities'
    save `elasticities', replace
}
use `elasticities', clear
sort system analysis_sample margin interpretation demand_good
export delimited using "$EASI_OUT/source_elasticity_comparison.csv", replace

* Three-stage income decomposition summaries by source. The separate self
* system is exported but marked invalid for structural interpretation.
tempname imem
tempfile income_summary
postfile `imem' str12 system byte structural_interpretation int good ///
    str36 elasticity ///
    long N double mean trimmed_mean sd p10 p50 p90 negative_rate ///
    support_rate min_share_floor ///
    using `income_summary', replace
foreach system in total buy omitself self {
    use "$EASI_OUT/source_`system'_income_distribution.dta", clear
    local isvalid = ("`system'" != "self")
    quietly summarize support_rate, meanonly
    local support = r(mean)
    quietly summarize min_share_floor, meanonly
    local floor = r(mean)
    foreach y in eta_totalexp_income expenditure_elasticity ///
        income_quantity_elasticity income_value_elasticity income_quality_elasticity {
        forvalues g = 1/6 {
            quietly summarize `y' if good == `g', detail
            local n = r(N)
            local mean = r(mean)
            local sd = r(sd)
            local p1 = r(p1)
            local p10 = r(p10)
            local p50 = r(p50)
            local p90 = r(p90)
            local p99 = r(p99)
            quietly summarize `y' if good == `g' & inrange(`y', `p1', `p99'), meanonly
            local trimmean = r(mean)
            quietly count if good == `g' & `y' < 0 & !missing(`y')
            local negrate = r(N) / `n'
            post `imem' ("`system'") (`isvalid') (`g') ("`y'") (`n') ///
                (`mean') (`trimmean') (`sd') (`p10') (`p50') (`p90') ///
                (`negrate') ///
                (`support') (`floor')
        }
    }
}
postclose `imem'
use `income_summary', clear
sort system elasticity good
export delimited using "$EASI_OUT/source_income_elasticity_summary.csv", replace

* Structural tests are collected without altering their original files.
tempfile diagnostics
clear
save `diagnostics', emptyok replace
foreach system in total buy omitself self {
    import delimited using "$EASI_OUT/source_`system'_tests.csv", clear varnames(1)
    gen str12 system = "`system'"
    gen byte structural_interpretation = ("`system'" != "self")
    append using `diagnostics'
    save `diagnostics', replace
}
use `diagnostics', clear
order system structural_interpretation
export delimited using "$EASI_OUT/source_model_diagnostics.csv", replace
