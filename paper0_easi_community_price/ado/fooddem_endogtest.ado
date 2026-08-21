*! Expenditure-endogeneity diagnostics after fooddem 1.0.0  12jul2026
program define fooddem_endogtest, rclass
    version 17
    if "`e(fooddem_model)'" == "" {
        di as error "fooddem estimation results not found"
        exit 301
    }
    return scalar firststage_F = e(fooddem_firststage_F)
    return scalar firststage_p = e(fooddem_firststage_p)
    return scalar firststage_r2 = e(fooddem_firststage_r2)
    if "`e(fooddem_endogeneity)'" == "cf" {
        local neq = e(fooddem_goods) - 1
        local tests ""
        forvalues i = 1/`neq' {
            local tests "`tests' [r`i']_cons"
        }
        quietly test `tests'
        return scalar endogeneity_chi2 = r(chi2)
        return scalar endogeneity_df = r(df)
        return scalar endogeneity_p = r(p)
    }
    if "`e(fooddem_estimator)'" == "gmm" {
        return scalar overid_J = e(J)
        return scalar overid_df = e(J_df)
        return scalar overid_p = cond(e(fooddem_gmmsteps) == 2, ///
            chi2tail(e(J_df), e(J)), .)
        return scalar overid_is_Hansen = e(fooddem_gmmsteps) == 2
    }
    return list
end
