version 17
clear all
set more off
capture log close _all
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
log using "$cmroot/logs/03_corner_optimizer_test.log", text replace
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
S=optimize_init()
optimize_init_evaluator(S,&cm_smd_objective())
optimize_init_evaluatortype(S,"d0")
optimize_init_which(S,"min")
optimize_init_technique(S,"nm")
optimize_init_nmsimplexdeltas(S,J(1,20,.18))
optimize_init_params(S,b)
optimize_init_argument(S,1,m)
optimize_init_argument(S,2,p)
optimize_init_argument(S,3,type)
optimize_init_argument(S,4,Z)
optimize_init_argument(S,5,pred)
optimize_init_argument(S,6,J(4,1,1))
optimize_init_argument(S,7,d)
optimize_init_conv_maxiter(S,2)
btest=optimize(S)
optimize_result_value(S)
optimize_result_converged(S)
end
display "PASS: corner simulated-moment optimizer API tested."
log close
