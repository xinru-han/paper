version 17
clear all
set more off
set seed 20261012
local base "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture mkdir "`base'/outputs/tests/simplex_edges"
capture mkdir "`base'/outputs/tests/simplex_edges/warm"
capture log close _all
log using "`base'/outputs/tests/simplex_edges/test.log", text replace
set obs 480
generate double utility_true=runiform()*8-4
generate double m=.
forvalues j=1/3 {
    generate double p`j'=exp(rnormal(0,.3))
    generate double w`j'=.
}
do "`base'/ado/maidads_simplex_core.mata"
mata:
MD_K=3
MD_SCALE=(1,1,1)
MD_MAI=1
MD_LO=(0,0,0,0,0,0,0,0,0,0,.005,-25)
MD_HI=(1,1,1,1,12,12,12,12,12,12,20,25)
par=(.6,.4,0\.25,0,.75\.2,.3,.1\.35,.25,.2)
raw=(.6,.4,.25,0,.2,.3,.1,.35,.25,.2,1.7,.4)
p=st_data(.,("p1","p2","p3"))
utrue=st_data(.,"utility_true")
terms=MD_terms(utrue,p,par,1.7,.4)
st_store(.,"m",terms[,1])
qq=ww=ee=mm=hh=J(0,0,.)
uu=J(0,1,.)
MD_predict(raw,1,p,terms[,1],qq,ww,uu,ee,mm,hh)
root_gap=max(abs(uu-utrue))
noise=rnormal(rows(ww),3,0,.0005)
noise=noise:-rowsum(noise):/3
ww=ww+noise
st_store(.,("w1","w2","w3"),ww)
MD_load("m","p1 p2 p3","w1 w2 w3","")
raw[5..7]=par[3,]:/MD_SCALE
raw[8..10]=par[4,]:/MD_SCALE
f=fp=fm=fbad=.
g=gp=gm=gbad=J(1,12,.)
MD_eval(raw,f,g)
T=MS_facebasis(raw)
fdgap=0
fdrows=J(cols(T),4,.)
for(j=1;j<=cols(T);j++) {
    direction=T[,j]'
    h=MS_probe_step(raw,direction,1e-8)
    MD_eval(raw+h*direction,fp,gp)
    MD_eval(raw-h*direction,fm,gm)
    if(h<=0 | fp>=1e9 | fm>=1e9) _error(3498)
    fdgap=max((fdgap,abs((fp-fm)/(2*h)-sum(g:*direction))))
    fdrows[j,]=(j,h,(fp-fm)/(2*h),sum(g:*direction))
}
MD_csv(st_local("base")+"/outputs/tests/simplex_edges/face_probe_checks.csv","direction,step,numeric_derivative,analytic_derivative",fdrows)
onesided=0
directions=(-1,0,0,0,J(1,8,0)\0,0,-1,1,J(1,8,0))
for(j=1;j<=rows(directions);j++) {
    h=1e-7
    direction=directions[j,]
    MD_eval(raw+h*direction,fp,gp)
    MD_eval(raw+2*h*direction,fm,gm)
    onesided=max((onesided,abs((-3*f+4*fp-fm)/(2*h)-sum(g:*direction))))
}
a=MD_natural(raw[1..2]);b=MD_natural(raw[3..4])
fulla=a-MS_project_simplex(a-(g[1..2],0))
fullb=b-MS_project_simplex(b-(g[3..4],0))
pg=MD_score(raw,g)
kktgap=max(abs((pg[1..2],-sum(pg[1..2]),pg[3..4],-sum(pg[3..4]))-(fulla,fullb)))
boxraw=raw;boxraw[5]=1e-9
boxg=g;boxg[5]=2
if(abs(MD_score(boxraw,boxg)[5]-1e-9)>1e-14) _error(3498)
endpoint_terms=MD_terms((-50\50),J(2,3,1),par,1.7,.4)
high_omega_terms=MD_terms((-50\50),J(2,3,1),par,20,.4)
phi_neg50=(1/(1+exp(-50)))*par[1,]+(1/(1+exp(50)))*par[2,]
phi_pos50=(1/(1+exp(50)))*par[1,]+(1/(1+exp(-50)))*par[2,]
positive_small=min((phi_neg50,phi_pos50))
projectiongap=max((abs(sum(MS_project_simplex((-.2,.4,.9)))-1),-min(MS_project_simplex((-.2,.4,.9)))))
if(MS_project_simplex((.25,0,.75))[2]!=0) _error(3498)
MD_csv(st_local("base")+"/outputs/tests/simplex_edges/numeric_checks.csv","root_utility_gap,face_gradient_gap,inward_gradient_gap,full_K_KKT_projection_gap,min_supported_endpoint_phi,projection_simplex_gap",(root_gap,fdgap,onesided,kktgap,positive_small,projectiongap))
if(hasmissing(endpoint_terms) | hasmissing(high_omega_terms) | positive_small<=0 | root_gap>1e-8 | fdgap>1e-3 | onesided>1e-3 | kktgap>1e-12 | projectiongap>1e-12) _error(3498)
badpar=par
badpar[1,3]=badpar[2,3]=0
MD_eval((.6,.4,.25,.75,raw[5..12]),fbad,gbad)
if(fbad<1e9) _error(3498)
MD_csv(st_local("base")+"/outputs/tests/simplex_edges/warm/parameters.csv","good,alpha,beta,delta,tau",((1..3)',par'))
MD_csv(st_local("base")+"/outputs/tests/simplex_edges/warm/model_summary.csv","omega,kappa",(1.7,.4))
end
capture mata: MD_terms((0),J(1,3,1),badpar,1.7,.4)
assert _rc==3498
display "DIRECT SIMPLEX EDGE TESTS PASSED"
export delimited using "`base'/outputs/tests/simplex_edges/synthetic_data.csv", replace
log close
