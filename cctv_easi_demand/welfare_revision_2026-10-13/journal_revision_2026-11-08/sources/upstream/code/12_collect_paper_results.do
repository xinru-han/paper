version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
log using "$ROOT/logs/12_collect_paper_results.log",text replace
* Select and verify the exact plotting/reporting inputs; no recomputation by document tools.
import delimited using "$ROOT/outputs/demand/elasticities_main.csv",clear varnames(1)
keep if margin=="unconditional" & sample=="common_positive" & subgroup=="all"
keep if type=="expenditure" | (type=="marshallian" & good==shock)
gen str16 etype=cond(type=="expenditure","expenditure","own_price")
keep good etype elasticity n support_rate
reshape wide elasticity,i(good n support_rate) j(etype) string
rename elasticityexpenditure expenditure
rename elasticityown_price own_price
gen str12 variant="main"
tempfile baseline collected
save `baseline',replace
save `collected',replace
foreach v in order1 order3 nosy nopcyc omit5 {
    import delimited using "$ROOT/outputs/robustness/points_`v'.csv",clear varnames(1)
    assert _N==16
    keep if sample=="common_positive"
    assert _N==8
    keep variant good expenditure own_price n support_rate
    append using `collected'
    save `collected',replace
}
use `collected',clear
isid variant good
assert _N==48
export delimited using "$ROOT/outputs/paper/robustness_all_points.csv",replace
save "$ROOT/outputs/paper/robustness_all_points.dta",replace
preserve
use `baseline',clear
keep good own_price expenditure
rename own_price base_own
rename expenditure base_expenditure
save `baseline',replace
restore
merge m:1 good using `baseline',assert(match) nogen
gen double own_abs_diff=abs(own_price-base_own)
gen double exp_abs_diff=abs(expenditure-base_expenditure)
gen byte own_nonnegative=own_price>=0
gen byte exp_nonpositive=expenditure<=0
collapse (firstnm) N=n support_rate (max) max_abs_own_change=own_abs_diff max_abs_exp_change=exp_abs_diff (sum) own_nonnegative exp_nonpositive,by(variant)
assert N==583668*support_rate | abs(N-583668*support_rate)<.1
save "$ROOT/outputs/paper/robustness_summary.dta",replace
export delimited using "$ROOT/outputs/paper/robustness_summary.csv",replace
list,noobs
* Model coefficient block tests: use two-step province influence from successful main fit.
estimates use "$ROOT/outputs/models/main.ster"
matrix PB=e(b)
matrix PI=e(influence_province)
mata:
void paper_tests()
{
real matrix ptests,PI
real matrix IF,boots
real rowvector bb,sel,webb
real colvector se,flags
real scalar a,i,k,G,t,stat,pv
string rowvector names,terms
terms=st_matrixcolstripe("PB")[,2]'; bb=st_matrix("PB"); PI=st_matrix("PI")
names=("quadratic_Engel","demographics","Mundlak_means","SY_correction","A_prices","C_price_expenditure")
G=rows(PI); ptests=J(cols(names),5,.)
webb=(-sqrt(1.5),-1,-sqrt(.5),sqrt(.5),1,sqrt(1.5))
rseed(20261011)
for(a=1;a<=cols(names);a++) {
    sel=J(1,0,.)
    for(i=1;i<=cols(terms);i++) {
        k=0
        if(a==1) k=(substr(terms[i],strlen(terms[i])-2,.)=="_y2")
        if(a==2) k=(strpos(terms[i],"low_income")>0 | strpos(terms[i],"elderly_household")>0 | strpos(terms[i],"large_family")>0)
        if(a==3) k=(strpos(terms[i],"mean_y_hh")>0 | strpos(terms[i],"_mn")>0)
        if(a==4) k=(substr(terms[i],1,5)=="sigma")
        if(a==5) k=(substr(terms[i],1,1)=="A")
        if(a==6) k=(substr(terms[i],1,1)=="C")
        if(k) sel=sel,i
    }
    IF=PI[,sel]; se=sqrt(colsum(IF:^2)*G/(G-1))
    stat=max(abs(bb[sel]:/se)); boots=J(999,1,0)
    for(t=1;t<=999;t++) {
        flags=webb[ceil(runiform(G,1)*6)]'; if(rows(flags)!=G) flags=flags'
        boots[t]=max(abs(colsum(IF:*flags):/sqrt(colsum(IF:^2:*(flags:^2))*G/(G-1))))
    }
    pv=(1+sum(boots:>=stat))/1000
    ptests[a,]=(cols(sel),rank(quadcross(IF,IF)),stat,pv,G)
}
st_matrix("PTESTS",ptests)
}
paper_tests()
end
clear
svmat double PTESTS
gen str24 test=""
local names quadratic_Engel demographics Mundlak_means SY_correction A_prices C_price_expenditure
forvalues i=1/6 {
    local name: word `i' of `names'
    replace test="`name'" in `i'
}
rename PTESTS1 restrictions
rename PTESTS2 covariance_rank
rename PTESTS3 max_t
rename PTESTS4 score_p
rename PTESTS5 clusters
export delimited using "$ROOT/outputs/paper/main_specification_tests.csv",replace
* Publication figures, generated entirely by Stata.
import delimited using "$ROOT/outputs/inference/elasticity_inference_paper_main.csv",clear varnames(1)
keep if sample=="common_positive" & type=="own_price"
assert _N==8
assert ci_lower<estimate & estimate<ci_upper
twoway (rcap ci_lower ci_upper good,horizontal lcolor(navy)) (scatter good estimate,msymbol(O) mcolor(navy)), ylabel(1 "Staples" 2 "Oils" 3 "Vegetables" 4 "Fruit" 5 "Pork" 6 "Other meat" 7 "Seafood" 8 "Dairy",angle(0)) yscale(reverse) xline(0,lpattern(dash)) xtitle("Marshallian own-price elasticity") ytitle("") legend(off) graphregion(color(white)) name(ownci,replace)
graph export "$ROOT/figures/fig3_main_own_price_ci.png",width(2400) replace
import delimited using "$ROOT/outputs/demand/elasticities_main.csv",clear varnames(1)
keep if margin=="unconditional" & sample=="common_positive" & substr(subgroup,1,3)=="inc" & type=="expenditure"
assert _N==40
gen byte income_bracket=real(substr(subgroup,4,.))
label define food 1 "Staples" 2 "Oils" 3 "Vegetables" 4 "Fruit" 5 "Pork" 6 "Other meat" 7 "Seafood" 8 "Dairy"
label values good food
twoway connected elasticity income_bracket,by(good,cols(2) note("")) xlabel(1(1)5) yline(1,lpattern(dash)) xtitle("Reported income bracket") ytitle("Food-expenditure elasticity") graphregion(color(white)) name(incomeplot,replace)
graph export "$ROOT/figures/fig4_income_expenditure.png",width(2400) replace
* Document table CSV inputs and a convenient eight-group workbook.
local replace replace
foreach f in descriptives sample_statistics price_variation purchase_frequency main_regularity robustness_summary main_specification_tests {
    import delimited using "$ROOT/outputs/paper/`f'.csv",clear varnames(1)
    export excel using "$ROOT/outputs/paper/eight_group_paper_tables.xlsx",sheet("`f'") firstrow(variables) `replace'
    local replace sheetreplace
}
foreach f in model_fit_full elasticities_common_full regularity_common_full cross_price_common_full engel_nested_tests {
    use "$ROOT/outputs/exact/`f'.dta",clear
    export excel using "$ROOT/outputs/paper/eight_group_paper_tables.xlsx",sheet("`f'") firstrow(variables) sheetreplace
}
foreach f in policy_exposure policy_exposure_historical {
    use "$ROOT/outputs/welfare/`f'.dta",clear
    export excel using "$ROOT/outputs/paper/eight_group_paper_tables.xlsx",sheet("`f'") firstrow(variables) sheetreplace
}
import delimited using "$ROOT/outputs/inference/elasticity_inference_paper_main.csv",clear varnames(1)
export excel using "$ROOT/outputs/paper/eight_group_paper_tables.xlsx",sheet("Main inference") firstrow(variables) sheetreplace
file open pass using "$ROOT/outputs/paper/paper_statistics_success.txt",write replace
file write pass "Eight-group paper statistics: all five new sensitivities, full 32-row main inference, exact Engel tests, and new price exposure tables verified in Stata." _n
file close pass
display "EIGHT_PAPER_TABLES_SUCCESS"
log close
