version 17
clear all
set more off
capture log close _all
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
log using "$cmroot/logs/03_corner_compile.log", text replace
do "$cmroot/ado/corner_maidads.mata"
do "$cmroot/ado/corner_smd.mata"
mata:
b=(J(1,7,0),J(1,8,-2),-1.4,ln(.8),0,0,0)
m=(.2\.5\1\2)
p=J(4,8,1)
type=(1\2\3\4)
d=cm_draws(16,8)
pred=cm_predict(b,m,p,type,d)
Z=J(4,3,1)
v=.; g=.; H=.
cm_smd_objective(0,b,m,p,type,Z,pred,J(4,1,1),d,v,g,H)
assert(v==0)
pred
cm_unpack(b)
end
display "PASS: corner SMD functions compile and evaluate."
log close
