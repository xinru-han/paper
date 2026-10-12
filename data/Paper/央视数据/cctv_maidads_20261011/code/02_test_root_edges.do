version 17
clear all
set more off
do "/root/data/Paper/央视数据/cctv_maidads_20261011/ado/maidads_core.mata"
capture mkdir "/root/data/Paper/央视数据/cctv_maidads_20261011/outputs/estimation/root_edge_test"
mata:
MD_K=2
MD_N=2
MD_MAI=1
MD_SCALE=(1,1)
MD_P=(1,1\1,1)
MD_W=(.3,.7\.6,.4)
MD_WEIGHT=(.5\.5)
MD_H=(1/sqrt(2)\-1/sqrt(2))
MD_LO=(-12,-12,0,0,0,0,.005,-25)
MD_HI=(12,12,12,12,12,12,20,25)
raw=(0,0,0,0,0,0,1.5,2)
par=MD_unpack(raw,1)
terms=MD_terms((0\1e-14),MD_P,par,1.5,2)
MD_M=terms[,1]
MD_OK=1
MD_audit("/root/data/Paper/央视数据/cctv_maidads_20261011/outputs/estimation/root_edge_test",raw,par,1)
end
