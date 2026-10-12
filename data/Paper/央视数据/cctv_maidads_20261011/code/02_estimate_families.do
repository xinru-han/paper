version 17
clear all
set more off
local run "/root/data/Paper/央视数据/cctv_maidads_20261011"
forvalues family=1/4 {
    do "`run'/code/02_estimate.do" "`run'/data/cells_quarter_8.csv" "`run'/outputs/estimation/maidads_family_`family'" maidads 8 2 400 "type==`family'"
}
