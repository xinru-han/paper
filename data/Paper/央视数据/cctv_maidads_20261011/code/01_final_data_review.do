version 17
clear all
set more off
set type double
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_final_data_review.log",text replace

tempname elasticity checks
postfile `elasticity' str12 model str28 specification byte good double share double expenditure_elasticity ///
    double marshallian_own double hicksian_own double cells double household_windows double stationary ///
    double max_score double positive_support double maximum_slutsky_eigenvalue ///
    using "$run/outputs/data_audit/final_elasticity_review.dta",replace
postfile `checks' str64 check double value using "$run/outputs/data_audit/final_data_review_checks.dta",replace

foreach spec in baseline permonth_size coarse complete_stable year year_permonth_size {
    if "`spec'"=="baseline" {
        local suffix _8
        local data cells_quarter_8
    }
    if inlist("`spec'","permonth_size","coarse","complete_stable") {
        local suffix _quarter_8_`spec'
        local data cells_quarter_8_`spec'
    }
    if "`spec'"=="year" {
        local suffix _year_8
        local data cells_year_8
    }
    if "`spec'"=="year_permonth_size" {
        local suffix _year_8_permonth_size
        local data cells_year_8_permonth_size
    }
    use "$run/data/`data'.dta",clear
    local expected_cells=_N
    quietly summarize nobs,meanonly
    local household_windows=r(sum)
    foreach model in aids quaids {
        local path "$run/outputs/comparators/`model'`suffix'"
        import delimited using "`path'/representative_elasticities.csv",clear asdouble
        sort good
        assert _N==8 & good==_n
        forvalues j=1/8 {
            scalar DA_share`j'=share[`j']
            scalar DA_eta`j'=expenditure_elasticity[`j']
            scalar DA_marshall`j'=marshallian_own[`j']
            scalar DA_hicks`j'=hicksian_own[`j']
            assert abs(hicksian_own-marshallian_own-expenditure_elasticity*share)<1e-10
        }
        import delimited using "`path'/hicksian_matrix.csv",clear asdouble
        sort good
        forvalues j=1/8 {
            assert abs(ct_hicksian`j'[`j']-scalar(DA_hicks`j'))<1e-10
        }
        import delimited using "`path'/fit_summary.csv",clear asdouble
        assert _N==1 & observations==`expected_cells'
        assert stationary==1
        assert budget_error<1e-10 & slutsky_symmetry_error<1e-10
        forvalues j=1/8 {
            post `elasticity' ("`model'") ("`spec'") (`j') (scalar(DA_share`j')) (scalar(DA_eta`j')) ///
                (scalar(DA_marshall`j')) (scalar(DA_hicks`j')) (`expected_cells') (`household_windows') ///
                (stationary[1]) (max_score[1]) (positive_support[1]) (slutsky_max_eig[1])
        }
    }
}
postclose `elasticity'
use "$run/outputs/data_audit/final_elasticity_review.dta",clear
export delimited using "$run/outputs/data_audit/final_elasticity_review.csv",replace
list model specification cells household_windows expenditure_elasticity hicksian_own positive_support maximum_slutsky_eigenvalue if good==1,noobs
preserve
gen byte positive_own=hicksian_own>0
collapse (sum) positive_own_count=positive_own,by(model specification)
export delimited using "$run/outputs/data_audit/final_elasticity_sign_counts.csv",replace
restore

* Income moments are linked from the latest actual quarter, not duplicated by quarter count.
use "$run/data/household_quarter_income_8.dta",clear
keep if year==2022
bysort hh_id (time): keep if _n==_N
keep hh_id year type income_band size_band income_pc_mean income_pc_geomean lnypc_mean lnypc_second ///
    inc1 inc2 budget_linear budget_quadratic food_budget_income_elasticity
foreach v of varlist type income_band size_band income_pc_mean income_pc_geomean lnypc_mean lnypc_second ///
    inc1 inc2 budget_linear budget_quadratic food_budget_income_elasticity {
    rename `v' l_`v'
}
tempfile latest anchor
save `latest'
use "$run/data/household_year_income_8.dta",clear
confirm string variable hh_id
isid hh_id year
assert year==2022 & m>0
local anchor_n=_N
post `checks' ("unique_positive_budget_2022_annual_anchors") (`anchor_n')
assert inc2>=inc1^2-1e-10
assert lnypc_second>=lnypc_mean^2-1e-10
assert income_pc_mean>=income_pc_geomean*(1-1e-12)
merge 1:1 hh_id year using `latest',keep(master match) assert(match using) nogen
foreach v of varlist type income_band size_band income_pc_mean income_pc_geomean lnypc_mean lnypc_second ///
    inc1 inc2 budget_linear budget_quadratic food_budget_income_elasticity {
    assert `v'==l_`v'
}
post `checks' ("annual_attributes_and_posterior_equal_latest_actual_quarter") (1)
keep hh_id year m type income_band size_band
rename m anchor_m
rename type anchor_type
rename income_band anchor_income_band
rename size_band anchor_size_band
save `anchor'
use "$run/data/household_year_8.dta",clear
keep if year==2022 & m>0
assert _N==`anchor_n'
merge 1:1 hh_id year using `anchor',assert(match) nogen
assert m==anchor_m & type==anchor_type & income_band==anchor_income_band & size_band==anchor_size_band
post `checks' ("annual_income_anchor_covers_all_positive_2022_households") (1)

use "$run/data/scenario_inputs_8.dta",clear
confirm string variable hh_id
isid hh_id year scenario_order
assert year==2022 & nobs==1
assert _N==14*`anchor_n'
bysort hh_id year: assert _N==14
merge m:1 hh_id year using `anchor',assert(match) nogen
assert m==anchor_m & baseline_m==anchor_m
assert type==anchor_type & income_band==anchor_income_band & size_band==anchor_size_band
assert m_new==baseline_m & budget_factor==1 & growth_factor==1 if scenario_order==1
assert m_new>0 & m_new<.
gen double __sumw=0
forvalues j=1/8 {
    assert p`j'>0 & p`j'<.
    assert abs(p`j'*q`j'-m*w`j')<1e-10*max(1,m)
    replace __sumw=__sumw+w`j'
    bysort province year: assert p`j'==p`j'[1]
}
assert abs(__sumw-1)<1e-10
post `checks' ("scenario_rows_14_per_unique_household_with_text_ID") (_N)
post `checks' ("scenario_baseline_budget_and_annual_price_budget_closure") (1)
postclose `checks'
use "$run/outputs/data_audit/final_data_review_checks.dta",clear
export delimited using "$run/outputs/data_audit/final_data_review_checks.csv",replace
list,noobs abbreviate(64)
log close
