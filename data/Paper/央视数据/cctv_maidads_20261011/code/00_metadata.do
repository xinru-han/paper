version 17
clear all
set more off
capture log close _all
log using "/root/data/Paper/央视数据/cctv_maidads_20261011/logs/00_metadata.log", text replace
use "/root/data/Paper/央视数据/Paper1-EASI/stata_rebuild_2026-10-10/data/transaction_inputs.dta", clear
describe
count
list hh_id family_type family_size family_income category spend volume in 1/4
clear
import excel using "/root/data/数据/央视数据/补充样本城市级别--20260610.xlsx", sheet("样本城市级别") firstrow clear
describe
list in 1/4
log close
