# CCTV conditional-food (M)AIDADS

## Scope

This implementation uses CCTV purchase-amount cells, not the rural household
survey and not physical kilogram demand. Every observed zero category share is
retained in a positive-budget cell. Predicted native (M)AIDADS demand is positive;
this cell-mean regression is not a micro corner-solution/participation model.
The quantity equivalent is `q_i = m*w_i/p_i`, with normalized external price
indices. It must not be described as an observed physical quantity.

## Native expenditure function

For any K >= 2:

```
s = logistic(u)
t = logistic(omega*u)
phi_i(u) = alpha_i*(1-s) + beta_i*s
gamma_i(u) = delta_i*(1-t) + tau_i*t
Q(u,p) = exp(u+kappa-sum_i phi_i*log(phi_i/p_i))
E(u,p) = sum_i p_i*gamma_i(u) + Q(u,p)
q_i(u,p) = gamma_i(u) + phi_i(u)*Q(u,p)/p_i
E(u,p) = m
```

Both alpha and beta are free positive simplex vectors. Unlike the saturated
provincial food/nonfood model, beta food coordinates are not all set to zero:
this system has only covered foods and no fabricated residual nonfood good.
MAIDADS has free nonnegative delta and tau endpoints, free omega and kappa.
AIDADS sets tau=delta and omega=0; alpha/beta remain free. No endpoint is fixed
at zero. Numerically estimated zero endpoints are admissible boundaries.

The functions and analytical responses match the native implementation in
`/root/data/Paper/省级食物消费/paper-AE/submission_0921/replication/code/estimate_demand.py`,
except for free beta and general K. Root bracketing searches [-50,50]. A final
grid of 0.25 utility units counts sign crossings, with derivative-bracketed
critical points inserted to resolve detectable paired roots between grid nodes.
Exact or numerically near-zero grid nodes are counted once, excluding adjacent
sign crossings that would duplicate the same root. Consecutive near-zero nodes
are flagged as an unresolved plateau rather than silently declared unique.
This remains a finite-grid diagnostic, not a proof excluding extrema whose
derivative changes are missed, unbracketed tangent roots or roots outside the
interval.

## Objective and estimation

Let H be the orthonormal K by K-1 Helmert contrast matrix. For all retained cells:

```
r_c = (w_observed_c-w_model_c)*H
Sigma = mean_c(r_c' r_c)
mean_nll = ((K-1)*(1+log(2*pi)) + logdet(Sigma))/2
```

The objective is concentrated Gaussian QML in budget shares. The provincial
physical-quantity-error objective cannot be carried across unchanged because
CCTV quantity recording is incomplete. Helmert contrasts make the objective
invariant to food-equation deletion and retain the adding-up constraint.
Cells receive equal weights in the baseline; this does not claim population
representativeness. `weight()` supports a separately labelled sensitivity.

Analytical raw-parameter gradients use implicit differentiation of E=m. A
preference-only numerical initialization optimizes alpha, beta and kappa with
zero commitment endpoints; all delta/tau coordinates and omega are then
released for the actual full-model estimation. This initialization is not a
restriction on the reported model. The zero-commitment initialization uses
the algebraically identical nested AIDADS evaluator to avoid computing
irrelevant endpoint/omega gradients, and is capped at 100 iterations. A
projected BFGS first-stage and Stata/Mata native BFGS log-endpoint polish are
followed by physical-coordinate projected-score checks. Multiple starts and
every candidate's objective, score, boundary coordinates and raw parameters
are saved. A nonconverged lower objective does not displace a stationary,
non-guard-binding candidate. A numerical guard includes endpoint upper 12 in
training quantity-scale units, alpha/beta logit +/-12, omega [.005,20], and
kappa +/-25. Binding numerical guards are not accepted as main-fit convergence.
The lower bound delta/tau=0 is an economic boundary, not a numerical guard.
The logit representation searches strictly positive alpha/beta coordinates.
An alpha or beta coordinate driven toward zero can reflect a legitimate
nonnegative-simplex economic boundary, not necessarily weak identification.
A logit guard is nevertheless not an exact natural-coordinate boundary/KKT
solution. Therefore rejection by this implementation does not prove that the
broader model allowing estimated alpha/beta zeros has no solution. Proper
estimated simplex-face boundaries would require a separate constrained
parameterization and derivative audit, not relaxing the numerical guard or
post-estimation truncation of small coefficients.

The reported score removes outward derivatives at explicit box bounds only.
It is not a general KKT test for the coupled, implicit root-admissibility
region. In particular, positive subsistence demand in AIDADS requires
`m > sum(p_i*delta_i)` for every cell; full MAIDADS also requires a positive
supernumerary budget on a positive-slope, unambiguous utility branch. A sequence
approaching the lowest observed food budget can hit this open-domain frontier
without a finite interior optimum. Such a failed box-score result is retained
as exploratory, not relabelled converged merely because objective improvement
stopped. Extremely low purchase-record budgets are not raised, deleted or
selected according to the resulting elasticity signs.

There are 3K-1 structural parameters in AIDADS and 4K in MAIDADS, plus K(K-1)/2
concentrated residual-covariance parameters. Both sets count in AIC/BIC. These
are Gaussian working-model criteria, not p-values or LR tests. No bootstrap,
confidence intervals or elasticity p-values are produced.

## Elasticities

```
Q_u = Q*(1-sum_i phi_i,u*log(phi_i/p_i))
E_u = sum_i p_i*gamma_i,u + Q_u
q_i,u = gamma_i,u + (phi_i,u*Q+phi_i*Q_u)/p_i
eta_i = m*q_i,u/(q_i*E_u)
S_ij = Q*phi_i*phi_j/(p_i*p_j) - 1(i=j)*Q*phi_i/p_i^2
H_ij = S_ij*p_j/q_i
M_ij = H_ij-eta_i*w_j
```

eta is the conditional covered-food-budget elasticity, not an income elasticity.
Income responses require a separately estimated budget/income mapping. The
Hicksian shape follows the original expenditure function; no Cholesky
parameterization or post-estimation sign correction is used. Negative own
Hicksian elasticities alone do not validate prices, measurement or identification.

Representative responses use arithmetic mean m and geometric mean p. Cell
distributions and predictions are also saved, so a representative elasticity
is not confused with the mean of nonlinear cell elasticities. Distribution
quantiles refer to cells, not population-weighted household quantiles.

## Audit and status

Audit files report budget closure, share adding-up, numerical roots, Slutsky
symmetry, homogeneity, representative curvature eigenvalues and finite-difference
elasticity comparisons. A weighted share-Jacobian SVD on the inactive-bound
tangent coordinates diagnoses numerical rank at relative tolerance 1e-6;
this is not a formal identification proof. Weak-rank or nonstationary results
are explicitly exploratory. Native full MAIDADS can remain weakly identified
even when all accounting identities and elasticities are numerically valid.

### Independent Numerical Validation

The native analytical quantities, utility roots, expenditure elasticities and
full Marshallian/Hicksian matrices were independently compared with the latest
provincial Python functions. Maximum absolute discrepancies were below 5e-13;
Python was used for verification, not the main statistical estimation.

`code/02_test_identified.do` generates 480 three-good observations with utility
covering [-4,4], positive free low/high commitments and independently varied
prices. The unrestricted three-start estimate passed the qualification gate
with physical score 3.56e-6 and recovered omega 0.79384 (true 0.8), kappa 0.97972
(true 1), delta (9.89,19.97,14.85) (true 10,20,15), and tau
(29.89,24.97,40.13) (true 30,25,40). This validates recovery in an informative
synthetic setting; it does not validate the CCTV sample or guarantee global
optimization. A separate weaker synthetic design hit the omega upper guard and
was correctly marked unqualified despite a small score.

The experimental `maidadstangentfit`/`maidads_tangent_core.mata` variant projects
outward numerical-search directions onto near-active low-end commitment-cost
constraints to let other parameters continue moving. It does not replace the
original physical box-score gate with a relaxed constraint-KKT score. It is
recorded in separate output directories with `KERNEL_VERSION.txt`, never by
overwriting completed baseline or validation runs. An open-frontier infimum
still fails the finite, stationary main-fit standard.

## CLI

```
env STATATMP=/path/to/unique/job/tmp /usr/local/stata17/stata -b do \
  code/02_estimate.do input.csv output_dir maidads 8 3 400 "year<=2021"
```

Use a unique STATATMP directory per concurrently running Stata process. The CSV
requires numeric m, p1..pK, w1..wK, nonnegative shares, positive prices/budget and
share sums of one. Output `parameters.csv` contains natural endpoint parameters;
`model_summary.csv` contains omega/kappa; `scale.csv` preserves training scales.
Forecasts must use these natural parameters, never rescale endpoints using the
test sample. Outputs include full representative Marshallian/Hicksian matrices,
cell predictions, budget elasticities, distributions, candidates and audits.

`maidadsfit` returns raw coefficients in `e(b)`, the estimation sample in
`e(sample)`, and natural parameters in `e(alpha)`, `e(beta)`, `e(delta)` and
`e(tau)`. It intentionally returns no variance matrix: `e(vce)` is
`none_point_only`. `weight()` must contain positive finite values for every
retained observation. Raw coefficients and natural endpoint units are distinct.
