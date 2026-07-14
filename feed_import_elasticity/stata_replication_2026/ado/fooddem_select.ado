*! AIDS/QUAIDS/EASI/GEASI model-selection diagnostics 1.0.0  12jul2026
program define fooddem_select, rclass
    version 17
    syntax using/ [if] [in], SHARES(varlist numeric min=3) PRICES(varlist numeric min=3) ///
        EXPenditure(varname numeric) [ESTimator(string) MAXOrder(integer 3) ///
        DEMographics(varlist numeric) QUANTities(varlist numeric) SELection(string) ///
        SELectvars(varlist numeric) ENDogeneity(string) INSTruments(varlist numeric) ///
        CLuster(varname) GMMsteps(integer 2) ITERate(integer 200) ///
        TOLerance(real 1e-6) GEASI REPLACE]
    if "`estimator'" == "" local estimator "gmm"
    local estimator = lower("`estimator'")
    local k : word count `shares'
    local neq = `k' - 1
    if `maxorder' >= `k' local maxorder = `k' - 1
    if `maxorder' < 1 local maxorder = 1
    local common "shares(`shares') prices(`prices') expenditure(`expenditure') estimator(`estimator')"
    local common "`common' gmmsteps(`gmmsteps') iterate(`iterate') tolerance(`tolerance')"
    if "`demographics'" != "" local common "`common' demographics(`demographics')"
    if "`quantities'" != "" local common "`common' quantities(`quantities')"
    if "`selection'" != "" local common "`common' selection(`selection')"
    if "`selectvars'" != "" local common "`common' selectvars(`selectvars')"
    if "`endogeneity'" != "" local common "`common' endogeneity(`endogeneity')"
    if "`instruments'" != "" local common "`common' instruments(`instruments')"
    if "`cluster'" != "" local common "`common' cluster(`cluster')"

    tempname mem
    tempfile results
    postfile `mem' str12 model int order byte gmm_steps int return_code ///
        double N parameters converged J J_df J_p ///
        rss aic bic Engel_order_p precommitment_p using `results', replace
    local models "aids quaids"
    forvalues h = 1/`maxorder' {
        local models "`models' easi`h'"
    }
    if "`geasi'" != "" {
        forvalues h = 1/`maxorder' {
            local models "`models' geasi`h'"
        }
    }

    foreach spec of local models {
        local preopt ""
        if substr("`spec'", 1, 4) == "easi" {
            local model "easi"
            local outputmodel "easi"
            local ord = real(substr("`spec'", 5, strlen("`spec'") - 4))
        }
        else if substr("`spec'", 1, 5) == "geasi" {
            local model "easi"
            local outputmodel "geasi"
            local ord = real(substr("`spec'", 6, strlen("`spec'") - 5))
            local preopt "precommitment"
        }
        else {
            local model "`spec'"
            local outputmodel "`spec'"
            local ord = cond("`model'" == "quaids", 2, 1)
        }
        local startopt ""
        if "`preopt'" != "" {
            capture estimates restore fd_easi`ord'
            if _rc {
                local rc = _rc
                post `mem' ("`outputmodel'") (`ord') (`gmmsteps') (`rc') ///
                    (.) (.) (0) (.) (.) (.) (.) (.) (.) (.) (.)
                continue
            }
            tempname warm czero
            matrix `warm' = e(b)
            matrix `czero' = J(1, `k', 0)
            local cn ""
            forvalues i = 1/`k' {
                local cn "`cn' c`i'"
            }
            matrix colnames `czero' = `cn'
            matrix `warm' = `warm', `czero'
            local startopt "from(`warm')"
        }
        noisily di as text "fooddem_select: estimating `outputmodel' order `ord' by `estimator'"
        capture quietly fooddem `if' `in', model(`model') order(`ord') ///
            `preopt' `startopt' `common'
        local rc = _rc
        if `rc' {
            noisily di as error "fooddem_select: `outputmodel' order `ord' failed with return code `rc'"
            post `mem' ("`outputmodel'") (`ord') (`gmmsteps') (`rc') ///
                (.) (.) (0) (.) (.) (.) (.) (.) (.) (.) (.)
            continue
        }
        local conv = cond(missing(e(converged)), 1, e(converged))
        local N = e(N)
        local kp = e(fooddem_npar)
        noisily di as result "fooddem_select: `outputmodel' order `ord' converged (N=" ///
            %9.0g `N' ", parameters=" %6.0g `kp' ")"
        local J = .
        local Jdf = .
        local Jp = .
        if "`estimator'" == "gmm" {
            local J = e(J)
            local Jdf = e(J_df)
            if `gmmsteps' == 2 & `Jdf' > 0 local Jp = chi2tail(`Jdf', `J')
        }
        local fitlist ""
        forvalues i = 1/`k' {
            tempvar f`i'
            local fitlist "`fitlist' `f`i''"
        }
        capture quietly fooddem_p `fitlist'
        local predict_rc = _rc
        if `predict_rc' {
            post `mem' ("`outputmodel'") (`ord') (`gmmsteps') (`predict_rc') ///
                (`N') (`kp') (0) (`J') (`Jdf') (`Jp') (.) (.) (.) (.) (.)
            continue
        }
        local sqlist ""
        forvalues i = 1/`neq' {
            local si : word `i' of `shares'
            local fi : word `i' of `fitlist'
            tempvar sq`i'
            gen double `sq`i'' = (`si' - `fi')^2 if e(sample)
            local sqlist "`sqlist' `sq`i''"
        }
        tempvar rssrow
        egen double `rssrow' = rowtotal(`sqlist') if e(sample)
        quietly summarize `rssrow', meanonly
        local rss = r(sum)
        local nres = `N' * `neq'
        local aic = `nres' * ln(`rss' / `nres') + 2 * `kp'
        local bic = `nres' * ln(`rss' / `nres') + ln(`nres') * `kp'

        local engelp = .
        if "`model'" == "quaids" {
            local tests ""
            forvalues i = 1/`neq' {
                local tests "`tests' [l`i']_cons"
            }
            quietly test `tests'
            local engelp = r(p)
        }
        if "`model'" == "easi" & `ord' > 1 {
            local tests ""
            forvalues i = 1/`neq' {
                local tests "`tests' [b`i'_`ord']_cons"
            }
            quietly test `tests'
            local engelp = r(p)
        }
        local prep = .
        if "`preopt'" != "" {
            local tests ""
            forvalues i = 1/`k' {
                local tests "`tests' [c`i']_cons"
            }
            quietly test `tests'
            local prep = r(p)
        }
        estimates store fd_`spec'
        post `mem' ("`outputmodel'") (`ord') (`gmmsteps') (0) (`N') (`kp') (`conv') (`J') (`Jdf') ///
            (`Jp') (`rss') (`aic') (`bic') (`engelp') (`prep')
    }
    postclose `mem'
    preserve
        use `results', clear
        gen double _raw_bic = cond(converged == 1, bic, .)
        egen double _min_raw_bic = min(_raw_bic)
        gen byte raw_bic_minimum = converged == 1 & bic == _min_raw_bic

        * Sequential nested tests choose the order inside each family. BIC is
        * then used only for the nonnested AIDS-family versus EASI comparison.
        local aidsfamily "aids"
        quietly summarize Engel_order_p if model == "quaids" & converged == 1, meanonly
        if r(N) > 0 & r(mean) < .05 local aidsfamily "quaids"
        local easiseq = 1
        local continueeasi = 1
        if `maxorder' > 1 {
            forvalues h = 2/`maxorder' {
                quietly summarize Engel_order_p if model == "easi" & ///
                    order == `h' & converged == 1, meanonly
                if `continueeasi' & r(N) > 0 & r(mean) < .05 local easiseq = `h'
                else local continueeasi = 0
            }
        }
        gen byte family_test_preferred = ///
            (model == "`aidsfamily'" | (model == "easi" & order == `easiseq')) ///
            & converged == 1
        gen double _overall_bic = cond(family_test_preferred, bic, .)
        egen double _min_overall = min(_overall_bic)
        gen byte bic_preferred = converged == 1 & bic == _min_overall
        gen byte easi_order_preferred = model == "easi" & ///
            order == `easiseq' & converged == 1
        quietly count if bic_preferred
        if r(N) == 0 {
            di as error "no candidate model converged"
            exit 430
        }
        quietly summarize order if bic_preferred, meanonly
        local bestorder = r(min)
        quietly levelsof model if bic_preferred, local(bestmodel) clean
        quietly summarize bic if bic_preferred, meanonly
        local bestbic = r(min)
        local bestestimate "fd_`bestmodel'"
        if "`bestmodel'" == "easi" local bestestimate "fd_easi`bestorder'"
        if "`bestmodel'" == "geasi" local bestestimate "fd_geasi`bestorder'"

        quietly count if easi_order_preferred
        if r(N) > 0 {
            quietly summarize order if easi_order_preferred, meanonly
            local besteasiorder = r(min)
            local besteasiestimate "fd_easi`besteasiorder'"
        }
        sort model order
        drop _raw_bic _min_raw_bic _overall_bic _min_overall
        if regexm(lower("`using'"), "[.]dta$") {
            if "`replace'" != "" save "`using'", replace
            else save "`using'"
        }
        else {
            if "`replace'" != "" export delimited using "`using'", replace
            else export delimited using "`using'"
        }
    restore
    return scalar preferred_order = `bestorder'
    return local preferred_model "`bestmodel'"
    return scalar preferred_bic = `bestbic'
    return local preferred_estimate "`bestestimate'"
    if "`besteasiorder'" != "" {
        return scalar preferred_easi_order = `besteasiorder'
        return local preferred_easi_estimate "`besteasiestimate'"
    }
end
