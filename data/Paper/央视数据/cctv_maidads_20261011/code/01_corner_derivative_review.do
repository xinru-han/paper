version 17
clear all
set more off
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_corner_derivative_review.log",text replace
import delimited using "$run/outputs/corner/estimated_free_parameters.csv",clear asdouble
mkmat cm_b*,matrix(DA_corner_b)
import delimited using "$run/outputs/corner/fit_status.csv",clear asdouble
scalar DA_corner_scale=budget_scale[1]
do "$run/ado/corner_maidads.mata"
do "$run/ado/corner_regular.mata"
do "$run/ado/corner_smd.mata"
do "$run/ado/corner_forecast.mata"
mata:
void DA_corner_derivatives()
{
    real matrix par,draw,alphas
    real rowvector p,a,low,x,q,qp,qm,fd,analytic,out
    real scalar scale,t,r,j,k,m,h,eta,checked,incomechecked,skip,incomeskip
    real scalar bmax,imax,qmax,dmax,zmax,regulargap,validcases
    par=cm_unpack(st_matrix("DA_corner_b"))
    scale=st_numscalar("DA_corner_scale")
    if(scale<=0 | scale>=.) _error(3498)
    k=cols(par);draw=cm_draws(32,k);alphas=J(rows(draw),k,.)
    for(r=1;r<=rows(draw);r++) alphas[r,]=cm_reweight(par[1,],draw[r,],par[4,2])
    p=(.75,1.3,1.7,.85,1.2,1.6,.9,1.05)
    if(k!=cols(p)) _error(3498)
    h=1e-6
    checked=incomechecked=skip=incomeskip=validcases=0
    bmax=imax=qmax=dmax=zmax=regulargap=0
    for(t=1;t<=4;t++) {
        low=exp(par[4,4+t])*par[2,]
        eta=(t==1 ? .4 : (t==2 ? 0 : (t==3 ? -.2 : 1.1)))
        for(r=1;r<=rows(draw);r++) {
            a=alphas[r,]
            for(j=1;j<=32;j++) {
                m=scale*exp(-4+j*.25)
                x=cs_response(m/scale,p,a,low,par[4,1],.7)
                if(hasmissing(x)) _error(3498)
                validcases++
                q=x[|1\k|]*scale
                analytic=x[|k+1\2*k|]
                qmax=max((qmax,abs(sum(p:*q)-m)/m))
                dmax=max((dmax,abs(sum(p:*analytic)-1)))
                if(any(q:==0)) zmax=max((zmax,max(abs(select(analytic,q:==0)))))
                regulargap=max((regulargap,max(abs(q/scale-cm_regular_q(m/scale,p,a,low,par[4,1],.7)))))
                qp=scale*cm_regular_q(m*(1+h)/scale,p,a,low,par[4,1],.7)
                qm=scale*cm_regular_q(m*(1-h)/scale,p,a,low,par[4,1],.7)
                if(hasmissing((qp,qm))) _error(3498)
                if(all((qp:>0):==(q:>0)) & all((qm:>0):==(q:>0))) {
                    fd=(qp-qm)/(2*h*m)
                    bmax=max((bmax,max(abs(fd-analytic))/max((1,max(abs(analytic))))))
                    checked++
                }
                else skip++
                qp=scale*cm_regular_q(m*exp(eta*h)/scale,p,a,low,par[4,1],.7)
                qm=scale*cm_regular_q(m*exp(-eta*h)/scale,p,a,low,par[4,1],.7)
                if(hasmissing((qp,qm))) _error(3498)
                if(all((qp:>0):==(q:>0)) & all((qm:>0):==(q:>0))) {
                    fd=(qp-qm)/(2*h)
                    imax=max((imax,max(abs(fd-analytic*m*eta))/max((1,max(abs(analytic*m*eta))))))
                    incomechecked++
                }
                else incomeskip++
            }
        }
    }
    if(bmax>1e-6 | imax>1e-6 | qmax>1e-8 | dmax>1e-8 | zmax>1e-12 | regulargap>1e-10) _error(3498)
    out=(validcases,checked,incomechecked,skip,incomeskip,bmax,imax,qmax,dmax,zmax,regulargap)
    st_matrix("DA_corner_validation",out)
}
DA_corner_derivatives()
end
matrix colnames DA_corner_validation=cases budget_fd_checked income_fd_checked budget_boundary_cases income_boundary_cases budget_derivative_relative_gap income_chain_relative_gap budget_closure_gap derivative_budget_closure_gap inactive_derivative_gap existing_solver_gap
clear
svmat double DA_corner_validation,names(col)
export delimited using "$run/outputs/data_audit/corner_derivative_review.csv",replace
list,noobs
log close
