version 17
clear all
set more off
set obs 180
set seed 1102026
adopath ++ "/root/data/Paper/央视数据/cctv_maidads_20261011/ado"
generate double m=exp(runiform()*3+3)
forvalues j=1/3 {
    generate double p`j'=exp(rnormal(0,.1))
    generate double w`j'=.
}
do "/root/data/Paper/央视数据/cctv_maidads_20261011/ado/maidads_core.mata"
mata:
MD_K=3
MD_SCALE=(1,1,1)
MD_P=st_data(.,("p1","p2","p3"))
MD_M=st_data(.,"m")
raw=(ln(.4/.3),ln(.3/.3),ln(.2/.4),ln(.4/.4),1,2,1,3,1,4,.5,3)
qq=ww=ee=mm=hh=J(0,0,.)
uu=J(0,1,.)
MD_predict(raw,1,MD_P,MD_M,qq,ww,uu,ee,mm,hh)
noise=rnormal(rows(ww),3,0,.01)
noise=noise:-rowsum(noise):/3
ww=ww+noise
st_store(.,("w1","w2","w3"),ww)
end
capture mkdir "/root/data/Paper/央视数据/cctv_maidads_20261011/outputs/estimation"
maidadsfit, expenditure(m) prices(p1 p2 p3) shares(w1 w2 w3) model(maidads) outdir("/root/data/Paper/央视数据/cctv_maidads_20261011/outputs/estimation/synthetic_test") starts(1) iterate(300)
ereturn list
