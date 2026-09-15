version 17
clear all
set more off
set type double
args source target
if `"`source'"' == "" local source "/root/data/Paper/饲料进口弹性/stata_aids_baseline_2026"
if `"`target'"' == "" local target "/root/data/Paper/饲料进口弹性/manuscript_cn_20260915"
capture mkdir `"`target'/tables"'
capture mkdir `"`target'/logs"'
log using `"`target'/logs/01_manuscript_audit.log"', text replace
use `"`source'/data/aids_estimation_panel.dta"', clear
assert _N == 634
isid province_id quarter_id
local goods "corn sorghum cassava oats barley"
tempname shmem
tempfile shares
postfile `shmem' str10 product int N positive_share zero_share imputed_price ///
    double mean_share sd_share using `shares'
forvalues i=1/5 {
    local g : word `i' of `goods'
    quietly count if w_`g' > 0
    local pos = r(N)
    quietly count if w_`g' == 0
    local zero = r(N)
    quietly count if price_imputed`i' == 1
    local imp = r(N)
    quietly summarize w_`g'
    post `shmem' ("`g'") (_N) (`pos') (`zero') (`imp') (r(mean)) (r(sd))
}
postclose `shmem'
preserve
use `shares', clear
export delimited using `"`target'/tables/verified_share_description.csv"', replace
restore

tempname vmem
tempfile variables
postfile `vmem' str24 variable int N double mean sd min median max using `variables'
foreach v in total_expenditure_usd w_corn w_sorghum w_cassava w_oats w_barley {
    quietly summarize `v', detail
    post `vmem' ("`v'") (r(N)) (r(mean)) (r(sd)) (r(min)) (r(p50)) (r(max))
}
foreach g of local goods {
    gen double price_`g' = exp(lnp_`g')
    quietly summarize price_`g', detail
    post `vmem' ("price_`g'") (r(N)) (r(mean)) (r(sd)) (r(min)) (r(p50)) (r(max))
}
postclose `vmem'
preserve
use `variables', clear
export delimited using `"`target'/tables/verified_variable_description.csv"', replace
restore

tempname rmem
tempfile regularity
postfile `rmem' str12 model double min_alpha observed_share_sum ///
    eigen1 eigen2 eigen3 eigen4 eigen5 byte reference_concave using `regularity'
foreach model in aids quaids sy_aids sy_quaids {
    local stem "`model'"
    if "`model'" == "aids" local stem "basic_aids"
    estimates use `"`source'/output/`stem'.ster"'
    matrix A = J(5,1,0)
    matrix G = J(5,5,0)
    forvalues i=1/4 {
        matrix A[`i',1] = _b[a`i':_cons]
        forvalues j=1/4 {
            local lo = min(`i',`j')
            local hi = max(`i',`j')
            matrix G[`i',`j'] = _b[g`lo'`hi':_cons]
        }
    }
    mata: a=st_matrix("A"); a[5]=1-sum(a[1..4]); st_matrix("A",a)
    mata: g=st_matrix("G"); g[1..4,5]=-rowsum(g[1..4,1..4]); g[5,1..4]=g[1..4,5]'; g[5,5]=-sum(g[5,1..4]); st_matrix("G",g)
    mata: c=g+a*a'-diag(a); ev=symeigenvalues(c); st_matrix("EV",ev); st_numscalar("min_a",min(a)); st_numscalar("concave",max(ev)<1e-8)
    scalar osum = 1
    if inlist("`model'", "sy_aids", "sy_quaids") {
        matrix D = J(5,1,0)
        forvalues i=1/5 {
            matrix D[`i',1] = _b[d`i':_cons]
        }
        preserve
        import delimited using `"`source'/output/sy_selection_reference.csv"', clear
        gen double fitted_observed_share = .
        forvalues i=1/5 {
            local g : word `i' of `goods'
            replace fitted_observed_share = phi_ref*A[`i',1]+pdf_ref*D[`i',1] if product=="`g'"
        }
        quietly summarize fitted_observed_share
        scalar osum = r(sum)
        export delimited using `"`target'/tables/`model'_observed_reference.csv"', replace
        restore
    }
    post `rmem' ("`model'") (min_a) (osum) (EV[1,1]) (EV[1,2]) ///
        (EV[1,3]) (EV[1,4]) (EV[1,5]) (concave)
}
postclose `rmem'
use `regularity', clear
export delimited using `"`target'/tables/reference_regularity_audit.csv"', replace
log close
