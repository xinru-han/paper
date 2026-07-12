*! Predictions after fooddem 1.0.0  12jul2026
program define fooddem_p
    version 17
    syntax newvarlist(min=3 numeric) [if] [in]
    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    local k = e(fooddem_goods)
    local neq = `k' - 1
    local kn : word count `varlist'
    if `kn' != `k' {
        di as error "specify exactly `k' new prediction variables"
        exit 198
    }
    marksample touse, novarlist
    quietly replace `touse' = 0 if !e(sample)

    * Active Shonkwiler-Yen probabilities are functions of the participation
    * covariates. Recompute them for every counterfactual so price, expenditure,
    * and demographic elasticities include both intensive and extensive margins.
    if "`e(fooddem_selection)'" == "sy" {
        tempname syb
        matrix `syb' = e(fooddem_syb)
        local active "`e(fooddem_syactive)'"
        local selcovars "`e(fooddem_selcovars)'"
        local philist "`e(fooddem_phi)'"
        local pdflist "`e(fooddem_pdf)'"
        forvalues i = 1/`k' {
            local ai : word `i' of `active'
            if `ai' {
                tempvar xb
                quietly gen double `xb' = `syb'[`i',1] if `touse'
                local sc = 1
                foreach z of local selcovars {
                    local ++sc
                    quietly replace `xb' = `xb' + `syb'[`i',`sc'] * `z' if `touse'
                }
                local phii : word `i' of `philist'
                local pdfi : word `i' of `pdflist'
                quietly replace `phii' = normal(`xb') if `touse'
                quietly replace `pdfi' = normalden(`xb') if `touse'
            }
        }
    }

    local prices "`e(fooddem_prices)'"
    local shares "`e(fooddem_shares)'"
    local expvar "`e(fooddem_expenditure)'"
    forvalues j = 1/`k' {
        local pj : word `j' of `prices'
        capture confirm variable _fd_lnp`j'
        if _rc quietly gen double _fd_lnp`j' = .
        quietly replace _fd_lnp`j' = `pj' - e(fooddem_pmean`j') if `touse'
    }
    capture confirm variable _fd_lnx
    if _rc quietly gen double _fd_lnx = .
    quietly replace _fd_lnx = `expvar' - e(fooddem_xmean) if `touse'

    global FD_MODEL "`e(fooddem_model)'"
    global FD_K `k'
    global FD_ORDER = e(fooddem_order)
    global FD_SHARES "`shares'"
    global FD_LNP "`e(fooddem_modelprices)'"
    global FD_EXP "`e(fooddem_modelexpenditure)'"
    global FD_ZVARS "`e(fooddem_demographics)'"
    global FD_PHI "`e(fooddem_phi)'"
    global FD_PDF "`e(fooddem_pdf)'"
    global FD_CF "`e(fooddem_cf)'"
    global FD_RAWLNP "`e(fooddem_prices)'"
    global FD_RAWEXP "`e(fooddem_expenditure)'"
    global FD_XMEAN = e(fooddem_xmean)
    global FD_PRECOMMIT = ("`e(fooddem_precommitment)'" != "")
    global FD_CSCALE "`e(fooddem_cscales)'"
    global FD_SY = ("`e(fooddem_selection)'" == "sy")
    global FD_SYACTIVE "`e(fooddem_syactive)'"
    global FD_PRED 1
    global FD_EASIY ""

    tempname b
    matrix `b' = e(b)
    local work ""
    forvalues i = 1/`neq' {
        tempvar f`i'
        quietly gen double `f`i'' = .
        local work "`work' `f`i''"
    }
    quietly fooddem_gmm `work' if `touse', at(`b')

    * EASI utility is implicit. Estimation uses observed shares as endogenous
    * regressors, but counterfactual prediction must solve its own shares and
    * real expenditure jointly. The scalar fixed-point equation is a polynomial
    * of the requested EASI order. Solve all roots exactly and follow the real
    * branch closest to observed implicit utility; never hide divergent cases by
    * allowing iteration-generated missing values to leave the sample.
    if "`e(fooddem_model)'" == "easi" {
        tempvar discretionary ystart yroot pAp xlevel totalcommit

        if "`e(fooddem_precommitment)'" != "" {
            quietly gen double `xlevel' = exp(`expvar') if `touse'
            quietly gen double `totalcommit' = 0 if `touse'
            local scales "`e(fooddem_cscales)'"
            local firstc = colsof(`b') - `k' + 1
            forvalues j = 1/`k' {
                local rawpj : word `j' of `prices'
                local scale : word `j' of `scales'
                local cj = `scale' * tanh(`b'[1,`=`firstc'+`j'-1'])
                quietly replace `totalcommit' = `totalcommit' + ///
                    `cj' * exp(`rawpj') / `xlevel' if `touse'
            }
            quietly gen double `discretionary' = ///
                ln(`xlevel' * (1 - `totalcommit')) - e(fooddem_xmean) if `touse'
        }
        else quietly gen double `discretionary' = _fd_lnx if `touse'

        quietly gen double `pAp' = 0 if `touse'
        forvalues j = 1/`k' {
            forvalues m = 1/`k' {
                quietly replace `pAp' = `pAp' + scalar(__fd_g`j'_`m') * ///
                    _fd_lnp`j' * _fd_lnp`m' if `touse'
            }
        }
        quietly gen double `ystart' = `discretionary' + 0.5 * `pAp' if `touse'
        forvalues j = 1/`k' {
            local sj : word `j' of `shares'
            quietly replace `ystart' = `ystart' - `sj' * _fd_lnp`j' if `touse'
        }

        local order = e(fooddem_order)
        local nodes ""
        local fvalues ""
        local plast "_fd_lnp`k'"
        forvalues h = 0/`order' {
            local node = `h' - `order' / 2
            local nodes "`nodes' `node'"
            tempvar yprobe fprobe
            quietly gen double `yprobe' = `ystart' + `node' if `touse'
            global FD_EASIY "`yprobe'"
            quietly fooddem_gmm `work' if `touse', at(`b')
            quietly gen double `fprobe' = `yprobe' - `discretionary' - ///
                0.5 * `pAp' + `plast' if `touse'
            forvalues j = 1/`neq' {
                local fj : word `j' of `work'
                quietly replace `fprobe' = `fprobe' + ///
                    `fj' * (_fd_lnp`j' - `plast') if `touse'
            }
            local fvalues "`fvalues' `fprobe'"
        }
        quietly gen double `yroot' = .
        mata: _fooddem_easi_root("`touse'", "`fvalues'", "`nodes'", ///
            "`ystart'", "`yroot'")
        quietly count if `touse' & missing(`yroot')
        if r(N) > 0 {
            local rootfail = r(N)
            global FD_EASIY ""
            global FD_PRED 0
            di as error "EASI counterfactual has no stable real utility root for `rootfail' observations"
            exit 430
        }
        global FD_EASIY "`yroot'"
        quietly fooddem_gmm `work' if `touse', at(`b')
    }
    local partial ""
    forvalues i = 1/`neq' {
        local newi : word `i' of `varlist'
        local fi : word `i' of `work'
        quietly gen double `newi' = `fi' if `touse'
        local partial "`partial' `newi'"
    }
    local newk : word `k' of `varlist'
    quietly egen double `newk' = rowtotal(`partial') if `touse'
    quietly replace `newk' = 1 - `newk' if `touse'
    global FD_EASIY ""
    global FD_PRED 0
end

capture mata: mata drop _fooddem_easi_root()
mata:
mata set matastrict on

void _fooddem_easi_root(
    string scalar tousevar,
    string scalar fvars,
    string scalar nodestr,
    string scalar ystartvar,
    string scalar yrootvar)
{
    real colvector idx, nodes, out, realroots, distance
    real matrix F, V, B, C
    real rowvector coef, keep
    complex rowvector roots
    real scalar n, degree, i, j, scale, chosen

    idx = selectindex(st_data(., tousevar) :!= 0)
    F = st_data(idx, tokens(fvars))
    nodes = strtoreal(tokens(nodestr))'
    n = rows(F)
    degree = rows(nodes) - 1
    V = J(degree + 1, degree + 1, .)
    for (i = 1; i <= degree + 1; i++) {
        for (j = 1; j <= degree + 1; j++) V[i, j] = nodes[i]^(j - 1)
    }
    B = invsym(quadcross(V, V)) * V'
    C = F * B'
    out = J(n, 1, .)
    for (i = 1; i <= n; i++) {
        coef = C[i, ]
        scale = max(abs(coef))
        if (scale == 0) {
            out[i] = 0
            continue
        }
        if (abs(coef[1]) <= 1e-10 * (1 + scale)) {
            out[i] = 0
            continue
        }
        roots = polyroots(coef)
        keep = selectindex(abs(Im(roots)) :<= 1e-7 * (1 :+ abs(Re(roots))))
        if (cols(keep) == 0) continue
        realroots = Re(roots[keep])'
        distance = abs(realroots)
        chosen = order(distance, 1)[1]
        out[i] = realroots[chosen]
    }
    st_store(idx, yrootvar, st_data(idx, ystartvar) + out)
}
end
