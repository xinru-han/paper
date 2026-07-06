# 4. Model

The empirical model is a saturated six-good MAIDADS demand system. For province-year observation c and good i, fitted demand is

```text
x_ci = gamma_i(u_c) + phi_i(u_c) [m_c - sum_j p_cj gamma_j(u_c)] / p_ci .
```

The marginal budget share is

```text
phi_i(u) = [alpha_i + beta_i exp(u)] / [1 + exp(u)],
```

and the subsistence term is

```text
gamma_i(u) = [delta_i + tau_i exp(omega u)] / [1 + exp(omega u)].
```

Utility is solved from the implicit equation

```text
sum_i phi_i(u_c) ln[x_ci - gamma_i(u_c)] - u_c - kappa = 0.
```

The saturated specification imposes beta equal to zero for covered food groups and one for the other/non-covered residual. The model is estimated by concentrated likelihood using quantity errors. AIDADS is estimated first and then used to initialize MAIDADS. Multi-start diagnostics, boundary reports, and gradient summaries are retained as part of the paper evidence package.

Income elasticities are computed by the model's prediction function using central differences. Marshallian price elasticities and Hicksian elasticities are reported for completeness and for demand-system checks, but price elasticity is not positioned as the main contribution because MAIDADS has limited independent price flexibility and provincial unit values may contain quality variation.

Unsupported or weak claims to resolve:
- Add direct analytic-vs-numeric elasticity unit tests before final submission.
- Add a stronger treatment of panel dependence beyond cluster bootstrap.
