*! General AIDS/QUAIDS/EASI demand systems 1.3.0  14jul2026
program define fooddem, eclass sortpreserve
    version 17
    syntax [if] [in], MODEL(string) SHARES(varlist numeric min=3) ///
        PRICES(varlist numeric min=3) EXPenditure(varname numeric) ///
        [ESTimator(string) ORDER(integer 2) DEMographics(varlist numeric) ///
         QUANTities(varlist numeric) SELection(string) SELectvars(varlist numeric) ///
         ENDogeneity(string) INSTruments(varlist numeric) CLuster(varname) ///
         PRECommitment FROM(name) GMMsteps(integer 2) ITERate(integer 200) ///
         TOLerance(real 1e-6) CURVature(string)]

    marksample touse, novarlist
    local model = lower("`model'")
    local estimator = lower("`estimator'")
    local selection = lower("`selection'")
    local endogeneity = lower("`endogeneity'")
    local curvature = lower("`curvature'")
    if "`estimator'" == "" local estimator "gmm"
    if "`selection'" == "" local selection "none"
    if "`endogeneity'" == "" local endogeneity "none"
    if "`curvature'" == "" local curvature "none"
    if !inlist("`model'", "aids", "quaids", "easi") {
        di as error "model() must be aids, quaids, or easi"
        exit 198
    }
    if !inlist("`estimator'", "gmm", "nlsur") {
        di as error "estimator() must be gmm or nlsur"
        exit 198
    }
    if !inlist("`selection'", "none", "sy") {
        di as error "selection() must be none or sy"
        exit 198
    }
    if !inlist("`endogeneity'", "none", "iv", "cf") {
        di as error "endogeneity() must be none, iv, or cf"
        exit 198
    }
    if !inlist("`curvature'", "none", "local", "global") {
        di as error "curvature() must be none, local, or global"
        exit 198
    }
    if "`curvature'" != "none" & ("`model'" != "easi" | "`estimator'" != "gmm") {
        di as error "curvature() is currently available for EASI GMM"
        exit 198
    }
    if "`curvature'" != "none" & "`precommitment'" != "" {
        di as error "curvature() is not available with precommitment"
        exit 198
    }
    if "`estimator'" == "nlsur" & "`endogeneity'" == "iv" {
        di as error "NLSUR cannot instrument expenditure directly; use endogeneity(cf)"
        exit 198
    }
    if !inlist(`gmmsteps', 1, 2) {
        di as error "gmmsteps() must be 1 or 2"
        exit 198
    }
    if "`endogeneity'" != "none" & "`instruments'" == "" {
        di as error "endogeneity() requires excluded instruments()"
        exit 198
    }

    local k : word count `shares'
    local kp : word count `prices'
    local neq = `k' - 1
    if `kp' != `k' {
        di as error "shares() and prices() must contain the same number of goods"
        exit 198
    }
    if "`quantities'" != "" {
        local kq : word count `quantities'
        if `kq' != `k' {
            di as error "quantities() must have one variable per good"
            exit 198
        }
    }
    if "`selection'" == "sy" & "`quantities'" == "" {
        di as error "selection(sy) requires quantities()"
        exit 198
    }
    if "`model'" == "easi" & (`order' < 1 | `order' >= `k') {
        di as error "For EASI, order() must be at least 1 and less than the number of goods"
        exit 198
    }
    if "`precommitment'" != "" & "`model'" != "easi" {
        di as error "precommitment is available only with model(easi)"
        exit 198
    }

    markout `touse' `shares' `prices' `expenditure' `demographics' ///
        `instruments' `selectvars'
    if "`selection'" == "sy" markout `touse' `quantities'
    if "`cluster'" != "" markout `touse' `cluster', strok
    quietly count if `touse'
    if r(N) <= 10 * `k' {
        di as error "insufficient complete observations for this system"
        exit 2001
    }

    tempvar sharesum
    quietly egen double `sharesum' = rowtotal(`shares') if `touse'
    quietly count if `touse' & (abs(`sharesum' - 1) > 1e-8)
    if r(N) > 0 {
        di as error "shares() must add to one within 1e-8 for every estimation observation"
        exit 459
    }
    foreach si of local shares {
        quietly count if `touse' & (`si' < 0 | `si' > 1)
        if r(N) > 0 {
            di as error "shares() must lie in [0,1] for every estimation observation"
            exit 459
        }
    }
    if "`selection'" == "sy" {
        foreach qi of local quantities {
            quietly count if `touse' & `qi' < 0
            if r(N) > 0 {
                di as error "quantities() must be nonnegative"
                exit 459
            }
        }
    }

    local vceopt "vce(robust)"
    if "`cluster'" != "" local vceopt "vce(cluster `cluster')"

    * Centering is a numerical normalization only; elasticities are invariant.
    local modelprices ""
    forvalues j = 1/`k' {
        local pj : word `j' of `prices'
        quietly summarize `pj' if `touse', meanonly
        local pmean = r(mean)
        local pmean`j' = r(mean)
        capture drop _fd_lnp`j'
        gen double _fd_lnp`j' = `pj' - `pmean' if `touse'
        local modelprices "`modelprices' _fd_lnp`j'"
    }
    quietly summarize `expenditure' if `touse', meanonly
    local xmean = r(mean)
    capture drop _fd_lnx
    gen double _fd_lnx = `expenditure' - `xmean' if `touse'
    local modelexp "_fd_lnx"

    local philist ""
    local pdflist ""
    local syactive ""
    local selcovars ""
    tempname syb
    if "`selection'" == "sy" {
        local selcovars "`expenditure' `prices' `demographics' `selectvars'"
        local selcovars : list uniq selcovars
        local nsel : word count `selcovars'
        matrix `syb' = J(`k', `nsel' + 1, .)
        forvalues i = 1/`k' {
            local qi : word `i' of `quantities'
            capture drop _fd_d`i' _fd_phi`i' _fd_pdf`i'
            gen byte _fd_d`i' = `qi' > 0 if `touse'
            quietly summarize _fd_d`i' if `touse', meanonly
            local rate = r(mean)
            if `rate' >= .98 {
                gen double _fd_phi`i' = 1 if `touse'
                gen double _fd_pdf`i' = 0 if `touse'
                local syactive "`syactive' 0"
            }
            else if `rate' <= .02 {
                di as error "good `i' has too few positive observations for a stable SY probit"
                exit 459
            }
            else {
                quietly probit _fd_d`i' `expenditure' `prices' `demographics' ///
                    `selectvars' if `touse', `vceopt'
                matrix `syb'[`i',1] = _b[_cons]
                local sc = 1
                foreach z of local selcovars {
                    local ++sc
                    matrix `syb'[`i',`sc'] = _b[`z']
                }
                tempvar xb
                predict double `xb' if e(sample), xb
                gen double _fd_phi`i' = normal(`xb') if `touse'
                gen double _fd_pdf`i' = normalden(`xb') if `touse'
                replace _fd_phi`i' = `rate' if missing(_fd_phi`i') & `touse'
                replace _fd_pdf`i' = 0 if missing(_fd_pdf`i') & `touse'
                local syactive "`syactive' 1"
            }
            local philist "`philist' _fd_phi`i'"
            local pdflist "`pdflist' _fd_pdf`i'"
        }
    }

    local cfvar ""
    local firstF = .
    local firstP = .
    local firstR2 = .
    if "`endogeneity'" != "none" {
        quietly regress `modelexp' `modelprices' `demographics' `selectvars' ///
            `instruments' if `touse', `vceopt'
        local firstR2 = e(r2)
        quietly test `instruments'
        local firstF = r(F)
        local firstP = r(p)
    }
    if "`endogeneity'" == "cf" {
        capture drop _fd_cf
        predict double _fd_cf if e(sample), residuals
        local cfvar "_fd_cf"
    }

    * GEASI precommitments are quantity parameters. The tanh transformation
    * permits an exact joint null at zero while the observation-specific scale
    * guarantees that aggregate committed expenditure stays below 50 percent
    * of total expenditure throughout numerical optimization.
    local cscales ""
    if "`precommitment'" != "" {
        forvalues j = 1/`k' {
            local pj : word `j' of `prices'
            tempvar xp
            gen double `xp' = exp(`expenditure' - `pj') if `touse'
            quietly summarize `xp' if `touse', meanonly
            local cs = 0.5 * r(min) / `k'
            if missing(`cs') | `cs' <= 0 {
                di as error "cannot construct a safe precommitment scale for good `j'"
                exit 459
            }
            local cscales "`cscales' `cs'"
        }
    }

    local pnames ""
    forvalues i = 1/`neq' {
        local pnames "`pnames' a`i'"
    }
    if inlist("`model'", "aids", "quaids") {
        forvalues i = 1/`neq' {
            local pnames "`pnames' b`i'"
        }
        if "`model'" == "quaids" {
            forvalues i = 1/`neq' {
                local pnames "`pnames' l`i'"
            }
        }
    }
    else {
        forvalues i = 1/`neq' {
            forvalues h = 1/`order' {
                local pnames "`pnames' b`i'_`h'"
            }
        }
    }
    forvalues i = 1/`neq' {
        forvalues j = `i'/`neq' {
            local pnames "`pnames' g`i'_`j'"
        }
    }
    local nz : word count `demographics'
    if `nz' > 0 {
        forvalues i = 1/`neq' {
            forvalues d = 1/`nz' {
                local pnames "`pnames' t`i'_`d'"
            }
        }
    }
    if "`cfvar'" != "" {
        forvalues i = 1/`neq' {
            local pnames "`pnames' r`i'"
        }
    }
    if "`selection'" == "sy" {
        forvalues i = 1/`neq' {
            local ai : word `i' of `syactive'
            if `ai' local pnames "`pnames' d`i'"
        }
    }
    if "`precommitment'" != "" {
        forvalues i = 1/`k' {
            local pnames "`pnames' c`i'"
        }
    }
    local npar : word count `pnames'
    tempname init
    if "`from'" == "" {
        matrix `init' = J(1, `npar', 0)
        matrix colnames `init' = `pnames'

        * A constrained linear projection gives nonlinear estimators a stable
        * starting point. Relative prices impose homogeneity, and averaging
        * reciprocal price coefficients projects the start onto symmetry.
        local relprices ""
        local plast : word `k' of `modelprices'
        forvalues j = 1/`neq' {
            local pj : word `j' of `modelprices'
            capture drop _fd_relp`j'
            gen double _fd_relp`j' = `pj' - `plast' if `touse'
            local relprices "`relprices' _fd_relp`j'"
        }
        capture drop _fd_ystart
        gen double _fd_ystart = `modelexp' if `touse'
        if inlist("`model'", "aids", "quaids") {
            forvalues j = 1/`k' {
                local sj : word `j' of `shares'
                local pj : word `j' of `modelprices'
                quietly summarize `sj' if `touse', meanonly
                quietly replace _fd_ystart = _fd_ystart - r(mean) * `pj' if `touse'
            }
        }
        else {
            forvalues j = 1/`k' {
                local sj : word `j' of `shares'
                local pj : word `j' of `modelprices'
                quietly replace _fd_ystart = _fd_ystart - `sj' * `pj' if `touse'
            }
        }
        local ypowers "_fd_ystart"
        local startorder = cond("`model'" == "aids", 1, ///
            cond("`model'" == "quaids", 2, `order'))
        if `startorder' > 1 {
            forvalues h = 2/`startorder' {
                capture drop _fd_ystart`h'
                gen double _fd_ystart`h' = _fd_ystart^`h' if `touse'
                local ypowers "`ypowers' _fd_ystart`h'"
            }
        }
        forvalues i = 1/`neq' {
            local si : word `i' of `shares'
            quietly regress `si' `relprices' `ypowers' `demographics' `cfvar' if `touse'
            matrix `init'[1, colnumb(`init', "a`i'")] = _b[_cons]
            if inlist("`model'", "aids", "quaids") {
                matrix `init'[1, colnumb(`init', "b`i'")] = _b[_fd_ystart]
                if "`model'" == "quaids" ///
                    matrix `init'[1, colnumb(`init', "l`i'")] = _b[_fd_ystart2]
            }
            else {
                forvalues h = 1/`order' {
                    local yh = cond(`h' == 1, "_fd_ystart", "_fd_ystart`h'")
                    matrix `init'[1, colnumb(`init', "b`i'_`h'")] = _b[`yh']
                }
            }
            forvalues j = 1/`neq' {
                local graw`i'_`j' = _b[_fd_relp`j']
            }
            if `nz' > 0 {
                forvalues d = 1/`nz' {
                    local zd : word `d' of `demographics'
                    matrix `init'[1, colnumb(`init', "t`i'_`d'")] = _b[`zd']
                }
            }
            if "`cfvar'" != "" ///
                matrix `init'[1, colnumb(`init', "r`i'")] = _b[`cfvar']
        }
        forvalues i = 1/`neq' {
            forvalues j = `i'/`neq' {
                local gij = (`graw`i'_`j'' + `graw`j'_`i'') / 2
                matrix `init'[1, colnumb(`init', "g`i'_`j'")] = `gij'
            }
        }
    }
    else {
        tempname supplied
        matrix `supplied' = `from'
        if colsof(`supplied') == `npar' {
            matrix `init' = `supplied'
        }
        else {
            local sourceeqs : coleq `supplied'
            local hasname = 0
            foreach sourceeq of local sourceeqs {
                if "`sourceeq'" != "_" local hasname = 1
            }
            if !`hasname' {
                di as error "from() has the wrong number of columns and no parameter equation names"
                exit 503
            }
            matrix `init' = J(1, `npar', 0)
            matrix colnames `init' = `pnames'
            local target = 0
            foreach ph of local pnames {
                local ++target
                local source : list posof "`ph'" in sourceeqs
                if `source' > 0 matrix `init'[1,`target'] = `supplied'[1,`source']
            }
        }
    }

    global FD_MODEL "`model'"
    global FD_K `k'
    global FD_ORDER `order'
    global FD_SHARES "`shares'"
    global FD_LNP "`modelprices'"
    global FD_EXP "`modelexp'"
    global FD_ZVARS "`demographics'"
    global FD_PHI "`philist'"
    global FD_PDF "`pdflist'"
    global FD_CF "`cfvar'"
    global FD_RAWLNP "`prices'"
    global FD_RAWEXP "`expenditure'"
    global FD_XMEAN `xmean'
    global FD_PRECOMMIT = ("`precommitment'" != "")
    global FD_CSCALE "`cscales'"
    global FD_SY = ("`selection'" == "sy")
    global FD_SYACTIVE "`syactive'"
    global FD_PRED 0
    global FD_EASIY ""

    local depneq ""
    forvalues i = 1/`neq' {
        local si : word `i' of `shares'
        local depneq "`depneq' `si'"
    }
    if "`estimator'" == "gmm" {
        local stepopt = cond(`gmmsteps' == 1, "onestep", "twostep")
        local modeliv ""
        local niv : word count `instruments'
        if `niv' > 0 {
            forvalues m = 1/`niv' {
                local ivm : word `m' of `instruments'
                quietly summarize `ivm' if `touse'
                if missing(r(sd)) | r(sd) <= 0 {
                    di as error "instrument `ivm' has no variation"
                    exit 459
                }
                local ivmean = r(mean)
                local ivsd = r(sd)
                capture drop _fd_ziv`m'
                gen double _fd_ziv`m' = (`ivm' - `ivmean') / `ivsd' if `touse'
                local modeliv "`modeliv' _fd_ziv`m'"
            }
        }
        local zinst "`modelprices' `demographics' `selectvars' `modeliv'"
        local instpower = cond("`model'" == "easi", `order', cond("`model'" == "quaids", 2, 1))
        if "`endogeneity'" == "none" {
            local zinst "`zinst' `modelexp'"
            if `instpower' > 1 {
                forvalues h = 2/`instpower' {
                    capture drop _fd_expinst`h'
                    gen double _fd_expinst`h' = `modelexp'^`h' if `touse'
                    local zinst "`zinst' _fd_expinst`h'"
                }
            }
        }
        else if `instpower' > 1 {
            forvalues m = 1/`niv' {
                local ivm "_fd_ziv`m'"
                forvalues h = 2/`instpower' {
                    capture drop _fd_iv`m'_`h'
                    gen double _fd_iv`m'_`h' = `ivm'^`h' if `touse'
                    local zinst "`zinst' _fd_iv`m'_`h'"
                }
            }
        }
        if "`precommitment'" != "" {
            if "`endogeneity'" == "none" {
                capture drop _fd_preinv
                gen double _fd_preinv = exp(-`modelexp') if `touse'
                local zinst "`zinst' _fd_preinv"
                forvalues j = 1/`k' {
                    local mpj : word `j' of `modelprices'
                    capture drop _fd_prepx`j'
                    gen double _fd_prepx`j' = `mpj' * _fd_preinv if `touse'
                    local zinst "`zinst' _fd_prepx`j'"
                }
            }
            else {
                forvalues m = 1/`niv' {
                    local ivm "_fd_ziv`m'"
                    forvalues j = 1/`k' {
                        local mpj : word `j' of `modelprices'
                        capture drop _fd_preiv`m'_`j'
                        gen double _fd_preiv`m'_`j' = `ivm' * `mpj' if `touse'
                        local zinst "`zinst' _fd_preiv`m'_`j'"
                    }
                }
            }
        }
        if "`model'" == "easi" {
            local linearopts ""
            if "`demographics'" != "" local linearopts "`linearopts' demographics(`demographics')"
            if "`cfvar'" != "" local linearopts "`linearopts' cf(`cfvar')"
            if "`philist'" != "" local linearopts "`linearopts' phi(`philist') pdf(`pdflist') syactive(`syactive')"
            if "`cluster'" != "" local linearopts "`linearopts' cluster(`cluster')"
            tempname easistart
            if "`from'" == "" & "`precommitment'" == "" {
                quietly fooddem_easi_linear if `touse', shares(`shares') lnp(`modelprices') ///
                    expenditure(`modelexp') order(`order') instruments(`zinst') ///
                    pnames(`pnames') steps(1) `linearopts'
                matrix `easistart' = e(b)
            }
            else matrix `easistart' = `init'
            local geasiopts ""
            if "`precommitment'" != "" {
                local geasiopts "rawlnp(`prices') rawexp(`expenditure') cscales(`cscales') xmean(`xmean')"
            }
            quietly fooddem_easi_gmm if `touse', shares(`shares') lnp(`modelprices') ///
                expenditure(`modelexp') order(`order') instruments(`zinst') ///
                pnames(`pnames') initial(`easistart') steps(`gmmsteps') ///
                iterate(`iterate') tolerance(`tolerance') curvature(`curvature') ///
                `linearopts' `geasiopts'
        }
        else {
            quietly gmm fooddem_gmm if `touse', nequations(`neq') parameters(`pnames') ///
                instruments(`zinst') from(`init') `stepopt' winitial(identity) ///
                `vceopt' iterate(`iterate') tolerance(`tolerance') quickderivatives
        }
    }
    else {
        local initlist ""
        forvalues h = 1/`npar' {
            local ph : word `h' of `pnames'
            local iv = `init'[1,`h']
            local initlist "`initlist' `ph' `iv'"
        }
        quietly nlsur fooddem @ `depneq' if `touse', parameters(`pnames') ///
            nequations(`neq') initial(`initlist') `vceopt' iterate(`iterate')
    }

    ereturn local fooddem_model "`model'"
    ereturn local fooddem_estimator "`estimator'"
    ereturn local fooddem_shares "`shares'"
    ereturn local fooddem_prices "`prices'"
    ereturn local fooddem_modelprices "`modelprices'"
    ereturn local fooddem_expenditure "`expenditure'"
    ereturn local fooddem_modelexpenditure "`modelexp'"
    ereturn local fooddem_demographics "`demographics'"
    ereturn local fooddem_quantities "`quantities'"
    ereturn local fooddem_selection "`selection'"
    ereturn local fooddem_selectvars "`selectvars'"
    ereturn local fooddem_selcovars "`selcovars'"
    ereturn local fooddem_phi "`philist'"
    ereturn local fooddem_pdf "`pdflist'"
    ereturn local fooddem_syactive "`syactive'"
    ereturn local fooddem_cf "`cfvar'"
    ereturn local fooddem_endogeneity "`endogeneity'"
    ereturn local fooddem_instruments "`instruments'"
    ereturn local fooddem_cluster "`cluster'"
    ereturn local fooddem_precommitment "`precommitment'"
    ereturn local fooddem_curvature "`curvature'"
    ereturn local fooddem_cscales "`cscales'"
    ereturn local fooddem_pnames "`pnames'"
    ereturn scalar fooddem_goods = `k'
    ereturn scalar fooddem_order = `order'
    ereturn scalar fooddem_npar = `npar'
    ereturn scalar fooddem_gmmsteps = `gmmsteps'
    ereturn scalar fooddem_firststage_F = `firstF'
    ereturn scalar fooddem_firststage_p = `firstP'
    ereturn scalar fooddem_firststage_r2 = `firstR2'
    ereturn scalar fooddem_xmean = `xmean'
    forvalues j = 1/`k' {
        ereturn scalar fooddem_pmean`j' = `pmean`j''
    }
    if "`selection'" == "sy" ereturn matrix fooddem_syb = `syb'
    ereturn local predict "fooddem_p"
    ereturn local cmd "fooddem"
end
