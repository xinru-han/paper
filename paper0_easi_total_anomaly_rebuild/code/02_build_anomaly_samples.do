version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_config.do"

use "$AR_DATA/household_core.dta", clear
rename nhCode household_id
replace household_id = strtrim(household_id)
assert strlen(household_id) <= 20 if household_id != ""
gen str12 village_id = substr(household_id, 1, 12)
gen str9 town_id = substr(village_id, 1, 9)
gen str6 county_id = substr(village_id, 1, 6)
gen str2 province_id = substr(village_id, 1, 2)
isid household_id data_year

merge 1:1 household_id data_year using "$AR_DATA/household_sources.dta", ///
    keep(master match) gen(source_merge)
preserve
    contract source_merge
    export delimited using "$AR_OUT/household_source_merge.csv", replace
restore
assert source_merge == 3
drop source_merge

merge m:1 village_id data_year using "$AR_DATA/village_community_prices.dta", ///
    keep(master match) gen(price_merge)
preserve
    contract price_merge
    export delimited using "$AR_OUT/household_price_merge.csv", replace
restore
assert price_merge == 3
drop price_merge vilLat vilLon

egen byte roster_size = rownonmiss(family1_01_HA1 family1_02_HA1 family1_03_HA1 ///
    family1_04_HA1 family1_05_HA1 family1_06_HA1 family1_07_HA1 family1_08_HA1)
gen byte hhsize_roster_repair = !inrange(HA0, 1, 20) & roster_size > 0
replace HA0 = roster_size if hhsize_roster_repair
rename HA0 hhsize
replace hhsize = . if !inrange(hhsize, 1, 20)

tempname flowmem
tempfile flow
postfile `flowmem' int sequence str60 stage long observations using `flow', replace
post `flowmem' (1) ("households matched to source and price data") (_N)
drop if missing(hhsize)
post `flowmem' (2) ("valid household size") (_N)

local caps "90 30 60 21 150 120"
local dailykg "1.5 .5 1 .35 2.5 2"
local reviewfloors "45 15 30 10.5 75 60"
local physical_flags ""
tempname phmem
tempfile physical_audit
postfile `phmem' int group double cap_jin_pc_month review_floor_jin_pc_month ///
    cap_kg_pc_day long flagged double max_observed using `physical_audit', replace
forvalues g = 1/6 {
    gen double qt`g' = source_total_quantity`g'
    gen double qb`g' = purchase_consumed_quantity`g'
    gen double qs`g' = self_consumed_quantity`g'
    gen double qg`g' = gift_consumed_quantity`g'
    assert abs(qt`g' - qb`g' - qs`g' - qg`g') < 1e-5 * max(1, qt`g')
    assert qt`g' >= 0 & qt`g' < . & qb`g' >= 0 & qb`g' < . & ///
        qs`g' >= 0 & qs`g' < . & qg`g' >= 0 & qg`g' < .
    foreach src in t b s g {
        gen double q`src'`g'_pc = q`src'`g' / hhsize
    }
    local cap : word `g' of `caps'
    local floor : word `g' of `reviewfloors'
    local dcap : word `g' of `dailykg'
    gen byte physical`g' = qt`g'_pc > `cap' if qt`g'_pc < .
    replace physical`g' = 0 if missing(physical`g')
    quietly count if physical`g' == 1
    local nphysical = r(N)
    quietly summarize qt`g'_pc, meanonly
    post `phmem' (`g') (`cap') (`floor') (`dcap') (`nphysical') (r(max))
    local physical_flags "`physical_flags' physical`g'"
}
postclose `phmem'
preserve
    use `physical_audit', clear
    export delimited using "$AR_OUT/physical_quantity_audit.csv", replace
restore
egen byte physical_any = rowmax(`physical_flags')

* Positive-tail screening is source-specific. Medians and MADs are computed
* among positive quantities; sparse province-year cells fall back to the
* positive distribution for the same survey year.
tempname amem
tempfile anomaly_audit
postfile `amem' int group str10 source double threshold long flagged ///
    positive_n double min_flagged median_flagged max_flagged using ///
    `anomaly_audit', replace
local f45 ""
local f50 ""
local f60 ""
local fp99 ""
local f45_main ""
local f50_main ""
local f60_main ""
local fp99_main ""
foreach src in t b s g {
    local sourcelabel "total"
    if "`src'" == "b" local sourcelabel "purchase"
    if "`src'" == "s" local sourcelabel "self"
    if "`src'" == "g" local sourcelabel "gift"
    forvalues g = 1/6 {
        local reviewfloor : word `g' of `reviewfloors'
        gen double lnq`src'`g' = ln(1 + q`src'`g'_pc) if q`src'`g'_pc > 0
        bysort province_id data_year: egen long npos`src'`g' = ///
            total(q`src'`g'_pc > 0)
        bysort province_id data_year: egen double med`src'`g' = ///
            median(lnq`src'`g')
        gen double ad`src'`g' = abs(lnq`src'`g' - med`src'`g') ///
            if q`src'`g'_pc > 0
        bysort province_id data_year: egen double mad`src'`g' = ///
            median(ad`src'`g')
        bysort data_year: egen double ymed`src'`g' = median(lnq`src'`g')
        gen double yad`src'`g' = abs(lnq`src'`g' - ymed`src'`g') ///
            if q`src'`g'_pc > 0
        bysort data_year: egen double ymad`src'`g' = median(yad`src'`g')
        gen double z`src'`g' = ///
            (lnq`src'`g' - med`src'`g') / (1.4826 * mad`src'`g') ///
            if q`src'`g'_pc > 0 & npos`src'`g' >= 10 & mad`src'`g' > 0
        replace z`src'`g' = ///
            (lnq`src'`g' - ymed`src'`g') / (1.4826 * ymad`src'`g') ///
            if q`src'`g'_pc > 0 & missing(z`src'`g') & ymad`src'`g' > 0
        foreach x in 45 50 60 {
            local cutoff = `x' / 10
            gen byte tail`x'_`src'`g' = z`src'`g' > `cutoff' & ///
                q`src'`g'_pc > `reviewfloor' ///
                if !missing(z`src'`g')
            replace tail`x'_`src'`g' = 0 if missing(tail`x'_`src'`g')
            quietly count if tail`x'_`src'`g' == 1
            local nf = r(N)
            quietly summarize q`src'`g'_pc if tail`x'_`src'`g' == 1, detail
            local qmin = r(min)
            local qmed = r(p50)
            local qmax = r(max)
            quietly count if q`src'`g'_pc > 0
            post `amem' (`g') ("`sourcelabel'") (`cutoff') (`nf') (r(N)) ///
                (`qmin') (`qmed') (`qmax')
        }
        gen byte p99_`src'`g' = 0
        quietly levelsof data_year, local(years)
        foreach y of local years {
            quietly count if data_year == `y' & q`src'`g'_pc > 0
            if r(N) >= 20 {
                quietly _pctile q`src'`g'_pc if data_year == `y' & ///
                    q`src'`g'_pc > 0, p(99)
                replace p99_`src'`g' = 1 if data_year == `y' & ///
                    q`src'`g'_pc > r(r1) & q`src'`g'_pc < .
            }
        }
        quietly count if p99_`src'`g' == 1
        local nf99 = r(N)
        quietly summarize q`src'`g'_pc if p99_`src'`g' == 1, detail
        local qmin99 = r(min)
        local qmed99 = r(p50)
        local qmax99 = r(max)
        quietly count if q`src'`g'_pc > 0
        post `amem' (`g') ("`sourcelabel'") (99) (`nf99') (r(N)) ///
            (`qmin99') (`qmed99') (`qmax99')
        local f45 "`f45' tail45_`src'`g'"
        local f50 "`f50' tail50_`src'`g'"
        local f60 "`f60' tail60_`src'`g'"
        local fp99 "`fp99' p99_`src'`g'"
        if inlist("`src'", "t", "s") {
            local f45_main "`f45_main' tail45_`src'`g'"
            local f50_main "`f50_main' tail50_`src'`g'"
            local f60_main "`f60_main' tail60_`src'`g'"
            local fp99_main "`fp99_main' p99_`src'`g'"
        }
    }
}
postclose `amem'
preserve
    use `anomaly_audit', clear
    export delimited using "$AR_OUT/quantity_source_anomaly_audit.csv", replace
restore

egen byte tail45_any = rowmax(`f45')
egen byte tail50_any = rowmax(`f50')
egen byte tail60_any = rowmax(`f60')
egen byte p99_any = rowmax(`fp99')
egen byte tail45_main_any = rowmax(`f45_main')
egen byte tail50_main_any = rowmax(`f50_main')
egen byte tail60_main_any = rowmax(`f60_main')
egen byte p99_main_any = rowmax(`fp99_main')

forvalues g = 1/6 {
    rename p`g'_village p`g'
    assert p`g' > 0 & p`g' < .
    gen double lnp`g' = ln(p`g')
    gen double v`g' = p`g' * qt`g'
    gen double uv_ratio`g' = uv`g' / p`g' if uv`g' > 0
    gen byte uv_ratio_extreme`g' = ///
        (uv_ratio`g' < .25 | uv_ratio`g' > 4) if uv_ratio`g' > 0
    replace uv_ratio_extreme`g' = 0 if missing(uv_ratio_extreme`g')
}
egen double food_exp = rowtotal(v1 v2 v3 v4 v5 v6)
drop if food_exp <= 0 | missing(food_exp)
post `flowmem' (3) ("positive total consumption replacement value") (_N)

gen byte sample_physical = physical_any == 0
gen byte sample_total5 = sample_physical
forvalues g = 1/6 {
    replace sample_total5 = 0 if tail50_t`g' == 1
}
gen byte sample_main = sample_physical & tail50_main_any == 0
gen byte sample_allcomponents = sample_physical & tail50_any == 0
gen byte sample_strict45 = sample_physical & tail45_main_any == 0
gen byte sample_lenient60 = sample_physical & tail60_main_any == 0
gen byte sample_p99 = sample_physical & p99_main_any == 0
gen byte local_all_prices = 1
forvalues g = 1/6 {
    replace local_all_prices = 0 if !inlist(p`g'_source, 1, 3, 4)
}
gen byte sample_main_localprice = sample_main & local_all_prices

quietly count if sample_physical
post `flowmem' (4) ("physical bounds only") (r(N))
quietly count if sample_total5
post `flowmem' (5) ("physical bounds plus total-quantity five-MAD tails") (r(N))
quietly count if sample_main
post `flowmem' (6) ("preferred: total and self-quantity five-MAD tails") (r(N))
quietly count if sample_allcomponents
post `flowmem' (7) ("sensitivity: all source components at five MAD") (r(N))
quietly count if sample_strict45
post `flowmem' (8) ("sensitivity: total and self at 4.5 MAD") (r(N))
quietly count if sample_lenient60
post `flowmem' (9) ("sensitivity: total and self at six MAD") (r(N))
quietly count if sample_p99
post `flowmem' (10) ("sensitivity: total and self positive p99") (r(N))
quietly count if sample_main_localprice
post `flowmem' (11) ("preferred anomalies and own/town/nearest prices") (r(N))
postclose `flowmem'
preserve
    use `flow', clear
    export delimited using "$AR_OUT/sample_flow.csv", replace
restore

forvalues g = 1/6 {
    gen double s`g' = v`g' / food_exp
    assert inrange(s`g', 0, 1)
}
egen double share_sum = rowtotal(s1 s2 s3 s4 s5 s6)
assert abs(share_sum - 1) < 1e-8
gen double ln_foodexp = ln(food_exp)

* Reconstruct household demographics without assuming roster member 01 is head.
gen double child_count = 0
gen double elderly_count = 0
gen double age_observed = 0
gen byte female_head = .
gen double head_education = .
forvalues m = 1/8 {
    local mm : display %02.0f `m'
    gen double age_`mm' = data_year - real(substr(family1_`mm'_HA3, 1, 4))
    replace age_`mm' = . if !inrange(age_`mm', 0, 110)
    replace child_count = child_count + (age_`mm' < 15) if !missing(age_`mm')
    replace elderly_count = elderly_count + (age_`mm' >= 65) if !missing(age_`mm')
    replace age_observed = age_observed + !missing(age_`mm')
    replace female_head = family1_`mm'_HA2 == 0 if family1_`mm'_HA1 == 1 & ///
        inlist(family1_`mm'_HA2, 0, 1) & missing(female_head)
    replace head_education = family2_`mm'_HA10 if family1_`mm'_HA1 == 1 & ///
        missing(head_education)
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

gen double income_annual = total_income_w
replace income_annual = . if income_annual <= 0
gen double ln_income = ln(income_annual)
gen double inv_income = 1 / income_annual if income_annual > 0
gen double total_exp_monthly = monthly_expense_total
replace total_exp_monthly = . if total_exp_monthly <= 0
gen double food_exp_pc = food_exp / hhsize
gen double food_to_total_exp = food_exp / total_exp_monthly ///
    if total_exp_monthly > 0

replace prov = real(substr(village_id, 1, 2)) if missing(prov)
tabulate prov, generate(province_)
tabulate data_year, generate(year_)
capture drop province_1
capture drop year_1
egen long village_cluster = group(village_id data_year)

egen byte uv_ratio_extreme_any = rowmax(uv_ratio_extreme1 uv_ratio_extreme2 ///
    uv_ratio_extreme3 uv_ratio_extreme4 uv_ratio_extreme5 uv_ratio_extreme6)
gen byte sample_model = sample_main & !missing(ln_income, inv_income)

preserve
    keep household_id data_year village_id physical_any tail45_any tail50_any ///
        tail60_any p99_any tail45_main_any tail50_main_any tail60_main_any ///
        p99_main_any uv_ratio_extreme_any sample_physical sample_total5 ///
        sample_main sample_allcomponents sample_strict45 sample_lenient60 ///
        sample_p99 sample_main_localprice
    export delimited using "$AR_OUT/household_anomaly_flags.csv", replace
restore

drop age_01 age_02 age_03 age_04 age_05 age_06 age_07 age_08 ///
    child_count elderly_count age_observed head_education roster_size
keep household_id village_id town_id county_id province_id data_year prov ///
    village_questionnaire_missing village_cluster hhsize ///
    qt1-qt6 qb1-qb6 qs1-qs6 qg1-qg6 ///
    qt1_pc-qt6_pc qb1_pc-qb6_pc qs1_pc-qs6_pc qg1_pc-qg6_pc ///
    p1-p6 lnp1-lnp6 p1_source-p6_source v1-v6 s1-s6 share_sum ///
    food_exp ln_foodexp food_exp_pc food_to_total_exp ///
    uv1-uv6 uv_ratio1-uv_ratio6 uv_ratio_extreme1-uv_ratio_extreme6 ///
    uv_ratio_extreme_any physical1-physical6 physical_any ///
    tail45_any tail50_any tail60_any p99_any tail45_main_any ///
    tail50_main_any tail60_main_any p99_main_any sample_physical ///
    sample_total5 sample_main sample_allcomponents sample_strict45 ///
    sample_lenient60 sample_p99 local_all_prices sample_main_localprice ///
    sample_model child_ratio elderly_ratio female_head head_no_education ///
    head_primary_education age_missing female_head_missing education_missing ///
    income_annual ln_income inv_income total_exp_monthly province_* year_*
compress
save "$AR_DATA/total_anomaly_analysis.dta", replace
