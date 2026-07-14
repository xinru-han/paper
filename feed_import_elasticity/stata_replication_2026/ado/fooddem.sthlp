{smcl}
{* *! version 1.3.0 14jul2026}{...}
{vieweralsosee "gmm" "help gmm"}{...}
{vieweralsosee "nlsur" "help nlsur"}{...}
{title:Title}

{phang}
{bf:fooddem} {hline 2} constrained arbitrary-good AIDS, QUAIDS, EASI, and GEASI demand systems

{title:Syntax}

{p 8 16 2}
{cmd:fooddem} {ifin}{cmd:,}
{opt model(aids|quaids|easi)}
{opt shares(varlist)}
{opt prices(varlist)}
{opt expenditure(varname)}
[{it:options}]

{synoptset 28 tabbed}{...}
{synopthdr}
{synoptline}
{synopt:{opt estimator(gmm|nlsur)}}estimator; default is {cmd:gmm}{p_end}
{synopt:{opt order(#)}}EASI polynomial order; 1 <= order < number of goods{p_end}
{synopt:{opt demographics(varlist)}}demographic demand shifters{p_end}
{synopt:{opt quantities(varlist)}}one nonnegative quantity per good{p_end}
{synopt:{opt selection(none|sy)}}Shonkwiler-Yen participation correction{p_end}
{synopt:{opt selectvars(varlist)}}additional participation and GMM conditioning variables{p_end}
{synopt:{opt endogeneity(none|iv|cf)}}expenditure treatment{p_end}
{synopt:{opt instruments(varlist)}}excluded expenditure instruments{p_end}
{synopt:{opt cluster(varname)}}clustered VCE{p_end}
{synopt:{opt precommitment}}estimate GEASI precommitted quantities with EASI{p_end}
{synopt:{opt from(matname)}}starting parameter row vector in internal order{p_end}
{synopt:{opt gmmsteps(1|2)}}one-step or two-step GMM; default is 2{p_end}
{synopt:{opt iterate(#)}}maximum optimizer iterations{p_end}
{synopt:{opt tolerance(#)}}GMM convergence tolerance{p_end}
{synopt:{opt curvature(none|local|global)}}EASI-GMM curvature parameterization; default is {cmd:none}{p_end}
{synoptline}

{title:Data requirements}

{pstd}
{opt shares()} and {opt prices()} must contain the same number of variables,
at least three. Prices must be logarithms of positive common-market prices.
{opt expenditure()} must be log total expenditure for the modeled group.
The share order, price order, and optional quantity order must be identical.

{pstd}
The command estimates K-1 equations and recovers good K by adding-up. The latent
demand system imposes adding-up, price homogeneity, and Slutsky symmetry by
construction. In AIDS and QUAIDS, demographic and control-function coefficients
translate both the share intercepts and the translog price index. EASI order must
be smaller than K.

{pstd}
Uncommitted EASI uses exact implicit utility
{it:y}={it:x}-{it:w}'{it:p}+0.5{it:p}'{it:A}{it:p}. A constrained linear GMM
solution supplies the ordinary-EASI start, after which a nonlinear Mata GMM
solver estimates the exact moments and robust or clustered one-step or two-step
covariance. The same solver handles GEASI's precommitted quantities and altered
discretionary expenditure. The test suite verifies ordinary EASI coefficients
against numerical {cmd:gmm} and GEASI moments against the generic evaluator.

{title:Zeros and endogeneity}

{pstd}
{cmd:selection(sy)} requires {opt quantities()}. A probit is estimated for a
good when both participation outcomes are sufficiently represented. When the
positive rate is at least .98, probability is set to one and the density term
to zero; an unidentified selection coefficient is not added. A positive rate
at most .02 produces an error. For active equations, prediction recomputes the
participation probability under every price, expenditure, or demographic
counterfactual, so reported elasticities include the extensive margin. The
analytic structural VCE conditions on the estimated probit coefficients; use a
sampling-cluster bootstrap when participation censoring is material.

{pstd}
{cmd:endogeneity(iv)} instruments log expenditure in GMM moments.
{cmd:endogeneity(cf)} includes a first-stage residual and is required for an
endogeneity test with NLSUR. Excluded instruments are standardized internally
before nonlinear powers are formed, but first-stage diagnostics use their
original scale. When {opt cluster()} is supplied, participation, first-stage,
and structural inference use that cluster. IV-GMM is the preferred EASI
estimator when implicit utility and group expenditure are endogenous; NLSUR
with a control function is provided as a conditional robustness estimator.

{title:Stored results}

{pstd}
In addition to standard {cmd:gmm} or {cmd:nlsur} results, {cmd:fooddem} stores:

{synoptset 32 tabbed}{...}
{synopt:{cmd:e(fooddem_model)}}functional form{p_end}
{synopt:{cmd:e(fooddem_goods)}}number of goods{p_end}
{synopt:{cmd:e(fooddem_order)}}EASI order{p_end}
{synopt:{cmd:e(fooddem_npar)}}number of free parameters{p_end}
{synopt:{cmd:e(fooddem_gmmsteps)}}requested GMM steps{p_end}
{synopt:{cmd:e(fooddem_firststage_F)}}excluded-instrument first-stage F{p_end}
{synopt:{cmd:e(fooddem_firststage_p)}}first-stage joint p-value{p_end}
{synopt:{cmd:e(fooddem_firststage_r2)}}first-stage R-squared{p_end}
{synopt:{cmd:e(fooddem_syactive)}}good-specific SY activation indicators{p_end}
{synopt:{cmd:e(fooddem_cluster)}}sampling-cluster variable, if supplied{p_end}
{synopt:{cmd:e(fooddem_curvature)}}curvature parameterization{p_end}

{title:Postestimation and companion commands}

{phang}{cmd:fooddem_p newshare1 ... newshareK [, latent holdselection]} predicts all K unconditional, intensive-margin, or latent shares.{p_end}
{phang}{cmd:fooddem_select using filename, ...} compares AIDS, QUAIDS, and EASI orders.{p_end}
{phang}{cmd:fooddem_tests using filename} exports nested, demographic, endogeneity, SY, GEASI, and overidentification tests.{p_end}
{phang}{cmd:fooddem_firststage using filename} exports joint and instrument-conditional excluded-instrument F tests and partial R-squared values.{p_end}
{phang}{cmd:fooddem_elasticities using filename [, margin(unconditional|intensive|latent) minshare(#) sample(varname)]} exports expenditure, Marshallian, and Hicksian elasticities on a common interior support plus quantity-weighted and tail-trimmed aggregates.{p_end}
{phang}{cmd:fooddem_regularity using filename [, margin(unconditional|intensive|latent)]} checks positivity, monotonicity, curvature, adding-up, and numerical Slutsky symmetry; latent is the default theory margin.{p_end}
{phang}{cmd:fooddem_curvature using filename} projects the local latent Slutsky matrix to the nearest symmetric negative-semidefinite matrix while preserving adding-up.{p_end}
{phang}{cmd:fooddem_reference using filename [, sample(varname)]} exports sample-average EASI elasticities with delta-method standard errors, p-values, and confidence intervals.{p_end}
{phang}{cmd:fooddem_demographics using filename} exports demographic elasticities or binary discrete effects.{p_end}
{phang}{cmd:fooddem_income using filename, income() values() [cluster() minshare(#)]} computes two-stage income and third-stage quality elasticities on the common interior support; PPML is the default value equation.{p_end}
{phang}{cmd:fooddem_uvprice, ...} recovers common-market prices from unit values or expenditures and quantities.{p_end}
{phang}{cmd:fooddem_precommitments using filename} transforms GEASI latent parameters into precommitted quantities with delta-method standard errors.{p_end}
{phang}{cmd:fooddem_export using filename} exports coefficients and standard errors.{p_end}

{title:Examples}

{phang2}{cmd:. fooddem, model(quaids) shares(w1 w2 w3 w4) prices(lnp1 lnp2 lnp3 lnp4) expenditure(lnx) demographics(hhsize children) endogeneity(iv) instruments(lnincome invincome) cluster(village)}{p_end}

{phang2}{cmd:. fooddem, model(easi) order(3) shares(w1 w2 w3 w4 w5) prices(lnp1 lnp2 lnp3 lnp4 lnp5) expenditure(lnx) estimator(nlsur) endogeneity(cf) instruments(lnincome) quantities(q1 q2 q3 q4 q5) selection(sy)}{p_end}

{phang2}{cmd:. fooddem_elasticities using elasticities.csv, replace}{p_end}

{phang2}{cmd:. fooddem, model(easi) order(1) shares(w1 w2 w3) prices(lnp1 lnp2 lnp3) expenditure(lnx) estimator(gmm) curvature(local)}{p_end}

{phang2}{cmd:. fooddem_reference using reference_elasticities.csv, replace}{p_end}
