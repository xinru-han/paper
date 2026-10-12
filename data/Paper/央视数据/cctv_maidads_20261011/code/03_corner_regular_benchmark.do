version 17
clear all
set more off
capture log close _all
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
log using "$cmroot/logs/03_corner_regular_benchmark.log", text replace
do "$cmroot/ado/corner_maidads.mata"
do "$cmroot/ado/corner_regular.mata"
timer clear
timer on 1
mata:
alpha=(.25,.08,.2,.12,.13,.07,.09,.06)
low=(.2,.05,.15,.1,.1,.07,.08,.05)
draw=cm_draws(32,8)
maxerr=0
for (i=1;i<=1000;i++) {
    for (j=1;j<=32;j++) {
        a=cm_reweight(alpha,draw[j,],.8)
        q=cm_regular_q(exp(-2+4*mod(i,51)/50),J(1,8,1),a,low,.15,.7)
        if (i<=10) {
            q0=cm_demand(exp(-2+4*mod(i,51)/50),J(1,8,1),a,a,low,.15*low,.7,0)
            maxerr=max((maxerr,max(abs(q-q0[|1\8|]))))
        }
    }
}
maxerr
assert(maxerr<1e-9)
end
timer off 1
timer list
log close
