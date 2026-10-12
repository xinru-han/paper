version 17
clear all
set more off
args input output model k starts maxiter filter
adopath ++ "/root/data/Paper/央视数据/cctv_maidads_20261011/ado"
capture mkdir "`output'"
capture log close _all
log using "`output'/estimate.log", text replace
import delimited using "`input'", clear varnames(1) encoding(utf8) asdouble
if "`filter'"!="" keep if `filter'
local prices
local shares
forvalues j=1/`k' {
    local prices `prices' p`j'
    local shares `shares' w`j'
}
file open version using "`output'/KERNEL_VERSION.txt", write text replace
file write version "maidads_tangent_core.mata: near-active low-endpoint-cost tangent search" _n
file write version "Original native objective, physical box score and qualification gate retained." _n
file write version "Separate experimental numerical-search variant; not a relaxation of stationarity." _n
file close version
maidadstangentfit, expenditure(m) prices(`prices') shares(`shares') model(`model') outdir("`output'") starts(`starts') iterate(`maxiter')
ereturn list
log close
