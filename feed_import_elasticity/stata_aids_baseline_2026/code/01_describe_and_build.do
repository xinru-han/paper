version 17
clear all
set more off
set type double
set linesize 180

args project rawdir
if `"`project'"' == "" local project "/root/data/Paper/饲料进口弹性/stata_aids_baseline_2026"
if `"`rawdir'"' == "" local rawdir "/root/data/Paper/饲料进口弹性/data"
local data   `"`project'/data"'
local output `"`project'/output"'
local logs   `"`project'/logs"'
capture mkdir `"`data'"'
capture mkdir `"`output'"'
capture mkdir `"`logs'"'
capture log close _all
log using `"`logs'/01_describe_and_build.log"', text replace

tempfile raw_all
local first = 1
forvalues year = 2017/2023 {
    import delimited using `"`rawdir'/`year'-feed.csv"', clear encoding(utf8) varnames(1)
    keep 进出口类型 日期 商品编码 商品名称 金额 第一数量 第一计量单位 贸易伙伴名称 贸易方式 货币 地址
    rename (进出口类型 日期 商品名称 第一计量单位 贸易伙伴名称 贸易方式 货币 地址) ///
           (trade_type date product_name qty_unit partner trade_mode currency province)
    capture confirm numeric variable 商品编码
    if !_rc tostring 商品编码, gen(hs8) format(%08.0f) force
    else gen str12 hs8 = strtrim(商品编码)
    capture confirm numeric variable 金额
    if !_rc gen double value_usd = 金额
    else destring 金额, gen(value_usd) ignore(",") force
    capture confirm numeric variable 第一数量
    if !_rc gen double qty_kg = 第一数量
    else destring 第一数量, gen(qty_kg) ignore(",") force
    drop 商品编码 金额 第一数量
    gen int source_year = `year'
    if `first' {
        save `raw_all', replace
        local first = 0
    }
    else {
        append using `raw_all'
        save `raw_all', replace
    }
}

use `raw_all', clear
keep if trade_type == "进口"
gen byte product_id = .
replace product_id = 1 if inlist(hs8, "10051000", "10059000")
replace product_id = 2 if inlist(hs8, "10071000", "10079000")
replace product_id = 3 if hs8 == "07141020"
replace product_id = 4 if inlist(hs8, "10041000", "10049000")
replace product_id = 5 if inlist(hs8, "10031000", "10039000")
keep if !missing(product_id)
label define product 1 "corn" 2 "sorghum" 3 "cassava" 4 "oats" 5 "barley"
label values product_id product
gen long raw_record_id = _n
gen int year = real(substr(date, 1, 4))
gen byte month = real(substr(date, 6, 2))
gen byte quarter = ceil(month / 3)
gen int quarter_id = yq(year, quarter)
format quarter_id %tq

gen byte invalid_value = missing(value_usd) | value_usd <= 0
gen byte invalid_qty = missing(qty_kg) | qty_kg <= 0
gen byte non_kg_unit = qty_unit != "千克"
gen byte seed_code = inlist(hs8, "10051000", "10071000", "10041000", "10031000")
gen double unit_value = value_usd / qty_kg if !invalid_value & !invalid_qty
gen double ln_unit_value = ln(unit_value) if unit_value > 0

sort product_id
by product_id: egen double lq1 = pctile(ln_unit_value), p(25)
by product_id: egen double lq3 = pctile(ln_unit_value), p(75)
gen double liqr = lq3 - lq1
gen byte price_outlier_mild = ln_unit_value < lq1 - 1.5*liqr | ln_unit_value > lq3 + 1.5*liqr if !missing(ln_unit_value)
gen byte price_outlier_severe = ln_unit_value < lq1 - 3*liqr | ln_unit_value > lq3 + 3*liqr if !missing(ln_unit_value)
by product_id: egen double lp01 = pctile(ln_unit_value), p(1)
by product_id: egen double lp99 = pctile(ln_unit_value), p(99)
gen byte price_outside_p1p99 = ln_unit_value < lp01 | ln_unit_value > lp99 if !missing(ln_unit_value)

save `"`data'/raw_selected_transactions.dta"', replace

preserve
    collapse (count) n_transactions=value_usd (count) n_valid_price=unit_value ///
        (sum) total_value_usd=value_usd total_qty_kg=qty_kg ///
        (mean) mean_value_usd=value_usd mean_qty_kg=qty_kg mean_unit_value=unit_value ///
        (sd) sd_unit_value=unit_value (p1) p01_unit_value=unit_value ///
        (p25) p25_unit_value=unit_value (p50) median_unit_value=unit_value ///
        (p75) p75_unit_value=unit_value (p99) p99_unit_value=unit_value ///
        (sum) n_invalid_value=invalid_value n_invalid_qty=invalid_qty n_non_kg=non_kg_unit ///
              n_mild_price_outlier=price_outlier_mild n_severe_price_outlier=price_outlier_severe, by(product_id)
    decode product_id, gen(product)
    order product product_id
    export delimited using `"`output'/raw_transaction_descriptive_by_product.csv"', replace
restore

preserve
    collapse (count) n_transactions=value_usd (sum) total_value_usd=value_usd ///
        total_qty_kg=qty_kg n_invalid_qty=invalid_qty n_seed_records=seed_code ///
        n_mild_price_outlier=price_outlier_mild n_severe_price_outlier=price_outlier_severe ///
        (p50) median_unit_value=unit_value (p99) p99_unit_value=unit_value, ///
        by(product_id hs8 product_name)
    bysort product_id: egen double product_value_usd = total(total_value_usd)
    gen double product_value_share = total_value_usd / product_value_usd
    decode product_id, gen(product)
    order product product_id hs8 product_name
    export delimited using `"`output'/raw_hs_code_descriptive.csv"', replace
restore

preserve
    keep if invalid_value | invalid_qty | non_kg_unit | seed_code | price_outlier_mild
    decode product_id, gen(product)
    order raw_record_id source_year date province product hs8 product_name partner trade_mode ///
          value_usd qty_kg unit_value seed_code invalid_value invalid_qty non_kg_unit ///
          price_outlier_mild price_outlier_severe price_outside_p1p99
    sort product_id unit_value
    export delimited using `"`output'/raw_transaction_anomalies.csv"', replace
restore

* Aggregate the untouched selected records. Invalid price records remain visible
* in the audit, while only positive values and quantities enter cell totals.
gen double agg_value = cond(value_usd > 0 & !missing(value_usd), value_usd, 0)
gen double agg_qty = cond(qty_kg > 0 & !missing(qty_kg), qty_kg, 0)
gen double seed_value_usd = agg_value * seed_code
collapse (sum) import_value_usd=agg_value import_qty_kg=agg_qty ///
    (count) n_transactions=raw_record_id (sum) n_invalid_value=invalid_value ///
    n_invalid_qty=invalid_qty n_raw_price_outliers=price_outlier_mild ///
    n_seed_records=seed_code seed_value_usd=seed_value_usd, ///
    by(province year quarter quarter_id product_id)
tempfile observed_cells ids grid products
save `observed_cells'

preserve
    keep province year quarter quarter_id
    duplicates drop
    save `ids'
restore
clear
set obs 5
gen byte product_id = _n
label values product_id product
save `products'
use `ids', clear
cross using `products'
merge 1:1 province quarter_id product_id using `observed_cells', assert(master match) nogen
foreach v in import_value_usd import_qty_kg n_transactions n_invalid_value n_invalid_qty n_raw_price_outliers n_seed_records seed_value_usd {
    replace `v' = 0 if missing(`v')
}

bysort province quarter_id: egen double total_expenditure_usd = total(import_value_usd)
keep if total_expenditure_usd > 0
gen double budget_share = import_value_usd / total_expenditure_usd
gen double cell_unit_value = import_value_usd / import_qty_kg if import_value_usd > 0 & import_qty_kg > 0
gen double ln_cell_price_raw = ln(cell_unit_value) if cell_unit_value > 0
gen byte price_imputed = missing(ln_cell_price_raw)
bysort product_id quarter_id: egen double quarter_product_median = median(ln_cell_price_raw)
bysort product_id: egen double product_median = median(ln_cell_price_raw)
gen double ln_price = ln_cell_price_raw
replace ln_price = quarter_product_median if missing(ln_price)
replace ln_price = product_median if missing(ln_price)
assert !missing(ln_price)

bysort product_id: egen double cq1 = pctile(ln_cell_price_raw), p(25)
bysort product_id: egen double cq3 = pctile(ln_cell_price_raw), p(75)
gen double ciqr = cq3 - cq1
gen byte cell_price_outlier_mild = ln_cell_price_raw < cq1 - 1.5*ciqr | ln_cell_price_raw > cq3 + 1.5*ciqr if !missing(ln_cell_price_raw)
gen byte cell_price_outlier_severe = ln_cell_price_raw < cq1 - 3*ciqr | ln_cell_price_raw > cq3 + 3*ciqr if !missing(ln_cell_price_raw)

preserve
    keep if cell_price_outlier_mild == 1 | n_invalid_value > 0 | n_invalid_qty > 0 | ///
        n_raw_price_outliers > 0 | n_seed_records > 0
    decode product_id, gen(product)
    order province year quarter product import_value_usd import_qty_kg cell_unit_value ///
          cell_price_outlier_mild cell_price_outlier_severe n_transactions ///
          n_invalid_value n_invalid_qty n_raw_price_outliers n_seed_records seed_value_usd
    gsort product_id -cell_price_outlier_severe -cell_unit_value
    export delimited using `"`output'/province_quarter_product_anomalies.csv"', replace
restore

preserve
    collapse (count) n_province_quarters=budget_share (sum) n_positive_share=price_imputed ///
        (mean) mean_share=budget_share (sd) sd_share=budget_share ///
        (p1) p01_share=budget_share (p25) p25_share=budget_share ///
        (p50) median_share=budget_share (p75) p75_share=budget_share (p99) p99_share=budget_share ///
        (mean) mean_cell_price=cell_unit_value (p50) median_cell_price=cell_unit_value ///
        (p1) p01_cell_price=cell_unit_value (p99) p99_cell_price=cell_unit_value, by(product_id)
    rename n_positive_share n_price_imputed
    gen n_positive_share = n_province_quarters - n_price_imputed
    gen zero_share_rate = n_price_imputed / n_province_quarters
    decode product_id, gen(product)
    order product product_id
    export delimited using `"`output'/product_cell_descriptive.csv"', replace
restore

preserve
    keep province year quarter quarter_id total_expenditure_usd
    duplicates drop
    gen double ln_total_expenditure = ln(total_expenditure_usd)
    summarize ln_total_expenditure, detail
    scalar exp_q1 = r(p25)
    scalar exp_q3 = r(p75)
    scalar exp_iqr = exp_q3 - exp_q1
    gen byte expenditure_outlier_mild = ln_total_expenditure < exp_q1 - 1.5*exp_iqr | ///
        ln_total_expenditure > exp_q3 + 1.5*exp_iqr
    gen byte expenditure_outlier_severe = ln_total_expenditure < exp_q1 - 3*exp_iqr | ///
        ln_total_expenditure > exp_q3 + 3*exp_iqr
    gsort -expenditure_outlier_severe -total_expenditure_usd
    export delimited using `"`output'/province_quarter_expenditure_diagnostics.csv"', replace
restore

* Reshape to one demand-system observation per province-quarter.
keep province year quarter quarter_id product_id total_expenditure_usd budget_share ///
     import_value_usd import_qty_kg cell_unit_value ln_cell_price_raw ln_price price_imputed ///
     cell_price_outlier_mild cell_price_outlier_severe n_transactions n_invalid_value n_invalid_qty n_raw_price_outliers
reshape wide budget_share import_value_usd import_qty_kg cell_unit_value ln_cell_price_raw ///
    ln_price price_imputed cell_price_outlier_mild cell_price_outlier_severe ///
    n_transactions n_invalid_value n_invalid_qty n_raw_price_outliers, ///
    i(province quarter_id) j(product_id)

rename budget_share1 w_corn
rename budget_share2 w_sorghum
rename budget_share3 w_cassava
rename budget_share4 w_oats
rename budget_share5 w_barley
rename ln_price1 lnp_corn
rename ln_price2 lnp_sorghum
rename ln_price3 lnp_cassava
rename ln_price4 lnp_oats
rename ln_price5 lnp_barley
encode province, gen(province_id)
gen double lnx = ln(total_expenditure_usd)

foreach v in lnx lnp_corn lnp_sorghum lnp_cassava lnp_oats lnp_barley {
    quietly summarize `v', meanonly
    scalar mean_`v' = r(mean)
    gen double c_`v' = `v' - r(mean)
}
egen double share_sum = rowtotal(w_corn w_sorghum w_cassava w_oats w_barley)
assert abs(share_sum - 1) < 1e-10
drop share_sum
xtset province_id quarter_id
compress
save `"`data'/aids_estimation_panel.dta"', replace

tempname mem
tempfile sample_desc
postfile `mem' str28 variable double N mean sd min p1 p25 p50 p75 p99 max using `sample_desc', replace
foreach v in total_expenditure_usd lnx w_corn w_sorghum w_cassava w_oats w_barley ///
             ln_cell_price_raw1 ln_cell_price_raw2 ln_cell_price_raw3 ln_cell_price_raw4 ln_cell_price_raw5 {
    quietly summarize `v', detail
    post `mem' ("`v'") (r(N)) (r(mean)) (r(sd)) (r(min)) (r(p1)) (r(p25)) ///
        (r(p50)) (r(p75)) (r(p99)) (r(max))
}
postclose `mem'
preserve
    use `sample_desc', clear
    export delimited using `"`output'/estimation_sample_descriptive.csv"', replace
restore

describe
summarize total_expenditure_usd w_* lnp_*
log close
