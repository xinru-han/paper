version 17
clear all
set more off
args project adodir
if `"`project'"' == "" local project "/root/data/Paper/饲料进口弹性/stata_replication_2026"
if `"`adodir'"' == "" local adodir `"`project'/ado"'
adopath ++ `"`adodir'"'
use `"`project'/data/feed_import_estimation.dta"', clear
capture program drop attach_estimation_sample
program define attach_estimation_sample, eclass
    ereturn repost, esample(estimation_sample)
end
foreach spec in aids quaids easi1 easi2 easi3 {
    capture confirm file `"`project'/output/estimate_nlsur_cf_no_sy_`spec'.ster"'
    if !_rc {
        estimates use `"`project'/output/estimate_nlsur_cf_no_sy_`spec'.ster"'
        capture drop estimation_sample
        gen byte estimation_sample = 1
        attach_estimation_sample
        global REFOUT `"`project'/output/reference_nlsur_cf_no_sy_`spec'.csv"'
        do `"`project'/code/03_reference_elasticities.do"'
    }
}
