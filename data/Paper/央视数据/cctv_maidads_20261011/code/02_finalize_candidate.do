version 17
clear all
set more off
args input rawfile output model k
adopath ++ "/root/data/Paper/央视数据/cctv_maidads_20261011/ado"
capture mkdir "`output'"
capture log close _all
log using "`output'/finalize.log", text replace
import delimited using "`rawfile'", clear varnames(1) asdouble
mkmat value lower upper, matrix(checkpoint)
import delimited using "`input'", clear varnames(1) encoding(utf8) asdouble
local prices
local shares
forvalues j=1/`k' {
    local prices `prices' p`j'
    local shares `shares' w`j'
    generate double fitq`j'=.
    generate double fitw`j'=.
    generate double eta`j'=.
}
generate double fitutility=.
do "/root/data/Paper/央视数据/cctv_maidads_20261011/ado/maidads_core.mata"
mata:
MD_load("m",st_local("prices"),st_local("shares"),"")
c=st_matrix("checkpoint")
MD_BEST=c[,1]';MD_LO=c[,2]';MD_HI=c[,3]'
MD_MAI=st_local("model")=="maidads"
MD_eval(MD_BEST,MD_BESTVAL,g)
MD_BESTSCORE=max(abs(MD_score(MD_BEST,g)))
MD_OK=0
par=MD_unpack(MD_BEST,MD_MAI)
out=st_local("output")
L=cols(MD_BEST);covpars=MD_K*(MD_K-1)/2;totalpars=L+covpars
MD_csv(out+"/parameters.csv","good,alpha,beta,delta,tau",((1..MD_K)',par'))
MD_csv(out+"/raw_parameters.csv","index,value,lower,upper",((1..L)',MD_BEST',MD_LO',MD_HI'))
MD_csv(out+"/scale.csv","good,training_quantity_equivalent_scale",((1..MD_K)',MD_SCALE'))
MD_audit(out,MD_BEST,par,MD_MAI)
MD_csv(out+"/model_summary.csv","N,K,mean_nll,nll,structural_parameter_count,covariance_parameter_count,total_parameter_count,AIC,BIC,projected_gradient,converged,omega,kappa",(MD_N,MD_K,MD_BESTVAL,MD_N*MD_BESTVAL,L,covpars,totalpars,2*MD_N*MD_BESTVAL+2*totalpars,2*MD_N*MD_BESTVAL+ln(MD_N)*totalpars,MD_BESTSCORE,0,(MD_MAI ? MD_BEST[L-1] : 0),MD_BEST[L]))
MD_store()
end
export delimited using "`output'/predictions.csv", replace
file open status using "`output'/RUN_STATUS.txt", write text replace
file write status "DIAGNOSTIC ONLY: a completed candidate from an interrupted multi-start run." _n
file write status "Source raw parameters: `rawfile'" _n
file write status "No further optimization; convergence is forced to 0, not promoted by post-processing." _n
file close status
log close
