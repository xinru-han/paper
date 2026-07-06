# CRITICAL CORRECTION — 7-group MAIDADS global optimum (2026-07-04)

## What happened
The 7-group MAIDADS likelihood surface has a deceptive local basin at nll ≈ −4344
(omega≈0.198, kappa≈1.31). The multistart in an earlier run converged there. That
basin produces a SPURIOUS negative pork income elasticity and a flat-to-declining
feed-grain trajectory — both artifacts of the wrong optimum.

Seeding a local optimization from the published paper's 2015–2023 parametrization
(omega=0.80, kappa=6.27) and re-optimizing on the 2015–2024 data reaches
nll = −4481.55 (omega=0.705, kappa=4.91), which is BETTER by ~137 nll and
qualitatively matches the paper.

## Correct optimum (authoritative)
- MAIDADS_sat: nll = −4481.554, k=22, AIC = −8919.11, BIC = −8836.90
- AIDADS_sat:  nll = −4248.285, k=14, AIC = −8468.57, BIC = −8416.26
- LR = 2*(4481.554 − 4248.285) = 466.54, df = 8  → MAIDADS decisively preferred
- Pork income elasticity POSITIVE: +0.93 @¥10k, +0.34 @¥20k, +0.17 @¥30k, →0 at high income (mature normal good)
- Feed-grain total RISES: 378.3 (2030) → 389.3 (2035) → 393.4 (2050) Mt; pork ≈42% of feed-grain

## Files
- Warm-start vector: scripts/maidads_warmstart_7g.npy (the −4481.55 optimum)
- Bad-basin backup:   scripts/maidads_warmstart_7g_BAD4344.npy.bak
- Authoritative bootstrap: Results/FormalBootstrap_correct/ (warm-started from −4481.55)
- DEFUNCT bootstrap (wrong basin, could not be killed): Results/FormalBootstrap/
