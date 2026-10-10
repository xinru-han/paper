version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
local geo "province_2 province_3 province_4 province_5 province_6 province_7 province_8"
local demos "`core' `geo'"
local excluded "ln_income inv_income"

foreach f in fruit_fresh_basket_prices.csv fruit_category_basket_prices.csv ///
    fruit_subcategory_weights.csv ///
    fruit_category_price_audit.csv fruit_price_identification_diagnostics.csv ///
    fruit_elasticity_specification_comparison.csv fruit_basket_model_selection.csv ///
    source_total_fruitdirect_parameters.csv source_total_fruitdirect_tests.csv ///
    source_total_fruitdirect_reference.csv source_total_fruitdirect_elasticities_latent.csv ///
    source_total_fruitdirect_regularity_latent.csv ///
    source_total_fruitdirect_curvature_parameters.csv ///
    source_total_fruitdirect_curvature_tests.csv ///
    source_total_fruitdirect_curvature_reference.csv ///
    source_total_fruitdirect_curvature_elasticities_latent.csv ///
    source_total_fruitdirect_curvature_regularity_latent.csv ///
    source_total_fruitclean_curvature_parameters.csv ///
    source_total_fruitclean_curvature_tests.csv ///
    source_total_fruitclean_curvature_reference.csv ///
    source_total_fruitclean_curvature_elasticities_latent.csv ///
    source_total_fruitclean_curvature_regularity_latent.csv ///
    source_total_trim99_reference.csv ///
    source_total_fruitbasket_parameters.csv source_total_fruitbasket_tests.csv ///
    source_total_fruitbasket_reference.csv source_total_fruitbasket_elasticities_latent.csv ///
    source_total_fruitbasket_regularity_latent.csv ///
    source_total_fruitbasket_curvature_parameters.csv ///
    source_total_fruitbasket_curvature_tests.csv ///
    source_total_fruitbasket_curvature_reference.csv ///
    source_total_fruitbasket_curvature_elasticities_latent.csv ///
    source_total_fruitbasket_curvature_regularity_latent.csv {
    capture erase "$EASI_OUT/`f'"
}
foreach f in source_total_fruitdirect_gmm.ster ///
    source_total_fruitdirect_curvature_gmm.ster ///
    source_total_fruitclean_curvature_gmm.ster ///
    source_total_fruitbasket_gmm.ster ///
    source_total_fruitbasket_curvature_gmm.ster {
    capture erase "$EASI_OUT/`f'"
}

* The main fruit price prioritizes apple/orange representative quotes even
* though the household quantity aggregate also includes nuts, preserved fruit,
* and dried fruit. Build seven subcategory prices, fill each one separately by
* the pre-specified geographic hierarchy, and combine them with a single set of
* pooled household purchase-expenditure weights. For a subcategory still
* missing after province-year, the builder records province-pooled, national-
* year, and overall medians as explicit last-resort tiers. Constant weights
* avoid local unit-value endogeneity and prevent the basket from changing.
shell /usr/bin/python3 "$EASI_CODE/build_fruit_category_price.py" ///
    --village "$EASI_RAW/村表数据_已清洗.dta" ///
    --household-source "/root/data/数据/食物消费调查数据/导出的数据/家庭食物获取消费/cleaned" ///
    --target "$EASI_DATA/village_community_prices.dta" ///
    --price-output "$EASI_OUT/fruit_category_basket_prices.csv" ///
    --weight-output "$EASI_OUT/fruit_subcategory_weights.csv" ///
    --audit-output "$EASI_OUT/fruit_category_price_audit.csv"
if _rc {
    display as error "seven-category fruit price construction failed"
    exit _rc
}
import delimited using "$EASI_OUT/fruit_category_basket_prices.csv", clear ///
    varnames(1) stringcols(2)
isid village_id data_year
assert p6_basket > 0 & p6_basket < .
compress
save "$EASI_DATA/fruit_category_basket_prices.dta", replace

capture program drop _fruit_reference_row
program define _fruit_reference_row, rclass
    version 17
    syntax using/
    preserve
        import delimited using `"`using'"', clear varnames(1)
        quietly summarize elasticity if elasticity_type == "hicksian" & ///
            demand_good == 6 & shock_good == 6, meanonly
        return scalar elasticity = r(mean)
        quietly summarize std_error if elasticity_type == "hicksian" & ///
            demand_good == 6 & shock_good == 6, meanonly
        return scalar se = r(mean)
        quietly summarize p_value if elasticity_type == "hicksian" & ///
            demand_good == 6 & shock_good == 6, meanonly
        return scalar p = r(mean)
        quietly summarize ci_low if elasticity_type == "hicksian" & ///
            demand_good == 6 & shock_good == 6, meanonly
        return scalar ci_low = r(mean)
        quietly summarize ci_high if elasticity_type == "hicksian" & ///
            demand_good == 6 & shock_good == 6, meanonly
        return scalar ci_high = r(mean)
    restore
end

tempname cmem
tempfile comparisons
postfile `cmem' str32 specification double N clusters J J_df Hansen_p converged ///
    fruit_hicksian se p_value ci_low ci_high using `comparisons', replace

* Existing full-sample and all-six-direct results are included on exactly the
* same sample-average, cluster-robust reference basis.
foreach spec in main_unrestricted main_curvature_local allprice_direct_unrestricted {
    if "`spec'" == "main_unrestricted" {
        estimates use "$EASI_OUT/source_total_gmm_twostep.ster"
        local ref "$EASI_OUT/source_total_reference_unconstrained.csv"
    }
    if "`spec'" == "main_curvature_local" {
        estimates use "$EASI_OUT/source_total_curvature_constrained_gmm.ster"
        local ref "$EASI_OUT/source_total_curvature_constrained_reference.csv"
    }
    if "`spec'" == "allprice_direct_unrestricted" {
        estimates use "$EASI_OUT/source_total_directprice_gmm.ster"
        local ref "$EASI_OUT/source_total_directprice_reference_unconstrained.csv"
    }
    _fruit_reference_row using "`ref'"
    post `cmem' ("`spec'") (e(N)) (e(N_clust)) (e(J)) (e(J_df)) ///
        (chi2tail(e(J_df), e(J))) (e(converged)) (r(elasticity)) (r(se)) ///
        (r(p)) (r(ci_low)) (r(ci_high))
}

use "$EASI_DATA/source_analysis_ready.dta", clear
isid household_id
egen long village_cluster = group(village_id data_year)
gen byte fruit_direct_sample = sample_total & inrange(p6_source, 1, 2)
gen byte fruit_clean_sample = sample_total & source_p996 == 0 & price_robust6 == 0
gen byte trim99_total_sample = sample_total & sample_trim99
merge m:1 village_id data_year using "$EASI_DATA/fruit_category_basket_prices.dta", ///
    keep(match) nogen
merge 1:1 household_id data_year using "$EASI_DATA/unit_value_prices_validation.dta", ///
    keep(master match) nogen

* Price-identification diagnostics distinguish nominal household counts from
* independent village-year support, price-source quality, and compositional
* agreement with corrected household unit values.
tempname dmem
tempfile diagnostics
postfile `dmem' str48 metric double value str160 interpretation using `diagnostics', replace
quietly count if sample_total
post `dmem' ("total_demand_households") (r(N)) ("positive reconstructed total food value")
quietly count if fruit_direct_sample
post `dmem' ("fruit_direct_households") (r(N)) ("fruit price source is own-village code 1 or 2")
quietly summarize fruit_direct_sample if sample_total, meanonly
post `dmem' ("fruit_direct_household_share") (r(mean)) ("remaining households borrow fruit prices geographically")
egen byte tag_cluster = tag(village_cluster) if sample_total
quietly count if tag_cluster
post `dmem' ("total_village_year_clusters") (r(N)) ("cluster level used for inference")
egen byte tag_direct_cluster = tag(village_cluster) if fruit_direct_sample
quietly count if tag_direct_cluster
post `dmem' ("fruit_direct_village_year_clusters") (r(N)) ("independent own-village fruit-price clusters")
egen byte tag_p6 = tag(p6) if sample_total
quietly count if tag_p6
post `dmem' ("main_fruit_unique_prices") (r(N)) ("fewest unique values among the six main community prices")
egen byte tag_p6_direct = tag(p6) if fruit_direct_sample
quietly count if tag_p6_direct
post `dmem' ("direct_fruit_unique_prices") (r(N)) ("unique own-village fruit prices")
egen byte tag_p6_basket = tag(p6_basket) if sample_total
quietly count if tag_p6_basket
post `dmem' ("weighted_basket_unique_prices") (r(N)) ("unique fixed-weight seven-category prices")
egen byte tag_allcat_direct = tag(village_cluster) ///
    if sample_total & all_categories_direct == 1
quietly count if tag_allcat_direct
post `dmem' ("all_categories_direct_clusters") (r(N)) ("villages directly reporting all seven category prices")
quietly summarize direct_category_count if tag_cluster, detail
post `dmem' ("direct_category_count_median") (r(p50)) ("median directly reported subcategories per village")
quietly count if sample_total & qt6 == 0
local fruit_zeros = r(N)
post `dmem' ("fruit_zero_consumption_households") (`fruit_zeros') ("reconstructed source quantities; small but nonzero corner-solution group")
quietly count if sample_total
post `dmem' ("fruit_zero_consumption_share") (`fruit_zeros' / r(N)) ("SY correction is estimated; it is not bypassed in the source system")
quietly summarize source_share_qty6 if sample_total, meanonly
post `dmem' ("fruit_self_quantity_share_mean") (r(mean)) ("own production is relevant but not the dominant fruit source")
quietly count if sample_total & qb6 > 0
local fruit_buyers = r(N)
quietly count if sample_total
post `dmem' ("fruit_purchase_participation") (`fruit_buyers' / r(N)) ("positive purchased fruit quantity")

egen byte village_tag = tag(village_id data_year)
gen double ln_main6 = ln(p6)
gen double ln_basket6 = ln(p6_basket)
gen double ln_uvp6 = ln(uvp6) if uvp6 > 0
quietly correlate ln_main6 ln_uvp6 if village_tag
matrix C = r(C)
post `dmem' ("main_corrected_uv_log_correlation") (C[1,2]) ("community price versus Deaton-corrected unit-value price")
quietly correlate ln_basket6 ln_uvp6 if village_tag
matrix C = r(C)
post `dmem' ("weighted_basket_corrected_uv_log_correlation") (C[1,2]) ("fixed-weight basket versus corrected unit-value price")
quietly correlate ln_basket6 ln_uvp6 if village_tag & all_categories_direct == 1
matrix C = r(C)
post `dmem' ("allcat_direct_corrected_uv_log_correlation") (C[1,2]) ("all seven subcategory prices directly reported")
gen double main_uv_ratio = uvp6 / p6 if village_tag
quietly summarize main_uv_ratio if village_tag, detail
post `dmem' ("main_corrected_uv_median_ratio") (r(p50)) ("corrected unit value divided by main community price")
gen double basket_uv_ratio = uvp6 / p6_basket if village_tag
quietly summarize basket_uv_ratio if village_tag, detail
post `dmem' ("weighted_basket_corrected_uv_median_ratio") (r(p50)) ("corrected unit value divided by weighted basket price")
postclose `dmem'
preserve
    use `diagnostics', clear
    export delimited using "$EASI_OUT/fruit_price_identification_diagnostics.csv", replace
restore

* Existing all-good p99/price-tail sensitivity supplies a broad outlier check.
* It is reported with its Hansen test rather than silently replacing the main
* model if the reduced sample violates the overidentifying restrictions.
estimates use "$EASI_OUT/source_total_trim99_gmm.ster"
fooddem_reference using "$EASI_OUT/source_total_trim99_reference.csv", ///
    sample(trim99_total_sample) replace
_fruit_reference_row using "$EASI_OUT/source_total_trim99_reference.csv"
post `cmem' ("allgood_trim99_unrestricted") (e(N)) (e(N_clust)) (e(J)) (e(J_df)) ///
    (chi2tail(e(J_df), e(J))) (e(converged)) (r(elasticity)) (r(se)) ///
    (r(p)) (r(ci_low)) (r(ci_high))

* Targeted check 1: retain households whose fruit price is observed in their
* own village while allowing the other five community prices to use the
* pre-specified donor hierarchy. This isolates fruit-price measurement without
* requiring all six price groups to be direct.
estimates use "$EASI_OUT/source_total_gmm_twostep.ster"
tempname full_start
matrix `full_start' = e(b)

* Fruit-specific tail check removes only the top one percent of fruit quantity
* and the pre-specified within-province/year fruit-price tail. Other foods do
* not determine this sample, so the diagnostic isolates fruit anomalies.
estimates use "$EASI_OUT/source_total_curvature_constrained_gmm.ster"
tempname fruit_clean_start
matrix `fruit_clean_start' = e(b)
fooddem if fruit_clean_sample, model(easi) order(1) ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    curvature(local) from(`fruit_clean_start') iterate(160) tolerance(1e-5)
estimates save "$EASI_OUT/source_total_fruitclean_curvature_gmm.ster", replace
fooddem_export using "$EASI_OUT/source_total_fruitclean_curvature_parameters.csv", ///
    label("total_easi_fruit_specific_tail_clean_curvature_local") replace
fooddem_tests using "$EASI_OUT/source_total_fruitclean_curvature_tests.csv", ///
    demographics(`core') replace
fooddem_reference using "$EASI_OUT/source_total_fruitclean_curvature_reference.csv", ///
    sample(fruit_clean_sample) replace
fooddem_elasticities using "$EASI_OUT/source_total_fruitclean_curvature_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using "$EASI_OUT/source_total_fruitclean_curvature_regularity_latent.csv", ///
    margin(latent) replace
_fruit_reference_row using "$EASI_OUT/source_total_fruitclean_curvature_reference.csv"
post `cmem' ("fruit_tailclean_curvature_local") (e(N)) (e(N_clust)) (e(J)) (e(J_df)) ///
    (chi2tail(e(J_df), e(J))) (e(converged)) (r(elasticity)) (r(se)) ///
    (r(p)) (r(ci_low)) (r(ci_high))

fooddem if fruit_direct_sample, model(easi) order(1) ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(`full_start') iterate(160) tolerance(1e-5)
estimates save "$EASI_OUT/source_total_fruitdirect_gmm.ster", replace
fooddem_export using "$EASI_OUT/source_total_fruitdirect_parameters.csv", ///
    label("total_easi_fruit_own_village_price") replace
fooddem_tests using "$EASI_OUT/source_total_fruitdirect_tests.csv", ///
    demographics(`core') replace
fooddem_reference using "$EASI_OUT/source_total_fruitdirect_reference.csv", ///
    sample(fruit_direct_sample) replace
fooddem_elasticities using "$EASI_OUT/source_total_fruitdirect_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using "$EASI_OUT/source_total_fruitdirect_regularity_latent.csv", ///
    margin(latent) replace
_fruit_reference_row using "$EASI_OUT/source_total_fruitdirect_reference.csv"
post `cmem' ("fruit_direct_unrestricted") (e(N)) (e(N_clust)) (e(J)) (e(J_df)) ///
    (chi2tail(e(J_df), e(J))) (e(converged)) (r(elasticity)) (r(se)) ///
    (r(p)) (r(ci_low)) (r(ci_high))

tempname fruit_direct_start
matrix `fruit_direct_start' = e(b)
fooddem if fruit_direct_sample, model(easi) order(1) ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    curvature(local) from(`fruit_direct_start') iterate(160) tolerance(1e-5)
estimates save "$EASI_OUT/source_total_fruitdirect_curvature_gmm.ster", replace
fooddem_export using "$EASI_OUT/source_total_fruitdirect_curvature_parameters.csv", ///
    label("total_easi_fruit_own_village_price_curvature_local") replace
fooddem_tests using "$EASI_OUT/source_total_fruitdirect_curvature_tests.csv", ///
    demographics(`core') replace
fooddem_reference using "$EASI_OUT/source_total_fruitdirect_curvature_reference.csv", ///
    sample(fruit_direct_sample) replace
fooddem_elasticities using "$EASI_OUT/source_total_fruitdirect_curvature_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using "$EASI_OUT/source_total_fruitdirect_curvature_regularity_latent.csv", ///
    margin(latent) replace
_fruit_reference_row using "$EASI_OUT/source_total_fruitdirect_curvature_reference.csv"
post `cmem' ("fruit_direct_curvature_local") (e(N)) (e(N_clust)) (e(J)) (e(J_df)) ///
    (chi2tail(e(J_df), e(J))) (e(converged)) (r(elasticity)) (r(se)) ///
    (r(p)) (r(ci_low)) (r(ci_high))

* Targeted check 2: substitute the fixed-weight category basket, then recompute
* replacement value of fruit, total food expenditure, and all budget shares.
* Holding old shares fixed after changing p6 would be internally inconsistent.
rename p6 p6_main
rename lnp6 lnp6_main
rename vt6 vt6_main
rename foodexp_total foodexp_total_main
rename ln_foodexp_total ln_foodexp_total_main
forvalues g = 1/6 {
    rename st`g' st`g'_main
}
gen double p6 = p6_basket
gen double lnp6 = ln(p6)
gen double vt6 = p6 * qt6
egen double foodexp_total = rowtotal(vt1 vt2 vt3 vt4 vt5 vt6)
gen double ln_foodexp_total = ln(foodexp_total)
forvalues g = 1/5 {
    gen double st`g' = vt`g' / foodexp_total
}
gen double st6 = vt6 / foodexp_total
egen double _stcheck = rowtotal(st1 st2 st3 st4 st5 st6)
assert abs(_stcheck - 1) < 1e-8 if sample_total
drop _stcheck
compress
save "$EASI_DATA/source_analysis_fruit_basket.dta", replace

* Changing a price and the associated budget shares can change functional-form
* selection. Repeat the pre-specified AIDS/QUAIDS/EASI comparison rather than
* carrying the main-price result into this sensitivity by assumption.
fooddem_select using "$EASI_OUT/fruit_basket_model_selection.csv" if sample_total, ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) maxorder(3) ///
    demographics(`demos') quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) ///
    endogeneity(iv) instruments(`excluded') cluster(village_cluster) ///
    gmmsteps(1) iterate(80) tolerance(1e-5) replace
local basket_model "`r(preferred_model)'"
local basket_order = r(preferred_order)
local basket_estimate "`r(preferred_estimate)'"
if "`basket_model'" != "easi" | `basket_order' != 1 {
    display as error "weighted fruit basket no longer selects EASI order 1; update the curvature sensitivity explicitly"
    exit 459
}
estimates restore `basket_estimate'
tempname basket_select_start
matrix `basket_select_start' = e(b)

fooddem if sample_total, model(easi) order(1) ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    from(`basket_select_start') iterate(160) tolerance(1e-5)
estimates save "$EASI_OUT/source_total_fruitbasket_gmm.ster", replace
fooddem_export using "$EASI_OUT/source_total_fruitbasket_parameters.csv", ///
    label("total_easi_weighted_seven_category_fruit_price") replace
fooddem_tests using "$EASI_OUT/source_total_fruitbasket_tests.csv", ///
    demographics(`core') replace
fooddem_reference using "$EASI_OUT/source_total_fruitbasket_reference.csv", ///
    sample(sample_total) replace
fooddem_elasticities using "$EASI_OUT/source_total_fruitbasket_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using "$EASI_OUT/source_total_fruitbasket_regularity_latent.csv", ///
    margin(latent) replace
_fruit_reference_row using "$EASI_OUT/source_total_fruitbasket_reference.csv"
post `cmem' ("weighted_basket_unrestricted") (e(N)) (e(N_clust)) (e(J)) (e(J_df)) ///
    (chi2tail(e(J_df), e(J))) (e(converged)) (r(elasticity)) (r(se)) ///
    (r(p)) (r(ci_low)) (r(ci_high))

tempname fruit_basket_start
matrix `fruit_basket_start' = e(b)
fooddem if sample_total, model(easi) order(1) ///
    shares(st1 st2 st3 st4 st5 st6) prices(`prices') ///
    expenditure(ln_foodexp_total) estimator(gmm) demographics(`demos') ///
    quantities(qt1 qt2 qt3 qt4 qt5 qt6) selection(sy) endogeneity(iv) ///
    instruments(`excluded') cluster(village_cluster) gmmsteps(2) ///
    curvature(local) from(`fruit_basket_start') iterate(160) tolerance(1e-5)
estimates save "$EASI_OUT/source_total_fruitbasket_curvature_gmm.ster", replace
fooddem_export using "$EASI_OUT/source_total_fruitbasket_curvature_parameters.csv", ///
    label("total_easi_weighted_seven_category_fruit_price_curvature_local") replace
fooddem_tests using "$EASI_OUT/source_total_fruitbasket_curvature_tests.csv", ///
    demographics(`core') replace
fooddem_reference using "$EASI_OUT/source_total_fruitbasket_curvature_reference.csv", ///
    sample(sample_total) replace
fooddem_elasticities using "$EASI_OUT/source_total_fruitbasket_curvature_elasticities_latent.csv", ///
    margin(latent) replace
fooddem_regularity using "$EASI_OUT/source_total_fruitbasket_curvature_regularity_latent.csv", ///
    margin(latent) replace
_fruit_reference_row using "$EASI_OUT/source_total_fruitbasket_curvature_reference.csv"
post `cmem' ("weighted_basket_curvature_local") (e(N)) (e(N_clust)) (e(J)) (e(J_df)) ///
    (chi2tail(e(J_df), e(J))) (e(converged)) (r(elasticity)) (r(se)) ///
    (r(p)) (r(ci_low)) (r(ci_high))

postclose `cmem'
preserve
    use `comparisons', clear
    export delimited using "$EASI_OUT/fruit_elasticity_specification_comparison.csv", replace
restore

display as result "fruit price-identification diagnostics and sensitivity estimates completed"
