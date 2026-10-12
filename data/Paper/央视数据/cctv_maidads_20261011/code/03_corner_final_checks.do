version 17
clear all
set more off
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$cmroot/logs/03_corner_final_checks.log", text replace
import delimited "$cmroot/outputs/corner/estimated_free_parameters.csv", clear asdouble
mkmat cm_b*, matrix(cm_check_b)
use "$cmroot/data/corner_smd_support.dta", clear
keep if train
do "$cmroot/ado/corner_maidads.mata"
do "$cmroot/ado/corner_regular.mata"
do "$cmroot/ado/corner_smd.mata"
mata:
void cm_final_checks()
{
    real matrix par,draw,rd,H,report
    real rowvector b,p,pp,pm,alpha,low,high,q0,hp,hm
    real colvector m,type
    real scalar i,r,j,mult,rootbad,budgetbad,qbad,maxroot,maxbudget,minFu,maxFu,maxsym,maxeig,maxhom,h,nfd,maxfast
    b=st_matrix("cm_check_b"); par=cm_unpack(b)
    m=st_data(.,"scaled_m"); type=st_data(.,"type")
    draw=cm_draws(64,8)
    rootbad=budgetbad=qbad=0; maxroot=maxbudget=maxsym=maxhom=maxfast=0
    minFu=.; maxFu=-1e100; maxeig=-1e100; nfd=0; h=1e-5
    for (i=1;i<=rows(m);i++) {
        p=st_data(i,("p1","p2","p3","p4","p5","p6","p7","p8"))
        mult=exp(par[4,4+type[i]])
        low=mult*par[2,]; high=mult*par[3,]
        rd=cm_random_demand(m[i],p,par[1,],par[1,],low,high,.7,0,par[4,2],draw)
        rootbad=rootbad+sum(rowmissing(rd):>0)
        if (hasmissing(rd)) continue
        rootbad=rootbad+sum((abs(rd[,10]):>1e-8):|(rd[,11]:>-1+1e-10))
        maxroot=max((maxroot,max(abs(rd[,10]))))
        minFu=min((minFu,min(rd[,11])))
        maxFu=max((maxFu,max(rd[,11])))
        for (r=1;r<=rows(draw);r++) {
            maxbudget=max((maxbudget,abs(sum(p:*rd[r,1..8])-m[i])/max((1,m[i]))))
            budgetbad=budgetbad+(abs(sum(p:*rd[r,1..8])-m[i])>1e-8*max((1,m[i])))
            qbad=qbad+(min(rd[r,1..8])<(-1e-10))
            alpha=cm_reweight(par[1,],draw[r,],par[4,2])
            q0=cm_regular_q(m[i],p,alpha,low,par[4,1],.7)
            if (hasmissing(q0)) _error(3498)
            maxfast=max((maxfast,max(abs(q0-rd[r,1..8]))))
            if (mod(i-1,120)!=0 | r>16) continue
            H=J(8,8,.)
            for (j=1;j<=8;j++) {
                pp=p; pm=p; pp[j]=p[j]*(1+h); pm[j]=p[j]*(1-h)
                hp=cm_hicks(rd[r,9],pp,alpha,alpha,low,high,.7,0)[|1\8|]
                hm=cm_hicks(rd[r,9],pm,alpha,alpha,low,high,.7,0)[|1\8|]
                if (hasmissing(hp) | hasmissing(hm)) _error(3498)
                H[,j]=(hp-hm)'/(2*h*p[j])
            }
            maxsym=max((maxsym,max(abs(H-H'))))
            maxeig=max((maxeig,max(symeigenvalues((H+H')/2))))
            maxhom=max((maxhom,max(abs(H*p'))))
            nfd++
        }
    }
    report=(rows(m)*rows(draw),rootbad,budgetbad,qbad,maxroot,maxbudget,minFu,maxFu,maxfast,
            nfd,maxsym,maxeig,maxhom,h,rows(draw))
    st_matrix("cm_final_check",report)
    assert(rootbad==0 & budgetbad==0 & qbad==0)
    assert(maxroot<1e-8 & maxbudget<1e-8 & maxsym<1e-6 & maxeig<1e-6)
}
cm_final_checks()
end
matrix colnames cm_final_check = evaluated_demands invalid_roots invalid_budgets negative_quantities max_root_error max_budget_error minimum_Fu maximum_Fu max_fast_generic_difference compensated_fd_cases max_slutsky_symmetry max_slutsky_eigenvalue max_hicks_homogeneity fd_perturbation integration_draws
clear
svmat double cm_final_check, names(col)
export delimited "$cmroot/outputs/corner/fitted_solver_checks.csv", replace
display "CORNER_FITTED_SOLVER_CHECKS_PASSED"
log close
