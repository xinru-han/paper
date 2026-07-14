version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

* Data invariants used by every structural specification.
use "$EASI_DATA/easi_analysis_ready.dta", clear
isid household_id
assert strlen(household_id) == 14
assert strlen(village_id) == 12
assert abs(share_sum - 1) < 1e-8
forvalues g = 1/6 {
    assert p`g' > 0 & q`g' >= 0 & inrange(s`g', 0, 1)
    bysort village_id data_year: assert p`g' == p`g'[1]
}

* Every one-step candidate must leave the Hansen p-value undefined. Exactly one
* converged candidate is selected after the nested tests and nonnested BIC step.
import delimited using "$EASI_OUT/model_selection_gmm_onestep.csv", clear
assert missing(j_p) if gmm_steps == 1
count if bic_preferred == 1
assert r(N) == 1
assert converged == 1 if bic_preferred == 1

import delimited using "$EASI_OUT/selected_model_summary.csv", clear
assert _N == 1
assert converged == 1 & gmm_steps == 2
assert inrange(j_p, 0, 1)
assert firststage_f > 0 & inrange(firststage_p, 0, 1)

import delimited using "$EASI_OUT/selected_model_tests.csv", clear
count if test == "Hansen_overidentification" & inrange(p_value, 0, 1)
assert r(N) == 1
count if test == "theory_restrictions_imposed" & statistic == 1
assert r(N) == 1

import delimited using "$EASI_OUT/selected_model_elasticities.csv", clear
assert _N == 78
assert n_valid > 0 & !missing(elasticity)
count if elasticity_type == "expenditure"
assert r(N) == 6

import delimited using "$EASI_OUT/income_elasticity_summary.csv", clear
assert _N == 30
assert n > 0 & !missing(mean)

foreach f in selected_model_regularity.csv selected_nlsur_regularity.csv {
    import delimited using "$EASI_OUT/`f'", clear
    count if diagnostic == "adding_up_max_abs_error" & passed == 1
    assert r(N) == 1
    count if diagnostic == "slutsky_symmetry_max_abs_error" & passed == 1
    assert r(N) == 1
}

import delimited using "$EASI_OUT/model_selection_nlsur_cf.csv", clear
count if bic_preferred == 1
assert r(N) == 1
assert converged == 1 if bic_preferred == 1

import delimited using "$EASI_OUT/instrument_firststage_diagnostics.csv", clear
assert _N == 3
count if test == "excluded_instruments_joint" & df_num == 2 & df_den > 0
assert r(N) == 1
assert partial_r2 > 0 & inrange(p_value, 0, 1)

import delimited using "$EASI_OUT/instrument_sensitivity_summary.csv", clear
assert _N == 4
assert n == 3200 & converged == 1
assert inrange(j_p, 0, 1)
assert max_abs_b_diff_main < 1e-5 if specification == "income_log_and_inverse"

import delimited using "$EASI_OUT/instrument_sensitivity_elasticities.csv", clear
assert _N == 312
assert n_valid > 0 & !missing(elasticity)

import delimited using "$EASI_OUT/instrument_sensitivity_regularity.csv", clear
assert _N == 28
count if diagnostic == "adding_up_max_abs_error" & passed == 1
assert r(N) == 4
count if diagnostic == "slutsky_symmetry_max_abs_error" & passed == 1
assert r(N) == 4

* Source-specific reconstruction and primary replacement-cost system.
use "$EASI_DATA/village_self_prices.dta", clear
isid village_id data_year
assert _N == 361
forvalues g = 1/6 {
    assert pself`g' > 0 & pself`g' < .
    assert inrange(pself`g'_source, 1, 6)
}

use "$EASI_DATA/source_analysis_ready.dta", clear
isid household_id
forvalues g = 1/6 {
    assert qt`g' >= 0 & qt`g' < . & qb`g' >= 0 & qb`g' < . & ///
        qs`g' >= 0 & qs`g' < . & qg`g' >= 0 & qg`g' < . & ///
        qo`g' >= 0 & qo`g' < .
    assert abs(qt`g' - qb`g' - qs`g' - qg`g') < 1e-5 * max(1, qt`g')
    assert abs(qo`g' - qb`g' - qg`g') < 1e-8
    assert p`g' > 0 & p`g' < .
    assert pself`g' > 0 & pself`g' < .
    assert inrange(st`g', 0, 1) if sample_total
}
egen double _check_st = rowtotal(st1 st2 st3 st4 st5 st6)
assert abs(_check_st - 1) < 1e-8 if sample_total
drop _check_st

import delimited using "$EASI_OUT/source_model_selection_total.csv", clear
count if bic_preferred == 1 & converged == 1
assert r(N) == 1

import delimited using "$EASI_OUT/source_composition_descriptives.csv", clear
assert _N == 6
assert n > 0 & total_quantity_mean >= 0
assert inrange(purchase_participation, 0, 1) & ///
    inrange(self_participation, 0, 1) & inrange(gift_participation, 0, 1)

foreach system in total buy omitself self {
    import delimited using "$EASI_OUT/source_`system'_tests.csv", clear
    count if test == "Hansen_overidentification" & inrange(p_value, 0, 1)
    assert r(N) == 1
    count if test == "theory_restrictions_imposed" & statistic == 1
    assert r(N) == 1
}

foreach f in source_total_elasticities_unconditional.csv ///
    source_total_elasticities_intensive.csv source_total_elasticities_latent.csv ///
    source_buy_elasticities_unconditional.csv source_buy_elasticities_latent.csv ///
    source_omitself_elasticities_unconditional.csv ///
    source_omitself_elasticities_latent.csv {
    import delimited using "$EASI_OUT/`f'", clear
    assert _N == 78
    assert n_valid > 0 & !missing(aggregate_elasticity)
}

import delimited using "$EASI_OUT/source_total_curvature_projection.csv", clear
assert _N == 36
assert projected_max_eigenvalue <= 1e-8
assert projected_hicksian <= 1e-10 if demand_good == shock_good

* The preferred repair reestimates EASI with local curvature at the sample
* average, rather than changing positive elasticities after estimation.
import delimited using "$EASI_OUT/source_total_curvature_estimation_comparison.csv", clear
assert _N == 5
assert converged == 1 if specification == "curvature_local"
assert reference_max_eigenvalue <= 1e-8 if specification == "curvature_local"
assert hansen_p > .05 if specification == "curvature_local"
assert converged == 0 & hansen_p < .01 if specification == "curvature_global"
assert converged == 1 & hansen_p > .05 if specification == "directprice_unrestr"
assert hansen_p < .01 if specification == "directprice_local"

import delimited using "$EASI_OUT/source_total_curvature_constrained_reference.csv", clear
assert _N == 78
assert elasticity <= 1e-8 if elasticity_type == "hicksian" & ///
    demand_good == shock_good
assert !missing(std_error, p_value, ci_low, ci_high)

* Global curvature is a deliberately stronger diagnostic. It must eliminate
* every positive own-price response, but it is not accepted as the main model
* unless it also converges and passes specification tests.
import delimited using "$EASI_OUT/source_total_curvature_global_regularity_latent.csv", clear
count if diagnostic == "negative_hicksian_own_elasticities" & passed == 1
assert r(N) == 1
count if diagnostic == "slutsky_max_eigenvalue" & passed == 1
assert r(N) == 1

* The direct-price unrestricted model is the price-identification robustness
* result: all six aggregate own-price elasticities are negative and its Hansen
* test passes. Locally constraining this smaller sample is rejected, so it is
* not substituted for the unrestricted direct-price estimates.
import delimited using "$EASI_OUT/source_total_directprice_elasticities_latent.csv", clear
assert aggregate_elasticity < 0 if elasticity_type == "hicksian" & ///
    demand_good == shock_good

import delimited using "$EASI_OUT/source_total_directprice_reference_unconstrained.csv", clear
assert _N == 78
assert elasticity < 0 if elasticity_type == "hicksian" & ///
    demand_good == shock_good
assert !missing(std_error, p_value, ci_low, ci_high)

import delimited using "$EASI_OUT/source_omission_bias_tests.csv", clear
assert _N == 12
assert bootstrap_reps_requested >= 199 & bootstrap_reps_successful >= 99 ///
    & clusters > 1
assert bootstrap_reps_successful + bootstrap_reps_failed == ///
    bootstrap_reps_requested
assert !missing(difference, se, p_value)

import delimited using "$EASI_OUT/source_self_allocation_models.csv", clear
assert _N == 72
assert n > 0 & !missing(coefficient, se, p_value)

import delimited using "$EASI_OUT/source_elasticity_comparison.csv", clear
assert _N == 120
assert !missing(aggregate_elasticity, trimmed_aggregate)
assert structural_interpretation == 0 if system == "self"
assert structural_interpretation == 1 if system != "self"

import delimited using "$EASI_OUT/source_income_elasticity_summary.csv", clear
assert _N == 120
assert n > 0 & !missing(mean)
assert structural_interpretation == 0 if system == "self"
assert structural_interpretation == 1 if system != "self"

display as result "community-price food-demand output validation passed"
