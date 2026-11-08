version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/00_config.do"
log using "$ROOT/logs/09_paper_inference.log",text replace
use "$ROOT/data/fitted_main.dta",clear
estimates use "$ROOT/outputs/models/main.ster"
do "$ROOT/ado/cctv_fit.ado"
do "$ROOT/ado/cctv_report.do"
do "$ROOT/ado/cctv_restore.do"
cctv_restore
forvalues i=1/8 {
    global CV_Z`i' "`e(syvars`i')'"
}
mata: mata matuse "$ROOT/outputs/models/main_influence.mmat",replace
mata:
CV.Gp=CV_ARCH_P; CV.Gh=CV_ARCH_H
CV.fs[1].X=CV_ARCH_FP1; CV.fs[1].R=CV_ARCH_FH1
CV.fs[2].X=CV_ARCH_FP2; CV.fs[2].R=CV_ARCH_FH2
CV.fs[3].X=CV_ARCH_FP3; CV.fs[3].R=CV_ARCH_FH3
CV.fs[4].X=CV_ARCH_FP4; CV.fs[4].R=CV_ARCH_FH4
CV.fs[5].X=CV_ARCH_FP5; CV.fs[5].R=CV_ARCH_FH5
CV.fs[6].X=CV_ARCH_FP6; CV.fs[6].R=CV_ARCH_FH6
CV.fs[7].X=CV_ARCH_FP7; CV.fs[7].R=CV_ARCH_FH7
cv_infer(st_global("ROOT")+"/outputs","paper_main",999)
end
* The analytic main derivative/Jacobian code matches the already-audited eight-group code.
do "$ROOT/ado/cctv_audit.do"
mata:
void paper_regular()
{
    struct cv_pred scalar R,P
    real matrix S
    real colvector keep,v
    real scalar f,i,j,N,fd
    string rowvector margins
    fd=cv_open(st_global("ROOT")+"/outputs/paper/main_regularity.csv")
    fput(fd,"margin,N,support_rate,mean_slutsky_asymmetry,max_eigenvalue")
    margins=("unconditional","intensive","latent")
    for(f=1;f<=3;f++) {
        R=cv_pred_all(margins[f],0); keep=rowmin(R.W):>1e-8; N=sum(keep); S=J(8,8,0)
        for(j=1;j<=8;j++) {
            P=cv_pred_all(margins[f],j)
            for(i=1;i<=8;i++) {
                v=P.dp[,i]+(R.W[,i]+R.dx[,i]):*R.W[,j]-(i==j)*R.W[,i]
                S[i,j]=quadcross(keep,v)/N
            }
        }
        fput(fd,margins[f]+","+invtokens(strofreal((N,N/rows(keep),max(abs(S-S')),max(symeigenvalues((S+S')/2))),"%20.12g"),","))
    }
    fclose(fd)
}
paper_regular()
end
* Check all exported inference matches point estimates in the previous trial.
import delimited using "$ROOT/outputs/inference/elasticity_inference_paper_main.csv",clear varnames(1)
assert _N==32
isid sample good type
assert !missing(estimate,se_province_two_step,ci_lower,ci_upper)
assert b==999 & clusters==24
display "EIGHT_PAPER_INFERENCE_SUCCESS"
log close
