version 17
clear all
set more off
capture log close _all
args modeldir
global cfroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
if "`modeldir'"=="" local modeldir "$cfroot/outputs/corner_freephi"
global cfout "`modeldir'"
log using "$cfout/elasticity.log", text replace
import delimited "$cfout/estimated_free_parameters.csv", clear asdouble
mkmat b*, matrix(cf_elastic_b)
import delimited "$cfout/fit_status.csv", clear asdouble
scalar cf_elastic_scale=budget_scale[1]
scalar cf_elastic_converged=converged[1]
import delimited "$cfout/regularity_domain.csv", clear asdouble
mkmat maximum_scaled_quantity, matrix(cf_elastic_qmax_col)
use "$cfroot/data/corner_freephi_support.dta", clear
keep if train
do "$cfroot/ado/corner_maidads.mata"
do "$cfroot/ado/corner_freephi.mata"
mata:
real matrix cf_integrate_q(real rowvector b, real scalar m, real rowvector p,
                           real scalar type, real matrix draws, real rowvector qmax)
{
    real matrix pred
    real rowvector w
    pred=cf_predict_vector(b,m,p,type,draws,qmax)
    if (hasmissing(pred)) _error(3498)
    w=(pred[1,1..7],1-sum(pred[1,1..7]))
    return((m*w:/p)\pred[1,8..15])
}

void cf_elasticity()
{
    real matrix par,draws,AA,BB,LO,P,SOL,Hp,Hm,qp,qm,price_out,budget_out,checks,H
    real rowvector b,qmax,p,pp,pm,low,Q,pi,emu,eme,emc,eM,eMe,eMc,eH,eHe,eHc
    real colvector w
    real scalar typ,g,i,j,r,m,mult,delta,den,error,sym,eig,hom
    b=st_matrix("cf_elastic_b"); qmax=st_matrix("cf_elastic_qmax_col")'
    par=cf_unpack(b,qmax); draws=cm_draws(4096,8)
    w=st_data(.,"support_weight")
    p=colsum(w:*st_data(.,("p1","p2","p3","p4","p5","p6","p7","p8")))/sum(w)
    delta=.025; den=ln((1+delta)/(1-delta))
    AA=J(rows(draws),8,.); BB=AA
    for (r=1;r<=rows(draws);r++) {
        AA[r,]=cm_reweight(par[1,],draws[r,],par[5,2])
        BB[r,]=cm_reweight(par[2,],draws[r,],par[5,2])
    }
    price_out=J(0,11,.); budget_out=J(0,11,.); checks=J(0,5,.)
    for (typ=1;typ<=4;typ++) {
        low=exp(par[5,4+typ])*par[3,]
        LO=J(rows(draws),1,1)*low
        for (g=1;g<=5;g++) {
            m=2^(g-3)
            qp=cf_integrate_q(b,m,p,typ,draws,qmax)
            Q=qp[1,]; pi=qp[2,]
            qp=cf_integrate_q(b,m*(1+delta),p,typ,draws,qmax)
            qm=cf_integrate_q(b,m*(1-delta),p,typ,draws,qmax)
            emu=ln(qp[1,]:/qm[1,])/den
            eme=ln(qp[2,]:/qm[2,])/den
            emc=ln((qp[1,]:/qp[2,]):/(qm[1,]:/qm[2,]))/den
            error=max(select(abs(emu-eme-emc),(emu:<.):&(eme:<.):&(emc:<.)))
            if (error<. & error>1e-9) _error(3498)
            for (i=1;i<=8;i++) budget_out=budget_out\(typ,
                m*st_numscalar("cf_elastic_scale"),i,Q[i]*st_numscalar("cf_elastic_scale"),
                pi[i],Q[i]/pi[i]*st_numscalar("cf_elastic_scale"),emu[i],eme[i],emc[i],delta,rows(draws))
            if (g!=3) continue
            P=J(rows(draws),1,1)*p
            SOL=cf_batch_solution(J(rows(draws),1,m),P,AA,BB,LO,par[5,1],.7)
            if (hasmissing(SOL)) _error(3498)
            H=J(8,8,.)
            for (j=1;j<=8;j++) {
                pp=p; pm=p
                pp[j]=p[j]*(1+delta); pm[j]=p[j]*(1-delta)
                qp=cf_integrate_q(b,m,pp,typ,draws,qmax)
                qm=cf_integrate_q(b,m,pm,typ,draws,qmax)
                eM=ln(qp[1,]:/qm[1,])/den
                eMe=ln(qp[2,]:/qm[2,])/den
                eMc=ln((qp[1,]:/qp[2,]):/(qm[1,]:/qm[2,]))/den
                Hp=cf_batch_hicks(SOL[,9],J(rows(draws),1,1)*pp,AA,BB,LO,par[5,1],.7)
                Hm=cf_batch_hicks(SOL[,9],J(rows(draws),1,1)*pm,AA,BB,LO,par[5,1],.7)
                if (hasmissing(Hp) | hasmissing(Hm)) _error(3498)
                if (max(Hp[,1..8]:/(J(rows(draws),1,1)*qmax))>1+1e-10 |
                    max(Hm[,1..8]:/(J(rows(draws),1,1)*qmax))>1+1e-10) _error(3498)
                eH=ln(colsum(Hp[,1..8]):/colsum(Hm[,1..8]))/den
                eHe=ln(colsum(Hp[,1..8]:>0):/colsum(Hm[,1..8]:>0))/den
                eHc=eH-eHe
                H[,j]=((colsum(Hp[,1..8])-colsum(Hm[,1..8]))/rows(draws))'/(2*delta*p[j])
                for (i=1;i<=8;i++) price_out=price_out\(typ,i,j,eM[i],eMe[i],eMc[i],eH[i],eHe[i],eHc[i],delta,rows(draws))
            }
            sym=max(abs(H-H')); eig=max(symeigenvalues((H+H')/2)); hom=max(abs(H*p'))
            checks=checks\(typ,max(abs(SOL[,10])),max(SOL[,11]),sym,eig)
            printf("Freephi family %g: root gap %12.5g, Fu max %12.5g, finite-response symmetry %12.5g, max eigenvalue %12.5g\n",
                typ,max(abs(SOL[,10])),max(SOL[,11]),sym,eig)
        }
    }
    st_matrix("cf_prices",price_out); st_matrix("cf_budgets",budget_out); st_matrix("cf_elastic_checks",checks)
}
cf_elasticity()
end
matrix colnames cf_prices = type good price_good marshall_total marshall_participation marshall_conditional hicks_total hicks_participation hicks_conditional perturbation integration_draws
matrix colnames cf_budgets = type budget_percap_proxy_month good mean_q purchase_prob positive_mean_q budget_total budget_participation budget_conditional perturbation integration_draws
matrix colnames cf_elastic_checks = type maximum_root_gap maximum_Fu finite_response_symmetry maximum_eigenvalue
clear
svmat double cf_prices, names(col)
generate str24 method="finite_domain_freephi"
generate byte estimate_converged=cf_elastic_converged
export delimited "$cfout/price_response_all_4_families.csv", replace
clear
svmat double cf_budgets, names(col)
generate str24 method="finite_domain_freephi"
generate byte estimate_converged=cf_elastic_converged
export delimited "$cfout/budget_response_curve_all_4_families.csv", replace
clear
svmat double cf_elastic_checks, names(col)
export delimited "$cfout/elasticity_numerical_checks.csv", replace
display "FREEPHI_ELASTICITIES_FINISHED"
log close
