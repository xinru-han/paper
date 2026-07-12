*! Recover common-market prices from household unit values 1.0.0  12jul2026
program define fooddem_uvprice, rclass sortpreserve
    version 17
    syntax [if] [in], QUANTities(varlist numeric min=1) MARKET(varlist) GENerate(name) ///
        [UNITValues(varlist numeric) VALUES(varlist numeric) DEMographics(varlist numeric) ///
         METHOD(string) MINCell(integer 3) TRIM(real 1) FALLBACK1(varlist) ///
         FALLBACK2(varlist) FALLBACK3(varlist) ALLOWOverall COMPLETE ///
         SOURCE(name) AUDIT(string) REPLACE]

    if ("`unitvalues'" == "") == ("`values'" == "") {
        di as error "specify exactly one of unitvalues() or values()"
        exit 198
    }
    local method = lower("`method'")
    if "`method'" == "" local method "deaton"
    if !inlist("`method'", "deaton", "median") {
        di as error "method() must be deaton or median"
        exit 198
    }
    if `mincell' < 2 {
        di as error "mincell() must be at least 2"
        exit 198
    }
    if `trim' < 0 | `trim' >= 25 {
        di as error "trim() must be in [0,25)"
        exit 198
    }

    local k : word count `quantities'
    local inputs = cond("`unitvalues'" != "", "`unitvalues'", "`values'")
    local ki : word count `inputs'
    if `ki' != `k' {
        di as error "the price/expenditure input must contain one variable per quantity"
        exit 198
    }
    if "`source'" == "" local source "`generate'_source"
    marksample touse, novarlist
    markout `touse' `market', strok
    tempvar market_id market_tag
    egen long `market_id' = group(`market') if `touse'
    bysort `market_id': gen byte `market_tag' = _n == 1 if `touse'

    tempname qcoef mem
    matrix `qcoef' = J(1, `k', .)
    matrix colnames `qcoef' = q1
    if `k' > 1 {
        local cn ""
        forvalues g = 1/`k' {
            local cn "`cn' q`g'"
        }
        matrix colnames `qcoef' = `cn'
    }
    tempfile auditdata
    postfile `mem' int good str36 statistic double value using `auditdata', replace

    forvalues g = 1/`k' {
        local qi : word `g' of `quantities'
        local ii : word `g' of `inputs'
        local out `generate'`g'
        local src `source'`g'
        capture confirm new variable `out'
        if _rc {
            if "`replace'" == "" {
                di as error "variable `out' already exists; specify replace"
                exit 110
            }
            drop `out'
        }
        capture confirm new variable `src'
        if _rc {
            if "`replace'" == "" {
                di as error "variable `src' already exists; specify replace"
                exit 110
            }
            drop `src'
        }

        tempvar uv lnuv lnq ncell exactp
        if "`unitvalues'" != "" gen double `uv' = `ii' if `touse' & `ii' > 0 & `qi' > 0
        else gen double `uv' = `ii' / `qi' if `touse' & `ii' > 0 & `qi' > 0
        if `trim' > 0 {
            quietly _pctile `uv' if `touse' & `uv' > 0, p(`trim' `=100-`trim'')
            local low = r(r1)
            local high = r(r2)
            replace `uv' = . if `uv' < `low' | `uv' > `high'
            post `mem' (`g') ("unit_value_trim_low") (`low')
            post `mem' (`g') ("unit_value_trim_high") (`high')
        }
        gen double `lnuv' = ln(`uv') if `uv' > 0
        gen double `lnq' = ln(`qi') if `qi' > 0 & !missing(`lnuv')
        bysort `market_id': egen long `ncell' = count(`lnuv')

        if "`method'" == "median" {
            bysort `market_id': egen double `exactp' = median(`uv')
            replace `exactp' = . if `ncell' < `mincell'
            matrix `qcoef'[1,`g'] = 0
        }
        else {
            tempvar meanuv meanq duv dq logprice
            bysort `market_id': egen double `meanuv' = mean(`lnuv')
            bysort `market_id': egen double `meanq' = mean(`lnq')
            gen double `duv' = `lnuv' - `meanuv'
            gen double `dq' = `lnq' - `meanq'
            local devs ""
            local means ""
            foreach z of local demographics {
                tempvar mz dz
                bysort `market_id': egen double `mz' = mean(`z')
                gen double `dz' = `z' - `mz'
                local devs "`devs' `dz'"
                local means "`means' `mz'"
            }
            quietly regress `duv' `dq' `devs' if `touse' & `ncell' >= `mincell', ///
                nocons vce(cluster `market_id')
            matrix `qcoef'[1,`g'] = _b[`dq']
            gen double `logprice' = `meanuv' - _b[`dq'] * `meanq' if `touse'
            local d = 0
            foreach z of local demographics {
                local ++d
                local dz : word `d' of `devs'
                local mz : word `d' of `means'
                replace `logprice' = `logprice' - _b[`dz'] * `mz' if `touse'
            }
            gen double `exactp' = exp(`logprice') if `ncell' >= `mincell'
            post `mem' (`g') ("quantity_adjustment") (_b[`dq'])
            post `mem' (`g') ("within_regression_N") (e(N))
            post `mem' (`g') ("within_regression_r2") (e(r2))
        }
        gen double `out' = `exactp' if `touse'
        gen byte `src' = 1 if !missing(`out') & `touse'

        local level = 1
        foreach fb in fallback1 fallback2 fallback3 {
            local fbvars "``fb''"
            if "`fbvars'" != "" {
                local ++level
                tempvar fallback_id fallback_price
                egen long `fallback_id' = group(`fbvars') if `touse'
                bysort `fallback_id': egen double `fallback_price' = ///
                    median(cond(`market_tag' & !missing(`exactp'), `exactp', .))
                replace `out' = `fallback_price' if missing(`out') & `touse' & `fallback_price' > 0
                replace `src' = `level' if missing(`src') & !missing(`out') & `touse'
            }
        }
        if "`allowoverall'" != "" {
            local ++level
            quietly summarize `exactp' if `market_tag' & `exactp' > 0, detail
            local overall = r(p50)
            replace `out' = `overall' if missing(`out') & `touse' & `overall' > 0
            replace `src' = `level' if missing(`src') & !missing(`out') & `touse'
        }
        quietly count if `touse' & !missing(`exactp')
        post `mem' (`g') ("observations_exact_market") (r(N))
        quietly count if `touse' & missing(`out')
        post `mem' (`g') ("observations_unresolved") (r(N))
        if "`complete'" != "" & r(N) > 0 {
            di as error "good `g' has " r(N) " unresolved market prices"
            exit 459
        }
        label variable `out' "Common-market price recovered from unit value, good `g'"
        label variable `src' "Price-source level, good `g' (1=market, 2+=fallback)"
    }
    postclose `mem'

    if "`audit'" != "" {
        preserve
            use `auditdata', clear
            if regexm(lower("`audit'"), "[.]dta$") {
                if "`replace'" != "" save "`audit'", replace
                else save "`audit'"
            }
            else {
                if "`replace'" != "" export delimited using "`audit'", replace
                else export delimited using "`audit'"
            }
        restore
    }
    return scalar goods = `k'
    return local method "`method'"
    return matrix quantity_adjustment = `qcoef'
end
