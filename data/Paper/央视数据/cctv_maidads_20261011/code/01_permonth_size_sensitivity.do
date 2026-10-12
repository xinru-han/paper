version 17
clear all
set more off
set type double
global run "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$run/logs/01_permonth_size_sensitivity.log",text replace

tempname result
postfile `result' str12 frequency str28 sample str36 metric double value ///
    using "$run/outputs/data_audit/permonth_size_sensitivity.dta",replace
local slist
local qlist
local wlist
local plist
local pclist
forvalues j=1/8 {
    local slist `slist' spend`j'
    local qlist `qlist' q`j'
    local wlist `wlist' w`j'
    local plist `plist' p`j'
    local pclist `pclist' perproxy_month_spend`j'
}

foreach frequency in quarter year {
    if "`frequency'"=="quarter" local period tq
    else local period year
    use "$run/data/household_month_8.dta",clear
    assert active_month==1
    local sums
    forvalues j=1/8 {
        gen double pc_sum`j'=spend`j'/size_proxy
        local sums `sums' pc_sum`j'
    }
    gen double nut_pc_sum=nut_spend/size_proxy
    collapse (sum) `sums' nut_pc_sum (count) source_months=ym ///
        (min) monthly_size_proxy_min=size_proxy (max) monthly_size_proxy_max=size_proxy, ///
        by(hh_id `period')
    forvalues j=1/8 {
        gen double perproxy_month_spend`j'=pc_sum`j'/source_months
        drop pc_sum`j'
    }
    gen double perproxy_month_nut_spend=nut_pc_sum/source_months
    drop nut_pc_sum
    tempfile month_normalized
    save `month_normalized'

    use "$run/data/household_`frequency'_8.dta",clear
    merge 1:1 hh_id `period' using `month_normalized',assert(match) nogen
    assert source_months==month_count
    rename m m_lastsize
    egen double m=rowtotal(`pclist')
    gen byte monthly_size_changes=monthly_size_proxy_min!=monthly_size_proxy_max
    assert monthly_size_changes==changed_size_band
    gen double relative_m_change=m/m_lastsize-1 if m_lastsize>0
    gen double absolute_relative_m_change=abs(relative_m_change)
    assert abs(relative_m_change)<1e-12 if !monthly_size_changes & m_lastsize>0
    assert m>=0 & m<.
    label var m "Monthly-equivalent covered purchases: each active month divided by its own population proxy"
    label var m_lastsize "Monthly-equivalent covered purchases divided by last recorded population proxy"
    gen str96 size_normalization="Monthly spending / month-end population proxy, then mean across genuine active months"
    forvalues j=1/8 {
        rename w`j' w_lastsize`j'
        rename q`j' q_lastsize`j'
        gen double w`j'=perproxy_month_spend`j'/m if m>0
        gen double q`j'=perproxy_month_spend`j'/p`j' if m>0
        assert q`j'>=0 & q`j'<. if m>0
        assert abs(p`j'*q`j'-m*w`j')<1e-10*max(1,m) if m>0
    }
    egen double __wsum=rowtotal(`wlist')
    assert abs(__wsum-1)<1e-10 if m>0
    drop __wsum source_months
    assert (m==0)==(m_lastsize==0)
    isid hh_id `period'
    save "$run/data/household_`frequency'_8_permonth_size.dta",replace
    export delimited using "$run/data/household_`frequency'_8_permonth_size.csv",replace nolabel

    foreach sample in all_positive size_changes no_size_changes complete_positive complete_size_changes {
        local condition m>0
        if "`sample'"=="size_changes" local condition m>0 & monthly_size_changes
        if "`sample'"=="no_size_changes" local condition m>0 & !monthly_size_changes
        if "`sample'"=="complete_positive" local condition m>0 & complete_window
        if "`sample'"=="complete_size_changes" local condition m>0 & complete_window & monthly_size_changes
        quietly count if `condition'
        post `result' ("`frequency'") ("`sample'") ("windows") (r(N))
        foreach v in m m_lastsize relative_m_change absolute_relative_m_change {
            quietly summarize `v' if `condition',detail
            foreach stat in mean min p1 p50 p99 max {
                post `result' ("`frequency'") ("`sample'") ("`v'_`stat'") (r(`stat'))
            }
        }
    }

    preserve
    keep if complete_window
    save "$run/data/household_`frequency'_8_permonth_size_complete.dta",replace
    restore
    keep if m>0
    gen long obs_count=1
    gen double complete_n=complete_window
    if "`frequency'"=="quarter" local cellby province province_name tq year type income_band size_band
    else local cellby province province_name year type income_band size_band
    collapse (mean) m m_lastsize `qlist' `slist' `pclist' nut_spend perproxy_month_nut_spend month_count size_proxy ///
        (firstnm) `plist' family_type (sum) nobs=obs_count complete_n n_size_changes=monthly_size_changes, ///
        by(`cellby')
    gen long n_households=nobs
    gen int time=`period'
    if "`frequency'"=="quarter" gen byte quarter=quarter(dofq(tq))
    forvalues j=1/8 {
        gen double w`j'=p`j'*q`j'/m
    }
    egen double __wsum=rowtotal(`wlist')
    assert abs(__wsum-1)<1e-10
    drop __wsum
    isid province `period' type income_band size_band
    save "$run/data/cells_`frequency'_8_permonth_size.dta",replace
    export delimited using "$run/data/cells_`frequency'_8_permonth_size.csv",replace nolabel
}
postclose `result'
use "$run/outputs/data_audit/permonth_size_sensitivity.dta",clear
export delimited using "$run/outputs/data_audit/permonth_size_sensitivity.csv",replace
list if inlist(metric,"windows","m_mean","m_lastsize_mean","relative_m_change_mean","relative_m_change_min","relative_m_change_max"),noobs abbreviate(36)
log close
