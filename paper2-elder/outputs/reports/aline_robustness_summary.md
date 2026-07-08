# A-line robustness summary
- Permutation p-value (1000 within-village reshuffles): 0.001
- Oster beta* (delta=1, Rmax=1.3 R2): 0.579 (OLS long: 0.566); delta for beta=0: -44.08
- CAUTION on delta_for_beta0: a large negative delta is NOT positive evidence of identification; it only says that, GIVEN the current observables, unobserved selection would have to act in the opposite direction and be implausibly strong to zero out the coefficient. It cannot rule out unobservables uncorrelated with the included controls.
- Estimator naming: IPW/entropy-balancing/AIPW use ATT-type weights but identify an adjusted (weighted) contrast under selection-on-observables, not a causal ATT.
- Estimator range: 0.532 to 0.592
- Matched sample: 254 pairs of 262 treated
