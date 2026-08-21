version 17
clear all
set more off
set type double

args project
if `"`project'"' == "" local project "/root/data/Paper/饲料进口弹性/stata_replication_2026"
local input  `"`project'/input"'
local data   `"`project'/data"'
local output `"`project'/output"'

capture mkdir `"`data'"'
capture mkdir `"`output'"'

import delimited using `"`input'/feed_import_panel.csv"', clear encoding(utf8) varnames(1)
encode province_name, gen(province_id)
gen byte quarter = real(substr(year_quarter, -1, 1))
gen int quarter_id = yq(year, quarter)
format quarter_id %tq
xtset province_id quarter_id

gen double ln_expenditure = ln(total_expenditure) if positive_budget == 1

* Match the old pipeline's participation definition: positive import value.
foreach g in corn sorghum cassava oats barley {
    gen byte part_`g' = v_`g' > 0 if !missing(v_`g')
}

* Match the control normalization in revision_2026/code/06.
foreach z in pork beef mutton poultry_meat eggs milk {
    quietly summarize `z' if positive_budget == 1
    gen double z_`z' = (`z' - r(mean)) / r(sd)
}

* Control-function first stage with province and quarter fixed effects.
quietly regress ln_expenditure bartik i.province_id i.quarter_id ///
    if positive_budget == 1
predict double vhat_stata if e(sample), residuals
test bartik
scalar fs_F_conventional = r(F)
scalar fs_p_conventional = r(p)
scalar fs_r2 = e(r2)
scalar fs_N = e(N)

quietly regress ln_expenditure bartik i.province_id i.quarter_id ///
    if positive_budget == 1, vce(cluster province_id)
test bartik
scalar fs_F_cluster = r(F)
scalar fs_p_cluster = r(p)
scalar fs_b = _b[bartik]
scalar fs_se_cluster = _se[bartik]

preserve
    clear
    set obs 1
    gen int N = scalar(fs_N)
    gen double r_squared = scalar(fs_r2)
    gen double coef_bartik = scalar(fs_b)
    gen double se_bartik_cluster = scalar(fs_se_cluster)
    gen double F_conventional = scalar(fs_F_conventional)
    gen double p_conventional = scalar(fs_p_conventional)
    gen double F_cluster = scalar(fs_F_cluster)
    gen double p_cluster = scalar(fs_p_cluster)
    export delimited using `"`output'/first_stage_stata.csv"', replace
restore

keep if positive_budget == 1
egen double share_sum = rowtotal(w_corn w_sorghum w_cassava w_oats w_barley)
foreach g in corn sorghum cassava oats barley {
    replace w_`g' = w_`g' / share_sum
}
drop share_sum
egen double share_sum = rowtotal(w_corn w_sorghum w_cassava w_oats w_barley)
assert abs(share_sum - 1) < 1e-8
assert !missing(bartik, ln_expenditure, vhat_stata)
drop share_sum
compress
save `"`data'/feed_import_estimation.dta"', replace

describe
summarize w_* lnp_* ln_expenditure bartik
