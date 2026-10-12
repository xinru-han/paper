version 17
clear all
set more off
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_fix_metadata_label.log", text replace
import delimited using "$run/outputs/data_audit/category_province_year_spending.csv", clear varnames(1) encoding("utf-8") asdouble
capture confirm variable rows_duplicate
if !_rc rename rows_duplicate duplicate_multiplicity_sum
export delimited using "$run/outputs/data_audit/category_province_year_spending.csv", replace
log close
