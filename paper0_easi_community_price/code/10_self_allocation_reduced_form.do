version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"
use "$EASI_DATA/source_analysis_ready.dta", clear
egen long village_cluster = group(village_id data_year)

local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
local geo "province_2 province_3 province_4 province_5 province_6 province_7 province_8"
local controls "ln_income `core' `geo'"
tempname mem
tempfile results
postfile `mem' str16 sample str20 outcome int good str18 price ///
    double coefficient se p_value average_elasticity N price_joint_p ///
    using `results', replace

forvalues g = 1/6 {
    gen double lnqt_control`g' = ln(1 + qt`g')
    foreach restrict in full local_price external_price {
        local qualifier "qt`g' > 0"
        if "`restrict'" == "local_price" local qualifier ///
            "qt`g' > 0 & pself`g'_source <= 3"
        if "`restrict'" == "external_price" local qualifier ///
            "qt`g' > 0 & inrange(pself`g'_source, 2, 4)"

        * Fractional-logit source allocation. The elasticities are elasticities
        * of the expected own-production share, conditional on total category
        * consumption; they are not Hicksian demand elasticities.
        quietly glm source_share_qty`g' lnp`g' lnps`g' lnqt_control`g' ///
            `controls' if `qualifier', family(binomial) link(logit) ///
            vce(cluster village_cluster) iterate(100)
        quietly test lnp`g' lnps`g'
        local jointp = r(p)
        tempvar mu es er
        quietly predict double `mu' if e(sample), mu
        gen double `es' = _b[lnps`g'] * (1 - `mu') if e(sample)
        gen double `er' = _b[lnp`g'] * (1 - `mu') if e(sample)
        quietly summarize `es' if e(sample), meanonly
        local aes = r(mean)
        quietly summarize `er' if e(sample), meanonly
        local aer = r(mean)
        local n = e(N)
        post `mem' ("`restrict'") ("own_quantity_share") (`g') ///
            ("own_opportunity") (_b[lnps`g']) (_se[lnps`g']) ///
            (2 * normal(-abs(_b[lnps`g'] / _se[lnps`g']))) (`aes') (`n') (`jointp')
        post `mem' ("`restrict'") ("own_quantity_share") (`g') ///
            ("community_retail") (_b[lnp`g']) (_se[lnp`g']) ///
            (2 * normal(-abs(_b[lnp`g'] / _se[lnp`g']))) (`aer') (`n') (`jointp')

        * PPML quantity equation retains structural zeros. Coefficients on log
        * prices are conditional reduced-form quantity elasticities.
        quietly glm qs`g' lnp`g' lnps`g' lnqt_control`g' `controls' ///
            if `qualifier', family(poisson) link(log) ///
            vce(cluster village_cluster) iterate(100)
        quietly test lnp`g' lnps`g'
        local jointp = r(p)
        local n = e(N)
        post `mem' ("`restrict'") ("own_quantity_ppml") (`g') ///
            ("own_opportunity") (_b[lnps`g']) (_se[lnps`g']) ///
            (2 * normal(-abs(_b[lnps`g'] / _se[lnps`g']))) ///
            (_b[lnps`g']) (`n') (`jointp')
        post `mem' ("`restrict'") ("own_quantity_ppml") (`g') ///
            ("community_retail") (_b[lnp`g']) (_se[lnp`g']) ///
            (2 * normal(-abs(_b[lnp`g'] / _se[lnp`g']))) ///
            (_b[lnp`g']) (`n') (`jointp')
    }
}
postclose `mem'
use `results', clear
export delimited using "$EASI_OUT/source_self_allocation_models.csv", replace
