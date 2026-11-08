version 17
clear all
set more off
set matsize 800
global ROOT "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
global OLD "/root/data/Paper/央视数据/Paper1-EASI/stata_rebuild_2026-10-10"
log using "$ROOT/logs/05_matched_exact.log",text replace
use "$ROOT/data/exact_support_aids_full.dta",clear
foreach model in quaids easi {
    merge 1:1 hh_id ym using "$ROOT/data/exact_support_`model'_full.dta",assert(match) nogen
}
gen byte matched_support=support_aids & support_quaids & support_easi
drop support_*
foreach model in aids quaids easi {
    merge 1:1 hh_id ym using "$OLD/data/exact_support_`model'_full.dta",assert(match) nogen
    replace matched_support=matched_support & support_`model'
    drop support_`model'
}
keep hh_id ym matched_support
save "$ROOT/data/matched_support.dta",replace
tempname out
postfile `out' str10 grouping str10 model byte good double N double expenditure double marshallian_own double hicksian_own using "$ROOT/outputs/comparison/exact_matched_sample.dta",replace
foreach grouping in nine eight {
    local path "$OLD"
    local ng=9
    if "`grouping'"=="eight" {
        local path "$ROOT"
        local ng=8
    }
    do "`path'/ado/cctv_exact.do"
    use "`path'/data/analysis_monthly.dta",clear
    merge 1:1 hh_id ym using "$ROOT/data/matched_support.dta",assert(match) nogen
    keep if matched_support
    local n=_N
    gen double ex=.
    forvalues j=1/`ng' {
        gen double ep`j'=.
    }
    gen byte xe_positive=0
    foreach model in aids quaids easi {
        estimates use "`path'/outputs/exact/`model'_full.ster"
        local demos `e(demographics)'
        replace ex=lnx-e(xmean)
        forvalues j=1/`ng' {
            replace ep`j'=lp`j'-e(pmean`j')
        }
        matrix XE_b=e(b)
        mata: xe_elasticities("`model'","`demos'")
        assert XE_positive_support==1
        forvalues j=1/`ng' {
            post `out' ("`grouping'") ("`model'") (`j') (`n') (XE_elasticity[`j',1]) (XE_elasticity[`j',2]) (XE_elasticity[`j',3])
        }
    }
}
postclose `out'
use "$ROOT/outputs/comparison/exact_matched_sample.dta",clear
export delimited using "$ROOT/outputs/comparison/exact_matched_sample.csv",replace
list if good==6 | (good==7 & grouping=="nine"),noobs
display "MEAT_MERGE_MATCHED_SUCCESS"
log close
