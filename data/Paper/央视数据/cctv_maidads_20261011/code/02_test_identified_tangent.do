version 17
clear all
set more off
set seed 20261012
set obs 480
adopath ++ "/root/data/Paper/央视数据/cctv_maidads_20261011/ado"
generate double utility_true=runiform()*8-4
generate double m=.
forvalues j=1/3 {
    generate double p`j'=exp(rnormal(0,.3))
    generate double w`j'=.
}
do "/root/data/Paper/央视数据/cctv_maidads_20261011/ado/maidads_core.mata"
mata:
MD_K=3
MD_SCALE=(1,1,1)
p=st_data(.,("p1","p2","p3"))
utrue=st_data(.,"utility_true")
par=(.4,.3,.3\.2,.3,.5\10,20,15\30,25,40)
terms=MD_terms(utrue,p,par,.8,1)
st_store(.,"m",terms[,1])
raw=(ln(.4/.3),ln(.3/.3),ln(.2/.5),ln(.3/.5),10,20,15,30,25,40,.8,1)
qq=ww=ee=mm=hh=J(0,0,.)
uu=J(0,1,.)
MD_predict(raw,1,p,terms[,1],qq,ww,uu,ee,mm,hh)
noise=rnormal(rows(ww),3,0,.001)
noise=noise:-rowsum(noise):/3
ww=ww+noise
st_store(.,("w1","w2","w3"),ww)
end
maidadstangentfit, expenditure(m) prices(p1 p2 p3) shares(w1 w2 w3) model(maidads) outdir("/root/data/Paper/央视数据/cctv_maidads_20261011/outputs/estimation/synthetic_identified_tangent") starts(3) iterate(400)
ereturn list
