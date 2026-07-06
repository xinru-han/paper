### Table A-IV. IV appendix: Wuhan-distance instrument + placebo distance instruments

| Variable | Wuhan distance x post | Placebo: Beijing dist x post | Placebo: Shanghai dist x post | Placebo: Guangzhou dist x post |
|---|---|---|---|---|
| Log(Covid) [2SLS] | -0.7196** | 1.2703 | -0.8248 | -1.1605* |
|  | (0.3198) | (1.7315) | (0.5503) | (0.6648) |
| N | 13,787 | 13,787 | 13,787 | 13,787 |
| Within R2 | 0.018 | 0.016 | 0.015 | 0.019 |

Note: SE clustered by township in parentheses. * p<0.10, ** p<0.05, *** p<0.01.


### First-stage F-statistics

| Instrument | First-stage F |
|---|---|
| dist-Wuhan x post | 1272.1 |
| dist-Beijing x post | 266.1 |
| dist-Shanghai x post | 379.5 |
| dist-Guangzhou x post | 587.4 |

### Anderson-Rubin weak-instrument-robust 95% CI (Wuhan IV)

AR 95% CI: [-2.100, -0.220]  (grid search, beta0 in [-2.5,2.0], step 0.02, township-clustered Wald test per beta0)
Conventional (2SLS asymptotic) 95% CI: [-1.346, -0.093]

### Interpretation

MIXED, NOT CLEAN evidence. The Wuhan-distance instrument's first-stage F (1272) is 2-5x every placebo instrument's F (266-587), and its 2SLS coefficient is the most precisely estimated (p=0.030). However, the placebo results are NOT uniformly null: dist-Beijing x post is insignificant (p=0.47) and dist-Shanghai x post is insignificant (p=0.14), but dist-Guangzhou x post is ALSO marginally significant (b=-1.16, p=0.089) and similar in sign/magnitude to the Wuhan estimate. This is a genuine caveat, not a clean pass: at least one alternative distance-to-a-major-city instrument produces a marginally 'significant' 2SLS estimate too, consistent with the concern (raised for the main IV in Sec 3.4 of the modification plan) that distance-based instruments may partly proxy a general geography-of-development/labor-migration-corridor gradient rather than a Wuhan-specific epidemic shock. The stronger first stage and lower p-value for Wuhan is suggestive of some Wuhan-specificity, but the Guangzhou result means this evidence should NOT be oversold in the manuscript -- report it as partially reassuring, explicitly flag the Guangzhou placebo as a residual identification concern, and lean on the event-study + province x year FE + county-trends evidence (Sec 3.1) as the primary identification argument, with the IV kept firmly in the appendix.

Note: given only 12 counties, all inference here should be read as suggestive; the IV strategy is reported as an APPENDIX robustness check, not as the paper's primary identification strategy (see main text Sec. 3.1, event-study + province x year FE + county trends).

