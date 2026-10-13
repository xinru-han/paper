# Finite-domain, varying-share corner extension

This is a separate methodological prototype. It does not replace the canonical
`alpha = beta` corner estimates, and it is not the unrestricted original
MAIDADS expenditure-function model.

## Utility and Quantity Domain

For positive endpoint shares summing to one, define

```
phi_i(u) = alpha_i (1 - s(u)) + beta_i s(u)
a_i(u)   = C(u) low_i
C(u)     = 1 - (1-r) s(omega u),  0 < r < 1, omega > 0
F(q,u)   = sum_i phi_i(u) log(q_i+a_i(u)) - u - kappa.
```

The model is defined and certified on the explicit box
`0 <= q_i <= Qmax_i`. A sufficient purchase-demand domain is
`0 < m <= mmax`, `p_i >= pmin_i > 0`, and
`Qmax_i = mmax/pmin_i`. Quantity and expenditure are first divided by the
fixed training expenditure scale. Zero purchases are allowed; no positive
constant is added to observed quantities or expenditures. The positive
`a_i` are preference shift parameters, not altered observations.

At a fixed utility, maximizing `F` under the purchase budget gives the same
water-filling KKT system as the general corner code:

```
q_i = max(phi_i / (nu p_i) - a_i, 0),
nu  = sum_active phi_i / (m + sum_active p_i a_i).
```

The active set is endogenous. It is not the observed positive-purchase set.
For fixed `u`, the upper contour is convex, because `F` is concave in `q`.
If `F_u < 0` throughout the stated box, the unique implicit utility orders
these upper contours consistently there. This is a **finite quantity-domain**
regularity certificate, not a global certificate for unlimited quantities.

## A Corrected Sufficient Bound

Let `Delta_i = beta_i-alpha_i`, so `sum Delta_i=0`. Differentiating at fixed
quantities yields

```
F_u = s(u)(1-s(u)) sum Delta_i log(q_i+C low_i)
      + C'(u) sum phi_i low_i/(q_i+C low_i) - 1.
```

The second term is nonpositive. The common `log C` cancels from the first
term. Since `r <= C <= 1`,

```
L_i = log(low_i)
U_i = log(Qmax_i/r+low_i)
L_i <= log(q_i/C+low_i) <= U_i.
A = sum_{Delta_i>0} Delta_i U_i
    + sum_{Delta_i<0} Delta_i L_i.
F_u <= max(0,A)/4 - 1.
```

The `max(0,A)` is essential. If `A<0`, replacing it by `A/4` is not an upper
bound: the logistic derivative tends to zero at the endpoints. This corrects
the proposed unqualified signed bound.

Let `TV(alpha,beta)=0.5 sum |Delta_i|` and

```
R = max_i U_i - min_i L_i >= 0.
```

Then `A <= TV R` and the simpler, always valid certificate is

```
F_u <= TV(alpha,beta) R/4 - 1.
```

## Random Tastes: An Endpoint-Ratio Certificate

The same taste multipliers `t_i=exp(sigma epsilon_i)>0` reweight both
endpoints:

```
alpha*_i = alpha_i t_i / sum alpha_j t_j
beta*_i  = beta_i  t_i / sum beta_j  t_j.
```

Consequently the range
`H = max log(beta_i/alpha_i) - min log(beta_i/alpha_i)` is invariant under
reweighting. For any positive probability vectors with this ratio range,

```
TV(alpha*,beta*) <= tanh(H/4).
```

Proof: write `L_i=beta*_i/alpha*_i`, with `a<=L_i<=b`,
`E_alpha* L=1`, and `b/a=exp(H)`. Convexity of `(L-1)_+` implies
`TV <= (b-1)(1-a)/(b-a)`. Maximizing this expression over `a`, subject to
`b=a exp(H)`, gives `a=exp(-H/2)`, `b=exp(H/2)`, and the displayed value.
It is sharp as a supremum over positive common reweightings: concentrate
probability on goods attaining the two endpoint ratio extremes.

Thus, for every random-taste draw, not only the finite integration draws,

```
F_u <= tanh(H/4) R/4 - 1.
```

For family-specific common shift multipliers, calculate `R` separately for
each allowed family and use the largest value. The prototype maps the raw
endpoint tilt into an `H` cap ensuring this bound is strictly below `-0.1`.
The cap depends on the declared domain and candidate shift parameters. This
is an explicit preference restriction, not evidence that unrestricted
preferences satisfy regularity.

## What This Does And Does Not Resolve

- Both endpoints vary, so budget nonhomotheticity is less restricted than
  `alpha=beta`. The previous `alpha=beta` proof of all-normality no longer
  applies. Whether this particular sufficient cap also restricts observed
  budget-response signs requires further analysis; the prototype must not
  report all-normality or unrestricted inferiority as a data-supported finding.
- Own Hicksian responses are nonpositive where the finite-domain ordering
  and the differentiable fixed-utility allocation apply. This is an intrinsic
  utility property, not a Cholesky reparameterization or sign screening.
- The fixed-utility shifted-log allocation also has nonnegative Hicksian
  cross-price derivatives between active goods. Common taste mixing does not
  remove this compensated gross-substitution restriction. Varying `phi(u)`
  therefore does not create a fully general complementarity system.
- Fixed-population expected purchase quantities integrate zero and positive
  outcomes. Conditional-positive means and purchase probabilities are
  separate response measures.
- `mmax`, `pmin`, and `Qmax` must be exported. Any forecast outside them is
  unqualified, even if the numerical solver returns a root.
- This does not repair invalid external price proxies, survey measurement,
  support-node approximation, expenditure endogeneity, or weak identification.
- No bootstrap, covariance matrix, p values, or confidence intervals are
  manufactured by this prototype.

## Actual Pilot Domain

The prototype is designed to retain every positive-budget, complete-quarter
CCTV purchase observation used by the canonical pilot. Its domain is set
before estimation to twice the largest eligible scaled budget and 80% of
each good's smallest observed eligible reference price. This covers an
explicit budget-doubling and up-to-20% price-decrease envelope, not every
income forecast: the first-stage income-to-budget prediction still has to be
checked against the budget domain. The source prices are common province-
quarter external reference prices; household unit values are not substituted.
The domain uses covariate/budget support from all eligible 2020-2022 records;
the shares and participation targets in 2022 are not fitted. This is a
conditional-demand held-out test with a predeclared observed-input domain,
not a fully prospective forecast whose future covariate support was unknown.

Eight actual budget-quantile support observations per province/family/income
stratum and 64 fixed integration draws improve on the canonical 2-node,
16-draw fitting approximation. This remains a support pilot, not full-sample
estimation; budgets and participation moment distortion must be exported.
Optimization is bounded, checkpointed, and classified as unconverged if the
time/evaluation cap is hit.

The current prototype is eight-good specific. It fixes `omega=0.7` and
`kappa=0`, retains four family common-shift multipliers, bounds `r` in
`[0.02,0.98]` and the taste standard deviation in `[0.05,4]`, and uses
27 raw parameters. These are disclosed compact-pilot restrictions; this is
not a claim that all original MAIDADS parameters are freely identified.

## Reproduction And Output Codes

Run, with a distinct existing `STATATMP` directory for each process:

```
stata-se -b do code/03_freephi_theory_test.do
stata-se -b do code/03_freephi_fit.do start1
stata-se -b do code/03_freephi_full_holdout.do
stata-se -b do code/03_freephi_elasticity.do
stata-se -b do code/03_freephi_identification.do
```

`03_freephi_fit.do` requires the canonical fitted parameter file as a numerical
initialization, not as a fixed parameter restriction. Without `start1` it runs
both predefined starting points. Each starting point has a 1,200-second /
1,200-evaluation cap and a 450-iteration limit. The best checkpoint is retained,
but cap hits cannot be relabeled convergence.

In `full_holdout_prediction_metrics.csv`, `model_code=0` is this prototype,
`-1` is the full-training-sample constant-mean baseline, and `-2` is the
province-by-calendar-quarter full-training-sample historical baseline. An
unseen historical cell uses the global training mean; its count is exported.
The three rows of `full_holdout_fit.csv` are observed mean, predicted mean,
and full-training-sample mean. Moment-Jacobian rank is a finite-64-draw,
finite-step sensitivity diagnostic, not proof of population identification.
No AIC/BIC or chi-squared model-selection p value is assigned to this SMD loss.
