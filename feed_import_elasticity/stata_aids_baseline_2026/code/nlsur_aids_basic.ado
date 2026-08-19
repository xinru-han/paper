*! Exact five-good AIDS evaluator, theory restricted 19aug2026
program define nlsurbasic_aids
    version 17
    syntax varlist(min=10 max=10) if, at(name)
    tokenize `varlist'
    args w1 w2 w3 w4 p1 p2 p3 p4 p5 lnx

    tempname a1 a2 a3 a4 a5 b1 b2 b3 b4 b5
    forvalues i = 1/4 {
        scalar `a`i'' = `at'[1, `i']
        scalar `b`i'' = `at'[1, `i' + 4]
    }
    scalar `a5' = 1 - `a1' - `a2' - `a3' - `a4'
    scalar `b5' = -`b1' - `b2' - `b3' - `b4'

    tempname g11 g12 g13 g14 g15 g21 g22 g23 g24 g25
    tempname g31 g32 g33 g34 g35 g41 g42 g43 g44 g45
    tempname g51 g52 g53 g54 g55
    scalar `g11' = `at'[1,  9]
    scalar `g12' = `at'[1, 10]
    scalar `g13' = `at'[1, 11]
    scalar `g14' = `at'[1, 12]
    scalar `g22' = `at'[1, 13]
    scalar `g23' = `at'[1, 14]
    scalar `g24' = `at'[1, 15]
    scalar `g33' = `at'[1, 16]
    scalar `g34' = `at'[1, 17]
    scalar `g44' = `at'[1, 18]

    scalar `g21' = `g12'
    scalar `g31' = `g13'
    scalar `g41' = `g14'
    scalar `g32' = `g23'
    scalar `g42' = `g24'
    scalar `g43' = `g34'

    scalar `g15' = -`g11' - `g12' - `g13' - `g14'
    scalar `g25' = -`g21' - `g22' - `g23' - `g24'
    scalar `g35' = -`g31' - `g32' - `g33' - `g34'
    scalar `g45' = -`g41' - `g42' - `g43' - `g44'
    scalar `g51' = `g15'
    scalar `g52' = `g25'
    scalar `g53' = `g35'
    scalar `g54' = `g45'
    scalar `g55' = `g11' + 2*`g12' + 2*`g13' + 2*`g14' + ///
                    `g22' + 2*`g23' + 2*`g24' + `g33' + 2*`g34' + `g44'

    local avec "`a1' `a2' `a3' `a4' `a5'"
    local bvec "`b1' `b2' `b3' `b4' `b5'"
    local pvec "`p1' `p2' `p3' `p4' `p5'"
    local G11 "`g11'"
    local G12 "`g12'"
    local G13 "`g13'"
    local G14 "`g14'"
    local G15 "`g15'"
    local G21 "`g21'"
    local G22 "`g22'"
    local G23 "`g23'"
    local G24 "`g24'"
    local G25 "`g25'"
    local G31 "`g31'"
    local G32 "`g32'"
    local G33 "`g33'"
    local G34 "`g34'"
    local G35 "`g35'"
    local G41 "`g41'"
    local G42 "`g42'"
    local G43 "`g43'"
    local G44 "`g44'"
    local G45 "`g45'"
    local G51 "`g51'"
    local G52 "`g52'"
    local G53 "`g53'"
    local G54 "`g54'"
    local G55 "`g55'"

    quietly {
        tempvar lnP realexp
        gen double `lnP' = 0 `if'
        forvalues j = 1/5 {
            local aj : word `j' of `avec'
            local pj : word `j' of `pvec'
            replace `lnP' = `lnP' + `aj' * `pj' `if'
            forvalues k = 1/5 {
                local pk : word `k' of `pvec'
                local gjk "`G`j'`k''"
                replace `lnP' = `lnP' + 0.5 * `gjk' * `pj' * `pk' `if'
            }
        }
        gen double `realexp' = `lnx' - `lnP' `if'

        forvalues i = 1/4 {
            local wi : word `i' of `varlist'
            local ai : word `i' of `avec'
            local bi : word `i' of `bvec'
            replace `wi' = `ai' + `bi' * `realexp' `if'
            forvalues j = 1/5 {
                local pj : word `j' of `pvec'
                local gij "`G`i'`j''"
                replace `wi' = `wi' + `gij' * `pj' `if'
            }
        }
    }
end
