version 17
clear all
set more off
capture set processors 2
set matsize 800
args mode
global rebuild "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
cap mkdir "$rebuild/outputs/exact"
local tag "full"
if "`mode'"=="pilot" local tag "pilot"
cap log close _all
log using "$rebuild/logs/04_exact_models_`tag'.log", text replace
do "$rebuild/ado/cctv_exact.do"
capture program drop xe_post
program define xe_post,eclass
    syntax, MODEL(string) DEMOS(string asis)
    tempvar touse
    quietly gen byte `touse'=1
    ereturn post XE_b XE_V, esample(`touse')
    ereturn local cmd "cctv_exact"
    ereturn local model "`model'"
    ereturn local demographics "`demos'"
    ereturn local estimator "one-step GMM; fixed inverse instrument second moment"
    ereturn local instruments "constant, normalized relative prices, controls, centered lnx, centered lnx squared"
    ereturn local selection "none"
    ereturn scalar xmean=XE_xmean
    forvalues j=1/8 {
        ereturn scalar pmean`j'=XE_pmean`j'
    }
    ereturn scalar N=XE_N
    ereturn scalar converged=XE_conv
    ereturn scalar iterations=XE_iters
    ereturn scalar criterion=XE_obj
end
if "`mode'"=="pilot" use "$rebuild/data/pilot.dta", clear
else use "$rebuild/data/analysis_monthly.dta", clear

local demos low_income elderly_household large_family z_cpi z_covid z_holiday z_temp z_precip z_wholesale
forvalues mm=2/12 {
    local ms : display %02.0f `mm'
    cap confirm variable m_`ms'
    if _rc gen byte m_`ms'=month==`mm'
    local demos `demos' m_`ms'
}
foreach yy in 2021 2022 {
    cap confirm variable yr_`yy'
    if _rc gen byte yr_`yy'=year==`yy'
    local demos `demos' yr_`yy'
}
quietly summarize lnx, meanonly
scalar XE_xmean=r(mean)
gen double ex=lnx-XE_xmean
gen double ex2=ex^2
forvalues j=1/8 {
    quietly summarize lp`j',meanonly
    scalar XE_pmean`j'=r(mean)
    gen double ep`j'=lp`j'-XE_pmean`j'
}
gen double uobs=ex
forvalues j=1/8 {
    replace uobs=uobs-w`j'*ep`j'
}
tempfile micro
save `micro',replace
tempname fits parms elast reg shares cross rep
postfile `fits' str10 model double N double cells double n_parameters double moment_jacobian_rank double converged double iterations double criterion double analytic_gradient_check double compressed_moment_check double provinces double runtime_seconds double support_rate double root_failures using "$rebuild/outputs/exact/model_fit_`tag'.dta",replace
postfile `parms' str10 model str32 parameter double estimate double se_province double z double p_value using "$rebuild/outputs/exact/coefficients_`tag'.dta",replace
postfile `elast' str10 model byte good double expenditure double marshallian_own double hicksian_own double mean_fitted_share using "$rebuild/outputs/exact/elasticities_`tag'.dta",replace
postfile `reg' str10 model double common_positive_support double slutsky_asymmetry double slutsky_max_eigenvalue using "$rebuild/outputs/exact/regularity_`tag'.dta",replace
postfile `shares' str10 model byte good double negative_share_rate double missing_share_rate double observed_mean_share double raw_predicted_mean_share using "$rebuild/outputs/exact/prediction_audit_`tag'.dta",replace
postfile `cross' str10 model byte demand_good byte price_good double marshallian double hicksian double mean_slutsky using "$rebuild/outputs/exact/cross_price_`tag'.dta",replace
postfile `rep' str10 model byte good double expenditure double marshallian_own double hicksian_own double mean_fitted_share using "$rebuild/outputs/exact/representative_`tag'.dta",replace

foreach model in aids quaids easi {
    use `micro',clear
    gen double nn=1
    gen double x1=ex
    gen double x2=ex^2
    gen double x3=ex^3
    gen double x4=ex^4
    gen double u1=ex
    if "`model'"=="easi" replace u1=uobs
    gen double u2=u1^2
    gen double u3=u1^3
    gen double u4=u1^4
    gen double u1x=u1*ex
    gen double u1x2=u1*ex^2
    gen double u2x=u2*ex
    gen double u2x2=u2*ex^2
    local sums nn x1 x2 x3 x4 u1 u2 u3 u4 u1x u1x2 u2x u2x2
    forvalues j=1/7 {
        gen double w0`j'=w`j'
        gen double w1`j'=w`j'*ex
        gen double w2`j'=w`j'*ex^2
        gen double wt1`j'=w`j'*u1
        gen double wt2`j'=w`j'*u2
        local sums `sums' w0`j' w1`j' w2`j' wt1`j' wt2`j'
    }
    local controls `demos'
    local indicators low_income elderly_household large_family
    local controls : list controls - indicators
    collapse (sum) `sums' (firstnm) ep1 ep2 ep3 ep4 ep5 ep6 ep7 ep8 `controls',by(province ym low_income elderly_household large_family)
    timer clear 1
    timer on 1
    mata: xe_fit("`model'","`demos'")
    assert XE_conv==1
    assert XE_rank==colsof(XE_b)
    assert XE_graderr<1e-6
    timer off 1
    quietly timer list 1
    local runtime=r(t1)
    local nd : word count `demos'
    local names ""
    forvalues j=1/7 {
        local names `names' a`j'
        local d=0
        foreach c of local demos {
            local ++d
            local names `names' t`j'_`d'
        }
    }
    forvalues j=1/7 {
        local names `names' b`j'
    }
    if "`model'"!="aids" {
        forvalues j=1/7 {
            local names `names' l`j'
        }
    }
    forvalues j=1/7 {
        forvalues k=`j'/7 {
            local names `names' g`j'_`k'
        }
    }
    matrix colnames XE_b=`names'
    matrix colnames XE_V=`names'
    matrix rownames XE_V=`names'
    local k=0
    foreach pn of local names {
        local ++k
        local est=XE_b[1,`k']
        local se=sqrt(max(0,XE_V[`k',`k']))
        local zz=`est'/`se'
        local pp=2*ttail(XE_clusters-1,abs(`zz'))
        post `parms' ("`model'") ("`pn'") (`est') (`se') (`zz') (`pp')
    }
    use `micro',clear
    gen byte xe_positive=0
    mata: xe_check_moments("`model'","`demos'")
    assert XE_compressionerr<1e-8
    mata: xe_elasticities("`model'","`demos'")
    forvalues j=1/8 {
        post `elast' ("`model'") (`j') (XE_elasticity[`j',1]) (XE_elasticity[`j',2]) (XE_elasticity[`j',3]) (XE_elasticity[`j',4])
        post `shares' ("`model'") (`j') (XE_share_audit[`j',1]) (XE_share_audit[`j',2]) (XE_share_audit[`j',3]) (XE_share_audit[`j',4])
        post `rep' ("`model'") (`j') (XE_rep_elasticity[`j',1]) (XE_rep_elasticity[`j',2]) (XE_rep_elasticity[`j',3]) (XE_rep_elasticity[`j',4])
        forvalues pp=1/8 {
            post `cross' ("`model'") (`j') (`pp') (XE_mar[`j',`pp']) (XE_hick[`j',`pp']) (XE_slutsky[`j',`pp'])
        }
    }
    post `fits' ("`model'") (XE_N) (XE_cells) (colsof(XE_b)) (XE_rank) (XE_conv) (XE_iters) (XE_obj) (XE_graderr) (XE_compressionerr) (XE_clusters) (`runtime') (XE_positive_support) (XE_rootfail)
    post `reg' ("`model'") (XE_reg[1,1]) (XE_reg[1,2]) (XE_reg[1,3])
    xe_post, model("`model'") demos("`demos'")
    estimates save "$rebuild/outputs/exact/`model'_`tag'.ster", replace
    preserve
    keep hh_id ym xe_positive
    rename xe_positive support_`model'
    save "$rebuild/data/exact_support_`model'_`tag'.dta",replace
    restore
}
postclose `fits'
postclose `parms'
postclose `elast'
postclose `reg'
postclose `shares'
postclose `cross'
postclose `rep'
foreach f in model_fit coefficients elasticities regularity prediction_audit cross_price representative {
    use "$rebuild/outputs/exact/`f'_`tag'.dta",clear
    export delimited using "$rebuild/outputs/exact/`f'_`tag'.csv",replace
}

* Recompute all three systems on the same intersection of raw positive supports.
use `micro',clear
gen byte xe_positive=0
foreach model in aids quaids easi {
    merge 1:1 hh_id ym using "$rebuild/data/exact_support_`model'_`tag'.dta",assert(match) nogen
}
gen byte common_support=support_aids & support_quaids & support_easi
quietly summarize common_support,meanonly
scalar XE_common_support=r(mean)
quietly count if common_support
scalar XE_common_N=r(N)
tempname cel cxp creg
postfile `cel' str10 model byte good double expenditure double marshallian_own double hicksian_own double mean_fitted_share double common_support_rate double N using "$rebuild/outputs/exact/elasticities_common_`tag'.dta",replace
postfile `cxp' str10 model byte demand_good byte price_good double marshallian double hicksian double mean_slutsky using "$rebuild/outputs/exact/cross_price_common_`tag'.dta",replace
postfile `creg' str10 model double slutsky_asymmetry double slutsky_max_eigenvalue using "$rebuild/outputs/exact/regularity_common_`tag'.dta",replace
keep if common_support
foreach model in aids quaids easi {
    estimates use "$rebuild/outputs/exact/`model'_`tag'.ster"
    matrix XE_b=e(b)
    mata: xe_elasticities("`model'","`demos'")
    forvalues j=1/8 {
        post `cel' ("`model'") (`j') (XE_elasticity[`j',1]) (XE_elasticity[`j',2]) (XE_elasticity[`j',3]) (XE_elasticity[`j',4]) (XE_common_support) (XE_common_N)
        forvalues pp=1/8 {
            post `cxp' ("`model'") (`j') (`pp') (XE_mar[`j',`pp']) (XE_hick[`j',`pp']) (XE_slutsky[`j',`pp'])
        }
    }
    post `creg' ("`model'") (XE_reg[1,2]) (XE_reg[1,3])
}
postclose `cel'
postclose `cxp'
postclose `creg'
foreach f in elasticities_common cross_price_common regularity_common {
    use "$rebuild/outputs/exact/`f'_`tag'.dta",clear
    export delimited using "$rebuild/outputs/exact/`f'_`tag'.csv",replace
}
display "MEAT_MERGE_EXACT_SUCCESS"
log close
