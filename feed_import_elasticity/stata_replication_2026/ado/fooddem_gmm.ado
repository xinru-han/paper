*! fooddem GMM evaluator 1.0.0  12jul2026
program define fooddem_gmm
    version 17
    syntax varlist if, at(name)

    local model  "$FD_MODEL"
    local k      = $FD_K
    local neq    = `k' - 1
    local order  = $FD_ORDER
    local shares "$FD_SHARES"
    local lnp    "$FD_LNP"
    local expvar "$FD_EXP"
    local zvars  "$FD_ZVARS"
    local phi    "$FD_PHI"
    local pdf    "$FD_PDF"
    local cf     "$FD_CF"
    local rawlnp "$FD_RAWLNP"
    local rawexp "$FD_RAWEXP"
    local xmean = $FD_XMEAN
    local precommit = $FD_PRECOMMIT
    local cscales "$FD_CSCALE"
    local sy     = $FD_SY
    local syactive "$FD_SYACTIVE"
    local predmode = $FD_PRED
    local easiyoverride "$FD_EASIY"
    local ncf    = ("`cf'" != "")
    local nz : word count `zvars'
    local pos = 1

    if inlist("`model'", "aids", "quaids") {
        * The translog price-index intercept is a normalization and is fixed at 0.
        scalar __fd_a0 = 0
    }
    forvalues i = 1/`neq' {
        scalar __fd_a`i' = `at'[1,`pos']
        local ++pos
    }
    scalar __fd_a`k' = 1
    forvalues i = 1/`neq' {
        scalar __fd_a`k' = scalar(__fd_a`k') - scalar(__fd_a`i')
    }

    if inlist("`model'", "aids", "quaids") {
        forvalues i = 1/`neq' {
            scalar __fd_b`i' = `at'[1,`pos']
            local ++pos
        }
        scalar __fd_b`k' = 0
        forvalues i = 1/`neq' {
            scalar __fd_b`k' = scalar(__fd_b`k') - scalar(__fd_b`i')
        }
        if "`model'" == "quaids" {
            forvalues i = 1/`neq' {
                scalar __fd_l`i' = `at'[1,`pos']
                local ++pos
            }
            scalar __fd_l`k' = 0
            forvalues i = 1/`neq' {
                scalar __fd_l`k' = scalar(__fd_l`k') - scalar(__fd_l`i')
            }
        }
    }
    else {
        forvalues i = 1/`neq' {
            forvalues h = 1/`order' {
                scalar __fd_b`i'_`h' = `at'[1,`pos']
                local ++pos
            }
        }
        forvalues h = 1/`order' {
            scalar __fd_b`k'_`h' = 0
            forvalues i = 1/`neq' {
                scalar __fd_b`k'_`h' = scalar(__fd_b`k'_`h') - scalar(__fd_b`i'_`h')
            }
        }
    }

    forvalues i = 1/`neq' {
        forvalues j = `i'/`neq' {
            scalar __fd_g`i'_`j' = `at'[1,`pos']
            scalar __fd_g`j'_`i' = scalar(__fd_g`i'_`j')
            local ++pos
        }
    }
    forvalues i = 1/`neq' {
        scalar __fd_g`i'_`k' = 0
        forvalues j = 1/`neq' {
            scalar __fd_g`i'_`k' = scalar(__fd_g`i'_`k') - scalar(__fd_g`i'_`j')
        }
        scalar __fd_g`k'_`i' = scalar(__fd_g`i'_`k')
    }
    scalar __fd_g`k'_`k' = 0
    forvalues i = 1/`neq' {
        forvalues j = 1/`neq' {
            scalar __fd_g`k'_`k' = scalar(__fd_g`k'_`k') + scalar(__fd_g`i'_`j')
        }
    }

    if `nz' > 0 {
        forvalues i = 1/`neq' {
            forvalues d = 1/`nz' {
                scalar __fd_t`i'_`d' = `at'[1,`pos']
                local ++pos
            }
        }
        forvalues d = 1/`nz' {
            scalar __fd_t`k'_`d' = 0
            forvalues i = 1/`neq' {
                scalar __fd_t`k'_`d' = scalar(__fd_t`k'_`d') - ///
                    scalar(__fd_t`i'_`d')
            }
        }
    }
    if `ncf' {
        forvalues i = 1/`neq' {
            scalar __fd_r`i' = `at'[1,`pos']
            local ++pos
        }
        scalar __fd_r`k' = 0
        forvalues i = 1/`neq' {
            scalar __fd_r`k' = scalar(__fd_r`k') - scalar(__fd_r`i')
        }
    }
    if `sy' {
        forvalues i = 1/`neq' {
            scalar __fd_d`i' = 0
            local ai : word `i' of `syactive'
            if `ai' {
                scalar __fd_d`i' = `at'[1,`pos']
                local ++pos
            }
        }
    }
    if `precommit' {
        forvalues i = 1/`k' {
            local cscale : word `i' of `cscales'
            scalar __fd_c`i' = `cscale' * tanh(`at'[1,`pos'])
            local ++pos
        }
    }

    tempvar lnpindex realexp bprice easiy pAp base pred xlevel commitshare totalcommit
    if inlist("`model'", "aids", "quaids") {
        quietly gen double `lnpindex' = scalar(__fd_a0) `if'
        forvalues j = 1/`k' {
            local pj : word `j' of `lnp'
            quietly replace `lnpindex' = `lnpindex' + scalar(__fd_a`j') * `pj' `if'
            if `nz' > 0 {
                forvalues d = 1/`nz' {
                    local zd : word `d' of `zvars'
                    quietly replace `lnpindex' = `lnpindex' + ///
                        scalar(__fd_t`j'_`d') * `zd' * `pj' `if'
                }
            }
            if `ncf' quietly replace `lnpindex' = `lnpindex' + ///
                scalar(__fd_r`j') * `cf' * `pj' `if'
        }
        forvalues j = 1/`k' {
            local pj : word `j' of `lnp'
            forvalues m = 1/`k' {
                local pm : word `m' of `lnp'
                quietly replace `lnpindex' = `lnpindex' + 0.5 * scalar(__fd_g`j'_`m') * `pj' * `pm' `if'
            }
        }
        quietly gen double `realexp' = `expvar' - `lnpindex' `if'
        if "`model'" == "quaids" {
            quietly gen double `bprice' = 0 `if'
            forvalues j = 1/`k' {
                local pj : word `j' of `lnp'
                quietly replace `bprice' = `bprice' + scalar(__fd_b`j') * `pj' `if'
            }
            quietly replace `bprice' = exp(`bprice') `if'
        }
    }
    else {
        if `precommit' {
            quietly gen double `xlevel' = exp(`rawexp') `if'
            quietly gen double `totalcommit' = 0 `if'
            forvalues j = 1/`k' {
                local rpj : word `j' of `rawlnp'
                quietly replace `totalcommit' = `totalcommit' + ///
                    scalar(__fd_c`j') * exp(`rpj') / `xlevel' `if'
            }
        }
        if "`easiyoverride'" != "" {
            quietly gen double `easiy' = `easiyoverride' `if'
        }
        else {
            if `precommit' quietly gen double `easiy' = ///
                ln(`xlevel' * (1 - `totalcommit')) - `xmean' `if'
            else quietly gen double `easiy' = `expvar' `if'
            forvalues j = 1/`k' {
                local sj : word `j' of `shares'
                local pj : word `j' of `lnp'
                quietly replace `easiy' = `easiy' - `sj' * `pj' `if'
            }
            quietly gen double `pAp' = 0 `if'
            forvalues j = 1/`k' {
                local pj : word `j' of `lnp'
                forvalues m = 1/`k' {
                    local pm : word `m' of `lnp'
                    quietly replace `pAp' = `pAp' + ///
                        scalar(__fd_g`j'_`m') * `pj' * `pm' `if'
                }
            }
            quietly replace `easiy' = `easiy' + 0.5 * `pAp' `if'
        }
    }

    forvalues i = 1/`neq' {
        local outi : word `i' of `varlist'
        local si : word `i' of `shares'
        quietly gen double `base' = scalar(__fd_a`i') `if'
        forvalues j = 1/`k' {
            local pj : word `j' of `lnp'
            quietly replace `base' = `base' + scalar(__fd_g`i'_`j') * `pj' `if'
        }
        if inlist("`model'", "aids", "quaids") {
            quietly replace `base' = `base' + scalar(__fd_b`i') * `realexp' `if'
            if "`model'" == "quaids" {
                quietly replace `base' = `base' + scalar(__fd_l`i') * (`realexp'^2 / `bprice') `if'
            }
        }
        else {
            forvalues h = 1/`order' {
                quietly replace `base' = `base' + scalar(__fd_b`i'_`h') * (`easiy'^`h') `if'
            }
        }
        if `nz' > 0 {
            forvalues d = 1/`nz' {
                local zd : word `d' of `zvars'
                quietly replace `base' = `base' + scalar(__fd_t`i'_`d') * `zd' `if'
            }
        }
        if `ncf' {
            quietly replace `base' = `base' + scalar(__fd_r`i') * `cf' `if'
        }
        if `precommit' {
            local rpi : word `i' of `rawlnp'
            quietly gen double `commitshare' = scalar(__fd_c`i') * exp(`rpi') / `xlevel' `if'
            quietly replace `base' = `commitshare' + (1 - `totalcommit') * `base' `if'
            drop `commitshare'
        }
        if `sy' {
            local phii : word `i' of `phi'
            local pdfi : word `i' of `pdf'
            quietly gen double `pred' = `phii' * `base' + scalar(__fd_d`i') * `pdfi' `if'
            if `predmode' quietly replace `outi' = `pred' `if'
            else quietly replace `outi' = `si' - `pred' `if'
            drop `pred'
        }
        else {
            if `predmode' quietly replace `outi' = `base' `if'
            else quietly replace `outi' = `si' - `base' `if'
        }
        drop `base'
    }
end
