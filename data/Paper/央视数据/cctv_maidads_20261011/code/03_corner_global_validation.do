version 17
clear all
set more off
capture log close _all
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
log using "$cmroot/logs/03_corner_global_validation.log", text replace
do "$cmroot/ado/corner_maidads.mata"
mata:
void cm_allsets()
{
    real rowvector alpha,low,high,q,a,p,x,pp,pm,h,active
    real scalar mask,j,k,u,l,r,F,om,kap,m,step,gap,identity,sym,curv,fu
    real matrix out,H
    k=8; om=.7; kap=0; step=1e-5
    alpha=(.22,.08,.2,.12,.14,.08,.1,.06)
    low=(.3,.1,.25,.16,.2,.1,.12,.08)
    high=.2*low
    out=J(255,8,.)
    for (mask=1;mask<=255;mask++) {
        active=J(1,k,0)
        for (j=1;j<=k;j++) active[j]=mod(floor(mask/2^(j-1)),2)
        q=active:*(.3:+.04*(1..k))
        l=-30; r=30
        for (j=1;j<=80;j++) {
            u=(l+r)/2
            F=cm_F(q,u,alpha,alpha,low,high,om,kap)
            if (F>0) l=u
            else r=u
        }
        u=(l+r)/2
        a=cm_shift(u,low,high,om)
        p=alpha:/(q+a)
        for (j=1;j<=k;j++) if (!active[j]) p[j]=1.4*alpha[j]/a[j]
        m=sum(p:*q)
        x=cm_demand(m,p,alpha,alpha,low,high,om,kap)
        identity=max(abs(q-x[|1\k|]))
        H=J(k,k,.)
        for (j=1;j<=k;j++) {
            pp=p; pm=p; pp[j]=pp[j]+step; pm[j]=pm[j]-step
            H[,j]=(cm_hicks(u,pp,alpha,alpha,low,high,om,kap)[|1\k|]-
                    cm_hicks(u,pm,alpha,alpha,low,high,om,kap)[|1\k|])'/(2*step)
        }
        sym=max(abs(H-H'))
        curv=max(symeigenvalues((H+H')/2))
        h=cm_hicks(u,p,alpha,alpha,low,high,om,kap)
        fu=cm_Fu(q,u,alpha,alpha,low,high,om)
        out[mask,]=(mask,sum(active),identity,abs(x[k+2]),fu,
                     abs(sum(p:*x[|1\k|])-m),sym,curv)
        if (any((x[|1\k|]:>1e-8):!=active)) _error(3498)
    }
    st_matrix("cm_global",out)
    if (max(out[,3])>1e-8 | max(out[,4])>1e-8 | max(out[,5])>=-1 |
        max(out[,6])>1e-8 | max(out[,7])>1e-5 | max(out[,8])>1e-5) _error(3498)
    printf("PASS: every nonempty eight-good consumption set (255) is reproduced by endogenous KKT.\n")
    printf("Global F_u<−1 follows analytically from alpha=beta and shift_high<shift_low.\n")
}
cm_allsets()
end
matrix colnames cm_global = active_mask active_goods quantity_error root_error Fu budget_error symmetry_error largest_slutsky_eigen
clear
svmat double cm_global, names(col)
export delimited "$cmroot/outputs/corner/restricted_8_all_255_sets_validation.csv", replace
summarize quantity_error root_error Fu budget_error symmetry_error largest_slutsky_eigen
assert quantity_error<1e-8 & root_error<1e-8 & Fu<(-1)
assert budget_error<1e-8 & symmetry_error<1e-5 & largest_slutsky_eigen<1e-5
display "CORNER_GLOBAL_8_ALLSETS_PASS"
log close
