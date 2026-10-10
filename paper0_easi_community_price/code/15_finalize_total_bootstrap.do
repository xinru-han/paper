version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

use "$EASI_OUT/total_bootstrap_replicates.dta", clear
quietly count if !missing(exp1)
local successful = r(N)
local failed = _N - `successful'
tempfile point
quietly import delimited using ///
    "$EASI_OUT/source_total_curvature_constrained_reference.csv", clear
quietly save `point'
use "$EASI_OUT/total_bootstrap_replicates.dta", clear

tempname emem
tempfile eres
postfile `emem' str14 elasticity_type int demand_good int shock_good ///
    double estimate delta_se delta_p ci_low ci_high bootstrap_mean ///
    bootstrap_se bootstrap_p bootstrap_reps_successful ///
    bootstrap_reps_failed using `eres', replace

forvalues i = 1/6 {
    quietly summarize exp`i', detail
    local bm = r(mean)
    local bs = r(sd)
    quietly _pctile exp`i', p(2.5 97.5)
    local b25 = r(r1)
    local b975 = r(r2)
    quietly preserve
        use `point', clear
        quietly summarize elasticity if elasticity_type == "expenditure" & demand_good == `i', meanonly
        local est = r(mean)
        quietly summarize p_value if elasticity_type == "expenditure" & demand_good == `i', meanonly
        local dp = r(mean)
        quietly summarize std_error if elasticity_type == "expenditure" & demand_good == `i', meanonly
        local dse = r(mean)
    restore
    post `emem' ("expenditure") (`i') (0) (`est') (`dse') (`dp') ///
        (`b25') (`b975') (`bm') (`bs') ///
        (2*normal(-abs(`est'/`bs'))) (`successful') (`failed')
    forvalues j = 1/6 {
        foreach typ in mar hix {
            local outtype = cond("`typ'" == "mar", "marshallian", "hicksian")
            local var "`typ'_`i'_`j'"
            quietly summarize `var', detail
            local bm = r(mean)
            local bs = r(sd)
            quietly _pctile `var', p(2.5 97.5)
            local b25 = r(r1)
            local b975 = r(r2)
            quietly preserve
                use `point', clear
                quietly summarize elasticity if elasticity_type == "`outtype'" & ///
                    demand_good == `i' & shock_good == `j', meanonly
                local est = r(mean)
                quietly summarize p_value if elasticity_type == "`outtype'" & ///
                    demand_good == `i' & shock_good == `j', meanonly
                local dp = r(mean)
                quietly summarize std_error if elasticity_type == "`outtype'" & ///
                    demand_good == `i' & shock_good == `j', meanonly
                local dse = r(mean)
            restore
            post `emem' ("`outtype'") (`i') (`j') (`est') (`dse') (`dp') ///
                (`b25') (`b975') (`bm') (`bs') ///
                (2*normal(-abs(`est'/`bs'))) (`successful') (`failed')
        }
    }
}
postclose `emem'
use `eres', clear
export delimited using "$EASI_OUT/total_bootstrap_elasticities.csv", replace

use "$EASI_OUT/total_bootstrap_replicates.dta", clear
tempname tmem
tempfile tres
postfile `tmem' str40 test double full_sample_statistic full_sample_p_value ///
    bootstrap_mean bootstrap_se bootstrap_p2_5 bootstrap_p50 bootstrap_p97_5 ///
    bootstrap_reps_successful bootstrap_reps_failed using `tres', replace
foreach pair in "stat_dem demographics_joint_zero p_dem" ///
    "stat_all all_share_shifters_joint_zero p_all" ///
    "stat_sy Shonkwiler_Yen_terms_joint_zero p_sy" ///
    "stat_hansen Hansen_overidentification p_hansen" ///
    "stat_first excluded_instruments_first_stage p_first" {
    tokenize `pair'
    local var "`1'"
    local test "`2'"
    quietly summarize `var', detail
    local bm = r(mean)
    local bs = r(sd)
    quietly _pctile `var', p(2.5 50 97.5)
    local b25 = r(r1)
    local b50 = r(r2)
    local b975 = r(r3)
    quietly preserve
        import delimited using "$EASI_OUT/source_total_curvature_constrained_tests.csv", clear
        quietly summarize statistic if test == "`test'", meanonly
        local fs = r(mean)
        quietly summarize p_value if test == "`test'", meanonly
        local fp = r(mean)
    restore
    post `tmem' ("`test'") (`fs') (`fp') (`bm') (`bs') (`b25') (`b50') (`b975') ///
        (`successful') (`failed')
}
postclose `tmem'
use `tres', clear
export delimited using "$EASI_OUT/total_bootstrap_tests.csv", replace
display as text "bootstrap post-processing completed: " `successful' ///
    " successful, " `failed' " failed"
