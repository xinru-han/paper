version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_config.do"

use "$AR_DATA/household_sources.dta", clear
isid household_id data_year
assert strlen(household_id) <= 20
forvalues g = 1/6 {
    assert abs(source_total_quantity`g' - purchase_consumed_quantity`g' - ///
        self_consumed_quantity`g' - gift_consumed_quantity`g') < ///
        1e-5 * max(1, source_total_quantity`g')
}

use "$AR_DATA/village_community_prices.dta", clear
isid village_id data_year
forvalues g = 1/6 {
    assert p`g'_village > 0 & p`g'_village <= 200
    assert inlist(p`g'_source, 1, 3, 4, 5, 6)
}

use "$AR_DATA/total_anomaly_analysis.dta", clear
isid household_id data_year
assert abs(share_sum - 1) < 1e-8
assert sample_allcomponents <= sample_main
assert sample_main <= sample_physical
forvalues g = 1/6 {
    assert qt`g' >= 0 & abs(qt`g' - qb`g' - qs`g' - qg`g') < ///
        1e-5 * max(1, qt`g')
    bysort village_id data_year: assert p`g' == p`g'[1]
}

import delimited using "$AR_OUT/model_selection.csv", clear
count if bic_preferred == 1 & converged == 1
assert r(N) == 1
count if easi_order_preferred == 1 & converged == 1
assert r(N) == 1

foreach model in aids quaids easi {
    import delimited using "$AR_OUT/`model'_tests.csv", clear
    count if test == "Hansen_overidentification" & inrange(p_value, 0, 1)
    assert r(N) == 1
    import delimited using "$AR_OUT/`model'_regularity.csv", clear
    count if diagnostic == "adding_up_max_abs_error" & passed == 1
    assert r(N) == 1
    count if diagnostic == "slutsky_symmetry_max_abs_error" & passed == 1
    assert r(N) == 1
}

import delimited using "$AR_OUT/easi_sample_sensitivity_status.csv", clear
assert return_code == 0 & converged == 1
assert inrange(hansen_p, 0, 1)

import delimited using "$AR_OUT/easi_reference_analytic.csv", clear
assert _N == 78
count if elasticity_type == "hicksian" & demand_good == shock_good
assert r(N) == 6
assert elasticity < 0 if elasticity_type == "hicksian" & ///
    demand_good == shock_good

import delimited using "$AR_OUT/easi_reference_bootstrap.csv", clear
assert _N == 18
assert reps_requested >= 199 & reps_successful >= 99 & clusters > 1
assert reps_failed == reps_requested - reps_successful
assert !missing(elasticity, se, p_value, ci_low, ci_high)

display as result "unconstrained anomaly-rebuild validation passed"
