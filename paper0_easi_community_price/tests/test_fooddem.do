version 17
clear all
set more off
set seed 12072026
adopath ++ "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/ado"

* Three-good QUAIDS DGP and model-selection interface.
set obs 400
gen long id = _n
gen double lp1 = rnormal(0, .3)
gen double lp2 = rnormal(0, .3)
gen double lp3 = rnormal(0, .3)
gen double lx = rnormal(5, .35)
gen double z = rnormal()
gen double yc = lx - 5 - (.40 * lp1 + .35 * lp2 + .25 * lp3)
gen double w1 = .40 + .04 * yc + .015 * yc^2 + .025 * (lp1 - lp3) ///
    - .010 * (lp2 - lp3) + .01 * z + rnormal(0, .004)
gen double w2 = .35 - .01 * yc - .010 * yc^2 - .010 * (lp1 - lp3) ///
    + .025 * (lp2 - lp3) - .005 * z + rnormal(0, .004)
gen double w3 = 1 - w1 - w2
assert inrange(w1, 0, 1) & inrange(w2, 0, 1) & inrange(w3, 0, 1)

fooddem_select using "/tmp/fooddem_test_selection.csv", shares(w1 w2 w3) ///
    prices(lp1 lp2 lp3) expenditure(lx) estimator(gmm) maxorder(2) ///
    demographics(z) gmmsteps(1) iterate(40) tolerance(1e-5) replace
local preferred "`r(preferred_estimate)'"
local preferred_easi_order = r(preferred_easi_order)
assert "`preferred'" != ""
assert `preferred_easi_order' >= 1 & `preferred_easi_order' < 3
estimates restore `preferred'
assert e(fooddem_goods) == 3
assert e(fooddem_npar) == colsof(e(b))
fooddem_p pw1 pw2 pw3
egen double psum = rowtotal(pw1 pw2 pw3)
assert abs(psum - 1) < 1e-10 if e(sample)
fooddem_export using "/tmp/fooddem_test_parameters.csv", label("quaids_test") replace
fooddem_elasticities using "/tmp/fooddem_test_elasticities.csv", replace
fooddem_regularity using "/tmp/fooddem_test_regularity.csv", replace

* The same general evaluator must work under NLSUR.
fooddem, model(aids) shares(w1 w2 w3) prices(lp1 lp2 lp3) ///
    expenditure(lx) estimator(nlsur) demographics(z) iterate(60)
assert e(fooddem_goods) == 3
assert colsof(e(b)) == e(fooddem_npar)
fooddem_regularity using "/tmp/fooddem_test_nlsur_regularity.csv", replace
assert r(slutsky_symmetry_error) < 1e-6

* IV scaling and first-stage diagnostics.
gen double income_iv = rnormal()
replace lx = 5 + .5 * income_iv + .2 * rnormal()
fooddem, model(aids) shares(w1 w2 w3) prices(lp1 lp2 lp3) ///
    expenditure(lx) estimator(gmm) demographics(z) endogeneity(iv) ///
    instruments(income_iv) gmmsteps(1) iterate(40) tolerance(1e-5)
assert e(fooddem_firststage_F) > 10
assert !missing(e(J))
fooddem_firststage using "/tmp/fooddem_test_firststage.csv", replace
assert r(joint_F) > 10
assert r(joint_partial_R2) > 0
assert "`e(fooddem_model)'" == "aids"

* Demographic translating and the control-function residual must enter both
* shares and the AIDS price index, preserving conditional Slutsky symmetry.
fooddem, model(aids) shares(w1 w2 w3) prices(lp1 lp2 lp3) ///
    expenditure(lx) estimator(nlsur) demographics(z) endogeneity(cf) ///
    instruments(income_iv) iterate(60)
fooddem_regularity using "/tmp/fooddem_test_nlsur_cf_regularity.csv", replace
assert r(slutsky_symmetry_error) < 1e-6

* Active Shonkwiler-Yen correction for one good, with universal-consumption
* bypasses for the other goods.
gen double select_z = rnormal()
gen byte d1 = select_z + rnormal() > 0
gen double q1 = d1 * exp(rnormal())
gen double q2 = exp(rnormal())
gen double q3 = exp(rnormal())
replace w1 = d1 * (.28 + .015 * (lp1 - lp3))
replace w2 = .32 + .01 * (lp2 - lp3)
replace w3 = 1 - w1 - w2
fooddem, model(aids) shares(w1 w2 w3) prices(lp1 lp2 lp3) ///
    expenditure(lx) estimator(gmm) quantities(q1 q2 q3) selection(sy) ///
    selectvars(select_z) gmmsteps(1) iterate(40) tolerance(1e-5)
local syactive "`e(fooddem_syactive)'"
local sy1 : word 1 of `syactive'
local sy2 : word 2 of `syactive'
assert `sy1' == 1
assert `sy2' == 0
gen double sy_select_bak = select_z
gen double sy_phi_bak = _fd_phi1
replace select_z = select_z + .2
fooddem_p syc1 syc2 syc3
count if abs(_fd_phi1 - sy_phi_bak) > 1e-10 & e(sample)
assert r(N) > 0
replace select_z = sy_select_bak

* Exact EASI GMM must place active SY density terms correctly.
fooddem, model(easi) order(1) shares(w1 w2 w3) prices(lp1 lp2 lp3) ///
    expenditure(lx) estimator(gmm) demographics(z) quantities(q1 q2 q3) ///
    selection(sy) selectvars(select_z) gmmsteps(1)
assert e(converged) == 1
local easisy "`e(fooddem_syactive)'"
local easisy1 : word 1 of `easisy'
local easisy2 : word 2 of `easisy'
assert `easisy1' == 1 & `easisy2' == 0
fooddem_p sw1 sw2 sw3
egen double ssum = rowtotal(sw1 sw2 sw3)
assert abs(ssum - 1) < 1e-10 if e(sample)

* Mata one-step EASI GMM must equal Stata's generic numerical GMM for the same
* exact moments, including 0.5*p'A*p and an active SY density term.
tempname mata_b numeric_b maxdiff
matrix `mata_b' = e(b)
local mata_pnames "`e(fooddem_pnames)'"
gen byte mata_sample = e(sample)
quietly gmm fooddem_gmm if mata_sample, nequations(2) ///
    parameters(`mata_pnames') ///
    instruments(_fd_lnp1 _fd_lnp2 _fd_lnp3 z select_z _fd_lnx) ///
    from(`mata_b') onestep winitial(identity) vce(robust) ///
    iterate(30) tolerance(1e-8) quickderivatives
matrix `numeric_b' = e(b)
mata: st_numscalar("`maxdiff'", max(abs(st_matrix("`mata_b'") :- st_matrix("`numeric_b'"))))
assert scalar(`maxdiff') < 1e-7

* Arbitrary five-good EASI, prediction adding-up, GEASI parameter extension,
* and two/three-stage income-quality elasticities with zeros retained by PPML.
clear
set obs 450
gen long id = _n
forvalues j = 1/5 {
    gen double lp`j' = rnormal(0, .25)
}
gen double lx = rnormal(5, .3)
gen double z = rnormal()
gen int village = ceil(_n / 10)
gen double ey = lx - 5 - .2 * (lp1 + lp2 + lp3 + lp4 + lp5)
gen double w1 = .20 + .025 * ey + .008 * ey^2 + .012 * (lp1 - lp5) + .006 * z
gen double w2 = .19 - .010 * ey + .004 * ey^2 + .010 * (lp2 - lp5) - .004 * z
gen double w3 = .18 + .008 * ey - .003 * ey^2 + .011 * (lp3 - lp5) + .002 * z
gen double w4 = .17 - .006 * ey + .002 * ey^2 + .009 * (lp4 - lp5) - .003 * z
gen double w5 = 1 - w1 - w2 - w3 - w4
assert inrange(w1, 0, 1) & inrange(w2, 0, 1) & inrange(w3, 0, 1) ///
    & inrange(w4, 0, 1) & inrange(w5, 0, 1)

fooddem, model(easi) order(2) shares(w1 w2 w3 w4 w5) ///
    prices(lp1 lp2 lp3 lp4 lp5) expenditure(lx) estimator(gmm) ///
    demographics(z) cluster(village) gmmsteps(2) iterate(50) tolerance(1e-5)
assert e(converged) == 1
assert e(fooddem_goods) == 5
assert e(fooddem_order) == 2
assert e(fooddem_npar) == colsof(e(b))
fooddem_p fw1 fw2 fw3 fw4 fw5
egen double fsum = rowtotal(fw1 fw2 fw3 fw4 fw5)
assert abs(fsum - 1) < 1e-10 if e(sample)
estimates store fd_five_easi

tempname eb cb gb
matrix `eb' = e(b)
matrix `cb' = J(1, 5, 0)
matrix colnames `cb' = c1 c2 c3 c4 c5
matrix `gb' = `eb', `cb'
fooddem, model(easi) order(2) precommitment shares(w1 w2 w3 w4 w5) ///
    prices(lp1 lp2 lp3 lp4 lp5) expenditure(lx) estimator(gmm) ///
    demographics(z) gmmsteps(1) from(`gb') iterate(30) tolerance(1e-5)
assert e(fooddem_npar) == colsof(e(b))
fooddem_p gw1 gw2 gw3 gw4 gw5
egen double gsum = rowtotal(gw1 gw2 gw3 gw4 gw5)
assert abs(gsum - 1) < 1e-10 if e(sample)
fooddem_precommitments using "/tmp/fooddem_test_precommitments.csv", replace

* The Mata GEASI objective must equal the generic evaluator's identity-weight
* moments at the same coefficients. Latent c parameters can be weakly identified,
* so optimizer-specific coefficient differences are not a valid equivalence test.
tempname geasi_mata_b geasi_manualJ
matrix `geasi_mata_b' = e(b)
local geasi_mataJ = e(J)
assert e(converged) == 1
gen byte geasi_sample = e(sample)
local geasi_errors ""
forvalues i = 1/4 {
    tempvar ge`i'
    gen double `ge`i'' = .
    local geasi_errors "`geasi_errors' `ge`i''"
}
global FD_PRED 0
global FD_EASIY ""
quietly fooddem_gmm `geasi_errors' if geasi_sample, at(`geasi_mata_b')
mata:
idx = selectindex(st_data(., "geasi_sample") :== 1)
Z = J(rows(idx), 1, 1), st_data(idx, ("_fd_lnp1", "_fd_lnp2", "_fd_lnp3", "_fd_lnp4", "_fd_lnp5", "z", "_fd_lnx", "_fd_expinst2", "_fd_preinv", "_fd_prepx1", "_fd_prepx2", "_fd_prepx3", "_fd_prepx4", "_fd_prepx5"))
E = st_data(idx, tokens("`geasi_errors'"))
g = (quadcross(Z,E[,1]) \ quadcross(Z,E[,2]) \ quadcross(Z,E[,3]) \ quadcross(Z,E[,4])) / rows(idx)
st_numscalar("`geasi_manualJ'", rows(idx) * quadcross(g,g))
end
assert abs(scalar(`geasi_manualJ') - `geasi_mataJ') < 1e-8

estimates restore fd_five_easi
gen double income = exp(10 + .5 * z + rnormal(0, .25))
forvalues j = 1/5 {
    gen double value`j' = exp(1 + .25 * ln(income) + .1 * z + rnormal(0, .2))
    replace value`j' = 0 if runiform() < .12
}
fooddem_income using "/tmp/fooddem_test_income.dta", income(income) ///
    values(value1 value2 value3 value4 value5) controls(z) id(id) ///
    valuemethod(ppml) cluster(village) replace
preserve
    use "/tmp/fooddem_test_income.dta", clear
    assert inrange(good, 1, 5)
    assert value_method == "ppml"
    assert !missing(income_quantity_elasticity)
    assert !missing(income_value_elasticity)
restore

* Common-market unit-value recovery must be constant within market and positive.
clear
set obs 500
gen long market = ceil(_n / 10)
gen double demo = rnormal()
gen double quantity = exp(rnormal())
bysort market: gen double common_price = exp(rnormal(.8, .15)) if _n == 1
bysort market: replace common_price = common_price[1]
gen double unit_value = common_price * quantity^.12 * exp(.08 * demo + rnormal(0, .03))
fooddem_uvprice, unitvalues(unit_value) quantities(quantity) market(market) ///
    demographics(demo) generate(uvp) source(uvps) method(deaton) ///
    mincell(3) trim(0) complete audit("/tmp/fooddem_test_uv.csv") replace
assert uvp1 > 0
bysort market: assert abs(uvp1 - uvp1[1]) < 1e-12

display as result "fooddem test suite passed"
