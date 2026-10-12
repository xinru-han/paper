version 17
clear all
set more off
set seed 10011
set obs 1200
global ROOT "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "$ROOT/outputs/tests"
capture mkdir "$ROOT/outputs/tests/aids"
gen double m=200*exp(rnormal(0,.5))
forvalues j=1/8 {
    gen double p`j'=exp(rnormal(0,.12))
    gen double w`j'=1/8
    gen double q`j'=m*w`j'/p`j'
}
replace w1=w1+.02*ln(m/200)-.01*ln(p1/p8)
replace w8=w8-.02*ln(m/200)+.01*ln(p1/p8)
forvalues j=1/7 {
    gen double ee`j'=rnormal(0,.007)
    replace w`j'=w`j'+ee`j'
    replace w8=w8-ee`j'
}
forvalues j=1/8 {
    replace q`j'=m*w`j'/p`j'
}
export delimited using "$ROOT/outputs/tests/comparator_synthetic.csv",replace
do "$ROOT/code/04_comparators.do" "$ROOT/outputs/tests/comparator_synthetic.csv" "$ROOT/outputs/tests/aids" aids 8 1
