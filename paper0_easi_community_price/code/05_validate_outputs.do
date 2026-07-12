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

import delimited using "$EASI_OUT/geasi_robustness_status.csv", clear
assert _N == 1
assert missing(j_p)
assert return_code == 0 & converged == 1

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

display as result "community-price food-demand output validation passed"
