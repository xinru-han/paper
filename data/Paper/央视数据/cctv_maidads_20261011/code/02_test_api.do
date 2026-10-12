version 17
clear all
set more off
set obs 24
set seed 1102026
adopath ++ "/root/data/Paper/央视数据/cctv_maidads_20261011/ado"
generate double m=exp(runiform()*2+3)
generate double p1=exp(rnormal(0,.1))
generate double p2=exp(rnormal(0,.1))
generate double w1=.2+.04*ln(m)+rnormal(0,.02)
generate double w2=1-w1
maidadsfit, expenditure(m) prices(p1 p2) shares(w1 w2) model(aidads) outdir("/root/data/Paper/央视数据/cctv_maidads_20261011/outputs/estimation/api_test") starts(1) iterate(1)
ereturn list
assert e(sample)==1
assert "`e(vce)'"=="none_point_only"
matrix V=e(V)
assert rowsof(V)==0 | colsof(V)==0
assert colsof(e(b))==5
