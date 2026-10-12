version 17
clear all
set more off
capture log close _all
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
log using "$cmroot/logs/03_corner_benchmark.log", text replace
do "$cmroot/ado/corner_maidads.mata"
timer clear
timer on 1
mata:
alpha=(.25,.08,.2,.12,.13,.07,.09,.06)
beta=(.20,.07,.19,.14,.14,.09,.1,.07)
low=(.2,.05,.15,.1,.1,.07,.08,.05)
high=.15*low
draw=cm_draws(32,8)
for (i=1;i<=1000;i++) {
    out=cm_random_demand(exp(-2+4*mod(i,51)/50),J(1,8,1),
        alpha,beta,low,high,.7,0,.8,draw)
}
end
timer off 1
timer list
log close
