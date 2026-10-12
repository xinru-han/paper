version 17
clear all
set more off
args input output model k starts maxiter filter
if "`model'"=="" local model maidads
if "`k'"=="" local k 8
if "`starts'"=="" local starts 3
if "`maxiter'"=="" local maxiter 400
adopath ++ "/root/data/Paper/央视数据/cctv_maidads_20261011/ado"
capture mkdir "`output'"
log using "`output'/estimate.log", text replace
import delimited using "`input'", clear varnames(1) encoding(utf8) asdouble
if "`filter'"!="" keep if `filter'
local prices
local shares
forvalues j=1/`k' {
    local prices `prices' p`j'
    local shares `shares' w`j'
}
maidadsfit, expenditure(m) prices(`prices') shares(`shares') model(`model') outdir("`output'") starts(`starts') iterate(`maxiter')
ereturn list
log close
