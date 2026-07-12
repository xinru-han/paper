*! version 1.0.0  12jul2026
program define easi_sy3sls, eclass
    version 17
    syntax , SHARES(varlist numeric) LNP(varlist numeric) EXPenditure(varname numeric) ///
        ZVARS(varlist numeric) PHI(varlist numeric) PDF(varlist numeric) ///
        [POWers(integer 2) MAXIter(integer 100) TOL(real 1e-6)]

    local k : word count `shares'
    local nk : word count `lnp'
    local nphi : word count `phi'
    local npdf : word count `pdf'
    if `k' < 3 | `k' != `nk' | `k' != `nphi' | `k' != `npdf' {
        di as error "shares, lnp, phi, and pdf must have the same length of at least three."
        exit 198
    }
    local neq = `k' - 1
    local ref : word `k' of `lnp'
    local refshare : word `k' of `shares'
    local prefix "_easi"

    * Relative prices impose homogeneity. The last share is omitted and recovered
    * by adding-up, so every fitted observation sums exactly to one.
    forvalues j = 1/`neq' {
        local pj : word `j' of `lnp'
        gen double `prefix'_np`j' = `pj' - `ref'
        gen double `prefix'_np`j'_backup = `prefix'_np`j'
    }
    gen double `prefix'_ystone = `expenditure'
    gen double `prefix'_yinst = `expenditure'
    forvalues j = 1/`k' {
        local sj : word `j' of `shares'
        local pj : word `j' of `lnp'
        quietly summarize `sj', meanonly
        replace `prefix'_ystone = `prefix'_ystone - `sj' * `pj'
        replace `prefix'_yinst = `prefix'_yinst - r(mean) * `pj'
    }
    gen double `prefix'_y = `prefix'_ystone

    local ylist ""
    local yinstlist ""
    forvalues h = 1/`powers' {
        gen double `prefix'_y`h' = `prefix'_y^`h'
        gen double `prefix'_yinst`h' = `prefix'_yinst^`h'
        local ylist "`ylist' `prefix'_y`h'"
        local yinstlist "`yinstlist' `prefix'_yinst`h'"
    }

    local eqlist ""
    local endog ""
    local instr ""
    forvalues i = 1/`neq' {
        local si : word `i' of `shares'
        local phii : word `i' of `phi'
        local pdfi : word `i' of `pdf'
        gen double `prefix'_c`i' = `phii'
        local rhs "`prefix'_c`i' `pdfi'"
        forvalues h = 1/`powers' {
            gen double `prefix'_py`i'_`h' = `phii' * `prefix'_y`h'
            gen double `prefix'_iy`i'_`h' = `phii' * `prefix'_yinst`h'
            local rhs "`rhs' `prefix'_py`i'_`h'"
            local endog "`endog' `prefix'_py`i'_`h'"
            local instr "`instr' `prefix'_iy`i'_`h'"
        }
        local znum : word count `zvars'
        forvalues h = 1/`znum' {
            local zh : word `h' of `zvars'
            gen double `prefix'_pz`i'_`h' = `phii' * `zh'
            local rhs "`rhs' `prefix'_pz`i'_`h'"
        }
        forvalues j = 1/`neq' {
            gen double `prefix'_pp`i'_`j' = `phii' * `prefix'_np`j'
            local rhs "`rhs' `prefix'_pp`i'_`j'"
        }
        local eqlist `"`eqlist' (`si' `rhs', noconstant)"'
    }

    * Symmetry on the unrestricted (K-1)x(K-1) price block. Together with the
    * omitted last equation and relative-price normalization, this delivers
    * symmetry, homogeneity, and adding-up for the complete K-good system.
    local conlist ""
    forvalues i = 1/`neq' {
        local ip1 = `i' + 1
        local si : word `i' of `shares'
        if `i' < `neq' {
            forvalues j = `ip1'/`neq' {
                local sj : word `j' of `shares'
                constraint define `i'`j' [`si']`prefix'_pp`i'_`j' = [`sj']`prefix'_pp`j'_`i'
                local conlist "`conlist' `i'`j'"
            }
        }
    }

    tempname crit
    scalar `crit' = 1
    local iter = 0
    while scalar(`crit') > `tol' & `iter' < `maxiter' {
        local iter = `iter' + 1
        quietly reg3 `eqlist', constraints(`conlist') endog(`endog') exog(`instr')
        gen double `prefix'_pAp = 0
        gen double `prefix'_yold = `prefix'_y
        forvalues j = 1/`neq' {
            local sj : word `j' of `shares'
            quietly predict double `prefix'_s`j'_p, equation(`sj')
        }
        forvalues i = 1/`neq' {
            forvalues j = 1/`neq' {
                replace `prefix'_pp`i'_`j' = 0
            }
        }
        forvalues j = 1/`neq' {
            local sj : word `j' of `shares'
            quietly predict double `prefix'_s`j'_0, equation(`sj')
            replace `prefix'_pAp = `prefix'_pAp + `prefix'_np`j'_backup * (`prefix'_s`j'_p - `prefix'_s`j'_0)
        }
        forvalues i = 1/`neq' {
            local phii : word `i' of `phi'
            forvalues j = 1/`neq' {
                replace `prefix'_pp`i'_`j' = `phii' * `prefix'_np`j'_backup
            }
        }
        replace `prefix'_y = `prefix'_ystone + 0.5 * `prefix'_pAp
        forvalues h = 1/`powers' {
            replace `prefix'_y`h' = `prefix'_y^`h'
            forvalues i = 1/`neq' {
                local phii : word `i' of `phi'
                replace `prefix'_py`i'_`h' = `phii' * `prefix'_y`h'
            }
        }
        gen double `prefix'_change = abs(`prefix'_y - `prefix'_yold)
        quietly summarize `prefix'_change, meanonly
        scalar `crit' = r(max)
        drop `prefix'_s*_p `prefix'_s*_0 `prefix'_pAp `prefix'_yold `prefix'_change
    }
    if scalar(`crit') > `tol' {
        di as error "EASI iteration failed to converge in `maxiter' iterations."
        exit 430
    }
    quietly reg3 `eqlist', constraints(`conlist') endog(`endog') exog(`instr')
    ereturn scalar easi_iterations = `iter'
    ereturn scalar easi_convergence = scalar(`crit')
    ereturn scalar easi_goods = `k'
    ereturn local easi_reference "`refshare'"
    ereturn local cmd "easi_sy3sls"
end
