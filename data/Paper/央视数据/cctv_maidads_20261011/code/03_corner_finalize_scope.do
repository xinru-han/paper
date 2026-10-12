version 17
clear all
set more off
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$ROOT/logs/03_corner_finalize_scope.log",text replace
foreach aggregation in province family {
    use "$ROOT/outputs/corner_scenarios/`aggregation'_income_growth_32.dta",clear
    capture drop participation_scope
    gen str120 participation_scope="Quarter-kernel conditional probability at annual monthly-equivalent budget; not annual purchase incidence"
    recast str120 result_status
    replace result_status="Restricted corner pilot diagnostic; full-household prediction, not full-sample fit"
    save "$ROOT/outputs/corner_scenarios/`aggregation'_income_growth_32.dta",replace
    export delimited using "$ROOT/outputs/corner_scenarios/`aggregation'_income_growth_32.csv",replace nolabel
}
log close
