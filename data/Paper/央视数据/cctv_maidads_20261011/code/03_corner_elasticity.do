version 17
clear all
set more off
capture log close _all
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
log using "$cmroot/logs/03_corner_elasticity.log", text replace
import delimited "$cmroot/outputs/corner/estimated_free_parameters.csv", clear asdouble
mkmat cm_b*, matrix(cm_elastic_b)
import delimited "$cmroot/outputs/corner/fit_status.csv", clear asdouble
scalar cm_elastic_scale=budget_scale[1]
use "$cmroot/data/corner_smd_support.dta", clear
keep if train
do "$cmroot/ado/corner_maidads.mata"
do "$cmroot/ado/corner_regular.mata"
do "$cmroot/ado/corner_smd.mata"
mata:
real matrix cm_integrate_q(real rowvector b, real scalar m, real rowvector p,
                            real scalar type, real matrix draws)
{
    real matrix par,rd
    real scalar mult
    par=cm_unpack(b)
    mult=exp(par[4,4+type])
    rd=cm_random_demand(m,p,par[1,],par[1,],mult*par[2,],mult*par[3,],
                       .7,0,par[4,2],draws)
    if (hasmissing(rd)) _error(3498)
    return(mean(rd[,1..8])\mean(rd[,1..8]:>0))
}

void cm_elasticity()
{
    real matrix price_out,budget_out,base_out,par,draws,rd,qp,qm,H,Hq,Hp,Hm
    real rowvector b,p,pp,pm,alpha,low,high,Q,pi,emu,emext,emcond,mu
    real rowvector epsh,epsm,epsext,epscond,ehi,ehe,ehc
    real scalar typ,g,j,i,r,m,mult,sigma,delta,den,sym,eig,hom,error
    real colvector weight
    b=st_matrix("cm_elastic_b")
    par=cm_unpack(b)
    weight=st_data(.,"support_weight")
    p=mean(weight:*st_data(.,("p1","p2","p3","p4","p5","p6","p7","p8")))/mean(weight)
    draws=cm_draws(16384,8)
    delta=.025
    den=ln((1+delta)/(1-delta))
    price_out=J(0,11,.)
    budget_out=J(0,11,.)
    base_out=J(0,6,.)
    for (typ=1;typ<=4;typ++) {
        mult=exp(par[4,4+typ]); low=mult*par[2,]; high=mult*par[3,]
        sigma=par[4,2]
        for (g=1;g<=5;g++) {
            m=2^(g-3)
            rd=cm_random_demand(m,p,par[1,],par[1,],low,high,.7,0,sigma,draws)
            if (hasmissing(rd)) _error(3498)
            Q=mean(rd[,1..8]); pi=mean(rd[,1..8]:>0)
            qp=cm_integrate_q(b,m*(1+delta),p,typ,draws)
            qm=cm_integrate_q(b,m*(1-delta),p,typ,draws)
            emu=ln(qp[1,]:/qm[1,])/den
            emext=ln(qp[2,]:/qm[2,])/den
            emcond=ln((qp[1,]:/qp[2,]):/(qm[1,]:/qm[2,]))/den
            error=max(select(abs(emu-emext-emcond),(emu:<.):&(emext:<.):&(emcond:<.)))
            if (error<. & error>1e-9) _error(3498)
            for (i=1;i<=8;i++) {
                budget_out=budget_out\(typ,m*st_numscalar("cm_elastic_scale"),i,
                    Q[i]*st_numscalar("cm_elastic_scale"),pi[i],
                    Q[i]/pi[i]*st_numscalar("cm_elastic_scale"),
                    emu[i],emext[i],emcond[i],delta,rows(draws))
            }
            if (g!=3) continue
            for (i=1;i<=8;i++) base_out=base_out\(typ,i,p[i],
                Q[i]*st_numscalar("cm_elastic_scale"),pi[i],m)
            H=J(8,8,.)
            for (j=1;j<=8;j++) {
                pp=p; pm=p; pp[j]=p[j]*(1+delta); pm[j]=p[j]*(1-delta)
                qp=cm_integrate_q(b,m,pp,typ,draws)
                qm=cm_integrate_q(b,m,pm,typ,draws)
                epsm=ln(qp[1,]:/qm[1,])/den
                epsext=ln(qp[2,]:/qm[2,])/den
                epscond=ln((qp[1,]:/qp[2,]):/(qm[1,]:/qm[2,]))/den
                Hp=J(rows(draws),8,.)
                Hm=J(rows(draws),8,.)
                for (r=1;r<=rows(draws);r++) {
                    alpha=cm_reweight(par[1,],draws[r,],sigma)
                    Hp[r,]=cm_hicks(rd[r,9],pp,alpha,alpha,low,high,.7,0)[|1\8|]
                    Hm[r,]=cm_hicks(rd[r,9],pm,alpha,alpha,low,high,.7,0)[|1\8|]
                }
                if (hasmissing(Hp) | hasmissing(Hm)) _error(3498)
                epsh=ln(mean(Hp):/mean(Hm))/den
                ehe=ln(mean(Hp:>0):/mean(Hm:>0))/den
                ehc=ln((mean(Hp):/mean(Hp:>0)):/(mean(Hm):/mean(Hm:>0)))/den
                H[,j]=(mean(Hp)-mean(Hm))'/(2*delta*p[j])
                for (i=1;i<=8;i++) {
                    price_out=price_out\(typ,i,j,epsm[i],epsext[i],epscond[i],
                        epsh[i],ehe[i],ehc[i],delta,rows(draws))
                }
                if (epsh[j]<. & epsh[j]>1e-10) _error(3498)
            }
            sym=max(abs(H-H'))
            eig=max(symeigenvalues((H+H')/2))
            hom=max(abs(H*p'))
            printf("Family type %g integrated compensated derivative symmetry %12.5g, max eigen %12.5g, homogeneity %12.5g\n",typ,sym,eig,hom)
        }
    }
    st_matrix("cm_price_elastic",price_out)
    st_matrix("cm_budget_elastic",budget_out)
    st_matrix("cm_base",base_out)
    printf("Actual fitted corner pilot: price responses are matched latent-draw compensation, not SY plug-in.\n")
    printf("Finite +/-2.5 percent response interval and 16384 fixed integration draws; no p values.\n")
}
cm_elasticity()
end
matrix colnames cm_price_elastic = type good price_good marshall_total marshall_participation marshall_conditional hicks_total hicks_participation hicks_conditional perturbation integration_draws
matrix colnames cm_budget_elastic = type budget_percap_month good mean_q purchase_prob positive_mean_q budget_total budget_participation budget_conditional perturbation integration_draws
matrix colnames cm_base = type good price_index quantity_equivalent purchase_prob scaled_budget
clear
svmat double cm_price_elastic, names(col)
generate str20 method="restricted_corner"
export delimited "$cmroot/outputs/corner/price_response_all_4_families.csv", replace
clear
svmat double cm_budget_elastic, names(col)
generate str20 method="restricted_corner"
export delimited "$cmroot/outputs/corner/budget_response_curve_all_4_families.csv", replace
clear
svmat double cm_base, names(col)
export delimited "$cmroot/outputs/corner/median_budget_purchase_probabilities.csv", replace
display "CORNER_ELASTICITIES_FINISHED"
log close
