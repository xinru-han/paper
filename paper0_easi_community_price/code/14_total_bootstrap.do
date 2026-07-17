version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

* Cluster bootstrap for the preferred total-consumption system.  Own
* production is already included in source_total_quantity and source_total
* expenditure; no source-allocation model enters the main result.
use "$EASI_DATA/source_analysis_ready.dta", clear
egen long village_cluster = group(village_id data_year)

local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
local geo "province_2 province_3 province_4 province_5 province_6 province_7 province_8"
local demos "`core' `geo'"
local excluded "ln_income inv_income"

foreach f in total_bootstrap_elasticities.csv total_bootstrap_tests.csv ///
    total_bootstrap_replicates.dta {
    capture erase "$EASI_OUT/`f'"
}

* Full-sample constrained estimates provide a stable starting point in the
* resampled samples.  The model itself is re-estimated in every replicate.
estimates use "$EASI_OUT/source_total_gmm_twostep.ster"
matrix FD_TOTAL_BOOT_START = e(b)

capture program drop _total_boot
program define _total_boot, rclass
    version 17
    local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
    local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
    local geo "province_2 province_3 province_4 province_5 province_6 province_7 province_8"
    local demos "`core' `geo'"
    local excluded "ln_income inv_income"
    local cl "village_cluster"
    capture confirm variable boot_cluster
    if !_rc {
        quietly count if !missing(boot_cluster)
        if r(N) > 0 local cl "boot_cluster"
    }

    quietly capture fooddem if sample_total, model(easi) order(1) ///
        shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
        expenditure(ln_foodexp_total) estimator(gmm) ///
        demographics(`demos') quantities(qt1 qt2 qt3 qt4 qt5 qt6) ///
        selection(sy) endogeneity(iv) instruments(`excluded') ///
        cluster(`cl') gmmsteps(2) curvature(local) ///
        from(FD_TOTAL_BOOT_START) iterate(20) tolerance(1e-3)
    if "`e(fooddem_model)'" != "easi" {
        forvalues i = 1/6 {
            return scalar exp`i' = .
            forvalues j = 1/6 {
                return scalar mar_`i'_`j' = .
                return scalar hix_`i'_`j' = .
            }
        }
        return scalar stat_dem = .
        return scalar stat_all = .
        return scalar stat_sy = .
        return scalar stat_hansen = .
        return scalar stat_first = .
        return scalar p_dem = .
        return scalar p_all = .
        return scalar p_sy = .
        return scalar p_hansen = .
        return scalar p_first = .
        exit 0
    }

    tempfile ref tests
    quietly fooddem_reference using "`ref'.csv", sample(sample_total) replace
    preserve
        quietly import delimited using "`ref'.csv", clear
        forvalues i = 1/6 {
            quietly summarize elasticity if elasticity_type == "expenditure" & ///
                demand_good == `i', meanonly
            return scalar exp`i' = r(mean)
            forvalues j = 1/6 {
                quietly summarize elasticity if elasticity_type == "marshallian" & ///
                    demand_good == `i' & shock_good == `j', meanonly
                return scalar mar_`i'_`j' = r(mean)
                quietly summarize elasticity if elasticity_type == "hicksian" & ///
                    demand_good == `i' & shock_good == `j', meanonly
                return scalar hix_`i'_`j' = r(mean)
            }
        }
    restore

    quietly fooddem_tests using "`tests'.csv", demographics(`core') replace
    preserve
        quietly import delimited using "`tests'.csv", clear
        quietly summarize statistic if test == "demographics_joint_zero", meanonly
        return scalar stat_dem = r(mean)
        quietly summarize statistic if test == "all_share_shifters_joint_zero", meanonly
        return scalar stat_all = r(mean)
        quietly summarize statistic if test == "Shonkwiler_Yen_terms_joint_zero", meanonly
        return scalar stat_sy = r(mean)
        quietly summarize statistic if test == "Hansen_overidentification", meanonly
        return scalar stat_hansen = r(mean)
        quietly summarize statistic if test == "excluded_instruments_first_stage", meanonly
        return scalar stat_first = r(mean)
        quietly summarize p_value if test == "demographics_joint_zero", meanonly
        return scalar p_dem = r(mean)
        quietly summarize p_value if test == "all_share_shifters_joint_zero", meanonly
        return scalar p_all = r(mean)
        quietly summarize p_value if test == "Shonkwiler_Yen_terms_joint_zero", meanonly
        return scalar p_sy = r(mean)
        quietly summarize p_value if test == "Hansen_overidentification", meanonly
        return scalar p_hansen = r(mean)
        quietly summarize p_value if test == "excluded_instruments_first_stage", meanonly
        return scalar p_first = r(mean)
    restore
end

local retlist ""
forvalues i = 1/6 {
    local retlist "`retlist' exp`i'=r(exp`i')"
    forvalues j = 1/6 {
        local retlist "`retlist' mar_`i'_`j'=r(mar_`i'_`j')"
        local retlist "`retlist' hix_`i'_`j'=r(hix_`i'_`j')"
    }
}
foreach z in stat_dem stat_all stat_sy stat_hansen stat_first ///
    p_dem p_all p_sy p_hansen p_first {
    local retlist "`retlist' `z'=r(`z')"
}

local reps = 19
if "$TOTAL_BOOT_REPS" != "" local reps = real("$TOTAL_BOOT_REPS")
bootstrap `retlist', reps(`reps') seed(20260714) ///
    cluster(village_cluster) idcluster(boot_cluster) ///
    saving("$EASI_OUT/total_bootstrap_replicates.dta", replace) nodots: ///
    _total_boot

local successful = e(N_reps)
local failed = `reps' - `successful'
local clusters = e(N_clust)

* Keep original reference estimates and delta-method p-values alongside the
* cluster-bootstrap standard errors and percentile confidence intervals.
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
    local b25 = r(p2_5)
    local b975 = r(p97_5)
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
        (`b25') (`b975') ///
        (`bm') (`bs') (2*normal(-abs(`est'/`bs'))) (`successful') (`failed')
    forvalues j = 1/6 {
        foreach typ in mar hix {
            local outtype = cond("`typ'" == "mar", "marshallian", "hicksian")
            local var "`typ'_`i'_`j'"
            quietly summarize `var', detail
            local bm = r(mean)
            local bs = r(sd)
            local b25 = r(p2_5)
            local b975 = r(p97_5)
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
                (`b25') (`b975') ///
                (`bm') (`bs') (2*normal(-abs(`est'/`bs'))) (`successful') (`failed')
        }
    }
}
postclose `emem'
use `eres', clear
export delimited using "$EASI_OUT/total_bootstrap_elasticities.csv", replace

* Bootstrap distributions of specification-test statistics are descriptive;
* the formal test p-values remain the full-sample Hansen/SY/first-stage values.
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
    local pvar "`3'"
    quietly summarize `var', detail
    local bm = r(mean)
    local bs = r(sd)
    local b25 = r(p2_5)
    local b50 = r(p50)
    local b975 = r(p97_5)
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

display as text "total-consumption cluster bootstrap completed: " ///
    `successful' " successful, " `failed' " failed, clusters=" `clusters'
