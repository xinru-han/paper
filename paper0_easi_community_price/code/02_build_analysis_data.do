version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

use "$EASI_RAW/户表数据_已清洗.dta", clear
rename nhCode household_id
replace household_id = strtrim(household_id)
assert strlen(household_id) == 14 if household_id != ""
gen str12 village_id = substr(household_id, 1, 12)
gen str9 town_id = substr(village_id, 1, 9)
gen str6 county_id = substr(village_id, 1, 6)
gen str2 province_id = substr(village_id, 1, 2)
isid household_id

* Six mutually exclusive demand groups, all measured in jin per month.
rename zhushi_cons_monthly_jin q1
rename doulei_cons_monthly_jin q2
rename roulei_cons_monthly_jin q3
rename youzhi_cons_monthly_jin q4
rename shucai_cons_monthly_jin q5
rename shuiguo_cons_monthly_jin q6
rename zhushi_price_wavg_yuan_per_jin uv_legacy1
rename doulei_price_wavg_yuan_per_jin uv_legacy2
rename roulei_price_wavg_yuan_per_jin uv_legacy3
rename youzhi_price_wavg_yuan_per_jin uv_legacy4
rename shucai_price_wavg_yuan_per_jin uv_legacy5
rename shuiguo_price_wavg_yuan_per_jin uv_legacy6
merge 1:1 household_id data_year using "$EASI_DATA/household_unit_values.dta", ///
    keep(master match) gen(uv_merge)
assert uv_merge == 3
drop uv_merge uv_legacy1 uv_legacy2 uv_legacy3 uv_legacy4 uv_legacy5 uv_legacy6
local qlist "q1 q2 q3 q4 q5 q6"
local ulist "uv1 uv2 uv3 uv4 uv5 uv6"
local plist "p1 p2 p3 p4 p5 p6"
local vlist "v1 v2 v3 v4 v5 v6"
local purchasevalues "purchase_value1 purchase_value2 purchase_value3 purchase_value4 purchase_value5 purchase_value6"
local slist "s1 s2 s3 s4 s5 s6"
local lnplist "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
forvalues g = 1/6 {
    replace q`g' = . if q`g' < 0
    replace uv`g' = . if uv`g' <= 0 | uv`g' > 200
}

* Exact text-key merge. The price build already includes household village-year
* keys absent from the village questionnaire, with a documented geographic
* source; no unmatched household is silently discarded here.
merge m:1 village_id data_year using "$EASI_DATA/village_community_prices.dta", ///
    keep(master match) gen(price_merge)
preserve
    contract price_merge
    export delimited using "$EASI_OUT/household_village_merge_audit.csv", replace
restore
assert price_merge == 3
drop price_merge vilLat vilLon

tempname flowmem
tempfile flow
postfile `flowmem' int sequence str48 stage long observations using `flow', replace
post `flowmem' (1) ("raw households with exact price-key match") (_N)

local household_raw = _N
egen byte roster_size = rownonmiss(family1_01_HA1 family1_02_HA1 family1_03_HA1 ///
    family1_04_HA1 family1_05_HA1 family1_06_HA1 family1_07_HA1 family1_08_HA1)
gen double hhsize_reported = HA0
quietly count if inrange(HA0, 1, 20) & roster_size > 0 & HA0 != roster_size
local hhsize_mismatch = r(N)
gen byte hhsize_roster_repair = !inrange(HA0, 1, 20) & roster_size > 0
quietly count if hhsize_roster_repair
local hhsize_repaired = r(N)
replace HA0 = roster_size if hhsize_roster_repair
rename HA0 hhsize
replace hhsize = . if !inrange(hhsize, 1, 20)
quietly count if missing(hhsize)
local hhsize_unresolved = r(N)
drop if missing(hhsize)
post `flowmem' (2) ("valid positive household size") (_N)
egen byte q_missing = rowmiss(`qlist')
drop if q_missing > 0
drop q_missing
post `flowmem' (3) ("complete nonnegative six-group quantities") (_N)

* The source cleaning notes explicitly leave extreme input/frequency errors
* unresolved. Apply conservative physical upper bounds to monthly per-capita
* quantities rather than winsorizing shares. In jin/person/month these imply
* daily maxima of 1.5kg staple, .5kg beans, 1kg meat, .35kg oil, 2.5kg
* vegetables, and 2kg fruit. Values below those generous bounds are untouched.
local caps "90 30 60 21 150 120"
local dailykg "1.5 .5 1 .35 2.5 2"
tempname qmem
tempfile qrules
postfile `qmem' int group double cap_jin_pc_month cap_kg_pc_day long flagged ///
    double observed_max_jin_pc_month using `qrules', replace
local qflags ""
forvalues g = 1/6 {
    local cap : word `g' of `caps'
    local dcap : word `g' of `dailykg'
    gen double q`g'_pc = q`g' / hhsize
    gen byte q`g'_implausible = q`g'_pc > `cap' if !missing(q`g'_pc)
    quietly count if q`g'_implausible == 1
    local nf = r(N)
    quietly summarize q`g'_pc, meanonly
    post `qmem' (`g') (`cap') (`dcap') (`nf') (r(max))
    local qflags "`qflags' q`g'_implausible"
}
postclose `qmem'
preserve
    use `qrules', clear
    export delimited using "$EASI_OUT/quantity_plausibility_audit.csv", replace
restore
egen byte quantity_implausible = rowmax(`qflags')
drop if quantity_implausible == 1
post `flowmem' (4) ("after physical quantity plausibility screen") (_N)

forvalues g = 1/6 {
    rename p`g'_village p`g'
    assert p`g' > 0 & p`g' < .
    gen double v`g' = p`g' * q`g'
}
egen double food_exp = rowtotal(`vlist')
drop if food_exp <= 0 | missing(food_exp)
post `flowmem' (5) ("positive six-group consumption expenditure") (_N)
postclose `flowmem'
preserve
    use `flow', clear
    gen long removed_from_previous = observations[_n-1] - observations
    replace removed_from_previous = 0 in 1
    export delimited using "$EASI_OUT/sample_flow.csv", replace
restore

forvalues g = 1/6 {
    gen double s`g' = v`g' / food_exp
    assert inrange(s`g', 0, 1)
    gen double lnp`g' = ln(p`g')
}
egen double share_sum = rowtotal(`slist')
assert abs(share_sum - 1) < 1e-8
gen double ln_foodexp = ln(food_exp)

* Household composition and the actual household head are reconstructed from
* relation codes. Member 01 is not assumed to be the head.
gen double child_count = 0
gen double elderly_count = 0
gen double age_observed = 0
gen byte female_head = .
gen double head_education = .
gen byte head_count = 0
forvalues m = 1/8 {
    local mm : display %02.0f `m'
    gen double age_`mm' = data_year - real(substr(family1_`mm'_HA3, 1, 4))
    replace age_`mm' = . if !inrange(age_`mm', 0, 110)
    replace child_count = child_count + (age_`mm' < 15) if !missing(age_`mm')
    replace elderly_count = elderly_count + (age_`mm' >= 65) if !missing(age_`mm')
    replace age_observed = age_observed + !missing(age_`mm')
    replace head_count = head_count + (family1_`mm'_HA1 == 1) if !missing(family1_`mm'_HA1)
    replace female_head = family1_`mm'_HA2 == 0 if family1_`mm'_HA1 == 1 & ///
        inlist(family1_`mm'_HA2, 0, 1) & missing(female_head)
    replace head_education = family2_`mm'_HA10 if family1_`mm'_HA1 == 1 & missing(head_education)
}
gen double child_ratio = child_count / age_observed if age_observed > 0
gen double elderly_ratio = elderly_count / age_observed if age_observed > 0
gen byte age_missing = missing(child_ratio) | missing(elderly_ratio)
replace child_ratio = 0 if missing(child_ratio)
replace elderly_ratio = 0 if missing(elderly_ratio)
gen byte female_head_missing = missing(female_head)
replace female_head = 0 if missing(female_head)
gen byte education_missing = missing(head_education)
gen byte head_no_education = head_education == 1 if !missing(head_education)
gen byte head_primary_education = head_education == 2 if !missing(head_education)
replace head_no_education = 0 if missing(head_no_education)
replace head_primary_education = 0 if missing(head_primary_education)

* Aggregate audit prevents silent repairs and documents the original coding.
tempname dmem
tempfile daudit
postfile `dmem' str48 metric double value using `daudit', replace
post `dmem' ("households before household-size screen") (`household_raw')
post `dmem' ("reported size differs from roster") (`hhsize_mismatch')
post `dmem' ("invalid size repaired from roster") (`hhsize_repaired')
post `dmem' ("unresolved size dropped") (`hhsize_unresolved')
quietly count if head_count > 0
post `dmem' ("households with identified head") (r(N))
quietly count if head_count > 1
post `dmem' ("households with multiple head codes") (r(N))
quietly count if female_head == 1
post `dmem' ("identified female heads (sex code zero)") (r(N))
quietly count if female_head_missing == 1
post `dmem' ("head sex missing") (r(N))
postclose `dmem'
preserve
    use `daudit', clear
    export delimited using "$EASI_OUT/household_demographic_audit.csv", replace
restore
drop age_01 age_02 age_03 age_04 age_05 age_06 age_07 age_08 ///
    child_count elderly_count age_observed head_education head_count ///
    roster_size hhsize_reported hhsize_roster_repair

gen double income_annual = total_income_w
replace income_annual = . if income_annual <= 0
gen double ln_income = ln(income_annual)
gen double inv_income = 1 / income_annual if income_annual > 0
gen double total_exp_monthly = monthly_expense_total
replace total_exp_monthly = . if total_exp_monthly <= 0
replace prov = real(substr(village_id, 1, 2)) if missing(prov)
tabulate prov, generate(province_)
tabulate data_year, generate(year_)
drop province_1 year_1
ds province_*, has(type numeric)
local province_fe `r(varlist)'
ds year_*, has(type numeric)
local year_fe `r(varlist)'
* Province and wave are not jointly identified: provinces 2, 4, 5, and 6 occur
* only in wave 2 and the remaining provinces only in wave 1. Retain wave dummies
* in the analysis file for description, but use province effects in share models.
global EASI_Z "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing `province_fe'"

order household_id village_id data_year `qlist' `plist' p1_source p2_source p3_source ///
    p4_source p5_source p6_source `vlist' `slist' `lnplist' food_exp ln_foodexp hhsize
label var food_exp "Six-group monthly food expenditure using village community prices"
label var p1 "Community price: staple foods (yuan/jin)"
label var p2 "Community price: beans and bean products (yuan/jin)"
label var p3 "Community price: meat (yuan/jin)"
label var p4 "Community price: edible oils (yuan/jin)"
label var p5 "Community price: vegetables (yuan/jin)"
label var p6 "Community price: fruit (yuan/jin)"
keep household_id village_id town_id county_id province_id data_year prov provn countyn townn viln ///
    village_questionnaire_missing `qlist' q1_pc q2_pc q3_pc q4_pc q5_pc q6_pc ///
    quantity_implausible `plist' p1_source p2_source p3_source p4_source p5_source p6_source ///
    `ulist' `purchasevalues' `vlist' `slist' `lnplist' food_exp ln_foodexp share_sum hhsize ///
    child_ratio elderly_ratio female_head head_no_education head_primary_education ///
    age_missing female_head_missing education_missing income_annual ln_income inv_income ///
    total_exp_monthly `province_fe' `year_fe'
compress
save "$EASI_DATA/easi_analysis_ready.dta", replace
