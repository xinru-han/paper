version 17
clear all
set more off
args input output model k starts maxiter filter warmdir
if "`filter'"=="" local filter 1
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
local warmoption
if "`warmdir'"!="" local warmoption warmdir("`warmdir'")
file open version using "`output'/KERNEL_VERSION.txt", write text replace
file write version "maidads_simplex_core.mata: natural nonnegative alpha/beta, exact simplex boundaries" _n
file write version "Same native model and orthogonal-share QML; all delta/tau endpoints remain free." _n
file write version "Qualification requires full-K projected natural KKT plus face/one-sided derivative and root audits." _n
file write version "Warm source: `warmdir'" _n
file close version
maidadssimplexfit, expenditure(m) prices(`prices') shares(`shares') model(`model') outdir("`output'") starts(`starts') iterate(`maxiter') `warmoption'
ereturn list
log close
