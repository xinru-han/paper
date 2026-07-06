### Table R1b (inference robustness). Wild cluster bootstrap p-values at the county level (12 clusters)

> `fwildclusterboot` unavailable for this R/CRAN snapshot; implemented as a Cameron-Gelbach-Miller (2008) WCR Rademacher bootstrap, B=999, restricted-residual resampling, refit per draw. Two-sided p = P(|t*| >= |t_obs|).

| Model | Coef. | Township-clustered SE (asymptotic) | Asymptotic p (township, 41 clusters) | **WCR bootstrap p (county, 12 clusters)** |
|---|---|---|---|---|
| Baseline | -0.1186 | (0.0455) | 0.0243 | **0.0841** |
| Province x Year FE | -0.1259 | (0.0519) | 0.0336 | **0.2222** |
| County-specific trends | -0.0844 | (0.0674) | 0.2361 | **0.5105** |
| Event study: 2020 x exposure | -0.2366 | (0.1797) | 0.2146 | **0.1742** |
| Event study: 2021 x exposure | -0.3265 | (0.0789) | 0.0017 | **0.0230** |

N: baseline=13787, prov x year=13787, county trends=13787, event-study=13922.

### Pre-trend joint Wald test (2013-2018 event-study coefficients = 0), reference

Wald F = 1.132, df1 = 6, df2 = 40, p = 0.362 (township-clustered; see tab_2023_persistence.md for the full event-study table and 01_baseline_and_dynamics_2023.R for the underlying model).

Note: WCR = wild cluster restricted bootstrap (Cameron, Gelbach & Miller 2008), Rademacher weights, B=999. Applied at the COUNTY level (xid, 12 clusters) because county-level CRVE with only 12 clusters is invalid (per modification plan Sec 3.2); the main text continues to report township-clustered SEs (41 clusters, adequate under conventional rules of thumb) alongside these bootstrap p-values as the more conservative/valid check.

