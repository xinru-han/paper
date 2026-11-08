version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/welfare_revision_2026-10-13/code/00_config.do"
log using "$REV/logs/02_welfare_scenarios.log",text replace
do "$REV/ado/cctv_exact.do"
do "$REV/ado/easi_welfare.do"
estimates use "$REV/outputs/exact/easi_curvature_full.ster"
assert e(converged)==1
matrix XE_b=e(b)
use "$REV/data/curvature_micro.dta",clear
gen byte wf_baseok=0
gen double wf_u0=.
forvalues j=1/8 {
    gen double wf_q0`j'=.
    gen double wd`j'=0
    gen double wf_qm`j'=.
    gen double wf_qh`j'=.
}
gen double wf_cv=.
gen double wf_ev=.
gen double wf_fitted_basket=.
gen double wf_observed_basket=.
gen byte wf_ok=0
mata: rw_load("$DEMOS")
assert WF_base_cost_error<1e-8
local scenarios no_change
foreach family in all_food oil meat dairy staple_oil fruit_veg {
    foreach dose in 5 10 20 {
        local scenarios `scenarios' `family'_`dose'
    }
}
local scenarios `scenarios' oil_minus10 fruit_veg_minus10 all10_staple_oil_protected
local K: word count `scenarios'
assert `K'==22
capture program drop set_welfare_shock
program define set_welfare_shock
    args scenario
    forvalues j=1/8 {
        replace wd`j'=0
    }
    if "`scenario'"=="no_change" exit
    if "`scenario'"=="all10_staple_oil_protected" {
        forvalues j=3/8 {
            replace wd`j'=ln(1.1)
        }
        exit
    }
    local dose=real(substr("`scenario'",strrpos("`scenario'","_")+1,.))
    if strpos("`scenario'","minus10") local dose=-10
    local change=ln(1+`dose'/100)
    if substr("`scenario'",1,8)=="all_food" {
        forvalues j=1/8 {
            replace wd`j'=`change'
        }
    }
    if substr("`scenario'",1,4)=="oil_" replace wd2=`change'
    if substr("`scenario'",1,5)=="meat_" {
        replace wd5=`change'
        replace wd6=`change'
    }
    if substr("`scenario'",1,6)=="dairy_" replace wd8=`change'
    if substr("`scenario'",1,10)=="staple_oil" {
        replace wd1=`change'
        replace wd2=`change'
    }
    if substr("`scenario'",1,9)=="fruit_veg" {
        replace wd3=`change'
        replace wd4=`change'
    }
end
* First pass establishes every scenario's support without clipping any shares.
tempname audit definitions
postfile `audit' str32 scenario double baseline_N supported_N support_rate double cost_CV_error cost_EV_error path_maxeig path_asymmetry laspeyres_violations using "$REV/outputs/audit/welfare_scenario_audit.dta",replace
postfile `definitions' str32 scenario double price1 price2 price3 price4 price5 price6 price7 price8 using "$REV/outputs/welfare/scenario_definitions.dta",replace
foreach scenario of local scenarios {
    quietly set_welfare_shock `scenario'
    mata: rw_scenario()
    gen byte ok_`scenario'=wf_ok
    quietly count if wf_ok
    local ns=r(N)
    assert WF_cv_cost_error<1e-8 & WF_ev_root_error<1e-8 & WF_path_maxeig<1e-8 & WF_path_asymmetry<1e-10 & WF_laspeyres_violations==0
    post `audit' ("`scenario'") (WF_baseline_support) (`ns') (`ns'/583668) (WF_cv_cost_error) (WF_ev_root_error) (WF_path_maxeig) (WF_path_asymmetry) (WF_laspeyres_violations)
    post `definitions' ("`scenario'") (100*(exp(wd1[1])-1)) (100*(exp(wd2[1])-1)) (100*(exp(wd3[1])-1)) (100*(exp(wd4[1])-1)) (100*(exp(wd5[1])-1)) (100*(exp(wd6[1])-1)) (100*(exp(wd7[1])-1)) (100*(exp(wd8[1])-1))
    if "`scenario'"=="no_change" assert abs(wf_cv)<1e-10 & abs(wf_ev)<1e-10 if wf_ok
    foreach dose in 5 10 20 {
        if "`scenario'"=="all_food_`dose'" {
            assert abs(wf_cv-`dose'/100)<1e-10 if wf_ok
            assert abs(wf_ev-`dose'/(100+`dose'))<1e-9 if wf_ok
        }
    }
}
postclose `audit'
postclose `definitions'
egen byte wf_common=rowmin(ok_*)
quietly count if wf_common
scalar WF_COMMON_N=r(N)
assert WF_COMMON_N>0
save "$REV/data/welfare_support_micro.dta",replace
* Second pass reports comparable scenarios on a single common evaluation sample,
* plus the scenario-specific sample as a transparent sensitivity comparison.
tempname summary quantities provinceout
postfile `summary' str32 scenario str20 support str12 subgroup double N support_rate mean_CV_pct mean_EV_pct mean_CV_yuan_pc median_CV_pct p10_CV_pct p90_CV_pct observed_basket_pct fitted_basket_pct substitution_saving_pct using "$REV/outputs/welfare/welfare_summary.dta",replace
postfile `quantities' str32 scenario str20 support byte good double N marshallian_change_pct hicksian_change_pct using "$REV/outputs/welfare/quantity_response.dta",replace
postfile `provinceout' str32 scenario int province str40 province_name double N mean_CV_pct mean_CV_yuan_pc using "$REV/outputs/welfare/province_welfare.dta",replace
levelsof province,local(provinces)
foreach scenario of local scenarios {
    quietly set_welfare_shock `scenario'
    mata: rw_scenario()
    gen double cv_pct=100*wf_cv
    gen double ev_pct=100*wf_ev
    gen double cv_yuan=wf_cv*total_food_spend_pc_month
    gen double ob_pct=100*wf_observed_basket
    gen double fb_pct=100*wf_fitted_basket
    gen double saving_pct=fb_pct-cv_pct
    foreach support in common_all scenario_specific {
        local cond "wf_common==1"
        if "`support'"=="scenario_specific" local cond "wf_ok==1"
        foreach subgroup in all inc1 inc2 inc3 inc4 inc5 {
            local inccond "1"
            if "`subgroup'"!="all" local inccond="income_group_order=="+substr("`subgroup'",4,.)
            quietly count if `inccond'
            local nd=r(N)
            quietly summarize cv_pct if `cond' & `inccond',detail
            local ns=r(N)
            local mc=r(mean)
            local med=r(p50)
            local p10=r(p10)
            local p90=r(p90)
            quietly summarize ev_pct if `cond' & `inccond',meanonly
            local me=r(mean)
            quietly summarize cv_yuan if `cond' & `inccond',meanonly
            local my=r(mean)
            quietly summarize ob_pct if `cond' & `inccond',meanonly
            local ob=r(mean)
            quietly summarize fb_pct if `cond' & `inccond',meanonly
            local fb=r(mean)
            quietly summarize saving_pct if `cond' & `inccond',meanonly
            post `summary' ("`scenario'") ("`support'") ("`subgroup'") (`ns') (`ns'/`nd') (`mc') (`me') (`my') (`med') (`p10') (`p90') (`ob') (`fb') (r(mean))
        }
        forvalues j=1/8 {
            gen double dm=wf_q0`j'*wf_qm`j'
            gen double dh=wf_q0`j'*wf_qh`j'
            quietly summarize wf_q0`j' if `cond',meanonly
            local sum0=r(sum)
            local ns=r(N)
            quietly summarize dm if `cond',meanonly
            local pm=100*r(sum)/`sum0'
            quietly summarize dh if `cond',meanonly
            post `quantities' ("`scenario'") ("`support'") (`j') (`ns') (`pm') (100*r(sum)/`sum0')
            drop dm dh
        }
    }
    foreach province of local provinces {
        quietly levelsof province_name if province==`province',local(pname) clean
        quietly summarize cv_pct if wf_common & province==`province',meanonly
        local ns=r(N)
        local mc=r(mean)
        quietly summarize cv_yuan if wf_common & province==`province',meanonly
        post `provinceout' ("`scenario'") (`province') ("`pname'") (`ns') (`mc') (r(mean))
    }
    drop cv_pct ev_pct cv_yuan ob_pct fb_pct saving_pct
}
postclose `summary'
postclose `quantities'
postclose `provinceout'
foreach file in welfare_summary quantity_response province_welfare scenario_definitions {
    use "$REV/outputs/welfare/`file'.dta",clear
    export delimited using "$REV/outputs/welfare/`file'.csv",replace
}
use "$REV/outputs/audit/welfare_scenario_audit.dta",clear
export delimited using "$REV/outputs/audit/welfare_scenario_audit.csv",replace
use "$REV/outputs/welfare/welfare_summary.dta",clear
isid scenario support subgroup
assert _N==264
assert N==WF_COMMON_N if support=="common_all" & subgroup=="all"
assert substitution_saving_pct>=-1e-8
list scenario N support_rate mean_CV_pct mean_EV_pct mean_CV_yuan_pc observed_basket_pct fitted_basket_pct if support=="common_all" & subgroup=="all",noobs
file open done using "$REV/outputs/audit/welfare_success.txt",write replace
file write done "EIGHT_GROUP_WELFARE_SCENARIOS_SUCCESS" _n
file close done
display "EIGHT_GROUP_WELFARE_SCENARIOS_SUCCESS"
log close
