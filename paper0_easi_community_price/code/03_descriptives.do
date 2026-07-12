version 17
do "$EASI_CODE/00_config.do"
use "$EASI_DATA/easi_analysis_ready.dta", clear

tempname mem
tempfile stats
postfile `mem' str32 variable long n double mean sd p50 min max using `stats', replace
foreach v of varlist q1-q6 p1-p6 s1-s6 food_exp hhsize {
    quietly summarize `v', detail
    post `mem' ("`v'") (r(N)) (r(mean)) (r(sd)) (r(p50)) (r(min)) (r(max))
}
postclose `mem'
use `stats', clear
export delimited using "$EASI_OUT/table_descriptives.csv", replace

use "$EASI_DATA/easi_analysis_ready.dta", clear
tempname zmem
tempfile zeros
postfile `zmem' str24 group long n_consuming double share_consuming using `zeros', replace
forvalues g = 1/6 {
    quietly summarize q`g' > 0
    post `zmem' ("group_`g'") (r(sum)) (r(mean))
}
postclose `zmem'
use `zeros', clear
export delimited using "$EASI_OUT/table_zero_consumption.csv", replace

use "$EASI_DATA/easi_analysis_ready.dta", clear
preserve
    keep p1_source-p6_source
    forvalues g = 1/6 {
        rename p`g'_source source`g'
    }
    gen long household_n = _n
    reshape long source, i(household_n) j(group)
    contract group source
    rename source price_source
    rename _freq households
    export delimited using "$EASI_OUT/table_price_sources.csv", replace
restore

count
file open fh using "$EASI_OUT/sample_flow.txt", write replace
file write fh "Analysis observations after exact village-year price merge: " %12.0fc r(N) _n
file close fh
