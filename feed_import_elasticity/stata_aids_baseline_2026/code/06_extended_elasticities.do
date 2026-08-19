version 17
clear all
set more off
set linesize 180

args project
if `"`project'"' == "" local project "/root/data/Paper/饲料进口弹性/stata_aids_baseline_2026"
local output `"`project'/output"'
local logs   `"`project'/logs"'
capture log close _all
log using `"`logs'/06_extended_elasticities.log"', text replace
use `"`project'/data/extended_estimation_panel.dta"', clear

tempname mem table
tempfile results
postfile `mem' str12 model str10 margin str12 elasticity_type byte demand_good shock_good ///
    double reference_share estimate std_error z_value p_value ci_low ci_high ///
    str3 significance double p_value_vs_one str3 significance_vs_one using `results', replace

foreach model in quaids sy_aids sy_quaids {
    estimates use `"`output'/`model'.ster"'
    forvalues i = 1/4 {
        local w`i' "_b[a`i':_cons]"
        local b`i' "_b[b`i':_cons]"
    }
    local w5 "(1-_b[a1:_cons]-_b[a2:_cons]-_b[a3:_cons]-_b[a4:_cons])"
    local b5 "(-_b[b1:_cons]-_b[b2:_cons]-_b[b3:_cons]-_b[b4:_cons])"
    forvalues i = 1/4 {
        forvalues j = 1/4 {
            local lo = min(`i', `j')
            local hi = max(`i', `j')
            local g`i'_`j' "_b[g`lo'`hi':_cons]"
        }
        local g`i'_5 "(-(`g`i'_1')-(`g`i'_2')-(`g`i'_3')-(`g`i'_4'))"
        local g5_`i' "`g`i'_5'"
    }
    local g5_5 "(_b[g11:_cons]+2*_b[g12:_cons]+2*_b[g13:_cons]+2*_b[g14:_cons]+_b[g22:_cons]+2*_b[g23:_cons]+2*_b[g24:_cons]+_b[g33:_cons]+2*_b[g34:_cons]+_b[g44:_cons])"

    forvalues i = 1/5 {
        quietly nlcom (share: `w`i'')
        matrix `table' = r(table)
        local share = `table'[1,1]
        quietly nlcom (elasticity: 1 + (`b`i'') / (`w`i''))
        matrix `table' = r(table)
        local pv = `table'[4,1]
        local stars = cond(`pv' < .01, "***", cond(`pv' < .05, "**", cond(`pv' < .10, "*", "")))
        local est = `table'[1,1]
        local se = `table'[2,1]
        local z = `table'[3,1]
        local lo = `table'[5,1]
        local hi = `table'[6,1]
        quietly nlcom (difference_from_one: (`b`i'') / (`w`i''))
        matrix `table' = r(table)
        local punit = `table'[4,1]
        local unitstars = cond(`punit' < .01, "***", cond(`punit' < .05, "**", cond(`punit' < .10, "*", "")))
        post `mem' ("`model'") ("latent") ("expenditure") (`i') (0) (`share') ///
            (`est') (`se') (`z') (`pv') (`lo') (`hi') ("`stars'") (`punit') ("`unitstars'")
    }
    forvalues i = 1/5 {
        quietly nlcom (share: `w`i'')
        matrix `table' = r(table)
        local share = `table'[1,1]
        forvalues j = 1/5 {
            local delta = (`i' == `j')
            local em "((`g`i'_`j'')/(`w`i'')-(`b`i'')*(`w`j'')/(`w`i'')-`delta')"
            local eh "((`g`i'_`j'')/(`w`i'')-`delta'+(`w`j''))"
            foreach type in marshallian hicksian {
                local expression "`em'"
                if "`type'" == "hicksian" local expression "`eh'"
                quietly nlcom (elasticity: `expression')
                matrix `table' = r(table)
                local pv = `table'[4,1]
                local stars = cond(`pv' < .01, "***", cond(`pv' < .05, "**", cond(`pv' < .10, "*", "")))
                post `mem' ("`model'") ("latent") ("`type'") (`i') (`j') (`share') ///
                    (`table'[1,1]) (`table'[2,1]) (`table'[3,1]) (`pv') ///
                    (`table'[5,1]) (`table'[6,1]) ("`stars'") (.) ("")
            }
        }
    }
}
postclose `mem'

use `results', clear
label define good 0 "none" 1 "corn" 2 "sorghum" 3 "cassava" 4 "oats" 5 "barley"
label values demand_good shock_good good
decode demand_good, gen(demand_product)
decode shock_good, gen(price_product)
replace price_product = "" if shock_good == 0
order model margin elasticity_type demand_product price_product reference_share estimate ///
    std_error z_value p_value ci_low ci_high significance p_value_vs_one significance_vs_one
sort model elasticity_type demand_good shock_good
export delimited using `"`output'/extended_elasticities_complete.csv"', replace
save `"`output'/extended_elasticities_complete.dta"', replace

log close
