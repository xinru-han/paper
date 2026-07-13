version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

use "$EASI_DATA/source_analysis_ready.dta", clear
egen long village_cluster = group(village_id data_year)
keep if sample_omitself

* Full-sample two-step estimates provide stable starts in resampled villages.
* They do not alter the one-step weighting used for the bootstrap contrast.
estimates use "$EASI_OUT/source_total_gmm_twostep.ster"
matrix FD_BOOT_TOTAL_START = e(b)
estimates use "$EASI_OUT/source_omitself_gmm_twostep.ster"
matrix FD_BOOT_OMIT_START = e(b)

capture program drop _source_gap
program define _source_gap, rclass
    version 17
    local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
    local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
    local geo "province_2 province_3 province_4 province_5 province_6 province_7 province_8"
    local demos "`core' `geo'"
    capture confirm variable boot_cluster
    if _rc local cl "village_cluster"
    else local cl "boot_cluster"
    capture estimates drop FD_BOOT_TOTAL_EST

    * Both systems use the same households, EASI(1) form, instruments, and
    * one-step GMM weighting. The paired difference isolates source omission.
    quietly fooddem, model(easi) order(1) shares(st1 st2 st3 st4 st5 st6) ///
        prices(`prices') expenditure(ln_foodexp_total) estimator(gmm) ///
        demographics(`demos') quantities(qt1 qt2 qt3 qt4 qt5 qt6) ///
        selection(sy) endogeneity(iv) instruments(ln_income inv_income) ///
        cluster(`cl') gmmsteps(1) from(FD_BOOT_TOTAL_START) ///
        iterate(80) tolerance(1e-5)
    estimates store FD_BOOT_TOTAL_EST
    local totalshares ""
    forvalues g = 1/6 {
        tempvar tw`g'
        local totalshares "`totalshares' `tw`g''"
    }
    quietly fooddem_p `totalshares'
    tempvar joint_support
    gen byte `joint_support' = 1
    foreach w of local totalshares {
        replace `joint_support' = 0 if missing(`w') | `w' <= 0
    }

    quietly fooddem, model(easi) order(1) shares(so1 so2 so3 so4 so5 so6) ///
        prices(`prices') expenditure(ln_foodexp_omitself) estimator(gmm) ///
        demographics(`demos') quantities(qo1 qo2 qo3 qo4 qo5 qo6) ///
        selection(sy) endogeneity(iv) instruments(ln_income inv_income) ///
        cluster(`cl') gmmsteps(1) from(FD_BOOT_OMIT_START) ///
        iterate(80) tolerance(1e-5)
    local omitshares ""
    forvalues g = 1/6 {
        tempvar ow`g'
        local omitshares "`omitshares' `ow`g''"
    }
    quietly fooddem_p `omitshares'
    foreach w of local omitshares {
        replace `joint_support' = 0 if missing(`w') | `w' <= 0
    }

    tempfile totalbase omitbase
    local totalfile "`totalbase'.dta"
    local omitfile "`omitbase'.dta"
    quietly fooddem_elasticities using `omitfile', margin(unconditional) ///
        sample(`joint_support') replace
    preserve
        use `omitfile', clear
        forvalues g = 1/6 {
            quietly summarize aggregate_elasticity if ///
                elasticity_type == "expenditure" & demand_good == `g', meanonly
            local oe`g' = r(mean)
            quietly summarize aggregate_elasticity if elasticity_type == "hicksian" & ///
                demand_good == `g' & shock_good == `g', meanonly
            local oh`g' = r(mean)
        }
    restore

    estimates restore FD_BOOT_TOTAL_EST
    quietly fooddem_elasticities using `totalfile', margin(unconditional) ///
        sample(`joint_support') replace
    preserve
        use `totalfile', clear
        forvalues g = 1/6 {
            quietly summarize aggregate_elasticity if ///
                elasticity_type == "expenditure" & demand_good == `g', meanonly
            local te`g' = r(mean)
            quietly summarize aggregate_elasticity if elasticity_type == "hicksian" & ///
                demand_good == `g' & shock_good == `g', meanonly
            local th`g' = r(mean)
        }
    restore
    estimates drop FD_BOOT_TOTAL_EST

    forvalues g = 1/6 {
        return scalar de`g' = `oe`g'' - `te`g''
        return scalar dh`g' = `oh`g'' - `th`g''
    }
end

local reps = 199
if "$SOURCE_BOOT_REPS" != "" local reps = real("$SOURCE_BOOT_REPS")
bootstrap de1=r(de1) de2=r(de2) de3=r(de3) de4=r(de4) de5=r(de5) de6=r(de6) ///
    dh1=r(dh1) dh2=r(dh2) dh3=r(dh3) dh4=r(dh4) dh5=r(dh5) dh6=r(dh6), ///
    reps(`reps') seed(20260713) cluster(village_cluster) idcluster(boot_cluster) ///
    nodots saving("$EASI_OUT/source_omission_bootstrap_replicates.dta", replace): ///
    _source_gap

tempname b V mem
matrix `b' = e(b)
matrix `V' = e(V)
local nclusters = e(N_clust)
local successful = e(N_reps)
if missing(`successful') local successful = `reps'
local failed = `reps' - `successful'
tempfile result
postfile `mem' str24 elasticity int good double difference se z p_value ///
    ci_low ci_high int bootstrap_reps_requested bootstrap_reps_successful ///
    bootstrap_reps_failed clusters byte gmm_steps str24 contrast ///
    str32 ci_method using `result', replace
local c = 0
foreach type in expenditure hicksian_own {
    forvalues g = 1/6 {
        local ++c
        local diff = `b'[1,`c']
        local se = sqrt(`V'[`c',`c'])
        local z = `diff' / `se'
        post `mem' ("`type'") (`g') (`diff') (`se') (`z') ///
            (2 * normal(-abs(`z'))) (`diff' - 1.96 * `se') ///
            (`diff' + 1.96 * `se') (`reps') (`successful') (`failed') ///
            (`nclusters') (1) ///
            ("omit-self minus total") ("cluster bootstrap normal")
    }
}
postclose `mem'
use `result', clear
export delimited using "$EASI_OUT/source_omission_bias_tests.csv", replace
