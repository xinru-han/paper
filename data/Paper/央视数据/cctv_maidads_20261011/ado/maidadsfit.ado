program define maidadsfit, eclass
    version 17
    syntax, Expenditure(varname numeric) Prices(varlist numeric) Shares(varlist numeric) ///
        Model(string) OUTdir(string) [STARTS(integer 3) ITERate(integer 400) WEIGHT(varname numeric)]
    local k : word count `prices'
    local kw : word count `shares'
    if `k' != `kw' | `k' < 2 {
        di as error "prices() and shares() must have the same K >= 2"
        exit 198
    }
    if !inlist("`model'", "aidads", "maidads") {
        di as error "model() must be aidads or maidads"
        exit 198
    }
    capture mkdir "`outdir'"
    quietly findfile maidads_core.mata
    local here "`r(fn)'"
    quietly do "`here'"
    mata: MD_load("`expenditure'", "`prices'", "`shares'", "`weight'")
    mata: MD_fit("`model'", "`outdir'", `starts', `iterate')
    forvalues j=1/`k' {
        quietly generate double fitw`j' = .
        quietly generate double fitq`j' = .
        quietly generate double eta`j' = .
    }
    quietly generate double fitutility = .
    mata: MD_store()
    export delimited using "`outdir'/predictions.csv", replace
    local bnames
    forvalues j=1/`=`k'-1' {
        local bnames `bnames' logalpha`j'
    }
    forvalues j=1/`=`k'-1' {
        local bnames `bnames' logbeta`j'
    }
    forvalues j=1/`k' {
        local bnames `bnames' delta_scale`j'
    }
    if "`model'"=="maidads" {
        forvalues j=1/`k' {
            local bnames `bnames' tau_scale`j'
        }
        local bnames `bnames' omega
    }
    local bnames `bnames' kappa
    matrix colnames MD_b = `bnames'
    tempvar touse
    quietly generate byte `touse'=1
    ereturn post MD_b, esample(`touse') obs(`=_N')
    ereturn matrix alpha = MD_alpha
    ereturn matrix beta = MD_beta
    ereturn matrix delta = MD_delta
    ereturn matrix tau = MD_tau
    ereturn matrix training_scale = MD_scale
    ereturn scalar N = _N
    ereturn scalar k = `k'
    ereturn scalar mean_nll = scalar(MD_bestvalue)
    ereturn scalar projected_gradient = scalar(MD_bestscore)
    ereturn scalar converged = scalar(MD_converged)
    ereturn local model "`model'"
    ereturn local vce "none_point_only"
    ereturn local cmd "maidadsfit"
end
