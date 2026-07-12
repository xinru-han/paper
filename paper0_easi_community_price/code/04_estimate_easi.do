version 17
do "$EASI_CODE/00_config.do"
use "$EASI_DATA/easi_analysis_ready.dta", clear

* Shonkwiler-Yen two-step correction. Probabilities are retained in the demand
* system; no zero quantity is logged and all six equations share the same sample.
forvalues g = 1/6 {
    gen byte d`g' = q`g' > 0
    quietly summarize d`g'
    if r(mean) == 0 | r(mean) == 1 {
        di as error "Demand group `g' has no extensive-margin variation."
        exit 459
    }
    quietly probit d`g' ln_foodexp lnp1-lnp6 $EASI_Z, vce(cluster village_id)
    predict double xb`g', xb
    gen double phi`g' = normal(xb`g')
    gen double pdf`g' = normalden(xb`g')
    drop xb`g'
}

easi_sy3sls, shares(s1-s6) lnp(lnp1-lnp6) expenditure(ln_foodexp) ///
    zvars($EASI_Z) phi(phi1-phi6) pdf(pdf1-pdf6) powers(2) maxiter(100) tol(1e-6)
estimates save "$EASI_OUT/easi_sy3sls.ster", replace

predict double s1_hat, equation(s1)
predict double s2_hat, equation(s2)
predict double s3_hat, equation(s3)
predict double s4_hat, equation(s4)
predict double s5_hat, equation(s5)
gen double s6_hat = 1 - s1_hat - s2_hat - s3_hat - s4_hat - s5_hat
egen double fitted_share_sum = rowtotal(s1_hat-s6_hat)
assert abs(fitted_share_sum - 1) < 1e-10

preserve
    keep household_id s1_hat-s6_hat fitted_share_sum
    export delimited using "$EASI_OUT/fitted_share_diagnostics.csv", replace
restore
save "$EASI_OUT/easi_estimation_sample.dta", replace
