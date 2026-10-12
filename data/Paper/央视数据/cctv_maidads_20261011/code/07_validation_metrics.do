version 17
clear all
set more off
set type double
args train prediction out model fold trainfilter k
if "`k'"=="" local k 8
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "`out'"
capture log close _all
log using "`out'/metrics.log",text replace
import delimited using "`train'",clear asdouble varnames(1) encoding("utf-8")
if "`trainfilter'"!="" keep if `trainfilter'
forvalues j=1/`k' {
    quietly summarize w`j' [aw=nobs]
    scalar VW`j'=r(mean)
    quietly summarize q`j' [aw=nobs]
    scalar VSD`j'=r(sd)
    assert scalar(VSD`j')>0 & scalar(VSD`j')<.
}
tempfile history
preserve
local histvars
forvalues j=1/`k' {
    local histvars `histvars' w`j'
}
collapse (mean) `histvars' [aw=nobs],by(province quarter)
forvalues j=1/`k' {
    rename w`j' historical_w`j'
}
save `history'
restore
import delimited using "`prediction'",clear asdouble varnames(1) encoding("utf-8")
capture confirm variable estimate_qualified
if _rc gen byte estimate_qualified=estimate_stationary
merge m:1 province quarter using `history',keep(master match)
gen byte historical_available=_merge==3
drop _merge
gen long cell_id=_n
gen double all_share_sse=0
gen double all_share_ae=0
gen double all_quantity_sse=0
gen double all_benchmark_share_sse=0
gen double all_history_share_sse=0
forvalues j=1/`k' {
    gen double share_se`j'=(fitw`j'-w`j')^2
    gen double share_ae`j'=abs(fitw`j'-w`j')
    gen double standardized_quantity_se`j'=((fitq`j'-q`j')/scalar(VSD`j'))^2
    gen double benchmark_share_se`j'=(scalar(VW`j')-w`j')^2
    replace historical_w`j'=scalar(VW`j') if missing(historical_w`j')
    gen double historical_share_se`j'=(historical_w`j'-w`j')^2
    replace all_share_sse=all_share_sse+share_se`j'
    replace all_share_ae=all_share_ae+share_ae`j'
    replace all_quantity_sse=all_quantity_sse+standardized_quantity_se`j'
    replace all_benchmark_share_sse=all_benchmark_share_sse+benchmark_share_se`j'
    replace all_history_share_sse=all_history_share_sse+historical_share_se`j'
}
gen double cell_share_rmse=sqrt(all_share_sse/`k')
gen double invalid_nobs=nobs*(prediction_valid!=1)
quietly summarize invalid_nobs,meanonly
scalar VINVALID=r(sum)
quietly summarize nobs,meanonly
scalar VTOTAL=r(sum)
count
scalar VCELLS=r(N)
egen double __miss=rowmiss(all_share_sse all_quantity_sse)
quietly count if __miss>0
scalar VMISSING=r(N)
quietly summarize all_share_sse,meanonly
scalar VCELLRMSE=sqrt(r(mean)/`k')
save "`out'/cell_errors.dta",replace
preserve
local vars all_share_sse all_share_ae all_quantity_sse all_benchmark_share_sse all_history_share_sse historical_available
forvalues j=1/`k' {
    local vars `vars' share_se`j' share_ae`j' standardized_quantity_se`j' benchmark_share_se`j'
}
collapse (mean) `vars' (min) estimate_stationary estimate_qualified [aw=nobs]
gen str12 model="`model'"
gen str20 fold="`fold'"
gen long target_cells=scalar(VCELLS)
gen double target_household_quarters=scalar(VTOTAL)
gen double invalid_household_quarters=scalar(VINVALID)
gen long missing_prediction_cells=scalar(VMISSING)
gen byte complete_coverage=invalid_household_quarters==0 & missing_prediction_cells==0
gen byte eligible_complete_fit=complete_coverage & estimate_stationary & estimate_qualified
gen double cell_equal_weight_rmse=scalar(VCELLRMSE)
gen double share_rmse=sqrt(all_share_sse/`k')
gen double share_mae=all_share_ae/`k'
gen double standardized_quantity_rmse=sqrt(all_quantity_sse/`k')
gen double training_mean_share_rmse=sqrt(all_benchmark_share_sse/`k')
gen double province_history_share_rmse=sqrt(all_history_share_sse/`k')
gen double rmse_ratio=share_rmse/training_mean_share_rmse
* A partial-case loss is not an eligible complete-fold validation score.
foreach v in share_rmse share_mae standardized_quantity_rmse rmse_ratio {
    gen double c_`v'=`v' if eligible_complete_fit
}
export delimited using "`out'/metrics.csv",replace
restore
log close
